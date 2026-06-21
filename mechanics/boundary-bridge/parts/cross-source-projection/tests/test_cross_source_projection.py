from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import kag_generation
import validate_kag


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def registry_surfaces() -> dict[str, dict[str, object]]:
    return validate_kag.validate_registry_payload(
        validate_kag.read_json(validate_kag.REGISTRY_MANIFEST_PATH),
        label="registry manifest",
    )


class CrossSourceProjectionTests(unittest.TestCase):
    def patched_read_json(self, overrides: dict[Path, object]):
        original = validate_kag.read_json
        normalized = {Path(path).resolve(): copy.deepcopy(payload) for path, payload in overrides.items()}

        def side_effect(path: Path) -> object:
            resolved = Path(path).resolve()
            if resolved in normalized:
                return copy.deepcopy(normalized[resolved])
            return original(path)

        return patch.object(validate_kag, "read_json", side_effect=side_effect)

    def patched_generation_read_json(self, overrides: dict[Path, object]):
        original = kag_generation.read_json
        normalized = {Path(path).resolve(): copy.deepcopy(payload) for path, payload in overrides.items()}

        def side_effect(path: Path) -> object:
            resolved = Path(path).resolve()
            if resolved in normalized:
                return copy.deepcopy(normalized[resolved])
            return original(path)

        return patch.object(kag_generation, "read_json", side_effect=side_effect)

    def dependencies(self) -> dict[tuple[str, str], dict[str, object]]:
        return validate_kag.validate_source_owned_export_dependency_manifest(
            registry_surfaces()
        )

    def test_current_cross_source_projection_contract_validates(self) -> None:
        surfaces = registry_surfaces()
        dependencies = self.dependencies()
        payload = kag_generation.build_cross_source_node_projection_payload(
            kag_generation.build_registry_payload()
        )

        validate_kag.validate_cross_source_node_projection_manifest(
            surfaces,
            dependencies,
        )
        validate_kag.validate_cross_source_node_projection_pack(payload, surfaces, payload)
        validate_kag.validate_cross_source_node_projection_example(payload)
        self.assertEqual(
            payload,
            load_json(kag_generation.CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATH),
        )

    def test_projection_pairings_failures_are_pairing_specific(self) -> None:
        surfaces = registry_surfaces()
        dependencies = self.dependencies()
        base_manifest = load_json(validate_kag.CROSS_SOURCE_NODE_PROJECTION_MANIFEST_PATH)
        assert isinstance(base_manifest, dict)

        missing_pairings = copy.deepcopy(base_manifest)
        missing_pairings.pop("projection_pairings", None)
        duplicate_pairings = copy.deepcopy(base_manifest)
        duplicate_pairings["projection_pairings"].append(
            copy.deepcopy(duplicate_pairings["projection_pairings"][0])
        )

        for label, manifest_override in (
            ("missing", missing_pairings),
            ("duplicate", duplicate_pairings),
        ):
            with self.subTest(case=label):
                with self.patched_read_json(
                    {validate_kag.CROSS_SOURCE_NODE_PROJECTION_MANIFEST_PATH: manifest_override}
                ):
                    with self.assertRaises(validate_kag.ValidationError) as context:
                        validate_kag.validate_cross_source_node_projection_manifest(
                            surfaces,
                            dependencies,
                        )
                self.assertIn("projection_pairings", str(context.exception))

    def test_projection_pairings_generator_failures_are_pairing_specific(self) -> None:
        base_manifest = load_json(kag_generation.CROSS_SOURCE_NODE_PROJECTION_MANIFEST_PATH)
        assert isinstance(base_manifest, dict)

        missing_pairings = copy.deepcopy(base_manifest)
        missing_pairings.pop("projection_pairings", None)
        duplicate_pairings = copy.deepcopy(base_manifest)
        duplicate_pairings["projection_pairings"].append(
            copy.deepcopy(duplicate_pairings["projection_pairings"][0])
        )

        for label, manifest_override in (
            ("missing", missing_pairings),
            ("duplicate", duplicate_pairings),
        ):
            with self.subTest(case=label):
                with self.patched_generation_read_json(
                    {kag_generation.CROSS_SOURCE_NODE_PROJECTION_MANIFEST_PATH: manifest_override}
                ):
                    with self.assertRaises(kag_generation.GenerationError) as context:
                        kag_generation.build_cross_source_node_projection_payload(
                            kag_generation.build_registry_payload()
                        )
                self.assertIn("projection_pairings", str(context.exception))

    def test_projection_pack_rejects_counterpart_ref_exposure(self) -> None:
        surfaces = registry_surfaces()
        expected = kag_generation.build_cross_source_node_projection_payload(
            kag_generation.build_registry_payload()
        )
        broken = copy.deepcopy(expected)
        broken["projections"][0]["retrieval_axis_ref"] = "mechanics/boundary-bridge/parts/counterpart-edge/docs/counterpart-edge-contracts.md"

        with self.assertRaises(validate_kag.ValidationError) as context:
            validate_kag.validate_cross_source_node_projection_pack(
                broken,
                surfaces,
                expected,
            )

        self.assertIn("counterpart refs", str(context.exception))


if __name__ == "__main__":
    unittest.main()
