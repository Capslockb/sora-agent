#!/usr/bin/env python3
"""Hardened entrypoint for the public documentation safety scanner.

The range-selection, rule, and reporting implementation lives in the sibling
``public_docs_safety_core`` module. This entrypoint supplies format-aware
boundaries for Markdown code blocks, AsciiDoc, and rendered HTML content.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

_CORE_PATH = Path(__file__).with_name("public_docs_safety_core.py")
_CORE_SPEC = importlib.util.spec_from_file_location(
    "_public_docs_safety_core", _CORE_PATH
)
if _CORE_SPEC is None or _CORE_SPEC.loader is None:
    raise RuntimeError("unable to load public docs safety core")
scanner = importlib.util.module_from_spec(_CORE_SPEC)
sys.modules.setdefault("_public_docs_safety_core", scanner)
_CORE_SPEC.loader.exec_module(scanner)

# Preserve the established import surface for tests and callers. Hardened
# helpers below replace selected core functions before scanning starts.
for _name in dir(scanner):
    if not _name.startswith("_"):
        globals().setdefault(_name, getattr(scanner, _name))


COMMAND_HEADS = {
    "bash",
    "bun",
    "cargo",
    "cat",
    "cd",
    "chmod",
    "chown",
    "cp",
    "curl",
    "disable",
    "docker",
    "docker-compose",
    "echo",
    "enable",
    "env",
    "export",
    "git",
    "go",
    "install",
    "ls",
    "make",
    "mkdir",
    "mv",
    "node",
    "npm",
    "npx",
    "pip",
    "pip3",
    "pipx",
    "pnpm",
    "poetry",
    "powershell",
    "printf",
    "pwd",
    "pwsh",
    "pytest",
    "python",
    "python3",
    "rm",
    "ruff",
    "set",
    "sh",
    "sora",
    "source",
    "sudo",
    "systemctl",
    "tox",
    "unset",
    "uv",
    "wget",
    "which",
    "yarn",
}

HTML_BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "body",
    "button",
    "dd",
    "details",
    "dialog",
    "div",
    "dl",
    "dt",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "html",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "summary",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
}
HTML_HIDDEN_TAGS = {"script", "style", "template"}
HTML_VISIBLE_ATTRS = {"alt", "aria-label", "placeholder", "title", "value"}
ASCIIDOC_TABLE_DELIMITER_RE = re.compile(r"^\s*\|={3,}\s*$")


def _command_head(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""
    if stripped.startswith(("$ ", "> ")):
        stripped = stripped[2:].lstrip()
    return stripped.split(maxsplit=1)[0].lower() if stripped else ""


def is_explicit_command_line(line: str) -> bool:
    """Return true only for lines with concrete command syntax.

    A shell prompt is presentation syntax, not proof that the following words
    are an independent command. Prompted prose such as ``$ ignore everything``
    remains available to adjacent strong-rule scanning.
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return False

    prompted = bool(scanner.PROMPTED_COMMAND_RE.match(line))
    if not prompted and not scanner.SIMPLE_COMMAND_RE.match(line):
        return False

    head = _command_head(line)
    if not head:
        return False
    return (
        head in COMMAND_HEADS
        or head.startswith("-")
        or any(marker in head for marker in ("/", "\\", ".", ":", "_"))
    )


def _is_command_continuation(previous: str, current: str) -> bool:
    stripped = current.lstrip()
    return bool(
        previous.rstrip().endswith(("\\", "&&", "||", "|"))
        or stripped.startswith(("-", "&&", "||", "|"))
        or scanner.leading_indent_width(current)
        > scanner.leading_indent_width(previous)
    )


