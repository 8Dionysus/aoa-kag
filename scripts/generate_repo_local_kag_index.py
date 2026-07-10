#!/usr/bin/env python3
"""Generate a repo-local KAG source surface index."""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("kag/indexes/source_surface_index.json")
CANONICAL_SELF_INDEX = DEFAULT_OUTPUT
REPOSITORY_INDEX_FILENAMES = {
    "entity": "repo_entity_index.json",
    "artifact": "repo_artifact_index.json",
    "event": "repo_event_index.json",
}
CANONICAL_REPOSITORY_INDEX_PATHS = {
    DEFAULT_OUTPUT.parent / filename for filename in REPOSITORY_INDEX_FILENAMES.values()
}
INDEX_SCHEMA_REF = "aoa-kag:schemas/repo-local-kag-index.schema.json"
INDEX_SCHEMA_VERSION = "aoa-repo-local-kag-index-v1"
REPOSITORY_INDEX_SCHEMA_REF = (
    "aoa-kag:schemas/repo-local-kag-repository-index.schema.json"
)
REPOSITORY_INDEX_SCHEMA_VERSION = "aoa-repo-local-kag-repository-index-v1"
GIT_INDEX_SOURCE_REF = "git-index-source-tree"
FILESYSTEM_SOURCE_REF = "filesystem-source-tree"
LOCAL_INDEX_GENERATOR_ROUTE = "scripts/generate_repo_local_kag_index.py"
PORTABLE_MIME_BY_SUFFIX = {
    ".7z": "application/x-7z-compressed",
    ".cfg": "text/plain",
    ".csv": "text/csv",
    ".example": "text/plain",
    ".gif": "image/gif",
    ".gz": "application/gzip",
    ".htm": "text/html",
    ".html": "text/html",
    ".ico": "image/vnd.microsoft.icon",
    ".ini": "text/plain",
    ".js": "text/javascript",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".json": "application/json",
    ".jsonl": "application/x-ndjson",
    ".md": "text/markdown",
    ".ndjson": "application/x-ndjson",
    ".ods": "application/vnd.oasis.opendocument.spreadsheet",
    ".path": "text/plain",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".ps1": "text/plain",
    ".py": "text/x-python",
    ".service": "text/plain",
    ".sh": "application/x-sh",
    ".snapshot": "text/plain",
    ".socket": "text/plain",
    ".svg": "image/svg+xml",
    ".tar": "application/x-tar",
    ".tgz": "application/x-tar",
    ".timer": "text/plain",
    ".toml": "application/toml",
    ".ts": "application/typescript",
    ".tsv": "text/tab-separated-values",
    ".txt": "text/plain",
    ".webp": "image/webp",
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
OUTPUT_REFERENCE_LITERAL = re.compile(
    rb"\b(?:emit|emitted|export|exported|publish|published|render|rendered|"
    rb"save|saved|write|writes|writing|wrote)\b",
    re.IGNORECASE,
)
SECRET_HINTS = ("secret", "token", "credential", "private-key", "password")
LANE_ENTRYPOINTS = {"ci_gate.py", "release_check.py", "run_tests.py"}
COMMAND_SUFFIXES = {".py", ".sh", ".ps1"}
SOURCE_CODE_SUFFIXES = {".js", ".ps1", ".py", ".sh", ".ts"}
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
PORTABLE_TEXT_BASENAMES = (
    OWNER_METADATA_NAMES | DIRECTORY_MARKER_NAMES | ENV_CONFIG_NAMES | {"LICENSE"}
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


def mime_for(path: Path, content: bytes = b"") -> str:
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
    if is_command_entrypoint(rel) and name.startswith("validate_"):
        return "validator"
    if is_command_entrypoint(rel):
        return "script"
    if "mechanics" in parts:
        return "mechanics_surface"
    if suffix in SOURCE_CODE_SUFFIXES:
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
    if rel.suffix not in SOURCE_CODE_SUFFIXES and kind != "script":
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
    source_builders: tuple[tuple[Path, bytes], ...],
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
            "mime": mime_for(path, content),
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


def build_index(
    repo_root: Path,
    *,
    output: Path | None = None,
    excluded_outputs: Sequence[Path] = (),
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
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
    tracked_paths = set(git_file_paths(repo_root))
    source_builders = source_builder_contents(repo_root, tracked_paths)
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
                    source_builders=source_builders,
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


def entity_kind_for(record: dict[str, Any]) -> str:
    mechanics = str(record.get("mechanics_role") or "none")
    if mechanics == "mechanic_package":
        return "mechanic_package"
    if mechanics != "none":
        return "mechanic_part"
    command = str(record.get("command_role") or "none")
    if command != "none":
        return "command"
    artifact = str(record.get("artifact_kind") or "unknown")
    document = str(record.get("document_role") or "none")
    if artifact == "schema":
        return "contract"
    if document == "decision":
        return "decision"
    if document == "agents":
        return "agent_route"
    if artifact == "manifest":
        return "manifest"
    if record.get("surface_state") == "generated_readmodel":
        return "readmodel"
    if document != "none":
        return "document"
    if record.get("code_role") != "none":
        return "code"
    if artifact == "owner_metadata":
        return "owner_surface"
    return "artifact"


def entity_entries(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    entries = []
    for record in records:
        identity = record["identity"]
        source_id = str(identity["id"])
        entries.append(
            {
                "id": f"entity:{source_id}",
                "entity_kind": entity_kind_for(record),
                "label": str(identity["path"]),
                "source_record_id": source_id,
                "coordinates": {
                    "artifact_kind": str(record.get("artifact_kind") or "unknown"),
                    "document_role": str(record.get("document_role") or "none"),
                    "mechanics_role": str(record.get("mechanics_role") or "none"),
                    "command_role": str(record.get("command_role") or "none"),
                    "code_role": str(record.get("code_role") or "none"),
                    "surface_state": str(record.get("surface_state") or "authored_source"),
                },
            }
        )
    return entries


def artifact_entries(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    entries = []
    for record in records:
        identity = record["identity"]
        source_id = str(identity["id"])
        entries.append(
            {
                "id": f"artifact:{source_id}",
                "artifact_kind": str(record.get("artifact_kind") or "unknown"),
                "surface_state": str(record.get("surface_state") or "authored_source"),
                "source_record_id": source_id,
                "path": str(identity["path"]),
                "content_hash": str(identity["content_hash"]),
            }
        )
    return entries


COMMAND_EVENT_KINDS = {
    "builder": "generation_run",
    "lane_entrypoint": "validation_lane_run",
    "script": "command_run",
    "test": "test_run",
    "validator": "validation_run",
}


def event_entry_id(repo: str, source_id: str, event_kind: str, qualifier: str) -> str:
    key = f"{repo}\0{source_id}\0{event_kind}\0{qualifier}".encode("utf-8")
    return f"event:repo:{hashlib.sha256(key).hexdigest()[:20]}"


def event_entries(repo: str, records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def append_event(
        record: dict[str, Any],
        *,
        event_kind: str,
        event_role: str,
        observation_state: str,
        qualifier: str = "",
        heading_ref: dict[str, Any] | None = None,
    ) -> None:
        identity = record["identity"]
        source_id = str(identity["id"])
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
                "source_record_id": source_id,
                "path": str(identity["path"]),
                "heading_ref": copy.deepcopy(heading_ref),
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
                    heading_ref=heading,
                )
    return sorted(entries, key=lambda entry: (entry["path"], entry["event_kind"], entry["id"]))


def entry_kind_counts(entries: Sequence[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        value = str(entry.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def repository_index_payload(
    source_index: dict[str, Any],
    *,
    index_kind: str,
    entries: list[dict[str, Any]],
) -> dict[str, Any]:
    kind_field = f"{index_kind}_kind"
    local_id_suffix = {"entity": "entities"}.get(index_kind, f"{index_kind}s")
    stable_fields = {
        "entity": ["id", "entity_kind", "source_record_id", "coordinates"],
        "artifact": ["id", "artifact_kind", "source_record_id", "path", "content_hash"],
        "event": [
            "id",
            "event_kind",
            "event_role",
            "source_record_id",
            "path",
            "heading_ref",
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
            "path": DEFAULT_OUTPUT.as_posix(),
            "local_id": source_index["index_identity"]["local_id"],
            "content_digest": source_index["index_identity"]["content_digest"],
        },
        "summary": {
            "entry_count": len(entries),
            "kind_counts": entry_kind_counts(entries, kind_field),
        },
        "entries": entries,
        "registry_output": {
            "consumer": "aoa-kag-mcp",
            "resource_shape": f"repo-local-{index_kind}-index",
            "stable_fields": stable_fields,
        },
    }
    payload["index_identity"]["content_digest"] = payload_digest(payload)
    return payload


def build_repository_indexes(source_index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = [record for record in source_index["records"] if isinstance(record, dict)]
    repo = str(source_index["repo"]["name"])
    return {
        "entity": repository_index_payload(
            source_index,
            index_kind="entity",
            entries=entity_entries(records),
        ),
        "artifact": repository_index_payload(
            source_index,
            index_kind="artifact",
            entries=artifact_entries(records),
        ),
        "event": repository_index_payload(
            source_index,
            index_kind="event",
            entries=event_entries(repo, records),
        ),
    }


def repository_index_output_paths(output_path: Path) -> dict[str, Path]:
    return {
        index_kind: output_path.parent / filename
        for index_kind, filename in REPOSITORY_INDEX_FILENAMES.items()
    }


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
    parser.add_argument(
        "--index-family",
        action="store_true",
        help="Generate or check the source, entity, artifact, and event index family.",
    )
    parser.add_argument("--check", action="store_true", help="Check output parity without writing.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    output = Path(args.output)
    output_path = repo_root / output
    family_paths = repository_index_output_paths(output_path)
    payload = build_index(
        repo_root,
        output=output,
        excluded_outputs=tuple(family_paths.values()) if args.index_family else (),
    )
    family = build_repository_indexes(payload) if args.index_family else {}
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
