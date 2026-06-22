#!/usr/bin/env python3
"""Validate the aoa-kag mechanics topology."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MECHANICS_ROOT = REPO_ROOT / "mechanics"
TOPOLOGY_PATH = MECHANICS_ROOT / "topology.json"

REQUIRED_ROOT_FILES = ("AGENTS.md", "README.md", "topology.json")
REQUIRED_PARTS_ROOT_FILES = ("AGENTS.md", "README.md")
REQUIRED_PART_FILES = ("README.md", "CONTRACT.md", "VALIDATION.md")
REQUIRED_LEGACY_FILES = ("AGENTS.md", "README.md", "INDEX.md", "DISTILLATION_LOG.md")
FORBIDDEN_ROOT_ENTRIES = ("_meta", "backlog", "legacy", "notes", "scratch", "templates")
FORBIDDEN_ACTIVE_PATH_TOKENS = ("landing", "seed", "stub")
FORBIDDEN_ACTIVE_PATH_PREFIXES = ("wave",)
COMMON_CENTER_PACKAGES = (
    "agon",
    "antifragility",
    "audit",
    "boundary-bridge",
    "checkpoint",
    "distillation",
    "experience",
    "growth-cycle",
    "method-growth",
    "questbook",
    "recurrence",
    "release-support",
    "rpg",
)
CANONICAL_AGENT_HEADINGS = (
    "## Applies to",
    "## Role",
    "## Read before editing",
    "## Boundaries",
    "## Validation",
    "## Closeout",
)
PACKAGE_README_HEADINGS = (
    "## Mechanic card",
    "### Trigger",
    "### Local owns",
    "### Stronger owner split",
    "### Inputs",
    "### Outputs",
    "### Must not claim",
    "### Next route",
)
README_SNIPPETS = (
    "`mechanics/` is the dispatcher for repeatable KAG operation pressure.",
    "KAG-local homes for the common center mechanics",
    "No KAG-only mechanic package is active yet.",
    "## Parts Rule",
    "python scripts/validate_mechanics_skeleton.py",
)
PARTS_STOP_LINE = "No part directories are active yet."
PARTS_NO_CANDIDATES_LINE = "No active KAG-specific"


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, f"{_display(path)}: file is missing"
    except json.JSONDecodeError as exc:
        return None, f"{_display(path)}: invalid JSON: {exc}"
    if not isinstance(payload, dict):
        return None, f"{_display(path)}: must be a JSON object"
    return payload, None


def _display(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _legacy_path_token(path: Path) -> str | None:
    for part in path.parts:
        tokens = [token for token in re.split(r"[^a-z0-9]+", part.lower()) if token]
        for token in tokens:
            if token in FORBIDDEN_ACTIVE_PATH_TOKENS:
                return token
            if any(token.startswith(prefix) for prefix in FORBIDDEN_ACTIVE_PATH_PREFIXES):
                return token
    return None


def _status_paragraph(text: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("Status:"):
            continue
        paragraph = [line.strip()]
        for next_line in lines[index + 1 :]:
            stripped = next_line.strip()
            if not stripped or stripped.startswith("#"):
                break
            paragraph.append(stripped)
        return " ".join(paragraph)
    return ""


def validate(repo_root: Path = REPO_ROOT) -> list[str]:
    mechanics_root = repo_root / "mechanics"
    issues: list[str] = []

    if not mechanics_root.is_dir():
        return ["mechanics/: directory is missing"]

    for name in FORBIDDEN_ROOT_ENTRIES:
        if (mechanics_root / name).exists():
            issues.append(f"mechanics/{name}: forbidden root mechanics entry")

    topology, topology_error = _load_json(mechanics_root / "topology.json")
    if topology_error:
        issues.append(topology_error)
        topology = None

    if topology is not None:
        if topology.get("version") != 1:
            issues.append("mechanics/topology.json: version must be 1")
        if topology.get("layer") != "aoa-kag":
            issues.append("mechanics/topology.json: layer must be aoa-kag")

        active_package_names: list[str] = []
        active_packages = topology.get("active_packages")
        if isinstance(active_packages, list):
            for package in active_packages:
                if isinstance(package, dict) and isinstance(package.get("path"), str):
                    package_path = package["path"]
                    if "/" in package_path or package_path in REQUIRED_ROOT_FILES:
                        issues.append(
                            "mechanics/topology.json: active package paths must be "
                            f"single directory names: {package_path!r}"
                        )
                    else:
                        active_package_names.append(package_path)

        if sorted(active_package_names) != sorted(COMMON_CENTER_PACKAGES):
            issues.append(
                "mechanics/topology.json: active_packages must match common center "
                f"packages {sorted(COMMON_CENTER_PACKAGES)!r}; found {sorted(active_package_names)!r}"
            )

        actual_root_entries = sorted(path.name for path in mechanics_root.iterdir())
        allowed_root_entries = sorted((*REQUIRED_ROOT_FILES, *active_package_names))
        if actual_root_entries != allowed_root_entries:
            issues.append(
                "mechanics/: root entries must match required root files plus "
                f"topology active packages {allowed_root_entries!r}; found {actual_root_entries!r}"
            )

        root_contract = topology.get("root_contract")
        if not isinstance(root_contract, dict):
            issues.append("mechanics/topology.json: root_contract must be an object")
        else:
            if sorted(root_contract.get("allowed_root_files", [])) != sorted(REQUIRED_ROOT_FILES):
                issues.append(
                    "mechanics/topology.json: root_contract.allowed_root_files "
                    f"must be {sorted(REQUIRED_ROOT_FILES)!r}"
                )
            if sorted(root_contract.get("forbidden_root_entries", [])) != sorted(FORBIDDEN_ROOT_ENTRIES):
                issues.append(
                    "mechanics/topology.json: root_contract.forbidden_root_entries "
                    f"must be {sorted(FORBIDDEN_ROOT_ENTRIES)!r}"
                )

        if not isinstance(active_packages, list):
            issues.append("mechanics/topology.json: active_packages must be a list")
        else:
            for package in active_packages:
                if not isinstance(package, dict) or not isinstance(package.get("path"), str):
                    issues.append("mechanics/topology.json: active_packages entries must name a path")
                    continue
                package_root = mechanics_root / package["path"]
                if not package_root.is_dir():
                    issues.append(f"mechanics/topology.json: package path is missing: {package['path']}")
                    continue
                if package.get("mechanic_class") != "common-center":
                    issues.append(f"mechanics/topology.json: {package['path']} mechanic_class must be common-center")
                expected_center_ref = f"Agents-of-Abyss/mechanics/{package['path']}"
                if package.get("center_mechanic_ref") != expected_center_ref:
                    issues.append(
                        f"mechanics/topology.json: {package['path']} center_mechanic_ref "
                        f"must be {expected_center_ref!r}"
                    )
                parts_status = package.get("parts_status")
                if parts_status not in {"no_active_part_dirs", "active_part_dirs"}:
                    issues.append(
                        f"mechanics/topology.json: {package['path']} parts_status must be "
                        "no_active_part_dirs or active_part_dirs"
                    )
                if not isinstance(package.get("local_function"), str) or not package["local_function"].strip():
                    issues.append(f"mechanics/topology.json: {package['path']} local_function must be a non-empty string")
                candidate_part_routes = package.get("candidate_part_routes")
                if not isinstance(candidate_part_routes, list) or not all(
                    isinstance(item, str) for item in candidate_part_routes
                ):
                    issues.append(
                        f"mechanics/topology.json: {package['path']} candidate_part_routes must be a string list"
                    )
                active_part_routes = package.get("active_part_routes", [])
                if parts_status == "active_part_dirs":
                    if not isinstance(active_part_routes, list) or not active_part_routes:
                        issues.append(
                            f"mechanics/topology.json: {package['path']} active_part_routes must be a non-empty list"
                        )
                    else:
                        active_paths: list[str] = []
                        for route in active_part_routes:
                            if not isinstance(route, dict) or not isinstance(route.get("path"), str):
                                issues.append(
                                    f"mechanics/topology.json: {package['path']} active_part_routes entries must name a path"
                                )
                                continue
                            active_path = route["path"]
                            active_paths.append(active_path)
                            legacy_token = _legacy_path_token(Path(active_path))
                            if legacy_token is not None:
                                issues.append(
                                    f"mechanics/topology.json: {package['path']} active part {active_path!r} "
                                    f"must not use legacy name token {legacy_token!r}"
                                )
                            if "/" in active_path or not active_path.strip():
                                issues.append(
                                    f"mechanics/topology.json: {package['path']} active part path must be a slug: "
                                    f"{active_path!r}"
                                )
                            if isinstance(candidate_part_routes, list) and active_path not in candidate_part_routes:
                                issues.append(
                                    f"mechanics/topology.json: {package['path']} active part {active_path!r} "
                                    "must also be listed in candidate_part_routes"
                                )
                            for field in ("owner_surface", "validation_surface", "payload_class"):
                                if not isinstance(route.get(field), str) or not route[field].strip():
                                    issues.append(
                                        f"mechanics/topology.json: {package['path']} active part {active_path!r} "
                                        f"must name {field}"
                                    )
                        if len(active_paths) != len(set(active_paths)):
                            issues.append(
                                f"mechanics/topology.json: {package['path']} active_part_routes must not duplicate paths"
                            )
                elif active_part_routes:
                    issues.append(
                        f"mechanics/topology.json: {package['path']} active_part_routes must be absent or empty "
                        "while parts_status is no_active_part_dirs"
                    )
                for filename in topology.get("package_contract", {}).get("required_files", []):
                    if not (package_root / filename).exists():
                        issues.append(f"{_display(package_root / filename)}: required package file is missing")
                _validate_package_surfaces(repo_root, package_root, package["path"], package, issues)

        local_only_mechanics = topology.get("local_only_mechanics")
        if local_only_mechanics != []:
            issues.append("mechanics/topology.json: local_only_mechanics must be empty until a KAG-only contract exists")

        local_only_candidate_pressure = topology.get("local_only_candidate_pressure")
        if not isinstance(local_only_candidate_pressure, list) or not local_only_candidate_pressure:
            issues.append("mechanics/topology.json: local_only_candidate_pressure must name KAG-only protocol pressure")
        else:
            pressure_ids = {
                item.get("id")
                for item in local_only_candidate_pressure
                if isinstance(item, dict)
            }
            if "local-kag-subtree-protocol" not in pressure_ids:
                issues.append(
                    "mechanics/topology.json: local_only_candidate_pressure must include local-kag-subtree-protocol"
                )
            for item in local_only_candidate_pressure:
                if not isinstance(item, dict) or item.get("id") != "local-kag-subtree-protocol":
                    continue
                if item.get("status") != "source_home_preflight_active":
                    issues.append(
                        "mechanics/topology.json: local-kag-subtree-protocol status must be source_home_preflight_active"
                    )
                if item.get("home_ref") != "kag/README.md":
                    issues.append(
                        "mechanics/topology.json: local-kag-subtree-protocol home_ref must be kag/README.md"
                    )

    agents_path = mechanics_root / "AGENTS.md"
    if agents_path.is_file():
        agents_text = agents_path.read_text(encoding="utf-8")
        for heading in CANONICAL_AGENT_HEADINGS:
            if heading not in agents_text:
                issues.append(f"mechanics/AGENTS.md: missing heading {heading!r}")
    else:
        issues.append("mechanics/AGENTS.md: file is missing")

    readme_path = mechanics_root / "README.md"
    if readme_path.is_file():
        readme_text = readme_path.read_text(encoding="utf-8")
        for snippet in README_SNIPPETS:
            if snippet not in readme_text:
                issues.append(f"mechanics/README.md: missing snippet {snippet!r}")
        if topology is not None and isinstance(topology.get("active_packages"), list):
            _validate_root_readme_package_map(readme_text, topology["active_packages"], issues)
    else:
        issues.append("mechanics/README.md: file is missing")

    return issues


def _validate_root_readme_package_map(
    readme_text: str,
    active_packages: list[Any],
    issues: list[str],
) -> None:
    for package in active_packages:
        if not isinstance(package, dict) or not isinstance(package.get("path"), str):
            continue
        package_name = package["path"]
        row_prefix = f"| `{package_name}` |"
        if row_prefix not in readme_text:
            issues.append(
                f"mechanics/README.md: common mechanics map must include package row {row_prefix!r}"
            )


def _validate_package_surfaces(
    repo_root: Path,
    package_root: Path,
    package_name: str,
    package: dict[str, Any],
    issues: list[str],
) -> None:
    agents_path = package_root / "AGENTS.md"
    if agents_path.is_file():
        agents_text = agents_path.read_text(encoding="utf-8")
        for heading in CANONICAL_AGENT_HEADINGS:
            if heading not in agents_text:
                issues.append(f"{_display(agents_path)}: missing heading {heading!r}")
    else:
        issues.append(f"{_display(agents_path)}: file is missing")

    readme_path = package_root / "README.md"
    if readme_path.is_file():
        readme_text = readme_path.read_text(encoding="utf-8")
        for heading in PACKAGE_README_HEADINGS:
            if heading not in readme_text:
                issues.append(f"{_display(readme_path)}: missing heading {heading!r}")
        if "Status: mapped common-center mechanic" not in readme_text:
            issues.append(f"{_display(readme_path)}: must name mapped common-center status")
        _validate_package_readme_status(readme_path, readme_text, package, issues)
    else:
        issues.append(f"{_display(readme_path)}: file is missing")

    parts_path = package_root / "PARTS.md"
    if parts_path.is_file():
        parts_text = parts_path.read_text(encoding="utf-8")
        if package.get("parts_status") == "no_active_part_dirs" and PARTS_STOP_LINE not in parts_text:
            issues.append(f"{_display(parts_path)}: missing part stop-line")
        if package.get("parts_status") == "active_part_dirs" and PARTS_STOP_LINE in parts_text:
            issues.append(f"{_display(parts_path)}: must not keep the no-active-parts stop-line")
        _validate_package_parts_map(parts_path, parts_text, package, issues)
    else:
        issues.append(f"{_display(parts_path)}: file is missing")

    provenance_path = package_root / "PROVENANCE.md"
    if provenance_path.is_file():
        provenance_text = provenance_path.read_text(encoding="utf-8")
        expected_ref = f"Agents-of-Abyss/mechanics/{package_name}"
        if expected_ref not in provenance_text:
            issues.append(f"{_display(provenance_path)}: missing center source ref {expected_ref!r}")
    else:
        issues.append(f"{_display(provenance_path)}: file is missing")

    parts_dir = package_root / "parts"
    if package.get("parts_status") == "no_active_part_dirs":
        if parts_dir.exists():
            issues.append(f"{_display(parts_dir)}: part directories are not active yet")
    else:
        _validate_active_parts(repo_root, package_root, package, issues)

    legacy_dir = package_root / "legacy"
    if legacy_dir.exists():
        if package.get("legacy_status") != "active_former_path_accounting":
            issues.append(f"{_display(legacy_dir)}: package legacy is only allowed after an active route exists")
        else:
            for filename in REQUIRED_LEGACY_FILES:
                if not (legacy_dir / filename).is_file():
                    issues.append(f"{_display(legacy_dir / filename)}: required legacy file is missing")
            legacy_agents = legacy_dir / "AGENTS.md"
            if legacy_agents.is_file():
                _validate_agent_headings(legacy_agents, issues)


def _validate_package_readme_status(
    readme_path: Path,
    readme_text: str,
    package: dict[str, Any],
    issues: list[str],
) -> None:
    status = _status_paragraph(readme_text)
    if not status:
        issues.append(f"{_display(readme_path)}: mechanic card must include a Status paragraph")
        return
    parts_status = package.get("parts_status")
    normalized = status.casefold()
    if parts_status == "active_part_dirs" and (
        "active" not in normalized or "part" not in normalized or "no active part" in normalized
    ):
        issues.append(
            f"{_display(readme_path)}: Status paragraph must reflect active part routes from topology"
        )
    if parts_status == "no_active_part_dirs" and "no active part directories yet" not in normalized:
        issues.append(
            f"{_display(readme_path)}: Status paragraph must reflect no active part directories from topology"
        )


def _validate_package_parts_map(
    parts_path: Path,
    parts_text: str,
    package: dict[str, Any],
    issues: list[str],
) -> None:
    candidate_part_routes = package.get("candidate_part_routes")
    if not isinstance(candidate_part_routes, list):
        return
    parts_status = package.get("parts_status")
    if candidate_part_routes:
        for part_name in candidate_part_routes:
            if f"`{part_name}`" not in parts_text:
                issues.append(
                    f"{_display(parts_path)}: candidate part route {part_name!r} "
                    "from topology must be named"
                )
    elif parts_status == "no_active_part_dirs" and PARTS_NO_CANDIDATES_LINE not in parts_text:
        issues.append(f"{_display(parts_path)}: must preserve no-candidate part pressure line")

    active_part_routes = package.get("active_part_routes", [])
    if not isinstance(active_part_routes, list):
        return
    for route in active_part_routes:
        if not isinstance(route, dict) or not isinstance(route.get("path"), str):
            continue
        part_name = route["path"]
        if f"`{part_name}`" not in parts_text:
            issues.append(
                f"{_display(parts_path)}: active part route {part_name!r} "
                "from topology must be named"
            )


def _validate_active_parts(
    repo_root: Path,
    package_root: Path,
    package: dict[str, Any],
    issues: list[str],
) -> None:
    parts_dir = package_root / "parts"
    if not parts_dir.is_dir():
        issues.append(f"{_display(parts_dir)}: active parts directory is missing")
        return

    active_routes = package.get("active_part_routes")
    if not isinstance(active_routes, list):
        active_routes = []
    active_names = [
        route["path"]
        for route in active_routes
        if isinstance(route, dict) and isinstance(route.get("path"), str)
    ]

    expected_entries = sorted((*REQUIRED_PARTS_ROOT_FILES, *active_names))
    actual_entries = sorted(path.name for path in parts_dir.iterdir())
    if actual_entries != expected_entries:
        issues.append(
            f"{_display(parts_dir)}: entries must match active part routes {expected_entries!r}; "
            f"found {actual_entries!r}"
        )

    for filename in REQUIRED_PARTS_ROOT_FILES:
        if not (parts_dir / filename).is_file():
            issues.append(f"{_display(parts_dir / filename)}: required parts root file is missing")
    parts_agents = parts_dir / "AGENTS.md"
    if parts_agents.is_file():
        _validate_agent_headings(parts_agents, issues)

    for route in active_routes:
        if not isinstance(route, dict) or not isinstance(route.get("path"), str):
            continue
        part_root = parts_dir / route["path"]
        if not part_root.is_dir():
            issues.append(f"{_display(part_root)}: active part directory is missing")
            continue
        _validate_active_part_path_names(part_root, issues)
        for filename in REQUIRED_PART_FILES:
            if not (part_root / filename).is_file():
                issues.append(f"{_display(part_root / filename)}: required part file is missing")
        for field in ("owner_surface", "validation_surface"):
            route_path = route.get(field)
            if isinstance(route_path, str) and route_path.strip() and not (repo_root / route_path).exists():
                issues.append(
                    f"mechanics/topology.json: active part {route['path']!r} {field} does not exist: {route_path}"
                )


def _validate_active_part_path_names(part_root: Path, issues: list[str]) -> None:
    for path in part_root.rglob("*"):
        if "__pycache__" in path.parts:
            continue
        legacy_token = _legacy_path_token(path.relative_to(part_root))
        if legacy_token is not None:
            issues.append(
                f"{_display(path)}: active part path must use functional naming, "
                f"found legacy token {legacy_token!r}"
            )


def _validate_agent_headings(path: Path, issues: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for heading in CANONICAL_AGENT_HEADINGS:
        if heading not in text:
            issues.append(f"{_display(path)}: missing heading {heading!r}")


def main() -> int:
    issues = validate(REPO_ROOT)
    if issues:
        print("Mechanics skeleton validation failed.", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    print("[ok] mechanics skeleton is present and bounded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
