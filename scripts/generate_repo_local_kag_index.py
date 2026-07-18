#!/usr/bin/env python3
"""Generate a repo-local KAG source surface index."""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence

try:
    from scripts.repo_local.identity import (
        artifact_identity,
        git_lineage_paths,
        qualified_id,
        repository_namespace,
    )
    from scripts.repo_local.history import git_commit_events
    from scripts.repo_local.indexes import (
        anchor_entries as project_anchor_entries,
        artifact_entries as project_artifact_entries,
        assertion_entries as project_assertion_entries,
        entity_entries as project_entity_entries,
        relation_entries as project_relation_entries,
    )
    from scripts.repo_local.structure import extract_structure, markdown_headings
except ImportError:  # pragma: no cover - direct script execution
    from repo_local.identity import (  # type: ignore
        artifact_identity,
        git_lineage_paths,
        qualified_id,
        repository_namespace,
    )
    from repo_local.history import git_commit_events  # type: ignore
    from repo_local.indexes import (  # type: ignore
        anchor_entries as project_anchor_entries,
        artifact_entries as project_artifact_entries,
        assertion_entries as project_assertion_entries,
        entity_entries as project_entity_entries,
        relation_entries as project_relation_entries,
    )
    from repo_local.structure import extract_structure, markdown_headings  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("kag/indexes/source_surface_index.json")
CANONICAL_SELF_INDEX = DEFAULT_OUTPUT
PORTABLE_FAMILY_MANIFEST = Path("kag/indexes/index_family.manifest.json")
PORTABLE_FAMILY_SHARD_ROOT = Path("kag/indexes/shards")
PORTABLE_FAMILY_BUDGET_RECEIPT_ROOT = Path(
    "kag/receipts/index_family_budget"
)
REPOSITORY_INDEX_FILENAMES = {
    "entity": "repo_entity_index.json",
    "artifact": "repo_artifact_index.json",
    "anchor": "repo_anchor_index.json",
    "event": "repo_event_index.json",
    "assertion": "repo_assertion_index.json",
    "relation": "repo_relation_index.json",
}
CANONICAL_REPOSITORY_INDEX_PATHS = {
    DEFAULT_OUTPUT.parent / filename for filename in REPOSITORY_INDEX_FILENAMES.values()
}
INDEX_SCHEMA_REF = "aoa-kag:schemas/repo-local-kag-index.schema.json"
INDEX_SCHEMA_VERSION = "aoa-repo-local-kag-index-v2"
REPOSITORY_INDEX_SCHEMA_REF = (
    "aoa-kag:schemas/repo-local-kag-repository-index.schema.json"
)
REPOSITORY_INDEX_SCHEMA_VERSION = "aoa-repo-local-kag-repository-index-v2"
GIT_INDEX_SOURCE_REF = "git-index-source-tree"
FILESYSTEM_SOURCE_REF = "filesystem-source-tree"
HISTORY_REPO_ENV = "AOA_REPO_LOCAL_KAG_HISTORY_REPO"
HISTORY_REF_ENV = "AOA_REPO_LOCAL_KAG_HISTORY_REF"
EVENT_HISTORY_REF_ENV = "AOA_REPO_LOCAL_KAG_EVENT_HISTORY_REF"
LOCAL_INDEX_GENERATOR_ROUTE = "scripts/generate_repo_local_kag_index.py"
REPO_LOCAL_GENERATOR_HELPER_PATHS = {
    Path("scripts/repo_local/history.py"),
    Path("scripts/repo_local/identity.py"),
    Path("scripts/repo_local/indexes.py"),
    Path("scripts/repo_local/structure.py"),
}
PORTABLE_MIME_BY_SUFFIX = {
    ".7z": "application/x-7z-compressed",
    ".alloy": "text/plain",
    ".c": "text/x-c",
    ".cc": "text/x-c++",
    ".cfg": "text/plain",
    ".conf": "text/plain",
    ".cpp": "text/x-c++",
    ".css": "text/css",
    ".csv": "text/csv",
    ".env": "text/plain",
    ".example": "text/plain",
    ".gif": "image/gif",
    ".go": "text/x-go",
    ".gz": "application/gzip",
    ".htm": "text/html",
    ".html": "text/html",
    ".h": "text/x-c",
    ".hpp": "text/x-c++",
    ".ico": "image/vnd.microsoft.icon",
    ".ini": "text/plain",
    ".js": "text/javascript",
    ".jsx": "text/jsx",
    ".java": "text/x-java-source",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".json": "application/json",
    ".jsonl": "application/x-ndjson",
    ".kt": "text/x-kotlin",
    ".md": "text/markdown",
    ".ndjson": "application/x-ndjson",
    ".ods": "application/vnd.oasis.opendocument.spreadsheet",
    ".path": "text/plain",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".ps1": "text/plain",
    ".properties": "text/plain",
    ".php": "application/x-httpd-php",
    ".py": "text/x-python",
    ".rb": "text/x-ruby",
    ".rs": "text/x-rust",
    ".scala": "text/x-scala",
    ".service": "text/plain",
    ".sh": "application/x-sh",
    ".snapshot": "text/plain",
    ".socket": "text/plain",
    ".svg": "image/svg+xml",
    ".svelte": "text/x-svelte",
    ".swift": "text/x-swift",
    ".tar": "application/x-tar",
    ".tgz": "application/x-tar",
    ".timer": "text/plain",
    ".toml": "application/toml",
    ".ts": "application/typescript",
    ".tsx": "text/tsx",
    ".tsv": "text/tab-separated-values",
    ".txt": "text/plain",
    ".webp": "image/webp",
    ".vue": "text/x-vue",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xml": "application/xml",
    ".xz": "application/x-xz",
    ".yaml": "application/yaml",
    ".yml": "application/yaml",
    ".zip": "application/zip",
}
PORTABLE_MIME_BY_SUFFIX_CHAIN = {
    (".tar", ".gz"): "application/x-tar",
    (".tar", ".xz"): "application/x-tar",
}
EXTERNAL_INDEX_GENERATOR_ROUTE = f"aoa-kag:{LOCAL_INDEX_GENERATOR_ROUTE}"
LOCAL_KAG_VALIDATOR_ROUTE = "scripts/validate_kag.py"
EXTERNAL_KAG_VALIDATOR_ROUTE = f"aoa-kag:{LOCAL_KAG_VALIDATOR_ROUTE}"
ZERO_DIGEST = "0" * 64
HOME_SKILL_PORT_MANIFEST = Path("skills/port.manifest.json")
HOME_SKILL_PORT_SCHEMA_VERSION_V1 = "aoa_skill_home_port_v1"
HOME_SKILL_PORT_SCHEMA_VERSION_V2 = "aoa_skill_home_port_v2"
HOME_SKILL_PROJECTION_BUILDER_ROUTE = (
    "aoa-skills:scripts/build_home_skill_projection.py"
)
HOME_SKILL_PROJECTION_VALIDATOR_ROUTE = (
    "aoa-skills:scripts/validate_home_skill_port.py"
)

BASELINE_TOOLS = (
    "git",
    "rg",
    "fd",
    "jq",
    "python",
    "sqlite3",
    "sha256sum",
    "file",
    "stat",
)

CAPABILITY_LANES = (
    {
        "lane": "code-structure",
        "status": "planned",
        "tools": ["ctags", "tree-sitter", "SCIP"],
    },
    {
        "lane": "material-inventory",
        "status": "planned",
        "tools": ["Syft", "SPDX", "CycloneDX"],
    },
    {
        "lane": "signing-attestation",
        "status": "planned",
        "tools": ["SLSA", "in-toto", "Cosign", "GitHub artifact attestations"],
    },
    {
        "lane": "static-findings",
        "status": "planned",
        "tools": ["Semgrep", "SARIF"],
    },
    {
        "lane": "document-conversion",
        "status": "planned",
        "tools": ["Docling", "MarkItDown", "Unstructured"],
    },
)

EXCLUDED_PARTS = {
    ".deps",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "htmlcov",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
OUTPUT_REFERENCE_LITERAL = re.compile(
    rb"\b(?:emit|emitted|export|exported|publish|published|render|rendered|"
    rb"save|saved|write|writes|writing|wrote)\b",
    re.IGNORECASE,
)
SECRET_HINTS = ("secret", "token", "credential", "private-key", "password")
LANE_ENTRYPOINTS = {"ci_gate.py", "release_check.py", "run_tests.py"}
COMMAND_SUFFIXES = {".py", ".sh", ".ps1"}
SOURCE_CODE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".htm",
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".php",
    ".ps1",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".sh",
    ".svelte",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
}
COMMAND_PREFIXES = ("build_", "generate_", "run_", "start_", "sync_", "validate_")
BUILDER_PREFIXES = ("build_", "generate_")
DECISION_INDEX_BUILDER_NAMES = {
    "build_decision_indexes.py",
    "generate_decision_indexes.py",
}
ASSET_SUFFIXES = {".gif", ".ico", ".jpg", ".jpeg", ".png", ".svg", ".webp"}
ARCHIVE_SUFFIXES = {".7z", ".gz", ".tar", ".tgz", ".xz", ".zip"}
SPREADSHEET_SUFFIXES = {".ods", ".xls", ".xlsx"}
DATA_TABLE_SUFFIXES = {".csv", ".tsv"}
RECORD_LOG_SUFFIXES = {".jsonl", ".ndjson"}
TEXT_ARTIFACT_SUFFIXES = {".txt"}
TEXT_WRAPPER_SUFFIXES = {".example", ".snapshot"}
HTML_SUFFIXES = {".htm", ".html"}
SERVICE_UNIT_SUFFIXES = {".path", ".service", ".socket", ".timer"}
OWNER_METADATA_NAMES = {".gitattributes", ".gitignore", "CODEOWNERS", "AOA_WORKSPACE_ROOT"}
DIRECTORY_MARKER_NAMES = {".gitkeep", ".keep"}
ENV_CONFIG_NAMES = {".env", ".env.example", ".env.sample", ".env.template"}
BUILD_CONFIG_NAMES = {"Dockerfile", "Justfile", "Makefile", "Procfile"}
CONFIG_SUFFIXES = {".alloy", ".cfg", ".conf", ".env", ".ini", ".properties"}
PORTABLE_TEXT_BASENAMES = (
    OWNER_METADATA_NAMES
    | DIRECTORY_MARKER_NAMES
    | ENV_CONFIG_NAMES
    | BUILD_CONFIG_NAMES
    | {"LICENSE"}
)


