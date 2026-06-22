from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence

from jsonschema import Draft202012Validator

from .expected_contracts import *

class ValidationError(RuntimeError):
    pass

def fail(message: str) -> None:
    raise ValidationError(message)

def display_path(path: Path) -> str:
    for root in VISIBLE_ROOTS:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            continue
    return path.as_posix()

def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing required file: {display_path(path)}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {display_path(path)}: {exc}")

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {display_path(path)}")

def format_schema_path(parts: Sequence[object]) -> str:
    return ".".join(str(part) for part in parts)

def markdown_anchor(text: str) -> str:
    anchor = text.strip().lower()
    anchor = re.sub(r"[^\w\s-]", "", anchor)
    anchor = re.sub(r"\s+", "-", anchor)
    anchor = re.sub(r"-+", "-", anchor)
    return anchor.strip("-")

def markdown_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    seen: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = MARKDOWN_HEADING.match(line)
        if not match:
            continue
        base = markdown_anchor(match.group(2))
        if not base:
            continue
        suffix = seen.get(base, 0)
        seen[base] = suffix + 1
        anchors.add(base if suffix == 0 else f"{base}-{suffix}")
    return anchors

def validate_unique_string_list(
    value: object,
    *,
    label: str,
    allow_empty: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        fail(f"{label} must be a list")
    if not value and not allow_empty:
        fail(f"{label} must be a non-empty list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or len(item) < 1:
            fail(f"{label} contains an invalid entry")
        result.append(item)
    if len(result) != len(set(result)):
        fail(f"{label} must not contain duplicates")
    return result

def iter_string_values(value: object):
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for nested_value in value.values():
            yield from iter_string_values(nested_value)
        return
    if isinstance(value, list):
        for nested_value in value:
            yield from iter_string_values(nested_value)

def validate_exact_set(
    values: list[str] | set[str],
    expected: set[str],
    *,
    label: str,
) -> None:
    if set(values) != expected:
        fail(f"{label} must match the exact expected set")
