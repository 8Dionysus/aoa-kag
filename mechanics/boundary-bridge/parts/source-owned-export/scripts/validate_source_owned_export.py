#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Callable, TypeVar

REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import validate_kag

T = TypeVar("T")

MEMO_SOURCE_KEY = ("aoa-memo", validate_kag.EXPECTED_MEMO_KAG_EXPORT_PATH)
EXPECTED_MEMO_ACTIVATION = {
    "registry_visible": True,
    "spine_visible": False,
    "routing_visible": False,
}


class SourceOwnedExportValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise SourceOwnedExportValidationError(message)


def root_check(callback: Callable[..., T], *args: Any) -> T:
    try:
        return callback(*args)
    except validate_kag.ValidationError as exc:
        fail(str(exc))


def registry_manifest_surfaces() -> dict[str, dict[str, object]]:
    payload = validate_kag.read_json(validate_kag.REGISTRY_MANIFEST_PATH)
    try:
        return validate_kag.validate_registry_payload(
            payload,
            label="registry manifest",
        )
    except validate_kag.ValidationError as exc:
        fail(str(exc))


def validate_source_owned_export_boundary() -> None:
    surfaces_by_id = registry_manifest_surfaces()
    dependencies = root_check(
        validate_kag.validate_source_owned_export_dependency_manifest,
        surfaces_by_id,
    )

    memo_dependency = dependencies.get(MEMO_SOURCE_KEY)
    if not isinstance(memo_dependency, dict):
        fail("source-owned export dependencies must include the aoa-memo donor export")
    if memo_dependency.get("consumed_by") != []:
        fail("aoa-memo donor export must remain registry-only with empty consumed_by")

    federation_entries = root_check(
        validate_kag.validate_federation_export_registry_manifest,
        dependencies,
    )
    memo_export = federation_entries.get(MEMO_SOURCE_KEY)
    if not isinstance(memo_export, dict):
        fail("federation export registry must include the aoa-memo donor export")
    if memo_export.get("activation") != EXPECTED_MEMO_ACTIVATION:
        fail("aoa-memo donor export must remain registry-visible only")
    if memo_export.get("routing_binding") is not None:
        fail("aoa-memo donor export must not have a routing binding")
    if memo_export.get("adjunct_surfaces") != []:
        fail("aoa-memo donor export must not expose adjunct surfaces while registry-only")

    root_check(validate_kag.validate_optional_memo_source_owned_export_readiness)
    root_check(validate_kag.validate_memo_source_owned_export_consumer_boundary_doc)


def main() -> int:
    try:
        validate_source_owned_export_boundary()
    except SourceOwnedExportValidationError as exc:
        print(f"[error] {exc}")
        return 1
    print("[ok] validated source-owned export boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
