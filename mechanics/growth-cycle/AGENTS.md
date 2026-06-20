# AGENTS.md

## Applies to

This card applies to `mechanics/growth-cycle/` and all descendants.

## Role

`mechanics/growth-cycle/` is the KAG-local route for surface growth posture,
owner wait states, maturity gates, and reviewed progression pressure for
existing `AOA-K-*` surfaces.

## Read before editing

Read root `AGENTS.md`, `DESIGN.md`, `mechanics/AGENTS.md`,
`mechanics/README.md`, this package `README.md`, `PARTS.md`, and
`PROVENANCE.md`. Then read the maturity, owner-wait, or roadmap surface being
changed.

## Boundaries

- Growth-cycle posture does not authorize new KAG surfaces by itself.
- Owner wait states require stronger owner evidence.
- `aoa-evals` owns proof strength.
- No part directory is active until a part-local growth contract and validator exist.

## Validation

Run `python scripts/validate_mechanics_skeleton.py`.
If maturity governance moves, run generated parity, focused tests, and release
checks.

## Closeout

Name the growth route changed, stop-rule effect, checks run, skipped checks,
and next owner route.
