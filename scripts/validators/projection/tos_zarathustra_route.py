from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_tos_zarathustra_route_pack(
    payload: object,
    surfaces_by_id: dict[str, dict[str, object]],
    expected_payload: dict[str, object],
) -> None:
    if not isinstance(payload, dict):
        fail("ToS Zarathustra route pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_repo",
        "source_manifest_ref",
        "source_inputs",
        "surface_bindings",
        "surface_id",
        "surface_name",
        "route_id",
        "route_capsule_ref",
        "relation_pack_ref",
        "node_count",
        "edge_count",
        "node_type_counts",
        "edge_kind_counts",
        "nodes",
        "edges",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"ToS Zarathustra route pack is missing required key '{key}'")

    if payload["pack_version"] != 1:
        fail("ToS Zarathustra route pack pack_version must equal 1")
    if payload["pack_type"] != "tos_zarathustra_route_pack":
        fail("ToS Zarathustra route pack pack_type must equal 'tos_zarathustra_route_pack'")
    if payload["source_repo"] != TOS_REPO:
        fail("ToS Zarathustra route pack source_repo must equal 'Tree-of-Sophia'")
    if payload["source_manifest_ref"] != TOS_ZARATHUSTRA_ROUTE_PACK_MANIFEST_REF:
        fail(
            "ToS Zarathustra route pack source_manifest_ref must point to "
            f"{TOS_ZARATHUSTRA_ROUTE_PACK_MANIFEST_REF}"
        )
    if payload["route_id"] != TOS_ZARATHUSTRA_ROUTE_ID:
        fail(
            "ToS Zarathustra route pack route_id must equal "
            f"'{TOS_ZARATHUSTRA_ROUTE_ID}'"
        )
    if payload["bounded_output_contract"] != EXPECTED_TOS_ZARATHUSTRA_ROUTE_PACK_CONTRACT:
        fail(
            "ToS Zarathustra route pack bounded_output_contract must match the current "
            "source-first guardrail"
        )
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail(
            "ToS Zarathustra route pack source_inputs must match the manifest-driven "
            "canonical donor set"
        )
    if payload["surface_bindings"] != expected_payload["surface_bindings"]:
        fail(
            "ToS Zarathustra route pack surface_bindings must match the current "
            "bounded route-pack binding"
        )

    surface_0010 = surfaces_by_id.get("AOA-K-0010")
    if surface_0010 is None or surface_0010.get("status") != "experimental":
        fail(
            "ToS Zarathustra route pack requires AOA-K-0010 to remain experimental in "
            "the generated registry"
        )

    route_capsule_ref = payload["route_capsule_ref"]
    relation_pack_ref = payload["relation_pack_ref"]
    if not isinstance(route_capsule_ref, str) or not route_capsule_ref:
        fail("ToS Zarathustra route pack route_capsule_ref must be a non-empty string")
    if not isinstance(relation_pack_ref, str) or not relation_pack_ref:
        fail("ToS Zarathustra route pack relation_pack_ref must be a non-empty string")
    resolve_known_ref(route_capsule_ref, label="ToS Zarathustra route pack route_capsule_ref")
    resolve_known_ref(relation_pack_ref, label="ToS Zarathustra route pack relation_pack_ref")
    if route_capsule_ref != repo_ref(TOS_REPO, TOS_ZARATHUSTRA_ROUTE_CAPSULE_PATH):
        fail(
            "ToS Zarathustra route pack route_capsule_ref must stay aligned with the "
            "canonical Zarathustra route capsule"
        )
    if relation_pack_ref != repo_ref(TOS_REPO, TOS_ZARATHUSTRA_ROUTE_RELATION_PACK_PATH):
        fail(
            "ToS Zarathustra route pack relation_pack_ref must stay aligned with the "
            "canonical ToS relation pack"
        )

    nodes = payload["nodes"]
    if not isinstance(nodes, list) or len(nodes) != sum(TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS.values()):
        fail("ToS Zarathustra route pack must contain exactly 92 nodes")
    if payload["node_count"] != len(nodes):
        fail("ToS Zarathustra route pack node_count must equal the number of nodes")
    if payload["node_type_counts"] != TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS:
        fail("ToS Zarathustra route pack node_type_counts must match the current canonical route")

    actual_node_type_counts = {key: 0 for key in TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS}
    seen_node_ids: set[str] = set()
    seen_authority_refs: set[str] = set()
    actual_node_type_order: list[str] = []
    for index, node in enumerate(nodes):
        location = f"ToS Zarathustra route pack nodes[{index}]"
        if not isinstance(node, dict):
            fail(f"{location} must be an object")
        for key in (
            "node_id",
            "node_type",
            "authority_ref",
            "source_anchor",
            "key_terms",
            "distilled_thesis",
            "interpretation_layers",
        ):
            if key not in node:
                fail(f"{location} is missing required key '{key}'")
        node_id = node["node_id"]
        node_type = node["node_type"]
        authority_ref = node["authority_ref"]
        if not isinstance(node_id, str) or not node_id.startswith("tos."):
            fail(f"{location}.node_id must be a canonical tos.* id")
        if node_id.startswith("literal."):
            fail(f"{location}.node_id must not carry literal residue")
        if node_id in seen_node_ids:
            fail(f"{location}.node_id '{node_id}' is duplicated")
        seen_node_ids.add(node_id)
        if node_type not in actual_node_type_counts:
            fail(f"{location}.node_type '{node_type}' is not allowed in the route pack")
        actual_node_type_counts[node_type] += 1
        actual_node_type_order.append(node_type)
        if not isinstance(authority_ref, str) or not authority_ref.startswith("Tree-of-Sophia/ToS/canon/"):
            fail(f"{location}.authority_ref must point into Tree-of-Sophia/ToS/canon/**/node.json")
        if not authority_ref.endswith("/node.json"):
            fail(f"{location}.authority_ref must resolve to a canonical node.json file")
        if "/intake/" in authority_ref or authority_ref.startswith("Tree-of-Sophia/intake/"):
            fail(f"{location}.authority_ref must not point at Tree-of-Sophia/intake")
        if authority_ref in seen_authority_refs:
            fail(
                f"{location}.authority_ref '{authority_ref}' is duplicated and would "
                "collapse distinct canonical nodes into one projection handle"
            )
        seen_authority_refs.add(authority_ref)
        resolve_known_ref(authority_ref, label=f"{location}.authority_ref")
        validate_unique_string_list(node["key_terms"], label=f"{location}.key_terms")
        validate_unique_string_list(
            node["interpretation_layers"],
            label=f"{location}.interpretation_layers",
        )
        if not isinstance(node["source_anchor"], str) or not node["source_anchor"]:
            fail(f"{location}.source_anchor must be a non-empty string")
        if not isinstance(node["distilled_thesis"], str) or not node["distilled_thesis"]:
            fail(f"{location}.distilled_thesis must be a non-empty string")

    if actual_node_type_counts != TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS:
        fail(
            "ToS Zarathustra route pack nodes must preserve the current family counts "
            "across the canonical route"
        )
    expected_node_type_order = [
        node_type
        for node_type in TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER
        for _ in range(TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS[node_type])
    ]
    if actual_node_type_order != expected_node_type_order:
        fail(
            "ToS Zarathustra route pack nodes must preserve the current family order "
            "source -> concept -> principle -> lineage -> event -> state -> support "
            "-> analogy -> synthesis"
        )

    edges = payload["edges"]
    if not isinstance(edges, list) or len(edges) != sum(TOS_ZARATHUSTRA_ROUTE_EDGE_KIND_COUNTS.values()):
        fail("ToS Zarathustra route pack must contain exactly 125 edges")
    if payload["edge_count"] != len(edges):
        fail("ToS Zarathustra route pack edge_count must equal the number of edges")
    if payload["edge_kind_counts"] != TOS_ZARATHUSTRA_ROUTE_EDGE_KIND_COUNTS:
        fail("ToS Zarathustra route pack edge_kind_counts must match the canonical relation pack")

    actual_edge_kind_counts = {key: 0 for key in TOS_ZARATHUSTRA_ROUTE_EDGE_KIND_COUNTS}
    actual_edge_ids: list[str] = []
    expected_edge_ids = [
        edge["edge_id"]
        for edge in expected_payload["edges"]
        if isinstance(edge, dict) and isinstance(edge.get("edge_id"), str)
    ]
    for index, edge in enumerate(edges):
        location = f"ToS Zarathustra route pack edges[{index}]"
        if not isinstance(edge, dict):
            fail(f"{location} must be an object")
        for key in (
            "edge_id",
            "edge_kind",
            "from_id",
            "predicate_id",
            "to_id",
            "layer",
            "anchor_mode",
            "anchor_start_secondary",
            "anchor_end_secondary",
            "anchor_segment_ids",
            "witness_scope",
            "connectivity_role",
            "confidence",
            "note",
        ):
            if key not in edge:
                fail(f"{location} is missing required key '{key}'")
        edge_id = edge["edge_id"]
        if not isinstance(edge_id, str) or not edge_id:
            fail(f"{location}.edge_id must be a non-empty string")
        actual_edge_ids.append(edge_id)
        edge_kind = edge["edge_kind"]
        if edge_kind not in actual_edge_kind_counts:
            fail(f"{location}.edge_kind '{edge_kind}' is not allowed in the route pack")
        actual_edge_kind_counts[edge_kind] += 1
        for endpoint_key in ("from_id", "to_id"):
            endpoint = edge[endpoint_key]
            if not isinstance(endpoint, str) or not endpoint.startswith("tos."):
                fail(f"{location}.{endpoint_key} must keep canonical tos.* ids")
            if endpoint.startswith("literal."):
                fail(f"{location}.{endpoint_key} must not carry literal residue")
            if endpoint not in seen_node_ids:
                fail(
                    f"{location}.{endpoint_key} '{endpoint}' must resolve to a node_id "
                    "projected into the same route pack"
                )
        if not isinstance(edge["predicate_id"], str) or not edge["predicate_id"]:
            fail(f"{location}.predicate_id must be a non-empty string")
        if not isinstance(edge["confidence"], int):
            fail(f"{location}.confidence must remain integer-valued")
    if actual_edge_kind_counts != TOS_ZARATHUSTRA_ROUTE_EDGE_KIND_COUNTS:
        fail(
            "ToS Zarathustra route pack edges must preserve the current canonical "
            "edge-kind counts"
        )
    if actual_edge_ids != expected_edge_ids:
        fail(
            "ToS Zarathustra route pack edges must preserve the canonical relation "
            "pack row order"
        )

    if payload != expected_payload:
        fail(
            "ToS Zarathustra route pack must match the committed manifest-driven "
            "canonical route payload"
        )
