from __future__ import annotations

import copy
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

from scripts import prepare_landing
from scripts import generate_repo_local_kag_coverage as coverage_generation


REPO_ROOT = Path(__file__).resolve().parents[1]


def git(repo_root: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ("git", *args),
        cwd=repo_root,
        input=input_bytes,
        check=True,
        capture_output=True,
    ).stdout


class PrepareLandingTests(unittest.TestCase):
    def make_repo(self, root: Path) -> Path:
        repo = root / "repo"
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "test@example.invalid")
        git(repo, "config", "user.name", "Prepare Landing Test")
        (repo / "generated").mkdir()
        (repo / "generated" / "out.txt").write_text("base\n", encoding="utf-8")
        (repo / "source.txt").write_text("base\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "base")
        return repo

    @staticmethod
    def fake_converge(
        repo_root: Path,
        _refs: object,
        *,
        max_iterations: int,
        full_coverage_cache: Path | None = None,
    ) -> tuple[int, str]:
        assert max_iterations > 0
        source = git(repo_root, "show", ":source.txt").decode("utf-8")
        note = (repo_root / "note.txt").read_text(encoding="utf-8")
        (repo_root / "generated" / "out.txt").write_text(source + note, encoding="utf-8")
        git(repo_root, "add", "generated/out.txt")
        return 2, git(repo_root, "write-tree").decode("ascii").strip()

    def candidate_repo(self, root: Path) -> tuple[Path, str, bytes]:
        repo = self.make_repo(root)
        (repo / "source.txt").write_text("candidate\n", encoding="utf-8")
        git(repo, "add", "source.txt")
        (repo / "note.txt").write_text("untracked\n", encoding="utf-8")
        head = git(repo, "rev-parse", "HEAD").decode("ascii").strip()
        cached = git(repo, "diff", "--cached", "--binary", "--full-index")
        return repo, head, cached

    def run_isolated(self, repo: Path, temp_root: Path, head: str, *, mode: str):
        with patch.object(
            prepare_landing,
            "verify_provider_identities",
            return_value=(),
        ), patch.object(
            prepare_landing,
            "converge_scc",
            side_effect=self.fake_converge,
        ), patch.object(
            prepare_landing,
            "ensure_budget_receipt",
            return_value="not_required",
        ), patch.object(
            prepare_landing,
            "final_confirmation",
        ):
            return prepare_landing.prepare_landing(
                repo,
                mode=mode,
                max_iterations=3,
                history_ref=head,
                event_history_ref=head,
                budget_base_ref=head,
                budget_reason=None,
                temp_root=temp_root,
            )

    def test_check_detects_drift_without_changing_worktree_or_index(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo, head, cached_before = self.candidate_repo(Path(repo_tmp))
            generated_before = (repo / "generated" / "out.txt").read_bytes()

            code, receipt = self.run_isolated(repo, Path(work_tmp), head, mode="check")

            self.assertEqual(1, code)
            self.assertEqual("drift", receipt["verdict"], receipt)
            self.assertTrue(receipt["fixed_point"]["drift_detected"])
            self.assertEqual(generated_before, (repo / "generated" / "out.txt").read_bytes())
            self.assertEqual(
                cached_before,
                git(repo, "diff", "--cached", "--binary", "--full-index"),
            )
            self.assertTrue((repo / "note.txt").is_file())

    def test_apply_updates_only_worktree_and_preserves_caller_index(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo, head, cached_before = self.candidate_repo(Path(repo_tmp))

            code, receipt = self.run_isolated(repo, Path(work_tmp), head, mode="apply")

            self.assertEqual(0, code)
            self.assertEqual("prepared", receipt["verdict"])
            self.assertEqual(
                "candidate\nuntracked\n",
                (repo / "generated" / "out.txt").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                cached_before,
                git(repo, "diff", "--cached", "--binary", "--full-index"),
            )
            self.assertIn(
                b"generated/out.txt",
                git(repo, "diff", "--name-only"),
            )
            self.assertEqual("verified", receipt["candidate_seal"]["status"])
            self.assertEqual(
                receipt["candidate_seal"]["content_identity"],
                receipt["candidate_seal"]["validated_content_identity"],
            )
            self.assertFalse(
                receipt["candidate_seal"]["immediate_zero_drift_check_required"]
            )

    def test_content_identity_ignores_times_but_not_candidate_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            first = prepare_landing.capture_candidate_snapshot(repo)
            source = repo / "source.txt"
            metadata = source.lstat()
            os.utime(
                source,
                ns=(metadata.st_atime_ns, metadata.st_mtime_ns + 1_000_000),
            )
            retimed = prepare_landing.capture_candidate_snapshot(repo)
            source.write_text("changed\n", encoding="utf-8")
            changed = prepare_landing.capture_candidate_snapshot(repo)

            self.assertNotEqual(first.identity(), retimed.identity())
            self.assertEqual(first.content_identity(), retimed.content_identity())
            self.assertNotEqual(retimed.content_identity(), changed.content_identity())

    def test_worktree_content_identity_survives_only_staging(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo, _head, _cached_before = self.candidate_repo(Path(repo_tmp))
            before = prepare_landing.capture_candidate_snapshot(repo)
            git(repo, "add", "note.txt")
            after = prepare_landing.capture_candidate_snapshot(repo)

            self.assertNotEqual(before.content_identity(), after.content_identity())
            self.assertEqual(
                before.worktree_content_identity(),
                after.worktree_content_identity(),
            )

    def test_content_identity_binds_staged_tracked_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            source = repo / "source.txt"
            before = prepare_landing.capture_candidate_snapshot(repo)

            source.unlink()
            unstaged = prepare_landing.capture_candidate_snapshot(repo)
            git(repo, "add", "source.txt")
            deleted = prepare_landing.capture_candidate_snapshot(repo)

            self.assertNotEqual(
                before.worktree_content_identity(),
                deleted.worktree_content_identity(),
            )
            self.assertEqual(
                unstaged.worktree_content_identity(),
                deleted.worktree_content_identity(),
            )
            self.assertNotEqual(unstaged.content_identity(), deleted.content_identity())
            self.assertIn(b"source.txt", deleted.cached_patch_bytes)

    def test_applied_seal_accepts_exact_staging_transition(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo, head, _cached_before = self.candidate_repo(Path(repo_tmp))
            code, apply_receipt = self.run_isolated(
                repo,
                Path(work_tmp),
                head,
                mode="apply",
            )
            self.assertEqual(0, code, apply_receipt)
            git(repo, "add", *apply_receipt["fixed_point"]["changed_paths"])

            with patch.object(
                prepare_landing,
                "verify_provider_identities",
                return_value=(),
            ):
                verify_code, verify_receipt = prepare_landing.verify_applied_seal(
                    repo,
                    apply_receipt,
                )

            self.assertEqual(0, verify_code, verify_receipt)
            self.assertEqual("verified", verify_receipt["verdict"])
            self.assertEqual(
                apply_receipt["candidate_seal"]["fixed_point_tree"],
                verify_receipt["fixed_point_tree"],
            )
            self.assertFalse(
                verify_receipt["immediate_zero_drift_check_required"]
            )

    def test_applied_seal_rejects_unstaged_generated_patch(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo, head, _cached_before = self.candidate_repo(Path(repo_tmp))
            code, apply_receipt = self.run_isolated(
                repo,
                Path(work_tmp),
                head,
                mode="apply",
            )
            self.assertEqual(0, code, apply_receipt)

            with patch.object(
                prepare_landing,
                "verify_provider_identities",
                return_value=(),
            ):
                verify_code, verify_receipt = prepare_landing.verify_applied_seal(
                    repo,
                    apply_receipt,
                )

            self.assertEqual(1, verify_code)
            self.assertEqual(
                "applied_seal_index_tree_mismatch",
                verify_receipt["failure_type"],
            )

    def test_applied_seal_rejects_post_staging_worktree_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo, head, _cached_before = self.candidate_repo(Path(repo_tmp))
            code, apply_receipt = self.run_isolated(
                repo,
                Path(work_tmp),
                head,
                mode="apply",
            )
            self.assertEqual(0, code, apply_receipt)
            git(repo, "add", *apply_receipt["fixed_point"]["changed_paths"])
            (repo / "generated" / "out.txt").write_text(
                "tampered after staging\n",
                encoding="utf-8",
            )

            with patch.object(
                prepare_landing,
                "verify_provider_identities",
                return_value=(),
            ):
                verify_code, verify_receipt = prepare_landing.verify_applied_seal(
                    repo,
                    apply_receipt,
                )

            self.assertEqual(1, verify_code)
            self.assertEqual(
                "applied_seal_worktree_mismatch",
                verify_receipt["failure_type"],
            )

    def test_apply_seal_rejects_post_apply_content_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo, head, _cached_before = self.candidate_repo(Path(repo_tmp))
            real_apply = prepare_landing.apply_generated_patch

            def corrupt_after_apply(
                source_root: Path,
                patch_bytes: bytes,
                *,
                expected_snapshot: prepare_landing.CandidateSnapshot,
            ) -> None:
                real_apply(
                    source_root,
                    patch_bytes,
                    expected_snapshot=expected_snapshot,
                )
                (source_root / "generated" / "out.txt").write_text(
                    "tampered after apply\n",
                    encoding="utf-8",
                )

            with patch.object(
                prepare_landing,
                "apply_generated_patch",
                side_effect=corrupt_after_apply,
            ):
                code, receipt = self.run_isolated(
                    repo,
                    Path(work_tmp),
                    head,
                    mode="apply",
                )

            self.assertEqual(1, code)
            self.assertEqual(
                "applied_candidate_seal_mismatch",
                receipt["failure_type"],
            )
            self.assertEqual("rollback_generated_patch", receipt["action_class"])

    def test_changed_tree_paths_reports_both_sides_of_a_rename(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            before_tree = git(repo, "write-tree").decode("ascii").strip()
            git(repo, "mv", "generated/out.txt", "generated/renamed.txt")
            after_tree = git(repo, "write-tree").decode("ascii").strip()

            self.assertEqual(
                {"generated/out.txt", "generated/renamed.txt"},
                set(prepare_landing.changed_tree_paths(repo, before_tree, after_tree)),
            )

    def test_prepare_rejects_provider_identity_change_at_closeout(self) -> None:
        before = (
            {
                "owner": "external",
                "head": "a" * 40,
                "head_tree": "b" * 40,
                "posture": "pinned",
            },
        )
        after = (
            {
                "owner": "external",
                "head": "a" * 40,
                "head_tree": "c" * 40,
                "posture": "pinned",
            },
        )
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo, head, _cached_before = self.candidate_repo(Path(repo_tmp))
            with patch.object(
                prepare_landing,
                "verify_provider_identities",
                side_effect=(before, after),
            ), patch.object(
                prepare_landing,
                "converge_budgeted_scc",
                return_value=(1, git(repo, "write-tree").decode("ascii").strip(), "not_required"),
            ), patch.object(
                prepare_landing,
                "final_confirmation",
            ):
                code, receipt = prepare_landing.prepare_landing(
                    repo,
                    mode="check",
                    max_iterations=3,
                    history_ref=head,
                    event_history_ref=head,
                    budget_base_ref=head,
                    budget_reason=None,
                    temp_root=Path(work_tmp),
                )

        self.assertEqual(1, code)
        self.assertEqual("provider_identity_mismatch", receipt["failure_type"])

    def test_apply_fails_closed_when_candidate_changes_during_preparation(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo, head, _cached_before = self.candidate_repo(Path(repo_tmp))

            def race_converge(
                temporary_root: Path,
                refs: object,
                *,
                max_iterations: int,
                full_coverage_cache: Path | None = None,
            ) -> tuple[int, str]:
                result = self.fake_converge(
                    temporary_root,
                    refs,
                    max_iterations=max_iterations,
                    full_coverage_cache=full_coverage_cache,
                )
                (repo / "source.txt").write_text("concurrent\n", encoding="utf-8")
                return result

            with patch.object(
                prepare_landing,
                "verify_provider_identities",
                return_value=(),
            ), patch.object(
                prepare_landing,
                "converge_scc",
                side_effect=race_converge,
            ), patch.object(
                prepare_landing,
                "ensure_budget_receipt",
                return_value="not_required",
            ), patch.object(prepare_landing, "final_confirmation"):
                code, receipt = prepare_landing.prepare_landing(
                    repo,
                    mode="apply",
                    max_iterations=3,
                    history_ref=head,
                    event_history_ref=head,
                    budget_base_ref=head,
                    budget_reason=None,
                    temp_root=Path(work_tmp),
                )

            self.assertEqual(1, code)
            self.assertEqual("candidate_snapshot_changed", receipt["failure_type"])
            self.assertEqual("base\n", (repo / "generated" / "out.txt").read_text())

    def test_check_also_fails_closed_when_candidate_changes_during_preparation(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo, head, _cached_before = self.candidate_repo(Path(repo_tmp))

            def race_converge(
                temporary_root: Path,
                refs: object,
                *,
                max_iterations: int,
                full_coverage_cache: Path | None = None,
            ) -> tuple[int, str]:
                result = self.fake_converge(
                    temporary_root,
                    refs,
                    max_iterations=max_iterations,
                    full_coverage_cache=full_coverage_cache,
                )
                (repo / "source.txt").write_text("concurrent\n", encoding="utf-8")
                return result

            with patch.object(
                prepare_landing,
                "verify_provider_identities",
                return_value=(),
            ), patch.object(
                prepare_landing,
                "converge_scc",
                side_effect=race_converge,
            ), patch.object(
                prepare_landing,
                "ensure_budget_receipt",
                return_value="not_required",
            ), patch.object(prepare_landing, "final_confirmation"):
                code, receipt = prepare_landing.prepare_landing(
                    repo,
                    mode="check",
                    max_iterations=3,
                    history_ref=head,
                    event_history_ref=head,
                    budget_base_ref=head,
                    budget_reason=None,
                    temp_root=Path(work_tmp),
                )

            self.assertEqual(1, code)
            self.assertEqual("candidate_snapshot_changed", receipt["failure_type"])

    def test_invalid_initial_snapshot_still_returns_typed_failure_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / "nested"
            nested.mkdir()

            code, receipt = prepare_landing.prepare_landing(
                nested,
                mode="check",
                max_iterations=3,
                history_ref=None,
                event_history_ref=None,
                budget_base_ref=None,
                budget_reason=None,
                temp_root=Path(work_tmp),
            )

            self.assertEqual(1, code)
            self.assertEqual("candidate_snapshot_invalid", receipt["failure_type"])
            self.assertEqual({"state": "unavailable"}, receipt["candidate"])

    def test_snapshot_hashes_untracked_directory_contents(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            untracked = repo / "validation-input"
            untracked.mkdir()
            (untracked / "receipt.txt").write_text("first\n", encoding="utf-8")

            first = prepare_landing.capture_candidate_snapshot(repo)
            (untracked / "receipt.txt").write_text("second\n", encoding="utf-8")
            second = prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual(("validation-input/receipt.txt",), first.untracked_paths)
            self.assertNotEqual(first.identity(), second.identity())

    def test_snapshot_hashes_untracked_permission_modes(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            untracked = repo / "run-validation.sh"
            untracked.write_text("#!/bin/sh\n", encoding="utf-8")
            first = prepare_landing.capture_candidate_snapshot(repo)
            untracked.chmod(0o755)
            second = prepare_landing.capture_candidate_snapshot(repo)

            self.assertNotEqual(first.identity(), second.identity())

    def test_snapshot_hashes_nonignored_directory_state_and_modes(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            first = prepare_landing.capture_candidate_snapshot(repo)
            empty = repo / "validation-input" / "empty"
            empty.mkdir(parents=True)
            second = prepare_landing.capture_candidate_snapshot(repo)
            empty.chmod(0o750)
            third = prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual(("generated",), first.directories)
            self.assertEqual(
                ("generated", "validation-input", "validation-input/empty"),
                second.directories,
            )
            self.assertNotEqual(first.identity(), second.identity())
            self.assertNotEqual(second.identity(), third.identity())

    def test_outer_materialization_preserves_untracked_hardlinks(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            first = repo / "first.txt"
            second = repo / "second.txt"
            first.write_text("shared\n", encoding="utf-8")
            os.link(first, second)

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(
                repo,
                isolated,
                snapshot,
            )

            self.assertEqual(
                (isolated / "first.txt").lstat().st_ino,
                (isolated / "second.txt").lstat().st_ino,
            )
            (isolated / "first.txt").write_text("changed\n", encoding="utf-8")
            self.assertEqual(
                "changed\n",
                (isolated / "second.txt").read_text(encoding="utf-8"),
            )

    def test_outer_snapshot_rejects_sparse_untracked_file(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            sparse = repo / "candidate.sparse"
            with sparse.open("wb") as handle:
                handle.seek(8 * 1024 * 1024 - 1)
                handle.write(b"\0")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                ["candidate.sparse"],
                raised.exception.details["sparse_worktree_paths"],
            )

    def test_outer_materialization_preserves_directory_times(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            candidate = repo / "validation-input"
            candidate.mkdir()
            (candidate / "input.txt").write_text("input\n", encoding="utf-8")
            expected_mtime = 1_700_000_000_123_456_789
            candidate_metadata = candidate.lstat()
            os.utime(
                candidate,
                ns=(candidate_metadata.st_atime_ns, expected_mtime),
            )

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            expected_atime = candidate.lstat().st_atime_ns
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)

            self.assertIn(
                ("validation-input", expected_atime, expected_mtime),
                snapshot.worktree_times,
            )
            self.assertEqual(
                expected_atime,
                (isolated / "validation-input").lstat().st_atime_ns,
            )
            self.assertEqual(
                expected_mtime,
                (isolated / "validation-input").lstat().st_mtime_ns,
            )

    def test_outer_materialization_preserves_tracked_file_modes(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            tracked = repo / "readonly.txt"
            tracked.write_text("bound mode\n", encoding="utf-8")
            git(repo, "add", "readonly.txt")
            git(repo, "commit", "-qm", "add readonly input")
            tracked.chmod(0o400)

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)

            self.assertIn(("readonly.txt", 0o400), snapshot.tracked_file_modes)
            self.assertEqual(
                0o400,
                stat.S_IMODE((isolated / "readonly.txt").lstat().st_mode),
            )

    def test_outer_materialization_preserves_checkout_root_mode(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            isolated = Path(work_tmp) / "isolated"
            repo.chmod(0o555)
            try:
                snapshot = prepare_landing.capture_candidate_snapshot(repo)
                git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
                prepare_landing.materialize_candidate(repo, isolated, snapshot)

                self.assertEqual(0o555, snapshot.root_mode)
                self.assertEqual(
                    0o555,
                    stat.S_IMODE(isolated.lstat().st_mode),
                )
            finally:
                repo.chmod(0o755)
                if isolated.exists():
                    isolated.chmod(0o755)

    def test_outer_materialization_preserves_tracked_file_mtimes(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            tracked = repo / "dated.txt"
            tracked.write_text("bound timestamp\n", encoding="utf-8")
            git(repo, "add", "dated.txt")
            git(repo, "commit", "-qm", "add dated input")
            expected_mtime = 946_684_800_123_456_789
            metadata = tracked.lstat()
            os.utime(tracked, ns=(metadata.st_atime_ns, expected_mtime))

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            expected_atime = tracked.lstat().st_atime_ns
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)

            self.assertIn(
                ("dated.txt", expected_atime, expected_mtime),
                snapshot.worktree_times,
            )
            self.assertEqual(
                expected_atime,
                (isolated / "dated.txt").lstat().st_atime_ns,
            )
            self.assertEqual(
                expected_mtime,
                (isolated / "dated.txt").lstat().st_mtime_ns,
            )

    def test_outer_materialization_preserves_tracked_file_xattrs(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            tracked = repo / "labeled.txt"
            tracked.write_text("bound metadata\n", encoding="utf-8")
            git(repo, "add", "labeled.txt")
            git(repo, "commit", "-qm", "add labeled input")
            try:
                os.setxattr(
                    tracked,
                    "user.aoa-kag-outer-test",
                    b"bound outer metadata",
                    follow_symlinks=False,
                )
            except OSError as exc:
                self.skipTest(f"extended attributes unavailable: {exc}")

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)

            self.assertEqual(
                b"bound outer metadata",
                os.getxattr(
                    isolated / "labeled.txt",
                    "user.aoa-kag-outer-test",
                    follow_symlinks=False,
                ),
            )

    def test_outer_snapshot_rejects_nonportable_directory_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            foreign = repo / "foreign-directory"
            foreign.mkdir()
            real_lstat = Path.lstat

            def foreign_owned_lstat(candidate: Path):
                metadata = real_lstat(candidate)
                if candidate != foreign:
                    return metadata
                return type(
                    "ForeignOwnedOuterDirectoryStat",
                    (),
                    {
                        "st_mode": metadata.st_mode,
                        "st_uid": metadata.st_uid + 1,
                        "st_gid": metadata.st_gid,
                    },
                )()

            with patch.object(Path, "lstat", foreign_owned_lstat):
                with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                    prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertIn(
                "foreign-directory uid=",
                raised.exception.details["nonportable_worktree_ownership"][0],
            )

    def test_outer_snapshot_rejects_nonportable_tracked_file_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            foreign = repo / "foreign-owned.txt"
            foreign.write_text("owned elsewhere\n", encoding="utf-8")
            git(repo, "add", foreign.name)
            git(repo, "commit", "-qm", "add foreign-owned input")
            real_lstat = Path.lstat

            def foreign_owned_lstat(candidate: Path):
                metadata = real_lstat(candidate)
                if candidate != foreign:
                    return metadata
                return type(
                    "ForeignOwnedOuterFileStat",
                    (),
                    {
                        "st_mode": metadata.st_mode,
                        "st_uid": metadata.st_uid + 1,
                        "st_gid": metadata.st_gid,
                    },
                )()

            with patch.object(Path, "lstat", foreign_owned_lstat):
                with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                    prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertIn(
                "foreign-owned.txt uid=",
                raised.exception.details["nonportable_worktree_ownership"][0],
            )

    def test_outer_snapshot_includes_only_ignored_nested_checkout_roots(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            (repo / ".gitignore").write_text(
                ".deps/\n.validator/\nordinary.cache\n",
                encoding="utf-8",
            )
            git(repo, "add", ".gitignore")
            git(repo, "commit", "-qm", "ignore validation checkout")
            (repo / "ordinary.cache").write_text("excluded\n", encoding="utf-8")
            provider = repo / ".deps" / "provider"
            provider.mkdir(parents=True)
            git(provider, "init", "-q")
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "needed").write_text("first\n", encoding="utf-8")
            git(nested, "add", "needed")
            git(nested, "commit", "-qm", "nested base")

            first = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), first.head)
            prepare_landing.materialize_candidate(repo, isolated, first)
            (nested / "needed").write_text("second\n", encoding="utf-8")
            second = prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual((".validator/",), first.untracked_paths)
            self.assertTrue((isolated / ".validator" / "needed").is_file())
            self.assertFalse((isolated / ".deps").exists())
            self.assertFalse((isolated / "ordinary.cache").exists())
            self.assertNotEqual(first.identity(), second.identity())

    def test_outer_snapshot_preserves_ignored_nested_checkout_ancestors(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            (repo / ".gitignore").write_text(".cache/\n", encoding="utf-8")
            git(repo, "add", ".gitignore")
            git(repo, "commit", "-qm", "ignore nested validation cache")
            cache = repo / ".cache"
            vendor = cache / "vendor"
            nested = vendor / "repo"
            nested.mkdir(parents=True)
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "needed").write_text("first\n", encoding="utf-8")
            git(nested, "add", "needed")
            git(nested, "commit", "-qm", "nested base")
            cache.chmod(0o700)
            vendor.chmod(0o711)
            cache_mtime_ns = 946_684_800_123_456_789
            vendor_mtime_ns = 978_307_200_987_654_321
            os.utime(cache, ns=(cache_mtime_ns, cache_mtime_ns))
            os.utime(vendor, ns=(vendor_mtime_ns, vendor_mtime_ns))

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            self.assertIn(
                (".cache", cache.lstat().st_atime_ns, cache_mtime_ns),
                snapshot.worktree_times,
            )
            self.assertIn(
                (".cache/vendor", vendor.lstat().st_atime_ns, vendor_mtime_ns),
                snapshot.worktree_times,
            )
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)

            self.assertEqual(
                (".cache", ".cache/vendor", "generated"),
                snapshot.directories,
            )
            isolated_cache = isolated / ".cache"
            isolated_vendor = isolated_cache / "vendor"
            self.assertEqual(0o700, stat.S_IMODE(isolated_cache.stat().st_mode))
            self.assertEqual(0o711, stat.S_IMODE(isolated_vendor.stat().st_mode))
            self.assertEqual(cache_mtime_ns, isolated_cache.stat().st_mtime_ns)
            self.assertEqual(vendor_mtime_ns, isolated_vendor.stat().st_mtime_ns)

    def test_nested_materialization_preserves_ignored_empty_directories(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / ".gitignore").write_text("ignored-cache/\n", encoding="utf-8")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            (nested / "expected-empty").mkdir()
            (nested / "ignored-cache").mkdir()

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            materialized_tree = prepare_landing.materialize_candidate(
                repo,
                isolated,
                snapshot,
            )

            self.assertEqual(snapshot.index_tree, materialized_tree)
            self.assertTrue((isolated / ".validator" / "expected-empty").is_dir())
            self.assertTrue((isolated / ".validator" / "ignored-cache").is_dir())

    def test_nested_materialization_preserves_root_and_restrictive_parent_modes(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            parent = nested / "readonly-parent"
            (parent / "empty-child").mkdir(parents=True)
            parent.chmod(0o555)
            nested.chmod(0o555)

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            materialized_tree = prepare_landing.materialize_candidate(
                repo,
                isolated,
                snapshot,
            )

            isolated_nested = isolated / ".validator"
            self.assertEqual(snapshot.index_tree, materialized_tree)
            self.assertTrue((isolated_nested / "readonly-parent" / "empty-child").is_dir())
            self.assertEqual(0o555, stat.S_IMODE(isolated_nested.stat().st_mode))
            self.assertEqual(
                0o555,
                stat.S_IMODE((isolated_nested / "readonly-parent").stat().st_mode),
            )

    def test_nested_materialization_preserves_tracked_parent_directory_mode(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            secret = nested / "secret"
            secret.mkdir()
            (secret / "test.txt").write_text("base\n", encoding="utf-8")
            (nested / ".gitignore").write_text("secret/\n", encoding="utf-8")
            git(nested, "add", ".gitignore")
            git(nested, "add", "-f", "secret/test.txt")
            git(nested, "commit", "-qm", "nested base")
            secret.chmod(0o700)

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            materialized_tree = prepare_landing.materialize_candidate(
                repo,
                isolated,
                snapshot,
            )

            self.assertEqual(snapshot.index_tree, materialized_tree)
            self.assertEqual(
                0o700,
                stat.S_IMODE((isolated / ".validator" / "secret").stat().st_mode),
            )

    def test_nested_materialization_preserves_tracked_file_mode(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            tracked = nested / "validator.txt"
            tracked.write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            tracked.chmod(0o600)

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            materialized_tree = prepare_landing.materialize_candidate(repo, isolated, snapshot)

            self.assertEqual(snapshot.index_tree, materialized_tree)
            self.assertEqual(
                0o600,
                stat.S_IMODE((isolated / ".validator" / "validator.txt").stat().st_mode),
            )

    def test_nested_materialization_preserves_staged_and_unstaged_split(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            tracked = nested / "validator.txt"
            tracked.write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            tracked.write_text("staged\n", encoding="utf-8")
            git(nested, "add", "validator.txt")
            tracked.write_text("unstaged\n", encoding="utf-8")
            (nested / "untracked.txt").write_text("untracked\n", encoding="utf-8")

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            materialized_tree = prepare_landing.materialize_candidate(
                repo,
                isolated,
                snapshot,
            )
            isolated_nested = isolated / ".validator"

            self.assertEqual(snapshot.index_tree, materialized_tree)
            self.assertEqual(b"staged\n", git(isolated_nested, "show", ":validator.txt"))
            self.assertEqual("unstaged\n", (isolated_nested / "validator.txt").read_text())
            self.assertEqual(
                b"validator.txt\n",
                git(isolated_nested, "diff", "--cached", "--name-only"),
            )
            self.assertEqual(
                b"validator.txt\n",
                git(isolated_nested, "diff", "--name-only"),
            )
            self.assertIn(b"?? untracked.txt\n", git(isolated_nested, "status", "--short"))

    def test_snapshot_hashes_nested_untracked_checkout_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("clean\n", encoding="utf-8")
            (nested / ".gitignore").write_text("ignored.cache\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            (nested / "ignored.cache").write_text("not candidate state\n", encoding="utf-8")

            first = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), first.head)
            materialized_tree = prepare_landing.materialize_candidate(
                repo,
                isolated,
                first,
            )
            (nested / "ignored.cache").write_text("changed ignored state\n", encoding="utf-8")
            second = prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual((".validator/",), first.untracked_paths)
            self.assertEqual(first.index_tree, materialized_tree)
            self.assertEqual(b"", git(isolated, "ls-files", "--stage", "--", ".validator"))
            self.assertTrue((isolated / ".validator" / "validator.txt").is_file())
            self.assertEqual(
                "not candidate state\n",
                (isolated / ".validator" / "ignored.cache").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                git(nested, "symbolic-ref", "--quiet", "HEAD"),
                git(isolated / ".validator", "symbolic-ref", "--quiet", "HEAD"),
            )
            self.assertEqual(
                prepare_landing._git_ref_state(nested),
                prepare_landing._git_ref_state(isolated / ".validator"),
            )
            self.assertEqual(
                prepare_landing._portable_local_config(nested),
                prepare_landing._portable_local_config(isolated / ".validator"),
            )
            self.assertEqual(
                prepare_landing._reflog_state(nested),
                prepare_landing._reflog_state(isolated / ".validator"),
            )
            self.assertNotEqual(first.identity(), second.identity())

    def test_nested_snapshot_binds_physical_object_storage(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            for index in range(8):
                (nested / f"object-{index}.txt").write_text(
                    f"object {index}\n",
                    encoding="utf-8",
                )
                git(nested, "add", ".")
                git(nested, "commit", "-qm", f"nested object {index}")

            snapshot = prepare_landing._nested_git_snapshot(nested)
            self.assertIsNotNone(snapshot)
            logical_before = (
                snapshot.object_inventory_count,
                snapshot.object_inventory_digest,
            )
            git(nested, "repack", "-ad")
            repacked = prepare_landing._nested_git_snapshot(nested)
            self.assertIsNotNone(repacked)

            self.assertEqual(
                logical_before,
                (repacked.object_inventory_count, repacked.object_inventory_digest),
            )
            self.assertNotEqual(
                snapshot.object_storage_state,
                repacked.object_storage_state,
            )
            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.require_nested_git_snapshot_unchanged(nested, snapshot)
            self.assertEqual("candidate_snapshot_changed", raised.exception.failure_type)

    def test_nested_snapshot_preserves_object_storage_mtimes(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            objects = nested / ".git" / "objects"
            tree_oid = git(nested, "write-tree").decode("ascii").strip()
            loose_object = objects / tree_oid[:2] / tree_oid[2:]
            self.assertTrue(loose_object.is_file())
            relative_object = loose_object.relative_to(objects)
            source_file_mtime_ns = 946_684_800_123_456_789
            source_dir_mtime_ns = 946_684_801_987_654_321
            os.utime(
                loose_object,
                ns=(source_file_mtime_ns, source_file_mtime_ns),
            )
            os.utime(
                loose_object.parent,
                ns=(source_dir_mtime_ns, source_dir_mtime_ns),
            )
            nested_snapshot = prepare_landing._nested_git_snapshot(nested)
            self.assertIsNotNone(nested_snapshot)
            self.assertEqual(source_file_mtime_ns, loose_object.stat().st_mtime_ns)
            self.assertEqual(source_dir_mtime_ns, loose_object.parent.stat().st_mtime_ns)

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)

            isolated_object = isolated / ".validator" / ".git" / "objects" / relative_object
            self.assertEqual(source_file_mtime_ns, isolated_object.stat().st_mtime_ns)
            self.assertEqual(source_dir_mtime_ns, isolated_object.parent.stat().st_mtime_ns)
            os.utime(
                loose_object,
                ns=(
                    source_file_mtime_ns + 1_000_000_000,
                    source_file_mtime_ns + 1_000_000_000,
                ),
            )
            changed = prepare_landing._nested_git_snapshot(nested)
            self.assertIsNotNone(changed)
            assert nested_snapshot is not None
            assert changed is not None
            self.assertNotEqual(nested_snapshot.identity(), changed.identity())
            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.require_nested_git_snapshot_unchanged(
                    nested,
                    nested_snapshot,
                )
            self.assertEqual("candidate_snapshot_changed", raised.exception.failure_type)

    def test_snapshot_preserves_nested_origin_default_ref(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("main\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested main")
            git(nested, "branch", "-M", "main")
            main_commit = git(nested, "rev-parse", "HEAD").decode().strip()
            git(nested, "checkout", "-qb", "feature")
            (nested / "validator.txt").write_text("feature\n", encoding="utf-8")
            git(nested, "commit", "-qam", "nested feature")
            git(nested, "update-ref", "refs/remotes/origin/main", main_commit)
            git(
                nested,
                "symbolic-ref",
                "refs/remotes/origin/HEAD",
                "refs/remotes/origin/main",
            )
            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)
            isolated_nested = isolated / ".validator"

            self.assertEqual(
                b"refs/heads/feature\n",
                git(isolated_nested, "symbolic-ref", "--quiet", "HEAD"),
            )
            self.assertEqual(
                prepare_landing._git_ref_state(nested),
                prepare_landing._git_ref_state(isolated_nested),
            )
            self.assertEqual(
                prepare_landing._portable_local_config(nested),
                prepare_landing._portable_local_config(isolated_nested),
            )
            self.assertEqual(
                main_commit,
                git(isolated_nested, "rev-parse", "refs/remotes/origin/HEAD")
                .decode()
                .strip(),
            )

    def test_nested_materialization_preserves_packed_ref_storage(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("main\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested main")
            git(nested, "branch", "packed-only")
            git(nested, "branch", "loose-only")
            git(nested, "tag", "-a", "packed-tag", "-m", "packed tag")
            before_packing = prepare_landing._nested_git_snapshot(nested)
            self.assertIsNotNone(before_packing)
            loose_commit = (
                git(nested, "rev-parse", "refs/heads/loose-only").decode().strip()
            )
            git(nested, "pack-refs", "--all", "--prune")
            loose_ref = Path(
                git(nested, "rev-parse", "--git-path", "refs/heads/loose-only")
                .decode()
                .strip()
            )
            if not loose_ref.is_absolute():
                loose_ref = nested / loose_ref
            loose_ref.parent.mkdir(parents=True, exist_ok=True)
            loose_ref.write_text(f"{loose_commit}\n", encoding="ascii")
            source_storage = prepare_landing._git_ref_storage_state(nested)
            self.assertIsNotNone(source_storage[3])
            self.assertIsNotNone(source_storage[4])
            self.assertTrue(
                any(
                    path == "heads/loose-only"
                    for path, _mode, _content in source_storage[2]
                )
            )

            after_packing = prepare_landing._nested_git_snapshot(nested)
            self.assertIsNotNone(after_packing)
            assert before_packing is not None
            assert after_packing is not None
            self.assertEqual(before_packing.git_refs, after_packing.git_refs)
            self.assertNotEqual(before_packing.identity(), after_packing.identity())
            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)
            isolated_nested = isolated / ".validator"

            self.assertEqual(
                prepare_landing._git_ref_state(nested),
                prepare_landing._git_ref_state(isolated_nested),
            )
            self.assertEqual(
                source_storage,
                prepare_landing._git_ref_storage_state(isolated_nested),
            )

    def test_materialization_neutralizes_nested_remote_transport(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            git(nested, "branch", "-M", "main")
            remote = Path(work_tmp) / "remote"
            remote.mkdir()
            git(remote, "init", "-q")
            git(remote, "config", "user.email", "test@example.invalid")
            git(remote, "config", "user.name", "Remote Test")
            (remote / "remote.txt").write_text("base\n", encoding="utf-8")
            git(remote, "add", ".")
            git(remote, "commit", "-qm", "remote base")
            git(remote, "branch", "-M", "main")
            git(nested, "config", "remote.origin.url", remote.as_posix())
            git(
                nested,
                "config",
                "remote.origin.fetch",
                "+refs/heads/main:refs/remotes/origin/main",
            )

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            (remote / "remote.txt").write_text("after snapshot\n", encoding="utf-8")
            git(remote, "commit", "-qam", "remote after snapshot")
            external_commit = git(remote, "rev-parse", "HEAD").decode().strip()
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)
            isolated_nested = isolated / ".validator"
            git(isolated_nested, "fetch", "origin")

            self.assertEqual(
                b".\n",
                git(isolated_nested, "config", "--local", "remote.origin.url"),
            )
            self.assertNotEqual(
                0,
                subprocess.run(
                    ("git", "cat-file", "-e", f"{external_commit}^{{commit}}"),
                    cwd=isolated_nested,
                    check=False,
                    capture_output=True,
                ).returncode,
            )

    def test_nested_snapshot_preserves_raw_local_config(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            config = nested / ".git" / "config"
            config.write_bytes(
                config.read_bytes() + b"\n# validator-visible raw config comment\n"
            )
            raw_config = config.read_bytes()
            source_mtime_ns = 946_684_800_123_456_789
            os.utime(config, ns=(source_mtime_ns, source_mtime_ns))
            nested_snapshot = prepare_landing._nested_git_snapshot(nested)
            self.assertIsNotNone(nested_snapshot)
            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)

            isolated_config = (isolated / ".validator" / ".git" / "config").read_bytes()
            assert nested_snapshot is not None
            self.assertEqual(source_mtime_ns, nested_snapshot.local_config_mtime_ns)
            self.assertEqual(raw_config, nested_snapshot.local_config_bytes)
            self.assertEqual(nested_snapshot.isolated_config_bytes, isolated_config)
            self.assertEqual(
                source_mtime_ns,
                (isolated / ".validator" / ".git" / "config").stat().st_mtime_ns,
            )
            self.assertIn(b"# validator-visible raw config comment\n", isolated_config)
            os.utime(
                config,
                ns=(
                    source_mtime_ns + 1_000_000_000,
                    source_mtime_ns + 1_000_000_000,
                ),
            )
            changed = prepare_landing._nested_git_snapshot(nested)
            self.assertIsNotNone(changed)
            assert changed is not None
            self.assertNotEqual(nested_snapshot.identity(), changed.identity())
            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.require_nested_git_snapshot_unchanged(
                    nested,
                    nested_snapshot,
                )
            self.assertEqual("candidate_snapshot_changed", raised.exception.failure_type)

    def test_nested_snapshot_rejects_hardlinked_local_config(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as peer_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", "validator.txt")
            git(nested, "commit", "-qm", "nested base")
            config = nested / ".git" / "config"
            peer = Path(peer_tmp) / "config-peer"
            os.link(config, peer)

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(2, raised.exception.details["link_count"])

    def test_nested_snapshot_preserves_remaining_git_admin_files(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            description = nested / ".git" / "description"
            description.write_bytes(b"validator-visible description\n")
            description.chmod(0o640)
            source_mtime_ns = 946_684_800_123_456_789
            os.utime(
                description,
                ns=(source_mtime_ns, source_mtime_ns),
            )
            source_state = prepare_landing._git_admin_state(nested)
            nested_snapshot = prepare_landing._nested_git_snapshot(nested)
            self.assertIsNotNone(nested_snapshot)

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)
            isolated_nested = isolated / ".validator"

            self.assertEqual(
                source_state,
                prepare_landing._git_admin_state(isolated_nested),
            )
            isolated_description = isolated_nested / ".git" / "description"
            self.assertEqual(
                b"validator-visible description\n",
                isolated_description.read_bytes(),
            )
            self.assertEqual(
                0o640,
                stat.S_IMODE(isolated_description.stat().st_mode),
            )
            self.assertEqual(source_mtime_ns, isolated_description.stat().st_mtime_ns)
            os.utime(
                description,
                ns=(source_mtime_ns + 1_000_000_000, source_mtime_ns + 1_000_000_000),
            )
            changed = prepare_landing._nested_git_snapshot(nested)
            self.assertIsNotNone(changed)
            assert nested_snapshot is not None
            assert changed is not None
            self.assertNotEqual(nested_snapshot.identity(), changed.identity())
            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.require_nested_git_snapshot_unchanged(
                    nested,
                    nested_snapshot,
                )
            self.assertEqual("candidate_snapshot_changed", raised.exception.failure_type)

    def test_nested_snapshot_preserves_git_admin_directory_mtimes(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            info = nested / ".git" / "info"
            source_mtime_ns = 946_684_800_123_456_789
            os.utime(info, ns=(source_mtime_ns, source_mtime_ns))
            source_git_mtime_ns = (nested / ".git").stat().st_mtime_ns
            nested_snapshot = prepare_landing._nested_git_snapshot(nested)
            self.assertIsNotNone(nested_snapshot)
            self.assertEqual(source_git_mtime_ns, (nested / ".git").stat().st_mtime_ns)

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)

            isolated_info = isolated / ".validator" / ".git" / "info"
            self.assertEqual(source_mtime_ns, isolated_info.stat().st_mtime_ns)
            self.assertEqual(
                source_git_mtime_ns,
                (isolated / ".validator" / ".git").stat().st_mtime_ns,
            )
            os.utime(
                info,
                ns=(source_mtime_ns + 1_000_000_000, source_mtime_ns + 1_000_000_000),
            )
            changed = prepare_landing._nested_git_snapshot(nested)
            self.assertIsNotNone(changed)
            assert nested_snapshot is not None
            assert changed is not None
            self.assertNotEqual(nested_snapshot.identity(), changed.identity())
            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.require_nested_git_snapshot_unchanged(
                    nested,
                    nested_snapshot,
                )
            self.assertEqual("candidate_snapshot_changed", raised.exception.failure_type)

    def test_snapshot_rejects_effective_url_rewrites(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            root = Path(repo_tmp)
            repo = self.make_repo(root)
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            git(nested, "config", "remote.origin.url", ".")
            global_config = root / "global.gitconfig"
            global_config.write_text(
                '[url "file:///mutable-external/"]\n\tinsteadOf = .\n',
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {
                    "GIT_CONFIG_GLOBAL": global_config.as_posix(),
                    "GIT_CONFIG_NOSYSTEM": "1",
                },
            ), self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual(
                [["global", "url.file:///mutable-external/.insteadof"]],
                raised.exception.details["url_rewrite_settings"],
            )

    def test_nested_materialization_preserves_reflogs(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            tracked = nested / "validator.txt"
            tracked.write_text("first\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested first")
            tracked.write_text("second\n", encoding="utf-8")
            git(nested, "commit", "-qam", "nested second")

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)

            self.assertEqual(
                prepare_landing._reflog_state(nested),
                prepare_landing._reflog_state(isolated / ".validator"),
            )

    def test_nested_materialization_defers_restrictive_reflog_modes(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            source_refs = prepare_landing._reflog_root(nested) / "refs"
            source_refs.chmod(0o555)
            isolated_refs: Path | None = None
            try:
                snapshot = prepare_landing.capture_candidate_snapshot(repo)
                isolated = Path(work_tmp) / "isolated"
                git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
                prepare_landing.materialize_candidate(repo, isolated, snapshot)
                isolated_nested = isolated / ".validator"
                isolated_refs = prepare_landing._reflog_root(isolated_nested) / "refs"

                self.assertEqual(
                    prepare_landing._reflog_state(nested),
                    prepare_landing._reflog_state(isolated_nested),
                )
                self.assertEqual(0o555, stat.S_IMODE(isolated_refs.lstat().st_mode))
            finally:
                source_refs.chmod(0o755)
                if isolated_refs is not None and isolated_refs.exists():
                    isolated_refs.chmod(0o755)

    def test_snapshot_rejects_restrictive_git_admin_directory_modes(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            refs_heads = Path(
                git(nested, "rev-parse", "--git-path", "refs/heads")
                .decode()
                .strip()
            )
            if not refs_heads.is_absolute():
                refs_heads = nested / refs_heads
            refs_heads.chmod(0o555)
            try:
                with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                    prepare_landing.capture_candidate_snapshot(repo)
            finally:
                refs_heads.chmod(0o755)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertIn(
                "refs/heads mode=0555",
                raised.exception.details["restrictive_git_admin_directory_modes"],
            )

    def test_snapshot_rejects_restrictive_git_admin_file_modes(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            config_path = Path(
                git(nested, "rev-parse", "--git-path", "config").decode().strip()
            )
            if not config_path.is_absolute():
                config_path = nested / config_path
            config_path.chmod(0o444)
            try:
                with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                    prepare_landing.capture_candidate_snapshot(repo)
            finally:
                config_path.chmod(0o644)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                ["config mode=0444"],
                raised.exception.details["restrictive_git_admin_file_modes"],
            )

    def test_snapshot_rejects_nested_git_administration_lock(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            config_path = Path(
                git(nested, "rev-parse", "--git-path", "config").decode().strip()
            )
            if not config_path.is_absolute():
                config_path = nested / config_path
            lock = config_path.with_name(config_path.name + ".lock")
            lock.write_text("active\n", encoding="utf-8")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                ["config.lock"],
                raised.exception.details["git_admin_lock_paths"],
            )

    def test_snapshot_rejects_sparse_tracked_and_ignored_files(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / ".gitignore").write_text("ignored.sparse\n", encoding="utf-8")
            tracked = nested / "tracked.sparse"
            with tracked.open("wb") as handle:
                handle.seek(8 * 1024 * 1024 - 1)
                handle.write(b"\0")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested sparse base")
            ignored = nested / "ignored.sparse"
            with ignored.open("wb") as handle:
                handle.seek(4 * 1024 * 1024 - 1)
                handle.write(b"\0")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                ["ignored.sparse", "tracked.sparse"],
                raised.exception.details["sparse_worktree_paths"],
            )

    def test_snapshot_rejects_sparse_git_object_storage(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested sparse object base")
            tree_oid = git(nested, "write-tree").decode("ascii").strip()
            loose_object = nested / ".git" / "objects" / tree_oid[:2] / tree_oid[2:]
            source_mode = stat.S_IMODE(loose_object.stat().st_mode)
            loose_object.chmod(source_mode | stat.S_IWUSR)
            with loose_object.open("r+b") as handle:
                handle.seek(8 * 1024 * 1024, os.SEEK_END)
                handle.write(b"\0")
            loose_object.chmod(source_mode)

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                [f"objects/{tree_oid[:2]}/{tree_oid[2:]}"],
                raised.exception.details["sparse_git_admin_paths"],
            )

    def test_snapshot_rejects_sparse_residual_git_admin_file(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested sparse admin base")
            description = nested / ".git" / "description"
            with description.open("wb") as handle:
                handle.write(b"validator\n")
                handle.seek(8 * 1024 * 1024 - 1)
                handle.write(b"\0")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                ["description"],
                raised.exception.details["sparse_git_admin_paths"],
            )

    def test_restore_git_admin_security_label_applies_uniform_label(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested security label base")
            security_label = b"system_u:object_r:git_content_t:s0"
            git_dir = nested / ".git"

            with patch.object(
                prepare_landing.os,
                "setxattr",
            ) as setxattr:
                prepare_landing._restore_git_admin_security_label(
                    nested,
                    security_label,
                )

            expected_paths = (git_dir, *git_dir.rglob("*"))
            self.assertEqual(len(expected_paths), setxattr.call_count)
            setxattr.assert_any_call(
                git_dir.resolve(),
                "security.selinux",
                security_label,
                follow_symlinks=False,
            )

    def test_restore_missing_git_admin_security_label_avoids_removal(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")

            with patch.object(
                prepare_landing.os,
                "listxattr",
                return_value=[],
            ), patch.object(
                prepare_landing.os,
                "removexattr",
            ) as removexattr:
                prepare_landing._restore_git_admin_security_label(nested, None)

            removexattr.assert_not_called()

    def test_snapshot_rejects_nested_rerere_cache_state(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            rr_cache = Path(
                git(nested, "rev-parse", "--git-path", "rr-cache").decode().strip()
            )
            if not rr_cache.is_absolute():
                rr_cache = nested / rr_cache
            resolution = rr_cache / ("a" * 40)
            resolution.mkdir(parents=True)
            (resolution / "preimage").write_text("conflict\n", encoding="utf-8")
            (resolution / "postimage").write_text("resolved\n", encoding="utf-8")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                [".", f"{'a' * 40}", f"{'a' * 40}/postimage", f"{'a' * 40}/preimage"],
                raised.exception.details["rerere_cache_state"],
            )

    def test_snapshot_rejects_nonportable_git_admin_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            refs_heads = Path(
                git(nested, "rev-parse", "--git-path", "refs/heads")
                .decode()
                .strip()
            )
            if not refs_heads.is_absolute():
                refs_heads = nested / refs_heads
            real_lstat = Path.lstat

            def foreign_owned_lstat(candidate: Path):
                metadata = real_lstat(candidate)
                if candidate != refs_heads:
                    return metadata
                return type(
                    "ForeignOwnedGitAdminStat",
                    (),
                    {
                        "st_mode": metadata.st_mode,
                        "st_uid": metadata.st_uid + 1,
                        "st_gid": metadata.st_gid,
                    },
                )()

            with patch.object(Path, "lstat", foreign_owned_lstat):
                with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                    prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertIn(
                "refs/heads uid=",
                raised.exception.details["git_admin_ownership"][0],
            )

    def test_snapshot_rejects_git_admin_extended_attributes(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            config_path = Path(
                git(nested, "rev-parse", "--git-path", "config").decode().strip()
            )
            if not config_path.is_absolute():
                config_path = nested / config_path
            try:
                os.setxattr(
                    config_path,
                    "user.aoa-kag-admin-test",
                    b"bound admin metadata",
                    follow_symlinks=False,
                )
            except OSError as exc:
                self.skipTest(f"extended attributes unavailable: {exc}")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                ["config attribute=user.aoa-kag-admin-test"],
                raised.exception.details["git_admin_xattrs"],
            )

    def test_nested_materialization_preserves_worktree_hardlinks(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            first = nested / "first.txt"
            second = nested / "second.txt"
            candidate = nested / "candidate.txt"
            first.write_text("shared\n", encoding="utf-8")
            os.link(first, second)
            git(nested, "add", "first.txt", "second.txt")
            git(nested, "commit", "-qm", "nested hardlinks")
            os.link(first, candidate)

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)
            isolated_nested = isolated / ".validator"
            inodes = {
                (isolated_nested / name).lstat().st_ino
                for name in ("candidate.txt", "first.txt", "second.txt")
            }

            self.assertEqual(1, len(inodes))
            (isolated_nested / "first.txt").write_text("changed\n", encoding="utf-8")
            self.assertEqual(
                "changed\n",
                (isolated_nested / "second.txt").read_text(encoding="utf-8"),
            )

    def test_nested_hardlinks_are_rebuilt_before_readonly_directory_modes(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            readonly = nested / "readonly"
            readonly.mkdir()
            first = readonly / "first.txt"
            second = readonly / "second.txt"
            candidate = readonly / "candidate.txt"
            first.write_text("shared\n", encoding="utf-8")
            os.link(first, second)
            git(nested, "add", "readonly/first.txt", "readonly/second.txt")
            git(nested, "commit", "-qm", "nested readonly hardlinks")
            os.link(first, candidate)
            readonly.chmod(0o555)

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)
            isolated_readonly = isolated / ".validator" / "readonly"
            inodes = {
                (isolated_readonly / name).lstat().st_ino
                for name in ("candidate.txt", "first.txt", "second.txt")
            }

            self.assertEqual(1, len(inodes))
            self.assertEqual(0o555, stat.S_IMODE(isolated_readonly.stat().st_mode))

    def test_snapshot_rejects_worktree_hardlinks_outside_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            outside = repo / "outside.txt"
            outside.write_text("shared\n", encoding="utf-8")
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            os.link(outside, nested / "validator.txt")
            git(nested, "add", "validator.txt")
            git(nested, "commit", "-qm", "nested external hardlink")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                ["validator.txt"],
                raised.exception.details["external_hardlink_paths"],
            )

    def test_snapshot_rejects_nonportable_nested_worktree_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            tracked = nested / "validator.txt"
            tracked.write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            real_lstat = Path.lstat

            def foreign_owned_lstat(candidate: Path):
                metadata = real_lstat(candidate)
                if candidate != tracked:
                    return metadata
                return type(
                    "ForeignOwnedStat",
                    (),
                    {
                        "st_mode": metadata.st_mode,
                        "st_uid": metadata.st_uid + 1,
                        "st_gid": metadata.st_gid,
                        "st_dev": metadata.st_dev,
                        "st_ino": metadata.st_ino,
                        "st_nlink": metadata.st_nlink,
                    },
                )()

            with patch.object(Path, "lstat", foreign_owned_lstat):
                with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                    prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertIn(
                "validator.txt uid=",
                raised.exception.details["nonportable_worktree_ownership"][0],
            )

    def test_nested_materialization_preserves_extended_attributes(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            tracked = nested / "validator.txt"
            tracked.write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            try:
                os.setxattr(
                    tracked,
                    "user.aoa-kag-test",
                    b"bound metadata",
                    follow_symlinks=False,
                )
            except OSError as exc:
                self.skipTest(f"extended attributes unavailable: {exc}")

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)
            isolated_tracked = isolated / ".validator" / "validator.txt"

            self.assertEqual(
                b"bound metadata",
                os.getxattr(
                    isolated_tracked,
                    "user.aoa-kag-test",
                    follow_symlinks=False,
                ),
            )

    def test_nested_xattrs_are_restored_before_readonly_modes(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            readonly = nested / "readonly"
            readonly.mkdir()
            tracked = readonly / "validator.txt"
            tracked.write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            try:
                os.setxattr(
                    tracked,
                    "user.aoa-kag-file",
                    b"readonly file metadata",
                    follow_symlinks=False,
                )
                os.setxattr(
                    readonly,
                    "user.aoa-kag-directory",
                    b"readonly directory metadata",
                    follow_symlinks=False,
                )
            except OSError as exc:
                self.skipTest(f"extended attributes unavailable: {exc}")
            tracked.chmod(0o444)
            readonly.chmod(0o555)
            isolated_readonly = Path(work_tmp) / "isolated" / ".validator" / "readonly"
            try:
                snapshot = prepare_landing.capture_candidate_snapshot(repo)
                isolated = Path(work_tmp) / "isolated"
                git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
                prepare_landing.materialize_candidate(repo, isolated, snapshot)
                isolated_tracked = isolated_readonly / "validator.txt"

                self.assertEqual(0o444, stat.S_IMODE(isolated_tracked.stat().st_mode))
                self.assertEqual(0o555, stat.S_IMODE(isolated_readonly.stat().st_mode))
                self.assertEqual(
                    b"readonly file metadata",
                    os.getxattr(
                        isolated_tracked,
                        "user.aoa-kag-file",
                        follow_symlinks=False,
                    ),
                )
                self.assertEqual(
                    b"readonly directory metadata",
                    os.getxattr(
                        isolated_readonly,
                        "user.aoa-kag-directory",
                        follow_symlinks=False,
                    ),
                )
            finally:
                tracked.chmod(0o644)
                readonly.chmod(0o755)
                if isolated_readonly.exists():
                    (isolated_readonly / "validator.txt").chmod(0o644)
                    isolated_readonly.chmod(0o755)

    def test_nested_materialization_preserves_access_and_modification_times(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            tracked = nested / "validator.txt"
            tracked.write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            historical_atime_ns = 915148800_000_000_000
            historical_mtime_ns = 946684800_000_000_000
            os.utime(
                tracked,
                ns=(historical_atime_ns, historical_mtime_ns),
            )
            os.utime(
                nested,
                ns=(historical_atime_ns, historical_mtime_ns),
            )

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            expected_nested_atime_ns = nested.lstat().st_atime_ns
            expected_tracked_atime_ns = tracked.lstat().st_atime_ns
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)
            isolated_nested = isolated / ".validator"

            self.assertEqual(
                expected_nested_atime_ns,
                isolated_nested.lstat().st_atime_ns,
            )
            self.assertEqual(
                expected_tracked_atime_ns,
                (isolated_nested / "validator.txt").lstat().st_atime_ns,
            )
            self.assertEqual(
                historical_mtime_ns,
                isolated_nested.lstat().st_mtime_ns,
            )
            self.assertEqual(
                historical_mtime_ns,
                (isolated_nested / "validator.txt").lstat().st_mtime_ns,
            )

    def test_nested_materialization_preserves_intent_to_add(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            (nested / "new.txt").write_text("candidate\n", encoding="utf-8")
            git(nested, "add", "--intent-to-add", "new.txt")

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)
            isolated_nested = isolated / ".validator"

            self.assertEqual(
                git(nested, "status", "--short"),
                git(isolated_nested, "status", "--short"),
            )
            self.assertEqual(
                git(nested, "diff", "--cached", "--name-only", "--ita-visible-in-index"),
                git(
                    isolated_nested,
                    "diff",
                    "--cached",
                    "--name-only",
                    "--ita-visible-in-index",
                ),
            )

    def test_snapshot_rejects_nested_checkout_root_with_outer_tracked_content(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / "validator"
            nested.mkdir()
            script = nested / "script.py"
            script.write_text("print('outer')\n", encoding="utf-8")
            git(repo, "add", "validator/script.py")
            git(repo, "commit", "-qm", "track validator from outer repository")
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            git(nested, "add", "script.py")
            git(nested, "commit", "-qm", "track validator from nested repository")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                ["validator"],
                raised.exception.details["nested_tracked_roots"],
            )

    def test_snapshot_rejects_tracked_file_replaced_by_nested_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / "validator"
            nested.write_text("tracked owner file\n", encoding="utf-8")
            git(repo, "add", "validator")
            git(repo, "commit", "-qm", "track validator file")
            nested.unlink()
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "script.py").write_text("print('nested')\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested validator")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                ["validator"],
                raised.exception.details["nested_tracked_roots"],
            )

    def test_snapshot_rejects_initialized_submodule_in_nested_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            temp_root = Path(repo_tmp)
            provider_root = temp_root / "provider-root"
            provider_root.mkdir()
            provider = self.make_repo(provider_root)
            owner_root = temp_root / "owner-root"
            owner_root.mkdir()
            owner = self.make_repo(owner_root)
            nested = owner / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            git(
                nested,
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                "-q",
                provider.as_posix(),
                "modules/provider",
            )
            git(nested, "commit", "-qam", "add initialized provider")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(owner)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertTrue(raised.exception.details["populated_submodules"])

            git(nested, "submodule", "deinit", "-f", "--", "modules/provider")
            residual = nested / "modules" / "provider" / "residual.txt"
            residual.parent.mkdir(parents=True, exist_ok=True)
            residual.write_text("residual\n", encoding="utf-8")
            with self.assertRaises(prepare_landing.PreparationFailure) as residual_raised:
                prepare_landing.capture_candidate_snapshot(owner)
            self.assertTrue(residual_raised.exception.details["populated_submodules"])

    def test_snapshot_rejects_uninitialized_submodule_transport(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            dependency_commit = git(nested, "rev-parse", "HEAD").decode().strip()
            (nested / ".gitmodules").write_text(
                '[submodule "dependency"]\n'
                "\tpath = dependency\n"
                "\turl = https://example.invalid/dependency.git\n",
                encoding="utf-8",
            )
            git(nested, "add", ".gitmodules")
            git(
                nested,
                "update-index",
                "--add",
                "--cacheinfo",
                f"160000,{dependency_commit},dependency",
            )
            git(nested, "commit", "-qm", "add uninitialized dependency")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                [
                    "candidate:.gitmodules",
                    "index:.gitmodules",
                    "HEAD:.gitmodules",
                ],
                raised.exception.details["submodule_transport_sources"],
            )

    def test_snapshot_rejects_effective_ambient_submodule_transport(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            root = Path(repo_tmp)
            repo = self.make_repo(root)
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            dependency_commit = git(nested, "rev-parse", "HEAD").decode().strip()
            (nested / ".gitmodules").write_text(
                '[submodule "dependency"]\n\tpath = dependency\n',
                encoding="utf-8",
            )
            git(nested, "add", ".gitmodules")
            git(
                nested,
                "update-index",
                "--add",
                "--cacheinfo",
                f"160000,{dependency_commit},dependency",
            )
            git(nested, "commit", "-qm", "add ambient dependency")
            global_config = root / "global.gitconfig"
            global_config.write_text(
                '[submodule "dependency"]\n'
                "\turl = https://example.invalid/dependency.git\n",
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {
                    "GIT_CONFIG_GLOBAL": global_config.as_posix(),
                    "GIT_CONFIG_NOSYSTEM": "1",
                },
            ), self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                [["global", "submodule.dependency.url"]],
                raised.exception.details["effective_submodule_transport"],
            )

    def test_snapshot_rejects_local_nested_checkout_conversion_settings(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            git(nested, "config", "core.autocrlf", "true")
            (nested / "validator.txt").write_bytes(b"line\r\n")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertTrue(raised.exception.details["conversion_settings"])

    def test_snapshot_rejects_dormant_default_directory_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            hooks_raw = git(nested, "rev-parse", "--git-path", "hooks").decode().strip()
            hooks = Path(hooks_raw)
            if not hooks.is_absolute():
                hooks = nested / hooks
            pre_commit = hooks / "pre-commit"
            pre_commit.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            pre_commit.chmod(0o644)

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                ["pre-commit"],
                raised.exception.details["default_hooks"],
            )

    def test_snapshot_rejects_external_git_object_storage_environment(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            external_objects = Path(repo_tmp) / "external-objects"
            external_objects.mkdir()

            with patch.dict(
                os.environ,
                {
                    "GIT_OBJECT_DIRECTORY": external_objects.as_posix(),
                    "GIT_ALTERNATE_OBJECT_DIRECTORIES": external_objects.as_posix(),
                },
            ), self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing._nested_git_snapshot(nested)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                ["GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"],
                raised.exception.details["git_object_storage_environment"],
            )

    def test_materialization_rejects_ambient_git_repository_routing(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            source_config = nested / ".git" / "config"
            config_before = source_config.read_bytes()
            destination = Path(work_tmp) / "candidate"
            destination.mkdir()

            with patch.dict(
                os.environ,
                {
                    "GIT_DIR": (nested / ".git").as_posix(),
                    "GIT_WORK_TREE": nested.as_posix(),
                    "GIT_COMMON_DIR": (nested / ".git").as_posix(),
                },
            ), self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.copy_untracked_candidate(
                    repo,
                    destination,
                    [".validator"],
                )

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                ["GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"],
                raised.exception.details["git_repository_environment"],
            )
            self.assertEqual(config_before, source_config.read_bytes())
            self.assertFalse((destination / ".validator").exists())

    def test_snapshot_rejects_ambient_git_repository_routing_before_git(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            index = repo / ".git" / "index"
            index_before = index.read_bytes()

            with patch.dict(
                os.environ,
                {
                    "GIT_DIR": (repo / ".git").as_posix(),
                    "GIT_WORK_TREE": repo.as_posix(),
                    "GIT_COMMON_DIR": (repo / ".git").as_posix(),
                },
            ), patch.object(prepare_landing, "git_text") as git_text_mock, self.assertRaises(
                prepare_landing.PreparationFailure
            ) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                ["GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"],
                raised.exception.details["git_repository_environment"],
            )
            git_text_mock.assert_not_called()
            self.assertEqual(index_before, index.read_bytes())

    def test_snapshot_rejects_nested_repository_local_exclude_rules(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            exclude_raw = git(nested, "rev-parse", "--git-path", "info/exclude")
            exclude = Path(exclude_raw.decode("utf-8").strip())
            if not exclude.is_absolute():
                exclude = nested / exclude
            exclude.write_text("local.cache\n", encoding="utf-8")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertTrue(
                any(
                    setting.startswith("info.exclude ")
                    for setting in raised.exception.details["conversion_settings"]
                )
            )

    def test_snapshot_rejects_path_conditional_nested_exclude_file(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            root = Path(repo_tmp)
            repo = self.make_repo(root)
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            excludes = root / "nested.exclude"
            excludes.write_text("build.cache\n", encoding="utf-8")
            conditional = root / "conditional.gitconfig"
            conditional.write_text(
                f"[core]\n\texcludesFile = {excludes.as_posix()}\n",
                encoding="utf-8",
            )
            global_config = root / "global.gitconfig"
            global_config.write_text(
                f'[includeIf "gitdir:{nested.resolve().as_posix()}/"]\n'
                f"\tpath = {conditional.as_posix()}\n",
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"GIT_CONFIG_GLOBAL": global_config.as_posix(), "GIT_CONFIG_NOSYSTEM": "1"},
            ), self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertTrue(raised.exception.details["external_rule_settings"])

    def test_snapshot_rejects_nested_promisor_clone_settings(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            git(nested, "config", "remote.origin.promisor", "true")
            git(nested, "config", "remote.origin.partialclonefilter", "blob:none")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertTrue(raised.exception.details["partial_clone_settings"])

    def test_snapshot_rejects_nested_replacement_refs(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            base = git(nested, "rev-parse", "HEAD").decode().strip()
            git(nested, "commit", "--allow-empty", "-qm", "nested second")
            unmodified_head = git(nested, "rev-parse", "HEAD").decode().strip()
            git(nested, "replace", "HEAD", base)

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                [f"refs/replace/{unmodified_head}"],
                raised.exception.details["replacement_refs"],
            )

    def test_snapshot_rejects_resolved_uncommitted_nested_merge(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "base.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            git(nested, "branch", "-M", "main")
            git(nested, "checkout", "-qb", "topic")
            (nested / "topic.txt").write_text("topic\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested topic")
            git(nested, "checkout", "-q", "main")
            (nested / "main.txt").write_text("main\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested main")
            git(nested, "merge", "--no-commit", "topic")
            self.assertEqual(b"", git(nested, "ls-files", "-u"))

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertIn("MERGE_HEAD", raised.exception.details["operation_state"])

    def test_snapshot_preserves_nested_shallow_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            root = Path(repo_tmp)
            repo = self.make_repo(root)
            source = root / "nested-source"
            source.mkdir()
            git(source, "init", "-q")
            git(source, "config", "user.email", "test@example.invalid")
            git(source, "config", "user.name", "Nested Validator Test")
            (source / "validator.txt").write_text("base\n", encoding="utf-8")
            git(source, "add", ".")
            git(source, "commit", "-qm", "nested base")
            (source / "validator.txt").write_text("tip\n", encoding="utf-8")
            git(source, "commit", "-qam", "nested tip")
            nested = repo / ".validator"
            git(
                repo,
                "clone",
                "-q",
                "--depth",
                "1",
                f"file://{source.resolve().as_posix()}",
                nested.as_posix(),
            )
            git(nested, "remote", "remove", "origin")

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)

            source_boundaries = prepare_landing._shallow_boundaries(nested)
            self.assertTrue(source_boundaries)
            self.assertEqual(
                source_boundaries,
                prepare_landing._shallow_boundaries(isolated / ".validator"),
            )

    def test_snapshot_rejects_nested_history_storage_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            grafts = Path(git(nested, "rev-parse", "--git-path", "info/grafts").decode().strip())
            if not grafts.is_absolute():
                grafts = nested / grafts
            grafts.parent.mkdir(parents=True, exist_ok=True)
            grafts.write_text(git(nested, "rev-parse", "HEAD").decode(), encoding="ascii")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                ["info/grafts"],
                raised.exception.details["history_storage_overrides"],
            )

    def test_snapshot_rejects_dormant_nested_filter_attributes(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / ".gitattributes").write_text(
                "*.generated filter=demo\n",
                encoding="utf-8",
            )
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                [
                    "HEAD:.gitattributes",
                    "candidate:.gitattributes",
                    "index:.gitattributes",
                ],
                raised.exception.details["filter_attribute_sources"],
            )

    def test_snapshot_rejects_staged_only_nested_filter_attributes(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            attributes = nested / ".gitattributes"
            attributes.write_text("# no filters\n", encoding="utf-8")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            attributes.write_text("*.generated filter=demo\n", encoding="utf-8")
            git(nested, "add", ".gitattributes")
            attributes.write_text("# no filters\n", encoding="utf-8")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                ["index:.gitattributes"],
                raised.exception.details["filter_attribute_sources"],
            )

    def test_materialization_rejects_path_conditional_nested_conversion_settings(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            root = Path(repo_tmp)
            repo = self.make_repo(root)
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            conditional_config = root / "conditional.gitconfig"
            conditional_config.write_text("[core]\n\tautocrlf = true\n", encoding="utf-8")
            global_config = root / "global.gitconfig"
            global_config.write_text(
                f'[includeIf "gitdir:{nested.resolve().as_posix()}/"]\n'
                f"\tpath = {conditional_config.as_posix()}\n",
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"GIT_CONFIG_GLOBAL": global_config.as_posix(), "GIT_CONFIG_NOSYSTEM": "1"},
            ), self.assertRaises(prepare_landing.PreparationFailure) as raised:
                snapshot = prepare_landing.capture_candidate_snapshot(repo)
                isolated = Path(work_tmp) / "isolated"
                git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
                prepare_landing.materialize_candidate(repo, isolated, snapshot)

            self.assertIn("source_settings_digest", raised.exception.details)

    def test_snapshot_rejects_nested_assume_unchanged_state(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            tracked = nested / "validator.txt"
            tracked.write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            git(nested, "update-index", "--assume-unchanged", "validator.txt")
            tracked.write_text("hidden change\n", encoding="utf-8")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertIn("assume-unchanged", raised.exception.details["conversion_settings"][-1])

    def test_snapshot_rejects_outer_worktree_hiding_index_flags(self) -> None:
        for flag, detail_key in (
            ("--assume-unchanged", "assume_unchanged_paths"),
            ("--skip-worktree", "skip_worktree_paths"),
        ):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as repo_tmp:
                repo = self.make_repo(Path(repo_tmp))
                tracked = repo / "source.txt"
                git(repo, "update-index", flag, "source.txt")
                tracked.write_text("hidden candidate bytes\n", encoding="utf-8")

                with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                    prepare_landing.capture_candidate_snapshot(repo)

                self.assertEqual(
                    "candidate_snapshot_invalid",
                    raised.exception.failure_type,
                )
                self.assertEqual(["source.txt"], raised.exception.details[detail_key])

    def test_snapshot_rejects_nested_core_filemode_false(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            tracked = nested / "validator.sh"
            tracked.write_text("#!/bin/sh\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            git(nested, "config", "core.filemode", "false")
            tracked.chmod(0o755)

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertIn("core.filemode false", raised.exception.details["conversion_settings"])

    def test_snapshot_rejects_nested_split_index_state(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            git(nested, "update-index", "--split-index")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertTrue(
                any(
                    setting.startswith("split-index ")
                    for setting in raised.exception.details["conversion_settings"]
                )
            )

    def test_nested_materialization_preserves_index_version_four(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            git(nested, "update-index", "--index-version", "4")

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)

            self.assertEqual(
                b"4",
                git(
                    isolated / ".validator",
                    "update-index",
                    "--show-index-version",
                ).strip(),
            )

    def test_nested_materialization_preserves_index_stat_cache(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            tracked = nested / "validator.txt"
            tracked.write_text("base\n", encoding="utf-8")
            os.utime(tracked, ns=(1_577_836_800_000_000_000, 1_577_836_800_000_000_000))
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            expected_debug = git(nested, "ls-files", "--debug")
            expected_index = prepare_landing._git_index_state(nested)

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)
            isolated_nested = isolated / ".validator"

            self.assertEqual(expected_debug, git(isolated_nested, "ls-files", "--debug"))
            self.assertEqual(expected_index, prepare_landing._git_index_state(isolated_nested))

    def test_materialization_preserves_outer_index_stat_cache(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            tracked = repo / "source.txt"
            old_mtime_ns = 978_307_200_000_000_000
            os.utime(tracked, ns=(old_mtime_ns, old_mtime_ns))
            git(repo, "add", "source.txt")
            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            expected_debug = git(repo, "ls-files", "--debug")
            expected_index = (snapshot.index_mode, snapshot.index_bytes)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)

            self.assertEqual(expected_debug, git(isolated, "ls-files", "--debug"))
            self.assertEqual(expected_index, prepare_landing._git_index_state(isolated))

    def test_nested_materialization_binds_unreachable_objects(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            unreachable = git(
                nested,
                "hash-object",
                "-w",
                "--stdin",
                input_bytes=b"unreachable validator evidence\n",
            ).decode().strip()
            expected_inventory = prepare_landing._git_object_inventory(nested)

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            prepare_landing.materialize_candidate(repo, isolated, snapshot)
            isolated_nested = isolated / ".validator"

            git(isolated_nested, "cat-file", "-e", f"{unreachable}^{{object}}")
            self.assertEqual(
                expected_inventory,
                prepare_landing._git_object_inventory(isolated_nested),
            )

    def test_snapshot_rejects_nested_linked_worktrees(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            linked = Path(work_tmp) / "linked"
            git(nested, "worktree", "add", "--detach", linked.as_posix(), "HEAD")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                {nested.resolve().as_posix(), linked.resolve().as_posix()},
                set(raised.exception.details["registered_worktrees"]),
            )

    def test_snapshot_rejects_nested_core_ignorecase_true(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            git(nested, "config", "core.ignorecase", "true")
            (nested / "File").write_text("tracked\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            (nested / "file").write_text("hidden by case folding\n", encoding="utf-8")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertIn("core.ignorecase true", raised.exception.details["conversion_settings"])

    def test_snapshot_rejects_unsupported_nested_local_config(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            git(nested, "config", "status.showUntrackedFiles", "no")
            (nested / "untracked.txt").write_text("candidate\n", encoding="utf-8")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual(
                ["status.showuntrackedfiles"],
                raised.exception.details["unsupported_local_config_keys"],
            )

    def test_materialization_rejects_path_conditional_effective_git_config(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            root = Path(repo_tmp)
            repo = self.make_repo(root)
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            (nested / "untracked.txt").write_text("candidate\n", encoding="utf-8")

            included = root / "included.gitconfig"
            included.write_text(
                "[status]\n\tshowUntrackedFiles = no\n",
                encoding="utf-8",
            )
            global_config = root / "global.gitconfig"
            global_config.write_text(
                f'[includeIf "gitdir:{nested.resolve().as_posix()}/"]\n'
                f"\tpath = {included.as_posix()}\n",
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"GIT_CONFIG_GLOBAL": global_config.as_posix(), "GIT_CONFIG_NOSYSTEM": "1"},
            ):
                snapshot = prepare_landing.capture_candidate_snapshot(repo)
                isolated = Path(work_tmp) / "isolated"
                git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
                with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                    prepare_landing.materialize_candidate(repo, isolated, snapshot)

            self.assertIn("effective Git configuration", str(raised.exception))
            self.assertNotEqual(
                raised.exception.details["source_config_digest"],
                raised.exception.details["destination_config_digest"],
            )

    def test_snapshot_rejects_nested_fetch_head(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            git(nested, "fetch", "-q", ".", "HEAD")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual(["FETCH_HEAD"], raised.exception.details["pseudo_ref_state"])

    def test_snapshot_rejects_nested_resolve_undo_state(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            tracked = nested / "validator.txt"
            tracked.write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            base_branch = git(nested, "symbolic-ref", "--short", "HEAD").decode().strip()
            git(nested, "checkout", "-qb", "conflict")
            tracked.write_text("branch\n", encoding="utf-8")
            git(nested, "commit", "-qam", "branch change")
            git(nested, "checkout", "-q", base_branch)
            tracked.write_text("base branch\n", encoding="utf-8")
            git(nested, "commit", "-qam", "base branch change")
            merge = subprocess.run(
                ("git", "merge", "--no-edit", "conflict"),
                cwd=nested,
                check=False,
                capture_output=True,
            )
            self.assertNotEqual(0, merge.returncode)
            tracked.write_text("resolved\n", encoding="utf-8")
            git(nested, "add", "validator.txt")
            git(nested, "merge", "--quit")
            orig_head = Path(
                git(nested, "rev-parse", "--git-path", "ORIG_HEAD").decode().strip()
            )
            if not orig_head.is_absolute():
                orig_head = nested / orig_head
            orig_head.unlink(missing_ok=True)
            self.assertTrue(prepare_landing._resolve_undo_entries(nested))

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertTrue(raised.exception.details["resolve_undo_entries"])

    def test_snapshot_rejects_symlinks_in_nested_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator-link").symlink_to("../ignored-validator-state")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested symlink")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual(["validator-link"], raised.exception.details["symlinks"])

    def test_snapshot_rejects_ambient_nested_hook_settings(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            root = Path(repo_tmp)
            repo = self.make_repo(root)
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            global_config = root / "global.gitconfig"
            global_config.write_text(
                f"[core]\n\thooksPath = {(root / 'hooks').as_posix()}\n",
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"GIT_CONFIG_GLOBAL": global_config.as_posix(), "GIT_CONFIG_NOSYSTEM": "1"},
            ), self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertTrue(raised.exception.details["hook_settings"])

    def test_snapshot_rejects_fsmonitor_before_candidate_git_reads(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            root = Path(repo_tmp)
            repo = self.make_repo(root)
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            marker = root / "fsmonitor-ran"
            hook = root / "fsmonitor-hook"
            hook.write_text(
                f"#!/bin/sh\n: > {marker.as_posix()}\n",
                encoding="utf-8",
            )
            hook.chmod(0o755)
            git(nested, "config", "core.fsmonitor", hook.as_posix())

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual([hook.as_posix()], raised.exception.details["fsmonitor_settings"])
            self.assertFalse(marker.exists())

    def test_nested_materialization_disables_destination_fsmonitor(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            root = Path(repo_tmp)
            repo = self.make_repo(root)
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            isolated_nested = isolated / ".validator"
            marker = root / "destination-fsmonitor-ran"
            hook = root / "destination-fsmonitor"
            hook.write_text(f"#!/bin/sh\n: > {marker.as_posix()}\n", encoding="utf-8")
            hook.chmod(0o755)
            conditional = root / "conditional.gitconfig"
            conditional.write_text(
                f"[core]\n\tfsmonitor = {hook.as_posix()}\n",
                encoding="utf-8",
            )
            global_config = root / "global.gitconfig"
            global_config.write_text(
                f'[includeIf "gitdir:{isolated_nested.resolve().as_posix()}/"]\n'
                f"\tpath = {conditional.as_posix()}\n",
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"GIT_CONFIG_GLOBAL": global_config.as_posix(), "GIT_CONFIG_NOSYSTEM": "1"},
            ):
                git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
                prepare_landing.materialize_candidate(repo, isolated, snapshot)
                self.assertEqual((), prepare_landing._effective_fsmonitor_settings(isolated_nested))
                git(isolated_nested, "status", "--short")

            self.assertFalse(marker.exists())

    def test_snapshot_disables_ambient_external_diff(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            root = Path(repo_tmp)
            repo = self.make_repo(root)
            marker = root / "external-diff-ran"
            external_diff = root / "external-diff"
            external_diff.write_text(
                f"#!/bin/sh\n: > {marker.as_posix()}\nexit 1\n",
                encoding="utf-8",
            )
            external_diff.chmod(0o755)
            git(repo, "config", "diff.external", external_diff.as_posix())
            (repo / "source.txt").write_text("candidate\n", encoding="utf-8")

            snapshot = prepare_landing.capture_candidate_snapshot(repo)

            self.assertTrue(snapshot.worktree_diff_digest.startswith("sha256:"))
            self.assertFalse(marker.exists())

    def test_snapshot_rejects_ambient_filter_driver_before_reconstruction(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            root = Path(repo_tmp)
            repo = self.make_repo(root)
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / ".gitattributes").write_text(
                "validator.txt filter=demo\n",
                encoding="utf-8",
            )
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            global_config = root / "global.gitconfig"
            global_config.write_text(
                "[filter \"demo\"]\n\tsmudge = cat\n",
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"GIT_CONFIG_GLOBAL": global_config.as_posix(), "GIT_CONFIG_NOSYSTEM": "1"},
            ), self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual(["validator.txt"], raised.exception.details["filtered_paths"])

    def test_snapshot_rejects_implicit_xdg_attribute_rules(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            root = Path(repo_tmp)
            repo = self.make_repo(root)
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            xdg_root = root / "xdg"
            attributes = xdg_root / "git" / "attributes"
            attributes.parent.mkdir(parents=True)
            attributes.write_text("*.generated filter=demo\n", encoding="utf-8")

            with patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": xdg_root.as_posix()},
            ), self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual("candidate_snapshot_invalid", raised.exception.failure_type)
            self.assertEqual(
                [attributes.as_posix()],
                raised.exception.details["implicit_rule_sources"],
            )

    def test_snapshot_rejects_dirty_filter_before_clean_driver_runs(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            root = Path(repo_tmp)
            repo = self.make_repo(root)
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / ".gitattributes").write_text(
                "validator.txt filter=demo\n",
                encoding="utf-8",
            )
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested filtered base")
            (nested / "validator.txt").write_text("dirty\n", encoding="utf-8")
            marker = root / "clean-filter-ran"
            clean_filter = root / "clean-filter"
            clean_filter.write_text(
                f"#!/bin/sh\n: > {marker.as_posix()}\ncat\n",
                encoding="utf-8",
            )
            clean_filter.chmod(0o755)
            global_config = root / "global.gitconfig"
            global_config.write_text(
                f"[filter \"demo\"]\n\tclean = {clean_filter.as_posix()}\n",
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"GIT_CONFIG_GLOBAL": global_config.as_posix(), "GIT_CONFIG_NOSYSTEM": "1"},
            ), self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual(["validator.txt"], raised.exception.details["filtered_paths"])
            self.assertFalse(marker.exists())

    def test_snapshot_rejects_filter_removed_only_from_nested_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            root = Path(repo_tmp)
            repo = self.make_repo(root)
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / ".gitattributes").write_text(
                "validator.txt filter=demo\n",
                encoding="utf-8",
            )
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested filtered base")
            (nested / ".gitattributes").write_text("", encoding="utf-8")
            git(nested, "add", ".gitattributes")
            global_config = root / "global.gitconfig"
            global_config.write_text(
                "[filter \"demo\"]\n\tsmudge = cat\n",
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"GIT_CONFIG_GLOBAL": global_config.as_posix(), "GIT_CONFIG_NOSYSTEM": "1"},
            ), self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual(
                ["validator.txt"],
                raised.exception.details["head_filtered_paths"],
            )

    def test_snapshot_checks_head_filters_against_candidate_added_paths(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            root = Path(repo_tmp)
            repo = self.make_repo(root)
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / ".gitattributes").write_text("*.dat filter=demo\n", encoding="utf-8")
            git(nested, "add", ".gitattributes")
            git(nested, "commit", "-qm", "nested filter policy")
            (nested / ".gitattributes").write_text("", encoding="utf-8")
            (nested / "candidate.dat").write_text("candidate\n", encoding="utf-8")
            git(nested, "add", ".gitattributes", "candidate.dat")

            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual(
                ["candidate.dat"],
                raised.exception.details["head_filtered_paths"],
            )

    def test_nested_checkout_pathspec_magic_is_reset_literally(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ":(glob)**"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            materialized_tree = prepare_landing.materialize_candidate(repo, isolated, snapshot)

            self.assertEqual(snapshot.index_tree, materialized_tree)
            self.assertEqual(
                b"",
                git(isolated, "--literal-pathspecs", "ls-files", "--stage", "--", ":(glob)**"),
            )

    def test_nested_checkout_does_not_restore_staged_directory_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo = self.make_repo(Path(repo_tmp))
            nested = repo / ".validator"
            nested.mkdir()
            (nested / "old.txt").write_text("old owner source\n", encoding="utf-8")
            git(repo, "add", ".validator/old.txt")
            git(repo, "commit", "-qm", "tracked validator predecessor")
            git(repo, "rm", "-qr", ".validator")
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("replacement\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested replacement")

            snapshot = prepare_landing.capture_candidate_snapshot(repo)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
            materialized_tree = prepare_landing.materialize_candidate(repo, isolated, snapshot)

            self.assertEqual(snapshot.index_tree, materialized_tree)
            self.assertEqual(b"", git(isolated, "ls-tree", "-r", materialized_tree, "--", ".validator"))
            self.assertTrue((isolated / ".validator" / "validator.txt").is_file())

    def test_nested_materialization_ignores_ambient_git_template_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            root = Path(repo_tmp)
            repo = self.make_repo(root)
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            (nested / "validator.txt").write_text("candidate\n", encoding="utf-8")
            template = root / "template"
            (template / "hooks").mkdir(parents=True)
            hook = template / "hooks" / "post-index-change"
            hook.write_text("#!/bin/sh\n: > hook.cache\n", encoding="utf-8")
            hook.chmod(0o755)
            (template / "info").mkdir()
            (template / "info" / "exclude").write_text("hook.cache\n", encoding="utf-8")

            with patch.dict(os.environ, {"GIT_TEMPLATE_DIR": template.as_posix()}):
                snapshot = prepare_landing.capture_candidate_snapshot(repo)
                isolated = Path(work_tmp) / "isolated"
                git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)
                materialized_tree = prepare_landing.materialize_candidate(repo, isolated, snapshot)

            self.assertEqual(snapshot.index_tree, materialized_tree)
            self.assertFalse((isolated / ".validator" / "hook.cache").exists())
            self.assertEqual(
                b"/dev/null\n",
                git(isolated / ".validator", "config", "--local", "--get", "core.hooksPath"),
            )

    def test_nested_clone_disables_ambient_reference_transaction_hook(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            root = Path(repo_tmp)
            repo = self.make_repo(root)
            nested = repo / ".validator"
            nested.mkdir()
            git(nested, "init", "-q")
            git(nested, "config", "user.email", "test@example.invalid")
            git(nested, "config", "user.name", "Nested Validator Test")
            git(nested, "config", "core.hooksPath", "/dev/null")
            (nested / "validator.txt").write_text("base\n", encoding="utf-8")
            git(nested, "add", ".")
            git(nested, "commit", "-qm", "nested base")
            with patch.dict(
                os.environ,
                {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"},
            ):
                snapshot = prepare_landing.capture_candidate_snapshot(repo)
                nested_snapshot = prepare_landing._nested_git_snapshot(nested)
            self.assertIsNotNone(nested_snapshot)
            isolated = Path(work_tmp) / "isolated"
            git(repo, "worktree", "add", "--detach", isolated.as_posix(), snapshot.head)

            hooks = root / "ambient-hooks"
            hooks.mkdir()
            marker = root / "reference-transaction-ran"
            hook = hooks / "reference-transaction"
            hook.write_text(
                f"#!/bin/sh\n: > {marker.as_posix()}\n",
                encoding="utf-8",
            )
            hook.chmod(0o755)
            global_config = root / "global.gitconfig"
            global_config.write_text(
                f"[core]\n\thooksPath = {hooks.as_posix()}\n",
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"GIT_CONFIG_GLOBAL": global_config.as_posix(), "GIT_CONFIG_NOSYSTEM": "1"},
            ), patch.object(
                prepare_landing,
                "_nested_git_snapshot",
                return_value=nested_snapshot,
            ):
                materialized_tree = prepare_landing.materialize_candidate(
                    repo,
                    isolated,
                    snapshot,
                )

            self.assertEqual(snapshot.index_tree, materialized_tree)
            self.assertFalse(marker.exists())

    def test_preparation_patch_rejects_paths_outside_generated_authority(self) -> None:
        prepare_landing.require_preparation_output_scope(
            ("generated/out.json", "kag/indexes/shards/a.jsonl")
        )
        with self.assertRaises(prepare_landing.PreparationFailure) as raised:
            prepare_landing.require_preparation_output_scope(
                ("generated/out.json", "scripts/unexpected.py")
            )

        self.assertEqual(
            "preparation_output_scope_violation",
            raised.exception.failure_type,
        )

    def test_portable_family_staging_includes_tiered_control_manifests(self) -> None:
        self.assertTrue(
            {
                "kag/indexes/index_family.manifest.json",
                "kag/indexes/corpus.manifest.json",
                "kag/indexes/hot_profile.json",
                "kag/indexes/artifact_locators.json",
                "kag/indexes/shards",
            }.issubset(set(prepare_landing.PORTABLE_FAMILY_PATHS))
        )

    def test_scc_order_is_staged_and_bounded_until_tree_convergence(self) -> None:
        refs = prepare_landing.ResolvedRefs("h", "e", "b")
        trees = iter(("tree-0", "tree-1", "tree-1", "tree-1"))
        with patch.object(prepare_landing, "git_text", side_effect=lambda *_args: next(trees)), patch.object(
            prepare_landing,
            "run_command",
        ) as run_command, patch.object(prepare_landing, "stage_paths") as stage_paths:
            iterations, tree = prepare_landing.converge_scc(
                Path("/candidate"),
                refs,
                max_iterations=3,
            )

        self.assertEqual(2, iterations)
        self.assertEqual("tree-1", tree)
        self.assertEqual(
            [
                prepare_landing.coverage_command(refs),
                prepare_landing.generated_command(),
                prepare_landing.portable_family_command(refs),
                prepare_landing.coverage_command(refs),
                prepare_landing.generated_command(),
                prepare_landing.portable_family_command(refs),
            ],
            [item.args[0] for item in run_command.call_args_list],
        )
        self.assertEqual(
            [
                call(Path("/candidate"), prepare_landing.COVERAGE_PATHS),
                call(Path("/candidate"), prepare_landing.GENERATED_PATHS),
                call(Path("/candidate"), prepare_landing.PORTABLE_FAMILY_PATHS),
            ]
            * 2,
            stage_paths.call_args_list,
        )

    def test_non_convergence_fails_closed(self) -> None:
        refs = prepare_landing.ResolvedRefs("h", "e", "b")
        trees = iter(("a", "b", "b", "c"))
        with patch.object(prepare_landing, "git_text", side_effect=lambda *_args: next(trees)), patch.object(
            prepare_landing,
            "run_command",
        ), patch.object(prepare_landing, "stage_paths"):
            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.converge_scc(Path("/candidate"), refs, max_iterations=2)

        self.assertEqual("fixed_point_non_convergence", raised.exception.failure_type)

    def test_budget_receipt_mutation_reenters_scc_until_stable(self) -> None:
        refs = prepare_landing.ResolvedRefs("h", "e", "b")
        with patch.object(
            prepare_landing,
            "converge_scc",
            side_effect=((2, "family-1"), (2, "family-2"), (1, "family-2")),
        ) as converge, patch.object(
            prepare_landing,
            "ensure_budget_receipt",
            side_effect=("created", "created", "accepted"),
        ) as ensure, patch.object(
            prepare_landing,
            "git_text",
            side_effect=("a", "b", "c", "d", "e", "e"),
        ):
            iterations, tree, receipt = prepare_landing.converge_budgeted_scc(
                Path("/candidate"),
                refs,
                max_iterations=3,
                budget_reason="bounded growth",
            )

        self.assertEqual(5, iterations)
        self.assertEqual("e", tree)
        self.assertEqual("created", receipt)
        self.assertEqual(3, converge.call_count)
        self.assertEqual(3, ensure.call_count)

    def test_external_seed_reuse_rejects_changed_canonical_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            git(repo, "init", "-q")
            git(repo, "config", "user.email", "test@example.invalid")
            git(repo, "config", "user.name", "Prepare Landing Test")
            (repo / "runtime.py").write_text("epoch = 1\n", encoding="utf-8")
            git(repo, "add", "runtime.py")
            git(repo, "commit", "-qm", "base")
            head = git(repo, "rev-parse", "HEAD").decode("ascii").strip()
            (repo / "runtime.py").write_text("epoch = 2\n", encoding="utf-8")
            git(repo, "add", "runtime.py")

            with patch.object(
                coverage_generation,
                "_coverage_runtime_input_paths",
                return_value=(Path("runtime.py"),),
            ):
                with self.assertRaisesRegex(RuntimeError, "runtime inputs differ"):
                    prepare_landing.require_seed_compatible_runtime(repo, head)

    def seeded_coverage_fixture(self):
        seed = json.loads(
            (REPO_ROOT / "generated" / "repo_local_kag_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        owners = seed["owners"]
        # The committed coverage report may be a partial v4 migration read model.
        # These tests exercise the legacy external-seed contract, so make that
        # fixture explicitly all-owner-green and v3 without changing the source
        # report used by the generated/release lanes.
        legacy_family = {
            "source": "kag/indexes/source_surface_index.json",
            "entity": "kag/indexes/repo_entity_index.json",
            "artifact": "kag/indexes/repo_artifact_index.json",
            "anchor": "kag/indexes/repo_anchor_index.json",
            "event": "kag/indexes/repo_event_index.json",
            "assertion": "kag/indexes/repo_assertion_index.json",
            "relation": "kag/indexes/repo_relation_index.json",
        }
        for owner in owners:
            if owner["repo"] == "aoa-kag":
                continue
            owner["index_status"] = "passed"
            owner["family_storage"] = "v3-portable-shards"
            owner["repository_index_family"] = copy.deepcopy(legacy_family)
        order = tuple(row["repo"] for row in owners)
        roots = {owner: Path("/providers") / owner for owner in order}
        entries = {
            owner: {"pinned_ref": f"{index + 1:040x}"}
            for index, owner in enumerate(order)
        }
        self_row = copy.deepcopy(next(row for row in owners if row["repo"] == "aoa-kag"))
        self_row["coverage"]["documents"] += 1
        return seed, order, roots, entries, self_row

    def test_seeded_coverage_rebuilds_only_self_and_reassembles_aggregate(self) -> None:
        seed, order, roots, entries, self_row = self.seeded_coverage_fixture()

        with patch.object(
            prepare_landing,
            "require_seed_compatible_runtime",
        ), patch.object(
            prepare_landing,
            "load_external_coverage_seed",
            return_value=copy.deepcopy(seed),
        ), patch.object(
            coverage_generation,
            "_validate_coverage_payload_schema",
        ), patch.object(
            coverage_generation,
            "provider_repo_order",
            return_value=order,
        ), patch.object(
            coverage_generation,
            "provider_by_repo",
            return_value=entries,
        ), patch.object(
            coverage_generation,
            "configured_owner_roots",
            return_value=list(roots.items()),
        ), patch.object(
            coverage_generation,
            "_git_head",
            side_effect=lambda owner, _root: entries[owner]["pinned_ref"],
        ), patch.object(
            coverage_generation,
            "_build_owner_coverage",
            return_value=(self_row, {"owner": "aoa-kag"}),
        ) as build_self, patch.object(
            coverage_generation,
            "load_portable_family",
            return_value=(self_row, {}, {}),
        ) as load_self_family, patch.object(
            prepare_landing,
            "expected_external_portable_family",
            side_effect=lambda owner, _root: next(
                row["portable_family"] for row in seed["owners"] if row["repo"] == owner
            ),
        ):
            payload = prepare_landing.build_preparation_coverage(
                REPO_ROOT,
                external_seed_ref="seed",
            )

        self.assertEqual(1, build_self.call_count)
        load_self_family.assert_called_once_with(
            REPO_ROOT,
            require_budget_receipt=False,
        )
        self.assertEqual(
            (self_row, {}, {}),
            build_self.call_args.kwargs["portable_bundle"],
        )
        rebuilt = next(row for row in payload["owners"] if row["repo"] == "aoa-kag")
        self.assertEqual(self_row, rebuilt)
        self.assertEqual(len(order), payload["coverage_summary"]["owner_count"])

    def test_seeded_coverage_rejects_external_manifest_identity_drift(self) -> None:
        seed, order, roots, entries, self_row = self.seeded_coverage_fixture()
        first_external = next(row for row in seed["owners"] if row["repo"] != "aoa-kag")
        drifted = copy.deepcopy(first_external["portable_family"])
        drifted["tracked_bytes"] += 1

        with patch.object(
            prepare_landing,
            "require_seed_compatible_runtime",
        ), patch.object(
            prepare_landing,
            "load_external_coverage_seed",
            return_value=copy.deepcopy(seed),
        ), patch.object(
            coverage_generation,
            "_validate_coverage_payload_schema",
        ), patch.object(
            coverage_generation,
            "provider_repo_order",
            return_value=order,
        ), patch.object(
            coverage_generation,
            "provider_by_repo",
            return_value=entries,
        ), patch.object(
            coverage_generation,
            "configured_owner_roots",
            return_value=list(roots.items()),
        ), patch.object(
            coverage_generation,
            "_git_head",
            side_effect=lambda owner, _root: entries[owner]["pinned_ref"],
        ), patch.object(
            coverage_generation,
            "_build_owner_coverage",
            return_value=(self_row, {"owner": "aoa-kag"}),
        ), patch.object(
            prepare_landing,
            "expected_external_portable_family",
            side_effect=lambda owner, _root: (
                drifted
                if owner == first_external["repo"]
                else next(
                    row["portable_family"]
                    for row in seed["owners"]
                    if row["repo"] == owner
                )
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "manifest identity drift"):
                prepare_landing.build_preparation_coverage(
                    REPO_ROOT,
                    external_seed_ref="seed",
                )

    def test_seed_only_sentinel_never_reads_external_checkouts(self) -> None:
        seed, order, roots, entries, self_row = self.seeded_coverage_fixture()

        with patch.object(
            prepare_landing,
            "require_seed_compatible_runtime",
        ), patch.object(
            prepare_landing,
            "load_external_coverage_seed",
            return_value=copy.deepcopy(seed),
        ), patch.object(
            coverage_generation,
            "_validate_coverage_payload_schema",
        ), patch.object(
            coverage_generation,
            "provider_repo_order",
            return_value=order,
        ), patch.object(
            coverage_generation,
            "provider_by_repo",
            return_value=entries,
        ), patch.object(
            coverage_generation,
            "configured_owner_roots",
            return_value=list(roots.items()),
        ), patch.object(
            coverage_generation,
            "_build_owner_coverage",
            return_value=(self_row, {"owner": "aoa-kag"}),
        ), patch.object(
            coverage_generation,
            "_git_head",
        ) as git_head, patch.object(
            prepare_landing,
            "expected_external_portable_family",
        ) as external_family:
            payload = prepare_landing.build_preparation_coverage(
                REPO_ROOT,
                external_seed_ref="seed",
                verify_external_manifests=False,
            )

        self.assertEqual(len(order), payload["coverage_summary"]["owner_count"])
        git_head.assert_not_called()
        external_family.assert_not_called()

    def test_prepare_coverage_rebuilds_every_owner_when_seed_runtime_drifted(self) -> None:
        coverage = unittest.mock.Mock()
        coverage.DEFAULT_OUTPUT = Path("coverage.json")
        coverage.DEFAULT_MIN_OUTPUT = Path("coverage.min.json")
        payload = {"owners": []}
        with patch.object(
            prepare_landing,
            "coverage_generation_module",
            return_value=coverage,
        ), patch.object(
            prepare_landing,
            "build_preparation_coverage",
            side_effect=prepare_landing.PreparationSeedInapplicable("runtime changed"),
        ), patch.object(
            prepare_landing,
            "build_full_preparation_coverage",
            return_value=payload,
        ) as full_build:
            result = prepare_landing.prepare_self_coverage(
                Path("/candidate"),
                external_seed_ref="base",
                check=False,
                verify_external_manifests=True,
            )

        self.assertEqual(0, result)
        full_build.assert_called_once_with(Path("/candidate"))
        coverage.write_outputs.assert_called_once_with(
            coverage.DEFAULT_OUTPUT,
            coverage.DEFAULT_MIN_OUTPUT,
            payload,
        )

    def test_prepare_coverage_reuses_verified_full_owner_cache_within_scc(self) -> None:
        coverage = unittest.mock.Mock()
        coverage.DEFAULT_OUTPUT = Path("coverage.json")
        coverage.DEFAULT_MIN_OUTPUT = Path("coverage.min.json")
        payload = {"owners": []}
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = Path(tmpdir) / "full-owner.json"
            cache.write_text("cached\n", encoding="utf-8")
            with patch.object(
                prepare_landing,
                "coverage_generation_module",
                return_value=coverage,
            ), patch.object(
                prepare_landing,
                "build_preparation_coverage",
                side_effect=prepare_landing.PreparationSeedInapplicable(
                    "runtime changed"
                ),
            ), patch.object(
                prepare_landing,
                "load_preparation_coverage_cache",
                return_value=payload,
            ) as load_cache, patch.object(
                prepare_landing,
                "build_full_preparation_coverage",
            ) as full_build:
                result = prepare_landing.prepare_self_coverage(
                    Path("/candidate"),
                    external_seed_ref="base",
                    check=False,
                    verify_external_manifests=True,
                    full_coverage_cache=cache,
                )

        self.assertEqual(0, result)
        load_cache.assert_called_once_with(Path("/candidate"), cache)
        full_build.assert_not_called()

    def test_full_owner_cache_is_private_runtime_bound_and_reverified(self) -> None:
        coverage = unittest.mock.Mock()
        coverage._coverage_runtime_inputs_digest.return_value = "sha256:runtime"
        cached = {"owners": [{"repo": "external"}]}
        rebuilt = {"owners": [{"repo": "aoa-kag"}]}
        provider_identity = (
            {
                "owner": "external",
                "head": "a" * 40,
                "head_tree": "b" * 40,
                "posture": "pinned",
            },
        )
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            prepare_landing,
            "coverage_generation_module",
            return_value=coverage,
        ), patch.object(
            prepare_landing,
            "verify_provider_identities",
            return_value=provider_identity,
        ), patch.object(
            prepare_landing,
            "build_preparation_coverage_from_payload",
            return_value=rebuilt,
        ) as verify_cache:
            cache = Path(tmpdir) / "full-owner.json"
            prepare_landing.write_preparation_coverage_cache(
                Path("/candidate"),
                cache,
                cached,
            )
            loaded = prepare_landing.load_preparation_coverage_cache(
                Path("/candidate"),
                cache,
            )

            self.assertEqual(0o600, stat.S_IMODE(cache.stat().st_mode))

        self.assertEqual(rebuilt, loaded)
        verify_cache.assert_called_once_with(
            Path("/candidate"),
            cached,
            verify_external_manifests=False,
        )

    def test_full_owner_cache_rejects_provider_edit_without_head_move(self) -> None:
        coverage = unittest.mock.Mock()
        coverage._coverage_runtime_inputs_digest.return_value = "sha256:runtime"
        cached = {"owners": [{"repo": "external"}]}
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            candidate = root / "candidate"
            provider_parent = root / "provider-parent"
            provider_parent.mkdir()
            provider = self.make_repo(provider_parent)
            candidate.mkdir()
            (candidate / "manifests").mkdir()
            head = git(provider, "rev-parse", "HEAD").decode("ascii").strip()
            (candidate / "manifests" / "provider_registry.json").write_text(
                json.dumps(
                    {
                        "providers": [
                            {
                                "repo": "external",
                                "root_kind": "direct",
                                "env": "TEST_PREPARE_PROVIDER_ROOT",
                                "checkout_mode": "pinned",
                                "pinned_ref": head,
                            }
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            cache = root / "full-owner.json"
            with patch.object(
                prepare_landing,
                "coverage_generation_module",
                return_value=coverage,
            ), patch.dict(
                os.environ,
                {"TEST_PREPARE_PROVIDER_ROOT": provider.as_posix()},
            ):
                prepare_landing.write_preparation_coverage_cache(
                    candidate,
                    cache,
                    cached,
                )
                (provider / "source.txt").write_text(
                    "concurrent edit\n",
                    encoding="utf-8",
                )
                with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                    prepare_landing.load_preparation_coverage_cache(
                        candidate,
                        cache,
                    )

        self.assertEqual("provider_identity_mismatch", raised.exception.failure_type)

    def test_sentinel_stops_on_coverage_drift_before_generated_check(self) -> None:
        coverage = unittest.mock.Mock()
        coverage.DEFAULT_OUTPUT = Path("coverage.json")
        coverage.DEFAULT_MIN_OUTPUT = Path("coverage.min.json")
        coverage.check_outputs.return_value = False
        with patch.object(
            prepare_landing,
            "coverage_generation_module",
            return_value=coverage,
        ), patch.object(
            prepare_landing,
            "build_preparation_coverage",
            return_value={},
        ), patch.object(
            prepare_landing,
            "build_self_coverage_check_payload",
            return_value={},
        ), patch.object(prepare_landing, "run_command") as run_command:
            code, receipt = prepare_landing.landing_sentinel(
                Path("/candidate"),
                external_seed_ref="base",
            )

        self.assertEqual(1, code)
        self.assertEqual("self_coverage_drift", receipt["failure_type"])
        run_command.assert_not_called()

    def test_sentinel_inapplicable_routes_to_unchanged_full_proof(self) -> None:
        with patch.object(
            prepare_landing,
            "coverage_generation_module",
        ), patch.object(
            prepare_landing,
            "build_preparation_coverage",
            side_effect=prepare_landing.PreparationSeedInapplicable("runtime changed"),
        ):
            code, receipt = prepare_landing.landing_sentinel(
                Path("/candidate"),
                external_seed_ref="base",
            )

        self.assertEqual(0, code)
        self.assertEqual("inapplicable", receipt["verdict"])
        self.assertTrue(receipt["fallback_required"])

    def test_sentinel_pass_still_requires_full_owner_proof(self) -> None:
        coverage = unittest.mock.Mock()
        coverage.DEFAULT_OUTPUT = Path("coverage.json")
        coverage.DEFAULT_MIN_OUTPUT = Path("coverage.min.json")
        coverage.check_outputs.return_value = True
        generated = prepare_landing.CommandResult(
            prepare_landing.generated_command(check=True),
            0,
            "",
            "",
            4,
        )
        with patch.object(
            prepare_landing,
            "coverage_generation_module",
            return_value=coverage,
        ), patch.object(
            prepare_landing,
            "build_preparation_coverage",
            return_value={},
        ), patch.object(
            prepare_landing,
            "build_self_coverage_check_payload",
            return_value={},
        ), patch.object(
            prepare_landing,
            "run_command",
            return_value=generated,
        ):
            code, receipt = prepare_landing.landing_sentinel(
                Path("/candidate"),
                external_seed_ref="base",
            )

        self.assertEqual(0, code)
        self.assertEqual("passed", receipt["verdict"])
        self.assertTrue(receipt["fallback_required"])

    def test_sentinel_distinguishes_generated_drift_from_missing_prerequisite(self) -> None:
        coverage = unittest.mock.Mock()
        coverage.DEFAULT_OUTPUT = Path("coverage.json")
        coverage.DEFAULT_MIN_OUTPUT = Path("coverage.min.json")
        coverage.check_outputs.return_value = True
        drift = prepare_landing.CommandResult(
            prepare_landing.generated_command(check=True),
            1,
            "",
            "[generate-kag] drift in generated/kag_registry.json\n",
            4,
        )
        missing = prepare_landing.CommandResult(
            prepare_landing.generated_command(check=True),
            1,
            "[error] missing required file: provider/kag/manifest.json\n",
            "",
            4,
        )
        with patch.object(
            prepare_landing,
            "coverage_generation_module",
            return_value=coverage,
        ), patch.object(
            prepare_landing,
            "build_preparation_coverage",
            return_value={},
        ), patch.object(
            prepare_landing,
            "build_self_coverage_check_payload",
            return_value={},
        ), patch.object(
            prepare_landing,
            "run_command",
            side_effect=(drift, missing),
        ):
            drift_code, drift_receipt = prepare_landing.landing_sentinel(
                Path("/candidate"),
                external_seed_ref="base",
            )
            missing_code, missing_receipt = prepare_landing.landing_sentinel(
                Path("/candidate"),
                external_seed_ref="base",
            )

        self.assertEqual(1, drift_code)
        self.assertEqual("generated_projection_drift", drift_receipt["failure_type"])
        self.assertEqual(0, missing_code)
        self.assertEqual("inapplicable", missing_receipt["verdict"])
        self.assertTrue(missing_receipt["fallback_required"])

    def test_budget_receipt_requires_explicit_reason_for_final_digest(self) -> None:
        refs = prepare_landing.ResolvedRefs("h", "e", "b")
        failure = prepare_landing.CommandResult(
            ("family", "--check"),
            1,
            "",
            "portable family budget is exceeded and no matching receipt exists",
            10,
        )
        with patch.object(prepare_landing, "run_command", return_value=failure):
            with self.assertRaises(prepare_landing.PreparationFailure) as raised:
                prepare_landing.ensure_budget_receipt(
                    Path("/candidate"),
                    refs,
                    budget_reason=None,
                )

        self.assertEqual("budget_receipt_authority_required", raised.exception.failure_type)

    def test_tiered_budget_receipt_uses_corpus_digest(self) -> None:
        digest = "a" * 64
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest = root / "kag" / "indexes" / "index_family.manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "aoa-repo-local-kag-distribution-manifest-v1",
                        "distribution_identity": {
                            "corpus_digest": f"sha256:{digest}"
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            receipt = prepare_landing._current_budget_receipt_path(root)

        self.assertEqual(
            Path("kag/receipts/index_family_budget") / f"{digest}.json",
            receipt,
        )

    def test_budget_receipt_is_created_only_after_final_check_requests_it(self) -> None:
        refs = prepare_landing.ResolvedRefs("h", "e", "b")
        failure = prepare_landing.CommandResult(
            ("family", "--check"),
            1,
            "",
            "portable family budget is exceeded and no matching receipt exists",
            10,
        )
        success = prepare_landing.CommandResult(("family",), 0, "", "", 10)
        with patch.object(
            prepare_landing,
            "run_command",
            side_effect=(failure, success, success),
        ) as run_command, patch.object(
            prepare_landing,
            "prune_obsolete_budget_receipts",
        ) as prune, patch.object(prepare_landing, "stage_paths"):
            result = prepare_landing.ensure_budget_receipt(
                Path("/candidate"),
                refs,
                budget_reason="final candidate growth",
            )

        self.assertEqual("created", result)
        self.assertTrue(run_command.call_args_list[1].args[0].count("--write-budget-receipt"))
        self.assertTrue(run_command.call_args_list[2].args[0].count("--check"))
        prune.assert_called_once_with(Path("/candidate"), refs)


if __name__ == "__main__":
    unittest.main()
