# AGENTS.md

## Applies to

This card applies to `mechanics/antifragility/parts/` and every Antifragility
part below it.

## Role

Antifragility parts own active KAG-side degraded-mode contracts when keeping
their docs, schemas, examples, or tests in root districts would hide the
recovery owner.

## Read before editing

Read root `AGENTS.md`, `mechanics/AGENTS.md`,
`mechanics/antifragility/AGENTS.md`, this card, and the target part
`README.md`, `CONTRACT.md`, and `VALIDATION.md`.

## Boundaries

- KAG may narrow consumer posture and point back to stronger refs.
- KAG must not claim runtime repair, source repair, proof verdicts, or hidden
  cleanup authority.
- Do not reactivate `seed`, `wave`, or `landing` names in active paths or
  payload language.

## Validation

Run the target part test named in `VALIDATION.md`, then:

```bash
python scripts/validate_mechanics_skeleton.py
python scripts/run_tests.py
```

## Closeout

Report the part, degraded-mode posture, part-local contract packets,
validation commands, skipped checks, and the next owner route.
