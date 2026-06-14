"""ElevenLabs Conversational AI WebSocket helpers for S0RA voice flows."""
from __future__ import annotations

import asyncio
import base64
import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

import aiohttp
import websockets


ELEVENLABS_CONVAI_WS = "wss://api.elevenlabs.io/v1/convai/conversation"
ELEVENLABS_SIGNED_URL = "https://api.elevenlabs.io/v1/convai/conversation/get-signed-url"


@dataclass
class ElevenLabsConversationConfig:
    """Runtime config for an ElevenLabs Conversational AI session."""

    agent_id: str
    api_key: Optional[str] = None
    signed_url: Optional[str] = None


def public_conversation_url(agent_id: str) -> str:
    """Build the public-agent ElevenLabs Conversation WebSocket URL."""
    return f"{ELEVENLABS_CONVAI_WS}?agent_id={agent_id}"


async def get_signed_conversation_url(agent_id: str, api_key: str) -> str:
    """Fetch a signed Conversation WebSocket URL for a private agent."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{ELEVENLABS_SIGNED_URL}?agent_id={agent_id}",
            headers={"xi-api-key": api_key},
        ) as resp:
            body = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f"ElevenLabs signed URL failed: HTTP {resp.status}: {body[:200]}")
            data = json.loads(body)
            signed_url = data.get("signed_url")
            if not signed_url:
                raise RuntimeError("ElevenLabs signed URL response did not contain signed_url")
            return signed_url


class ElevenLabsConversationClient:
    """Small async client for the ElevenLabs Conversational AI WebSocket.

    Audio input is sent as JSON events using the official `user_audio_chunk`
    field, where the value is a base64-encoded PCM chunk. Audio output arrives
    in `type=audio` events under `audio_event.audio_base_64`.
    """

    def __init__(
        self,
        config: ElevenLabsConversationConfig,
        on_audio: Optional[Callable[[bytes, dict[str, Any]], Awaitable[None]]] = None,
        on_transcript: Optional[Callable[[str, dict[str, Any]], Awaitable[None]]] = None,
        on_agent_response: Optional[Callable[[str, dict[str, Any]], Awaitable[None]]] = None,
    ) -> None:
        self.config = config
        self.on_audio = on_audio
        self.on_transcript = on_transcript
        self.on_agent_response = on_agent_response
        self.websocket: Any = None
        self._receive_task: Optional[asyncio.Task] = None

    async def resolve_url(self) -> str:
        if self.config.signed_url:
            return self.config.signed_url
        if self.config.api_key:
            return await get_signed_conversation_url(self.config.agent_id, self.config.api_key)
        return public_conversation_url(self.config.agent_id)

    async def connect(self) -> None:
        url = await self.resolve_url()
        self.websocket = await websockets.connect(url, ping_interval=20, ping_timeout=20)
        await self.websocket.send(json.dumps({"type": "conversation_initiation_client_data"}))
        self._receive_task = asyncio.create_task(self._receive_loop())

    async def close(self) -> None:
        task = self._receive_task
        self._receive_task = None
        if task:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def send_audio(self, pcm_chunk: bytes) -> None:
        """Send a PCM chunk to ElevenLabs as a base64 user_audio_chunk event."""
        if not self.websocket:
            raise RuntimeError("ElevenLabs conversation is not connected")
        await self.websocket.send(json.dumps({"user_audio_chunk": base64.b64encode(pcm_chunk).decode("ascii")}))

    async def send_contextual_update(self, text: str) -> None:
        if not self.websocket:
            raise RuntimeError("ElevenLabs conversation is not connected")
        await self.websocket.send(json.dumps({"type": "contextual_update", "text": text}))

    async def _receive_loop(self) -> None:
        assert self.websocket is not None
        async for raw in self.websocket:
            event = json.loads(raw) if isinstance(raw, str) else json.loads(raw.decode("utf-8"))
            await self.handle_event(event)

    async def handle_event(self, event: dict[str, Any]) -> None:
        """Handle one server event, including ping/pong and decoded audio."""
        event_type = event.get("type")
        if event_type == "ping":
            ping = event.get("ping_event") or {}
            delay_ms = ping.get("ping_ms") or 0
            if delay_ms:
                await asyncio.sleep(float(delay_ms) / 1000.0)
            if self.websocket:
                await self.websocket.send(json.dumps({"type": "pong", "event_id": ping.get("event_id")}))
            return

        if event_type == "audio" and self.on_audio:
            audio_event = event.get("audio_event") or {}
            chunk = base64.b64decode(audio_event.get("audio_base_64") or "")
            await self.on_audio(chunk, event)
            return

        if event_type == "user_transcript" and self.on_transcript:
            text = (event.get("user_transcription_event") or {}).get("user_transcript") or ""
            await self.on_transcript(text, event)
            return

        if event_type in {"agent_response", "agent_response_correction"} and self.on_agent_response:
            payload = event.get("agent_response_event") or event.get("agent_response_correction_event") or {}
            text = payload.get("agent_response") or payload.get("corrected_agent_response") or ""
            await self.on_agent_response(text, event)
