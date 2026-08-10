from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import time
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
    def gate(
        self,
        *,
        jobs: int = 1,
        sentinel_receipt: object | None = None,
    ) -> tuple[int, dict[str, object]]:
        return GATE.run_gate(
            repo_root=REPO_ROOT,
            output=GATE.DEFAULT_OUTPUT,
            history_ref="HEAD",
            event_history_ref="HEAD",
            budget_base_ref="HEAD",
            jobs=jobs,
            sentinel_receipt=sentinel_receipt,
        )

    @staticmethod
    def sentinel_handoff(identity: dict[str, str]) -> dict[str, object]:
        component = GATE.sentinel_component(
            repo_root=REPO_ROOT,
            output=GATE.DEFAULT_OUTPUT,
            history_ref="HEAD",
            event_history_ref="HEAD",
            budget_base_ref="HEAD",
        )
        return {
            "schema_version": GATE.SENTINEL_SCHEMA_VERSION,
            "verdict": "verified",
            "candidate": identity,
            "candidate_stable": True,
            "refs": {
                "history_ref": "HEAD",
                "event_history_ref": "HEAD",
                "budget_base_ref": "HEAD",
            },
            "components": [result(component).payload()],
        }

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

    def test_candidate_identity_hashes_dirty_tracked_and_untracked_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            subprocess.run(("git", "init", "-q"), cwd=repo, check=True)
            subprocess.run(
                ("git", "config", "user.email", "test@example.invalid"),
                cwd=repo,
                check=True,
            )
            subprocess.run(
                ("git", "config", "user.name", "Owner Gate Test"),
                cwd=repo,
                check=True,
            )
            tracked = repo / "tracked.txt"
            tracked.write_text("base\n", encoding="utf-8")
            subprocess.run(("git", "add", "tracked.txt"), cwd=repo, check=True)
            subprocess.run(("git", "commit", "-qm", "base"), cwd=repo, check=True)

            tracked.write_text("first\n", encoding="utf-8")
            untracked = repo / "untracked.txt"
            untracked.write_text("one\n", encoding="utf-8")
            first = GATE.candidate_identity(repo)

            tracked.write_text("second\n", encoding="utf-8")
            second = GATE.candidate_identity(repo)
            self.assertNotEqual(first, second)

            untracked.write_text("two\n", encoding="utf-8")
            third = GATE.candidate_identity(repo)
            self.assertNotEqual(second, third)

            metadata = tracked.lstat()
            os.utime(
                tracked,
                ns=(metadata.st_atime_ns, metadata.st_mtime_ns + 1_000_000_000),
            )
            fourth = GATE.candidate_identity(repo)
            self.assertNotEqual(third, fourth)

    def test_candidate_mutation_identity_ignores_only_access_times(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            subprocess.run(("git", "init", "-q"), cwd=repo, check=True)
            subprocess.run(
                ("git", "config", "user.email", "test@example.invalid"),
                cwd=repo,
                check=True,
            )
            subprocess.run(
                ("git", "config", "user.name", "Owner Gate Test"),
                cwd=repo,
                check=True,
            )
            tracked = repo / "tracked.txt"
            tracked.write_text("base\n", encoding="utf-8")
            subprocess.run(("git", "add", "tracked.txt"), cwd=repo, check=True)
            subprocess.run(("git", "commit", "-qm", "base"), cwd=repo, check=True)

            gate_before = GATE.candidate_identity(repo)
            full_before = GATE.isolation.capture_candidate_snapshot(repo)
            metadata = tracked.lstat()
            future_atime_ns = max(
                metadata.st_atime_ns + 1_000_000_000,
                time.time_ns() + 86_400_000_000_000,
            )
            os.utime(
                tracked,
                ns=(future_atime_ns, metadata.st_mtime_ns),
            )
            gate_after = GATE.candidate_identity(repo)
            full_after = GATE.isolation.capture_candidate_snapshot(repo)

            self.assertEqual(gate_before, gate_after)
            self.assertEqual(
                full_before.mutation_identity(),
                full_after.mutation_identity(),
            )
            self.assertNotEqual(full_before.identity(), full_after.identity())

    def test_component_failure_requires_a_changed_candidate(self) -> None:
        identity = {
            "repo_root": REPO_ROOT.as_posix(),
            "head": "a" * 40,
            "index_tree": "b" * 40,
            "candidate_identity": "sha256:" + "c" * 64,
        }

        def fake_run(component: GATE.Component, *, repo_root: Path) -> GATE.ComponentResult:
            self.assertEqual(REPO_ROOT, repo_root)
            return result(
                component,
                returncode=1 if component.component_id == "family-contract" else 0,
            )

        with (
            mock.patch.object(GATE, "candidate_identity", return_value=identity),
            mock.patch.object(GATE, "run_component", side_effect=fake_run),
        ):
            code, receipt = self.gate(jobs=2)

        self.assertEqual(1, code)
        self.assertEqual("owner_family_proof_failed", receipt["failure_type"])
        self.assertEqual("fix_candidate", receipt["action_class"])

    def test_verified_same_run_sentinel_handoff_skips_duplicate_sentinel(self) -> None:
        identity = {
            "repo_root": REPO_ROOT.as_posix(),
            "head": "a" * 40,
            "index_tree": "b" * 40,
            "candidate_identity": "sha256:" + "c" * 64,
        }
        calls: list[str] = []

        def fake_run(component: GATE.Component, *, repo_root: Path) -> GATE.ComponentResult:
            self.assertEqual(REPO_ROOT, repo_root)
            calls.append(component.component_id)
            return result(component)

        with (
            mock.patch.object(GATE, "candidate_identity", return_value=identity),
            mock.patch.object(GATE, "run_component", side_effect=fake_run),
        ):
            code, receipt = self.gate(
                jobs=2,
                sentinel_receipt=self.sentinel_handoff(identity),
            )

        self.assertEqual(0, code)
        self.assertEqual("same-run-handoff", receipt["sentinel_source"])
        self.assertCountEqual(
            ["full-parity", "family-contract", "compatibility-assembly"],
            calls,
        )
        self.assertEqual(4, len(receipt["components"]))

    def test_sentinel_handoff_rejects_a_different_candidate_before_fanout(self) -> None:
        expected = {
            "repo_root": REPO_ROOT.as_posix(),
            "head": "a" * 40,
            "index_tree": "b" * 40,
            "candidate_identity": "sha256:" + "c" * 64,
        }
        observed = dict(expected, candidate_identity="sha256:" + "d" * 64)
        with (
            mock.patch.object(GATE, "candidate_identity", return_value=observed),
            mock.patch.object(GATE, "run_component") as run_component,
        ):
            code, receipt = self.gate(
                jobs=2,
                sentinel_receipt=self.sentinel_handoff(expected),
            )

        self.assertEqual(1, code)
        self.assertEqual("sentinel_handoff_invalid", receipt["failure_type"])
        self.assertEqual("rerun_stable_candidate", receipt["action_class"])
        run_component.assert_not_called()

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

    def test_component_disables_python_bytecode_side_effects(self) -> None:
        component = GATE.Component("check", ("python", "check.py"))
        completed = subprocess.CompletedProcess(component.command, 0, "ok", "")

        with mock.patch.object(GATE.subprocess, "run", return_value=completed) as run:
            observed = GATE.run_component(component, repo_root=REPO_ROOT)

        self.assertEqual(0, observed.returncode)
        self.assertEqual("1", run.call_args.kwargs["env"]["PYTHONDONTWRITEBYTECODE"])

    def test_component_keeps_fresh_python_checkout_metadata_stable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            (repo / "fresh_import.py").write_text("VALUE = 1\n", encoding="utf-8")
            initial_mtime = repo.lstat().st_mtime_ns
            component = GATE.Component(
                "fresh-python-check",
                (GATE.sys.executable, "-c", "import fresh_import"),
            )

            observed = GATE.run_component(component, repo_root=repo)

            self.assertEqual(0, observed.returncode)
            self.assertFalse((repo / "__pycache__").exists())
            self.assertEqual(initial_mtime, repo.lstat().st_mtime_ns)


if __name__ == "__main__":
    unittest.main()
