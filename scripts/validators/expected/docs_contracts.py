from __future__ import annotations

import re

from .core import *

MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

VISIBLE_ROOTS = (
    REPO_ROOT,
    AOA_TECHNIQUES_ROOT,
    AOA_PLAYBOOKS_ROOT,
    AOA_EVALS_ROOT,
    AOA_MEMO_ROOT,
    AOA_AGENTS_ROOT,
    TREE_OF_SOPHIA_ROOT,
)

FULL_CROSS_REPO_ROOTS = {
    "aoa-techniques": AOA_TECHNIQUES_ROOT,
    "aoa-playbooks": AOA_PLAYBOOKS_ROOT,
    "aoa-evals": AOA_EVALS_ROOT,
    "aoa-memo": AOA_MEMO_ROOT,
    "aoa-agents": AOA_AGENTS_ROOT,
    TOS_REPO: TREE_OF_SOPHIA_ROOT,
}

REQUIRED_KAG_STRESS_REGROUNDING_SNIPPETS = (
    "Teach the derived substrate to become more honest under drift.",
    "do not silently regenerate and republish drifted surfaces as if nothing happened",
    "do not let KAG overrule source-owned truth",
    "It is not a new claim about source meaning.",
)

REQUIRED_KAG_PROJECTION_QUARANTINE_SNIPPETS = (
    "Make quarantine a bounded honesty mechanism for derived surfaces that are currently unsafe to expand.",
    "preserve evidence refs",
    "narrow consumer posture",
    "silently disappear without review",
)
