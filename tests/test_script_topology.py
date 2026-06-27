from __future__ import annotations

import importlib
import json
import runpy
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from scripts import run_part_local_checks, validation_lanes


REPO_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = REPO_ROOT / "docs" / "validation" / "script_inventory.json"

ALLOWED_ORGAN_LANES = {
    "source/topology",
    "projection/generated",
    "capability/security contract",
    "release/ci-lane",
    "mechanics/root-topology",
    "mechanics/part-local",
}

ALLOWED_VALIDATION_LANES = {
    "source_fast",
    "generated",
    "release",
    "compatibility_canary",
    "advisory",
}

REQUIRED_ENTRY_FIELDS = {
    "path",
    "family",
    "organ_lane",
    "owner_surface",
    "source_truth",
    "reads",
    "writes",
    "side_effects",
    "validation_lane",
    "ci_inclusion",
    "test_target",
    "disposition",
}
EXCLUDED_DISCOVERY_PARTS = {".deps", ".git", "__pycache__", "dist"}


def load_inventory() -> dict:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def inventory_entries() -> list[dict]:
    return load_inventory()["script_surfaces"]


def inventory_paths() -> set[str]:
    return {entry["path"] for entry in inventory_entries()}


def discovered_script_surfaces(repo_root: Path = REPO_ROOT) -> set[str]:
    paths: set[str] = set()
    for path in repo_root.rglob("*"):
        relative_path = path.relative_to(repo_root)
        if EXCLUDED_DISCOVERY_PARTS.intersection(relative_path.parts):
            continue
        if (
            path.is_file()
            and "/scripts/" in f"/{relative_path.as_posix()}"
            and path.suffix != ".pyc"
        ):
            paths.add(relative_path.as_posix())
    return paths


def command_script_paths(commands: tuple[tuple[str, ...], ...]) -> set[str]:
    paths: set[str] = set()
    for command in commands:
        for part in command:
            if part.endswith(".py") and "/" in part:
                paths.add(part)
    return paths


def all_lane_command_script_paths() -> set[str]:
    commands = (
        validation_lanes.SOURCE_FAST_COMMAND_SEQUENCE
        + validation_lanes.GENERATED_CHECK_COMMAND_SEQUENCE
        + validation_lanes.RELEASE_CHECK_COMMAND_SEQUENCE
        + validation_lanes.COMPATIBILITY_CANARY_COMMAND_SEQUENCE
    )
    return command_script_paths(commands)


def discovered_part_local_check_scripts() -> set[str]:
    return {
        path.relative_to(REPO_ROOT).as_posix()
        for path in run_part_local_checks.discovered_part_local_scripts()
    }


@contextmanager
def import_path_for(script_path: Path):
    old_path = list(sys.path)
    sys.path.insert(0, str(script_path.parent))
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    sys.path.insert(0, str(REPO_ROOT))
    try:
        yield
    finally:
        sys.path[:] = old_path


