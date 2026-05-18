from __future__ import annotations

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "repo-validation.yml"
RELEASE_CHECK_PATH = REPO_ROOT / "scripts" / "release_check.py"
CURRENT_DEPENDENCY_PINS = {
    "Tree-of-Sophia": "0278961afae2dc9b45f10e15d8a70bfdfdcdcc9c",
    "aoa-memo": "a0fb807bf97b045517ba05a4da3d8e1e58b5483d",
    "aoa-playbooks": "2e7b7bab23e192cf5bb2f1aee5c59f5b24f51e34",
    "aoa-evals": "1fd85f515b9b72240a9d1c676c3935129ea84800",
    "aoa-agents": "272801c52d359b85833944b9bea57273b42c870e",
    "aoa-techniques": "60ceea4090fec76933fcf41cc0c963a6f1aeb2be",
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

    def test_repo_validation_uses_current_dependency_pins(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

        for repo, pin in CURRENT_DEPENDENCY_PINS.items():
            with self.subTest(repo=repo):
                self.assertIn(pin, workflow_text)


if __name__ == "__main__":
    unittest.main()
