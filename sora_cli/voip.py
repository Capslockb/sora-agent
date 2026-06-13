"""
Sora VOIP CLI subcommand handlers.
Manages the VOIP bridge (Asterisk + Dograh + Gemini Live).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Add plugin path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "plugins"))

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path.home() / ".config" / "sora" / "voip.env")
except ImportError:
    pass


def _print_json(data: dict) -> None:
    """Print data as JSON."""
    print(json.dumps(data, indent=2, default=str))


def cmd_start(args: argparse.Namespace) -> int:
    """Start the VOIP bridge."""
    # Override env from args
    if args.dograh_ws:
        os.environ["SORA_DOGRAH_WS_URL"] = args.dograh_ws
    if args.gemini_model:
        os.environ["SORA_GEMINI_MODEL"] = args.gemini_model

    try:
        from plugins.sora_voip.bridge import VoipBridge, VoipConfig

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
            print("Error: SORA_DOGRAH_WS_URL is required (set in ~/.config/sora/voip.env or --dograh-ws)")
            return 1

        bridge = VoipConfig(config)
        # Start the bridge in async
        async def run_bridge():
            bridge = VoipBridge(config)
            await bridge.start()
            print(f"VOIP bridge started")
            print(f"  HTTP API: http://{config.http_host}:{config.http_port}")
            print(f"  Health:   http://{config.http_host}:{config.http_port}/health")

            if args.detach:
                # Run in background
                print("Running in background...")
                while True:
                    await asyncio.sleep(3600)
            else:
                try:
                    while bridge._running:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    print("\nShutting down...")
                await bridge.stop()

        if args.detach:
            # Run in background using a detached process
            import subprocess
            result = subprocess.Popen([
                sys.executable, "-m", "plugins.sora_voip.cli",
                "--dograh-ws", config.dograh_ws_url,
                "--gemini-model", config.gemini_model,
            ], start_new_session=True)
            print(f"VOIP bridge started in background (PID: {result.pid})")
            return 0
        else:
            asyncio.run(run_bridge())
            return 0

    except Exception as e:
        print(f"Error starting VOIP bridge: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_stop(args: argparse.Namespace) -> int:
    """Stop the VOIP bridge."""
    try:
        import aiohttp
        # Get bridge URL from env
        http_host = os.getenv("SORA_HTTP_HOST", "0.0.0.0")
        http_port = int(os.getenv("SORA_HTTP_PORT", "18944"))
        url = f"http://{http_host}:{http_port}/control"

        async def stop_bridge():
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"action": "shutdown"}, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(data.get("status", "stopped"))
                    else:
                        print(f"Error: {resp.status}")

        asyncio.run(stop_bridge())
        print("VOIP bridge stopped")
        return 0
    except Exception as e:
        print(f"Error stopping VOIP bridge: {e}")
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show VOIP bridge status."""
    try:
        import aiohttp
        http_host = os.getenv("SORA_HTTP_HOST", "0.0.0.0")
        http_port = int(os.getenv("SORA_HTTP_PORT", "18944"))
        url = f"http://{http_host}:{http_port}/health"

        async def get_status():
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"status": "error", "http_status": resp.status}

        result = asyncio.run(get_status())

        if args.json:
            _print_json(result)
        else:
            status_val = result.get("status", "unknown")
            if status_val in ("healthy", "running"):
                print(f"Status: {status_val}")
                print(f"  Active calls: {result.get('active_calls', 0)}")
                print(f"  ARI connected: {result.get('ari_connected', False)}")
                print(f"  Uptime: {result.get('timestamp', 'unknown')}")
            else:
                print(f"Status: {status_val}")
                if "error" in result:
                    print(f"  Error: {result['error']}")
        return 0
    except Exception as e:
        if args.json:
            _print_json({"status": "error", "error": str(e)})
        else:
            print(f"Error: {e}")
        return 1


def cmd_calls(args: argparse.Namespace) -> int:
    """List active VOIP calls."""
    try:
        import aiohttp
        http_host = os.getenv("SORA_HTTP_HOST", "0.0.0.0")
        http_port = int(os.getenv("SORA_HTTP_PORT", "18944"))
        url = f"http://{http_host}:{http_port}/calls"

        async def get_calls():
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"status": "error", "http_status": resp.status}

        result = asyncio.run(get_calls())

        if args.json:
            _print_json(result)
        else:
            calls = result.get("calls", [])
            if not calls:
                print("No active calls")
                return 0

            print(f"Active calls ({len(calls)}):")
            for call in calls:
                print(f"  {call.get('call_id', 'unknown')}")
                print(f"    Channel: {call.get('channel_id', 'unknown')}")
                print(f"    Duration: {call.get('duration_seconds', 0):.1f}s")
                print(f"    Audio in/out: {call.get('audio_in_chunks', 0)}/{call.get('audio_out_chunks', 0)}")
                print(f"    Playback: {'active' if call.get('playback_active') else 'idle'}")
                print(f"    RTP port: {call.get('external_media_port', 'unknown')}")
        return 0
    except Exception as e:
        if args.json:
            _print_json({"status": "error", "error": str(e)})
        else:
            print(f"Error: {e}")
        return 1


def cmd_hangup(args: argparse.Namespace) -> int:
    """Hang up a VOIP call."""
    try:
        import aiohttp
        http_host = os.getenv("SORA_HTTP_HOST", "0.0.0.0")
        http_port = int(os.getenv("SORA_HTTP_PORT", "18944"))
        url = f"http://{http_host}:{http_port}/calls/{args.call_id}/hangup"

        async def do_hangup():
            async with aiohttp.ClientSession() as session:
                async with session.post(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"status": "error", "http_status": resp.status}

        result = asyncio.run(do_hangup())

        if result.get("status") == "hangup initiated":
            print(f"Hangup initiated for call {args.call_id}")
            return 0
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_control(args: argparse.Namespace) -> int:
    """Control a VOIP call (mute/unmute)."""
    try:
        import aiohttp
        http_host = os.getenv("SORA_HTTP_HOST", "0.0.0.0")
        http_port = int(os.getenv("SORA_HTTP_PORT", "18944"))
        url = f"http://{http_host}:{http_port}/control"

        async def do_control():
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"action": args.action, "call_id": args.call_id}, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"status": "error", "http_status": resp.status}

        result = asyncio.run(do_control())

        if result.get("status") in ("muted", "unmuted"):
            print(f"Call {args.call_id} {result['status']}")
            return 0
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def main(args: argparse.Namespace) -> int:
    """Main VOIP subcommand dispatcher."""
    subcommand = getattr(args, "voip_command", None)

    if subcommand is None:
        print("Sora VOIP Bridge Management")
        print()
        print("Usage: sora voip <subcommand> [options]")
        print()
        print("Subcommands:")
        print("  start     Start VOIP bridge")
        print("  stop      Stop VOIP bridge")
        print("  status    Show bridge status")
        print("  calls     List active calls")
        print("  hangup    Hang up a call")
        print("  control   Mute/unmute a call")
        print()
        print("Run 'sora voip <subcommand> --help' for more info")
        return 0

    handlers = {
        "start": cmd_start,
        "stop": cmd_stop,
        "status": cmd_status,
        "calls": cmd_calls,
        "hangup": cmd_hangup,
        "control": cmd_control,
    }

    handler = handlers.get(subcommand)
    if handler:
        return handler(args)
    else:
        print(f"Unknown subcommand: {subcommand}")
        return 1