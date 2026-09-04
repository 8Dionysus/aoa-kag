from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import prepare_owner_landing as PREPARE


def git(repo_root: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ("git", *args),
        cwd=repo_root,
        input=input_bytes,
        check=True,
        capture_output=True,
    ).stdout


class PrepareOwnerLandingTests(unittest.TestCase):
    def make_repo(self, root: Path) -> Path:
        repo = root / "owner"
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "test@example.invalid")
        git(repo, "config", "user.name", "Owner Prepare Test")
        (repo / "source.txt").write_text("base\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "base")
        return repo

    @staticmethod
    def fake_generate(
        repo_root: Path,
        *,
        output: str,
        refs: object,
        budget_reason: str | None,
    ) -> str:
        assert output == PREPARE.DEFAULT_OUTPUT
        assert refs is not None
        assert budget_reason is None
        shard_dir = repo_root / "kag" / "indexes" / "shards"
        shard_dir.mkdir(parents=True)
        (repo_root / "kag" / "indexes" / "index_family.manifest.json").write_text(
            '{"prepared":true}\n', encoding="utf-8"
        )
        (shard_dir / "records.jsonl").write_text("{}\n", encoding="utf-8")
        git(repo_root, "add", "kag/indexes")
        return "not_required"

    @staticmethod
    def green_gate(**_kwargs: object) -> tuple[int, dict[str, object]]:
        return 0, {
            "schema_version": "aoa-kag-owner-family-gate-receipt-v1",
            "verdict": "verified",
        }

    def run_prepare(self, repo: Path, *, mode: str) -> tuple[int, dict[str, object]]:
        with (
            mock.patch.object(PREPARE, "generate_owner_family", side_effect=self.fake_generate),
            mock.patch.object(PREPARE.owner_gate, "run_gate", side_effect=self.green_gate),
        ):
            return PREPARE.prepare_owner_landing(
                repo,
                mode=mode,
                output=PREPARE.DEFAULT_OUTPUT,
                history_ref="HEAD",
                event_history_ref="HEAD",
                budget_base_ref="HEAD",
                budget_reason=None,
                jobs=3,
                temp_root=None,
            )

    def test_check_reports_drift_without_changing_caller_or_index(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = self.make_repo(Path(raw))
            (repo / "source.txt").write_text("candidate\n", encoding="utf-8")
            git(repo, "add", "source.txt")
            cached_before = git(repo, "diff", "--cached", "--binary")

            code, receipt = self.run_prepare(repo, mode="check")

            self.assertEqual(1, code)
            self.assertEqual("drift", receipt["verdict"])
            self.assertFalse((repo / "kag").exists())
            self.assertEqual(cached_before, git(repo, "diff", "--cached", "--binary"))

    def test_apply_updates_only_generated_worktree_paths_and_preserves_index(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = self.make_repo(Path(raw))
            (repo / "source.txt").write_text("candidate\n", encoding="utf-8")
            git(repo, "add", "source.txt")
            cached_before = git(repo, "diff", "--cached", "--binary")

            code, receipt = self.run_prepare(repo, mode="apply")

            self.assertEqual(0, code)
            self.assertEqual("prepared", receipt["verdict"])
            self.assertTrue((repo / "kag" / "indexes" / "index_family.manifest.json").is_file())
            self.assertEqual(cached_before, git(repo, "diff", "--cached", "--binary"))
            self.assertEqual(
                [
                    "kag/indexes/index_family.manifest.json",
                    "kag/indexes/shards/records.jsonl",
                ],
                receipt["generated_patch"]["changed_paths"],
            )

    def test_output_scope_rejects_non_kag_changes(self) -> None:
        with self.assertRaises(PREPARE.isolation.PreparationFailure) as raised:
            PREPARE.require_owner_output_scope(("README.md", "kag/indexes/shards/a.jsonl"))
        self.assertEqual("preparation_output_scope_violation", raised.exception.failure_type)

    def test_stage_outputs_skips_absent_untracked_budget_receipt_directory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = self.make_repo(Path(raw))
            shard_dir = repo / "kag" / "indexes" / "shards"
            shard_dir.mkdir(parents=True)
            for name in (
                "artifact_locators.json",
                "corpus.manifest.json",
                "hot_profile.json",
            ):
                (repo / "kag" / "indexes" / name).write_text(
                    '{"prepared":true}\n', encoding="utf-8"
                )
            (repo / "kag" / "indexes" / "index_family.manifest.json").write_text(
                '{"prepared":true}\n', encoding="utf-8"
            )
            (shard_dir / "records.jsonl").write_text("{}\n", encoding="utf-8")

            PREPARE.stage_owner_outputs(repo)

            staged = git(repo, "diff", "--cached", "--name-only").decode().splitlines()
            self.assertEqual(
                [
                    "kag/indexes/artifact_locators.json",
                    "kag/indexes/corpus.manifest.json",
                    "kag/indexes/hot_profile.json",
                    "kag/indexes/index_family.manifest.json",
                    "kag/indexes/shards/records.jsonl",
                ],
                staged,
            )
            self.assertFalse((repo / "kag" / "receipts" / "index_family_budget").exists())

    def test_generator_command_preserves_exact_refs_and_budget_authority(self) -> None:
        refs = PREPARE.isolation.ResolvedRefs("history", "events", "budget")
        command = PREPARE.generator_command(
            repo_root=Path("/tmp/owner"),
            output=PREPARE.DEFAULT_OUTPUT,
            refs=refs,
            check=True,
        )
        self.assertIn("--portable-family", command)
        self.assertIn("--check", command)
        self.assertEqual("history", command[command.index("--history-ref") + 1])
        self.assertEqual("events", command[command.index("--event-history-ref") + 1])
        self.assertEqual("budget", command[command.index("--budget-base-ref") + 1])


if __name__ == "__main__":
    unittest.main()
