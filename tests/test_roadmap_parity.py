from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


CURRENT_RELEASE_SURFACES = (
    "generated/kag_registry.min.json",
    "generated/federation_export_registry.min.json",
    "docs/FEDERATION_KAG_READINESS.md",
    "generated/technique_lift_pack.min.json",
    "generated/tos_text_chunk_map.min.json",
    "generated/tos_retrieval_axis_pack.min.json",
    "generated/tos_zarathustra_route_pack.min.json",
    "generated/tos_zarathustra_route_retrieval_pack.min.json",
    "docs/TOS_RAW_TABLE_INTAKE_STUB.md",
    "generated/kag_maturity_governance.min.json",
    "docs/KAG_MATURITY_GOVERNANCE.md",
    "docs/KAG_OWNER_WAIT_STATES.md",
    "docs/KAG_PROOF_EXPECTATIONS.md",
    "generated/reasoning_handoff_pack.min.json",
    "generated/return_regrounding_pack.min.json",
    "docs/BRIDGE_CONTRACTS.md",
    "docs/RECURRENCE_REGROUNDING.md",
    "docs/KAG_STRESS_REGROUNDING.md",
    "docs/KAG_PROJECTION_QUARANTINE.md",
    "generated/federation_spine.min.json",
    "generated/counterpart_federation_exposure_review.min.json",
    "generated/tiny_consumer_bundle.min.json",
    "generated/cross_source_node_projection.min.json",
    "docs/COUNTERPART_CONSUMER_CONTRACT.md",
    "docs/COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md",
    "docs/COUNTERPART_EDGE_CONTRACTS.md",
)


class RoadmapParityTestCase(unittest.TestCase):
    def test_roadmap_matches_current_v0_2_0_release_contour(self) -> None:
        roadmap = (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

        self.assertIn("Current release: `v0.2.0`", readme)
        self.assertIn("## [0.2.0]", changelog)
        self.assertIn("`v0.2.0`", roadmap)
        self.assertIn("release contour", roadmap)
        self.assertIn("Roadmap drift", roadmap)
        self.assertIn("source repositories remain authoritative", roadmap)
        self.assertIn("not a claim that KAG is a full graph engine", roadmap)
        self.assertNotIn("`aoa-kag` is in bootstrap.", roadmap)

        for surface in CURRENT_RELEASE_SURFACES:
            with self.subTest(surface=surface):
                self.assertTrue((REPO_ROOT / surface).is_file())
                self.assertIn(surface, roadmap)


if __name__ == "__main__":
    unittest.main()
