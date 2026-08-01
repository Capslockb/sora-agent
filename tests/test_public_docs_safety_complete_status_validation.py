import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = REPO_ROOT / "scripts" / "public_docs_safety_entrypoint_v3.py"

spec = importlib.util.spec_from_file_location(
    "public_docs_safety_complete_status_validation", ENTRYPOINT
)
assert spec and spec.loader
scanner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = scanner
spec.loader.exec_module(scanner)


class CompleteStatusValidationTests(unittest.TestCase):
    def test_public_deletion_does_not_skip_truncated_later_record(self) -> None:
        malformed = subprocess.CompletedProcess(
            args=["git", "diff"],
            returncode=0,
            stdout=b"D\0README.md\0M\0",
            stderr=b"",
        )
        with mock.patch.object(
            scanner.scanner.subprocess, "run", return_value=malformed
        ):
            with self.assertRaises(scanner.scanner.ComparisonError):
                scanner.public_doc_removed_or_renamed(["base", "HEAD"])

    def test_public_deletion_is_reported_after_all_valid_records(self) -> None:
        valid = subprocess.CompletedProcess(
            args=["git", "diff"],
            returncode=0,
            stdout=b"D\0README.md\0M\0src/module.py\0",
            stderr=b"",
        )
        with mock.patch.object(
            scanner.scanner.subprocess, "run", return_value=valid
        ):
            self.assertTrue(
                scanner.public_doc_removed_or_renamed(["base", "HEAD"])
            )

    def test_public_rename_does_not_skip_invalid_later_status(self) -> None:
        malformed = subprocess.CompletedProcess(
            args=["git", "diff"],
            returncode=0,
            stdout=b"R100\0README.md\0docs/archive.md\0Q\0file.txt\0",
            stderr=b"",
        )
        with mock.patch.object(
            scanner.scanner.subprocess, "run", return_value=malformed
        ):
            with self.assertRaises(scanner.scanner.ComparisonError):
                scanner.public_doc_removed_or_renamed(["base", "HEAD"])


if __name__ == "__main__":
    unittest.main()
