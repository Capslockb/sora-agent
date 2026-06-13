#!/usr/bin/env python3
"""
Standalone Sora VOIP Bridge CLI
Can be run independently: `sora-voip-bridge [options]`
Also installable via pipx.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

from .bridge import VoipBridge, VoipConfig, main as bridge_main


def load_config(config_path: Path) -> VoipConfig:
    """Load config from YAML file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    if yaml is None:
        raise ImportError("PyYAML required for config file support: pip install pyyaml")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    voip_config = data.get("voip", {})
    return VoipConfig(
        # Asterisk
        ari_url=voip_config.get("asterisk", {}).get("ari_url", "http://localhost:8088/ari"),
        ari_user=voip_config.get("asterisk", {}).get("ari_user", "sora"),
        ari_password=voip_config.get("asterisk", {}).get("ari_password", ""),
        app_name=voip_config.get("asterisk", {}).get("app_name", "sora"),
        external_media_host=voip_config.get("asterisk", {}).get("external_media_host", "0.0.0.0"),
        external_media_port=voip_config.get("asterisk", {}).get("external_media_port", 5000),
        # Dograh
        dograh_ws_url=voip_config.get("dograh", {}).get("ws_url", ""),
        dograh_api_key=voip_config.get("dograh", {}).get("api_key", ""),
        # Gemini
        gemini_model=voip_config.get("gemini", {}).get("model", "gemini-2.0-flash-exp"),
        gemini_voice=voip_config.get("gemini", {}).get("voice", "Puck"),
        gemini_temperature=voip_config.get("gemini", {}).get("temperature", 0.7),
        # HTTP API
        http_host=voip_config.get("http_api", {}).get("host", "0.0.0.0"),
        http_port=voip_config.get("http_api", {}).get("port", 18944),
    )


def load_env():
    """Load environment variables from .env file if present."""
    env_paths = [
        Path.cwd() / ".env",
        Path.home() / ".config" / "sora" / "voip.env",
        Path("/etc/sora/voip.env"),
    ]
    for path in env_paths:
        if path.exists():
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ.setdefault(key.strip(), val.strip())
            break


async def run_bridge(config: VoipConfig):
    """Run the VOIP bridge with given config."""
    bridge = VoipBridge(config)
    try:
        await bridge.start()
        print(f"Sora VOIP Bridge running on http://{config.http_host}:{config.http_port}")
        print("Press Ctrl+C to stop")
        while bridge._running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await bridge.stop()


def main():
    parser = argparse.ArgumentParser(
        description="Sora VOIP Bridge — Asterisk + Dograh + Gemini Live",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with environment variables
  SORA_DOGRAH_WS_URL=ws://dograh:8080/gemini sora-voip-bridge

  # Run with config file
  sora-voip-bridge --config ~/.config/sora/voip.yaml

  # Run with explicit args
  sora-voip-bridge --ari-url http://asterisk:8088/ari --dograh-ws ws://dograh:8080/gemini
        """,
    )

    parser.add_argument("--config", "-c", type=Path, help="YAML config file")
    parser.add_argument("--ari-url", help="Asterisk ARI base URL")
    parser.add_argument("--ari-user", help="ARI username")
    parser.add_argument("--ari-password", help="ARI password")
    parser.add_argument("--ari-app", default="sora", help="ARI application name")
    parser.add_argument("--external-media-host", default="0.0.0.0", help="ExternalMedia bind host")
    parser.add_argument("--external-media-port", type=int, default=5000, help="ExternalMedia base port")
    parser.add_argument("--dograh-ws", dest="dograh_ws_url", help="Dograh WebSocket URL (required)")
    parser.add_argument("--dograh-api-key", help="Dograh API key")
    parser.add_argument("--gemini-model", default="gemini-2.0-flash-exp", help="Gemini model")
    parser.add_argument("--gemini-voice", default="Puck", help="Gemini voice")
    parser.add_argument("--gemini-temperature", type=float, default=0.7, help="Gemini temperature")
    parser.add_argument("--http-host", default="0.0.0.0", help="HTTP API bind host")
    parser.add_argument("--http-port", type=int, default=18944, help="HTTP API port")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    load_env()

    # Build config: CLI args > env > config file > defaults
    if args.config:
        config = load_config(args.config)
    else:
        config = VoipConfig(
            ari_url=args.ari_url or os.getenv("SORA_ARI_URL", "http://localhost:8088/ari"),
            ari_user=args.ari_user or os.getenv("SORA_ARI_USER", "sora"),
            ari_password=args.ari_password or os.getenv("SORA_ARI_PASSWORD", ""),
            app_name=args.ari_app or os.getenv("SORA_ARI_APP", "sora"),
            external_media_host=args.external_media_host or os.getenv("SORA_EXTERNAL_MEDIA_HOST", "0.0.0.0"),
            external_media_port=args.external_media_port or int(os.getenv("SORA_EXTERNAL_MEDIA_PORT", "5000")),
            dograh_ws_url=args.dograh_ws_url or os.getenv("SORA_DOGRAH_WS_URL", ""),
            dograh_api_key=args.dograh_api_key or os.getenv("SORA_DOGRAH_API_KEY", ""),
            gemini_model=args.gemini_model or os.getenv("SORA_GEMINI_MODEL", "gemini-2.0-flash-exp"),
            gemini_voice=args.gemini_voice or os.getenv("SORA_GEMINI_VOICE", "Puck"),
            gemini_temperature=args.gemini_temperature or float(os.getenv("SORA_GEMINI_TEMPERATURE", "0.7")),
            http_host=args.http_host or os.getenv("SORA_HTTP_HOST", "0.0.0.0"),
            http_port=args.http_port or int(os.getenv("SORA_HTTP_PORT", "18944")),
        )

    # Override with explicit CLI args (non-empty)
    if args.ari_url:
        config.ari_url = args.ari_url
    if args.ari_user:
        config.ari_user = args.ari_user
    if args.ari_password:
        config.ari_password = args.ari_password
    if args.dograh_ws_url:
        config.dograh_ws_url = args.dograh_ws_url
    if args.dograh_api_key:
        config.dograh_api_key = args.dograh_api_key

    if not config.dograh_ws_url:
        parser.error("Dograh WebSocket URL is required (--dograh-ws or SORA_DOGRAH_WS_URL)")

    try:
        asyncio.run(run_bridge(config))
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())