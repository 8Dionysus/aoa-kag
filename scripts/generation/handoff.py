from __future__ import annotations

from .common import *
from .markdown import *
from .registry import build_registry_payload
from .source_refs import *

def load_counterpart_consumer_contract_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    payload = read_json(COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("counterpart consumer contract example must be a JSON object")

    registry_surfaces = registry_payload.get("surfaces")
    if not isinstance(registry_surfaces, list):
        fail("registry payload must declare surfaces")
    registry_by_id = {
        surface["id"]: surface
        for surface in registry_surfaces
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }

    surface_id = require_string(
        payload.get("surface_id"),
        label="counterpart consumer contract example surface_id",
    )
    if surface_id != "AOA-K-0008":
        fail("counterpart consumer contract example surface_id must equal 'AOA-K-0008'")

    registry_surface = registry_by_id.get(surface_id)
    if registry_surface is None:
        fail("counterpart consumer contract example surface_id must exist in the registry")
    if registry_surface.get("status") != "planned":
        fail("counterpart consumer contract example requires AOA-K-0008 to remain planned")

    contract_type = require_string(
        payload.get("contract_type"),
        label="counterpart consumer contract example contract_type",
    )
    if contract_type != "counterpart_consumer_contract":
        fail(
            "counterpart consumer contract example contract_type must equal "
            "'counterpart_consumer_contract'"
        )

    surface_status = require_string(
        payload.get("surface_status"),
        label="counterpart consumer contract example surface_status",
    )
    if surface_status != "planned":
        fail("counterpart consumer contract example surface_status must equal 'planned'")

    consumer_surface_type = require_string(
        payload.get("consumer_surface_type"),
        label="counterpart consumer contract example consumer_surface_type",
    )
    if consumer_surface_type != "reasoning_handoff_guardrail":
        fail(
            "counterpart consumer contract example consumer_surface_type must equal "
            "'reasoning_handoff_guardrail'"
        )

    allowed_return_field = require_string(
        payload.get("allowed_return_field"),
        label="counterpart consumer contract example allowed_return_field",
    )
    if allowed_return_field != "counterpart_refs":
        fail(
            "counterpart consumer contract example allowed_return_field must equal "
            "'counterpart_refs'"
        )

    federation_exposure_review_ref = ensure_local_ref_exists(
        payload.get("federation_exposure_review_ref"),
        label="counterpart consumer contract example federation_exposure_review_ref",
        allow_missing_refs={COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_REF},
    )
    if federation_exposure_review_ref != COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_REF:
        fail(
            "counterpart consumer contract example federation_exposure_review_ref must "
            f"equal '{COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_REF}'"
        )

    required_contract_refs = payload.get("required_contract_refs")
    if not isinstance(required_contract_refs, dict):
        fail("counterpart consumer contract example required_contract_refs must be an object")
    expected_required_contract_refs = {
        "counterpart_contract_doc": COUNTERPART_EDGE_CONTRACT_DOC_REF,
        "counterpart_contract_schema": COUNTERPART_EDGE_SCHEMA_REF,
        "counterpart_contract_example": COUNTERPART_EDGE_EXAMPLE_REF,
    }
    for key, expected_ref in expected_required_contract_refs.items():
        actual_ref = ensure_local_ref_exists(
            required_contract_refs.get(key),
            label=f"counterpart consumer contract example required_contract_refs.{key}",
        )
        if actual_ref != expected_ref:
            fail(
                "counterpart consumer contract example "
                f"required_contract_refs.{key} must equal '{expected_ref}'"
            )

    allowed_refs = payload.get("allowed_refs")
    if not isinstance(allowed_refs, list) or not allowed_refs:
        fail("counterpart consumer contract example allowed_refs must be a non-empty list")
    normalized_allowed_refs = ordered_unique(
        [
            ensure_local_ref_exists(
                raw_ref,
                label=f"counterpart consumer contract example allowed_refs[{index}]",
            )
            for index, raw_ref in enumerate(allowed_refs)
        ]
    )
    if len(normalized_allowed_refs) != len(allowed_refs):
        fail("counterpart consumer contract example allowed_refs must not contain duplicates")
    expected_allowed_refs = [
        COUNTERPART_CONSUMER_CONTRACT_DOC_REF,
        COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_REF,
        COUNTERPART_EDGE_CONTRACT_DOC_REF,
        COUNTERPART_EDGE_EXAMPLE_REF,
    ]
    if normalized_allowed_refs != expected_allowed_refs:
        fail(
            "counterpart consumer contract example allowed_refs must match the current "
            "contract/example-only posture"
        )

    forbidden_interpretations = payload.get("forbidden_interpretations")
    if (
        not isinstance(forbidden_interpretations, list)
        or not forbidden_interpretations
    ):
        fail(
            "counterpart consumer contract example forbidden_interpretations must be "
            "a non-empty list"
        )
    normalized_forbidden_interpretations = ordered_unique(
        [
            require_string(
                raw_value,
                label=(
                    "counterpart consumer contract example "
                    f"forbidden_interpretations[{index}]"
                ),
            )
            for index, raw_value in enumerate(forbidden_interpretations)
        ]
    )
    if len(normalized_forbidden_interpretations) != len(forbidden_interpretations):
        fail(
            "counterpart consumer contract example forbidden_interpretations must not "
            "contain duplicates"
        )
    expected_forbidden_interpretations = [
        "identity_proof",
        "routing_authority",
        "graph_sovereign_activation",
        "silent_federation_exposure",
    ]
    if normalized_forbidden_interpretations != expected_forbidden_interpretations:
        fail(
            "counterpart consumer contract example forbidden_interpretations must match "
            "the bounded counterpart contract"
        )

    payload["federation_exposure_review_ref"] = federation_exposure_review_ref

    return payload


def build_artifact_descriptor(
    artifact_name: str,
    contract_strength: str,
    artifact_contract_refs: list[str],
) -> dict[str, object]:
    refs = ordered_unique(artifact_contract_refs)
    if not refs:
        fail(f"artifact '{artifact_name}' must keep at least one contract ref")
    return {
        "artifact_name": artifact_name,
        "contract_strength": contract_strength,
        "artifact_contract_refs": refs,
    }


def build_eval_anchor_refs(eval_anchors: list[str]) -> list[str]:
    refs: list[str] = []
    for eval_anchor in eval_anchors:
        refs.append(repo_ref("aoa-evals", eval_path_for_anchor(eval_anchor)))
    return refs


def build_reasoning_handoff_scenario(
    binding: dict[str, object],
    inputs_by_name: dict[str, dict[str, str]],
    query_modes: list[str],
    return_contract: dict[str, object],
    boundary_guardrails: dict[str, str],
    kag_guardrail_refs: list[str],
) -> dict[str, object]:
    scenario_ref = binding["scenario_ref"]
    playbook_input = inputs_by_name[binding["playbook_input"]]
    eval_hook_input = inputs_by_name[binding["eval_hook_input"]]
    memo_contract_inputs = [
        inputs_by_name[input_name]
        for input_name in binding["memo_contract_inputs"]
    ]
    optional_trace_inputs = [
        inputs_by_name[input_name]
        for input_name in binding["optional_trace_inputs"]
    ]

    playbook_path = manifest_input_path(playbook_input)
    playbook_meta = read_markdown_frontmatter(playbook_path)
    playbook_id = get_frontmatter_string(
        playbook_meta,
        "id",
        label=f"playbook frontmatter for {scenario_ref}",
    )
    if playbook_id != scenario_ref:
        fail(f"playbook '{playbook_path.as_posix()}' does not match scenario '{scenario_ref}'")

    expected_artifacts = get_frontmatter_list(
        playbook_meta,
        "expected_artifacts",
        label=f"playbook frontmatter for {scenario_ref}",
    )
    eval_anchors = get_frontmatter_list(
        playbook_meta,
        "eval_anchors",
        label=f"playbook frontmatter for {scenario_ref}",
    )
    memo_contract_refs = [
        normalize_relative_ref("aoa-memo", ref)
        for ref in get_frontmatter_list(
            playbook_meta,
            "memo_contract_refs",
            label=f"playbook frontmatter for {scenario_ref}",
        )
    ]
    memo_writeback_targets = get_frontmatter_list(
        playbook_meta,
        "memo_writeback_targets",
        label=f"playbook frontmatter for {scenario_ref}",
    )

    for ref in memo_contract_refs:
        repo_name, relative_path = ref.split("/", 1)
        if not resolve_repo_path(repo_name, relative_path).exists():
            fail(f"playbook memo contract ref does not exist: {ref}")

    eval_hook_payload = read_json(manifest_input_path(eval_hook_input))
    if not isinstance(eval_hook_payload, dict):
        fail(f"eval hook fixture for {scenario_ref} must be a JSON object")
    if eval_hook_payload.get("playbook_id") != scenario_ref:
        fail(f"eval hook fixture for {scenario_ref} must keep matching playbook_id")

    verification_surface = eval_hook_payload.get("verification_surface")
    if not isinstance(verification_surface, str) or not verification_surface:
        fail(f"eval hook fixture for {scenario_ref} must keep verification_surface")
    if verification_surface not in expected_artifacts:
        fail(f"verification surface '{verification_surface}' must be declared in the playbook expected_artifacts")

    hook_eval_anchor = eval_hook_payload.get("eval_anchor")
    if not isinstance(hook_eval_anchor, str) or hook_eval_anchor not in eval_anchors:
        fail(f"eval hook fixture for {scenario_ref} must point to a playbook-declared eval anchor")

    hook_artifact_inputs = eval_hook_payload.get("artifact_inputs")
    if not isinstance(hook_artifact_inputs, list) or not hook_artifact_inputs:
        fail(f"eval hook fixture for {scenario_ref} must keep artifact_inputs")

    normalized_hook_contract_refs = [
        normalize_repo_pointer(raw_ref)
        for raw_ref in eval_hook_payload.get("artifact_contract_refs", [])
    ]
    if not normalized_hook_contract_refs:
        fail(f"eval hook fixture for {scenario_ref} must keep artifact_contract_refs")

    normalized_trace_surfaces = [
        normalize_repo_pointer(raw_ref)
        for raw_ref in eval_hook_payload.get("trace_surfaces", [])
    ]
    report_expectation = eval_hook_payload.get("report_expectation")
    if not isinstance(report_expectation, dict):
        fail(f"eval hook fixture for {scenario_ref} must keep report_expectation")

    checkpoint_contract_payload = read_json(manifest_input_path(memo_contract_inputs[0]))
    if not isinstance(checkpoint_contract_payload, dict):
        fail(f"memo contract input for {scenario_ref} must be a JSON object")
    if checkpoint_contract_payload.get("contract_type") != "checkpoint_to_memory_contract":
        fail(f"memo contract input for {scenario_ref} must keep contract_type")

    playbook_ref = manifest_input_ref(playbook_input)
    playbook_artifact_ref = f"{playbook_ref}#expected-artifacts"

    if scenario_ref == "AOA-P-0008":
        schema_refs_by_artifact: dict[str, list[str]] = {}
        for contract_ref in normalized_hook_contract_refs:
            if not contract_ref.startswith(
                "aoa-agents/mechanics/runtime-seam/parts/artifact-contracts/"
                "schemas/artifact."
            ):
                continue
            schema_name = Path(contract_ref).name
            artifact_name = schema_name.removeprefix("artifact.").removesuffix(".schema.json")
            schema_refs_by_artifact[artifact_name] = [contract_ref]

        missing_artifacts = [
            artifact_name
            for artifact_name in expected_artifacts
            if artifact_name not in schema_refs_by_artifact
        ]
        if missing_artifacts:
            fail(f"AOA-P-0008 is missing schema-backed artifact refs for: {', '.join(missing_artifacts)}")

        verification_descriptor = build_artifact_descriptor(
            "verification_result",
            "schema_backed",
            schema_refs_by_artifact["verification_result"],
        )
        supporting_descriptors = [
            build_artifact_descriptor(
                artifact_name,
                "schema_backed",
                schema_refs_by_artifact[artifact_name],
            )
            for artifact_name in expected_artifacts
            if artifact_name != "verification_result"
        ]

        witness_trace_contract = next(
            (
                source_input
                for source_input in optional_trace_inputs
                if source_input["name"] == "witness_trace_contract"
            ),
            None,
        )
        if witness_trace_contract is None:
            fail("AOA-P-0008 must declare witness_trace_contract as an optional trace input")

        witness_trace_schema = next(
            (
                source_input
                for source_input in optional_trace_inputs
                if source_input["name"] == "witness_trace_schema"
            ),
            None,
        )
        if witness_trace_schema is None:
            fail("AOA-P-0008 must declare witness_trace_schema as an optional trace input")

        optional_trace_sidecars = [
            build_artifact_descriptor(
                "WitnessTrace",
                "doc_backed",
                [manifest_input_ref(witness_trace_contract)],
            )
        ]
        continuity_surface = None
        memo_refs = ordered_unique(
            memo_contract_refs + [manifest_input_ref(witness_trace_contract)]
        )
        artifact_schema_refs = ordered_unique(
            normalized_hook_contract_refs + [manifest_input_ref(witness_trace_schema)]
        )
        delta_split = None
    elif scenario_ref == "AOA-P-0009":
        continuity_input_name = binding.get("continuity_input")
        if not isinstance(continuity_input_name, str) or not continuity_input_name:
            fail("AOA-P-0009 must declare a continuity_input")
        continuity_input = inputs_by_name[continuity_input_name]
        continuity_schema_payload = read_json(manifest_input_path(continuity_input))
        if not isinstance(continuity_schema_payload, dict):
            fail("AOA-P-0009 continuity schema must be a JSON object")

        continuity_schema_ref = manifest_input_ref(continuity_input)
        verification_descriptor = build_artifact_descriptor(
            "inquiry_checkpoint",
            "schema_backed",
            [continuity_schema_ref],
        )
        continuity_surface = build_artifact_descriptor(
            "inquiry_checkpoint",
            "schema_backed",
            [continuity_schema_ref],
        )
        supporting_descriptors = [
            build_artifact_descriptor(
                artifact_name,
                "playbook_declared",
                [playbook_artifact_ref],
            )
            for artifact_name in expected_artifacts
            if artifact_name != "inquiry_checkpoint"
        ]
        optional_trace_sidecars = []
        memo_refs = memo_contract_refs
        artifact_schema_refs = ordered_unique(
            [
                continuity_schema_ref,
                normalize_repo_pointer(
                    "repo:aoa-memo/mechanics/checkpoint/parts/checkpoint-to-memory-mapping/schemas/checkpoint-to-memory-contract.schema.json"
                ),
            ]
        )
        delta_split = {
            "memory_delta": {
                "artifact_name": "memory_delta",
                "checkpoint_field": "memory_delta_refs",
                "field_contract_ref": continuity_schema_ref,
            },
            "canon_delta": {
                "artifact_name": "canon_delta",
                "checkpoint_field": "canon_delta_refs",
                "field_contract_ref": continuity_schema_ref,
            },
        }
    else:
        fail(f"unsupported reasoning handoff scenario '{scenario_ref}'")

    if hook_artifact_inputs != expected_artifacts:
        fail(f"eval hook fixture for {scenario_ref} must match playbook expected_artifacts exactly")

    eval_anchor_refs = build_eval_anchor_refs(eval_anchors)
    verdict_bundle_ref = eval_hook_payload.get("verdict_bundle_ref")
    if not isinstance(verdict_bundle_ref, str) or not verdict_bundle_ref:
        fail(f"eval hook fixture for {scenario_ref} must keep verdict_bundle_ref")
    eval_refs = ordered_unique(
        eval_anchor_refs
        + [normalize_repo_pointer(verdict_bundle_ref)]
        + [
            normalize_repo_pointer(raw_ref)
            for raw_ref in eval_hook_payload.get("contract_test_refs", [])
        ]
    )
    if len(eval_refs) == len(eval_anchor_refs):
        fail(f"eval hook fixture for {scenario_ref} must keep contract_test_refs")

    return {
        "scenario_ref": scenario_ref,
        "playbook_ref": playbook_ref,
        "artifact_spine": {
            "verification_surface": verification_descriptor,
            "continuity_surface": continuity_surface,
            "supporting_artifacts": supporting_descriptors,
            "optional_trace_sidecars": optional_trace_sidecars,
        },
        "eval_bridge": {
            "eval_anchor_refs": eval_anchor_refs,
            "verification_surface": verification_surface,
            "trace_surfaces": normalized_trace_surfaces,
            "artifact_contract_refs": normalized_hook_contract_refs,
            "report_expectation": report_expectation,
        },
        "memo_bridge": {
            "memo_contract_refs": memo_contract_refs,
            "memo_writeback_targets": memo_writeback_targets,
            "delta_split": delta_split,
        },
        "compatible_query_modes": query_modes,
        "authoritative_refs": {
            "playbook_refs": [playbook_ref],
            "eval_refs": eval_refs,
            "memo_refs": memo_refs,
            "kag_guardrail_refs": kag_guardrail_refs,
            "artifact_schema_refs": artifact_schema_refs,
        },
        "return_contract": return_contract,
        "boundary_guardrails": boundary_guardrails,
    }


def build_reasoning_handoff_pack_payload() -> dict[str, object]:
    manifest = read_json(REASONING_HANDOFF_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("reasoning handoff manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    scenario_bindings = manifest.get("scenario_bindings")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("reasoning handoff manifest must declare source_inputs")
    if not isinstance(scenario_bindings, list) or not scenario_bindings:
        fail("reasoning handoff manifest must declare scenario_bindings")

    inputs_by_name: dict[str, dict[str, str]] = {}
    emitted_source_inputs: list[dict[str, str]] = []

    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail("reasoning handoff manifest source_inputs entries must be objects")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail("reasoning handoff manifest source_inputs must keep name, repo, path, and role")
        if name in inputs_by_name:
            fail(f"duplicate reasoning handoff source input '{name}'")

        normalized_input = {
            "name": name,
            "repo": repo,
            "path": path,
            "role": role,
        }
        if not manifest_input_path(normalized_input).exists():
            fail(f"reasoning handoff donor input does not exist: {repo_ref(repo, path)}")

        inputs_by_name[name] = normalized_input
        emitted_source_inputs.append(
            {
                "name": name,
                "repo": repo,
                "role": role,
                "ref": manifest_input_ref(normalized_input),
            }
        )

    guardrail_doc_input = inputs_by_name.get("reasoning_handoff_doc")
    if guardrail_doc_input is None:
        fail("reasoning handoff manifest must include reasoning_handoff_doc")
    guardrail_doc_path = manifest_input_path(guardrail_doc_input)

    artifact_hook_schema = inputs_by_name.get("artifact_to_verdict_hook_schema")
    if artifact_hook_schema is None:
        fail("reasoning handoff manifest must include artifact_to_verdict_hook_schema")
    hook_schema_payload = read_json(manifest_input_path(artifact_hook_schema))
    if not isinstance(hook_schema_payload, dict):
        fail("artifact_to_verdict_hook_schema must be a JSON object")

    counterpart_consumer_contract = load_counterpart_consumer_contract_payload()
    if counterpart_consumer_contract["consumer_surface_type"] != "reasoning_handoff_guardrail":
        fail(
            "counterpart consumer contract must stay bound to the reasoning handoff "
            "guardrail in the current scope"
        )

    guardrail_text = read_text(guardrail_doc_path)
    query_modes = extract_query_modes_from_doc(guardrail_doc_path)
    return_contract = {
        "must_include": extract_bullets_after_marker(
            guardrail_text,
            "Every reasoning handoff should be able to return:",
        ),
        "may_include": extract_bullets_after_marker(
            guardrail_text,
            "It may also return:",
        ),
        "normalized_return_fields": ["axis_summary"],
    }
    boundary_guardrails = extract_boundary_guardrails_from_doc(guardrail_doc_path)
    kag_guardrail_refs = ordered_unique(
        [
            manifest_input_ref(source_input)
            for source_input in inputs_by_name.values()
            if source_input["repo"] == "aoa-kag"
            and source_input["role"]
            in {
                "kag_guardrail_doc",
                "kag_guardrail_schema",
                "kag_guardrail_example",
            }
        ]
    )
    if kag_guardrail_refs != [
        REASONING_HANDOFF_GUARDRAIL_REF,
        REASONING_HANDOFF_GUARDRAIL_SCHEMA_REF,
        COUNTERPART_CONSUMER_CONTRACT_DOC_REF,
        COUNTERPART_CONSUMER_CONTRACT_SCHEMA_REF,
        COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_REF,
        COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_REF,
    ]:
        fail("reasoning handoff manifest must keep the current ordered KAG guardrail refs")

    scenarios = [
        build_reasoning_handoff_scenario(
            binding,
            inputs_by_name,
            query_modes,
            return_contract,
            boundary_guardrails,
            kag_guardrail_refs,
        )
        for binding in scenario_bindings
        if isinstance(binding, dict)
    ]
    if len(scenarios) != len(scenario_bindings):
        fail("reasoning handoff manifest scenario_bindings entries must be objects")

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_manifest_ref": REASONING_HANDOFF_MANIFEST_REF,
        "source_inputs": emitted_source_inputs,
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "bounded_output_contract": manifest["bounded_output_contract"],
    }
