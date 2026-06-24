"""xAI Grok Realtime WebSocket bridge for S0RA voice flows.

Connects to wss://api.x.ai/v1/realtime with xai-api-key auth.
Audio I/O: PCM16 16kHz mono (same format as Gemini Live).
"""
from __future__ import annotations

import asyncio
import base64
import json
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

import aiohttp
import websockets

from sora_logging import get_logger

logger = get_logger(__name__)

XAI_REALTIME_WS = "wss://api.x.ai/v1/realtime"
RECONNECT_BACKOFF = (1, 2, 4, 8, 16)


@dataclass
class XAIConfig:
    """Runtime config for an xAI Grok Realtime session."""

    api_key: str
    model: str = "grok-2-realtime"
    voice: str = "ember"
    instructions: str = "You are a helpful voice assistant."
    modalities: list[str] = field(default_factory=lambda: ["audio", "text"])
    temperature: float = 0.8


class XAIClient:
    """Async client for xAI Grok Realtime API via WebSocket.

    Audio input: PCM16 16kHz mono → base64 JSON events.
    Audio output: base64 PCM from server audio events.

    Callbacks:
        on_audio(bytes, meta) — server audio output.
        on_transcript(str, meta) — transcription text.
        on_error(str) — connection/parsing errors.
    """

    def __init__(
        self,
        config: XAIConfig,
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
        self._receive_task: Optional[asyncio.Task] = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self.ws is not None

    async def connect(self) -> None:
        """Open WebSocket to xAI Realtime API and send session config."""
        headers = {
            "x-api-key": self.config.api_key,
        }
        # Build query params with model
        url = f"{XAI_REALTIME_WS}?model={self.config.model}"

        try:
            self.ws = await websockets.connect(
                url,
                additional_headers=headers,
                open_timeout=self.connection_timeout,
                ping_interval=20,
                ping_timeout=20,
            )

            # Send session update to configure voice
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": self.config.modalities,
                    "instructions": self.config.instructions,
                    "voice": self.config.voice,
                    "temperature": self.config.temperature,
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                },
            }
            await self.ws.send(json.dumps(session_config))
            self._connected = True
            self._receive_task = asyncio.create_task(self._receive_loop())
            logger.info("xAI Grok session connected (model=%s)", self.config.model)
        except Exception as exc:
            self._connected = False
            if self.ws:
                await self.ws.close()
            self.ws = None
            logger.error("xAI WebSocket connection failed: %s", exc)
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
                    "xAI reconnect attempt %d/%d failed: %s",
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
            logger.error("xAI WebSocket health check failed: %s", exc)
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
        logger.info("xAI Grok session disconnected")

    async def send_audio(self, pcm_bytes: bytes) -> None:
        """Send a PCM16 audio chunk to xAI."""
        if not self.is_connected:
            logger.warning("Cannot send audio: not connected")
            return
        b64 = base64.b64encode(pcm_bytes).decode("ascii")
        message = {
            "type": "input_audio_buffer.append",
            "audio": b64,
        }
        await self.ws.send(json.dumps(message))

    async def _receive_loop(self) -> None:
        """Receive and dispatch server events."""
        try:
            async for raw in self.ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                msg_type = msg.get("type", "")

                if msg_type == "response.audio.delta" and self.on_audio:
                    b64 = msg.get("delta", "")
                    if b64:
                        pcm = base64.b64decode(b64)
                        await self.on_audio(pcm, msg)
                elif msg_type == "response.audio_transcript.done" and self.on_transcript:
                    text = msg.get("transcript", "")
                    if text:
                        await self.on_transcript(text, msg)
                elif msg_type == "error" and self.on_error:
                    err = msg.get("error", {}).get("message", "Unknown xAI error")
                    await self.on_error(err)
        except websockets.ConnectionClosed:
            logger.info("xAI WebSocket closed")
        except Exception as exc:
            logger.error("xAI receive loop error: %s", exc)
            if self.on_error:
                await self.on_error(str(exc))
        finally:
            self._connected = False
