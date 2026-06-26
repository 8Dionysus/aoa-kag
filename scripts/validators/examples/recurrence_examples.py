from __future__ import annotations

from ..common import *
from ..projection_parity import *
from ..source_refs import *

def validate_return_regrounding_example(expected_payload: dict[str, object]) -> None:
    payload = read_json(RETURN_REGROUNDING_EXAMPLE_PATH)
    validate_return_regrounding_pack(payload, expected_payload)
