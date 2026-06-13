"""
Sora Agent — Agent runner utilities.

Provides run_agent() for executing agent sessions programmatically.
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional


async def run_agent(
    prompt: str,
    *,
    model: str = "minimax-m3",
    provider: str = "ollama-cloud",
    toolsets: list[str] | None = None,
    skills: list[str] | None = None,
    system_prompt: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Run a single agent turn programmatically.

    This is a convenience wrapper for CLI tools and scripts that want to
    invoke the agent without the full interactive session.

    Args:
        prompt: The user prompt/input
        model: Model name to use
        provider: Provider name (ollama-cloud, openrouter, etc.)
        toolsets: List of toolsets to enable
        skills: List of skills to load
        system_prompt: Optional system prompt override
        max_tokens: Maximum response tokens
        temperature: Sampling temperature
        **kwargs: Additional arguments passed to the agent

    Returns:
        Dict with 'response' (str), 'tool_calls' (list), 'usage' (dict)
    """
    # Import here to avoid circular imports
    from sora_cli.cli import AgentRunner

    runner = AgentRunner(
        model=model,
        provider=provider,
        toolsets=toolsets or [],
        skills=skills or [],
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    try:
        result = await runner.run(prompt, **kwargs)
        return result
    finally:
        await runner.cleanup()


def run_agent_sync(prompt: str, **kwargs: Any) -> dict[str, Any]:
    """Synchronous wrapper for run_agent()."""
    return asyncio.run(run_agent(prompt, **kwargs))


__all__ = ["run_agent", "run_agent_sync"]