class ScriptTopologyTests(unittest.TestCase):
    def test_script_inventory_covers_every_active_script_surface(self) -> None:
        inventory = load_inventory()
        entries = inventory["script_surfaces"]
        paths = [entry["path"] for entry in entries]

        self.assertEqual("docs/validation/SCRIPT_TOPOLOGY.md", inventory["owner"])
        self.assertEqual("config/validation_lanes.json", inventory["command_authority"])
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(discovered_script_surfaces(), set(paths))

    def test_script_discovery_ignores_dependency_checkouts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            local_script = repo_root / "scripts" / "local.py"
            dependency_script = repo_root / ".deps" / "aoa-memo" / "scripts" / "memo.py"
            dist_script = repo_root / "dist" / "artifact" / "scripts" / "copied.py"
            local_script.parent.mkdir(parents=True)
            dependency_script.parent.mkdir(parents=True)
            dist_script.parent.mkdir(parents=True)
            local_script.write_text("", encoding="utf-8")
            dependency_script.write_text("", encoding="utf-8")
            dist_script.write_text("", encoding="utf-8")

            self.assertEqual({"scripts/local.py"}, discovered_script_surfaces(repo_root))

    def test_script_inventory_entries_are_complete_and_owner_routed(self) -> None:
        for entry in inventory_entries():
            with self.subTest(path=entry.get("path")):
                self.assertEqual(REQUIRED_ENTRY_FIELDS, set(entry))
                self.assertIn(entry["organ_lane"], ALLOWED_ORGAN_LANES)
                self.assertIn(entry["validation_lane"], ALLOWED_VALIDATION_LANES)
                self.assertEqual("keep", entry["disposition"])
                self.assertTrue((REPO_ROOT / entry["path"]).is_file())
                self.assertTrue((REPO_ROOT / entry["owner_surface"]).exists())
                self.assertTrue((REPO_ROOT / entry["test_target"]).exists())
                self.assertIsInstance(entry["source_truth"], list)
                self.assertTrue(entry["source_truth"])
                self.assertIsInstance(entry["reads"], list)
                self.assertTrue(entry["reads"])
                self.assertIsInstance(entry["writes"], list)
                self.assertIsInstance(entry["side_effects"], str)
                self.assertTrue(entry["ci_inclusion"])

    def test_script_families_have_function_groups(self) -> None:
        inventory = load_inventory()
        groups = inventory.get("function_groups", {})
        grouped_families = {
            family for families in groups.values() for family in families
        }
        inventory_families = {entry["family"] for entry in inventory_entries()}

        self.assertTrue(groups)
        self.assertEqual(inventory_families, grouped_families)

    def test_generation_package_surfaces_are_owner_routed(self) -> None:
        expected_paths = {
            "scripts/generation/AGENTS.md",
            "scripts/generation/__init__.py",
            "scripts/generation/common.py",
            "scripts/generation/consumer.py",
            "scripts/generation/context.py",
            "scripts/generation/federation.py",
            "scripts/generation/governance.py",
            "scripts/generation/handoff.py",
            "scripts/generation/markdown.py",
            "scripts/generation/provider_map.py",
            "scripts/generation/registry.py",
            "scripts/generation/regrounding.py",
            "scripts/generation/source_refs.py",
            "scripts/generation/technique.py",
            "scripts/generation/tos.py",
            "scripts/generation/writer.py",
        }
        entries_by_path = {entry["path"]: entry for entry in inventory_entries()}

        self.assertEqual(
            expected_paths,
            {
                path
                for path in entries_by_path
                if path.startswith("scripts/generation/")
            },
        )
        for path in expected_paths - {"scripts/generation/AGENTS.md"}:
            with self.subTest(path=path):
                self.assertEqual(
                    "scripts/generation/AGENTS.md",
                    entries_by_path[path]["owner_surface"],
                )
                self.assertEqual("projection/generated", entries_by_path[path]["organ_lane"])

        self.assertEqual(
            "script_route_card",
            entries_by_path["scripts/generation/AGENTS.md"]["family"],
        )

    def test_lane_commands_reference_inventoried_scripts_not_hidden_commands(self) -> None:
        command_paths = all_lane_command_script_paths()

        self.assertTrue(command_paths)
        self.assertTrue(command_paths <= inventory_paths())

        source_fast_paths = command_script_paths(validation_lanes.SOURCE_FAST_COMMAND_SEQUENCE)
        self.assertNotIn("scripts/release_check.py", source_fast_paths)
        self.assertNotIn("scripts/ci_gate.py", source_fast_paths)
        self.assertNotIn("scripts/generate_kag.py", source_fast_paths)
        self.assertIn("scripts/run_part_local_checks.py", source_fast_paths)

    def test_part_local_check_runner_covers_part_local_scripts(self) -> None:
        part_local_inventory_paths = {
            entry["path"]
            for entry in inventory_entries()
            if entry["organ_lane"] == "mechanics/part-local"
            and entry["path"].startswith("mechanics/")
            and entry["path"].endswith(".py")
        }
        command_paths = {
            part
            for command in run_part_local_checks.coverage_commands()
            for part in command
            if part.endswith(".py")
        }
        build_commands = [
            command
            for command in run_part_local_checks.coverage_commands()
            if command[1].split("/")[-1].startswith("build_")
        ]

        self.assertEqual(part_local_inventory_paths, discovered_part_local_check_scripts())
        self.assertEqual(part_local_inventory_paths, command_paths)
        self.assertTrue(build_commands)
        for command in build_commands:
            self.assertEqual("--check", command[-1])

    def test_side_effect_boundaries_are_visible(self) -> None:
        for entry in inventory_entries():
            path = entry["path"]
            with self.subTest(path=path):
                if entry["writes"]:
                    self.assertNotIn("validation output only", entry["side_effects"])
                if entry["validation_lane"] == "source_fast" and entry["writes"]:
                    self.assertIn("--check", entry["ci_inclusion"])
                if entry["family"] == "projection_validator":
                    self.assertEqual([], entry["writes"])
                    self.assertIn("validation", entry["side_effects"])

    def test_python_scripts_import_without_running_main(self) -> None:
        for entry in inventory_entries():
            path = entry["path"]
            if not path.endswith(".py"):
                continue
            script_path = REPO_ROOT / path
            with self.subTest(path=path):
                with import_path_for(script_path):
                    if path.startswith("scripts/"):
                        module_name = path.removesuffix(".py").replace("/", ".")
                        try:
                            importlib.import_module(module_name)
                        except ModuleNotFoundError:
                            runpy.run_path(
                                str(script_path),
                                run_name=f"__script_inventory_smoke__:{path}",
                            )


if __name__ == "__main__":
    unittest.main()
