from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_tiny_consumer_bundle_manifest(
    surfaces_by_id: dict[str, dict[str, object]]
) -> None:
    payload = read_json(TINY_CONSUMER_BUNDLE_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("tiny consumer bundle manifest must be a JSON object")

    for key in (
        "manifest_version",
        "bundle_type",
        "source_inputs",
        "bundle_order",
        "deferred_counterpart",
        "output_paths",
    ):
        if key not in payload:
            fail(f"tiny consumer bundle manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("tiny consumer bundle manifest manifest_version must equal 1")
    if payload["bundle_type"] != "tiny_consumer_bundle":
        fail("tiny consumer bundle manifest bundle_type must equal 'tiny_consumer_bundle'")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("tiny consumer bundle manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    seen_input_names: set[str] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"tiny consumer bundle manifest source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail(f"{location} must keep name, repo, path, and role")
        if name in seen_input_names:
            fail(f"{location} duplicates source input '{name}'")
        seen_input_names.add(name)
        actual_source_inputs.add((name, repo, path, role))
        resolve_known_ref(repo_ref(repo, path), label=location)
    if actual_source_inputs != EXPECTED_TINY_CONSUMER_BUNDLE_INPUTS:
        fail("tiny consumer bundle manifest source_inputs must match the current bounded donor set")

    bundle_order = validate_unique_string_list(
        payload["bundle_order"],
        label="tiny consumer bundle manifest bundle_order",
    )
    if bundle_order != EXPECTED_TINY_CONSUMER_BUNDLE_ORDER:
        fail("tiny consumer bundle manifest bundle_order must keep the current stable bundle order")
    if set(bundle_order) != {name for name, _, _, _ in EXPECTED_TINY_CONSUMER_BUNDLE_INPUTS}:
        fail("tiny consumer bundle manifest bundle_order must reference each declared source input exactly once")

    deferred_counterpart = payload["deferred_counterpart"]
    if not isinstance(deferred_counterpart, dict):
        fail("tiny consumer bundle manifest deferred_counterpart must be an object")
    if deferred_counterpart != EXPECTED_TINY_CONSUMER_BUNDLE_DEFERRED_COUNTERPART:
        fail("tiny consumer bundle manifest deferred_counterpart must match the contract-only posture")

    surface_id = deferred_counterpart["surface_id"]
    if surface_id not in surfaces_by_id:
        fail("tiny consumer bundle manifest deferred_counterpart.surface_id must exist in the registry")
    if surfaces_by_id[surface_id].get("status") != "planned":
        fail("tiny consumer bundle manifest deferred_counterpart.surface_id must remain planned in the registry")
    resolve_known_ref(
        deferred_counterpart["federation_exposure_review_ref"],
        label="tiny consumer bundle manifest deferred_counterpart.federation_exposure_review_ref",
    )
    for index, ref in enumerate(deferred_counterpart["allowed_refs"]):
        resolve_known_ref(
            ref,
            label=f"tiny consumer bundle manifest deferred_counterpart.allowed_refs[{index}]",
        )
    for index, ref in enumerate(deferred_counterpart["forbidden_active_payload_refs"]):
        resolve_known_ref(
            ref,
            label=(
                "tiny consumer bundle manifest "
                f"deferred_counterpart.forbidden_active_payload_refs[{index}]"
            ),
        )

    if payload["output_paths"] != EXPECTED_TINY_CONSUMER_BUNDLE_OUTPUT_PATHS:
        fail("tiny consumer bundle manifest output_paths must match the committed generated output paths")
