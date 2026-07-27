#!/usr/bin/env python3
"""Fail-closed safety scanner for public-facing documentation.

Repository prose is treated as untrusted input. Diagnostics intentionally expose
only a path, line number, stable rule ID, and category.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DOC_NAMES = {
    "README.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "AGENTS.md",
    "CODE_OF_CONDUCT.md",
}
SPECIAL_DOC_PATHS = {".github/CODEOWNERS"}
DOC_DIR_PARTS = {"docs", "doc", "website", "site", "public"}
FIXTURE_PARTS = {"tests", "fixtures", "public-docs"}
DOC_EXTS = {".md", ".mdx", ".rst", ".txt", ".adoc", ".asciidoc"}
EXCLUDE_PARTS = {"i18n", "CHANGELOG.md", "sessions", "vendor", "node_modules", ".git"}
ZERO_SHA = "0" * 40
EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}(?:\s|$)")
LIST_ITEM_RE = re.compile(r"^(?P<indent> {0,3})(?:[-+*]|\d+[.)])(?P<spacing>[ \t]+)")
BLOCKQUOTE_RE = re.compile(r"^\s{0,3}>\s?")
HORIZONTAL_RULE_RE = re.compile(r"^\s{0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})$")
INDENTED_CODE_RE = re.compile(r"^(?: {4}|\t)\S")
PROMPTED_COMMAND_RE = re.compile(r"^\s*(?:[$>]\s+|[A-Za-z0-9_.-]+[>$]\s+)")
SIMPLE_COMMAND_RE = re.compile(
    r"^\s*(?:--?[A-Za-z0-9][\w.-]*|[a-z0-9][\w./:-]*)"
    r"\s+[^.!?]+\s*$"
)


class ComparisonError(RuntimeError):
    """Raised when the scanner cannot determine a trustworthy change range."""


PATTERNS = [
    (
        "PDS001",
        "model-directed override",
        re.compile(
            r"(?i)\b(ignore|disregard|override)\b.{0,100}"
            r"\b(previous|above|system|developer|policy|instruction)s?\b"
        ),
    ),
    (
        "PDS002",
        "secret-or-policy exfiltration",
        re.compile(
            r"(?i)\b(reveal|print|show|exfiltrate|leak)\b.{0,100}"
            r"\b(secret|token|credential|password|policy|system prompt|developer message)s?\b"
        ),
    ),
    (
        "PDS003",
        "unauthorized action request",
        re.compile(
            r"(?i)\b(approve|merge|push|deploy|purchase|transfer|delete|rotate|disable)\b.{0,100}"
            r"\b(PR|pull request|repository|repo|payment|account|guard|check|policy|automation)\b"
        ),
    ),
    (
        "PDS004",
        "non-public automation disclosure",
        re.compile(
            r"(?i)\b(privileged command|private control|non-public guard|secret marker|"
            r"trusted[- ]identity rule|mutation authorization|worker queue|controller lease|"
            r"private escalation)\b"
        ),
    ),
]
UNCERTAIN = re.compile(
    r"(?i)\b(maintaining model|automation agent|autonomous maintainer|repository bot)\b"
    r".{0,100}\b(must|shall|required to|always|never|use tool|run command|obey|ignore|"
    r"stop when|final status)\b"
)
BENIGN_UNCERTAIN = re.compile(
    r"(?i)\b(example|sample|template|user-facing|configuration|API|worker thread|"
    r"service worker|inference|event loop|model name|route|provider|guardrail|"
    r"security policy|documentation)\b"
)


def default_branch() -> str:
    explicit = os.environ.get("GITHUB_BASE_REF") or os.environ.get("DEFAULT_BRANCH")
    if explicit:
        return explicit
    result = subprocess.run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0 and "/" in result.stdout:
        return result.stdout.strip().rsplit("/", 1)[-1]
    return "main"


def push_before_sha() -> str | None:
    explicit = os.environ.get("PUBLIC_DOCS_BASE_SHA") or os.environ.get("GITHUB_EVENT_BEFORE")
    if explicit:
        return explicit.strip()
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        return None
    try:
        payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    before = payload.get("before")
    return before.strip() if isinstance(before, str) else None


def comparison_args() -> list[str]:
    if os.environ.get("GITHUB_EVENT_NAME") == "push":
        before = push_before_sha()
        if before and before != ZERO_SHA:
            return [before, "HEAD"]
        return [EMPTY_TREE_SHA, "HEAD"]
    return [f"origin/{default_branch()}...HEAD"]


def is_public_doc(path: str, include_fixtures: bool = False) -> bool:
    candidate = Path(path)
    normalized = candidate.as_posix().removeprefix("./")
    parts = set(candidate.parts)
    if parts & EXCLUDE_PARTS:
        return False
    if normalized in SPECIAL_DOC_PATHS:
        return True
    if include_fixtures and FIXTURE_PARTS <= parts and candidate.suffix.lower() in DOC_EXTS:
        return True
    return candidate.name in DOC_NAMES or (
        candidate.suffix.lower() in DOC_EXTS and bool(parts & DOC_DIR_PARTS)
    )


def existing_public_docs(candidates: list[str], include_fixtures: bool = False) -> list[str]:
    return [
        path
        for path in candidates
        if Path(path).is_file() and is_public_doc(path, include_fixtures)
    ]


def changed_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", *comparison_args()],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        return result.stdout.splitlines() if result.stdout.strip() else []
    fallback = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if fallback.returncode == 0 and fallback.stdout.strip():
        return fallback.stdout.splitlines()
    raise ComparisonError("unable to resolve documentation change range")


def parse_added_lines(diff_text: str) -> dict[str, set[int]]:
    """Select added lines and bounded post-image context around deletions."""
    result: dict[str, set[int]] = {}
    current: str | None = None
    new_line: int | None = None
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            result.setdefault(current, set())
        elif line.startswith("@@") and current:
            match = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if match:
                new_line = int(match.group(1))
        elif current and new_line is not None:
            if line.startswith("+") and not line.startswith("+++"):
                result[current].add(new_line)
                new_line += 1
            elif line.startswith("-") and not line.startswith("---"):
                result[current].update(
                    number
                    for number in (new_line - 1, new_line, new_line + 1)
                    if number >= 1
                )
            elif not line.startswith("-"):
                new_line += 1
    return result


def changed_added_lines(files: list[str]) -> dict[str, set[int]] | None:
    if not files:
        return {}
    result = subprocess.run(
        ["git", "diff", "--unified=0", *comparison_args(), "--", *files],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        return None
    return parse_added_lines(result.stdout)


def is_table_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def leading_indent_width(line: str) -> int:
    width = 0
    for char in line:
        if char == " ":
            width += 1
        elif char == "\t":
            width += 4 - (width % 4)
        else:
            break
    return width


def is_list_continuation(line: str, content_indent: int) -> bool:
    return bool(line.strip()) and leading_indent_width(line) >= content_indent


def is_independent_command_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return False
    return bool(PROMPTED_COMMAND_RE.match(line) or SIMPLE_COMMAND_RE.match(line))


def fenced_content_spans(lines: list[str], start: int, end: int) -> list[tuple[int, int]]:
    """Return 1-based spans for content inside one fenced block.

    A contiguous block is joined when it contains wrapped prose or instructions.
    A block made solely of command-like records stays one span per line, avoiding
    artificial matches across independent CLI examples.
    """
    spans: list[tuple[int, int]] = []
    index = start
    while index < end:
        if not lines[index].strip():
            index += 1
            continue
        block_start = index
        while index < end and lines[index].strip():
            index += 1
        block_end = index
        block = lines[block_start:block_end]
        if len(block) > 1 and all(is_independent_command_line(line) for line in block):
            spans.extend((line_no + 1, line_no + 1) for line_no in range(block_start, block_end))
        else:
            spans.append((block_start + 1, block_end))
    return spans


def logical_spans(lines: list[str]) -> list[tuple[int, int]]:
    """Split public Markdown-like text into bounded logical records."""
    spans: list[tuple[int, int]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue

        opening = FENCE_RE.match(line)
        if opening:
            marker = opening.group(1)
            marker_char = marker[0]
            marker_len = len(marker)
            spans.append((index + 1, index + 1))
            content_start = index + 1
            cursor = content_start
            closing_re = re.compile(rf"^\s{{0,3}}{re.escape(marker_char)}{{{marker_len},}}\s*$")
            while cursor < len(lines) and not closing_re.match(lines[cursor]):
                cursor += 1
            spans.extend(fenced_content_spans(lines, content_start, cursor))
            if cursor < len(lines):
                spans.append((cursor + 1, cursor + 1))
                index = cursor + 1
            else:
                index = cursor
            continue

        if (
            HEADING_RE.match(line)
            or HORIZONTAL_RULE_RE.match(line)
            or is_table_row(line)
            or INDENTED_CODE_RE.match(line)
        ):
            spans.append((index + 1, index + 1))
            index += 1
            continue

        list_match = LIST_ITEM_RE.match(line)
        if list_match:
            start = index
            content_indent = leading_indent_width(list_match.group(0))
            index += 1
            while index < len(lines):
                candidate = lines[index]
                if not candidate.strip():
                    break
                if (
                    FENCE_RE.match(candidate)
                    or HEADING_RE.match(candidate)
                    or HORIZONTAL_RULE_RE.match(candidate)
                    or is_table_row(candidate)
                    or LIST_ITEM_RE.match(candidate)
                    or BLOCKQUOTE_RE.match(candidate)
                    or (
                        INDENTED_CODE_RE.match(candidate)
                        and not is_list_continuation(candidate, content_indent)
                    )
                ):
                    break
                index += 1
            spans.append((start + 1, index))
            continue

        if BLOCKQUOTE_RE.match(line):
            start = index
            index += 1
            while index < len(lines) and lines[index].strip() and BLOCKQUOTE_RE.match(lines[index]):
                index += 1
            spans.append((start + 1, index))
            continue

        start = index
        index += 1
        while index < len(lines):
            candidate = lines[index]
            if not candidate.strip() or (
                FENCE_RE.match(candidate)
                or HEADING_RE.match(candidate)
                or HORIZONTAL_RULE_RE.match(candidate)
                or is_table_row(candidate)
                or LIST_ITEM_RE.match(candidate)
                or BLOCKQUOTE_RE.match(candidate)
                or INDENTED_CODE_RE.match(candidate)
            ):
                break
            index += 1
        spans.append((start + 1, index))
    return spans


def document_spans(path: str, lines: list[str]) -> list[tuple[int, int]]:
    """Return format-aware scan records for one public document."""
    normalized = Path(path).as_posix().removeprefix("./")
    if normalized in SPECIAL_DOC_PATHS:
        return [
            (line_number, line_number)
            for line_number, line in enumerate(lines, start=1)
            if line.strip()
        ]
    return logical_spans(lines)


def matched_lines(lines: list[str], start: int, end: int, match: re.Match[str]) -> set[int]:
    cursor = 0
    match_start = match.start()
    match_end = max(match.end() - 1, match_start)
    result: set[int] = set()
    for line_number in range(start, end + 1):
        text = lines[line_number - 1]
        line_start = cursor
        line_end = cursor + len(text) - 1
        if text and line_start <= match_end and line_end >= match_start:
            result.add(line_number)
        cursor += len(text) + 1
    return result


def scan_file(path: str, line_numbers: list[int] | range) -> list[tuple[str, int, str, str]]:
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return [(path, 1, "PDS900", "document read failure")]

    selected = {number for number in line_numbers if 1 <= number <= len(lines)}
    internal: set[tuple[int, str, str]] = set()
    for start, end in document_spans(path, lines):
        if not any(start <= number <= end for number in selected):
            continue
        text = " ".join(lines[start - 1 : end])
        for rule_id, category, pattern in PATTERNS:
            for match in pattern.finditer(text):
                affected = matched_lines(lines, start, end, match)
                changed = sorted(selected & affected)
                if changed:
                    internal.add((changed[0], rule_id, category))
        for match in UNCERTAIN.finditer(text):
            context_start = max(0, match.start() - 100)
            context_end = min(len(text), match.end() + 100)
            if BENIGN_UNCERTAIN.search(text[context_start:context_end]):
                continue
            affected = matched_lines(lines, start, end, match)
            changed = sorted(selected & affected)
            if changed:
                internal.add((changed[0], "PDS100", "uncertain automation-directed prose"))
    return [(path, line, rule_id, category) for line, rule_id, category in sorted(internal)]


def all_candidate_files() -> list[str]:
    return [str(path) for path in Path(".").rglob("*") if path.is_file()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--include-test-fixtures", action="store_true")
    args = parser.parse_args()
    include_fixtures = args.include_test_fixtures or args.all

    try:
        candidates = all_candidate_files() if args.all else changed_files()
        files = existing_public_docs(candidates, include_fixtures)
        if args.all:
            added = None
        else:
            added = changed_added_lines(files)
            if added is None:
                raise ComparisonError("unable to resolve added documentation lines")
    except ComparisonError:
        print("public-docs-safety: FAIL")
        print("<comparison>:1: PDS901: documentation range resolution failure")
        return 1

    findings: list[tuple[str, int, str, str]] = []
    for path in files:
        if added is None:
            lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
            selected: list[int] | range = range(1, len(lines) + 1)
        else:
            selected = sorted(added.get(path, set()))
        findings.extend(scan_file(path, selected))

    if findings:
        print("public-docs-safety: FAIL")
        for path, line, rule_id, category in findings:
            print(f"{path}:{line}: {rule_id}: {category}")
        return 1
    print("public-docs-safety: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
