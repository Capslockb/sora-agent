"""
S0RA Agent Constants — Profile-aware paths and display helpers.
Mirrors hermes_constants.py from Hermes Agent.
"""

import os
from pathlib import Path
from typing import Optional

# Default root for all sora profiles
DEFAULT_SORA_ROOT = Path.home() / ".sora"


def get_sora_root() -> Path:
    """
    Get the root directory for the default sora profile (~/.sora/).
    This is the base that contains config.yaml, .env, plugins/, etc.
    """
    return DEFAULT_SORA_ROOT


def get_sora_home() -> Path:
    """
    Get the active SORA_HOME directory.
    Reads SORA_HOME env var, falls back to ~/.sora/.
    This is the profile-aware home directory.
    """
    home = os.environ.get("SORA_HOME")
    if home:
        return Path(home).expanduser().resolve()
    return get_sora_root()


def get_default_sora_root() -> Path:
    """
    Get the default sora root ( ~/.sora/ ) regardless of SORA_HOME.
    Used for finding active_profile file.
    """
    return DEFAULT_SORA_ROOT


def display_sora_home() -> str:
    """
    Return a human-readable display string for the current SORA_HOME.
    Uses ~ for home directory.
    """
    home = get_sora_home()
    try:
        return str(home.relative_to(Path.home())).replace(str(Path.home()), "~")
    except ValueError:
        return str(home)


def get_config_path() -> Path:
    """Get the path to config.yaml for the active profile."""
    return get_sora_home() / "config.yaml"


def get_env_path() -> Path:
    """Get the path to .env for the active profile."""
    return get_sora_home() / ".env"


def get_sessions_dir() -> Path:
    """Get the sessions directory for the active profile."""
    return get_sora_home() / "sessions"


def get_plugins_dir() -> Path:
    """Get the plugins directory for the active profile."""
    return get_sora_home() / "plugins"


def get_skills_dir() -> Path:
    """Get the skills directory for the active profile."""
    return get_sora_home() / "skills"


def get_cron_dir() -> Path:
    """Get the cron directory for the active profile."""
    return get_sora_home() / "cron"


def get_logs_dir() -> Path:
    """Get the logs directory for the active profile."""
    return get_sora_home() / "logs"


def get_state_db_path() -> Path:
    """Get the SQLite state database path for the active profile."""
    return get_sora_home() / "state.db"


def get_optional_skills_dir() -> Path:
    """Get the optional-skills directory (bundled with repo)."""
    # This points to the repo's optional-skills/ not the user's
    return Path(__file__).parent.parent / "optional-skills"


def ensure_sora_home() -> Path:
    """
    Ensure the SORA_HOME directory exists with standard subdirectories.
    Returns the home path.
    """
    home = get_sora_home()
    home.mkdir(parents=True, exist_ok=True)
    (home / "plugins").mkdir(exist_ok=True)
    (home / "skills").mkdir(exist_ok=True)
    (home / "cron").mkdir(exist_ok=True)
    (home / "sessions").mkdir(exist_ok=True)
    (home / "logs").mkdir(exist_ok=True)
    return home


def resolve_profile_env(profile_name: str) -> str:
    """
    Resolve a profile name to its SORA_HOME path.
    Profiles live under ~/.sora/profiles/<name>/ or as ~/.sora-<name>/.
    """
    profile_name = profile_name.strip().lower()

    # Special case: "default" -> ~/.sora/
    if profile_name == "default":
        return str(get_sora_root())

    # Check ~/.sora/profiles/<name>/
    profiles_dir = get_default_sora_root() / "profiles"
    profile_path = profiles_dir / profile_name
    if profile_path.exists():
        return str(profile_path.resolve())

    # Check ~/.sora-<name>/
    alt_path = Path.home() / f".sora-{profile_name}"
    if alt_path.exists():
        return str(alt_path.resolve())

    raise FileNotFoundError(
        f"Profile '{profile_name}' not found. "
        f"Checked ~/.sora/profiles/{profile_name}/ and ~/.sora-{profile_name}/"
    )


def apply_ipv4_preference(force: bool = False) -> None:
    """
    Apply IPv4 preference for network calls.
    If force=True or config says so, set environment to prefer IPv4.
    """
    if force:
        os.environ["SORA_FORCE_IPV4"] = "1"


def _read_config_value(key: str) -> Optional[str]:
    """Read a single value from config.yaml (best effort)."""
    try:
        import yaml
        cfg_path = get_config_path()
        if cfg_path.exists():
            with open(cfg_path, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            # Navigate dot-notation key
            parts = key.split(".")
            value = config
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return None
            return str(value) if value is not None else None
    except Exception:
        pass
    return None