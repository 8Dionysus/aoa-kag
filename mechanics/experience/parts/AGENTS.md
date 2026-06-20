# AGENTS.md

## Applies to

This card applies to `mechanics/experience/parts/` and every Experience part
below it.

## Role

Experience parts own active KAG-side contracts for bounded experience-derived
payload families when keeping their docs or tests in root districts would hide
the operation owner.

## Read before editing

Read root `AGENTS.md`, `mechanics/AGENTS.md`, `mechanics/experience/AGENTS.md`,
`mechanics/experience/PARTS.md`, `mechanics/experience/PROVENANCE.md`, this
card, and the target part `README.md`, `CONTRACT.md`, and `VALIDATION.md`.

## Boundaries

- KAG represents experience-derived candidate surfaces; it does not own lived
  operation or adoption.
- Active Experience part contracts keep their docs, schemas, examples, and
  tests inside the owning part.
- Do not reactivate `seed`, `wave`, or `landing` names in active paths or
  payload language.
- No part may claim owner adoption, release execution, proof certification,
  runtime state, or forced local change.

## Validation

Run the target part test named in `VALIDATION.md`, then:

```bash
python scripts/validate_mechanics_skeleton.py
python scripts/run_tests.py
```

## Closeout

Report the part, part-local contract packets, validation commands, whether
legacy accounting changed, skipped checks, and the next owner route.
