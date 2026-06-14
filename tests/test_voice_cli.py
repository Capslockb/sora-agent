import asyncio
import base64
import json


def test_resolve_discord_target_prefers_config(monkeypatch):
    from sora_cli.voice import _resolve_discord_target

    monkeypatch.delenv("DISCORD_GUILD_ID", raising=False)
    monkeypatch.delenv("DISCORD_VOICE_CHANNEL_ID", raising=False)
    config = {
        "voice": {
            "discord": {
                "guild_id": "guild-default",
                "voice_channel_id": "chan-default",
                "default_user_id": "user-default",
            },
            "elevenlabs": {"channel_id": "chan-eleven"},
        }
    }

    assert _resolve_discord_target(config, "elevenlabs") == (
        "guild-default",
        "chan-eleven",
        "user-default",
    )


def test_resolve_discord_target_uses_env_fallback(monkeypatch):
    from sora_cli.voice import _resolve_discord_target

    monkeypatch.setenv("DISCORD_GUILD_ID", "guild-env")
    monkeypatch.setenv("DISCORD_VOICE_CHANNEL_ID", "chan-env")
    monkeypatch.setenv("DISCORD_USER_ID", "user-env")

    assert _resolve_discord_target({}, "gemini_live") == (
        "guild-env",
        "chan-env",
        "user-env",
    )


def test_start_elevenlabs_builds_public_websocket_from_autodetected_config(tmp_path, monkeypatch):
    home = tmp_path / "sora-home"
    home.mkdir()
    (home / "config.yaml").write_text(
        "voice:\n"
        "  discord:\n"
        "    guild_id: guild-1\n"
        "    voice_channel_id: channel-1\n"
        "    default_user_id: user-1\n"
        "  elevenlabs:\n"
        "    agent_id: agent-1\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DISCORD" + "_BOT_TOKEN", "dummy")
    monkeypatch.setenv("SORA_HOME", str(home))
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)

    from sora_cli.voice import start_elevenlabs

    result = asyncio.run(start_elevenlabs())

    assert result["status"] == "success"
    assert result["guild_id"] == "guild-1"
    assert result["channel_id"] == "channel-1"
    assert result["user_id"] == "user-1"
    assert result["auth_mode"] == "public-agent-url"
    assert result["websocket_url"] == (
        "wss://api.elevenlabs.io/v1/convai/conversation?agent_id=agent-1"
    )


def test_main_registers_elevenlabs_subcommand():
    from sora_cli.main import parser

    args = parser.parse_args(["voice", "elevenlabs", "--guild", "g", "--channel", "c"])

    assert args.command == "voice"
    assert args.voice_command == "elevenlabs"
    assert args.guild == "g"
    assert args.channel == "c"



def test_elevenlabs_public_conversation_url():
    from sora_cli.elevenlabs_client import public_conversation_url

    assert public_conversation_url("agent-x") == (
        "wss://api.elevenlabs.io/v1/convai/conversation?agent_id=agent-x"
    )


def test_elevenlabs_client_handles_ping_and_audio():
    from sora_cli.elevenlabs_client import ElevenLabsConversationClient, ElevenLabsConversationConfig

    sent = []
    received_audio = []

    class FakeWebSocket:
        async def send(self, payload):
            sent.append(payload)

    async def on_audio(chunk, event):
        received_audio.append((chunk, event["audio_event"]["event_id"]))

    client = ElevenLabsConversationClient(
        ElevenLabsConversationConfig(agent_id="agent-x"),
        on_audio=on_audio,
    )
    client.websocket = FakeWebSocket()

    asyncio.run(client.handle_event({"type": "ping", "ping_event": {"event_id": 7}}))
    asyncio.run(
        client.handle_event(
            {
                "type": "audio",
                "audio_event": {
                    "audio_base_64": base64.b64encode(b"pcm").decode("ascii"),
                    "event_id": 8,
                },
            }
        )
    )

    assert json.loads(sent[0]) == {"type": "pong", "event_id": 7}
    assert received_audio == [(b"pcm", 8)]
