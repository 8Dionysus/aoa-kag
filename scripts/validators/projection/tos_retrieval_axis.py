from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_tos_retrieval_axis_pack(
    payload: object,
    surfaces_by_id: dict[str, dict[str, object]],
    expected_payload: dict[str, object],
) -> None:
    if not isinstance(payload, dict):
        fail("ToS retrieval axis pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "source_inputs",
        "surface_bindings",
        "surface_id",
        "surface_name",
        "axis_count",
        "axes",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"ToS retrieval axis pack is missing required key '{key}'")

    if payload["pack_type"] != "tos_retrieval_axis_pack":
        fail("ToS retrieval axis pack pack_type must equal 'tos_retrieval_axis_pack'")
    if payload["bounded_output_contract"] != EXPECTED_TOS_RETRIEVAL_AXIS_CONTRACT:
        fail("ToS retrieval axis pack bounded_output_contract must match the current source-first guardrail")
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail("ToS retrieval axis pack source_inputs must match the manifest-driven donor set")
    if payload["surface_bindings"] != expected_payload["surface_bindings"]:
        fail("ToS retrieval axis pack surface_bindings must match the current bounded retrieval binding")

    surface_0007 = surfaces_by_id.get("AOA-K-0007")
    if surface_0007 is None or surface_0007.get("status") != "experimental":
        fail("ToS retrieval axis pack requires AOA-K-0007 to remain experimental in the generated registry")

    axes = payload["axes"]
    if not isinstance(axes, list) or len(axes) != 1:
        fail("ToS retrieval axis pack must contain exactly one axis in the current pilot")
    if payload["axis_count"] != 1:
        fail("ToS retrieval axis pack axis_count must equal 1 in the current pilot")
    axis = axes[0]
    if not isinstance(axis, dict):
        fail("ToS retrieval axis pack axis must be an object")
    for key in (
        "chunk_map_ref",
        "source_refs",
        "lineage_refs",
        "conflict_refs",
        "practice_refs",
        "bridge_surface_ref",
        "bridge_envelope_ref",
        "memo_face_refs",
    ):
        value = axis.get(key)
        if value is None:
            fail(f"ToS retrieval axis pack axis is missing required key '{key}'")
    resolve_known_ref(axis["chunk_map_ref"], label="ToS retrieval axis pack chunk_map_ref")
    resolve_known_ref(axis["bridge_surface_ref"], label="ToS retrieval axis pack bridge_surface_ref")
    resolve_known_ref(axis["bridge_envelope_ref"], label="ToS retrieval axis pack bridge_envelope_ref")
    for ref_list_key in ("source_refs", "lineage_refs", "conflict_refs", "practice_refs", "memo_face_refs"):
        refs = validate_unique_string_list(axis[ref_list_key], label=f"ToS retrieval axis pack {ref_list_key}")
        for ref in refs:
            resolve_known_ref(ref, label=f"ToS retrieval axis pack {ref_list_key}")

    if payload != expected_payload:
        fail("ToS retrieval axis pack must match the committed manifest-driven retrieval-axis payload")
