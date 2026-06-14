"""
S0RA Agent Configuration — Config loading, defaults, and helpers.
Mirrors hermes_cli/config.py from Hermes Agent.
"""

import copy
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

from sora_constants import ensure_sora_home, get_config_path, get_env_path, get_sora_home


# Default configuration — mirrors Hermes structure but tailored for Sora
DEFAULT_CONFIG: Dict[str, Any] = {
    "model": {
        "provider": "openrouter",
        "base_url": "https://openrouter.ai/api/v1",
        "default": "nvidia/nemotron-3-ultra:free",
        "reasoning_effort": "medium",
    },
    "agent": {
        "max_iterations": 50,
        "enabled_toolsets": ["hermes", "terminal", "web", "skills"],
        "disabled_toolsets": [],
        "compression": {
            "enabled": True,
            "threshold": 0.8,
            "target_ratio": 0.5,
        },
    },
    "terminal": {
        "backend": "local",
        "cwd": "~",
        "timeout": 180,
    },
    "compression": {
        "enabled": True,
        "mode": "auto",
        "summarize_tool_output": True,
    },
    "display": {
        "interface": "cli",
        "skin": "sora",
        "tool_prefix": "┊",
        "show_tool_progress": True,
        "show_reasoning": True,
        "context_bar": True,
    },
    "stt": {
        "provider": "faster-whisper",
        "language": "en",
    },
    "tts": {
        "provider": "edge",
        "voice": "en-US-AriaNeural",
    },
    "memory": {
        "provider": "honcho",
        "honcho": {
            "host": "http://localhost:8377",
            "peer": "user",
        },
    },
    "security": {
        "redact_secrets": True,
        "allow_dangerous_commands": False,
    },
    "delegation": {
        "enabled": True,
        "max_concurrent_children": 6,
        "max_spawn_depth": 2,
    },
    "smart_model_routing": {
        "enabled": True,
        "cheap_model": {
            "model": "nvidia/nemotron-3-ultra:free",
            "provider": "openrouter",
        },
        "max_simple_chars": 500,
    },
    "checkpoints": {
        "enabled": True,
        "interval_minutes": 30,
    },
    "auxiliary": {
        "curator": {"provider": "openrouter", "model": "nvidia/nemotron-3-ultra:free"},
        "vision": {"provider": "openrouter", "model": "nvidia/nemotron-3-ultra:free"},
        "embedding": {"provider": "openrouter", "model": "nvidia/nemotron-3-ultra:free"},
        "title": {"provider": "openrouter", "model": "nvidia/nemotron-3-ultra:free"},
        "session_search": {"provider": "openrouter", "model": "nvidia/nemotron-3-ultra:free"},
    },
    "curator": {
        "enabled": True,
        "interval_hours": 24,
        "min_idle_hours": 2,
        "stale_after_days": 30,
        "archive_after_days": 90,
    },
    "skills": {
        "auto_update": True,
        "bundles_enabled": True,
    },
    "gateway": {
        "host": "0.0.0.0",
        "port": 9119,
        "platforms": {},
    },
    "logging": {
        "level": "INFO",
        "file_level": "DEBUG",
    },
    "cron": {
        "enabled": True,
    },
    "profiles": {
        "active": "default",
    },
    "plugins": {
        "enabled": [],
    },
    "honcho": {
        "enabled": True,
        "host": "http://localhost:8377",
    },
    # Sora-specific: Voice bridges
    "voice": {
        "gemini_live": {
            "enabled": True,
            "model": "gemini-3.1-flash-live-preview",
            "voice": "Kore",
            "auto_greeting": "I'm here.",
            "allowed_speakers": [],
            "video_enabled": True,
            "video_max_fps": 1.0,
            "audio_preroll_ms": 320,
            "auto_leave_quiet_seconds": 900,
        },
        "vapi": {
            "enabled": True,
            "assistant_id": "",
            "phone_number_id": "",
        },
        "elevenlabs": {
            "enabled": False,
            "agent_id": "",
            "voice_id": "",
            "channel_id": "",
        },
        "discord": {
            "bot_token": "",
            "application_id": "",
            "guild_id": "",
            "default_user_id": "",
            "voice_channel_id": "",
        },
    },
    # Sora-specific: MCP
    "mcp": {
        "enabled": True,
        "servers": {},
    },
}

