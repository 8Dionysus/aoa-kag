from __future__ import annotations

import ast
import copy
import hashlib
import importlib.metadata
import json
import math
import os
import stat
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "aoa-repo-local-kag-family-manifest-v3"
SCHEMA_REF = "aoa-kag:schemas/repo-local-kag-family-manifest.schema.json"
MANIFEST_RELATIVE_PATH = Path("kag/indexes/index_family.manifest.json")
SHARD_ROOT_RELATIVE_PATH = Path("kag/indexes/shards")
BUDGET_RECEIPT_ROOT_RELATIVE_PATH = Path(
    "kag/receipts/index_family_budget"
)
BUDGET_RECEIPT_EXCLUDED_PREFIX = "kag/receipts/index_family_budget/"
BUDGET_RECEIPT_PRODUCER_MANIFEST_PATH = Path(
    "config/repo-local-kag-budget-producer.json"
)
BUDGET_RECEIPT_PRODUCER_MANIFEST_SCHEMA_PATH = Path(
    "schemas/repo-local-kag-budget-producer-manifest.schema.json"
)
BUDGET_RECEIPT_SCHEMA_PATH = Path(
    "schemas/repo-local-kag-budget-receipt.schema.json"
)
TIERED_CONTROL_PATHS = {
    Path("kag/indexes/corpus.manifest.json"),
    Path("kag/indexes/hot_profile.json"),
    Path("kag/indexes/artifact_locators.json"),
}
BUDGET_RECEIPT_SCHEMA_VERSION = "aoa-repo-local-kag-budget-receipt-v2"
BUDGET_CANDIDATE_IDENTITY_VERSION = (
    "aoa-kag:budget-receipt-candidate-identity-v2"
)
BUDGET_CANDIDATE_SEAL_ALGORITHM = "sha256:canonical-json-file-inventory-v2"
BUDGET_PRODUCER_IDENTITY_VERSION = "aoa-kag:budget-receipt-producer-identity-v4"
BUDGET_PRODUCER_MANIFEST_VERSION = (
    "aoa-kag:budget-receipt-producer-manifest-v2"
)
BUDGET_PRODUCER_CLOSURE_MODE = "ast-import-closure-portable-runtime-contract-v1"
BUDGET_PRODUCER_DYNAMIC_IMPORT_POLICY = "fail-closed-unresolved-local-v1"
BUDGET_DYNAMIC_IMPORT_ATTRIBUTES = frozenset(
    {
        "__import__",
        "import_module",
        "module_from_spec",
        "spec_from_file_location",
    }
)
BUDGET_DECLARED_DYNAMIC_IMPORT_KINDS = frozenset(
    {
        "module_from_spec",
        "spec_from_file_location",
    }
)
BUDGET_DYNAMIC_IMPORT_MAPPING_METHODS = frozenset(
    {
        "get",
        "getitem",
        "__getitem__",
    }
)
BUDGET_PRODUCER_RUNTIME_INPUTS_VERSION = (
    "aoa-kag:budget-receipt-producer-runtime-inputs-v2"
)
BUDGET_SOURCE_EPOCH_VERSION = "aoa-kag:budget-receipt-source-epoch-v1"
BUDGET_PRODUCER_ACTION_PATH = Path(
    ".github/actions/repo-local-kag-index/action.yml"
)
BUDGET_RECEIPT_FIELDS = frozenset(
    {
        "schema_version",
        "repo",
        "scope",
        "base_ref",
        "head_family_digest",
        "head_source_snapshot",
        "candidate_identity",
        "producer_identity",
        "changed_generated_bytes",
        "changed_generated_files",
        "default_limit_bytes",
        "allowed_bytes",
        "tracked_bytes",
        "tracked_bytes_max",
        "allowed_tracked_bytes",
        "reason",
        "approved_by",
        "decision_ref",
    }
)
LEGACY_BUDGET_RECEIPT_SCHEMA_VERSION = "aoa-repo-local-kag-budget-receipt-v1"
LEGACY_BUDGET_RECEIPT_FIELDS = frozenset(
    {
        "schema_version",
        "repo",
        "scope",
        "base_ref",
        "head_family_digest",
        "changed_generated_bytes",
        "changed_generated_files",
        "default_limit_bytes",
        "allowed_bytes",
        "tracked_bytes",
        "tracked_bytes_max",
        "allowed_tracked_bytes",
        "reason",
        "approved_by",
        "decision_ref",
    }
)
DECISION_REF = (
    "aoa-kag:docs/decisions/"
    "AOA-KAG-D-0017-portable-content-addressed-repository-family.md"
)
TIERED_DECISION_REF = (
    "aoa-kag:docs/decisions/"
    "AOA-KAG-D-0039-tiered-content-addressed-kag-distribution.md"
)
TIERED_DISTRIBUTION_SCHEMA_VERSION = (
    "aoa-repo-local-kag-distribution-manifest-v1"
)

TARGET_SHARD_BYTES = 128 * 1024
HARD_MAX_SHARD_BYTES = 192 * 1024
MAX_RECORD_BYTES = 128 * 1024
CHUNK_TARGET_BYTES = 64 * 1024
DEFAULT_DELTA_BYTES_MAX = 1024 * 1024
GLOBAL_TRACKED_BYTES_MAX = 48 * 1024 * 1024
OS_AGGREGATE_TRACKED_BYTES_MAX = 320 * 1024 * 1024
MIN_BASELINE_BYTES = 4 * 1024 * 1024
BASELINE_HEADROOM = 1.10
HEX_DIGITS = "0123456789abcdef"
ZERO_DIGEST = "0" * 64

LEGACY_INDEX_FILENAMES = {
    "source": "source_surface_index.json",
    "artifact": "repo_artifact_index.json",
    "anchor": "repo_anchor_index.json",
    "entity": "repo_entity_index.json",
    "event": "repo_event_index.json",
    "assertion": "repo_assertion_index.json",
    "relation": "repo_relation_index.json",
}
COMPATIBILITY_ORDER = (
    "source",
    "artifact",
    "anchor",
    "entity",
    "event",
    "assertion",
    "relation",
)
ANCHOR_DEFAULTS = {
    "evidence_class": "deterministic",
    "provenance_ref": "deterministic",
    "temporal_ref": "current",
    "trust_ref": "deterministic",
}
CHUNKABLE_FIELDS = {
    "anchor": ("outbound_refs",),
    "event": (
        "anchor_ids",
        "changes",
        "evidence_refs",
        "object_ids",
        "source_record_ids",
    ),
}


class PortableFamilyError(ValueError):
    pass


def _budget_procedure_root() -> Path:
    """Resolve the checkout that owns the budget procedure itself."""
    root = Path(__file__).resolve().parents[2]
    if not (root / BUDGET_RECEIPT_PRODUCER_MANIFEST_PATH).is_file():
        raise PortableFamilyError(
            "executing aoa-kag procedure checkout is missing its producer manifest"
        )
    return root


@lru_cache(maxsize=32)
def _budget_git_object_format(root: str) -> str:
    try:
        result = subprocess.run(
            ("git", "rev-parse", "--show-object-format"),
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, OSError) as exc:
        raise PortableFamilyError(
            "cannot resolve producer Git object format"
        ) from exc
    object_format = result.stdout.strip()
    if result.returncode == 0 and object_format in {"sha1", "sha256"}:
        return object_format

    # GitHub distributes a referenced composite action as a source archive,
    # without the producer repository's .git directory. Ask the executing Git
    # binary for its standalone object format so the archive computes the same
    # blob identities as its SHA-1-backed source checkout. A SHA-256 producer
    # checkout still takes the repository-backed branch above.
    try:
        probe = subprocess.run(
            ("git", "hash-object", "--no-filters", "--stdin"),
            cwd=root,
            check=False,
            capture_output=True,
            input=b"",
        )
    except (FileNotFoundError, OSError) as exc:
        raise PortableFamilyError(
            "cannot resolve producer Git object format"
        ) from exc
    digest = probe.stdout.strip().decode("ascii", errors="ignore")
    empty_blob = b"blob 0\0"
    inferred_format = next(
        (
            algorithm
            for algorithm in ("sha1", "sha256")
            if digest == hashlib.new(algorithm, empty_blob).hexdigest()
        ),
        None,
    )
    if probe.returncode != 0 or inferred_format is None:
        raise PortableFamilyError(
            "cannot resolve producer Git object format"
        )
    return inferred_format


def _budget_git_blob(root: Path, relative: Path) -> str:
    resolved_root = root.resolve()
    object_format = _budget_git_object_format(str(resolved_root))
    expected_length = {
        "sha1": 40,
        "sha256": 64,
    }[object_format]
    result = subprocess.run(
        ("git", "hash-object", "--no-filters", "--", relative.as_posix()),
        cwd=resolved_root,
        check=False,
        capture_output=True,
        text=True,
    )
    blob = result.stdout.strip()
    if result.returncode != 0 or len(blob) != expected_length or any(
        character not in HEX_DIGITS for character in blob
    ):
        raise PortableFamilyError(
            f"cannot resolve producer Git blob for {relative.as_posix()}"
        )
    return f"{object_format}:{blob}"


def _budget_valid_git_blob(value: object) -> bool:
    if not isinstance(value, str):
        return False
    algorithm, separator, digest = value.partition(":")
    expected_length = {
        "sha1": 40,
        "sha256": 64,
    }.get(algorithm)
    return (
        separator == ":"
        and expected_length is not None
        and len(digest) == expected_length
        and all(character in HEX_DIGITS for character in digest)
    )


def _budget_relative_path(value: object, *, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise PortableFamilyError(f"{label} must be a non-empty relative path")
    relative = Path(value)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise PortableFamilyError(f"{label} is outside the owner root: {value}")
    return relative


def _budget_regular_owner_file(
    root: Path,
    relative: Path,
    *,
    label: str,
) -> Path:
    path = root.joinpath(*relative.parts)
    try:
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise PortableFamilyError(
            f"{label} is missing: {relative.as_posix()}"
        ) from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise PortableFamilyError(
            f"{label} must be a regular in-root file: {relative.as_posix()}"
        )
    try:
        path.resolve(strict=True).relative_to(root.resolve())
    except ValueError as exc:
        raise PortableFamilyError(
            f"{label} resolves outside the owner root: {relative.as_posix()}"
        ) from exc
    return path


def _budget_load_producer_manifest(
    root: Path,
) -> tuple[dict[str, Any], bytes]:
    manifest_path = _budget_regular_owner_file(
        root,
        BUDGET_RECEIPT_PRODUCER_MANIFEST_PATH,
        label="producer manifest",
    )
    raw = manifest_path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PortableFamilyError("producer manifest is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise PortableFamilyError("producer manifest must contain an object")
    if payload.get("schema_version") != BUDGET_PRODUCER_MANIFEST_VERSION:
        raise PortableFamilyError("producer manifest schema version is unsupported")
    if payload.get("owner") != "aoa-kag":
        raise PortableFamilyError("producer manifest owner must be aoa-kag")
    if payload.get("closure_mode") != BUDGET_PRODUCER_CLOSURE_MODE:
        raise PortableFamilyError("producer manifest closure mode is unsupported")
    if payload.get("dynamic_import_policy") != BUDGET_PRODUCER_DYNAMIC_IMPORT_POLICY:
        raise PortableFamilyError("producer manifest dynamic import policy is unsupported")
    for key in (
        "python_entrypoints",
        "python_import_closure",
        "schema_inputs",
        "action_inputs",
        "environment",
        "dependencies",
    ):
        if not isinstance(payload.get(key), list) or not payload[key]:
            raise PortableFamilyError(f"producer manifest {key} must be non-empty")
    dynamic_imports = payload.get("dynamic_imports", [])
    if not isinstance(dynamic_imports, list):
        raise PortableFamilyError("producer manifest dynamic_imports must be a list")
    action_path = _budget_relative_path(
        payload.get("action_path"),
        label="producer manifest action_path",
    )
    if action_path != BUDGET_PRODUCER_ACTION_PATH:
        raise PortableFamilyError("producer manifest action_path is not canonical")
    for key in ("python_entrypoints", "python_import_closure", "schema_inputs"):
        values: list[Path] = []
        for index, value in enumerate(payload[key]):
            values.append(
                _budget_relative_path(
                    value,
                    label=f"producer manifest {key}[{index}]",
                )
            )
        if len(values) != len(set(values)):
            raise PortableFamilyError(
                f"producer manifest {key} contains duplicate paths"
            )
    entrypoints = {
        _budget_relative_path(value, label="producer manifest entrypoint")
        for value in payload["python_entrypoints"]
    }
    closure = {
        _budget_relative_path(value, label="producer manifest closure path")
        for value in payload["python_import_closure"]
    }
    if not entrypoints <= closure:
        raise PortableFamilyError(
            "producer manifest entrypoints must be in the import closure"
        )
    declared_dynamic_imports = _budget_declared_dynamic_import_targets(
        root,
        dynamic_imports,
    )
    for source, _kind in declared_dynamic_imports:
        if source not in closure:
            raise PortableFamilyError(
                "producer manifest dynamic import source must be in the import closure: "
                + source.as_posix()
            )
    for index, item in enumerate(payload["environment"]):
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("name"), str)
            or not item["name"]
            or not isinstance(item.get("role"), str)
            or not item["role"]
        ):
            raise PortableFamilyError(
                f"producer manifest environment[{index}] is malformed"
            )
    for index, item in enumerate(payload["dependencies"]):
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("name"), str)
            or not item["name"]
            or not isinstance(item.get("version"), str)
            or not item["version"]
            or (
                "required" in item
                and not isinstance(item.get("required"), bool)
            )
        ):
            raise PortableFamilyError(
                f"producer manifest dependencies[{index}] is malformed"
            )
    return payload, raw


def _budget_module_name(root: Path, relative: Path) -> list[str]:
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return parts


def _budget_local_module_path(root: Path, module: str) -> Path | None:
    if not module:
        return None
    parts = module.split(".")
    for base in (root, root / "scripts"):
        candidate = base.joinpath(*parts)
        file_candidate = candidate.with_suffix(".py")
        if file_candidate.is_file():
            return file_candidate.relative_to(root)
        init_candidate = candidate / "__init__.py"
        if init_candidate.is_file():
            return init_candidate.relative_to(root)
    return None


def _budget_package_initializers(root: Path, relative: Path) -> list[Path]:
    """Return every producer package initializer on a local import path.

    Python executes each package initializer before loading a descendant
    module, including compatibility facades with eager re-exports. Binding
    the full ancestor chain keeps the producer identity aligned with the
    code that the owner-callable runtime actually executes.
    """
    initializers: list[Path] = []
    parent = relative.parent
    while parent.parts:
        initializer = root / parent / "__init__.py"
        if initializer.is_file():
            candidate = initializer.relative_to(root)
            initializers.append(candidate)
        parent = parent.parent
    return initializers


def _budget_resolve_local_import(
    root: Path,
    relative: Path,
    module: str,
    level: int,
) -> Path | None:
    current = _budget_module_name(root, relative)
    package = current if relative.name == "__init__.py" else current[:-1]
    if level:
        if level - 1 > len(package):
            return None
        prefix = package[: len(package) - (level - 1)]
        qualified = ".".join(prefix + ([*module.split(".")] if module else []))
        return _budget_local_module_path(root, qualified)
    return _budget_local_module_path(root, module)


