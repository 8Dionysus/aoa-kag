from __future__ import annotations

from .core import *

EXPECTED_AOA_K_0006_SOURCE_INPUTS = [
    {
        "repo": "aoa-techniques",
        "source_class": "technique_bundle",
        "role": "primary",
    },
    {
        "repo": TOS_REPO,
        "source_class": "tos_text",
        "role": "supporting",
    },
]

EXPECTED_AOA_K_0009_SOURCE_INPUTS = [
    {
        "repo": "aoa-techniques",
        "source_class": "review_surface",
        "role": "primary",
    },
    {
        "repo": TOS_REPO,
        "source_class": "tos_text",
        "role": "supporting",
    },
]
