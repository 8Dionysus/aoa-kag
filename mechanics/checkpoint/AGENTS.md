# AGENTS.md

## Applies to

This card applies to `mechanics/checkpoint/` and all descendants.

## Role

`mechanics/checkpoint/` is the KAG-local route for handoff and return packets
that preserve intermediate state without becoming owner truth.

## Read before editing

Read root `AGENTS.md`, `DESIGN.md`, `mechanics/AGENTS.md`,
`mechanics/README.md`, this package `README.md`, `PARTS.md`, and
`PROVENANCE.md`. Then read the handoff, return, or checkpoint-adjacent surface
being changed.

## Boundaries

- KAG handoff packets are derived guides, not state ownership.
- `aoa-memo` owns memory writeback and durable memory objects.
- `aoa-evals` owns proof.
- `aoa-routing` owns live re-entry.
- Active part directories must stay listed in `mechanics/topology.json` and keep
  a part-local checkpoint contract, validator, and focused tests.

## Validation

Run `python scripts/validate_mechanics_skeleton.py`.
If handoff packs move, run the relevant KAG validator/tests and release gate.
For the active reasoning handoff part, run
`python mechanics/checkpoint/parts/reasoning-handoff/scripts/validate_reasoning_handoff.py`.

## Closeout

Name the checkpoint route changed, owner state preserved, checks run, skipped
checks, and next owner route.
