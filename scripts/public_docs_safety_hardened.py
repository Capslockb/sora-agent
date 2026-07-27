#!/usr/bin/env python3
"""Hardened entrypoint for the public documentation safety scanner.

This module keeps the existing scanner's range selection, diagnostics, and rules,
while replacing two format-boundary helpers that need stricter behavior:

* fenced examples distinguish explicit commands from wrapped prose;
* HTML records retain descendant text within one containing element without
  joining unrelated sibling elements.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser

import public_docs_safety as scanner


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
    "enable",
    "git",
    "go",
    "install",
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
    "pwsh",
    "pytest",
    "python",
    "python3",
    "rm",
    "ruff",
    "sh",
    "sora",
    "sudo",
    "systemctl",
    "tox",
    "uv",
    "wget",
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
    "script",
    "section",
    "style",
    "summary",
    "table",
    "tbody",
    "td",
    "template",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
}


def _command_head(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""
    if stripped.startswith(("$ ", "> ")):
        stripped = stripped[2:].lstrip()
    elif "> " in stripped.split(maxsplit=1)[0]:
        stripped = stripped.split(">", 1)[1].lstrip()
    return stripped.split(maxsplit=1)[0].lower() if stripped else ""


def is_explicit_command_line(line: str) -> bool:
    """Return true only for lines with concrete command syntax.

    The former generic two-word heuristic classified ordinary prose such as
    ``ignore everything`` and ``previous policy`` as separate commands. That
    allowed a wrapped strong-rule phrase to evade scanning.
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return False
    if scanner.PROMPTED_COMMAND_RE.match(line):
        return True
    if not scanner.SIMPLE_COMMAND_RE.match(line):
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
        or scanner.leading_indent_width(current) > scanner.leading_indent_width(previous)
    )


def fenced_content_spans(
    lines: list[str], start: int, end: int
) -> list[tuple[int, int]]:
    """Return format-aware 1-based spans for one fenced block.

    Explicit command records remain separate. Consecutive non-command text is
    kept together so strong rules can see instructions wrapped by Markdown.
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


@dataclass
class _HTMLFrame:
    tag: str
    parts: list[tuple[int, str]] = field(default_factory=list)


class HTMLRecordParser(HTMLParser):
    """Build records from visible HTML structure rather than parser callbacks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.records: list[scanner.ScanRecord] = []
        self.frames: list[_HTMLFrame] = []
        self.root_parts: list[tuple[int, str]] = []

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

    def _emit_tag(self, text: str) -> None:
        parts = self._parts(self.getpos()[0], text)
        if parts:
            self.records.append(scanner.ScanRecord(tuple(parts)))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self._emit_tag(self.get_starttag_text() or f"<{tag}>")
        if tag in HTML_BLOCK_TAGS:
            self._emit(self._target())
            self.frames.append(_HTMLFrame(tag))

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self._emit_tag(self.get_starttag_text() or f"<{tag}/>")

    def handle_data(self, data: str) -> None:
        self._target().extend(self._parts(self.getpos()[0], data))

    def handle_comment(self, data: str) -> None:
        parts = self._parts(self.getpos()[0], data)
        if parts:
            self.records.append(scanner.ScanRecord(tuple(parts)))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
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


# Patch the implementation module before its main routine or callers resolve
# these helpers through module globals.
scanner.is_independent_command_line = is_explicit_command_line
scanner.fenced_content_spans = fenced_content_spans
scanner.html_records = html_records


def main() -> int:
    return scanner.main()


if __name__ == "__main__":
    sys.exit(main())
