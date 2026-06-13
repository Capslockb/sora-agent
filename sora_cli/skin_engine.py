"""
S0RA CLI Skin Engine — Data-driven CLI visual customization.
Mirrors hermes_cli/skin_engine.py from Hermes Agent.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from sora_constants import get_sora_home


@dataclass(frozen=True)
class SkinConfig:
    """Complete skin configuration."""
    name: str
    description: str
    colors: Dict[str, str]
    spinner: Dict[str, Any]
    branding: Dict[str, str]
    tool_prefix: str
    tool_emojis: Dict[str, str] = field(default_factory=dict)


# Built-in skins
_BUILTIN_SKINS: Dict[str, Dict[str, Any]] = {
    "sora": {
        "name": "sora",
        "description": "S0RA Agent default — teal/amber with kawaii spinner",
        "colors": {
            "banner_border": "teal",
            "banner_title": "amber",
            "banner_accent": "teal",
            "banner_dim": "bright_black",
            "banner_text": "white",
            "response_border": "teal",
        },
        "spinner": {
            "waiting_faces": ["(◕‿◕)", "(◕ᴗ◕✿)", "(◕‿◕✿)", "(◕ᴗ◕)"],
            "thinking_faces": ["(•̀ᴗ•́)و", "(⌐■_■)", "(╭ರ_•́)", "(•̀ᴗ•́)"],
            "thinking_verbs": ["thinking", "processing", "analyzing", "synthesizing", "contemplating"],
            "wings": ["✦", "⋆", "✧", "⋆"],
        },
        "branding": {
            "agent_name": "S0RA",
            "welcome": "Your voice-first AI companion",
            "response_label": "S0RA",
            "prompt_symbol": "▸",
        },
        "tool_prefix": "┊",
        "tool_emojis": {
            "web": "🔍",
            "terminal": "⚡",
            "voice": "🎙️",
            "mcp": "🔌",
            "skills": "🎯",
            "memory": "🧠",
            "image": "🎨",
        },
    },
    "sora-dark": {
        "name": "sora-dark",
        "description": "S0RA dark mode — muted teal/gray",
        "colors": {
            "banner_border": "bright_black",
            "banner_title": "teal",
            "banner_accent": "bright_black",
            "banner_dim": "bright_black",
            "banner_text": "white",
            "response_border": "bright_black",
        },
        "spinner": {
            "waiting_faces": ["(・_・)", "(・ω・)", "(・_・)"],
            "thinking_faces": ["(・・?)", "(・_・?)", "(´・ω・`)"],
            "thinking_verbs": ["thinking", "processing", "analyzing"],
            "wings": ["", ""],
        },
        "branding": {
            "agent_name": "S0RA",
            "welcome": "Voice-first AI companion",
            "response_label": "S0RA",
            "prompt_symbol": ">",
        },
        "tool_prefix": "|",
        "tool_emojis": {},
    },
    "minimal": {
        "name": "minimal",
        "description": "Clean minimal skin — no colors, no emoji",
        "colors": {
            "banner_border": "white",
            "banner_title": "white",
            "banner_accent": "white",
            "banner_dim": "bright_black",
            "banner_text": "white",
            "response_border": "white",
        },
        "spinner": {
            "waiting_faces": [".", "..", "...", ".."],
            "thinking_faces": ["[.]", "[..]", "[...]"],
            "thinking_verbs": ["working", "processing"],
            "wings": ["", ""],
        },
        "branding": {
            "agent_name": "SORA",
            "welcome": "",
            "response_label": "SORA",
            "prompt_symbol": ">",
        },
        "tool_prefix": ">",
        "tool_emojis": {},
    },
    "hermes": {
        "name": "hermes",
        "description": "Classic Hermes gold/kawaii theme",
        "colors": {
            "banner_border": "yellow",
            "banner_title": "bright_yellow",
            "banner_accent": "yellow",
            "banner_dim": "bright_black",
            "banner_text": "white",
            "response_border": "yellow",
        },
        "spinner": {
            "waiting_faces": ["(◕‿◕)", "(◕ᴗ◕✿)", "(◕‿◕✿)", "(◕ᴗ◕)"],
            "thinking_faces": ["(•̀ᴗ•́)و", "(⌐■_■)", "(╭ರ_•́)", "(•̀ᴗ•́)"],
            "thinking_verbs": ["thinking", "processing", "analyzing", "synthesizing"],
            "wings": ["✦", "⋆", "✧", "⋆"],
        },
        "branding": {
            "agent_name": "Hermes",
            "welcome": "The self-improving AI agent",
            "response_label": "Hermes",
            "prompt_symbol": "▸",
        },
        "tool_prefix": "┊",
        "tool_emojis": {
            "web": "🔍",
            "terminal": "⚡",
            "code": "💻",
            "skills": "🎯",
        },
    },
}


_active_skin: Optional[SkinConfig] = None


def init_skin_from_config() -> SkinConfig:
    """Initialize skin from config.yaml at startup."""
    global _active_skin
    try:
        from sora_cli.config import load_raw_config
        config = load_raw_config()
        skin_name = config.get("display", {}).get("skin", "sora")
        _active_skin = load_skin(skin_name)
    except Exception:
        _active_skin = load_skin("sora")
    return _active_skin


def get_active_skin() -> SkinConfig:
    """Get the currently active skin."""
    global _active_skin
    if _active_skin is None:
        return init_skin_from_config()
    return _active_skin


def set_active_skin(name: str) -> SkinConfig:
    """Switch skin at runtime."""
    global _active_skin
    _active_skin = load_skin(name)
    # Update config
    try:
        from sora_cli.config import load_config, save_config
        config = load_config()
        config.setdefault("display", {})["skin"] = name
        save_config(config)
    except Exception:
        pass
    return _active_skin


def load_skin(name: str) -> SkinConfig:
    """Load a skin by name — user skins first, then built-ins, then default."""
    # Check user skins
    user_skins_dir = get_sora_home() / "skins"
    user_skin_path = user_skins_dir / f"{name}.yaml"
    if user_skin_path.exists():
        return _load_skin_yaml(user_skin_path)

    # Check built-ins
    if name in _BUILTIN_SKINS:
        return SkinConfig(**_BUILTIN_SKINS[name])

    # Fallback to default
    return SkinConfig(**_BUILTIN_SKINS["sora"])


def _load_skin_yaml(path: Path) -> SkinConfig:
    """Load skin from YAML file."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Merge with default for missing keys
    base = _BUILTIN_SKINS["sora"]
    for key, value in base.items():
        if key not in data:
            data[key] = value
        elif isinstance(value, dict) and isinstance(data.get(key), dict):
            # Deep merge for nested dicts
            merged = dict(value)
            merged.update(data[key])
            data[key] = merged

    return SkinConfig(**data)


def get_skin_names() -> list[str]:
    """Get list of all available skin names."""
    names = set(_BUILTIN_SKINS.keys())
    user_skins_dir = get_sora_home() / "skins"
    if user_skins_dir.exists():
        for f in user_skins_dir.glob("*.yaml"):
            names.add(f.stem)
    return sorted(names)


def create_user_skin_template(name: str) -> Path:
    """Create a user skin YAML template."""
    user_skins_dir = get_sora_home() / "skins"
    user_skins_dir.mkdir(parents=True, exist_ok=True)
    path = user_skins_dir / f"{name}.yaml"

    template = {
        "name": name,
        "description": f"Custom skin: {name}",
        "colors": _BUILTIN_SKINS["sora"]["colors"],
        "spinner": _BUILTIN_SKINS["sora"]["spinner"],
        "branding": _BUILTIN_SKINS["sora"]["branding"],
        "tool_prefix": "┊",
        "tool_emojis": {},
    }

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(template, f, sort_keys=False, allow_unicode=True)

    return path