"""
Sora Agent — Toolset definitions and management.

Toolsets are curated collections of tools for specific domains.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolSpec:
    """Specification for a single tool."""
    name: str
    description: str
    module: str
    function: str
    params_schema: dict[str, Any] = field(default_factory=dict)
    required: bool = False


@dataclass
class Toolset:
    """A curated collection of tools for a specific domain."""
    name: str
    description: str
    tools: list[ToolSpec] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)  # Other toolset names
    env_vars: list[str] = field(default_factory=list)  # Required env vars


# Built-in toolset registry
TOOLSETS: dict[str, Toolset] = {
    "core": Toolset(
        name="core",
        description="Core tools always available: file, terminal, web search, memory",
        tools=[
            ToolSpec("read_file", "Read a file", "hermes_tools", "read_file"),
            ToolSpec("write_file", "Write a file", "hermes_tools", "write_file"),
            ToolSpec("patch", "Patch a file", "hermes_tools", "patch"),
            ToolSpec("search_files", "Search files", "hermes_tools", "search_files"),
            ToolSpec("terminal", "Run terminal command", "hermes_tools", "terminal"),
            ToolSpec("web_search", "Search the web", "hermes_tools", "web_search"),
            ToolSpec("web_extract", "Extract web content", "hermes_tools", "web_extract"),
            ToolSpec("memory", "Access persistent memory", "hermes_tools", "memory"),
            ToolSpec("session_search", "Search past sessions", "hermes_tools", "session_search"),
        ],
    ),
    "web": Toolset(
        name="web",
        description="Web research and extraction tools",
        tools=[
            ToolSpec("web_search_plus", "Multi-provider web search", "hermes_tools", "web_search_plus"),
            ToolSpec("web_extract_plus", "Multi-provider extraction", "hermes_tools", "web_extract_plus"),
            ToolSpec("browser_navigate", "Navigate browser", "hermes_tools", "browser_navigate"),
            ToolSpec("browser_click", "Click element", "hermes_tools", "browser_click"),
            ToolSpec("browser_snapshot", "Page snapshot", "hermes_tools", "browser_snapshot"),
        ],
        dependencies=["core"],
    ),
    "code": Toolset(
        name="code",
        description="Code execution and development tools",
        tools=[
            ToolSpec("execute_code", "Execute Python code", "hermes_tools", "execute_code"),
            ToolSpec("search_files", "Search codebase", "hermes_tools", "search_files"),
            ToolSpec("terminal", "Run build/test commands", "hermes_tools", "terminal"),
        ],
        dependencies=["core"],
    ),
    "delegation": Toolset(
        name="delegation",
        description="Subagent delegation and orchestration",
        tools=[
            ToolSpec("delegate_task", "Spawn subagent", "hermes_tools", "delegate_task"),
            ToolSpec("delegate_with_model", "Delegate to specific model", "hermes_tools", "delegate_with_model"),
            ToolSpec("delegate_parallel", "Parallel delegation", "hermes_tools", "delegate_parallel"),
        ],
        dependencies=["core"],
    ),
    "voice": Toolset(
        name="voice",
        description="Voice bridge tools (Discord, VOIP, TTS/STT)",
        tools=[
            ToolSpec("voice_live", "Start Gemini Live bridge", "hermes_tools", "voice_live"),
            ToolSpec("voice_vapi", "Start Vapi bridge", "hermes_tools", "voice_vapi"),
            ToolSpec("voice_eleven", "Start ElevenLabs bridge", "hermes_tools", "voice_eleven"),
            ToolSpec("voice_live_status", "Voice bridge status", "hermes_tools", "voice_live_status"),
            ToolSpec("sora_voip_start", "Start VOIP bridge", "hermes_tools", "sora_voip_start"),
            ToolSpec("sora_voip_status", "VOIP bridge status", "hermes_tools", "sora_voip_status"),
            ToolSpec("sora_voip_calls", "List VOIP calls", "hermes_tools", "sora_voip_calls"),
            ToolSpec("text_to_speech", "Text to speech", "hermes_tools", "text_to_speech"),
        ],
        dependencies=["core"],
        env_vars=["GEMINI_API_KEY", "VAPI_API_KEY", "ELEVENLABS_API_KEY"],
    ),
    "mcp": Toolset(
        name="mcp",
        description="MCP server management and tools",
        tools=[
            ToolSpec("sora_mcp_start", "Start MCP server", "hermes_tools", "sora_mcp_start"),
            ToolSpec("sora_mcp_status", "MCP server status", "hermes_tools", "sora_mcp_status"),
            ToolSpec("mcporter", "MCP server management", "hermes_tools", "mcporter"),
        ],
        dependencies=["core"],
    ),
    "github": Toolset(
        name="github",
        description="GitHub repository and PR management",
        tools=[
            ToolSpec("github_status", "Check GitHub repos", "hermes_tools", "github_status"),
            ToolSpec("github_pr_status", "Check PR status", "hermes_tools", "github_pr_status"),
            ToolSpec("github_code_review", "Review PR", "hermes_tools", "github_code_review"),
        ],
        dependencies=["core"],
        env_vars=["GITHUB_TOKEN"],
    ),
    "discord": Toolset(
        name="discord",
        description="Discord messaging and voice",
        tools=[
            ToolSpec("send_message", "Send Discord message", "hermes_tools", "send_message"),
            ToolSpec("voice_live", "Discord voice bridge", "hermes_tools", "voice_live"),
        ],
        dependencies=["core"],
        env_vars=["DISCORD_TOKEN"],
    ),
    "telegram": Toolset(
        name="telegram",
        description="Telegram messaging",
        tools=[
            ToolSpec("send_message", "Send Telegram message", "hermes_tools", "send_message"),
            ToolSpec("telegram_status", "Send status", "hermes_tools", "telegram_status"),
            ToolSpec("telegram_card", "Send formatted card", "hermes_tools", "telegram_card"),
        ],
        dependencies=["core"],
        env_vars=["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"],
    ),
    "memory": Toolset(
        name="memory",
        description="Advanced memory operations (Honcho, fabric)",
        tools=[
            ToolSpec("honcho_search", "Search Honcho memory", "hermes_tools", "honcho_search"),
            ToolSpec("honcho_reasoning", "Honcho reasoning", "hermes_tools", "honcho_reasoning"),
            ToolSpec("fabric_search", "Search fabric", "hermes_tools", "fabric_search"),
            ToolSpec("fabric_write", "Write to fabric", "hermes_tools", "fabric_write"),
            ToolSpec("fabric_recall", "Recall from fabric", "hermes_tools", "fabric_recall"),
        ],
        dependencies=["core"],
        env_vars=["HONCHO_API_KEY", "FABRIC_API_KEY"],
    ),
    "skills": Toolset(
        name="skills",
        description="Skill management and loading",
        tools=[
            ToolSpec("skill_view", "View skill", "hermes_tools", "skill_view"),
            ToolSpec("skills_list", "List skills", "hermes_tools", "skills_list"),
            ToolSpec("skill_manage", "Manage skills", "hermes_tools", "skill_manage"),
        ],
        dependencies=["core"],
    ),
    "cron": Toolset(
        name="cron",
        description="Scheduled job management",
        tools=[
            ToolSpec("cronjob", "Manage cron jobs", "hermes_tools", "cronjob"),
        ],
        dependencies=["core"],
    ),
    "browser": Toolset(
        name="browser",
        description="Full browser automation",
        tools=[
            ToolSpec("browser_navigate", "Navigate", "hermes_tools", "browser_navigate"),
            ToolSpec("browser_click", "Click", "hermes_tools", "browser_click"),
            ToolSpec("browser_type", "Type text", "hermes_tools", "browser_type"),
            ToolSpec("browser_snapshot", "Snapshot", "hermes_tools", "browser_snapshot"),
            ToolSpec("browser_console", "Console logs", "hermes_tools", "browser_console"),
            ToolSpec("browser_vision", "Screenshot", "hermes_tools", "browser_vision"),
        ],
        dependencies=["web"],
    ),
}


def get_toolset(name: str) -> Toolset | None:
    """Get a toolset by name."""
    return TOOLSETS.get(name)


def list_toolsets() -> list[Toolset]:
    """List all available toolsets."""
    return list(TOOLSETS.values())


def resolve_toolsets(names: list[str]) -> list[Toolset]:
    """Resolve toolset names to Toolset objects, including dependencies."""
    result = []
    seen = set()

    def add_toolset(name: str):
        if name in seen:
            return
        ts = get_toolset(name)
        if not ts:
            return
        for dep in ts.dependencies:
            add_toolset(dep)
        result.append(ts)
        seen.add(name)

    for name in names:
        add_toolset(name)

    return result


def get_all_tools(toolset_names: list[str]) -> list[ToolSpec]:
    """Get all ToolSpecs for the given toolset names (with deps)."""
    toolsets = resolve_toolsets(toolset_names)
    tools = []
    for ts in toolsets:
        tools.extend(ts.tools)
    return tools


__all__ = [
    "ToolSpec",
    "Toolset",
    "TOOLSETS",
    "get_toolset",
    "list_toolsets",
    "resolve_toolsets",
    "get_all_tools",
]