from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from ..common import *
from ..local_kag_subtree import validate_local_kag_provider_homes_contract_with_progress
from ..repo_local_kag_index import validate_repo_local_kag_os_wide_contract_with_progress
from .examples import validate_examples
from .expected_payloads import build_expected_payloads
from .generated_structures import validate_generated_structures
from .generated_text import validate_generated_text_outputs
from .manifests import load_registry_context, validate_manifest_contracts
from .static_surfaces import validate_static_surfaces
from .status import print_os_wide_success_status, print_success_status


VALIDATION_SCOPES = ("local", "os-wide", "full")


def _runner_phase(label: str) -> None:
    print(f"[validate-kag] {label}", file=sys.stderr, flush=True)


def parse_args(argv: Sequence[str] = ()) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate aoa-kag contracts.")
    parser.add_argument(
        "--scope",
        choices=VALIDATION_SCOPES,
        default="full",
        help=(
            "local avoids the OS-wide provider sweep; os-wide validates only "
            "provider coverage; full preserves the compatibility behavior"
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] = ()) -> int:
    args = parse_args(argv)
    run_local = args.scope in {"local", "full"}
    run_os_wide = args.scope in {"os-wide", "full"}

    try:
        if run_local:
            _runner_phase("static-surfaces")
            validate_static_surfaces()
        if run_os_wide:
            _runner_phase("os-wide-provider-homes")
            validate_local_kag_provider_homes_contract_with_progress()
            _runner_phase("os-wide-provider-coverage")
            validate_repo_local_kag_os_wide_contract_with_progress()
        if run_local:
            _runner_phase("registry-context")
            registry_manifest_payload, registry_manifest_surfaces, missing_roots = (
                load_registry_context()
            )
            if missing_roots:
                print(
                    "[warn] skipped cross-repo manifest/generated validation because "
                    "source roots are unavailable: " + ", ".join(missing_roots),
                    file=sys.stderr,
                )
                print(
                    "[ok] validated local KAG surfaces; full cross-repo validation "
                    "was skipped"
                )
                if run_os_wide:
                    print_os_wide_success_status()
                return 0

            _runner_phase("manifest-contracts")
            validate_manifest_contracts(registry_manifest_surfaces)
            _runner_phase("expected-payloads")
            expected_payloads = build_expected_payloads(registry_manifest_payload)
            _runner_phase("generated-text")
            validate_generated_text_outputs(expected_payloads)
            _runner_phase("generated-structures")
            generated_surfaces_by_id = validate_generated_structures(expected_payloads)
            _runner_phase("examples")
            validate_examples(expected_payloads, generated_surfaces_by_id)
    except ValidationError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    _runner_phase("success-status")
    if run_local:
        print_success_status()
    if run_os_wide:
        print_os_wide_success_status()
    return 0
