from __future__ import annotations

from collections import Counter

from .common import *


RECORD_CLASS_DIRECTORIES = {
    "node": "nodes",
    "edge": "edges",
    "index": "indexes",
    "projection": "projections",
    "receipt": "receipts",
}
PROVIDER_RECORD_DIRECTORIES = tuple(RECORD_CLASS_DIRECTORIES.values())


def _provider_root(repo: str) -> Path:
    root = KNOWN_REPO_ROOTS.get(repo)
    if root is None:
        fail(f"unsupported repository '{repo}'")
    return root


def _provider_fallback_allowed(repo: str, fallback_provider: dict[str, object] | None) -> bool:
    return fallback_provider is not None and not _provider_root(repo).exists()


def _is_repo_local_source_index_payload(payload: object) -> bool:
    return (
        isinstance(payload, dict)
        and payload.get("schema_version") == "aoa-repo-local-kag-index-v1"
    )


def _is_repo_local_source_index_path(group: str, path: Path) -> bool:
    return group == "indexes" and path.name == "source_surface_index.json"


def _provider_record_payloads(
    repo: str,
    fallback_provider: dict[str, object] | None,
) -> list[dict[str, object]] | None:
    root = resolve_repo_path(repo, "kag")
    if not root.exists() and _provider_fallback_allowed(repo, fallback_provider):
        return None

    records: list[dict[str, object]] = []
    for group in PROVIDER_RECORD_DIRECTORIES:
        directory = root / group
        if not directory.is_dir():
            fail(f"{repo} local KAG provider is missing kag/{group}/")
        for path in sorted(directory.glob("*.json")):
            if _is_repo_local_source_index_path(group, path):
                continue
            payload = read_json(path)
            if not isinstance(payload, dict):
                fail(
                    f"{repo} local KAG provider record must be a JSON object: "
                    f"{path.as_posix()}"
                )
            if _is_repo_local_source_index_payload(payload):
                continue
            records.append(payload)
    if not records:
        fail(f"{repo} local KAG provider must contain records")
    return records


def _existing_provider_map_by_repo() -> dict[str, dict[str, object]]:
    if not LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH.exists():
        return {}
    payload = read_json(LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH)
    if not isinstance(payload, dict):
        fail("existing local KAG provider map must be a JSON object")
    providers = payload.get("providers")
    if not isinstance(providers, list):
        fail("existing local KAG provider map must declare providers")
    result: dict[str, dict[str, object]] = {}
    for index, provider in enumerate(providers):
        if not isinstance(provider, dict):
            fail(f"existing local KAG provider map providers[{index}] must be an object")
        repo = require_string(provider.get("repo"), label=f"providers[{index}].repo")
        result[repo] = provider
    return result


def _repo_local_coverage_by_repo() -> dict[str, dict[str, object]]:
    payload = read_json(REPO_LOCAL_KAG_COVERAGE_OUTPUT_PATH)
    if not isinstance(payload, dict):
        fail("repo-local KAG coverage report must be a JSON object")
    owners = payload.get("owners")
    if not isinstance(owners, list):
        fail("repo-local KAG coverage report must declare owners")
    result: dict[str, dict[str, object]] = {}
    for index, owner in enumerate(owners):
        if not isinstance(owner, dict):
            fail(f"repo-local KAG coverage owners[{index}] must be an object")
        repo = require_string(owner.get("repo"), label=f"coverage owners[{index}].repo")
        if repo in result:
            fail(f"repo-local KAG coverage must keep one row for {repo}")
        result[repo] = owner
    return result


def _provider_repo_local_index_packet(
    repo: str,
    coverage_by_repo: dict[str, dict[str, object]],
) -> dict[str, object]:
    owner = coverage_by_repo.get(repo)
    if owner is None:
        fail(f"repo-local KAG coverage is missing provider row for {repo}")
    status = require_string(
        owner.get("index_status"),
        label=f"{repo} repo-local KAG coverage index_status",
    )
    index_files = owner.get("index_files")
    if not isinstance(index_files, list):
        fail(f"{repo} repo-local KAG coverage index_files must be a list")
    coverage = owner.get("coverage")
    if not isinstance(coverage, dict):
        fail(f"{repo} repo-local KAG coverage must declare coverage counts")
    source_index_ref = (
        "kag/indexes/source_surface_index.json"
        if status == "passed" and "kag/indexes/source_surface_index.json" in index_files
        else ""
    )
    return {
        "status": status,
        "source_index_ref": source_index_ref,
        "index_files": index_files,
        "coverage": coverage,
        "coverage_report_ref": "generated/repo_local_kag_coverage.min.json",
        "coverage_owner_key": repo,
    }


