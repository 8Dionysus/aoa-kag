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


def registry_surfaces() -> dict[str, dict[str, object]]:
    return validate_kag.validate_registry_payload(
        validate_kag.read_json(validate_kag.REGISTRY_MANIFEST_PATH),
        label="registry manifest",
    )


class ProofExpectationRefsTests(unittest.TestCase):
    def test_maturity_proof_refs_validate_without_proof_ownership(self) -> None:
        surfaces = registry_surfaces()
        expected = kag_generation.build_kag_maturity_governance_payload(
            kag_generation.build_registry_payload()
        )

        validate_kag.validate_kag_maturity_governance_manifest(surfaces)
        validate_kag.validate_kag_maturity_governance_pack(expected, expected, surfaces)

        for surface in expected["surfaces"]:
            self.assertTrue(surface["proof_expectation_refs"])
            for proof_ref in surface["proof_expectation_refs"]:
                self.assertTrue(proof_ref.startswith("aoa-evals/"))
        self.assertEqual(
            expected["bounded_output_contract"]["proof_ownership"],
            "forbidden",
        )

    def test_planned_counterpart_surface_keeps_named_proof_gap(self) -> None:
        payload = kag_generation.build_kag_maturity_governance_payload(
            kag_generation.build_registry_payload()
        )
        surfaces_by_id = {surface["surface_id"]: surface for surface in payload["surfaces"]}

        self.assertEqual(
            surfaces_by_id["AOA-K-0008"]["stability_tier"],
            "planned_contract_only",
        )
        self.assertIn("proof_gap_note", surfaces_by_id["AOA-K-0008"])
        self.assertIn(
            "aoa-evals/evals/comparison/longitudinal-window/aoa-stress-recovery-window/EVAL.md",
            surfaces_by_id["AOA-K-0008"]["proof_expectation_refs"],
        )


if __name__ == "__main__":
    unittest.main()
