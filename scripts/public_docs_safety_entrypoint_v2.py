#!/usr/bin/env python3
"""Final exact-head boundaries for the public documentation safety workflow.

This wrapper keeps the established canonical entrypoint intact while correcting
structural-deletion selection, command-continuation grouping, and document-read
failure handling. It remains a scanner/workflow change only; S0RA application
runtime behavior is unaffected.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ENTRYPOINT_PATH = Path(__file__).with_name("public_docs_safety_entrypoint.py")
_ENTRYPOINT_SPEC = importlib.util.spec_from_file_location(
    "_public_docs_safety_entrypoint", _ENTRYPOINT_PATH
)
if _ENTRYPOINT_SPEC is None or _ENTRYPOINT_SPEC.loader is None:
    raise RuntimeError("unable to load public docs safety entrypoint")
entrypoint = importlib.util.module_from_spec(_ENTRYPOINT_SPEC)
sys.modules.setdefault("_public_docs_safety_entrypoint", entrypoint)
_ENTRYPOINT_SPEC.loader.exec_module(entrypoint)

scanner = entrypoint.scanner
runner = entrypoint.runner


def _continues_command(
    lines: list[str],
    command_index: int,
    previous_index: int,
    current_index: int,
    continuation_indent: int | None,
) -> tuple[bool, int | None]:
    """Keep sibling continuation lines relative to the command's base indent."""
    previous = lines[previous_index]
    current = lines[current_index]
    current_stripped = current.lstrip()
    base_indent = scanner.leading_indent_width(lines[command_index])
    current_indent = scanner.leading_indent_width(current)

    previous_continues = previous.rstrip().endswith(("\\", "&&", "||", "|"))
    current_is_continuation_token = current_stripped.startswith(
        ("-", "&&", "||", "|")
    )
    explicit_continuation = bool(
        previous_continues or current_is_continuation_token
    )
    indented_continuation = current_indent > base_indent
    sibling_continuation = bool(
        continuation_indent is not None and current_indent >= continuation_indent
    )

    # Once a continuation block is established, indentation alone must not absorb
    # a later independent command. Argument/operator continuations remain grouped,
    # and wrapped prose siblings remain grouped because they are not recognized as
    # explicit commands.
    if (
        sibling_continuation
        and entrypoint.is_explicit_command_line(current)
        and not previous_continues
        and not current_is_continuation_token
    ):
        return False, continuation_indent

    if not (explicit_continuation or indented_continuation or sibling_continuation):
        return False, continuation_indent

    if continuation_indent is None and current_indent > base_indent:
        continuation_indent = current_indent
    return True, continuation_indent


def fenced_content_spans(
    lines: list[str], start: int, end: int
) -> list[tuple[int, int]]:
    """Split code-like content without dropping equal-indented continuations."""
    spans: list[tuple[int, int]] = []
    index = start
    while index < end:
        if not lines[index].strip():
            index += 1
            continue

        block_start = index
        if entrypoint.is_explicit_command_line(lines[index]):
            command_index = index
            continuation_indent: int | None = None
            index += 1
            while index < end and lines[index].strip():
                continues, continuation_indent = _continues_command(
                    lines,
                    command_index,
                    index - 1,
                    index,
                    continuation_indent,
                )
                if not continues:
                    break
                index += 1
            spans.append((block_start + 1, index))
            continue

        index += 1
        while (
            index < end
            and lines[index].strip()
            and not entrypoint.is_explicit_command_line(lines[index])
        ):
            index += 1
        spans.append((block_start + 1, index))
    return spans


# Markdown, indented-code, and AsciiDoc listing paths resolve this helper through
# either the core scanner or the implementation module at call time.
scanner.fenced_content_spans = fenced_content_spans
runner.implementation.fenced_content_spans = fenced_content_spans
runner.fenced_content_spans = fenced_content_spans
entrypoint.fenced_content_spans = fenced_content_spans

_original_changed_files_with_diff_args = scanner.changed_files_with_diff_args
_original_changed_added_lines = scanner.changed_added_lines
_original_scan_file = scanner.scan_file
_full_scan_paths: set[str] = set()


def public_docs_with_deletions(files: list[str], diff_args: list[str]) -> set[str]:
    """Return changed public documents whose post-image needs a complete scan.

    Any deleted line can remove a structural delimiter and alter parser records
    arbitrarily far below the hunk. Numstat is used only to detect deletion
    counts; path parsing is deliberately avoided so unusual filenames remain
    handled by the existing raw-path comparison logic.
    """
    documents = [
        path
        for path in files
        if Path(path).is_file() and runner.is_public_doc(path)
    ]
    if not documents:
        return set()

    result = scanner.subprocess.run(
        ["git", "diff", "--numstat", *diff_args, "--", *documents],
        text=True,
        stdout=scanner.subprocess.PIPE,
        stderr=scanner.subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise scanner.ComparisonError(
            "unable to resolve public-document deletion ranges"
        )

    for line in result.stdout.splitlines():
        if not line:
            continue
        fields = line.split("\t", 2)
        if len(fields) != 3:
            raise scanner.ComparisonError(
                "unable to parse public-document deletion ranges"
            )
        deleted = fields[1]
        if deleted == "-" or (deleted.isdigit() and int(deleted) > 0):
            return set(documents)
        if not deleted.isdigit():
            raise scanner.ComparisonError(
                "unable to parse public-document deletion ranges"
            )
    return set()


def changed_files_with_diff_args() -> tuple[list[str], list[str]]:
    """Record changed documents requiring full post-image selection."""
    global _full_scan_paths
    files, diff_args = _original_changed_files_with_diff_args()
    if entrypoint._full_scan_due_to_public_removal:
        _full_scan_paths = set()
    else:
        _full_scan_paths = public_docs_with_deletions(files, diff_args)
    return files, diff_args


def _all_lines(path: str) -> set[int]:
    try:
        line_count = len(Path(path).read_text(encoding="utf-8").splitlines())
    except (OSError, UnicodeError):
        # Preserve one selected line so the strict scan path emits controlled,
        # metadata-only PDS900 evidence rather than silently passing.
        return {1}
    return set(range(1, line_count + 1))


def changed_added_lines(
    files: list[str], diff_args: list[str] | None = None
) -> dict[str, set[int]] | None:
    """Expand every document containing deletions to its full post-image."""
    selected = _original_changed_added_lines(files, diff_args)
    if selected is None:
        return None
    for path in _full_scan_paths:
        selected[path] = _all_lines(path)
    return selected


def scan_file(
    path: str, line_numbers: list[int] | range
) -> list[tuple[str, int, str, str]]:
    """Fail closed before the inherited parser can ignore invalid UTF-8 bytes."""
    try:
        Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return [(path, 1, "PDS900", "document read failure")]
    return _original_scan_file(path, line_numbers)


scanner.changed_files_with_diff_args = changed_files_with_diff_args
scanner.changed_added_lines = changed_added_lines
scanner.scan_file = scan_file
entrypoint.changed_files_with_diff_args = changed_files_with_diff_args
entrypoint.changed_added_lines = changed_added_lines
entrypoint.scan_file = scan_file
runner.implementation.scan_file = scan_file
runner.scan_file = scan_file


def main() -> int:
    global _full_scan_paths
    _full_scan_paths = set()
    return entrypoint.main()


if __name__ == "__main__":
    sys.exit(main())