def _provider_manifest(
    repo: str, fallback_provider: dict[str, object] | None
) -> dict[str, object]:
    manifest_path = resolve_repo_path(repo, "kag/manifest.json")
    if not manifest_path.exists() and _provider_fallback_allowed(repo, fallback_provider):
        return fallback_provider
    payload = read_json(manifest_path)
    if not isinstance(payload, dict):
        fail(f"{repo} local KAG manifest must be a JSON object")
    return payload


def _provider_record_counts(
    repo: str, fallback_provider: dict[str, object] | None
) -> dict[str, int]:
    root = resolve_repo_path(repo, "kag")
    if not root.exists() and _provider_fallback_allowed(repo, fallback_provider):
        counts = fallback_provider.get("record_counts")
        if not isinstance(counts, dict):
            fail(f"{repo} fallback local KAG provider must declare record_counts")
        result: dict[str, int] = {}
        for group in PROVIDER_RECORD_DIRECTORIES:
            value = counts.get(group)
            if not isinstance(value, int) or value < 1:
                fail(f"{repo} fallback local KAG provider record_counts.{group} must be positive")
            result[group] = value
        return result
    result: dict[str, int] = {}
    for group in PROVIDER_RECORD_DIRECTORIES:
        directory = root / group
        if not directory.is_dir():
            fail(f"{repo} local KAG provider is missing kag/{group}/")
        result[group] = 0
        for path in sorted(directory.glob("*.json")):
            if _is_repo_local_source_index_path(group, path):
                continue
            payload = read_json(path)
            if _is_repo_local_source_index_payload(payload):
                continue
            result[group] += 1
        if result[group] < 1:
            fail(f"{repo} local KAG provider kag/{group}/ must contain JSON records")
    return result


def _provider_generation_profile(
    repo: str,
    readiness_entry: dict[str, object],
    manifest: dict[str, object],
    fallback_provider: dict[str, object] | None,
) -> dict[str, object]:
    records = _provider_record_payloads(repo, fallback_provider)
    if records is None and fallback_provider is not None:
        fallback_profile = fallback_provider.get("generation_profile")
        if not isinstance(fallback_profile, dict):
            fail(f"{repo} fallback local KAG provider must declare generation_profile")
        return fallback_profile
    if records is None:
        fail(f"{repo} local KAG provider records are unavailable")

    record_authoring_counts = Counter()
    record_class_counts = Counter()
    builder_counts: Counter[tuple[str, str]] = Counter()
    for index, record in enumerate(records):
        record_class = require_string(
            record.get("record_class"),
            label=f"{repo} local KAG record[{index}].record_class",
        )
        generated_or_authored = require_string(
            record.get("generated_or_authored"),
            label=f"{repo} local KAG record[{index}].generated_or_authored",
        )
        builder = record.get("builder")
        if not isinstance(builder, dict):
            fail(f"{repo} local KAG record[{index}] must declare builder")
        route = require_string(
            builder.get("route"),
            label=f"{repo} local KAG record[{index}].builder.route",
        )
        surface = require_string(
            builder.get("surface"),
            label=f"{repo} local KAG record[{index}].builder.surface",
        )
        record_authoring_counts[generated_or_authored] += 1
        record_class_counts[record_class] += 1
        builder_counts[(route, surface)] += 1

    source_surfaces = manifest.get("source_surfaces")
    if not isinstance(source_surfaces, list) or not source_surfaces:
        fail(f"{repo} local KAG manifest must declare source_surfaces")

    source_authority_counts = Counter()
    for index, source_surface in enumerate(source_surfaces):
        if not isinstance(source_surface, dict):
            fail(f"{repo} local KAG manifest source_surfaces[{index}] must be an object")
        authority = require_string(
            source_surface.get("authority"),
            label=f"{repo} local KAG manifest source_surfaces[{index}].authority",
        )
        source_authority_counts[authority] += 1

    return {
        "source_home_surfaces": readiness_entry["source_home_surfaces"],
        "candidate_source_surfaces": readiness_entry["candidate_source_surfaces"],
        "source_owned_exports": readiness_entry["source_owned_exports"],
        "graph_entities": readiness_entry["graph_entities"],
        "event_surfaces": readiness_entry["event_surfaces"],
        "document_surfaces": readiness_entry["document_surfaces"],
        "validators": readiness_entry["validators"],
        "release_gate": readiness_entry["release_gate"],
        "runtime_consumers": readiness_entry["runtime_consumers"],
        "record_authoring_counts": dict(sorted(record_authoring_counts.items())),
        "record_class_counts": dict(sorted(record_class_counts.items())),
        "source_authority_counts": dict(sorted(source_authority_counts.items())),
        "builder_routes": [
            {
                "route": route,
                "surface": surface,
                "record_count": count,
            }
            for (route, surface), count in sorted(
                builder_counts.items(),
                key=lambda item: (item[0][0], item[0][1]),
            )
        ],
    }


