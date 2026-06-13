"""
S0RA Agent Logging — Centralized file logging setup.
Mirrors hermes_logging.py from Hermes Agent.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

from sora_constants import get_logs_dir, get_sora_home

_LOGGING_INITIALIZED = False


def setup_logging(mode: str = "cli") -> None:
    """
    Initialize file logging for SORA.

    Args:
        mode: "cli" for agent.log/errors.log, "gui" for gui.log, "gateway" for gateway.log
    """
    global _LOGGING_INITIALIZED
    if _LOGGING_INITIALIZED:
        return

    try:
        logs_dir = get_logs_dir()
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Determine log file names based on mode
        if mode == "gui":
            log_file = logs_dir / "gui.log"
            error_file = logs_dir / "gui_errors.log"
        elif mode == "gateway":
            log_file = logs_dir / "gateway.log"
            error_file = logs_dir / "gateway_errors.log"
        else:
            log_file = logs_dir / "agent.log"
            error_file = logs_dir / "errors.log"

        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # Clear existing handlers to avoid duplicates on re-init
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # File handler for INFO+ (all logs)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # Separate error file for WARNING+
        error_handler = logging.FileHandler(error_file, encoding="utf-8")
        error_handler.setLevel(logging.WARNING)
        error_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)

        # Console handler for WARNING+ (only errors to console by default)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter(
            "[%(levelname)s] %(name)s: %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # Redact secrets from logs if enabled
        _setup_secret_redaction(root_logger)

        _LOGGING_INITIALIZED = True

        logger = logging.getLogger("sora_logging")
        logger.info(
            f"SORA logging initialized (mode={mode}, log_file={log_file})"
        )

    except Exception as e:
        # Never crash on logging setup failure
        print(f"Warning: Failed to initialize logging: {e}", file=sys.stderr)


def _setup_secret_redaction(root_logger: logging.Logger) -> None:
    """Add a filter to redact secrets from log messages."""
    try:
        redact_env = os.environ.get("SORA_REDACT_SECRETS", "").lower()
        if redact_env not in {"1", "true", "yes", "on"}:
            # Also check config.yaml
            from sora_constants import _read_config_value
            config_val = _read_config_value("security.redact_secrets")
            if config_val and config_val.lower() not in {"1", "true", "yes", "on"}:
                return

        from agent.redact import SecretFilter
        secret_filter = SecretFilter()

        for handler in root_logger.handlers:
            handler.addFilter(secret_filter)
    except Exception:
        # Best effort — if redaction fails, continue without it
        pass


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)


def set_console_level(level: int) -> None:
    """Change the console handler level (for verbose/debug modes)."""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stderr:
            handler.setLevel(level)
            break


def set_file_level(level: int) -> None:
    """Change the file handler level."""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.setLevel(level)