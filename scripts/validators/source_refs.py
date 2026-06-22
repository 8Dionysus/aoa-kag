from __future__ import annotations

from .common import *

def missing_full_cross_repo_roots() -> list[str]:
    missing: list[str] = []
    for repo, root in FULL_CROSS_REPO_ROOTS.items():
        if not root.exists():
            missing.append(f"{repo}={root.as_posix()}")
    return missing

def resolve_relative_ref(root: Path, raw_ref: str, *, label: str) -> Path:
    path_text, _, anchor = raw_ref.partition("#")
    target = root / path_text
    if root != REPO_ROOT and not root.exists():
        return target
    if not target.exists():
        repo_name = next(
            (
                candidate_repo
                for candidate_repo, candidate_root in FULL_CROSS_REPO_ROOTS.items()
                if root == candidate_root
            ),
            KAG_REPO if root == REPO_ROOT else "",
        )
        for alias in COMPATIBILITY_REF_ALIASES.get(repo_name, {}).get(path_text, ()):
            alias_target = root / alias
            if alias_target.exists():
                target = alias_target
                break
        else:
            fail(f"{label} references a missing path: {raw_ref}")
    if anchor:
        if target.suffix.lower() != ".md":
            fail(f"{label} uses a markdown anchor on a non-markdown target: {raw_ref}")
        if anchor not in markdown_anchors(target):
            fail(f"{label} references a missing markdown anchor: {raw_ref}")
    return target

def path_matches_current_or_alias(repo: str, current_path: str, observed_path: object) -> bool:
    if observed_path == current_path:
        return True
    return observed_path in COMPATIBILITY_REF_ALIASES.get(repo, {}).get(current_path, ())

def resolve_authoritative_ref(raw_ref: str, *, label: str) -> Path:
    if raw_ref.startswith("Tree-of-Sophia/"):
        return resolve_relative_ref(
            TREE_OF_SOPHIA_ROOT,
            raw_ref.split("/", 1)[1],
            label=label,
        )
    if raw_ref.startswith("aoa-memo/"):
        return resolve_relative_ref(
            AOA_MEMO_ROOT,
            raw_ref.split("/", 1)[1],
            label=label,
        )
    fail(f"{label} must reference Tree-of-Sophia or aoa-memo: {raw_ref}")

def resolve_aoa_techniques_ref(raw_ref: str, *, label: str) -> Path:
    if not raw_ref.startswith("aoa-techniques/"):
        fail(f"{label} must reference aoa-techniques: {raw_ref}")
    return resolve_relative_ref(
        AOA_TECHNIQUES_ROOT,
        raw_ref.split("/", 1)[1],
        label=label,
    )

def resolve_aoa_playbooks_ref(raw_ref: str, *, label: str) -> Path:
    if not raw_ref.startswith("aoa-playbooks/"):
        fail(f"{label} must reference aoa-playbooks: {raw_ref}")
    return resolve_relative_ref(
        AOA_PLAYBOOKS_ROOT,
        raw_ref.split("/", 1)[1],
        label=label,
    )

def resolve_aoa_evals_ref(raw_ref: str, *, label: str) -> Path:
    if not raw_ref.startswith("aoa-evals/"):
        fail(f"{label} must reference aoa-evals: {raw_ref}")
    return resolve_relative_ref(
        AOA_EVALS_ROOT,
        raw_ref.split("/", 1)[1],
        label=label,
    )

def resolve_aoa_agents_ref(raw_ref: str, *, label: str) -> Path:
    if not raw_ref.startswith("aoa-agents/"):
        fail(f"{label} must reference aoa-agents: {raw_ref}")
    return resolve_relative_ref(
        AOA_AGENTS_ROOT,
        raw_ref.split("/", 1)[1],
        label=label,
    )

def resolve_known_ref(raw_ref: str, *, label: str) -> Path:
    if raw_ref.startswith("aoa-techniques/"):
        return resolve_aoa_techniques_ref(raw_ref, label=label)
    if raw_ref.startswith("aoa-playbooks/"):
        return resolve_aoa_playbooks_ref(raw_ref, label=label)
    if raw_ref.startswith("aoa-evals/"):
        return resolve_aoa_evals_ref(raw_ref, label=label)
    if raw_ref.startswith("aoa-memo/"):
        return resolve_relative_ref(
            AOA_MEMO_ROOT,
            raw_ref.split("/", 1)[1],
            label=label,
        )
    if raw_ref.startswith("aoa-agents/"):
        return resolve_aoa_agents_ref(raw_ref, label=label)
    if raw_ref.startswith("Tree-of-Sophia/"):
        return resolve_relative_ref(
            TREE_OF_SOPHIA_ROOT,
            raw_ref.split("/", 1)[1],
            label=label,
        )
    return resolve_relative_ref(REPO_ROOT, raw_ref, label=label)

def resolve_source_owned_export_ref(raw_ref: str, *, owner_repo: str, label: str) -> Path:
    if raw_ref.startswith("repo:"):
        return resolve_known_ref(raw_ref.split("repo:", 1)[1], label=label)
    if owner_repo == "aoa-memo":
        return resolve_relative_ref(AOA_MEMO_ROOT, raw_ref, label=label)
    if owner_repo == "aoa-techniques":
        return resolve_relative_ref(AOA_TECHNIQUES_ROOT, raw_ref, label=label)
    if owner_repo == "aoa-playbooks":
        return resolve_relative_ref(AOA_PLAYBOOKS_ROOT, raw_ref, label=label)
    if owner_repo == "aoa-evals":
        return resolve_relative_ref(AOA_EVALS_ROOT, raw_ref, label=label)
    if owner_repo == "aoa-agents":
        return resolve_relative_ref(AOA_AGENTS_ROOT, raw_ref, label=label)
    if owner_repo == TOS_REPO:
        return resolve_relative_ref(TREE_OF_SOPHIA_ROOT, raw_ref, label=label)
    return resolve_known_ref(raw_ref, label=label)
