from __future__ import annotations

from ..common import *
from ..projection_parity import *
from ..source_refs import *

def validate_bridge_example(surfaces_by_id: dict[str, dict[str, object]]) -> None:
    payload = read_json(BRIDGE_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("bridge example must be a JSON object")

    surface_id = payload.get("surface_id")
    if surface_id != "AOA-K-0007":
        fail("bridge example surface_id must equal 'AOA-K-0007'")
    if surface_id not in surfaces_by_id:
        fail("bridge example surface_id must exist in the generated registry")

    registry_entry = surfaces_by_id[surface_id]
    if registry_entry["derived_kind"] != "retrieval_surface":
        fail("AOA-K-0007 must remain a retrieval_surface")
    if registry_entry["source_class"] != "tos_text":
        fail("AOA-K-0007 must keep 'tos_text' as its primary source_class")

    for key in ("source_refs", "lineage_refs"):
        value = payload.get(key)
        validate_unique_string_list(value, label=f"bridge example '{key}'")

    for key in ("conflict_refs", "practice_refs"):
        value = payload.get(key)
        if value is None:
            continue
        validate_unique_string_list(value, label=f"bridge example '{key}'")

    axis_summary = payload.get("axis_summary")
    if not isinstance(axis_summary, str) or len(axis_summary) < 20:
        fail("bridge example 'axis_summary' must be a string of length >= 20")

def validate_bridge_envelope_example() -> None:
    payload = read_json(BRIDGE_ENVELOPE_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("bridge envelope example must be a JSON object")

    if payload.get("bridge_id") != "aoa-tos-bridge-envelope-v1":
        fail("bridge envelope example bridge_id must equal 'aoa-tos-bridge-envelope-v1'")
    if payload.get("source_class") != "tos_text":
        fail("bridge envelope example source_class must remain 'tos_text'")
    if payload.get("kag_lift_status") != "candidate":
        fail("bridge envelope example kag_lift_status must remain 'candidate'")

    source_inputs = payload.get("source_inputs")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("bridge envelope example source_inputs must be a non-empty list")
    expected_inputs = {
        ("Tree-of-Sophia", "tos_text", "primary"),
        ("aoa-memo", "memo_object", "supporting"),
    }
    actual_inputs: set[tuple[str, str, str]] = set()
    primary_count = 0
    for index, item in enumerate(source_inputs):
        location = f"bridge envelope example source_inputs[{index}]"
        if not isinstance(item, dict):
            fail(f"{location} must be an object")
        repo = item.get("repo")
        source_class = item.get("source_class")
        role = item.get("role")
        if not isinstance(repo, str) or not repo:
            fail(f"{location}.repo must be a non-empty string")
        if not isinstance(source_class, str) or not source_class:
            fail(f"{location}.source_class must be a non-empty string")
        if not isinstance(role, str) or not role:
            fail(f"{location}.role must be a non-empty string")
        if role == "primary":
            primary_count += 1
        actual_inputs.add((repo, source_class, role))
    if actual_inputs != expected_inputs:
        fail("bridge envelope example source_inputs must match the current strict bridge contract")
    if primary_count != 1:
        fail("bridge envelope example must keep exactly one primary source input")

    for index, ref in enumerate(
        validate_unique_string_list(payload.get("tos_refs"), label="bridge envelope example tos_refs")
    ):
        if not ref.startswith("Tree-of-Sophia/"):
            fail(f"bridge envelope example tos_refs[{index}] must point to Tree-of-Sophia")
        resolve_known_ref(ref, label=f"bridge envelope example tos_refs[{index}]")
    for index, ref in enumerate(
        validate_unique_string_list(payload.get("memory_refs"), label="bridge envelope example memory_refs")
    ):
        if not ref.startswith("aoa-memo/"):
            fail(f"bridge envelope example memory_refs[{index}] must point to aoa-memo")
        resolve_known_ref(ref, label=f"bridge envelope example memory_refs[{index}]")

    faces = payload.get("faces")
    if not isinstance(faces, dict):
        fail("bridge envelope example faces must be an object")
    expected_faces = {
        "retrieval_surface": "mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/tos_retrieval_axis_surface.example.json",
        "chunk_face": "aoa-memo/mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/memory_chunk_face.bridge.example.json",
        "graph_face": "aoa-memo/mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/memory_graph_face.bridge.example.json",
    }
    if set(faces) != set(expected_faces):
        fail("bridge envelope example faces must expose retrieval_surface, chunk_face, and graph_face")
    for key, expected_ref in expected_faces.items():
        value = faces.get(key)
        if value != expected_ref:
            fail(f"bridge envelope example faces.{key} must equal '{expected_ref}'")
        resolve_known_ref(value, label=f"bridge envelope example faces.{key}")
