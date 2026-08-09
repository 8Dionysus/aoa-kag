from __future__ import annotations

import copy
import json
import os
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
    def fake_converge(repo_root: Path, _refs: object, *, max_iterations: int) -> tuple[int, str]:
        assert max_iterations > 0
        source = git(repo_root, "show", ":source.txt").decode("utf-8")
        note = git(repo_root, "show", ":note.txt").decode("utf-8")
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
            self.assertEqual("drift", receipt["verdict"])
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

    def test_apply_fails_closed_when_candidate_changes_during_preparation(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as work_tmp:
            repo, head, _cached_before = self.candidate_repo(Path(repo_tmp))

            def race_converge(
                temporary_root: Path,
                refs: object,
                *,
                max_iterations: int,
            ) -> tuple[int, str]:
                result = self.fake_converge(
                    temporary_root,
                    refs,
                    max_iterations=max_iterations,
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
            ) -> tuple[int, str]:
                result = self.fake_converge(
                    temporary_root,
                    refs,
                    max_iterations=max_iterations,
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
            (nested / "validator.txt").write_text("dirty\n", encoding="utf-8")
            second = prepare_landing.capture_candidate_snapshot(repo)

            self.assertEqual((".validator/",), first.untracked_paths)
            self.assertEqual(first.index_tree, materialized_tree)
            self.assertEqual(b"", git(isolated, "ls-files", "--stage", "--", ".validator"))
            self.assertTrue((isolated / ".validator" / "validator.txt").is_file())
            self.assertFalse((isolated / ".validator" / "ignored.cache").exists())
            self.assertNotEqual(first.identity(), second.identity())

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
        ) as run_command, patch.object(prepare_landing, "stage_paths"):
            result = prepare_landing.ensure_budget_receipt(
                Path("/candidate"),
                refs,
                budget_reason="final candidate growth",
            )

        self.assertEqual("created", result)
        self.assertTrue(run_command.call_args_list[1].args[0].count("--write-budget-receipt"))
        self.assertTrue(run_command.call_args_list[2].args[0].count("--check"))


if __name__ == "__main__":
    unittest.main()
