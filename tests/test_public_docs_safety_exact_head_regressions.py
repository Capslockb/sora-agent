import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = REPO_ROOT / "scripts" / "public_docs_safety_entrypoint.py"

spec = importlib.util.spec_from_file_location(
    "public_docs_safety_exact_head_entrypoint", ENTRYPOINT
)
assert spec and spec.loader
scanner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = scanner
spec.loader.exec_module(scanner)


class ExactHeadRegressionTests(unittest.TestCase):
    def scan(self, suffix: str, text: str) -> list[tuple[str, int, str, str]]:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "docs" / f"example{suffix}"
            path.parent.mkdir(parents=True)
            path.write_text(text, encoding="utf-8")
            line_count = len(text.splitlines())
            return scanner.scan_file(str(path), range(1, line_count + 1))

    def rule_ids(self, suffix: str, text: str) -> set[str]:
        return {finding[2] for finding in self.scan(suffix, text)}

    def test_punctuated_lowercase_prose_remains_wrapped(self) -> None:
        rules = self.rule_ids(
            ".md",
            "```text\nignore. these\nprevious policy\n```\n",
        )
        self.assertIn("PDS001", rules)

    def test_actual_fenced_commands_remain_independent(self) -> None:
        rules = self.rule_ids(
            ".md",
            "```sh\ndisable NAME\ninstall repository\n```\n",
        )
        self.assertNotIn("PDS003", rules)

    def test_versioned_command_token_remains_independent(self) -> None:
        rules = self.rule_ids(
            ".md",
            "```sh\npython3.12 --version\ninstall repository\n```\n",
        )
        self.assertNotIn("PDS003", rules)

    def test_rst_simple_multiline_cell_is_one_record(self) -> None:
        rules = self.rule_ids(
            ".rst",
            "==========  =================\n"
            "Name        Value\n"
            "==========  =================\n"
            "Directive   Ignore\n"
            "            previous policy\n"
            "==========  =================\n",
        )
        self.assertIn("PDS001", rules)

    def test_rst_simple_rows_remain_independent(self) -> None:
        rules = self.rule_ids(
            ".rst",
            "==========  =================\n"
            "Action      Target\n"
            "==========  =================\n"
            "Disable     Name\n"
            "Install     Repository\n"
            "==========  =================\n",
        )
        self.assertNotIn("PDS003", rules)

    def test_rst_grid_escaped_pipe_remains_in_one_cell(self) -> None:
        rules = self.rule_ids(
            ".rst",
            "+--------------------------------+-------+\n"
            "| Ignore \\| previous policy     | Safe  |\n"
            "+--------------------------------+-------+\n",
        )
        self.assertIn("PDS001", rules)

    def test_rst_grid_substitution_reference_remains_in_one_cell(self) -> None:
        rules = self.rule_ids(
            ".rst",
            "+--------------------------------+-------+\n"
            "| Ignore |name| previous policy | Safe  |\n"
            "+--------------------------------+-------+\n",
        )
        self.assertIn("PDS001", rules)

    def test_rst_grid_columns_remain_independent(self) -> None:
        rules = self.rule_ids(
            ".rst",
            "+----------+------------+\n"
            "| Disable  | Repository |\n"
            "+----------+------------+\n",
        )
        self.assertNotIn("PDS003", rules)


if __name__ == "__main__":
    unittest.main()
