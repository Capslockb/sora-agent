"""
Sora Agent — Provider Management CLI.

Allows switching between TTS, STT, Gemini Live, Vapi, ElevenLabs providers.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

from sora_cli.config import (
    cfg_get,
    cfg_set,
    get_config_path,
    load_config,
    save_config,
    get_env_value,
    save_env_value,
    remove_env_value,
)
from sora_constants import get_sora_home


# Provider definitions with their capabilities and required env vars
PROVIDERS = {
    # LLM Voice (Gemini Live, Vapi, etc.)
    "gemini-live": {
        "category": "llm_voice",
        "name": "Gemini Live API",
        "description": "Google's low-latency multimodal live voice API",
        "env_vars": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "config_keys": ["voice.gemini_live.model", "voice.gemini_live.voice"],
        "features": ["realtime", "multimodal", "function_calling"],
    },
    "vapi": {
        "category": "llm_voice",
        "name": "Vapi.ai",
        "description": "Voice AI platform for building voice agents",
        "env_vars": ["VAPI_API_KEY", "VAPI_PRIVATE_KEY"],
        "config_keys": ["voice.vapi.assistant_id", "voice.vapi.phone_number_id"],
        "features": ["phone", "sip", "web", "function_calling"],
    },
    "elevenlabs": {
        "category": "llm_voice",
        "name": "ElevenLabs Conversational AI",
        "description": "Ultra-realistic voice conversations with ElevenLabs",
        "env_vars": ["ELEVENLABS_AGENT_ID"],
        "config_keys": ["voice.elevenlabs.agent_id", "voice.elevenlabs.voice_id", "voice.elevenlabs.channel_id"],
        "features": ["realtime", "high_quality", "multilingual"],
    },

    # TTS Providers
    "edge-tts": {
        "category": "tts",
        "name": "Edge TTS (Microsoft)",
        "description": "Free, high-quality neural TTS with many voices",
        "env_vars": [],
        "config_keys": ["voice.tts.edge_tts.voice", "voice.tts.edge_tts.rate"],
        "features": ["free", "many_voices", "ssml", "streaming"],
    },
    "openai-tts": {
        "category": "tts",
        "name": "OpenAI TTS",
        "description": "OpenAI's TTS models (tts-1, tts-1-hd)",
        "env_vars": ["OPENAI_API_KEY"],
        "config_keys": ["voice.tts.openai.model", "voice.tts.openai.voice"],
        "features": ["high_quality", "streaming", "multiple_voices"],
    },
    "elevenlabs-tts": {
        "category": "tts",
        "name": "ElevenLabs TTS",
        "description": "ElevenLabs text-to-speech with voice cloning",
        "env_vars": ["ELEVENLABS_API_KEY"],
        "config_keys": ["voice.tts.elevenlabs.voice_id", "voice.tts.elevenlabs.model"],
        "features": ["voice_cloning", "high_quality", "multilingual"],
    },
    "gemini-tts": {
        "category": "tts",
        "name": "Gemini TTS",
        "description": "Google Gemini text-to-speech",
        "env_vars": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "config_keys": ["voice.tts.gemini.voice", "voice.tts.gemini.model"],
        "features": ["multimodal", "free_tier"],
    },
    "minimax-tts": {
        "category": "tts",
        "name": "MiniMax TTS",
        "description": "MiniMax speech synthesis",
        "env_vars": ["MINIMAX_API_KEY", "MINIMAX_GROUP_ID"],
        "config_keys": ["voice.tts.minimax.voice_id"],
        "features": ["chinese_optimized", "emotional"],
    },
    "mistral-tts": {
        "category": "tts",
        "name": "Mistral TTS",
        "description": "Mistral AI text-to-speech",
        "env_vars": ["MISTRAL_API_KEY"],
        "config_keys": ["voice.tts.mistral.voice"],
        "features": ["european_optimized"],
    },

    # STT Providers
    "faster-whisper": {
        "category": "stt",
        "name": "Faster Whisper (Local)",
        "description": "Optimized local Whisper inference (CPU/GPU)",
        "env_vars": [],
        "config_keys": ["voice.stt.whisper.model", "voice.stt.whisper.device", "voice.stt.whisper.compute_type"],
        "features": ["local", "offline", "multilingual", "gpu_accelerated"],
    },
    "openai-whisper": {
        "category": "stt",
        "name": "OpenAI Whisper API",
        "description": "OpenAI's hosted Whisper API",
        "env_vars": ["OPENAI_API_KEY"],
        "config_keys": ["voice.stt.openai.model"],
        "features": ["hosted", "high_accuracy", "multilingual"],
    },
    "gemini-stt": {
        "category": "stt",
        "name": "Gemini STT",
        "description": "Google Gemini speech-to-text",
        "env_vars": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "config_keys": ["voice.stt.gemini.model"],
        "features": ["multimodal", "context_aware"],
    },
}


CATEGORIES = {
    "llm_voice": "LLM Voice Bridges (realtime conversation)",
    "tts": "Text-to-Speech",
    "stt": "Speech-to-Text",
}


def list_providers(args) -> int:
    """List all available providers."""
    from sora_cli.colors import Colors, color
    from sora_cli.cli_output import print_info, print_success
    from sora_cli.setup import print_header

    config = load_config()
    current = {
        "llm_voice": cfg_get(config, "voice", "provider", default="gemini-live"),
        "tts": cfg_get(config, "voice", "tts", "provider", default="edge-tts"),
        "stt": cfg_get(config, "voice", "stt", "provider", default="faster-whisper"),
    }

    print_header("Available Voice Providers")
    print()

    for cat_key, cat_name in CATEGORIES.items():
        print(color(f"◆ {cat_name}", Colors.CYAN, Colors.BOLD))
        providers = [(k, v) for k, v in PROVIDERS.items() if v["category"] == cat_key]
        for prov_key, prov in providers:
            is_current = current.get(cat_key) == prov_key
            marker = color("●", Colors.GREEN) if is_current else color("○", Colors.DIM)
            status = ""
            if prov["env_vars"]:
                missing = [v for v in prov["env_vars"] if not get_env_value(v)]
                if missing:
                    status = color(f" (needs: {', '.join(missing)})", Colors.YELLOW)
                else:
                    status = color(" (configured)", Colors.GREEN)
            else:
                status = color(" (local)", Colors.BLUE)
            print(f"  {marker} {prov['name']} ({prov_key}){status}")
            print(f"      {prov['description']}")
        print()

    return 0


def enable_provider(args) -> int:
    """Enable a provider for a category."""
    from sora_cli.colors import Colors, color
    from sora_cli.cli_output import print_info, print_success, print_error, print_warning
    from sora_cli.setup import print_header

    provider_id = args.provider
    if provider_id not in PROVIDERS:
        print_error(f"Unknown provider: {provider_id}")
        print_info(f"Run 'sora providers list' to see available providers")
        return 1

    prov = PROVIDERS[provider_id]
    category = prov["category"]

    config = load_config()
    cfg_set(config, "voice", category, "provider", provider_id)
    save_config(config)

    missing = [v for v in prov["env_vars"] if not get_env_value(v)]
    if missing:
        print_warning(f"Provider enabled but missing env vars: {', '.join(missing)}")
        print_info("Set them with: export VAR=value or add to ~/.sora/.env")
    else:
        print_success(f"Enabled {prov['name']} for {CATEGORIES[category]}")

    return 0


def disable_provider(args) -> int:
    """Disable a provider (reset to default for category)."""
    from sora_cli.colors import Colors, color
    from sora_cli.cli_output import print_info, print_success

    category = args.category
    if category not in CATEGORIES:
        print_error(f"Invalid category: {category}. Use: {', '.join(CATEGORIES.keys())}")
        return 1

    config = load_config()
    defaults = {"llm_voice": "gemini-live", "tts": "edge-tts", "stt": "faster-whisper"}
    cfg_set(config, "voice", category, "provider", defaults.get(category))
    save_config(config)

    print_success(f"Reset {CATEGORIES[category]} to default: {defaults[category]}")
    return 0


def configure_provider(args) -> int:
    """Configure a provider's settings."""
    from sora_cli.colors import Colors, color
    from sora_cli.cli_output import print_info, print_success, print_error, print_warning
    from sora_cli.setup import print_header, prompt, prompt_yes_no

    provider_id = args.provider
    if provider_id not in PROVIDERS:
        print_error(f"Unknown provider: {provider_id}")
        return 1

    prov = PROVIDERS[provider_id]
    config = load_config()

    print_header(f"Configure {prov['name']}")
    print()

    # Check/env vars
    for env_var in prov["env_vars"]:
        current = get_env_value(env_var)
        if current:
            print_info(f"{env_var}: {'*' * 8}... (set)")
        else:
            if prompt_yes_no(f"Set {env_var}?", default=True):
                value = prompt(f"{env_var} value", password=True)
                if value:
                    save_env_value(env_var, value)
                    print_success(f"Set {env_var}")

    # Config keys
    for config_key in prov["config_keys"]:
        parts = config_key.split(".")
        current = cfg_get(config, *parts, default="")
        if current:
            print_info(f"{config_key}: {current}")

        new_val = prompt(f"{config_key} [{current}]")
        if new_val:
            d = config
            for p in parts[:-1]:
                d = d.setdefault(p, {})
            d[parts[-1]] = new_val
            print_success(f"Set {config_key}")

    save_config(config)
    print_success(f"Configuration saved for {prov['name']}")
    return 0


