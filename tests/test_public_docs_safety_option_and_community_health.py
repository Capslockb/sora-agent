import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = REPO_ROOT / "scripts" / "public_docs_safety_entrypoint.py"
CODEOWNERS = REPO_ROOT / ".github" / "CODEOWNERS"

spec = importlib.util.spec_from_file_location(
    "public_docs_safety_option_community_entrypoint", ENTRYPOINT
)
assert spec and spec.loader
entrypoint = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = entrypoint
spec.loader.exec_module(entrypoint)
scanner = entrypoint.scanner


class OptionAndCommunityHealthTests(unittest.TestCase):
    def rule_ids(self, text: str) -> set[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "docs" / "example.html"
            path.parent.mkdir(parents=True)
            path.write_text(text, encoding="utf-8")
            selected = range(1, len(text.splitlines()) + 1)
            findings = scanner.scan_file(str(path), selected)
        return {finding[2] for finding in findings}

    def test_sibling_options_are_independent_records(self) -> None:
        rules = self.rule_ids(
            "<select>\n"
            "  <option>Disable</option>\n"
            "  <option>Repository</option>\n"
            "</select>\n"
        )
        self.assertNotIn("PDS003", rules)

    def test_nested_inline_text_inside_one_option_remains_one_record(self) -> None:
        rules = self.rule_ids(
            "<select><option>Disable <strong>repository</strong></option></select>\n"
        )
        self.assertIn("PDS003", rules)

    def test_enforceable_support_and_governance_locations_are_classified(self) -> None:
        paths = (
            "SUPPORT.md",
            "support.md",
            "GOVERNANCE.md",
            "governance.md",
            ".github/SUPPORT.md",
            ".github/support.md",
            ".github/GOVERNANCE.md",
            ".github/governance.md",
            "docs/Support.md",
            "docs/Governance.md",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue(scanner.is_public_doc(path))

    def test_unowned_mixed_case_root_and_github_variants_are_excluded(self) -> None:
        paths = (
            "Support.md",
            "Governance.md",
            ".github/Support.md",
            ".github/Governance.md",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertFalse(scanner.is_public_doc(path))

    def test_codeowners_covers_every_enforceable_variant(self) -> None:
        rules = set(CODEOWNERS.read_text(encoding="utf-8").splitlines())
        expected = {
            "/SUPPORT.md @Capslockb",
            "/support.md @Capslockb",
            "/GOVERNANCE.md @Capslockb",
            "/governance.md @Capslockb",
            "/.github/SUPPORT.md @Capslockb",
            "/.github/support.md @Capslockb",
            "/.github/GOVERNANCE.md @Capslockb",
            "/.github/governance.md @Capslockb",
            "/docs/ @Capslockb",
        }
        self.assertTrue(expected <= rules)


if __name__ == "__main__":
    unittest.main()
