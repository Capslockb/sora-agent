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


async def _get_bridge_or_error() -> tuple:
    """Get bridge instance or return error response."""
    try:
        from sora_voip.__init__ import _get_bridge
        bridge = await _get_bridge()
        return bridge, None
    except Exception as e:
        return None, str(e)


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
        from sora_voip.__init__ import sora_voip_start

        # Create a mock context for the tool
        class MockContext:
            pass

        result = asyncio.run(sora_voip_start(MockContext(),
            dograh_ws_url=args.dograh_ws or "",
            gemini_model=args.gemini_model or ""))

        if result.get("status") == "started":
            print(f"VOIP bridge started")
            print(f"  HTTP API: {result.get('http_api')}")
            print(f"  Health:   {result.get('health_endpoint')}")
            return 0
        elif result.get("status") == "already_running":
            print("VOIP bridge already running")
            return 0
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            return 1
    except Exception as e:
        print(f"Error starting VOIP bridge: {e}")
        return 1


def cmd_stop(args: argparse.Namespace) -> int:
    """Stop the VOIP bridge."""
    try:
        from sora_voip.__init__ import sora_voip_stop

        class MockContext:
            pass

        result = asyncio.run(sora_voip_stop(MockContext()))

        if result.get("status") == "stopped":
            print("VOIP bridge stopped")
            return 0
        elif result.get("status") == "not_running":
            print("VOIP bridge not running")
            return 0
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            return 1
    except Exception as e:
        print(f"Error stopping VOIP bridge: {e}")
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show VOIP bridge status."""
    try:
        from sora_voip.__init__ import sora_voip_status

        class MockContext:
            pass

        result = asyncio.run(sora_voip_status(MockContext()))

        if args.json:
            _print_json(result)
        else:
            status = result.get("status", "unknown")
            if status == "healthy" or status == "running":
                print(f"Status: {status}")
                print(f"  Active calls: {result.get('active_calls', 0)}")
                print(f"  ARI connected: {result.get('ari_connected', False)}")
                print(f"  Uptime: {result.get('timestamp', 'unknown')}")
            else:
                print(f"Status: {status}")
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
        from sora_voip.__init__ import sora_voip_calls

        class MockContext:
            pass

        result = asyncio.run(sora_voip_calls(MockContext()))

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
        from sora_voip.__init__ import sora_voip_hangup

        class MockContext:
            pass

        result = asyncio.run(sora_voip_hangup(MockContext(), call_id=args.call_id))

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
        from sora_voip.__init__ import sora_voip_control

        class MockContext:
            pass

        result = asyncio.run(sora_voip_control(MockContext(), call_id=args.call_id, action=args.action))

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
        # No subcommand - show help
        print("Sora VOIP Bridge Management")
        print("")
        print("Usage: sora voip <subcommand> [options]")
        print("")
        print("Subcommands:")
        print("  start     Start VOIP bridge")
        print("  stop      Stop VOIP bridge")
        print("  status    Show bridge status")
        print("  calls     List active calls")
        print("  hangup    Hang up a call")
        print("  control   Mute/unmute a call")
        print("")
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