def status_provider(args) -> int:
    """Show current provider status."""
    from sora_cli.colors import Colors, color
    from sora_cli.cli_output import print_info, print_success
    from sora_cli.config import load_config
    from sora_cli.setup import print_header

    config = load_config()
    current = {
        "llm_voice": cfg_get(config, "voice", "provider", default="gemini-live"),
        "tts": cfg_get(config, "voice", "tts", "provider", default="edge-tts"),
        "stt": cfg_get(config, "voice", "stt", "provider", default="faster-whisper"),
    }

    print_header("Current Provider Status")
    print()

    for cat_key, cat_name in CATEGORIES.items():
        prov_name = current.get(cat_key)
        prov = PROVIDERS.get(prov_name, {})
        print(f"  {cat_name}: {color(prov.get('name', prov_name), Colors.CYAN)} ({prov_name})")

        for config_key in prov.get("config_keys", []):
            val = cfg_get(config, *config_key.split("."), default="")
            if val:
                print(f"    {config_key}: {val}")

        for env_var in prov.get("env_vars", []):
            val = get_env_value(env_var)
            status = color("✓", Colors.GREEN) if val else color("✗", Colors.RED)
            print(f"    {env_var}: {status}")
        print()

    return 0


# Import helpers from setup.py
from sora_cli.setup import (
    print_header, prompt, prompt_yes_no, Colors, color,
    print_info, print_success, print_error, print_warning,
)


