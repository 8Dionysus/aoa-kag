from __future__ import annotations

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "repo-validation.yml"
RELEASE_CHECK_PATH = REPO_ROOT / "scripts" / "release_check.py"
CURRENT_DEPENDENCY_PINS = {
    "Tree-of-Sophia": "3b658722d9aeb2bcfadbebffd9e648e31f72cd90",
    "aoa-memo": "5f87c4f2db09738eae8ba782a7dff26b4be76c62",
    "aoa-playbooks": "5667de359e7aae2f9b409435cb8fcacaab2d37b1",
    "aoa-evals": "0bed981d9fc2974d6ba2af235d33836322d3c98e",
    "aoa-agents": "3ac8066e74fd7bc0a4235b3b8ee057de99b8fb19",
    "aoa-techniques": "1a7d146957108ecefc24219c7d56357c5a4a2c2c",
}


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

    def test_release_check_includes_decision_record_guards(self) -> None:
        release_check_text = RELEASE_CHECK_PATH.read_text(encoding="utf-8")

        self.assertIn("check decision indexes", release_check_text)
        self.assertIn("scripts/generate_decision_indexes.py", release_check_text)
        self.assertIn("validate decision records", release_check_text)
        self.assertIn("scripts/validate_decision_records.py", release_check_text)

    def test_repo_validation_uses_current_dependency_pins(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

        for repo, pin in CURRENT_DEPENDENCY_PINS.items():
            with self.subTest(repo=repo):
                self.assertIn(pin, workflow_text)


if __name__ == "__main__":
    unittest.main()