def _provider_freshness_handles(
    repo: str, fallback_provider: dict[str, object] | None
) -> list[dict[str, object]]:
    root = resolve_repo_path(repo, "kag")
    if not root.exists() and _provider_fallback_allowed(repo, fallback_provider):
        handles = fallback_provider.get("freshness_handles")
        if not isinstance(handles, list):
            fail(f"{repo} fallback local KAG provider must declare freshness_handles")
        return handles

    receipts_dir = root / "receipts"
    if not receipts_dir.is_dir():
        fail(f"{repo} local KAG provider is missing kag/receipts/")
    handles: list[dict[str, object]] = []
    for path in sorted(receipts_dir.glob("*.json")):
        receipt = read_json(path)
        if not isinstance(receipt, dict):
            fail(f"{repo} local KAG receipt must be a JSON object: {path.as_posix()}")
        freshness = receipt.get("freshness")
        validator = receipt.get("validator")
        if not isinstance(freshness, dict) or not isinstance(validator, dict):
            fail(f"{repo} local KAG receipt must declare freshness and validator")
        checked_ref = _provider_freshness_checked_ref(
            repo,
            freshness.get("checked_ref"),
            label=f"{repo} local KAG receipt freshness.checked_ref",
        )
        state = require_string(
            freshness.get("state"),
            label=f"{repo} local KAG receipt freshness.state",
        )
        validator_route = require_string(
            validator.get("route"),
            label=f"{repo} local KAG receipt validator.route",
        )
        handles.append(
            {
                "receipt_ref": f"kag/receipts/{path.name}",
                "checked_ref": checked_ref,
                "state": state,
                "validator": validator_route,
                "owner_return_route": receipt["owner_return_route"],
            }
        )
    if not handles:
        fail(f"{repo} local KAG provider must keep freshness receipts")
    return handles


def _provider_freshness_checked_ref(repo: str, raw_ref: object, *, label: str) -> str:
    checked_ref = ensure_repo_relative_path(raw_ref, label=label)
    if not resolve_repo_path(repo, checked_ref).exists():
        fail(f"{label} target is missing inside provider root: {checked_ref}")
    return checked_ref


def _generation_readiness_summary(
    providers: list[dict[str, object]],
    os_surfaces: list[dict[str, object]],
) -> dict[str, object]:
    record_authoring_counts = Counter()
    source_authority_counts = Counter()
    generated_record_repos: list[str] = []
    source_owned_export_repos: list[str] = []

    for provider in providers:
        repo = require_string(provider.get("repo"), label="provider repo")
        profile = provider.get("generation_profile")
        if not isinstance(profile, dict):
            fail(f"{repo} provider map entry must keep generation_profile")

        authoring_counts = profile.get("record_authoring_counts")
        if not isinstance(authoring_counts, dict):
            fail(f"{repo} generation_profile must keep record_authoring_counts")
        for key, value in authoring_counts.items():
            if not isinstance(key, str) or not isinstance(value, int):
                fail(
                    f"{repo} generation_profile record_authoring_counts must map "
                    "strings to integers"
                )
            record_authoring_counts[key] += value
        if authoring_counts.get("generated_from_source", 0) > 0:
            generated_record_repos.append(repo)

        authority_counts = profile.get("source_authority_counts")
        if not isinstance(authority_counts, dict):
            fail(f"{repo} generation_profile must keep source_authority_counts")
        for key, value in authority_counts.items():
            if not isinstance(key, str) or not isinstance(value, int):
                fail(
                    f"{repo} generation_profile source_authority_counts must map "
                    "strings to integers"
                )
            source_authority_counts[key] += value

        source_owned_exports = profile.get("source_owned_exports")
        if not isinstance(source_owned_exports, list):
            fail(f"{repo} generation_profile must keep source_owned_exports")
        if source_owned_exports:
            source_owned_export_repos.append(repo)

    os_surface_status_counts = Counter()
    surface_ids_by_status: dict[str, list[str]] = {}
    for surface in os_surfaces:
        status = require_string(
            surface.get("provider_status"),
            label="os surface provider_status",
        )
        surface_id = require_string(surface.get("surface_id"), label="os surface surface_id")
        os_surface_status_counts[status] += 1
        surface_ids_by_status.setdefault(status, []).append(surface_id)

    return {
        "provider_generation_record_counts": dict(sorted(record_authoring_counts.items())),
        "provider_source_authority_counts": dict(sorted(source_authority_counts.items())),
        "generated_record_repos": sorted(generated_record_repos),
        "source_owned_export_repos": sorted(source_owned_export_repos),
        "os_surface_status_counts": dict(sorted(os_surface_status_counts.items())),
        "os_surface_ids_by_status": {
            status: sorted(surface_ids)
            for status, surface_ids in sorted(surface_ids_by_status.items())
        },
    }