def build_parser(subparsers) -> None:
    """Add provider subcommands to main parser."""
    providers_parser = subparsers.add_parser("providers", help="Manage voice providers (TTS/STT/LLM Voice)")
    providers_sub = providers_parser.add_subparsers(dest="providers_command", metavar="<subcommand>")

    # list
    list_p = providers_sub.add_parser("list", help="List all available providers")
    list_p.add_argument("-h", "--help", action="help")

    # enable
    enable_p = providers_sub.add_parser("enable", help="Enable a provider for its category")
    enable_p.add_argument("-h", "--help", action="help")
    enable_p.add_argument("provider", help="Provider name (e.g., gemini-live, vapi, edge-tts)")

    # disable
    disable_p = providers_sub.add_parser("disable", help="Disable a provider (reset category to default)")
    disable_p.add_argument("-h", "--help", action="help")
    disable_p.add_argument("category", choices=list(CATEGORIES.keys()), help="Category to reset")

    # config
    config_p = providers_sub.add_parser("config", help="Configure a provider's settings")
    config_p.add_argument("-h", "--help", action="help")
    config_p.add_argument("provider", help="Provider name")

    # status
    status_p = providers_sub.add_parser("status", help="Show current provider status")
    status_p.add_argument("-h", "--help", action="help")


def main(args) -> int:
    """Main entry point for providers command."""
    cmd = getattr(args, "providers_command", None)

    if cmd is None:
        print("Provider Management")
        print()
        print("Usage: sora providers <subcommand> [options]")
        print()
        print("Subcommands:")
        print("  list     List all available providers")
        print("  enable   Enable a provider for its category")
        print("  disable  Reset a category to default provider")
        print("  config   Configure a provider's settings")
        print("  status   Show current provider status")
        print()
        return 0

    handlers = {
        "list": list_providers,
        "enable": enable_provider,
        "disable": disable_provider,
        "config": configure_provider,
        "status": status_provider,
    }

    handler = handlers.get(cmd)
    if handler:
        return handler(args)
    else:
        print(f"Unknown subcommand: {cmd}")
        return 1