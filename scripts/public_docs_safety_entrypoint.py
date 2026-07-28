#!/usr/bin/env python3
"""Canonical workflow entrypoint for public-documentation safety checks.

The established runner owns comparison selection, classification, format parsing,
and diagnostics. This entrypoint applies the final workflow boundaries for HTML
option records, enforceable community-health filenames, and deletion or rename
scans that can expose unchanged fallback documentation.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_RUNNER_PATH = Path(__file__).with_name("public_docs_safety_runner.py")
_RUNNER_SPEC = importlib.util.spec_from_file_location(
    "_public_docs_safety_runner", _RUNNER_PATH
)
if _RUNNER_SPEC is None or _RUNNER_SPEC.loader is None:
    raise RuntimeError("unable to load public docs safety runner")
runner = importlib.util.module_from_spec(_RUNNER_SPEC)
sys.modules.setdefault("_public_docs_safety_runner", runner)
_RUNNER_SPEC.loader.exec_module(runner)

scanner = runner.scanner

# GitHub exposes each option as an independent user-visible choice. Keep sibling
# options in separate records while preserving nested inline content inside one
# option frame.
runner.implementation.HTML_BLOCK_TAGS.add("option")

# CODEOWNERS paths are case-sensitive and do not support character classes.
# Restrict root and .github community-health filenames to the exact uppercase and
# lowercase forms protected by this branch. Mixed-case files under docs/ remain
# covered through the directory-wide public-document and ownership rules.
_original_is_public_doc = scanner.is_public_doc
COMMUNITY_HEALTH_NAMES = {
    "SUPPORT.md",
    "support.md",
    "GOVERNANCE.md",
    "governance.md",
}
COMMUNITY_HEALTH_NAMES_UPPER = {name.upper() for name in COMMUNITY_HEALTH_NAMES}
COMMUNITY_HEALTH_PARENTS = {".", ".github"}


def is_public_doc(path: str, include_fixtures: bool = False) -> bool:
    """Recognize only community-health forms with enforceable ownership parity."""
    candidate = Path(path)
    parent = candidate.parent.as_posix()
    if (
        parent in COMMUNITY_HEALTH_PARENTS
        and candidate.name.upper() in COMMUNITY_HEALTH_NAMES_UPPER
    ):
        return candidate.name in COMMUNITY_HEALTH_NAMES
    return _original_is_public_doc(path, include_fixtures)


scanner.is_public_doc = is_public_doc
runner.is_public_doc = is_public_doc
runner.implementation.is_public_doc = is_public_doc

_original_changed_files_with_diff_args = scanner.changed_files_with_diff_args
_original_changed_added_lines = scanner.changed_added_lines
_full_scan_due_to_public_removal = False


def public_doc_removed_or_renamed(diff_args: list[str]) -> bool:
    """Return whether the selected comparison removes a public-document path."""
    result = scanner.subprocess.run(
        ["git", "diff", "--name-status", "--find-renames", *diff_args],
        text=True,
        stdout=scanner.subprocess.PIPE,
        stderr=scanner.subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise scanner.ComparisonError(
            "unable to resolve public-document deletion status"
        )

    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) < 2:
            continue
        status = fields[0]
        old_path = fields[1]
        if status.startswith("D") and runner.is_public_doc(old_path):
            return True
        if status.startswith("R") and len(fields) >= 3 and runner.is_public_doc(old_path):
            return True
    return False


def changed_files_with_diff_args() -> tuple[list[str], list[str]]:
    """Expand deletion/rename comparisons to all remaining repository files."""
    global _full_scan_due_to_public_removal
    files, diff_args = _original_changed_files_with_diff_args()
    _full_scan_due_to_public_removal = public_doc_removed_or_renamed(diff_args)
    if _full_scan_due_to_public_removal:
        return scanner.all_candidate_files(), diff_args
    return files, diff_args


def changed_added_lines(
    files: list[str], diff_args: list[str] | None = None
) -> dict[str, set[int]] | None:
    """Select every line when a removal may expose unchanged fallback content."""
    if not _full_scan_due_to_public_removal:
        return _original_changed_added_lines(files, diff_args)

    selected: dict[str, set[int]] = {}
    for path in files:
        try:
            line_count = len(
                Path(path)
                .read_text(encoding="utf-8", errors="ignore")
                .splitlines()
            )
        except OSError:
            selected[path] = {1}
        else:
            selected[path] = set(range(1, line_count + 1))
    return selected


scanner.changed_files_with_diff_args = changed_files_with_diff_args
scanner.changed_added_lines = changed_added_lines


def main() -> int:
    global _full_scan_due_to_public_removal
    _full_scan_due_to_public_removal = False
    return scanner.main()


if __name__ == "__main__":
    sys.exit(main())
