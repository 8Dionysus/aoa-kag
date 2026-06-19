# AGENTS.md

## Applies to

This card applies to `docs/validation/` and all descendants.

## Role

`docs/validation/` owns the active map of validation lanes, command authority,
validator posture, script inventory, lane posture, and failure routes for
`aoa-kag`.

It documents how guards are routed. It does not author KAG source meaning,
generated payload meaning, runtime graph state, eval verdicts, memory truth, or
sibling-repo authority.

## Read before editing

Read root `AGENTS.md`, `DESIGN.md`, `DESIGN.AGENTS.md`,
`config/validation_lanes.json`, `scripts/validation_lanes.py`, and
`scripts/ci_gate.py`.

For script-surface changes, also read `SCRIPT_TOPOLOGY.md` and
`script_inventory.json`.

## Boundaries

- Do not duplicate full lane command sequences in docs.
- Do not let `script_inventory.json` become command authority; it describes
  owner, lane, side-effect, and focused test coverage only.
- Do not promote future graph, RAG, runtime, local `/kag`, eval, memory, or
  mechanic part-local notes into hard gates until `aoa-kag` owns one concrete
  checked surface.
- Do not let generated validators define source-authored meaning from sibling
  repositories or Tree of Sophia.

## Validation

Run:

```bash
python -m unittest tests.test_validation_command_authority tests.test_script_topology
python scripts/ci_gate.py --mode source-fast
```

For release-visible lane changes, run:

```bash
python scripts/release_check.py
```

## Closeout

Report changed lane ids, command-authority surfaces, script inventory entries,
checks run, checks skipped, and any advisory boundary intentionally left out of
a hard gate.
