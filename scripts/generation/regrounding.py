from __future__ import annotations

from .common import *
from .registry import build_registry_payload
from .source_refs import load_source_owned_export_dependencies

def build_return_regrounding_pack_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(RETURN_REGROUNDING_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("return regrounding manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    mode_bindings = manifest.get("mode_bindings")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("return regrounding manifest must declare source_inputs")
    if not isinstance(mode_bindings, list) or not mode_bindings:
        fail("return regrounding manifest must declare mode_bindings")

    registry_surfaces = registry_payload.get("surfaces")
    if not isinstance(registry_surfaces, list):
        fail("registry manifest must declare surfaces")
    registry_by_id = {
        surface["id"]: surface
        for surface in registry_surfaces
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }
    for surface_id, expected_status in RETURN_REGROUNDING_EXPECTED_REGISTRY_POSTURE.items():
        surface = registry_by_id.get(surface_id)
        if surface is None:
            fail(f"return regrounding pack requires registry surface '{surface_id}'")
        if surface.get("status") != expected_status:
            fail(
                f"return regrounding pack requires {surface_id} to remain "
                f"'{expected_status}'"
            )

    inputs_by_name: dict[str, dict[str, str]] = {}
    emitted_source_inputs: list[dict[str, str]] = []
    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail("return regrounding manifest source_inputs entries must be objects")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail(
                "return regrounding manifest source_inputs must keep name, repo, path, and role"
            )
        if name in inputs_by_name:
            fail(f"duplicate return regrounding source input '{name}'")

        normalized_input = {
            "name": name,
            "repo": repo,
            "path": path,
            "role": role,
        }
        input_path = manifest_input_path(normalized_input)
        allow_same_run_generated_input = (
            repo == "aoa-kag" and path in RETURN_REGROUNDING_ALLOWED_SAME_RUN_INPUTS
        )
        if not input_path.exists() and not allow_same_run_generated_input:
            fail(
                "return regrounding donor input does not exist: "
                + manifest_input_ref(normalized_input)
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

    missing_inputs = [
        name for name in RETURN_REGROUNDING_EXPECTED_INPUT_REFS if name not in inputs_by_name
    ]
    if missing_inputs:
        fail(
            "return regrounding manifest is missing required inputs: "
            + ", ".join(sorted(missing_inputs))
        )
    for input_name, expected_ref in RETURN_REGROUNDING_EXPECTED_INPUT_REFS.items():
        actual_ref = manifest_input_ref(inputs_by_name[input_name])
        if actual_ref != expected_ref:
            fail(
                f"return regrounding manifest {input_name} must point to "
                f"'{expected_ref}'"
            )

    dependency_refs_by_id, _ = load_source_owned_export_dependencies()

    modes: list[dict[str, object]] = []
    seen_mode_refs: set[str] = set()
    for binding in mode_bindings:
        if not isinstance(binding, dict):
            fail("return regrounding manifest mode_bindings entries must be objects")
        mode_ref = binding.get("mode_ref")
        primary_input = binding.get("primary_input")
        supporting_inputs = binding.get("supporting_inputs")
        dependency_refs = binding.get("dependency_refs", [])
        if not isinstance(mode_ref, str) or not mode_ref:
            fail("return regrounding mode binding must keep mode_ref")
        if mode_ref in seen_mode_refs:
            fail(f"duplicate return regrounding mode '{mode_ref}'")
        seen_mode_refs.add(mode_ref)
        if mode_ref not in RETURN_REGROUNDING_MODE_DETAILS:
            fail(f"unsupported return regrounding mode '{mode_ref}'")
        if not isinstance(primary_input, str) or not primary_input:
            fail(f"return regrounding mode '{mode_ref}' must keep primary_input")
        if not isinstance(supporting_inputs, list) or not supporting_inputs:
            fail(
                f"return regrounding mode '{mode_ref}' must keep supporting_inputs"
            )
        if not all(isinstance(value, str) and value for value in supporting_inputs):
            fail(
                f"return regrounding mode '{mode_ref}'.supporting_inputs contains an invalid entry"
            )
        if not isinstance(dependency_refs, list):
            fail(
                f"return regrounding mode '{mode_ref}'.dependency_refs must be a list when present"
            )
        if not all(isinstance(value, str) and value for value in dependency_refs):
            fail(
                f"return regrounding mode '{mode_ref}'.dependency_refs contains an invalid entry"
            )

        details = RETURN_REGROUNDING_MODE_DETAILS[mode_ref]
        if primary_input != details["primary_input"]:
            fail(
                f"return regrounding mode '{mode_ref}' must keep primary_input "
                f"'{details['primary_input']}'"
            )
        if supporting_inputs != details["supporting_inputs"]:
            fail(
                f"return regrounding mode '{mode_ref}' must keep the current supporting_inputs order"
            )
        if primary_input not in inputs_by_name:
            fail(
                f"return regrounding mode '{mode_ref}' references unknown primary input '{primary_input}'"
            )
        for supporting_input in supporting_inputs:
            if supporting_input not in inputs_by_name:
                fail(
                    "return regrounding mode "
                    f"'{mode_ref}' references unknown supporting input '{supporting_input}'"
                )
        for dependency_ref in dependency_refs:
            if dependency_ref not in dependency_refs_by_id:
                fail(
                    f"return regrounding mode '{mode_ref}' references unknown dependency '{dependency_ref}'"
                )
        if dependency_refs != details["dependency_refs"]:
            fail(
                f"return regrounding mode '{mode_ref}' must keep the current dependency_refs"
            )

        modes.append(
            {
                "mode_id": mode_ref,
                "used_when": details["used_when"],
                "query_mode_hint": details["query_mode_hint"],
                "trigger_surface_refs": list(details["trigger_surface_refs"]),
                "stronger_refs": list(details["stronger_refs"]),
                "supporting_surface_refs": list(details["supporting_surface_refs"]),
                "preserved_fields": list(details["preserved_fields"]),
                "reentry_note": details["reentry_note"],
                "non_identity_boundary": details["non_identity_boundary"],
                "prohibited_promotions": list(details["prohibited_promotions"]),
            }
        )

    if [mode["mode_id"] for mode in modes] != RETURN_REGROUNDING_MODE_ORDER:
        fail("return regrounding manifest mode_bindings must keep the current stable mode order")

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_manifest_ref": RETURN_REGROUNDING_MANIFEST_REF,
        "source_inputs": emitted_source_inputs,
        "mode_count": len(modes),
        "modes": modes,
        "bounded_output_contract": manifest["bounded_output_contract"],
    }
