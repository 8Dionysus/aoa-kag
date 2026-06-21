#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
from typing import Callable, TypeVar

REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import kag_generation
import validate_kag

T = TypeVar("T")

REQUIRED_EXAMPLE_REFS = {
    "mechanics/boundary-bridge/parts/counterpart-edge/docs/counterpart-consumer-contract.md",
    "mechanics/boundary-bridge/parts/counterpart-edge/examples/counterpart_consumer_contract.example.json",
    "mechanics/audit/parts/exposure-review/docs/counterpart-federation-exposure-review.md",
}


class ReasoningHandoffValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ReasoningHandoffValidationError(message)


def root_check(callback: Callable[..., T], *args: object) -> T:
    try:
        return callback(*args)
    except (kag_generation.GenerationError, validate_kag.ValidationError) as exc:
        fail(str(exc))


def validate_reasoning_handoff_boundary() -> None:
    root_check(validate_kag.validate_reasoning_handoff_manifest)
    payload = root_check(kag_generation.build_reasoning_handoff_pack_payload)
    root_check(validate_kag.validate_reasoning_handoff_pack, payload)
    root_check(validate_kag.validate_reasoning_handoff_example)

    example = validate_kag.read_json(validate_kag.REASONING_HANDOFF_EXAMPLE_PATH)
    if not isinstance(example, dict):
        fail("reasoning handoff example must be a JSON object")
    derived_refs = example.get("derived_surface_refs")
    if not isinstance(derived_refs, list):
        fail("reasoning handoff example derived_surface_refs must be a list")
    missing_refs = sorted(REQUIRED_EXAMPLE_REFS - set(derived_refs))
    if missing_refs:
        fail("reasoning handoff example is missing required counterpart refs: " + ", ".join(missing_refs))


def main() -> int:
    try:
        validate_reasoning_handoff_boundary()
    except ReasoningHandoffValidationError as exc:
        print(f"[error] {exc}")
        return 1
    print("[ok] validated reasoning handoff boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
