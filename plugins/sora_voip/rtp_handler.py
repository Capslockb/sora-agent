"""
RTP Media Handler
=================
Handles RTP audio streams between Asterisk and Dograh/Gemini.
Uses aiortc for RTP or raw UDP sockets for lower-level control.
"""

from __future__ import annotations

import asyncio
import logging
import socket
import struct
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

log = logging.getLogger("sora.voip.rtp")


@dataclass
class RtpStream:
    """Represents an active RTP stream."""
    stream_id: str
    call_id: str
    local_port: int
    remote_host: str = ""
    remote_port: int = 0
    sample_rate: int = 48000
    channels: int = 1
    active: bool = False
    _socket: Optional[socket.socket] = None
    _recv_task: Optional[asyncio.Task] = None
    _queue: asyncio.Queue = field(default_factory=asyncio.Queue)

    # Statistics
    packets_sent: int = 0
    packets_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0


class RtpHandler:
    """
    Manages RTP streams for Asterisk externalMedia/snoopChannel.
    Allocates UDP ports, handles encoding/decoding, bridges to Dograh.
    """

    def __init__(
        self,
        port_range: str = "10000-20000",
        sample_rate: int = 48000,
        local_host: str = "0.0.0.0",
    ):
        self.port_range = port_range
        self.sample_rate = sample_rate
        self.local_host = local_host

        # Parse port range
        start, end = port_range.split("-")
        self.port_start = int(start)
        self.port_end = int(end)

        self._streams: Dict[str, RtpStream] = {}
        self._used_ports: set = set()
        self._running = False
        self._external_media_host: Optional[str] = None

    async def start(self) -> None:
        """Start RTP handler."""
        self._running = True
        # Determine external media host (for Asterisk to connect to)
        self._external_media_host = await self._get_external_ip()
        log.info("RTP handler started", extra={"host": self._external_media_host, "port_range": self.port_range})

    async def stop(self) -> None:
        """Stop all streams and handler."""
        self._running = False
        for stream in list(self._streams.values()):
            await self.stop_stream(stream)
        self._streams.clear()
        log.info("RTP handler stopped")

    async def reconfigure(self, port_range: str = None, sample_rate: int = None) -> None:
        """Hot-reconfigure handler."""
        if port_range:
            start, end = port_range.split("-")
            self.port_start = int(start)
            self.port_end = int(end)
            self.port_range = port_range
        if sample_rate:
            self.sample_rate = sample_rate
        log.info("RTP handler reconfigured", extra={"port_range": self.port_range, "sample_rate": self.sample_rate})

    def get_status(self) -> Dict[str, Any]:
        """Get handler status."""
        return {
            "running": self._running,
            "port_range": self.port_range,
            "sample_rate": self.sample_rate,
            "active_streams": len(self._streams),
            "streams": {
                sid: {
                    "call_id": s.call_id,
                    "local_port": s.local_port,
                    "remote": f"{s.remote_host}:{s.remote_port}" if s.remote_host else "unknown",
                    "active": s.active,
                    "packets_sent": s.packets_sent,
                    "packets_received": s.packets_received,
                }
                for sid, s in self._streams.items()
            },
        }

    # ──────────────────────────────────────────
    # Stream Management
    # ──────────────────────────────────────────

    def _allocate_port(self) -> int:
        """Allocate next available UDP port."""
        for port in range(self.port_start, self.port_end + 1):
            if port not in self._used_ports:
                self._used_ports.add(port)
                return port
        raise RuntimeError(f"No available ports in range {self.port_range}")

    def _release_port(self, port: int) -> None:
        """Release UDP port."""
        self._used_ports.discard(port)

    async def create_stream(
        self,
        call_id: str,
        sample_rate: int = None,
        channels: int = 1,
    ) -> RtpStream:
        """Create new RTP stream for a call."""
        stream_id = str(uuid.uuid4())[:8]
        port = self._allocate_port()

        stream = RtpStream(
            stream_id=stream_id,
            call_id=call_id,
            local_port=port,
            sample_rate=sample_rate or self.sample_rate,
            channels=channels,
        )

        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        sock.bind((self.local_host, port))

        stream._socket = sock

        self._streams[stream_id] = stream
        log.debug("RTP stream created", extra={"stream_id": stream_id, "port": port, "call_id": call_id})

        return stream

    async def start_stream(
        self,
        stream: RtpStream,
        channel_id: str,
        ari_client: Any,  # AriClient
    ) -> None:
        """Start RTP stream via Asterisk externalMedia."""
        if not self._external_media_host:
            raise RuntimeError("External media host not determined")

        try:
            # Use externalMedia for bidirectional audio
            await ari_client.external_media(
                channel_id=channel_id,
                host=self._external_media_host,
                port=stream.local_port,
                format="slin48",  # 48kHz signed linear
                direction="both",
            )

            # Start receive task
            stream.active = True
            stream._recv_task = asyncio.create_task(self._recv_loop(stream))

            log.info("RTP stream started via externalMedia", extra={
                "stream_id": stream.stream_id,
                "channel_id": channel_id,
                "host": self._external_media_host,
                "port": stream.local_port,
            })

        except Exception as e:
            log.error("Failed to start RTP stream", extra={"stream_id": stream.stream_id, "error": str(e)})
            raise

    async def stop_stream(self, stream: RtpStream) -> None:
        """Stop RTP stream and cleanup."""
        stream.active = False

        if stream._recv_task:
            stream._recv_task.cancel()
            try:
                await stream._recv_task
            except asyncio.CancelledError:
                raise NotImplementedError("TODO")

        if stream._socket:
            stream._socket.close()
            stream._socket = None

        self._release_port(stream.local_port)
        self._streams.pop(stream.stream_id, None)

        log.debug("RTP stream stopped", extra={"stream_id": stream.stream_id})

    # ──────────────────────────────────────────
    # Audio I/O
    # ──────────────────────────────────────────

    async def send_audio(self, stream: RtpStream, pcm_data: bytes) -> bool:
        """Send PCM audio to remote endpoint via RTP."""
        if not stream.active or not stream._socket or not stream.remote_host:
            return False

        try:
            # Simple RTP header (version=2, payload_type=0 for PCMU, sequence, timestamp, ssrc)
            # For SLIN48, we'd use dynamic payload type, but Asterisk handles negotiation
            # Here we send raw PCM frames; Asterisk expects RTP packets
            rtp_packets = self._pcm_to_rtp(pcm_data, stream)
            for packet in rtp_packets:
                stream._socket.sendto(packet, (stream.remote_host, stream.remote_port))
                stream.packets_sent += 1
                stream.bytes_sent += len(packet)
            return True
        except Exception as e:
            log.error("RTP send error", extra={"stream_id": stream.stream_id, "error": str(e)})
            return False

    def _pcm_to_rtp(self, pcm: bytes, stream: RtpStream) -> List[bytes]:
        """Wrap PCM data in RTP packets (160 samples per 20ms @ 48kHz = 960 bytes per channel)."""
        # RTP packetization for 48kHz mono: 20ms frames = 960 samples = 1920 bytes (16-bit)
        frame_size = 1920  # 48000 * 0.02 * 2 bytes
        packets = []

        for i in range(0, len(pcm), frame_size):
            frame = pcm[i:i + frame_size]
            if len(frame) < frame_size:
                # Pad last frame
                frame = frame + b"\x00" * (frame_size - len(frame))

            # RTP header (minimal)
            # V=2, P=0, X=0, CC=0, M=1 (last frame), PT=dynamic (96-127), seq, ts, ssrc
            sequence = stream.packets_sent & 0xFFFF
            timestamp = int((stream.packets_sent * 960) % 0xFFFFFFFF)  # 960 samples per packet
            ssrc = hash(stream.stream_id) & 0xFFFFFFFF

            header = struct.pack("!BBHII", 0x80, 96, sequence, timestamp, ssrc)
            packets.append(header + frame)

        return packets

    async def _recv_loop(self, stream: RtpStream) -> None:
        """Receive RTP packets from Asterisk."""
        loop = asyncio.get_event_loop()
        sock = stream._socket

        while stream.active:
            try:
                data, addr = await loop.sock_recvfrom(sock, 4096)
                if not stream.remote_host:
                    stream.remote_host, stream.remote_port = addr
                    log.debug("RTP remote discovered", extra={"stream_id": stream.stream_id, "remote": addr})

                # Parse RTP packet, extract PCM
                pcm = self._rtp_to_pcm(data)
                if pcm:
                    stream.packets_received += 1
                    stream.bytes_received += len(data)
                    # Put in queue for Dograh consumer
                    await stream._queue.put(pcm)

            except asyncio.CancelledError:
                break
            except Exception as e:
                if stream.active:
                    log.error("RTP recv error", extra={"stream_id": stream.stream_id, "error": str(e)})

    def _rtp_to_pcm(self, rtp_packet: bytes) -> bytes:
        """Extract PCM from RTP packet (skip 12-byte header + extensions)."""
        if len(rtp_packet) < 12:
            return b""

        # Parse RTP header
        # byte 0: V=2, P, X, CC
        # byte 1: M, PT
        # bytes 2-3: sequence
        # bytes 4-7: timestamp
        # bytes 8-11: ssrc
        # CSRC list (CC * 4 bytes)
        # Extension header (if X=1)

        header = rtp_packet[:12]
        version = (header[0] >> 6) & 0x3
        padding = (header[0] >> 5) & 0x1
        extension = (header[0] >> 4) & 0x1
        cc = header[0] & 0xF
        marker = (header[1] >> 7) & 0x1
        payload_type = header[1] & 0x7F

        header_len = 12 + cc * 4

        if extension:
            # Extension header: 4 bytes (profile, length) + variable
            if len(rtp_packet) >= header_len + 4:
                ext_len = struct.unpack("!H", rtp_packet[header_len + 2:header_len + 4])[0]
                header_len += 4 + ext_len * 4

        payload = rtp_packet[header_len:]

        if padding and payload:
            pad_len = payload[-1]
            payload = payload[:-pad_len]

        # For SLIN48, payload is raw PCM 16-bit little-endian
        return payload

    async def receive_audio(self, stream: RtpStream) -> Optional[bytes]:
        """Get next PCM frame from queue (for sending to Dograh)."""
        try:
            return await asyncio.wait_for(stream._queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            return None

    # ──────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────

    async def _get_external_ip(self) -> str:
        """Get external IP for Asterisk to connect to."""
        try:
            # Try to detect public IP
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.ipify.org", timeout=5) as resp:
                    return await resp.text()
        except Exception:
            raise NotImplementedError("TODO")

        # Fallback: get local IP
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"


# Import aiohttp for external IP detection
import aiohttp
