"""
S0RA Agent Bootstrap — UTF-8 stdio setup for Windows.
Must be the FIRST import in any sora entry point.
No-op on POSIX. Mirrors hermes_bootstrap.
"""

import os
import sys

if os.name == "nt":
    # Windows: force UTF-8 mode for stdout/stderr/stdin
    # This must happen before any print() or file I/O
    try:
        # Python 3.7+: reconfigure stdio with UTF-8
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        # Best effort — if reconfigure fails, continue anyway
        pass

    # Also set the env var for child processes
    os.environ.setdefault("PYTHONUTF8", "1")

# Make sure we can import sora modules from the package root
# This allows `python -m sora_cli.main` to work from the repo root
import sys as _sys
from pathlib import Path as _Path

_repo_root = _Path(__file__).parent.parent.resolve()
if str(_repo_root) not in _sys.path:
    _sys.path.insert(0, str(_repo_root))

del _sys, _Path, _repo_root