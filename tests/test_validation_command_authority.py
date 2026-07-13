from __future__ import annotations

import json
import re
import subprocess
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scripts import ci_gate, release_check, validation_lanes
from scripts.provider_registry import provider_ci_envs


REPO_ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_COMMAND_BLOCK = re.compile(r"```[^\n]*\n(?P<body>.*?)(?:\n```)", re.DOTALL)
EXECUTABLE_VALIDATION_LINE = re.compile(
    r"(?m)^\s*(?:-\s*)?(?:python(?:\s+-m)?\s+|pytest\b|git\s+(?:status|diff)\b|gh\s+|aoa\s+)"
)
INLINE_EXECUTABLE_VALIDATION_COMMAND = re.compile(
    r"`(?:python(?:\s+-m)?\s+|pytest\b|git\s+(?:status|diff)\b)[^`]+`"
)
CANARY_PROVIDER_ROOT_ENVS = provider_ci_envs()


def command_sequence_from_manifest(name: str) -> tuple[tuple[str, ...], ...]:
    manifest = json.loads(
        (REPO_ROOT / "config" / "validation_lanes.json").read_text(encoding="utf-8")
    )
    return tuple(tuple(command) for command in manifest["command_sequences"][name])


def drift_paths_from_manifest(name: str) -> tuple[str, ...]:
    manifest = json.loads(
        (REPO_ROOT / "config" / "validation_lanes.json").read_text(encoding="utf-8")
    )
    return tuple(manifest["drift_paths"][name])


def provider_ready_repos_from_manifest() -> set[str]:
    manifest = json.loads(
        (REPO_ROOT / "manifests" / "local_kag_readiness.json").read_text(encoding="utf-8")
    )
    return {
        entry["repo"]
        for entry in manifest["repos"]
        if entry["provider_status"] == "provider_ready"
    }


