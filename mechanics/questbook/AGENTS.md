# AGENTS.md

## Applies to

This card applies to `mechanics/questbook/` and all descendants.

## Role

`mechanics/questbook/` is the KAG-local route for durable derived-layer
obligations, quest source posture, and quest dispatch or catalog projections.

## Read before editing

Read root `AGENTS.md`, `DESIGN.md`, `mechanics/AGENTS.md`,
this package `PARTS.md`, `PROVENANCE.md`,
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

Run the mechanics skeleton validator.
If quest surfaces move, run
the quest-store validator,
focused questbook tests, the KAG validator, and broader release
checks when the change is release-facing.

## Closeout

Name quest surfaces changed, generated view status, checks run, skipped checks,
and next owner route.
