"""Provider-neutral, source-epoch-bound code observations.

The first provider is deliberately small: Python's standard-library AST gives
the repo-local index a deterministic symbol and call observation without
making the KAG substrate depend on a third-party parser. The envelope keeps
provider identity, parser configuration, source epoch, occurrence coordinates,
and provenance together so a later Tree-sitter, SCIP, or LSP adapter can
produce the same shape without changing consumers.

This module owns only file-local structural observations. It does not claim
cross-file resolution, runtime freshness, proof, or owner acceptance.
"""

from __future__ import annotations

import ast
import copy
import difflib
import hashlib
import json
import re
import resource
import time
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence

from .identity import qualified_id


OBSERVATION_SCHEMA_VERSION = "aoa-code-observation-v1"
DELTA_SCHEMA_VERSION = "aoa-code-observation-delta-v1"
PROVIDER_ID = "python-ast"
PROVIDER_VERSION = "1"
PARSER_REF = f"{PROVIDER_ID}@{PROVIDER_VERSION}"
CAPABILITY_CLASS = "code-structure"
EXTRACTOR_REF = "aoa-kag:scripts/repo_local/code_observations.py"
CTAGS_PROVIDER_ID = "universal-ctags"
CTAGS_EXTRACTOR_REF = "aoa-kag:scripts/repo_local/code_observations.py#ctags-json"
MACHINE_OBSERVATION_SCHEMA = "abyss_machine_code_observation_envelope_v1"
MACHINE_PROVIDER_BINDING_SCHEMA = (
    "abyss-machine-code-intelligence-provider-binding-v1"
)
MACHINE_PROVIDER_VERSION = "6.2.1"
MACHINE_PROVIDER_ARCHIVE_DIGEST = (
    "sha256:fa8a609bc834286a9c9b2e32e2b78791072cefe7956ba7a838b02004b29b0845"
)
MACHINE_PROVIDER_SUBJECT_DIGEST = (
    "sha256:03e503df1a06356c5db39ce589d07ad161099746b1a0b7e178fbb0feb42cf9"
)
MACHINE_CTAGS_INTERFACE_COMMAND = [
    "PROVIDER",
    "--output-format=json",
    "--fields=+ne",
    "--extras=+q",
    "--languages=Python",
    "-o",
    "-",
    "SOURCE_FILE",
]
MACHINE_CONSUMER_ABI = {
    "owner": "abyss-stack",
    "binding_schema": "abyss-machine-code-intelligence-provider-binding-v1",
    "evidence_schema": "abyss-stack-machine-code-intelligence-evidence-v1",
    "gate_schema": "abyss-stack-machine-code-intelligence-gate-v1",
    "gate_record_schema": "abyss-machine-admission-gate-v1",
    "signed_payload_schema": "abyss-machine-admission-gate-signed-payload-v1",
    "public_key_schema": "abyss-machine-code-intelligence-gate-public-key-v1",
    "algorithm": "ed25519",
    "verification_method": "ed25519-owner-signature-v1",
    "trust_anchor_ref": "/etc/abyss-machine/trust/code-intelligence-gate-ed25519.json",
    "trust_anchor_posture": "existing_root_owned_anchor_only",
    "provider_neutral": True,
    "state_axes": ["candidate", "current", "last_good"],
    "required_separations": [
        "machine artifact trust vs machine evidence gate",
        "installation and admission vs deployed runtime lifecycle",
        "runtime observation vs normalized observation meaning",
        "runtime evidence vs semantic proof and eval verdict",
    ],
}
MACHINE_PROVIDER_BINDING = {
    "schema_version": MACHINE_PROVIDER_BINDING_SCHEMA,
    "provider_id": CTAGS_PROVIDER_ID,
    "provider_owner": "abyss-machine",
    "consumer_owner": "abyss-stack",
    "mode": "indexed",
    "provider": {
        "id": CTAGS_PROVIDER_ID,
        "display_name": "Universal Ctags",
        "owner": "abyss-machine",
        "consumer": "abyss-stack",
        "version": MACHINE_PROVIDER_VERSION,
        "artifact_class": "runtime_or_container_artifact",
        "source_ref_required": True,
        "subject_digest_required": True,
        "trust_gate_required": True,
    },
    "artifact": {
        "class": "runtime_or_container_artifact",
        "archive_sha256": MACHINE_PROVIDER_ARCHIVE_DIGEST,
        "subject_digest": MACHINE_PROVIDER_SUBJECT_DIGEST,
        "signature_status": "not_signed",
        "registry_status": "not_promoted",
        "admission_status": "not_admitted",
    },
    "installation": {
        "executable": "ctags",
        "version_command": ["ctags", "--version"],
        "interface_command": list(MACHINE_CTAGS_INTERFACE_COMMAND),
        "raw_output": "discarded",
    },
    "resource": {
        "kind": "indexing",
        "class": "light",
        "demand_mib": 512,
        "max_parallel": 1,
    },
    "semantic": {
        "status": "unproven",
        "proof_owner": "aoa-evals",
    },
    "consumer_abi": MACHINE_CONSUMER_ABI,
    "trust_anchor": {
        "ref": MACHINE_CONSUMER_ABI["trust_anchor_ref"],
        "posture": "existing_root_owned_anchor_only",
        "created_or_replaced": False,
    },
    "claim_limit": (
        "candidate ABI and artifact identity are source declarations only; "
        "the Universal Ctags candidate is unsigned, unpromoted, and unadmitted"
    ),
}
DEFAULT_PROVIDER_CONFIG: dict[str, Any] = {
    "include_calls": True,
    "language": "python",
    "parser": "stdlib-ast",
}
JAVASCRIPT_PROVIDER_ID = "javascript-lexical"
TYPESCRIPT_PROVIDER_ID = "typescript-lexical"
SECOND_LANGUAGE_PROVIDER_VERSION = "1"
_JS_LANGUAGE_SUFFIXES = {
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
}
_OBSERVATION_EVIDENCE_CLASSES = frozenset(
    {"deterministic", "declared", "observed", "inferred"}
)
_OBSERVATION_KINDS = frozenset({"symbol", "relation"})
_PARSE_STATUSES = frozenset({"parsed", "unparseable", "degraded"})
_QUALIFICATION_MATERIALIZATION_STATES = frozenset(
    {"source_local", "untrusted_observation"}
)
_PROVIDER_LIFECYCLE_STATES = frozenset({"source_local", "unobserved"})
_PROVIDER_LIFECYCLE_HEALTH = frozenset({"source_local", "unobserved"})
_MACHINE_ADMISSION_STATES = frozenset({"not_applicable", "not_admitted"})
_MACHINE_TRUST_REFS = frozenset({"not_applicable", "untrusted"})
_MATERIALIZATION_TRUST_REFS = frozenset({"deterministic", "untrusted"})
_CONFIDENCE_RANK = {
    "inferred": 0,
    "declared": 1,
    "observed": 2,
    "deterministic": 3,
}
_PROVIDER_LANE_DEFINITIONS = {
    "python-ast": {
        "status": "source_local",
        "availability": "source_local",
        "admission": "not_applicable",
    },
    "javascript-lexical": {
        "status": "source_local_fallback",
        "availability": "source_local",
        "admission": "not_applicable",
    },
    "typescript-lexical": {
        "status": "source_local_fallback",
        "availability": "source_local",
        "admission": "not_applicable",
    },
    "universal-ctags": {
        "status": "absent",
        "availability": "absent",
        "admission": "not_admitted",
    },
    "tree-sitter": {
        "status": "absent",
        "availability": "absent",
        "admission": "not_admitted",
    },
    "scip": {
        "status": "absent",
        "availability": "absent",
        "admission": "not_admitted",
    },
    "lsp": {
        "status": "absent",
        "availability": "absent",
        "admission": "not_admitted",
    },
}


def provider_lane_posture(
    provider_id: str,
    *,
    supplied: bool = False,
) -> dict[str, str]:
    """Describe a provider lane without turning an input envelope into trust."""

    normalized = str(provider_id).strip()
    if not normalized:
        raise ValueError("provider_id must be a non-empty string")
    definition = _PROVIDER_LANE_DEFINITIONS.get(normalized)
    if supplied:
        return {
            "id": normalized,
            "status": "supplied_unadmitted",
            "availability": "supplied_input",
            "admission": "not_admitted",
            "claim_limit": "supplied observations are source-bound input only",
        }
    if definition is None:
        return {
            "id": normalized,
            "status": "unknown_unadmitted",
            "availability": "unknown",
            "admission": "not_admitted",
            "claim_limit": "provider lane is not owner-admitted",
        }
    return {
        "id": normalized,
        **definition,
        "claim_limit": (
            "source-local lexical fallback only; not semantic portability"
            if definition["status"] == "source_local_fallback"
            else "source-local observation only"
            if definition["status"] == "source_local"
            else "provider is absent or not admitted"
        ),
    }


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _content_bytes(content: str | bytes) -> tuple[str, bytes]:
    if isinstance(content, bytes):
        return content.decode("utf-8"), content
    if isinstance(content, str):
        return content, content.encode("utf-8")
    raise TypeError("Python source content must be str or bytes")


def _location(node: ast.AST) -> dict[str, int]:
    start_line = int(getattr(node, "lineno", 1))
    end_line = int(getattr(node, "end_lineno", start_line))
    start_column = int(getattr(node, "col_offset", 0)) + 1
    end_column = int(
        getattr(node, "end_col_offset", getattr(node, "col_offset", 0))
    ) + 1
    return {
        "start_line": max(start_line, 1),
        "end_line": max(end_line, start_line, 1),
        "start_column": max(start_column, 1),
        "end_column": max(end_column, start_column, 1),
    }


def _python_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _python_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else ""
    return ""


def _occurrence_key(base: str, counts: dict[str, int]) -> str:
    occurrence = counts.get(base, 0) + 1
    counts[base] = occurrence
    return base if occurrence == 1 else f"{base}#occurrence-{occurrence}"


