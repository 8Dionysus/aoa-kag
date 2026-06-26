from __future__ import annotations

import copy
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Iterator
from unittest.mock import patch

from generation import common, consumer, context, federation, governance, handoff, registry
from generation import regrounding, source_refs, technique, tos


GENERATION_MODULES = (
    context,
    common,
    source_refs,
    registry,
    technique,
    tos,
    handoff,
    federation,
    regrounding,
    governance,
    consumer,
)

READ_JSON_MODULES = tuple(
    module for module in GENERATION_MODULES if hasattr(module, "read_json")
)


@contextmanager
def patched_generation_read_json(overrides: dict[Path, object]) -> Iterator[None]:
    original = common.read_json
    normalized = {
        Path(path).resolve(): copy.deepcopy(payload)
        for path, payload in overrides.items()
    }

    def side_effect(path: Path) -> object:
        resolved = Path(path).resolve()
        if resolved in normalized:
            return copy.deepcopy(normalized[resolved])
        return original(path)

    with ExitStack() as stack:
        for module in READ_JSON_MODULES:
            stack.enter_context(patch.object(module, "read_json", side_effect=side_effect))
        yield


@contextmanager
def patched_generation_attribute(name: str, value: object) -> Iterator[None]:
    with ExitStack() as stack:
        for module in GENERATION_MODULES:
            if hasattr(module, name):
                stack.enter_context(patch.object(module, name, value))
        yield
