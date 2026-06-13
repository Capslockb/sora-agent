"""
Sora Agent — Model and provider utilities.

Utilities for model selection, provider routing, and capability detection.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ModelTier(Enum):
    """Model capability tiers for smart routing."""
    FAST = "fast"          # Cheap, fast models for simple tasks
    BALANCED = "balanced"  # Good balance of quality/speed
    POWERFUL = "powerful"  # Best quality, slower, more expensive
    REASONING = "reasoning"  # Specialized reasoning models


class ProviderType(Enum):
    """Supported provider types."""
    OLLAMA = "ollama"
    OLLAMA_CLOUD = "ollama-cloud"
    OPENROUTER = "openrouter"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    TOGETHER = "together"
    LOCAL = "local"


@dataclass
class ModelSpec:
    """Specification for a model."""
    name: str
    provider: ProviderType
    tier: ModelTier
    max_tokens: int = 8192
    supports_tools: bool = True
    supports_vision: bool = False
    supports_audio: bool = False
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    context_window: int = 8192


# Known model registry
MODEL_REGISTRY: dict[str, ModelSpec] = {
    # Ollama models
    "minimax-m3": ModelSpec(
        name="minimax-m3", provider=ProviderType.OLLAMA_CLOUD, tier=ModelTier.POWERFUL,
        max_tokens=32768, supports_tools=True, supports_vision=True, context_window=128000
    ),
    "nemotron-3-ultra": ModelSpec(
        name="nemotron-3-ultra", provider=ProviderType.OLLAMA_CLOUD, tier=ModelTier.POWERFUL,
        max_tokens=32768, supports_tools=True, context_window=128000
    ),
    "qwen2.5-coder-32b": ModelSpec(
        name="qwen2.5-coder-32b", provider=ProviderType.OLLAMA, tier=ModelTier.BALANCED,
        max_tokens=32768, supports_tools=True, context_window=32768
    ),
    "llama3.1-70b": ModelSpec(
        name="llama3.1-70b", provider=ProviderType.OLLAMA, tier=ModelTier.POWERFUL,
        max_tokens=32768, supports_tools=True, context_window=128000
    ),
    # OpenRouter models
    "anthropic/claude-3.5-sonnet": ModelSpec(
        name="anthropic/claude-3.5-sonnet", provider=ProviderType.OPENROUTER, tier=ModelTier.POWERFUL,
        max_tokens=8192, supports_tools=True, supports_vision=True, context_window=200000
    ),
    "openai/gpt-4o": ModelSpec(
        name="openai/gpt-4o", provider=ProviderType.OPENROUTER, tier=ModelTier.POWERFUL,
        max_tokens=4096, supports_tools=True, supports_vision=True, context_window=128000
    ),
    "google/gemini-2.0-flash-exp": ModelSpec(
        name="google/gemini-2.0-flash-exp", provider=ProviderType.OPENROUTER, tier=ModelTier.BALANCED,
        max_tokens=8192, supports_tools=True, supports_vision=True, supports_audio=True, context_window=1048576
    ),
}


def get_model_spec(model_name: str) -> ModelSpec | None:
    """Get model specification by name."""
    return MODEL_REGISTRY.get(model_name)


def list_models(tier: ModelTier | None = None, provider: ProviderType | None = None) -> list[ModelSpec]:
    """List available models, optionally filtered."""
    models = list(MODEL_REGISTRY.values())
    if tier:
        models = [m for m in models if m.tier == tier]
    if provider:
        models = [m for m in models if m.provider == provider]
    return models


def resolve_model(model: str | None, tier: ModelTier = ModelTier.BALANCED) -> str:
    """Resolve a model name, falling back to tier default."""
    if model and model in MODEL_REGISTRY:
        return model

    # Tier defaults
    defaults = {
        ModelTier.FAST: "qwen2.5-coder-32b",
        ModelTier.BALANCED: "minimax-m3",
        ModelTier.POWERFUL: "minimax-m3",
        ModelTier.REASONING: "nemotron-3-ultra",
    }
    return defaults.get(tier, "minimax-m3")


def get_provider_for_model(model_name: str) -> ProviderType | None:
    """Get the provider type for a model."""
    spec = get_model_spec(model_name)
    return spec.provider if spec else None


def estimate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost for a model call."""
    spec = get_model_spec(model_name)
    if not spec:
        return 0.0
    input_cost = (input_tokens / 1000) * spec.cost_per_1k_input
    output_cost = (output_tokens / 1000) * spec.cost_per_1k_output
    return input_cost + output_cost


__all__ = [
    "ModelTier",
    "ProviderType",
    "ModelSpec",
    "MODEL_REGISTRY",
    "get_model_spec",
    "list_models",
    "resolve_model",
    "get_provider_for_model",
    "estimate_cost",
]