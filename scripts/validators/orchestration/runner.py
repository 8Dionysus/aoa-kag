from __future__ import annotations

import sys

from ..common import *
from .examples import validate_examples
from .expected_payloads import build_expected_payloads
from .generated_structures import validate_generated_structures
from .generated_text import validate_generated_text_outputs
from .manifests import load_registry_context, validate_manifest_contracts
from .static_surfaces import validate_static_surfaces
from .status import print_success_status


def main() -> int:
    try:
        validate_static_surfaces()
        registry_manifest_payload, registry_manifest_surfaces, missing_roots = (
            load_registry_context()
        )
        if missing_roots:
            print(
                "[warn] skipped cross-repo manifest/generated validation because "
                "source roots are unavailable: " + ", ".join(missing_roots),
                file=sys.stderr,
            )
            print("[ok] validated local KAG surfaces; full cross-repo validation was skipped")
            return 0

        validate_manifest_contracts(registry_manifest_surfaces)
        expected_payloads = build_expected_payloads(registry_manifest_payload)
        validate_generated_text_outputs(expected_payloads)
        generated_surfaces_by_id = validate_generated_structures(expected_payloads)
        validate_examples(expected_payloads, generated_surfaces_by_id)
    except ValidationError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print_success_status()
    return 0
