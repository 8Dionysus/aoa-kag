from __future__ import annotations

import sys
from collections.abc import Callable

from ..local_contracts import *
from ..local_kag_subtree import *
from ..provider_registry import *
from ..repo_local_kag_index import *
from ..schema_surfaces import *

Check = Callable[[], None]

STATIC_SURFACE_PHASES: tuple[tuple[str, tuple[Check, ...]], ...] = (
    (
        "local-route-surfaces",
        (
            validate_nested_agents_docs,
            validate_mechanics_skeleton_surface,
            validate_questbook_surface,
        ),
    ),
    ("core-schema-surface", (validate_schema_surface,)),
    ("core-provider-registry", (validate_provider_registry_contract,)),
    ("core-local-kag-subtree", (validate_local_kag_subtree_contract_with_progress,)),
    ("core-repo-local-index", (validate_repo_local_kag_index_contract_with_progress,)),
    (
        "schema-surfaces",
        (
            validate_bridge_schema_surface,
            validate_bridge_envelope_schema_surface,
            validate_counterpart_schema_surface,
            validate_counterpart_federation_exposure_review_manifest_schema_surface,
            validate_counterpart_federation_exposure_review_schema_surface,
            validate_counterpart_consumer_contract_schema_surface,
            validate_reasoning_handoff_schema_surface,
            validate_projection_health_receipt_schema_surface,
            validate_regrounding_ticket_schema_surface,
            validate_technique_lift_manifest_schema_surface,
            validate_technique_lift_pack_schema_surface,
            validate_tos_text_chunk_map_manifest_schema_surface,
            validate_tos_text_chunk_map_schema_surface,
            validate_tos_retrieval_axis_manifest_schema_surface,
            validate_tos_retrieval_axis_schema_surface,
            validate_tos_zarathustra_route_pack_manifest_schema_surface,
            validate_tos_zarathustra_route_pack_schema_surface,
            validate_tos_zarathustra_route_retrieval_pack_manifest_schema_surface,
            validate_tos_zarathustra_route_retrieval_pack_schema_surface,
            validate_reasoning_handoff_pack_manifest_schema_surface,
            validate_reasoning_handoff_pack_schema_surface,
            validate_return_regrounding_manifest_schema_surface,
            validate_return_regrounding_schema_surface,
            validate_kag_maturity_governance_manifest_schema_surface,
            validate_kag_maturity_governance_schema_surface,
            validate_source_owned_export_dependencies_schema_surface,
            validate_federation_export_registry_manifest_schema_surface,
            validate_federation_export_registry_schema_surface,
            validate_federation_kag_export_schema_surface,
            validate_federation_spine_manifest_schema_surface,
            validate_federation_spine_schema_surface,
            validate_cross_source_node_projection_manifest_schema_surface,
            validate_cross_source_node_projection_schema_surface,
            validate_tiny_consumer_bundle_manifest_schema_surface,
            validate_tiny_consumer_bundle_schema_surface,
        ),
    ),
    (
        "antifragility-surfaces",
        (validate_antifragility_stress_surfaces,),
    ),
)


def _static_phase(label: str) -> None:
    print(f"[validate-kag:static] {label}", file=sys.stderr, flush=True)


def validate_static_surfaces() -> None:
    for label, checks in STATIC_SURFACE_PHASES:
        _static_phase(label)
        for check in checks:
            check()
