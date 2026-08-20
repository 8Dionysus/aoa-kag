from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts import impact_routing


REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = REPO_ROOT / "tests" / "fixtures" / "impact_routing_corpus.json"


class ImpactRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))

    def test_positive_owner_local_corpus(self) -> None:
        self.assertEqual(
            "aoa-kag-impact-routing-corpus-v1",
            self.corpus["schema_version"],
        )
        for case in self.corpus["positive_owner_local_cases"]:
            with self.subTest(case=case["id"]):
                classification = impact_routing.classify_changed_paths(case["paths"])
                self.assertEqual(impact_routing.OWNER_LOCAL_ROUTE, classification.route)
                self.assertFalse(classification.full_audit_required)
                self.assertEqual(
                    set(case["expected_reason_ids"]),
                    set(classification.reason_ids),
                )
                payload = classification.as_dict()
                self.assertTrue(payload["source_fast_required"])
                self.assertTrue(payload["owner_family_required"])
                self.assertEqual("not-required", payload["os_wide_audit_disposition"])

    def test_negative_fail_closed_corpus(self) -> None:
        for case in self.corpus["negative_fail_closed_cases"]:
            with self.subTest(case=case["id"]):
                classification = impact_routing.classify_changed_paths(case["paths"])
                self.assertEqual(impact_routing.FULL_AUDIT_ROUTE, classification.route)
                self.assertTrue(classification.full_audit_required)
                self.assertTrue(
                    set(case["expected_reason_ids"]).issubset(
                        classification.reason_ids
                    )
                )
                self.assertEqual(
                    "required",
                    classification.as_dict()["os_wide_audit_disposition"],
                )

    def test_pr_174_regressions_are_explicit_in_corpus(self) -> None:
        case_ids = {
            case["id"] for case in self.corpus["negative_fail_closed_cases"]
        }
        self.assertIn("pr-174-unverified-pack-blob", case_ids)
        self.assertIn("pr-174-trusted-import-code", case_ids)

    def test_empty_invalid_and_unknown_paths_require_full_audit(self) -> None:
        empty = impact_routing.classify_changed_paths(())
        invalid = impact_routing.classify_changed_paths(("../escape",))
        unknown = impact_routing.classify_changed_paths(("new-owner-surface/data.json",))

        self.assertEqual(("empty-change-set",), empty.reason_ids)
        self.assertEqual(("invalid-path",), invalid.reason_ids)
        self.assertEqual(("unknown-path",), unknown.reason_ids)
        self.assertTrue(empty.full_audit_required)
        self.assertTrue(invalid.full_audit_required)
        self.assertTrue(unknown.full_audit_required)

    def test_non_pr_and_unprovable_pr_events_require_full_audit(self) -> None:
        main = impact_routing.classify_event(
            event_name="push",
            repo_root=REPO_ROOT,
            base_ref="",
            head_ref="HEAD",
            explicit_paths=(),
        )
        missing = impact_routing.classify_event(
            event_name="pull_request",
            repo_root=REPO_ROOT,
            base_ref="",
            head_ref="HEAD",
            explicit_paths=(),
        )
        unprovable = impact_routing.classify_event(
            event_name="pull_request",
            repo_root=REPO_ROOT,
            base_ref="missing-ref",
            head_ref="HEAD",
            explicit_paths=(),
        )

        self.assertEqual(("non-pull-request-event",), main.reason_ids)
        self.assertEqual(("missing-change-set",), missing.reason_ids)
        self.assertEqual(("unprovable-change-set",), unprovable.reason_ids)
        self.assertTrue(main.full_audit_required)
        self.assertTrue(missing.full_audit_required)
        self.assertTrue(unprovable.full_audit_required)

    def test_git_change_discovery_preserves_both_sides_of_a_rename(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-b", "main", str(root)), check=True)
            subprocess.run(
                ("git", "-C", str(root), "config", "user.name", "KAG Test"),
                check=True,
            )
            subprocess.run(
                (
                    "git",
                    "-C",
                    str(root),
                    "config",
                    "user.email",
                    "kag-test@example.invalid",
                ),
                check=True,
            )
            old_path = root / "schemas" / "old.schema.json"
            old_path.parent.mkdir()
            old_path.write_text("{}\n", encoding="utf-8")
            subprocess.run(("git", "-C", str(root), "add", "."), check=True)
            subprocess.run(
                ("git", "-C", str(root), "commit", "-m", "base"),
                check=True,
                capture_output=True,
            )
            base = subprocess.run(
                ("git", "-C", str(root), "rev-parse", "HEAD"),
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            new_path = root / "docs" / "old.schema.json"
            new_path.parent.mkdir()
            old_path.rename(new_path)
            subprocess.run(("git", "-C", str(root), "add", "-A"), check=True)
            subprocess.run(
                ("git", "-C", str(root), "commit", "-m", "rename"),
                check=True,
                capture_output=True,
            )

            paths = impact_routing.git_changed_paths(root, base, "HEAD")

        self.assertEqual(
            {"schemas/old.schema.json", "docs/old.schema.json"},
            set(paths),
        )
        self.assertTrue(
            impact_routing.classify_changed_paths(paths).full_audit_required
        )

    def test_required_summary_distinguishes_verified_and_not_required(self) -> None:
        narrow = impact_routing.evaluate_landing_summary(
            event_name="pull_request",
            source_fast_result="success",
            full_audit_result="skipped",
            full_audit_required=False,
        )
        full = impact_routing.evaluate_landing_summary(
            event_name="pull_request",
            source_fast_result="success",
            full_audit_result="success",
            full_audit_required=True,
        )

        self.assertEqual("passed", narrow.verdict)
        self.assertEqual("verified", narrow.source_fast_status)
        self.assertEqual("verified", narrow.owner_family_status)
        self.assertEqual("correctly-not-required", narrow.full_audit_status)
        self.assertEqual("passed", full.verdict)
        self.assertEqual("verified", full.full_audit_status)

    def test_required_summary_rejects_skipped_required_or_replaced_source_fast(self) -> None:
        skipped_full = impact_routing.evaluate_landing_summary(
            event_name="pull_request",
            source_fast_result="success",
            full_audit_result="skipped",
            full_audit_required=True,
        )
        replaced_source_fast = impact_routing.evaluate_landing_summary(
            event_name="pull_request",
            source_fast_result="skipped",
            full_audit_result="success",
            full_audit_required=True,
        )
        non_pr_narrow = impact_routing.evaluate_landing_summary(
            event_name="push",
            source_fast_result="success",
            full_audit_result="skipped",
            full_audit_required=False,
        )

        self.assertEqual("failed", skipped_full.verdict)
        self.assertEqual("failed", replaced_source_fast.verdict)
        self.assertEqual("failed", non_pr_narrow.verdict)

    def test_cli_emits_stable_github_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "github.output"
            exit_code = impact_routing.main(
                (
                    "classify",
                    "--path",
                    "docs/guides/bounded-route.md",
                    "--github-output",
                    str(output),
                )
            )
            values = dict(
                line.split("=", 1)
                for line in output.read_text(encoding="utf-8").splitlines()
            )

        self.assertEqual(0, exit_code)
        self.assertEqual("owner-local", values["route"])
        self.assertEqual("false", values["full-audit-required"])
        self.assertEqual("owner-authored-surface", values["reason-ids"])


if __name__ == "__main__":
    unittest.main()
