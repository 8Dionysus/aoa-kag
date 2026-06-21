# AGENTS.md

## Applies to

This card applies to `mechanics/questbook/` and all descendants.

## Role

`mechanics/questbook/` is the KAG-local route for durable derived-layer
obligations, quest source posture, and quest dispatch or catalog projections.

## Read before editing

Read root `AGENTS.md`, `DESIGN.md`, `mechanics/AGENTS.md`,
`mechanics/README.md`, this package `README.md`, `PARTS.md`, `PROVENANCE.md`,
`QUESTBOOK.md`, and
`parts/quest-store/docs/questbook-kag-integration.md`.

## Boundaries

- Quest objects track obligations; they are not private scratch.
- Generated quest views do not author quest meaning.
- Owner repositories prove acceptance or closure.
- KAG quests should stay about derived-substrate work.
- `parts/quest-store/` owns focused quest source, public-index, and
  catalog/dispatch alignment validation.
- Additional part directories need a part-local quest contract and validator
  first.

## Validation

Run `python scripts/validate_mechanics_skeleton.py`.
If quest surfaces move, run
`python mechanics/questbook/parts/quest-store/scripts/validate_quest_store.py`,
focused questbook tests, `python scripts/validate_kag.py`, and broader release
checks when the change is release-facing.

## Closeout

Name quest surfaces changed, generated view status, checks run, skipped checks,
and next owner route.
