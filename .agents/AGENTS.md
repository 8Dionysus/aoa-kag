# AGENTS.md

## Applies to

This card applies to `.agents/` and all descendants unless a nearer
`AGENTS.md` narrows the lane.

## Role

`.agents/` holds agent-facing companion lanes for `aoa-kag`: repo-local skills,
Codex Spark guidance, handoff prompts, and model-facing support surfaces.

It helps agents operate inside the KAG derived-substrate repository. It does
not author KAG model meaning, source-owner truth, generated payload truth,
proof verdicts, runtime state, or mechanics law.

## Read before editing

Read root `AGENTS.md`, `DESIGN.AGENTS.md`, this card, and the nearest lane
card before changing prompt-like or agent-facing material.

For Codex Spark work, read `.agents/spark/AGENTS.md`; use
`.agents/spark/SWARM.md` only when a Spark swarm is explicitly requested.

For exported skill material, read `.agents/skills/AGENTS.md` and the target
`SKILL.md`.

## Boundaries

- Keep maintained agent lanes under `.agents/<lane>/`.
- Keep exported skill guidance under `.agents/skills/`.
- Do not restore root `Spark/` as an active lane.
- Do not encode private memory, hidden authority, local-only host assumptions,
  secrets, or unreviewable autonomy here.
- Do not make `.agents/` stronger than root route law, KAG source docs,
  mechanics packages, manifests, schemas, builders, validators, tests, or
  sibling-owner truth.

## Validation

For agent-lane route changes, run:

```bash
python scripts/validate_nested_agents.py
python scripts/validate_semantic_agents.py
```

Use the touched owner surface's validation when an agent lane points at a
source, generated, mechanic, quest, or release surface.

## Closeout

Report the agent lane changed, which stronger owner surface it routes to,
what validation ran, what was skipped, and whether a slower route or owner
handoff remains.
