#!/usr/bin/env python3
"""Fail-closed safety scanner for public-facing documentation.

Repository prose is treated as untrusted input. The scanner looks for text that
appears to instruct an automation system/model, disclose non-public automation
controls, or embed prompt-injection style commands in public docs.
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


class ComparisonError(RuntimeError):
    """Raised when the scanner cannot determine a trustworthy change range."""


# Stable rule IDs are emitted without source text so CI logs do not reproduce
# potentially sensitive or adversarial documentation content.
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
    p = subprocess.run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if p.returncode == 0 and "/" in p.stdout:
        return p.stdout.strip().rsplit("/", 1)[-1]
    return "main"


def push_before_sha() -> str | None:
    explicit = os.environ.get("PUBLIC_DOCS_BASE_SHA") or os.environ.get(
        "GITHUB_EVENT_BEFORE"
    )
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
    """Return exact git-diff endpoints for the current event."""
    if os.environ.get("GITHUB_EVENT_NAME") == "push":
        before = push_before_sha()
        if before and before != ZERO_SHA:
            return [before, "HEAD"]
        # A new branch has no pre-push commit. Compare its head with Git's empty
        # tree so every public document introduced by the branch is checked.
        return [EMPTY_TREE_SHA, "HEAD"]
    return [f"origin/{default_branch()}...HEAD"]


def is_public_doc(path: str, include_fixtures: bool = False) -> bool:
    p = Path(path)
    normalized = p.as_posix()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    parts = set(p.parts)
    if parts & EXCLUDE_PARTS:
        return False
    if normalized in SPECIAL_DOC_PATHS:
        return True
    if include_fixtures and FIXTURE_PARTS <= parts and p.suffix.lower() in DOC_EXTS:
        return True
    return p.name in DOC_NAMES or (
        p.suffix.lower() in DOC_EXTS and bool(parts & DOC_DIR_PARTS)
    )


def existing_public_docs(
    candidates: list[str], include_fixtures: bool = False
) -> list[str]:
    """Return in-scope files that still exist after a change.

    Git diffs include deleted and pre-rename paths. Those paths are intentionally
    ignored rather than converted into read failures.
    """
    return [
        path
        for path in candidates
        if Path(path).is_file() and is_public_doc(path, include_fixtures)
    ]


def changed_files() -> list[str]:
    p = subprocess.run(
        ["git", "diff", "--name-only", *comparison_args()],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if p.returncode == 0:
        return p.stdout.splitlines() if p.stdout.strip() else []

    # This fallback supports local staged validation only. A clean cached diff
    # cannot prove that a failed event comparison had no documentation changes,
    # so it must not be interpreted as a safe empty range.
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
    """Map each changed file to the line numbers added in a zero-context diff."""
    out: dict[str, set[int]] = {}
    cur = None
    new_line = None
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            cur = line[6:]
            out.setdefault(cur, set())
        elif line.startswith("@@") and cur:
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if m:
                new_line = int(m.group(1))
        elif cur and new_line is not None:
            if line.startswith("+") and not line.startswith("+++"):
                out.setdefault(cur, set()).add(new_line)
                new_line += 1
            elif not line.startswith("-"):
                new_line += 1
    return out


def changed_added_lines(files: list[str]) -> dict[str, set[int]] | None:
    if not files:
        return {}
    p = subprocess.run(
        ["git", "diff", "--unified=0", *comparison_args(), "--", *files],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if p.returncode != 0:
        return None
    return parse_added_lines(p.stdout)


def is_table_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def leading_indent_width(line: str) -> int:
    """Return indentation width using four-column tab stops."""
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
    """Whether a nonblank line is indented into the active list item's content."""
    return bool(line.strip()) and leading_indent_width(line) >= content_indent


