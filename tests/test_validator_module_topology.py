from __future__ import annotations

import ast
import importlib
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATE_KAG_PATH = REPO_ROOT / "scripts" / "validate_kag.py"
VALIDATORS_DIR = REPO_ROOT / "scripts" / "validators"
INVENTORY_PATH = REPO_ROOT / "docs" / "validation" / "validator_inventory.json"
SCRIPT_INVENTORY_PATH = REPO_ROOT / "docs" / "validation" / "script_inventory.json"
TEST_INVENTORY_PATH = REPO_ROOT / "docs" / "testing" / "test_inventory.json"
LANES_PATH = REPO_ROOT / "config" / "validation_lanes.json"

OWNER_MODULES = {
    "scripts/validators/common.py",
    "scripts/validators/generation.py",
    "scripts/validators/expected_contracts.py",
    "scripts/validators/source_refs.py",
    "scripts/validators/schema_surfaces.py",
    "scripts/validators/local_contracts.py",
    "scripts/validators/manifest_contracts.py",
    "scripts/validators/projection_parity.py",
    "scripts/validators/example_contracts.py",
    "scripts/validators/sibling_readiness.py",
    "scripts/validators/orchestrator.py",
}
ADAPTER_MODULES = {
    "scripts/validate_kag.py",
    "scripts/validators/__init__.py",
}
REQUIRED_ENTRY_FIELDS = {
    "path",
    "module_type",
    "function",
    "inputs",
    "outputs",
    "covered_by",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def module_ast(relative_path: str) -> ast.Module:
    return ast.parse((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def defined_names(relative_path: str) -> set[str]:
    tree = module_ast(relative_path)
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def validator_inventory_entries() -> list[dict]:
    return load_json(INVENTORY_PATH)["validator_modules"]


class ValidatorModuleTopologyTests(unittest.TestCase):
    def test_validate_kag_entrypoint_shape(self) -> None:
        text = VALIDATE_KAG_PATH.read_text(encoding="utf-8")
        tree = ast.parse(text)

        self.assertLessEqual(len(text.splitlines()), 12)
        self.assertEqual(set(), defined_names("scripts/validate_kag.py"))
        self.assertIn("raise SystemExit(main())", text)

        imports_validator_package = any(
            isinstance(node, ast.Try)
            and any(
                isinstance(child, ast.ImportFrom)
                and child.module in {"scripts.validators", "validators"}
                for block in (node.body, node.handlers[0].body if node.handlers else [])
                for child in block
            )
            for node in tree.body
        )
        self.assertTrue(imports_validator_package)

    def test_validator_package_reexports_modules(self) -> None:
        text = (VALIDATORS_DIR / "__init__.py").read_text(encoding="utf-8")

        self.assertLessEqual(len(text.splitlines()), 12)
        self.assertEqual(set(), defined_names("scripts/validators/__init__.py"))
        self.assertIn("from .orchestrator import *", text)

    def test_inventory_matches_validator_files(self) -> None:
        inventory = load_json(INVENTORY_PATH)
        entries = inventory["validator_modules"]
        inventory_paths = {entry["path"] for entry in entries}
        discovered_paths = {
            path.relative_to(REPO_ROOT).as_posix()
            for path in VALIDATORS_DIR.glob("*.py")
            if path.name != "__init__.py"
        }

        self.assertEqual("docs/validation/VALIDATOR_TOPOLOGY.md", inventory["owner"])
        self.assertEqual("config/validation_lanes.json", inventory["command_authority"])
        self.assertEqual(OWNER_MODULES, discovered_paths)
        self.assertEqual(OWNER_MODULES | ADAPTER_MODULES, inventory_paths)

        for entry in entries:
            with self.subTest(path=entry["path"]):
                self.assertTrue(REQUIRED_ENTRY_FIELDS <= set(entry))
                self.assertTrue((REPO_ROOT / entry["path"]).is_file())
                self.assertTrue(entry["function"])
                self.assertTrue(entry["inputs"])
                self.assertTrue(entry["outputs"])
                self.assertTrue((REPO_ROOT / entry["covered_by"]).is_file())

    def test_owner_modules_import_cleanly(self) -> None:
        for relative_path in OWNER_MODULES:
            module_name = relative_path.removesuffix(".py").replace("/", ".")
            with self.subTest(module=module_name):
                importlib.import_module(module_name)

    def test_rule_definitions_have_single_module_home(self) -> None:
        seen: dict[str, str] = {}
        duplicates: dict[str, list[str]] = {}

        for relative_path in sorted(OWNER_MODULES):
            for name in defined_names(relative_path):
                if name in seen:
                    duplicates.setdefault(name, [seen[name]]).append(relative_path)
                else:
                    seen[name] = relative_path

        self.assertEqual({}, duplicates)

    def test_function_families_have_expected_homes(self) -> None:
        source_defs = defined_names("scripts/validators/source_refs.py")
        expected_defs = defined_names("scripts/validators/expected_contracts.py")
        manifest_defs = defined_names("scripts/validators/manifest_contracts.py")
        projection_defs = defined_names("scripts/validators/projection_parity.py")
        example_defs = defined_names("scripts/validators/example_contracts.py")

        self.assertIn("repo_root_from_env", expected_defs)
        self.assertTrue(
            {
                "missing_full_cross_repo_roots",
                "resolve_relative_ref",
                "resolve_known_ref",
                "resolve_source_owned_export_ref",
            }
            <= source_defs
        )
        self.assertTrue(
            {
                "validate_technique_lift_manifest",
                "validate_federation_spine_manifest",
                "validate_source_owned_export_dependency_manifest",
            }
            <= manifest_defs
        )
        self.assertTrue(
            {
                "validate_generated_text",
                "validate_technique_lift_pack",
                "validate_federation_spine_pack",
                "validate_counterpart_federation_exposure_review_pack",
            }
            <= projection_defs
        )
        self.assertTrue(
            {
                "validate_bridge_envelope_example",
                "validate_counterpart_consumer_contract_example",
                "validate_federation_kag_export_example",
            }
            <= example_defs
        )

    def test_projection_module_is_marked_as_projection_surface(self) -> None:
        entries_by_path = {entry["path"]: entry for entry in validator_inventory_entries()}
        projection_entry = entries_by_path["scripts/validators/projection_parity.py"]

        self.assertEqual("projection", projection_entry["module_type"])
        self.assertTrue(projection_entry["projection_only"])
        self.assertIn("generated payloads", projection_entry["inputs"])
        self.assertIn("projection parity verdicts", projection_entry["outputs"])

    def test_lane_entrypoints_stay_at_script_level(self) -> None:
        lanes = load_json(LANES_PATH)

        self.assertIn(
            ["python", "scripts/validate_kag.py"],
            lanes["command_sequences"]["source_fast"],
        )
        self.assertIn(
            ["python", "scripts/validate_kag.py"],
            lanes["command_sequences"]["generated_check"],
        )

    def test_script_and_test_inventories_cover_validator_topology(self) -> None:
        script_paths = {
            entry["path"]
            for entry in load_json(SCRIPT_INVENTORY_PATH)["script_surfaces"]
        }
        test_entries = [
            file_entry
            for home in load_json(TEST_INVENTORY_PATH)["homes"]
            for file_entry in home["files"]
        ]
        test_paths = {entry["path"] for entry in test_entries}

        self.assertTrue(OWNER_MODULES | ADAPTER_MODULES <= script_paths)
        self.assertIn("scripts/validators/AGENTS.md", script_paths)
        self.assertIn("tests/test_validator_module_topology.py", test_paths)


if __name__ == "__main__":
    unittest.main()
