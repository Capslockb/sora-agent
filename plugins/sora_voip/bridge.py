"""
Sora VOIP Bridge — Asterisk ARI + Dograh + Gemini Live

Replaces Discord transport with Asterisk ARI externalMedia.
Dograh handles Gemini Live WebSocket; we pipe RTP <-> Dograh WS.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import aiohttp
from aiohttp import web

logger = logging.getLogger("sora_voip.bridge")


@dataclass
class VoipConfig:
    """Configuration for VOIP bridge."""
    # Asterisk ARI
    ari_url: str
    ari_user: str
    ari_password: str
    app_name: str = "sora"
    external_media_host: str = "0.0.0.0"
    external_media_port: int = 5000

    # Dograh / Gemini
    dograh_ws_url: str
    dograh_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash-exp"
    gemini_voice: str = "Puck"
    gemini_temperature: float = 0.7

    # HTTP API
    http_host: str = "0.0.0.0"
    http_port: int = 18944


@dataclass
class CallState:
    """Tracks a single active call."""
    call_id: str
    channel_id: str
    ari_app: str
    dograh_ws: Optional[aiohttp.ClientWebSocketResponse] = None
    external_media_port: int = 0
    rtp_task: Optional[asyncio.Task] = None
    dograh_task: Optional[asyncio.Task] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    audio_in_chunks: int = 0
    audio_out_chunks: int = 0
    playback_active: bool = False


class DograhSession:
    """
    Manages WebSocket connection to Dograh (which fronts Gemini Live).
    Protocol matches Gemini Live API with Dograh auth wrapper.
    """

    def __init__(self, config: VoipConfig, call_state: CallState):
        self.config = config
        self.call_state = call_state
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._running = False
        self._send_queue: asyncio.Queue[bytes] = asyncio.Queue()

    async def connect(self) -> bool:
        """Connect to Dograh WebSocket."""
        headers = {}
        if self.config.dograh_api_key:
            headers["Authorization"] = f"Bearer {self.config.dograh_api_key}"

        try:
            session = aiohttp.ClientSession()
            self.ws = await session.ws_connect(
                self.config.dograh_ws_url,
                headers=headers,
                heartbeat=30,
            )
            self._running = True

            # Send session initialization (Gemini Live format)
            init_msg = {
                "setup": {
                    "model": f"models/{self.config.gemini_model}",
                    "generation_config": {
                        "response_modalities": ["AUDIO"],
                        "speech_config": {
                            "voice_config": {
                                "prebuilt_voice_config": {
                                    "voice_name": self.config.gemini_voice
                                }
                            }
                        },
                        "temperature": self.config.gemini_temperature,
                    },
                    "system_instruction": {
                        "parts": [{"text": "You are Sora, a helpful voice assistant."}]
                    },
                }
            }
            await self.ws.send_json(init_msg)
            logger.info(f"[{self.call_state.call_id}] Dograh session initialized")

            # Start receive loop
            self.call_state.dograh_task = asyncio.create_task(self._receive_loop())
            self.call_state.dograh_ws = self.ws

            # Start send loop
            asyncio.create_task(self._send_loop())
            return True

        except Exception as e:
            logger.error(f"[{self.call_state.call_id}] Dograh connect failed: {e}")
            return False

    async def _receive_loop(self):
        """Receive audio from Dograh/Gemini, queue for RTP output."""
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self._handle_gemini_message(data)
                elif msg.type == aiohttp.WSMsgType.BINARY:
                    # Raw PCM audio from Gemini
                    self.call_state.audio_out_chunks += 1
                    await self._send_queue.put(msg.data)
                elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSED):
                    logger.info(f"[{self.call_state.call_id}] Dograh WS closed")
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"[{self.call_state.call_id}] Dograh WS error: {self.ws.exception()}")
                    break
        except Exception as e:
            logger.error(f"[{self.call_state.call_id}] Dograh receive error: {e}")
        finally:
            self._running = False

    async def _handle_gemini_message(self, data: dict):
        """Handle non-audio messages from Gemini (setup complete, turn complete, etc.)."""
        if "setupComplete" in data:
            logger.info(f"[{self.call_state.call_id}] Gemini setup complete")
        elif "serverContent" in data:
            content = data["serverContent"]
            if "modelTurn" in content:
                # Model turn started - could trigger playback start
                self.call_state.playback_active = True
            if "turnComplete" in content:
                # Turn ended - could trigger pause
                self.call_state.playback_active = False

    async def _send_loop(self):
        """Send queued audio to Dograh."""
        while self._running and self.ws and not self.ws.closed:
            try:
                chunk = await asyncio.wait_for(self._send_queue.get(), timeout=0.1)
                await self.ws.send_bytes(chunk)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"[{self.call_state.call_id}] Dograh send error: {e}")
                break

    async def send_audio(self, pcm_data: bytes):
        """Queue PCM audio to send to Dograh/Gemini."""
        if self._running:
            await self._send_queue.put(pcm_data)

    async def close(self):
        """Close Dograh connection."""
        self._running = False
        if self.ws and not self.ws.closed:
            await self.ws.close()


class AriClient:
    """
    Minimal Asterisk ARI client for externalMedia handling.
    Uses aiohttp for REST + WebSocket events.
    """

    def __init__(self, config: VoipConfig):
        self.config = config
        self.base_url = config.ari_url.rstrip("/")
        self.auth = aiohttp.BasicAuth(config.ari_user, config.ari_password)
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._event_handlers: dict[str, list] = {}
        self._running = False
        self._port_counter = config.external_media_port

    async def connect(self) -> bool:
        """Connect to ARI and start event stream."""
        try:
            self.session = aiohttp.ClientSession(auth=self.auth)

            # Subscribe to application events
            ws_url = f"{self.base_url.replace('http', 'ws')}/events?app={self.config.app_name}&subscribeAll=true"
            self.ws = await self.session.ws_connect(ws_url, heartbeat=30)
            self._running = True

            # Start event loop
            asyncio.create_task(self._event_loop())
            logger.info(f"ARI connected to {self.base_url}")
            return True

        except Exception as e:
            logger.error(f"ARI connect failed: {e}")
            return False

    async def _event_loop(self):
        """Process ARI events."""
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    event = json.loads(msg.data)
                    await self._dispatch_event(event)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"ARI WS error: {self.ws.exception()}")
                    break
        except Exception as e:
            logger.error(f"ARI event loop error: {e}")
        finally:
            self._running = False

    def on(self, event_type: str, handler):
        """Register event handler."""
        self._event_handlers.setdefault(event_type, []).append(handler)

    async def _dispatch_event(self, event: dict):
        """Dispatch event to registered handlers."""
        event_type = event.get("type", "")
        for handler in self._event_handlers.get(event_type, []):
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Handler error for {event_type}: {e}")

    def _next_port(self) -> int:
        """Get next available RTP port (even numbers for RTP, odd for RTCP)."""
        port = self._port_counter
        self._port_counter += 2
        return port

    async def start_external_media(self, channel_id: str, call_state: CallState) -> bool:
        """Start externalMedia on a channel to fork RTP to our port."""
        port = self._next_port()
        call_state.external_media_port = port

        # externalMedia expects: host, port, format, transport
        payload = {
            "external_host": self.config.external_media_host,
            "port": port,
            "format": "slin16",  # 16-bit linear PCM, 8kHz
            "transport": "udp",
            "connection_type": "fork",  # fork = copy, not bridge
            "direction": "both",  # send and receive
        }

        try:
            url = f"{self.base_url}/channels/{channel_id}/externalMedia"
            async with self.session.post(url, json=payload) as resp:
                if resp.status == 200:
                    logger.info(f"[{call_state.call_id}] externalMedia started on port {port}")
                    return True
                else:
                    text = await resp.text()
                    logger.error(f"externalMedia failed: {resp.status} {text}")
                    return False
        except Exception as e:
            logger.error(f"externalMedia error: {e}")
            return False

    async def stop_external_media(self, channel_id: str):
        """Stop externalMedia on a channel."""
        try:
            url = f"{self.base_url}/channels/{channel_id}/externalMedia"
            await self.session.delete(url)
        except Exception as e:
            logger.error(f"Stop externalMedia error: {e}")

    async def answer_channel(self, channel_id: str):
        """Answer an incoming call."""
        url = f"{self.base_url}/channels/{channel_id}/answer"
        await self.session.post(url)

    async def hangup_channel(self, channel_id: str):
        """Hang up a channel."""
        url = f"{self.base_url}/channels/{channel_id}/hangup"
        await self.session.post(url)

    async def close(self):
        """Close ARI connection."""
        self._running = False
        if self.ws and not self.ws.closed:
            await self.ws.close()
        if self.session and not self.session.closed:
            await self.session.close()


class RtpHandler:
    """
    Handles raw RTP UDP sockets for externalMedia.
    Receives from Asterisk (caller audio) -> sends to Dograh.
    Receives from Dograh (Gemini audio) -> sends to Asterisk (callee audio).
    """

    def __init__(self, config: VoipConfig, call_state: CallState, dograh_session: DograhSession):
        self.config = config
        self.call_state = call_state
        self.dograh = dograh_session
        self.recv_sock: Optional[asyncio.DatagramTransport] = None
        self.send_sock: Optional[asyncio.DatagramTransport] = None
        self.remote_addr: Optional[tuple] = None
        self._running = False

    async def start(self):
        """Start RTP listener on the externalMedia port."""
        loop = asyncio.get_event_loop()

        # Create UDP socket for receiving from Asterisk
        self.recv_sock, _ = await loop.create_datagram_endpoint(
            lambda: RtpProtocol(self),
            local_addr=("0.0.0.0", self.call_state.external_media_port),
        )
        self._running = True
        logger.info(f"[{self.call_state.call_id}] RTP listening on port {self.call_state.external_media_port}")

    def on_rtp_received(self, data: bytes, addr: tuple):
        """Called when RTP packet received from Asterisk."""
        if not self._running:
            return

        self.remote_addr = addr
        self.call_state.audio_in_chunks += 1

        # Strip RTP header (12 bytes minimum) -> raw PCM
        # Note: externalMedia with format=slin16 sends raw PCM without RTP header
        # If you get RTP, parse: payload = data[12:]
        pcm = data  # Assuming raw slin16 from externalMedia

        # Send to Dograh/Gemini
        asyncio.create_task(self.dograh.send_audio(pcm))

    async def send_to_asterisk(self, pcm_data: bytes):
        """Send PCM audio to Asterisk via externalMedia port."""
        if self.remote_addr and self.send_sock:
            # externalMedia expects raw slin16, no RTP header
            self.send_sock.sendto(pcm_data, self.remote_addr)

    async def stop(self):
        """Stop RTP handling."""
        self._running = False
        if self.recv_sock:
            self.recv_sock.close()
        if self.send_sock:
            self.send_sock.close()


class RtpProtocol(asyncio.DatagramProtocol):
    """asyncio UDP protocol for RTP."""

    def __init__(self, handler: RtpHandler):
        self.handler = handler
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        self.handler.send_sock = transport

    def datagram_received(self, data, addr):
        self.handler.on_rtp_received(data, addr)

    def error_received(self, exc):
        logger.error(f"RTP error: {exc}")


class VoipBridge:
    """
    Main bridge orchestrator.
    Manages ARI connection, call lifecycle, Dograh sessions, RTP.
    """

    def __init__(self, config: VoipConfig):
        self.config = config
        self.ari = AriClient(config)
        self.calls: dict[str, CallState] = {}
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self._running = False

        # Register ARI event handlers
        self.ari.on("StasisStart", self._on_stasis_start)
        self.ari.on("StasisEnd", self._on_stasis_end)
        self.ari.on("ChannelTalkingStarted", self._on_talking_started)
        self.ari.on("ChannelTalkingFinished", self._on_talking_finished)

    async def start(self):
        """Start the bridge."""
        logger.info("Starting Sora VOIP bridge...")

        # Connect to ARI
        if not await self.ari.connect():
            raise RuntimeError("Failed to connect to Asterisk ARI")

        # Start HTTP API
        await self._start_http_api()

        self._running = True
        logger.info(f"VOIP bridge running. HTTP API on {self.config.http_host}:{self.config.http_port}")

    async def _start_http_api(self):
        """Start HTTP control/health API."""
        self.app = web.Application()
        self.app.router.add_get("/health", self._health_handler)
        self.app.router.add_get("/calls", self._calls_handler)
        self.app.router.add_post("/calls/{call_id}/hangup", self._hangup_handler)
        self.app.router.add_post("/control", self._control_handler)

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.config.http_host, self.config.http_port)
        await site.start()

    async def _health_handler(self, request):
        return web.json_response({
            "status": "healthy",
            "bridge": "sora-voip",
            "running": self._running,
            "active_calls": len(self.calls),
            "ari_connected": self.ari._running,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def _calls_handler(self, request):
        calls_data = []
        for call in self.calls.values():
            calls_data.append({
                "call_id": call.call_id,
                "channel_id": call.channel_id,
                "duration_seconds": (datetime.utcnow() - call.started_at).total_seconds(),
                "audio_in_chunks": call.audio_in_chunks,
                "audio_out_chunks": call.audio_out_chunks,
                "playback_active": call.playback_active,
                "external_media_port": call.external_media_port,
            })
        return web.json_response({"calls": calls_data})

    async def _hangup_handler(self, request):
        call_id = request.match_info["call_id"]
        call = self.calls.get(call_id)
        if call:
            await self._cleanup_call(call)
            return web.json_response({"status": "hangup initiated"})
        return web.json_response({"error": "call not found"}, status=404)

    async def _control_handler(self, request):
        data = await request.json()
        action = data.get("action")
        call_id = data.get("call_id")

        if action == "mute" and call_id:
            call = self.calls.get(call_id)
            if call:
                call.playback_active = False
                return web.json_response({"status": "muted"})
        elif action == "unmute" and call_id:
            call = self.calls.get(call_id)
            if call:
                call.playback_active = True
                return web.json_response({"status": "unmuted"})

        return web.json_response({"error": "invalid action"}, status=400)

    async def _on_stasis_start(self, event: dict):
        """New channel entered Stasis app (incoming call)."""
        channel = event.get("channel", {})
        channel_id = channel.get("id")
        call_id = str(uuid.uuid4())[:8]

        logger.info(f"[{call_id}] StasisStart: channel {channel_id}")

        # Create call state
        call = CallState(
            call_id=call_id,
            channel_id=channel_id,
            ari_app=self.config.app_name,
        )
        self.calls[call_id] = call

        # Answer the call
        await self.ari.answer_channel(channel_id)

        # Start externalMedia
        if not await self.ari.start_external_media(channel_id, call):
            await self._cleanup_call(call)
            return

        # Connect to Dograh
        dograh = DograhSession(self.config, call)
        if not await dograh.connect():
            await self._cleanup_call(call)
            return

        # Start RTP handler
        rtp = RtpHandler(self.config, call, dograh)
        await rtp.start()
        call.rtp_task = asyncio.current_task()  # Track for cleanup

    async def _on_stasis_end(self, event: dict):
        """Channel left Stasis app (call ended)."""
        channel_id = event.get("channel", {}).get("id")
        # Find call by channel_id
        call = next((c for c in self.calls.values() if c.channel_id == channel_id), None)
        if call:
            logger.info(f"[{call.call_id}] StasisEnd")
            await self._cleanup_call(call)

    async def _on_talking_started(self, event: dict):
        """Voice activity detected."""
        channel_id = event.get("channel", {}).get("id")
        call = next((c for c in self.calls.values() if c.channel_id == channel_id), None)
        if call:
            call.playback_active = True

    async def _on_talking_finished(self, event: dict):
        """Voice activity ended."""
        channel_id = event.get("channel", {}).get("id")
        call = next((c for c in self.calls.values() if c.channel_id == channel_id), None)
        if call:
            call.playback_active = False

    async def _cleanup_call(self, call: CallState):
        """Clean up call resources."""
        logger.info(f"[{call.call_id}] Cleaning up call")

        # Stop externalMedia
        await self.ari.stop_external_media(call.channel_id)

        # Close Dograh
        if call.dograh_ws:
            dograh = DograhSession(self.config, call)
            dograh.ws = call.dograh_ws
            await dograh.close()

        # Cancel tasks
        if call.rtp_task and not call.rtp_task.done():
            call.rtp_task.cancel()
        if call.dograh_task and not call.dograh_task.done():
            call.dograh_task.cancel()

        # Remove from active calls
        self.calls.pop(call.call_id, None)

    async def stop(self):
        """Stop the bridge."""
        logger.info("Stopping VOIP bridge...")
        self._running = False

        # Hangup all calls
        for call in list(self.calls.values()):
            await self._cleanup_call(call)

        # Stop HTTP API
        if self.runner:
            await self.runner.cleanup()

        # Close ARI
        await self.ari.close()

        logger.info("VOIP bridge stopped")


# --- CLI entry point ---

async def main():
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Sora VOIP Bridge")
    parser.add_argument("--config", type=Path, help="Config file (YAML)")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Load config
    if args.config:
        import yaml
        with open(args.config) as f:
            cfg_dict = yaml.safe_load(f)
        config = VoipConfig(**cfg_dict.get("voip", {}))
    else:
        # From environment
        config = VoipConfig(
            ari_url=os.getenv("SORA_ARI_URL", "http://localhost:8088/ari"),
            ari_user=os.getenv("SORA_ARI_USER", "sora"),
            ari_password=os.getenv("SORA_ARI_PASSWORD", ""),
            app_name=os.getenv("SORA_ARI_APP", "sora"),
            external_media_host=os.getenv("SORA_EXTERNAL_MEDIA_HOST", "0.0.0.0"),
            external_media_port=int(os.getenv("SORA_EXTERNAL_MEDIA_PORT", "5000")),
            dograh_ws_url=os.getenv("SORA_DOGRAH_WS_URL", ""),
            dograh_api_key=os.getenv("SORA_DOGRAH_API_KEY", ""),
            gemini_model=os.getenv("SORA_GEMINI_MODEL", "gemini-2.0-flash-exp"),
            gemini_voice=os.getenv("SORA_GEMINI_VOICE", "Puck"),
            gemini_temperature=float(os.getenv("SORA_GEMINI_TEMPERATURE", "0.7")),
            http_host=os.getenv("SORA_HTTP_HOST", "0.0.0.0"),
            http_port=int(os.getenv("SORA_HTTP_PORT", "18944")),
        )

    if not config.dograh_ws_url:
        logger.error("DOGRAH_WS_URL is required (set SORA_DOGRAH_WS_URL)")
        return 1

    bridge = VoipBridge(config)
    try:
        await bridge.start()
        # Run forever
        while bridge._running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await bridge.stop()
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))