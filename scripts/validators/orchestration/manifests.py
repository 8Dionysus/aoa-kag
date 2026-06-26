from __future__ import annotations

from ..common import *
from ..manifest_contracts import *
from ..projection_parity import *
from ..source_refs import *


def load_registry_context() -> tuple[dict[str, object], dict[str, dict[str, object]], list[str]]:
    registry_manifest_payload = read_json(REGISTRY_MANIFEST_PATH)
    if not isinstance(registry_manifest_payload, dict):
        fail("registry manifest must be a JSON object")
    registry_manifest_surfaces = validate_registry_payload(
        registry_manifest_payload,
        label="registry manifest",
    )
    return (
        registry_manifest_payload,
        registry_manifest_surfaces,
        missing_full_cross_repo_roots(),
    )


def validate_manifest_contracts(
    registry_manifest_surfaces: dict[str, dict[str, object]],
) -> tuple[
    dict[tuple[str, str], dict[str, object]],
    dict[tuple[str, str], dict[str, object]],
]:
    validate_technique_lift_manifest(registry_manifest_surfaces)
    validate_tos_text_chunk_map_manifest(registry_manifest_surfaces)
    validate_tos_retrieval_axis_manifest(registry_manifest_surfaces)
    validate_tos_zarathustra_route_pack_manifest(registry_manifest_surfaces)
    validate_tos_zarathustra_route_retrieval_pack_manifest(registry_manifest_surfaces)
    validate_reasoning_handoff_manifest()
    validate_return_regrounding_manifest()
    validate_kag_maturity_governance_manifest(registry_manifest_surfaces)
    source_owned_export_dependencies = validate_source_owned_export_dependency_manifest(
        registry_manifest_surfaces
    )
    federation_export_registry_entries = validate_federation_export_registry_manifest(
        source_owned_export_dependencies
    )
    validate_federation_spine_manifest(
        registry_manifest_surfaces,
        source_owned_export_dependencies,
        federation_export_registry_entries,
    )
    validate_cross_source_node_projection_manifest(
        registry_manifest_surfaces,
        source_owned_export_dependencies,
    )
    validate_tiny_consumer_bundle_manifest(registry_manifest_surfaces)
    validate_counterpart_federation_exposure_review_manifest()
    return source_owned_export_dependencies, federation_export_registry_entries
