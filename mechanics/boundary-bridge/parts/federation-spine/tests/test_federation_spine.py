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


def source_dependencies() -> dict[tuple[str, str], dict[str, object]]:
    return validate_kag.validate_source_owned_export_dependency_manifest(
        registry_surfaces()
    )


class FederationSpineTests(unittest.TestCase):
    def patched_generation_read_json(self, overrides: dict[Path, object]):
        original = kag_generation.read_json
        normalized = {Path(path).resolve(): copy.deepcopy(payload) for path, payload in overrides.items()}

        def side_effect(path: Path) -> object:
            resolved = Path(path).resolve()
            if resolved in normalized:
                return copy.deepcopy(normalized[resolved])
            return original(path)

        return patch.object(kag_generation, "read_json", side_effect=side_effect)

    def test_current_federation_spine_contract_validates(self) -> None:
        surfaces = registry_surfaces()
        dependencies = source_dependencies()
        federation_entries = validate_kag.validate_federation_export_registry_manifest(
            dependencies
        )
        payload = kag_generation.build_federation_spine_payload(
            kag_generation.build_registry_payload()
        )

        validate_kag.validate_federation_spine_manifest(
            surfaces,
            dependencies,
            federation_entries,
        )
        validate_kag.validate_federation_spine_pack(payload, surfaces, payload)
        self.assertEqual(payload, load_json(kag_generation.FEDERATION_SPINE_OUTPUT_PATH))

    def test_spine_keeps_artifact_identity_and_tos_adjunct_only(self) -> None:
        payload = kag_generation.build_federation_spine_payload(
            kag_generation.build_registry_payload()
        )
        repos_by_name = {repo["repo"]: repo for repo in payload["repos"]}

        self.assertEqual(payload["artifact_identity"], kag_generation.FEDERATION_SPINE_ARTIFACT_IDENTITY)
        self.assertEqual(repos_by_name["aoa-techniques"]["adjunct_surfaces"], [])
        self.assertEqual(
            repos_by_name["Tree-of-Sophia"]["adjunct_surfaces"][0]["surface_id"],
            "AOA-K-0011",
        )
        self.assertEqual(
            repos_by_name["Tree-of-Sophia"]["adjunct_surfaces"][0]["adjunct_budget"][
                "numbered_tiny_path_inclusion"
            ],
            "forbidden",
        )

    def test_spine_pack_rejects_counterpart_ref_exposure(self) -> None:
        surfaces = registry_surfaces()
        expected = kag_generation.build_federation_spine_payload(
            kag_generation.build_registry_payload()
        )
        broken = copy.deepcopy(expected)
        broken["repos"][0]["entry_surface_ref"] = "mechanics/boundary-bridge/parts/counterpart-edge/docs/counterpart-edge-contracts.md"

        with self.assertRaises(validate_kag.ValidationError) as context:
            validate_kag.validate_federation_spine_pack(broken, surfaces, expected)

        self.assertIn("counterpart refs", str(context.exception))

    def test_dependency_failure_names_dependency_id_and_registry_surface(self) -> None:
        broken_export = load_json(
            kag_generation.AOA_TECHNIQUES_ROOT / "generated" / "kag_export.min.json"
        )
        assert isinstance(broken_export, dict)
        broken_export["owner_repo"] = "wrong-owner"

        with self.patched_generation_read_json(
            {
                kag_generation.AOA_TECHNIQUES_ROOT / "generated" / "kag_export.min.json": broken_export,
            }
        ):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.build_federation_spine_payload(
                    kag_generation.build_registry_payload()
                )

        self.assertIn("aoa-techniques-kag-export", str(context.exception))
        self.assertIn("federation_export_registry", str(context.exception))


if __name__ == "__main__":
    unittest.main()