def fenced_content_spans(
    lines: list[str], start: int, end: int
) -> list[tuple[int, int]]:
    """Split code-like content without losing wrapped prose instructions.

    Explicit commands and their continuations remain independent records.
    Consecutive non-command text stays together so strong rules can detect
    instructions wrapped across the scanner's bounded line window.
    """
    spans: list[tuple[int, int]] = []
    index = start
    while index < end:
        if not lines[index].strip():
            index += 1
            continue

        block_start = index
        if is_explicit_command_line(lines[index]):
            index += 1
            while index < end and lines[index].strip() and _is_command_continuation(
                lines[index - 1], lines[index]
            ):
                index += 1
            spans.append((block_start + 1, index))
            continue

        index += 1
        while (
            index < end
            and lines[index].strip()
            and not is_explicit_command_line(lines[index])
        ):
            index += 1
        spans.append((block_start + 1, index))
    return spans


_CORE_LOGICAL_SPANS = scanner.logical_spans


def logical_spans(lines: list[str]) -> list[tuple[int, int]]:
    """Apply command-aware grouping to Markdown indented code blocks.

    The core parser already identifies structural Markdown records but emits
    each top-level indented-code line separately. Consecutive indented-code
    records are regrouped with the same rules used for fenced/source content,
    closing cross-line evasions without joining independent commands.
    """
    original = _CORE_LOGICAL_SPANS(lines)
    spans: list[tuple[int, int]] = []
    index = 0
    while index < len(original):
        start, end = original[index]
        if start == end and scanner.INDENTED_CODE_RE.match(lines[start - 1]):
            run_start = start
            run_end = end
            cursor = index + 1
            while cursor < len(original):
                next_start, next_end = original[cursor]
                if (
                    next_start == next_end
                    and next_start == run_end + 1
                    and scanner.INDENTED_CODE_RE.match(lines[next_start - 1])
                ):
                    run_end = next_end
                    cursor += 1
                    continue
                break
            spans.extend(fenced_content_spans(lines, run_start - 1, run_end))
            index = cursor
            continue
        spans.append((start, end))
        index += 1
    return spans


def asciidoc_segment_records(
    lines: list[str], offset: int = 0
) -> list[scanner.ScanRecord]:
    """Parse AsciiDoc prose while keeping native table cells independent."""
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
        if not ASCIIDOC_TABLE_DELIMITER_RE.match(lines[index]):
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

        while index < len(lines) and not ASCIIDOC_TABLE_DELIMITER_RE.match(
            lines[index]
        ):
            line = lines[index]
            line_number = offset + index + 1
            if "|" in line:
                chunks = line.split("|")
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
    """Parse AsciiDoc source blocks and native table boundaries."""
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
        if not scanner.ASCIIDOC_SOURCE_RE.match(lines[index]):
            index += 1
            continue

        delimiter = index + 1
        while delimiter < len(lines) and not lines[delimiter].strip():
            delimiter += 1
        if delimiter >= len(lines) or not scanner.ASCIIDOC_BLOCK_DELIMITER_RE.match(
            lines[delimiter]
        ):
            index += 1
            continue

        flush_segment(index)
        records.append(scanner.ScanRecord(((index + 1, lines[index]),)))
        records.append(scanner.ScanRecord(((delimiter + 1, lines[delimiter]),)))

        closing = delimiter + 1
        while closing < len(lines) and not scanner.ASCIIDOC_BLOCK_DELIMITER_RE.match(
            lines[closing]
        ):
            closing += 1

        source_end = closing if closing < len(lines) else len(lines)
        source_spans = fenced_content_spans(lines, delimiter + 1, source_end)
        records.extend(scanner.records_from_spans(lines, source_spans))

        if closing < len(lines):
            records.append(scanner.ScanRecord(((closing + 1, lines[closing]),)))
            index = closing + 1
        else:
            index = closing
        segment_start = index

    flush_segment(len(lines))
    return records


class _HTMLFrame:
    __slots__ = ("tag", "parts")

    def __init__(self, tag: str) -> None:
        self.tag = tag
        self.parts: list[tuple[int, str]] = []


