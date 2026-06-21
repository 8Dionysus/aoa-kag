from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import kag_generation
import validate_kag


class CounterpartEdgePartTests(unittest.TestCase):
    def test_counterpart_contracts_remain_planned_contract_refs(self) -> None:
        surfaces_by_id = validate_kag.validate_registry_payload(
            kag_generation.build_registry_payload(),
            label="generated registry",
        )

        validate_kag.validate_counterpart_schema_surface()
        validate_kag.validate_counterpart_consumer_contract_schema_surface()
        validate_kag.validate_counterpart_example(surfaces_by_id)
        validate_kag.validate_counterpart_consumer_contract_example(surfaces_by_id)

    def test_counterpart_refs_are_part_local(self) -> None:
        expected_prefix = "mechanics/boundary-bridge/parts/counterpart-edge/"
        for ref in (
            kag_generation.COUNTERPART_CONSUMER_CONTRACT_DOC_REF,
            kag_generation.COUNTERPART_CONSUMER_CONTRACT_SCHEMA_REF,
            kag_generation.COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_REF,
            kag_generation.COUNTERPART_EDGE_CONTRACT_DOC_REF,
            kag_generation.COUNTERPART_EDGE_SCHEMA_REF,
            kag_generation.COUNTERPART_EDGE_EXAMPLE_REF,
        ):
            self.assertTrue(ref.startswith(expected_prefix), ref)


if __name__ == "__main__":
    unittest.main()
