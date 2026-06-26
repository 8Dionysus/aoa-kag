from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_tiny_consumer_bundle_pack(expected_payload: dict[str, object]) -> None:
    payload = read_json(TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH)
    if not isinstance(payload, dict):
        fail("tiny consumer bundle pack must be a JSON object")

    for key in (
        "bundle_version",
        "bundle_type",
        "source_manifest_ref",
        "source_inputs",
        "bundle_item_count",
        "bundle_items",
        "deferred_counterpart",
    ):
        if key not in payload:
            fail(f"tiny consumer bundle pack is missing required key '{key}'")

    if payload["bundle_version"] != 1:
        fail("tiny consumer bundle pack bundle_version must equal 1")
    if payload["bundle_type"] != "tiny_consumer_bundle":
        fail("tiny consumer bundle pack bundle_type must equal 'tiny_consumer_bundle'")
    if payload["source_manifest_ref"] != TINY_CONSUMER_BUNDLE_MANIFEST_REF:
        fail(
            "tiny consumer bundle pack source_manifest_ref must point to "
            f"{TINY_CONSUMER_BUNDLE_MANIFEST_REF}"
        )
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail("tiny consumer bundle pack source_inputs must match the manifest-driven donor set")

    bundle_items = payload["bundle_items"]
    if not isinstance(bundle_items, list) or not bundle_items:
        fail("tiny consumer bundle pack bundle_items must be a non-empty list")
    if payload["bundle_item_count"] != len(bundle_items):
        fail("tiny consumer bundle pack bundle_item_count must equal the number of bundle_items")

    observed_order: list[str] = []
    for index, bundle_item in enumerate(bundle_items):
        location = f"tiny consumer bundle pack bundle_items[{index}]"
        if not isinstance(bundle_item, dict):
            fail(f"{location} must be an object")
        for key in ("order", "name", "role", "ref"):
            if key not in bundle_item:
                fail(f"{location} is missing required key '{key}'")
        if bundle_item["order"] != index + 1:
            fail(f"{location}.order must keep the stable 1-based bundle order")
        if not isinstance(bundle_item["name"], str) or not bundle_item["name"]:
            fail(f"{location}.name must be a non-empty string")
        if not isinstance(bundle_item["role"], str) or not bundle_item["role"]:
            fail(f"{location}.role must be a non-empty string")
        if not isinstance(bundle_item["ref"], str) or not bundle_item["ref"]:
            fail(f"{location}.ref must be a non-empty string")
        resolve_known_ref(bundle_item["ref"], label=f"{location}.ref")
        observed_order.append(bundle_item["name"])

    if observed_order != EXPECTED_TINY_CONSUMER_BUNDLE_ORDER:
        fail("tiny consumer bundle pack bundle_items must keep the current stable bundle order")
    if payload["deferred_counterpart"] != EXPECTED_TINY_CONSUMER_BUNDLE_DEFERRED_COUNTERPART:
        fail("tiny consumer bundle pack deferred_counterpart must match the contract-only posture")
    resolve_known_ref(
        payload["deferred_counterpart"]["federation_exposure_review_ref"],
        label="tiny consumer bundle pack deferred_counterpart.federation_exposure_review_ref",
    )
    if payload != expected_payload:
        fail("tiny consumer bundle pack must match the committed manifest-driven bundle payload")