def build_local_kag_provider_map_payload() -> dict[str, object]:
    readiness = read_json(LOCAL_KAG_READINESS_MANIFEST_PATH)
    if not isinstance(readiness, dict):
        fail("local KAG readiness manifest must be a JSON object")

    repos = readiness.get("repos")
    surfaces = readiness.get("os_surfaces")
    if not isinstance(repos, list) or not isinstance(surfaces, list):
        fail("local KAG readiness manifest must declare repos and os_surfaces lists")

    status_counts = Counter()
    providers: list[dict[str, object]] = []
    remaining_routes: list[dict[str, object]] = []
    fallback_providers = _existing_provider_map_by_repo()
    coverage_by_repo = _repo_local_coverage_by_repo()
    for entry in sorted(repos, key=lambda item: item["adoption_order"]):
        if not isinstance(entry, dict):
            fail("local KAG readiness repo entries must be objects")
        repo = require_string(entry.get("repo"), label="readiness repo")
        status = require_string(entry.get("provider_status"), label=f"{repo} provider_status")
        status_counts[status] += 1
        if status == "provider_ready":
            fallback_provider = fallback_providers.get(repo)
            manifest = _provider_manifest(repo, fallback_provider)
            generation_profile = _provider_generation_profile(
                repo,
                entry,
                manifest,
                fallback_provider,
            )
            providers.append(
                {
                    "repo": repo,
                    "provider_status": status,
                    "adoption_order": entry["adoption_order"],
                    "local_kag_path": "kag/",
                    "manifest_ref": "kag/manifest.json",
                    "record_class_coverage": entry["first_record_classes"],
                    "record_counts": _provider_record_counts(repo, fallback_provider),
                    "repo_local_index": _provider_repo_local_index_packet(
                        repo,
                        coverage_by_repo,
                    ),
                    "freshness_handles": _provider_freshness_handles(repo, fallback_provider),
                    "source_surfaces": manifest["source_surfaces"],
                    "validation_routes": manifest["validation_routes"],
                    "consumer_routes": manifest["consumer_routes"],
                    "owner_return_routes": manifest["owner_return_routes"],
                    "generation_profile": generation_profile,
                    "mcp_access_shape": entry["mcp_access_shape"],
                }
            )
        else:
            remaining_routes.append(
                {
                    "repo": repo,
                    "adoption_order": entry["adoption_order"],
                    "provider_status": status,
                    "candidate_source_surfaces": entry["candidate_source_surfaces"],
                    "owner_return_routes": entry["owner_return_routes"],
                    "mcp_access_shape": entry["mcp_access_shape"],
                }
            )

    os_surface_packets = [
        {
            "surface_id": surface["surface_id"],
            "surface_class": surface["surface_class"],
            "root": surface["root"],
            "provider_status": surface["provider_status"],
            "owner_return_route": surface["owner_return_route"],
            "mcp_access_shape": surface["mcp_access_shape"],
            "candidate_source_surfaces": surface["candidate_source_surfaces"],
        }
        for surface in sorted(surfaces, key=lambda item: item["adoption_order"])
        if isinstance(surface, dict)
    ]
    generation_profiles_by_repo = {
        provider["repo"]: provider["generation_profile"]
        for provider in providers
    }
    repo_local_indexes_by_repo = {
        provider["repo"]: provider["repo_local_index"]
        for provider in providers
    }

    return {
        "artifact_type": "local_kag_provider_map",
        "schema_version": "aoa-local-kag-provider-map-v1",
        "owner_repo": "aoa-kag",
        "source_ref": "manifests/local_kag_readiness.json",
        "provider_status_counts": dict(sorted(status_counts.items())),
        "providers": providers,
        "provider_generation_profiles": generation_profiles_by_repo,
        "provider_repo_local_indexes": repo_local_indexes_by_repo,
        "remaining_routes": remaining_routes,
        "os_surfaces": os_surface_packets,
        "mcp_handoff": {
            "service_route": "abyss-stack/mcp/services/aoa-kag-mcp",
            "resource_uri_scheme": "aoa-kag://{scope}/{identifier}",
            "resource_templates": [
                {
                    "uri_template": "aoa-kag://providers/{repo}/manifest",
                    "source": "{repo}/kag/manifest.json",
                },
                {
                    "uri_template": "aoa-kag://providers/{repo}/records/{record_class}",
                    "source": "{repo}/kag/{record_class_directory}/",
                    "record_class_directory_map": RECORD_CLASS_DIRECTORIES,
                },
                {
                    "uri_template": "aoa-kag://providers/{repo}/generation",
                    "source": (
                        "aoa-kag/generated/local_kag_provider_map.min.json"
                        "#/provider_generation_profiles/{repo}"
                    ),
                },
                {
                    "uri_template": "aoa-kag://providers/{repo}/source-index",
                    "source": (
                        "aoa-kag/generated/local_kag_provider_map.min.json"
                        "#/provider_repo_local_indexes/{repo}/source_index_ref"
                    ),
                    "fallback_source": (
                        "aoa-kag/generated/local_kag_provider_map.min.json"
                        "#/provider_repo_local_indexes/{repo}/index_files"
                    ),
                    "resolution": (
                        "Dereference source_index_ref only when non-empty; "
                        "owner-specific providers expose index_files instead."
                    ),
                },
                {
                    "uri_template": "aoa-kag://providers/{repo}/repo-local-index",
                    "source": (
                        "aoa-kag/generated/local_kag_provider_map.min.json"
                        "#/provider_repo_local_indexes/{repo}"
                    ),
                },
                {
                    "uri_template": "aoa-kag://registry/provider-map",
                    "source": "aoa-kag/generated/local_kag_provider_map.min.json",
                },
                {
                    "uri_template": "aoa-kag://coverage/repo-local-source-indexes",
                    "source": "aoa-kag/generated/repo_local_kag_coverage.min.json",
                },
                {
                    "uri_template": "aoa-kag://readiness/os-surfaces",
                    "source": "aoa-kag/manifests/local_kag_readiness.json",
                },
            ],
            "root_boundaries": [
                {
                    "root_kind": "provider_home",
                    "path_template": "{repo}/kag/",
                    "purpose": "validated provider records and source-return handles",
                },
                {
                    "root_kind": "source_return",
                    "path_template": "{owner_return_route.surface}",
                    "purpose": "stronger owner surface for meaning changes",
                },
                {
                    "root_kind": "runtime_owner",
                    "path_template": "abyss-stack/mcp/services/aoa-kag-mcp",
                    "purpose": "runnable access plane and serving integration",
                },
            ],
            "tools": [
                "provider_lookup",
                "provider_status",
                "generation_route_lookup",
                "source_index_lookup",
                "repo_local_coverage_status",
                "freshness_check",
                "source_return_lookup",
                "registry_slice",
                "composition_slice",
                "validation_status",
            ],
            "prompts": [
                "bounded_provider_query",
                "source_return_summary",
                "repo_source_surface_brief",
                "cross_repo_relation_preview",
                "runtime_handoff_brief",
            ],
            "package_surfaces": [
                "AGENTS.md",
                "DESIGN.md",
                "README.md",
                "pyproject.toml",
                "src/aoa_kag_mcp/",
                "tests/",
                "scripts/validate_kag_mcp.py",
            ],
            "runtime_state_route": "abyss-stack and .aoa runtime stores",
        },
        "generation_readiness": _generation_readiness_summary(
            providers,
            os_surface_packets,
        ),
    }