def run_text(command: Sequence[str], cwd: Path) -> str:
    result = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def git_ref(repo_root: Path) -> str:
    try:
        return run_text(("git", "rev-parse", "HEAD"), repo_root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "nogit"


def source_snapshot_ref(repo_root: Path) -> str:
    try:
        run_text(("git", "rev-parse", "--show-toplevel"), repo_root)
        return GIT_INDEX_SOURCE_REF
    except (subprocess.CalledProcessError, FileNotFoundError):
        return FILESYSTEM_SOURCE_REF


def git_file_paths(repo_root: Path) -> list[Path]:
    return sorted(git_file_modes(repo_root))


def manifest_repo_name(repo_root: Path) -> str:
    manifest_path = repo_root / "kag" / "manifest.json"
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return ""
    if not isinstance(payload, dict):
        return ""
    repo = payload.get("repo")
    if isinstance(repo, str) and repo.strip():
        return repo.strip()
    return ""


def repo_name(repo_root: Path) -> str:
    manifest_name = manifest_repo_name(repo_root)
    if manifest_name:
        return manifest_name
    try:
        top = Path(run_text(("git", "rev-parse", "--show-toplevel"), repo_root))
        return top.name
    except (subprocess.CalledProcessError, FileNotFoundError):
        return repo_root.name


def effective_history_ref(repo_root: Path, history_ref: str | None = None) -> str | None:
    if history_ref:
        return history_ref
    env_ref = os.environ.get(HISTORY_REF_ENV, "").strip()
    env_repo = os.environ.get(HISTORY_REPO_ENV, "").strip()
    if env_ref and env_repo == repo_name(repo_root):
        return env_ref
    return local_default_history_ref(repo_root)


def effective_event_history_ref(
    repo_root: Path,
    event_history_ref: str | None = None,
    *,
    fallback: str | None = None,
) -> str | None:
    if event_history_ref:
        return event_history_ref
    env_ref = os.environ.get(EVENT_HISTORY_REF_ENV, "").strip()
    env_repo = os.environ.get(HISTORY_REPO_ENV, "").strip()
    if env_ref and env_repo == repo_name(repo_root):
        return env_ref
    return fallback


def local_default_history_ref(repo_root: Path) -> str | None:
    try:
        default_ref = run_text(
            ("git", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"),
            repo_root,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        default_ref = "refs/remotes/origin/main"
    try:
        return run_text(("git", "merge-base", "HEAD", default_ref), repo_root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def owner_type_for(name: str, repo_root: Path) -> str:
    parts = set(repo_root.parts)
    if name == "Agents-of-Abyss":
        return "center"
    if "connectors" in parts or name.endswith("-connector"):
        return "connector"
    if "bundles" in parts or name == "aoa-session-memory":
        return "bundle_provider"
    if name in {"abyss-machine", "abyss-stack"}:
        return "runtime_source"
    if name in {"8Dionysus", "Dionysus", "ATM10-Agent"}:
        return "workspace"
    if name.startswith("aoa-") or name == "Tree-of-Sophia":
        return "organ"
    return "unknown"


def is_source_path(path: Path) -> bool:
    if EXCLUDED_PARTS.intersection(path.parts):
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    if path.name.endswith("~"):
        return False
    return True


def is_portable_family_control_path(path: Path) -> bool:
    return (
        path == PORTABLE_FAMILY_MANIFEST
        or PORTABLE_FAMILY_SHARD_ROOT in (path, *path.parents)
        or PORTABLE_FAMILY_BUDGET_RECEIPT_ROOT in (path, *path.parents)
    )


def git_file_entries(repo_root: Path) -> dict[Path, dict[str, str]]:
    try:
        raw = subprocess.run(
            ("git", "ls-files", "-s", "-z", "--cached"),
            cwd=repo_root,
            check=True,
            capture_output=True,
        ).stdout
        entries: dict[Path, dict[str, str]] = {}
        for item in raw.split(b"\0"):
            if not item:
                continue
            metadata, separator, path_bytes = item.partition(b"\t")
            if not separator:
                continue
            metadata_fields = metadata.split(b" ")
            if len(metadata_fields) < 2:
                continue
            mode = metadata_fields[0].decode()
            blob_id = metadata_fields[1].decode()
            path = Path(path_bytes.decode())
            if is_source_path(path):
                entries[path] = {"mode": mode, "blob_id": blob_id}
        return dict(sorted(entries.items()))
    except (subprocess.CalledProcessError, FileNotFoundError):
        entries: dict[Path, dict[str, str]] = {}
        for path in repo_root.rglob("*"):
            if not path.is_file() and not path.is_symlink():
                continue
            relative = path.relative_to(repo_root)
            if is_source_path(relative):
                content = (
                    path.readlink().as_posix().encode("utf-8")
                    if path.is_symlink()
                    else path.read_bytes()
                )
                entries[relative] = {
                    "mode": "120000" if path.is_symlink() else "100644",
                    "blob_id": sha256_bytes(content),
                }
        return dict(sorted(entries.items()))


def git_file_modes(repo_root: Path) -> dict[Path, str]:
    return {path: entry["mode"] for path, entry in git_file_entries(repo_root).items()}


def source_bytes(repo_root: Path, rel: Path, path: Path) -> bytes:
    try:
        return subprocess.run(
            ("git", "show", f":{rel.as_posix()}"),
            cwd=repo_root,
            check=True,
            capture_output=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        if path.is_symlink():
            return path.readlink().as_posix().encode("utf-8")
        return path.read_bytes()


def sha256_bytes(content: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(content)
    return digest.hexdigest()


def json_object(content: bytes) -> dict[str, Any] | None:
    try:
        payload = json.loads(content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if isinstance(payload, dict):
        return payload
    return None


def manifest_relative_path(value: Any, *, field: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError(f"{field} must be a non-empty POSIX relative path")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts or candidate.as_posix() == ".":
        raise ValueError(f"{field} must stay inside the owner repository")
    return candidate


def home_skill_projection_sources(
    repo_root: Path,
    tracked_entries: dict[Path, dict[str, str]],
) -> dict[Path, dict[str, Path]]:
    """Validate owner skill exposure and resolve v1 copies to owner sources."""

    if HOME_SKILL_PORT_MANIFEST not in tracked_entries:
        return {}
    payload = json_object(
        source_bytes(
            repo_root,
            HOME_SKILL_PORT_MANIFEST,
            repo_root / HOME_SKILL_PORT_MANIFEST,
        )
    )
    if payload is None:
        raise ValueError(f"{HOME_SKILL_PORT_MANIFEST} must be a JSON object")
    schema_version = payload.get("schema_version")
    if schema_version not in {
        HOME_SKILL_PORT_SCHEMA_VERSION_V1,
        HOME_SKILL_PORT_SCHEMA_VERSION_V2,
    }:
        return {}

    bundles = payload.get("bundles")
    if not isinstance(bundles, list):
        raise ValueError(f"{HOME_SKILL_PORT_MANIFEST} must declare bundles")
    source_roots: dict[str, Path] = {}
    for bundle in bundles:
        if not isinstance(bundle, dict):
            raise ValueError(f"{HOME_SKILL_PORT_MANIFEST} bundles must be objects")
        name = bundle.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError(f"{HOME_SKILL_PORT_MANIFEST} bundle name is invalid")
        if name in source_roots:
            raise ValueError(f"{HOME_SKILL_PORT_MANIFEST} repeats bundle {name}")
        source_roots[name] = manifest_relative_path(
            bundle.get("path"),
            field=f"skills/port.manifest.json bundle {name} path",
        )

    if schema_version == HOME_SKILL_PORT_SCHEMA_VERSION_V2:
        exposure = payload.get("exposure")
        if not isinstance(exposure, dict):
            raise ValueError(
                f"{HOME_SKILL_PORT_MANIFEST} v2 must declare exposure"
            )
        expected_exposure = {
            "runtime": "codex",
            "scope": "user",
            "profile": "os-user-default",
            "mode": "profile-selected",
        }
        for field, expected in expected_exposure.items():
            if exposure.get(field) != expected:
                raise ValueError(
                    f"{HOME_SKILL_PORT_MANIFEST} exposure.{field} "
                    f"must equal {expected!r}"
                )
        exposed_names = exposure.get("skills")
        if not isinstance(exposed_names, list) or not all(
            isinstance(name, str) and name for name in exposed_names
        ):
            raise ValueError(
                f"{HOME_SKILL_PORT_MANIFEST} exposure.skills must name bundles"
            )
        if exposed_names != list(source_roots):
            raise ValueError(
                f"{HOME_SKILL_PORT_MANIFEST} bundle and exposure names must match"
            )
        for name, source_root in source_roots.items():
            skill_source = source_root / "SKILL.md"
            if skill_source not in tracked_entries:
                raise ValueError(
                    f"declared owner skill {name} has no canonical source "
                    f"{skill_source.as_posix()}"
                )
            repo_projection_root = Path(".agents/skills") / name
            duplicate_paths = sorted(
                rel.as_posix()
                for rel in tracked_entries
                if rel == repo_projection_root or repo_projection_root in rel.parents
            )
            if duplicate_paths:
                raise ValueError(
                    f"OS user-exposed skill {name} has a same-name repo projection: "
                    + ", ".join(duplicate_paths)
                )
        return {}

    projection = payload.get("projection")
    if not isinstance(projection, dict):
        raise ValueError(
            f"{HOME_SKILL_PORT_MANIFEST} v1 must declare projection"
        )
    if projection.get("mode") != "generated-copy":
        raise ValueError(
            f"{HOME_SKILL_PORT_MANIFEST} v1 projection mode must be generated-copy"
        )
    projection_root = manifest_relative_path(
        projection.get("root"),
        field="skills/port.manifest.json projection.root",
    )
    projected_names = projection.get("skills")
    if not isinstance(projected_names, list) or not all(
        isinstance(name, str) and name for name in projected_names
    ):
        raise ValueError(
            f"{HOME_SKILL_PORT_MANIFEST} projection.skills must name bundles"
        )
    if set(projected_names) != set(source_roots):
        raise ValueError(
            f"{HOME_SKILL_PORT_MANIFEST} bundle and projection names must match"
        )

    resolved: dict[Path, dict[str, Path]] = {}
    for rel, projection_entry in tracked_entries.items():
        try:
            within_projection = rel.relative_to(projection_root)
        except ValueError:
            continue
        if len(within_projection.parts) < 2:
            raise ValueError(
                f"declared skill projection file is outside a bundle: {rel.as_posix()}"
            )
        bundle_name = within_projection.parts[0]
        source_root = source_roots.get(bundle_name)
        if source_root is None:
            raise ValueError(
                f"undeclared skill projection bundle: {bundle_name}"
            )
        source_rel = source_root.joinpath(*within_projection.parts[1:])
        source_entry = tracked_entries.get(source_rel)
        if source_entry is None:
            raise ValueError(
                f"skill projection {rel.as_posix()} has no canonical source "
                f"{source_rel.as_posix()}"
            )
        if (
            projection_entry["blob_id"] != source_entry["blob_id"]
            or projection_entry["mode"] != source_entry["mode"]
        ):
            raise ValueError(
                f"skill projection {rel.as_posix()} does not match canonical source "
                f"{source_rel.as_posix()}"
            )
        resolved[rel] = {
            "source": source_rel,
            "manifest": HOME_SKILL_PORT_MANIFEST,
        }
    return resolved


def declares_generated_from_source(content: bytes) -> bool:
    payload = json_object(content)
    if payload is None:
        return False
    return payload.get("generated_or_authored") == "generated_from_source"


def generated_record_builder_surface(content: bytes) -> str:
    payload = json_object(content)
    if payload is None:
        return ""
    builder = payload.get("builder")
    if not isinstance(builder, dict):
        return ""
    surface = builder.get("surface")
    if isinstance(surface, str) and surface:
        return surface
    return ""


def local_kag_manifest(repo_root: Path) -> dict[str, Any] | None:
    manifest_path = repo_root / "kag" / "manifest.json"
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    if isinstance(payload, dict):
        return payload
    return None


def manifest_validation_route(repo_root: Path, lane: str) -> str:
    manifest = local_kag_manifest(repo_root)
    if manifest is None:
        return ""
    routes = manifest.get("validation_routes")
    if not isinstance(routes, list):
        return ""
    for item in routes:
        if not isinstance(item, dict):
            continue
        if item.get("lane") == lane and isinstance(item.get("route"), str):
            return item["route"]
    return ""


def index_generator_route(repo: str) -> str:
    if repo == "aoa-kag":
        return LOCAL_INDEX_GENERATOR_ROUTE
    return EXTERNAL_INDEX_GENERATOR_ROUTE


def kag_validator_route(repo_root: Path, repo: str, tracked_paths: set[Path]) -> str:
    if repo == "aoa-kag" or Path(LOCAL_KAG_VALIDATOR_ROUTE) in tracked_paths:
        return LOCAL_KAG_VALIDATOR_ROUTE
    return manifest_validation_route(repo_root, "local-kag") or EXTERNAL_KAG_VALIDATOR_ROUTE


def heading_refs(content: bytes, rel_path: str) -> list[dict[str, Any]]:
    try:
        headings = markdown_headings(content.decode("utf-8"))
    except UnicodeDecodeError:
        return []
    return [
        {
            "level": int(heading["level"]),
            "title": str(heading["title"]),
            "anchor": str(heading["fragment"]),
            "line": int(heading["line"]),
            "ref": f"{rel_path}#{heading['fragment']}",
        }
        for heading in headings
    ]


def mime_for(path: Path, content: bytes = b"", *, git_mode: str = "") -> str:
    if git_mode == "120000":
        return "inode/symlink"
    suffix_chain = tuple(suffix.lower() for suffix in path.suffixes[-2:])
    chain_mime = PORTABLE_MIME_BY_SUFFIX_CHAIN.get(suffix_chain)
    if chain_mime:
        return chain_mime
    suffix_mime = PORTABLE_MIME_BY_SUFFIX.get(path.suffix.lower())
    if suffix_mime:
        return suffix_mime
    if path.name in PORTABLE_TEXT_BASENAMES or path.name.startswith("LICENSE."):
        return "text/plain"
    first_line = content.partition(b"\n")[0].lower()
    if first_line.startswith(b"#!"):
        interpreter_tokens = set(re.split(rb"[/\s]+", first_line[2:].strip()))
        if any(
            re.fullmatch(rb"python(?:\d+(?:\.\d+)*)?", token)
            for token in interpreter_tokens
        ):
            return "text/x-python"
        if interpreter_tokens & {b"bash", b"dash", b"ksh", b"sh", b"zsh"}:
            return "application/x-sh"
        if interpreter_tokens & {b"bun", b"deno", b"node"}:
            return "text/javascript"
        return "text/plain"
    return "application/octet-stream"


def document_role(rel: Path) -> str:
    name = rel.name
    parts = rel.parts
    if rel.suffix != ".md":
        return "none"
    if name == "SKILL.md" and len(parts) >= 3 and parts[0] == "skills":
        return "skill"
    if name == "README.md":
        return "readme"
    if name == "AGENTS.md":
        return "agents"
    if name == "DESIGN.md":
        return "design"
    if name == "DESIGN.AGENTS.md":
        return "design_agents"
    if name == "PARTS.md":
        return "parts"
    if name == "PROVENANCE.md":
        return "provenance"
    if name == "ROADMAP.md":
        return "roadmap"
    if name == "CHANGELOG.md":
        return "changelog"
    if name == "COMMANDS.md":
        return "commands"
    if "decisions" in parts:
        return "decision"
    if "mechanics" in parts:
        return "mechanics_doc"
    if "reports" in parts:
        return "report"
    if "audit" in rel.as_posix():
        return "audit"
    if "release" in rel.as_posix().lower():
        return "release_notes"
    if "handoff" in rel.as_posix().lower():
        return "handoff"
    if "validation" in parts:
        return "validation_doc"
    if "testing" in parts:
        return "testing_doc"
    if name == "SOURCE_POLICY.md":
        return "source_policy"
    if name == "BOUNDARIES.md":
        return "boundary"
    return "unknown_document"


def is_env_config_name(name: str) -> bool:
    return name in ENV_CONFIG_NAMES or any(
        name.endswith(suffix)
        for suffix in (".env", ".env.example", ".env.sample", ".env.template")
    )


def has_shebang(content: bytes) -> bool:
    return content.startswith(b"#!")


def artifact_kind(rel: Path, content: bytes = b"", *, git_mode: str = "") -> str:
    parts = rel.parts
    name = rel.name
    suffix = rel.suffix.lower()
    if git_mode == "120000":
        return "symlink"
    if name in {"LICENSE", "COPYING"}:
        return "license"
    if name in OWNER_METADATA_NAMES or (len(parts) >= 2 and parts[0] == ".github" and name == "CODEOWNERS"):
        return "owner_metadata"
    if name in DIRECTORY_MARKER_NAMES:
        return "directory_marker"
    if (
        is_env_config_name(name)
        or name in BUILD_CONFIG_NAMES
        or name.endswith(".Dockerfile")
        or suffix in CONFIG_SUFFIXES
    ):
        return "config"
    if name.startswith("requirements") and suffix == ".txt":
        return "dependency_manifest"
    if "receipts" in parts:
        return "receipt"
    if suffix in ASSET_SUFFIXES:
        return "asset"
    if suffix in DATA_TABLE_SUFFIXES:
        return "data_table"
    if suffix in RECORD_LOG_SUFFIXES:
        return "record_log"
    if "fixtures" in parts and suffix in HTML_SUFFIXES:
        return "fixture"
    if suffix in SPREADSHEET_SUFFIXES:
        return "spreadsheet"
    if suffix in ARCHIVE_SUFFIXES:
        return "archive"
    if suffix in SERVICE_UNIT_SUFFIXES:
        return "service_unit"
    if name == "SECURITY.md":
        return "security"
    if is_generated_decision_index(rel):
        return "generated_readmodel"
    if suffix == ".md":
        return "document"
    if "indexes" in parts:
        return "index"
    if "projections" in parts:
        return "projection"
    if "generated" in parts:
        return "generated_readmodel"
    if suffix == ".json" and ("schemas" in parts or name.endswith(".schema.json")):
        return "schema"
    if suffix in {".json", ".yaml", ".yml", ".toml"} and (
        "manifests" in parts or name in {"package.json", "pyproject.toml"}
    ):
        return "manifest" if name != "package.json" else "package_manifest"
    if suffix in {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}:
        return "config"
    if suffix == ".py" and is_test_entrypoint(rel):
        return "test"
    if is_command_entrypoint(rel, content) and name.startswith("validate_"):
        return "validator"
    if is_command_entrypoint(rel, content):
        return "script"
    if "mechanics" in parts:
        return "mechanics_surface"
    if suffix in SOURCE_CODE_SUFFIXES:
        return "source_code"
    if suffix in TEXT_ARTIFACT_SUFFIXES:
        return "text_artifact"
    if suffix in TEXT_WRAPPER_SUFFIXES:
        return "text_artifact"
    return "unknown"


def is_command_entrypoint(rel: Path, content: bytes = b"") -> bool:
    if len(rel.parts) >= 2 and rel.parts[0] == ".codex" and rel.parts[1] == "bin":
        return True
    if has_shebang(content):
        return True
    if rel.suffix not in COMMAND_SUFFIXES:
        return False
    name = rel.name
    if rel.suffix == ".py" and name in LANE_ENTRYPOINTS:
        return True
    if name.startswith(COMMAND_PREFIXES):
        return True
    return False


def is_test_entrypoint(rel: Path) -> bool:
    return rel.suffix == ".py" and "tests" in rel.parts and rel.name.startswith("test_")


def is_generated_decision_index(rel: Path) -> bool:
    return len(rel.parts) >= 4 and rel.parts[:3] == ("docs", "decisions", "indexes")


def decision_index_builder_for(tracked_paths: set[Path]) -> str:
    candidates = sorted(
        candidate
        for candidate in tracked_paths
        if candidate.parts
        and candidate.parts[0] == "scripts"
        and candidate.name in DECISION_INDEX_BUILDER_NAMES
    )
    if len(candidates) == 1:
        return candidates[0].as_posix()
    return ""


def code_role(rel: Path, kind: str) -> str:
    if rel.suffix not in SOURCE_CODE_SUFFIXES and kind not in {"script", "validator"}:
        return "none"
    if kind == "test":
        return "test"
    if kind == "validator":
        return "validator"
    if rel.name.startswith(BUILDER_PREFIXES):
        return "builder"
    if rel.name in {"ci_gate.py", "release_check.py"}:
        return "entrypoint"
    if kind == "script":
        return "entrypoint"
    return "source_module"


def mechanics_role(rel: Path) -> str:
    parts = rel.parts
    if "mechanics" not in parts:
        return "none"
    if "legacy" in parts:
        return "legacy"
    if "parts" in parts:
        part_index = parts.index("parts")
        if len(parts) > part_index + 1:
            if rel.name == "CONTRACT.md":
                return "part_contract"
            if rel.suffix == ".md":
                return "part_doc"
            if "schemas" in parts:
                return "part_schema"
            if "scripts" in parts:
                return "part_script"
            if "tests" in parts:
                return "part_test"
            return "mechanic_part"
    return "mechanic_package"


def command_role(rel: Path, kind: str, doc_role: str) -> str:
    if doc_role == "commands":
        return "command_doc"
    if kind == "validator":
        return "validator"
    if kind == "test":
        return "test"
    if kind == "script" and rel.name.startswith(BUILDER_PREFIXES):
        return "builder"
    if kind == "script":
        if rel.name in {"ci_gate.py", "release_check.py", "run_tests.py"}:
            return "lane_entrypoint"
        return "script"
    return "none"


def surface_state(
    rel: Path,
    kind: str,
    *,
    repo: str,
    declared_generated: bool = False,
    generated_projection: bool = False,
) -> str:
    parts = rel.parts
    if generated_projection:
        return "generated_projection"
    if declared_generated:
        return "generated_readmodel"
    if "legacy" in parts or "archive" in parts:
        return "legacy"
    if rel.name == "AGENTS.md":
        return "authored_source"
    if is_generated_decision_index(rel):
        return "generated_readmodel"
    if kind == "receipt":
        return "receipt"
    if kind == "generated_readmodel" or "generated" in parts:
        return "generated_readmodel"
    if kind in {"index", "projection"} and (not parts or parts[0] != "kag"):
        return "generated_readmodel"
    return "authored_source"


def observed_form(
    kind: str,
    command: str,
    *,
    state: str = "",
    git_mode: str = "",
) -> str:
    if git_mode == "120000":
        return "symlink"
    if command != "none":
        return "command"
    if kind == "generated_readmodel" or state in {
        "generated_projection",
        "generated_readmodel",
    }:
        return "generated_output"
    return "file"


def primary_kind(kind: str, doc_role: str, command: str) -> str:
    if doc_role != "none":
        return "document"
    if command != "none":
        return "command"
    if kind in {
        "archive",
        "asset",
        "data_table",
        "dependency_manifest",
        "directory_marker",
        "fixture",
        "generated_readmodel",
        "index",
        "owner_metadata",
        "projection",
        "receipt",
        "record_log",
        "service_unit",
        "spreadsheet",
        "symlink",
        "text_artifact",
    }:
        return "artifact"
    if kind == "unknown":
        return "unknown"
    return "surface"


def source_authority(state: str) -> str:
    if state in {"generated_projection", "generated_readmodel"}:
        return "derived_readmodel"
    if state == "receipt":
        return "generated_receipt"
    return "authored_source"


def route_kind_for(kind: str, doc_role: str, command: str) -> str:
    if doc_role != "none":
        return "document_owner"
    if command in {"validator", "test"}:
        return f"{command}_owner"
    if command != "none":
        return "command_owner"
    if kind in {"schema", "manifest"}:
        return f"{kind}_owner"
    return "source_owner"


def repo_uses_pytest(repo_root: Path, tracked_paths: set[Path]) -> bool:
    if Path("pyproject.toml") in tracked_paths:
        try:
            pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
        except FileNotFoundError:
            pyproject = ""
        if "[tool.pytest" in pyproject or "pytest" in pyproject:
            return True
    return Path("pytest.ini") in tracked_paths or Path("tox.ini") in tracked_paths


def pytest_command_for(repo_root: Path) -> str:
    prefix = "PYTHONPATH=src " if (repo_root / "src").is_dir() else ""
    return f"{prefix}python -m pytest -q"


def owner_commands_for(
    rel: Path,
    command: str,
    *,
    repo_root: Path,
    tracked_paths: set[Path],
) -> list[str]:
    executable = {
        ".py": "python",
        ".ps1": "pwsh",
        ".sh": "bash",
    }.get(rel.suffix)
    command_surface = f"{executable} {rel.as_posix()}" if executable else rel.as_posix()
    if command == "validator":
        return [command_surface]
    if command == "test":
        if repo_uses_pytest(repo_root, tracked_paths):
            return [pytest_command_for(repo_root)]
        return [f"python -m unittest {rel.as_posix()}"]
    if rel.as_posix() == "scripts/ci_gate.py":
        return [
            "python scripts/ci_gate.py --mode source-fast",
            "python scripts/ci_gate.py --mode generated",
        ]
    if command in {"script", "builder", "lane_entrypoint"}:
        return [command_surface]
    return []


def part_local_generated_by_for(rel: Path, tracked_paths: set[Path]) -> str:
    parts = rel.parts
    if len(parts) < 6 or parts[0] != "mechanics" or "parts" not in parts or "generated" not in parts:
        return ""
    generated_index = parts.index("generated")
    part_root = Path(*parts[:generated_index])
    builder_prefix = part_root / "scripts"
    builders = sorted(
        candidate
        for candidate in tracked_paths
        if candidate.parent == builder_prefix
        and candidate.name.startswith("build_")
        and candidate.suffix == ".py"
    )
    if len(builders) == 1:
        return builders[0].as_posix()
    return ""


def source_builder_contents(
    repo_root: Path,
    tracked_paths: set[Path],
) -> tuple[tuple[Path, bytes], ...]:
    builders: list[tuple[Path, bytes]] = []
    for candidate in sorted(tracked_paths):
        if (
            candidate.parts
            and candidate.parts[0] == "scripts"
            and candidate.suffix == ".py"
            and candidate.name.startswith(BUILDER_PREFIXES)
        ):
            builders.append((candidate, source_bytes(repo_root, candidate, repo_root / candidate)))
    return tuple(builders)


def ast_contains_reference(node: ast.AST, reference_pattern: re.Pattern[bytes]) -> bool:
    return any(
        isinstance(candidate, ast.Constant)
        and isinstance(candidate.value, str)
        and reference_pattern.search(candidate.value.encode("utf-8"))
        for candidate in ast.walk(node)
    )


def ast_target_names(node: ast.AST) -> set[str]:
    return {
        candidate.id
        for candidate in ast.walk(node)
        if isinstance(candidate, ast.Name)
    }


def identifier_tokens(name: str) -> set[str]:
    snake_case = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name).lower()
    return {token for token in re.split(r"[^a-z0-9]+", snake_case) if token}


def call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr.lower()
    if isinstance(node.func, ast.Name):
        return node.func.id.lower()
    return ""


def ast_expression_references(
    node: ast.AST,
    reference_pattern: re.Pattern[bytes],
    reference_names: set[str],
) -> bool:
    return ast_contains_reference(node, reference_pattern) or any(
        isinstance(candidate, ast.Name) and candidate.id in reference_names
        for candidate in ast.walk(node)
    )


@lru_cache(maxsize=None)
def parsed_builder_ast(content: bytes) -> ast.Module | None:
    try:
        return ast.parse(content.decode("utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return None


def builder_reference_role(content: bytes, reference_pattern: re.Pattern[bytes]) -> str:
    tree = parsed_builder_ast(content)
    if tree is None:
        return "unknown"

    reference_names: set[str] = set()
    output_names: set[str] = set()
    input_names: set[str] = set()
    for node in ast.walk(tree):
        targets: list[ast.AST] = []
        value: ast.AST | None = None
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        elif isinstance(node, ast.NamedExpr):
            targets = [node.target]
            value = node.value
        if value is None or not ast_contains_reference(value, reference_pattern):
            continue
        names = set().union(*(ast_target_names(target) for target in targets))
        reference_names.update(names)
        for name in names:
            tokens = identifier_tokens(name)
            if tokens & {"dest", "destination", "generated", "out", "output", "target"}:
                output_names.add(name)
            if tokens & {"donor", "input", "read", "reader", "source"}:
                input_names.add(name)

    input_call_found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            encoded = node.value.encode("utf-8")
            if reference_pattern.search(encoded) and OUTPUT_REFERENCE_LITERAL.search(encoded):
                return "output"
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node)
        receiver = node.func.value if isinstance(node.func, ast.Attribute) else None
        first_arg = node.args[0] if node.args else None
        receiver_references = receiver is not None and ast_expression_references(
            receiver,
            reference_pattern,
            reference_names,
        )
        first_arg_references = first_arg is not None and ast_expression_references(
            first_arg,
            reference_pattern,
            reference_names,
        )
        if name.startswith("write") and (receiver_references or first_arg_references):
            return "output"
        if name.startswith(("emit", "export", "publish", "save")):
            if first_arg_references:
                return "output"
        if name.startswith(("load", "read")) and (receiver_references or first_arg_references):
            input_call_found = True
        if name == "open":
            method_call = isinstance(node.func, ast.Attribute)
            path_references = receiver_references if method_call else first_arg_references
            mode_arg_index = 0 if method_call else 1
            modes: set[str] = set()
            if len(node.args) > mode_arg_index and isinstance(
                node.args[mode_arg_index], ast.Constant
            ):
                mode_value = node.args[mode_arg_index].value
                if isinstance(mode_value, str):
                    modes.add(mode_value)
            modes.update(
                keyword.value.value
                for keyword in node.keywords
                if keyword.arg == "mode"
                and isinstance(keyword.value, ast.Constant)
                and isinstance(keyword.value.value, str)
            )
            if path_references and any(set(mode) & {"a", "w", "x"} for mode in modes):
                return "output"
            if path_references and (not modes or any("r" in mode for mode in modes)):
                input_call_found = True

    if output_names:
        return "output"
    if input_names or input_call_found:
        return "input"
    return "unknown"


def normalized_generated_stem(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    for suffix in ("_catalog", "_index", "_inventory", "_manifest", "_registry"):
        normalized = normalized.removesuffix(suffix)
    return normalized


def source_referencing_builder_for(
    rel: Path,
    builders: tuple[tuple[Path, bytes], ...],
) -> str:
    output_stem = rel.name
    for suffix in reversed(rel.suffixes):
        output_stem = output_stem[: -len(suffix)]
        if suffix not in {".json", ".yaml", ".yml", ".md"}:
            break
    output_stem = output_stem.removesuffix(".min").removesuffix(".example")
    target_ref = re.escape(rel.as_posix().encode("utf-8"))
    reference_pattern = re.compile(
        rb"(?<![A-Za-z0-9._/-])" + target_ref + rb"(?![A-Za-z0-9._/-])"
    )
    referencing = [
        (candidate, builder_reference_role(content, reference_pattern))
        for candidate, content in builders
        if reference_pattern.search(content)
    ]
    output_matches = [candidate for candidate, role in referencing if role == "output"]
    if len(output_matches) == 1:
        return output_matches[0].as_posix()
    if len(output_matches) > 1:
        return ""
    normalized_output_stem = normalized_generated_stem(output_stem)
    matching = [
        candidate
        for candidate, role in referencing
        if role != "input"
        and normalized_generated_stem(
            candidate.stem.removeprefix("build_").removeprefix("generate_")
        )
        == normalized_output_stem
    ]
    if len(matching) == 1:
        return matching[0].as_posix()
    return ""


def generated_by_for(
    rel: Path,
    state: str,
    tracked_paths: set[Path],
    source_builders: tuple[tuple[Path, bytes], ...],
    content: bytes,
    *,
    repo_root: Path,
) -> str:
    if state == "generated_projection":
        return HOME_SKILL_PROJECTION_BUILDER_ROUTE
    if state != "generated_readmodel":
        return ""
    rel_path = rel.as_posix()
    builder_surface = generated_record_builder_surface(content)
    if builder_surface:
        return builder_surface
    payload = json_object(content)
    if (
        isinstance(payload, dict)
        and payload.get("generated_or_authored") == "generated_from_source"
        and len(rel.parts) >= 2
        and rel.parts[0] == "kag"
    ):
        owner_route = manifest_validation_route(repo_root, "owner-local")
        if owner_route:
            return owner_route
    if rel_path.startswith("generated/repo_local_kag_coverage"):
        return "scripts/generate_repo_local_kag_coverage.py"
    if is_generated_decision_index(rel):
        return decision_index_builder_for(tracked_paths)
    part_local_builder = part_local_generated_by_for(rel, tracked_paths)
    if part_local_builder:
        return part_local_builder
    source_referencing_builder = source_referencing_builder_for(
        rel,
        source_builders,
    )
    if source_referencing_builder:
        return source_referencing_builder
    if rel_path.startswith("generated/") or "/generated/" in rel_path:
        generic_builder = Path("scripts/generate_kag.py")
        return generic_builder.as_posix() if generic_builder in tracked_paths else ""
    return ""


def abi_for(content: bytes, rel: Path, kind: str, state: str) -> dict[str, str]:
    schema_version = "none"
    contract_version = "none"
    if rel.suffix == ".json":
        try:
            payload = json.loads(content.decode("utf-8"))
            if isinstance(payload, dict):
                schema_version = str(payload.get("schema_version") or payload.get("$schema") or "none")
                contract_version = str(payload.get("$id") or payload.get("contract_version") or "none")
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    compatibility = (
        "generated"
        if state in {"generated_projection", "generated_readmodel"}
        else "stable"
    )
    if state == "legacy":
        compatibility = "legacy"
    if kind == "unknown":
        compatibility = "unknown"
    return {
        "artifact_class": kind,
        "schema_version": schema_version,
        "abi_epoch": "source",
        "contract_version": contract_version,
        "compatibility": compatibility,
    }


def access_for(rel_path: str) -> dict[str, str]:
    lowered = rel_path.lower()
    risk = "review" if any(hint in lowered for hint in SECRET_HINTS) else "none"
    return {"scope": "public", "secrets_risk": risk}


def build_record(
    path: Path,
    rel: Path,
    *,
    repo_root: Path,
    repo: str,
    snapshot_ref: str,
    tracked_paths: set[Path],
    source_builders: tuple[tuple[Path, bytes], ...],
    lineage_path: Path,
    git_blob_id: str,
    git_mode: str = "",
    skill_projection: dict[str, Path] | None = None,
) -> dict[str, Any]:
    rel_path = rel.as_posix()
    content = source_bytes(repo_root, rel, path)
    digest = sha256_bytes(content)
    stable_identity = artifact_identity(
        repo,
        rel,
        lineage_path=lineage_path,
        content_hash=digest,
    )
    declared_generated = declares_generated_from_source(content)
    kind = artifact_kind(rel, content, git_mode=git_mode)
    doc_role = document_role(rel)
    code = code_role(rel, kind)
    mech = mechanics_role(rel)
    command = command_role(rel, kind, doc_role)
    state = surface_state(
        rel,
        kind,
        repo=repo,
        declared_generated=declared_generated,
        generated_projection=skill_projection is not None,
    )
    headings = heading_refs(content, rel_path) if doc_role != "none" else []
    line_refs = [f"{rel_path}:1"] if content else []
    source_rel = skill_projection["source"] if skill_projection else rel
    authority = "authored_source" if skill_projection else source_authority(state)
    provenance_source_ref = {
        "repo": repo,
        "path": source_rel.as_posix(),
        "role": "primary",
        "authority": authority,
    }
    provenance_materials = (
        [
            {
                "repo": repo,
                "path": skill_projection["manifest"].as_posix(),
                "role": "material",
                "authority": "authored_source",
            }
        ]
        if skill_projection
        else []
    )
    generated_by = generated_by_for(
        rel,
        state,
        tracked_paths,
        source_builders,
        content,
        repo_root=repo_root,
    )
    observed_by = index_generator_route(repo)
    validated_by = kag_validator_route(repo_root, repo, tracked_paths)
    provenance_validators = [validated_by]
    if skill_projection:
        provenance_validators.append(HOME_SKILL_PROJECTION_VALIDATOR_ROUTE)
    mime = mime_for(path, content, git_mode=git_mode)
    required_tools = []
    if rel.suffix == ".py":
        required_tools.append("python")
    if command != "none" and rel.suffix == ".ps1":
        required_tools.append("pwsh")
    if command != "none" and rel.suffix == ".sh":
        required_tools.append("bash")
    if command != "none" and not rel.suffix:
        if mime == "text/x-python":
            required_tools.append("python")
        elif mime == "application/x-sh":
            required_tools.append("bash")
        elif mime == "text/javascript":
            required_tools.append("node")
    if rel.suffix in {".json", ".yaml", ".yml"}:
        required_tools.append("jq")
    return {
        "identity": {
            **stable_identity,
            "repo": repo,
            "path": rel_path,
            "git_ref": snapshot_ref,
            "git_blob_id": git_blob_id,
            "content_hash": digest,
            "size_bytes": len(content),
            "mime": mime,
        },
        "observed_form": observed_form(
            kind,
            command,
            state=state,
            git_mode=git_mode,
        ),
        "surface_state": state,
        "artifact_kind": kind,
        "document_role": doc_role,
        "code_role": code,
        "mechanics_role": mech,
        "command_role": command,
        "abi": abi_for(content, rel, kind, state),
        "signs": {
            "digest": digest,
            "signature_ref": "",
            "attestation_ref": "",
            "verification_state": "digest-only",
        },
        "provenance": {
            "observed_by": observed_by,
            "generated_by": generated_by,
            "validated_by": provenance_validators,
            "source_refs": [provenance_source_ref],
            "materials": provenance_materials,
        },
        "toolchain": {
            "detected_tools": ["git", "python"],
            "required_tools": sorted(set(required_tools)),
            "owner_commands": owner_commands_for(
                rel,
                command,
                repo_root=repo_root,
                tracked_paths=tracked_paths,
            ),
        },
        "classification": {
            "primary_kind": primary_kind(kind, doc_role, command),
            "confidence": "low" if kind == "unknown" else "high",
        },
        "freshness": {"mode": "source_snapshot", "state": "current", "checked_ref": snapshot_ref},
        "access": access_for(rel_path),
        "refs": {
            "path_ref": rel_path,
            "line_refs": line_refs,
            "heading_refs": headings,
        },
        "owner_return_route": {
            "repo": repo,
            "surface": source_rel.as_posix(),
            "route_kind": route_kind_for(kind, doc_role, command),
        },
        "validator_route": {
            "repo": "aoa-kag" if validated_by.startswith("aoa-kag:") else repo,
            "surface": validated_by,
            "route_kind": "source_fast",
        },
        "consumer_route": {
            "repo": "aoa-kag",
            "surface": "scripts/query_repo_local_kag.py",
            "route_kind": "query",
        },
    }


def coverage_summary(records: Sequence[dict[str, Any]]) -> dict[str, int]:
    return {
        "record_count": len(records),
        "document_count": sum(1 for record in records if record["document_role"] != "none"),
        "heading_count": sum(len(record["refs"]["heading_refs"]) for record in records),
        "mechanics_count": sum(1 for record in records if record["mechanics_role"] != "none"),
        "command_count": sum(1 for record in records if record["command_role"] != "none"),
        "validator_count": sum(1 for record in records if record["command_role"] == "validator"),
        "test_count": sum(1 for record in records if record["command_role"] == "test"),
        "script_count": sum(1 for record in records if record["artifact_kind"] == "script"),
        "schema_count": sum(1 for record in records if record["artifact_kind"] == "schema"),
        "generated_count": sum(1 for record in records if record["surface_state"] == "generated_readmodel"),
        "unknown_count": sum(1 for record in records if record["artifact_kind"] == "unknown"),
    }


def count_values(records: Sequence[dict[str, Any]], *keys: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value: Any = record
        for key in keys:
            if not isinstance(value, dict):
                value = ""
                break
            value = value.get(key)
        if isinstance(value, str) and value:
            counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def classification_summary(records: Sequence[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        "artifact_kind": count_values(records, "artifact_kind"),
        "primary_kind": count_values(records, "classification", "primary_kind"),
        "surface_state": count_values(records, "surface_state"),
        "document_role": count_values(records, "document_role"),
        "mechanics_role": count_values(records, "mechanics_role"),
        "command_role": count_values(records, "command_role"),
    }


def payload_digest(payload: dict[str, Any]) -> str:
    copy_payload = copy.deepcopy(payload)
    copy_payload["index_identity"]["content_digest"] = ZERO_DIGEST
    encoded = json.dumps(copy_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_index(
    repo_root: Path,
    *,
    output: Path | None = None,
    excluded_outputs: Sequence[Path] = (),
    previous_index: dict[str, Any] | None = None,
    history_ref: str | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    history_ref = effective_history_ref(repo_root, history_ref)
    name = repo_name(repo_root)
    snapshot_ref = source_snapshot_ref(repo_root)
    excluded_paths = {CANONICAL_SELF_INDEX, *CANONICAL_REPOSITORY_INDEX_PATHS}
    selected_outputs = (*excluded_outputs, *((output,) if output is not None else ()))
    for selected_output in selected_outputs:
        output_path = (
            selected_output
            if selected_output.is_absolute()
            else repo_root / selected_output
        )
        try:
            excluded_paths.add(output_path.resolve().relative_to(repo_root))
        except ValueError:
            if not selected_output.is_absolute():
                excluded_paths.add(selected_output)
    tracked_entries = git_file_entries(repo_root)
    tracked_paths = set(tracked_entries)
    skill_projections = home_skill_projection_sources(repo_root, tracked_entries)
    indexed_paths = {
        path
        for path in tracked_paths - excluded_paths
        if not is_portable_family_control_path(path)
    }
    lineage_paths = git_lineage_paths(
        repo_root,
        tracked_paths,
        history_ref=history_ref,
    )
    source_builders = source_builder_contents(repo_root, tracked_paths)
    previous_records = {
        Path(str(record["identity"]["path"])): record
        for record in (previous_index or {}).get("records", [])
        if isinstance(record, dict) and isinstance(record.get("identity"), dict)
    }
    previous_paths = set(previous_records)
    global_invalidation = previous_paths != indexed_paths
    if not global_invalidation and previous_records:
        global_inputs = {
            path
            for path in indexed_paths
            if path == Path("kag/manifest.json")
            or path == HOME_SKILL_PORT_MANIFEST
            or path in REPO_LOCAL_GENERATOR_HELPER_PATHS
            or path.name.startswith(("build_", "generate_"))
            or "builders" in path.parts
        }
        global_invalidation = any(
            str(previous_records[path]["identity"].get("git_blob_id") or "")
            != tracked_entries[path]["blob_id"]
            for path in global_inputs
            if path in previous_records
        )
    records = []
    for rel in sorted(indexed_paths):
        path = repo_root / rel
        if snapshot_ref == GIT_INDEX_SOURCE_REF or path.is_file():
            previous = previous_records.get(rel)
            if (
                previous is not None
                and not global_invalidation
                # Projection meaning comes from the owner manifest and KAG
                # classifier, not only from the copied file blob. Rebuild the
                # small declared projection set so an incremental migration
                # cannot preserve older authored-source provenance.
                and rel not in skill_projections
                and str(previous["identity"].get("git_blob_id") or "")
                == tracked_entries[rel]["blob_id"]
                and str(previous["identity"].get("lineage_path") or "")
                == lineage_paths[rel].as_posix()
            ):
                records.append(copy.deepcopy(previous))
                continue
            records.append(
                build_record(
                    path,
                    rel,
                    repo_root=repo_root,
                    repo=name,
                    snapshot_ref=snapshot_ref,
                    tracked_paths=tracked_paths,
                    source_builders=source_builders,
                    lineage_path=lineage_paths[rel],
                    git_blob_id=tracked_entries[rel]["blob_id"],
                    git_mode=tracked_entries[rel]["mode"],
                    skill_projection=skill_projections.get(rel),
                )
            )
    records.sort(key=lambda record: record["identity"]["path"])
    payload: dict[str, Any] = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "repo": {
            "name": name,
            "namespace": repository_namespace(name),
            "owner_type": owner_type_for(name, repo_root),
            "root": ".",
            "git_ref": snapshot_ref,
        },
        "index_identity": {
            "local_id": "index:repo-local:source-surfaces",
            "artifact_kind": "source_surface_index",
            "content_digest": ZERO_DIGEST,
            "schema_ref": INDEX_SCHEMA_REF,
        },
        "toolchain": {
            "baseline_tools": list(BASELINE_TOOLS),
            "capability_lanes": list(CAPABILITY_LANES),
        },
        "coverage_summary": coverage_summary(records),
        "classification_summary": classification_summary(records),
        "records": records,
        "registry_output": {
            "consumer": "aoa-kag",
            "resource_shape": [
                "repo-local-source-surface-index",
                "repo-local-document-records",
                "repo-local-mechanics-records",
                "repo-local-command-records",
            ],
            "stable_fields": [
                "identity.id",
                "identity.path",
                "identity.content_hash",
                "artifact_kind",
                "surface_state",
                "document_role",
                "mechanics_role",
                "command_role",
                "abi",
                "signs.digest",
                "provenance.source_refs",
                "refs.heading_refs",
            ],
        },
    }
    payload["index_identity"]["content_digest"] = payload_digest(payload)
    return payload


def build_index_incremental(
    repo_root: Path,
    previous_index: dict[str, Any],
    *,
    output: Path | None = None,
    excluded_outputs: Sequence[Path] = (),
    history_ref: str | None = None,
) -> dict[str, Any]:
    return build_index(
        repo_root,
        output=output,
        excluded_outputs=excluded_outputs,
        previous_index=previous_index,
        history_ref=history_ref,
    )


COMMAND_EVENT_KINDS = {
    "builder": "generation_run",
    "lane_entrypoint": "validation_lane_run",
    "script": "command_run",
    "test": "test_run",
    "validator": "validation_run",
}


def event_entry_id(repo: str, source_id: str, event_kind: str, qualifier: str) -> str:
    return qualified_id(repo, "event", f"{source_id}:{event_kind}:{qualifier}")


def event_entries(
    repo: str,
    records: Sequence[dict[str, Any]],
    *,
    repo_root: Path | None = None,
    artifacts: Sequence[dict[str, Any]] = (),
    excluded_paths: set[str] | None = None,
    history_ref: str | None = None,
    event_history_ref: str | None = None,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def append_event(
        record: dict[str, Any],
        *,
        event_kind: str,
        event_role: str,
        observation_state: str,
        qualifier: str = "",
        label: str = "",
        heading_ref: dict[str, Any] | None = None,
    ) -> None:
        identity = record["identity"]
        source_id = str(identity["id"])
        refs = record.get("refs") if isinstance(record.get("refs"), dict) else {}
        anchors = refs.get("anchor_refs") if isinstance(refs, dict) else []
        anchor_ids = [
            str(anchor["id"])
            for anchor in anchors if isinstance(anchor, dict) and anchor.get("anchor_kind") == "artifact"
        ]
        if heading_ref is not None:
            fragment = str(heading_ref.get("anchor") or "")
            heading_anchor = next(
                (
                    anchor
                    for anchor in anchors
                    if isinstance(anchor, dict)
                    and anchor.get("anchor_kind") == "markdown_heading"
                    and isinstance(anchor.get("locator"), dict)
                    and anchor["locator"].get("fragment") == fragment
                ),
                None,
            )
            if isinstance(heading_anchor, dict):
                anchor_ids = [str(heading_anchor["id"])]
        key = (source_id, event_kind, qualifier)
        if key in seen:
            return
        seen.add(key)
        entries.append(
            {
                "id": event_entry_id(repo, source_id, event_kind, qualifier),
                "event_kind": event_kind,
                "event_role": event_role,
                "observation_state": observation_state,
                "label": label or qualifier or str(identity["path"]),
                "source_record_ids": [source_id],
                "anchor_ids": anchor_ids,
                "object_ids": [source_id],
                "changes": [],
                "occurred_at": "",
                "actor": {"name": "source-owner", "email": ""},
                "evidence_refs": [
                    {"kind": "source_anchor", "ref": anchor_id}
                    for anchor_id in anchor_ids
                ],
                "temporal_ref": "current",
                "provenance_ref": "observed" if observation_state == "observed" else "declared",
                "trust_ref": "observed" if observation_state == "observed" else "declared",
            }
        )

    for record in records:
        path = str(record["identity"]["path"])
        if path.startswith(".github/workflows/"):
            append_event(
                record,
                event_kind="workflow_run",
                event_role="producer",
                observation_state="declared",
            )
        command_kind = COMMAND_EVENT_KINDS.get(str(record.get("command_role") or "none"))
        if command_kind:
            append_event(
                record,
                event_kind=command_kind,
                event_role="producer",
                observation_state="declared",
            )
        if record.get("artifact_kind") == "receipt" or "/receipts/" in f"/{path}":
            append_event(
                record,
                event_kind="validation_receipt",
                event_role="receipt",
                observation_state="observed",
            )
        if record.get("document_role") == "decision":
            append_event(
                record,
                event_kind="decision_record",
                event_role="declaration",
                observation_state="declared",
            )
        if record.get("document_role") == "changelog":
            refs = record.get("refs")
            headings = refs.get("heading_refs") if isinstance(refs, dict) else []
            for heading in headings if isinstance(headings, list) else []:
                if not isinstance(heading, dict) or heading.get("level") != 2:
                    continue
                title = str(heading.get("title") or "")
                append_event(
                    record,
                    event_kind=(
                        "release_lane" if "unreleased" in title.lower() else "release_declaration"
                    ),
                    event_role="declaration",
                    observation_state="declared",
                    qualifier=str(heading.get("anchor") or title),
                    label=title,
                    heading_ref=heading,
                )
    if repo_root is not None:
        current_ids = {
            str(record["identity"]["path"]): str(record["identity"]["id"])
            for record in records
        }
        artifact_anchor_ids = {
            str(artifact["id"]): str(artifact["anchor_id"])
            for artifact in artifacts
        }
        entries.extend(
            git_commit_events(
                repo_root,
                repo=repo,
                current_ids=current_ids,
                artifact_anchor_ids=artifact_anchor_ids,
                excluded_paths=excluded_paths,
                history_ref=(
                    event_history_ref
                    if event_history_ref is not None
                    else history_ref
                ),
            )
        )
    return sorted(entries, key=lambda entry: (entry["event_kind"], entry["id"]))


def entry_kind_counts(entries: Sequence[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        value = str(entry.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def repository_index_profiles(entries: Sequence[dict[str, Any]]) -> dict[str, Any]:
    parsers: dict[str, dict[str, str]] = {}
    for entry in entries:
        parser_ref = entry.get("parser_ref")
        if not isinstance(parser_ref, str) or "@" not in parser_ref:
            continue
        name, version = parser_ref.rsplit("@", 1)
        parsers[parser_ref] = {"name": name, "version": version}
    return {
        "extractors": {
            "aoa-repo-local-kag@2": {"name": "aoa-repo-local-kag", "version": "2"}
        },
        "parsers": dict(sorted(parsers.items())),
        "provenance": {
            mode: {"mode": mode, "extractor_ref": "aoa-repo-local-kag@2"}
            for mode in ("declared", "deterministic", "inferred", "observed")
        },
        "temporal": {
            "current": {"state": "current", "valid_from": "", "valid_to": ""},
            "historical": {"state": "historical", "valid_from": "", "valid_to": ""},
        },
        "trust": {
            "declared": {"class": "declared", "confidence": 0.75},
            "deterministic": {"class": "deterministic", "confidence": 1.0},
            "inferred": {"class": "inferred", "confidence": 0.5},
            "observed": {"class": "observed", "confidence": 1.0},
        },
    }


def repository_index_payload(
    source_index: dict[str, Any],
    *,
    index_kind: str,
    entries: list[dict[str, Any]],
    source_index_path: Path,
) -> dict[str, Any]:
    kind_field = f"{index_kind}_kind"
    local_id_suffix = {
        "entity": "entities",
        "anchor": "anchors",
        "relation": "relations",
    }.get(index_kind, f"{index_kind}s")
    stable_fields = {
        "entity": [
            "id",
            "entity_kind",
            "semantic_key",
            "source_record_ids",
            "anchor_ids",
            "provenance_ref",
            "temporal_ref",
            "trust_ref",
        ],
        "artifact": [
            "id",
            "version_id",
            "artifact_kind",
            "anchor_id",
            "path",
            "content_hash",
            "provenance_ref",
            "temporal_ref",
            "trust_ref",
        ],
        "anchor": [
            "id",
            "anchor_kind",
            "source_record_id",
            "locator",
            "parser_ref",
            "provenance_ref",
            "temporal_ref",
            "trust_ref",
        ],
        "event": [
            "id",
            "event_kind",
            "event_role",
            "source_record_ids",
            "anchor_ids",
            "object_ids",
            "occurred_at",
            "provenance_ref",
            "temporal_ref",
            "trust_ref",
        ],
        "assertion": [
            "id",
            "assertion_kind",
            "subject_id",
            "predicate",
            "object",
            "source_record_ids",
            "evidence_anchor_ids",
            "evidence_class",
            "confidence",
            "quality_state",
            "provenance_ref",
            "temporal_ref",
            "trust_ref",
        ],
        "relation": [
            "id",
            "relation_kind",
            "from_id",
            "to_id",
            "evidence_anchor_ids",
            "evidence_class",
            "provenance_ref",
            "temporal_ref",
            "trust_ref",
        ],
    }[index_kind]
    payload: dict[str, Any] = {
        "schema_version": REPOSITORY_INDEX_SCHEMA_VERSION,
        "repo": copy.deepcopy(source_index["repo"]),
        "index_identity": {
            "local_id": f"index:repo-local:{local_id_suffix}",
            "index_kind": index_kind,
            "artifact_kind": f"repository_{index_kind}_index",
            "content_digest": ZERO_DIGEST,
            "schema_ref": REPOSITORY_INDEX_SCHEMA_REF,
        },
        "source_index": {
            "path": source_index_path.as_posix(),
            "local_id": source_index["index_identity"]["local_id"],
            "content_digest": source_index["index_identity"]["content_digest"],
        },
        "summary": {
            "entry_count": len(entries),
            "kind_counts": entry_kind_counts(entries, kind_field),
        },
        "profiles": repository_index_profiles(entries),
        "entries": entries,
        "registry_output": {
            "consumer": "aoa-kag",
            "resource_shape": f"repo-local-{index_kind}-index",
            "stable_fields": stable_fields,
        },
    }
    payload["index_identity"]["content_digest"] = payload_digest(payload)
    return payload


def previous_structure_refs(
    source_index: dict[str, Any],
    previous_family: dict[str, dict[str, Any]] | None,
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    if not previous_family or set(previous_family) != set(REPOSITORY_INDEX_FILENAMES):
        return {}
    if any(
        payload.get("schema_version") != REPOSITORY_INDEX_SCHEMA_VERSION
        or payload.get("profiles", {}).get("extractors", {}).get("aoa-repo-local-kag@2")
        != {"name": "aoa-repo-local-kag", "version": "2"}
        for payload in previous_family.values()
    ):
        return {}
    previous_hashes = {
        str(entry["id"]): str(entry["content_hash"])
        for entry in previous_family["artifact"].get("entries", [])
        if isinstance(entry, dict)
    }
    anchors_by_source: dict[str, list[dict[str, Any]]] = {}
    for anchor in previous_family["anchor"].get("entries", []):
        if isinstance(anchor, dict):
            anchors_by_source.setdefault(str(anchor["source_record_id"]), []).append(anchor)

    reusable: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for record in source_index["records"]:
        identity = record["identity"]
        source_id = str(identity["id"])
        previous_anchors = anchors_by_source.get(source_id)
        if (
            previous_hashes.get(source_id) != str(identity["content_hash"])
            or not previous_anchors
        ):
            continue
        raw_anchors: list[dict[str, Any]] = []
        outbound_refs: list[dict[str, Any]] = []
        for normalized_anchor in previous_anchors:
            raw_anchor = copy.deepcopy(normalized_anchor)
            parser_ref = str(raw_anchor.pop("parser_ref"))
            parser_name, parser_version = parser_ref.rsplit("@", 1)
            raw_anchor["parser"] = {"name": parser_name, "version": parser_version}
            raw_anchor.pop("source_record_id", None)
            raw_anchor.pop("evidence_class", None)
            raw_anchor.pop("provenance_ref", None)
            raw_anchor.pop("temporal_ref", None)
            raw_anchor.pop("trust_ref", None)
            for reference in raw_anchor.pop("outbound_refs", []):
                outbound_refs.append(
                    {**copy.deepcopy(reference), "source_anchor_id": str(raw_anchor["id"])}
                )
            raw_anchors.append(raw_anchor)
        reusable[source_id] = {
            "anchor_refs": raw_anchors,
            "outbound_refs": outbound_refs,
        }
    return reusable


def build_repository_indexes(
    source_index: dict[str, Any],
    *,
    source_index_path: Path = DEFAULT_OUTPUT,
    repo_root: Path | None = None,
    previous_family: dict[str, dict[str, Any]] | None = None,
    history_ref: str | None = None,
    event_history_ref: str | None = None,
) -> dict[str, dict[str, Any]]:
    if repo_root is not None:
        resolved_root = repo_root.resolve()
        history_ref = effective_history_ref(resolved_root, history_ref)
        event_history_ref = effective_event_history_ref(
            resolved_root,
            event_history_ref,
            fallback=history_ref,
        )
    effective_event_ref = (
        event_history_ref if event_history_ref is not None else history_ref
    )
    records = [copy.deepcopy(record) for record in source_index["records"] if isinstance(record, dict)]
    repo = str(source_index["repo"]["name"])
    reusable_structure = previous_structure_refs(source_index, previous_family)
    for record in records:
        identity = record["identity"]
        source_id = str(identity["id"])
        if source_id in reusable_structure:
            refs = record["refs"]
            refs.update(copy.deepcopy(reusable_structure[source_id]))
            continue
        rel = Path(str(identity["path"]))
        content = b""
        if repo_root is not None:
            resolved_root = repo_root.resolve()
            content = source_bytes(resolved_root, rel, resolved_root / rel)
        structure = extract_structure(
            repo=repo,
            source_id=source_id,
            path=rel.as_posix(),
            mime=str(identity["mime"]),
            content=content,
        )
        refs = record["refs"]
        refs["anchor_refs"] = structure["anchor_refs"]
        refs["outbound_refs"] = structure["outbound_refs"]
    artifacts = project_artifact_entries(records)
    anchors = project_anchor_entries(records)
    entities = project_entity_entries(repo, records)
    family_paths = {
        source_index_path.as_posix(),
        PORTABLE_FAMILY_MANIFEST.as_posix(),
        PORTABLE_FAMILY_SHARD_ROOT.as_posix() + "/",
        PORTABLE_FAMILY_BUDGET_RECEIPT_ROOT.as_posix() + "/",
        *(
            (source_index_path.parent / filename).as_posix()
            for filename in REPOSITORY_INDEX_FILENAMES.values()
        ),
    }
    events = event_entries(
        repo,
        records,
        repo_root=repo_root,
        artifacts=artifacts,
        excluded_paths=family_paths,
        history_ref=history_ref,
        event_history_ref=effective_event_ref,
    )
    assertions = project_assertion_entries(
        repo,
        records,
        artifacts=artifacts,
    )
    relations = project_relation_entries(
        repo,
        records,
        artifacts=artifacts,
        anchors=anchors,
        entities=entities,
    )
    return {
        "entity": repository_index_payload(
            source_index,
            index_kind="entity",
            entries=entities,
            source_index_path=source_index_path,
        ),
        "artifact": repository_index_payload(
            source_index,
            index_kind="artifact",
            entries=artifacts,
            source_index_path=source_index_path,
        ),
        "anchor": repository_index_payload(
            source_index,
            index_kind="anchor",
            entries=anchors,
            source_index_path=source_index_path,
        ),
        "event": repository_index_payload(
            source_index,
            index_kind="event",
            entries=events,
            source_index_path=source_index_path,
        ),
        "assertion": repository_index_payload(
            source_index,
            index_kind="assertion",
            entries=assertions,
            source_index_path=source_index_path,
        ),
        "relation": repository_index_payload(
            source_index,
            index_kind="relation",
            entries=relations,
            source_index_path=source_index_path,
        ),
    }


def build_repository_indexes_incremental(
    source_index: dict[str, Any],
    previous_family: dict[str, dict[str, Any]],
    *,
    source_index_path: Path = DEFAULT_OUTPUT,
    repo_root: Path | None = None,
    history_ref: str | None = None,
    event_history_ref: str | None = None,
) -> dict[str, dict[str, Any]]:
    return build_repository_indexes(
        source_index,
        source_index_path=source_index_path,
        repo_root=repo_root,
        previous_family=previous_family,
        history_ref=history_ref,
        event_history_ref=event_history_ref,
    )


def repository_index_output_paths(output_path: Path) -> dict[str, Path]:
    return {
        index_kind: output_path.parent / filename
        for index_kind, filename in REPOSITORY_INDEX_FILENAMES.items()
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(normalized_json(payload), encoding="utf-8")


def normalized_json(payload: Any) -> str:
    if not isinstance(payload, dict):
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    collection_key = next(
        (
            key
            for key in ("records", "entries")
            if isinstance(payload.get(key), list)
        ),
        "",
    )
    if not collection_key:
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    lines = ["{"]
    keys = sorted(payload)
    for key_index, key in enumerate(keys):
        trailing = "," if key_index < len(keys) - 1 else ""
        encoded_key = json.dumps(key, ensure_ascii=False)
        if key == collection_key:
            lines.append(f"  {encoded_key}: [")
            items = payload[key]
            for item_index, item in enumerate(items):
                item_trailing = "," if item_index < len(items) - 1 else ""
                compact = json.dumps(
                    item,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                lines.append(f"    {compact}{item_trailing}")
            lines.append(f"  ]{trailing}")
            continue
        rendered = json.dumps(
            payload[key],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ).splitlines()
        block = [f"  {encoded_key}: {rendered[0]}"]
        block.extend(f"  {line}" for line in rendered[1:])
        block[-1] += trailing
        lines.extend(block)
    lines.append("}")
    return "\n".join(lines) + "\n"


def check_output(path: Path, payload: Any) -> bool:
    if not path.exists():
        print(f"[repo-local-kag-index] missing {path}", file=sys.stderr)
        return False
    current = path.read_text(encoding="utf-8")
    expected = normalized_json(payload)
    if current != expected:
        print(f"[repo-local-kag-index] drift in {path}", file=sys.stderr)
        return False
    return True


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a repo-local KAG source surface index.")
    parser.add_argument("--repo-root", default=".", help="Repository root to index.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT.as_posix(), help="Index output path relative to repo root.")
    parser.add_argument(
        "--index-family",
        action="store_true",
        help="Generate or check the source, artifact, anchor, entity, event, assertion, and relation index family.",
    )
    parser.add_argument(
        "--portable-family",
        action="store_true",
        help=(
            "Generate or check the content-addressed portable v3 record corpus "
            "and its deterministic v2 compatibility contract."
        ),
    )
    parser.add_argument(
        "--keep-v2",
        action="store_true",
        help="Keep legacy v2 monoliths while writing a portable family.",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Reuse unchanged source records from the current source index while preserving full-build parity.",
    )
    parser.add_argument(
        "--history-ref",
        help="Git ref whose lineage should back current source records.",
    )
    parser.add_argument(
        "--event-history-ref",
        help="Git ref whose history precedes the current repository snapshot.",
    )
    parser.add_argument(
        "--budget-base-ref",
        help="Git ref used to enforce the changed-generated-bytes budget.",
    )
    parser.add_argument(
        "--write-budget-receipt",
        action="store_true",
        help="Write an explicit receipt for a generated-delta budget exceedance.",
    )
    parser.add_argument(
        "--budget-reason",
        default="",
        help="Owner reason recorded by --write-budget-receipt.",
    )
    parser.add_argument("--check", action="store_true", help="Check output parity without writing.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.index_family and args.portable_family:
        raise SystemExit("--index-family and --portable-family are mutually exclusive")
    if args.keep_v2 and not args.portable_family:
        raise SystemExit("--keep-v2 requires --portable-family")
    if args.write_budget_receipt and (
        not args.portable_family
        or args.check
        or not args.budget_base_ref
        or not args.budget_reason.strip()
    ):
        raise SystemExit(
            "--write-budget-receipt requires a write-mode --portable-family run "
            "with --budget-base-ref and --budget-reason"
        )
    repo_root = Path(args.repo_root).resolve()
    output = Path(args.output)
    output_path = repo_root / output
    history_ref = effective_history_ref(repo_root, args.history_ref)
    event_history_ref = effective_event_history_ref(
        repo_root,
        args.event_history_ref,
        fallback=history_ref,
    )
    family_paths = repository_index_output_paths(output_path)
    previous_index: dict[str, Any] | None = None
    previous_family: dict[str, dict[str, Any]] | None = None
    previous_manifest: dict[str, Any] | None = None
    portable_manifest_path = repo_root / PORTABLE_FAMILY_MANIFEST
    if args.portable_family and portable_manifest_path.is_file():
        try:
            loaded_manifest = json.loads(
                portable_manifest_path.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, UnicodeDecodeError):
            loaded_manifest = None
        if not isinstance(loaded_manifest, dict):
            raise SystemExit(
                f"invalid portable family manifest: {portable_manifest_path}"
            )
        previous_manifest = loaded_manifest
    if args.incremental and args.portable_family and previous_manifest is not None:
        try:
            from scripts.repo_local.portable_family import load_portable_family
        except ImportError:  # pragma: no cover - direct script execution
            from repo_local.portable_family import load_portable_family  # type: ignore
        try:
            previous_index, previous_family, _ = load_portable_family(repo_root)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    elif args.incremental and output_path.is_file():
        try:
            loaded_previous = json.loads(output_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            loaded_previous = None
        if isinstance(loaded_previous, dict):
            previous_index = loaded_previous
        if (
            (args.index_family or args.portable_family)
            and all(path.is_file() for path in family_paths.values())
        ):
            loaded_family: dict[str, dict[str, Any]] = {}
            try:
                for index_kind, path in family_paths.items():
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    if not isinstance(payload, dict):
                        raise ValueError(path)
                    loaded_family[index_kind] = payload
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
                loaded_family = {}
            if set(loaded_family) == set(REPOSITORY_INDEX_FILENAMES):
                previous_family = loaded_family
    payload = build_index(
        repo_root,
        output=output,
        excluded_outputs=(
            tuple(family_paths.values())
            if args.index_family or args.portable_family
            else ()
        ),
        previous_index=previous_index,
        history_ref=history_ref,
    )
    if args.index_family or args.portable_family:
        try:
            source_index_path = output_path.resolve().relative_to(repo_root)
        except ValueError as exc:
            raise SystemExit("--index-family output must stay inside --repo-root") from exc
        family = build_repository_indexes(
            payload,
            source_index_path=source_index_path,
            repo_root=repo_root,
            previous_family=previous_family,
            history_ref=history_ref,
            event_history_ref=event_history_ref,
        )
    else:
        family = {}
    if args.portable_family:
        try:
            from scripts.repo_local.portable_family import (
                PortableFamilyError,
                build_budget_receipt,
                build_portable_family,
                check_portable_output,
                validate_changed_generated_budget,
                write_budget_receipt,
                write_portable_output,
            )
        except ImportError:  # pragma: no cover - direct script execution
            from repo_local.portable_family import (  # type: ignore
                PortableFamilyError,
                build_budget_receipt,
                build_portable_family,
                check_portable_output,
                validate_changed_generated_budget,
                write_budget_receipt,
                write_portable_output,
            )
        try:
            portable_manifest, portable_shards = build_portable_family(
                payload,
                family,
                previous_manifest=previous_manifest,
            )
        except PortableFamilyError as exc:
            print(f"[repo-local-kag-index] {exc}", file=sys.stderr)
            return 1
        if args.check:
            ok = check_portable_output(
                repo_root,
                portable_manifest,
                portable_shards,
                require_legacy_absent=not args.keep_v2,
            )
            if not ok:
                print(
                    "[repo-local-kag-index] portable family drifted",
                    file=sys.stderr,
                )
            if args.budget_base_ref:
                try:
                    changed_bytes, changed_files, receipted = (
                        validate_changed_generated_budget(
                            repo_root,
                            base_ref=args.budget_base_ref,
                            manifest=portable_manifest,
                        )
                    )
                except (PortableFamilyError, subprocess.CalledProcessError) as exc:
                    print(f"[repo-local-kag-index] {exc}", file=sys.stderr)
                    return 1
                receipt_label = " receipt=accepted" if receipted else ""
                print(
                    "[repo-local-kag-index] generated delta "
                    f"bytes={changed_bytes} files={changed_files}{receipt_label}"
                )
            return 0 if ok else 1
        write_portable_output(
            repo_root,
            portable_manifest,
            portable_shards,
            remove_legacy=not args.keep_v2,
        )
        if args.write_budget_receipt:
            try:
                receipt_path, receipt = build_budget_receipt(
                    repo_root,
                    base_ref=args.budget_base_ref,
                    manifest=portable_manifest,
                    reason=args.budget_reason,
                )
            except (PortableFamilyError, subprocess.CalledProcessError) as exc:
                print(f"[repo-local-kag-index] {exc}", file=sys.stderr)
                return 1
            write_budget_receipt(repo_root, receipt_path, receipt)
            print(f"[repo-local-kag-index] wrote {repo_root / receipt_path}")
        if args.budget_base_ref:
            try:
                changed_bytes, changed_files, receipted = (
                    validate_changed_generated_budget(
                        repo_root,
                        base_ref=args.budget_base_ref,
                        manifest=portable_manifest,
                    )
                )
            except (PortableFamilyError, subprocess.CalledProcessError) as exc:
                print(f"[repo-local-kag-index] {exc}", file=sys.stderr)
                return 1
            receipt_label = " receipt=accepted" if receipted else ""
            print(
                "[repo-local-kag-index] generated delta "
                f"bytes={changed_bytes} files={changed_files}{receipt_label}"
            )
        print(
            "[repo-local-kag-index] wrote portable family "
            f"{portable_manifest_path} "
            f"shards={portable_manifest['summary']['shards']} "
            f"bytes={portable_manifest['summary']['tracked_bytes']}"
        )
        return 0
    if args.check:
        ok = check_output(output_path, payload)
        if args.index_family:
            for index_kind, family_payload in family.items():
                ok = check_output(family_paths[index_kind], family_payload) and ok
        return 0 if ok else 1
    write_json(output_path, payload)
    for index_kind, family_payload in family.items():
        write_json(family_paths[index_kind], family_payload)
    print(f"[repo-local-kag-index] wrote {output_path}")
    if args.index_family:
        print(
            "[repo-local-kag-index] wrote "
            + ", ".join(path.as_posix() for path in family_paths.values())
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
