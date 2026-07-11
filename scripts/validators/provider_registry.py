from __future__ import annotations

import re

from .common import *
from .schema_surfaces import validate_top_level_schema

try:
    from scripts.provider_registry import (
        provider_ci_envs,
        configured_provider_roots,
        provider_dependency_pins,
        provider_entries,
        provider_repo_order,
    )
except ImportError:  # pragma: no cover - direct script execution
    from provider_registry import (  # type: ignore
        provider_ci_envs,
        configured_provider_roots,
        provider_dependency_pins,
        provider_entries,
        provider_repo_order,
    )


PIN_RE = re.compile(r"^[a-f0-9]{40}$")


def _validate_provider_registry_schema() -> None:
    validate_top_level_schema(PROVIDER_REGISTRY_SCHEMA_PATH, "provider registry")
    payload = read_json(PROVIDER_REGISTRY_MANIFEST_PATH)
    schema = read_json(PROVIDER_REGISTRY_SCHEMA_PATH)
    if not isinstance(schema, dict):
        fail("provider registry schema must be a JSON object")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        path = format_schema_path(first.path)
        suffix = f" at {path}" if path else ""
        fail(f"provider registry does not match schema{suffix}: {first.message}")


def _readiness_provider_repos() -> set[str]:
    readiness = read_json(LOCAL_KAG_READINESS_MANIFEST_PATH)
    if not isinstance(readiness, dict):
        fail("local KAG readiness matrix must be a JSON object")
    repos = readiness.get("repos")
    if not isinstance(repos, list):
        fail("local KAG readiness matrix repos must be a list")
    return {
        str(entry["repo"])
        for entry in repos
        if isinstance(entry, dict) and entry.get("provider_status") == "provider_ready"
    }


def _validate_provider_rows() -> None:
    entries = provider_entries()
    repos = [str(entry["repo"]) for entry in entries]
    if len(repos) != len(set(repos)):
        fail("provider registry must keep one row per repo")
    if set(repos) != _readiness_provider_repos():
        fail("provider registry provider set must match provider-ready readiness rows")
    if "aoa-kag" not in repos:
        fail("provider registry must include aoa-kag")

    roots = configured_provider_roots(os_root=OS_ABYSS_ROOT, entries=entries)
    for entry in entries:
        repo = str(entry["repo"])
        root = roots[repo]
        if entry["checkout_mode"] == "self" and repo != KAG_REPO:
            fail("provider registry self checkout mode is reserved for aoa-kag")
        if (entry["owner_type"] == "runtime_source") != (
            entry["root_kind"] == "runtime_source"
        ):
            fail(
                f"provider registry runtime source {repo} must pair "
                "owner_type and root_kind"
            )
        if entry["checkout_mode"] == "pinned":
            pin = str(entry.get("pinned_ref", ""))
            if not PIN_RE.match(pin):
                fail(f"provider registry pinned provider {repo} must keep a 40-char git ref")
            if not entry.get("env"):
                fail(f"provider registry pinned provider {repo} must keep an env route")
            if not entry.get("github_repository"):
                fail(f"provider registry pinned provider {repo} must keep github_repository")
            if not entry.get("checkout_path"):
                fail(f"provider registry pinned provider {repo} must keep checkout_path")
        if repo in KNOWN_REPO_ROOTS and KNOWN_REPO_ROOTS[repo] != root:
            fail(f"provider registry root for {repo} must match KNOWN_REPO_ROOTS")

    if set(provider_repo_order()) != set(repos):
        fail("provider registry order helper must cover every provider")


def _validate_workflow_provider_routes() -> None:
    repo_validation = (REPO_ROOT / ".github" / "workflows" / "repo-validation.yml").read_text(
        encoding="utf-8"
    )
    canary = (REPO_ROOT / ".github" / "workflows" / "compatibility-canary.yml").read_text(
        encoding="utf-8"
    )
    entries = provider_entries()
    envs = provider_ci_envs()
    pins = provider_dependency_pins()
    for repo, env_name in envs.items():
        checkout_path = next(
            str(entry["checkout_path"])
            for entry in entries
            if entry["repo"] == repo
        )
        expected_env = f"{env_name}: ${{{{ github.workspace }}}}/{checkout_path}"
        if expected_env not in repo_validation:
            fail(f"repo validation workflow must route {repo} through {env_name}")
        if expected_env not in canary:
            fail(f"compatibility canary workflow must route {repo} through {env_name}")
    for repo, pin in pins.items():
        if pin not in repo_validation:
            fail(f"repo validation workflow must pin {repo} at registry ref")
    for entry in entries:
        secret = str(entry.get("checkout_ssh_key_secret") or "")
        if not secret:
            continue
        repository = str(entry["github_repository"])
        marker = f"repository: {repository}"
        expected_secret = f"ssh-key: ${{{{ secrets.{secret} }}}}"
        for workflow_name, workflow in (
            ("repo validation", repo_validation),
            ("compatibility canary", canary),
        ):
            start = workflow.find(marker)
            if start < 0:
                fail(f"{workflow_name} workflow must checkout {entry['repo']}")
            end = workflow.find("\n      - name:", start)
            block = workflow[start:] if end < 0 else workflow[start:end]
            if expected_secret not in block:
                fail(f"{workflow_name} workflow must authorize {entry['repo']} with {secret}")
            if "persist-credentials: false" not in block:
                fail(f"{workflow_name} workflow must clear credentials for {entry['repo']}")


def validate_provider_registry_contract() -> None:
    _validate_provider_registry_schema()
    _validate_provider_rows()
    _validate_workflow_provider_routes()
