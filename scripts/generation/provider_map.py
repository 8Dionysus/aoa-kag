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


def _provider_manifest(
    repo: str, fallback_provider: dict[str, object] | None
) -> dict[str, object]:
    manifest_path = resolve_repo_path(repo, "kag/manifest.json")
    if not manifest_path.exists() and fallback_provider is not None:
        return fallback_provider
    payload = read_json(manifest_path)
    if not isinstance(payload, dict):
        fail(f"{repo} local KAG manifest must be a JSON object")
    return payload


def _provider_record_counts(
    repo: str, fallback_provider: dict[str, object] | None
) -> dict[str, int]:
    root = resolve_repo_path(repo, "kag")
    if not root.exists() and fallback_provider is not None:
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
        result[group] = len(sorted(directory.glob("*.json")))
        if result[group] < 1:
            fail(f"{repo} local KAG provider kag/{group}/ must contain JSON records")
    return result


def _provider_freshness_handles(
    repo: str, fallback_provider: dict[str, object] | None
) -> list[dict[str, object]]:
    root = resolve_repo_path(repo, "kag")
    if not root.exists() and fallback_provider is not None:
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
        checked_ref = require_string(
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
    for entry in sorted(repos, key=lambda item: item["adoption_order"]):
        if not isinstance(entry, dict):
            fail("local KAG readiness repo entries must be objects")
        repo = require_string(entry.get("repo"), label="readiness repo")
        status = require_string(entry.get("provider_status"), label=f"{repo} provider_status")
        status_counts[status] += 1
        if status == "provider_ready":
            fallback_provider = fallback_providers.get(repo)
            manifest = _provider_manifest(repo, fallback_provider)
            providers.append(
                {
                    "repo": repo,
                    "provider_status": status,
                    "adoption_order": entry["adoption_order"],
                    "local_kag_path": "kag/",
                    "manifest_ref": "kag/manifest.json",
                    "record_class_coverage": entry["first_record_classes"],
                    "record_counts": _provider_record_counts(repo, fallback_provider),
                    "freshness_handles": _provider_freshness_handles(repo, fallback_provider),
                    "source_surfaces": manifest["source_surfaces"],
                    "validation_routes": manifest["validation_routes"],
                    "consumer_routes": manifest["consumer_routes"],
                    "owner_return_routes": manifest["owner_return_routes"],
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

    return {
        "artifact_type": "local_kag_provider_map",
        "schema_version": "aoa-local-kag-provider-map-v1",
        "owner_repo": "aoa-kag",
        "source_ref": "manifests/local_kag_readiness.json",
        "provider_status_counts": dict(sorted(status_counts.items())),
        "providers": providers,
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
                    "uri_template": "aoa-kag://registry/provider-map",
                    "source": "aoa-kag/generated/local_kag_provider_map.min.json",
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
                "freshness_check",
                "source_return_lookup",
                "registry_slice",
                "composition_slice",
                "validation_status",
            ],
            "prompts": [
                "bounded_provider_query",
                "source_return_summary",
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
    }
