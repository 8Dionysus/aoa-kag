from __future__ import annotations

from ..common import *
from ..projection_parity import *
from ..source_refs import *

def validate_tos_text_chunk_map_example(
    expected_payload: dict[str, object],
) -> None:
    payload = read_json(TOS_TEXT_CHUNK_MAP_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("ToS text chunk map example must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_repo",
        "source_manifest_ref",
        "source_inputs",
        "surface_bindings",
        "surface_id",
        "surface_name",
        "node_id",
        "node_type",
        "source_anchor",
        "authority_surface_ref",
        "route_ref",
        "capsule_ref",
        "interpretation_layers",
        "chunk_count",
        "chunks",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"ToS text chunk map example is missing required key '{key}'")

    for key in (
        "pack_version",
        "pack_type",
        "source_repo",
        "source_manifest_ref",
        "surface_id",
        "surface_name",
        "node_id",
        "node_type",
        "source_anchor",
        "authority_surface_ref",
        "route_ref",
        "capsule_ref",
        "interpretation_layers",
        "bounded_output_contract",
    ):
        if payload[key] != expected_payload[key]:
            fail(f"ToS text chunk map example {key} must match the current bounded pilot payload")

    source_inputs = payload["source_inputs"]
    if source_inputs != expected_payload["source_inputs"]:
        fail("ToS text chunk map example source_inputs must match the current bounded donor set")
    surface_bindings = payload["surface_bindings"]
    if surface_bindings != expected_payload["surface_bindings"]:
        fail("ToS text chunk map example surface_bindings must match the current bounded chunk-map binding")

    chunks = payload["chunks"]
    if not isinstance(chunks, list) or len(chunks) != 1:
        fail("ToS text chunk map example must contain exactly one chunk")
    if payload["chunk_count"] != 1:
        fail("ToS text chunk map example chunk_count must equal 1")

    expected_chunks = expected_payload["chunks"]
    if not isinstance(expected_chunks, list):
        fail("expected ToS text chunk map payload must declare chunks")
    expected_chunk = next(
        (
            chunk
            for chunk in expected_chunks
            if isinstance(chunk, dict)
            and chunk.get("segment_id") == TOS_TEXT_CHUNK_MAP_EXAMPLE_SEGMENT_ID
        ),
        None,
    )
    if expected_chunk is None:
        fail(
            "expected ToS text chunk map payload must keep the current bounded example "
            f"segment '{TOS_TEXT_CHUNK_MAP_EXAMPLE_SEGMENT_ID}'"
        )
    if chunks[0] != expected_chunk:
        fail(
            "ToS text chunk map example must mirror the bounded "
            f"'{TOS_TEXT_CHUNK_MAP_EXAMPLE_SEGMENT_ID}' chunk with translation tension"
        )

def validate_tos_retrieval_axis_example(expected_payload: dict[str, object]) -> None:
    payload = read_json(TOS_RETRIEVAL_AXIS_EXAMPLE_PATH)
    if payload != expected_payload:
        fail("ToS retrieval axis example must match the current bounded retrieval-axis payload")

def validate_tos_zarathustra_route_pack_example(
    expected_payload: dict[str, object],
) -> None:
    payload = read_json(TOS_ZARATHUSTRA_ROUTE_PACK_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("ToS Zarathustra route pack example must be a JSON object")

    schema = read_json(TOS_ZARATHUSTRA_ROUTE_PACK_SCHEMA_PATH)
    if not isinstance(schema, dict):
        fail("ToS Zarathustra route pack schema must be a JSON object")
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(payload),
        key=lambda error: list(error.path),
    )
    if errors:
        first = errors[0]
        error_path = format_schema_path(first.path)
        if error_path:
            fail(
                "ToS Zarathustra route pack example schema violation at "
                f"'{error_path}': {first.message}"
            )
        fail(f"ToS Zarathustra route pack example schema violation: {first.message}")

    expected_nodes = expected_payload.get("nodes")
    expected_edges = expected_payload.get("edges")
    if not isinstance(expected_nodes, list) or not isinstance(expected_edges, list):
        fail("expected ToS Zarathustra route payload must declare nodes and edges")

    fixture_nodes = [
        node
        for node in expected_nodes
        if isinstance(node, dict)
        and node.get("node_id") in EXPECTED_TOS_ZARATHUSTRA_ROUTE_EXAMPLE_NODE_IDS
    ]
    fixture_edges = [
        edge
        for edge in expected_edges
        if isinstance(edge, dict)
        and edge.get("edge_id") in EXPECTED_TOS_ZARATHUSTRA_ROUTE_EXAMPLE_EDGE_IDS
    ]
    if {
        node.get("node_id") for node in fixture_nodes
    } != EXPECTED_TOS_ZARATHUSTRA_ROUTE_EXAMPLE_NODE_IDS:
        fail("expected ToS Zarathustra route payload lost a fixture node")
    if {
        edge.get("edge_id") for edge in fixture_edges
    } != EXPECTED_TOS_ZARATHUSTRA_ROUTE_EXAMPLE_EDGE_IDS:
        fail("expected ToS Zarathustra route payload lost a fixture edge")

    expected_fixture = dict(expected_payload)
    expected_fixture["nodes"] = fixture_nodes
    expected_fixture["edges"] = fixture_edges
    expected_fixture["node_count"] = len(fixture_nodes)
    expected_fixture["edge_count"] = len(fixture_edges)
    expected_fixture["node_type_counts"] = {
        node_type: sum(
            node.get("node_type") == node_type for node in fixture_nodes
        )
        for node_type in expected_payload["node_type_counts"]
    }
    expected_fixture["edge_kind_counts"] = {
        edge_kind: sum(
            edge.get("edge_kind") == edge_kind for edge in fixture_edges
        )
        for edge_kind in expected_payload["edge_kind_counts"]
    }

    if any(count < 1 for count in expected_fixture["node_type_counts"].values()):
        fail("ToS Zarathustra route fixture must cover every canonical node type")
    if any(count < 1 for count in expected_fixture["edge_kind_counts"].values()):
        fail("ToS Zarathustra route fixture must cover every canonical edge kind")
    fixture_node_ids = {node["node_id"] for node in fixture_nodes}
    if any(
        edge["from_id"] not in fixture_node_ids
        or edge["to_id"] not in fixture_node_ids
        for edge in fixture_edges
    ):
        fail("ToS Zarathustra route fixture edge endpoints must stay inside the fixture")

    if payload != expected_fixture:
        fail(
            "ToS Zarathustra route pack example must match the reviewed bounded "
            "node-type and edge-kind fixture"
        )

def validate_tos_zarathustra_route_retrieval_pack_example(
    expected_payload: dict[str, object],
) -> None:
    payload = read_json(TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_EXAMPLE_PATH)
    if payload != expected_payload:
        fail(
            "ToS Zarathustra route retrieval pack example must match the current "
            "bounded retrieval payload"
        )
