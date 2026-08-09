from __future__ import annotations

from pathlib import Path
from unittest import mock
import unittest

from scripts import repo_local_kag_gate as GATE


REPO_ROOT = Path(__file__).resolve().parents[1]


def result(component: GATE.Component, returncode: int = 0) -> GATE.ComponentResult:
    return GATE.ComponentResult(
        component_id=component.component_id,
        command=component.command,
        returncode=returncode,
        duration_ms=1,
        stdout="",
        stderr="failure" if returncode else "",
    )


class RepoLocalKagGateTests(unittest.TestCase):
    def gate(self, *, jobs: int = 1) -> tuple[int, dict[str, object]]:
        return GATE.run_gate(
            repo_root=REPO_ROOT,
            output=GATE.DEFAULT_OUTPUT,
            history_ref="HEAD",
            event_history_ref="HEAD",
            budget_base_ref="HEAD",
            jobs=jobs,
        )

    def test_incremental_failure_stops_before_expensive_fanout(self) -> None:
        calls: list[str] = []

        def fake_run(component: GATE.Component, *, repo_root: Path) -> GATE.ComponentResult:
            self.assertEqual(REPO_ROOT, repo_root)
            calls.append(component.component_id)
            return result(component, returncode=1)

        identity = {
            "repo_root": REPO_ROOT.as_posix(),
            "head": "a" * 40,
            "index_tree": "b" * 40,
            "status_digest": "sha256:" + "c" * 64,
        }
        with (
            mock.patch.object(GATE, "candidate_identity", return_value=identity),
            mock.patch.object(GATE, "run_component", side_effect=fake_run),
        ):
            code, receipt = self.gate()

        self.assertEqual(1, code)
        self.assertEqual(["incremental-drift-sentinel"], calls)
        self.assertEqual("owner_family_drift", receipt["failure_type"])
        self.assertEqual("regenerate_owner_family", receipt["action_class"])

    def test_clean_sentinel_runs_every_canonical_component(self) -> None:
        calls: list[str] = []

        def fake_run(component: GATE.Component, *, repo_root: Path) -> GATE.ComponentResult:
            self.assertEqual(REPO_ROOT, repo_root)
            calls.append(component.component_id)
            return result(component)

        identity = {
            "repo_root": REPO_ROOT.as_posix(),
            "head": "a" * 40,
            "index_tree": "b" * 40,
            "status_digest": "sha256:" + "c" * 64,
        }
        with (
            mock.patch.object(GATE, "candidate_identity", return_value=identity),
            mock.patch.object(GATE, "run_component", side_effect=fake_run),
        ):
            code, receipt = self.gate(jobs=3)

        self.assertEqual(0, code)
        self.assertEqual(
            [
                "incremental-drift-sentinel",
                "full-parity",
                "family-contract",
                "compatibility-assembly",
            ],
            [component["component_id"] for component in receipt["components"]],
        )
        self.assertCountEqual(
            [
                "incremental-drift-sentinel",
                "full-parity",
                "family-contract",
                "compatibility-assembly",
            ],
            calls,
        )
        self.assertEqual("verified", receipt["verdict"])
        self.assertTrue(receipt["candidate_stable"])

    def test_changed_candidate_rejects_otherwise_green_results(self) -> None:
        identities = [
            {
                "repo_root": REPO_ROOT.as_posix(),
                "head": "a" * 40,
                "index_tree": "b" * 40,
                "status_digest": "sha256:" + "c" * 64,
            },
            {
                "repo_root": REPO_ROOT.as_posix(),
                "head": "a" * 40,
                "index_tree": "b" * 40,
                "status_digest": "sha256:" + "d" * 64,
            },
        ]
        with (
            mock.patch.object(GATE, "candidate_identity", side_effect=identities),
            mock.patch.object(
                GATE,
                "run_component",
                side_effect=lambda component, *, repo_root: result(component),
            ),
        ):
            code, receipt = self.gate()

        self.assertEqual(1, code)
        self.assertEqual("candidate_identity_changed", receipt["failure_type"])
        self.assertFalse(receipt["candidate_stable"])

    def test_generator_commands_keep_exact_history_and_budget_boundaries(self) -> None:
        command = GATE.generator_command(
            repo_root=REPO_ROOT,
            output=GATE.DEFAULT_OUTPUT,
            history_ref="history",
            event_history_ref="events",
            budget_base_ref="budget",
            incremental=True,
        )

        self.assertIn("--portable-family", command)
        self.assertIn("--incremental", command)
        self.assertIn("--check", command)
        self.assertEqual("history", command[command.index("--history-ref") + 1])
        self.assertEqual("events", command[command.index("--event-history-ref") + 1])
        self.assertEqual("budget", command[command.index("--budget-base-ref") + 1])


if __name__ == "__main__":
    unittest.main()
