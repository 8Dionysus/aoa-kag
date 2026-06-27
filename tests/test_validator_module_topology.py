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
    "scripts/validators/expected/core.py",
    "scripts/validators/expected/registry_contracts.py",
    "scripts/validators/expected/governance_contracts.py",
    "scripts/validators/expected/recurrence_contracts.py",
    "scripts/validators/expected/technique_contracts.py",
    "scripts/validators/expected/tos_contracts.py",
    "scripts/validators/expected/handoff_contracts.py",
    "scripts/validators/expected/federation_contracts.py",
    "scripts/validators/expected/cross_source_contracts.py",
    "scripts/validators/expected/consumer_contracts.py",
    "scripts/validators/expected/registry_surface_inputs.py",
    "scripts/validators/expected/docs_contracts.py",
    "scripts/validators/source_refs.py",
    "scripts/validators/schema_surfaces.py",
    "scripts/validators/local_contracts.py",
    "scripts/validators/local_kag_subtree.py",
    "scripts/validators/manifests/technique_lift.py",
    "scripts/validators/manifests/tos_text_chunk_map.py",
    "scripts/validators/manifests/tos_retrieval_axis.py",
    "scripts/validators/manifests/tos_zarathustra_route.py",
    "scripts/validators/manifests/tos_zarathustra_route_retrieval.py",
    "scripts/validators/manifests/reasoning_handoff.py",
    "scripts/validators/manifests/return_regrounding.py",
    "scripts/validators/manifests/governance.py",
    "scripts/validators/manifests/source_owned_export.py",
    "scripts/validators/manifests/federation_export_registry.py",
    "scripts/validators/manifests/federation_spine.py",
    "scripts/validators/manifests/cross_source_node_projection.py",
    "scripts/validators/manifests/tiny_consumer_bundle.py",
    "scripts/validators/manifests/counterpart_federation_exposure_review.py",
    "scripts/validators/examples/tos_examples.py",
    "scripts/validators/examples/recurrence_examples.py",
    "scripts/validators/examples/governance_examples.py",
    "scripts/validators/examples/federation_examples.py",
    "scripts/validators/examples/cross_source_examples.py",
    "scripts/validators/examples/tiny_consumer_bundle_examples.py",
    "scripts/validators/examples/exposure_review_examples.py",
    "scripts/validators/examples/bridge_examples.py",
    "scripts/validators/examples/counterpart_examples.py",
    "scripts/validators/examples/reasoning_handoff_examples.py",
    "scripts/validators/sibling_readiness.py",
    "scripts/validators/orchestration/static_surfaces.py",
    "scripts/validators/orchestration/manifests.py",
    "scripts/validators/orchestration/expected_payloads.py",
    "scripts/validators/orchestration/generated_text.py",
    "scripts/validators/orchestration/generated_structures.py",
    "scripts/validators/orchestration/examples.py",
    "scripts/validators/orchestration/status.py",
    "scripts/validators/orchestration/runner.py",
    "scripts/validators/projection/registry.py",
    "scripts/validators/projection/tos_text_chunk_map.py",
    "scripts/validators/projection/tos_retrieval_axis.py",
    "scripts/validators/projection/tos_zarathustra_route.py",
    "scripts/validators/projection/tos_zarathustra_route_retrieval.py",
    "scripts/validators/projection/reasoning_handoff.py",
    "scripts/validators/projection/return_regrounding.py",
    "scripts/validators/projection/governance.py",
    "scripts/validators/projection/federation_export_registry.py",
    "scripts/validators/projection/federation_spine.py",
    "scripts/validators/projection/cross_source_node_projection.py",
    "scripts/validators/projection/tiny_consumer_bundle.py",
    "scripts/validators/projection/counterpart_federation_exposure_review.py",
    "scripts/validators/projection/technique.py",
}
ADAPTER_MODULES = {
    "scripts/validate_kag.py",
    "scripts/validators/__init__.py",
    "scripts/validators/expected_contracts.py",
    "scripts/validators/expected/__init__.py",
    "scripts/validators/manifest_contracts.py",
    "scripts/validators/manifests/__init__.py",
    "scripts/validators/projection_parity.py",
    "scripts/validators/projection/__init__.py",
    "scripts/validators/example_contracts.py",
    "scripts/validators/examples/__init__.py",
    "scripts/validators/orchestrator.py",
    "scripts/validators/orchestration/__init__.py",
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

    def test_projection_parity_facade_shape(self) -> None:
        text = (VALIDATORS_DIR / "projection_parity.py").read_text(encoding="utf-8")

        self.assertLessEqual(len(text.splitlines()), 8)
        self.assertEqual(set(), defined_names("scripts/validators/projection_parity.py"))
        self.assertIn("from .projection import *", text)

    def test_manifest_contracts_facade_shape(self) -> None:
        text = (VALIDATORS_DIR / "manifest_contracts.py").read_text(encoding="utf-8")

        self.assertLessEqual(len(text.splitlines()), 8)
        self.assertEqual(set(), defined_names("scripts/validators/manifest_contracts.py"))
        self.assertIn("from .manifests import *", text)

    def test_expected_contracts_facade_shape(self) -> None:
        text = (VALIDATORS_DIR / "expected_contracts.py").read_text(encoding="utf-8")

        self.assertLessEqual(len(text.splitlines()), 8)
        self.assertEqual(set(), defined_names("scripts/validators/expected_contracts.py"))
        self.assertIn("from .expected import *", text)

    def test_example_contracts_facade_shape(self) -> None:
        text = (VALIDATORS_DIR / "example_contracts.py").read_text(encoding="utf-8")

        self.assertLessEqual(len(text.splitlines()), 8)
        self.assertEqual(set(), defined_names("scripts/validators/example_contracts.py"))
        self.assertIn("from .examples import *", text)

    def test_orchestrator_facade_shape(self) -> None:
        text = (VALIDATORS_DIR / "orchestrator.py").read_text(encoding="utf-8")

        self.assertLessEqual(len(text.splitlines()), 8)
        self.assertEqual(set(), defined_names("scripts/validators/orchestrator.py"))
        self.assertIn("from .orchestration import *", text)

    def test_inventory_matches_validator_files(self) -> None:
        inventory = load_json(INVENTORY_PATH)
        entries = inventory["validator_modules"]
        inventory_paths = {entry["path"] for entry in entries}
        discovered_paths = {
            path.relative_to(REPO_ROOT).as_posix()
            for path in VALIDATORS_DIR.rglob("*.py")
            if path.name != "__init__.py"
        }
        adapter_paths = {
            path
            for path in ADAPTER_MODULES
            if path != "scripts/validate_kag.py" and not path.endswith("__init__.py")
        }

        self.assertEqual("docs/validation/VALIDATOR_TOPOLOGY.md", inventory["owner"])
        self.assertEqual("config/validation_lanes.json", inventory["command_authority"])
        self.assertEqual(OWNER_MODULES | adapter_paths, discovered_paths)
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
        expected_core_defs = defined_names("scripts/validators/expected/core.py")
        manifest_technique_defs = defined_names("scripts/validators/manifests/technique_lift.py")
        manifest_federation_spine_defs = defined_names(
            "scripts/validators/manifests/federation_spine.py"
        )
        manifest_source_owned_export_defs = defined_names(
            "scripts/validators/manifests/source_owned_export.py"
        )
        projection_registry_defs = defined_names("scripts/validators/projection/registry.py")
        projection_tos_text_chunk_map_defs = defined_names(
            "scripts/validators/projection/tos_text_chunk_map.py"
        )
        projection_tos_retrieval_axis_defs = defined_names(
            "scripts/validators/projection/tos_retrieval_axis.py"
        )
        projection_tos_route_defs = defined_names(
            "scripts/validators/projection/tos_zarathustra_route.py"
        )
        projection_tos_route_retrieval_defs = defined_names(
            "scripts/validators/projection/tos_zarathustra_route_retrieval.py"
        )
        projection_reasoning_handoff_defs = defined_names(
            "scripts/validators/projection/reasoning_handoff.py"
        )
        projection_return_regrounding_defs = defined_names(
            "scripts/validators/projection/return_regrounding.py"
        )
        projection_governance_defs = defined_names("scripts/validators/projection/governance.py")
        projection_federation_export_defs = defined_names(
            "scripts/validators/projection/federation_export_registry.py"
        )
        projection_federation_spine_defs = defined_names(
            "scripts/validators/projection/federation_spine.py"
        )
        projection_cross_source_defs = defined_names(
            "scripts/validators/projection/cross_source_node_projection.py"
        )
        projection_tiny_consumer_defs = defined_names(
            "scripts/validators/projection/tiny_consumer_bundle.py"
        )
        projection_exposure_review_defs = defined_names(
            "scripts/validators/projection/counterpart_federation_exposure_review.py"
        )
        projection_technique_defs = defined_names("scripts/validators/projection/technique.py")
        example_bridge_defs = defined_names("scripts/validators/examples/bridge_examples.py")
        example_counterpart_defs = defined_names(
            "scripts/validators/examples/counterpart_examples.py"
        )
        example_federation_defs = defined_names("scripts/validators/examples/federation_examples.py")

        self.assertIn("repo_root_from_env", expected_core_defs)
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
            }
            <= manifest_technique_defs
        )
        self.assertIn("validate_federation_spine_manifest", manifest_federation_spine_defs)
        self.assertIn(
            "validate_source_owned_export_dependency_manifest",
            manifest_source_owned_export_defs,
        )
        self.assertIn("validate_registry_payload", projection_registry_defs)
        self.assertIn(
            "validate_tos_text_chunk_map_pack",
            projection_tos_text_chunk_map_defs,
        )
        self.assertIn(
            "validate_tos_retrieval_axis_pack",
            projection_tos_retrieval_axis_defs,
        )
        self.assertIn("validate_tos_zarathustra_route_pack", projection_tos_route_defs)
        self.assertIn(
            "validate_tos_zarathustra_route_retrieval_pack",
            projection_tos_route_retrieval_defs,
        )
        self.assertIn(
            "validate_reasoning_handoff_pack",
            projection_reasoning_handoff_defs,
        )
        self.assertIn(
            "validate_return_regrounding_pack",
            projection_return_regrounding_defs,
        )
        self.assertIn("validate_kag_maturity_governance_pack", projection_governance_defs)
        self.assertIn(
            "validate_federation_export_registry_pack",
            projection_federation_export_defs,
        )
        self.assertIn("validate_federation_spine_pack", projection_federation_spine_defs)
        self.assertIn(
            "validate_cross_source_node_projection_pack",
            projection_cross_source_defs,
        )
        self.assertIn(
            "validate_tiny_consumer_bundle_pack",
            projection_tiny_consumer_defs,
        )
        self.assertIn(
            "validate_counterpart_federation_exposure_review_pack",
            projection_exposure_review_defs,
        )
        self.assertTrue(
            {"validate_generated_text", "validate_technique_lift_pack"}
            <= projection_technique_defs
        )
        self.assertTrue(
            {
                "validate_bridge_envelope_example",
            }
            <= example_bridge_defs
        )
        self.assertTrue(
            {
                "validate_counterpart_consumer_contract_example",
            }
            <= example_counterpart_defs
        )
        self.assertTrue(
            {
                "validate_federation_kag_export_example",
            }
            <= example_federation_defs
        )

    def test_projection_module_is_marked_as_projection_surface(self) -> None:
        entries_by_path = {entry["path"]: entry for entry in validator_inventory_entries()}
        projection_entry = entries_by_path["scripts/validators/projection_parity.py"]
        projection_leaf_entries = [
            entry
            for path, entry in entries_by_path.items()
            if path.startswith("scripts/validators/projection/") and not path.endswith("__init__.py")
        ]

        self.assertEqual("projection_facade", projection_entry["module_type"])
        self.assertTrue(projection_entry["projection_only"])
        self.assertIn("scripts/validators/projection package", projection_entry["inputs"])
        self.assertTrue(projection_leaf_entries)
        for entry in projection_leaf_entries:
            with self.subTest(path=entry["path"]):
                self.assertTrue(entry["module_type"].startswith("projection_"))
                self.assertTrue(entry["inputs"])
                self.assertTrue(entry["outputs"])

    def test_generation_validator_port_routes_to_generation_package(self) -> None:
        entries_by_path = {entry["path"]: entry for entry in validator_inventory_entries()}
        generation_entry = entries_by_path["scripts/validators/generation.py"]

        self.assertEqual("generation_port", generation_entry["module_type"])
        self.assertIn("scripts/generation package", generation_entry["inputs"])
        self.assertIn("scripts/kag_generation.py compatibility facade", generation_entry["inputs"])

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
