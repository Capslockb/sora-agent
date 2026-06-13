"""
S0RA Logs CLI — View logs.
"""

import sys
from pathlib import Path

from sora_constants import get_logs_dir
from sora_logging import setup_logging

setup_logging("cli")


def tail_file(filepath: Path, lines: int = 100, follow: bool = False) -> None:
    """Tail a file, optionally following."""
    if not filepath.exists():
        print(f"Log file not found: {filepath}", file=sys.stderr)
        return

    if follow:
        # Use subprocess to tail -f
        import subprocess
        try:
            subprocess.run(["tail", "-f", "-n", str(lines), str(filepath)], check=True)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Error following log: {e}", file=sys.stderr)
    else:
        # Read last N lines
        try:
            with open(filepath, "r") as f:
                all_lines = f.readlines()
                for line in all_lines[-lines:]:
                    print(line.rstrip())
        except Exception as e:
            print(f"Error reading log: {e}", file=sys.stderr)


def main(args) -> int:
    logs_dir = get_logs_dir()

    if not logs_dir.exists():
        print(f"Logs directory not found: {logs_dir}", file=sys.stderr)
        return 1

    log_files = {
        "agent": logs_dir / "agent.log",
        "errors": logs_dir / "errors.log",
        "gateway": logs_dir / "gateway.log",
        "gui": logs_dir / "gui.log",
    }

    if args.session:
        # Filter by session - not implemented yet
        print("Session filtering not yet implemented", file=sys.stderr)
        return 1

    # Determine which log file to show
    if hasattr(args, 'log_type') and args.log_type:
        log_file = log_files.get(args.log_type)
        if not log_file:
            print(f"Unknown log type: {args.log_type}", file=sys.stderr)
            return 1
        tail_file(log_file, args.lines, args.follow)
    else:
        # Show all logs summary
        print("SORA Logs")
        print("=" * 50)
        for name, path in log_files.items():
            size = path.stat().st_size if path.exists() else 0
            print(f"  {name}: {path} ({size} bytes)")
        print()
        print("Usage: sora logs [--follow] [--lines N] [--level LEVEL] [agent|errors|gateway|gui]")
        print("Example: sora logs --follow agent")

    return 0