"""
S0RA Agent Setup Wizard — Interactive configuration for Sora.

Modular wizard with independently-runnable sections:
  1. Model & Provider — choose your AI provider and model
  2. Discord Bot — configure Discord for voice bridges
  3. Voice Bridges — Gemini Live & Vapi configuration
  4. MCP — Model Context Protocol servers
  5. Memory — Honcho or local memory
  6. Tools — TTS, STT, web search, image generation

Config files are stored in ~/.sora/ for easy access.
"""

import importlib.util
import logging
import os
import re
import shutil
import sys
import copy
from pathlib import Path
from typing import Optional, Dict, Any, List

from sora_cli.config import (
    cfg_get,
    DEFAULT_CONFIG,
    get_config_path,
    get_env_path,
    load_config,
    save_config,
    save_env_value,
    remove_env_value,
    get_env_value,
    load_sora_dotenv,
)
from sora_constants import (
    ensure_sora_home as ensure_hermes_home,
    get_sora_home,
    get_config_path as _get_config_path,
    get_env_path as _get_env_path,
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

_DOCS_BASE = "https://github.com/capslockb/sora-agent/docs"


def _model_config_dict(config: Dict[str, Any]) -> Dict[str, Any]:
    current_model = config.get("model")
    if isinstance(current_model, dict):
        return dict(current_model)
    if isinstance(current_model, str) and current_model.strip():
        return {"default": current_model.strip()}
    return {}


def _current_reasoning_effort(config: Dict[str, Any]) -> str:
    agent_cfg = config.get("agent")
    if isinstance(agent_cfg, dict):
        return str(agent_cfg.get("reasoning_effort") or "").strip().lower()
    return ""


def _set_reasoning_effort(config: Dict[str, Any], effort: str) -> None:
    agent_cfg = config.get("agent")
    if not isinstance(agent_cfg, dict):
        agent_cfg = {}
        config["agent"] = agent_cfg
    agent_cfg["reasoning_effort"] = effort


from sora_cli.config import (
    get_sora_home,
    get_config_path,
    get_env_path,
    load_config,
    save_config,
    save_env_value,
    remove_env_value,
    get_env_value,
)
from sora_constants import (
    ensure_sora_home as ensure_hermes_home,
)

from sora_cli.colors import Colors, color
from sora_cli.cli_output import (
    print_error,
    print_info,
    print_success,
    print_warning,
)
from sora_cli.secret_prompt import masked_secret_prompt

# Animation helpers
_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

def _animate_spinner(message: str, duration: float = 2.0) -> None:
    """Show an animated spinner for the given duration."""
    import sys
    import time
    if not is_interactive_stdin():
        print_info(message)
        return
    
    start = time.time()
    i = 0
    while time.time() - start < duration:
        frame = _SPINNER_FRAMES[i % len(_SPINNER_FRAMES)]
        sys.stdout.write(f"\r{color(frame, Colors.CYAN)} {message}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write(f"\r{color('✓', Colors.GREEN)} {message}\n")
    sys.stdout.flush()


SORA_LOGO = color("""
    ███████╗██╗  ██╗██╗  ██╗
    ██╔════╝██║  ██║██║  ██║
    ███████╗███████║███████║
    ╚════██║██╔══██║██╔══██║
    ███████║██║  ██║██║  ██║
    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝
""", Colors.CYAN, Colors.BOLD)

def print_header(title: str):
    """Print a section header."""
    print()
    print(color(f"◆ {title}", Colors.CYAN, Colors.BOLD))


def is_interactive_stdin() -> bool:
    import sys
    stdin = getattr(sys, "stdin", None)
    if stdin is None:
        return False
    try:
        return bool(stdin.isatty())
    except Exception:
        return False


def print_noninteractive_setup_guidance(reason: str | None = None) -> None:
    print()
    print(color("⚕ Sora Setup — Non-interactive mode", Colors.CYAN, Colors.BOLD))
    print()
    if reason:
        print_info(reason)
    print_info("The interactive wizard cannot be used here.")
    print()
    print_info("Configure Sora using environment variables or config commands:")
    print_info("  sora config set model.provider openrouter")
    print_info("  sora config set model.base_url https://openrouter.ai/api/v1")
    print_info("  sora config set model.default nvidia/nemotron-3-ultra:free")
    print()
    print_info("Or set OPENROUTER_API_KEY / GEMINI_API_KEY / VAPI_API_KEY in your environment.")
    print_info("Run 'sora setup' in an interactive terminal to use the full wizard.")
    print()


def prompt(question: str, default: str = None, password: bool = False) -> str:
    if default:
        display = f"{question} [{default}]: "
    else:
        display = f"{question}: "

    try:
        if password:
            value = masked_secret_prompt(color(display, Colors.YELLOW))
        else:
            value = input(color(display, Colors.YELLOW))
        cleaned = _sanitize_pasted_input(value)
        return cleaned.strip() or default or ""
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(1)


_BRACKETED_PASTE_PATTERN = re.compile(r"\x1b\[\s*200~|\x1b\[\s*201~")


def _sanitize_pasted_input(value: str) -> str:
    if not isinstance(value, str) or not value:
        return value
    return _BRACKETED_PASTE_PATTERN.sub("", value)


def _curses_prompt_choice(question: str, choices: list, default: int = 0, description: str | None = None) -> int:
    from sora_cli.curses_ui import curses_radiolist
    return curses_radiolist(question, choices, selected=default, cancel_returns=-1, description=description)


def prompt_choice(question: str, choices: list, default: int = 0, description: str | None = None) -> int:
    idx = _curses_prompt_choice(question, choices, default, description=description)
    if idx >= 0:
        if idx == default:
            print_info("  Skipped (keeping current)")
            print()
            return default
        print()
        return idx

    print(color(question, Colors.YELLOW))
    for i, choice in enumerate(choices):
        marker = "●" if i == default else "○"
        if i == default:
            print(color(f"  {marker} {choice}", Colors.GREEN))
        else:
            print(f"  {marker} {choice}")
    print_info(f"  Enter for default ({default + 1})  Ctrl+C to exit")

    while True:
        try:
            value = input(color(f"  Select [1-{len(choices)}] ({default + 1}): ", Colors.DIM))
            if not value:
                return default
            idx = int(value) - 1
            if 0 <= idx < len(choices):
                return idx
            print_error(f"Please enter a number between 1 and {len(choices)}")
        except ValueError:
            print_error("Please enter a number")
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(1)


def prompt_yes_no(question: str, default: bool = True) -> bool:
    default_str = "Y/n" if default else "y/N"
    while True:
        try:
            value = (
                input(color(f"{question} [{default_str}]: ", Colors.YELLOW))
                .strip()
                .lower()
            )
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(1)
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print_error("Please enter 'y' or 'n'")


def prompt_checklist(title: str, items: list, pre_selected: list = None) -> list:
    if pre_selected is None:
        pre_selected = []

    from sora_cli.curses_ui import curses_checklist

    chosen = curses_checklist(
        title,
        items,
        set(pre_selected),
        cancel_returns=set(pre_selected),
    )
    return sorted(chosen)


# ---- Provider/Model Lists ----

_DEFAULT_PROVIDER_MODELS = {
    "openrouter": [
        "nvidia/nemotron-3-ultra:free",
        "google/gemini-2.5-pro-preview",
        "anthropic/claude-sonnet-4.6",
        "openai/gpt-5.4",
        "meta-llama/llama-3.3-70b-instruct",
    ],
    "gemini": [
        "gemini-3.1-pro-preview",
        "gemini-3-pro-preview",
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite-preview",
    ],
    "anthropic": [
        "claude-opus-4.6",
        "claude-sonnet-4.6",
        "claude-haiku-4.5",
    ],
    "openai": [
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5-mini",
        "gpt-4o",
        "gpt-4o-mini",
    ],
    "custom": [],
}


def _build_provider_list(config: Dict[str, Any]) -> List[tuple]:
    """Build list of (provider_key, display_name, is_available)."""
    providers = [
        ("openrouter", "OpenRouter (multi-model, free tier available)"),
        ("gemini", "Google Gemini (native, incl. Live API)"),
        ("anthropic", "Anthropic (Claude models)"),
        ("openai", "OpenAI (GPT models)"),
        ("custom", "Custom/OpenAI-compatible endpoint"),
    ]
    result = []
    for key, desc in providers:
        available = False
        if key == "openrouter":
            available = bool(get_env_value("OPENROUTER_API_KEY"))
        elif key == "gemini":
            available = bool(get_env_value("GEMINI_API_KEY") or get_env_value("GOOGLE_API_KEY"))
        elif key == "anthropic":
            available = bool(get_env_value("ANTHROPIC_API_KEY"))
        elif key == "openai":
            available = bool(get_env_value("OPENAI_API_KEY"))
        elif key == "custom":
            available = True  # Always available if user provides URL/key
        result.append((key, desc, available))
    return result


def _load_live_models(provider: str, api_key: str, base_url: str = "") -> List[str]:
    """Try to fetch live model list from provider API."""
    try:
        import httpx
        headers = {"Authorization": f"Bearer {api_key}"}
        if provider == "openrouter":
            url = "https://openrouter.ai/api/v1/models"
            resp = httpx.get(url, headers=headers, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                return [m["id"] for m in data.get("data", []) if "free" in m.get("id", "").lower() or "preview" in m.get("id", "").lower()][:20]
        elif provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            resp = httpx.get(url, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                return [m["name"].split("/")[-1] for m in data.get("models", []) if "gemini" in m.get("name", "").lower()][:20]
    except Exception:
        pass
    return _DEFAULT_PROVIDER_MODELS.get(provider, [])


# ---- Wizard Sections ----

def wizard_model_provider(config: Dict[str, Any]) -> Dict[str, Any]:
    """Section 1: Model & Provider."""
    print_header("1. Model & Provider")
    print_info("Choose your AI provider. Sora works best with providers that support:")
    print_info("  • Function calling / tools")
    print_info("  • Streaming responses")
    print_info("  • Reasoning models (for complex tasks)")
    print()

    providers = _build_provider_list(config)
    current_provider = cfg_get(config, "model", "provider", default="openrouter")
    current_model = cfg_get(_model_config_dict(config), "default", default="")

    # Show current
    curr_desc = next((d for k, d, _ in providers if k == current_provider), current_provider)
    print_info(f"Current: {curr_desc} | Model: {current_model or '(auto)'}")
    print()

    # Provider selection
    choices = [f"{'✓ ' if avail else '  '}{desc} ({key})" for key, desc, avail in providers]
    default_idx = next((i for i, (k, _, _) in enumerate(providers) if k == current_provider), 0)

    idx = prompt_choice("Select provider", choices, default=default_idx,
                       description="Providers with ✓ have API keys configured")
    selected_key = providers[idx][0]

    if selected_key != current_provider:
        config["model"]["provider"] = selected_key
        # Clear model when provider changes
        if "model" in config and isinstance(config["model"], dict):
            config["model"]["default"] = ""

    # API Key setup if needed
    if selected_key in {"openrouter", "gemini", "anthropic", "openai"}:
        env_var = {
            "openrouter": "OPENROUTER_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
        }[selected_key]

        if not get_env_value(env_var):
            print()
            print_info(f"No {env_var} found. You'll need one to use {selected_key}.")
            if prompt_yes_no("Enter API key now?"):
                _prompt_api_key({
                    "name": env_var,
                    "description": f"{selected_key.title()} API Key",
                    "prompt": f"{selected_key.title()} API Key",
                    "url": {
                        "openrouter": "https://openrouter.ai/keys",
                        "gemini": "https://aistudio.google.com/apikey",
                        "anthropic": "https://console.anthropic.com/settings/keys",
                        "openai": "https://platform.openai.com/api-keys",
                    }[selected_key],
                    "password": True,
                    "tools": ["chat", "tools", "voice"],
                })

    # Model selection
    if selected_key != "custom":
        api_key = get_env_value({
            "openrouter": "OPENROUTER_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
        }.get(selected_key, ""))

        if api_key:
            print()
            print_info("Fetching available models...")
            models = _load_live_models(selected_key, api_key)
            if models:
                print_info(f"Found {len(models)} models")
            else:
                models = _DEFAULT_PROVIDER_MODELS.get(selected_key, [])
        else:
            models = _DEFAULT_PROVIDER_MODELS.get(selected_key, [])

        if models:
            model_choices = [f"{m}" for m in models[:15]]
            model_choices.append("Other (enter manually)")
            default_model_idx = 0
            if current_model in models:
                default_model_idx = models.index(current_model)

            idx = prompt_choice("Select model", model_choices, default=default_model_idx)
            if idx < len(models):
                config["model"]["default"] = models[idx]
            else:
                custom = prompt("Enter model identifier")
                if custom:
                    config["model"]["default"] = custom
    else:
        # Custom endpoint
        base_url = prompt("Base URL (e.g. http://localhost:8080/v1)",
                         default=cfg_get(config, "model", "base_url", default=""))
        if base_url:
            config["model"]["base_url"] = base_url
        api_key = prompt("API Key (optional)", password=True)
        if api_key:
            save_env_value("CUSTOM_API_KEY", api_key)
        model = prompt("Model identifier")
        if model:
            config["model"]["default"] = model

    # Reasoning effort
    print()
    reasoning_choices = ["none", "minimal", "low", "medium", "high", "xhigh"]
    current_effort = _current_reasoning_effort(config) or "medium"
    default_idx = reasoning_choices.index(current_effort) if current_effort in reasoning_choices else 3
    idx = prompt_choice("Reasoning effort", reasoning_choices, default=default_idx)
    _set_reasoning_effort(config, reasoning_choices[idx])

    print()
    print_success("✓ Model & Provider configured")
    return config


def wizard_discord(config: Dict[str, Any]) -> Dict[str, Any]:
    """Section 2: Discord Bot Configuration."""
    print_header("2. Discord Bot (for Voice Bridges)")
    print_info("Sora's voice bridges (Gemini Live & Vapi) run on Discord.")
    print_info("You need a Discord bot token and application ID.")
    print()

    current_token = get_env_value("DISCORD_BOT_TOKEN", "")
    current_app_id = get_env_value("DISCORD_APPLICATION_ID", "")
    current_guild = cfg_get(config, "voice", "discord", "guild_id", default="")
    current_user = cfg_get(config, "voice", "discord", "default_user_id", default="")

    if current_token:
        print_info(f"Bot token: {'*' * 20}... (configured)")
    else:
        print_warning("Bot token: NOT CONFIGURED")
    if current_app_id:
        print_info(f"Application ID: {current_app_id}")
    else:
        print_warning("Application ID: NOT CONFIGURED")

    print()
    if not current_token or not current_app_id:
        print_info("Create a bot at: https://discord.com/developers/applications")
        print_info("  1. New Application → Bot → Reset Token (copy)")
        print_info("  2. General Information → Application ID (copy)")
        print_info("  3. Enable 'Message Content Intent' and 'Server Members Intent'")
        print_info("  4. Invite bot to your server with 'Manage Channels', 'Connect', 'Speak' permissions")
        print()

    if prompt_yes_no("Configure Discord bot now?", default=bool(not current_token)):
        token = prompt("Bot Token", password=True)
        if token:
            save_env_value("DISCORD_BOT_TOKEN", token)
            config.setdefault("voice", {}).setdefault("discord", {})["bot_token"] = "***"

        app_id = prompt("Application ID")
        if app_id:
            save_env_value("DISCORD_APPLICATION_ID", app_id)
            config.setdefault("voice", {}).setdefault("discord", {})["application_id"] = app_id

        guild = prompt("Default Guild/Server ID (optional)", default=current_guild)
        if guild:
            config.setdefault("voice", {}).setdefault("discord", {})["guild_id"] = guild

        user = prompt("Default User ID (to auto-find voice channel)", default=current_user)
        if user:
            config.setdefault("voice", {}).setdefault("discord", {})["default_user_id"] = user

    print()
    print_success("✓ Discord configured")
    return config


def wizard_voice_bridges(config: Dict[str, Any]) -> Dict[str, Any]:
    """Section 3: Voice Bridges — all 7 providers."""
    print_header("3. Voice Bridges")
    print_info("Sora supports 7 voice bridge backends:")
    print_info("  • Gemini Live — Direct streaming to Google's multimodal live API")
    print_info("  • Vapi.ai — Managed conversational AI platform")
    print_info("  • ElevenLabs — Ultra-realistic voice conversations")
    print_info("  • OpenAI Realtime — WebRTC-based realtime voice API")
    print_info("  • xAI Grok — xAI's realtime voice API")
    print_info("  • Ultravox — Managed STT/LLM/TTS pipeline")
    print_info("  • Retell AI — Telephony and web call voice agents")
    print()
    print_info("You can set up individual providers with: sora setup --provider <name>")
    print()

    # Gemini Live
    gemini_enabled = cfg_get(config, "voice", "gemini_live", "enabled", default=True)
    gemini_model = cfg_get(config, "voice", "gemini_live", "model", default="gemini-3.1-flash-live-preview")
    gemini_voice = cfg_get(config, "voice", "gemini_live", "voice", default="Kore")
    gemini_key = get_env_value("GEMINI_API_KEY") or get_env_value("GOOGLE_API_KEY")

    print_info(f"Gemini Live: {'Enabled' if gemini_enabled else 'Disabled'}")
    if gemini_key:
        print_info(f"  API Key: {'*' * 20}... (configured)")
    else:
        print_warning("  API Key: NOT CONFIGURED (needs GEMINI_API_KEY or GOOGLE_API_KEY)")
    print_info(f"  Model: {gemini_model}")
    print_info(f"  Voice: {gemini_voice}")

    print()
    if not gemini_key and prompt_yes_no("Configure Gemini Live API key?", default=True):
        print_info("Get your key at: https://aistudio.google.com/apikey")
        key = prompt("GEMINI_API_KEY (or GOOGLE_API_KEY)", password=True)
        if key:
            save_env_value("GEMINI_API_KEY", key)

    if prompt_yes_no("Enable Gemini Live voice bridge?", default=gemini_enabled):
        config.setdefault("voice", {}).setdefault("gemini_live", {})["enabled"] = True

        model = prompt("Model", default=gemini_model)
        if model:
            config["voice"]["gemini_live"]["model"] = model

        voice_choices = ["Kore", "Puck", "Charon", "Aoede", "Fenrir", "Leda", "Orus", "Zephyr"]
        idx = prompt_choice("Voice", voice_choices, default=voice_choices.index(gemini_voice) if gemini_voice in voice_choices else 0)
        config["voice"]["gemini_live"]["voice"] = voice_choices[idx]

    # Vapi
    print()
    vapi_enabled = cfg_get(config, "voice", "vapi", "enabled", default=True)
    vapi_assistant = cfg_get(config, "voice", "vapi", "assistant_id", default="")
    vapi_key = get_env_value("VAPI_API_KEY", "")

    print_info(f"Vapi.ai: {'Enabled' if vapi_enabled else 'Disabled'}")
    if vapi_key:
        print_info(f"  API Key: {'*' * 20}... (configured)")
    else:
        print_warning("  API Key: NOT CONFIGURED (needs VAPI_API_KEY)")
    if vapi_assistant:
        print_info(f"  Assistant ID: {vapi_assistant}")

    print()
    if not vapi_key and prompt_yes_no("Configure Vapi API key?", default=True):
        print_info("Get your key at: https://dashboard.vapi.ai/api-keys")
        key = prompt("VAPI_API_KEY", password=True)
        if key:
            save_env_value("VAPI_API_KEY", key)

    if prompt_yes_no("Enable Vapi voice bridge?", default=vapi_enabled):
        config.setdefault("voice", {}).setdefault("vapi", {})["enabled"] = True

        assistant = prompt("Assistant ID (create at dashboard.vapi.ai)", default=vapi_assistant)
        if assistant:
            config["voice"]["vapi"]["assistant_id"] = assistant

        phone = prompt("Phone Number ID (for phone calls, optional)", default=cfg_get(config, "voice", "vapi", "phone_number_id", default=""))
        if phone:
            config["voice"]["vapi"]["phone_number_id"] = phone

    print()
    print_success("✓ Voice Bridges configured")
    return config


def wizard_voip(config: Dict[str, Any]) -> Dict[str, Any]:
    """Section 3b: VOIP / Asterisk + Dograh Integration."""
    print_header("3b. VOIP Integration (Asterisk + Dograh)")
    print_info("Connect Sora to your phone system via Asterisk ARI and Dograh/Gemini Live.")
    print_info("This enables inbound/outbound phone calls with AI conversation.")
    print()

    voip_config = config.setdefault("voip", {})

    # Asterisk ARI
    print_subheader("Asterisk ARI Configuration")
    ari_url = cfg_get(voip_config, "asterisk_ari_url", default="http://localhost:8088/ari")
    ari_user = cfg_get(voip_config, "asterisk_username", default="sora")
    ari_pass = cfg_get(voip_config, "asterisk_password", default="")

    print_info(f"ARI URL: {ari_url}")
    print_info(f"Username: {ari_user}")
    print_info(f"Password: {'*' * len(ari_pass) if ari_pass else 'NOT SET'}")

    if prompt_yes_no("Configure Asterisk ARI connection?", default=bool(ari_pass)):
        url = prompt("ARI URL (e.g., http://asterisk:8088/ari)", default=ari_url)
        if url:
            voip_config["asterisk_ari_url"] = url

        user = prompt("ARI Username", default=ari_user)
        if user:
            voip_config["asterisk_username"] = user

        passwd = prompt("ARI Password", password=True)
        if passwd:
            voip_config["asterisk_password"] = passwd

        app = prompt("ARI Application Name", default=cfg_get(voip_config, "asterisk_app_name", default="sora-bridge"))
        if app:
            voip_config["asterisk_app_name"] = app

    # Dograh / Gemini Live
    print()
    print_subheader("Dograh / Gemini Live Configuration")
    dograh_url = cfg_get(voip_config, "dograh_ws_url", default="wss://dograh.local/ws")
    dograh_key = cfg_get(voip_config, "dograh_api_key", default="")
    gemini_model = cfg_get(voip_config, "gemini_model", default="gemini-2.0-flash-exp")

    print_info(f"Dograh WS URL: {dograh_url}")
    print_info(f"Dograh API Key: {'*' * len(dograh_key) if dograh_key else 'NOT SET'}")
    print_info(f"Gemini Model: {gemini_model}")

    if prompt_yes_no("Configure Dograh connection?", default=bool(dograh_key)):
        url = prompt("Dograh WebSocket URL (e.g., wss://dograh.local/ws)", default=dograh_url)
        if url:
            voip_config["dograh_ws_url"] = url

        key = prompt("Dograh API Key", password=True)
        if key:
            voip_config["dograh_api_key"] = key

        model = prompt("Gemini Model", default=gemini_model)
        if model:
            voip_config["gemini_model"] = model

    # Audio / RTP settings
    print()
    print_subheader("Audio & RTP Settings")
    sample_rate = cfg_get(voip_config, "sample_rate", default=48000)
    rtp_range = cfg_get(voip_config, "rtp_port_range", default="10000-20000")
    auto_answer = cfg_get(voip_config, "auto_answer", default=True)
    record_calls = cfg_get(voip_config, "record_calls", default=False)

    print_info(f"Sample Rate: {sample_rate} Hz")
    print_info(f"RTP Port Range: {rtp_range}")
    print_info(f"Auto Answer: {'Yes' if auto_answer else 'No'}")
    print_info(f"Record Calls: {'Yes' if record_calls else 'No'}")

    if prompt_yes_no("Adjust audio/RTP settings?", default=False):
        rate = prompt_int("Sample Rate (8000/16000/48000)", default=sample_rate)
        if rate:
            voip_config["sample_rate"] = rate

        rng = prompt("RTP Port Range (e.g., 10000-20000)", default=rtp_range)
        if rng:
            voip_config["rtp_port_range"] = rng

        aa = prompt_yes_no("Auto-answer inbound calls?", default=auto_answer)
        voip_config["auto_answer"] = aa

        rc = prompt_yes_no("Record all calls by default?", default=record_calls)
        voip_config["record_calls"] = rc

    print()
    print_success("✓ VOIP Integration configured")
    return config


def wizard_mcp(config: Dict[str, Any]) -> Dict[str, Any]:
    """Section 4: MCP (Model Context Protocol)."""
    print_header("4. MCP — Model Context Protocol")
    print_info("MCP lets Sora connect to external tools and data sources.")
    print_info("Examples: filesystem, GitHub, databases, browser automation, etc.")
    print()

    mcp_enabled = cfg_get(config, "mcp", "enabled", default=True)
    servers = cfg_get(config, "mcp", "servers", default={})

    print_info(f"MCP: {'Enabled' if mcp_enabled else 'Disabled'}")
    if servers:
        print_info(f"Configured servers: {', '.join(servers.keys())}")
    else:
        print_info("No MCP servers configured yet")

    # Auto-detect running MCP servers on device
    print()
    _animate_spinner("Scanning for running MCP servers...", 1.5)
    detected = _detect_mcp_servers()
    if detected:
        print_success(f"✓ Found running MCP servers: {', '.join(detected.keys())}")
        for name, info in detected.items():
            print_info(f"  • {name}: {info['description']} (port {info.get('port', '?')})")
            if name not in servers and prompt_yes_no(f"  Add {name} to Sora config?", default=True):
                servers[name] = info
    else:
        print_info("No running MCP servers detected")

    print()

    # Common MCP servers to suggest
    common_servers = {
        "filesystem": "Local filesystem access (read/write files)",
        "github": "GitHub API (repos, issues, PRs)",
        "postgres": "PostgreSQL database",
        "sqlite": "SQLite database",
        "browser": "Browser automation (Playwright)",
        "slack": "Slack workspace",
        "notion": "Notion workspace",
        "google-drive": "Google Drive",
        "memory": "Persistent memory/knowledge graph",
    }

    if not servers and prompt_yes_no("Add common MCP servers now?", default=True):
        choices = [f"{name} — {desc}" for name, desc in common_servers.items()]
        selected = prompt_checklist("Select MCP servers to configure", choices)

        for idx in selected:
            name = list(common_servers.keys())[idx]
            if name == "filesystem":
                path = prompt("  Allowed directory path", default=str(Path.home()))
                servers[name] = {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", path]}
            elif name == "github":
                token = prompt("  GitHub token (optional, for private repos)", password=True)
                args = ["-y", "@modelcontextprotocol/server-github"]
                if token:
                    save_env_value("GITHUB_TOKEN", token)
                servers[name] = {"command": "npx", "args": args}
            elif name == "sqlite":
                db_path = prompt("  Database path", default="~/.sora/mcp.sqlite")
                servers[name] = {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-sqlite", db_path]}
            elif name == "postgres":
                conn = prompt("  Connection string (postgresql://...)", password=True)
                if conn:
                    save_env_value("POSTGRES_CONNECTION", conn)
                servers[name] = {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-postgres"]}
            elif name == "browser":
                servers[name] = {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-playwright"]}
            else:
                print_info(f"  {name}: Configure manually in ~/.sora/config.yaml later")

    config.setdefault("mcp", {})["enabled"] = mcp_enabled
    config["mcp"]["servers"] = servers

    print()
    print_success("✓ MCP configured")
    return config


def wizard_memory(config: Dict[str, Any]) -> Dict[str, Any]:
    """Section 5: Memory (Honcho or Local)."""
    print_header("5. Memory")
    print_info("Sora uses Honcho for persistent, cross-session memory.")
    print_info("Honcho runs as a local service (default: http://localhost:8377).")
    print()

    honcho_enabled = cfg_get(config, "honcho", "enabled", default=True)
    honcho_host = cfg_get(config, "honcho", "host", default="http://localhost:8377")
    memory_provider = cfg_get(config, "memory", "provider", default="honcho")

    print_info(f"Provider: {memory_provider}")
    print_info(f"Honcho: {'Enabled' if honcho_enabled else 'Disabled'}")
    print_info(f"Honcho Host: {honcho_host}")

    print()
    if prompt_yes_no("Use Honcho for memory?", default=honcho_enabled):
        config.setdefault("honcho", {})["enabled"] = True
        config.setdefault("memory", {})["provider"] = "honcho"

        host = prompt("Honcho host URL", default=honcho_host)
        if host:
            config["honcho"]["host"] = host
            config["memory"]["honcho"]["host"] = host
    else:
        config.setdefault("honcho", {})["enabled"] = False
        config.setdefault("memory", {})["provider"] = "local"

    print()
    print_success("✓ Memory configured")
    return config


def wizard_tools(config: Dict[str, Any]) -> Dict[str, Any]:
    """Section 6: Tools — TTS, STT, Web Search, Image Gen."""
    print_header("6. Tools")
    print_info("Configure optional tool backends.")
    print()

    # TTS
    print_header("6a. Text-to-Speech")
    tts_provider = cfg_get(config, "tts", "provider", default="edge")
    tts_voice = cfg_get(config, "tts", "voice", default="en-US-AriaNeural")

    tts_choices = [
        ("edge", "Edge TTS (free, Microsoft voices)", "edge-tts"),
        ("elevenlabs", "ElevenLabs (premium, best quality)", "elevenlabs"),
        ("openai", "OpenAI TTS", "openai"),
        ("minimax", "MiniMax TTS", "minimax-tts"),
        ("mistral", "Mistral Voxtral", "mistral-tts"),
        ("gemini", "Google Gemini TTS", "gemini-tts"),
    ]

    print_info(f"Current: {tts_provider} ({tts_voice})")
    print()

    choices = [f"{'✓ ' if get_env_value({'edge': '', 'elevenlabs': 'ELEVENLABS_API_KEY', 'openai': 'OPENAI_API_KEY', 'minimax': 'MINIMAX_API_KEY', 'mistral': 'MISTRAL_API_KEY', 'gemini': 'GEMINI_API_KEY'}.get(key, '')) else '  '}{desc} ({key})" for key, desc, _ in tts_choices]
    default_idx = next((i for i, (k, _, _) in enumerate(tts_choices) if k == tts_provider), 0)
    idx = prompt_choice("Select TTS provider", choices, default=default_idx)
    selected_tts = tts_choices[idx][0]

    if selected_tts != tts_provider:
        config.setdefault("tts", {})["provider"] = selected_tts

    # TTS-specific API key
    tts_keys = {"elevenlabs": "ELEVENLABS_API_KEY", "openai": "OPENAI_API_KEY", "minimax": "MINIMAX_API_KEY", "mistral": "MISTRAL_API_KEY", "gemini": "GEMINI_API_KEY"}
    if selected_tts in tts_keys and not get_env_value(tts_keys[selected_tts]):
        if prompt_yes_no(f"Enter {tts_keys[selected_tts]}?", default=True):
            key = prompt(f"{tts_keys[selected_tts]}", password=True)
            if key:
                save_env_value(tts_keys[selected_tts], key)

    # Voice selection for Edge
    if selected_tts == "edge":
        edge_voices = ["en-US-AriaNeural", "en-US-GuyNeural", "en-GB-SoniaNeural", "en-GB-RyanNeural", "en-AU-NatashaNeural", "en-AU-WilliamNeural"]
        idx = prompt_choice("Voice", edge_voices, default=edge_voices.index(tts_voice) if tts_voice in edge_voices else 0)
        config["tts"]["voice"] = edge_voices[idx]

    # STT
    print()
    print_header("6b. Speech-to-Text")
    stt_provider = cfg_get(config, "stt", "provider", default="faster-whisper")
    print_info(f"Current: {stt_provider}")

    stt_choices = [
        ("faster-whisper", "Faster-Whisper (local, fast, good quality)", "faster-whisper"),
        ("openai", "OpenAI Whisper API", "openai"),
        ("gemini", "Google Gemini (audio input)", "gemini"),
    ]
    choices = [f"{'✓ ' if get_env_value({'openai': 'OPENAI_API_KEY', 'gemini': 'GEMINI_API_KEY'}.get(k, '')) else '  '}{desc} ({key})" for key, desc, _ in stt_choices]
    default_idx = next((i for i, (k, _, _) in enumerate(stt_choices) if k == stt_provider), 0)
    idx = prompt_choice("Select STT provider", choices, default=default_idx)
    selected_stt = stt_choices[idx][0]
    if selected_stt != stt_provider:
        config.setdefault("stt", {})["provider"] = selected_stt

    # Web Search
    print()
    print_header("6c. Web Search")
    web_providers = {
        "exa": "EXA_API_KEY",
        "firecrawl": "FIRECRAWL_API_KEY",
        "parallel-web": "PARALLEL_API_KEY",
        "tavily": "TAVILY_API_KEY",
        "searxng": "SEARXNG_URL",
    }

    configured = [k for k, v in web_providers.items() if get_env_value(v)]
    print_info(f"Configured: {', '.join(configured) if configured else 'None'}")

    if prompt_yes_no("Add web search provider?", default=not configured):
        choices = list(web_providers.keys())
        idx = prompt_choice("Select provider", choices)
        provider = choices[idx]
        env_var = web_providers[provider]
        if env_var:
            val = prompt(f"{env_var}", password=True)
            if val:
                save_env_value(env_var, val)

    # Image Generation
    print()
    print_header("6d. Image Generation")
    img_providers = {
        "fal": "FAL_KEY",
        "openai": "OPENAI_API_KEY",
    }
    configured = [k for k, v in img_providers.items() if get_env_value(v)]
    print_info(f"Configured: {', '.join(configured) if configured else 'None'}")

    if prompt_yes_no("Add image generation provider?", default=not configured):
        choices = list(img_providers.keys())
        idx = prompt_choice("Select provider", choices)
        provider = choices[idx]
        env_var = img_providers[provider]
        if env_var:
            val = prompt(f"{env_var}", password=True)
            if val:
                save_env_value(env_var, val)

    print()
    print_success("✓ Tools configured")
    return config


def _prompt_api_key(var: dict):
    tools = var.get("tools", [])
    tools_str = ", ".join(tools[:3])
    if len(tools) > 3:
        tools_str += f", +{len(tools) - 3} more"

    print()
    print(color(f"  ─── {var.get('description', var['name'])} ───", Colors.CYAN))
    print()
    if tools_str:
        print_info(f"  Enables: {tools_str}")
    if var.get("url"):
        print_info(f"  Get your key at: {var['url']}")
    print()

    if var.get("password"):
        value = prompt(f"  {var.get('prompt', var['name'])}", password=True)
    else:
        value = prompt(f"  {var.get('prompt', var['name'])}")

    if value:
        save_env_value(var["name"], value)
        print_success("  ✓ Saved")
    else:
        print_warning("  Skipped (configure later with 'sora setup')")


def _print_setup_summary(config: dict):
    """Print the setup completion summary."""
    print()
    print_header("Setup Complete — Tool Availability Summary")

    tool_status = []

    # Vision
    try:
        from agent.auxiliary_client import get_available_vision_backends
        _vision_backends = get_available_vision_backends()
    except Exception:
        _vision_backends = []

    if _vision_backends:
        tool_status.append(("Vision (image analysis)", True, None))
    else:
        tool_status.append(("Vision (image analysis)", False, "run 'sora setup' to configure"))

    # Web Search
    web_keys = ["EXA_API_KEY", "PARALLEL_API_KEY", "FIRECRAWL_API_KEY", "TAVILY_API_KEY", "SEARXNG_URL"]
    if any(get_env_value(k) for k in web_keys):
        tool_status.append(("Web Search & Extract", True, None))
    else:
        tool_status.append(("Web Search & Extract", False, "EXA_API_KEY, PARALLEL_API_KEY, FIRECRAWL_API_KEY, TAVILY_API_KEY, or SEARXNG_URL"))

    # MCP
    try:
        import mcp
        tool_status.append(("MCP Client", True, None))
    except ImportError:
        tool_status.append(("MCP Client", False, "pip install mcp"))

    # Image Generation
    if get_env_value("FAL_KEY") or get_env_value("OPENAI_API_KEY"):
        tool_status.append(("Image Generation", True, None))
    else:
        tool_status.append(("Image Generation", False, "FAL_KEY or OPENAI_API_KEY"))

    # TTS
    tts_provider = cfg_get(config, "tts", "provider", default="edge")
    tts_keys = {"edge": True, "elevenlabs": "ELEVENLABS_API_KEY", "openai": "OPENAI_API_KEY",
                "minimax": "MINIMAX_API_KEY", "mistral": "MISTRAL_API_KEY", "gemini": "GEMINI_API_KEY"}
    if tts_keys.get(tts_provider, False):
        tool_status.append((f"Text-to-Speech ({tts_provider})", True, None))
    else:
        tool_status.append((f"Text-to-Speech ({tts_provider})", False, tts_keys.get(tts_provider, "API key")))

    # Voice Bridges
    gemini_key = get_env_value("GEMINI_API_KEY") or get_env_value("GOOGLE_API_KEY")
    vapi_key = get_env_value("VAPI_API_KEY")
    discord_token = get_env_value("DISCORD_BOT_TOKEN")

    if gemini_key and discord_token:
        tool_status.append(("Gemini Live Voice Bridge", True, None))
    else:
        missing = []
        if not gemini_key: missing.append("GEMINI_API_KEY")
        if not discord_token: missing.append("DISCORD_BOT_TOKEN")
        tool_status.append(("Gemini Live Voice Bridge", False, ", ".join(missing)))

    if vapi_key and discord_token:
        tool_status.append(("Vapi Voice Bridge", True, None))
    else:
        missing = []
        if not vapi_key: missing.append("VAPI_API_KEY")
        if not discord_token: missing.append("DISCORD_BOT_TOKEN")
        tool_status.append(("Vapi Voice Bridge", False, ", ".join(missing)))

    # Print table
    print()
    for name, available, hint in tool_status:
        status = color("✓", Colors.GREEN) if available else color("✗", Colors.RED)
        hint_str = f"  ({hint})" if hint else ""
        print(f"  {status}  {name}{hint_str}")

    print()
    print_info("Run 'sora chat' to start, or 'sora voice live' to launch a voice bridge.")
    print_info("Config saved to ~/.sora/config.yaml, secrets to ~/.sora/.env")


def main(args) -> int:
    """Main entry point for sora setup."""
    if not is_interactive_stdin():
        print_noninteractive_setup_guidance("stdin is not a terminal")
        return 1

    # Ensure sora home exists
    ensure_hermes_home()

    # Load existing config
    config = load_config()

    # Check for OpenClaw migration
    _check_openclaw_migration(config)

    # If --provider is specified, jump directly to provider setup
    provider = getattr(args, "provider", None)
    if provider:
        return _setup_single_provider(provider, config)

    print()
    print(SORA_LOGO)
    print(color("═══ S0RA Agent Setup ═══", Colors.CYAN, Colors.BOLD))
    print(color("Welcome! Let's configure your Sora voice agent.", Colors.CYAN))
    print()

    # Run wizard sections
    config = wizard_model_provider(config)
    config = wizard_discord(config)
    config = wizard_voice_bridges(config)
    config = wizard_voip(config)
    config = wizard_mcp(config)
    config = wizard_memory(config)
    config = wizard_tools(config)

    # OpenWakeWord setup
    config = wizard_wake_word(config)

    # Save
    save_config(config)
    print()
    _print_setup_summary(config)

    return 0


def _migrate_from_openclaw(config: Dict[str, Any]) -> None:
    """Migrate settings from OpenClaw."""
    import json
    import shutil
    
    openclaw_path = Path.home() / ".openclaw"
    
    # Migrate config
    openclaw_config = openclaw_path / "config.yaml"
    if openclaw_config.exists():
        try:
            import yaml
            with open(openclaw_config, encoding="utf-8") as f:
                oc_config = yaml.safe_load(f) or {}
            
            # Migrate model settings
            if "model" in oc_config:
                config["model"] = oc_config["model"]
                print_success("✓ Migrated model configuration")
            
            # Migrate Discord settings
            if "discord" in oc_config:
                config.setdefault("voice", {})["discord"] = oc_config["discord"]
                print_success("✓ Migrated Discord configuration")
            
            # Migrate MCP settings
            if "mcp" in oc_config:
                config["mcp"] = oc_config["mcp"]
                print_success("✓ Migrated MCP configuration")
                
        except Exception as e:
            print_warning(f"Failed to migrate config: {e}")
    
    # Migrate .env (secrets)
    openclaw_env = openclaw_path / ".env"
    if openclaw_env.exists():
        try:
            # Copy .env to sora
            target_env = Path.home() / ".sora" / ".env"
            shutil.copy2(openclaw_env, target_env)
            print_success("✓ Migrated API keys and secrets")
        except Exception as e:
            print_warning(f"Failed to migrate secrets: {e}")
    
    # Migrate skills
    openclaw_skills = openclaw_path / "skills"
    if openclaw_skills.exists():
        sora_skills = Path.home() / ".sora" / "skills"
        try:
            if not sora_skills.exists():
                sora_skills.mkdir(parents=True)
            for skill_dir in openclaw_skills.iterdir():
                if skill_dir.is_dir():
                    dest = sora_skills / skill_dir.name
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(skill_dir, dest)
            print_success("✓ Migrated skills")
        except Exception as e:
            print_warning(f"Failed to migrate skills: {e}")


PROVIDER_MAP = {
    "gemini-live": {"env": "GEMINI_API_KEY", "key_url": "https://aistudio.google.com/apikey", "provider": "Gemini Live"},
    "vapi": {"env": "VAPI_API_KEY", "key_url": "https://dashboard.vapi.ai/api-keys", "provider": "Vapi.ai"},
    "elevenlabs": {"env": "ELEVENLABS_AGENT_ID", "key_url": "https://elevenlabs.io/app/conversational-ai", "provider": "ElevenLabs"},
    "openai-realtime": {"env": "OPENAI_API_KEY", "key_url": "https://platform.openai.com/api-keys", "provider": "OpenAI Realtime"},
    "xai-grok": {"env": "XAI_API_KEY", "key_url": "https://x.ai/api", "provider": "xAI Grok"},
    "ultravox": {"env": "ULTRAVOX_API_KEY", "key_url": "https://docs.ultravox.ai", "provider": "Ultravox"},
    "retell": {"env": "RETELL_API_KEY", "key_url": "https://docs.retellai.com", "provider": "Retell AI"},
}


def _setup_single_provider(provider: str, config: Dict[str, Any]) -> int:
    """Quick-setup a single voice provider via sora setup --provider <name>."""
    info = PROVIDER_MAP.get(provider)
    if not info:
        print_error(f"Unknown provider: {provider}")
        print_info("Available: gemini-live, vapi, elevenlabs, openai-realtime, xai-grok, ultravox, retell")
        return 1

    print()
    print_header(f"Setup: {info['provider']}")
    print_info(f"Configure the {info['provider']} voice bridge.")
    print()

    key = get_env_value(info["env"])
    if key:
        print_info(f"API key: {'*' * 12}... (configured)")
    else:
        print_warning(f"API key: NOT CONFIGURED (needs {info['env']})")
        print_info(f"Get your key at: {info['key_url']}")
        print()
        if prompt_yes_no("Enter API key now?", default=True):
            val = prompt(info["env"], password=True)
            if val:
                save_env_value(info["env"], val)

    # Provider-specific extra config
    if provider == "elevenlabs":
        agent_id = prompt("ElevenLabs Agent ID", default=get_env_value("ELEVENLABS_AGENT_ID") or "")
        if agent_id:
            save_env_value("ELEVENLABS_AGENT_ID", agent_id)
    elif provider == "retell":
        agent_id = prompt("Retell Agent ID", default=get_env_value("RETELL_AGENT_ID") or "")
        if agent_id:
            save_env_value("RETELL_AGENT_ID", agent_id)

    save_config(config)
    print()
    print_success(f"✓ {info['provider']} configured")
    return 0


def wizard_wake_word(config: Dict[str, Any]) -> Dict[str, Any]:
    """Setup OpenWakeWord for 'Hey Sora' wake word detection."""
    print_header("Wake Word Detection (OpenWakeWord)")
    print_info("OpenWakeWord enables hands-free 'Hey Sora' activation.")
    print_info("This runs locally on your device — no cloud required.")
    print()
    
    wake_enabled = cfg_get(config, "voice", "wake_word", "enabled", default=False)
    wake_model = cfg_get(config, "voice", "wake_word", "model", default="hey_sora")
    
    print_info(f"Wake Word: {'Enabled' if wake_enabled else 'Disabled'}")
    if wake_enabled:
        print_info(f"  Model: {wake_model}")
    
    print()
    if prompt_yes_no("Enable 'Hey Sora' wake word detection?", default=False):
        _animate_spinner("Installing OpenWakeWord...", 3.0)
        try:
            import subprocess
            result = subprocess.run(
                ["pip", "install", "openwakeword", "onnxruntime"],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                config.setdefault("voice", {}).setdefault("wake_word", {})["enabled"] = True
                config["voice"]["wake_word"]["model"] = prompt(
                    "Wake word model", default="hey_sora"
                )
                print_success("✓ OpenWakeWord installed and enabled")
            else:
                print_error(f"Installation failed: {result.stderr}")
        except Exception as e:
            print_error(f"Failed to install: {e}")
    else:
        config.setdefault("voice", {}).setdefault("wake_word", {})["enabled"] = False
    
    return config


def _detect_mcp_servers() -> Dict[str, Any]:
    """Detect running MCP servers on the local device."""
    import socket
    import subprocess
    import json
    
    detected = {}
    
    # Common MCP server ports and their identifiers
    MCP_PORTS = {
        3000: ("mcp-filesystem", "Filesystem MCP Server", "stdio/sse"),
        3001: ("mcp-github", "GitHub MCP Server", "stdio/sse"),
        3002: ("mcp-postgres", "PostgreSQL MCP Server", "stdio/sse"),
        3003: ("mcp-sqlite", "SQLite MCP Server", "stdio/sse"),
        3004: ("mcp-browser", "Playwright Browser MCP Server", "stdio/sse"),
        3005: ("mcp-slack", "Slack MCP Server", "stdio/sse"),
        3006: ("mcp-notion", "Notion MCP Server", "stdio/sse"),
        3007: ("mcp-gdrive", "Google Drive MCP Server", "stdio/sse"),
        3008: ("mcp-memory", "Memory/Knowledge Graph MCP Server", "stdio/sse"),
        3009: ("mcp-brave", "Brave Search MCP Server", "stdio/sse"),
        3010: ("mcp-fetch", "Fetch/HTTP MCP Server", "stdio/sse"),
    }
    
    # Check common ports
    for port, (name, desc, transport) in MCP_PORTS.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            if result == 0:
                detected[name] = {
                    "description": desc,
                    "port": port,
                    "transport": transport,
                    "auto_detected": True,
                }
        except Exception:
            pass
    
    # Also check for stdio-based MCP servers by looking at running processes
    try:
        # Check for mcp processes
        result = subprocess.run(
            ["pgrep", "-f", "mcp.*server"],
            capture_output=True, text=True, timeout=2
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                try:
                    # Get command line to identify the server
                    cmd_result = subprocess.run(
                        ["ps", "-p", pid, "-o", "args="],
                        capture_output=True, text=True, timeout=1
                    )
                    cmd = cmd_result.stdout.strip()
                    if "filesystem" in cmd and "mcp-filesystem" not in detected:
                        detected["mcp-filesystem"] = {"description": "Filesystem MCP Server", "port": "stdio", "transport": "stdio", "auto_detected": True}
                    elif "github" in cmd and "mcp-github" not in detected:
                        detected["mcp-github"] = {"description": "GitHub MCP Server", "port": "stdio", "transport": "stdio", "auto_detected": True}
                    elif "postgres" in cmd and "mcp-postgres" not in detected:
                        detected["mcp-postgres"] = {"description": "PostgreSQL MCP Server", "port": "stdio", "transport": "stdio", "auto_detected": True}
                    elif "sqlite" in cmd and "mcp-sqlite" not in detected:
                        detected["mcp-sqlite"] = {"description": "SQLite MCP Server", "port": "stdio", "transport": "stdio", "auto_detected": True}
                    elif "playwright" in cmd and "mcp-browser" not in detected:
                        detected["mcp-browser"] = {"description": "Playwright Browser MCP Server", "port": "stdio", "transport": "stdio", "auto_detected": True}
                except Exception:
                    pass
    except Exception:
        pass
    
    return detected


if __name__ == "__main__":
    sys.exit(main([]))