from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OS_ROOT = Path("/srv/AbyssOS")
PROVIDER_REGISTRY_PATH = REPO_ROOT / "manifests" / "provider_registry.json"


def load_provider_registry(path: Path = PROVIDER_REGISTRY_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("provider registry must be a JSON object")
    providers = payload.get("providers")
    if not isinstance(providers, list) or not providers:
        raise ValueError("provider registry must contain providers")
    return payload


def provider_entries(path: Path = PROVIDER_REGISTRY_PATH) -> tuple[dict[str, Any], ...]:
    payload = load_provider_registry(path)
    entries = payload["providers"]
    return tuple(entry for entry in entries if isinstance(entry, dict))


def provider_repo_order(path: Path = PROVIDER_REGISTRY_PATH) -> tuple[str, ...]:
    return tuple(str(entry["repo"]) for entry in provider_entries(path))


def provider_by_repo(path: Path = PROVIDER_REGISTRY_PATH) -> dict[str, dict[str, Any]]:
    return {str(entry["repo"]): entry for entry in provider_entries(path)}


def connector_repos(path: Path = PROVIDER_REGISTRY_PATH) -> frozenset[str]:
    return frozenset(
        str(entry["repo"])
        for entry in provider_entries(path)
        if entry.get("owner_type") == "connector"
    )


def sealed_provider_repos(path: Path = PROVIDER_REGISTRY_PATH) -> frozenset[str]:
    return frozenset(
        str(entry["repo"])
        for entry in provider_entries(path)
        if entry.get("checkout_mode") == "sealed"
    )


def provider_ci_envs(path: Path = PROVIDER_REGISTRY_PATH) -> dict[str, str]:
    return {
        str(entry["repo"]): str(entry["env"])
        for entry in provider_entries(path)
        if entry.get("env")
    }


def provider_dependency_pins(path: Path = PROVIDER_REGISTRY_PATH) -> dict[str, str]:
    return {
        str(entry["repo"]): str(entry["pinned_ref"])
        for entry in provider_entries(path)
        if entry.get("checkout_mode") == "pinned"
    }


def pinned_provider_entries(path: Path = PROVIDER_REGISTRY_PATH) -> tuple[dict[str, Any], ...]:
    return tuple(
        entry for entry in provider_entries(path) if entry.get("checkout_mode") == "pinned"
    )


def provider_checkout_envs(
    *,
    repo_root: Path = REPO_ROOT,
    path: Path = PROVIDER_REGISTRY_PATH,
) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for entry in provider_entries(path):
        if entry.get("checkout_mode") != "pinned":
            continue
        env_name = str(entry.get("env") or "")
        checkout_path = str(entry.get("checkout_path") or "")
        if env_name and checkout_path:
            result[env_name] = (repo_root / checkout_path).resolve()
    return result


def provider_root_from_entry(entry: dict[str, Any], *, os_root: Path = DEFAULT_OS_ROOT) -> Path:
    root_kind = entry.get("root_kind")
    root = Path(str(entry["root"]))
    if root_kind == "self":
        return REPO_ROOT
    if root.is_absolute():
        return root
    return os_root / root


def provider_roots(
    *,
    os_root: Path = DEFAULT_OS_ROOT,
    entries: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Path]:
    source_entries = tuple(entries) if entries is not None else provider_entries()
    return {
        str(entry["repo"]): provider_root_from_entry(entry, os_root=os_root).resolve()
        for entry in source_entries
    }


def provider_root_from_env(entry: dict[str, Any], *, os_root: Path = DEFAULT_OS_ROOT) -> Path:
    env_name = str(entry.get("env") or "")
    if env_name:
        override = os.environ.get(env_name)
        if override:
            return Path(override).expanduser().resolve()
    return provider_root_from_entry(entry, os_root=os_root).resolve()


def configured_provider_roots(
    *,
    os_root: Path = DEFAULT_OS_ROOT,
    entries: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Path]:
    source_entries = tuple(entries) if entries is not None else provider_entries()
    return {
        str(entry["repo"]): provider_root_from_env(entry, os_root=os_root)
        for entry in source_entries
    }
