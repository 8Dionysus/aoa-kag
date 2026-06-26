from __future__ import annotations

from ..common import *
from ..projection_parity import *
from ..source_refs import *

def validate_tiny_consumer_bundle_example(expected_payload: dict[str, object]) -> None:
    payload = read_json(TINY_CONSUMER_BUNDLE_EXAMPLE_PATH)
    if payload != expected_payload:
        fail("tiny consumer bundle example must match the current bundle payload")
