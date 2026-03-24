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

import validate_kag


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class ValidateKagTestCase(unittest.TestCase):
    def patched_read_json(self, overrides: dict[Path, object]):
        original = validate_kag.read_json
        normalized_overrides = {
            Path(path).resolve(): copy.deepcopy(payload)
            for path, payload in overrides.items()
        }

        def side_effect(path: Path) -> object:
            resolved = Path(path).resolve()
            if resolved in normalized_overrides:
                return copy.deepcopy(normalized_overrides[resolved])
            return original(path)

        return patch.object(validate_kag, "read_json", side_effect=side_effect)

    def registry_manifest_surfaces(self) -> dict[str, dict[str, object]]:
        registry_manifest_payload = validate_kag.read_json(validate_kag.REGISTRY_MANIFEST_PATH)
        return validate_kag.validate_registry_payload(
            registry_manifest_payload,
            label="registry manifest",
        )

    def test_projection_pairings_validator_failures_are_pairing_specific(self) -> None:
        registry_surfaces = self.registry_manifest_surfaces()
        dependencies = validate_kag.validate_source_owned_export_dependency_manifest(
            registry_surfaces
        )
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
                    {
                        validate_kag.CROSS_SOURCE_NODE_PROJECTION_MANIFEST_PATH: manifest_override,
                    }
                ):
                    with self.assertRaises(validate_kag.ValidationError) as context:
                        validate_kag.validate_cross_source_node_projection_manifest(
                            registry_surfaces,
                            dependencies,
                        )
                self.assertIn("projection_pairings", str(context.exception))


if __name__ == "__main__":
    unittest.main()
