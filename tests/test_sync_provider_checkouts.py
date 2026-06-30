from __future__ import annotations

from contextlib import redirect_stderr
from contextlib import redirect_stdout
import io
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

    def test_command_environment_scrubs_unmanaged_provider_envs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            base_env = {
                "AOA_MEMO_ROOT": "/tmp/stale-memo",
                "AOA_SESSION_MEMORY_ROOT": "/tmp/stale-session-memory",
                "PATH": "/usr/bin",
            }

            env = sync_provider_checkouts.command_environment(
                {"AOA_MEMO_ROOT": "/tmp/checked-memo"},
                base_env=base_env,
                repo_root=repo_root,
            )

        self.assertEqual("/tmp/checked-memo", env["AOA_MEMO_ROOT"])
        self.assertEqual("/usr/bin", env["PATH"])
        self.assertEqual(
            (repo_root / ".deps" / ".absent-provider-roots" / "aoa-session-memory")
            .resolve()
            .as_posix(),
            env["AOA_SESSION_MEMORY_ROOT"],
        )
        self.assertFalse(Path(env["AOA_SESSION_MEMORY_ROOT"]).exists())

    def test_command_environment_rejects_existing_absent_provider_sentinel(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            sentinel = repo_root / ".deps" / ".absent-provider-roots" / "aoa-session-memory"
            sentinel.mkdir(parents=True)

            with self.assertRaisesRegex(RuntimeError, "absent provider root sentinel"):
                sync_provider_checkouts.command_environment(
                    {"AOA_MEMO_ROOT": "/tmp/checked-memo"},
                    base_env={},
                    repo_root=repo_root,
                )

    def test_main_check_mode_routes_to_existing_checkout_check(self) -> None:
        with patch.object(sync_provider_checkouts, "sync_or_check") as sync:
            with patch.object(sync_provider_checkouts, "provider_env", return_value={}):
                result = sync_provider_checkouts.main(["--check"])

        self.assertEqual(0, result)
        sync.assert_called_once_with(check=True)

    def test_main_print_env_exports_checked_provider_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            output = io.StringIO()
            with patch.object(sync_provider_checkouts, "REPO_ROOT", repo_root):
                with patch.object(sync_provider_checkouts, "sync_or_check"):
                    with patch.object(
                        sync_provider_checkouts,
                        "provider_env",
                        return_value={"AOA_MEMO_ROOT": "/tmp/checked-memo"},
                    ):
                        with redirect_stdout(output):
                            result = sync_provider_checkouts.main(["--print-env"])

        self.assertEqual(0, result)
        text = output.getvalue()
        self.assertIn("export AOA_MEMO_ROOT=/tmp/checked-memo", text)
        self.assertIn(
            "export AOA_SESSION_MEMORY_ROOT="
            + (repo_root / ".deps" / ".absent-provider-roots" / "aoa-session-memory")
            .resolve()
            .as_posix(),
            text,
        )

    def test_main_print_env_stdout_only_contains_exports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            stdout = io.StringIO()
            stderr = io.StringIO()

            def fake_sync_or_check(*, check: bool) -> list[Path]:
                self.assertTrue(check)
                print(
                    "[provider-checkout] aoa-demo .deps/aoa-demo abc123",
                    file=sync_provider_checkouts.sys.stderr,
                )
                return [repo_root / ".deps" / "aoa-demo"]

            with patch.object(sync_provider_checkouts, "REPO_ROOT", repo_root):
                with patch.object(
                    sync_provider_checkouts,
                    "sync_or_check",
                    side_effect=fake_sync_or_check,
                ):
                    with patch.object(
                        sync_provider_checkouts,
                        "provider_env",
                        return_value={"AOA_MEMO_ROOT": "/tmp/checked-memo"},
                    ):
                        with redirect_stdout(stdout), redirect_stderr(stderr):
                            result = sync_provider_checkouts.main(
                                ["--check", "--print-env"]
                            )

        self.assertEqual(0, result)
        self.assertNotIn("[provider-checkout]", stdout.getvalue())
        self.assertIn("export AOA_MEMO_ROOT=/tmp/checked-memo", stdout.getvalue())
        self.assertIn(
            "[provider-checkout] aoa-demo .deps/aoa-demo abc123",
            stderr.getvalue(),
        )

    def test_sync_or_check_writes_provider_status_to_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            target = repo_root / ".deps" / "aoa-demo"
            target.mkdir(parents=True)
            entry = {
                "repo": "aoa-demo",
                "checkout_path": ".deps/aoa-demo",
                "pinned_ref": "abc123",
            }
            stdout = io.StringIO()
            stderr = io.StringIO()

            with patch.object(
                sync_provider_checkouts,
                "pinned_provider_entries",
                return_value=[entry],
            ):
                with patch.object(
                    sync_provider_checkouts,
                    "check_checkout",
                    return_value=target,
                ):
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        paths = sync_provider_checkouts.sync_or_check(
                            check=True,
                            repo_root=repo_root,
                        )

        self.assertEqual([target], paths)
        self.assertEqual("", stdout.getvalue())
        self.assertIn(
            "[provider-checkout] aoa-demo .deps/aoa-demo abc123",
            stderr.getvalue(),
        )

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
            self.assertLess(
                run.call_args_list.index(
                    call(
                        (
                            "git",
                            "remote",
                            "set-url",
                            "origin",
                            "https://github.com/8Dionysus/aoa-demo.git",
                        ),
                        cwd=target,
                    )
                ),
                run.call_args_list.index(
                    call(("git", "fetch", "--depth", "1", "origin", "abc123"), cwd=target)
                ),
            )
            self.assertLess(
                run.call_args_list.index(call(("git", "clean", "-ffdx"), cwd=target)),
                run.call_args_list.index(
                    call(("git", "checkout", "--force", "--detach", "abc123"), cwd=target)
                ),
            )
            self.assertIn(
                call(("git", "checkout", "--force", "--detach", "abc123"), cwd=target),
                run.call_args_list,
            )

    def test_checkout_path_stays_under_deps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            entry = {"repo": "aoa-demo", "checkout_path": ".deps/aoa-demo"}

            self.assertEqual(
                (repo_root / ".deps" / "aoa-demo").resolve(),
                sync_provider_checkouts.checkout_path(entry, repo_root=repo_root),
            )
            for checkout_path in ("/tmp/aoa-demo", "../aoa-demo", "aoa-demo", ".deps"):
                with self.subTest(checkout_path=checkout_path):
                    with self.assertRaisesRegex(
                        RuntimeError,
                        "checkout_path must (stay|name a provider)",
                    ):
                        sync_provider_checkouts.checkout_path(
                            {"repo": "aoa-demo", "checkout_path": checkout_path},
                            repo_root=repo_root,
                        )

    def test_checkout_path_rejects_symlinked_deps_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            repo_root = temp_root / "repo"
            outside_root = temp_root / "outside"
            repo_root.mkdir()
            outside_root.mkdir()
            (repo_root / ".deps").symlink_to(outside_root, target_is_directory=True)

            with self.assertRaisesRegex(RuntimeError, "repo-local \\.deps"):
                sync_provider_checkouts.checkout_path(
                    {"repo": "aoa-demo", "checkout_path": ".deps/aoa-demo"},
                    repo_root=repo_root,
                )

    def test_checkout_path_rejects_symlinked_provider_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            deps_root = repo_root / ".deps"
            shared_checkout = deps_root / "shared-checkout"
            deps_root.mkdir(parents=True)
            shared_checkout.mkdir()
            (deps_root / "aoa-demo").symlink_to(shared_checkout, target_is_directory=True)

            with self.assertRaisesRegex(RuntimeError, "must not contain symlinks"):
                sync_provider_checkouts.checkout_path(
                    {"repo": "aoa-demo", "checkout_path": ".deps/aoa-demo"},
                    repo_root=repo_root,
                )

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

    def test_checkout_status_includes_ignored_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / ".deps" / "aoa-demo"
            target.mkdir(parents=True)
            with patch.object(sync_provider_checkouts.subprocess, "run") as run:
                run.return_value.stdout = "!! kag/generated.json\n"

                status = sync_provider_checkouts.checkout_status(target)

        self.assertEqual("!! kag/generated.json", status)
        run.assert_called_once()
        self.assertEqual(
            ("git", "status", "--porcelain", "--ignored"),
            run.call_args.args[0],
        )

    def test_check_checkout_rejects_ignored_provider_tree_artifacts(self) -> None:
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
                        return_value="!! kag/generated.json",
                    ):
                        with self.assertRaisesRegex(RuntimeError, "checkout must be clean"):
                            sync_provider_checkouts.check_checkout(
                                entry,
                                repo_root=Path(temp_dir),
                            )


if __name__ == "__main__":
    unittest.main()
