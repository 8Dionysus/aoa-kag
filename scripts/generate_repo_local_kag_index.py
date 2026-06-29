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


def repo_name(repo_root: Path) -> str:
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
    if name == "SECURITY.md":
        return "security"
    if is_generated_decision_index(rel):
        return "generated_readmodel"
    if suffix == ".md":
        return "document"
    if "receipts" in parts:
        return "receipt"
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
    if suffix == ".py" and is_command_entrypoint(rel) and name.startswith("validate_"):
        return "validator"
    if suffix == ".py" and is_command_entrypoint(rel):
        return "script"
    if "mechanics" in parts:
        return "mechanics_surface"
    if suffix in {".py", ".js", ".ts", ".sh"}:
        return "source_code"
    return "unknown"


def is_command_entrypoint(rel: Path) -> bool:
    if rel.suffix != ".py":
        return False
    name = rel.name
    if name in LANE_ENTRYPOINTS:
        return True
    if name.startswith(("build_", "generate_", "run_", "validate_")):
        return True
    return False


def is_test_entrypoint(rel: Path) -> bool:
    return rel.suffix == ".py" and "tests" in rel.parts and rel.name.startswith("test_")


def is_generated_decision_index(rel: Path) -> bool:
    return len(rel.parts) >= 4 and rel.parts[:3] == ("docs", "decisions", "indexes")


def code_role(rel: Path, kind: str) -> str:
    if rel.suffix != ".py":
        return "none"
    if kind == "test":
        return "test"
    if kind == "validator":
        return "validator"
    if rel.name.startswith(("build_", "generate_")):
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
    if kind == "script" and rel.name.startswith(("build_", "generate_")):
        return "builder"
    if kind == "script":
        if rel.name in {"ci_gate.py", "release_check.py", "run_tests.py"}:
            return "lane_entrypoint"
        return "script"
    return "none"


def surface_state(rel: Path, kind: str) -> str:
    parts = rel.parts
    if "legacy" in parts:
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
    if kind in {"receipt", "generated_readmodel", "index", "projection"}:
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


def owner_commands_for(rel: Path, command: str) -> list[str]:
    if command == "validator":
        return [f"python {rel.as_posix()}"]
    if command == "test":
        return [f"python -m unittest {rel.as_posix()}"]
    if rel.as_posix() == "scripts/ci_gate.py":
        return [
            "python scripts/ci_gate.py --mode source-fast",
            "python scripts/ci_gate.py --mode generated",
        ]
    if command in {"script", "builder", "lane_entrypoint"}:
        return [f"python {rel.as_posix()}"]
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


def generated_by_for(rel: Path, state: str, tracked_paths: set[Path]) -> str:
    if state != "generated_readmodel":
        return ""
    rel_path = rel.as_posix()
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
    kind = artifact_kind(rel)
    doc_role = document_role(rel)
    code = code_role(rel, kind)
    mech = mechanics_role(rel)
    command = command_role(rel, kind, doc_role)
    state = surface_state(rel, kind)
    headings = heading_refs(content, rel_path) if doc_role != "none" else []
    line_refs = [f"{rel_path}:1"] if content else []
    authority = source_authority(state)
    provenance_source_ref = {"repo": repo, "path": rel_path, "role": "primary", "authority": authority}
    generated_by = generated_by_for(rel, state, tracked_paths)
    required_tools = ["python"] if rel.suffix == ".py" else []
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
            "observed_by": "scripts/generate_repo_local_kag_index.py",
            "generated_by": generated_by,
            "validated_by": ["scripts/validate_kag.py"],
            "source_refs": [provenance_source_ref],
            "materials": [],
        },
        "toolchain": {
            "detected_tools": ["git", "python"],
            "required_tools": sorted(set(required_tools)),
            "owner_commands": owner_commands_for(rel, command),
        },
        "classification": {
            "primary_kind": primary_kind(kind, doc_role, command),
            "confidence": "low" if kind == "unknown" else "high",
        },
        "freshness": {"mode": "source_snapshot", "state": "current", "checked_ref": snapshot_ref},
        "access": access_for(rel_path),
        "refs": {"path_ref": rel_path, "line_refs": line_refs, "heading_refs": headings},
        "owner_return_route": {"surface": rel_path, "route_kind": route_kind_for(kind, doc_role, command)},
        "validator_route": {"surface": "scripts/validate_kag.py", "route_kind": "source_fast"},
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
