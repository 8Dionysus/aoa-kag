from __future__ import annotations

from ..common import *
from ..projection_parity import *
from ..source_refs import *

def validate_federation_export_registry_example() -> None:
    payload = read_json(FEDERATION_EXPORT_REGISTRY_EXAMPLE_PATH)
    validate_federation_export_registry_pack(payload, payload)
    if not isinstance(payload, dict):
        fail("federation export registry example must be a JSON object")

    exports = payload["exports"]
    if len(exports) != 3:
        fail("federation export registry example must keep the current three-donor illustration")
    memo_export = next(
        (export for export in exports if export.get("owner_repo") == "aoa-memo"),
        None,
    )
    if memo_export is None:
        fail("federation export registry example must include aoa-memo as a registry-only donor")
    if memo_export["activation"] != {
        "registry_visible": True,
        "spine_visible": False,
        "routing_visible": False,
    }:
        fail(
            "federation export registry example aoa-memo activation must keep the "
            "registry-only donor posture"
        )
    if memo_export["source_inputs"] != EXPECTED_MEMO_KAG_EXPORT_SOURCE_INPUTS:
        fail(
            "federation export registry example aoa-memo source_inputs must keep the "
            "memo-primary / Tree-of-Sophia-supporting split"
        )
    if memo_export["consumed_by"] != []:
        fail("federation export registry example aoa-memo consumed_by must stay empty")

def validate_federation_kag_export_example() -> None:
    payload = read_json(FEDERATION_KAG_EXPORT_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("federation KAG export example must be a JSON object")

    for key in (
        "owner_repo",
        "kind",
        "object_id",
        "primary_question",
        "summary_50",
        "summary_200",
        "source_inputs",
        "entry_surface",
        "section_handles",
        "direct_relations",
        "provenance_note",
        "non_identity_boundary",
    ):
        if key not in payload:
            fail(f"federation KAG export example is missing required key '{key}'")

    owner_repo = payload["owner_repo"]
    kind = payload["kind"]
    object_id = payload["object_id"]
    primary_question = payload["primary_question"]
    summary_50 = payload["summary_50"]
    summary_200 = payload["summary_200"]
    provenance_note = payload["provenance_note"]
    non_identity_boundary = payload["non_identity_boundary"]

    if owner_repo != "aoa-techniques":
        fail("federation KAG export example owner_repo must equal 'aoa-techniques'")
    if kind != "technique":
        fail("federation KAG export example kind must equal 'technique'")
    if not isinstance(object_id, str) or not re.match(r"^AOA-T-[0-9]{4}$", object_id):
        fail("federation KAG export example object_id must be an AOA technique id")
    for label, value, min_length in (
        ("primary_question", primary_question, 10),
        ("summary_50", summary_50, 10),
        ("summary_200", summary_200, 20),
        ("provenance_note", provenance_note, 10),
        ("non_identity_boundary", non_identity_boundary, 10),
    ):
        if not isinstance(value, str) or len(value) < min_length:
            fail(f"federation KAG export example {label} must be a string of length >= {min_length}")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("federation KAG export example source_inputs must be a non-empty list")
    primary_count = 0
    for index, source_input in enumerate(source_inputs):
        location = f"federation KAG export example source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        repo = source_input.get("repo")
        source_class = source_input.get("source_class")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (repo, source_class, role)):
            fail(f"{location} must keep repo, source_class, and role")
        if role == "primary":
            primary_count += 1
    if primary_count != 1:
        fail("federation KAG export example source_inputs must contain exactly one primary input")

    entry_surface = payload["entry_surface"]
    if not isinstance(entry_surface, dict):
        fail("federation KAG export example entry_surface must be an object")
    for key in ("repo", "path", "match_key", "match_value"):
        if key not in entry_surface:
            fail(f"federation KAG export example entry_surface is missing '{key}'")
    entry_repo = entry_surface["repo"]
    entry_path = entry_surface["path"]
    match_key = entry_surface["match_key"]
    match_value = entry_surface["match_value"]
    if not all(isinstance(value, str) and value for value in (entry_repo, entry_path, match_key, match_value)):
        fail("federation KAG export example entry_surface fields must be non-empty strings")
    resolve_known_ref(repo_ref(entry_repo, entry_path), label="federation KAG export example entry_surface")
    if match_value != object_id:
        fail("federation KAG export example entry_surface.match_value must equal object_id")

    section_handles = validate_unique_string_list(
        payload["section_handles"],
        label="federation KAG export example section_handles",
    )
    if not section_handles:
        fail("federation KAG export example section_handles must not be empty")

    direct_relations = payload["direct_relations"]
    if not isinstance(direct_relations, list):
        fail("federation KAG export example direct_relations must be a list")
    for index, relation in enumerate(direct_relations):
        location = f"federation KAG export example direct_relations[{index}]"
        if not isinstance(relation, dict):
            fail(f"{location} must be an object")
        relation_type = relation.get("relation_type")
        target_ref = relation.get("target_ref")
        if not all(isinstance(value, str) and value for value in (relation_type, target_ref)):
            fail(f"{location} must keep relation_type and target_ref")
        resolve_known_ref(target_ref, label=location)