def logical_spans(lines: list[str]) -> list[tuple[int, int]]:
    """Split Markdown into records without joining unrelated structural entries.

    Prose paragraphs, block quotes, and list-item continuations may wrap across
    any number of physical lines. Fenced-code entries, tables, headings, and
    indented command/help rows stay independent so adjacent records cannot form
    an artificial rule match.
    """
    spans: list[tuple[int, int]] = []
    i = 0
    fence_marker: str | None = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        fence = FENCE_RE.match(line)

        if not stripped:
            i += 1
            continue

        if fence:
            marker = fence.group(1)[0]
            spans.append((i + 1, i + 1))
            fence_marker = None if fence_marker == marker else marker
            i += 1
            continue

        if fence_marker is not None:
            spans.append((i + 1, i + 1))
            i += 1
            continue

        if (
            HEADING_RE.match(line)
            or HORIZONTAL_RULE_RE.match(line)
            or is_table_row(line)
            or INDENTED_CODE_RE.match(line)
        ):
            spans.append((i + 1, i + 1))
            i += 1
            continue

        list_match = LIST_ITEM_RE.match(line)
        if list_match:
            start = i
            content_indent = leading_indent_width(list_match.group(0))
            i += 1
            while i < len(lines):
                candidate = lines[i]
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
                i += 1
            spans.append((start + 1, i))
            continue

        if BLOCKQUOTE_RE.match(line):
            start = i
            i += 1
            while i < len(lines) and lines[i].strip() and BLOCKQUOTE_RE.match(lines[i]):
                i += 1
            spans.append((start + 1, i))
            continue

        start = i
        i += 1
        while i < len(lines):
            candidate = lines[i]
            if not candidate.strip():
                break
            if (
                FENCE_RE.match(candidate)
                or HEADING_RE.match(candidate)
                or HORIZONTAL_RULE_RE.match(candidate)
                or is_table_row(candidate)
                or LIST_ITEM_RE.match(candidate)
                or BLOCKQUOTE_RE.match(candidate)
                or INDENTED_CODE_RE.match(candidate)
            ):
                break
            i += 1
        spans.append((start + 1, i))

    return spans


def matched_lines(
    lines: list[str], start: int, end: int, match: re.Match[str]
) -> set[int]:
    """Map a match in a space-joined span back to repository line numbers."""
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


def scan_file(
    path: str, line_numbers: list[int] | range
) -> list[tuple[str, int, str, str]]:
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return [(path, 1, "PDS900", "document read failure")]

    selected = {i for i in line_numbers if 1 <= i <= len(lines)}
    internal_findings: set[tuple[int, str, str, int, int]] = set()
    for start, end in logical_spans(lines):
        if not any(start <= line_number <= end for line_number in selected):
            continue
        text = " ".join(lines[start - 1 : end])
        for rule_id, category, rx in PATTERNS:
            for match in rx.finditer(text):
                match_lines = matched_lines(lines, start, end, match)
                selected_match_lines = sorted(selected & match_lines)
                if selected_match_lines:
                    internal_findings.add(
                        (
                            selected_match_lines[0],
                            rule_id,
                            category,
                            min(match_lines),
                            max(match_lines),
                        )
                    )
        for match in UNCERTAIN.finditer(text):
            context_start = max(0, match.start() - 100)
            context_end = min(len(text), match.end() + 100)
            if BENIGN_UNCERTAIN.search(text[context_start:context_end]):
                continue
            match_lines = matched_lines(lines, start, end, match)
            selected_match_lines = sorted(selected & match_lines)
            if selected_match_lines:
                internal_findings.add(
                    (
                        selected_match_lines[0],
                        "PDS100",
                        "uncertain automation-directed prose",
                        min(match_lines),
                        max(match_lines),
                    )
                )

    findings = {
        (path, report_line, rule_id, category)
        for report_line, rule_id, category, _match_start, _match_end in internal_findings
    }
    return sorted(findings, key=lambda item: (item[1], item[2], item[3]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--include-test-fixtures", action="store_true")
    args = ap.parse_args()
    include_fixtures = args.include_test_fixtures or args.all
    try:
        candidates = (
            [str(x) for x in Path(".").rglob("*") if x.is_file()]
            if args.all
            else changed_files()
        )
    except ComparisonError:
        print("public-docs-safety: FAIL")
        print("<comparison>:1: PDS901: change-range resolution failure")
        return 1

    files = existing_public_docs(candidates, include_fixtures)
    added = None if args.all else changed_added_lines(files)
    findings = []
    for path in files:
        if added is None:
            line_numbers = range(
                1,
                len(
                    Path(path)
                    .read_text(encoding="utf-8", errors="ignore")
                    .splitlines()
                )
                + 1,
            )
        else:
            line_numbers = sorted(added.get(path, set()))
        findings.extend(scan_file(path, line_numbers))
    if findings:
        print("public-docs-safety: FAIL")
        for path, line_number, rule_id, category in findings:
            print(f"{path}:{line_number}: {rule_id}: {category}")
        return 1
    print("public-docs-safety: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
