"""
S0RA Update CLI — Update SORA Agent to latest version.
"""

import subprocess
import sys
from pathlib import Path

from sora_cli.config import get_sora_home
from sora_logging import setup_logging
from sora_cli.cli_output import print_error, print_success, print_info

setup_logging("cli")


def main(args) -> int:
    project_root = Path(__file__).parent.parent.resolve()

    print("S0RA Agent Update")
    print("=" * 30)
    print()

    if not (project_root / ".git").exists():
        print_error("Not a git repository — cannot update via git")
        print_info("Reinstall with: pipx install --force sora-agent")
        return 1

    # Check current version
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True
        )
        current_commit = result.stdout.strip()[:8]
    except subprocess.CalledProcessError:
        print_error("Failed to get current commit")
        return 1

    print_info(f"Current commit: {current_commit}")

    # Fetch latest
    print_info("Fetching latest changes...")
    try:
        subprocess.run(["git", "-C", str(project_root), "fetch", "origin"], check=True)
    except subprocess.CalledProcessError:
        print_error("Failed to fetch from origin")
        return 1

    # Check if behind
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "rev-list", "HEAD..origin/main", "--count"],
            capture_output=True, text=True, check=True
        )
        behind = int(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        behind = 0

    if behind == 0 and not args.force:
        print_success("Already up to date!")
        return 0

    print_info(f"Behind by {behind} commit(s)")

    if args.check_only:
        print_info("Update available (use without --check-only to apply)")
        return 0

    # Pull changes
    print_info("Pulling changes...")
    try:
        subprocess.run(["git", "-C", str(project_root), "pull", "origin", "main"], check=True)
    except subprocess.CalledProcessError:
        print_error("Failed to pull changes")
        return 1

    # Reinstall dependencies
    print_info("Reinstalling dependencies...")
    try:
        subprocess.run(["uv", "pip", "install", "-e", str(project_root)], check=True)
    except subprocess.CalledProcessError:
        print_error("Failed to reinstall dependencies")
        return 1

    # Get new version
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True
        )
        new_commit = result.stdout.strip()[:8]
    except subprocess.CalledProcessError:
        new_commit = "unknown"

    print_success(f"Updated successfully! (was {current_commit}, now {new_commit})")
    print_info("Restart any running SORA processes to use the new version")
    return 0