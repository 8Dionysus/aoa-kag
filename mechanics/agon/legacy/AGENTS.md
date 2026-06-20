# AGENTS.md

## Applies to

This card applies to `mechanics/agon/legacy/`.

## Role

`legacy/` preserves former root path and naming accounting for Agon KAG payloads
that now have active part-local routes. It is not the first route for current
edits.

## Read before editing

Read `../README.md`, `../PARTS.md`, `../PROVENANCE.md`, this `README.md`,
`INDEX.md`, and the active part route named by the legacy entry.

## Boundaries

- Do not add current behavior only under legacy.
- Do not use legacy as a trash archive.
- Do not reactivate `seed`, `wave`, or landing names in active paths.
- Do not put generated outputs, active schemas, active tests, or source truth in
  this directory.
- Keep every entry mapped to an active route or explicit hold.

## Validation

Run:

```bash
python scripts/validate_mechanics_skeleton.py
```

## Closeout

Report former path entries changed, active routes they map to, and whether any
active part contract changed.
