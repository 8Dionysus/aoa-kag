from __future__ import annotations

from .common import *
from .federation import build_cross_source_node_projection_payload, build_federation_spine_payload
from .handoff import build_reasoning_handoff_pack_payload, load_counterpart_consumer_contract_payload
from .registry import build_registry_payload

def build_counterpart_federation_exposure_review_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("counterpart federation exposure review manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    review_bindings = manifest.get("review_bindings")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("counterpart federation exposure review manifest must declare source_inputs")
    if not isinstance(review_bindings, list) or not review_bindings:
        fail("counterpart federation exposure review manifest must declare review_bindings")

    counterpart_consumer_contract = load_counterpart_consumer_contract_payload(
        registry_payload
    )
    reasoning_handoff_payload = build_reasoning_handoff_pack_payload()
    federation_spine_payload = build_federation_spine_payload(registry_payload)
    cross_source_payload = build_cross_source_node_projection_payload(registry_payload)
    tiny_bundle_payload = build_tiny_consumer_bundle_payload(registry_payload)

    inputs_by_name: dict[str, dict[str, str]] = {}
    emitted_source_inputs: list[dict[str, str]] = []
    allow_same_run_generated_inputs = {
        "mechanics/checkpoint/parts/reasoning-handoff/generated/reasoning_handoff_pack.min.json",
        TINY_CONSUMER_BUNDLE_MIN_OUTPUT_REF,
        FEDERATION_SPINE_MIN_OUTPUT_REF,
        CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_REF,
    }
    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail(
                "counterpart federation exposure review manifest source_inputs entries "
                "must be objects"
            )
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail(
                "counterpart federation exposure review manifest source_inputs must keep "
                "name, repo, path, and role"
            )
        if name in inputs_by_name:
            fail(f"duplicate counterpart federation exposure review source input '{name}'")

        normalized_input = {
            "name": name,
            "repo": repo,
            "path": path,
            "role": role,
        }
        input_path = manifest_input_path(normalized_input)
        allow_same_run_generated_input = repo == "aoa-kag" and path in allow_same_run_generated_inputs
        if not input_path.exists() and not allow_same_run_generated_input:
            fail(
                "counterpart federation exposure review donor input does not exist: "
                + repo_ref(repo, path)
            )
        inputs_by_name[name] = normalized_input
        emitted_source_inputs.append(
            {
                "name": name,
                "repo": repo,
                "role": role,
                "ref": manifest_input_ref(normalized_input),
            }
        )

    expected_input_order = [
        "reasoning_handoff_pack",
        "tiny_consumer_bundle",
        "federation_spine",
        "cross_source_node_projection",
        "counterpart_consumer_contract_doc",
        "counterpart_consumer_contract_example",
        "counterpart_edge_contract_doc",
        "counterpart_edge_contract_example",
    ]
    if list(inputs_by_name) != expected_input_order:
        fail(
            "counterpart federation exposure review manifest source_inputs must keep "
            "the current reviewed surface order"
        )

    current_allowed_refs = counterpart_consumer_contract["allowed_refs"]
    expected_reviewed_surface_ref = counterpart_consumer_contract[
        "federation_exposure_review_ref"
    ]
    if counterpart_consumer_contract["surface_status"] != "planned":
        fail(
            "counterpart federation exposure review requires AOA-K-0008 to remain "
            "planned in the current scope"
        )
    if expected_reviewed_surface_ref != COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_REF:
        fail(
            "counterpart federation exposure review requires the current counterpart "
            "consumer contract to stay aligned with the review artifact"
        )
    if (
        tiny_bundle_payload["deferred_counterpart"]["federation_exposure_review_ref"]
        != expected_reviewed_surface_ref
    ):
        fail(
            "counterpart federation exposure review requires the tiny consumer bundle "
            "to stay aligned with the review artifact"
        )

    reasoning_guardrail_refs = {
        ref
        for scenario in reasoning_handoff_payload["scenarios"]
        for ref in scenario["authoritative_refs"]["kag_guardrail_refs"]
    }
    if COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_REF not in reasoning_guardrail_refs:
        fail(
            "counterpart federation exposure review requires reasoning handoff "
            "guardrail refs to include the review doc"
        )

    federation_spine_refs = {
        source_input["ref"] for source_input in federation_spine_payload["source_inputs"]
    }
    if any(ref in current_allowed_refs for ref in federation_spine_refs):
        fail(
            "counterpart federation exposure review requires federation spine to avoid "
            "counterpart refs"
        )
    if any(
        repo.get("object_id") == "AOA-K-0008"
        for repo in federation_spine_payload["repos"]
        if isinstance(repo, dict)
    ):
        fail(
            "counterpart federation exposure review requires federation spine to avoid "
            "AOA-K-0008 activation hints"
        )

    cross_source_refs = {
        source_input["ref"] for source_input in cross_source_payload["source_inputs"]
    }
    if any(ref in current_allowed_refs for ref in cross_source_refs):
        fail(
            "counterpart federation exposure review requires cross-source projection to "
            "avoid counterpart refs"
        )
    if cross_source_payload["bounded_output_contract"].get("counterpart_activation") != "forbidden":
        fail(
            "counterpart federation exposure review requires cross-source projection to "
            "keep counterpart activation forbidden"
        )

    reviewed_surfaces: list[dict[str, object]] = []
    seen_surface_names: set[str] = set()
    for index, binding in enumerate(review_bindings):
        location = f"counterpart federation exposure review manifest review_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")

        surface_name = require_string(
            binding.get("surface_name"),
            label=f"{location}.surface_name",
        )
        surface_input = require_string(
            binding.get("surface_input"),
            label=f"{location}.surface_input",
        )
        exposure_posture = require_string(
            binding.get("exposure_posture"),
            label=f"{location}.exposure_posture",
        )
        review_note = require_string(
            binding.get("review_note"),
            label=f"{location}.review_note",
        )
        if surface_name in seen_surface_names:
            fail(f"{location}.surface_name must be unique")
        if surface_input not in inputs_by_name:
            fail(f"{location}.surface_input references unknown source input")
        if surface_name != surface_input:
            fail(f"{location}.surface_name must match surface_input in the current review scope")
        seen_surface_names.add(surface_name)

        reviewed_surface: dict[str, object] = {
            "surface_name": surface_name,
            "surface_ref": manifest_input_ref(inputs_by_name[surface_input]),
            "exposure_posture": exposure_posture,
            "review_note": review_note,
        }

        allowed_counterpart_refs = binding.get("allowed_counterpart_refs")
        if allowed_counterpart_refs is not None:
            if not isinstance(allowed_counterpart_refs, list) or not allowed_counterpart_refs:
                fail(f"{location}.allowed_counterpart_refs must be a non-empty list")
            normalized_allowed_counterpart_refs = ordered_unique(
                [
                    ensure_local_ref_exists(
                        raw_ref,
                        label=f"{location}.allowed_counterpart_refs[{allowed_index}]",
                    )
                    for allowed_index, raw_ref in enumerate(allowed_counterpart_refs)
                ]
            )
            if len(normalized_allowed_counterpart_refs) != len(allowed_counterpart_refs):
                fail(f"{location}.allowed_counterpart_refs must not contain duplicates")
            if normalized_allowed_counterpart_refs != current_allowed_refs:
                fail(
                    f"{location}.allowed_counterpart_refs must stay aligned with the "
                    "current counterpart consumer contract"
                )
            reviewed_surface["allowed_counterpart_refs"] = normalized_allowed_counterpart_refs

        forbidden_refs = binding.get("forbidden_refs")
        if forbidden_refs is not None:
            if not isinstance(forbidden_refs, list) or not forbidden_refs:
                fail(f"{location}.forbidden_refs must be a non-empty list")
            normalized_forbidden_refs = ordered_unique(
                [
                    ensure_local_ref_exists(
                        raw_ref,
                        label=f"{location}.forbidden_refs[{forbidden_index}]",
                    )
                    for forbidden_index, raw_ref in enumerate(forbidden_refs)
                ]
            )
            if len(normalized_forbidden_refs) != len(forbidden_refs):
                fail(f"{location}.forbidden_refs must not contain duplicates")
            if normalized_forbidden_refs != current_allowed_refs:
                fail(
                    f"{location}.forbidden_refs must stay aligned with the current "
                    "forbidden counterpart ref set"
                )
            reviewed_surface["forbidden_refs"] = normalized_forbidden_refs

        reviewed_surfaces.append(reviewed_surface)

    if [record["surface_name"] for record in reviewed_surfaces] != expected_input_order:
        fail(
            "counterpart federation exposure review manifest review_bindings must keep "
            "the current reviewed surface order"
        )

    return {
        "review_version": manifest["manifest_version"],
        "review_type": manifest["review_type"],
        "source_manifest_ref": COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_REF,
        "source_inputs": emitted_source_inputs,
        "surface_id": counterpart_consumer_contract["surface_id"],
        "surface_status": counterpart_consumer_contract["surface_status"],
        "review_status": "passed_for_planned_posture",
        "reviewed_surface_count": len(reviewed_surfaces),
        "reviewed_surfaces": reviewed_surfaces,
        "bounded_output_contract": manifest["bounded_output_contract"],
    }


