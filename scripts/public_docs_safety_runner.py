#!/usr/bin/env python3
"""Canonical workflow entrypoint for public-documentation safety checks.

This module loads the existing scanner implementation, then applies the final
range and format boundaries required by the workflow. Diagnostics and rule
semantics remain owned by the existing scanner modules.
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path

_IMPL_PATH = Path(__file__).with_name("public_docs_safety.py")
_IMPL_SPEC = importlib.util.spec_from_file_location(
    "_public_docs_safety_existing", _IMPL_PATH
)
if _IMPL_SPEC is None or _IMPL_SPEC.loader is None:
    raise RuntimeError("unable to load public docs safety implementation")
implementation = importlib.util.module_from_spec(_IMPL_SPEC)
sys.modules.setdefault("_public_docs_safety_existing", implementation)
_IMPL_SPEC.loader.exec_module(implementation)

scanner = implementation.scanner

# Markdown indented code permits additional indentation after the initial four
# spaces. Keep those deeper continuations in the same command-aware run.
scanner.INDENTED_CODE_RE = re.compile(r"^(?: {4,}|\t+)\S")


def comparison_args() -> list[str]:
    """Use an accepted branch baseline for branch-creation pushes.

    GitHub represents a new branch with an all-zero ``before`` SHA. Comparing
    that push to the empty tree scans unrelated pre-existing documentation.
    Instead, compare the new branch to the configured default branch. A missing
    baseline still fails closed through the existing comparison error path.
    """
    if os.environ.get("GITHUB_EVENT_NAME") == "push":
        before = scanner.push_before_sha()
        if before and before != scanner.ZERO_SHA:
            return [before, "HEAD"]
        return [f"origin/{scanner.default_branch()}...HEAD"]
    return [f"origin/{scanner.default_branch()}...HEAD"]


def split_unescaped_asciidoc_pipes(line: str) -> list[str]:
    """Split AsciiDoc cells only at pipes with an even escape depth."""
    chunks: list[str] = []
    current: list[str] = []
    backslashes = 0
    for character in line:
        if character == "|" and backslashes % 2 == 0:
            chunks.append("".join(current))
            current = []
            backslashes = 0
            continue
        current.append(character)
        if character == "\\":
            backslashes += 1
        else:
            backslashes = 0
    chunks.append("".join(current))
    return chunks


def asciidoc_segment_records(
    lines: list[str], offset: int = 0
) -> list[scanner.ScanRecord]:
    """Parse AsciiDoc prose while keeping real table cells independent."""
    records: list[scanner.ScanRecord] = []
    segment_start = 0
    index = 0

    def flush_plain(end: int) -> None:
        nonlocal segment_start
        if segment_start < end:
            records.extend(
                scanner.markdown_records(
                    lines[segment_start:end], offset=offset + segment_start
                )
            )

    while index < len(lines):
        if not implementation.ASCIIDOC_TABLE_DELIMITER_RE.match(lines[index]):
            index += 1
            continue

        flush_plain(index)
        records.append(scanner.ScanRecord(((offset + index + 1, lines[index]),)))
        index += 1
        cell_parts: list[tuple[int, str]] = []

        def flush_cell() -> None:
            if cell_parts:
                records.append(scanner.ScanRecord(tuple(cell_parts)))
                cell_parts.clear()

        while index < len(lines) and not implementation.ASCIIDOC_TABLE_DELIMITER_RE.match(
            lines[index]
        ):
            line = lines[index]
            line_number = offset + index + 1
            chunks = split_unescaped_asciidoc_pipes(line)
            if len(chunks) > 1:
                for chunk in chunks[1:]:
                    flush_cell()
                    if chunk.strip():
                        cell_parts.append((line_number, chunk))
            elif line.strip():
                cell_parts.append((line_number, line))
            else:
                flush_cell()
            index += 1

        flush_cell()
        if index < len(lines):
            records.append(scanner.ScanRecord(((offset + index + 1, lines[index]),)))
            index += 1
        segment_start = index

    flush_plain(len(lines))
    return records


def asciidoc_records(lines: list[str]) -> list[scanner.ScanRecord]:
    """Parse labeled and unlabeled AsciiDoc listing blocks plus table records."""
    records: list[scanner.ScanRecord] = []
    segment_start = 0
    index = 0

    def flush_segment(end: int) -> None:
        nonlocal segment_start
        if segment_start < end:
            records.extend(
                asciidoc_segment_records(
                    lines[segment_start:end], offset=segment_start
                )
            )

    while index < len(lines):
        marker_index: int | None = None
        delimiter: int | None = None

        if scanner.ASCIIDOC_SOURCE_RE.match(lines[index]):
            marker_index = index
            candidate = index + 1
            while candidate < len(lines) and not lines[candidate].strip():
                candidate += 1
            if candidate < len(lines) and scanner.ASCIIDOC_BLOCK_DELIMITER_RE.match(
                lines[candidate]
            ):
                delimiter = candidate
        elif scanner.ASCIIDOC_BLOCK_DELIMITER_RE.match(lines[index]):
            delimiter = index

        if delimiter is None:
            index += 1
            continue

        closing = delimiter + 1
        while closing < len(lines) and not scanner.ASCIIDOC_BLOCK_DELIMITER_RE.match(
            lines[closing]
        ):
            closing += 1
        if closing >= len(lines):
            index += 1
            continue

        flush_segment(marker_index if marker_index is not None else delimiter)
        if marker_index is not None:
            records.append(scanner.ScanRecord(((marker_index + 1, lines[marker_index]),)))
        records.append(scanner.ScanRecord(((delimiter + 1, lines[delimiter]),)))

        content_spans = implementation.fenced_content_spans(
            lines, delimiter + 1, closing
        )
        records.extend(scanner.records_from_spans(lines, content_spans))
        records.append(scanner.ScanRecord(((closing + 1, lines[closing]),)))

        index = closing + 1
        segment_start = index

    flush_segment(len(lines))
    return records


RST_SIMPLE_BORDER_RE = re.compile(
    r"^\s*(?:[=~-]{2,}[ \t]+)+[=~-]{2,}\s*$"
)
RST_GRID_BORDER_RE = re.compile(r"^\s*\+(?:[-=]+\+)+\s*$")


def _append_record(
    records: list[scanner.ScanRecord], line_number: int, text: str
) -> None:
    if text.strip():
        records.append(scanner.ScanRecord(((line_number, text),)))


def _simple_table_cells(border: str, row: str) -> list[str]:
    spans = [match.span() for match in re.finditer(r"[=~-]{2,}", border)]
    if len(spans) < 2:
        return [row]
    cells: list[str] = []
    for position, (start, end) in enumerate(spans):
        next_start = spans[position + 1][0] if position + 1 < len(spans) else None
        cell = row[start:next_start] if next_start is not None else row[start:]
        if cell.strip():
            cells.append(cell)
    return cells


def _grid_table_cells(row: str) -> list[str]:
    stripped = row.strip()
    if not stripped.startswith("|"):
        return [row]
    return stripped.strip("|").split("|")


def rst_records(lines: list[str]) -> list[scanner.ScanRecord]:
    """Apply reStructuredText-aware table and multiline-cell boundaries."""
    records: list[scanner.ScanRecord] = []
    segment_start = 0
    index = 0

    def flush_plain(end: int) -> None:
        nonlocal segment_start
        if segment_start < end:
            records.extend(scanner.markdown_records(lines[segment_start:end], segment_start))

    while index < len(lines):
        line = lines[index]
        simple = RST_SIMPLE_BORDER_RE.match(line)
        grid = RST_GRID_BORDER_RE.match(line)
        if not simple and not grid:
            index += 1
            continue

        flush_plain(index)
        border = line
        _append_record(records, index + 1, line)
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
                if RST_GRID_BORDER_RE.match(current):
                    flush_grid_cells()
                    _append_record(records, index + 1, current)
                elif current.strip().startswith("|"):
                    cells = _grid_table_cells(current)
                    while len(columns) < len(cells):
                        columns.append([])
                    for position, cell in enumerate(cells):
                        if cell.strip():
                            columns[position].append((index + 1, cell))
                else:
                    flush_grid_cells()
                    _append_record(records, index + 1, current)
                index += 1
            flush_grid_cells()
        else:
            while index < len(lines) and lines[index].strip():
                current = lines[index]
                if RST_SIMPLE_BORDER_RE.match(current):
                    _append_record(records, index + 1, current)
                else:
                    for cell in _simple_table_cells(border, current):
                        _append_record(records, index + 1, cell)
                index += 1

        segment_start = index

    flush_plain(len(lines))
    return records


_original_document_records = scanner.document_records


def document_records(path: str, lines: list[str]) -> list[scanner.ScanRecord]:
    if Path(path).suffix.lower() == ".rst":
        return rst_records(lines)
    return _original_document_records(path, lines)


# Patch the module globals used by the established scanner functions.
scanner.comparison_args = comparison_args
implementation.comparison_args = comparison_args
implementation.asciidoc_segment_records = asciidoc_segment_records
implementation.asciidoc_records = asciidoc_records
scanner.asciidoc_records = asciidoc_records
scanner.document_records = document_records
implementation.document_records = document_records

# Preserve the import surface expected by the test suite and direct callers.
for _name in dir(implementation):
    if not _name.startswith("_"):
        globals().setdefault(_name, getattr(implementation, _name))

globals().update(
    {
        "comparison_args": comparison_args,
        "split_unescaped_asciidoc_pipes": split_unescaped_asciidoc_pipes,
        "asciidoc_segment_records": asciidoc_segment_records,
        "asciidoc_records": asciidoc_records,
        "rst_records": rst_records,
        "document_records": document_records,
        "scan_file": scanner.scan_file,
    }
)


def main() -> int:
    return scanner.main()


if __name__ == "__main__":
    sys.exit(main())
