"""
Dograh Client
=============
WebSocket client for Dograh → Gemini Live bridge.
Dograh speaks the Gemini Live protocol with auth wrapper.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import aiohttp

log = logging.getLogger("sora.voip.dograh")


@dataclass
class DograhEvent:
    """Normalized Dograh event."""
    event_type: str
    session_id: str
    audio_data: Optional[bytes] = None
    transcript: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = None


class DograhClient:
    """
    Dograh WebSocket client for Gemini Live sessions.
    Handles multiple concurrent sessions (one per call).
    """

    def __init__(
        self,
        ws_url: str,
        api_key: str = "",
        model: str = "gemini-2.0-flash-exp",
    ):
        self.ws_url = ws_url
        self.api_key = api_key
        self.model = model

        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._connected = False

        self._sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> session info
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._ws_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """Connect to Dograh WebSocket."""
        if self._connected:
            return

        self._session = aiohttp.ClientSession()

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self._ws = await self._session.ws_connect(self.ws_url, headers=headers)
        self._connected = True

        self._ws_task = asyncio.create_task(self._ws_listener())
        log.info("Dograh connected", extra={"url": self.ws_url})

    async def disconnect(self) -> None:
        """Disconnect from Dograh."""
        self._connected = False

        # End all sessions
        for session_id in list(self._sessions.keys()):
            await self.end_session(session_id)

        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass

        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()

        log.info("Dograh disconnected")

    def is_connected(self) -> bool:
        return self._connected and self._ws and not self._ws.closed

    def get_status(self) -> Dict[str, Any]:
        """Get client status."""
        return {
            "connected": self.is_connected(),
            "url": self.ws_url,
            "model": self.model,
            "active_sessions": len(self._sessions),
            "sessions": list(self._sessions.keys()),
        }

    async def reconfigure(
        self,
        ws_url: str = None,
        api_key: str = None,
        model: str = None,
    ) -> None:
        """Hot-reconfigure client."""
        if ws_url:
            self.ws_url = ws_url
        if api_key is not None:
            self.api_key = api_key
        if model:
            self.model = model

        # Reconnect if URL changed
        if ws_url and self._connected:
            await self.disconnect()
            await self.connect()

        log.info("Dograh client reconfigured", extra={"url": self.ws_url, "model": self.model})

    # ──────────────────────────────────────────
    # Event handling
    # ──────────────────────────────────────────

    def on_event(self, event_type: str, handler: Callable) -> None:
        self._event_handlers.setdefault(event_type, []).append(handler)

    def off_event(self, event_type: str, handler: Callable) -> None:
        if event_type in self._event_handlers:
            self._event_handlers[event_type].remove(handler)

    async def _ws_listener(self) -> None:
        """Listen for Dograh WebSocket messages."""
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._dispatch_message(msg.json())
                elif msg.type == aiohttp.WSMsgType.BINARY:
                    await self._dispatch_binary(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    log.error("Dograh WebSocket error", extra={"error": self._ws.exception()})
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error("Dograh listener error", extra={"error": str(e)})
        finally:
            self._connected = False

    async def _dispatch_message(self, data: Dict[str, Any]) -> None:
        """Dispatch JSON message to handlers."""
        msg_type = data.get("type") or data.get("event")
        if not msg_type:
            return

        session_id = data.get("session_id") or data.get("sessionId")

        event = DograhEvent(
            event_type=msg_type,
            session_id=session_id or "",
            raw=data,
        )

        # Parse specific message types
        if msg_type in ("audio", "audioData", "media"):
            # Audio from Dograh/Gemini - base64 encoded
            b64_audio = data.get("data") or data.get("audio") or data.get("media", {}).get("payload")
            if b64_audio:
                event.audio_data = base64.b64decode(b64_audio)

        elif msg_type in ("transcript", "transcription", "speechEvent"):
            event.transcript = data.get("transcript") or data.get("text") or ""

        elif msg_type in ("error", "sessionError"):
            event.error = data.get("error") or data.get("message") or "Unknown error"

        elif msg_type in ("sessionStarted", "session_started", "started"):
            event.metadata = data.get("metadata", {})

        elif msg_type in ("sessionEnded", "session_ended", "ended"):
            pass

        # Dispatch to handlers
        for handler in self._event_handlers.get(msg_type, []):
            try:
                await handler(event)
            except Exception as e:
                log.error("Dograh handler error", extra={"event": msg_type, "error": str(e)})

        # Also dispatch by session_id
        if session_id:
            for handler in self._event_handlers.get(f"session:{session_id}", []):
                try:
                    await handler(event)
                except Exception as e:
                    log.error("Dograh session handler error", extra={"session": session_id, "error": str(e)})

    async def _dispatch_binary(self, data: bytes) -> None:
        """Dispatch binary message (raw audio)."""
        # Dograh may send raw audio as binary frames
        # This would be associated with the most recent session
        for handler in self._event_handlers.get("binary_audio", []):
            try:
                await handler(data)
            except Exception as e:
                log.error("Dograh binary handler error", extra={"error": str(e)})

    # ──────────────────────────────────────────
    # Session Management
    # ──────────────────────────────────────────

    async def start_session(
        self,
        call_id: str,
        caller_number: str,
        called_number: str,
        direction: str,
        sample_rate: int = 48000,
    ) -> str:
        """Start a new Dograh/Gemini Live session for a call."""
        session_id = f"sora-{call_id}-{uuid.uuid4().hex[:8]}"

        # Dograh session start message (Gemini Live protocol)
        start_msg = {
            "type": "sessionStart",
            "sessionId": session_id,
            "model": self.model,
            "config": {
                "sampleRate": sample_rate,
                "channels": 1,
                "language": "en-US",
                "voice": "en-US-Neural2-F",
            },
            "metadata": {
                "call_id": call_id,
                "caller": caller_number,
                "called": called_number,
                "direction": direction,
                "source": "sora-voip",
            },
        }

        await self._ws.send_json(start_msg)

        # Store session info
        self._sessions[session_id] = {
            "call_id": call_id,
            "caller": caller_number,
            "called": called_number,
            "direction": direction,
            "sample_rate": sample_rate,
            "started_at": datetime.utcnow(),
            "state": "starting",
        }

        log.info("Dograh session started", extra={"session_id": session_id, "call_id": call_id})
        return session_id

    async def end_session(self, session_id: str) -> None:
        """End a Dograh session."""
        if session_id not in self._sessions:
            return

        end_msg = {
            "type": "sessionEnd",
            "sessionId": session_id,
        }
        await self._ws.send_json(end_msg)

        self._sessions.pop(session_id, None)
        log.info("Dograh session ended", extra={"session_id": session_id})

    async def send_audio(self, session_id: str, pcm_data: bytes) -> bool:
        """Send PCM audio to Dograh/Gemini (base64 encoded)."""
        if session_id not in self._sessions:
            return False

        if not self._connected:
            return False

        try:
            b64_audio = base64.b64encode(pcm_data).decode("ascii")
            msg = {
                "type": "audio",
                "sessionId": session_id,
                "data": b64_audio,
                "config": {
                    "sampleRate": self._sessions[session_id]["sample_rate"],
                    "channels": 1,
                },
            }
            await self._ws.send_json(msg)
            return True
        except Exception as e:
            log.error("Dograh send_audio error", extra={"session_id": session_id, "error": str(e)})
            return False

    async def send_dtmf(self, session_id: str, digit: str) -> bool:
        """Send DTMF to Dograh session as control signal."""
        if session_id not in self._sessions:
            return False

        try:
            msg = {
                "type": "dtmf",
                "sessionId": session_id,
                "digit": digit,
            }
            await self._ws.send_json(msg)
            return True
        except Exception as e:
            log.error("Dograh send_dtmf error", extra={"session_id": session_id, "error": str(e)})
            return False

    async def send_text(self, session_id: str, text: str) -> bool:
        """Send text input to Dograh/Gemini (for text-mode interaction)."""
        if session_id not in self._sessions:
            return False

        try:
            msg = {
                "type": "text",
                "sessionId": session_id,
                "text": text,
            }
            await self._ws.send_json(msg)
            return True
        except Exception as e:
            log.error("Dograh send_text error", extra={"session_id": session_id, "error": str(e)})
            return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session info."""
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions."""
        return [
            {"session_id": sid, **info}
            for sid, info in self._sessions.items()
        ]


async def create_dograh_client(
    ws_url: str,
    api_key: str = "",
    model: str = "gemini-2.0-flash-exp",
) -> DograhClient:
    """Factory function to create and connect Dograh client."""
    client = DograhClient(ws_url, api_key, model)
    await client.connect()
    return client