def build_tiny_consumer_bundle_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(TINY_CONSUMER_BUNDLE_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("tiny consumer bundle manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    bundle_order = manifest.get("bundle_order")
    deferred_counterpart = manifest.get("deferred_counterpart")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("tiny consumer bundle manifest must declare source_inputs")
    if not isinstance(bundle_order, list) or not bundle_order:
        fail("tiny consumer bundle manifest must declare bundle_order")
    if not isinstance(deferred_counterpart, dict):
        fail("tiny consumer bundle manifest must declare deferred_counterpart")

    counterpart_consumer_contract = load_counterpart_consumer_contract_payload(
        registry_payload
    )

    inputs_by_name: dict[str, dict[str, str]] = {}
    emitted_source_inputs: list[dict[str, str]] = []
    allow_same_run_generated_inputs = {
        TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_REF,
        "mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_retrieval_axis_pack.min.json",
        FEDERATION_SPINE_MIN_OUTPUT_REF,
        CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_REF,
    }
    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail("tiny consumer bundle manifest source_inputs entries must be objects")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail(
                "tiny consumer bundle manifest source_inputs must keep name, repo, path, "
                "and role"
            )
        if name in inputs_by_name:
            fail(f"duplicate tiny consumer bundle source input '{name}'")

        normalized_input = {
            "name": name,
            "repo": repo,
            "path": path,
            "role": role,
        }
        input_path = manifest_input_path(normalized_input)
        allow_same_run_generated_input = (
            repo == "aoa-kag" and path in allow_same_run_generated_inputs
        )
        if not input_path.exists() and not allow_same_run_generated_input:
            fail(
                "tiny consumer bundle donor input does not exist: "
                + repo_ref(repo, path)
            )
        inputs_by_name[name] = normalized_input
        emitted_source_inputs.append(
            {
                "name": name,
                "repo": repo,
                "role": role,
                "ref": manifest_input_ref(normalized_input),
            }
        )

    ordered_input_names = [
        require_string(
            raw_name,
            label=f"tiny consumer bundle manifest bundle_order[{index}]",
        )
        for index, raw_name in enumerate(bundle_order)
    ]
    if len(ordered_unique(ordered_input_names)) != len(ordered_input_names):
        fail("tiny consumer bundle manifest bundle_order must not contain duplicates")
    if set(ordered_input_names) != set(inputs_by_name):
        fail(
            "tiny consumer bundle manifest bundle_order must reference each declared "
            "source input exactly once"
        )
    if ordered_input_names != [
        "tos_text_chunk_map",
        "tos_retrieval_axis_pack",
        "federation_spine",
        "cross_source_node_projection",
        "consumer_guide",
        "counterpart_consumer_contract_doc",
        "counterpart_consumer_contract_example",
    ]:
        fail(
            "tiny consumer bundle manifest bundle_order must keep the current stable "
            "consumer chain order"
        )

    surface_id = require_string(
        deferred_counterpart.get("surface_id"),
        label="tiny consumer bundle manifest deferred_counterpart.surface_id",
    )
    surface_status = require_string(
        deferred_counterpart.get("surface_status"),
        label="tiny consumer bundle manifest deferred_counterpart.surface_status",
    )
    posture = require_string(
        deferred_counterpart.get("posture"),
        label="tiny consumer bundle manifest deferred_counterpart.posture",
    )
    federation_exposure_review_ref = ensure_local_ref_exists(
        deferred_counterpart.get("federation_exposure_review_ref"),
        label=(
            "tiny consumer bundle manifest deferred_counterpart."
            "federation_exposure_review_ref"
        ),
        allow_missing_refs={COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_REF},
    )
    if surface_id != counterpart_consumer_contract["surface_id"]:
        fail(
            "tiny consumer bundle manifest deferred_counterpart.surface_id must stay "
            "aligned with the counterpart consumer contract"
        )
    if surface_status != counterpart_consumer_contract["surface_status"]:
        fail(
            "tiny consumer bundle manifest deferred_counterpart.surface_status must stay "
            "aligned with the counterpart consumer contract"
        )
    if posture != "planned_contract_only":
        fail(
            "tiny consumer bundle manifest deferred_counterpart.posture must equal "
            "'planned_contract_only'"
        )
    if (
        federation_exposure_review_ref
        != counterpart_consumer_contract["federation_exposure_review_ref"]
    ):
        fail(
            "tiny consumer bundle manifest deferred_counterpart."
            "federation_exposure_review_ref must stay aligned with the counterpart "
            "consumer contract"
        )

    allowed_refs = deferred_counterpart.get("allowed_refs")
    if not isinstance(allowed_refs, list) or not allowed_refs:
        fail(
            "tiny consumer bundle manifest deferred_counterpart.allowed_refs must be a "
            "non-empty list"
        )
    normalized_allowed_refs = ordered_unique(
        [
            ensure_local_ref_exists(
                raw_ref,
                label=(
                    "tiny consumer bundle manifest deferred_counterpart."
                    f"allowed_refs[{index}]"
                ),
            )
            for index, raw_ref in enumerate(allowed_refs)
        ]
    )
    if len(normalized_allowed_refs) != len(allowed_refs):
        fail(
            "tiny consumer bundle manifest deferred_counterpart.allowed_refs must not "
            "contain duplicates"
        )
    if normalized_allowed_refs != counterpart_consumer_contract["allowed_refs"]:
        fail(
            "tiny consumer bundle manifest deferred_counterpart.allowed_refs must stay "
            "aligned with the counterpart consumer contract"
        )

    forbidden_active_payload_refs = deferred_counterpart.get(
        "forbidden_active_payload_refs"
    )
    if (
        not isinstance(forbidden_active_payload_refs, list)
        or not forbidden_active_payload_refs
    ):
        fail(
            "tiny consumer bundle manifest deferred_counterpart."
            "forbidden_active_payload_refs must be a non-empty list"
        )
    normalized_forbidden_active_payload_refs = ordered_unique(
        [
            ensure_local_ref_exists(
                raw_ref,
                label=(
                    "tiny consumer bundle manifest deferred_counterpart."
                    f"forbidden_active_payload_refs[{index}]"
                ),
            )
            for index, raw_ref in enumerate(forbidden_active_payload_refs)
        ]
    )
    if (
        len(normalized_forbidden_active_payload_refs)
        != len(forbidden_active_payload_refs)
    ):
        fail(
            "tiny consumer bundle manifest deferred_counterpart."
            "forbidden_active_payload_refs must not contain duplicates"
        )
    if normalized_forbidden_active_payload_refs != [COUNTERPART_EDGE_EXAMPLE_REF]:
        fail(
            "tiny consumer bundle manifest deferred_counterpart."
            "forbidden_active_payload_refs must keep the current deferred counterpart "
            "payload boundary"
        )

    forbidden_interpretations = deferred_counterpart.get("forbidden_interpretations")
    if (
        not isinstance(forbidden_interpretations, list)
        or not forbidden_interpretations
    ):
        fail(
            "tiny consumer bundle manifest deferred_counterpart."
            "forbidden_interpretations must be a non-empty list"
        )
    normalized_forbidden_interpretations = ordered_unique(
        [
            require_string(
                raw_value,
                label=(
                    "tiny consumer bundle manifest deferred_counterpart."
                    f"forbidden_interpretations[{index}]"
                ),
            )
            for index, raw_value in enumerate(forbidden_interpretations)
        ]
    )
    if len(normalized_forbidden_interpretations) != len(forbidden_interpretations):
        fail(
            "tiny consumer bundle manifest deferred_counterpart."
            "forbidden_interpretations must not contain duplicates"
        )
    if normalized_forbidden_interpretations != [
        "active_retrieval_payload",
        "active_projection_payload",
    ]:
        fail(
            "tiny consumer bundle manifest deferred_counterpart."
            "forbidden_interpretations must keep the current deferred posture"
        )

    bundle_items = [
        {
            "order": index + 1,
            "name": input_name,
            "role": inputs_by_name[input_name]["role"],
            "ref": manifest_input_ref(inputs_by_name[input_name]),
        }
        for index, input_name in enumerate(ordered_input_names)
    ]

    return {
        "bundle_version": manifest["manifest_version"],
        "bundle_type": manifest["bundle_type"],
        "source_manifest_ref": TINY_CONSUMER_BUNDLE_MANIFEST_REF,
        "source_inputs": emitted_source_inputs,
        "bundle_item_count": len(bundle_items),
        "bundle_items": bundle_items,
        "deferred_counterpart": {
            "surface_id": surface_id,
            "surface_status": surface_status,
            "posture": posture,
            "federation_exposure_review_ref": federation_exposure_review_ref,
            "allowed_refs": normalized_allowed_refs,
            "forbidden_active_payload_refs": (
                normalized_forbidden_active_payload_refs
            ),
            "forbidden_interpretations": normalized_forbidden_interpretations,
        },
    }