def _budget_import_aliases(
    tree: ast.AST,
) -> tuple[set[str], set[str], set[str], set[str]]:
    """Collect a deliberately bounded set of import-capability aliases.

    This is not a general Python data-flow engine.  It follows only direct
    imports and simple assignments so the producer can fail closed on the
    common ways a dynamic import primitive is hidden without claiming whole-
    language analysis.
    """
    importlib_modules: set[str] = set()
    dynamic_imports: set[str] = {"__import__"}
    getattr_aliases: set[str] = {"getattr"}
    builtin_modules: set[str] = set()
    assignments: list[tuple[ast.AST, ast.AST]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound_name = alias.asname or alias.name.split(".", 1)[0]
                if alias.name == "builtins":
                    builtin_modules.add(bound_name)
                if alias.name == "importlib" or alias.name.startswith(
                    "importlib."
                ):
                    importlib_modules.add(bound_name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "builtins":
                for alias in node.names:
                    bound_name = alias.asname or alias.name
                    if alias.name == "getattr":
                        getattr_aliases.add(bound_name)
                    elif alias.name == "__import__":
                        dynamic_imports.add(bound_name)
            elif module == "importlib" or module.startswith("importlib."):
                for alias in node.names:
                    bound_name = alias.asname or alias.name
                    if alias.name in BUDGET_DYNAMIC_IMPORT_ATTRIBUTES:
                        dynamic_imports.add(bound_name)
                    elif alias.name != "*":
                        importlib_modules.add(bound_name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                assignments.append((target, node.value))
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            assignments.append((node.target, node.value))
        elif isinstance(node, ast.NamedExpr):
            assignments.append((node.target, node.value))

    changed = True
    while changed:
        changed = False
        for target, value in assignments:
            names = set(_budget_assignment_names(target))
            if not names:
                continue
            if _budget_is_importlib_reference(
                value,
                importlib_modules=importlib_modules,
            ):
                before = len(importlib_modules)
                importlib_modules.update(names)
                changed |= len(importlib_modules) != before
            if _budget_dynamic_import_reference(
                value,
                importlib_modules=importlib_modules,
                dynamic_imports=dynamic_imports,
                getattr_aliases=getattr_aliases,
                builtin_modules=builtin_modules,
            ):
                before = len(dynamic_imports)
                dynamic_imports.update(names)
                changed |= len(dynamic_imports) != before
            if _budget_is_getattr_reference(
                value,
                getattr_aliases=getattr_aliases,
                builtin_modules=builtin_modules,
            ):
                before = len(getattr_aliases)
                getattr_aliases.update(names)
                changed |= len(getattr_aliases) != before

    return importlib_modules, dynamic_imports, getattr_aliases, builtin_modules


def _budget_assignment_names(target: ast.AST) -> Iterable[str]:
    if isinstance(target, ast.Name):
        yield target.id
    elif isinstance(target, (ast.List, ast.Tuple)):
        for element in target.elts:
            yield from _budget_assignment_names(element)


def _budget_is_importlib_reference(
    node: ast.AST,
    *,
    importlib_modules: set[str],
) -> bool:
    if isinstance(node, ast.Name):
        return node.id in importlib_modules
    if isinstance(node, ast.Attribute):
        return _budget_is_importlib_reference(
            node.value,
            importlib_modules=importlib_modules,
        )
    return False


def _budget_is_builtin_reference(
    node: ast.AST,
    *,
    builtin_modules: set[str],
) -> bool:
    if isinstance(node, ast.Name):
        return node.id in builtin_modules
    if isinstance(node, ast.Attribute):
        return _budget_is_builtin_reference(
            node.value,
            builtin_modules=builtin_modules,
        )
    return False


def _budget_is_getattr_callable(
    node: ast.AST,
    *,
    getattr_aliases: set[str],
    builtin_modules: set[str],
) -> bool:
    if isinstance(node, ast.Name):
        return node.id in getattr_aliases
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "getattr"
        and _budget_is_builtin_reference(
            node.value,
            builtin_modules=builtin_modules,
        )
    )


def _budget_dynamic_getattr_call(
    node: ast.AST,
    *,
    importlib_modules: set[str],
    getattr_aliases: set[str],
    builtin_modules: set[str],
) -> str | None:
    if not isinstance(node, ast.Call) or not _budget_is_getattr_callable(
        node.func,
        getattr_aliases=getattr_aliases,
        builtin_modules=builtin_modules,
    ):
        return None
    if len(node.args) < 2:
        return None
    if _budget_is_importlib_reference(
        node.args[0],
        importlib_modules=importlib_modules,
    ):
        return "getattr(importlib)"
    attribute = node.args[1]
    if (
        isinstance(attribute, ast.Constant)
        and isinstance(attribute.value, str)
        and attribute.value in BUDGET_DYNAMIC_IMPORT_ATTRIBUTES
    ):
        return f"getattr({attribute.value})"
    return None


def _budget_dynamic_import_reference(
    node: ast.AST,
    *,
    importlib_modules: set[str],
    dynamic_imports: set[str],
    getattr_aliases: set[str],
    builtin_modules: set[str],
) -> str | None:
    if isinstance(node, ast.Name):
        return node.id if node.id in dynamic_imports else None
    if isinstance(node, ast.Attribute):
        if node.attr in BUDGET_DYNAMIC_IMPORT_ATTRIBUTES:
            return node.attr
        return None
    if isinstance(node, ast.Call):
        dynamic_getattr = _budget_dynamic_getattr_call(
            node,
            importlib_modules=importlib_modules,
            getattr_aliases=getattr_aliases,
            builtin_modules=builtin_modules,
        )
        if dynamic_getattr is not None:
            return dynamic_getattr
        return _budget_dynamic_import_reference(
            node.func,
            importlib_modules=importlib_modules,
            dynamic_imports=dynamic_imports,
            getattr_aliases=getattr_aliases,
            builtin_modules=builtin_modules,
        )
    return None


def _budget_is_getattr_reference(
    node: ast.AST,
    *,
    getattr_aliases: set[str],
    builtin_modules: set[str],
) -> bool:
    return _budget_is_getattr_callable(
        node,
        getattr_aliases=getattr_aliases,
        builtin_modules=builtin_modules,
    )


def _budget_dynamic_import_call(
    node: ast.Call,
    *,
    importlib_modules: set[str],
    dynamic_imports: set[str],
    getattr_aliases: set[str],
    builtin_modules: set[str],
) -> str | None:
    return _budget_dynamic_import_reference(
        node.func,
        importlib_modules=importlib_modules,
        dynamic_imports=dynamic_imports,
        getattr_aliases=getattr_aliases,
        builtin_modules=builtin_modules,
    )


def _budget_static_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _budget_indirect_dynamic_import_lookup(
    node: ast.AST,
    *,
    importlib_modules: set[str],
) -> str | None:
    """Reject importer lookups that bypass the bounded alias recognizer."""
    if isinstance(node, ast.Subscript):
        key = _budget_static_string(node.slice)
        if key in BUDGET_DYNAMIC_IMPORT_ATTRIBUTES:
            return f"subscript[{key}]"
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
            if node.value.func.id in {"globals", "locals", "vars"}:
                return f"{node.value.func.id}()[...]"
        if isinstance(node.value, ast.Name) and node.value.id in {
            "__builtins__",
            "builtins",
        }:
            return "builtins[...]"
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        lookup_method = node.func.attr
        if lookup_method in BUDGET_DYNAMIC_IMPORT_MAPPING_METHODS:
            if lookup_method == "get":
                key_argument = 0
            elif lookup_method == "getitem":
                key_argument = 1
            else:
                key_argument = 1 if len(node.args) > 1 else 0
            key = (
                _budget_static_string(node.args[key_argument])
                if len(node.args) > key_argument
                else None
            )
            if key in BUDGET_DYNAMIC_IMPORT_ATTRIBUTES:
                return f"{lookup_method}[{key}]"
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr not in {"__getattribute__", "__getattr__"}:
            return None
        if _budget_is_importlib_reference(
            node.func.value,
            importlib_modules=importlib_modules,
        ):
            return f"importlib.{node.func.attr}(...)"
        attribute = _budget_static_string(node.args[1]) if len(node.args) > 1 else None
        if attribute in BUDGET_DYNAMIC_IMPORT_ATTRIBUTES:
            return f"{node.func.attr}({attribute})"
    return None


def _budget_dynamic_import_from(node: ast.ImportFrom) -> str | None:
    module = node.module or ""
    if module == "importlib" or module.startswith("importlib."):
        for alias in node.names:
            if alias.name == "*" or alias.name in BUDGET_DYNAMIC_IMPORT_ATTRIBUTES:
                return f"from {module} import {alias.name}"
    if module == "builtins":
        for alias in node.names:
            if alias.name in {"__import__", "getattr"}:
                return f"from builtins import {alias.name}"
    return None


def _budget_declared_dynamic_import_targets(
    root: Path,
    declarations: Sequence[Mapping[str, Any]],
) -> dict[tuple[Path, str], Path]:
    """Normalize the small, explicit dynamic-import allowlist.

    Dynamic imports remain rejected by default.  A declaration binds one
    reviewed call primitive in one source file to one in-root target file;
    the target is then traversed as part of the same producer closure.
    """
    targets: dict[tuple[Path, str], Path] = {}
    for index, item in enumerate(declarations):
        if not isinstance(item, Mapping) or set(item) != {"kind", "source", "target"}:
            raise PortableFamilyError(
                f"producer manifest dynamic_imports[{index}] is malformed"
            )
        kind = item.get("kind")
        if (
            not isinstance(kind, str)
            or kind not in BUDGET_DECLARED_DYNAMIC_IMPORT_KINDS
        ):
            raise PortableFamilyError(
                f"producer manifest dynamic_imports[{index}] kind is unsupported"
            )
        source = _budget_relative_path(
            item.get("source"),
            label=f"producer manifest dynamic_imports[{index}].source",
        )
        target = _budget_relative_path(
            item.get("target"),
            label=f"producer manifest dynamic_imports[{index}].target",
        )
        _budget_regular_owner_file(
            root,
            source,
            label=f"producer dynamic import source[{index}]",
        )
        _budget_regular_owner_file(
            root,
            target,
            label=f"producer dynamic import target[{index}]",
        )
        key = (source, kind)
        if key in targets:
            raise PortableFamilyError(
                "producer manifest dynamic_imports contains duplicate source/kind: "
                f"{source.as_posix()}:{kind}"
            )
        targets[key] = target
    return targets


def _budget_import_closure(
    root: Path,
    entrypoints: Sequence[Path],
    *,
    declared_dynamic_imports: Sequence[Mapping[str, Any]] = (),
) -> list[Path]:
    declared_dynamic_targets = _budget_declared_dynamic_import_targets(
        root,
        declared_dynamic_imports,
    )
    used_dynamic_imports: set[tuple[Path, str]] = set()
    seen: set[Path] = set()
    queue = list(entrypoints)
    unresolved: list[str] = []
    while queue:
        relative = queue.pop()
        if relative in seen:
            continue
        path = _budget_regular_owner_file(
            root,
            relative,
            label="producer import closure file",
        )
        seen.add(relative)
        queue.extend(_budget_package_initializers(root, relative))
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            raise PortableFamilyError(
                f"producer import closure cannot parse {relative.as_posix()}"
            ) from exc
        parents = {
            id(child): node
            for node in ast.walk(tree)
            for child in ast.iter_child_nodes(node)
        }
        (
            importlib_modules,
            dynamic_imports,
            getattr_aliases,
            builtin_modules,
        ) = _budget_import_aliases(tree)
        for node in ast.walk(tree):
            indirect_dynamic_import = _budget_indirect_dynamic_import_lookup(
                node,
                importlib_modules=importlib_modules,
            )
            if indirect_dynamic_import is not None:
                raise PortableFamilyError(
                    "producer import closure contains an unresolved dynamic "
                    f"import ({indirect_dynamic_import}) in {relative.as_posix()}"
                )
            if isinstance(node, ast.ImportFrom):
                dynamic_import = _budget_dynamic_import_from(node)
                if dynamic_import is not None:
                    raise PortableFamilyError(
                        "producer import closure contains an unresolved dynamic "
                        f"import ({dynamic_import}) in {relative.as_posix()}"
                    )
            elif isinstance(node, ast.Attribute):
                dynamic_import = _budget_dynamic_import_reference(
                    node,
                    importlib_modules=importlib_modules,
                    dynamic_imports=dynamic_imports,
                    getattr_aliases=getattr_aliases,
                    builtin_modules=builtin_modules,
                )
                if dynamic_import is not None:
                    parent = parents.get(id(node))
                    if isinstance(parent, ast.Call) and parent.func is node:
                        continue
                    raise PortableFamilyError(
                        "producer import closure contains an unresolved dynamic "
                        f"import ({dynamic_import}) in {relative.as_posix()}"
                    )
            elif isinstance(node, ast.Call):
                dynamic_import = _budget_dynamic_import_call(
                    node,
                    importlib_modules=importlib_modules,
                    dynamic_imports=dynamic_imports,
                    getattr_aliases=getattr_aliases,
                    builtin_modules=builtin_modules,
                )
                if dynamic_import is not None:
                    dynamic_key = (relative, dynamic_import)
                    dynamic_target = declared_dynamic_targets.get(dynamic_key)
                    if dynamic_target is None:
                        raise PortableFamilyError(
                            "producer import closure contains an unresolved dynamic "
                            f"import ({dynamic_import}) in {relative.as_posix()}"
                        )
                    used_dynamic_imports.add(dynamic_key)
                    queue.append(dynamic_target)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = _budget_resolve_local_import(
                        root,
                        relative,
                        alias.name,
                        0,
                    )
                    if target is not None:
                        queue.append(target)
                    elif alias.name not in {"scripts", "repo_local"} and (
                        alias.name.startswith(("scripts", "repo_local"))
                    ):
                        unresolved.append(f"{relative.as_posix()}:{alias.name}")
            elif isinstance(node, ast.ImportFrom):
                base_target = _budget_resolve_local_import(
                    root,
                    relative,
                    node.module or "",
                    node.level,
                )
                if base_target is not None:
                    queue.append(base_target)
                for alias in node.names:
                    module = ".".join(
                        part for part in ((node.module or ""), alias.name) if part
                    )
                    target = _budget_resolve_local_import(
                        root,
                        relative,
                        module,
                        node.level,
                    )
                    if target is not None:
                        queue.append(target)
                    elif node.level and node.module is None:
                        unresolved.append(
                            f"{relative.as_posix()}:{'.' * node.level}{alias.name}"
                        )
                    elif module.startswith(("scripts", "repo_local")) and (
                        base_target is None and module not in {"scripts", "repo_local"}
                    ):
                        unresolved.append(f"{relative.as_posix()}:{module}")
    if unresolved:
        raise PortableFamilyError(
            "producer import closure has unresolved local imports: "
            + ", ".join(sorted(set(unresolved)))
        )
    unused_dynamic_imports = sorted(
        set(declared_dynamic_targets) - used_dynamic_imports,
        key=lambda item: (item[0].as_posix(), item[1]),
    )
    if unused_dynamic_imports:
        raise PortableFamilyError(
            "producer manifest declares unused dynamic imports: "
            + ", ".join(
                f"{source.as_posix()}:{kind}"
                for source, kind in unused_dynamic_imports
            )
        )
    return sorted(seen)


def _budget_producer_file_entry(root: Path, relative: Path) -> dict[str, Any]:
    path = _budget_regular_owner_file(
        root,
        relative,
        label="producer identity source",
    )
    content = path.read_bytes()
    return {
        "path": relative.as_posix(),
        "state": "present",
        "content_digest": sha256_bytes(content),
        "bytes": len(content),
        "git_blob": _budget_git_blob(root, relative),
    }


def _budget_runtime_value(value: object, *, kind: str = "string") -> dict[str, Any]:
    if value is None:
        raw = b"<unset>"
        return {
            "state": "unset",
            "kind": kind,
            "value_digest": sha256_bytes(raw),
            "bytes": 0,
        }
    if isinstance(value, Path):
        text = value.as_posix()
    elif isinstance(value, bool):
        text = "true" if value else "false"
    else:
        text = str(value)
    raw = text.encode("utf-8", errors="surrogateescape")
    return {
        "state": "set",
        "kind": kind,
        "value_digest": sha256_bytes(raw),
        "bytes": len(raw),
    }


def _budget_runtime_path_digest(path: Path) -> str:
    return sha256_bytes(path.as_posix().encode("utf-8", errors="surrogateescape"))


def _budget_runtime_contract_digest(value: str) -> str:
    return sha256_bytes(
        ("aoa-kag:budget-producer-runtime-contract:" + value).encode("utf-8")
    )


def _budget_dependency_inputs(
    manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in manifest["dependencies"]:
        name = item["name"]
        declared = item["version"]
        required = item.get("required", True)
        contract_digest = _budget_runtime_contract_digest(f"dependency:{name}:{declared}")
        contract_path_digest = _budget_runtime_path_digest(
            Path(f"<approved-dependency-root>/{name}")
        )
        if name == "python":
            if not (
                declared.startswith(">=")
                and tuple(sys.version_info[:2])
                >= tuple(int(part) for part in declared[2:].split(".")[:2])
            ):
                raise PortableFamilyError(
                    f"producer dependency version does not satisfy python {declared}"
                )
            result.append(
                {
                    "name": name,
                    "declared_version": declared,
                    "required": required,
                    "state": "available",
                    "resolved_version": declared,
                    "path_digest": contract_path_digest,
                    "artifact_digest": contract_digest,
                    "artifact_bytes": len(contract_digest),
                    "artifact_files": 1,
                }
            )
            continue
        if not required:
            result.append(
                {
                    "name": name,
                    "declared_version": declared,
                    "required": required,
                    "state": "declared",
                    "resolved_version": None,
                    "path_digest": contract_path_digest,
                    "artifact_digest": contract_digest,
                    "artifact_bytes": len(contract_digest),
                    "artifact_files": 1,
                }
            )
            continue
        try:
            resolved = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            raise PortableFamilyError(
                f"required producer dependency is unavailable: {name}"
            )
        if resolved != declared:
            raise PortableFamilyError(
                f"producer dependency {name} is {resolved}, expected {declared}"
            )
        result.append(
            {
                "name": name,
                "declared_version": declared,
                "required": required,
                "state": "available",
                "resolved_version": resolved,
                "path_digest": contract_path_digest,
                "artifact_digest": contract_digest,
                "artifact_bytes": len(contract_digest),
                "artifact_files": 1,
            }
        )
    return result


def _budget_default_history_ref(repo_root: Path) -> str:
    environment_ref = os.environ.get("AOA_REPO_LOCAL_KAG_HISTORY_REF", "").strip()
    if environment_ref:
        return environment_ref
    try:
        return subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise PortableFamilyError(
            "producer execution inputs require an explicit history boundary"
        ) from exc


def capture_budget_producer_execution_inputs(
    repo_root: Path,
    *,
    base_ref: str,
    history_ref: str | None = None,
    event_history_ref: str | None = None,
    output: Path | str = Path("kag/indexes/source_surface_index.json"),
    family_mode: str = "portable",
    artifact_root: Path | None = None,
    externalized: bool = False,
    jobs: int | str | None = None,
) -> dict[str, Any]:
    """Capture concrete execution inputs used by the budget producer.

    Secrets and ambient values are represented by state, size, and digests;
    command boundaries and non-secret paths remain explicit so a receipt can
    be replayed without treating a declaration-only manifest as provenance.
    """
    target_root = repo_root.resolve()
    procedure_root = _budget_procedure_root()
    manifest, manifest_raw = _budget_load_producer_manifest(procedure_root)
    resolved_history = history_ref or _budget_default_history_ref(target_root)
    resolved_event = event_history_ref or os.environ.get(
        "AOA_REPO_LOCAL_KAG_EVENT_HISTORY_REF", ""
    ).strip() or resolved_history
    if not isinstance(base_ref, str) or not base_ref:
        raise PortableFamilyError("producer execution inputs require base_ref")
    if not isinstance(resolved_history, str) or not resolved_history:
        raise PortableFamilyError("producer execution inputs require history_ref")
    if not isinstance(resolved_event, str) or not resolved_event:
        raise PortableFamilyError("producer execution inputs require event_history_ref")
    output_value = Path(output).as_posix()
    # Scheduler fan-out changes only execution parallelism; it is not a
    # generated-output input and must not change the producer identity.
    action_values = {
        "repo-root": _budget_runtime_value(Path("<owner-root>"), kind="path"),
        "output": _budget_runtime_value(output_value, kind="relative-path"),
        "history-ref": _budget_runtime_value(resolved_history, kind="git-ref"),
        "event-history-ref": _budget_runtime_value(resolved_event, kind="git-ref"),
    }
    missing_action_inputs = sorted(
        set(manifest["action_inputs"]) - set(action_values)
    )
    if missing_action_inputs:
        raise PortableFamilyError(
            "producer action input capture is incomplete: "
            + ", ".join(missing_action_inputs)
        )
    environment_inputs: list[dict[str, Any]] = []
    for item in manifest["environment"]:
        name = item["name"]
        value = os.environ.get(name)
        captured = _budget_runtime_value(value, kind="environment")
        environment_inputs.append(
            {
                "name": name,
                "role": item["role"],
                **captured,
            }
        )
    runtime_files: list[dict[str, Any]] = []
    runtime_paths = sorted(
        {
            *(
                _budget_relative_path(value, label="producer schema input")
                for value in manifest["schema_inputs"]
            ),
            BUDGET_RECEIPT_PRODUCER_MANIFEST_PATH,
            BUDGET_RECEIPT_PRODUCER_MANIFEST_SCHEMA_PATH,
            BUDGET_PRODUCER_ACTION_PATH,
        }
    )
    for relative in runtime_paths:
        path = _budget_regular_owner_file(
            procedure_root,
            relative,
            label="producer non-Python input",
        )
        content = path.read_bytes()
        runtime_files.append(
            {
                "path": relative.as_posix(),
                "content_digest": sha256_bytes(content),
                "bytes": len(content),
            }
        )
    dependencies = _budget_dependency_inputs(manifest)
    python_dependency = next(
        (item for item in dependencies if item["name"] == "python"),
        None,
    )
    if python_dependency is None:
        raise PortableFamilyError("producer dependency contract omits python")
    command_targets = {
        "repo_root": {
            "path_digest": _budget_runtime_path_digest(Path("<owner-root>")),
            "resolved_path_digest": _budget_runtime_path_digest(Path("<owner-root>")),
        },
        "base_ref": base_ref,
        "history_ref": resolved_history,
        "event_history_ref": resolved_event,
        "output": output_value,
        "family_mode": family_mode,
        "artifact_root": (
            {
                "path": "<task-local-artifact-root>",
                "path_digest": _budget_runtime_path_digest(
                    Path("<task-local-artifact-root>")
                ),
            }
            if artifact_root is not None
            else None
        ),
        "externalized": bool(externalized),
    }
    return {
        "schema_version": BUDGET_PRODUCER_RUNTIME_INPUTS_VERSION,
        "action_inputs": {
            key: action_values[key] for key in sorted(action_values)
        },
        "environment": sorted(environment_inputs, key=lambda item: item["name"]),
        "dependencies": dependencies,
        "interpreter": {
            "implementation": sys.implementation.name,
            "version": python_dependency["declared_version"],
            "invoked_path_digest": _budget_runtime_path_digest(
                Path("<approved-python-interpreter>")
            ),
            "resolved_path_digest": _budget_runtime_path_digest(
                Path("<approved-python-interpreter>")
            ),
            "artifact_digest": _budget_runtime_contract_digest(
                "python:" + sys.implementation.name + ":"
                + str(python_dependency["declared_version"])
            ),
        },
        "non_python_inputs": runtime_files,
        "dynamic_imports": [],
        "command_targets": command_targets,
        "manifest_digest": sha256_bytes(manifest_raw),
    }


def _budget_producer_identity(
    producer_execution_inputs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a reviewed, content-addressed producer closure identity.

    The manifest names the callable entrypoints, their complete local Python
    import closure, admitted schema inputs, action inputs, environment names,
    and dependency versions. The AST replay is deliberately fail-closed when
    a new local or dynamic import is not reviewed into that manifest. Concrete
    action, environment, interpreter, dependency, non-Python, and command
    inputs are bound separately. Producer commit and tree identities remain
    outside the receipt to avoid a self-owner cycle.
    """
    root = _budget_procedure_root()
    if producer_execution_inputs is None:
        producer_execution_inputs = capture_budget_producer_execution_inputs(
            root,
            base_ref="HEAD",
            history_ref="HEAD",
            event_history_ref="HEAD",
            output=Path("kag/indexes/source_surface_index.json"),
        )
    manifest, manifest_raw = _budget_load_producer_manifest(root)
    entrypoints = [
        _budget_relative_path(value, label="producer entrypoint")
        for value in manifest["python_entrypoints"]
    ]
    declared_closure = [
        _budget_relative_path(value, label="producer import closure")
        for value in manifest["python_import_closure"]
    ]
    actual_closure = _budget_import_closure(
        root,
        entrypoints,
        declared_dynamic_imports=manifest.get("dynamic_imports", []),
    )
    if actual_closure != sorted(declared_closure):
        missing = sorted(set(actual_closure) - set(declared_closure))
        extra = sorted(set(declared_closure) - set(actual_closure))
        details = []
        if missing:
            details.append("missing=" + ",".join(path.as_posix() for path in missing))
        if extra:
            details.append("extra=" + ",".join(path.as_posix() for path in extra))
        raise PortableFamilyError(
            "producer import closure differs from reviewed manifest"
            + (f" ({'; '.join(details)})" if details else "")
        )
    schema_inputs = [
        _budget_relative_path(value, label="producer schema input")
        for value in manifest["schema_inputs"]
    ]
    manifest_paths = [
        *actual_closure,
        *schema_inputs,
        BUDGET_RECEIPT_PRODUCER_MANIFEST_PATH,
        BUDGET_RECEIPT_PRODUCER_MANIFEST_SCHEMA_PATH,
        BUDGET_PRODUCER_ACTION_PATH,
    ]
    unique_paths = sorted(set(manifest_paths))
    files = [_budget_producer_file_entry(root, relative) for relative in unique_paths]
    action = next(
        entry for entry in files if entry["path"] == BUDGET_PRODUCER_ACTION_PATH.as_posix()
    )
    procedure_manifest = {
        "manifest_path": BUDGET_RECEIPT_PRODUCER_MANIFEST_PATH.as_posix(),
        "manifest_digest": sha256_bytes(manifest_raw),
        "schema_path": BUDGET_RECEIPT_PRODUCER_MANIFEST_SCHEMA_PATH.as_posix(),
        "closure_mode": manifest["closure_mode"],
        "dynamic_import_policy": manifest["dynamic_import_policy"],
        "dynamic_imports": copy.deepcopy(manifest.get("dynamic_imports", [])),
        "python_entrypoints": [path.as_posix() for path in entrypoints],
        "python_import_closure": [path.as_posix() for path in actual_closure],
        "schema_inputs": [path.as_posix() for path in schema_inputs],
        "action_path": BUDGET_PRODUCER_ACTION_PATH.as_posix(),
        "action_inputs": copy.deepcopy(manifest["action_inputs"]),
        "environment": copy.deepcopy(manifest["environment"]),
        "dependencies": copy.deepcopy(manifest["dependencies"]),
    }
    source_digest = sha256_bytes(canonical_json_bytes(files))
    identity_material = {
        "contract_version": BUDGET_PRODUCER_IDENTITY_VERSION,
        "owner": "aoa-kag",
        "revision_binding": (
            "content-addressed-procedure-import-closure-portable-runtime-"
            "contract-and-descriptor-io-v1"
        ),
        "source_digest": source_digest,
        "procedure_manifest": procedure_manifest,
        "action": action,
        "execution_inputs": copy.deepcopy(dict(producer_execution_inputs)),
    }
    return {
        **identity_material,
        "files": files,
        "identity_digest": sha256_bytes(canonical_json_bytes(identity_material)),
    }


def _budget_is_receipt_control_path(relative: Path) -> bool:
    return (
        Path("kag/indexes") in (relative, *relative.parents)
        or relative in {
            Path("kag/indexes/corpus.manifest.json"),
            Path("kag/indexes/hot_profile.json"),
            Path("kag/indexes/artifact_locators.json"),
        }
        or Path("kag/indexes/shards") in (relative, *relative.parents)
        or BUDGET_RECEIPT_ROOT_RELATIVE_PATH in (relative, *relative.parents)
    )


def _budget_filesystem_source_epoch_files(
    root: Path,
) -> tuple[str, list[dict[str, Any]]]:
    entries: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        if not path.is_file() and not path.is_symlink():
            continue
        relative = path.relative_to(root)
        if _budget_is_receipt_control_path(relative):
            continue
        metadata = path.lstat()
        if stat.S_ISREG(metadata.st_mode):
            content = path.read_bytes()
            kind = "file"
            mode = "0755" if metadata.st_mode & stat.S_IXUSR else "0644"
        elif stat.S_ISLNK(metadata.st_mode):
            content = os.readlink(path).encode("utf-8", errors="surrogateescape")
            kind = "symlink"
            mode = "0777"
        else:
            continue
        entries.append(
            {
                "path": relative.as_posix(),
                "mode": mode,
                "kind": kind,
                "bytes": len(content),
                "content_digest": sha256_bytes(content),
            }
        )
    return "nogit", sorted(entries, key=lambda item: item["path"])


def _budget_git_nul_paths(root: Path, *arguments: str) -> set[Path]:
    result = subprocess.run(
        ("git", *arguments, "-z"),
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise PortableFamilyError("source epoch requires a readable Git worktree")
    paths: set[Path] = set()
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            relative = Path(raw.decode("utf-8", errors="strict"))
        except UnicodeDecodeError as exc:
            raise PortableFamilyError("source epoch encountered a non-UTF-8 path") from exc
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            raise PortableFamilyError("source epoch encountered an unsafe path")
        paths.add(relative)
    return paths


def _budget_source_epoch_index_entries(
    root: Path,
) -> dict[Path, dict[str, str]]:
    raw = subprocess.run(
        ("git", "ls-files", "-s", "--cached", "-z"),
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    entries: dict[Path, dict[str, str]] = {}
    for item in raw.split(b"\0"):
        if not item:
            continue
        metadata, separator, path_bytes = item.partition(b"\t")
        fields = metadata.split(b" ")
        if not separator or len(fields) != 3:
            raise PortableFamilyError("source epoch found a malformed Git index entry")
        try:
            mode, blob_id, stage = (field.decode("ascii") for field in fields)
            relative = Path(path_bytes.decode("utf-8", errors="strict"))
        except UnicodeDecodeError as exc:
            raise PortableFamilyError(
                "source epoch found a non-UTF-8 Git index entry"
            ) from exc
        if (
            stage != "0"
            or relative.is_absolute()
            or not relative.parts
            or ".." in relative.parts
        ):
            raise PortableFamilyError(
                f"source epoch found an unstable Git index entry: {relative}"
            )
        entries[relative] = {"mode": mode, "blob_id": blob_id}
    return entries


def _budget_worktree_source_epoch_files(
    root: Path,
    *,
    index_entries: Mapping[Path, Mapping[str, str]],
) -> list[dict[str, Any]]:
    """Read the effective candidate without mutating its Git index.

    Generation may run against a caller candidate that has staged, unstaged,
    or non-ignored untracked source.  The regular admission path remains
    clean-source-only; this candidate path binds the epoch to the bytes that
    are actually visible in the materialized worktree so preparation can
    regenerate a family before the caller commits the candidate.
    """
    paths = set(index_entries)
    paths.update(
        _budget_git_nul_paths(
            root,
            "ls-files",
            "--others",
            "--exclude-standard",
        )
    )
    entries: list[dict[str, Any]] = []
    for relative in sorted(paths):
        if _budget_is_receipt_control_path(relative):
            continue
        path = root / relative
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            # A deleted tracked source is absent from the effective candidate
            # and therefore must not survive into the candidate epoch.
            continue
        if index_entries.get(relative, {}).get("mode") == "160000":
            entries.append(
                {
                    "path": relative.as_posix(),
                    "mode": "160000",
                    "blob_id": index_entries[relative]["blob_id"],
                    "kind": "gitlink",
                }
            )
            continue
        if stat.S_ISREG(metadata.st_mode):
            content = path.read_bytes()
            kind = "file"
            mode = "100755" if metadata.st_mode & stat.S_IXUSR else "100644"
        elif stat.S_ISLNK(metadata.st_mode):
            content = os.readlink(path).encode("utf-8", errors="surrogateescape")
            kind = "symlink"
            mode = "120000"
        elif stat.S_ISDIR(metadata.st_mode) and (
            (path / ".git").exists()
            or (path / ".git").is_file()
        ):
            # Nested validation checkouts are candidate context, not outer
            # owner source. Their own identity is handled by preparation.
            continue
        else:
            raise PortableFamilyError(
                f"source epoch found a non-file source path: {relative.as_posix()}"
            )
        entries.append(
            {
                "path": relative.as_posix(),
                "mode": mode,
                "kind": kind,
                "bytes": len(content),
                "content_digest": sha256_bytes(content),
            }
        )
    return sorted(entries, key=lambda item: item["path"])


def _budget_source_epoch_files(
    root: Path,
    *,
    allow_dirty: bool = False,
) -> tuple[str, list[dict[str, Any]]]:
    try:
        head = subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return _budget_filesystem_source_epoch_files(root)
    try:
        staged = _budget_git_nul_paths(root, "diff", "--name-only", "--cached")
        unstaged = _budget_git_nul_paths(root, "diff", "--name-only")
        untracked = _budget_git_nul_paths(
            root,
            "ls-files",
            "--others",
            "--exclude-standard",
        )
        dirty = {
            path
            for path in staged | unstaged | untracked
            if not _budget_is_receipt_control_path(path)
        }
        if dirty and not allow_dirty:
            raise PortableFamilyError(
                "source epoch is not clean; source drift is present at: "
                + ", ".join(path.as_posix() for path in sorted(dirty))
            )
        if allow_dirty and dirty:
            return head, _budget_worktree_source_epoch_files(
                root,
                index_entries=_budget_source_epoch_index_entries(root),
            )
        raw = subprocess.run(
            ("git", "ls-files", "-s", "--cached", "-z"),
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout
        entries: list[dict[str, Any]] = []
        for item in raw.split(b"\0"):
            if not item:
                continue
            metadata, separator, path_bytes = item.partition(b"\t")
            fields = metadata.split(b" ")
            if not separator or len(fields) != 3:
                raise PortableFamilyError("source epoch found a malformed Git index entry")
            mode, blob_id, stage = (field.decode("ascii") for field in fields)
            relative = Path(path_bytes.decode("utf-8", errors="strict"))
            if stage != "0" or relative.is_absolute() or ".." in relative.parts:
                raise PortableFamilyError(
                    f"source epoch found an unstable Git index entry: {relative}"
                )
            if _budget_is_receipt_control_path(relative):
                continue
            path = root / relative
            metadata = path.lstat()
            if mode == "160000":
                entries.append(
                    {
                        "path": relative.as_posix(),
                        "mode": mode,
                        "blob_id": blob_id,
                        "kind": "gitlink",
                    }
                )
                continue
            if stat.S_ISREG(metadata.st_mode):
                content = path.read_bytes()
                kind = "file"
            elif stat.S_ISLNK(metadata.st_mode):
                content = os.readlink(path).encode("utf-8", errors="surrogateescape")
                kind = "symlink"
            else:
                raise PortableFamilyError(
                    f"source epoch found a non-file source path: {relative.as_posix()}"
                )
            expected_kind = "symlink" if mode == "120000" else "file"
            if kind != expected_kind:
                raise PortableFamilyError(
                    f"source epoch mode changed for {relative.as_posix()}"
                )
            entries.append(
                {
                    "path": relative.as_posix(),
                    "mode": mode,
                    "kind": kind,
                    "bytes": len(content),
                    "content_digest": sha256_bytes(content),
                }
            )
        return head, sorted(entries, key=lambda item: item["path"])
    except subprocess.CalledProcessError as exc:
        raise PortableFamilyError("source epoch cannot inspect the Git worktree") from exc


def capture_budget_source_epoch(
    repo_root: Path,
    *,
    allow_dirty: bool = False,
) -> str:
    """Capture a source epoch, optionally from an effective dirty candidate."""
    root = repo_root.resolve()
    _head, files = _budget_source_epoch_files(root, allow_dirty=allow_dirty)
    return "sha256:" + sha256_bytes(
        canonical_json_bytes(
            {
                "contract_version": BUDGET_SOURCE_EPOCH_VERSION,
                "files": files,
            }
        )
    )


def _budget_require_source_epoch(
    repo_root: Path,
    expected: str | None = None,
    *,
    allow_dirty: bool = False,
) -> str:
    actual = capture_budget_source_epoch(repo_root, allow_dirty=allow_dirty)
    if expected is not None and actual != expected:
        raise PortableFamilyError(
            "source epoch changed between generation and receipt construction"
        )
    return actual


def _budget_candidate_file_inventory(
    repo_root: Path,
    *,
    excluded_path: Path,
) -> list[dict[str, Any]]:
    root = repo_root.resolve()
    _budget_confined_receipt_path(root, excluded_path, allow_missing=True)
    result = subprocess.run(
        ("git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"),
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise PortableFamilyError(
            "candidate identity requires a readable Git worktree"
        )
    try:
        index_entries = _budget_source_epoch_index_entries(root)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise PortableFamilyError(
            "candidate identity requires a readable Git index"
        ) from exc
    relative_paths: set[str] = set()
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            relative = Path(raw.decode("utf-8", errors="strict"))
        except UnicodeDecodeError as exc:
            raise PortableFamilyError(
                "candidate identity encountered a non-UTF-8 Git path"
            ) from exc
        if (
            relative.is_absolute()
            or not relative.parts
            or ".." in relative.parts
        ):
            raise PortableFamilyError("candidate identity encountered an unsafe path")
        relative_text = relative.as_posix()
        if relative == excluded_path:
            continue
        relative_paths.add(relative_text)

    inventory: list[dict[str, Any]] = []
    for relative_text in sorted(relative_paths):
        relative = Path(relative_text)
        path = root / relative
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            # A deleted tracked path can still be listed by ``git ls-files
            # --cached`` until the deletion is committed.  Candidate identity
            # is bound to the effective worktree, so the absent path must stay
            # absent across the dirty-to-commit boundary instead of changing
            # from a ``missing`` record to no record at all.
            continue
        index_entry = index_entries.get(relative)
        if index_entry is not None and index_entry.get("mode") == "160000":
            # A materialized submodule is a directory in the worktree, but its
            # candidate identity is the commit object recorded by the parent
            # index. Do not recurse into the nested checkout or hash ambient
            # files that are outside the parent candidate.
            gitlink_commit = index_entry.get("blob_id")
            if not isinstance(gitlink_commit, str) or not gitlink_commit:
                raise PortableFamilyError(
                    f"candidate identity has an invalid Gitlink entry {relative_text}"
                )
            inventory.append(
                {
                    "path": relative_text,
                    "state": "present",
                    "kind": "gitlink",
                    "mode": "160000",
                    "bytes": 0,
                    "content_digest": sha256_bytes(
                        gitlink_commit.encode("ascii")
                    ),
                    "gitlink_commit": gitlink_commit,
                }
            )
            continue
        if stat.S_ISREG(metadata.st_mode):
            content = path.read_bytes()
            kind = "file"
            mode = "0755" if metadata.st_mode & stat.S_IXUSR else "0644"
        elif stat.S_ISLNK(metadata.st_mode):
            target = os.readlink(path).encode("utf-8", errors="surrogateescape")
            content = target
            kind = "symlink"
            mode = "0777"
        else:
            raise PortableFamilyError(
                f"candidate identity cannot inventory non-file path {relative_text}"
            )
        inventory.append(
            {
                "path": relative_text,
                "state": "present",
                "kind": kind,
                "mode": mode,
                "bytes": len(content),
                "content_digest": sha256_bytes(content),
            }
        )
    return inventory


def _budget_candidate_identity(
    repo_root: Path,
    *,
    resolved_base_ref: str,
    manifest: Mapping[str, Any],
    source_epoch: str | None = None,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    family_identity = manifest.get("family_identity")
    if not isinstance(family_identity, Mapping):
        raise PortableFamilyError("budget candidate needs family identity")
    family_digest = family_identity.get("content_digest")
    source_snapshot = family_identity.get("source_snapshot")
    if isinstance(family_digest, str):
        family_digest = family_digest.removeprefix("sha256:")
    if (
        not isinstance(family_digest, str)
        or len(family_digest) != 64
        or any(character not in HEX_DIGITS for character in family_digest)
        or not isinstance(source_snapshot, str)
        or not source_snapshot.startswith("sha256:")
    ):
        raise PortableFamilyError(
            "budget candidate needs content-addressed family and source identities"
        )
    actual_source_epoch = _budget_require_source_epoch(
        repo_root,
        source_epoch,
        allow_dirty=allow_dirty,
    )
    excluded_path = receipt_path_for(manifest)
    inventory = _budget_candidate_file_inventory(
        repo_root,
        excluded_path=excluded_path,
    )
    seal_material = {
        "contract_version": BUDGET_CANDIDATE_IDENTITY_VERSION,
        "algorithm": BUDGET_CANDIDATE_SEAL_ALGORITHM,
        "excluded_path": excluded_path.as_posix(),
        "files": inventory,
    }
    return {
        "contract_version": BUDGET_CANDIDATE_IDENTITY_VERSION,
        "algorithm": BUDGET_CANDIDATE_SEAL_ALGORITHM,
        "seal": sha256_bytes(canonical_json_bytes(seal_material)),
        "file_count": len(inventory),
        "excluded_path": excluded_path.as_posix(),
        "base_ref": resolved_base_ref,
        "family_digest": family_digest,
        "source_snapshot": source_snapshot,
        "source_epoch": actual_source_epoch,
    }


def _budget_receipt_identities(
    repo_root: Path,
    *,
    resolved_base_ref: str,
    manifest: Mapping[str, Any],
    source_epoch: str | None = None,
    producer_execution_inputs: Mapping[str, Any] | None = None,
    allow_dirty: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    actual_source_epoch = _budget_require_source_epoch(
        repo_root,
        source_epoch,
        allow_dirty=allow_dirty,
    )
    if producer_execution_inputs is None:
        producer_execution_inputs = capture_budget_producer_execution_inputs(
            repo_root,
            base_ref=resolved_base_ref,
        )
    return (
        _budget_candidate_identity(
            repo_root,
            resolved_base_ref=resolved_base_ref,
            manifest=manifest,
            source_epoch=actual_source_epoch,
            allow_dirty=allow_dirty,
        ),
        _budget_producer_identity(producer_execution_inputs),
    )


def effective_index_surface_record(
    manifest: Mapping[str, Any],
    *,
    repo: str,
) -> dict[str, object]:
    """Project a portable-only family manifest as one effective index surface."""
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise PortableFamilyError(
            "effective index surface requires a v3 portable family manifest"
        )
    family_identity = manifest.get("family_identity")
    source_index_header = manifest.get("source_index_header")
    if not isinstance(family_identity, Mapping) or not isinstance(
        source_index_header,
        Mapping,
    ):
        raise PortableFamilyError(
            "portable family manifest needs family and source index identity"
        )
    index_identity = source_index_header.get("index_identity")
    if not isinstance(index_identity, Mapping):
        raise PortableFamilyError(
            "portable family manifest needs source_index_header.index_identity"
        )
    local_id = index_identity.get("local_id")
    content_digest = family_identity.get("content_digest")
    if not isinstance(local_id, str) or not local_id:
        raise PortableFamilyError(
            "portable family source index identity needs local_id"
        )
    if not isinstance(content_digest, str) or not content_digest:
        raise PortableFamilyError(
            "portable family identity needs content_digest"
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "repo": repo,
        "local_id": local_id,
        "record_class": "index",
        "generated_or_authored": "generated_from_source",
        "builder": {
            "route": "repo-local KAG portable family",
            "surface": MANIFEST_RELATIVE_PATH.as_posix(),
        },
        "effective_index_surface": "portable_family_manifest",
        "portable_family_content_digest": content_digest,
    }


def canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def render_manifest(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def render_row(payload: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(payload) + b"\n"


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def manifest_digest(payload: Mapping[str, Any]) -> str:
    candidate = copy.deepcopy(dict(payload))
    identity = candidate.get("family_identity")
    if not isinstance(identity, dict):
        raise PortableFamilyError("portable family manifest needs family_identity")
    identity["content_digest"] = ZERO_DIGEST
    return sha256_bytes(canonical_json_bytes(candidate))


def is_portable_control_path(path: Path) -> bool:
    return (
        path == MANIFEST_RELATIVE_PATH
        or path in TIERED_CONTROL_PATHS
        or SHARD_ROOT_RELATIVE_PATH in (path, *path.parents)
        or BUDGET_RECEIPT_ROOT_RELATIVE_PATH in (path, *path.parents)
    )


def _row_key(row: Mapping[str, Any]) -> str:
    value = row.get("_key")
    if not isinstance(value, str) or not value:
        raise PortableFamilyError("portable record needs a non-empty _key")
    return value


def _row_kind(row: Mapping[str, Any]) -> str:
    value = row.get("_kind")
    if not isinstance(value, str) or not value:
        raise PortableFamilyError("portable record needs a non-empty _kind")
    return value


def _chunk_large_row(
    row: dict[str, Any],
    *,
    parent_kind: str,
    chunkable_fields: Sequence[str],
) -> list[dict[str, Any]]:
    if len(render_row(row)) <= MAX_RECORD_BYTES:
        return [row]
    parent_key = _row_key(row)
    core = copy.deepcopy(row)
    chunked_fields: list[str] = []
    chunks: list[dict[str, Any]] = []
    for field in chunkable_fields:
        values = core.get(field)
        if not isinstance(values, list) or not values:
            continue
        core[field] = []
        chunked_fields.append(field)
        batch: list[Any] = []
        position = 0
        for value in values:
            candidate = [*batch, copy.deepcopy(value)]
            probe = {
                "_kind": f"{parent_kind}_chunk",
                "_key": f"{parent_key}:{field}:{position}",
                "parent": parent_key,
                "field": field,
                "position": position,
                "values": candidate,
            }
            if batch and len(render_row(probe)) > CHUNK_TARGET_BYTES:
                chunks.append(
                    {
                        "_kind": f"{parent_kind}_chunk",
                        "_key": f"{parent_key}:{field}:{position}",
                        "parent": parent_key,
                        "field": field,
                        "position": position,
                        "values": batch,
                    }
                )
                position += 1
                batch = [copy.deepcopy(value)]
            else:
                batch = candidate
        if batch:
            chunks.append(
                {
                    "_kind": f"{parent_kind}_chunk",
                    "_key": f"{parent_key}:{field}:{position}",
                    "parent": parent_key,
                    "field": field,
                    "position": position,
                    "values": batch,
                }
            )
    core["_chunked"] = chunked_fields
    expanded = [core, *chunks]
    oversized = [
        (_row_key(candidate), len(render_row(candidate)))
        for candidate in expanded
        if len(render_row(candidate)) > MAX_RECORD_BYTES
    ]
    if oversized:
        key, size = oversized[0]
        raise PortableFamilyError(
            f"portable record {key} is {size} bytes; maximum is "
            f"{MAX_RECORD_BYTES}"
        )
    return expanded


def _portable_rows(
    source_index: Mapping[str, Any],
    family: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_records = source_index.get("records")
    if not isinstance(source_records, list):
        raise PortableFamilyError("source index must carry records")
    for source in source_records:
        if not isinstance(source, dict):
            raise PortableFamilyError("source records must be objects")
        identity = source.get("identity")
        if not isinstance(identity, dict) or not isinstance(identity.get("id"), str):
            raise PortableFamilyError("source record needs identity.id")
        key = f"source:{identity['id']}"
        rows.extend(
            _chunk_large_row(
                {"_kind": "source", "_key": key, **copy.deepcopy(source)},
                parent_kind="source",
                chunkable_fields=(),
            )
        )

    anchor_payload = family.get("anchor")
    anchor_entries = (
        anchor_payload.get("entries") if isinstance(anchor_payload, Mapping) else None
    )
    if not isinstance(anchor_entries, list):
        raise PortableFamilyError("repository family must carry anchor entries")
    for source_anchor in anchor_entries:
        if not isinstance(source_anchor, dict):
            raise PortableFamilyError("anchor entries must be objects")
        anchor = copy.deepcopy(source_anchor)
        source_id = anchor.pop("source_record_id", None)
        anchor_id = anchor.get("id")
        if not isinstance(source_id, str) or not isinstance(anchor_id, str):
            raise PortableFamilyError("anchor needs id and source_record_id")
        for field, expected in ANCHOR_DEFAULTS.items():
            if anchor.pop(field, None) != expected:
                raise PortableFamilyError(
                    f"anchor {anchor_id} has non-canonical {field}"
                )
        key = f"anchor:{source_id}:{anchor_id}"
        rows.extend(
            _chunk_large_row(
                {
                    "_kind": "anchor",
                    "_key": key,
                    "source_id": source_id,
                    **anchor,
                },
                parent_kind="anchor",
                chunkable_fields=CHUNKABLE_FIELDS["anchor"],
            )
        )

    event_payload = family.get("event")
    event_entries = (
        event_payload.get("entries") if isinstance(event_payload, Mapping) else None
    )
    if not isinstance(event_entries, list):
        raise PortableFamilyError("repository family must carry event entries")
    for source_event in event_entries:
        if not isinstance(source_event, dict) or not isinstance(
            source_event.get("id"), str
        ):
            raise PortableFamilyError("event entries must carry id")
        key = f"event:{source_event['id']}"
        rows.extend(
            _chunk_large_row(
                {"_kind": "event", "_key": key, **copy.deepcopy(source_event)},
                parent_kind="event",
                chunkable_fields=CHUNKABLE_FIELDS["event"],
            )
        )

    keys = [_row_key(row) for row in rows]
    if len(keys) != len(set(keys)):
        raise PortableFamilyError("portable record keys must be unique")
    return sorted(rows, key=lambda row: (_row_kind(row), _row_key(row)))


def _initial_ranges() -> list[str]:
    return list(HEX_DIGITS)


def _previous_ranges(
    previous_manifest: Mapping[str, Any] | None,
    kind: str,
) -> list[str]:
    if previous_manifest is None:
        return []
    partitioning = previous_manifest.get("partitioning")
    ranges = (
        partitioning.get("ranges")
        if isinstance(partitioning, Mapping)
        else None
    )
    values = ranges.get(kind) if isinstance(ranges, Mapping) else None
    if not isinstance(values, list) or not all(
        isinstance(value, str) and value for value in values
    ):
        return []
    return sorted(set(values), key=lambda value: (len(value), value))


def _range_for_hash(digest: str, ranges: Sequence[str]) -> str:
    matches = [prefix for prefix in ranges if digest.startswith(prefix)]
    if not matches:
        raise PortableFamilyError(
            f"partition ranges do not cover digest {digest}"
        )
    return max(matches, key=len)


def _split_ranges(
    rows: Sequence[dict[str, Any]],
    *,
    ranges: Sequence[str],
    threshold: int,
) -> tuple[list[str], dict[str, list[dict[str, Any]]]]:
    leaves = set(ranges or _initial_ranges())
    encoded = {
        _row_key(row): render_row(row)
        for row in rows
    }
    hashes = {
        key: sha256_bytes(key.encode("utf-8"))
        for key in encoded
    }
    while True:
        buckets: dict[str, list[dict[str, Any]]] = {
            prefix: [] for prefix in leaves
        }
        for row in rows:
            key = _row_key(row)
            buckets[_range_for_hash(hashes[key], tuple(leaves))].append(row)
        oversized = [
            prefix
            for prefix, bucket in buckets.items()
            if sum(len(encoded[_row_key(row)]) for row in bucket) > threshold
        ]
        if not oversized:
            return (
                sorted(leaves, key=lambda value: (len(value), value)),
                buckets,
            )
        for prefix in oversized:
            if len(prefix) >= 64:
                raise PortableFamilyError(
                    f"cannot split oversized portable shard {prefix}"
                )
            leaves.remove(prefix)
            leaves.update(f"{prefix}{digit}" for digit in HEX_DIGITS)


def _compatibility_files(
    source_index: Mapping[str, Any],
    family: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for kind in COMPATIBILITY_ORDER:
        payload = source_index if kind == "source" else family[kind]
        identity = payload.get("index_identity")
        if not isinstance(identity, Mapping):
            raise PortableFamilyError(f"{kind} compatibility view needs identity")
        collection = payload.get("records" if kind == "source" else "entries")
        if not isinstance(collection, list):
            raise PortableFamilyError(f"{kind} compatibility view needs records")
        content_digest = identity.get("content_digest")
        if not isinstance(content_digest, str):
            raise PortableFamilyError(
                f"{kind} compatibility view needs content digest"
            )
        files.append(
            {
                "kind": kind,
                "path": (
                    Path("kag/indexes") / LEGACY_INDEX_FILENAMES[kind]
                ).as_posix(),
                "schema_version": payload.get("schema_version"),
                "content_digest": content_digest,
                "records": len(collection),
            }
        )
    return files


def _baseline_cap(tracked_bytes: int) -> int:
    rounded = math.ceil(
        (tracked_bytes * BASELINE_HEADROOM) / (1024 * 1024)
    ) * 1024 * 1024
    return min(
        GLOBAL_TRACKED_BYTES_MAX,
        max(MIN_BASELINE_BYTES, rounded),
    )


def _preserved_tracked_cap(
    previous_manifest: Mapping[str, Any] | None,
) -> int | None:
    budgets = (
        previous_manifest.get("budgets")
        if isinstance(previous_manifest, Mapping)
        else None
    )
    value = (
        budgets.get("tracked_bytes_max")
        if isinstance(budgets, Mapping)
        else None
    )
    if isinstance(value, int) and 0 < value <= GLOBAL_TRACKED_BYTES_MAX:
        return value
    return None


def build_portable_family(
    source_index: Mapping[str, Any],
    family: Mapping[str, Mapping[str, Any]],
    *,
    previous_manifest: Mapping[str, Any] | None = None,
    manifest_path: Path = MANIFEST_RELATIVE_PATH,
) -> tuple[dict[str, Any], dict[Path, bytes]]:
    rows = _portable_rows(source_index, family)
    rows_by_kind: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        rows_by_kind.setdefault(_row_kind(row), []).append(row)

    ranges_by_kind: dict[str, list[str]] = {}
    shard_bytes: dict[Path, bytes] = {}
    shard_descriptors: list[dict[str, Any]] = []
    for kind, kind_rows in sorted(rows_by_kind.items()):
        previous_ranges = _previous_ranges(previous_manifest, kind)
        ranges, buckets = _split_ranges(
            kind_rows,
            ranges=previous_ranges or _initial_ranges(),
            threshold=(
                HARD_MAX_SHARD_BYTES
                if previous_ranges
                else TARGET_SHARD_BYTES
            ),
        )
        ranges_by_kind[kind] = ranges
        for prefix in ranges:
            bucket = sorted(buckets[prefix], key=_row_key)
            if not bucket:
                continue
            content = b"".join(render_row(row) for row in bucket)
            if len(content) > HARD_MAX_SHARD_BYTES:
                raise PortableFamilyError(
                    f"portable shard {kind}/{prefix} is {len(content)} bytes"
                )
            path = (
                manifest_path.parent
                / "shards"
                / kind
                / f"{prefix}.jsonl"
            )
            shard_bytes[path] = content
            shard_descriptors.append(
                {
                    "kind": kind,
                    "range": prefix,
                    "path": path.as_posix(),
                    "digest": f"sha256:{sha256_bytes(content)}",
                    "bytes": len(content),
                    "records": len(bucket),
                }
            )

    source_header = copy.deepcopy(dict(source_index))
    source_records = source_header.pop("records", None)
    if not isinstance(source_records, list):
        raise PortableFamilyError("source index records are required")
    repo = source_index.get("repo")
    source_identity = source_index.get("index_identity")
    if not isinstance(repo, Mapping) or not isinstance(source_identity, Mapping):
        raise PortableFamilyError("source index repo and identity are required")
    source_digest = source_identity.get("content_digest")
    if not isinstance(source_digest, str):
        raise PortableFamilyError("source index content digest is required")

    preserved_cap = _preserved_tracked_cap(previous_manifest)
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "repo": copy.deepcopy(dict(repo)),
        "family_identity": {
            "local_id": "family:repo-local:portable-record-corpus",
            "artifact_kind": "repo_local_kag_portable_family",
            "content_digest": ZERO_DIGEST,
            "schema_ref": SCHEMA_REF,
            "source_snapshot": f"sha256:{source_digest}",
        },
        "partitioning": {
            "algorithm": "sha256-record-key-adaptive-prefix",
            "target_shard_bytes": TARGET_SHARD_BYTES,
            "hard_max_shard_bytes": HARD_MAX_SHARD_BYTES,
            "max_record_bytes": MAX_RECORD_BYTES,
            "split_policy": "prefix-split-only",
            "merge_policy": "never-automatic",
            "ranges": ranges_by_kind,
        },
        "normalization": {
            "canonical_record_classes": [
                "source",
                "anchor",
                "event",
            ],
            "derived_compatibility_classes": [
                "artifact",
                "entity",
                "assertion",
                "relation",
            ],
            "anchor_defaults": copy.deepcopy(ANCHOR_DEFAULTS),
            "chunking": {
                "strategy": "oversize-list-content-chunks",
                "chunk_target_bytes": CHUNK_TARGET_BYTES,
                "chunkable_fields": {
                    kind: list(fields)
                    for kind, fields in CHUNKABLE_FIELDS.items()
                },
            },
        },
        "source_index_header": source_header,
        "compatibility": {
            "view": "aoa-repo-local-kag-v2",
            "assembly": "deterministic-on-demand",
            "files": _compatibility_files(source_index, family),
        },
        "budgets": {
            "tracked_bytes_max": (
                preserved_cap
                if preserved_cap is not None
                else GLOBAL_TRACKED_BYTES_MAX
            ),
            "changed_generated_bytes_max": DEFAULT_DELTA_BYTES_MAX,
            "global_tracked_bytes_max": GLOBAL_TRACKED_BYTES_MAX,
            "exceedance_route": (
                BUDGET_RECEIPT_ROOT_RELATIVE_PATH.as_posix()
                + "/<family-digest>.json"
            ),
        },
        "summary": {
            "source_records": len(source_records),
            "anchor_records": len(family["anchor"]["entries"]),
            "event_records": len(family["event"]["entries"]),
            "canonical_records": len(rows),
            "shards": len(shard_descriptors),
            "shard_bytes": sum(len(content) for content in shard_bytes.values()),
            "tracked_bytes": 0,
        },
        "shards": sorted(
            shard_descriptors,
            key=lambda item: (item["kind"], len(item["range"]), item["range"]),
        ),
    }

    for _ in range(12):
        tracked = len(render_manifest(manifest)) + manifest["summary"]["shard_bytes"]
        if manifest["summary"]["tracked_bytes"] == tracked:
            break
        manifest["summary"]["tracked_bytes"] = tracked
    else:  # pragma: no cover - integer-width convergence guard
        raise PortableFamilyError("portable tracked byte count did not converge")

    if preserved_cap is None:
        manifest["budgets"]["tracked_bytes_max"] = _baseline_cap(
            manifest["summary"]["tracked_bytes"]
        )
        for _ in range(12):
            tracked = (
                len(render_manifest(manifest))
                + manifest["summary"]["shard_bytes"]
            )
            if manifest["summary"]["tracked_bytes"] == tracked:
                break
            manifest["summary"]["tracked_bytes"] = tracked
        else:  # pragma: no cover
            raise PortableFamilyError(
                "portable tracked byte count did not converge after baseline"
            )

    if (
        manifest["summary"]["tracked_bytes"]
        > manifest["budgets"]["global_tracked_bytes_max"]
    ):
        raise PortableFamilyError(
            "portable family tracked bytes exceed the global owner ceiling: "
            f"{manifest['summary']['tracked_bytes']} > "
            f"{manifest['budgets']['global_tracked_bytes_max']}"
        )
    manifest["family_identity"]["content_digest"] = manifest_digest(manifest)
    final_tracked = (
        len(render_manifest(manifest))
        + manifest["summary"]["shard_bytes"]
    )
    if final_tracked != manifest["summary"]["tracked_bytes"]:
        raise PortableFamilyError("portable tracked byte count changed after digest")
    return manifest, shard_bytes


def _validate_manifest_shape(manifest: object) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise PortableFamilyError("portable family manifest must be an object")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise PortableFamilyError(
            f"portable family schema must be {SCHEMA_VERSION}"
        )
    identity = manifest.get("family_identity")
    if not isinstance(identity, dict):
        raise PortableFamilyError("portable family needs family_identity")
    if identity.get("content_digest") != manifest_digest(manifest):
        raise PortableFamilyError("portable family manifest digest does not match")
    summary = manifest.get("summary")
    shards = manifest.get("shards")
    if not isinstance(summary, dict) or not isinstance(shards, list):
        raise PortableFamilyError("portable family needs summary and shards")
    return manifest


def _load_rows(
    repo_root: Path,
    manifest: Mapping[str, Any],
    *,
    require_budget_receipt: bool,
    producer_execution_inputs: Mapping[str, Any] | None = None,
    require_current_producer_identity: bool = True,
    allow_legacy_external_receipt: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    shards = manifest.get("shards")
    if not isinstance(shards, list):
        raise PortableFamilyError("portable family shards must be a list")
    shard_bytes = 0
    for descriptor in shards:
        if not isinstance(descriptor, dict):
            raise PortableFamilyError("portable shard descriptors must be objects")
        relative = descriptor.get("path")
        if not isinstance(relative, str):
            raise PortableFamilyError("portable shard path must be a string")
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise PortableFamilyError("portable shard path must stay in repository")
        content = (repo_root / path).read_bytes()
        digest = descriptor.get("digest")
        if digest != f"sha256:{sha256_bytes(content)}":
            raise PortableFamilyError(
                f"portable shard digest does not match: {relative}"
            )
        if descriptor.get("bytes") != len(content):
            raise PortableFamilyError(
                f"portable shard byte count does not match: {relative}"
            )
        shard_rows: list[dict[str, Any]] = []
        for line_number, line in enumerate(content.splitlines(), start=1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise PortableFamilyError(
                    f"{relative}:{line_number} is not valid JSON"
                ) from exc
            if not isinstance(row, dict):
                raise PortableFamilyError(
                    f"{relative}:{line_number} must be an object"
                )
            if _row_kind(row) != descriptor.get("kind"):
                raise PortableFamilyError(
                    f"{relative}:{line_number} record kind does not match shard"
                )
            if len(line) + 1 > MAX_RECORD_BYTES:
                raise PortableFamilyError(
                    f"{relative}:{line_number} exceeds record budget"
                )
            shard_rows.append(row)
        if descriptor.get("records") != len(shard_rows):
            raise PortableFamilyError(
                f"portable shard record count does not match: {relative}"
            )
        rows.extend(shard_rows)
        shard_bytes += len(content)
    keys = [_row_key(row) for row in rows]
    if len(keys) != len(set(keys)):
        raise PortableFamilyError("portable record keys must be unique")
    summary = manifest["summary"]
    if summary.get("canonical_records") != len(rows):
        raise PortableFamilyError("portable canonical record count does not match")
    if summary.get("shard_bytes") != shard_bytes:
        raise PortableFamilyError("portable shard byte total does not match")
    manifest_bytes = render_manifest(manifest)
    if summary.get("tracked_bytes") != len(manifest_bytes) + shard_bytes:
        raise PortableFamilyError("portable tracked byte total does not match")
    budgets = manifest.get("budgets")
    if not isinstance(budgets, dict):
        raise PortableFamilyError("portable family needs budgets")
    if budgets.get("global_tracked_bytes_max") != GLOBAL_TRACKED_BYTES_MAX:
        raise PortableFamilyError("portable global tracked byte budget drifted")
    if (
        require_budget_receipt
        and summary["tracked_bytes"] > budgets.get("tracked_bytes_max", -1)
    ):
        _validate_tracked_size_receipt(
            repo_root,
            manifest,
            producer_execution_inputs=producer_execution_inputs,
            require_current_producer_identity=require_current_producer_identity,
            allow_legacy_external_receipt=allow_legacy_external_receipt,
        )
    return rows


def _expanded_parents(
    rows: Sequence[dict[str, Any]],
    *,
    parent_kind: str,
) -> list[dict[str, Any]]:
    chunk_kind = f"{parent_kind}_chunk"
    parents = {
        _row_key(row): dict(row)
        for row in rows
        if _row_kind(row) == parent_kind
    }
    chunks_by_parent: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for row in rows:
        if _row_kind(row) != chunk_kind:
            continue
        parent = row.get("parent")
        field = row.get("field")
        position = row.get("position")
        values = row.get("values")
        if (
            not isinstance(parent, str)
            or not isinstance(field, str)
            or not isinstance(position, int)
            or not isinstance(values, list)
        ):
            raise PortableFamilyError(f"{chunk_kind} record is malformed")
        chunks_by_parent.setdefault(parent, {}).setdefault(field, []).append(row)
    for parent_key, fields in chunks_by_parent.items():
        parent = parents.get(parent_key)
        if parent is None:
            raise PortableFamilyError(
                f"portable chunk has no parent: {parent_key}"
            )
        declared = parent.get("_chunked")
        if not isinstance(declared, list):
            raise PortableFamilyError(
                f"portable parent does not declare chunks: {parent_key}"
            )
        for field, chunks in fields.items():
            if field not in declared:
                raise PortableFamilyError(
                    f"portable parent does not declare chunk field {field}"
                )
            positions = sorted(int(chunk["position"]) for chunk in chunks)
            if positions != list(range(len(positions))):
                raise PortableFamilyError(
                    f"portable chunks are not contiguous for {parent_key}:{field}"
                )
            parent[field] = [
                copy.deepcopy(value)
                for chunk in sorted(chunks, key=lambda item: item["position"])
                for value in chunk["values"]
            ]
        missing = set(declared) - set(fields)
        if missing:
            raise PortableFamilyError(
                f"portable parent is missing chunks for {sorted(missing)}"
            )
    return sorted(parents.values(), key=_row_key)


def _strip_portable_fields(row: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    payload.pop("_kind", None)
    payload.pop("_key", None)
    payload.pop("_chunked", None)
    return payload


def reconstruct_source_index(
    manifest: Mapping[str, Any],
    rows: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Reconstruct and verify the Git-hot source compatibility view.

    Tiered externalized checkouts retain every source record while
    artifact-cold anchor and event records may be absent. Source-fast
    consumers can therefore verify authored coverage without pretending that
    the complete seven-view family is hydrated.
    """
    source_rows = [
        _strip_portable_fields(row)
        for row in rows
        if _row_kind(row) == "source"
    ]
    source_rows.sort(key=lambda record: record["identity"]["path"])
    source_header = manifest.get("source_index_header")
    if not isinstance(source_header, dict):
        raise PortableFamilyError("portable family needs source_index_header")
    source_index = dict(source_header)
    source_index["records"] = source_rows

    compatibility = manifest.get("compatibility")
    files = (
        compatibility.get("files")
        if isinstance(compatibility, Mapping)
        else None
    )
    expected_source_digest = next(
        (
            item["content_digest"]
            for item in files or []
            if isinstance(item, dict)
            and item.get("kind") == "source"
            and isinstance(item.get("content_digest"), str)
        ),
        None,
    )
    identity = source_index.get("index_identity")
    if (
        not isinstance(identity, Mapping)
        or identity.get("content_digest") != expected_source_digest
    ):
        raise PortableFamilyError(
            "portable source compatibility digest does not match"
        )
    try:
        from scripts.generate_repo_local_kag_index import payload_digest
    except ImportError:  # pragma: no cover - direct script execution
        from generate_repo_local_kag_index import payload_digest  # type: ignore
    if identity.get("content_digest") != payload_digest(source_index):
        raise PortableFamilyError(
            "portable source compatibility content has drifted"
        )
    return source_index


def reconstruct_compatibility_family(
    manifest: Mapping[str, Any],
    rows: Sequence[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    source_index = reconstruct_source_index(manifest, rows)
    source_rows = source_index["records"]
    if not isinstance(source_rows, list):
        raise PortableFamilyError("portable source records must be a list")
    structure_records: list[dict[str, Any]] = []
    for source_record in source_rows:
        structure_record = dict(source_record)
        source_refs = source_record.get("refs")
        if not isinstance(source_refs, dict):
            raise PortableFamilyError("portable source refs must be an object")
        structure_refs = dict(source_refs)
        for field in ("anchor_refs", "outbound_refs"):
            value = source_refs.get(field)
            if isinstance(value, list):
                structure_refs[field] = list(value)
        structure_record["refs"] = structure_refs
        structure_records.append(structure_record)
    anchor_rows = _expanded_parents(rows, parent_kind="anchor")
    anchors: list[dict[str, Any]] = []
    records_by_id = {
        str(record["identity"]["id"]): record
        for record in structure_records
    }
    for row in anchor_rows:
        anchor = _strip_portable_fields(row)
        source_id = anchor.pop("source_id", None)
        if not isinstance(source_id, str) or source_id not in records_by_id:
            raise PortableFamilyError("portable anchor source does not resolve")
        anchor["source_record_id"] = source_id
        anchor.update(ANCHOR_DEFAULTS)
        anchors.append(anchor)
        raw_anchor = copy.deepcopy(anchor)
        parser_ref = raw_anchor.pop("parser_ref", None)
        if not isinstance(parser_ref, str) or "@" not in parser_ref:
            raise PortableFamilyError("portable anchor parser_ref is invalid")
        parser_name, parser_version = parser_ref.rsplit("@", 1)
        raw_anchor["parser"] = {
            "name": parser_name,
            "version": parser_version,
        }
        raw_anchor.pop("source_record_id", None)
        for field in ANCHOR_DEFAULTS:
            raw_anchor.pop(field, None)
        outbound = raw_anchor.pop("outbound_refs", [])
        refs = records_by_id[source_id].get("refs")
        if not isinstance(refs, dict):
            raise PortableFamilyError("portable source refs must be an object")
        refs.setdefault("anchor_refs", []).append(raw_anchor)
        refs.setdefault("outbound_refs", []).extend(
            {
                **copy.deepcopy(reference),
                "source_anchor_id": str(raw_anchor["id"]),
            }
            for reference in outbound
        )
    anchors.sort(
        key=lambda item: (
            item["source_record_id"],
            item["locator"]["start_line"],
            item["id"],
        )
    )
    for record in structure_records:
        refs = record["refs"]
        refs.setdefault("anchor_refs", [])
        refs.setdefault("outbound_refs", [])
        refs["anchor_refs"].sort(
            key=lambda item: (
                item["locator"]["start_line"],
                item["id"],
            )
        )
        refs["outbound_refs"].sort(
            key=lambda item: (
                item["source_anchor_id"],
                item["relation_kind"],
                item["target_ref"],
            )
        )

    event_rows = _expanded_parents(rows, parent_kind="event")
    events = [_strip_portable_fields(row) for row in event_rows]
    events.sort(key=lambda entry: (entry["event_kind"], entry["id"]))

    try:
        from scripts.generate_repo_local_kag_index import (
            DEFAULT_OUTPUT,
            repository_index_payload,
        )
        from scripts.repo_local.indexes import (
            artifact_entries,
            assertion_entries,
            entity_entries,
            relation_entries,
        )
    except ImportError:  # pragma: no cover - direct script execution
        from generate_repo_local_kag_index import (  # type: ignore
            DEFAULT_OUTPUT,
            repository_index_payload,
        )
        from repo_local.indexes import (  # type: ignore
            artifact_entries,
            assertion_entries,
            entity_entries,
            relation_entries,
        )

    repo = str(source_index["repo"]["name"])
    artifacts = artifact_entries(structure_records)
    entities = entity_entries(repo, structure_records)
    assertions = assertion_entries(
        repo,
        structure_records,
        artifacts=artifacts,
    )
    relations = relation_entries(
        repo,
        structure_records,
        artifacts=artifacts,
        anchors=anchors,
        entities=entities,
    )
    entries = {
        "artifact": artifacts,
        "anchor": anchors,
        "entity": entities,
        "event": events,
        "assertion": assertions,
        "relation": relations,
    }
    family = {
        kind: repository_index_payload(
            source_index,
            index_kind=kind,
            entries=entries[kind],
            source_index_path=DEFAULT_OUTPUT,
        )
        for kind in (
            "entity",
            "artifact",
            "anchor",
            "event",
            "assertion",
            "relation",
        )
    }
    compatibility = manifest.get("compatibility")
    files = (
        compatibility.get("files")
        if isinstance(compatibility, Mapping)
        else None
    )
    expected_digests = {
        item["kind"]: item["content_digest"]
        for item in files or []
        if isinstance(item, dict)
        and isinstance(item.get("kind"), str)
        and isinstance(item.get("content_digest"), str)
    }
    actual_payloads = {"source": source_index, **family}
    for kind in COMPATIBILITY_ORDER:
        identity = actual_payloads[kind]["index_identity"]
        if identity["content_digest"] != expected_digests.get(kind):
            raise PortableFamilyError(
                f"portable {kind} compatibility digest does not match"
            )
    return source_index, family


def load_portable_family_with_state(
    repo_root: Path,
    *,
    manifest_path: Path = MANIFEST_RELATIVE_PATH,
    artifact_root: Path | None = None,
    allow_shadow_git: bool = True,
    require_budget_receipt: bool = True,
    producer_execution_inputs: Mapping[str, Any] | None = None,
    require_current_producer_identity: bool = True,
    allow_legacy_external_receipt: bool = False,
) -> tuple[
    dict[str, Any],
    dict[str, dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
]:
    """Load either v3 or v4 and preserve the observed delivery state.

    The long-standing ``load_portable_family`` triple remains the compatibility
    API. Runtime, query, and MCP adapters use this state-bearing route so a
    missing cold object can never be flattened into a successful full read.
    """
    root = repo_root.resolve()
    path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise PortableFamilyError(
            f"cannot read portable family manifest {path}"
        ) from exc
    if manifest.get("schema_version") != SCHEMA_VERSION:
        try:
            from scripts.repo_local.tiered_family import (
                DISTRIBUTION_SCHEMA_VERSION,
                load_tiered_family,
            )
        except ImportError:  # pragma: no cover - direct script execution
            from repo_local.tiered_family import (  # type: ignore
                DISTRIBUTION_SCHEMA_VERSION,
                load_tiered_family,
            )
        if manifest.get("schema_version") != DISTRIBUTION_SCHEMA_VERSION:
            raise PortableFamilyError(
                "portable family manifest has an unsupported schema version"
            )
        source, family, distribution, state = load_tiered_family(
            root,
            artifact_root=artifact_root,
            allow_shadow_git=allow_shadow_git,
        )
        return source, family, distribution, state
    validated = _validate_manifest_shape(manifest)
    rows = _load_rows(
        root,
        validated,
        require_budget_receipt=require_budget_receipt,
        producer_execution_inputs=producer_execution_inputs,
        require_current_producer_identity=require_current_producer_identity,
        allow_legacy_external_receipt=allow_legacy_external_receipt,
    )
    source, family = reconstruct_compatibility_family(validated, rows)
    state = {
        "state": "git_hot_complete",
        "complete": True,
        "missing_objects": [],
        "routes": {
            "git_hot": len(validated["shards"]),
            "local_cas": 0,
            "shadow_git": 0,
        },
        "corpus_digest": (
            "sha256:" + validated["family_identity"]["content_digest"]
        ),
        "distribution_digest": "",
    }
    return source, family, validated, state


def load_portable_family(
    repo_root: Path,
    *,
    manifest_path: Path = MANIFEST_RELATIVE_PATH,
    artifact_root: Path | None = None,
    allow_shadow_git: bool = True,
    require_budget_receipt: bool = True,
    producer_execution_inputs: Mapping[str, Any] | None = None,
    require_current_producer_identity: bool = True,
    allow_legacy_external_receipt: bool = False,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, Any]]:
    source, family, manifest, _ = load_portable_family_with_state(
        repo_root,
        manifest_path=manifest_path,
        artifact_root=artifact_root,
        allow_shadow_git=allow_shadow_git,
        require_budget_receipt=require_budget_receipt,
        producer_execution_inputs=producer_execution_inputs,
        require_current_producer_identity=require_current_producer_identity,
        allow_legacy_external_receipt=allow_legacy_external_receipt,
    )
    return source, family, manifest


def expected_portable_paths(
    manifest: Mapping[str, Any],
    *,
    manifest_path: Path = MANIFEST_RELATIVE_PATH,
) -> set[Path]:
    paths = {manifest_path}
    for descriptor in manifest.get("shards", []):
        if isinstance(descriptor, dict) and isinstance(
            descriptor.get("path"), str
        ):
            paths.add(Path(descriptor["path"]))
    return paths


def check_portable_output(
    repo_root: Path,
    manifest: Mapping[str, Any],
    shards: Mapping[Path, bytes],
    *,
    manifest_path: Path = MANIFEST_RELATIVE_PATH,
    require_legacy_absent: bool = True,
) -> bool:
    root = repo_root.resolve()
    ok = True
    expected_manifest = render_manifest(manifest)
    actual_manifest_path = root / manifest_path
    if (
        not actual_manifest_path.is_file()
        or actual_manifest_path.read_bytes() != expected_manifest
    ):
        ok = False
    for path, expected in shards.items():
        actual = root / path
        if not actual.is_file() or actual.read_bytes() != expected:
            ok = False
    actual_shards = {
        path.relative_to(root)
        for path in (root / manifest_path.parent / "shards").glob("*/*.jsonl")
        if path.is_file()
    }
    if actual_shards != set(shards):
        ok = False
    if require_legacy_absent:
        legacy_root = root / manifest_path.parent
        if any(
            (legacy_root / filename).exists()
            for filename in LEGACY_INDEX_FILENAMES.values()
        ):
            ok = False
    return ok


def write_portable_output(
    repo_root: Path,
    manifest: Mapping[str, Any],
    shards: Mapping[Path, bytes],
    *,
    manifest_path: Path = MANIFEST_RELATIVE_PATH,
    remove_legacy: bool = True,
) -> None:
    root = repo_root.resolve()
    expected = set(shards)
    shard_root = root / manifest_path.parent / "shards"
    for existing in shard_root.glob("*/*.jsonl"):
        relative = existing.relative_to(root)
        if relative not in expected:
            existing.unlink()
    for path, content in shards.items():
        destination = root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.is_file() or destination.read_bytes() != content:
            destination.write_bytes(content)
    manifest_destination = root / manifest_path
    manifest_destination.parent.mkdir(parents=True, exist_ok=True)
    rendered = render_manifest(manifest)
    if (
        not manifest_destination.is_file()
        or manifest_destination.read_bytes() != rendered
    ):
        manifest_destination.write_bytes(rendered)
    if remove_legacy:
        for filename in LEGACY_INDEX_FILENAMES.values():
            (root / manifest_path.parent / filename).unlink(missing_ok=True)


def _git_bytes(repo_root: Path, ref: str, path: Path) -> bytes | None:
    result = subprocess.run(
        ("git", "show", f"{ref}:{path.as_posix()}"),
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def _base_portable_paths(repo_root: Path, base_ref: str) -> set[Path]:
    manifest_bytes = _git_bytes(repo_root, base_ref, MANIFEST_RELATIVE_PATH)
    if manifest_bytes is None:
        return {
            Path("kag/indexes") / filename
            for filename in LEGACY_INDEX_FILENAMES.values()
            if _git_bytes(
                repo_root,
                base_ref,
                Path("kag/indexes") / filename,
            )
            is not None
        }
    try:
        manifest = json.loads(manifest_bytes)
    except json.JSONDecodeError as exc:
        raise PortableFamilyError(
            f"{base_ref} portable family manifest is invalid"
        ) from exc
    if manifest.get("schema_version") == TIERED_DISTRIBUTION_SCHEMA_VERSION:
        corpus_bytes = _git_bytes(
            repo_root,
            base_ref,
            Path("kag/indexes/corpus.manifest.json"),
        )
        hot_profile_bytes = _git_bytes(
            repo_root,
            base_ref,
            Path("kag/indexes/hot_profile.json"),
        )
        if corpus_bytes is None or hot_profile_bytes is None:
            raise PortableFamilyError(
                f"{base_ref} tiered family control manifests are incomplete"
            )
        try:
            corpus = json.loads(corpus_bytes)
            hot_profile = json.loads(hot_profile_bytes)
        except json.JSONDecodeError as exc:
            raise PortableFamilyError(
                f"{base_ref} tiered family control manifest is invalid"
            ) from exc
        objects = corpus.get("objects") if isinstance(corpus, dict) else None
        selection = (
            hot_profile.get("selection")
            if isinstance(hot_profile, dict)
            else None
        )
        hot_kinds = (
            selection.get("include_record_kinds")
            if isinstance(selection, dict)
            else None
        )
        placement = manifest.get("placement")
        placement_state = (
            placement.get("state") if isinstance(placement, dict) else None
        )
        if (
            not isinstance(objects, list)
            or not isinstance(hot_kinds, list)
            or placement_state not in {"shadow", "externalized"}
        ):
            raise PortableFamilyError(
                f"{base_ref} tiered family placement is malformed"
            )
        paths = {
            MANIFEST_RELATIVE_PATH,
            Path("kag/indexes/corpus.manifest.json"),
            Path("kag/indexes/hot_profile.json"),
            Path("kag/indexes/artifact_locators.json"),
        }
        for descriptor in objects:
            if not isinstance(descriptor, dict):
                raise PortableFamilyError(
                    f"{base_ref} tiered object descriptor is malformed"
                )
            kind = descriptor.get("kind")
            range_value = descriptor.get("range")
            if not isinstance(kind, str) or not isinstance(range_value, str):
                raise PortableFamilyError(
                    f"{base_ref} tiered object path is malformed"
                )
            if placement_state == "shadow" or kind in hot_kinds:
                paths.add(
                    Path("kag/indexes/shards")
                    / kind
                    / f"{range_value}.jsonl"
                )
        return paths
    return expected_portable_paths(manifest)


def _base_manifest(
    repo_root: Path,
    base_ref: str,
) -> dict[str, Any] | None:
    content = _git_bytes(repo_root, base_ref, MANIFEST_RELATIVE_PATH)
    if content is None:
        return None
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise PortableFamilyError(
            f"{base_ref} portable family manifest is invalid"
        ) from exc
    if not isinstance(payload, dict):
        raise PortableFamilyError(
            f"{base_ref} portable family manifest must be an object"
        )
    return payload


def _budget_receipt_scope(
    *,
    base_has_v3: bool,
    generated_delta_exceeded: bool,
    tracked_size_exceeded: bool,
) -> str:
    if not base_has_v3:
        return "v2_to_v3_migration"
    if generated_delta_exceeded and tracked_size_exceeded:
        return "generated_delta_and_tracked_size"
    if tracked_size_exceeded:
        return "tracked_size"
    return "generated_delta"


def _validate_standing_budget(
    manifest: Mapping[str, Any],
    base_manifest: Mapping[str, Any] | None,
) -> None:
    if base_manifest is None:
        return
    head_budgets = manifest.get("budgets")
    base_budgets = base_manifest.get("budgets")
    if not isinstance(head_budgets, Mapping) or not isinstance(
        base_budgets,
        Mapping,
    ):
        raise PortableFamilyError("portable family budgets are malformed")
    for field in ("tracked_bytes_max", "changed_generated_bytes_max"):
        head_value = head_budgets.get(field)
        base_field = (
            "owner_git_hot_bytes_max"
            if field == "tracked_bytes_max"
            and base_manifest.get("schema_version")
            == TIERED_DISTRIBUTION_SCHEMA_VERSION
            else field
        )
        base_value = base_budgets.get(base_field)
        if (
            not isinstance(head_value, int)
            or not isinstance(base_value, int)
        ):
            raise PortableFamilyError(
                f"portable family budget {field} is malformed"
            )
        if head_value > base_value:
            raise PortableFamilyError(
                f"standing budget {field} cannot be raised by generated output "
                "or a one-change receipt"
            )


def _budget_decision_ref(manifest: Mapping[str, Any]) -> str:
    return (
        TIERED_DECISION_REF
        if manifest.get("schema_version")
        == TIERED_DISTRIBUTION_SCHEMA_VERSION
        else DECISION_REF
    )


def changed_generated_bytes(
    repo_root: Path,
    *,
    base_ref: str,
    manifest: Mapping[str, Any],
) -> tuple[int, int, str]:
    root = repo_root.resolve()
    resolved = subprocess.run(
        ("git", "rev-parse", base_ref),
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    head_paths = expected_portable_paths(manifest)
    base_paths = _base_portable_paths(root, resolved)
    changed_bytes = 0
    changed_files = 0
    for path in sorted(head_paths | base_paths):
        old = _git_bytes(root, resolved, path)
        new_path = root / path
        new = new_path.read_bytes() if new_path.is_file() else None
        if old == new:
            continue
        changed_files += 1
        changed_bytes += max(len(old or b""), len(new or b""))
    return changed_bytes, changed_files, resolved


def _resolve_receipt_base_ref(repo_root: Path, receipt: Mapping[str, Any]) -> str:
    base_ref = receipt.get("base_ref")
    if not isinstance(base_ref, str) or not base_ref:
        raise PortableFamilyError("budget receipt base_ref is missing")
    try:
        resolved = subprocess.run(
            ("git", "rev-parse", base_ref),
            cwd=repo_root.resolve(),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise PortableFamilyError(
            "budget receipt base_ref cannot be resolved"
        ) from exc
    if resolved != base_ref:
        raise PortableFamilyError(
            "budget receipt base_ref must be an exact resolved commit"
        )
    return resolved


def _validate_budget_receipt_shape(
    receipt: object,
    *,
    allow_legacy_external_receipt: bool = False,
) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise PortableFamilyError("budget receipt must be a JSON object")
    if (
        allow_legacy_external_receipt
        and receipt.get("schema_version") == LEGACY_BUDGET_RECEIPT_SCHEMA_VERSION
        and set(receipt) == set(LEGACY_BUDGET_RECEIPT_FIELDS)
    ):
        return receipt
    if set(receipt) != set(BUDGET_RECEIPT_FIELDS):
        missing = sorted(BUDGET_RECEIPT_FIELDS - set(receipt))
        extra = sorted(set(receipt) - BUDGET_RECEIPT_FIELDS)
        details: list[str] = []
        if missing:
            details.append(f"missing={','.join(missing)}")
        if extra:
            details.append(f"extra={','.join(extra)}")
        raise PortableFamilyError(
            "budget receipt shape is not the current identity-bound contract"
            + (f" ({'; '.join(details)})" if details else "")
        )
    return receipt


def _budget_execution_inputs_from_receipt(
    repo_root: Path,
    receipt: Mapping[str, Any],
    *,
    resolved_base_ref: str,
) -> dict[str, Any]:
    producer = receipt.get("producer_identity")
    execution = producer.get("execution_inputs") if isinstance(producer, Mapping) else None
    targets = execution.get("command_targets") if isinstance(execution, Mapping) else None
    action_inputs = execution.get("action_inputs") if isinstance(execution, Mapping) else None
    if not isinstance(targets, Mapping) or not isinstance(action_inputs, Mapping):
        raise PortableFamilyError(
            "budget receipt producer identity has no replayable execution inputs"
        )
    history_ref = targets.get("history_ref")
    event_history_ref = targets.get("event_history_ref")
    output = targets.get("output")
    base_ref = targets.get("base_ref", resolved_base_ref)
    jobs = targets.get("jobs")
    family_mode = targets.get("family_mode", "portable")
    artifact = targets.get("artifact_root")
    artifact_root = (
        Path(artifact["path"])
        if isinstance(artifact, Mapping) and isinstance(artifact.get("path"), str)
        else None
    )
    if not all(
        isinstance(value, str) and value
        for value in (base_ref, history_ref, event_history_ref, output, family_mode)
    ):
        raise PortableFamilyError(
            "budget receipt producer command targets are incomplete"
        )
    if jobs is not None and not isinstance(jobs, (str, int)):
        raise PortableFamilyError("budget receipt producer jobs target is malformed")
    return capture_budget_producer_execution_inputs(
        repo_root,
        base_ref=base_ref,
        history_ref=history_ref,
        event_history_ref=event_history_ref,
        output=output,
        family_mode=family_mode,
        artifact_root=artifact_root,
        externalized=bool(targets.get("externalized", False)),
        jobs=jobs,
    )


def _validate_budget_receipt_identities(
    repo_root: Path,
    *,
    manifest: Mapping[str, Any],
    receipt: Mapping[str, Any],
    resolved_base_ref: str,
    producer_execution_inputs: Mapping[str, Any] | None = None,
    require_current_producer_identity: bool = True,
    allow_dirty: bool = False,
) -> None:
    expected_source_snapshot = manifest["family_identity"]["source_snapshot"]
    if receipt.get("head_source_snapshot") != expected_source_snapshot:
        raise PortableFamilyError(
            "budget receipt source snapshot does not match current family"
        )
    candidate_identity = _budget_candidate_identity(
        repo_root,
        resolved_base_ref=resolved_base_ref,
        manifest=manifest,
        allow_dirty=allow_dirty,
    )
    if receipt.get("candidate_identity") != candidate_identity:
        raise PortableFamilyError(
            "budget receipt candidate identity does not match current candidate"
        )
    recorded_producer = receipt.get("producer_identity")
    if require_current_producer_identity:
        if producer_execution_inputs is None:
            producer_execution_inputs = _budget_execution_inputs_from_receipt(
                repo_root,
                receipt,
                resolved_base_ref=resolved_base_ref,
            )
        producer_identity = _budget_producer_identity(producer_execution_inputs)
        if recorded_producer != producer_identity:
            raise PortableFamilyError(
                "budget receipt producer identity does not match executing aoa-kag procedure"
            )
    else:
        _validate_recorded_budget_producer_identity(recorded_producer)


def _validate_recorded_budget_producer_identity(identity: object) -> None:
    """Validate a foreign owner's producer identity without rebinding it.

    A downstream owner may intentionally execute a pinned historical aoa-kag
    action.  Its receipt still has to be an internally coherent identity-bound
    object, but it must not be compared with the newer producer currently
    executing this coverage scan.  Current-owner admission remains strict via
    ``require_current_producer_identity=True``.
    """
    if not isinstance(identity, Mapping):
        raise PortableFamilyError("budget receipt producer identity is malformed")
    required = {
        "contract_version",
        "owner",
        "revision_binding",
        "source_digest",
        "procedure_manifest",
        "files",
        "action",
        "execution_inputs",
        "identity_digest",
    }
    if set(identity) != required:
        raise PortableFamilyError(
            "foreign budget receipt producer identity shape is invalid"
        )
    contract_version = identity.get("contract_version")
    revision_binding = identity.get("revision_binding")
    valid_bindings = {
        "aoa-kag:budget-receipt-producer-identity-v3":
            "content-addressed-procedure-import-closure-runtime-inputs-and-descriptor-io-v1",
        "aoa-kag:budget-receipt-producer-identity-v4":
            "content-addressed-procedure-import-closure-portable-runtime-contract-and-descriptor-io-v1",
    }
    if (
        not isinstance(contract_version, str)
        or valid_bindings.get(contract_version) != revision_binding
        or identity.get("owner") != "aoa-kag"
    ):
        raise PortableFamilyError(
            "foreign budget receipt producer identity contract is invalid"
        )
    source_digest = identity.get("source_digest")
    files = identity.get("files")
    action = identity.get("action")
    procedure_manifest = identity.get("procedure_manifest")
    execution_inputs = identity.get("execution_inputs")
    identity_digest = identity.get("identity_digest")
    if (
        not isinstance(source_digest, str)
        or len(source_digest) != 64
        or any(character not in HEX_DIGITS for character in source_digest)
        or not isinstance(files, list)
        or not files
        or not isinstance(action, Mapping)
        or not isinstance(procedure_manifest, Mapping)
        or not isinstance(execution_inputs, Mapping)
        or not isinstance(identity_digest, str)
        or len(identity_digest) != 64
        or any(character not in HEX_DIGITS for character in identity_digest)
    ):
        raise PortableFamilyError(
            "foreign budget receipt producer identity fields are invalid"
        )
    normalized_files: list[dict[str, Any]] = []
    for item in files:
        if not isinstance(item, Mapping) or set(item) != {
            "path",
            "state",
            "content_digest",
            "bytes",
            "git_blob",
        }:
            raise PortableFamilyError(
                "foreign budget receipt producer files are invalid"
            )
        path = item.get("path")
        content_digest = item.get("content_digest")
        bytes_value = item.get("bytes")
        git_blob = item.get("git_blob")
        if (
            not isinstance(path, str)
            or not path
            or item.get("state") != "present"
            or not isinstance(content_digest, str)
            or len(content_digest) != 64
            or any(character not in HEX_DIGITS for character in content_digest)
            or not isinstance(bytes_value, int)
            or isinstance(bytes_value, bool)
            or bytes_value < 0
            or not _budget_valid_git_blob(git_blob)
        ):
            raise PortableFamilyError(
                "foreign budget receipt producer file entry is invalid"
            )
        normalized_files.append(dict(item))
    if sha256_bytes(canonical_json_bytes(normalized_files)) != source_digest:
        raise PortableFamilyError(
            "foreign budget receipt producer source identity is inconsistent"
        )
    action_path = action.get("path")
    if action_path != BUDGET_PRODUCER_ACTION_PATH.as_posix():
        raise PortableFamilyError(
            "foreign budget receipt producer action path is invalid"
        )
    matching_actions = [
        item for item in normalized_files if item.get("path") == action_path
    ]
    if len(matching_actions) != 1 or matching_actions[0] != dict(action):
        raise PortableFamilyError(
            "foreign budget receipt producer action is not in its source identity"
        )
    identity_material = {
        key: identity[key]
        for key in (
            "contract_version",
            "owner",
            "revision_binding",
            "source_digest",
            "procedure_manifest",
            "action",
            "execution_inputs",
        )
    }
    if sha256_bytes(canonical_json_bytes(identity_material)) != identity_digest:
        raise PortableFamilyError(
            "foreign budget receipt producer identity digest is inconsistent"
        )


def _validate_budget_receipt_approval(
    receipt: Mapping[str, Any],
    *,
    changed_bytes: int | None,
    tracked_bytes: int,
) -> None:
    reason = receipt.get("reason")
    approved_by = receipt.get("approved_by")
    allowed_bytes = receipt.get("allowed_bytes")
    allowed_tracked_bytes = receipt.get("allowed_tracked_bytes")
    if (
        not isinstance(reason, str)
        or not reason.strip()
        or not isinstance(approved_by, str)
        or not approved_by.strip()
        or not isinstance(allowed_bytes, int)
        or isinstance(allowed_bytes, bool)
        or not isinstance(allowed_tracked_bytes, int)
        or isinstance(allowed_tracked_bytes, bool)
        or allowed_tracked_bytes < tracked_bytes
        or (changed_bytes is not None and allowed_bytes < changed_bytes)
    ):
        raise PortableFamilyError("budget receipt approval is incomplete")


def receipt_path_for(manifest: Mapping[str, Any]) -> Path:
    digest = manifest["family_identity"]["content_digest"]
    return (
        BUDGET_RECEIPT_ROOT_RELATIVE_PATH
        / f"{digest}.json"
    )


def _budget_confined_receipt_path(
    root: Path,
    relative: Path,
    *,
    allow_missing: bool,
) -> Path:
    if (
        relative.is_absolute()
        or not relative.parts
        or ".." in relative.parts
        or relative.parent != BUDGET_RECEIPT_ROOT_RELATIVE_PATH
        or relative.suffix != ".json"
    ):
        raise PortableFamilyError(
            f"budget receipt path is not the exact in-root receipt object: {relative}"
        )
    resolved_root = root.resolve()
    parent = resolved_root
    for component in relative.parts[:-1]:
        parent = parent / component
        try:
            metadata = parent.lstat()
        except FileNotFoundError:
            if allow_missing:
                continue
            raise PortableFamilyError(
                f"budget receipt parent is missing: {parent}"
            )
        if not stat.S_ISDIR(metadata.st_mode):
            raise PortableFamilyError(
                f"budget receipt parent must be a regular directory: {parent}"
            )
    destination = resolved_root.joinpath(*relative.parts)
    try:
        metadata = destination.lstat()
    except FileNotFoundError:
        if allow_missing:
            return destination
        raise PortableFamilyError(f"budget receipt is missing: {relative}")
    if not stat.S_ISREG(metadata.st_mode):
        raise PortableFamilyError(
            f"budget receipt must be a regular in-root file: {relative}"
        )
    try:
        destination.resolve(strict=True).relative_to(resolved_root)
    except ValueError as exc:
        raise PortableFamilyError(
            f"budget receipt resolves outside the owner root: {relative}"
        ) from exc
    return destination


def _budget_require_descriptor_receipt_io() -> None:
    supports_dir_fd = getattr(os, "supports_dir_fd", set())
    required = (os.open, os.mkdir, os.rename, os.unlink)
    if (
        os.name != "posix"
        or not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
        or not all(function in supports_dir_fd for function in required)
    ):
        raise PortableFamilyError(
            "budget receipt descriptor confinement is unavailable on this platform"
        )


def _budget_open_receipt_parent(
    root: Path,
    relative: Path,
    *,
    allow_missing: bool,
) -> tuple[int, str]:
    """Open and pin the receipt parent, never following a path component."""
    if (
        relative.is_absolute()
        or not relative.parts
        or ".." in relative.parts
        or relative.parent != BUDGET_RECEIPT_ROOT_RELATIVE_PATH
        or relative.suffix != ".json"
    ):
        raise PortableFamilyError(
            f"budget receipt path is not the exact in-root receipt object: {relative}"
        )
    _budget_require_descriptor_receipt_io()
    resolved_root = root.resolve()
    flags = (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(resolved_root, flags)
    except OSError as exc:
        raise PortableFamilyError(
            f"budget receipt owner root cannot be pinned: {resolved_root}"
        ) from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISDIR(metadata.st_mode):
            raise PortableFamilyError("budget receipt owner root is not a directory")
        for component in relative.parts[:-1]:
            try:
                child = os.open(component, flags, dir_fd=descriptor)
            except FileNotFoundError as exc:
                if not allow_missing:
                    raise PortableFamilyError(
                        f"budget receipt parent is missing: {relative}"
                    ) from exc
                try:
                    os.mkdir(component, 0o755, dir_fd=descriptor)
                except FileExistsError:
                    pass
                try:
                    child = os.open(component, flags, dir_fd=descriptor)
                except OSError as retry_exc:
                    raise PortableFamilyError(
                        "budget receipt parent could not be opened under the "
                        "pinned owner root"
                    ) from retry_exc
            except OSError as exc:
                raise PortableFamilyError(
                    "budget receipt parent must be a pinned directory; "
                    "traversal rejected a symlink or non-directory component"
                ) from exc
            os.close(descriptor)
            descriptor = child
        return descriptor, relative.name
    except BaseException:
        os.close(descriptor)
        raise


def _budget_open_receipt_leaf(
    parent_descriptor: int,
    leaf: str,
    *,
    allow_missing: bool,
) -> int | None:
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(leaf, flags, dir_fd=parent_descriptor)
    except FileNotFoundError as exc:
        if allow_missing:
            return None
        raise PortableFamilyError(f"budget receipt is missing: {leaf}") from exc
    except OSError as exc:
        raise PortableFamilyError(
            "budget receipt cannot be opened as a regular in-root file"
        ) from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise PortableFamilyError(
                "budget receipt must be a regular in-root file"
            )
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _budget_read_receipt(
    repo_root: Path,
    manifest: Mapping[str, Any],
    *,
    allow_legacy_external_receipt: bool = False,
) -> dict[str, Any]:
    relative = receipt_path_for(manifest)
    parent_descriptor, leaf = _budget_open_receipt_parent(
        repo_root,
        relative,
        allow_missing=False,
    )
    try:
        descriptor = _budget_open_receipt_leaf(
            parent_descriptor,
            leaf,
            allow_missing=False,
        )
        assert descriptor is not None
        with os.fdopen(descriptor, "rb") as stream:
            raw = stream.read()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PortableFamilyError(
            f"budget receipt is unreadable: {relative}"
        ) from exc
    finally:
        os.close(parent_descriptor)
    return _validate_budget_receipt_shape(
        payload,
        allow_legacy_external_receipt=allow_legacy_external_receipt,
    )


def build_budget_receipt(
    repo_root: Path,
    *,
    base_ref: str,
    manifest: Mapping[str, Any],
    reason: str,
    approved_by: str = "repository-owner",
    source_epoch: str | None = None,
    producer_execution_inputs: Mapping[str, Any] | None = None,
    allow_dirty: bool = False,
) -> tuple[Path, dict[str, Any]]:
    if not reason.strip():
        raise PortableFamilyError("budget receipt reason must not be empty")
    changed_bytes, changed_files, resolved = changed_generated_bytes(
        repo_root,
        base_ref=base_ref,
        manifest=manifest,
    )
    base_manifest = _base_manifest(repo_root, resolved)
    _validate_standing_budget(manifest, base_manifest)
    budgets = manifest["budgets"]
    summary = manifest["summary"]
    delta_exceeded = (
        changed_bytes > budgets["changed_generated_bytes_max"]
    )
    tracked_exceeded = (
        summary["tracked_bytes"] > budgets["tracked_bytes_max"]
    )
    scope = _budget_receipt_scope(
        base_has_v3=base_manifest is not None,
        generated_delta_exceeded=delta_exceeded,
        tracked_size_exceeded=tracked_exceeded,
    )
    candidate_identity, producer_identity = _budget_receipt_identities(
        repo_root,
        resolved_base_ref=resolved,
        manifest=manifest,
        source_epoch=source_epoch,
        producer_execution_inputs=producer_execution_inputs,
        allow_dirty=allow_dirty,
    )
    receipt = {
        "schema_version": BUDGET_RECEIPT_SCHEMA_VERSION,
        "repo": manifest["repo"]["name"],
        "scope": scope,
        "base_ref": resolved,
        "head_family_digest": manifest["family_identity"]["content_digest"],
        "head_source_snapshot": manifest["family_identity"]["source_snapshot"],
        "candidate_identity": candidate_identity,
        "producer_identity": producer_identity,
        "changed_generated_bytes": changed_bytes,
        "changed_generated_files": changed_files,
        "default_limit_bytes": DEFAULT_DELTA_BYTES_MAX,
        "allowed_bytes": changed_bytes,
        "tracked_bytes": summary["tracked_bytes"],
        "tracked_bytes_max": budgets["tracked_bytes_max"],
        "allowed_tracked_bytes": summary["tracked_bytes"],
        "reason": reason.strip(),
        "approved_by": approved_by,
        "decision_ref": _budget_decision_ref(manifest),
    }
    return receipt_path_for(manifest), receipt


def write_budget_receipt(
    repo_root: Path,
    path: Path,
    receipt: Mapping[str, Any],
) -> None:
    candidate_identity = receipt.get("candidate_identity")
    expected_path = (
        Path(candidate_identity["excluded_path"])
        if isinstance(candidate_identity, Mapping)
        and isinstance(candidate_identity.get("excluded_path"), str)
        else None
    )
    if expected_path is None or path != expected_path:
        raise PortableFamilyError(
            "budget receipt write path must match candidate excluded_path"
        )
    parent_descriptor, leaf = _budget_open_receipt_parent(
        repo_root,
        path,
        allow_missing=True,
    )
    content = render_manifest(receipt)
    try:
        existing = _budget_open_receipt_leaf(
            parent_descriptor,
            leaf,
            allow_missing=True,
        )
        if existing is not None:
            with os.fdopen(existing, "rb") as stream:
                if stream.read() == content:
                    return
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0)
        )
        temporary_name: str | None = None
        descriptor: int | None = None
        for _ in range(16):
            candidate = f".{leaf}.{os.getpid()}.{os.urandom(8).hex()}.tmp"
            try:
                descriptor = os.open(
                    candidate,
                    flags,
                    0o644,
                    dir_fd=parent_descriptor,
                )
            except FileExistsError:
                continue
            temporary_name = candidate
            break
        if descriptor is None or temporary_name is None:
            raise PortableFamilyError(
                "budget receipt could not allocate a private temporary object"
            )
        try:
            with os.fdopen(descriptor, "wb") as stream:
                descriptor = None
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.rename(
                temporary_name,
                leaf,
                src_dir_fd=parent_descriptor,
                dst_dir_fd=parent_descriptor,
            )
            os.fsync(parent_descriptor)
            temporary_name = None
        finally:
            if descriptor is not None:
                os.close(descriptor)
            if temporary_name is not None:
                try:
                    os.unlink(temporary_name, dir_fd=parent_descriptor)
                except FileNotFoundError:
                    pass
    finally:
        os.close(parent_descriptor)


def validate_changed_generated_budget(
    repo_root: Path,
    *,
    base_ref: str,
    manifest: Mapping[str, Any],
    producer_execution_inputs: Mapping[str, Any] | None = None,
    allow_dirty: bool = False,
) -> tuple[int, int, bool]:
    _budget_require_source_epoch(repo_root, allow_dirty=allow_dirty)
    changed_bytes, changed_files, resolved = changed_generated_bytes(
        repo_root,
        base_ref=base_ref,
        manifest=manifest,
    )
    base_manifest = _base_manifest(repo_root, resolved)
    _validate_standing_budget(manifest, base_manifest)
    budgets = manifest["budgets"]
    summary = manifest["summary"]
    limit = budgets["changed_generated_bytes_max"]
    delta_exceeded = changed_bytes > limit
    tracked_exceeded = (
        summary["tracked_bytes"] > budgets["tracked_bytes_max"]
    )
    if not delta_exceeded and not tracked_exceeded:
        return changed_bytes, changed_files, False
    try:
        receipt = _budget_read_receipt(repo_root, manifest)
    except PortableFamilyError as exc:
        raise PortableFamilyError(
            "portable family budget is exceeded and no matching receipt exists: "
            f"changed={changed_bytes}/{limit}, "
            f"tracked={summary['tracked_bytes']}/"
            f"{budgets['tracked_bytes_max']}; {exc}"
        ) from exc
    expected_scope = _budget_receipt_scope(
        base_has_v3=base_manifest is not None,
        generated_delta_exceeded=delta_exceeded,
        tracked_size_exceeded=tracked_exceeded,
    )
    expected = {
        "schema_version": BUDGET_RECEIPT_SCHEMA_VERSION,
        "repo": manifest["repo"]["name"],
        "base_ref": resolved,
        "head_family_digest": manifest["family_identity"]["content_digest"],
        "head_source_snapshot": manifest["family_identity"]["source_snapshot"],
        "changed_generated_bytes": changed_bytes,
        "changed_generated_files": changed_files,
        "default_limit_bytes": limit,
        "tracked_bytes": summary["tracked_bytes"],
        "tracked_bytes_max": budgets["tracked_bytes_max"],
        "decision_ref": _budget_decision_ref(manifest),
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise PortableFamilyError(
                f"budget receipt field {field} does not match current delta"
            )
    _validate_budget_receipt_identities(
        repo_root,
        manifest=manifest,
        receipt=receipt,
        resolved_base_ref=resolved,
        producer_execution_inputs=producer_execution_inputs,
        allow_dirty=allow_dirty,
    )
    if receipt.get("scope") != expected_scope:
        raise PortableFamilyError(
            "budget receipt scope does not match the current exceedance"
        )
    _validate_budget_receipt_approval(
        receipt,
        changed_bytes=changed_bytes,
        tracked_bytes=summary["tracked_bytes"],
    )
    return changed_bytes, changed_files, True


def _validate_tracked_size_receipt(
    repo_root: Path,
    manifest: Mapping[str, Any],
    *,
    producer_execution_inputs: Mapping[str, Any] | None = None,
    require_current_producer_identity: bool = True,
    allow_legacy_external_receipt: bool = False,
) -> None:
    try:
        receipt = _budget_read_receipt(
            repo_root,
            manifest,
            allow_legacy_external_receipt=allow_legacy_external_receipt,
        )
    except PortableFamilyError as exc:
        raise PortableFamilyError(
            "portable tracked byte budget is exceeded without a matching "
            f"digest-bound receipt; {exc}"
        ) from exc
    if receipt.get("schema_version") == LEGACY_BUDGET_RECEIPT_SCHEMA_VERSION:
        if not allow_legacy_external_receipt or require_current_producer_identity:
            raise PortableFamilyError(
                "legacy budget receipts are historical and require explicit "
                "foreign-owner observation mode"
            )
        _validate_legacy_tracked_size_receipt(repo_root, manifest, receipt)
        return
    resolved_base_ref = _resolve_receipt_base_ref(repo_root, receipt)
    summary = manifest["summary"]
    budgets = manifest["budgets"]
    expected = {
        "schema_version": BUDGET_RECEIPT_SCHEMA_VERSION,
        "repo": manifest["repo"]["name"],
        "base_ref": resolved_base_ref,
        "head_family_digest": manifest["family_identity"]["content_digest"],
        "head_source_snapshot": manifest["family_identity"]["source_snapshot"],
        "tracked_bytes": summary["tracked_bytes"],
        "tracked_bytes_max": budgets["tracked_bytes_max"],
        "decision_ref": _budget_decision_ref(manifest),
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise PortableFamilyError(
                f"tracked-size receipt field {field} does not match family"
            )
    _validate_budget_receipt_identities(
        repo_root,
        manifest=manifest,
        receipt=receipt,
        resolved_base_ref=resolved_base_ref,
        producer_execution_inputs=producer_execution_inputs,
        require_current_producer_identity=require_current_producer_identity,
    )
    if receipt.get("scope") not in {
        "tracked_size",
        "generated_delta_and_tracked_size",
    }:
        raise PortableFamilyError(
            "tracked-size receipt scope does not authorize this exceedance"
        )
    _validate_budget_receipt_approval(
        receipt,
        changed_bytes=None,
        tracked_bytes=summary["tracked_bytes"],
    )


def _validate_legacy_tracked_size_receipt(
    repo_root: Path,
    manifest: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> None:
    """Observe a retained external v1 receipt without authorizing current work.

    Historical v1 receipts do not contain the identity-bound candidate and
    producer fields required by current owner admission.  The explicit
    external coverage path may still use one as a bounded observation when
    its old digest, size, base, scope, and approval fields match the current
    published family.  No current budget validator opts into this path.
    """
    resolved_base_ref = _resolve_receipt_base_ref(repo_root, receipt)
    summary = manifest["summary"]
    budgets = manifest["budgets"]
    expected = {
        "schema_version": LEGACY_BUDGET_RECEIPT_SCHEMA_VERSION,
        "repo": manifest["repo"]["name"],
        "base_ref": resolved_base_ref,
        "head_family_digest": manifest["family_identity"]["content_digest"],
        "tracked_bytes": summary["tracked_bytes"],
        "tracked_bytes_max": budgets["tracked_bytes_max"],
        "decision_ref": _budget_decision_ref(manifest),
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise PortableFamilyError(
                f"legacy tracked-size receipt field {field} does not match family"
            )
    if receipt.get("scope") not in {
        "tracked_size",
        "generated_delta_and_tracked_size",
    }:
        raise PortableFamilyError(
            "legacy tracked-size receipt scope does not authorize this exceedance"
        )
    _validate_budget_receipt_approval(
        receipt,
        changed_bytes=None,
        tracked_bytes=summary["tracked_bytes"],
    )

def write_compatibility_view(
    output_root: Path,
    source_index: Mapping[str, Any],
    family: Mapping[str, Mapping[str, Any]],
    *,
    normalized_json: Any,
) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    payloads = {"source": source_index, **family}
    for kind in COMPATIBILITY_ORDER:
        destination = output_root / LEGACY_INDEX_FILENAMES[kind]
        destination.write_text(
            normalized_json(payloads[kind]),
            encoding="utf-8",
        )
