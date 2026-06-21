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


class ToSRouteLiftTests(unittest.TestCase):
    def test_current_route_pack_contract_validates(self) -> None:
        surfaces = registry_surfaces()
        payload = kag_generation.build_tos_zarathustra_route_pack_payload(
            kag_generation.build_registry_payload()
        )

        validate_kag.validate_tos_zarathustra_route_pack_manifest(surfaces)
        validate_kag.validate_tos_zarathustra_route_pack(payload, surfaces, payload)
        validate_kag.validate_tos_zarathustra_route_pack_example(payload)
        self.assertEqual(
            payload,
            load_json(kag_generation.TOS_ZARATHUSTRA_ROUTE_PACK_OUTPUT_PATH),
        )

    def test_route_pack_keeps_family_order_and_unique_authority_refs(self) -> None:
        payload = kag_generation.build_tos_zarathustra_route_pack_payload(
            kag_generation.build_registry_payload()
        )

        self.assertEqual(
            [node["node_type"] for node in payload["nodes"]],
            [
                node_type
                for node_type in kag_generation.TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER
                for _ in range(kag_generation.TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS[node_type])
            ],
        )
        authority_refs = [node["authority_ref"] for node in payload["nodes"]]
        self.assertEqual(len(authority_refs), len(set(authority_refs)))
        node_ids = {node["node_id"] for node in payload["nodes"]}
        for edge in payload["edges"]:
            self.assertIn(edge["from_id"], node_ids)
            self.assertIn(edge["to_id"], node_ids)

    def test_raw_table_intake_hold_stays_part_local_and_inactive(self) -> None:
        doc_path = (
            REPO_ROOT
            / "mechanics"
            / "distillation"
            / "parts"
            / "tos-route-lift"
            / "docs"
            / "tos-raw-table-intake-hold.md"
        )
        text = doc_path.read_text(encoding="utf-8")

        self.assertIn("does not define", text)
        self.assertIn("a new raw-table manifest", text)
        self.assertIn("a new generated pack", text)
        self.assertIn("not from `Tree-of-Sophia/intake/**`", text)
        self.assertFalse((REPO_ROOT / "docs" / "TOS_RAW_TABLE_INTAKE_HOLD.md").exists())


if __name__ == "__main__":
    unittest.main()
