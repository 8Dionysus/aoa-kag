from __future__ import annotations

from ..common import *
from ..projection_parity import *
from ..source_refs import *

def validate_counterpart_federation_exposure_review_example(
    expected_payload: dict[str, object],
) -> None:
    payload = read_json(COUNTERPART_FEDERATION_EXPOSURE_REVIEW_EXAMPLE_PATH)
    if payload != expected_payload:
        fail(
            "counterpart federation exposure review example must match the current "
            "review payload"
        )
