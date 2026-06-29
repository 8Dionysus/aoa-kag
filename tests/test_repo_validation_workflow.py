from __future__ import annotations

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "repo-validation.yml"
RELEASE_CHECK_PATH = REPO_ROOT / "scripts" / "release_check.py"
CURRENT_DEPENDENCY_PINS = {
    "8Dionysus": "112637f833ab4af299f55229f2687344b194f256",
    "ATM10-Agent": "590e53dfb9b8ac118067221245e427f52d0af84a",
    "Tree-of-Sophia": "592f4b82ca05dbd06de1727255a257e03b69b722",
    "Agents-of-Abyss": "5e7ea384179eda2e371bd6597bd96ef0a8f2e485",
    "Dionysus": "a8a394d4c2dccf0167d3b1e6a5dfa82c6db5ce8c",
    "aoa-memo": "19b1e267553262d8eff17e36f6822c60fe7cb133",
    "aoa-playbooks": "5559ac60aea644b6aeb26261f2d48741cc97dbc6",
    "aoa-evals": "79b11474c9efa42dcf09c0fe5236f76ddca513bf",
    "aoa-agents": "6b9c84e380700f032d964d270a00586b75dc1b82",
    "aoa-techniques": "326f70bf4ae30426db54c82800ba254b2061d02f",
    "aoa-routing": "e0892f750d4d738108fb246f231529933604365a",
    "aoa-sdk": "fe23e661789888e862771f5857d99c8dd263fdb6",
    "aoa-skills": "6033851ada090f557e41da472e416ba43a580b46",
    "aoa-stats": "8918dc8f77d76d3b3f2babb835b46b6f45610575",
    "aoa-4pda-connector": "b67062779b0c0204b239e10518704dbd704c184a",
    "aoa-discord-connector": "e9e58b2f9839f6e64b8aa18a0c4f0fa535f93fc5",
    "aoa-stackoverflow-connector": "7b9e52678974f1e268e2558bf928f8d2eb233049",
    "aoa-telegram-connector": "a622d0dc42ac938b3f41b77a94a4602fd92a18fe",
    "aoa-xda-connector": "edcd6981e5091cf9bdf13702d0a1ebb5550bccb8",
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
