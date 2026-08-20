#!/usr/bin/env python3
"""Build a validated OS Abyss repo-self KAG federation projection."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from scripts.provider_registry import configured_provider_roots
    from scripts.repo_local.federation import RepoKagFederation, github_ref_names_by_repo
    from scripts.repo_local.portable_family import load_portable_family_with_state
    from scripts.validators.repo_local_kag_index import (
        load_repo_local_kag_repository_index_family,
        validate_repo_local_kag_repository_index_family,
    )
except ImportError:  # pragma: no cover - direct script execution
    from provider_registry import configured_provider_roots  # type: ignore
    from repo_local.federation import RepoKagFederation, github_ref_names_by_repo  # type: ignore
    from repo_local.portable_family import load_portable_family_with_state  # type: ignore
    from validators.repo_local_kag_index import (  # type: ignore
        load_repo_local_kag_repository_index_family,
        validate_repo_local_kag_repository_index_family,
    )


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _sha256_uri(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def load_owner_bundle_with_delivery(
    repo_root: Path,
    *,
    artifact_root: Path | None = None,
    allow_shadow_git: bool = True,
) -> tuple[
    dict[str, Any],
    dict[str, dict[str, Any]],
    dict[str, Any],
]:
    root = repo_root.resolve()
    manifest_path = root / "kag" / "indexes" / "index_family.manifest.json"
    if manifest_path.is_file():
        source, family, manifest, state = load_portable_family_with_state(
            root,
            artifact_root=artifact_root,
            allow_shadow_git=allow_shadow_git,
        )
        family = validate_repo_local_kag_repository_index_family(
            family,
            source_payload=source,
            label=f"{root.name} federation family",
        )
        corpus_digest = str(state.get("corpus_digest") or "")
        distribution_digest = str(state.get("distribution_digest") or "")
        if not corpus_digest:
            corpus_digest = _sha256_uri(
                json.dumps(
                    {"source": source, "family": family},
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
        if not distribution_digest:
            distribution_digest = _sha256_uri(
                manifest_path.read_bytes()
            )
        delivery = {
            "corpus_digest": corpus_digest,
            "distribution_digest": distribution_digest,
            "delivery_state": str(state.get("state") or "stale"),
            "complete": bool(state.get("complete")),
            "manifest_schema": str(manifest.get("schema_version") or ""),
            "routes": dict(state.get("routes") or {}),
        }
        distribution_identity = manifest.get("distribution_identity")
        if isinstance(distribution_identity, Mapping):
            delivery["distribution_digest"] = str(
                distribution_identity.get("content_digest")
                or delivery["distribution_digest"]
            )
            delivery["corpus_digest"] = str(
                distribution_identity.get("corpus_digest")
                or delivery["corpus_digest"]
            )
        for key, field in (
            ("hot_profile", "hot_profile_digest"),
            ("artifact_locators", "locator_digest"),
        ):
            packet = manifest.get(key)
            if isinstance(packet, Mapping) and packet.get("content_digest"):
                delivery[field] = str(packet["content_digest"])
        transport = manifest.get("transport")
        if isinstance(transport, Mapping) and transport.get("pack_index_digest"):
            delivery["pack_index_digest"] = str(
                transport["pack_index_digest"]
            )
        return source, family, delivery

    source, family = load_repo_local_kag_repository_index_family(
        root,
        label=f"{root.name} federation family",
        artifact_root=artifact_root,
        allow_shadow_git=allow_shadow_git,
    )
    logical_digest = _sha256_uri(
        json.dumps(
            {"source": source, "family": family},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return source, family, {
        "corpus_digest": logical_digest,
        "distribution_digest": _sha256_uri(
            f"legacy-git-full:{logical_digest}".encode("utf-8")
        ),
        "delivery_state": "legacy_git_full",
        "complete": True,
        "manifest_schema": "legacy-monolith",
        "routes": {"git_hot": len(family) + 1},
    }


def load_owner_bundle(
    repo_root: Path,
    *,
    artifact_root: Path | None = None,
    allow_shadow_git: bool = True,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    source, family, _ = load_owner_bundle_with_delivery(
        repo_root,
        artifact_root=artifact_root,
        allow_shadow_git=allow_shadow_git,
    )
    return source, family


def parse_owner_artifact_roots(
    values: Sequence[str],
    *,
    known_owners: set[str],
) -> dict[str, Path]:
    roots: dict[str, Path] = {}
    for raw in values:
        owner, separator, raw_path = raw.partition("=")
        if not separator or not owner or not raw_path:
            raise SystemExit(
                "--owner-artifact-root must use OWNER=/absolute/or/relative/path"
            )
        if owner not in known_owners:
            raise SystemExit(f"unknown artifact-root owner: {owner}")
        if owner in roots:
            raise SystemExit(f"duplicate artifact root for owner: {owner}")
        roots[owner] = Path(raw_path).expanduser().resolve()
    return roots


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a federated graph projection from repo-owned KAG families."
    )
    parser.add_argument("--os-root", type=Path, default=Path("/srv/AbyssOS"))
    parser.add_argument("--home-src-root", type=Path, default=Path("/home/dionysus/src"))
    parser.add_argument("--repo", action="append", dest="repos")
    parser.add_argument(
        "--owner-artifact-root",
        action="append",
        default=[],
        metavar="OWNER=PATH",
    )
    parser.add_argument(
        "--no-shadow-git",
        action="store_true",
        help="Require cold objects from the supplied owner artifact roots.",
    )
    parser.add_argument("--output", default="-", help="Projection path or '-' for stdout.")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    roots = configured_provider_roots(
        os_root=args.os_root.resolve(),
        home_src_root=args.home_src_root.resolve(),
    )
    selected = set(args.repos or roots)
    unknown = sorted(selected - set(roots))
    if unknown:
        raise SystemExit(f"unknown provider repos: {', '.join(unknown)}")
    artifact_roots = parse_owner_artifact_roots(
        args.owner_artifact_root,
        known_owners=set(roots),
    )
    bundles = {
        repo: load_owner_bundle(
            roots[repo],
            artifact_root=artifact_roots.get(repo),
            allow_shadow_git=not args.no_shadow_git,
        )
        for repo in sorted(selected)
    }
    selected_roots = {repo: roots[repo] for repo in sorted(selected)}
    projection = RepoKagFederation(
        bundles,
        github_refs_by_repo=github_ref_names_by_repo(selected_roots),
    ).projection()
    rendered = json.dumps(
        projection,
        ensure_ascii=False,
        indent=2 if args.pretty else None,
        sort_keys=True,
        separators=None if args.pretty else (",", ":"),
    ) + "\n"
    if args.output == "-":
        if args.check:
            raise SystemExit("--check requires a file --output")
        sys.stdout.write(rendered)
        return 0
    output = Path(args.output).resolve()
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
            print(f"[repo-local-kag-federation] drift in {output}", file=sys.stderr)
            return 1
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"[repo-local-kag-federation] wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
