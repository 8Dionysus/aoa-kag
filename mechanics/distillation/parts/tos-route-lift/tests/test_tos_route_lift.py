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
from scripts.validators.examples import tos_examples


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def registry_surfaces() -> dict[str, dict[str, object]]:
    return validate_kag.validate_registry_payload(
        validate_kag.read_json(validate_kag.REGISTRY_MANIFEST_PATH),
        label="registry manifest",
    )


class ToSRouteLiftTests(unittest.TestCase):
    @staticmethod
    def build_route_payload() -> dict[str, object]:
        return kag_generation.build_tos_zarathustra_route_pack_payload(
            kag_generation.build_registry_payload()
        )

    def assert_example_rejected(
        self,
        example: dict[str, object],
        expected_payload: dict[str, object],
        message: str,
    ) -> None:
        real_read_json = tos_examples.read_json

        def read_json(path: Path) -> object:
            if path == validate_kag.TOS_ZARATHUSTRA_ROUTE_PACK_EXAMPLE_PATH:
                return example
            return real_read_json(path)

        with patch.object(tos_examples, "read_json", side_effect=read_json):
            with self.assertRaisesRegex(validate_kag.ValidationError, message):
                validate_kag.validate_tos_zarathustra_route_pack_example(
                    expected_payload
                )

    def test_current_route_pack_contract_validates(self) -> None:
        surfaces = registry_surfaces()
        payload = self.build_route_payload()

        validate_kag.validate_tos_zarathustra_route_pack_manifest(surfaces)
        validate_kag.validate_tos_zarathustra_route_pack(payload, surfaces, payload)
        validate_kag.validate_tos_zarathustra_route_pack_example(payload)
        self.assertEqual(
            payload,
            load_json(kag_generation.TOS_ZARATHUSTRA_ROUTE_PACK_OUTPUT_PATH),
        )

    def test_route_pack_example_is_bounded_invariant_fixture(self) -> None:
        payload = self.build_route_payload()
        example = load_json(validate_kag.TOS_ZARATHUSTRA_ROUTE_PACK_EXAMPLE_PATH)
        assert isinstance(example, dict)

        self.assertNotEqual(payload, example)
        self.assertEqual(10, example["node_count"])
        self.assertEqual(6, example["edge_count"])
        self.assertTrue(
            all(count > 0 for count in example["node_type_counts"].values())
        )
        self.assertTrue(
            all(count > 0 for count in example["edge_kind_counts"].values())
        )
        validate_kag.validate_tos_zarathustra_route_pack_example(payload)

    def test_route_pack_example_rejects_selected_content_drift(self) -> None:
        payload = self.build_route_payload()
        example = load_json(validate_kag.TOS_ZARATHUSTRA_ROUTE_PACK_EXAMPLE_PATH)
        assert isinstance(example, dict)
        broken = copy.deepcopy(example)
        broken["nodes"][0]["distilled_thesis"] += " drift"

        self.assert_example_rejected(broken, payload, "reviewed bounded")

    def test_route_pack_example_rejects_node_type_coverage_loss(self) -> None:
        payload = self.build_route_payload()
        broken = copy.deepcopy(payload)
        analogy = next(
            node
            for node in broken["nodes"]
            if node["node_id"]
            == "tos.analogy.thus-spoke-zarathustra.prologue.bee-honey-analogy"
        )
        analogy["node_type"] = "concept"

        with self.assertRaisesRegex(
            validate_kag.ValidationError,
            "cover every canonical node type",
        ):
            validate_kag.validate_tos_zarathustra_route_pack_example(broken)

    def test_route_pack_example_rejects_edge_kind_coverage_loss(self) -> None:
        payload = self.build_route_payload()
        broken = copy.deepcopy(payload)
        bridge = next(edge for edge in broken["edges"] if edge["edge_id"] == "m038")
        bridge["edge_kind"] = "source_edge"

        with self.assertRaisesRegex(
            validate_kag.ValidationError,
            "cover every canonical edge kind",
        ):
            validate_kag.validate_tos_zarathustra_route_pack_example(broken)

    def test_route_pack_example_rejects_external_edge_endpoint(self) -> None:
        payload = self.build_route_payload()
        broken = copy.deepcopy(payload)
        bridge = next(edge for edge in broken["edges"] if edge["edge_id"] == "m038")
        bridge["to_id"] = "tos.concept.overcoming"

        with self.assertRaisesRegex(
            validate_kag.ValidationError,
            "edge endpoints must stay inside",
        ):
            validate_kag.validate_tos_zarathustra_route_pack_example(broken)

    def test_route_pack_example_rejects_missing_selected_source_node(self) -> None:
        payload = self.build_route_payload()
        broken = copy.deepcopy(payload)
        broken["nodes"] = [
            node
            for node in broken["nodes"]
            if node["node_id"] != "tos.source.thus-spoke-zarathustra.prologue"
        ]

        with self.assertRaisesRegex(
            validate_kag.ValidationError,
            "lost a fixture node",
        ):
            validate_kag.validate_tos_zarathustra_route_pack_example(broken)

    def test_route_pack_keeps_family_order_and_unique_authority_refs(self) -> None:
        payload = self.build_route_payload()

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
