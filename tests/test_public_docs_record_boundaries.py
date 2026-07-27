import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import public_docs_safety as scanner  # noqa: E402


class PublicDocsRecordBoundaryTests(unittest.TestCase):
    def scan(self, suffix: str, text: str, selected: list[int]):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"example{suffix}"
            path.write_text(text, encoding="utf-8")
            return scanner.scan_file(str(path), selected)

    def test_html_inline_descendants_stay_in_one_record(self):
        findings = self.scan(
            ".html",
            "<p>Ignore <strong>previous</strong> policy</p>\n",
            [1],
        )
        self.assertTrue(any(item[2] == "PDS001" for item in findings), findings)

    def test_html_sibling_elements_are_not_joined(self):
        findings = self.scan(
            ".html",
            '<button>Disable</button><a href="/repository">Repository</a>\n',
            [1],
        )
        self.assertFalse(any(item[2] == "PDS003" for item in findings), findings)

    def test_wrapped_fenced_instruction_is_detected(self):
        findings = self.scan(
            ".md",
            "```text\nignore everything\nprevious policy\n```\n",
            [2, 3],
        )
        self.assertTrue(any(item[2] == "PDS001" for item in findings), findings)

    def test_independent_fenced_commands_remain_separate(self):
        findings = self.scan(
            ".md",
            "```text\ndisable NAME\ninstall repository\n```\n",
            [2, 3],
        )
        self.assertFalse(any(item[2] == "PDS003" for item in findings), findings)

    def test_explicit_multiline_command_keeps_continuations(self):
        records = scanner.document_records(
            "docs/example.md",
            [
                "```sh",
                "sora voice start \\",
                "  --provider gemini",
                "```",
            ],
        )
        self.assertTrue(
            any(
                [line for line, _ in record.parts] == [2, 3]
                for record in records
            ),
            records,
        )


if __name__ == "__main__":
    unittest.main()
