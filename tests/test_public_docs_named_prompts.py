import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = REPO_ROOT / "scripts" / "public_docs_safety_entrypoint.py"

spec = importlib.util.spec_from_file_location(
    "public_docs_safety_named_prompt_entrypoint", ENTRYPOINT
)
assert spec and spec.loader
scanner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = scanner
spec.loader.exec_module(scanner)


class NamedPromptTests(unittest.TestCase):
    def rule_ids(self, text: str) -> set[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "docs" / "example.md"
            path.parent.mkdir(parents=True)
            path.write_text(text, encoding="utf-8")
            selected = range(1, len(text.splitlines()) + 1)
            return {finding[2] for finding in scanner.scan_file(str(path), selected)}

    def test_named_prompt_is_removed_from_command_head(self) -> None:
        self.assertEqual("disable", scanner._command_head("root$ disable NAME"))
        self.assertEqual("git", scanner._command_head("developer> git status"))

    def test_independent_named_prompt_commands_remain_separate(self) -> None:
        rules = self.rule_ids(
            "```text\n"
            "root$ disable NAME\n"
            "root$ install repository\n"
            "```\n"
        )
        self.assertNotIn("PDS003", rules)

    def test_named_prompt_wrapped_instruction_is_still_scanned(self) -> None:
        rules = self.rule_ids(
            "```text\n"
            "root$ ignore everything\n"
            "root$ previous policy\n"
            "```\n"
        )
        self.assertIn("PDS001", rules)


if __name__ == "__main__":
    unittest.main()
