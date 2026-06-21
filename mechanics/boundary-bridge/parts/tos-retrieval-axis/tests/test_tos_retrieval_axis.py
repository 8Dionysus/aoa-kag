from __future__ import annotations

import copy
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


class ToSRetrievalAxisTests(unittest.TestCase):
    def test_current_retrieval_axis_contract_validates(self) -> None:
        surfaces = registry_surfaces()
        payload = kag_generation.build_tos_retrieval_axis_pack_payload(
            kag_generation.build_registry_payload()
        )

        validate_kag.validate_tos_retrieval_axis_manifest(surfaces)
        validate_kag.validate_tos_retrieval_axis_pack(payload, surfaces, payload)
        validate_kag.validate_tos_retrieval_axis_example(payload)
        self.assertEqual(payload, load_json(kag_generation.TOS_RETRIEVAL_AXIS_OUTPUT_PATH))

    def test_route_retrieval_handles_match_route_pack(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        route_pack = kag_generation.build_tos_zarathustra_route_pack_payload(registry_payload)
        retrieval_pack = kag_generation.build_tos_zarathustra_route_retrieval_pack_payload(
            registry_payload
        )
        route = retrieval_pack["routes"][0]

        seen_node_ids: set[str] = set()
        for node_type in kag_generation.TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER:
            expected_handles = [
                {"node_id": node["node_id"], "authority_ref": node["authority_ref"]}
                for node in route_pack["nodes"]
                if node["node_type"] == node_type
            ]
            self.assertEqual(route[f"{node_type}_handles"], expected_handles)
            seen_node_ids.update(handle["node_id"] for handle in expected_handles)

        self.assertEqual(seen_node_ids, {node["node_id"] for node in route_pack["nodes"]})

    def test_route_retrieval_rejects_source_first_reentry_drift(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        surfaces = registry_surfaces()
        route_pack = kag_generation.build_tos_zarathustra_route_pack_payload(registry_payload)
        expected = kag_generation.build_tos_zarathustra_route_retrieval_pack_payload(
            registry_payload
        )
        broken = copy.deepcopy(expected)
        broken["subordinate_posture"]["source_first_reentry_ref"] = (
            "mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_zarathustra_route_retrieval_pack.min.json"
        )

        with self.assertRaises(validate_kag.ValidationError) as context:
            validate_kag.validate_tos_zarathustra_route_retrieval_pack(
                broken,
                surfaces,
                expected,
                route_pack,
            )

        self.assertIn("subordinate_posture", str(context.exception))


if __name__ == "__main__":
    unittest.main()
