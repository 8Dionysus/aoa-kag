from __future__ import annotations

from collections import Counter

from .common import *


def _provider_manifest(repo: str) -> dict[str, object]:
    manifest_path = resolve_repo_path(repo, "kag/manifest.json")
    payload = read_json(manifest_path)
    if not isinstance(payload, dict):
        fail(f"{repo} local KAG manifest must be a JSON object")
    return payload


def _provider_record_counts(repo: str) -> dict[str, int]:
    root = resolve_repo_path(repo, "kag")
    result: dict[str, int] = {}
    for group in ("nodes", "edges", "indexes", "projections", "receipts"):
        directory = root / group
        if not directory.is_dir():
            fail(f"{repo} local KAG provider is missing kag/{group}/")
        result[group] = len(sorted(directory.glob("*.json")))
        if result[group] < 1:
            fail(f"{repo} local KAG provider kag/{group}/ must contain JSON records")
    return result


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
    for entry in sorted(repos, key=lambda item: item["adoption_order"]):
        if not isinstance(entry, dict):
            fail("local KAG readiness repo entries must be objects")
        repo = require_string(entry.get("repo"), label="readiness repo")
        status = require_string(entry.get("provider_status"), label=f"{repo} provider_status")
        status_counts[status] += 1
        if status == "provider_ready":
            manifest = _provider_manifest(repo)
            providers.append(
                {
                    "repo": repo,
                    "adoption_order": entry["adoption_order"],
                    "local_kag_path": "kag/",
                    "manifest_ref": "kag/manifest.json",
                    "record_class_coverage": entry["first_record_classes"],
                    "record_counts": _provider_record_counts(repo),
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
                    "source": "{repo}/kag/{record_class}/",
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
