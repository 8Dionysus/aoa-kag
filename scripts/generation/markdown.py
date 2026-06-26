from __future__ import annotations

from .common import *

def read_markdown_frontmatter(path: Path) -> dict[str, object]:
    lines = read_text(path).splitlines()
    if not lines or lines[0].strip() != "---":
        fail(f"markdown file is missing frontmatter fence: {path.as_posix()}")

    closing_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        fail(f"markdown file is missing closing frontmatter fence: {path.as_posix()}")

    payload: dict[str, object] = {}
    current_list_key: str | None = None

    for raw_line in lines[1:closing_index]:
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("  - "):
            if current_list_key is None:
                fail(f"frontmatter list item without a key in {path.as_posix()}")
            current_value = payload.get(current_list_key)
            if not isinstance(current_value, list):
                fail(f"frontmatter key '{current_list_key}' is not a list in {path.as_posix()}")
            current_value.append(line[4:].strip())
            continue
        if ":" not in line:
            fail(f"unsupported frontmatter line in {path.as_posix()}: {line}")

        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if not key:
            fail(f"frontmatter key cannot be empty in {path.as_posix()}")
        if value:
            payload[key] = value
            current_list_key = None
            continue
        payload[key] = []
        current_list_key = key

    return payload


def get_frontmatter_string(
    payload: dict[str, object], key: str, *, label: str
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        fail(f"{label} must keep '{key}' as a non-empty string")
    return value


def get_frontmatter_list(
    payload: dict[str, object], key: str, *, label: str
) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not value:
        fail(f"{label} must keep '{key}' as a non-empty list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            fail(f"{label} contains an invalid '{key}' entry")
        result.append(item)
    return result


def normalize_repo_pointer(raw_ref: str) -> str:
    if not raw_ref.startswith("repo:"):
        fail(f"expected repo-qualified ref, received '{raw_ref}'")
    pointer = raw_ref[5:]
    parts = pointer.split("/")
    if len(parts) < 2:
        fail(f"invalid repo-qualified ref '{raw_ref}'")

    repo_name = parts[0]
    remainder = parts[1:]
    if repo_name not in KNOWN_REPO_ROOTS and len(parts) >= 3 and parts[1] in KNOWN_REPO_ROOTS:
        repo_name = parts[1]
        remainder = parts[2:]
    if repo_name not in KNOWN_REPO_ROOTS:
        fail(f"unsupported repo-qualified ref '{raw_ref}'")
    if not remainder:
        fail(f"repo-qualified ref is missing a path '{raw_ref}'")
    return repo_ref(repo_name, canonical_repo_path(repo_name, "/".join(remainder)))


def normalize_relative_ref(repo: str, raw_ref: str) -> str:
    if raw_ref.startswith("repo:"):
        return normalize_repo_pointer(raw_ref)
    return repo_ref(repo, canonical_repo_path(repo, raw_ref))


def markdown_section_lines(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    inside = False
    target_level = heading.count("#")
    section_lines: list[str] = []

    for line in lines:
        if line.strip() == heading:
            inside = True
            continue
        if inside and line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if level <= target_level:
                break
        if inside:
            section_lines.append(line)

    if not section_lines:
        fail(f"missing markdown section '{heading}' in {REASONING_HANDOFF_GUARDRAIL_PATH.as_posix()}")
    return section_lines


def extract_query_modes_from_doc(path: Path) -> list[str]:
    section_lines = markdown_section_lines(read_text(path), "## Query modes")
    query_modes: list[str] = []
    for line in section_lines:
        match = QUERY_MODE_HEADING.match(line.strip())
        if match:
            query_modes.append(match.group(1))
    if not query_modes:
        fail("reasoning handoff doc must declare query modes")
    return query_modes


def extract_bullets_after_marker(text: str, marker: str) -> list[str]:
    lines = text.splitlines()
    collecting = False
    items: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped == marker:
            collecting = True
            continue
        if not collecting:
            continue
        if stripped.startswith("- "):
            items.append(stripped[2:].strip().strip("`"))
            continue
        if items and not stripped:
            break

    if not items:
        fail(f"reasoning handoff doc is missing bullet list after '{marker}'")
    return items


def extract_boundary_guardrails_from_doc(path: Path) -> dict[str, str]:
    bullets = [
        line.strip()[2:].strip()
        for line in markdown_section_lines(read_text(path), "## Boundary guardrails")
        if line.strip().startswith("- ")
    ]
    if not bullets:
        fail("reasoning handoff doc must declare boundary guardrails")

    boundary_guardrails: dict[str, str] = {}
    for bullet in bullets:
        if bullet.startswith("`aoa-routing` owns "):
            boundary_guardrails["routing_owner"] = "aoa-routing"
        elif bullet.startswith("`aoa-memo` owns "):
            boundary_guardrails["memory_owner"] = "aoa-memo"
        elif bullet.startswith("`Tree-of-Sophia` owns "):
            boundary_guardrails["canon_owner"] = "Tree-of-Sophia"
        elif "direct canon authorship" in bullet and "forbidden" in bullet:
            boundary_guardrails["direct_canon_authorship"] = "forbidden"

    expected_keys = {
        "routing_owner",
        "memory_owner",
        "canon_owner",
        "direct_canon_authorship",
    }
    if set(boundary_guardrails) != expected_keys:
        fail("reasoning handoff doc boundary guardrails are incomplete")
    return boundary_guardrails
