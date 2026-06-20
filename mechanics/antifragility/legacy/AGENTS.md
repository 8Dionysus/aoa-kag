# AGENTS.md

## Applies to

This card applies to `mechanics/antifragility/legacy/`.

## Role

`legacy/` preserves former root path and naming accounting for Antifragility
payloads after an active part route exists.

## Read before editing

Read root `AGENTS.md`, `mechanics/antifragility/AGENTS.md`,
`mechanics/antifragility/PROVENANCE.md`, this card, and `INDEX.md`.

## Boundaries

- Do not add current behavior only under legacy.
- Do not use legacy as a trash archive.
- Do not reactivate `seed`, `wave`, or `landing` names in active paths.

## Validation

Run:

```bash
python scripts/validate_mechanics_skeleton.py
```

## Closeout

Report the legacy entry changed, active part route, validation commands, skipped
checks, and why the entry belongs in legacy instead of active payloads.