def tracked_markdown_paths() -> tuple[Path, ...]:
    result = subprocess.run(
        ("git", "ls-files", "*.md"),
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(REPO_ROOT / line for line in result.stdout.splitlines() if line)


class ValidationCommandAuthorityTests(unittest.TestCase):
    def test_validation_lanes_manifest_is_loader_authority(self) -> None:
        self.assertEqual(
            REPO_ROOT / "config" / "validation_lanes.json",
            validation_lanes.VALIDATION_LANES_PATH,
        )
        self.assertEqual(
            command_sequence_from_manifest("source_fast"),
            validation_lanes.SOURCE_FAST_COMMAND_SEQUENCE,
        )
        self.assertEqual(
            command_sequence_from_manifest("generated_check"),
            validation_lanes.GENERATED_CHECK_COMMAND_SEQUENCE,
        )
        self.assertEqual(
            command_sequence_from_manifest("release_check"),
            validation_lanes.RELEASE_CHECK_COMMAND_SEQUENCE,
        )
        self.assertEqual(
            command_sequence_from_manifest("compatibility_canary"),
            validation_lanes.COMPATIBILITY_CANARY_COMMAND_SEQUENCE,
        )
        self.assertEqual(
            drift_paths_from_manifest("generated"),
            validation_lanes.GENERATED_DRIFT_PATHS,
        )
        self.assertEqual(
            (
                "git",
                "diff",
                "--binary",
                "--no-ext-diff",
                "--",
                *validation_lanes.GENERATED_DRIFT_PATHS,
            ),
            validation_lanes.GENERATED_DRIFT_SNAPSHOT_COMMAND,
        )

    def test_validation_lanes_api_resolves_lane_ids_to_command_sequences(self) -> None:
        self.assertEqual(
            command_sequence_from_manifest("source_fast"),
            validation_lanes.command_sequence_for_lane("source_fast"),
        )
        self.assertEqual(
            command_sequence_from_manifest("generated_check"),
            validation_lanes.command_sequence_for_lane("generated"),
        )
        self.assertEqual(
            command_sequence_from_manifest("release_check"),
            validation_lanes.command_sequence_for_lane("release"),
        )

        with self.assertRaisesRegex(ValueError, "does not define a command sequence"):
            validation_lanes.command_sequence_for_lane("advisory")
        with self.assertRaisesRegex(ValueError, "unknown lane"):
            validation_lanes.command_sequence_for_lane("missing")

    def test_generated_lanes_rebuild_source_index_after_final_coverage_refresh(self) -> None:
        coverage_command = ("python", "scripts/generate_repo_local_kag_coverage.py")
        coverage_check_command = (
            "python",
            "scripts/generate_repo_local_kag_coverage.py",
            "--check",
        )
        generate_kag_command = ("python", "scripts/generate_kag.py")
        generate_kag_check_command = ("python", "scripts/generate_kag.py", "--check")
        index_command = (
            "python",
            "scripts/generate_repo_local_kag_index.py",
            "--repo-root",
            ".",
            "--output",
            "kag/indexes/source_surface_index.json",
            "--index-family",
        )
        index_check_command = (*index_command, "--check")
        for lane_name in ("generated_check", "compatibility_canary"):
            sequence = command_sequence_from_manifest(lane_name)
            last_coverage = max(
                index for index, command in enumerate(sequence) if command == coverage_command
            )
            last_generate_kag = max(
                index for index, command in enumerate(sequence) if command == generate_kag_command
            )
            last_index = max(
                index for index, command in enumerate(sequence) if command == index_command
            )
            last_coverage_check = max(
                index
                for index, command in enumerate(sequence)
                if command == coverage_check_command
            )
            last_index_check = max(
                index for index, command in enumerate(sequence) if command == index_check_command
            )
            last_check = max(
                index
                for index, command in enumerate(sequence)
                if command == generate_kag_check_command
            )
            self.assertLess(last_coverage, last_generate_kag)
            self.assertLess(last_generate_kag, last_index)
            self.assertLess(last_index, last_coverage_check)
            self.assertLess(last_coverage_check, last_index_check)
            self.assertLess(last_index_check, last_check)
            self.assertLess(last_index, last_check)
            self.assertNotIn(coverage_command, sequence[last_coverage_check + 1 :])
            self.assertNotIn(index_command, sequence[last_index_check + 1 :])
            self.assertNotIn(generate_kag_command, sequence[last_check + 1 :])

    def test_ci_gate_executes_lane_sequences_from_loader(self) -> None:
        with patch.object(ci_gate, "run_sequence") as run_sequence:
            ci_gate.run_source_fast()
            run_sequence.assert_called_once_with(validation_lanes.SOURCE_FAST_COMMAND_SEQUENCE)

        with patch.object(ci_gate, "run_sequence") as run_sequence:
            with patch.object(ci_gate, "capture_command_output", return_value="stable") as capture:
                ci_gate.run_generated()
            run_sequence.assert_called_once_with(validation_lanes.GENERATED_CHECK_COMMAND_SEQUENCE)
            self.assertEqual(
                [
                    (validation_lanes.GENERATED_DRIFT_SNAPSHOT_COMMAND,),
                    (validation_lanes.GENERATED_DRIFT_SNAPSHOT_COMMAND,),
                ],
                [call.args for call in capture.call_args_list],
            )

        with patch.object(ci_gate, "run_command") as run_command:
            ci_gate.run_release()
            run_command.assert_called_once_with(("python", "scripts/release_check.py"))

        with patch.object(ci_gate, "run_sequence") as run_sequence:
            ci_gate.run_compatibility_canary()
            run_sequence.assert_called_once_with(
                validation_lanes.COMPATIBILITY_CANARY_COMMAND_SEQUENCE
            )

    def test_generated_lane_fails_when_projection_snapshot_changes(self) -> None:
        with patch.object(ci_gate, "run_sequence"):
            with patch.object(
                ci_gate,
                "capture_command_output",
                side_effect=("before", "after"),
            ):
                with redirect_stderr(StringIO()):
                    with self.assertRaises(subprocess.CalledProcessError):
                        ci_gate.run_generated()

    def test_release_check_preserves_entrypoint_without_owning_sequence(self) -> None:
        self.assertEqual("release", release_check.RELEASE_LANE_ID)
        self.assertEqual(
            validation_lanes.command_sequence_for_lane("release"),
            release_check.release_lane_commands(),
        )

        release_check_text = (REPO_ROOT / "scripts" / "release_check.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("validation_lanes.command_sequence_for_lane(RELEASE_LANE_ID)", release_check_text)
        self.assertNotIn("COMMANDS =", release_check_text)
        self.assertNotIn('"validate committed KAG surfaces"', release_check_text)
        self.assertNotIn('"generate KAG outputs"', release_check_text)

    def test_workflows_call_lane_entrypoints_not_inline_sequences(self) -> None:
        repo_validation = (
            REPO_ROOT / ".github" / "workflows" / "repo-validation.yml"
        ).read_text(encoding="utf-8")
        canary = (
            REPO_ROOT / ".github" / "workflows" / "compatibility-canary.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("python scripts/release_check.py", repo_validation)
        self.assertNotIn("python scripts/run_tests.py", repo_validation)
        self.assertNotIn("python scripts/run_part_local_checks.py", repo_validation)
        self.assertNotIn("python scripts/validate_kag.py", repo_validation)
        self.assertIn("python scripts/ci_gate.py --mode compatibility-canary", canary)
        self.assertNotIn("python scripts/generate_kag.py", canary)

    def test_repo_local_index_action_routes_to_canonical_builder(self) -> None:
        action = (
            REPO_ROOT
            / ".github"
            / "actions"
            / "repo-local-kag-index"
            / "action.yml"
        ).read_text(encoding="utf-8")
        workflow = (
            REPO_ROOT / ".github" / "workflows" / "repo-validation.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("scripts/generate_repo_local_kag_index.py", action)
        self.assertIn('--repo-root "${{ inputs.repo-root }}"', action)
        self.assertIn('--output "${{ inputs.output }}"', action)
        self.assertIn("--index-family", action)
        self.assertIn("--incremental", action)
        self.assertIn("history-ref:", action)
        self.assertIn("--unshallow", action)
        self.assertIn("AOA_REPO_LOCAL_KAG_HISTORY_REPO", action)
        self.assertIn("AOA_REPO_LOCAL_KAG_HISTORY_REF", action)
        self.assertIn('>> "$GITHUB_ENV"', action)
        self.assertIn('--history-ref "${{ steps.history.outputs.ref }}"', action)
        self.assertIn("--check", action)
        self.assertIn("scripts/validate_repo_local_kag_family.py", action)
        self.assertIn('--source-index "${{ inputs.output }}"', action)
        self.assertIn("uses: ./.github/actions/repo-local-kag-index", workflow)

    def test_compatibility_canary_checks_out_source_ready_provider_roots(self) -> None:
        repo_validation = (
            REPO_ROOT / ".github" / "workflows" / "repo-validation.yml"
        ).read_text(encoding="utf-8")
        canary = (
            REPO_ROOT / ".github" / "workflows" / "compatibility-canary.yml"
        ).read_text(encoding="utf-8")

        expected_sibling_providers = provider_ready_repos_from_manifest() - {"aoa-kag"}
        self.assertEqual(
            expected_sibling_providers,
            set(CANARY_PROVIDER_ROOT_ENVS),
        )
        self.assertEqual(
            len(expected_sibling_providers),
            repo_validation.count("fetch-depth: 0"),
        )
        self.assertEqual(
            len(expected_sibling_providers),
            canary.count("fetch-depth: 0"),
        )
        for repo, env_name in CANARY_PROVIDER_ROOT_ENVS.items():
            with self.subTest(repo=repo):
                self.assertIn(f"{env_name}: ${{{{ github.workspace }}}}/.deps/{repo}", repo_validation)
                self.assertIn(f"{env_name}: ${{{{ github.workspace }}}}/.deps/{repo}", canary)
                self.assertIn(f"repository: 8Dionysus/{repo}", repo_validation)
                self.assertIn(f"path: .deps/{repo}", repo_validation)
                self.assertIn(f"repository: 8Dionysus/{repo}", canary)
                self.assertIn(f"path: .deps/{repo}", canary)

    def test_active_docs_route_to_lane_ids_instead_of_full_sequences(self) -> None:
        active_docs = (
            "AGENTS.md",
            ".github/AGENTS.md",
            "config/AGENTS.md",
            "scripts/AGENTS.md",
            "tests/AGENTS.md",
            "docs/RELEASING.md",
            "docs/validation/COMMAND_AUTHORITY.md",
        )
        forbidden_sequence_markers = (
            "scripts/run_tests.py\npython scripts/run_part_local_checks.py",
            "scripts/run_part_local_checks.py\npython scripts/validate_nested_agents.py",
            "scripts/validate_kag.py\npython scripts/generate_kag.py",
            "scripts/generate_decision_indexes.py --check\npython scripts/validate_decision_records.py",
        )

        for relative_path in active_docs:
            text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
            with self.subTest(surface=relative_path):
                self.assertRegex(text, r"(source-fast|generated|release|validation_lanes|COMMAND_AUTHORITY)")
            for marker in forbidden_sequence_markers:
                with self.subTest(surface=relative_path, marker=marker):
                    self.assertNotIn(marker, text)

    def test_non_agent_markdown_does_not_embed_validation_command_blocks(self) -> None:
        offenders: list[str] = []
        for path in tracked_markdown_paths():
            relative_path = path.relative_to(REPO_ROOT).as_posix()
            if relative_path.endswith("AGENTS.md"):
                continue
            if relative_path == "docs/validation/COMMAND_AUTHORITY.md":
                continue

            text = path.read_text(encoding="utf-8")
            for match in MARKDOWN_COMMAND_BLOCK.finditer(text):
                if not EXECUTABLE_VALIDATION_LINE.search(match.group("body")):
                    continue
                line_number = text[: match.start()].count("\n") + 1
                offenders.append(f"{relative_path}:{line_number}")

        self.assertEqual([], offenders)

    def test_non_agent_markdown_does_not_embed_inline_validation_commands(self) -> None:
        offenders: list[str] = []
        for path in tracked_markdown_paths():
            relative_path = path.relative_to(REPO_ROOT).as_posix()
            if relative_path.endswith("AGENTS.md"):
                continue
            if relative_path == "docs/validation/COMMAND_AUTHORITY.md":
                continue

            text = path.read_text(encoding="utf-8")
            for match in INLINE_EXECUTABLE_VALIDATION_COMMAND.finditer(text):
                line_number = text[: match.start()].count("\n") + 1
                offenders.append(f"{relative_path}:{line_number}")

        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()
