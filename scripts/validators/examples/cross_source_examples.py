from __future__ import annotations

from ..common import *
from ..projection_parity import *
from ..source_refs import *

def validate_cross_source_node_projection_example(expected_payload: dict[str, object]) -> None:
    payload = read_json(CROSS_SOURCE_NODE_PROJECTION_EXAMPLE_PATH)
    if payload != expected_payload:
        fail("cross-source node projection example must match the current bounded projection payload")
