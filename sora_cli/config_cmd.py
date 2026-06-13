"""
S0RA Config CLI — Configuration management.
"""

import sys
from pathlib import Path

from sora_cli.config import (
    load_config, save_config, load_raw_config,
    get_env_value, save_env_value, remove_env_value,
    get_config_path, get_env_path,
)
from sora_constants import (
    ensure_sora_home as ensure_hermes_home,
)
from sora_cli.cli_output import print_error, print_success, print_info

from sora_logging import setup_logging
setup_logging("cli")


def show_config(args) -> int:
    config = load_raw_config()
    if not config:
        print_info("No user config.yaml found. Run 'sora setup' to create one.")
        return 0

    import yaml
    print(yaml.dump(config, sort_keys=False, allow_unicode=True))
    return 0


def get_config(args) -> int:
    config = load_config()
    key = args.key
    value = config
    for part in key.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            print_error(f"Key not found: {key}")
            return 1

    if value is None:
        print_error(f"Key not found: {key}")
        return 1

    if isinstance(value, dict):
        import yaml
        print(yaml.dump(value, sort_keys=False, allow_unicode=True))
    else:
        print(value)
    return 0


def set_config(args) -> int:
    config = load_config()
    key = args.key
    value_str = args.value

    # Parse value
    try:
        import json
        value = json.loads(value_str)
    except json.JSONDecodeError:
        # Try to interpret as bool/int/float
        if value_str.lower() in ("true", "false"):
            value = value_str.lower() == "true"
        elif value_str.isdigit():
            value = int(value_str)
        else:
            try:
                value = float(value_str)
            except ValueError:
                value = value_str

    # Navigate and set
    parts = key.split(".")
    target = config
    for part in parts[:-1]:
        if part not in target:
            target[part] = {}
        target = target[part]

    target[parts[-1]] = value
    save_config(config)
    print_success(f"Set {key} = {value}")
    return 0


def reset_config(args) -> int:
    from sora_cli.config import DEFAULT_CONFIG
    save_config(DEFAULT_CONFIG)
    print_success("Configuration reset to defaults")
    return 0


def edit_config(args) -> int:
    ensure_hermes_home()
    cfg_path = get_config_path()
    import os
    editor = os.environ.get("EDITOR", "nano")
    import subprocess
    result = subprocess.run([editor, str(cfg_path)])
    if result.returncode == 0:
        print_success("Configuration edited")
    else:
        print_error("Editor exited with error")
    return result.returncode


def wizard_config(args) -> int:
    from sora_cli.setup import main as setup_main
    return setup_main(args)


def main(args) -> int:
    if args.config_command is None:
        print("Usage: sora config <show|get|set|reset|edit|wizard>")
        return 1

    handlers = {
        "show": show_config,
        "get": get_config,
        "set": set_config,
        "reset": reset_config,
        "edit": edit_config,
        "wizard": wizard_config,
    }

    handler = handlers.get(args.config_command)
    if handler:
        return handler(args)
    else:
        print_error(f"Unknown config command: {args.config_command}")
        return 1