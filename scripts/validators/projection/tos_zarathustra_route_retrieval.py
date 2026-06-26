from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_tos_zarathustra_route_retrieval_pack(
    payload: object,
    surfaces_by_id: dict[str, dict[str, object]],
    expected_payload: dict[str, object],
    route_pack_payload: dict[str, object],
) -> None:
    if not isinstance(payload, dict):
        fail("ToS Zarathustra route retrieval pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "source_inputs",
        "surface_bindings",
        "surface_id",
        "surface_name",
        "adjunct_budget",
        "subordinate_posture",
        "route_count",
        "routes",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(
                "ToS Zarathustra route retrieval pack is missing required key "
                f"'{key}'"
            )

    if payload["pack_version"] != 1:
        fail("ToS Zarathustra route retrieval pack pack_version must equal 1")
    if payload["pack_type"] != "tos_zarathustra_route_retrieval_pack":
        fail(
            "ToS Zarathustra route retrieval pack pack_type must equal "
            "'tos_zarathustra_route_retrieval_pack'"
        )
    if (
        payload["source_manifest_ref"]
        != TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MANIFEST_REF
    ):
        fail(
            "ToS Zarathustra route retrieval pack source_manifest_ref must point to "
            f"{TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MANIFEST_REF}"
        )
    if (
        payload["bounded_output_contract"]
        != EXPECTED_TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_CONTRACT
    ):
        fail(
            "ToS Zarathustra route retrieval pack bounded_output_contract must "
            "match the current source-first guardrail"
        )
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail(
            "ToS Zarathustra route retrieval pack source_inputs must match the "
            "single-donor route-pack contract"
        )
    if payload["adjunct_budget"] != EXPECTED_TOS_STANDALONE_ADJUNCT_BUDGET:
        fail(
            "ToS Zarathustra route retrieval pack adjunct_budget must match the "
            "current standalone adjunct budget"
        )
    if (
        payload["subordinate_posture"]
        != EXPECTED_TOS_STANDALONE_ADJUNCT_SUBORDINATE_POSTURE
    ):
        fail(
            "ToS Zarathustra route retrieval pack subordinate_posture must match "
            "the current source-first subordinate posture"
        )
    if payload["surface_bindings"] != expected_payload["surface_bindings"]:
        fail(
            "ToS Zarathustra route retrieval pack surface_bindings must match the "
            "current bounded retrieval binding"
        )

    surface_0011 = surfaces_by_id.get("AOA-K-0011")
    if surface_0011 is None or surface_0011.get("status") != "experimental":
        fail(
            "ToS Zarathustra route retrieval pack requires AOA-K-0011 to remain "
            "experimental in the generated registry"
        )

    if payload["route_count"] != 1:
        fail("ToS Zarathustra route retrieval pack route_count must equal 1")
    routes = payload["routes"]
    if not isinstance(routes, list) or len(routes) != 1:
        fail(
            "ToS Zarathustra route retrieval pack must contain exactly one route in "
            "the current pilot"
        )
    route = routes[0]
    if not isinstance(route, dict):
        fail("ToS Zarathustra route retrieval pack route must be an object")

    for key in (
        "retrieval_id",
        "route_id",
        "route_pack_ref",
        "route_capsule_ref",
        "relation_pack_ref",
        "node_type_counts",
        "edge_kind_counts",
        "source_handles",
        "concept_handles",
        "principle_handles",
        "lineage_handles",
        "event_handles",
        "state_handles",
        "support_handles",
        "analogy_handles",
        "synthesis_handles",
        "retrieval_summary",
    ):
        if key not in route:
            fail(
                "ToS Zarathustra route retrieval pack route is missing required key "
                f"'{key}'"
            )

    if route["retrieval_id"] != TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_ID:
        fail(
            "ToS Zarathustra route retrieval pack retrieval_id must stay aligned "
            "with AOA-K-0011"
        )
    if route["route_id"] != TOS_ZARATHUSTRA_ROUTE_ID:
        fail(
            "ToS Zarathustra route retrieval pack route_id must equal "
            f"'{TOS_ZARATHUSTRA_ROUTE_ID}'"
        )
    if route["route_pack_ref"] != TOS_ZARATHUSTRA_ROUTE_PACK_INPUT_REF:
        fail(
            "ToS Zarathustra route retrieval pack route_pack_ref must point to "
            f"{TOS_ZARATHUSTRA_ROUTE_PACK_INPUT_REF}"
        )
    if "/intake/" in route["route_pack_ref"] or route["route_pack_ref"].startswith("Tree-of-Sophia/intake/"):
        fail("ToS Zarathustra route retrieval pack route_pack_ref must not point at intake")
    resolve_known_ref(
        route["route_pack_ref"],
        label="ToS Zarathustra route retrieval pack route_pack_ref",
    )
    resolve_known_ref(
        route["route_capsule_ref"],
        label="ToS Zarathustra route retrieval pack route_capsule_ref",
    )
    resolve_known_ref(
        route["relation_pack_ref"],
        label="ToS Zarathustra route retrieval pack relation_pack_ref",
    )
    if route["route_capsule_ref"] != repo_ref(TOS_REPO, TOS_ZARATHUSTRA_ROUTE_CAPSULE_PATH):
        fail(
            "ToS Zarathustra route retrieval pack route_capsule_ref must stay "
            "aligned with the canonical Zarathustra capsule"
        )
    if (
        route["relation_pack_ref"]
        != repo_ref(TOS_REPO, TOS_ZARATHUSTRA_ROUTE_RELATION_PACK_PATH)
    ):
        fail(
            "ToS Zarathustra route retrieval pack relation_pack_ref must stay "
            "aligned with the canonical ToS relation pack"
        )
    route_pack_nodes = route_pack_payload.get("nodes")
    if not isinstance(route_pack_nodes, list):
        fail("ToS Zarathustra route retrieval pack validation requires AOA-K-0010 nodes[]")
    if route["route_capsule_ref"] != route_pack_payload.get("route_capsule_ref"):
        fail(
            "ToS Zarathustra route retrieval pack route_capsule_ref must match the "
            "live AOA-K-0010 route_capsule_ref"
        )
    if route["relation_pack_ref"] != route_pack_payload.get("relation_pack_ref"):
        fail(
            "ToS Zarathustra route retrieval pack relation_pack_ref must match the "
            "live AOA-K-0010 relation_pack_ref"
        )
    if route["node_type_counts"] != route_pack_payload.get("node_type_counts"):
        fail(
            "ToS Zarathustra route retrieval pack node_type_counts must match the "
            "live AOA-K-0010 counts"
        )
    if route["edge_kind_counts"] != route_pack_payload.get("edge_kind_counts"):
        fail(
            "ToS Zarathustra route retrieval pack edge_kind_counts must match the "
            "live AOA-K-0010 counts"
        )
    if route["retrieval_summary"] != TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_SUMMARY:
        fail(
            "ToS Zarathustra route retrieval pack retrieval_summary must match the "
            "current bounded adjunct wording"
        )

    route_pack_nodes_by_type = {
        node_type: [
            {
                "node_id": node["node_id"],
                "authority_ref": node["authority_ref"],
            }
            for node in route_pack_nodes
            if isinstance(node, dict) and node.get("node_type") == node_type
        ]
        for node_type in TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER
    }
    seen_handle_node_ids: set[str] = set()
    for node_type, expected_count in TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS.items():
        handle_key = f"{node_type}_handles"
        handles = route[handle_key]
        if not isinstance(handles, list) or len(handles) != expected_count:
            fail(
                "ToS Zarathustra route retrieval pack must preserve the current "
                f"handle count for '{node_type}'"
            )
        seen_node_ids: set[str] = set()
        normalized_handles: list[dict[str, str]] = []
        for index, handle in enumerate(handles):
            location = (
                "ToS Zarathustra route retrieval pack "
                f"{handle_key}[{index}]"
            )
            if not isinstance(handle, dict):
                fail(f"{location} must be an object")
            if set(handle) != {"node_id", "authority_ref"}:
                fail(
                    f"{location} must keep exactly node_id and authority_ref in the "
                    "handles-only retrieval scope"
                )
            node_id = handle["node_id"]
            authority_ref = handle["authority_ref"]
            if not isinstance(node_id, str) or not node_id.startswith("tos."):
                fail(f"{location}.node_id must keep canonical tos.* ids")
            if node_id.startswith("literal."):
                fail(f"{location}.node_id must not carry literal residue")
            if node_id in seen_node_ids:
                fail(f"{location}.node_id '{node_id}' is duplicated")
            seen_node_ids.add(node_id)
            seen_handle_node_ids.add(node_id)
            if not isinstance(authority_ref, str) or not authority_ref.startswith("Tree-of-Sophia/ToS/canon/"):
                fail(f"{location}.authority_ref must point into Tree-of-Sophia/ToS/canon/**/node.json")
            if not authority_ref.endswith("/node.json"):
                fail(f"{location}.authority_ref must resolve to a canonical node.json file")
            if authority_ref.startswith("Tree-of-Sophia/intake/") or "/intake/" in authority_ref:
                fail(f"{location}.authority_ref must not point at Tree-of-Sophia/intake")
            if authority_ref.startswith("aoa-memo/") or authority_ref.startswith("aoa-routing/"):
                fail(f"{location}.authority_ref must not point at aoa-memo or aoa-routing")
            resolve_known_ref(authority_ref, label=f"{location}.authority_ref")
            normalized_handles.append(
                {
                    "node_id": node_id,
                    "authority_ref": authority_ref,
                }
            )
        if normalized_handles != route_pack_nodes_by_type[node_type]:
            fail(
                "ToS Zarathustra route retrieval pack must preserve family handle "
                f"order and authority parity with AOA-K-0010 for '{node_type}'"
            )

    route_pack_node_ids = {
        node["node_id"]
        for node in route_pack_nodes
        if isinstance(node, dict) and isinstance(node.get("node_id"), str)
    }
    if seen_handle_node_ids != route_pack_node_ids:
        fail(
            "ToS Zarathustra route retrieval pack handles must cover exactly the "
            "node set published by AOA-K-0010"
        )

    if payload != expected_payload:
        fail(
            "ToS Zarathustra route retrieval pack must match the committed "
            "manifest-driven retrieval payload"
        )
