# AGENTS.md

## Applies to

This card applies to `mechanics/checkpoint/` and all descendants.

## Role

`mechanics/checkpoint/` is the KAG-local route for handoff and return packets
that preserve intermediate state without becoming owner truth.

## Read before editing

Read root `AGENTS.md`, `DESIGN.md`, `mechanics/AGENTS.md`,
this package `PARTS.md`, and
`PROVENANCE.md`. Then read the handoff, return, or checkpoint-adjacent surface
being changed.

## Boundaries

- KAG handoff packets are derived guides, not state ownership.
- `aoa-memo` owns memory writeback and durable memory objects.
- `aoa-evals` owns proof.
- The `aoa-sdk` routing control plane owns live re-entry.
- Active part directories must stay listed in `mechanics/topology.json` and keep
  a part-local checkpoint contract, validator, and focused tests.

## Validation

Run the mechanics skeleton validator.
If handoff packs move, run the relevant KAG validator/tests and release gate.
For the active reasoning handoff part, run
the part-local validator.

## Closeout

Name the checkpoint route changed, owner state preserved, checks run, skipped
checks, and next owner route.
