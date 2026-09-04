# AGENTS.md

## Applies to

This card applies to `mechanics/questbook/parts/` and every questbook part.

## Role

Questbook parts own focused KAG-local operation contracts for quest source
shape, public index posture, dispatch examples, and validation.

## Read before editing

Read root `AGENTS.md`, `mechanics/AGENTS.md`,
`mechanics/questbook/AGENTS.md`, `mechanics/questbook/PARTS.md`, the target
part `CONTRACT.md`, and `VALIDATION.md`, then read the source
quest surface, schema, example, or validator being changed.

## Boundaries

- Quest source records remain public source surfaces, not private notes.
- Part-local validators may enforce quest shape, but they do not own owner
  acceptance, proof closure, or implementation activation.
- Root compatibility entrypoints may delegate here; they should not duplicate
  quest-store rules after a part owns them.
- Do not reactivate `seed`, `wave`, `stub`, or `landing` names in active part
  paths or payload keys.

## Validation

The target part `VALIDATION.md` owns the focused route; review quest-source and
root-compatibility boundaries afterward.

## Closeout

Report the questbook part changed, source records preserved, root entrypoints
kept compatible, checks run, skipped checks, and remaining questbook package
pressure.