_config_version = 1


def get_hermes_home() -> Path:
    """Compatibility alias for get_sora_home()."""
    return get_sora_home()


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the full merged configuration.
    Merges DEFAULT_CONFIG with user config.yaml (deep merge).
    """
    if config_path is None:
        config_path = get_config_path()

    user_config: Dict[str, Any] = {}
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                user_config = yaml.load(f, Loader=SafeLoader) or {}
        except Exception:
            user_config = {}

    return _deep_merge(DEFAULT_CONFIG, user_config)


def load_raw_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load raw user config.yaml without merging defaults."""
    if config_path is None:
        config_path = get_config_path()

    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                return yaml.load(f, Loader=SafeLoader) or {}
        except Exception:
            return {}
    return {}


def save_config(config: Dict[str, Any], config_path: Optional[Path] = None) -> None:
    """Save configuration to config.yaml."""
    if config_path is None:
        config_path = get_config_path()

    ensure_sora_home()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Add version marker
    config = dict(config)
    config["_config_version"] = _config_version

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, Dumper=yaml.SafeDumper, sort_keys=False, allow_unicode=True)


def read_raw_config() -> Dict[str, Any]:
    """Read raw config.yaml (for gateway runtime)."""
    return load_raw_config()


def get_config_path_for_profile(profile_name: str) -> Path:
    """Get config.yaml path for a specific profile."""
    from sora_constants import resolve_profile_env
    try:
        home = resolve_profile_env(profile_name)
        return Path(home) / "config.yaml"
    except FileNotFoundError:
        return get_sora_root() / "profiles" / profile_name / "config.yaml"


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def cfg_get(config: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Get a nested config value using dot-separated keys."""
    value = config
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
    return value if value is not None else default


def cfg_set(config: Dict[str, Any], *keys: str, value: Any) -> None:
    """Set a nested config value using dot-separated keys."""
    obj = config
    for key in keys[:-1]:
        if key not in obj or not isinstance(obj[key], dict):
            obj[key] = {}
        obj = obj[key]
    obj[keys[-1]] = value


# Environment variable handling
_dotenv_loaded = False


def load_sora_dotenv(hermes_home: Optional[Path] = None, project_env: Optional[Path] = None) -> None:
    """
    Load .env from SORA_HOME and optionally from project root.
    Mirrors hermes_cli.env_loader.load_hermes_dotenv.
    """
    global _dotenv_loaded
    if _dotenv_loaded:
        return

    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    # 1. Load from SORA_HOME (~/.sora/.env)
    if hermes_home:
        env_path = hermes_home / ".env"
    else:
        env_path = get_env_path()

    if env_path.exists():
        load_dotenv(env_path, override=True)

    # 2. Load from project root as dev fallback
    if project_env and project_env.exists():
        load_dotenv(project_env, override=False)

    _dotenv_loaded = True


def get_env_value(key: str, default: str = "") -> str:
    """Get an environment variable value."""
    return os.environ.get(key, default)


def save_env_value(key: str, value: str) -> None:
    """Save a value to the .env file."""
    ensure_sora_home()
    env_path = get_env_path()

    # Read existing
    existing = {}
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    existing[k.strip()] = v.strip()

    # Update
    existing[key] = value

    # Write back
    with open(env_path, "w", encoding="utf-8") as f:
        for k, v in sorted(existing.items()):
            f.write(f"{k}={v}\n")

    # Also update current process
    os.environ[key] = value


def remove_env_value(key: str) -> None:
    """Remove a key from .env file."""
    env_path = get_env_path()
    if not env_path.exists():
        return

    existing = {}
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                existing[k.strip()] = v.strip()

    if key in existing:
        del existing[key]

    with open(env_path, "w", encoding="utf-8") as f:
        for k, v in sorted(existing.items()):
            f.write(f"{k}={v}\n")

    os.environ.pop(key, None)