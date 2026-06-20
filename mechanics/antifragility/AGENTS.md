# AGENTS.md

## Applies to

This card applies to `mechanics/antifragility/` and all descendants.

## Role

`mechanics/antifragility/` is the KAG-local route for stress, projection-health,
quarantine, and source-first recovery when derived surfaces weaken.

## Read before editing

Read root `AGENTS.md`, `DESIGN.md`, `mechanics/AGENTS.md`,
`mechanics/README.md`, this package `README.md`, `PARTS.md`, and
`PROVENANCE.md`. Then read the stress, quarantine, or projection-health surface
being changed.

## Boundaries

- Antifragility pressure must improve source return, not invent KAG authority.
- Quarantine does not delete source truth or close owner work.
- Projection health is not a proof verdict.
- Only the parts listed in `PARTS.md` and `mechanics/topology.json` are active.
  Additional part directories need a part-local stress contract and validator.

## Validation

Run `python scripts/validate_mechanics_skeleton.py`.
When changing an active part payload, run that part's `VALIDATION.md`.

## Closeout

Name the stress route changed, degraded mode or quarantine posture, checks run,
skipped checks, and next owner route.
