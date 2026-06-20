# AGENTS.md

## Applies to

This card applies to `mechanics/recurrence/` and all descendants.

## Role

`mechanics/recurrence/` is the KAG-local route for recurrence pressure that
needs to return a caller from derived substrate drift to stronger source,
owner, proof, memory, or routing refs.

## Read before editing

Read root `AGENTS.md`, `DESIGN.md`, `mechanics/AGENTS.md`,
`mechanics/README.md`, this package `README.md`, `PARTS.md`, and `PROVENANCE.md`.
Then read the current recurrence, regrounding, or generated surface being
changed.

## Boundaries

- KAG regrounding is a derived return route, not recurrence law.
- `aoa-routing` owns live route behavior.
- `aoa-memo` owns memory truth.
- `aoa-evals` owns proof.
- Source repositories own source meaning.
- No part directory is active until a part-local return contract and validator exist.

## Validation

Run `python scripts/validate_mechanics_skeleton.py`.
If recurrence payloads move, run the relevant KAG generator, validator, focused
tests, and release gate.

## Closeout

Name the recurrence route changed, the stronger return refs preserved, checks
run, skipped checks, and the next owner route.