class _PythonObservationVisitor(ast.NodeVisitor):
    def __init__(self, repo: str, lineage_path: str, *, include_calls: bool) -> None:
        self.repo = repo
        self.lineage_path = lineage_path
        self.include_calls = include_calls
        self.scope: list[str] = []
        # A function nested inside a class is a method only when the class is
        # its immediate lexical owner.  A nested helper inside a method is a
        # function, even though a class name remains in the outer scope.
        self.scope_kinds: list[str] = []
        self.symbol_counts: dict[str, int] = {}
        self.symbols_by_scope: dict[str, dict[str, Any]] = {}
        self.observations: list[dict[str, Any]] = []

    def _roles_for(self, name: str, symbol_kind: str) -> list[str]:
        roles: list[str] = []
        if (
            name.startswith("test")
            or name.startswith("Test")
        ):
            roles.append("test")
        return roles

    def _symbol(self, node: ast.AST, name: str, symbol_kind: str) -> dict[str, Any]:
        qualified_name = ".".join((*self.scope, name))
        semantic_key = _occurrence_key(
            f"python:{symbol_kind}:{qualified_name}",
            self.symbol_counts,
        )
        symbol_id = qualified_id(
            self.repo,
            "code-symbol",
            f"{self.lineage_path}:{semantic_key}",
        )
        subject = {
            "symbol_id": symbol_id,
            "qualified_name": qualified_name,
            "symbol_kind": symbol_kind,
            "label": name,
        }
        roles = self._roles_for(name, symbol_kind)
        if roles:
            subject["roles"] = roles
        self.symbols_by_scope[qualified_name] = subject
        self.observations.append(
            {
                "observation_kind": "symbol",
                "semantic_key": semantic_key,
                "subject": subject,
                "occurrence": _location(node),
                "relation": None,
                "confidence": {"evidence_class": "deterministic", "value": 1.0},
            }
        )
        return subject

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        subject = self._symbol(node, node.name, "class")
        for base in node.bases:
            target_name = _python_name(base)
            if target_name:
                self._relation(node, subject, "inherits", target_name)
        self.scope.append(node.name)
        self.scope_kinds.append("class")
        self.generic_visit(node)
        self.scope_kinds.pop()
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(
            node,
            "method"
            if self.scope_kinds and self.scope_kinds[-1] == "class"
            else "function",
        )

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(
            node,
            "method"
            if self.scope_kinds and self.scope_kinds[-1] == "class"
            else "function",
        )

    def _visit_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        kind: str,
    ) -> None:
        self._symbol(node, node.name, kind)
        self.scope.append(node.name)
        self.scope_kinds.append("function")
        self.generic_visit(node)
        self.scope_kinds.pop()
        self.scope.pop()

    def _relation(
        self,
        node: ast.AST,
        subject: Mapping[str, Any],
        kind: str,
        target_name: str,
    ) -> None:
        location = _location(node)
        subject_name = str(subject["qualified_name"])
        semantic_key = (
            f"python:{kind}:{subject_name}:{location['start_line']}:"
            f"{location['start_column']}:{target_name}"
        )
        self.observations.append(
            {
                "observation_kind": "relation",
                "semantic_key": semantic_key,
                "subject": subject,
                "occurrence": location,
                "relation": {
                    "kind": kind,
                    "target_name": target_name,
                    "resolution": "unresolved",
                },
                "confidence": {
                    "evidence_class": "inferred",
                    "value": 0.9 if kind == "inherits" else 0.75,
                },
            }
        )

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.asname or alias.name.split(".", 1)[0]
            subject = self._symbol(node, name, "import")
            self._relation(node, subject, "imports", alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = "." * int(node.level) + (node.module or "")
        for alias in node.names:
            if alias.name == "*":
                name = "*"
                target_name = module or "*"
            else:
                name = alias.asname or alias.name
                target_name = f"{module}.{alias.name}" if module else alias.name
            subject = self._symbol(node, name, "import")
            self._relation(node, subject, "imports", target_name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if self.include_calls:
            target_name = _python_name(node.func)
            scope_name = ".".join(self.scope)
            subject = self.symbols_by_scope.get(scope_name)
            if target_name and subject:
                self._relation(node, subject, "calls", target_name)
        self.generic_visit(node)


def _parse_python(content: str) -> tuple[ast.Module | None, SyntaxError | None]:
    try:
        return ast.parse(content), None
    except SyntaxError as exc:
        return None, exc
    except (UnicodeError, ValueError) as exc:
        return None, SyntaxError(str(exc))


def _normalized_path(value: str | PurePosixPath, *, field_name: str) -> str:
    path = PurePosixPath(str(value))
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{field_name} must be a relative POSIX path")
    normalized = path.as_posix()
    if not normalized or normalized == ".":
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _visit_python_tree(
    repo: str,
    lineage_path: str,
    tree: ast.Module,
    *,
    include_calls: bool,
) -> list[dict[str, Any]]:
    visitor = _PythonObservationVisitor(
        repo,
        lineage_path,
        include_calls=include_calls,
    )
    visitor.visit(tree)
    for observation in visitor.observations:
        relation = observation["relation"]
        if relation is None:
            continue
        target = visitor.symbols_by_scope.get(str(relation["target_name"]))
        if target is None:
            continue
        relation["resolution"] = "resolved_local"
        relation["target_symbol_id"] = target["symbol_id"]
    return sorted(
        visitor.observations,
        key=lambda observation: (
            observation["occurrence"]["start_line"],
            observation["occurrence"]["start_column"],
            observation["observation_kind"],
            observation["semantic_key"],
        ),
    )


def extract_python_observations(
    *,
    repo: str,
    path: str,
    content: str | bytes,
    lineage_path: str | None = None,
    include_calls: bool = True,
) -> list[dict[str, Any]]:
    """Extract deterministic raw observations for the existing index adapter."""

    try:
        source_text, _ = _content_bytes(content)
    except UnicodeDecodeError:
        # The raw adapter has no envelope in which to carry diagnostics; an
        # invalid source therefore contributes no structure and cannot poison
        # the repository index.
        return []
    source_path = _normalized_path(path, field_name="path")
    lineage = _normalized_path(lineage_path or source_path, field_name="lineage_path")
    tree, error = _parse_python(source_text)
    if error is not None or tree is None:
        return []
    return _visit_python_tree(
        repo,
        lineage,
        tree,
        include_calls=include_calls,
    )


def _diagnostic(error: SyntaxError) -> dict[str, Any]:
    diagnostic: dict[str, Any] = {
        "kind": "syntax_error",
        "message": str(error),
    }
    if error.lineno is not None:
        diagnostic["line"] = max(int(error.lineno), 1)
    if error.offset is not None:
        diagnostic["column"] = max(int(error.offset), 1)
    return diagnostic


def _encoding_diagnostic(error: UnicodeDecodeError) -> dict[str, Any]:
    return {
        "kind": "invalid_utf8",
        "message": "source is not valid UTF-8; code observations were degraded",
        "encoding": "utf-8",
        "byte_start": max(int(error.start), 0),
        "byte_end": max(int(error.end), int(error.start) + 1),
    }


def _normalized_observation(
    repo: str,
    lineage_path: str,
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    semantic_key = str(observation["semantic_key"])
    observation_id = qualified_id(
        repo,
        "code-observation",
        f"{lineage_path}:{semantic_key}",
    )
    subject = dict(observation["subject"])
    relation = observation["relation"]
    return {
        "observation_id": observation_id,
        "observation_kind": str(observation["observation_kind"]),
        "capability_class": CAPABILITY_CLASS,
        "semantic_key": semantic_key,
        "subject": subject,
        "occurrence": dict(observation["occurrence"]),
        "relation": None if relation is None else dict(relation),
        "confidence": dict(observation["confidence"]),
    }


def _provider_symbol_id(
    repo: str,
    lineage_path: str,
    language: str,
    subject: Mapping[str, Any],
) -> str:
    symbol_key = ":".join(
        (
            language,
            str(subject.get("symbol_kind") or "symbol"),
            str(subject.get("qualified_name") or ""),
        )
    )
    return qualified_id(repo, "code-symbol", f"{lineage_path}:{symbol_key}")


def _validate_occurrence(value: object, *, observation_index: int) -> dict[str, int]:
    if not isinstance(value, Mapping):
        raise ValueError(f"provider observation {observation_index} occurrence must be an object")
    occurrence: dict[str, int] = {}
    for field in ("start_line", "end_line", "start_column", "end_column"):
        raw = value.get(field)
        if isinstance(raw, bool) or not isinstance(raw, int) or raw < 1:
            raise ValueError(
                f"provider observation {observation_index} occurrence.{field} must be a positive integer"
            )
        occurrence[field] = raw
    return occurrence


def _validated_subject(
    value: object,
    *,
    observation_index: int,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"provider observation {observation_index} subject must be an object")
    subject: dict[str, Any] = {}
    for field in ("qualified_name", "symbol_kind", "label"):
        raw = value.get(field)
        if not isinstance(raw, str) or not raw:
            raise ValueError(
                f"provider observation {observation_index} subject.{field} must be non-empty"
            )
        subject[field] = raw
    raw_roles = value.get("roles", [])
    if raw_roles is not None:
        if not isinstance(raw_roles, list) or any(
            not isinstance(role, str) or not role for role in raw_roles
        ):
            raise ValueError(
                f"provider observation {observation_index} subject.roles must be non-empty strings"
            )
        if raw_roles:
            subject["roles"] = sorted(set(raw_roles))
    raw_symbol_id = value.get("symbol_id")
    if raw_symbol_id is not None:
        if not isinstance(raw_symbol_id, str) or not raw_symbol_id:
            raise ValueError(
                f"provider observation {observation_index} subject.symbol_id must be non-empty"
            )
        subject["provider_symbol_id"] = raw_symbol_id
    return subject


def _validated_canonical_subject(
    value: object,
    *,
    observation_index: int,
) -> dict[str, Any]:
    """Validate a subject that has already crossed the provider boundary."""

    if not isinstance(value, Mapping):
        raise ValueError(f"provider observation {observation_index} subject must be an object")
    unknown_fields = set(value) - {
        "symbol_id",
        "qualified_name",
        "symbol_kind",
        "label",
        "roles",
    }
    if unknown_fields:
        raise ValueError(
            f"provider observation {observation_index} subject has unsupported fields"
        )
    subject: dict[str, Any] = {}
    for field in ("symbol_id", "qualified_name", "symbol_kind", "label"):
        raw = value.get(field)
        if not isinstance(raw, str) or not raw:
            raise ValueError(
                f"provider observation {observation_index} subject.{field} must be non-empty"
            )
        subject[field] = raw
    raw_roles = value.get("roles", [])
    if raw_roles is not None:
        if not isinstance(raw_roles, list) or any(
            not isinstance(role, str) or not role for role in raw_roles
        ):
            raise ValueError(
                f"provider observation {observation_index} subject.roles must be non-empty strings"
            )
        if raw_roles:
            subject["roles"] = sorted(set(raw_roles))
    return subject


def _validated_confidence(value: object, *, observation_index: int) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"provider observation {observation_index} confidence must be an object")
    evidence_class = value.get("evidence_class")
    confidence_value = value.get("value")
    if evidence_class not in _OBSERVATION_EVIDENCE_CLASSES:
        raise ValueError(
            f"provider observation {observation_index} confidence.evidence_class is invalid"
        )
    if isinstance(confidence_value, bool) or not isinstance(
        confidence_value, (int, float)
    ) or not 0 <= float(confidence_value) <= 1:
        raise ValueError(
            f"provider observation {observation_index} confidence.value must be between 0 and 1"
        )
    return {"evidence_class": str(evidence_class), "value": float(confidence_value)}


def _semantic_confidence(observations: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize semantic confidence without promoting it to provider trust."""

    confidences = [
        dict(observation["confidence"])
        for observation in observations
        if isinstance(observation, Mapping)
        and isinstance(observation.get("confidence"), Mapping)
    ]
    if not confidences:
        return {"evidence_class": "inferred", "value": 0.0}
    weakest = min(
        confidences,
        key=lambda confidence: (
            _CONFIDENCE_RANK[str(confidence["evidence_class"])],
            float(confidence["value"]),
        ),
    )
    return {
        "evidence_class": str(weakest["evidence_class"]),
        "value": float(weakest["value"]),
    }


def _qualification(
    observations: Sequence[Mapping[str, Any]],
    *,
    supplied: bool,
) -> dict[str, Any]:
    """Build the explicit source/lifecycle/admission/trust boundary."""

    if supplied:
        return {
            "provider_lifecycle": {
                "state": "unobserved",
                "health": "unobserved",
                "evidence_refs": [],
            },
            "machine_admission": {
                "state": "not_admitted",
                "trust_ref": "untrusted",
                "evidence_refs": [],
            },
            "semantic_confidence": _semantic_confidence(observations),
            "materialization": {
                "state": "untrusted_observation",
                "trust_ref": "untrusted",
            },
        }
    return {
        "provider_lifecycle": {
            "state": "source_local",
            "health": "source_local",
            "evidence_refs": [EXTRACTOR_REF],
        },
        "machine_admission": {
            "state": "not_applicable",
            "trust_ref": "not_applicable",
            "evidence_refs": [],
        },
        "semantic_confidence": _semantic_confidence(observations),
        "materialization": {
            "state": "source_local",
            "trust_ref": "deterministic",
        },
    }


def _validated_qualification(
    value: object,
    *,
    supplied: bool,
    observations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("provider observation batch qualification is missing")
    qualification = copy.deepcopy(dict(value))
    lifecycle = qualification.get("provider_lifecycle")
    admission = qualification.get("machine_admission")
    semantic = qualification.get("semantic_confidence")
    materialization = qualification.get("materialization")
    if not all(isinstance(item, Mapping) for item in (lifecycle, admission, semantic, materialization)):
        raise ValueError("provider observation batch qualification is incomplete")
    lifecycle_state = str(lifecycle.get("state") or "")
    lifecycle_health = str(lifecycle.get("health") or "")
    admission_state = str(admission.get("state") or "")
    admission_trust = str(admission.get("trust_ref") or "")
    materialization_state = str(materialization.get("state") or "")
    materialization_trust = str(materialization.get("trust_ref") or "")
    if lifecycle_state not in _PROVIDER_LIFECYCLE_STATES:
        raise ValueError("provider observation batch provider lifecycle state is invalid")
    if lifecycle_health not in _PROVIDER_LIFECYCLE_HEALTH:
        raise ValueError("provider observation batch provider lifecycle health is invalid")
    if admission_state not in _MACHINE_ADMISSION_STATES:
        raise ValueError("provider observation batch machine admission state is invalid")
    if admission_trust not in _MACHINE_TRUST_REFS:
        raise ValueError("provider observation batch machine trust is invalid")
    if materialization_state not in _QUALIFICATION_MATERIALIZATION_STATES:
        raise ValueError("provider observation batch materialization state is invalid")
    if materialization_trust not in _MATERIALIZATION_TRUST_REFS:
        raise ValueError("provider observation batch materialization trust is invalid")
    validated_semantic = _validated_confidence(
        semantic,
        observation_index=-1,
    )
    expected_semantic = _semantic_confidence(observations)
    if validated_semantic != expected_semantic:
        raise ValueError(
            "provider observation batch semantic confidence does not match observations"
        )
    if supplied and (
        lifecycle_state != "unobserved"
        or lifecycle_health != "unobserved"
        or admission_state != "not_admitted"
        or admission_trust != "untrusted"
        or materialization_state != "untrusted_observation"
        or materialization_trust != "untrusted"
    ):
        raise ValueError(
            "supplied provider observation batch is not explicitly untrusted"
        )
    if not supplied and (
        lifecycle_state != "source_local"
        or lifecycle_health != "source_local"
        or admission_state != "not_applicable"
        or admission_trust != "not_applicable"
        or materialization_state != "source_local"
        or materialization_trust != "deterministic"
    ):
        raise ValueError("source-local observation batch qualification is invalid")
    for section_name in ("provider_lifecycle", "machine_admission"):
        refs = qualification[section_name].get("evidence_refs")
        if not isinstance(refs, list) or any(
            not isinstance(ref, str) or not ref for ref in refs
        ):
            raise ValueError(
                f"provider observation batch {section_name}.evidence_refs is invalid"
            )
    return qualification


def _validated_relation(
    value: object,
    *,
    observation_index: int,
) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError(f"provider observation {observation_index} relation must be an object or null")
    kind = value.get("kind")
    target_name = value.get("target_name")
    resolution = value.get("resolution")
    if not isinstance(kind, str) or not kind:
        raise ValueError(f"provider observation {observation_index} relation.kind must be non-empty")
    if not isinstance(target_name, str) or not target_name:
        raise ValueError(
            f"provider observation {observation_index} relation.target_name must be non-empty"
        )
    if resolution not in {"resolved_local", "unresolved"}:
        raise ValueError(
            f"provider observation {observation_index} relation.resolution is invalid"
        )
    relation: dict[str, Any] = {
        "kind": kind,
        "target_name": target_name,
        "resolution": str(resolution),
    }
    target_symbol_id = value.get("target_symbol_id")
    if target_symbol_id is not None:
        if not isinstance(target_symbol_id, str) or not target_symbol_id:
            raise ValueError(
                f"provider observation {observation_index} relation.target_symbol_id must be non-empty"
            )
        relation["provider_target_symbol_id"] = target_symbol_id
    return relation


def _validate_canonical_relation(
    value: object,
    *,
    observation_index: int,
) -> None:
    """Validate relation fields without treating provider ids as canonical ids."""

    if value is None:
        return
    if not isinstance(value, Mapping):
        raise ValueError(f"provider observation {observation_index} relation must be an object or null")
    unknown_fields = set(value) - {
        "kind",
        "target_name",
        "resolution",
        "target_symbol_id",
    }
    if unknown_fields:
        raise ValueError(
            f"provider observation {observation_index} relation has unsupported fields"
        )
    kind = value.get("kind")
    target_name = value.get("target_name")
    resolution = value.get("resolution")
    if not isinstance(kind, str) or not kind:
        raise ValueError(f"provider observation {observation_index} relation.kind must be non-empty")
    if not isinstance(target_name, str) or not target_name:
        raise ValueError(
            f"provider observation {observation_index} relation.target_name must be non-empty"
        )
    if resolution not in {"resolved_local", "unresolved"}:
        raise ValueError(
            f"provider observation {observation_index} relation.resolution is invalid"
        )
    target_symbol_id = value.get("target_symbol_id")
    if target_symbol_id is not None and (
        not isinstance(target_symbol_id, str) or not target_symbol_id
    ):
        raise ValueError(
            f"provider observation {observation_index} relation.target_symbol_id must be non-empty"
        )
    if resolution == "resolved_local" and target_symbol_id is None:
        raise ValueError(
            f"provider observation {observation_index} resolved relation needs target_symbol_id"
        )


def _normalize_provider_observations(
    *,
    repo: str,
    lineage_path: str,
    language: str,
    observations: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize one provider's raw observations into the stable envelope shape."""

    prepared: list[dict[str, Any]] = []
    input_symbol_ids: dict[str, str] = {}
    qualified_symbols: dict[str, str] = {}
    for index, raw in enumerate(observations):
        if not isinstance(raw, Mapping):
            raise ValueError(f"provider observation {index} must be an object")
        kind = raw.get("observation_kind")
        if kind not in _OBSERVATION_KINDS:
            raise ValueError(f"provider observation {index} observation_kind is invalid")
        semantic_key = raw.get("semantic_key")
        if not isinstance(semantic_key, str) or not semantic_key:
            raise ValueError(f"provider observation {index} semantic_key must be non-empty")
        subject = _validated_subject(raw.get("subject"), observation_index=index)
        canonical_symbol_id = _provider_symbol_id(
            repo,
            lineage_path,
            language,
            subject,
        )
        provider_symbol_id = subject.pop("provider_symbol_id", None)
        subject["symbol_id"] = canonical_symbol_id
        if provider_symbol_id:
            input_symbol_ids[str(provider_symbol_id)] = canonical_symbol_id
        qualified_symbols.setdefault(str(subject["qualified_name"]), canonical_symbol_id)
        relation = _validated_relation(raw.get("relation"), observation_index=index)
        if kind == "symbol" and relation is not None:
            raise ValueError(
                f"provider observation {index} symbol observations cannot carry relations"
            )
        prepared.append(
            {
                "observation_id": qualified_id(
                    repo,
                    "code-observation",
                    f"{lineage_path}:{semantic_key}",
                ),
                "observation_kind": str(kind),
                "capability_class": CAPABILITY_CLASS,
                "semantic_key": semantic_key,
                "subject": subject,
                "occurrence": _validate_occurrence(
                    raw.get("occurrence"),
                    observation_index=index,
                ),
                "relation": relation,
                "confidence": _validated_confidence(
                    raw.get("confidence"),
                    observation_index=index,
                ),
            }
        )
    observation_ids = [str(item["observation_id"]) for item in prepared]
    if len(observation_ids) != len(set(observation_ids)):
        raise ValueError("provider observation semantic keys must be unique within a batch")
    for item in prepared:
        relation = item["relation"]
        if relation is None:
            continue
        provider_target_id = relation.pop("provider_target_symbol_id", None)
        target_name = str(relation["target_name"])
        target_id = (
            input_symbol_ids.get(str(provider_target_id))
            if provider_target_id is not None
            else None
        )
        target_id = target_id or qualified_symbols.get(target_name)
        if target_id is not None:
            relation["target_symbol_id"] = target_id
        elif relation["resolution"] == "resolved_local":
            relation["resolution"] = "unresolved"
    return prepared


def normalize_provider_observations(
    *,
    repo: str,
    path: str,
    content: str | bytes,
    source_epoch: str,
    language: str,
    provider_id: str,
    provider_version: str,
    observations: Sequence[Mapping[str, Any]],
    lineage_path: str | None = None,
    provider_config: Mapping[str, Any] | None = None,
    parse_status: str = "parsed",
    diagnostics: Sequence[Mapping[str, Any]] = (),
    provenance_mode: str = "observed",
    extractor_ref: str = EXTRACTOR_REF,
) -> dict[str, Any]:
    """Bind supplied provider output to source identity without launching a provider.

    This is the owner-source adapter boundary for a future admitted provider. The
    caller supplies observations and provider identity; this function does not
    discover, install, trust, or activate that provider.
    """

    source_path = _normalized_path(path, field_name="path")
    lineage = _normalized_path(lineage_path or source_path, field_name="lineage_path")
    if not isinstance(language, str) or not language.strip():
        raise ValueError("language must be a non-empty string")
    if not isinstance(repo, str) or not repo.strip():
        raise ValueError("repo must be a non-empty string")
    if not isinstance(source_epoch, str) or not source_epoch:
        raise ValueError("source_epoch must be a non-empty string")
    if not isinstance(provider_id, str) or not provider_id.strip():
        raise ValueError("provider_id must be a non-empty string")
    if not isinstance(provider_version, str) or not provider_version.strip():
        raise ValueError("provider_version must be a non-empty string")
    if parse_status not in _PARSE_STATUSES:
        raise ValueError(f"unsupported provider parse status: {parse_status}")
    if provenance_mode not in _OBSERVATION_EVIDENCE_CLASSES:
        raise ValueError(f"unsupported provider provenance mode: {provenance_mode}")
    source_text, source_bytes = _content_bytes(content)
    del source_text
    content_digest = hashlib.sha256(source_bytes).hexdigest()
    config = dict(provider_config or {})
    config.setdefault("binding", "supplied")
    config["language"] = language
    parser_ref = f"{provider_id}@{provider_version}"
    config_digest = _canonical_digest(config)
    normalized_observations = _normalize_provider_observations(
        repo=str(repo),
        lineage_path=lineage,
        language=language,
        observations=observations,
    )
    batch = {
        "schema_version": OBSERVATION_SCHEMA_VERSION,
        "batch_id": qualified_id(
            repo,
            "code-observation-batch",
            f"{lineage}:{source_epoch}:{content_digest}:{parser_ref}:{config_digest}",
        ),
        "capability_class": CAPABILITY_CLASS,
        "provider": {
            "id": provider_id,
            "version": provider_version,
            "config_digest": config_digest,
            "config": config,
            "lane": provider_lane_posture(provider_id, supplied=True),
        },
        "source": {
            "repo": str(repo),
            "path": source_path,
            "lineage_path": lineage,
            "source_epoch": source_epoch,
            "content_digest": content_digest,
            "language": language,
        },
        "parse_status": parse_status,
        "observations": normalized_observations,
        "diagnostics": [copy.deepcopy(dict(diagnostic)) for diagnostic in diagnostics],
        "provenance": {
            "mode": provenance_mode,
            "extractor_ref": extractor_ref,
            "parser_ref": parser_ref,
            "source_refs": [
                {
                    "repo": str(repo),
                    "path": source_path,
                    "role": "primary_source",
                    "authority": "authored_source",
                }
            ],
        },
        "qualification": _qualification(normalized_observations, supplied=True),
    }
    for index, diagnostic in enumerate(batch["diagnostics"]):
        if not isinstance(diagnostic, dict) or not isinstance(
            diagnostic.get("kind"), str
        ) or not isinstance(diagnostic.get("message"), str):
            raise ValueError(f"provider diagnostic {index} must contain kind and message")
    return _with_currentness(
        batch,
        source_epoch=source_epoch,
        content_digest=content_digest,
        provider_id=provider_id,
        provider_version=provider_version,
        provider_config_digest=config_digest,
    )


def observe_python_source(
    *,
    repo: str,
    path: str,
    content: str | bytes,
    source_epoch: str,
    lineage_path: str | None = None,
    provider_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return one source-bound provider-neutral observation envelope."""

    source_path = _normalized_path(path, field_name="path")
    lineage = _normalized_path(lineage_path or source_path, field_name="lineage_path")
    if not repo or not str(repo).strip():
        raise ValueError("repo must not be empty")
    if not isinstance(source_epoch, str) or not source_epoch:
        raise ValueError("source_epoch must be a non-empty string")

    decode_error: UnicodeDecodeError | None = None
    try:
        source_text, source_bytes = _content_bytes(content)
    except UnicodeDecodeError as exc:
        if not isinstance(content, bytes):
            raise
        decode_error = exc
        source_text = ""
        source_bytes = content

    config = dict(DEFAULT_PROVIDER_CONFIG)
    if provider_config is not None:
        config.update(dict(provider_config))
    config["language"] = "python"
    include_calls = bool(config.get("include_calls", True))
    content_digest = hashlib.sha256(source_bytes).hexdigest()
    batch_id = qualified_id(
        repo,
        "code-observation-batch",
        f"{lineage}:{source_epoch}:{content_digest}",
    )
    tree, error = _parse_python(source_text)
    observations: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    parse_status = "parsed"
    if decode_error is not None:
        parse_status = "degraded"
        diagnostics.append(_encoding_diagnostic(decode_error))
    elif error is not None or tree is None:
        parse_status = "unparseable"
        if error is not None:
            diagnostics.append(_diagnostic(error))
    else:
        raw_observations = _visit_python_tree(
            str(repo),
            lineage,
            tree,
            include_calls=include_calls,
        )
        observations = [
            _normalized_observation(str(repo), lineage, observation)
            for observation in raw_observations
        ]

    batch = {
        "schema_version": OBSERVATION_SCHEMA_VERSION,
        "batch_id": batch_id,
        "capability_class": CAPABILITY_CLASS,
        "provider": {
            "id": PROVIDER_ID,
            "version": PROVIDER_VERSION,
            "config_digest": _canonical_digest(config),
            "config": config,
            "lane": provider_lane_posture(PROVIDER_ID),
        },
        "source": {
            "repo": str(repo),
            "path": source_path,
            "lineage_path": lineage,
            "source_epoch": source_epoch,
            "content_digest": content_digest,
            "language": "python",
        },
        "parse_status": parse_status,
        "observations": observations,
        "diagnostics": diagnostics,
        "provenance": {
            "mode": "deterministic",
            "extractor_ref": EXTRACTOR_REF,
            "parser_ref": PARSER_REF,
            "source_refs": [
                {
                    "repo": str(repo),
                    "path": source_path,
                    "role": "primary_source",
                    "authority": "authored_source",
                }
            ],
        },
        "qualification": _qualification(observations, supplied=False),
    }
    return _with_currentness(
        batch,
        source_epoch=source_epoch,
        content_digest=content_digest,
        provider_id=PROVIDER_ID,
        provider_version=PROVIDER_VERSION,
        provider_config_digest=str(batch["provider"]["config_digest"]),
    )


def language_for_path(path: str | PurePosixPath) -> str | None:
    """Return the supported code language for a relative source path."""

    suffix = PurePosixPath(str(path)).suffix.lower()
    if suffix in {".py", ".pyi"}:
        return "python"
    return _JS_LANGUAGE_SUFFIXES.get(suffix)


def _provider_for_language(language: str) -> tuple[str, str, str]:
    if language == "python":
        return PROVIDER_ID, PROVIDER_VERSION, PARSER_REF
    if language == "javascript":
        provider_id = JAVASCRIPT_PROVIDER_ID
    elif language == "typescript":
        provider_id = TYPESCRIPT_PROVIDER_ID
    else:
        raise ValueError(f"unsupported code language: {language}")
    return (
        provider_id,
        SECOND_LANGUAGE_PROVIDER_VERSION,
        f"{provider_id}@{SECOND_LANGUAGE_PROVIDER_VERSION}",
    )


_JS_CALL_RE = re.compile(
    r"(?<![\w$])([A-Za-z_$][\w$]*(?:\s*\.\s*[A-Za-z_$][\w$]*)?)\s*\("
)
_JS_FUNCTION_RE = re.compile(
    r"\b(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s*\*?\s*"
    r"([A-Za-z_$][\w$]*)"
)
_JS_CLASS_RE = re.compile(
    r"\b(?:export\s+(?:default\s+)?)?class\s+([A-Za-z_$][\w$]*)"
    r"(?:\s+extends\s+([A-Za-z_$][\w$]*(?:\s*\.\s*[A-Za-z_$][\w$]*)?))?"
)
_JS_ARROW_RE = re.compile(
    r"\b(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*"
    r"(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*"
    r"(?:\:\s*[^=;{]+?)?=>"
)
_JS_METHOD_RE = re.compile(
    r"(?<![\w$])(?:async\s+)?([A-Za-z_$][\w$]*)\s*\("
)
_JS_INTERFACE_RE = re.compile(
    r"\b(?:export\s+)?interface\s+([A-Za-z_$][\w$]*)"
    r"(?:\s+extends\s+([A-Za-z_$][\w$]*(?:\s*,\s*[A-Za-z_$][\w$]*)*))?"
)
_JS_TYPE_RE = re.compile(r"\b(?:export\s+)?type\s+([A-Za-z_$][\w$]*)\s*=")
_JS_IMPORT_FROM_RE = re.compile(
    r"^\s*import\s+(.+?)\s+from\s+['\"]([^'\"]+)['\"]"
)
_JS_IMPORT_SIDE_EFFECT_RE = re.compile(r"^\s*import\s+['\"]([^'\"]+)['\"]")
_JS_REQUIRE_RE = re.compile(
    r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*require\(\s*['\"]([^'\"]+)['\"]\s*\)"
)
_JS_RESERVED_CALL_NAMES = {
    "catch",
    "class",
    "constructor",
    "for",
    "function",
    "if",
    "import",
    "return",
    "switch",
    "while",
}


def _mask_javascript_line(line: str, state: dict[str, Any] | None = None) -> str:
    """Mask strings and comments while retaining line length for columns.

    ``state`` is carried by the lexical collector so a block comment or a
    template literal cannot leak declarations into a later source line. The
    optional argument keeps the helper useful as a stateless line masker for
    callers that only need one line.
    """

    mask_state = state if state is not None else {}
    chars = list(line)
    in_block_comment = bool(mask_state.get("in_block_comment", False))
    quote = mask_state.get("quote")
    if quote not in {None, "'", '"', "`"}:
        quote = None
    escaped = bool(mask_state.get("escaped", False))
    index = 0
    while index < len(chars):
        char = chars[index]
        next_char = chars[index + 1] if index + 1 < len(chars) else ""
        if in_block_comment:
            chars[index] = " "
            if char == "*" and next_char == "/":
                chars[index + 1] = " "
                in_block_comment = False
                index += 2
                continue
        elif quote is not None:
            chars[index] = " "
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in {"'", '"', "`"}:
            chars[index] = " "
            quote = char
            escaped = False
        elif char == "/" and next_char == "/":
            for rest in range(index, len(chars)):
                chars[rest] = " "
            break
        elif char == "/" and next_char == "*":
            chars[index] = " "
            chars[index + 1] = " "
            in_block_comment = True
            index += 2
            continue
        index += 1
    mask_state["in_block_comment"] = in_block_comment
    mask_state["quote"] = quote
    mask_state["escaped"] = escaped
    return "".join(chars)


def _js_location(line_number: int, column: int, width: int = 1) -> dict[str, int]:
    start = max(int(column), 1)
    return {
        "start_line": max(int(line_number), 1),
        "end_line": max(int(line_number), 1),
        "start_column": start,
        "end_column": max(start + max(int(width), 1), start + 1),
    }


class _JavaScriptObservationCollector:
    def __init__(
        self,
        repo: str,
        lineage_path: str,
        language: str,
        *,
        include_calls: bool = True,
    ) -> None:
        self.repo = repo
        self.lineage_path = lineage_path
        self.language = language
        self.include_calls = include_calls
        self.scope: list[dict[str, Any]] = []
        self.brace_depth = 0
        self.symbol_counts: dict[str, int] = {}
        self.symbols_by_scope: dict[str, dict[str, Any]] = {}
        self.symbols_by_label: dict[str, list[dict[str, Any]]] = {}
        self.observations: list[dict[str, Any]] = []
        self.mask_state: dict[str, Any] = {}

    def _roles_for(self, name: str, symbol_kind: str) -> list[str]:
        if symbol_kind in {"function", "method", "class"} and (
            name.startswith("test")
            or name.startswith("Test")
        ):
            return ["test"]
        return []

    def _qualified_name(self, name: str) -> str:
        return ".".join([*(str(frame["name"]) for frame in self.scope), name])

    def _symbol(
        self,
        name: str,
        symbol_kind: str,
        line_number: int,
        column: int,
    ) -> dict[str, Any]:
        qualified_name = self._qualified_name(name)
        semantic_key = _occurrence_key(
            f"{self.language}:{symbol_kind}:{qualified_name}",
            self.symbol_counts,
        )
        subject: dict[str, Any] = {
            "symbol_id": qualified_id(
                self.repo,
                "code-symbol",
                f"{self.lineage_path}:{semantic_key}",
            ),
            "qualified_name": qualified_name,
            "symbol_kind": symbol_kind,
            "label": name,
        }
        roles = self._roles_for(name, symbol_kind)
        if roles:
            subject["roles"] = roles
        self.symbols_by_scope[qualified_name] = subject
        self.symbols_by_label.setdefault(name, []).append(subject)
        self.observations.append(
            {
                "observation_kind": "symbol",
                "semantic_key": semantic_key,
                "subject": subject,
                "occurrence": _js_location(line_number, column, len(name)),
                "relation": None,
                "confidence": {"evidence_class": "deterministic", "value": 1.0},
            }
        )
        return subject

    def _relation(
        self,
        subject: Mapping[str, Any],
        kind: str,
        target_name: str,
        line_number: int,
        column: int,
    ) -> None:
        subject_name = str(subject["qualified_name"])
        semantic_key = (
            f"{self.language}:{kind}:{subject_name}:{line_number}:{column}:"
            f"{target_name}"
        )
        self.observations.append(
            {
                "observation_kind": "relation",
                "semantic_key": semantic_key,
                "subject": subject,
                "occurrence": _js_location(line_number, column),
                "relation": {
                    "kind": kind,
                    "target_name": target_name,
                    "resolution": "unresolved",
                },
                "confidence": {
                    "evidence_class": "inferred",
                    "value": 0.9 if kind == "inherits" else 0.75,
                },
            }
        )

    def _push_frame(self, name: str, kind: str, body_depth: int) -> None:
        self.scope.append(
            {
                "name": name,
                "kind": kind,
                "body_depth": body_depth,
            }
        )

    def _open_depth(self, masked: str, match_end: int) -> int | None:
        opening = masked.find("{", match_end)
        if opening < 0:
            return None
        return self.brace_depth + masked[:opening].count("{") + 1

    def _current_subject(self) -> dict[str, Any] | None:
        for index in range(len(self.scope) - 1, -1, -1):
            frame = self.scope[index]
            if frame["kind"] in {"function", "method"}:
                return self.symbols_by_scope.get(
                    ".".join(str(item["name"]) for item in self.scope[: index + 1])
                )
        return None

    def _record_imports(self, line: str, masked: str, line_number: int) -> None:
        match = _JS_IMPORT_FROM_RE.match(line)
        if match is not None:
            bindings, module = match.groups()
            names: list[tuple[str, str]] = []
            if bindings.strip().startswith("{"):
                inside = bindings.strip()[1:-1]
                for item in inside.split(","):
                    parts = re.split(r"\s+as\s+", item.strip())
                    if item.strip():
                        names.append((parts[-1].strip(), parts[0].strip()))
            elif bindings.strip().startswith("*"):
                namespace = re.search(r"\bas\s+([A-Za-z_$][\w$]*)", bindings)
                if namespace:
                    names.append((namespace.group(1), "*"))
            else:
                default_name = bindings.split(",", 1)[0].strip()
                if default_name:
                    names.append((default_name, "default"))
            for name, imported in names:
                column = max(line.find(name) + 1, 1)
                subject = self._symbol(name, "import", line_number, column)
                target = f"{module}.{imported}" if imported != "*" else module
                self._relation(subject, "imports", target, line_number, column)
            return
        side_effect = _JS_IMPORT_SIDE_EFFECT_RE.match(line)
        if side_effect is not None:
            module = side_effect.group(1)
            subject = self._symbol(module, "import", line_number, max(line.find(module) + 1, 1))
            self._relation(subject, "imports", module, line_number, max(line.find(module) + 1, 1))
            return
        require = _JS_REQUIRE_RE.search(line)
        if require is not None:
            name, module = require.groups()
            column = max(line.find(name) + 1, 1)
            subject = self._symbol(name, "import", line_number, column)
            self._relation(subject, "imports", module, line_number, column)

    def _record_calls(
        self,
        masked: str,
        line_number: int,
        declaration_spans: list[tuple[int, int]],
        subject_override: dict[str, Any] | None = None,
    ) -> None:
        if not self.include_calls:
            return
        subject = subject_override or self._current_subject()
        if subject is None:
            return
        for match in _JS_CALL_RE.finditer(masked):
            target_name = re.sub(r"\s+", "", match.group(1))
            label = target_name.rsplit(".", 1)[-1]
            if label in _JS_RESERVED_CALL_NAMES:
                continue
            if any(start <= match.start() < end for start, end in declaration_spans):
                continue
            self._relation(
                subject,
                "calls",
                target_name,
                line_number,
                match.start(1) + 1,
            )

    def _resolve_relations(self) -> None:
        for observation in self.observations:
            relation = observation.get("relation")
            if not isinstance(relation, Mapping):
                continue
            target_name = str(relation.get("target_name", ""))
            if not target_name:
                continue
            candidates: list[dict[str, Any] | None] = [
                self.symbols_by_scope.get(target_name)
            ]
            if "." not in target_name:
                candidates.extend(self.symbols_by_label.get(target_name, []))
            target = next((candidate for candidate in candidates if candidate), None)
            if target is not None:
                relation["resolution"] = "resolved_local"
                relation["target_symbol_id"] = target["symbol_id"]

    def collect(self, source_text: str) -> list[dict[str, Any]]:
        for line_number, line in enumerate(source_text.splitlines(), 1):
            masked = _mask_javascript_line(line, self.mask_state)
            while self.scope and self.brace_depth < int(self.scope[-1]["body_depth"]):
                self.scope.pop()

            self._record_imports(line, masked, line_number)
            declaration_spans: list[tuple[int, int]] = []
            line_subject: dict[str, Any] | None = None

            class_match = _JS_CLASS_RE.search(masked)
            if class_match is not None:
                name = class_match.group(1)
                column = class_match.start(1) + 1
                subject = self._symbol(name, "class", line_number, column)
                base = class_match.group(2)
                if base:
                    self._relation(
                        subject,
                        "inherits",
                        re.sub(r"\s+", "", base),
                        line_number,
                        column,
                    )
                opening_depth = self._open_depth(masked, class_match.end())
                if opening_depth is not None:
                    self._push_frame(name, "class", opening_depth)
                declaration_spans.append((class_match.start(), class_match.end()))

            interface_match = _JS_INTERFACE_RE.search(masked)
            if interface_match is not None:
                name = interface_match.group(1)
                subject = self._symbol(name, "interface", line_number, interface_match.start(1) + 1)
                if interface_match.group(2):
                    for base in interface_match.group(2).split(","):
                        self._relation(
                            subject,
                            "inherits",
                            base.strip(),
                            line_number,
                            interface_match.start(1) + 1,
                        )
                declaration_spans.append((interface_match.start(), interface_match.end()))

            type_match = _JS_TYPE_RE.search(masked)
            if type_match is not None:
                name = type_match.group(1)
                self._symbol(name, "type", line_number, type_match.start(1) + 1)
                declaration_spans.append((type_match.start(), type_match.end()))

            function_match = _JS_FUNCTION_RE.search(masked)
            if function_match is not None:
                name = function_match.group(1)
                column = function_match.start(1) + 1
                kind = (
                    "method"
                    if self.scope and self.scope[-1]["kind"] == "class"
                    else "function"
                )
                line_subject = self._symbol(name, kind, line_number, column)
                opening_depth = self._open_depth(masked, function_match.end())
                if opening_depth is not None:
                    self._push_frame(name, kind, opening_depth)
                declaration_spans.append((function_match.start(), function_match.end()))

            arrow_match = _JS_ARROW_RE.search(masked)
            if arrow_match is not None:
                name = arrow_match.group(1)
                column = arrow_match.start(1) + 1
                kind = (
                    "method"
                    if self.scope and self.scope[-1]["kind"] == "class"
                    else "function"
                )
                line_subject = self._symbol(name, kind, line_number, column)
                opening_depth = self._open_depth(masked, arrow_match.end())
                if opening_depth is not None:
                    self._push_frame(name, kind, opening_depth)
                declaration_spans.append((arrow_match.start(), arrow_match.end()))

            if self.scope and self.scope[-1]["kind"] == "class":
                for method_match in _JS_METHOD_RE.finditer(masked):
                    name = method_match.group(1)
                    if name in _JS_RESERVED_CALL_NAMES:
                        continue
                    if any(start <= method_match.start() < end for start, end in declaration_spans):
                        continue
                    column = method_match.start(1) + 1
                    self._symbol(name, "method", line_number, column)
                    opening_depth = self._open_depth(masked, method_match.end())
                    if opening_depth is not None:
                        self._push_frame(name, "method", opening_depth)
                    declaration_spans.append((method_match.start(), method_match.end()))
                    break

            self._record_calls(
                masked,
                line_number,
                declaration_spans,
                subject_override=line_subject,
            )
            self.brace_depth += masked.count("{") - masked.count("}")
            while self.scope and self.brace_depth < int(self.scope[-1]["body_depth"]):
                self.scope.pop()

        self._resolve_relations()
        return sorted(
            self.observations,
            key=lambda observation: (
                observation["occurrence"]["start_line"],
                observation["occurrence"]["start_column"],
                observation["observation_kind"],
                observation["semantic_key"],
            ),
        )


def _extract_javascript_observations(
    *,
    repo: str,
    path: str,
    content: str | bytes,
    lineage_path: str | None,
    language: str,
    include_calls: bool = True,
) -> list[dict[str, Any]]:
    try:
        source_text, _ = _content_bytes(content)
    except UnicodeDecodeError:
        return []
    source_path = _normalized_path(path, field_name="path")
    lineage = _normalized_path(lineage_path or source_path, field_name="lineage_path")
    return _JavaScriptObservationCollector(
        repo,
        lineage,
        language,
        include_calls=include_calls,
    ).collect(source_text)


def extract_javascript_observations(
    *,
    repo: str,
    path: str,
    content: str | bytes,
    lineage_path: str | None = None,
) -> list[dict[str, Any]]:
    return _extract_javascript_observations(
        repo=repo,
        path=path,
        content=content,
        lineage_path=lineage_path,
        language="javascript",
    )


def extract_typescript_observations(
    *,
    repo: str,
    path: str,
    content: str | bytes,
    lineage_path: str | None = None,
) -> list[dict[str, Any]]:
    return _extract_javascript_observations(
        repo=repo,
        path=path,
        content=content,
        lineage_path=lineage_path,
        language="typescript",
    )


_CTAGS_SYMBOL_KINDS = {
    "class": "class",
    "enum": "enum",
    "function": "function",
    "interface": "interface",
    "macro": "macro",
    "member": "member",
    "method": "method",
    "namespace": "namespace",
    "struct": "struct",
    "type": "type",
    "typedef": "type",
    "variable": "variable",
}


def parse_ctags_json_observations(
    payload: str | bytes,
    *,
    language: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse Ctags JSON as supplied observations; never infer admission."""

    if not isinstance(language, str) or not language.strip():
        raise ValueError("language must be a non-empty string")
    text, _ = _content_bytes(payload)
    observations: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            tag = json.loads(line)
        except json.JSONDecodeError as exc:
            diagnostics.append(
                {
                    "kind": "invalid_ctags_json",
                    "message": f"line {line_number}: {exc.msg}",
                    "line": line_number,
                }
            )
            continue
        if not isinstance(tag, Mapping) or tag.get("_type") != "tag":
            continue
        name = tag.get("name")
        kind = _CTAGS_SYMBOL_KINDS.get(str(tag.get("kind") or ""))
        tag_line = tag.get("line")
        if not isinstance(name, str) or not name or kind is None:
            continue
        if isinstance(tag_line, bool) or not isinstance(tag_line, int) or tag_line < 1:
            diagnostics.append(
                {
                    "kind": "invalid_ctags_location",
                    "message": f"tag {name!r} has no positive line",
                    "line": line_number,
                }
            )
            continue
        scope = tag.get("scope")
        qualified_name = (
            f"{scope}.{name}"
            if isinstance(scope, str) and scope
            else name
        )
        roles = ["test"] if name.startswith(("test", "Test")) else []
        semantic_key = f"{language}:ctags:{kind}:{qualified_name}:{tag_line}"
        observations.append(
            {
                "observation_kind": "symbol",
                "semantic_key": semantic_key,
                "subject": {
                    "qualified_name": qualified_name,
                    "symbol_kind": kind,
                    "label": name,
                    **({"roles": roles} if roles else {}),
                },
                "occurrence": {
                    "start_line": tag_line,
                    "end_line": tag_line,
                    "start_column": 1,
                    "end_column": max(len(name), 1),
                },
                "relation": None,
                "confidence": {"evidence_class": "observed", "value": 0.8},
            }
        )
    return observations, diagnostics


def observe_ctags_json_source(
    *,
    repo: str,
    path: str,
    content: str | bytes,
    source_epoch: str,
    ctags_json: str | bytes,
    provider_version: str,
    language: str,
    lineage_path: str | None = None,
) -> dict[str, Any]:
    """Bind real or supplied Ctags JSON to source identity as untrusted input."""

    observations, diagnostics = parse_ctags_json_observations(
        ctags_json,
        language=language,
    )
    return normalize_provider_observations(
        repo=repo,
        path=path,
        content=content,
        source_epoch=source_epoch,
        language=language,
        provider_id=CTAGS_PROVIDER_ID,
        provider_version=provider_version,
        observations=observations,
        lineage_path=lineage_path,
        parse_status="degraded" if diagnostics else "parsed",
        diagnostics=diagnostics,
        provenance_mode="observed",
        extractor_ref=CTAGS_EXTRACTOR_REF,
    )


def _machine_digest(value: object) -> bool:
    return bool(
        isinstance(value, str)
        and re.fullmatch(r"sha256:[0-9a-f]{64}", value)
    )


def _machine_evidence_ref(value: object) -> bool:
    return bool(
        isinstance(value, str)
        and value == value.strip()
        and re.fullmatch(r"[a-z][a-z0-9+.-]*:[^\s]+", value)
    )


def _machine_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    normalized = value[:-1] + "+00:00" if value.endswith(("Z", "z")) else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _machine_binding_snapshot(envelope: Mapping[str, Any]) -> dict[str, Any]:
    provider = envelope["provider"]
    source = envelope["source"]
    provenance = envelope["provenance"]
    return {
        "schema_version": MACHINE_PROVIDER_BINDING_SCHEMA,
        "observation_schema": MACHINE_OBSERVATION_SCHEMA,
        "consumer_abi": copy.deepcopy(MACHINE_CONSUMER_ABI),
        "provider": {
            **copy.deepcopy(MACHINE_PROVIDER_BINDING["provider"]),
            "config_digest": str(provider["config_digest"]),
        },
        "candidate_artifact": copy.deepcopy(MACHINE_PROVIDER_BINDING["artifact"]),
        "source": {
            "owner": str(source["owner"]),
            "ref": str(source["ref"]),
            "epoch": str(source["epoch"]),
            "binding_status": str(source["binding_status"]),
        },
        "provenance": {
            "evidence_ref": str(provenance["evidence_ref"]),
            "binding_status": str(provenance["binding_status"]),
        },
        "admission": {
            "status": "not_admitted",
            "trust_ref": "untrusted",
            "installation": "not_installed",
            "activation": "not_active",
        },
        "semantic": {
            "status": "unproven",
            "proof_owner": "aoa-evals",
        },
        "claim_limit": (
            "machine envelope is caller-supplied source-bound input only; "
            "it is not installation, admission, runtime health, semantic proof, "
            "or owner acceptance"
        ),
    }


def validate_machine_provider_binding(
    envelope: Mapping[str, Any],
    *,
    repo: str,
    path: str,
    content: str | bytes,
    source_epoch: str,
    language: str,
    lineage_path: str | None = None,
) -> dict[str, Any]:
    """Validate the exact G59 envelope without installing or admitting Ctags.

    The machine envelope is intentionally treated as a future provider input.
    Only a bound source/provenance envelope is accepted for normalization, and
    the returned snapshot keeps the candidate explicitly unsigned/unadmitted.
    """

    if not isinstance(envelope, Mapping):
        raise ValueError("machine observation envelope must be an object")
    if envelope.get("schema") != MACHINE_OBSERVATION_SCHEMA:
        raise ValueError("machine observation envelope schema is unsupported")
    if envelope.get("version") != "0.1.0":
        raise ValueError("machine observation envelope contract version is unsupported")
    if not _machine_timestamp(envelope.get("generated_at")):
        raise ValueError("machine observation envelope generated_at is invalid")
    provider = envelope.get("provider")
    source = envelope.get("source")
    provenance = envelope.get("provenance")
    lineage = envelope.get("lineage")
    semantic = envelope.get("semantic")
    policy = envelope.get("policy")
    records = envelope.get("records")
    if not all(
        isinstance(item, Mapping)
        for item in (provider, source, provenance, lineage, semantic, policy)
    ):
        raise ValueError("machine observation envelope is missing boundary objects")
    if not isinstance(records, list) or any(
        not isinstance(record, Mapping) for record in records
    ):
        raise ValueError("machine observation envelope records must be objects")
    if envelope.get("record_count") != len(records):
        raise ValueError("machine observation envelope record_count mismatch")
    if provider.get("id") != CTAGS_PROVIDER_ID:
        raise ValueError("machine observation envelope provider is not Universal Ctags")
    if provider.get("owner") != "abyss-machine":
        raise ValueError("machine observation envelope provider owner is invalid")
    if not _machine_digest(provider.get("config_digest")):
        raise ValueError("machine observation envelope provider config digest is invalid")
    if source.get("owner") != "abyss-machine":
        raise ValueError("machine observation envelope source owner is invalid")
    if not _machine_evidence_ref(source.get("ref")):
        raise ValueError("machine observation envelope source ref is not bound")
    if not _machine_digest(source.get("epoch")):
        raise ValueError("machine observation envelope source epoch is invalid")
    if str(source.get("epoch")) != str(source_epoch):
        raise ValueError("machine observation envelope source epoch mismatch")
    if source.get("binding_status") != "bound":
        raise ValueError("machine observation envelope source is not bound")
    if not _machine_evidence_ref(provenance.get("evidence_ref")):
        raise ValueError("machine observation envelope provenance is not bound")
    if provenance.get("binding_status") != "bound":
        raise ValueError("machine observation envelope provenance is not bound")
    if lineage.get("derived_from_source") is not True:
        raise ValueError("machine observation envelope lineage is not source-derived")
    if lineage.get("canonical_source") != "owner_repository":
        raise ValueError("machine observation envelope canonical source is invalid")
    if lineage.get("observation_consumer") != "aoa-kag":
        raise ValueError("machine observation envelope consumer is invalid")
    if semantic.get("status") != "unproven":
        raise ValueError("machine observation envelope semantic status must be unproven")
    if semantic.get("proof_owner") != "aoa-evals":
        raise ValueError("machine observation envelope proof owner is invalid")
    if semantic.get("admission_is_not_semantic_proof") is not True:
        raise ValueError("machine observation envelope semantic boundary is invalid")
    if policy.get("machine_layer_materializes_no_kag_truth") is not True:
        raise ValueError("machine observation envelope policy is invalid")
    if policy.get("unbound_source_or_provenance_is_not_admitted") is not True:
        raise ValueError("machine observation envelope fail-closed policy is invalid")
    if str(language).casefold() != "python":
        raise ValueError("the exact G59 Universal Ctags interface is Python-only")

    normalized_records: list[Mapping[str, Any]]
    ctags_lines = ""
    has_canonical = any("observation_kind" in record for record in records)
    if has_canonical:
        if not all("observation_kind" in record for record in records):
            raise ValueError("machine observation records must not mix canonical and Ctags shapes")
        normalized_records = records
        diagnostics: list[dict[str, Any]] = []
    else:
        ctags_lines = "\n".join(
            json.dumps(dict(record), ensure_ascii=False, sort_keys=True)
            for record in records
        )
        parsed, diagnostics = parse_ctags_json_observations(
            ctags_lines,
            language="python",
        )
        normalized_records = parsed

    snapshot = _machine_binding_snapshot(envelope)
    batch = normalize_provider_observations(
        repo=repo,
        path=path,
        content=content,
        source_epoch=str(source_epoch),
        language="python",
        provider_id=CTAGS_PROVIDER_ID,
        provider_version=MACHINE_PROVIDER_VERSION,
        observations=normalized_records,
        lineage_path=lineage_path,
        provider_config={
            "binding": "abyss-machine-envelope",
            "machine_envelope_schema": MACHINE_OBSERVATION_SCHEMA,
            "machine_provider_config_digest": str(provider["config_digest"]),
            "machine_source_ref": str(source["ref"]),
            "machine_generated_at": str(envelope["generated_at"]),
            "consumer_abi": copy.deepcopy(MACHINE_CONSUMER_ABI),
        },
        parse_status="degraded" if diagnostics else "parsed",
        diagnostics=diagnostics,
        provenance_mode="observed",
        extractor_ref="abyss-machine:src/abyss_machine/code_intelligence_contracts.py#code_observation_envelope",
    )
    batch["machine_binding"] = snapshot
    return batch


def normalize_machine_observation_envelope(
    envelope: Mapping[str, Any],
    *,
    repo: str,
    path: str,
    content: str | bytes,
    source_epoch: str,
    language: str,
    lineage_path: str | None = None,
) -> dict[str, Any]:
    """Compatibility name for the fail-closed G59 source adapter."""

    return validate_machine_provider_binding(
        envelope,
        repo=repo,
        path=path,
        content=content,
        source_epoch=source_epoch,
        language=language,
        lineage_path=lineage_path,
    )


def _observe_lexical_source(
    *,
    repo: str,
    path: str,
    content: str | bytes,
    source_epoch: str,
    lineage_path: str | None,
    language: str,
    provider_config: Mapping[str, Any] | None,
) -> dict[str, Any]:
    source_path = _normalized_path(path, field_name="path")
    lineage = _normalized_path(lineage_path or source_path, field_name="lineage_path")
    if not repo or not str(repo).strip():
        raise ValueError("repo must not be empty")
    if not isinstance(source_epoch, str) or not source_epoch:
        raise ValueError("source_epoch must be a non-empty string")
    provider_id, provider_version, parser_ref = _provider_for_language(language)
    config: dict[str, Any] = {
        "include_calls": True,
        "language": language,
        "parser": "deterministic-lexical",
    }
    if provider_config is not None:
        config.update(dict(provider_config))
    config["language"] = language
    decode_error: UnicodeDecodeError | None = None
    try:
        source_text, source_bytes = _content_bytes(content)
    except UnicodeDecodeError as exc:
        if not isinstance(content, bytes):
            raise
        decode_error = exc
        source_text = ""
        source_bytes = content
    content_digest = hashlib.sha256(source_bytes).hexdigest()
    batch_id = qualified_id(
        repo,
        "code-observation-batch",
        f"{lineage}:{source_epoch}:{content_digest}",
    )
    diagnostics: list[dict[str, Any]] = []
    if decode_error is not None:
        parse_status = "degraded"
        diagnostics.append(_encoding_diagnostic(decode_error))
        observations: list[dict[str, Any]] = []
    else:
        collector = _JavaScriptObservationCollector(
            str(repo),
            lineage,
            language,
            include_calls=bool(config.get("include_calls", True)),
        )
        raw_observations = collector.collect(source_text)
        if collector.brace_depth != 0:
            parse_status = "unparseable"
            diagnostics.append(
                {
                    "kind": "unbalanced_braces",
                    "message": "source braces are unbalanced; code observations were withheld",
                }
            )
            observations = []
        else:
            parse_status = "parsed"
            observations = [
                _normalized_observation(str(repo), lineage, observation)
                for observation in raw_observations
            ]
    batch = {
        "schema_version": OBSERVATION_SCHEMA_VERSION,
        "batch_id": batch_id,
        "capability_class": CAPABILITY_CLASS,
        "provider": {
            "id": provider_id,
            "version": provider_version,
            "config_digest": _canonical_digest(config),
            "config": config,
            "lane": provider_lane_posture(provider_id),
        },
        "source": {
            "repo": str(repo),
            "path": source_path,
            "lineage_path": lineage,
            "source_epoch": source_epoch,
            "content_digest": content_digest,
            "language": language,
        },
        "parse_status": parse_status,
        "observations": observations,
        "diagnostics": diagnostics,
        "provenance": {
            "mode": "deterministic",
            "extractor_ref": EXTRACTOR_REF,
            "parser_ref": parser_ref,
            "source_refs": [
                {
                    "repo": str(repo),
                    "path": source_path,
                    "role": "primary_source",
                    "authority": "authored_source",
                }
            ],
        },
        "qualification": _qualification(observations, supplied=False),
    }
    return _with_currentness(
        batch,
        source_epoch=source_epoch,
        content_digest=content_digest,
        provider_id=provider_id,
        provider_version=provider_version,
        provider_config_digest=str(batch["provider"]["config_digest"]),
    )


def observe_javascript_source(
    *,
    repo: str,
    path: str,
    content: str | bytes,
    source_epoch: str,
    lineage_path: str | None = None,
    provider_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return _observe_lexical_source(
        repo=repo,
        path=path,
        content=content,
        source_epoch=source_epoch,
        lineage_path=lineage_path,
        language="javascript",
        provider_config=provider_config,
    )


def observe_typescript_source(
    *,
    repo: str,
    path: str,
    content: str | bytes,
    source_epoch: str,
    lineage_path: str | None = None,
    provider_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return _observe_lexical_source(
        repo=repo,
        path=path,
        content=content,
        source_epoch=source_epoch,
        lineage_path=lineage_path,
        language="typescript",
        provider_config=provider_config,
    )


def observe_source(
    *,
    repo: str,
    path: str,
    content: str | bytes,
    source_epoch: str,
    language: str | None = None,
    lineage_path: str | None = None,
    provider_config: Mapping[str, Any] | None = None,
    provider_batch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    detected_language = language_for_path(path)
    requested_language = (
        str(language).strip().casefold()
        if language is not None
        else detected_language
    )
    if requested_language not in {"python", "javascript", "typescript"}:
        raise ValueError(f"unsupported code path: {path}")
    if detected_language is not None and detected_language != requested_language:
        raise ValueError(
            "code observation language does not match the source path: "
            f"path={path!r} language={requested_language!r}"
        )
    if provider_batch is not None:
        if not isinstance(provider_batch, Mapping):
            raise ValueError("provider observation batch must be an object")
        if provider_batch.get("schema") == MACHINE_OBSERVATION_SCHEMA:
            return normalize_machine_observation_envelope(
                provider_batch,
                repo=repo,
                path=path,
                content=content,
                source_epoch=source_epoch,
                language=requested_language,
                lineage_path=lineage_path,
            )
        return validate_provider_observation_batch(
            provider_batch,
            repo=repo,
            path=path,
            content=content,
            source_epoch=source_epoch,
            language=requested_language,
            lineage_path=lineage_path,
        )
    if requested_language == "python":
        return observe_python_source(
            repo=repo,
            path=path,
            content=content,
            source_epoch=source_epoch,
            lineage_path=lineage_path,
            provider_config=provider_config,
        )
    if requested_language == "javascript":
        return observe_javascript_source(
            repo=repo,
            path=path,
            content=content,
            source_epoch=source_epoch,
            lineage_path=lineage_path,
            provider_config=provider_config,
        )
    if requested_language == "typescript":
        return observe_typescript_source(
            repo=repo,
            path=path,
            content=content,
            source_epoch=source_epoch,
            lineage_path=lineage_path,
            provider_config=provider_config,
        )
    raise AssertionError(f"unsupported code language: {requested_language!r}")


def validate_provider_observation_batch(
    batch: Mapping[str, Any],
    *,
    repo: str,
    path: str,
    content: str | bytes,
    source_epoch: str,
    language: str,
    lineage_path: str | None = None,
) -> dict[str, Any]:
    """Validate and rebind a supplied canonical batch to the current source."""

    if not isinstance(batch, Mapping):
        raise ValueError("provider observation batch must be an object")
    bound = copy.deepcopy(dict(batch))
    if bound.get("schema_version") != OBSERVATION_SCHEMA_VERSION:
        raise ValueError("provider observation batch schema version is unsupported")
    if bound.get("capability_class") != CAPABILITY_CLASS:
        raise ValueError("provider observation batch capability class is unsupported")
    parse_status = bound.get("parse_status")
    if parse_status not in _PARSE_STATUSES:
        raise ValueError("provider observation batch parse status is unsupported")
    if not isinstance(repo, str) or not repo.strip():
        raise ValueError("repo must be a non-empty string")
    if not isinstance(source_epoch, str) or not source_epoch:
        raise ValueError("source_epoch must be a non-empty string")
    if language not in {"python", "javascript", "typescript"}:
        raise ValueError("provider observation batch language is unsupported")
    source = bound.get("source")
    provider = bound.get("provider")
    if not isinstance(source, Mapping) or not isinstance(provider, Mapping):
        raise ValueError("provider observation batch needs source and provider identities")
    expected_path = _normalized_path(path, field_name="path")
    expected_lineage = _normalized_path(
        lineage_path or expected_path,
        field_name="lineage_path",
    )
    source_path = _normalized_path(str(source.get("path") or ""), field_name="source.path")
    source_lineage = _normalized_path(
        str(source.get("lineage_path") or ""),
        field_name="source.lineage_path",
    )
    if str(source.get("repo")) != str(repo):
        raise ValueError("provider observation batch repository identity mismatch")
    if source_path != expected_path:
        raise ValueError(
            f"provider observation batch path mismatch: expected={expected_path!r} actual={source_path!r}"
        )
    if source_lineage != expected_lineage:
        raise ValueError(
            "provider observation batch lineage mismatch: "
            f"expected={expected_lineage!r} actual={source_lineage!r}"
        )
    if str(source.get("source_epoch")) != str(source_epoch):
        raise ValueError("provider observation batch source epoch mismatch")
    if str(source.get("language")) != str(language):
        raise ValueError("provider observation batch language mismatch")
    _, source_bytes = _content_bytes(content)
    expected_digest = hashlib.sha256(source_bytes).hexdigest()
    if str(source.get("content_digest")) != expected_digest:
        raise ValueError("provider observation batch content digest mismatch")
    provider_id = provider.get("id")
    provider_version = provider.get("version")
    provider_config = provider.get("config")
    provider_config_digest = provider.get("config_digest")
    if not isinstance(provider_id, str) or not provider_id:
        raise ValueError("provider observation batch provider id is missing")
    if not isinstance(provider_version, str) or not provider_version:
        raise ValueError("provider observation batch provider version is missing")
    provider_lane = provider_lane_posture(provider_id, supplied=True)
    supplied_lane = provider.get("lane")
    if supplied_lane is not None:
        if not isinstance(supplied_lane, Mapping):
            raise ValueError("provider observation batch provider lane is invalid")
        if dict(supplied_lane) != provider_lane:
            raise ValueError(
                "provider observation batch provider lane must remain supplied and unadmitted"
            )
    provider["lane"] = provider_lane
    if not isinstance(provider_config, Mapping):
        raise ValueError("provider observation batch provider config is missing")
    if str(provider_config_digest) != _canonical_digest(provider_config):
        raise ValueError("provider observation batch provider config digest mismatch")
    batch_id = bound.get("batch_id")
    parser_ref = f"{provider_id}@{provider_version}"
    expected_batch_ids = {
        qualified_id(
            str(repo),
            "code-observation-batch",
            f"{expected_lineage}:{source_epoch}:{expected_digest}",
        ),
        qualified_id(
            str(repo),
            "code-observation-batch",
            f"{expected_lineage}:{source_epoch}:{expected_digest}:{parser_ref}:{provider_config_digest}",
        ),
    }
    if not isinstance(batch_id, str) or batch_id not in expected_batch_ids:
        raise ValueError("provider observation batch id is not bound to its source identity")

    provenance = bound.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ValueError("provider observation batch provenance is missing")
    if provenance.get("mode") not in _OBSERVATION_EVIDENCE_CLASSES:
        raise ValueError("provider observation batch provenance mode is invalid")
    extractor_ref = provenance.get("extractor_ref")
    if not isinstance(extractor_ref, str) or not extractor_ref:
        raise ValueError("provider observation batch provenance extractor is missing")
    if provenance.get("parser_ref") != parser_ref:
        raise ValueError("provider observation batch provenance parser mismatch")
    source_refs = provenance.get("source_refs")
    if not isinstance(source_refs, list) or not source_refs:
        raise ValueError("provider observation batch provenance source refs are missing")
    has_primary_source = False
    for index, source_ref in enumerate(source_refs):
        if not isinstance(source_ref, Mapping):
            raise ValueError(f"provider observation source ref {index} must be an object")
        source_ref_repo = source_ref.get("repo")
        source_ref_path = source_ref.get("path")
        if not isinstance(source_ref_repo, str) or not source_ref_repo:
            raise ValueError(f"provider observation source ref {index} repository is invalid")
        normalized_ref_path = _normalized_path(
            str(source_ref_path or ""),
            field_name=f"provider observation source ref {index} path",
        )
        if source_ref.get("role") not in {"primary_source", "supporting_source"}:
            raise ValueError(f"provider observation source ref {index} role is invalid")
        if source_ref.get("authority") not in {
            "authored_source",
            "declared_config",
            "derived_projection",
        }:
            raise ValueError(
                f"provider observation source ref {index} authority is invalid"
            )
        if (
            source_ref.get("role") == "primary_source"
            and source_ref_repo == str(repo)
            and normalized_ref_path == expected_path
        ):
            has_primary_source = True
    if not has_primary_source:
        raise ValueError("provider observation provenance has no matching primary source")

    diagnostics = bound.get("diagnostics")
    if not isinstance(diagnostics, list):
        raise ValueError("provider observation batch diagnostics must be a list")
    for index, diagnostic in enumerate(diagnostics):
        if not isinstance(diagnostic, Mapping):
            raise ValueError(f"provider diagnostic {index} must be an object")
        if not isinstance(diagnostic.get("kind"), str) or not diagnostic["kind"]:
            raise ValueError(f"provider diagnostic {index} kind is invalid")
        if not isinstance(diagnostic.get("message"), str) or not diagnostic["message"]:
            raise ValueError(f"provider diagnostic {index} message is invalid")

    observations = bound.get("observations")
    if not isinstance(observations, list):
        raise ValueError("provider observation batch observations must be a list")
    observation_ids: set[str] = set()
    semantic_keys: set[str] = set()
    for index, observation in enumerate(observations):
        if not isinstance(observation, Mapping):
            raise ValueError(f"provider observation {index} must be an object")
        observation_id = observation.get("observation_id")
        if not isinstance(observation_id, str) or not observation_id:
            raise ValueError(f"provider observation {index} observation_id is missing")
        if observation_id in observation_ids:
            raise ValueError("provider observation ids must be unique")
        observation_ids.add(observation_id)
        semantic_key = observation.get("semantic_key")
        if not isinstance(semantic_key, str) or not semantic_key:
            raise ValueError(f"provider observation {index} semantic_key is missing")
        if semantic_key in semantic_keys:
            raise ValueError("provider observation semantic keys must be unique")
        semantic_keys.add(semantic_key)
        expected_observation_id = qualified_id(
            str(repo),
            "code-observation",
            f"{expected_lineage}:{semantic_key}",
        )
        if observation_id != expected_observation_id:
            raise ValueError(
                f"provider observation {index} id is not bound to its semantic key"
            )
        if observation.get("observation_kind") not in _OBSERVATION_KINDS:
            raise ValueError(f"provider observation {index} observation_kind is invalid")
        if observation.get("capability_class") != CAPABILITY_CLASS:
            raise ValueError(f"provider observation {index} capability class is invalid")
        _validated_canonical_subject(
            observation.get("subject"),
            observation_index=index,
        )
        _validate_occurrence(observation.get("occurrence"), observation_index=index)
        if observation.get("observation_kind") == "symbol" and observation.get("relation") is not None:
            raise ValueError(
                f"provider observation {index} symbol observations cannot carry relations"
            )
        _validate_canonical_relation(
            observation.get("relation"),
            observation_index=index,
        )
        _validated_confidence(observation.get("confidence"), observation_index=index)
    bound["qualification"] = _validated_qualification(
        bound.get("qualification"),
        supplied=True,
        observations=observations,
    )
    return _with_currentness(
        bound,
        source_epoch=source_epoch,
        content_digest=expected_digest,
        provider_id=provider_id,
        provider_version=provider_version,
        provider_config_digest=str(provider_config_digest),
    )


def extract_source_observations(
    *,
    repo: str,
    path: str,
    content: str | bytes,
    lineage_path: str | None = None,
) -> list[dict[str, Any]]:
    language = language_for_path(path)
    if language == "python":
        return extract_python_observations(
            repo=repo,
            path=path,
            content=content,
            lineage_path=lineage_path,
        )
    if language in {"javascript", "typescript"}:
        return _extract_javascript_observations(
            repo=repo,
            path=path,
            content=content,
            lineage_path=lineage_path,
            language=language,
        )
    return []

def _source_summary(batch: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if batch is None:
        return None
    source = batch["source"]
    return {
        "batch_id": str(batch["batch_id"]),
        "repo": str(source["repo"]),
        "path": str(source["path"]),
        "lineage_path": str(source["lineage_path"]),
        "source_epoch": str(source["source_epoch"]),
        "content_digest": str(source["content_digest"]),
        "language": str(source.get("language", "python")),
    }


def _provider_summary(batch: Mapping[str, Any] | None) -> dict[str, str] | None:
    if batch is None:
        return None
    provider = batch.get("provider")
    if not isinstance(provider, Mapping):
        return None
    return {
        "id": str(provider.get("id", "")),
        "version": str(provider.get("version", "")),
        "config_digest": str(provider.get("config_digest", "")),
    }


def _validate_delta_identity(
    before: Mapping[str, Any] | None,
    after: Mapping[str, Any] | None,
) -> None:
    if before is None or after is None:
        return
    before_source = before.get("source")
    after_source = after.get("source")
    if not isinstance(before_source, Mapping) or not isinstance(after_source, Mapping):
        raise ValueError("observation batches must contain source identity")
    before_repo = str(before_source.get("repo", ""))
    after_repo = str(after_source.get("repo", ""))
    if not before_repo or not after_repo:
        raise ValueError("repository identity is missing from observation batches")
    if before_repo != after_repo:
        raise ValueError(
            "repository identity mismatch: "
            f"before={before_repo!r} after={after_repo!r}"
        )
    before_provider = _provider_summary(before)
    after_provider = _provider_summary(after)
    if before_provider is None or after_provider is None:
        raise ValueError("provider identity is missing from observation batches")
    if before_provider != after_provider:
        raise ValueError(
            "provider identity mismatch: "
            f"before={before_provider!r} after={after_provider!r}"
        )


def _observation_map(batch: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    if batch is None:
        return {}
    return {
        str(observation["observation_id"]): observation
        for observation in batch.get("observations", [])
    }


def _observation_digest(observation: Mapping[str, Any]) -> str:
    return _canonical_digest(observation)


def _subject_symbol_id(observation: Mapping[str, Any]) -> str | None:
    subject = observation.get("subject")
    if not isinstance(subject, Mapping):
        return None
    symbol_id = subject.get("symbol_id")
    return None if symbol_id is None else str(symbol_id)


def _target_symbol_id(observation: Mapping[str, Any]) -> str | None:
    relation = observation.get("relation")
    if not isinstance(relation, Mapping):
        return None
    target_symbol_id = relation.get("target_symbol_id")
    return None if target_symbol_id is None else str(target_symbol_id)


def _delta_qualification(batch: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if batch is None:
        return None
    qualification = batch.get("qualification")
    materialization = (
        qualification.get("materialization")
        if isinstance(qualification, Mapping)
        else None
    )
    if not isinstance(materialization, Mapping):
        raise ValueError("observation batch qualification is missing")
    supplied = str(materialization.get("trust_ref") or "") == "untrusted"
    observations = batch.get("observations")
    if not isinstance(observations, list):
        raise ValueError("observation batch observations must be a list")
    return _validated_qualification(
        qualification,
        supplied=supplied,
        observations=observations,
    )


def _path_change_kind(before_path: str, after_path: str) -> str:
    if before_path == after_path:
        return "unchanged"
    before_value = PurePosixPath(before_path)
    after_value = PurePosixPath(after_path)
    if before_value.parent == after_value.parent:
        return "rename"
    return "move"


def _observation_signature(observation: Mapping[str, Any]) -> tuple[str, str, str, str]:
    subject = observation.get("subject")
    if not isinstance(subject, Mapping):
        return (str(observation.get("observation_kind") or ""), "", "", "")
    return (
        str(observation.get("observation_kind") or ""),
        str(subject.get("symbol_kind") or ""),
        str(subject.get("qualified_name") or ""),
        str(subject.get("label") or ""),
    )


def _symbol_similarity(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> float:
    before_signature = _observation_signature(before)
    after_signature = _observation_signature(after)
    if before_signature[0] != "symbol" or after_signature[0] != "symbol":
        return 0.0
    if before_signature[1] != after_signature[1]:
        return 0.0
    before_name = before_signature[2].rsplit(".", 1)[-1].casefold()
    after_name = after_signature[2].rsplit(".", 1)[-1].casefold()
    if before_name == after_name:
        return 0.95
    before_label = before_signature[3].casefold()
    after_label = after_signature[3].casefold()
    return max(
        difflib.SequenceMatcher(None, before_name, after_name).ratio(),
        difflib.SequenceMatcher(None, before_label, after_label).ratio(),
    )


def _lineage_matches(
    before_map: Mapping[str, Mapping[str, Any]],
    after_map: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    matched_before: set[str] = set()
    matched_after: set[str] = set()

    for observation_id in sorted(set(before_map) & set(after_map)):
        matches.append(
            {
                "before_observation_id": observation_id,
                "after_observation_id": observation_id,
                "match_kind": "stable_observation_id",
                "confidence": {"evidence_class": "deterministic", "value": 1.0},
            }
        )
        matched_before.add(observation_id)
        matched_after.add(observation_id)

    def unique_by(key: str, candidates: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
        grouped: dict[str, list[str]] = {}
        for observation_id, observation in candidates.items():
            if observation_id in (matched_before if candidates is before_map else matched_after):
                continue
            grouped.setdefault(str(observation.get(key) or ""), []).append(observation_id)
        return {
            value: ids[0]
            for value, ids in grouped.items()
            if value and len(ids) == 1
        }

    before_by_semantic = unique_by("semantic_key", before_map)
    after_by_semantic = unique_by("semantic_key", after_map)
    for semantic_key in sorted(set(before_by_semantic) & set(after_by_semantic)):
        before_id = before_by_semantic[semantic_key]
        after_id = after_by_semantic[semantic_key]
        if before_id in matched_before or after_id in matched_after:
            continue
        matches.append(
            {
                "before_observation_id": before_id,
                "after_observation_id": after_id,
                "match_kind": "stable_semantic_key",
                "confidence": {"evidence_class": "declared", "value": 0.95},
            }
        )
        matched_before.add(before_id)
        matched_after.add(after_id)

    before_by_signature: dict[tuple[str, str, str, str], list[str]] = {}
    after_by_signature: dict[tuple[str, str, str, str], list[str]] = {}
    for observation_id, observation in before_map.items():
        if observation_id not in matched_before:
            before_by_signature.setdefault(_observation_signature(observation), []).append(observation_id)
    for observation_id, observation in after_map.items():
        if observation_id not in matched_after:
            after_by_signature.setdefault(_observation_signature(observation), []).append(observation_id)
    for signature in sorted(set(before_by_signature) & set(after_by_signature)):
        before_ids = before_by_signature[signature]
        after_ids = after_by_signature[signature]
        if len(before_ids) != 1 or len(after_ids) != 1:
            continue
        before_id, after_id = before_ids[0], after_ids[0]
        matches.append(
            {
                "before_observation_id": before_id,
                "after_observation_id": after_id,
                "match_kind": "stable_symbol_signature",
                "confidence": {"evidence_class": "inferred", "value": 0.9},
            }
        )
        matched_before.add(before_id)
        matched_after.add(after_id)
    return sorted(
        matches,
        key=lambda item: (
            item["before_observation_id"],
            item["after_observation_id"],
        ),
    )


def _transformation_alternatives(
    before_map: Mapping[str, Mapping[str, Any]],
    after_map: Mapping[str, Mapping[str, Any]],
    matches: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    matched_before = {str(item["before_observation_id"]) for item in matches}
    matched_after = {str(item["after_observation_id"]) for item in matches}
    before_symbols = {
        observation_id: observation
        for observation_id, observation in before_map.items()
        if observation_id not in matched_before
        and _observation_signature(observation)[0] == "symbol"
    }
    after_symbols = {
        observation_id: observation
        for observation_id, observation in after_map.items()
        if observation_id not in matched_after
        and _observation_signature(observation)[0] == "symbol"
    }
    candidates_by_before: dict[str, list[tuple[float, str]]] = {}
    candidates_by_after: dict[str, list[tuple[float, str]]] = {}
    for before_id, before in before_symbols.items():
        for after_id, after in after_symbols.items():
            score = _symbol_similarity(before, after)
            if score < 0.45:
                continue
            candidates_by_before.setdefault(before_id, []).append((score, after_id))
            candidates_by_after.setdefault(after_id, []).append((score, before_id))

    alternatives: list[dict[str, Any]] = []
    emitted: set[tuple[str, tuple[str, ...], tuple[str, ...]]] = set()

    def add_alternative(
        kind: str,
        before_ids: Sequence[str],
        after_ids: Sequence[str],
        confidence: float,
        reason: str,
    ) -> None:
        key = (kind, tuple(sorted(before_ids)), tuple(sorted(after_ids)))
        if key in emitted:
            return
        emitted.add(key)
        alternatives.append(
            {
                "kind": kind,
                "before_observation_ids": sorted(before_ids),
                "after_observation_ids": sorted(after_ids),
                "confidence": {
                    "evidence_class": "inferred",
                    "value": round(min(max(confidence, 0.0), 1.0), 3),
                },
                "selected": False,
                "reason": reason,
                "claim_limit": "candidate lineage only; requires owner/provider review",
            }
        )

    for before_id, candidates in candidates_by_before.items():
        if len(candidates) >= 2:
            add_alternative(
                "split",
                [before_id],
                [after_id for _, after_id in candidates],
                min(score for score, _ in candidates) * 0.85,
                "one prior symbol has multiple plausible successor symbols",
            )
        elif len(candidates) == 1:
            score, after_id = candidates[0]
            add_alternative(
                "symbol_rename",
                [before_id],
                [after_id],
                score * 0.9,
                "one unmatched symbol has one plausible renamed successor",
            )
    for after_id, candidates in candidates_by_after.items():
        if len(candidates) >= 2:
            add_alternative(
                "merge",
                [before_id for _, before_id in candidates],
                [after_id],
                min(score for score, _ in candidates) * 0.85,
                "multiple prior symbols have one plausible successor symbol",
            )
    for before_id, candidates in candidates_by_before.items():
        if len(candidates) > 1:
            for score, after_id in candidates:
                add_alternative(
                    "ambiguous",
                    [before_id],
                    [after_id],
                    score * 0.75,
                    "multiple successor candidates remain unresolved",
                )
    return sorted(
        alternatives,
        key=lambda item: (
            item["kind"],
            item["before_observation_ids"],
            item["after_observation_ids"],
        ),
    )


def build_dependency_affected_graph(
    batches: Sequence[Mapping[str, Any]],
    changed_symbol_ids: Sequence[str],
    *,
    max_hops: int = 64,
) -> dict[str, Any]:
    """Return bounded reverse dependency closure over supplied observations."""

    if max_hops < 1:
        raise ValueError("max_hops must be positive")
    observations: list[Mapping[str, Any]] = []
    seen_batches: set[str] = set()
    for batch in batches:
        if not isinstance(batch, Mapping):
            continue
        batch_id = str(batch.get("batch_id") or "")
        if batch_id and batch_id in seen_batches:
            continue
        if batch_id:
            seen_batches.add(batch_id)
        raw_observations = batch.get("observations")
        if isinstance(raw_observations, list):
            observations.extend(
                item for item in raw_observations if isinstance(item, Mapping)
            )

    reverse_edges: dict[str, list[dict[str, Any]]] = {}
    symbol_paths: dict[str, set[str]] = {}
    symbol_observations: dict[str, set[str]] = {}
    unresolved_edge_count = 0
    for observation in observations:
        observation_id = str(observation.get("observation_id") or "")
        subject_id = _subject_symbol_id(observation)
        if subject_id:
            symbol_observations.setdefault(subject_id, set()).add(observation_id)
        relation = observation.get("relation")
        if not isinstance(relation, Mapping):
            continue
        target_id = _target_symbol_id(observation)
        if not subject_id or not target_id:
            unresolved_edge_count += 1
            continue
        reverse_edges.setdefault(target_id, []).append(
            {
                "source_symbol_id": subject_id,
                "target_symbol_id": target_id,
                "relation_kind": str(relation.get("kind") or "references"),
                "observation_id": observation_id,
                "confidence": copy.deepcopy(
                    observation.get(
                        "confidence",
                        {"evidence_class": "inferred", "value": 0.0},
                    )
                ),
            }
        )
    for batch in batches:
        source = batch.get("source") if isinstance(batch, Mapping) else None
        if not isinstance(source, Mapping):
            continue
        path = str(source.get("path") or "")
        for observation in batch.get("observations", []):
            if not isinstance(observation, Mapping):
                continue
            subject_id = _subject_symbol_id(observation)
            if subject_id and path:
                symbol_paths.setdefault(subject_id, set()).add(path)

    changed = {str(symbol_id) for symbol_id in changed_symbol_ids if str(symbol_id)}
    distances: dict[str, int] = {symbol_id: 0 for symbol_id in changed}
    queue = list(sorted(changed))
    truncated = False
    while queue:
        target_id = queue.pop(0)
        distance = distances[target_id]
        if distance >= max_hops:
            if reverse_edges.get(target_id):
                truncated = True
            continue
        for edge in sorted(
            reverse_edges.get(target_id, []),
            key=lambda item: (item["source_symbol_id"], item["observation_id"]),
        ):
            source_id = str(edge["source_symbol_id"])
            candidate_distance = distance + 1
            if source_id not in distances or candidate_distance < distances[source_id]:
                distances[source_id] = candidate_distance
                queue.append(source_id)

    affected_symbols = set(distances)
    affected_observations = {
        observation_id
        for symbol_id in affected_symbols
        for observation_id in symbol_observations.get(symbol_id, set())
    }
    edges = [
        {
            **edge,
            "distance": distances.get(str(edge["target_symbol_id"]), 0) + 1,
            "direction": "dependent_of_changed_symbol",
        }
        for target_id in sorted(reverse_edges)
        for edge in sorted(
            reverse_edges[target_id],
            key=lambda item: (item["source_symbol_id"], item["observation_id"]),
        )
        if edge["source_symbol_id"] in affected_symbols
        and edge["target_symbol_id"] in affected_symbols
    ]
    return {
        "scope": "supplied_observation_batches",
        "changed_symbol_ids": sorted(changed),
        "affected_symbol_ids": sorted(affected_symbols),
        "dependent_symbol_ids": sorted(affected_symbols - changed),
        "affected_observation_ids": sorted(affected_observations),
        "affected_paths": sorted(
            {
                path
                for symbol_id in affected_symbols
                for path in symbol_paths.get(symbol_id, set())
            }
        ),
        "edges": edges,
        "max_hops": max_hops,
        "truncated": truncated,
        "coverage": {
            "batch_count": len(seen_batches),
            "observation_count": len(observations),
            "unresolved_edge_count": unresolved_edge_count,
            "claim_limit": "closure is bounded to supplied observation batches",
        },
    }


def _observation_set_digest(batch: Mapping[str, Any] | None) -> str | None:
    if batch is None:
        return None
    return _canonical_digest(
        sorted(
            (copy.deepcopy(observation) for observation in batch.get("observations", [])),
            key=lambda item: str(item.get("observation_id") or ""),
        )
    )


def measure_observation_delta(
    before: Mapping[str, Any] | None,
    after: Mapping[str, Any] | None,
    *,
    full_rebuild: Mapping[str, Any] | None = None,
    stable_universe_paths: Sequence[str] | None = None,
    stable_universe_observation_ids: Sequence[str] | None = None,
    dependency_batches: Sequence[Mapping[str, Any]] | None = None,
    max_graph_hops: int = 64,
) -> dict[str, Any]:
    """Measure a bounded delta plan and optionally compare a clean rebuild."""

    started = time.perf_counter()
    rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    delta = plan_observation_delta(
        before,
        after,
        stable_universe_paths=stable_universe_paths,
        stable_universe_observation_ids=stable_universe_observation_ids,
        dependency_batches=dependency_batches,
        max_graph_hops=max_graph_hops,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    rss_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    parity: dict[str, Any]
    if full_rebuild is None:
        parity = {
            "state": "not_supplied",
            "matched": False,
            "claim_limit": "clean full-rebuild input was not supplied",
        }
    else:
        expected_digest = _observation_set_digest(after)
        actual_digest = _observation_set_digest(full_rebuild)
        parity = {
            "state": "matched" if expected_digest == actual_digest else "mismatch",
            "matched": expected_digest == actual_digest,
            "expected_observation_digest": expected_digest,
            "full_rebuild_observation_digest": actual_digest,
            "claim_limit": "observation-set parity only; repository family parity is separate",
        }
    delta["measurement"] = {
        "latency_ms": round(elapsed_ms, 3),
        "peak_rss_kib": max(int(rss_before), int(rss_after)),
        "full_rebuild_parity": parity,
    }
    return delta


def plan_observation_delta(
    before: Mapping[str, Any] | None,
    after: Mapping[str, Any] | None,
    *,
    stable_universe_paths: Sequence[str] | None = None,
    stable_universe_observation_ids: Sequence[str] | None = None,
    current_source_epoch: str | None = None,
    current_content_digest: str | None = None,
    dependency_batches: Sequence[Mapping[str, Any]] | None = None,
    max_graph_hops: int = 64,
) -> dict[str, Any]:
    """Plan bounded observation reuse and invalidation for one source change."""

    if before is None and after is None:
        raise ValueError("at least one observation batch is required")
    if max_graph_hops < 1:
        raise ValueError("max_graph_hops must be positive")
    _validate_delta_identity(before, after)
    before_summary = _source_summary(before)
    after_summary = _source_summary(after)
    before_map = _observation_map(before)
    after_map = _observation_map(after)
    before_ids = set(before_map)
    after_ids = set(after_map)
    added_ids = sorted(after_ids - before_ids)
    removed_ids = sorted(before_ids - after_ids)
    common_ids = before_ids & after_ids
    reused_ids = sorted(
        observation_id
        for observation_id in common_ids
        if _observation_digest(before_map[observation_id])
        == _observation_digest(after_map[observation_id])
    )
    updated_ids = sorted(common_ids - set(reused_ids))

    if before is None:
        change_kind = "add"
    elif after is None:
        change_kind = "delete"
    elif before_summary["content_digest"] == after_summary["content_digest"]:
        change_kind = (
            _path_change_kind(before_summary["path"], after_summary["path"])
            if before_summary["path"] != after_summary["path"]
            else "unchanged"
        )
    else:
        change_kind = "modify"

    lineage_matches = _lineage_matches(before_map, after_map)
    transformation_alternatives = _transformation_alternatives(
        before_map,
        after_map,
        lineage_matches,
    )
    affected_symbol_ids: set[str] = set()
    changed_ids = set(added_ids) | set(removed_ids) | set(updated_ids)
    combined_map: dict[str, Mapping[str, Any]] = {}
    combined_map.update(before_map)
    combined_map.update(after_map)
    for observation_id in changed_ids:
        observation = combined_map[observation_id]
        subject_symbol_id = _subject_symbol_id(observation)
        if subject_symbol_id is not None:
            affected_symbol_ids.add(subject_symbol_id)
        target_symbol_id = _target_symbol_id(observation)
        if target_symbol_id is not None:
            affected_symbol_ids.add(target_symbol_id)

    content_changed = (
        before_summary is not None
        and after_summary is not None
        and before_summary["content_digest"] != after_summary["content_digest"]
    )
    graph_seed_symbol_ids = set(affected_symbol_ids)
    if content_changed and not graph_seed_symbol_ids:
        graph_seed_symbol_ids.update(
            subject_symbol_id
            for observation in (*before_map.values(), *after_map.values())
            for subject_symbol_id in (_subject_symbol_id(observation),)
            if subject_symbol_id is not None
        )
    supplied_graph_batches = [
        batch
        for batch in (before, after)
        if batch is not None
    ]
    if dependency_batches:
        supplied_graph_batches.extend(dependency_batches)
    affected_graph = build_dependency_affected_graph(
        supplied_graph_batches,
        sorted(graph_seed_symbol_ids),
        max_hops=max_graph_hops,
    )
    affected_symbol_ids.update(affected_graph["affected_symbol_ids"])
    affected_paths = sorted(
        {
            summary["path"]
            for summary in (before_summary, after_summary)
            if summary is not None
        }
        | set(affected_graph["affected_paths"])
    )
    has_changes = bool(added_ids or removed_ids or updated_ids or content_changed)
    dependency_paths = set(affected_graph["affected_paths"]) - set(
        summary["path"]
        for summary in (before_summary, after_summary)
        if summary is not None
    )
    invalidation_scope = (
        "graph"
        if dependency_paths
        else "file"
        if has_changes or change_kind in {"rename", "move", "delete"}
        else "none"
    )
    dependency_invalidated_ids = sorted(
        set(affected_graph["affected_observation_ids"])
        - set(changed_ids)
    )
    invalidated_ids = sorted(
        set(removed_ids) | set(updated_ids) | set(dependency_invalidated_ids)
    )
    recomputed_ids = sorted(set(added_ids) | set(updated_ids))
    path_reanchored_ids = sorted(
        {
            str(item["after_observation_id"])
            for item in lineage_matches
            if before_summary is not None
            and after_summary is not None
            and before_summary["path"] != after_summary["path"]
        }
    )
    input_batch_ids = sorted(
        {
            summary["batch_id"]
            for summary in (before_summary, after_summary)
            if summary is not None
        }
    )
    delta_key = ":".join(input_batch_ids) + f":{change_kind}"
    repo = (after_summary or before_summary)["repo"]
    provider = _provider_summary(after or before)
    before_qualification = _delta_qualification(before)
    after_qualification = _delta_qualification(after)

    declared_paths = (
        {
            _normalized_path(path, field_name="stable_universe_paths")
            for path in stable_universe_paths
        }
        if stable_universe_paths is not None
        else set(affected_paths)
    )
    declared_observation_ids = (
        {str(observation_id) for observation_id in stable_universe_observation_ids}
        if stable_universe_observation_ids is not None
        else before_ids | after_ids
    )
    affected_path_set = set(affected_paths) & declared_paths
    affected_observation_set = changed_ids & declared_observation_ids
    if declared_observation_ids:
        blast_radius_ratio = len(affected_observation_set) / len(declared_observation_ids)
        universe_basis = "observation_ids"
    elif declared_paths:
        blast_radius_ratio = len(affected_path_set) / len(declared_paths)
        universe_basis = "path_union"
    else:
        blast_radius_ratio = 0.0
        universe_basis = "empty"
    blast_radius_ratio = min(max(blast_radius_ratio, 0.0), 1.0)
    reuse_ratio = len(reused_ids) / max(len(before_ids), 1)
    metrics = {
        "before_observation_count": len(before_ids),
        "after_observation_count": len(after_ids),
        "reused_observation_count": len(reused_ids),
        "recomputation_count": len(recomputed_ids),
        "direct_invalidation_count": len(set(removed_ids) | set(updated_ids)),
        "dependency_invalidation_count": len(dependency_invalidated_ids),
        "affected_symbol_count": len(affected_symbol_ids),
        "affected_graph_edge_count": len(affected_graph["edges"]),
        "reuse_ratio": round(reuse_ratio, 6),
        "blast_radius_ratio": round(blast_radius_ratio, 6),
    }

    currentness_provider = provider or {}
    current_boundary_batch = after if after is not None else before
    current_boundary_source = (
        current_boundary_batch.get("source")
        if isinstance(current_boundary_batch, Mapping)
        else None
    )
    default_current_source_epoch = (
        str(current_boundary_source.get("source_epoch") or "")
        if isinstance(current_boundary_source, Mapping)
        else ""
    )
    default_current_content_digest = (
        str(current_boundary_source.get("content_digest") or "")
        if isinstance(current_boundary_source, Mapping)
        else ""
    )

    def delta_currentness(batch: Mapping[str, Any] | None) -> dict[str, Any] | None:
        if batch is None:
            return None
        source = batch.get("source")
        if not isinstance(source, Mapping):
            return None
        return classify_observation_currentness(
            batch,
            source_epoch=str(current_source_epoch or default_current_source_epoch),
            content_digest=current_content_digest or default_current_content_digest,
            provider_id=str(currentness_provider.get("id") or "") or None,
            provider_version=str(currentness_provider.get("version") or "") or None,
            provider_config_digest=(
                str(currentness_provider.get("config_digest") or "") or None
            ),
        )

    return {
        "schema_version": DELTA_SCHEMA_VERSION,
        "delta_id": qualified_id(repo, "code-observation-delta", delta_key),
        "capability_class": CAPABILITY_CLASS,
        "repository": repo,
        "provider": provider,
        "change_kind": change_kind,
        "before": before_summary,
        "after": after_summary,
        "observation_delta": {
            "added_observation_ids": added_ids,
            "removed_observation_ids": removed_ids,
            "updated_observation_ids": updated_ids,
            "reused_observation_ids": reused_ids,
            "affected_symbol_ids": sorted(affected_symbol_ids),
        },
        "invalidation": {
            "scope": invalidation_scope,
            "affected_paths": affected_paths,
            "recomputed_observation_ids": recomputed_ids,
            "invalidated_observation_ids": invalidated_ids,
            "source_content_changed": content_changed,
            "dependency_invalidated_observation_ids": dependency_invalidated_ids,
            "path_reanchored_observation_ids": path_reanchored_ids,
            "blast_radius": len(affected_symbol_ids),
            "blast_radius_ratio": round(blast_radius_ratio, 6),
            "stable_universe": {
                "basis": universe_basis,
                "declared": (
                    stable_universe_paths is not None
                    or stable_universe_observation_ids is not None
                ),
                "path_count": len(declared_paths),
                "affected_path_count": len(affected_path_set),
                "observation_count": len(declared_observation_ids),
                "affected_observation_count": len(affected_observation_set),
            },
        },
        "lineage": {
            "state": (
                "added"
                if before is None
                else "deleted"
                if after is None
                else "stable"
                if before_summary["lineage_path"] == after_summary["lineage_path"]
                else "recovered_by_content"
                if before_summary["content_digest"] == after_summary["content_digest"]
                else "changed"
            ),
            "before_path": before_summary["path"] if before_summary else None,
            "after_path": after_summary["path"] if after_summary else None,
            "before_lineage_path": before_summary["lineage_path"] if before_summary else None,
            "after_lineage_path": after_summary["lineage_path"] if after_summary else None,
            "stable_lineage_path": (
                after_summary["lineage_path"]
                if after_summary is not None
                else before_summary["lineage_path"]
            ),
            "matches": lineage_matches,
            "alternatives": transformation_alternatives,
            "claim_limit": "explicit and inferred mappings are not provider or owner acceptance",
        },
        "affected_graph": affected_graph,
        "metrics": metrics,
        "currentness": {
            "before": delta_currentness(before),
            "after": delta_currentness(after),
        },
        "qualification": {
            "before": before_qualification,
            "after": after_qualification,
        },
        "provenance": {
            "planner_ref": EXTRACTOR_REF,
            "input_batch_ids": input_batch_ids,
        },
    }


def classify_observation_currentness(
    batch: Mapping[str, Any],
    *,
    source_epoch: str,
    content_digest: str | None = None,
    provider_id: str | None = None,
    provider_version: str | None = None,
    provider_config_digest: str | None = None,
) -> dict[str, Any]:
    """Classify a batch against an explicitly supplied currentness boundary."""

    source = batch.get("source")
    if not isinstance(source, Mapping):
        raise ValueError("observation batch must contain source identity")
    provider = batch.get("provider")
    if not isinstance(provider, Mapping):
        raise ValueError("observation batch must contain provider identity")
    reasons: list[str] = []
    if str(source.get("source_epoch")) != str(source_epoch):
        reasons.append("source_epoch_mismatch")
    if content_digest is not None and str(source.get("content_digest")) != str(content_digest):
        reasons.append("content_digest_mismatch")
    if provider_id is not None and str(provider.get("id")) != str(provider_id):
        reasons.append("provider_id_mismatch")
    if provider_version is not None and str(provider.get("version")) != str(provider_version):
        reasons.append("provider_version_mismatch")
    if provider_config_digest is not None and str(
        provider.get("config_digest")
    ) != str(provider_config_digest):
        reasons.append("provider_config_digest_mismatch")
    parse_status = str(batch.get("parse_status") or "")
    if parse_status == "degraded":
        state = "degraded"
        reasons.insert(0, "diagnostic_degradation")
    elif parse_status == "unparseable":
        state = "unparseable"
        reasons.insert(0, "source_unparseable")
    elif reasons:
        state = "stale"
    else:
        state = "current"
    return {
        "state": state,
        "batch_id": str(batch.get("batch_id") or ""),
        "source_epoch": str(source.get("source_epoch") or ""),
        "current_source_epoch": str(source_epoch),
        "content_digest": str(source.get("content_digest") or ""),
        "current_content_digest": str(content_digest or source.get("content_digest") or ""),
        "provider": {
            "id": str(provider.get("id") or ""),
            "version": str(provider.get("version") or ""),
            "config_digest": str(provider.get("config_digest") or ""),
        },
        "reasons": reasons,
    }


def _with_currentness(
    batch: dict[str, Any],
    *,
    source_epoch: str,
    content_digest: str,
    provider_id: str,
    provider_version: str,
    provider_config_digest: str,
) -> dict[str, Any]:
    batch["currentness"] = classify_observation_currentness(
        batch,
        source_epoch=source_epoch,
        content_digest=content_digest,
        provider_id=provider_id,
        provider_version=provider_version,
        provider_config_digest=provider_config_digest,
    )
    return batch