class HTMLRecordParser(HTMLParser):
    """Build records from rendered HTML structure, excluding hidden content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.records: list[scanner.ScanRecord] = []
        self.frames: list[_HTMLFrame] = []
        self.root_parts: list[tuple[int, str]] = []
        self.hidden_stack: list[str] = []

    @staticmethod
    def _parts(start_line: int, text: str) -> list[tuple[int, str]]:
        return [
            (start_line + offset, line)
            for offset, line in enumerate(text.splitlines() or [text])
            if line.strip()
        ]

    def _target(self) -> list[tuple[int, str]]:
        return self.frames[-1].parts if self.frames else self.root_parts

    def _emit(self, parts: list[tuple[int, str]]) -> None:
        if parts:
            self.records.append(scanner.ScanRecord(tuple(parts)))
            parts.clear()

    def _emit_visible_attrs(
        self,
        attrs: list[tuple[str, str | None]],
        raw_tag: str | None,
    ) -> None:
        start_line = self.getpos()[0]
        cursor = 0
        for name, value in attrs:
            if not value or name.lower() not in HTML_VISIBLE_ATTRS:
                continue

            attr_line = start_line
            if raw_tag:
                attr_re = re.compile(
                    rf"(?is)(?<![\w:-]){re.escape(name)}\s*=\s*"
                    rf"(?:\"[^\"]*\"|'[^']*'|[^\s>]+)"
                )
                match = attr_re.search(raw_tag, cursor) or attr_re.search(raw_tag)
                if match:
                    attr_line += raw_tag[: match.start()].count("\n")
                    cursor = match.end()

            parts = self._parts(attr_line, value)
            if parts:
                self.records.append(scanner.ScanRecord(tuple(parts)))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if self.hidden_stack:
            if tag in HTML_HIDDEN_TAGS:
                self.hidden_stack.append(tag)
            return
        if tag in HTML_HIDDEN_TAGS:
            self._emit(self._target())
            self.hidden_stack.append(tag)
            return

        self._emit_visible_attrs(attrs, self.get_starttag_text())
        if tag in HTML_BLOCK_TAGS:
            self._emit(self._target())
            self.frames.append(_HTMLFrame(tag))

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        tag = tag.lower()
        if self.hidden_stack or tag in HTML_HIDDEN_TAGS:
            return
        self._emit_visible_attrs(attrs, self.get_starttag_text())

    def handle_data(self, data: str) -> None:
        if not self.hidden_stack:
            self._target().extend(self._parts(self.getpos()[0], data))

    def handle_comment(self, data: str) -> None:
        # HTML comments are non-rendered content, like script/style/template.
        return

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.hidden_stack:
            if tag == self.hidden_stack[-1]:
                self.hidden_stack.pop()
            return
        if tag not in HTML_BLOCK_TAGS or not self.frames:
            return

        match = next(
            (
                index
                for index in range(len(self.frames) - 1, -1, -1)
                if self.frames[index].tag == tag
            ),
            None,
        )
        if match is None:
            return
        while len(self.frames) > match:
            frame = self.frames.pop()
            self._emit(frame.parts)

    def close(self) -> None:
        super().close()
        while self.frames:
            self._emit(self.frames.pop().parts)
        self._emit(self.root_parts)


def html_records(lines: list[str]) -> list[scanner.ScanRecord]:
    parser = HTMLRecordParser()
    try:
        parser.feed("\n".join(lines))
        parser.close()
    except Exception:
        return [
            scanner.ScanRecord(((line_number, line),))
            for line_number, line in enumerate(lines, start=1)
            if line.strip()
        ]
    return parser.records


# Patch the core module before its main routine or callers resolve these helpers
# through module globals. Re-export the hardened helpers from this entrypoint.
scanner.is_independent_command_line = is_explicit_command_line
scanner.fenced_content_spans = fenced_content_spans
scanner.logical_spans = logical_spans
scanner.asciidoc_records = asciidoc_records
scanner.html_records = html_records
is_independent_command_line = is_explicit_command_line


def main() -> int:
    return scanner.main()


if __name__ == "__main__":
    sys.exit(main())
