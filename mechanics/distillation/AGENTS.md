# AGENTS.md

## Applies to

This card applies to `mechanics/distillation/` and all descendants.

## Role

`mechanics/distillation/` is the KAG-local route for source lifts, donor-derived
projection narrowing, ToS chunk or route packs, and provenance-preserving
derived substrate formation.

## Read before editing

Read root `AGENTS.md`, `DESIGN.md`, `mechanics/AGENTS.md`,
`mechanics/README.md`, this package `README.md`, `PARTS.md`, and
`PROVENANCE.md`. Then read the manifest, source policy, generated output, or
source owner being lifted.

## Boundaries

- Source owners keep authored meaning.
- KAG distillation creates derived substrate shape, not source canon.
- Generated outputs remain weaker than manifests and builders.
- No part directory is active until a part-local distillation contract and validator exist.

## Validation

Run `python scripts/validate_mechanics_skeleton.py`.
If lift packs move, run the relevant KAG generator, validator, focused tests,
and release gate.

## Closeout

Name the lift route changed, source owner preserved, generated refresh status,
checks run, skipped checks, and next owner route.
