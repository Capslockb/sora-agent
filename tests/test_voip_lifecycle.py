"""
Lifecycle regression tests for sora_voip (issue #3).

Commit f62d06f replaced intentional no-op / cancellation / fallback branches
with `raise NotImplementedError("TODO")`. These tests pin the restored
semantics so it cannot regress again.

Run:  python -m pytest tests/test_voip_lifecycle.py -v
(no pytest-asyncio required — async paths are driven with asyncio.run)
"""

import asyncio
import os
import socket
import sys
from types import SimpleNamespace
from unittest import mock

import pytest

from plugins.sora_voip.ari_client import AriClient
from plugins.sora_voip.dograh_client import DograhClient
from plugins.sora_voip.rtp_handler import RtpHandler, RtpStream
from plugins.sora_voip import _load_config


def run(coro):
    return asyncio.run(coro)


# ──────────────────────────────────────────────
# 1. disconnect() completes after task cancellation
# ──────────────────────────────────────────────

async def _hang_forever():
    await asyncio.Event().wait()


def test_ari_disconnect_after_cancellation():
    async def scenario():
        client = AriClient("http://localhost:8088", "u", "p", "app")
        client._ws_task = asyncio.create_task(_hang_forever())
        # no _ws / _session: cleanup path only
        await client.disconnect()  # must not raise
    run(scenario())


def test_dograh_disconnect_after_cancellation():
    async def scenario():
        client = DograhClient("ws://localhost/ws")
        client._ws_task = asyncio.create_task(_hang_forever())
        await client.disconnect()  # must not raise
    run(scenario())


# ──────────────────────────────────────────────
# 2. RTP stop_stream() completes cleanup after cancellation
# ──────────────────────────────────────────────

def test_rtp_stop_stream_after_cancellation():
    async def scenario():
        handler = RtpHandler(port_range="10000-10010")
        stream = RtpStream(stream_id="t1", call_id="c1", local_port=10000)
        handler._used_ports.add(10000)
        handler._streams["t1"] = stream
        stream.active = True
        stream._recv_task = asyncio.create_task(_hang_forever())
        await handler.stop_stream(stream)  # must not raise
        assert "t1" not in handler._streams
        assert 10000 not in handler._used_ports
    run(scenario())


# ──────────────────────────────────────────────
# 3. Dograh session-end messages reach handlers
# ──────────────────────────────────────────────

def test_dograh_session_end_dispatches():
    async def scenario():
        client = DograhClient("ws://localhost/ws")
        received = []

        async def handler(event):
            received.append(event)

        for msg_type in ("sessionEnded", "session_ended", "ended"):
            client.on_event(msg_type, handler)

        client._sessions["s1"] = {"call_id": "c1"}
        await client._dispatch_message({"type": "sessionEnded", "sessionId": "s1"})

        assert len(received) == 1
        assert received[0].event_type == "sessionEnded"
        assert "s1" not in client._sessions  # session cleaned up
    run(scenario())


# ──────────────────────────────────────────────
# 4. Broken optional config still permits env fallback
# ──────────────────────────────────────────────

def test_broken_optional_config_falls_back_to_env(monkeypatch=None):
    class BrokenConfig:
        def get(self, *a, **k):
            raise RuntimeError("config store corrupted")

    ctx = SimpleNamespace(config=BrokenConfig(), hermes_config=None)

    os.environ["DOGRAH_WS_URL"] = "wss://env-fallback/ws"
    try:
        config = _load_config(ctx)  # must not raise
    finally:
        del os.environ["DOGRAH_WS_URL"]

    assert config["dograh_ws_url"] == "wss://env-fallback/ws"
    assert config["asterisk_ari_url"] == "http://localhost:8088/ari"  # defaults intact


# ──────────────────────────────────────────────
# 5. Public-IP lookup failure reaches local fallback
# ──────────────────────────────────────────────

def test_external_ip_falls_back_to_local():
    async def scenario():
        handler = RtpHandler()
        with mock.patch("plugins.sora_voip.rtp_handler.aiohttp.ClientSession") as m:
            m.side_effect = OSError("no network")
            ip = await handler._get_external_ip()
        # Should be a local IP or loopback — never NotImplementedError
        assert ip and isinstance(ip, str)
        socket.inet_aton(ip)
    run(scenario())


# ──────────────────────────────────────────────
# 6. ARI unregister_app is an explicit no-op, not a crash
# ──────────────────────────────────────────────

def test_ari_unregister_app_is_noop():
    async def scenario():
        client = AriClient("http://localhost:8088", "u", "p", "app")
        await client.unregister_app("app")  # must not raise
    run(scenario())
