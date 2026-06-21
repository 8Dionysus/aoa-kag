from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


CURRENT_RELEASE_SURFACES = (
    "generated/kag_registry.min.json",
    "mechanics/boundary-bridge/parts/source-owned-export/generated/federation_export_registry.min.json",
    "mechanics/boundary-bridge/parts/source-owned-export/docs/federation-kag-readiness.md",
    "mechanics/distillation/parts/technique-lift/generated/technique_lift_pack.min.json",
    "mechanics/distillation/parts/tos-text-chunk-map/generated/tos_text_chunk_map.min.json",
    "mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_retrieval_axis_pack.min.json",
    "mechanics/distillation/parts/tos-route-lift/generated/tos_zarathustra_route_pack.min.json",
    "mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_zarathustra_route_retrieval_pack.min.json",
    "mechanics/distillation/parts/tos-route-lift/docs/tos-raw-table-intake-hold.md",
    "mechanics/growth-cycle/parts/surface-growth-stop-rule/generated/kag_maturity_governance.min.json",
    "mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-maturity-governance.md",
    "mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-owner-wait-states.md",
    "mechanics/audit/parts/proof-expectation-refs/docs/kag-proof-expectations.md",
    "mechanics/checkpoint/parts/reasoning-handoff/generated/reasoning_handoff_pack.min.json",
    "mechanics/recurrence/parts/return-regrounding/generated/return_regrounding_pack.min.json",
    "docs/BRIDGE_CONTRACTS.md",
    "mechanics/recurrence/parts/return-regrounding/docs/recurrence-regrounding.md",
    "mechanics/antifragility/parts/projection-health/docs/stress-regrounding.md",
    "mechanics/antifragility/parts/projection-quarantine/docs/projection-quarantine.md",
    "mechanics/antifragility/parts/retrieval-outage-regrounding/docs/retrieval-outage-regrounding.md",
    "mechanics/antifragility/parts/projection-health/examples/projection_health_receipt.retrieval-outage-honesty.example.json",
    "mechanics/antifragility/parts/retrieval-outage-regrounding/examples/regrounding_ticket.retrieval-outage-honesty.example.json",
    "mechanics/boundary-bridge/parts/federation-spine/generated/federation_spine.min.json",
    "mechanics/audit/parts/exposure-review/generated/counterpart_federation_exposure_review.min.json",
    "mechanics/boundary-bridge/parts/tiny-consumer-bundle/generated/tiny_consumer_bundle.min.json",
    "mechanics/boundary-bridge/parts/cross-source-projection/generated/cross_source_node_projection.min.json",
    "mechanics/boundary-bridge/parts/counterpart-edge/docs/counterpart-consumer-contract.md",
    "mechanics/audit/parts/exposure-review/docs/counterpart-federation-exposure-review.md",
    "mechanics/boundary-bridge/parts/counterpart-edge/docs/counterpart-edge-contracts.md",
)


class RoadmapParityTestCase(unittest.TestCase):
    def test_roadmap_matches_current_v0_2_0_release_contour(self) -> None:
        roadmap = (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

        self.assertIn("Current release: `v0.2.2`", readme)
        self.assertIn("## [0.2.2]", changelog)
        self.assertIn("`v0.2.2`", roadmap)
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
