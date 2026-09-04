# AGENTS.md

## Applies to

This card applies to `mechanics/audit/` and all descendants.

## Role

`mechanics/audit/` is the KAG-local route for making derived-surface evidence,
proof expectation refs, exposure reviews, and owner-route risk visible without
turning KAG into a proof owner.

## Read before editing

Read root `AGENTS.md`, `DESIGN.md`, `mechanics/AGENTS.md`,
this package `PARTS.md`, and
`PROVENANCE.md`. Then read the proof, exposure, or owner evidence route being
changed.

## Boundaries

- `aoa-evals` owns proof verdicts.
- KAG may point at proof expectation refs but must not certify them.
- Exposure review does not activate counterpart generation.
- No part directory is active until a part-local audit contract and validator exist.

## Validation

Run the mechanics skeleton validator.
If proof expectation or exposure-review surfaces move, run the focused KAG
validators/tests and release gate.

## Closeout

Name the audit route changed, proof owner preserved, checks run, skipped
checks, and next owner route.
