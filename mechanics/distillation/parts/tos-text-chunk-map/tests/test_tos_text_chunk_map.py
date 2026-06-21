from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

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


class ToSTextChunkMapTests(unittest.TestCase):
    def test_current_chunk_map_contract_validates(self) -> None:
        surfaces = registry_surfaces()
        payload = kag_generation.build_tos_text_chunk_map_payload(
            kag_generation.build_registry_payload()
        )

        validate_kag.validate_tos_text_chunk_map_manifest(surfaces)
        validate_kag.validate_tos_text_chunk_map_pack(payload, surfaces, payload)
        validate_kag.validate_tos_text_chunk_map_example(payload)
        self.assertEqual(payload, load_json(kag_generation.TOS_TEXT_CHUNK_MAP_OUTPUT_PATH))

    def test_chunk_map_stays_below_activation_and_replacement(self) -> None:
        payload = kag_generation.build_tos_text_chunk_map_payload(
            kag_generation.build_registry_payload()
        )

        self.assertEqual(payload["surface_id"], "AOA-K-0005")
        self.assertTrue(payload["route_ref"].startswith("Tree-of-Sophia/"))
        self.assertTrue(payload["capsule_ref"].startswith("Tree-of-Sophia/"))
        self.assertEqual(
            payload["bounded_output_contract"]["source_replacement"],
            "forbidden",
        )
        self.assertEqual(
            payload["bounded_output_contract"]["counterpart_projection"],
            "forbidden",
        )
        self.assertEqual(
            payload["bounded_output_contract"]["federation_export_activation"],
            "forbidden",
        )


if __name__ == "__main__":
    unittest.main()
