from pathlib import Path

from fastapi.testclient import TestClient


def test_visualizer_state_endpoint(monkeypatch, tmp_path):
    home = tmp_path / "sora-home"
    home.mkdir()
    (home / "config.yaml").write_text(
        "voice:\n"
        "  provider: elevenlabs\n"
        "  discord:\n"
        "    guild_id: guild-1\n"
        "    voice_channel_id: channel-1\n"
        "  elevenlabs:\n"
        "    agent_id: agent-1\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SORA_HOME", str(home))

    from sora_api import app

    response = TestClient(app).get("/api/visualizer/state")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["call"]["provider"] == "elevenlabs"
    assert payload["call"]["guild"] == "guild-1"
    assert payload["call"]["channel"] == "channel-1"
    assert any(provider["id"] == "elevenlabs" and provider["active"] for provider in payload["providers"])


def test_resolve_website_dir_prefers_dev_checkout():
    from sora_cli.main import _resolve_website_dir

    website_dir = _resolve_website_dir()

    assert website_dir.name == "website"
    assert (website_dir / "package.json").exists()
    assert (website_dir / "src" / "main.tsx").exists()
