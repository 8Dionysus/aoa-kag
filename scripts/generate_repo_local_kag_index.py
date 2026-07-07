#!/usr/bin/env python3
"""Generate a repo-local KAG source surface index."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import mimetypes
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("kag/indexes/source_surface_index.json")
CANONICAL_SELF_INDEX = DEFAULT_OUTPUT
INDEX_SCHEMA_REF = "aoa-kag:schemas/repo-local-kag-index.schema.json"
INDEX_SCHEMA_VERSION = "aoa-repo-local-kag-index-v1"
GIT_INDEX_SOURCE_REF = "git-index-source-tree"
FILESYSTEM_SOURCE_REF = "filesystem-source-tree"
LOCAL_INDEX_GENERATOR_ROUTE = "scripts/generate_repo_local_kag_index.py"
EXTERNAL_INDEX_GENERATOR_ROUTE = f"aoa-kag:{LOCAL_INDEX_GENERATOR_ROUTE}"
LOCAL_KAG_VALIDATOR_ROUTE = "scripts/validate_kag.py"
EXTERNAL_KAG_VALIDATOR_ROUTE = f"aoa-kag:{LOCAL_KAG_VALIDATOR_ROUTE}"
ZERO_DIGEST = "0" * 64

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
MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
SECRET_HINTS = ("secret", "token", "credential", "private-key", "password")
LANE_ENTRYPOINTS = {"ci_gate.py", "release_check.py", "run_tests.py"}
COMMAND_SUFFIXES = {".py", ".sh", ".ps1"}
COMMAND_PREFIXES = ("build_", "generate_", "run_", "start_", "sync_", "validate_")
BUILDER_PREFIXES = ("build_", "generate_")
ASSET_SUFFIXES = {".gif", ".ico", ".jpg", ".jpeg", ".png", ".svg", ".webp"}
ARCHIVE_SUFFIXES = {".7z", ".gz", ".tar", ".tgz", ".xz", ".zip"}
SPREADSHEET_SUFFIXES = {".ods", ".xls", ".xlsx"}
DATA_TABLE_SUFFIXES = {".csv", ".tsv"}
TEXT_ARTIFACT_SUFFIXES = {".txt"}
HTML_SUFFIXES = {".htm", ".html"}
SERVICE_UNIT_SUFFIXES = {".path", ".service", ".socket", ".timer"}
OWNER_METADATA_NAMES = {".gitattributes", ".gitignore", "CODEOWNERS", "AOA_WORKSPACE_ROOT"}
DIRECTORY_MARKER_NAMES = {".gitkeep", ".keep"}
ENV_CONFIG_NAMES = {".env", ".env.example", ".env.sample", ".env.template"}


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


def owner_type_for(name: str, repo_root: Path) -> str:
    parts = set(repo_root.parts)
    if name == "Agents-of-Abyss":
        return "center"
    if "connectors" in parts or name.endswith("-connector"):
        return "connector"
    if "bundles" in parts or name == "aoa-session-memory":
        return "bundle_provider"
    if name in {"abyss-machine", "abyss-stack"} and str(repo_root).startswith("/home/"):
        return "runtime_source"
    if name == "abyss-stack":
        return "runtime_mirror"
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


def git_file_paths(repo_root: Path) -> list[Path]:
    try:
        raw = subprocess.run(
            ("git", "ls-files", "-z", "--cached"),
            cwd=repo_root,
            check=True,
            capture_output=True,
        ).stdout
        paths = [Path(item.decode()) for item in raw.split(b"\0") if item]
    except (subprocess.CalledProcessError, FileNotFoundError):
        paths = [path.relative_to(repo_root) for path in repo_root.rglob("*") if path.is_file()]
    return sorted(path for path in paths if is_source_path(path))


def source_bytes(repo_root: Path, rel: Path, path: Path) -> bytes:
    try:
        return subprocess.run(
            ("git", "show", f":{rel.as_posix()}"),
            cwd=repo_root,
            check=True,
            capture_output=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
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


def markdown_anchor(text: str) -> str:
    anchor = text.strip().lower()
    anchor = re.sub(r"[^\w\s-]", "", anchor)
    anchor = re.sub(r"\s+", "-", anchor)
    anchor = re.sub(r"-+", "-", anchor)
    return anchor.strip("-")


def heading_refs(content: bytes, rel_path: str) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    try:
        lines = content.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return refs
    for line_number, line in enumerate(lines, start=1):
        match = MARKDOWN_HEADING.match(line)
        if not match:
            continue
        title = match.group(2).strip()
        base = markdown_anchor(title)
        if not base:
            continue
        suffix = seen.get(base, 0)
        seen[base] = suffix + 1
        anchor = base if suffix == 0 else f"{base}-{suffix}"
        refs.append(
            {
                "level": len(match.group(1)),
                "title": title,
                "anchor": anchor,
                "line": line_number,
                "ref": f"{rel_path}#{anchor}",
            }
        )
    return refs


def mime_for(path: Path) -> str:
    if path.suffix == ".md":
        return "text/markdown"
    if path.suffix == ".py":
        return "text/x-python"
    if path.suffix in {".yaml", ".yml"}:
        return "application/yaml"
    guessed, _ = mimetypes.guess_type(path.as_posix())
    return guessed or "application/octet-stream"


def path_id(rel_path: str) -> str:
    value = rel_path.lower()
    value = re.sub(r"[^a-z0-9_.:/#-]", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    suffix = hashlib.sha256(rel_path.encode("utf-8")).hexdigest()[:10]
    return f"file:{value}:{suffix}"


def document_role(rel: Path) -> str:
    name = rel.name
    parts = rel.parts
    if rel.suffix != ".md":
        return "none"
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


def artifact_kind(rel: Path) -> str:
    parts = rel.parts
    name = rel.name
    suffix = rel.suffix
    if name in {"LICENSE", "COPYING"}:
        return "license"
    if name in OWNER_METADATA_NAMES or (len(parts) >= 2 and parts[0] == ".github" and name == "CODEOWNERS"):
        return "owner_metadata"
    if name in DIRECTORY_MARKER_NAMES:
        return "directory_marker"
    if name in ENV_CONFIG_NAMES:
        return "config"
    if name.startswith("requirements") and suffix == ".txt":
        return "dependency_manifest"
    if "receipts" in parts:
        return "receipt"
    if suffix in ASSET_SUFFIXES:
        return "asset"
    if suffix in DATA_TABLE_SUFFIXES:
        return "data_table"
    if suffix in {".jsonl", ".ndjson"}:
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
    if is_command_entrypoint(rel) and name.startswith("validate_"):
        return "validator"
    if is_command_entrypoint(rel):
        return "script"
    if "mechanics" in parts:
        return "mechanics_surface"
    if suffix in {".py", ".js", ".ts", ".sh", ".ps1"}:
        return "source_code"
    if suffix in TEXT_ARTIFACT_SUFFIXES:
        return "text_artifact"
    return "unknown"


def is_command_entrypoint(rel: Path) -> bool:
    if len(rel.parts) >= 2 and rel.parts[0] == ".codex" and rel.parts[1] == "bin":
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


def code_role(rel: Path, kind: str) -> str:
    if rel.suffix not in {".py", ".js", ".ts", ".sh", ".ps1"} and kind != "script":
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
    if kind == "validator" and is_command_entrypoint(rel):
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
) -> str:
    parts = rel.parts
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


def observed_form(kind: str, command: str) -> str:
    if command != "none":
        return "command"
    if kind == "generated_readmodel":
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
        "text_artifact",
    }:
        return "artifact"
    if kind == "unknown":
        return "unknown"
    return "surface"


def source_authority(state: str) -> str:
    if state == "generated_readmodel":
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


def generated_by_for(
    rel: Path,
    state: str,
    tracked_paths: set[Path],
    content: bytes,
    *,
    repo_root: Path,
) -> str:
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
        return "scripts/generate_decision_indexes.py"
    part_local_builder = part_local_generated_by_for(rel, tracked_paths)
    if part_local_builder:
        return part_local_builder
    if rel_path.startswith("generated/") or "/generated/" in rel_path:
        return "scripts/generate_kag.py"
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
    compatibility = "generated" if state == "generated_readmodel" else "stable"
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
) -> dict[str, Any]:
    rel_path = rel.as_posix()
    content = source_bytes(repo_root, rel, path)
    digest = sha256_bytes(content)
    declared_generated = declares_generated_from_source(content)
    kind = artifact_kind(rel)
    doc_role = document_role(rel)
    code = code_role(rel, kind)
    mech = mechanics_role(rel)
    command = command_role(rel, kind, doc_role)
    state = surface_state(rel, kind, repo=repo, declared_generated=declared_generated)
    headings = heading_refs(content, rel_path) if doc_role != "none" else []
    line_refs = [f"{rel_path}:1"] if content else []
    authority = source_authority(state)
    provenance_source_ref = {"repo": repo, "path": rel_path, "role": "primary", "authority": authority}
    generated_by = generated_by_for(rel, state, tracked_paths, content, repo_root=repo_root)
    observed_by = index_generator_route(repo)
    validated_by = kag_validator_route(repo_root, repo, tracked_paths)
    required_tools = []
    if rel.suffix == ".py":
        required_tools.append("python")
    if command != "none" and rel.suffix == ".ps1":
        required_tools.append("pwsh")
    if command != "none" and rel.suffix == ".sh":
        required_tools.append("bash")
    if rel.suffix in {".json", ".yaml", ".yml"}:
        required_tools.append("jq")
    return {
        "identity": {
            "id": path_id(rel_path),
            "repo": repo,
            "path": rel_path,
            "git_ref": snapshot_ref,
            "content_hash": digest,
            "size_bytes": len(content),
            "mime": mime_for(path),
        },
        "observed_form": observed_form(kind, command),
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
            "validated_by": [validated_by],
            "source_refs": [provenance_source_ref],
            "materials": [],
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
        "refs": {"path_ref": rel_path, "line_refs": line_refs, "heading_refs": headings},
        "owner_return_route": {"surface": rel_path, "route_kind": route_kind_for(kind, doc_role, command)},
        "validator_route": {"surface": validated_by, "route_kind": "source_fast"},
        "consumer_route": {"surface": "aoa-kag-mcp", "route_kind": "resource"},
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


def build_index(repo_root: Path, *, output: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    name = repo_name(repo_root)
    snapshot_ref = source_snapshot_ref(repo_root)
    excluded_paths = {CANONICAL_SELF_INDEX}
    if output is not None:
        output_path = output if output.is_absolute() else repo_root / output
        try:
            excluded_paths.add(output_path.resolve().relative_to(repo_root))
        except ValueError:
            if not output.is_absolute():
                excluded_paths.add(output)
    tracked_paths = set(git_file_paths(repo_root))
    records = []
    for rel in sorted(tracked_paths):
        if rel in excluded_paths:
            continue
        path = repo_root / rel
        if snapshot_ref == GIT_INDEX_SOURCE_REF or path.is_file():
            records.append(
                build_record(
                    path,
                    rel,
                    repo_root=repo_root,
                    repo=name,
                    snapshot_ref=snapshot_ref,
                    tracked_paths=tracked_paths,
                )
            )
    records.sort(key=lambda record: record["identity"]["path"])
    payload: dict[str, Any] = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "repo": {
            "name": name,
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
            "consumer": "aoa-kag-mcp",
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalized_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


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
    parser.add_argument("--check", action="store_true", help="Check output parity without writing.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    output = Path(args.output)
    payload = build_index(repo_root, output=output)
    output_path = repo_root / output
    if args.check:
        return 0 if check_output(output_path, payload) else 1
    write_json(output_path, payload)
    print(f"[repo-local-kag-index] wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
