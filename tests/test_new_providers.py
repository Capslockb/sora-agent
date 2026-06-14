"""Tests for new voice bridge clients: OpenAI Realtime, xAI, Ultravox, Retell."""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock

from sora_cli.openai_realtime_client import (
    OpenAIRealtimeConfig,
    OpenAIRealtimeClient,
    create_ephemeral_token,
)
from sora_cli.xai_client import XAIConfig, XAIClient
from sora_cli.ultravox_client import UltravoxConfig, UltravoxClient, create_ultravox_call
from sora_cli.retell_client import RetellConfig, RetellClient, create_web_call


# ── OpenAI Realtime ──

class TestOpenAIRealtime:
    def test_config_defaults(self):
        cfg = OpenAIRealtimeConfig(api_key="sk-test")
        assert cfg.model == "gpt-4o-realtime-preview"
        assert cfg.voice == "alloy"

    @pytest.mark.asyncio
    async def test_create_ephemeral_token(self):
        mock_resp = {
            "client_secret": {"value": "ephemeral-key-123"},
            "model": "gpt-4o-realtime-preview",
        }
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=json.dumps(mock_resp)
            )
            cfg = OpenAIRealtimeConfig(api_key="sk-test")
            result = await create_ephemeral_token(cfg)
            assert result["client_secret"]["value"] == "ephemeral-key-123"

    @pytest.mark.asyncio
    async def test_client_connect_disconnect(self):
        cfg = OpenAIRealtimeConfig(api_key="sk-test")
        client = OpenAIRealtimeClient(cfg)
        with patch(
            "sora_cli.openai_realtime_client.create_ephemeral_token",
            return_value={"client_secret": {"value": "k"}},
        ):
            await client.connect()
            assert client.is_connected
            assert client.ephemeral_key() == "k"
            await client.disconnect()
            assert not client.is_connected


# ── xAI Grok ──

class TestXAIClient:
    def test_config_defaults(self):
        cfg = XAIConfig(api_key="xai-test")
        assert cfg.model == "grok-2-realtime"
        assert cfg.voice == "ember"

    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        cfg = XAIConfig(api_key="xai-test")
        client = XAIClient(cfg)
        with patch("websockets.connect", new_callable=AsyncMock) as mock_ws:
            mock_ws.return_value.send = AsyncMock()
            mock_ws.return_value.close = AsyncMock()
            mock_ws.return_value.__aiter__ = AsyncMock(
                return_value=AsyncMock().__aiter__.return_value
            )
            await client.connect()
            assert client.is_connected
            await client.disconnect()
            assert not client.is_connected


# ── Ultravox ──

class TestUltravoxClient:
    def test_config_defaults(self):
        cfg = UltravoxConfig(api_key="uv-test")
        assert cfg.model == "fixie-ai/ultravox"

    @pytest.mark.asyncio
    async def test_create_call(self):
        mock_resp = {
            "callId": "call-123",
            "joinUrl": "wss://ultravox.example/join",
        }
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 201
            mock_post.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=json.dumps(mock_resp)
            )
            cfg = UltravoxConfig(api_key="uv-test")
            url = await create_ultravox_call(cfg)
            assert url == "wss://ultravox.example/join"


# ── Retell ──

class TestRetellClient:
    def test_config_defaults(self):
        cfg = RetellConfig(api_key="rt-test", agent_id="agent-1")
        assert cfg.agent_id == "agent-1"

    @pytest.mark.asyncio
    async def test_create_web_call(self):
        mock_resp = {
            "call_id": "call-456",
            "access_token": "tok",
            "websocket_url": "wss://retell.example/ws",
        }
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 201
            mock_post.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=json.dumps(mock_resp)
            )
            cfg = RetellConfig(api_key="rt-test", agent_id="agent-1")
            data = await create_web_call(cfg)
            assert data["call_id"] == "call-456"
            assert data["access_token"] == "tok"
