#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Callable, TypeVar

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import kag_generation
import validate_kag

T = TypeVar("T")

MEMO_READINESS_REF = "aoa-memo/mechanics/readiness-boundary/docs/MEMORY_READINESS_BOUNDARY.md"
RETURN_REGROUNDING_PART_ROOT = (
    Path("mechanics") / "recurrence" / "parts" / "return-regrounding"
)
RECURRENCE_KAG_PROJECTION_SCHEMA_PATH = (
    RETURN_REGROUNDING_PART_ROOT / "schemas" / "recurrence-kag-projection.schema.json"
)
RECURRENCE_KAG_PROJECTION_EXAMPLE_PATH = (
    RETURN_REGROUNDING_PART_ROOT / "examples" / "recurrence_kag_projection.example.json"
)
EXPECTED_RECURRENCE_KAG_PROJECTION_VERSION = "aoa_recurrence_kag_projection_v1"


class ReturnRegroundingValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ReturnRegroundingValidationError(message)


def root_check(callback: Callable[..., T], *args: object) -> T:
    try:
        return callback(*args)
    except (kag_generation.GenerationError, validate_kag.ValidationError) as exc:
        fail(str(exc))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing required file: {display_path(path)}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {display_path(path)}: {exc}")


def validate_recurrence_kag_projection_companion() -> None:
    schema_path = REPO_ROOT / RECURRENCE_KAG_PROJECTION_SCHEMA_PATH
    example_path = REPO_ROOT / RECURRENCE_KAG_PROJECTION_EXAMPLE_PATH
    schema = read_json(schema_path)
    if not isinstance(schema, dict):
        fail(f"{display_path(schema_path)} must contain a JSON object")
    Draft202012Validator.check_schema(schema)
    schema_version = schema.get("properties", {}).get("schema_version")
    if not isinstance(schema_version, dict) or schema_version.get("const") != EXPECTED_RECURRENCE_KAG_PROJECTION_VERSION:
        fail(
            f"{display_path(schema_path)} schema_version must stay pinned to "
            f"{EXPECTED_RECURRENCE_KAG_PROJECTION_VERSION!r}"
        )

    example = read_json(example_path)
    if not isinstance(example, dict):
        fail(f"{display_path(example_path)} must contain a JSON object")
    errors = sorted(
        Draft202012Validator(schema).iter_errors(example),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    if errors:
        first = errors[0]
        error_path = ".".join(str(part) for part in first.absolute_path)
        if error_path:
            fail(
                f"{display_path(example_path)} schema violation at "
                f"{error_path!r}: {first.message}"
            )
        fail(f"{display_path(example_path)} schema violation: {first.message}")
    if example.get("schema_version") != EXPECTED_RECURRENCE_KAG_PROJECTION_VERSION:
        fail(
            f"{display_path(example_path)} schema_version must equal "
            f"{EXPECTED_RECURRENCE_KAG_PROJECTION_VERSION!r}"
        )
    if "source_export_reentry" not in example.get("regrounding_modes", []):
        fail(f"{display_path(example_path)} must keep at least one source-first regrounding mode")


def validate_return_regrounding_boundary() -> None:
    validate_recurrence_kag_projection_companion()
    root_check(validate_kag.validate_return_regrounding_manifest)
    payload = root_check(
        kag_generation.build_return_regrounding_pack_payload,
        kag_generation.build_registry_payload(),
    )
    root_check(validate_kag.validate_return_regrounding_pack, payload, payload)

    inputs_by_name = {source["name"]: source for source in payload["source_inputs"]}
    modes_by_id = {mode["mode_id"]: mode for mode in payload["modes"]}

    if inputs_by_name.get("memo_memory_readiness_boundary") != {
        "name": "memo_memory_readiness_boundary",
        "repo": "aoa-memo",
        "role": "owner_contract",
        "ref": MEMO_READINESS_REF,
    }:
        fail("return regrounding must keep memo memory readiness as an aoa-memo owner contract")
    for mode_id in ("handoff_guardrail_reentry", "owner_boundary_reentry"):
        if MEMO_READINESS_REF not in modes_by_id[mode_id]["stronger_refs"]:
            fail(f"{mode_id} must return memory readiness pressure to aoa-memo")
    if MEMO_READINESS_REF in modes_by_id["source_export_reentry"]["stronger_refs"]:
        fail("source_export_reentry must not absorb memo memory readiness")
    if payload["bounded_output_contract"].get("memory_truth_ownership") != "forbidden":
        fail("return regrounding must forbid memory truth ownership")


def main() -> int:
    try:
        validate_return_regrounding_boundary()
    except ReturnRegroundingValidationError as exc:
        print(f"[error] {exc}")
        return 1
    print("[ok] validated return regrounding boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
