#!/usr/bin/env python3
"""Generate an OS Abyss coverage report for repo-local KAG indexes."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence

from jsonschema import Draft202012Validator

try:
    from scripts.generate_repo_local_kag_index import (
        EXCLUDED_PARTS,
        INDEX_SCHEMA_VERSION,
        REPOSITORY_INDEX_FILENAMES,
        build_index,
        build_repository_indexes,
        classification_summary,
        coverage_summary,
        git_file_paths,
        is_portable_family_control_path,
        manifest_validation_route,
        normalized_json,
        owner_type_for,
        payload_digest,
        repo_name,
        sha256_bytes,
        source_bytes,
    )
    from scripts.generation.context import KNOWN_REPO_ROOTS
    from scripts.repo_local.portable_family import (
        MANIFEST_RELATIVE_PATH,
        OS_AGGREGATE_TRACKED_BYTES_MAX,
        load_portable_family,
        reconstruct_source_index,
        receipt_path_for,
    )
    from scripts.repo_local.tiered_family import (
        CORPUS_MANIFEST_RELATIVE_PATH,
        DISTRIBUTION_SCHEMA_VERSION,
        OS_GIT_HOT_TARGET_BYTES,
        load_tiered_manifests,
        load_tiered_rows,
    )
    from scripts.provider_registry import (
        connector_repos,
        provider_roots,
        provider_repo_order,
    )
except ImportError:  # pragma: no cover - direct script execution
    from generate_repo_local_kag_index import (  # type: ignore
        EXCLUDED_PARTS,
        INDEX_SCHEMA_VERSION,
        REPOSITORY_INDEX_FILENAMES,
        build_index,
        build_repository_indexes,
        classification_summary,
        coverage_summary,
        git_file_paths,
        is_portable_family_control_path,
        manifest_validation_route,
        normalized_json,
        owner_type_for,
        payload_digest,
        repo_name,
        sha256_bytes,
        source_bytes,
    )
    from generation.context import KNOWN_REPO_ROOTS  # type: ignore
    from repo_local.portable_family import (  # type: ignore
        MANIFEST_RELATIVE_PATH,
        OS_AGGREGATE_TRACKED_BYTES_MAX,
        load_portable_family,
        reconstruct_source_index,
        receipt_path_for,
    )
    from repo_local.tiered_family import (  # type: ignore
        CORPUS_MANIFEST_RELATIVE_PATH,
        DISTRIBUTION_SCHEMA_VERSION,
        OS_GIT_HOT_TARGET_BYTES,
        load_tiered_manifests,
        load_tiered_rows,
    )
    from provider_registry import (  # type: ignore
        connector_repos,
        provider_roots,
        provider_repo_order,
    )


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OS_ROOT = Path("/srv/AbyssOS")
DEFAULT_OUTPUT = REPO_ROOT / "generated" / "repo_local_kag_coverage.json"
DEFAULT_MIN_OUTPUT = REPO_ROOT / "generated" / "repo_local_kag_coverage.min.json"
COVERAGE_PACKET_ENV = "AOA_KAG_COVERAGE_PACKET"
COVERAGE_PACKET_SCHEMA_VERSION = "aoa-kag-coverage-build-packet-v1"
COVERAGE_CANONICALIZATION_EPOCH = "portable-record-normalization-v3"
COVERAGE_PACKET_BUILDER_PATHS = (
    Path("manifests/provider_registry.json"),
    Path("schemas/local-kag-subtree.schema.json"),
    Path("schemas/repo-local-kag-coverage.schema.json"),
    Path("schemas/repo-local-kag-index.schema.json"),
    Path("scripts/generate_repo_local_kag_coverage.py"),
    Path("scripts/generate_repo_local_kag_index.py"),
    Path("scripts/repo_local/portable_family.py"),
    Path("scripts/repo_local/tiered_family.py"),
)
OWNER_STATUS = ("passed", "migration-needed", "missing", "owner-specific")
PUBLIC_OS_ROOT = "aoa-os:canonical-providers"
INDEX_SCHEMA_PATH = REPO_ROOT / "schemas" / "repo-local-kag-index.schema.json"
LOCAL_KAG_SUBTREE_SCHEMA_PATH = REPO_ROOT / "schemas" / "local-kag-subtree.schema.json"
SOURCE_SURFACE_INDEX_REL = Path("kag/indexes/source_surface_index.json")
REPOSITORY_INDEX_RELS = {
    Path("kag") / "indexes" / filename
    for filename in REPOSITORY_INDEX_FILENAMES.values()
}
COMMON_GENERATED_INDEX_RELS = {SOURCE_SURFACE_INDEX_REL, *REPOSITORY_INDEX_RELS}
REPOSITORY_INDEX_FAMILY_REFS = {
    "source": SOURCE_SURFACE_INDEX_REL.as_posix(),
    **{
        index_kind: (Path("kag") / "indexes" / filename).as_posix()
        for index_kind, filename in REPOSITORY_INDEX_FILENAMES.items()
    },
}
DOMAIN_INDEX_CATALOG_REF = "kag/indexes/domain_index_catalog.json"
META_INDEX_NAMES = {
    SOURCE_SURFACE_INDEX_REL.name,
    *(path.name for path in REPOSITORY_INDEX_RELS),
    "domain_index_catalog.json",
}
PROVIDER_REPO_ORDER = provider_repo_order()
CONNECTOR_REPOS = connector_repos()
OWNER_SPECIFIC_INDEX_NAMES = {
    "session_memory_source_inventory.json",
    "source_inventory.json",
}
OWNER_SPECIFIC_OWNER_TYPES = {
    "bundle_provider",
    "connector",
}
PROVIDER_RECORD_DIRS = ("nodes", "edges", "indexes", "projections", "receipts")
COMMON_PROFILE_COUNT_KEYS = (
    "artifact_kind",
    "primary_kind",
    "surface_state",
    "document_role",
    "mechanics_role",
    "command_role",
)
LOCAL_KAG_RECORD_SCHEMA_VERSION = "aoa-local-kag-record-v1"
PROVIDER_RECORD_SCHEMA_DEFS = {
    "nodes": "nodeRecord",
    "edges": "edgeRecord",
    "indexes": "indexRecord",
    "projections": "projectionRecord",
    "receipts": "receiptRecord",
}


def coverage_progress(label: str) -> None:
    print(f"[repo-local-kag-coverage] {label}", file=sys.stderr, flush=True)


def local_kag_record_schema(def_name: str, *, schema_id_suffix: str) -> dict[str, Any]:
    schema = json.loads(LOCAL_KAG_SUBTREE_SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise ValueError("local KAG subtree schema must be an object")
    wrapper = {
        "$schema": schema.get("$schema"),
        "$id": f"{schema.get('$id', 'local-kag-subtree')}.{schema_id_suffix}.json",
        "$defs": schema.get("$defs", {}),
        "$ref": f"#/$defs/{def_name}",
    }
    Draft202012Validator.check_schema(wrapper)
    return wrapper


def local_kag_index_record_schema() -> dict[str, Any]:
    return local_kag_record_schema("indexRecord", schema_id_suffix="indexRecord.coverage")


def local_kag_provider_record_schemas() -> dict[str, dict[str, Any]]:
    return {
        group_name: local_kag_record_schema(def_name, schema_id_suffix=f"{def_name}.coverage")
        for group_name, def_name in PROVIDER_RECORD_SCHEMA_DEFS.items()
    }


def git_root(path: Path) -> Path | None:
    try:
        output = subprocess.run(
            ("git", "rev-parse", "--show-toplevel"),
            cwd=path,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return Path(output).resolve()


def direct_owner_roots(os_root: Path) -> list[Path]:
    roots: list[Path] = []
    for child in os_root.iterdir() if os_root.is_dir() else ():
        if child.name.startswith(".") or not child.is_dir():
            continue
        if child.name in {"connectors", "bundles", "Services"}:
            continue
        if child.name.startswith("aoa-") or child.name in {
            "Agents-of-Abyss",
            "Tree-of-Sophia",
            "8Dionysus",
            "Dionysus",
            "ATM10-Agent",
        }:
            roots.append(child)
    for parent_name in ("connectors", "bundles"):
        parent = os_root / parent_name
        if parent.is_dir():
            roots.extend(child for child in parent.iterdir() if child.is_dir() and not child.name.startswith("."))
    return sorted({root.resolve() for root in roots}, key=lambda path: path.as_posix())


def source_counts(owner_root: Path) -> dict[str, int]:
    counts = {
        "documents": 0,
        "mechanics": 0,
        "commands": 0,
        "validators": 0,
        "tests": 0,
        "scripts": 0,
        "schemas": 0,
        "generated": 0,
    }
    for rel in git_file_paths(owner_root):
        if (EXCLUDED_PARTS | {".deps", "dist"}).intersection(rel.parts):
            continue
        if rel.suffix == ".md":
            counts["documents"] += 1
        if "mechanics" in rel.parts:
            counts["mechanics"] += 1
        if "scripts" in rel.parts and rel.suffix in {".py", ".sh"}:
            counts["scripts"] += 1
            counts["commands"] += 1
        if rel.name.startswith("validate_") or "validators" in rel.parts:
            counts["validators"] += 1
        if "tests" in rel.parts and rel.suffix == ".py":
            counts["tests"] += 1
            counts["commands"] += 1
        if "schemas" in rel.parts or rel.name.endswith(".schema.json"):
            counts["schemas"] += 1
        if "generated" in rel.parts:
            counts["generated"] += 1
    return counts


def canonical_owner_root(os_root: Path, repo: str) -> Path:
    if repo == "aoa-kag":
        return os_root / repo
    canonical_roots = provider_roots(os_root=os_root)
    if repo in canonical_roots:
        return canonical_roots[repo]
    if repo in CONNECTOR_REPOS:
        return os_root / "connectors" / repo
    if repo == "aoa-session-memory":
        return os_root / "bundles" / repo
    return os_root / repo


def configured_owner_roots() -> list[tuple[str, Path]]:
    return [(repo, KNOWN_REPO_ROOTS[repo].resolve()) for repo in PROVIDER_REPO_ORDER]


def source_index_matches_owner(owner_root: Path, payload: dict[str, Any]) -> bool:
    repo = repo_name(owner_root)
    repo_payload = payload.get("repo")
    if not isinstance(repo_payload, dict) or repo_payload.get("name") != repo:
        return False
    records = payload.get("records")
    summary = payload.get("coverage_summary")
    identity = payload.get("index_identity")
    if not isinstance(records, list) or not isinstance(summary, dict) or not isinstance(identity, dict):
        return False
    if identity.get("content_digest") != payload_digest(payload):
        return False
    if summary.get("record_count") != len(records):
        return False
    indexed_paths: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            return False
        identity = record.get("identity")
        if not isinstance(identity, dict):
            return False
        if identity.get("repo") != repo:
            return False
        rel_path = identity.get("path")
        if not isinstance(rel_path, str) or not rel_path:
            return False
        if rel_path in indexed_paths:
            return False
        indexed_paths.add(rel_path)
    try:
        if summary != coverage_summary(records):
            return False
    except (KeyError, TypeError):
        return False
    expected_paths = {
        rel.as_posix()
        for rel in git_file_paths(owner_root)
        if rel not in COMMON_GENERATED_INDEX_RELS
        and not is_portable_family_control_path(rel)
    }
    if indexed_paths != expected_paths:
        return False
    for record in records:
        identity = record["identity"]
        rel_path = identity["path"]
        if rel_path.startswith("generated/repo_local_kag_coverage"):
            continue
        rel = Path(rel_path)
        try:
            content = source_bytes(owner_root, rel, owner_root / rel)
        except (FileNotFoundError, IsADirectoryError, subprocess.CalledProcessError):
            return False
        digest = sha256_bytes(content)
        if identity.get("content_hash") != digest:
            return False
        signs = record.get("signs")
        if isinstance(signs, dict) and signs.get("digest") != digest:
            return False
    return True


def _count_map(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, count in value.items():
        if isinstance(key, str) and isinstance(count, int) and count >= 0:
            result[key] = count
    return dict(sorted(result.items()))


def _source_index_payload(owner_root: Path) -> dict[str, Any] | None:
    source_index = owner_root / SOURCE_SURFACE_INDEX_REL
    try:
        payload = json.loads(source_index.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError, IsADirectoryError):
        payload = None
    if isinstance(payload, dict) and payload.get("schema_version") == INDEX_SCHEMA_VERSION:
        return payload
    portable = _portable_bundle(owner_root)
    if portable is not None:
        return portable[0]
    return _externalized_hot_source(owner_root)


@lru_cache(maxsize=None)
def _externalized_hot_source(
    owner_root: Path,
) -> dict[str, Any] | None:
    manifest_path = owner_root / MANIFEST_RELATIVE_PATH
    try:
        raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        placement = raw_manifest.get("placement")
        if (
            raw_manifest.get("schema_version")
            != DISTRIBUTION_SCHEMA_VERSION
            or not isinstance(placement, dict)
            or placement.get("state") != "externalized"
        ):
            return None
        distribution, corpus, _, _, _ = load_tiered_manifests(owner_root)
        rows, delivery = load_tiered_rows(
            owner_root,
            artifact_root=None,
            allow_shadow_git=False,
            allow_hot_only=True,
        )
        cold_objects = distribution["summary"]["artifact_cold_objects"]
        expected_state = "hot_only" if cold_objects else "complete"
        if delivery.get("state") != expected_state:
            return None
        return reconstruct_source_index(corpus, rows)
    except (
        FileNotFoundError,
        IsADirectoryError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        return None


def portable_family_profile(
    owner_root: Path,
    *,
    owner_name: str,
    status: str,
) -> tuple[str, dict[str, Any]]:
    manifest_path = owner_root / MANIFEST_RELATIVE_PATH
    try:
        raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        raw_manifest = None
    if (
        isinstance(raw_manifest, dict)
        and raw_manifest.get("schema_version") == DISTRIBUTION_SCHEMA_VERSION
    ):
        artifact_root_value = os.environ.get("KAG_ARTIFACT_ROOT")
        artifact_root = (
            Path(artifact_root_value).expanduser().resolve()
            if artifact_root_value
            else None
        )
        distribution, corpus, _, _, _ = load_tiered_manifests(
            owner_root,
            artifact_root=artifact_root,
        )
        summary = distribution["summary"]
        budgets = distribution["budgets"]
        corpus_digest = corpus["corpus_identity"]["content_digest"]
        distribution_digest = distribution["distribution_identity"][
            "content_digest"
        ]
        git_hot_bytes = summary["git_hot_bytes"]
        tracked_bytes_max = budgets["owner_git_hot_bytes_max"]
        receipted = git_hot_bytes > tracked_bytes_max
        self_manifest = (
            owner_name == "aoa-kag"
            and owner_root.resolve() == REPO_ROOT.resolve()
        )
        public_identity = "" if self_manifest else corpus_digest.removeprefix("sha256:")
        measured_git_hot_bytes = 0 if self_manifest else git_hot_bytes
        measured_corpus_total_bytes = (
            0 if self_manifest else summary["corpus_total_bytes"]
        )
        measured_artifact_cold_bytes = (
            0 if self_manifest else summary["artifact_cold_bytes"]
        )
        measured_git_hot_objects = (
            0 if self_manifest else summary["git_hot_objects"]
        )
        measured_artifact_cold_objects = (
            0 if self_manifest else summary["artifact_cold_objects"]
        )
        measured_shards = 0 if self_manifest else corpus["summary"]["objects"]
        return (
            "v4-tiered-content-addressed",
            {
                "manifest_ref": MANIFEST_RELATIVE_PATH.as_posix(),
                "content_digest": public_identity,
                "digest_state": "self-manifest" if self_manifest else "published",
                "tracked_bytes": measured_git_hot_bytes,
                "tracked_bytes_max": tracked_bytes_max,
                "shards": measured_shards,
                "budget_state": (
                    "self-excluded"
                    if self_manifest
                    else ("receipted" if receipted else "passed")
                ),
                "receipt_ref": (
                    (
                        "kag/receipts/index_family_budget/"
                        f"{public_identity}.json"
                    )
                    if receipted and not self_manifest
                    else ""
                ),
                "corpus_digest": "" if self_manifest else corpus_digest,
                "distribution_digest": (
                    "" if self_manifest else distribution_digest
                ),
                "git_hot_bytes": measured_git_hot_bytes,
                "corpus_total_bytes": measured_corpus_total_bytes,
                "artifact_cold_bytes": measured_artifact_cold_bytes,
                "git_hot_objects": measured_git_hot_objects,
                "artifact_cold_objects": measured_artifact_cold_objects,
                "placement_state": distribution["placement"]["state"],
                "hot_profile_ref": "kag/indexes/hot_profile.json",
                "artifact_locator_ref": "kag/indexes/artifact_locators.json",
                "os_git_hot_target_bytes": budgets["os_git_hot_target_bytes"],
                "aggregate_ceiling_receiptable_by_owner": budgets[
                    "aggregate_ceiling_receiptable_by_owner"
                ],
                "measurement_state": (
                    "self-excluded" if self_manifest else "measured"
                ),
                "measurement_ref": (
                    "owner-family-release.json#/measurements"
                    if self_manifest
                    else ""
                ),
            },
        )
    portable = _portable_bundle(owner_root)
    if portable is not None:
        manifest = portable[2]
        tracked_bytes = manifest["summary"]["tracked_bytes"]
        tracked_bytes_max = manifest["budgets"]["tracked_bytes_max"]
        receipted = tracked_bytes > tracked_bytes_max
        self_manifest = (
            owner_name == "aoa-kag"
            and owner_root.resolve() == REPO_ROOT.resolve()
        )
        return (
            "v3-portable-shards",
            {
                "manifest_ref": MANIFEST_RELATIVE_PATH.as_posix(),
                "content_digest": (
                    ""
                    if self_manifest
                    else manifest["family_identity"]["content_digest"]
                ),
                "digest_state": (
                    "self-manifest"
                    if self_manifest
                    else "published"
                ),
                "tracked_bytes": 0 if self_manifest else tracked_bytes,
                "tracked_bytes_max": tracked_bytes_max,
                "shards": 0 if self_manifest else manifest["summary"]["shards"],
                "budget_state": (
                    "self-excluded"
                    if self_manifest
                    else ("receipted" if receipted else "passed")
                ),
                "receipt_ref": (
                    receipt_path_for(manifest).as_posix()
                    if receipted and not self_manifest
                    else ""
                ),
                "corpus_digest": "",
                "distribution_digest": "",
                "git_hot_bytes": 0 if self_manifest else tracked_bytes,
                "corpus_total_bytes": 0 if self_manifest else tracked_bytes,
                "artifact_cold_bytes": 0,
                "git_hot_objects": (
                    0 if self_manifest else manifest["summary"]["shards"]
                ),
                "artifact_cold_objects": 0,
                "placement_state": "git-full",
                "hot_profile_ref": "",
                "artifact_locator_ref": "",
                "os_git_hot_target_bytes": OS_GIT_HOT_TARGET_BYTES,
                "aggregate_ceiling_receiptable_by_owner": False,
                "measurement_state": (
                    "self-excluded" if self_manifest else "measured"
                ),
                "measurement_ref": (
                    "owner-family-release.json#/measurements"
                    if self_manifest
                    else ""
                ),
            },
        )
    if status == "passed":
        return (
            "v2-monoliths",
            {
                "manifest_ref": "",
                "content_digest": "",
                "digest_state": "not-applicable",
                "tracked_bytes": 0,
                "tracked_bytes_max": 0,
                "shards": 0,
                "budget_state": "not-applicable",
                "receipt_ref": "",
                "corpus_digest": "",
                "distribution_digest": "",
                "git_hot_bytes": 0,
                "corpus_total_bytes": 0,
                "artifact_cold_bytes": 0,
                "git_hot_objects": 0,
                "artifact_cold_objects": 0,
                "placement_state": "not-applicable",
                "hot_profile_ref": "",
                "artifact_locator_ref": "",
                "os_git_hot_target_bytes": OS_GIT_HOT_TARGET_BYTES,
                "aggregate_ceiling_receiptable_by_owner": False,
                "measurement_state": "not-applicable",
                "measurement_ref": "",
            },
        )
    return (
        "none",
        {
            "manifest_ref": "",
            "content_digest": "",
            "digest_state": "not-applicable",
            "tracked_bytes": 0,
            "tracked_bytes_max": 0,
            "shards": 0,
            "budget_state": "not-applicable",
            "receipt_ref": "",
            "corpus_digest": "",
            "distribution_digest": "",
            "git_hot_bytes": 0,
            "corpus_total_bytes": 0,
            "artifact_cold_bytes": 0,
            "git_hot_objects": 0,
            "artifact_cold_objects": 0,
            "placement_state": "not-applicable",
            "hot_profile_ref": "",
            "artifact_locator_ref": "",
            "os_git_hot_target_bytes": OS_GIT_HOT_TARGET_BYTES,
            "aggregate_ceiling_receiptable_by_owner": False,
            "measurement_state": "not-applicable",
            "measurement_ref": "",
        },
    )


def repository_index_family_refs(
    relative_files: Sequence[str],
    *,
    status: str,
    storage: str,
) -> dict[str, str]:
    present = set(relative_files)
    if status == "passed" and storage in {
        "v3-portable-shards",
        "v4-tiered-content-addressed",
    }:
        return dict(REPOSITORY_INDEX_FAMILY_REFS)
    return {
        index_kind: path
        for index_kind, path in REPOSITORY_INDEX_FAMILY_REFS.items()
        if path in present
    }


@lru_cache(maxsize=None)
def _portable_bundle(
    owner_root: Path,
) -> tuple[
    dict[str, Any],
    dict[str, dict[str, Any]],
    dict[str, Any],
] | None:
    manifest = owner_root / MANIFEST_RELATIVE_PATH
    if not manifest.is_file():
        return None
    try:
        artifact_root_value = os.environ.get("KAG_ARTIFACT_ROOT")
        return load_portable_family(
            owner_root,
            artifact_root=(
                Path(artifact_root_value).expanduser().resolve()
                if artifact_root_value
                else None
            ),
        )
    except (ValueError, FileNotFoundError, json.JSONDecodeError):
        return None


def repository_event_history_ref(owner_root: Path) -> str | None:
    portable = _portable_bundle(owner_root)
    if portable is not None:
        entries = portable[1]["event"].get("entries")
    else:
        event_index = (
            owner_root
            / "kag"
            / "indexes"
            / REPOSITORY_INDEX_FILENAMES["event"]
        )
        try:
            payload = json.loads(event_index.read_text(encoding="utf-8"))
            entries = payload.get("entries")
        except (
            FileNotFoundError,
            json.JSONDecodeError,
            UnicodeDecodeError,
            IsADirectoryError,
        ):
            return None
    if not isinstance(entries, list):
        return None
    published_refs = {
        str(evidence["ref"])
        for entry in entries
        if isinstance(entry, dict) and entry.get("event_kind") == "git_commit"
        for evidence in entry.get("evidence_refs", [])
        if isinstance(evidence, dict)
        and evidence.get("kind") == "git_commit"
        and isinstance(evidence.get("ref"), str)
    }
    if not published_refs:
        return None
    try:
        ancestry = subprocess.run(
            ("git", "rev-list", "--topo-order", "HEAD"),
            cwd=owner_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return next((ref for ref in ancestry if ref in published_refs), None)


def repository_index_family_matches_owner(
    owner_root: Path,
    source_index: dict[str, Any],
) -> bool:
    history_ref = repository_event_history_ref(owner_root)
    expected = build_repository_indexes(
        source_index,
        source_index_path=SOURCE_SURFACE_INDEX_REL,
        repo_root=owner_root,
        history_ref=history_ref,
        event_history_ref=history_ref,
    )
    portable = _portable_bundle(owner_root)
    if portable is not None:
        actual = portable[1]
    else:
        actual = {}
        for index_kind, filename in REPOSITORY_INDEX_FILENAMES.items():
            path = owner_root / "kag" / "indexes" / filename
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (
                FileNotFoundError,
                json.JSONDecodeError,
                UnicodeDecodeError,
                IsADirectoryError,
            ):
                return False
            actual[index_kind] = payload
    for index_kind in REPOSITORY_INDEX_FILENAMES:
        if actual[index_kind] != expected[index_kind]:
            return False
    try:
        try:
            from scripts.validators.common import ValidationError
            from scripts.validators.repo_local_kag_index import (
                validate_repo_local_kag_repository_index_family,
            )
        except ImportError:  # pragma: no cover - direct script execution
            from validators.common import ValidationError  # type: ignore
            from validators.repo_local_kag_index import (  # type: ignore
                validate_repo_local_kag_repository_index_family,
            )

        validate_repo_local_kag_repository_index_family(
            actual,
            source_payload=source_index,
            label=f"{owner_root.name} coverage family",
        )
    except ValidationError:
        return False
    return True


def _profile_payload(owner_root: Path, *, index_status: str) -> tuple[str, dict[str, Any]]:
    payload = _source_index_payload(owner_root)
    if payload is not None and (index_status == "passed" or source_index_matches_owner(owner_root, payload)):
        return "source_surface_index", payload
    return "source_tree_scan", build_index(owner_root, output=SOURCE_SURFACE_INDEX_REL)


def _records_have_owner_commands(records: object) -> bool:
    if not isinstance(records, list):
        return False
    for record in records:
        if not isinstance(record, dict):
            continue
        toolchain = record.get("toolchain")
        if not isinstance(toolchain, dict):
            continue
        owner_commands = toolchain.get("owner_commands")
        if isinstance(owner_commands, list) and owner_commands:
            return True
    return False


def _record_classes_present(owner_root: Path) -> bool:
    kag_root = owner_root / "kag"
    return all((kag_root / directory).is_dir() for directory in PROVIDER_RECORD_DIRS)


def common_surface_profile(
    owner_root: Path,
    *,
    index_status: str,
) -> dict[str, Any]:
    source, payload = _profile_payload(owner_root, index_status=index_status)
    records = payload.get("records")
    if not isinstance(records, list):
        records = []
    summary = coverage_summary(records)
    classification = classification_summary(records)
    counts = {
        key: _count_map(classification.get(key))
        for key in COMMON_PROFILE_COUNT_KEYS
    }
    return {
        "source": source,
        "counts": counts,
        "quality": {
            "unknown_count": int(summary.get("unknown_count", 0)),
            "has_kag_home": (owner_root / "kag").is_dir(),
            "has_record_classes": _record_classes_present(owner_root),
            "has_source_index": source == "source_surface_index",
            "has_owner_commands": _records_have_owner_commands(records),
            "has_generated_readmodels": int(summary.get("generated_count", 0)) > 0,
            "has_validation_route": (
                int(summary.get("validator_count", 0)) > 0
                or bool(manifest_validation_route(owner_root, "local-kag"))
            ),
        },
    }


def has_owner_specific_index(owner_name: str, owner_root: Path, relative_files: list[str]) -> bool:
    owner_type = owner_type_for(owner_name, owner_root)
    if owner_type not in OWNER_SPECIFIC_OWNER_TYPES:
        return False
    schema = local_kag_index_record_schema()
    for relative_file in relative_files:
        rel = Path(relative_file)
        if rel.name not in OWNER_SPECIFIC_INDEX_NAMES:
            continue
        try:
            payload = json.loads((owner_root / rel).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError, IsADirectoryError):
            continue
        if owner_specific_index_is_usable(owner_name, owner_root, payload, schema=schema):
            return True
    return False


def owner_specific_index_is_usable(
    owner_name: str,
    owner_root: Path,
    payload: object,
    *,
    schema: dict[str, Any],
) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get("schema_version") != LOCAL_KAG_RECORD_SCHEMA_VERSION:
        return False
    errors = list(Draft202012Validator(schema).iter_errors(payload))
    if errors:
        return False
    if payload.get("repo") != owner_name or payload.get("source_owner") != owner_name:
        return False
    if not owner_specific_checked_ref_is_source_linked(
        payload,
        label=f"{owner_name} owner-specific local KAG index",
    ):
        return False
    owner_return_route = payload.get("owner_return_route")
    if not isinstance(owner_return_route, dict) or owner_return_route.get("repo") != owner_name:
        return False
    source_refs = payload.get("source_refs")
    if not isinstance(source_refs, list):
        return False
    for source_ref in source_refs:
        if not isinstance(source_ref, dict) or source_ref.get("repo") != owner_name:
            return False
        source_path = source_ref.get("path")
        if not isinstance(source_path, str) or not (owner_root / source_path).is_file():
            return False
    if not owner_specific_provider_records_are_usable(owner_name, owner_root):
        return False
    return True


def owner_specific_checked_ref_is_source_linked(payload: object, *, label: str) -> bool:
    try:
        try:
            from scripts.validators.common import ValidationError
            from scripts.validators.local_kag_subtree import _validate_checked_ref_is_source_linked
        except ImportError:  # pragma: no cover - direct script execution
            from validators.common import ValidationError  # type: ignore
            from validators.local_kag_subtree import _validate_checked_ref_is_source_linked  # type: ignore

        _validate_checked_ref_is_source_linked(payload, label=label)
    except ValidationError:
        return False
    return True


def owner_specific_provider_records_are_usable(owner_name: str, owner_root: Path) -> bool:
    try:
        try:
            from scripts.validators.common import ValidationError
            from scripts.validators.local_kag_subtree import (
                _validate_checked_ref_is_source_linked,
                _validate_record_links,
                _validate_source_refs_exist,
            )
        except ImportError:  # pragma: no cover - direct script execution
            from validators.common import ValidationError  # type: ignore
            from validators.local_kag_subtree import (  # type: ignore
                _validate_checked_ref_is_source_linked,
                _validate_record_links,
                _validate_source_refs_exist,
            )

        groups: dict[str, list[dict[str, object]]] = {}
        schemas = local_kag_provider_record_schemas()
        kag_root = owner_root / "kag"
        for group_name in PROVIDER_RECORD_SCHEMA_DEFS:
            directory = kag_root / group_name
            if not directory.is_dir():
                return False
            records: list[dict[str, object]] = []
            for path in sorted(directory.glob("*.json")):
                if group_name == "indexes" and path.name in META_INDEX_NAMES:
                    continue
                payload = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(payload, dict):
                    return False
                if list(Draft202012Validator(schemas[group_name]).iter_errors(payload)):
                    return False
                if payload.get("repo") != owner_name or payload.get("source_owner") != owner_name:
                    return False
                label = f"{owner_name} owner-specific {path.relative_to(owner_root).as_posix()}"
                _validate_source_refs_exist(owner_name, owner_root, payload, label=label)
                _validate_checked_ref_is_source_linked(payload, label=label)
                records.append(payload)
            groups[group_name] = records
        _validate_record_links({"records": groups})
    except (
        FileNotFoundError,
        IsADirectoryError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
        UnicodeDecodeError,
        ValidationError,
    ):
        return False
    return True


def index_status(owner_root: Path, *, owner_name: str | None = None) -> tuple[str, list[str]]:
    owner_name = owner_name or owner_root.name
    indexes = owner_root / "kag" / "indexes"
    if not indexes.is_dir():
        return "missing", []
    files = sorted(path for path in indexes.glob("*.json") if path.is_file())
    if not files:
        return "missing", []
    relative_files = [path.relative_to(owner_root).as_posix() for path in files]
    portable = _portable_bundle(owner_root)
    if portable is not None:
        payload = portable[0]
        schema = json.loads(INDEX_SCHEMA_PATH.read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema).iter_errors(payload))
        if (
            payload.get("schema_version") == INDEX_SCHEMA_VERSION
            and not errors
            and source_index_matches_owner(owner_root, payload)
        ):
            return (
                "passed"
                if repository_index_family_matches_owner(owner_root, payload)
                else "migration-needed",
                relative_files,
            )
        return "migration-needed", relative_files
    externalized_source = _externalized_hot_source(owner_root)
    if externalized_source is not None:
        schema = json.loads(INDEX_SCHEMA_PATH.read_text(encoding="utf-8"))
        errors = list(
            Draft202012Validator(schema).iter_errors(externalized_source)
        )
        if (
            externalized_source.get("schema_version")
            == INDEX_SCHEMA_VERSION
            and not errors
            and source_index_matches_owner(
                owner_root,
                externalized_source,
            )
        ):
            return "passed", relative_files
        return "migration-needed", relative_files
    source_index = indexes / "source_surface_index.json"
    if source_index.is_file():
        try:
            payload = json.loads(source_index.read_text(encoding="utf-8"))
            schema = json.loads(INDEX_SCHEMA_PATH.read_text(encoding="utf-8"))
            errors = list(Draft202012Validator(schema).iter_errors(payload))
            if (
                isinstance(payload, dict)
                and payload.get("schema_version") == INDEX_SCHEMA_VERSION
                and not errors
                and source_index_matches_owner(owner_root, payload)
            ):
                return (
                    "passed"
                    if repository_index_family_matches_owner(owner_root, payload)
                    else "migration-needed",
                    relative_files,
                )
        except (json.JSONDecodeError, UnicodeDecodeError):
            return "migration-needed", relative_files
        return "migration-needed", relative_files
    if has_owner_specific_index(owner_name, owner_root, relative_files):
        return "owner-specific", relative_files
    return "migration-needed", relative_files


def build_coverage(
    os_root: Path,
    owner_roots: Sequence[tuple[str, Path]] | None = None,
    *,
    progress: bool = False,
) -> dict[str, Any]:
    owners: list[dict[str, Any]] = []
    roots = list(owner_roots) if owner_roots is not None else [
        (owner_root.name, owner_root) for owner_root in direct_owner_roots(os_root)
    ]
    if progress:
        coverage_progress(f"owners {len(roots)}")
    for index, (name, owner_root) in enumerate(roots, start=1):
        if progress:
            coverage_progress(f"owner {index}/{len(roots)} {name}")
        status, files = index_status(owner_root, owner_name=name)
        family_storage, portable_family = portable_family_profile(
            owner_root,
            owner_name=name,
            status=status,
        )
        display_root = f"aoa-owner:{name}"
        display_kag_home = (
            f"{display_root}:kag"
            if (owner_root / "kag").is_dir()
            else ""
        )
        owners.append(
            {
                "repo": name,
                "owner_type": owner_type_for(name, owner_root),
                "root": display_root,
                "kag_home": display_kag_home,
                "index_status": status,
                "index_files": files,
                "family_storage": family_storage,
                "portable_family": portable_family,
                "repository_index_family": repository_index_family_refs(
                    files,
                    status=status,
                    storage=family_storage,
                ),
                "domain_index_catalog_ref": (
                    DOMAIN_INDEX_CATALOG_REF if DOMAIN_INDEX_CATALOG_REF in files else ""
                ),
                "coverage": source_counts(owner_root),
                "common_surface_profile": common_surface_profile(
                    owner_root,
                    index_status=status,
                ),
            }
        )
    summary = {status: sum(1 for owner in owners if owner["index_status"] == status) for status in OWNER_STATUS}
    portable_owners = [
        owner
        for owner in owners
        if owner["family_storage"] == "v3-portable-shards"
    ]
    portable_tracked_bytes = sum(
        owner["portable_family"]["tracked_bytes"]
        for owner in portable_owners
        if owner["portable_family"]["measurement_state"] == "measured"
    )
    tiered_owners = [
        owner
        for owner in owners
        if owner["family_storage"] == "v4-tiered-content-addressed"
    ]
    family_owners = [*portable_owners, *tiered_owners]
    measured_family_owners = [
        owner
        for owner in family_owners
        if owner["portable_family"]["measurement_state"] == "measured"
    ]
    self_excluded_owners = [
        owner
        for owner in family_owners
        if owner["portable_family"]["measurement_state"] == "self-excluded"
    ]
    git_hot_bytes = sum(
        owner["portable_family"]["git_hot_bytes"]
        for owner in measured_family_owners
    )
    corpus_total_bytes = sum(
        owner["portable_family"]["corpus_total_bytes"]
        for owner in measured_family_owners
    )
    artifact_cold_bytes = sum(
        owner["portable_family"]["artifact_cold_bytes"]
        for owner in measured_family_owners
        if owner["family_storage"] == "v4-tiered-content-addressed"
    )
    aggregate_budget_state = (
        "exceeded"
        if git_hot_bytes > OS_AGGREGATE_TRACKED_BYTES_MAX
        else (
            "passed"
            if len(measured_family_owners) == len(owners)
            else "partial"
        )
    )
    target_budget_state = (
        "exceeded"
        if git_hot_bytes > OS_GIT_HOT_TARGET_BYTES
        else (
            "passed"
            if (
                len(tiered_owners) == len(owners)
                and len(measured_family_owners) == len(owners)
            )
            else "partial"
        )
    )
    return {
        "schema_version": "aoa-repo-local-kag-coverage-v1",
        "source_contract": "schemas/repo-local-kag-index.schema.json",
        "root": PUBLIC_OS_ROOT,
        "coverage_summary": {
            "owner_count": len(owners),
            "passed": summary["passed"],
            "migration_needed": summary["migration-needed"],
            "missing": summary["missing"],
            "owner_specific": summary["owner-specific"],
            "measured_owner_count": len(measured_family_owners),
            "self_excluded_owner_count": len(self_excluded_owners),
            "portable_v3": len(portable_owners),
            "tiered_v4": len(tiered_owners),
            "portable_tracked_bytes": portable_tracked_bytes,
            "git_hot_bytes": git_hot_bytes,
            "corpus_total_bytes": corpus_total_bytes,
            "artifact_cold_bytes": artifact_cold_bytes,
            "os_aggregate_tracked_bytes_max": OS_AGGREGATE_TRACKED_BYTES_MAX,
            "os_git_hot_target_bytes": OS_GIT_HOT_TARGET_BYTES,
            "aggregate_budget_state": aggregate_budget_state,
            "target_budget_state": target_budget_state,
        },
        "owners": owners,
    }


def build_provider_coverage(
    os_root: Path = DEFAULT_OS_ROOT,
    *,
    progress: bool = False,
) -> dict[str, Any]:
    packet_value = os.environ.get(COVERAGE_PACKET_ENV, "").strip()
    if not packet_value:
        return build_coverage(
            os_root,
            owner_roots=configured_owner_roots(),
            progress=progress,
        )

    packet_path = Path(packet_value).expanduser().resolve()
    packet_key = coverage_packet_key()
    if packet_path.exists():
        payload = load_coverage_packet(packet_path, expected_key=packet_key)
        if progress:
            coverage_progress(f"reused verified packet {packet_path}")
        return payload

    payload = build_coverage(
        os_root,
        owner_roots=configured_owner_roots(),
        progress=progress,
    )
    write_coverage_packet(packet_path, key=packet_key, payload=payload)
    if progress:
        coverage_progress(f"wrote verified packet {packet_path}")
    return payload


def _git_index_tree(owner: str, owner_root: Path) -> str:
    try:
        tree = subprocess.run(
            ("git", "write-tree"),
            cwd=owner_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise RuntimeError(
            f"coverage packet requires a Git-index snapshot for {owner}: {owner_root}"
        ) from exc
    if not tree:
        raise RuntimeError(f"coverage packet received an empty Git tree for {owner}")
    return f"git-tree:{tree}"


def _coverage_builder_digest() -> str:
    digest = hashlib.sha256()
    for rel in COVERAGE_PACKET_BUILDER_PATHS:
        path = REPO_ROOT / rel
        try:
            content = source_bytes(REPO_ROOT, rel, path)
        except (FileNotFoundError, IsADirectoryError, subprocess.CalledProcessError) as exc:
            raise RuntimeError(f"coverage packet builder input is unavailable: {rel}") from exc
        digest.update(rel.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def coverage_packet_key() -> dict[str, Any]:
    return {
        "builder_digest": _coverage_builder_digest(),
        "canonicalization_epoch": COVERAGE_CANONICALIZATION_EPOCH,
        "schema_epoch": INDEX_SCHEMA_VERSION,
        "distribution_epoch": DISTRIBUTION_SCHEMA_VERSION,
        "owner_snapshots": [
            {
                "owner": owner,
                "source_snapshot": _git_index_tree(owner, owner_root),
            }
            for owner, owner_root in configured_owner_roots()
        ],
    }


def _coverage_payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def write_coverage_packet(
    path: Path,
    *,
    key: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    if path.is_symlink():
        raise RuntimeError(f"coverage packet path must not be a symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    packet = {
        "schema_version": COVERAGE_PACKET_SCHEMA_VERSION,
        "cache_key": key,
        "payload_digest": _coverage_payload_digest(payload),
        "coverage": payload,
    }
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(normalized_json(packet), encoding="utf-8")
    temporary.replace(path)


def load_coverage_packet(
    path: Path,
    *,
    expected_key: dict[str, Any],
) -> dict[str, Any]:
    try:
        packet = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, IsADirectoryError) as exc:
        raise RuntimeError(f"coverage packet is unreadable: {path}") from exc
    if not isinstance(packet, dict):
        raise RuntimeError(f"coverage packet must be an object: {path}")
    if packet.get("schema_version") != COVERAGE_PACKET_SCHEMA_VERSION:
        raise RuntimeError(f"coverage packet schema is incompatible: {path}")
    if packet.get("cache_key") != expected_key:
        raise RuntimeError(
            "coverage packet snapshot changed during the build phase; "
            f"discard the run-scoped packet and restart the audit: {path}"
        )
    payload = packet.get("coverage")
    if not isinstance(payload, dict):
        raise RuntimeError(f"coverage packet payload must be an object: {path}")
    expected_digest = _coverage_payload_digest(payload)
    if packet.get("payload_digest") != expected_digest:
        raise RuntimeError(f"coverage packet payload digest mismatch: {path}")
    return copy.deepcopy(payload)


def write_outputs(output: Path, min_output: Path, payload: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(normalized_json(payload), encoding="utf-8")
    min_output.parent.mkdir(parents=True, exist_ok=True)
    min_output.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def check_outputs(output: Path, min_output: Path, payload: dict[str, Any]) -> bool:
    expected = normalized_json(payload)
    expected_min = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ok = True
    if not output.exists() or output.read_text(encoding="utf-8") != expected:
        print(f"[repo-local-kag-coverage] drift in {output}", file=sys.stderr)
        ok = False
    if not min_output.exists() or min_output.read_text(encoding="utf-8") != expected_min:
        print(f"[repo-local-kag-coverage] drift in {min_output}", file=sys.stderr)
        ok = False
    return ok


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate repo-local KAG coverage for OS Abyss.")
    parser.add_argument("--os-root")
    parser.add_argument("--output", default=DEFAULT_OUTPUT.as_posix())
    parser.add_argument("--min-output", default=DEFAULT_MIN_OUTPUT.as_posix())
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    payload = (
        build_coverage(Path(args.os_root).resolve(), progress=True)
        if args.os_root
        else build_provider_coverage(progress=True)
    )
    output = Path(args.output)
    min_output = Path(args.min_output)
    if args.check:
        return 0 if check_outputs(output, min_output, payload) else 1
    write_outputs(output, min_output, payload)
    print(f"[repo-local-kag-coverage] wrote {output} and {min_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
