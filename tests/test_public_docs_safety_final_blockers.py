import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "public_docs_safety_runner.py"

spec = importlib.util.spec_from_file_location("public_docs_safety_final", SCRIPT)
assert spec and spec.loader
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)


class PublicDocsSafetyFinalBlockers(unittest.TestCase):
    def scan(self, suffix: str, text: str, selected):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / f"example{suffix}"
            path.write_text(text, encoding="utf-8")
            return scanner.scan_file(str(path), selected)

    def test_new_branch_push_uses_default_branch_baseline(self):
        with mock.patch.dict(
            os.environ,
            {
                "GITHUB_EVENT_NAME": "push",
                "PUBLIC_DOCS_BASE_SHA": scanner.ZERO_SHA,
                "DEFAULT_BRANCH": "main",
            },
            clear=True,
        ):
            self.assertEqual(scanner.comparison_args(), ["origin/main...HEAD"])

    def test_existing_branch_push_uses_event_before_sha(self):
        before = "1" * 40
        with mock.patch.dict(
            os.environ,
            {
                "GITHUB_EVENT_NAME": "push",
                "PUBLIC_DOCS_BASE_SHA": before,
                "DEFAULT_BRANCH": "main",
            },
            clear=True,
        ):
            self.assertEqual(scanner.comparison_args(), [before, "HEAD"])

    def test_escaped_asciidoc_pipe_does_not_split_unsafe_phrase(self):
        findings = self.scan(
            ".adoc",
            "|===\n|Ignore \\| previous policy\n|===\n",
            [2],
        )
        self.assertTrue(any(item[2] == "PDS001" for item in findings), findings)

    def test_asciidoc_cells_remain_independent(self):
        findings = self.scan(
            ".adoc",
            "|===\n|Disable\n|Repository\n|===\n",
            [2, 3],
        )
        self.assertFalse(any(item[2] == "PDS003" for item in findings), findings)

    def test_rst_simple_table_rows_remain_independent(self):
        findings = self.scan(
            ".rst",
            "========  ==========\n"
            "Command   Target\n"
            "========  ==========\n"
            "Disable   Name\n"
            "Install   Repository\n"
            "========  ==========\n",
            range(1, 7),
        )
        self.assertFalse(any(item[2] == "PDS003" for item in findings), findings)

    def test_rst_simple_table_cell_is_scanned(self):
        findings = self.scan(
            ".rst",
            "========================  =====\n"
            "Message                   Note\n"
            "========================  =====\n"
            "Ignore previous policy    text\n"
            "========================  =====\n",
            [4],
        )
        self.assertTrue(any(item[2] == "PDS001" for item in findings), findings)

    def test_rst_grid_table_cells_remain_independent(self):
        findings = self.scan(
            ".rst",
            "+----------+------------+\n"
            "| Disable  | Name       |\n"
            "+----------+------------+\n"
            "| Install  | Repository |\n"
            "+----------+------------+\n",
            range(1, 6),
        )
        self.assertFalse(any(item[2] == "PDS003" for item in findings), findings)


if __name__ == "__main__":
    unittest.main()
