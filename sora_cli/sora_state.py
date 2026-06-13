"""
Sora Agent — Global application state management.

Manages runtime state, configuration, and cross-component communication.
"""
from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from sora_constants import get_default_sora_root


@dataclass
class SoraState:
    """Global Sora application state."""
    # Directories
    sora_root: Path
    config_path: Path
    data_dir: Path
    logs_dir: Path
    cache_dir: Path
    profiles_dir: Path

    # Configuration
    config: dict[str, Any] = field(default_factory=dict)
    profile_name: str = "default"

    # Runtime
    started_at: datetime = field(default_factory=datetime.utcnow)
    session_id: str = ""
    pid: int = field(default_factory=lambda: os.getpid())

    # Component states
    voice_bridge: dict[str, Any] = field(default_factory=dict)
    mcp_servers: dict[str, Any] = field(default_factory=dict)
    active_sessions: dict[str, Any] = field(default_factory=dict)

    # Feature flags
    features: dict[str, bool] = field(default_factory=lambda: {
        "voice": True,
        "mcp": True,
        "web_dashboard": True,
        "tui": True,
        "honcho": True,
        "telemetry": True,
    })

    # Lock for thread-safe updates
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    @classmethod
    def create(cls, profile_name: str = "default", sora_home: str | None = None) -> "SoraState":
        """Create state for a profile."""
        if sora_home:
            root = Path(sora_home)
        else:
            from sora_constants import resolve_profile_env
            root = resolve_profile_env(profile_name)

        return cls(
            sora_root=root,
            config_path=root / "config.yaml",
            data_dir=root / "data",
            logs_dir=root / "logs",
            cache_dir=root / "cache",
            profiles_dir=root.parent,
            profile_name=profile_name,
            session_id=f"sora-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Get a state value thread-safely."""
        with self._lock:
            return getattr(self, key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a state value thread-safely."""
        with self._lock:
            setattr(self, key, value)

    def update_voice_bridge(self, bridge_type: str, data: dict[str, Any]) -> None:
        """Update voice bridge state."""
        with self._lock:
            self.voice_bridge[bridge_type] = {
                **self.voice_bridge.get(bridge_type, {}),
                **data,
                "updated_at": datetime.utcnow().isoformat(),
            }

    def get_voice_bridge(self, bridge_type: str) -> dict[str, Any] | None:
        """Get voice bridge state."""
        with self._lock:
            return self.voice_bridge.get(bridge_type)

    def register_mcp_server(self, name: str, info: dict[str, Any]) -> None:
        """Register an MCP server."""
        with self._lock:
            self.mcp_servers[name] = {
                **info,
                "registered_at": datetime.utcnow().isoformat(),
            }

    def unregister_mcp_server(self, name: str) -> None:
        """Unregister an MCP server."""
        with self._lock:
            self.mcp_servers.pop(name, None)

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        with self._lock:
            return self.features.get(feature, False)

    def toggle_feature(self, feature: str, enabled: bool | None = None) -> bool:
        """Toggle a feature flag."""
        with self._lock:
            if enabled is None:
                enabled = not self.features.get(feature, False)
            self.features[feature] = enabled
            return enabled


# Global state instance (lazy initialization)
_state: SoraState | None = None
_state_lock = threading.Lock()


def get_state(profile_name: str = "default", sora_home: str | None = None) -> SoraState:
    """Get or create the global state instance."""
    global _state
    with _state_lock:
        if _state is None:
            _state = SoraState.create(profile_name, sora_home)
        return _state


def set_state(state: SoraState) -> None:
    """Set the global state instance."""
    global _state
    with _state_lock:
        _state = state


def reset_state() -> None:
    """Reset the global state (for testing)."""
    global _state
    with _state_lock:
        _state = None


__all__ = ["SoraState", "get_state", "set_state", "reset_state"]