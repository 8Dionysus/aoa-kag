from __future__ import annotations

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "repo-validation.yml"
RELEASE_CHECK_PATH = REPO_ROOT / "scripts" / "release_check.py"
CURRENT_DEPENDENCY_PINS = {
    "Tree-of-Sophia": "84372b134e3c51d3033000125361e6adbb81c122",
    "Agents-of-Abyss": "ba0722f5b2cf3764cbdaffdcd6006a6963bad0a9",
    "aoa-memo": "79951a2a056c11a30602a71fb91236e2a2ba45bc",
    "aoa-playbooks": "24c762868fbb257852d6ce0b03dd356566e2cfd1",
    "aoa-evals": "5a1c410ef8cb4b692fad43adb65d2eecb2a1f639",
    "aoa-agents": "e3703f06c05dc4dab155e3ffafff9414de22649b",
    "aoa-techniques": "50f14c92f12062a13274fb537a6a0478c0385da4",
    "aoa-routing": "986098c46ea813b0f61a2cc240c5438ce489d46d",
    "aoa-sdk": "a49420fc86133f78d554401c46e7d2230cdd7b1e",
    "aoa-skills": "5c36e4cf1b996cacd70b63ecc7ec5ba13fcc57b5",
}


class RepoValidationWorkflowTests(unittest.TestCase):
    def test_generated_drift_gate_checks_untracked_files(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("git status --porcelain --untracked-files=all -- generated", workflow_text)
        self.assertNotIn("git diff --exit-code -- generated", workflow_text)

    def test_release_check_validates_committed_outputs_before_regeneration(self) -> None:
        release_check_text = RELEASE_CHECK_PATH.read_text(encoding="utf-8")
        manifest_text = (REPO_ROOT / "config" / "validation_lanes.json").read_text(
            encoding="utf-8"
        )

        self.assertIn("validation_lanes.command_sequence_for_lane(RELEASE_LANE_ID)", release_check_text)
        self.assertIn('"generated_check"', manifest_text)
        self.assertLess(
            manifest_text.index('"scripts/validate_kag.py"'),
            manifest_text.index('"scripts/generate_kag.py"'),
        )

    def test_release_check_includes_decision_record_guards(self) -> None:
        manifest_text = (REPO_ROOT / "config" / "validation_lanes.json").read_text(
            encoding="utf-8"
        )

        self.assertIn('"scripts/generate_decision_indexes.py"', manifest_text)
        self.assertIn('"--check"', manifest_text)
        self.assertIn('"scripts/validate_decision_records.py"', manifest_text)

    def test_repo_validation_uses_current_dependency_pins(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

        for repo, pin in CURRENT_DEPENDENCY_PINS.items():
            with self.subTest(repo=repo):
                self.assertIn(pin, workflow_text)


if __name__ == "__main__":
    unittest.main()
