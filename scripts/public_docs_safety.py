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

DOC_NAMES = {"README.md", "SECURITY.md", "CONTRIBUTING.md", "AGENTS.md"}
DOC_DIR_PARTS = {"docs", "doc", "website", "site", "public"}
FIXTURE_PARTS = {"tests", "fixtures", "public-docs"}
DOC_EXTS = {".md", ".mdx", ".rst", ".txt"}
EXCLUDE_PARTS = {"i18n", "CHANGELOG.md", "sessions", "vendor", "node_modules", ".git"}
ZERO_SHA = "0" * 40
EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
MAX_SPAN_LINES = 3

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
    parts = set(p.parts)
    if parts & EXCLUDE_PARTS:
        return False
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

    p = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if p.returncode == 0:
        return p.stdout.splitlines() if p.stdout.strip() else []

    return [str(x) for x in Path(".").rglob("*") if x.is_file()]


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


def candidate_spans(
    total_lines: int, selected_lines: list[int] | range
) -> list[tuple[int, int]]:
    """Return unique one-to-three-line spans that include a selected line."""
    selected = sorted({i for i in selected_lines if 1 <= i <= total_lines})
    spans: set[tuple[int, int]] = set()
    for line_number in selected:
        for width in range(1, MAX_SPAN_LINES + 1):
            for offset in range(width):
                start = line_number - offset
                end = start + width - 1
                if 1 <= start <= end <= total_lines:
                    spans.add((start, end))
    return sorted(spans)


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
    for start, end in candidate_spans(len(lines), sorted(selected)):
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
            if BENIGN_UNCERTAIN.search(match.group(0)):
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
    candidates = (
        [str(x) for x in Path(".").rglob("*") if x.is_file()]
        if args.all
        else changed_files()
    )
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
