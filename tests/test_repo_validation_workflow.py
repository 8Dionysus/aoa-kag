from __future__ import annotations

from pathlib import Path
import re
import unittest

from scripts.provider_registry import provider_dependency_pins, provider_entries


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "repo-validation.yml"
COMPATIBILITY_WORKFLOW_PATH = (
    REPO_ROOT / ".github" / "workflows" / "compatibility-canary.yml"
)
RELEASE_CHECK_PATH = REPO_ROOT / "scripts" / "release_check.py"
CI_PREFLIGHT_DAG_PATH = REPO_ROOT / "scripts" / "ci_preflight_dag.py"


class RepoValidationWorkflowTests(unittest.TestCase):
    def test_concurrency_cancels_only_superseded_runs_of_the_same_pr(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        workflow_header = workflow_text.split("jobs:\n", 1)[0]

        self.assertIn("concurrency:\n", workflow_header)
        self.assertNotIn("github.workflow", workflow_header)
        self.assertIn("aoa-kag-repo-validation-pr-{0}", workflow_header)
        self.assertIn("github.event_name == 'pull_request'", workflow_header)
        self.assertIn("github.run_attempt == '1'", workflow_header)
        self.assertIn("github.event.pull_request.number", workflow_header)
        self.assertIn(
            "aoa-kag-repo-validation-{0}-{1}-attempt-{2}",
            workflow_header,
        )
        self.assertIn("github.run_id, github.run_attempt", workflow_header)
        self.assertIn(
            "cancel-in-progress: true",
            workflow_header,
        )

        compatibility_text = COMPATIBILITY_WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertNotIn("github.event.pull_request.number", compatibility_text)

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

    def test_local_job_checks_out_only_the_eight_source_fast_dependencies(self) -> None:
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
                ".deps/aoa-sdk",
                ".deps/aoa-stats",
                ".deps/aoa-techniques",
            },
            dependency_paths,
        )
        self.assertNotIn("AOA_SESSION_MEMORY_ROOT", source_fast)

        dependency_checkout_blocks = [
            block
            for block in source_fast.split("      - name: ")[1:]
            if "          path: .deps/" in block
        ]
        self.assertEqual(8, len(dependency_checkout_blocks))
        self.assertTrue(
            all(
                "          fetch-depth: 1" in block
                for block in dependency_checkout_blocks
            )
        )
        self.assertEqual(8, source_fast.count("          fetch-depth: 1"))
        self.assertEqual(1, source_fast.count("          fetch-depth: 0"))
        compatibility_text = COMPATIBILITY_WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertNotIn("fetch-depth: 1", compatibility_text)

    def test_full_audit_is_additive_and_fail_closed(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        release_audit = workflow_text.split("  release_audit:\n", 1)[1].split(
            "  required_summary:\n",
            1,
        )[0]

        self.assertIn("name: Full OS-wide Release Audit", release_audit)
        self.assertIn("needs: source_fast", release_audit)
        self.assertIn("!cancelled()", release_audit)
        self.assertNotIn("always()", release_audit)
        self.assertIn("needs.source_fast.result == 'success'", release_audit)
        self.assertIn(
            "needs.source_fast.outputs.full-audit-required == 'true'",
            release_audit,
        )
        self.assertIn("python scripts/ci_release_check.py", release_audit)
        self.assertIn(
            "AOA_KAG_SOURCE_FAST_HANDOFF: ${{ needs.source_fast.outputs.source_fast_handoff }}",
            release_audit,
        )
        self.assertIn("fetch-depth: 0", release_audit)
        self.assertNotIn("fetch-depth: 1", release_audit)
        self.assertNotIn("filter:", release_audit)

    def test_full_audit_uses_bounded_manifest_owned_public_checkout(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        preflight_text = CI_PREFLIGHT_DAG_PATH.read_text(encoding="utf-8")
        release_audit = workflow_text.split("  release_audit:\n", 1)[1].split(
            "  required_summary:\n",
            1,
        )[0]

        self.assertIn('AOA_KAG_CHECKOUT_WORKERS: "3"', release_audit)
        self.assertIn("inputs.preflight_mode || 'candidate'", release_audit)
        self.assertIn(
            "inputs.history_ref || github.event.pull_request.base.sha || github.sha",
            workflow_text,
        )
        self.assertIn("python scripts/ci_preflight_dag.py", release_audit)
        self.assertIn('--mode "$AOA_KAG_PREFLIGHT_MODE"', release_audit)
        self.assertIn('--jobs "$AOA_KAG_CHECKOUT_WORKERS"', release_audit)
        self.assertIn('"scripts/sync_provider_checkouts.py"', preflight_text)
        self.assertIn('"--exclude-secret-checkouts"', preflight_text)
        self.assertEqual(1, release_audit.count("          path: .deps/"))
        self.assertIn("repository: 8Dionysus/aoa-session-memory", release_audit)
        self.assertIn("ssh-key: ${{ secrets.AOA_SESSION_MEMORY_DEPLOY_KEY }}", release_audit)
        self.assertIn("persist-credentials: false", release_audit)

        public_entries = [
            entry
            for entry in provider_entries()
            if entry.get("checkout_mode") == "pinned"
            and not entry.get("checkout_ssh_key_secret")
        ]
        for entry in public_entries:
            with self.subTest(repo=entry["repo"]):
                self.assertNotIn(
                    f"repository: {entry['github_repository']}",
                    release_audit,
                )

    def test_required_summary_preserves_context_and_typed_skip_status(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        summary = workflow_text.split("  required_summary:\n", 1)[1]

        self.assertIn("name: Repo Validation", summary)
        self.assertIn("if: ${{ !cancelled() }}", summary)
        self.assertNotIn("if: always()", summary)
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
            "validation_lanes.command_sequence_for_lane(lane_id)",
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

    def test_workflows_route_current_dependency_pins_through_owned_surfaces(self) -> None:
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        preflight_text = CI_PREFLIGHT_DAG_PATH.read_text(encoding="utf-8")

        for repo, pin in provider_dependency_pins().items():
            with self.subTest(repo=repo):
                entry = next(entry for entry in provider_entries() if entry["repo"] == repo)
                if entry.get("checkout_ssh_key_secret"):
                    self.assertIn(pin, workflow_text)
                else:
                    self.assertIn("python scripts/ci_preflight_dag.py", workflow_text)
                    self.assertIn('"scripts/sync_provider_checkouts.py"', preflight_text)


if __name__ == "__main__":
    unittest.main()
