"""Ultravox voice bridge for S0RA voice flows.

Ultravox provides a managed STT → LLM → TTS pipeline. The bridge only
handles audio I/O — no separate STT/TTS providers needed.
Audio: PCM16 16kHz mono (bidirectional).
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

import aiohttp
import websockets

from sora_logging import get_logger

logger = get_logger(__name__)

ULTRAVOX_API = "https://api.ultravox.ai/api"


@dataclass
class UltravoxConfig:
    """Runtime config for an Ultravox voice session."""

    api_key: str
    model: str = "fixie-ai/ultravox"
    voice: str = "default"
    system_prompt: str = "You are a helpful voice assistant."
    temperature: float = 0.8


async def create_ultravox_call(config: UltravoxConfig) -> str:
    """Create a new Ultravox call and return the join URL (WebSocket)."""
    payload = {
        "model": config.model,
        "voice": config.voice,
        "systemPrompt": config.system_prompt,
        "temperature": config.temperature,
        "medium": {"serverWebSocket": {}},
    }
    headers = {
        "X-API-Key": config.api_key,
        "Content-Type": "application/json",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{ULTRAVOX_API}/calls", json=payload, headers=headers
        ) as resp:
            body = await resp.text()
            if resp.status not in (200, 201):
                raise RuntimeError(
                    f"Ultravox call creation failed: HTTP {resp.status}: {body[:300]}"
                )
            data = json.loads(body)
            join_url = data.get("joinUrl")
            if not join_url:
                raise RuntimeError("Ultravox response missing joinUrl")
            logger.info("Ultravox call created: %s", data.get("callId", "unknown"))
            return join_url


class UltravoxClient:
    """Async client for Ultravox voice AI via WebSocket.

    Audio input: raw PCM16 16kHz mono sent as binary frames.
    Audio output: raw PCM16 16kHz mono received as binary frames.

    Callbacks:
        on_audio(bytes, meta) — server audio output.
        on_transcript(str, meta) — transcription text.
        on_error(str) — connection errors.
    """

    def __init__(
        self,
        config: UltravoxConfig,
        on_audio: Optional[Callable[[bytes, dict[str, Any]], Awaitable[None]]] = None,
        on_transcript: Optional[Callable[[str, dict[str, Any]], Awaitable[None]]] = None,
        on_error: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> None:
        self.config = config
        self.on_audio = on_audio
        self.on_transcript = on_transcript
        self.on_error = on_error
        self.ws: Any = None
        self._receive_task: Optional[asyncio.Task] = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self.ws is not None

    async def connect(self) -> None:
        """Create Ultravox call and open WebSocket for audio streaming."""
        join_url = await create_ultravox_call(self.config)

        self.ws = await websockets.connect(
            join_url,
            ping_interval=20,
            ping_timeout=20,
        )
        self._connected = True
        self._receive_task = asyncio.create_task(self._receive_loop())
        logger.info("Ultravox session connected (model=%s)", self.config.model)

    async def disconnect(self) -> None:
        """Close the WebSocket connection."""
        self._connected = False
        if self._receive_task:
            self._receive_task.cancel()
            self._receive_task = None
        if self.ws:
            await self.ws.close()
            self.ws = None
        logger.info("Ultravox session disconnected")

    async def send_audio(self, pcm_bytes: bytes) -> None:
        """Send PCM16 audio as binary frame to Ultravox."""
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
                    msg_type = msg.get("type", "")
                    if msg_type == "transcript" and self.on_transcript:
                        text = msg.get("text", "")
                        if text:
                            await self.on_transcript(text, msg)
                    elif msg_type == "error" and self.on_error:
                        err = msg.get("message", "Unknown Ultravox error")
                        await self.on_error(err)
        except websockets.ConnectionClosed:
            logger.info("Ultravox WebSocket closed")
        except Exception as exc:
            logger.error("Ultravox receive loop error: %s", exc)
            if self.on_error:
                await self.on_error(str(exc))
        finally:
            self._connected = False
