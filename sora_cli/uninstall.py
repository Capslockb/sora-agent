"""
S0RA Uninstall CLI — Uninstall SORA Agent.
"""

import shutil
import sys
from pathlib import Path

from sora_constants import get_sora_home, get_default_sora_root
from sora_logging import setup_logging
from sora_cli.cli_output import print_error, print_success, print_info, print_warning

setup_logging("cli")


def main(args) -> int:
    if not args.confirm:
        print_warning("This will remove SORA Agent and all its data.")
        print_warning(f"Data directory: {get_sora_home()}")
        print()
        confirm = input("Type 'yes' to confirm uninstallation: ").strip()
        if confirm.lower() != "yes":
            print_info("Uninstallation cancelled")
            return 0

    sora_home = get_sora_home()
    default_root = get_default_sora_root()

    # Remove profile directory
    if sora_home.exists() and sora_home != default_root:
        # Named profile
        print_info(f"Removing profile: {sora_home}")
        shutil.rmtree(sora_home)
        print_success("Profile removed")

        # Remove active_profile if it points to this
        active_file = default_root / "active_profile"
        if active_file.exists():
            current = active_file.read_text().strip()
            if current == sora_home.name:
                active_file.unlink()
                print_info("Cleared active_profile")
    elif sora_home == default_root:
        # Default profile - remove everything
        print_warning(f"Removing default SORA installation: {sora_home}")
        shutil.rmtree(sora_home)
        print_success("Default SORA installation removed")
    else:
        print_info(f"SORA home not found: {sora_home}")

    # Also remove the pipx/pip installation if requested
    print()
    print_info("To also remove the Python package:")
    print_info("  pipx uninstall sora-agent")
    print_info("  # or")
    print_info("  pip uninstall sora-agent")

    print_success("Uninstallation complete")
    return 0