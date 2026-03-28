from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import validate_nested_agents  # noqa: E402


class NestedAgentsDocsTests(unittest.TestCase):
    def materialize_valid_agents(self, repo_root: Path) -> None:
        for spec in validate_nested_agents.REQUIRED_DOCS:
            path = repo_root / spec.path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "# AGENTS.md\n\n"
                + "\n".join(f"- {snippet}" for snippet in spec.required_snippets)
                + "\n",
                encoding="utf-8",
            )

    def test_nested_agents_docs_are_present_and_shaped(self) -> None:
        self.assertEqual([], validate_nested_agents.validate(REPO_ROOT))

    def test_validator_reports_missing_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            self.materialize_valid_agents(temp_root)
            (temp_root / "generated" / "AGENTS.md").unlink()

            self.assertIn(
                "generated/AGENTS.md: file is missing",
                validate_nested_agents.validate(temp_root),
            )

    def test_validator_reports_missing_snippet(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            self.materialize_valid_agents(temp_root)
            target = temp_root / "examples" / "AGENTS.md"
            target.write_text("# AGENTS.md\n\nExample surface without anchors.\n", encoding="utf-8")

            issues = validate_nested_agents.validate(temp_root)

            self.assertTrue(
                any(
                    issue.startswith("examples/AGENTS.md: missing snippet ")
                    and "public-safe" in issue
                    for issue in issues
                )
            )


if __name__ == "__main__":
    unittest.main()
