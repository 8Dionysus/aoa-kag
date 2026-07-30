from __future__ import annotations

from pathlib import Path
import re
import unittest

from scripts.provider_registry import provider_dependency_pins


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "repo-validation.yml"
RELEASE_CHECK_PATH = REPO_ROOT / "scripts" / "release_check.py"


class RepoValidationWorkflowTests(unittest.TestCase):
    def test_source_fast_and_owner_family_are_always_in_the_required_local_job(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        source_fast = workflow_text.split("  source_fast:\n", 1)[1].split(
            "  release_audit:\n",
            1,
        )[0]

        self.assertIn("name: Source Fast and Owner Family", source_fast)
        self.assertIn("python scripts/impact_routing.py classify", source_fast)
        self.assertIn("uses: ./.github/actions/repo-local-kag-index", source_fast)
        self.assertIn("python scripts/ci_gate.py --mode source-fast", source_fast)
        self.assertLess(
            source_fast.index("uses: ./.github/actions/repo-local-kag-index"),
            source_fast.index("python scripts/ci_gate.py --mode source-fast"),
        )
        self.assertNotIn("owner_fast:", workflow_text)

    def test_local_job_checks_out_only_the_seven_source_fast_dependencies(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        source_fast = workflow_text.split("  source_fast:\n", 1)[1].split(
            "  release_audit:\n",
            1,
        )[0]

        dependency_paths = set(
            re.findall(r"          path: (\.deps/[^\n]+)", source_fast)
        )
        self.assertEqual(
            {
                ".deps/Tree-of-Sophia",
                ".deps/aoa-agents",
                ".deps/aoa-evals",
                ".deps/aoa-memo",
                ".deps/aoa-playbooks",
                ".deps/aoa-stats",
                ".deps/aoa-techniques",
            },
            dependency_paths,
        )
        self.assertNotIn("AOA_SESSION_MEMORY_ROOT", source_fast)

    def test_full_audit_is_additive_and_fail_closed(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        release_audit = workflow_text.split("  release_audit:\n", 1)[1].split(
            "  required_summary:\n",
            1,
        )[0]

        self.assertIn("name: Full OS-wide Release Audit", release_audit)
        self.assertIn("needs: source_fast", release_audit)
        self.assertIn("needs.source_fast.result == 'success'", release_audit)
        self.assertIn(
            "needs.source_fast.outputs.full-audit-required == 'true'",
            release_audit,
        )
        self.assertIn("python scripts/release_check.py", release_audit)
        self.assertIn("fetch-depth: 0", release_audit)

    def test_required_summary_preserves_context_and_typed_skip_status(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        summary = workflow_text.split("  required_summary:\n", 1)[1]

        self.assertIn("name: Repo Validation", summary)
        self.assertIn("if: always()", summary)
        self.assertIn("SOURCE_FAST_RESULT: ${{ needs.source_fast.result }}", summary)
        self.assertIn(
            "FULL_AUDIT_RESULT: ${{ needs.release_audit.result }}",
            summary,
        )
        self.assertIn("python scripts/impact_routing.py summarize", summary)
        self.assertIn("--full-audit-required", summary)
        self.assertIn("--github-step-summary", summary)

    def test_generated_drift_gate_checks_untracked_files(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn(
            "git status --porcelain --untracked-files=all -- generated",
            workflow_text,
        )
        self.assertNotIn("git diff --exit-code -- generated", workflow_text)

    def test_release_check_validates_committed_outputs_before_regeneration(self) -> None:
        release_check_text = RELEASE_CHECK_PATH.read_text(encoding="utf-8")
        manifest_text = (REPO_ROOT / "config" / "validation_lanes.json").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "validation_lanes.command_sequence_for_lane(RELEASE_LANE_ID)",
            release_check_text,
        )
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
