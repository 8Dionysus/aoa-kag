from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import call
from unittest.mock import patch

from scripts import sync_provider_checkouts


class SyncProviderCheckoutsTests(unittest.TestCase):
    def test_resolve_command_uses_current_python(self) -> None:
        command = sync_provider_checkouts.resolve_command(("python", "scripts/release_check.py"))

        self.assertEqual(sync_provider_checkouts.sys.executable, command[0])
        self.assertEqual(("scripts/release_check.py",), command[1:])

    def test_main_runs_command_with_provider_env(self) -> None:
        with patch.object(sync_provider_checkouts, "sync_or_check") as sync:
            with patch.object(
                sync_provider_checkouts,
                "provider_env",
                return_value={"AOA_DEMO_ROOT": "/tmp/aoa-demo"},
            ):
                with patch.object(sync_provider_checkouts.subprocess, "run") as run:
                    run.return_value.returncode = 7

                    result = sync_provider_checkouts.main(
                        ["--", "python", "scripts/release_check.py"]
                    )

        self.assertEqual(7, result)
        sync.assert_called_once_with(check=False)
        run.assert_called_once()
        command = run.call_args.args[0]
        self.assertEqual(sync_provider_checkouts.sys.executable, command[0])
        self.assertEqual("scripts/release_check.py", command[1])
        self.assertEqual("/tmp/aoa-demo", run.call_args.kwargs["env"]["AOA_DEMO_ROOT"])

    def test_main_check_mode_routes_to_existing_checkout_check(self) -> None:
        with patch.object(sync_provider_checkouts, "sync_or_check") as sync:
            with patch.object(sync_provider_checkouts, "provider_env", return_value={}):
                result = sync_provider_checkouts.main(["--check"])

        self.assertEqual(0, result)
        sync.assert_called_once_with(check=True)

    def test_sync_checkout_removes_ignored_provider_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / ".deps" / "aoa-demo"
            (target / ".git").mkdir(parents=True)
            entry = {
                "repo": "aoa-demo",
                "github_repository": "8Dionysus/aoa-demo",
                "checkout_path": ".deps/aoa-demo",
                "pinned_ref": "abc123",
            }

            with patch.object(sync_provider_checkouts, "checkout_path", return_value=target):
                with patch.object(sync_provider_checkouts, "run") as run:
                    sync_provider_checkouts.sync_checkout(entry, repo_root=Path(temp_dir))

            self.assertIn(call(("git", "clean", "-ffdx"), cwd=target), run.call_args_list)

    def test_check_checkout_rejects_dirty_provider_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / ".deps" / "aoa-demo"
            (target / ".git").mkdir(parents=True)
            entry = {
                "repo": "aoa-demo",
                "checkout_path": ".deps/aoa-demo",
                "pinned_ref": "abc123",
            }

            with patch.object(sync_provider_checkouts, "checkout_path", return_value=target):
                with patch.object(sync_provider_checkouts, "current_head", return_value="abc123"):
                    with patch.object(
                        sync_provider_checkouts,
                        "checkout_status",
                        return_value="?? kag/generated.json",
                    ):
                        with self.assertRaisesRegex(RuntimeError, "checkout must be clean"):
                            sync_provider_checkouts.check_checkout(
                                entry,
                                repo_root=Path(temp_dir),
                            )


if __name__ == "__main__":
    unittest.main()
