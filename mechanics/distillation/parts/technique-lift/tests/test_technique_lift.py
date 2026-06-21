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


class TechniqueLiftTests(unittest.TestCase):
    def test_current_technique_lift_contract_validates(self) -> None:
        surfaces = registry_surfaces()
        payload = kag_generation.build_technique_lift_pack_payload(
            kag_generation.build_registry_payload()
        )

        validate_kag.validate_technique_lift_manifest(surfaces)
        validate_kag.validate_technique_lift_pack(payload, surfaces)
        self.assertEqual(payload, load_json(kag_generation.TECHNIQUE_LIFT_OUTPUT_PATH))

    def test_surface_bindings_stay_technique_owned_and_active(self) -> None:
        payload = kag_generation.build_technique_lift_pack_payload(
            kag_generation.build_registry_payload()
        )

        self.assertEqual(
            [binding["surface_id"] for binding in payload["surface_bindings"]],
            ["AOA-K-0001", "AOA-K-0002", "AOA-K-0003", "AOA-K-0004"],
        )
        self.assertEqual(payload["source_repo"], "aoa-techniques")
        self.assertTrue(
            all(
                source_input["ref"].startswith("aoa-techniques/")
                for source_input in payload["source_inputs"]
            )
        )


if __name__ == "__main__":
    unittest.main()
