from __future__ import annotations

from .common import *

def build_registry_payload() -> dict[str, object]:
    payload = read_json(REGISTRY_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("registry manifest must be a JSON object")
    if payload.get("artifact_identity") != KAG_REGISTRY_ARTIFACT_IDENTITY:
        fail("registry manifest artifact_identity must match KAG_REGISTRY_ARTIFACT_IDENTITY")
    return payload
