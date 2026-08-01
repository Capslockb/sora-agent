#!/usr/bin/env python3
"""Complete name-status validation for the public-docs safety workflow.

This thin wrapper preserves the exact-path and parser behavior in the v2
entrypoint while ensuring every NUL-delimited Git name-status record is
validated before a public-document removal result is returned.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_V2_PATH = Path(__file__).with_name("public_docs_safety_entrypoint_v2.py")
_V2_SPEC = importlib.util.spec_from_file_location(
    "_public_docs_safety_entrypoint_v2", _V2_PATH
)
if _V2_SPEC is None or _V2_SPEC.loader is None:
    raise RuntimeError("unable to load public docs safety v2 entrypoint")
v2 = importlib.util.module_from_spec(_V2_SPEC)
sys.modules.setdefault("_public_docs_safety_entrypoint_v2", v2)
_V2_SPEC.loader.exec_module(v2)

scanner = v2.scanner
runner = v2.runner


def public_doc_removed_or_renamed(diff_args: list[str]) -> bool:
    """Validate the complete status stream, then report public removals."""
    result = scanner.subprocess.run(
        ["git", "diff", "--name-status", "-z", "--find-renames", *diff_args],
        text=False,
        stdout=scanner.subprocess.PIPE,
        stderr=scanner.subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise scanner.ComparisonError(
            "unable to resolve public-document deletion status"
        )

    raw_output = v2._raw_bytes(result.stdout)
    if raw_output and not raw_output.endswith(b"\0"):
        raise scanner.ComparisonError(
            "unable to parse public-document deletion status"
        )
    fields = raw_output.split(b"\0")[:-1] if raw_output else []

    public_removal = False
    index = 0
    while index < len(fields):
        try:
            status = fields[index].decode("ascii")
        except UnicodeDecodeError as exc:
            raise scanner.ComparisonError(
                "unable to parse public-document deletion status"
            ) from exc
        index += 1

        if not v2._NAME_STATUS_RE.fullmatch(status):
            raise scanner.ComparisonError(
                "unable to parse public-document deletion status"
            )
        if status[0] in {"R", "C"} and status[1:] and int(status[1:]) > 100:
            raise scanner.ComparisonError(
                "unable to parse public-document deletion status"
            )

        path_count = 2 if status[0] in {"R", "C"} else 1
        if len(fields) - index < path_count:
            raise scanner.ComparisonError(
                "unable to parse public-document deletion status"
            )
        raw_paths = fields[index : index + path_count]
        if any(not raw_path for raw_path in raw_paths):
            raise scanner.ComparisonError(
                "unable to parse public-document deletion status"
            )
        old_path = v2._decode_git_path(raw_paths[0])
        index += path_count

        if status == "D" and runner.is_public_doc(old_path):
            public_removal = True
        elif status.startswith("R") and runner.is_public_doc(old_path):
            public_removal = True

    return public_removal


# The v2 change-range selector resolves this function through its imported
# entrypoint module, so replace both public references before main() executes.
v2.public_doc_removed_or_renamed = public_doc_removed_or_renamed
v2.entrypoint.public_doc_removed_or_renamed = public_doc_removed_or_renamed


def main() -> int:
    return v2.main()


if __name__ == "__main__":
    sys.exit(main())
