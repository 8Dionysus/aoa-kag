from __future__ import annotations

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "repo-validation.yml"
RELEASE_CHECK_PATH = REPO_ROOT / "scripts" / "release_check.py"
CURRENT_AOA_TECHNIQUES_PIN = "fe4b04ed877916c46e60e70aaa9a1d4c86e81b6e"


class RepoValidationWorkflowTests(unittest.TestCase):
    def test_generated_drift_gate_checks_untracked_files(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("git status --porcelain --untracked-files=all -- generated", workflow_text)
        self.assertNotIn("git diff --exit-code -- generated", workflow_text)

    def test_release_check_validates_committed_outputs_before_regeneration(self) -> None:
        release_check_text = RELEASE_CHECK_PATH.read_text(encoding="utf-8")

        self.assertLess(
            release_check_text.index("validate committed KAG surfaces"),
            release_check_text.index("generate KAG outputs"),
        )

    def test_repo_validation_uses_current_technique_export_pin(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn(CURRENT_AOA_TECHNIQUES_PIN, workflow_text)


if __name__ == "__main__":
    unittest.main()
