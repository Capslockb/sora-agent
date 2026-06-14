"""
Sora VOIP Bridge Core
=====================
Orchestrates Asterisk ARI ↔ RTP ↔ Dograh/Gemini Live for phone calls.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

import aiohttp

from .ari_client import AriClient, AriEvent
from .rtp_handler import RtpHandler, RtpStream
from .dograh_client import DograhClient, DograhEvent

log = logging.getLogger("sora.voip.bridge")


# ──────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────

@dataclass
class ActiveCall:
    """Represents an active phone call bridged to Dograh/Gemini."""
    call_id: str
    channel_id: str
    caller_number: str
    called_number: str
    direction: str  # "inbound" | "outbound"
    state: str  # "ringing" | "answered" | "bridged" | "ended"
    started_at: datetime
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    rtp_stream: Optional[RtpStream] = None
    dograh_session_id: Optional[str] = None
    recording_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BridgeConfig:
    """Runtime configuration for the bridge."""
    asterisk_ari_url: str
    asterisk_username: str
    asterisk_password: str
    asterisk_app_name: str
    dograh_ws_url: str
    dograh_api_key: str
    gemini_model: str
    sample_rate: int
    rtp_port_range: str
    auto_answer: bool
    record_calls: bool
    recording_dir: str


# ──────────────────────────────────────────────
# Main Bridge Class
# ──────────────────────────────────────────────

class VoipBridge:
    """
    Main VOIP bridge orchestrating:
    - Asterisk ARI for call control (SIP signaling)
    - RTP media streams (audio)
    - Dograh/Gemini Live for AI conversation
    """

    def __init__(
        self,
        ari_client: AriClient,
        rtp_handler: RtpHandler,
        dograh_client: DograhClient,
        config: Dict[str, Any],
    ):
        self.ari = ari_client
        self.rtp = rtp_handler
        self.dograh = dograh_client
        self.config = BridgeConfig(**config)

        self._calls: Dict[str, ActiveCall] = {}
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._event_handlers: Dict[str, List[Callable]] = {}

        # Bind event handlers
        self.ari.on_event("StasisStart", self._on_stasis_start)
        self.ari.on_event("StasisEnd", self._on_stasis_end)
        self.ari.on_event("ChannelStateChange", self._on_channel_state_change)
        self.ari.on_event("ChannelTalkingStarted", self._on_talking_started)
        self.ari.on_event("ChannelTalkingFinished", self._on_talking_finished)
        self.ari.on_event("ChannelDtmfReceived", self._on_dtmf)

        self.dograh.on_event("session_started", self._on_dograh_session_started)
        self.dograh.on_event("session_ended", self._on_dograh_session_ended)
        self.dograh.on_event("audio_received", self._on_dograh_audio)
        self.dograh.on_event("transcript", self._on_dograh_transcript)
        self.dograh.on_event("error", self._on_dograh_error)

    # ──────────────────────────────────────────
    # Lifecycle
    # ──────────────────────────────────────────

    async def start(self) -> None:
        """Start the bridge: connect ARI, Dograh, start RTP handler."""
        if self._running:
            return

        log.info("Starting Sora VOIP bridge")

        # Connect to Asterisk ARI
        await self.ari.connect()
        log.info("ARI connected")

        # Register ARI application
        await self.ari.register_app(self.config.asterisk_app_name)
        log.info("ARI app registered", extra={"app": self.config.asterisk_app_name})

        # Connect to Dograh/Gemini
        await self.dograh.connect()
        log.info("Dograh connected")

        # Start RTP handler
        await self.rtp.start()
        log.info("RTP handler started")

        self._running = True

        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._ari_event_loop()),
            asyncio.create_task(self._dograh_event_loop()),
            asyncio.create_task(self._call_monitor_loop()),
        ]

        log.info("Sora VOIP bridge started successfully")

    async def stop(self) -> None:
        """Stop the bridge gracefully."""
        if not self._running:
            return

        log.info("Stopping Sora VOIP bridge")
        self._running = False

        # Hang up all active calls
        for call in list(self._calls.values()):
            await self.hangup(call.channel_id)

        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

        # Disconnect clients
        await self.dograh.disconnect()
        await self.ari.disconnect()
        await self.rtp.stop()

        self._calls.clear()
        self._tasks.clear()
        log.info("Sora VOIP bridge stopped")

    async def reload_config(self, config: Dict[str, Any]) -> None:
        """Hot-reload configuration."""
        self.config = BridgeConfig(**config)
        # Reconfigure components
        await self.rtp.reconfigure(port_range=self.config.rtp_port_range)
        await self.dograh.reconfigure(
            ws_url=self.config.dograh_ws_url,
            api_key=self.config.dograh_api_key,
            model=self.config.gemini_model,
        )
        log.info("VOIP bridge config reloaded")

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    async def sip_register(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register SIP endpoint (via ARI endpoint registration)."""
        # This would typically be done via Asterisk config (pjsip.conf)
        # but we can trigger a reload or use AMI for dynamic registration
        return {
            "status": "ok",
            "message": "SIP registration managed via Asterisk config (pjsip.conf). Use 'asterisk -rx \"pjsip show registrations\"' to verify.",
            "note": "Dynamic SIP registration via ARI not directly supported; configure endpoints in pjsip.conf",
        }

    async def sip_unregister(self) -> Dict[str, Any]:
        """Unregister SIP endpoint."""
        return {"status": "ok", "message": "SIP unregistration managed via Asterisk config"}

    async def sip_status(self) -> Dict[str, Any]:
        """Get SIP registration status (via ARI endpoint query)."""
        try:
            endpoints = await self.ari.get_endpoints()
            return {
                "status": "ok",
                "endpoints": endpoints,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def ari_connect(self, app_name: Optional[str] = None) -> Dict[str, Any]:
        """Connect/register ARI application."""
        name = app_name or self.config.asterisk_app_name
        await self.ari.register_app(name)
        return {"status": "ok", "app": name}

    async def ari_disconnect(self) -> Dict[str, Any]:
        """Disconnect ARI application."""
        await self.ari.unregister_app(self.config.asterisk_app_name)
        return {"status": "ok"}

    def ari_status(self) -> Dict[str, Any]:
        """Get ARI connection status."""
        return {
            "status": "ok",
            "connected": self.ari.is_connected(),
            "app": self.config.asterisk_app_name,
            "url": self.config.asterisk_ari_url,
        }

    async def ari_list_apps(self) -> Dict[str, Any]:
        """List registered ARI applications."""
        apps = await self.ari.list_apps()
        return {"status": "ok", "apps": apps}

    async def originate_call(
        self,
        number: str,
        caller_id: Optional[str] = None,
        auto_answer: Optional[bool] = None,
        record: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Originate an outbound call and bridge to Dograh."""
        call_id = str(uuid.uuid4())[:8]
        channel_id = f"Sora/{call_id}"

        # Prepare originate parameters
        originate_params = {
            "endpoint": f"PJSIP/{number}",
            "app": self.config.asterisk_app_name,
            "appArgs": f"outbound,{call_id}",
            "callerId": caller_id or "Sora",
            "timeout": 30,
        }

        if auto_answer is not None:
            originate_params["autoAnswer"] = auto_answer
        elif self.config.auto_answer:
            originate_params["autoAnswer"] = True

        try:
            # Originate call via ARI
            channel = await self.ari.originate(**originate_params)
            if not channel:
                return {"status": "error", "error": "Failed to originate call", "call_id": call_id}

            actual_channel_id = channel.get("id")
            log.info("Call originated", extra={"call_id": call_id, "channel": actual_channel_id})

            # Create call record
            call = ActiveCall(
                call_id=call_id,
                channel_id=actual_channel_id,
                caller_number=caller_id or "Sora",
                called_number=number,
                direction="outbound",
                state="ringing",
                started_at=datetime.utcnow(),
            )
            self._calls[call_id] = call

            # Start recording if requested
            if record is True or (record is None and self.config.record_calls):
                await self._start_recording(call)

            return {
                "status": "ok",
                "call_id": call_id,
                "channel_id": actual_channel_id,
                "number": number,
                "state": "ringing",
            }

        except Exception as e:
            log.error("Originate failed", extra={"error": str(e)})
            return {"error": str(e), "call_id": call_id}

    async def hangup(self, channel_id: Optional[str] = None, all_calls: bool = False) -> Dict[str, Any]:
        """Hang up call(s)."""
        results = []

        if all_calls:
            for call in list(self._calls.values()):
                results.append(await self._hangup_call(call))
        elif channel_id:
            call = self._find_call_by_channel(channel_id)
            if call:
                results.append(await self._hangup_call(call))
            else:
                return {"status": "error", "error": f"Channel not found: {channel_id}"}
        else:
            return {"status": "error", "error": "channel_id or all_calls required"}

        return {"status": "ok", "results": results}

    async def _hangup_call(self, call: ActiveCall) -> Dict[str, Any]:
        """Hang up a single call and cleanup."""
        try:
            # Hang up via ARI
            await self.ari.hangup(call.channel_id)

            # Stop RTP stream
            if call.rtp_stream:
                await self.rtp.stop_stream(call.rtp_stream)
                call.rtp_stream = None

            # End Dograh session
            if call.dograh_session_id:
                await self.dograh.end_session(call.dograh_session_id)
                call.dograh_session_id = None

            # Stop recording
            if call.recording_path:
                await self._stop_recording(call)

            call.state = "ended"
            call.ended_at = datetime.utcnow()

            # Remove from active calls
            self._calls.pop(call.call_id, None)

            log.info("Call ended", extra={"call_id": call.call_id, "duration": self._call_duration(call)})
            return {"status": "ok", "call_id": call.call_id}

        except Exception as e:
            log.error("Hangup failed", extra={"call_id": call.call_id, "error": str(e)})
            return {"status": "error", "error": str(e), "call_id": call.call_id}

    def get_status(self, detailed: bool = False) -> Dict[str, Any]:
        """Get bridge status."""
        status = {
            "running": self._running,
            "ari": self.ari_status(),
            "dograh": self.dograh.get_status(),
            "rtp": self.rtp.get_status(),
            "active_calls": len(self._calls),
            "calls": [],
        }

        if detailed:
            for call in self._calls.values():
                status["calls"].append({
                    "call_id": call.call_id,
                    "channel_id": call.channel_id,
                    "caller": call.caller_number,
                    "called": call.called_number,
                    "direction": call.direction,
                    "state": call.state,
                    "duration": self._call_duration(call).seconds if call.answered_at else 0,
                    "recording": call.recording_path,
                    "dograh_session": call.dograh_session_id,
                })

        return status

    # ──────────────────────────────────────────
    # ARI Event Handlers
    # ──────────────────────────────────────────

    async def _on_stasis_start(self, event: AriEvent) -> None:
        """Channel entered Stasis app - inbound call or originate answered."""
        channel = event.channel
        channel_id = channel["id"]
        args = event.args or []

        # Parse app args: direction,call_id
        direction = args[0] if args else "inbound"
        call_id = args[1] if len(args) > 1 else str(uuid.uuid4())[:8]

        # Check if we already track this call (outbound)
        existing_call = self._find_call_by_channel(channel_id)
        if existing_call:
            existing_call.state = "answered"
            existing_call.answered_at = datetime.utcnow()
            await self._bridge_call(existing_call)
            return

        # New inbound call
        caller = channel.get("caller", {}).get("number", "unknown")
        called = channel.get("connected", {}).get("number", "unknown")

        call = ActiveCall(
            call_id=call_id,
            channel_id=channel_id,
            caller_number=caller,
            called_number=called,
            direction=direction,
            state="answered",
            started_at=datetime.utcnow(),
            answered_at=datetime.utcnow(),
        )
        self._calls[call_id] = call

        log.info("Call answered", extra={"call_id": call_id, "channel": channel_id, "direction": direction})

        # Auto-answer if configured
        if self.config.auto_answer and direction == "inbound":
            await self.ari.answer(channel_id)

        # Start recording if configured
        if self.config.record_calls:
            await self._start_recording(call)

        # Bridge to Dograh
        await self._bridge_call(call)

    async def _on_stasis_end(self, event: AriEvent) -> None:
        """Channel left Stasis app - call ended."""
        channel_id = event.channel["id"]
        call = self._find_call_by_channel(channel_id)
        if call:
            await self._hangup_call(call)

    async def _on_channel_state_change(self, event: AriEvent) -> None:
        """Channel state changed."""
        channel = event.channel
        state = channel.get("state")
        channel_id = channel["id"]
        call = self._find_call_by_channel(channel_id)
        if call:
            call.state = state.lower()
            log.debug("Channel state change", extra={"call_id": call.call_id, "state": state})

    async def _on_talking_started(self, event: AriEvent) -> None:
        """Channel started talking - start sending audio to Dograh."""
        channel_id = event.channel["id"]
        call = self._find_call_by_channel(channel_id)
        if call and call.rtp_stream:
            call.rtp_stream.active = True
            log.debug("Talking started", extra={"call_id": call.call_id})

    async def _on_talking_finished(self, event: AriEvent) -> None:
        """Channel stopped talking."""
        channel_id = event.channel["id"]
        call = self._find_call_by_channel(channel_id)
        if call and call.rtp_stream:
            call.rtp_stream.active = False
            log.debug("Talking finished", extra={"call_id": call.call_id})

    async def _on_dtmf(self, event: AriEvent) -> None:
        """DTMF received - forward to Dograh as control signal."""
        channel_id = event.channel["id"]
        digit = event.digit
        call = self._find_call_by_channel(channel_id)
        if call and call.dograh_session_id:
            await self.dograh.send_dtmf(call.dograh_session_id, digit)
            log.debug("DTMF forwarded", extra={"call_id": call.call_id, "digit": digit})

    # ──────────────────────────────────────────
    # Dograh Event Handlers
    # ──────────────────────────────────────────

    async def _on_dograh_session_started(self, event: DograhEvent) -> None:
        """Dograh session established."""
        session_id = event.session_id
        call_id = event.metadata.get("call_id")
        call = self._calls.get(call_id)
        if call:
            call.dograh_session_id = session_id
            log.info("Dograh session started", extra={"call_id": call_id, "session_id": session_id})

    async def _on_dograh_session_ended(self, event: DograhEvent) -> None:
        """Dograh session ended."""
        session_id = event.session_id
        call = self._find_call_by_dograh_session(session_id)
        if call:
            call.dograh_session_id = None
            log.info("Dograh session ended", extra={"call_id": call.call_id})

    async def _on_dograh_audio(self, event: DograhEvent) -> None:
        """Audio received from Dograh/Gemini - play to caller via RTP."""
        session_id = event.session_id
        audio_data = event.audio_data  # base64 encoded PCM
        call = self._find_call_by_dograh_session(session_id)
        if call and call.rtp_stream:
            # Decode base64 PCM and send via RTP
            pcm = base64.b64decode(audio_data)
            await self.rtp.send_audio(call.rtp_stream, pcm)

    async def _on_dograh_transcript(self, event: DograhEvent) -> None:
        """Transcript from Dograh/Gemini."""
        session_id = event.session_id
        transcript = event.transcript
        call = self._find_call_by_dograh_session(session_id)
        if call:
            log.info("Transcript", extra={"call_id": call.call_id, "text": transcript})
            self.emit("transcript", {"call_id": call.call_id, "text": transcript, "timestamp": datetime.utcnow().isoformat()})

    async def _on_dograh_error(self, event: DograhEvent) -> None:
        """Dograh error."""
        log.error("Dograh error", extra={"error": event.error, "session_id": event.session_id})

    # ──────────────────────────────────────────
    # Call Bridging Logic
    # ──────────────────────────────────────────

    async def _bridge_call(self, call: ActiveCall) -> None:
        """Bridge a call to Dograh/Gemini via RTP."""
        try:
            # Allocate RTP port
            rtp_stream = await self.rtp.create_stream(
                call_id=call.call_id,
                sample_rate=self.config.sample_rate,
            )
            call.rtp_stream = rtp_stream

            # Start RTP stream (will handle Asterisk externalMedia or snoopChannel)
            await self.rtp.start_stream(rtp_stream, call.channel_id, self.ari)

            # Start Dograh session
            session_id = await self.dograh.start_session(
                call_id=call.call_id,
                caller_number=call.caller_number,
                called_number=call.called_number,
                direction=call.direction,
                sample_rate=self.config.sample_rate,
            )
            call.dograh_session_id = session_id

            call.state = "bridged"
            log.info("Call bridged to Dograh", extra={"call_id": call.call_id, "session_id": session_id})

        except Exception as e:
            log.error("Bridge failed", extra={"call_id": call.call_id, "error": str(e)})
            await self._hangup_call(call)

    # ──────────────────────────────────────────
    # Recording
    # ──────────────────────────────────────────

    async def _start_recording(self, call: ActiveCall) -> None:
        """Start call recording via ARI."""
        recording_dir = Path(self.config.recording_dir).expanduser()
        recording_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{call.call_id}_{call.caller_number}_{call.called_number}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.wav"
        path = recording_dir / filename

        try:
            await self.ari.record(call.channel_id, str(path), format="wav", mix=True)
            call.recording_path = str(path)
            log.info("Recording started", extra={"call_id": call.call_id, "path": str(path)})
        except Exception as e:
            log.warning("Failed to start recording", extra={"call_id": call.call_id, "error": str(e)})

    async def _stop_recording(self, call: ActiveCall) -> None:
        """Stop call recording."""
        if call.recording_path:
            try:
                await self.ari.stop_recording(call.channel_id, call.recording_path)
                log.info("Recording stopped", extra={"call_id": call.call_id, "path": call.recording_path})
            except Exception as e:
                log.warning("Failed to stop recording", extra={"call_id": call.call_id, "error": str(e)})

    # ──────────────────────────────────────────
    # Background Loops
    # ──────────────────────────────────────────

    async def _ari_event_loop(self) -> None:
        """Process ARI events."""
        while self._running:
            try:
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("ARI event loop error", extra={"error": str(e)})

    async def _dograh_event_loop(self) -> None:
        """Process Dograh events."""
        while self._running:
            try:
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("Dograh event loop error", extra={"error": str(e)})

    async def _call_monitor_loop(self) -> None:
        """Monitor active calls for timeouts, etc."""
        while self._running:
            try:
                await asyncio.sleep(10)
                # Check for stale calls, timeouts, etc.
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("Call monitor error", extra={"error": str(e)})

    # ──────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────

    def _find_call_by_channel(self, channel_id: str) -> Optional[ActiveCall]:
        for call in self._calls.values():
            if call.channel_id == channel_id:
                return call
        return None

    def _find_call_by_dograh_session(self, session_id: str) -> Optional[ActiveCall]:
        for call in self._calls.values():
            if call.dograh_session_id == session_id:
                return call
        return None

    def _call_duration(self, call: ActiveCall) -> datetime:
        end = call.ended_at or datetime.utcnow()
        return end - call.started_at

    # Event emitter for external consumers
    def emit(self, event: str, data: Any) -> None:
        for handler in self._event_handlers.get(event, []):
            try:
                handler(data)
            except Exception as e:
                log.error("Event handler error", extra={"event": event, "error": str(e)})

    def on(self, event: str, handler: Callable) -> None:
        self._event_handlers.setdefault(event, []).append(handler)

    def off(self, event: str, handler: Callable) -> None:
        if event in self._event_handlers:
            self._event_handlers[event].remove(handler)