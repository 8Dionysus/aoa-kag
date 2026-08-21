from __future__ import annotations

import sys
import tempfile
import time
import unittest
import argparse
import json
from pathlib import Path
from unittest.mock import patch

from scripts import ci_preflight_dag


class CiPreflightDagTests(unittest.TestCase):
    @staticmethod
    def sentinel_receipt(verdict: str = "passed") -> dict[str, object]:
        return {
            "schema_version": "aoa-kag-prepare-landing-receipt-v1",
            "mode": "sentinel",
            "verdict": verdict,
            "partial_result_is_green": False,
        }

    def test_parallel_preflight_overlaps_independent_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            started = time.perf_counter()
            checkout, sentinel = ci_preflight_dag.run_parallel_preflight(
                (sys.executable, "-c", "import time; time.sleep(0.2)"),
                (sys.executable, "-c", "import time; time.sleep(0.2)"),
                repo_root=Path(tmpdir),
            )
            wall = time.perf_counter() - started

        self.assertEqual(0, checkout.returncode)
        self.assertEqual(0, sentinel.returncode)
        self.assertLess(wall, 0.38)

    def test_sentinel_failure_cancels_only_its_checkout_peer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            started = time.perf_counter()
            checkout, sentinel = ci_preflight_dag.run_parallel_preflight(
                (sys.executable, "-c", "import time; time.sleep(5)"),
                (sys.executable, "-c", "raise SystemExit(7)"),
                repo_root=Path(tmpdir),
            )
            wall = time.perf_counter() - started

        self.assertEqual(7, sentinel.returncode)
        self.assertTrue(checkout.cancelled_by_peer)
        self.assertLess(wall, 2)

    def test_checkout_failure_cancels_only_its_sentinel_peer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            checkout, sentinel = ci_preflight_dag.run_parallel_preflight(
                (sys.executable, "-c", "raise SystemExit(9)"),
                (sys.executable, "-c", "import time; time.sleep(5)"),
                repo_root=Path(tmpdir),
            )

        self.assertEqual(9, checkout.returncode)
        self.assertTrue(sentinel.cancelled_by_peer)

    def test_child_receipt_validation_is_fail_closed(self) -> None:
        self.assertEqual(
            "missing-or-invalid-json",
            ci_preflight_dag.child_receipt_error(None, returncode=0),
        )
        self.assertEqual(
            "verdict-return-code-mismatch",
            ci_preflight_dag.child_receipt_error(
                self.sentinel_receipt("drift"),
                returncode=0,
            ),
        )
        self.assertIsNone(
            ci_preflight_dag.child_receipt_error(
                self.sentinel_receipt("inapplicable"),
                returncode=0,
            )
        )

    def test_successful_child_without_receipt_cannot_pass_scheduler(self) -> None:
        args = argparse.Namespace(
            base_ref="base", jobs=3, mode="candidate", receipt_output=None
        )
        success = ci_preflight_dag.ProcessResult(("command",), 0, 1, False)
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            ci_preflight_dag,
            "run_parallel_preflight",
            return_value=(success, success),
        ), patch.object(ci_preflight_dag.subprocess, "run") as generated:
            code = ci_preflight_dag.run_preflight(
                args,
                receipt_parent=Path(tmpdir),
            )

        self.assertEqual(1, code)
        generated.assert_not_called()

    def test_candidate_uses_separate_coverage_seed_without_changing_base(self) -> None:
        args = argparse.Namespace(
            base_ref="history",
            coverage_seed_ref="candidate",
            jobs=3,
            mode="candidate",
            receipt_output=None,
        )
        success = ci_preflight_dag.ProcessResult(("command",), 0, 1, False)

        def parallel(_checkout, sentinel, *, repo_root):
            del repo_root
            seed_index = sentinel.index("--external-seed-ref")
            self.assertEqual("candidate", sentinel[seed_index + 1])
            Path(sentinel[-1]).write_text(
                json.dumps(self.sentinel_receipt()),
                encoding="utf-8",
            )
            return success, success

        def generated(command, *, cwd, check):
            del cwd, check
            seed_index = command.index("--external-seed-ref")
            self.assertEqual("candidate", command[seed_index + 1])
            Path(command[-1]).write_text(
                json.dumps(self.sentinel_receipt()),
                encoding="utf-8",
            )
            return unittest.mock.Mock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            ci_preflight_dag,
            "run_parallel_preflight",
            side_effect=parallel,
        ), patch.object(
            ci_preflight_dag.subprocess,
            "run",
            side_effect=generated,
        ):
            code = ci_preflight_dag.run_preflight(
                args,
                receipt_parent=Path(tmpdir),
            )

        self.assertEqual(0, code)

    def test_direct_control_runs_only_the_same_bounded_checkout(self) -> None:
        args = argparse.Namespace(
            base_ref="base",
            jobs=3,
            mode="direct-control",
            receipt_output=None,
        )
        completed = unittest.mock.Mock(returncode=0)
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            ci_preflight_dag.subprocess,
            "run",
            return_value=completed,
        ) as run, patch.object(ci_preflight_dag, "write_receipt") as write_receipt:
            code = ci_preflight_dag.run_preflight(
                args,
                receipt_parent=Path(tmpdir),
            )

        self.assertEqual(0, code)
        command = run.call_args.args[0]
        self.assertIn("scripts/sync_provider_checkouts.py", command)
        self.assertIn("--exclude-secret-checkouts", command)
        aggregate = write_receipt.call_args.args[1]
        self.assertEqual("direct-control", aggregate["experiment_mode"])
        self.assertFalse(aggregate["partial_result_is_green"])

    def test_sentinel_infrastructure_failure_is_not_misclassified_as_drift(self) -> None:
        args = argparse.Namespace(
            base_ref="base", jobs=3, mode="candidate", receipt_output=None
        )

        def parallel(_checkout, sentinel, *, repo_root):
            del repo_root
            receipt_path = Path(sentinel[-1])
            payload = self.sentinel_receipt("failed")
            payload.update(
                {
                    "failure_type": "sentinel_infrastructure_failure",
                    "action_class": "code_fix",
                }
            )
            receipt_path.write_text(json.dumps(payload), encoding="utf-8")
            return (
                ci_preflight_dag.ProcessResult(("checkout",), -15, 2, True),
                ci_preflight_dag.ProcessResult(("sentinel",), 1, 1, False),
            )

        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            ci_preflight_dag,
            "run_parallel_preflight",
            side_effect=parallel,
        ), patch.object(ci_preflight_dag, "write_receipt") as write_receipt:
            code = ci_preflight_dag.run_preflight(
                args,
                receipt_parent=Path(tmpdir),
            )

        self.assertEqual(1, code)
        aggregate = write_receipt.call_args.args[1]
        self.assertEqual("sentinel_infrastructure_failure", aggregate["failure_type"])
        self.assertEqual("code_fix", aggregate["action_class"])


if __name__ == "__main__":
    unittest.main()
