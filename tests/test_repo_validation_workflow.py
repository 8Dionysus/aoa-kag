from __future__ import annotations

from pathlib import Path
import subprocess
import textwrap
import unittest

from scripts.provider_registry import provider_dependency_pins


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "repo-validation.yml"
RELEASE_CHECK_PATH = REPO_ROOT / "scripts" / "release_check.py"


class RepoValidationWorkflowTests(unittest.TestCase):
    def test_owner_fast_gate_controls_full_fanout(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("owner_fast:", workflow_text)
        self.assertIn("id: kag", workflow_text)
        self.assertIn("validation-lane: ${{ steps.kag.outputs.validation-lane }}", workflow_text)
        self.assertIn("incremental_federation:", workflow_text)
        self.assertIn("name: Incremental Federation Gate", workflow_text)
        self.assertIn("python scripts/ci_gate.py --mode incremental-federation", workflow_text)
        self.assertIn("needs.owner_fast.outputs.validation-lane == 'incremental-federation'", workflow_text)
        self.assertIn("needs.owner_fast.outputs.validation-lane == 'full-24-owner-audit'", workflow_text)
        self.assertIn("github.event_name != 'pull_request'", workflow_text)
        self.assertIn('cron: "31 7 * * 1"', workflow_text)

    def test_generated_drift_gate_uses_lane_authority_for_untracked_files(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        ci_gate_text = (REPO_ROOT / "scripts" / "ci_gate.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("python scripts/release_check.py", workflow_text)
        self.assertIn(
            "validation_lanes.GENERATED_UNTRACKED_PATHS_COMMAND",
            ci_gate_text,
        )
        self.assertNotIn("git status --porcelain --untracked-files=all -- generated", workflow_text)
        self.assertNotIn("git diff --exit-code -- generated", workflow_text)

    def test_required_summary_preserves_branch_protection_context(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("required_summary:", workflow_text)
        self.assertIn("name: Repo Validation", workflow_text)
        self.assertIn("OWNER_FAST_RESULT: ${{ needs.owner_fast.result }}", workflow_text)
        self.assertIn(
            "INCREMENTAL_FEDERATION_RESULT: ${{ needs.incremental_federation.result }}",
            workflow_text,
        )
        self.assertIn(
            "RELEASE_AUDIT_RESULT: ${{ needs.release_audit.result }}",
            workflow_text,
        )
        self.assertIn(
            'if [ "$OWNER_FAST_RESULT" != "success" ]',
            workflow_text,
        )
        self.assertIn(
            '[ "$VALIDATION_LANE" = "full-24-owner-audit" ]',
            workflow_text,
        )
        self.assertIn(
            '[ "$VALIDATION_LANE" = "incremental-federation" ]',
            workflow_text,
        )
        self.assertIn(
            '[ "$INCREMENTAL_FEDERATION_RESULT" != "success" ]',
            workflow_text,
        )
        self.assertIn(
            'if [ "$RELEASE_AUDIT_RESULT" != "success" ]',
            workflow_text,
        )

    def test_required_summary_shell_is_syntactically_valid(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        summary = workflow_text.split("  required_summary:\n", 1)[1]
        run_block = summary.split("        run: |\n", 1)[1]
        script_lines = []
        for line in run_block.splitlines():
            if line and not line.startswith("          "):
                break
            script_lines.append(line[10:] if line else "")
        result = subprocess.run(
            ("bash", "-n"),
            input=textwrap.dedent("\n".join(script_lines)) + "\n",
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr)

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

        for repo, pin in provider_dependency_pins().items():
            with self.subTest(repo=repo):
                self.assertIn(pin, workflow_text)


if __name__ == "__main__":
    unittest.main()
