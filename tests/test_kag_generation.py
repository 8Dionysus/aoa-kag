from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import kag_generation


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class KagGenerationTestCase(unittest.TestCase):
    def patched_read_json(self, overrides: dict[Path, object]):
        original = kag_generation.read_json
        normalized_overrides = {
            Path(path).resolve(): copy.deepcopy(payload)
            for path, payload in overrides.items()
        }

        def side_effect(path: Path) -> object:
            resolved = Path(path).resolve()
            if resolved in normalized_overrides:
                return copy.deepcopy(normalized_overrides[resolved])
            return original(path)

        return patch.object(kag_generation, "read_json", side_effect=side_effect)

    def assert_builder_matches_generated(
        self,
        builder,
        full_output_path: Path,
        min_output_path: Path,
        *,
        registry_payload: dict[str, object] | None = None,
    ) -> None:
        payload = builder() if registry_payload is None else builder(registry_payload)
        expected_payload = load_json(full_output_path)
        self.assertEqual(payload, expected_payload)
        self.assertEqual(
            kag_generation.encode_json(payload, pretty=True),
            full_output_path.read_text(encoding="utf-8"),
        )
        self.assertEqual(
            kag_generation.encode_json(payload, pretty=False),
            min_output_path.read_text(encoding="utf-8"),
        )

    def test_ordered_unique_preserves_first_seen_order(self) -> None:
        self.assertEqual(
            kag_generation.ordered_unique(["alpha", "beta", "alpha", "gamma", "beta"]),
            ["alpha", "beta", "gamma"],
        )

    def test_ensure_repo_relative_path_rejects_absolute_path(self) -> None:
        with self.assertRaises(kag_generation.GenerationError):
            kag_generation.ensure_repo_relative_path(
                "D:/aoa-kag/generated/kag_registry.json",
                label="absolute_path",
            )

    def test_tos_text_chunk_map_builder_matches_generated_outputs(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        self.assert_builder_matches_generated(
            kag_generation.build_tos_text_chunk_map_payload,
            kag_generation.TOS_TEXT_CHUNK_MAP_OUTPUT_PATH,
            kag_generation.TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH,
            registry_payload=registry_payload,
        )

    def test_tos_retrieval_axis_builder_matches_generated_outputs(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        self.assert_builder_matches_generated(
            kag_generation.build_tos_retrieval_axis_pack_payload,
            kag_generation.TOS_RETRIEVAL_AXIS_OUTPUT_PATH,
            kag_generation.TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH,
            registry_payload=registry_payload,
        )

    def test_federation_spine_builder_matches_generated_outputs(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        self.assert_builder_matches_generated(
            kag_generation.build_federation_spine_payload,
            kag_generation.FEDERATION_SPINE_OUTPUT_PATH,
            kag_generation.FEDERATION_SPINE_MIN_OUTPUT_PATH,
            registry_payload=registry_payload,
        )

    def test_cross_source_projection_builder_matches_generated_outputs(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        self.assert_builder_matches_generated(
            kag_generation.build_cross_source_node_projection_payload,
            kag_generation.CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATH,
            kag_generation.CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH,
            registry_payload=registry_payload,
        )

    def test_dependency_failure_names_dependency_id_and_consumer_surface(self) -> None:
        broken_export = load_json(
            kag_generation.AOA_TECHNIQUES_ROOT / "generated" / "kag_export.min.json"
        )
        assert isinstance(broken_export, dict)
        broken_export["owner_repo"] = "wrong-owner"

        with self.patched_read_json(
            {
                kag_generation.AOA_TECHNIQUES_ROOT / "generated" / "kag_export.min.json": broken_export,
            }
        ):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.build_federation_spine_payload(
                    kag_generation.build_registry_payload()
                )

        self.assertIn("aoa-techniques-kag-export", str(context.exception))
        self.assertIn("AOA-K-0009", str(context.exception))

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
                with self.patched_read_json(
                    {
                        kag_generation.CROSS_SOURCE_NODE_PROJECTION_MANIFEST_PATH: manifest_override,
                    }
                ):
                    with self.assertRaises(kag_generation.GenerationError) as context:
                        kag_generation.build_cross_source_node_projection_payload(
                            kag_generation.build_registry_payload()
                        )
                self.assertIn("projection_pairings", str(context.exception))


if __name__ == "__main__":
    unittest.main()
