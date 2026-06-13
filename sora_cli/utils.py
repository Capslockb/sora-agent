"""
Sora Agent — Common utilities and helpers.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterator, TypeVar

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


T = TypeVar("T")


def get_console(stderr: bool = False) -> Console:
    """Get a Rich console instance."""
    return Console(stderr=stderr, force_terminal=sys.stderr.isatty() if stderr else sys.stdout.isatty())


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def truncate(text: str, max_len: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length."""
    if len(text) <= max_len:
        return text
    return text[:max_len - len(suffix)] + suffix


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{int(m)}m {int(s)}s"
    else:
        h, rem = divmod(seconds, 3600)
        m, _ = divmod(rem, 60)
        return f"{int(h)}h {int(m)}m"


def format_bytes(bytes_val: int) -> str:
    """Format bytes in human-readable form."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f}PB"


def sha256_hash(data: str | bytes) -> str:
    """Compute SHA256 hash."""
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()


def short_hash(data: str | bytes, length: int = 8) -> str:
    """Short hash for display."""
    return sha256_hash(data)[:length]


def run_command(
    cmd: list[str] | str,
    *,
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
    timeout: float | None = 30,
    capture: bool = True,
    check: bool = True,
) -> tuple[int, str, str]:
    """
    Run a shell command and return (exit_code, stdout, stderr).

    Args:
        cmd: Command as list or string
        cwd: Working directory
        env: Environment variables
        timeout: Timeout in seconds
        capture: Capture stdout/stderr
        check: Raise on non-zero exit

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)

    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=proc_env,
            capture_output=capture,
            text=True,
            timeout=timeout,
            check=False,
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""

        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd, stdout, stderr)

        return result.returncode, stdout, stderr

    except subprocess.TimeoutExpired as e:
        stdout = e.stdout.decode() if e.stdout else ""
        stderr = e.stderr.decode() if e.stderr else ""
        raise RuntimeError(f"Command timed out after {timeout}s: {cmd}") from e


async def run_command_async(
    cmd: list[str] | str,
    *,
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
    timeout: float | None = 30,
) -> tuple[int, str, str]:
    """Async version of run_command."""
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)

    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        env=proc_env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode or 0, stdout.decode(), stderr.decode()
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise RuntimeError(f"Command timed out after {timeout}s: {cmd}")


@contextmanager
def spinner(message: str, console: Console | None = None) -> Iterator[Progress]:
    """Context manager for a spinner."""
    c = console or get_console()
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold]{task.description}"),
        console=c,
        transient=True,
    ) as progress:
        task = progress.add_task(message, total=None)
        yield progress


def load_json_file(path: Path | str) -> Any:
    """Load JSON from file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json_file(path: Path | str, data: Any, indent: int = 2) -> None:
    """Save JSON to file atomically."""
    path = Path(path)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    tmp_path.replace(path)


def load_yaml_file(path: Path | str) -> Any:
    """Load YAML from file."""
    import yaml
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_yaml_file(path: Path | str, data: Any) -> None:
    """Save YAML to file atomically."""
    import yaml
    path = Path(path)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    tmp_path.replace(path)


def ensure_dir(path: Path | str) -> Path:
    """Ensure directory exists."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def find_executable(name: str) -> Path | None:
    """Find executable in PATH."""
    result = shutil.which(name)
    return Path(result) if result else None


def is_command_available(name: str) -> bool:
    """Check if a command is available."""
    return find_executable(name) is not None


def get_git_root(path: Path | str | None = None) -> Path | None:
    """Find git repository root."""
    start = Path(path or os.getcwd())
    for p in [start] + list(start.parents):
        if (p / ".git").exists():
            return p
    return None


def get_git_branch() -> str | None:
    """Get current git branch."""
    try:
        _, out, _ = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], check=False)
        branch = out.strip()
        return branch if branch != "HEAD" else None
    except Exception:
        return None


def get_git_hash(short: bool = True) -> str | None:
    """Get current git commit hash."""
    try:
        cmd = ["git", "rev-parse", "--short" if short else "HEAD"]
        _, out, _ = run_command(cmd, check=False)
        return out.strip() or None
    except Exception:
        return None


def retry(
    func: Callable[..., T],
    *args: Any,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    **kwargs: Any,
) -> T:
    """Retry a function with exponential backoff."""
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exc = e
            if attempt < max_attempts - 1:
                time.sleep(delay)
                delay *= backoff
    raise last_exc


async def retry_async(
    func: Callable[..., Coroutine[Any, Any, T]],
    *args: Any,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    **kwargs: Any,
) -> T:
    """Async retry with exponential backoff."""
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exc = e
            if attempt < max_attempts - 1:
                await asyncio.sleep(delay)
                delay *= backoff
    raise last_exc


def parse_key_value(s: str) -> tuple[str, str]:
    """Parse 'key=value' string."""
    if "=" not in s:
        raise ValueError(f"Expected key=value, got: {s}")
    k, v = s.split("=", 1)
    return k.strip(), v.strip()


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


__all__ = [
    "get_console",
    "slugify",
    "truncate",
    "format_duration",
    "format_bytes",
    "sha256_hash",
    "short_hash",
    "run_command",
    "run_command_async",
    "spinner",
    "load_json_file",
    "save_json_file",
    "load_yaml_file",
    "save_yaml_file",
    "ensure_dir",
    "find_executable",
    "is_command_available",
    "get_git_root",
    "get_git_branch",
    "get_git_hash",
    "retry",
    "retry_async",
    "parse_key_value",
    "deep_merge",
]