# AGENTS.md

## Applies to

This card applies to `mechanics/questbook/` and all descendants.

## Role

`mechanics/questbook/` is the KAG-local route for durable derived-layer
obligations, quest source posture, and quest dispatch or catalog projections.

## Read before editing

Read root `AGENTS.md`, `DESIGN.md`, `mechanics/AGENTS.md`,
`mechanics/README.md`, this package `README.md`, `PARTS.md`, `PROVENANCE.md`,
`QUESTBOOK.md`, and `docs/QUESTBOOK_KAG_INTEGRATION.md`.

## Boundaries

- Quest objects track obligations; they are not private scratch.
- Generated quest views do not author quest meaning.
- Owner repositories prove acceptance or closure.
- KAG quests should stay about derived-substrate work.
- No part directory is active until a part-local quest contract and validator exist.

## Validation

Run `python scripts/validate_mechanics_skeleton.py`.
If quest surfaces move, run `python scripts/validate_kag.py` and focused
questbook tests before broader release checks.

## Closeout

Name quest surfaces changed, generated view status, checks run, skipped checks,
and next owner route.
