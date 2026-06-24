"""Retell AI voice bridge for S0RA voice flows.

Retell uses a web call model: create a call via REST API, get a WebSocket
URL, then stream bidirectional audio. Supports telephony and web calls.
Audio: PCM16 16kHz mono (bidirectional).
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

import aiohttp
import websockets

from sora_logging import get_logger

logger = get_logger(__name__)

RETELL_API = "https://api.retellai.com"
RECONNECT_BACKOFF = (1, 2, 4, 8, 16)


@dataclass
class RetellConfig:
    """Runtime config for a Retell voice session."""

    api_key: str
    agent_id: str
    voice_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


async def create_web_call(config: RetellConfig) -> dict[str, Any]:
    """Create a new Retell web call and return the call details.

    Returns a dict with 'call_id' and 'websocket_url' for audio streaming,
    plus 'access_token' for the Retell client SDK.
    """
    payload: dict[str, Any] = {
        "agent_id": config.agent_id,
    }
    if config.voice_id:
        payload["override_agent"] = {"voice": {"voice_id": config.voice_id}}
    if config.metadata:
        payload["metadata"] = config.metadata

    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{RETELL_API}/v2/create-web-call", json=payload, headers=headers
        ) as resp:
            body = await resp.text()
            if resp.status not in (200, 201):
                raise RuntimeError(
                    f"Retell web call creation failed: HTTP {resp.status}: {body[:300]}"
                )
            data = json.loads(body)
            call_id = data.get("call_id")
            if not call_id:
                raise RuntimeError("Retell response missing call_id")
            logger.info("Retell web call created: %s", call_id)
            return data


class RetellClient:
    """Async client for Retell AI voice agents via WebSocket.

    Audio input: raw PCM16 16kHz mono sent as binary frames.
    Audio output: raw PCM16 16kHz mono received as binary frames.

    Callbacks:
        on_audio(bytes, meta) — server audio output.
        on_transcript(str, meta) — transcription text.
        on_error(str) — connection errors.
    """

    def __init__(
        self,
        config: RetellConfig,
        on_audio: Optional[Callable[[bytes, dict[str, Any]], Awaitable[None]]] = None,
        on_transcript: Optional[Callable[[str, dict[str, Any]], Awaitable[None]]] = None,
        on_error: Optional[Callable[[str], Awaitable[None]]] = None,
        connection_timeout: float = 30,
    ) -> None:
        self.config = config
        self.on_audio = on_audio
        self.on_transcript = on_transcript
        self.on_error = on_error
        self.connection_timeout = connection_timeout
        self.ws: Any = None
        self.call_data: Optional[dict[str, Any]] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self.ws is not None

    async def connect(self) -> None:
        """Create Retell web call and open WebSocket for audio."""
        self.call_data = await create_web_call(self.config)

        ws_url = self.call_data.get("websocket_url")
        if not ws_url:
            # Fall back to access token based connection via Retell SDK pattern
            access_token = self.call_data.get("access_token")
            if not access_token:
                raise RuntimeError("Retell response missing websocket_url and access_token")
            ws_url = f"wss://api.retellai.com/audio/websocket?access_token={access_token}"

        try:
            self.ws = await websockets.connect(
                ws_url,
                open_timeout=self.connection_timeout,
                ping_interval=20,
                ping_timeout=20,
            )
            self._connected = True
            self._receive_task = asyncio.create_task(self._receive_loop())
            logger.info("Retell session connected (call_id=%s)", self.call_data.get("call_id", "unknown"))
        except Exception as exc:
            self._connected = False
            self.ws = None
            logger.error("Retell WebSocket connection failed: %s", exc)
            raise

    async def reconnect(self) -> bool:
        """Reconnect with bounded exponential backoff."""
        await self.disconnect()
        for attempt, delay in enumerate(RECONNECT_BACKOFF, start=1):
            await asyncio.sleep(delay)
            try:
                await self.connect()
                return True
            except Exception as exc:
                logger.error(
                    "Retell reconnect attempt %d/%d failed: %s",
                    attempt,
                    len(RECONNECT_BACKOFF),
                    exc,
                )
        return False

    async def health_check(self) -> bool:
        """Ping the active WebSocket and return whether it responds."""
        if not self.is_connected:
            return False
        try:
            pong_waiter = await self.ws.ping()
            await asyncio.wait_for(pong_waiter, timeout=self.connection_timeout)
            return True
        except Exception as exc:
            logger.error("Retell WebSocket health check failed: %s", exc)
            return False

    async def disconnect(self) -> None:
        """Close the WebSocket connection."""
        self._connected = False
        if self._receive_task:
            self._receive_task.cancel()
            self._receive_task = None
        if self.ws:
            await self.ws.close()
            self.ws = None
        logger.info("Retell session disconnected")

    async def send_audio(self, pcm_bytes: bytes) -> None:
        """Send PCM16 audio as binary frame to Retell."""
        if not self.is_connected:
            logger.warning("Cannot send audio: not connected")
            return
        await self.ws.send(pcm_bytes)

    async def _receive_loop(self) -> None:
        """Receive and dispatch server events (binary=audio, text=json)."""
        try:
            async for message in self.ws:
                if isinstance(message, bytes):
                    if self.on_audio:
                        await self.on_audio(message, {})
                elif isinstance(message, str):
                    try:
                        msg = json.loads(message)
                    except json.JSONDecodeError:
                        continue
                    msg_type = msg.get("event", "")
                    if msg_type == "transcript" and self.on_transcript:
                        text = msg.get("transcript", {}).get("text", "")
                        if text:
                            await self.on_transcript(text, msg)
                    elif msg_type == "error" and self.on_error:
                        err = msg.get("error", {}).get("message", "Unknown Retell error")
                        await self.on_error(err)
        except websockets.ConnectionClosed:
            logger.info("Retell WebSocket closed")
        except Exception as exc:
            logger.error("Retell receive loop error: %s", exc)
            if self.on_error:
                await self.on_error(str(exc))
        finally:
            self._connected = False
