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
- No part directory is active until a part-local checkpoint contract and validator exist.

## Validation

Run `python scripts/validate_mechanics_skeleton.py`.
If handoff packs move, run the relevant KAG validator/tests and release gate.

## Closeout

Name the checkpoint route changed, owner state preserved, checks run, skipped
checks, and next owner route.
