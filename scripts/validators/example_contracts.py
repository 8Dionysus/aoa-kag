from __future__ import annotations

from .common import *
from .projection_parity import *
from .source_refs import *

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
    if payload != expected_payload:
        fail(
            "ToS Zarathustra route pack example must match the current bounded "
            "canonical route payload"
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

def validate_return_regrounding_example(expected_payload: dict[str, object]) -> None:
    payload = read_json(RETURN_REGROUNDING_EXAMPLE_PATH)
    validate_return_regrounding_pack(payload, expected_payload)

def validate_kag_maturity_governance_example() -> None:
    schema = read_json(KAG_MATURITY_GOVERNANCE_SCHEMA_PATH)
    if not isinstance(schema, dict):
        fail("KAG maturity governance schema must be a JSON object")
    Draft202012Validator.check_schema(schema)

    payload = read_json(KAG_MATURITY_GOVERNANCE_EXAMPLE_PATH)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(payload),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    if errors:
        first = errors[0]
        error_path = format_schema_path(list(first.absolute_path))
        if error_path:
            fail(
                f"{display_path(KAG_MATURITY_GOVERNANCE_EXAMPLE_PATH)} schema violation at "
                f"'{error_path}': {first.message}"
            )
        fail(
            f"{display_path(KAG_MATURITY_GOVERNANCE_EXAMPLE_PATH)} schema violation: "
            f"{first.message}"
        )

    if not isinstance(payload, dict):
        fail("KAG maturity governance example must be a JSON object")
    if payload.get("pack_type") != "kag_maturity_governance":
        fail("KAG maturity governance example pack_type must equal 'kag_maturity_governance'")
    if payload.get("source_manifest_ref") != KAG_MATURITY_GOVERNANCE_MANIFEST_REF:
        fail(
            "KAG maturity governance example source_manifest_ref must point to "
            f"{KAG_MATURITY_GOVERNANCE_MANIFEST_REF}"
        )
    if payload.get("stability_tier_count") != len(payload.get("stability_tiers", [])):
        fail("KAG maturity governance example stability_tier_count must equal the number of tiers")
    if payload.get("surface_count") != len(payload.get("surfaces", [])):
        fail("KAG maturity governance example surface_count must equal the number of surfaces")
    if payload.get("owner_wait_state_count") != len(payload.get("owner_wait_states", [])):
        fail("KAG maturity governance example owner_wait_state_count must equal the number of owner wait states")

    surfaces = payload.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        fail("KAG maturity governance example surfaces must be a non-empty list")
    example_surface = surfaces[0]
    if not isinstance(example_surface, dict):
        fail("KAG maturity governance example first surface must be an object")
    if example_surface.get("surface_id") != "AOA-K-0008":
        fail("KAG maturity governance example must center the planned-only AOA-K-0008 posture")
    if example_surface.get("stability_tier") != "planned_contract_only":
        fail("KAG maturity governance example first surface must stay planned_contract_only")
    for proof_ref in validate_unique_string_list(
        example_surface.get("proof_expectation_refs"),
        label="KAG maturity governance example proof_expectation_refs",
    ):
        resolve_aoa_evals_ref(proof_ref, label="KAG maturity governance example proof_expectation_refs")
    for field_name in (
        "stress_receipt_schema_ref",
        "regrounding_ticket_schema_ref",
        "stress_doc_ref",
        "quarantine_doc_ref",
        "regrounding_pack_ref",
    ):
        projection_recovery = payload.get("projection_recovery")
        if not isinstance(projection_recovery, dict):
            fail("KAG maturity governance example projection_recovery must be an object")
        ref = projection_recovery.get(field_name)
        if not isinstance(ref, str) or not ref:
            fail(f"KAG maturity governance example projection_recovery.{field_name} must be a non-empty string")
        resolve_known_ref(
            ref,
            label=f"KAG maturity governance example projection_recovery.{field_name}",
        )

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

def validate_cross_source_node_projection_example(expected_payload: dict[str, object]) -> None:
    payload = read_json(CROSS_SOURCE_NODE_PROJECTION_EXAMPLE_PATH)
    if payload != expected_payload:
        fail("cross-source node projection example must match the current bounded projection payload")

def validate_tiny_consumer_bundle_example(expected_payload: dict[str, object]) -> None:
    payload = read_json(TINY_CONSUMER_BUNDLE_EXAMPLE_PATH)
    if payload != expected_payload:
        fail("tiny consumer bundle example must match the current bundle payload")

def validate_counterpart_federation_exposure_review_example(
    expected_payload: dict[str, object],
) -> None:
    payload = read_json(COUNTERPART_FEDERATION_EXPOSURE_REVIEW_EXAMPLE_PATH)
    if payload != expected_payload:
        fail(
            "counterpart federation exposure review example must match the current "
            "review payload"
        )

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

def validate_counterpart_example(surfaces_by_id: dict[str, dict[str, object]]) -> None:
    payload = read_json(COUNTERPART_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("counterpart example must be a JSON object")

    surface_id = payload.get("surface_id")
    if surface_id != "AOA-K-0008":
        fail("counterpart example surface_id must equal 'AOA-K-0008'")
    if surface_id not in surfaces_by_id:
        fail("counterpart example surface_id must exist in the generated registry")

    registry_entry = surfaces_by_id[surface_id]
    if registry_entry["derived_kind"] != "edge_projection":
        fail("AOA-K-0008 must remain an edge_projection")
    if registry_entry["status"] != "planned":
        fail("AOA-K-0008 must remain planned in the registry")
    if registry_entry["source_class"] != "tos_text":
        fail("AOA-K-0008 must keep 'tos_text' as its primary source_class")

    mappings = payload.get("mappings")
    if not isinstance(mappings, list) or not mappings:
        fail("counterpart example 'mappings' must be a non-empty list")

    seen_mapping_ids: set[str] = set()
    seen_modes: set[str] = set()
    source_inputs = registry_entry.get("source_inputs")
    supporting_repos = {
        item["repo"]
        for item in source_inputs
        if isinstance(item, dict) and item.get("role") == "supporting"
    }

    for index, mapping in enumerate(mappings):
        location = f"counterpart example mappings[{index}]"
        if not isinstance(mapping, dict):
            fail(f"{location} must be an object")
        for key in (
            "mapping_id",
            "concept_ref",
            "operational_ref",
            "counterpart_mode",
            "evidence_note",
            "non_identity_note",
        ):
            if key not in mapping:
                fail(f"{location} is missing required key '{key}'")

        mapping_id = mapping["mapping_id"]
        concept_ref = mapping["concept_ref"]
        operational_ref = mapping["operational_ref"]
        counterpart_mode = mapping["counterpart_mode"]
        evidence_note = mapping["evidence_note"]
        non_identity_note = mapping["non_identity_note"]
        supporting_refs = mapping.get("supporting_refs")

        if not isinstance(mapping_id, str) or len(mapping_id) < 1:
            fail(f"{location}.mapping_id must be a non-empty string")
        if mapping_id in seen_mapping_ids:
            fail(f"{location}.mapping_id '{mapping_id}' is duplicated")
        seen_mapping_ids.add(mapping_id)

        if not isinstance(concept_ref, str) or not concept_ref.startswith("Tree-of-Sophia/"):
            fail(f"{location}.concept_ref must point to a Tree-of-Sophia surface")
        if not isinstance(operational_ref, str) or "/" not in operational_ref:
            fail(f"{location}.operational_ref must be a non-empty repo-qualified string")
        operational_repo = operational_ref.split("/", 1)[0]
        if operational_repo not in supporting_repos:
            fail(f"{location}.operational_ref repo '{operational_repo}' must match a supporting source repo")

        if counterpart_mode not in ALLOWED_COUNTERPART_MODE:
            fail(f"{location}.counterpart_mode '{counterpart_mode}' is not allowed")
        seen_modes.add(counterpart_mode)

        if not isinstance(evidence_note, str) or len(evidence_note) < 20:
            fail(f"{location}.evidence_note must be a string of length >= 20")
        if not isinstance(non_identity_note, str) or len(non_identity_note) < 20:
            fail(f"{location}.non_identity_note must be a string of length >= 20")

        if supporting_refs is not None:
            refs = validate_unique_string_list(
                supporting_refs,
                label=f"{location}.supporting_refs",
            )
            for supporting_ref in refs:
                if "/" not in supporting_ref:
                    fail(f"{location}.supporting_refs contains an invalid repo-qualified ref")
                supporting_repo = supporting_ref.split("/", 1)[0]
                if supporting_repo not in supporting_repos:
                    fail(f"{location}.supporting_refs repo '{supporting_repo}' must match a supporting source repo")

    if seen_modes != ALLOWED_COUNTERPART_MODE:
        fail("counterpart example must cover all supported counterpart modes at least once")

def validate_counterpart_consumer_contract_example(
    surfaces_by_id: dict[str, dict[str, object]]
) -> None:
    payload = read_json(COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("counterpart consumer contract example must be a JSON object")

    for key in (
        "contract_type",
        "surface_id",
        "surface_status",
        "consumer_surface_type",
        "allowed_return_field",
        "federation_exposure_review_ref",
        "required_contract_refs",
        "allowed_refs",
        "forbidden_interpretations",
    ):
        if key not in payload:
            fail(f"counterpart consumer contract example is missing required key '{key}'")

    if payload["contract_type"] != "counterpart_consumer_contract":
        fail(
            "counterpart consumer contract example contract_type must equal "
            "'counterpart_consumer_contract'"
        )
    if payload["surface_id"] != "AOA-K-0008":
        fail("counterpart consumer contract example surface_id must equal 'AOA-K-0008'")
    if payload["surface_status"] != "planned":
        fail("counterpart consumer contract example surface_status must equal 'planned'")
    if payload["consumer_surface_type"] != "reasoning_handoff_guardrail":
        fail(
            "counterpart consumer contract example consumer_surface_type must equal "
            "'reasoning_handoff_guardrail'"
        )
    if payload["allowed_return_field"] != "counterpart_refs":
        fail(
            "counterpart consumer contract example allowed_return_field must equal "
            "'counterpart_refs'"
        )
    if (
        payload["federation_exposure_review_ref"]
        != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_REF
    ):
        fail(
            "counterpart consumer contract example federation_exposure_review_ref must "
            "point to the current review artifact"
        )
    resolve_known_ref(
        payload["federation_exposure_review_ref"],
        label="counterpart consumer contract example federation_exposure_review_ref",
    )

    registry_surface = surfaces_by_id.get("AOA-K-0008")
    if registry_surface is None:
        fail("counterpart consumer contract example requires AOA-K-0008 in the generated registry")
    if registry_surface.get("status") != "planned":
        fail("counterpart consumer contract example requires AOA-K-0008 to remain planned")

    required_contract_refs = payload["required_contract_refs"]
    if not isinstance(required_contract_refs, dict):
        fail("counterpart consumer contract example required_contract_refs must be an object")
    if required_contract_refs != EXPECTED_COUNTERPART_CONSUMER_CONTRACT_REFS:
        fail(
            "counterpart consumer contract example required_contract_refs must match the "
            "current counterpart contract surfaces"
        )
    for key, ref in required_contract_refs.items():
        resolve_known_ref(
            ref,
            label=f"counterpart consumer contract example required_contract_refs.{key}",
        )

    allowed_refs = validate_unique_string_list(
        payload["allowed_refs"],
        label="counterpart consumer contract example allowed_refs",
    )
    if allowed_refs != EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS:
        fail(
            "counterpart consumer contract example allowed_refs must keep the current "
            "contract/example-only posture"
        )
    for index, ref in enumerate(allowed_refs):
        resolve_known_ref(
            ref,
            label=f"counterpart consumer contract example allowed_refs[{index}]",
        )

    forbidden_interpretations = validate_unique_string_list(
        payload["forbidden_interpretations"],
        label="counterpart consumer contract example forbidden_interpretations",
    )
    if forbidden_interpretations != EXPECTED_COUNTERPART_CONSUMER_FORBIDDEN_INTERPRETATIONS:
        fail(
            "counterpart consumer contract example forbidden_interpretations must match "
            "the bounded contract"
        )

def validate_reasoning_handoff_example() -> None:
    payload = read_json(REASONING_HANDOFF_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("reasoning handoff example must be a JSON object")

    for key in (
        "surface_type",
        "handoff_id",
        "supported_query_modes",
        "authoritative_source_refs",
        "derived_surface_refs",
        "provenance_posture",
        "return_contract",
        "boundary_guardrails",
    ):
        if key not in payload:
            fail(f"reasoning handoff example is missing required key '{key}'")

    if payload["surface_type"] != "reasoning_handoff_guardrail":
        fail("reasoning handoff example surface_type must equal 'reasoning_handoff_guardrail'")

    handoff_id = payload["handoff_id"]
    if not isinstance(handoff_id, str) or len(handoff_id) < 3:
        fail("reasoning handoff example handoff_id must be a string of length >= 3")

    query_modes = validate_unique_string_list(
        payload["supported_query_modes"],
        label="reasoning handoff example supported_query_modes",
    )
    validate_exact_set(
        query_modes,
        ALLOWED_QUERY_MODES,
        label="reasoning handoff example supported_query_modes",
    )

    authoritative_source_refs = validate_unique_string_list(
        payload["authoritative_source_refs"],
        label="reasoning handoff example authoritative_source_refs",
    )
    validate_exact_set(
        authoritative_source_refs,
        EXPECTED_AUTHORITATIVE_SOURCE_REFS,
        label="reasoning handoff example authoritative_source_refs",
    )
    for ref in authoritative_source_refs:
        resolve_authoritative_ref(ref, label="reasoning handoff example authoritative_source_refs")

    derived_surface_refs = validate_unique_string_list(
        payload["derived_surface_refs"],
        label="reasoning handoff example derived_surface_refs",
    )
    validate_exact_set(
        derived_surface_refs,
        EXPECTED_DERIVED_SURFACE_REFS,
        label="reasoning handoff example derived_surface_refs",
    )
    for ref in derived_surface_refs:
        resolve_relative_ref(
            REPO_ROOT,
            ref,
            label="reasoning handoff example derived_surface_refs",
        )

    provenance_posture = payload["provenance_posture"]
    if provenance_posture != EXPECTED_PROVENANCE_POSTURE:
        fail("reasoning handoff example provenance_posture must match the bounded guardrail contract")

    return_contract = payload["return_contract"]
    if not isinstance(return_contract, dict):
        fail("reasoning handoff example return_contract must be an object")

    for key in ("must_include", "may_include"):
        if key not in return_contract:
            fail(f"reasoning handoff example return_contract is missing '{key}'")

    must_include = validate_unique_string_list(
        return_contract["must_include"],
        label="reasoning handoff example return_contract.must_include",
    )
    validate_exact_set(
        must_include,
        EXPECTED_RETURN_MUST_INCLUDE,
        label="reasoning handoff example return_contract.must_include",
    )

    may_include = validate_unique_string_list(
        return_contract["may_include"],
        label="reasoning handoff example return_contract.may_include",
    )
    validate_exact_set(
        may_include,
        EXPECTED_RETURN_MAY_INCLUDE,
        label="reasoning handoff example return_contract.may_include",
    )

    if set(must_include) & set(may_include):
        fail("reasoning handoff example return_contract must not overlap must_include and may_include")

    boundary_guardrails = payload["boundary_guardrails"]
    if boundary_guardrails != EXPECTED_BOUNDARY_GUARDRAILS:
        fail("reasoning handoff example boundary_guardrails must match the bounded guardrail contract")

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
