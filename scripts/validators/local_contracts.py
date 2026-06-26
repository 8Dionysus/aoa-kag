from __future__ import annotations

from .common import *
from .source_refs import *

def validate_nested_agents_docs() -> None:
    issues = validate_nested_agents.validate(REPO_ROOT)
    if issues:
        joined = "; ".join(issues)
        fail(f"nested AGENTS docs validation failed: {joined}")

def validate_mechanics_skeleton_surface() -> None:
    issues = validate_mechanics_skeleton.validate(REPO_ROOT)
    if issues:
        joined = "; ".join(issues)
        fail(f"mechanics skeleton validation failed: {joined}")

def validate_questbook_surface() -> None:
    spec = importlib.util.spec_from_file_location(
        "_aoa_kag_quest_store_validator",
        QUEST_STORE_VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        fail(f"cannot load quest-store validator: {display_path(QUEST_STORE_VALIDATOR_PATH)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        module.validate_questbook_surface(REPO_ROOT)
    except module.QuestStoreValidationError as exc:
        fail(str(exc))

def validate_antifragility_stress_surfaces() -> None:
    readme = read_text(REPO_ROOT / "README.md")
    docs_readme = read_text(REPO_ROOT / "docs" / "README.md")
    regrounding_doc = read_text(KAG_STRESS_REGROUNDING_DOC_PATH)
    quarantine_doc = read_text(KAG_PROJECTION_QUARANTINE_DOC_PATH)

    for token in ("[docs](docs/README.md)", "[mechanics](mechanics/README.md)"):
        if token not in readme:
            fail(f"README.md must link {token}")
    for token in ("stress-regrounding", "projection-quarantine"):
        if token not in docs_readme:
            fail(f"docs/README.md must mention {token}")
    for snippet in REQUIRED_KAG_STRESS_REGROUNDING_SNIPPETS:
        if snippet not in regrounding_doc:
            fail(
                "mechanics/antifragility/parts/projection-health/docs/"
                f"stress-regrounding.md is missing required stress guidance: {snippet}"
            )
    for snippet in REQUIRED_KAG_PROJECTION_QUARANTINE_SNIPPETS:
        if snippet not in quarantine_doc:
            fail(
                "mechanics/antifragility/parts/projection-quarantine/docs/"
                f"projection-quarantine.md is missing required quarantine guidance: {snippet}"
            )

    for schema_path, example_glob, example_paths in (
        (
            PROJECTION_HEALTH_RECEIPT_SCHEMA_PATH,
            "projection_health_receipt*.example.json",
            PROJECTION_HEALTH_RECEIPT_EXAMPLE_PATHS,
        ),
        (
            REGROUNDING_TICKET_SCHEMA_PATH,
            "regrounding_ticket*.example.json",
            REGROUNDING_TICKET_EXAMPLE_PATHS,
        ),
    ):
        schema = read_json(schema_path)
        if not isinstance(schema, dict):
            fail(f"{display_path(schema_path)} must remain a JSON object")
        Draft202012Validator.check_schema(schema)
        if not example_paths:
            fail(
                f"examples glob matched no files for {display_path(schema_path)}: {example_glob}"
            )
        for example_path in example_paths:
            payload = read_json(example_path)
            errors = sorted(
                Draft202012Validator(schema).iter_errors(payload),
                key=lambda error: (list(error.absolute_path), error.message),
            )
            if errors:
                first = errors[0]
                error_path = format_schema_path(list(first.absolute_path))
                if error_path:
                    fail(f"{display_path(example_path)} schema violation at '{error_path}': {first.message}")
                fail(f"{display_path(example_path)} schema violation: {first.message}")

    for projection_example_path in PROJECTION_HEALTH_RECEIPT_EXAMPLE_PATHS:
        projection_example = read_json(projection_example_path)
        example_label = display_path(projection_example_path)
        if not isinstance(projection_example, dict):
            fail(f"{example_label} must remain an object")
        bounded_scope = projection_example.get("bounded_scope")
        if not isinstance(bounded_scope, dict):
            fail(f"{example_label} bounded_scope must be an object")
        resolve_relative_ref(
            REPO_ROOT,
            str(bounded_scope.get("value")),
            label=f"{example_label} bounded_scope.value",
        )
        for index, ref in enumerate(validate_unique_string_list(
            projection_example.get("affected_generated_surfaces"),
            label=f"{example_label} affected_generated_surfaces",
        )):
            resolve_relative_ref(
                REPO_ROOT,
                ref,
                label=f"{example_label} affected_generated_surfaces[{index}]",
            )
        for index, ref in enumerate(validate_unique_string_list(
            projection_example.get("evidence_refs"),
            label=f"{example_label} evidence_refs",
        )):
            if ":" not in ref:
                resolve_known_ref(
                    ref,
                    label=f"{example_label} evidence_refs[{index}]",
                )
        for index, ref in enumerate(validate_unique_string_list(
            projection_example.get("source_fallback_refs"),
            label=f"{example_label} source_fallback_refs",
        )):
            if ":" not in ref:
                resolve_known_ref(
                    ref,
                    label=f"{example_label} source_fallback_refs[{index}]",
                )

    for regrounding_ticket_path in REGROUNDING_TICKET_EXAMPLE_PATHS:
        regrounding_ticket = read_json(regrounding_ticket_path)
        example_label = display_path(regrounding_ticket_path)
        if not isinstance(regrounding_ticket, dict):
            fail(f"{example_label} must remain an object")
        projection_ref = regrounding_ticket.get("projection_ref")
        if not isinstance(projection_ref, str) or not projection_ref:
            fail(f"{example_label} projection_ref must be a non-empty string")
        if ":" not in projection_ref:
            resolve_known_ref(
                projection_ref,
                label=f"{example_label} projection_ref",
            )
        for index, ref in enumerate(validate_unique_string_list(
            regrounding_ticket.get("trigger_receipt_refs"),
            label=f"{example_label} trigger_receipt_refs",
        )):
            if ":" not in ref:
                resolve_known_ref(
                    ref,
                    label=f"{example_label} trigger_receipt_refs[{index}]",
                )
        for index, ref in enumerate(validate_unique_string_list(
            regrounding_ticket.get("expected_outputs"),
            label=f"{example_label} expected_outputs",
        )):
            resolve_relative_ref(
                REPO_ROOT,
                ref,
                label=f"{example_label} expected_outputs[{index}]",
            )
        for index, ref in enumerate(validate_unique_string_list(
            regrounding_ticket.get("evidence_refs"),
            label=f"{example_label} evidence_refs",
            allow_empty=True,
        )):
            if ":" not in ref:
                resolve_known_ref(
                    ref,
                    label=f"{example_label} evidence_refs[{index}]",
                )

def validate_tos_relative_surface(raw_ref: object, *, label: str) -> str:
    if not isinstance(raw_ref, str) or not raw_ref.strip():
        fail(f"{label} must be a non-empty Tree-of-Sophia-relative path")
    normalized = raw_ref.replace("\\", "/")
    if re.match(r"^[A-Za-z]:[/\\\\]", normalized) or normalized.startswith(("/", "\\")):
        fail(f"{label} must be Tree-of-Sophia-relative, not absolute")
    if ".." in Path(normalized).parts:
        fail(f"{label} must not traverse outside Tree-of-Sophia")
    if ":" in normalized:
        fail(f"{label} must stay Tree-of-Sophia-relative and must not use repo-qualified refs")
    if normalized.startswith(("aoa-kag/", "aoa-routing/")):
        fail(f"{label} must stay inside Tree-of-Sophia and must not point at downstream repos")
    resolve_relative_ref(TREE_OF_SOPHIA_ROOT, normalized, label=label)
    return normalized

def validate_tos_tiny_entry_route() -> dict[str, object]:
    route_label = repo_ref(TOS_REPO, TOS_TINY_ENTRY_ROUTE_PATH)
    payload = read_json(TREE_OF_SOPHIA_ROOT / TOS_TINY_ENTRY_ROUTE_PATH)
    if not isinstance(payload, dict):
        fail("Tree-of-Sophia tiny-entry route must be a JSON object")

    route_id = payload.get("route_id")
    if route_id != TOS_TINY_ENTRY_ROUTE_ID:
        fail(f"{route_label}.route_id must stay '{TOS_TINY_ENTRY_ROUTE_ID}'")

    root_surface = validate_tos_relative_surface(
        payload.get("root_surface"),
        label=f"{route_label}.root_surface",
    )
    if root_surface != TOS_ROOT_README_PATH:
        fail(f"{route_label}.root_surface must stay '{TOS_ROOT_README_PATH}'")

    if not isinstance(payload.get("node_kind"), str) or not payload["node_kind"]:
        fail(f"{route_label}.node_kind must be a non-empty string")
    if not isinstance(payload.get("node_id"), str) or not payload["node_id"]:
        fail(f"{route_label}.node_id must be a non-empty string")

    capsule_surface = validate_tos_relative_surface(
        payload.get("capsule_surface"),
        label=f"{route_label}.capsule_surface",
    )
    if capsule_surface != TOS_TINY_ENTRY_CAPSULE_PATH:
        fail(f"{route_label}.capsule_surface must stay '{TOS_TINY_ENTRY_CAPSULE_PATH}'")

    authority_surface = validate_tos_relative_surface(
        payload.get("authority_surface"),
        label=f"{route_label}.authority_surface",
    )
    if authority_surface != TOS_TINY_ENTRY_AUTHORITY_PATH:
        fail(f"{route_label}.authority_surface must stay '{TOS_TINY_ENTRY_AUTHORITY_PATH}'")

    validate_tos_tiny_entry_hop_surface(payload, route_label=route_label)

    fallback = validate_tos_relative_surface(
        payload.get("fallback"),
        label=f"{route_label}.fallback",
    )
    if fallback != TOS_TINY_ENTRY_FALLBACK_PATH:
        fail(f"{route_label}.fallback must stay '{TOS_TINY_ENTRY_FALLBACK_PATH}'")

    boundary = payload.get("non_identity_boundary")
    if not isinstance(boundary, str) or not boundary.strip():
        fail(f"{route_label}.non_identity_boundary must be a non-empty string")
    if "aoa-kag" not in boundary or "aoa-routing" not in boundary:
        fail(f"{route_label}.non_identity_boundary must explicitly keep aoa-kag and aoa-routing downstream")

    return payload

def validate_tos_tiny_entry_hop_surface(payload: dict[str, object], *, route_label: str) -> str:
    bounded_hop: str | None = None
    if payload.get(TOS_TINY_ENTRY_PRIMARY_HOP_FIELD) is not None:
        bounded_hop = validate_tos_relative_surface(
            payload.get(TOS_TINY_ENTRY_PRIMARY_HOP_FIELD),
            label=f"{route_label}.{TOS_TINY_ENTRY_PRIMARY_HOP_FIELD}",
        )

    legacy_hop: str | None = None
    if payload.get(TOS_TINY_ENTRY_LEGACY_HOP_FIELD) is not None:
        legacy_hop = validate_tos_relative_surface(
            payload.get(TOS_TINY_ENTRY_LEGACY_HOP_FIELD),
            label=f"{route_label}.{TOS_TINY_ENTRY_LEGACY_HOP_FIELD}",
        )

    if bounded_hop is None and legacy_hop is None:
        fail(
            f"{route_label} must define '{TOS_TINY_ENTRY_PRIMARY_HOP_FIELD}' or "
            f"'{TOS_TINY_ENTRY_LEGACY_HOP_FIELD}'"
        )

    if bounded_hop is not None and legacy_hop is not None and bounded_hop != legacy_hop:
        fail(
            f"{route_label}.{TOS_TINY_ENTRY_PRIMARY_HOP_FIELD} and "
            f"{route_label}.{TOS_TINY_ENTRY_LEGACY_HOP_FIELD} must resolve to the same surface"
        )

    hop_surface = bounded_hop or legacy_hop
    if hop_surface != TOS_TINY_ENTRY_HOP_PATH:
        fail(
            f"{route_label}.{TOS_TINY_ENTRY_PRIMARY_HOP_FIELD} must stay "
            f"'{TOS_TINY_ENTRY_HOP_PATH}' in the current KAG route scope"
        )
    return hop_surface

def validate_reasoning_artifact_descriptor(
    payload: object,
    *,
    label: str,
) -> dict[str, object]:
    if not isinstance(payload, dict):
        fail(f"{label} must be an object")
    for key in ("artifact_name", "contract_strength", "artifact_contract_refs"):
        if key not in payload:
            fail(f"{label} is missing required key '{key}'")
    artifact_name = payload["artifact_name"]
    contract_strength = payload["contract_strength"]
    artifact_contract_refs = payload["artifact_contract_refs"]
    if not isinstance(artifact_name, str) or not artifact_name:
        fail(f"{label}.artifact_name must be a non-empty string")
    if contract_strength not in ALLOWED_CONTRACT_STRENGTH:
        fail(f"{label}.contract_strength '{contract_strength}' is not allowed")
    refs = validate_unique_string_list(
        artifact_contract_refs,
        label=f"{label}.artifact_contract_refs",
    )
    for ref in refs:
        resolve_known_ref(ref, label=f"{label}.artifact_contract_refs")
    if contract_strength == "schema_backed" and not any(ref.endswith(".schema.json") for ref in refs):
        fail(f"{label} marked as schema_backed must include at least one schema ref")
    return payload
