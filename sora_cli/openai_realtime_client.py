"""OpenAI Realtime API WebRTC bridge for S0RA voice flows.

Uses ephemeral tokens (POST /v1/realtime/sessions) for secure browser-less
WebRTC connections. Audio I/O: PCM16 24kHz mono (OpenAI native format).
"""
from __future__ import annotations

import asyncio
import base64
import json
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

import aiohttp

from sora_logging import get_logger

logger = get_logger(__name__)

OPENAI_REALTIME_SESSIONS = "https://api.openai.com/v1/realtime/sessions"


@dataclass
class OpenAIRealtimeConfig:
    """Runtime config for an OpenAI Realtime session."""

    api_key: str
    model: str = "gpt-4o-realtime-preview"
    voice: str = "alloy"
    instructions: str = "You are a helpful voice assistant."
    modalities: list[str] = field(default_factory=lambda: ["audio", "text"])
    temperature: float = 0.8
    input_audio_format: str = "pcm16"
    output_audio_format: str = "pcm16"


async def create_ephemeral_token(config: OpenAIRealtimeConfig) -> dict[str, Any]:
    """Request an ephemeral Realtime session token from OpenAI.

    Returns the full session object which includes client_secret.value
    (the ephemeral key) and the WebRTC ICE server configuration.
    """
    payload: dict[str, Any] = {
        "model": config.model,
        "voice": config.voice,
        "modalities": config.modalities,
        "instructions": config.instructions,
        "temperature": config.temperature,
        "input_audio_format": config.input_audio_format,
        "output_audio_format": config.output_audio_format,
    }

    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            OPENAI_REALTIME_SESSIONS, json=payload, headers=headers
        ) as resp:
            body = await resp.text()
            if resp.status != 200:
                raise RuntimeError(
                    f"OpenAI ephemeral token failed: HTTP {resp.status}: {body[:300]}"
                )
            data = json.loads(body)
            logger.info("Ephemeral token obtained for model=%s", config.model)
            return data


class OpenAIRealtimeClient:
    """Async client for OpenAI Realtime API via WebRTC.

    Audio input: PCM16 24kHz mono → base64-encoded JSON events.
    Audio output: base64-encoded PCM16 24kHz mono from server events.

    Callbacks:
        on_audio(bytes, meta) — called when server produces audio output.
        on_transcript(str, meta) — called for input/output transcripts.
        on_error(str) — called on connection/parsing errors.
    """

    def __init__(
        self,
        config: OpenAIRealtimeConfig,
        on_audio: Optional[Callable[[bytes, dict[str, Any]], Awaitable[None]]] = None,
        on_transcript: Optional[Callable[[str, dict[str, Any]], Awaitable[None]]] = None,
        on_error: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> None:
        self.config = config
        self.on_audio = on_audio
        self.on_transcript = on_transcript
        self.on_error = on_error
        self.session_data: Optional[dict[str, Any]] = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        """Mint ephemeral token and prepare session.

        Full WebRTC connection requires a browser or aiortc peer connection.
        For headless/server usage, token minting alone is sufficient —
        the token can be passed to a browser-side WebRTC client.
        """
        self.session_data = await create_ephemeral_token(self.config)
        self._connected = True
        logger.info("OpenAI Realtime session ready (token minted)")

    async def disconnect(self) -> None:
        """Mark session as disconnected."""
        self._connected = False
        self.session_data = None
        logger.info("OpenAI Realtime session closed")

    async def send_audio(self, pcm_bytes: bytes) -> None:
        """Enqueue PCM16 audio for the Realtime session.

        In a full WebRTC implementation this would send via the data channel.
        For headless use, this is a no-op that logs the chunk size.
        """
        if not self._connected:
            logger.warning("Cannot send audio: not connected")
            return
        logger.debug("Audio chunk queued: %d bytes", len(pcm_bytes))

    def ephemeral_key(self) -> Optional[str]:
        """Return the ephemeral API key for browser-side WebRTC client."""
        if not self.session_data:
            return None
        return self.session_data.get("client_secret", {}).get("value")
