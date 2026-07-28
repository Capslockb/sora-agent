#!/usr/bin/env python3
"""Canonical workflow entrypoint for public-documentation safety checks.

The established runner owns comparison selection, classification, format parsing,
and diagnostics. This entrypoint applies the final workflow boundaries for HTML
option records, case-insensitive community-health filenames, deletion or rename
scans that can expose unchanged fallback documentation, command-aware code-block
records, named shell prompts, and multiline reStructuredText table cells.
"""
from __future__ import annotations

import importlib.util
import re
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

# GitHub recognizes SUPPORT.md and GOVERNANCE.md as public community-health files
# in the repository root, .github/, and docs/. Classification remains
# case-insensitive. Broad root and .github CODEOWNERS rules provide ownership
# parity for mixed-case filenames that CODEOWNERS cannot express individually.
_original_is_public_doc = scanner.is_public_doc
COMMUNITY_HEALTH_NAMES_UPPER = {"SUPPORT.MD", "GOVERNANCE.MD"}
COMMUNITY_HEALTH_PARENTS = {".", ".github"}


def is_public_doc(path: str, include_fixtures: bool = False) -> bool:
    """Recognize public community-health files without case-based gaps."""
    candidate = Path(path)
    parent = candidate.parent.as_posix()
    if (
        parent in COMMUNITY_HEALTH_PARENTS
        and candidate.name.upper() in COMMUNITY_HEALTH_NAMES_UPPER
    ):
        return True
    return _original_is_public_doc(path, include_fixtures)


scanner.is_public_doc = is_public_doc
runner.is_public_doc = is_public_doc
runner.implementation.is_public_doc = is_public_doc

# A recognized shell prompt is presentation syntax, not the command head. Strip
# the complete prompt before classifying the following token so named prompts
# such as ``root$`` behave like bare ``$`` prompts.
def _command_head(line: str) -> str:
    prompt = scanner.PROMPTED_COMMAND_RE.match(line)
    stripped = line[prompt.end() :].lstrip() if prompt else line.strip()
    if not stripped:
        return ""
    return stripped.split(maxsplit=1)[0].lower()


runner.implementation._command_head = _command_head
runner._command_head = _command_head

# A punctuation mark at the end of a lowercase prose word is not executable
# syntax. Keep such lines in the surrounding wrapped record while retaining
# recognized commands, flags, paths, and genuinely command-like tokens as
# independent records.
def is_explicit_command_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return False

    prompted = bool(scanner.PROMPTED_COMMAND_RE.match(line))
    if not prompted and not scanner.SIMPLE_COMMAND_RE.match(line):
        return False

    head = _command_head(line)
    if not head:
        return False
    if head in runner.implementation.COMMAND_HEADS or head.startswith("-"):
        return True

    # Reject ordinary sentence punctuation such as ``ignore.`` or ``note:``.
    if head[-1:] in ".,;:!?":[
        return False

    return any(marker in head for marker in ("/", "\\", ".", ":", "_"))


runner.implementation.is_explicit_command_line = is_explicit_command_line
runner.implementation.is_independent_command_line = is_explicit_command_line
runner.is_explicit_command_line = is_explicit_command_line
runner.is_independent_command_line = is_explicit_command_line
scanner.is_independent_command_line = is_explicit_command_line


def _simple_table_cells_with_empty(border: str, row: str) -> list[str]:
    """Return every simple-table column, preserving empty continuation cells."""
    spans = [match.span() for match in re.finditer(r"[=~-]{2,}", border)]
    if len(spans) < 2:
        return [row]
    cells: list[str] = []
    for position, (start, _end) in enumerate(spans):
        next_start = spans[position + 1][0] if position + 1 < len(spans) else None
        cells.append(row[start:next_start] if next_start is not None else row[start:])
    return cells


def rst_records(lines: list[str]) -> list[scanner.ScanRecord]:
    """Apply RST table boundaries while preserving multiline simple-table cells."""
    records: list[scanner.ScanRecord] = []
    segment_start = 0
    index = 0

    def flush_plain(end: int) -> None:
        nonlocal segment_start
        if segment_start < end:
            records.extend(scanner.markdown_records(lines[segment_start:end], segment_start))

    while index < len(lines):
        line = lines[index]
        simple = runner.RST_SIMPLE_BORDER_RE.match(line)
        grid = runner.RST_GRID_BORDER_RE.match(line)
        if not simple and not grid:
            index += 1
            continue

        flush_plain(index)
        border = line
        runner._append_record(records, index + 1, line)
        index += 1

        if grid:
            columns: list[list[tuple[int, str]]] = []

            def flush_grid_cells() -> None:
                for parts in columns:
                    if parts:
                        records.append(scanner.ScanRecord(tuple(parts)))
                columns.clear()

            while index < len(lines) and lines[index].strip():
                current = lines[index]
                if runner.RST_GRID_BORDER_RE.match(current):
                    flush_grid_cells()
                    runner._append_record(records, index + 1, current)
                elif current.strip().startswith("|"):
                    cells = runner._grid_table_cells(current)
                    while len(columns) < len(cells):
                        columns.append([])
                    for position, cell in enumerate(cells):
                        if cell.strip():
                            columns[position].append((index + 1, cell))
                else:
                    flush_grid_cells()
                    runner._append_record(records, index + 1, current)
                index += 1
            flush_grid_cells()
        else:
            row_cells: list[list[tuple[int, str]]] = []

            def flush_simple_cells() -> None:
                for parts in row_cells:
                    if parts:
                        records.append(scanner.ScanRecord(tuple(parts)))
                row_cells.clear()

            while index < len(lines) and lines[index].strip():
                current = lines[index]
                if runner.RST_SIMPLE_BORDER_RE.match(current):
                    flush_simple_cells()
                    runner._append_record(records, index + 1, current)
                    index += 1
                    continue

                cells = _simple_table_cells_with_empty(border, current)
                starts_new_row = not row_cells or bool(cells and cells[0].strip())
                if starts_new_row:
                    flush_simple_cells()
                while len(row_cells) < len(cells):
                    row_cells.append([])
                for position, cell in enumerate(cells):
                    if cell.strip():
                        row_cells[position].append((index + 1, cell))
                index += 1
            flush_simple_cells()

        segment_start = index

    flush_plain(len(lines))
    return records


# scanner.document_records is the runner function and resolves ``rst_records``
# through the runner module globals at call time.
runner.rst_records = rst_records

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
scan_file = scanner.scan_file


def main() -> int:
    global _full_scan_due_to_public_removal
    _full_scan_due_to_public_removal = False
    return scanner.main()


if __name__ == "__main__":
    sys.exit(main())
