# AGENTS.md

## Applies to

This card applies to `mechanics/growth-cycle/parts/` and every growth-cycle
part.

## Role

Growth-cycle parts own focused KAG-local operation contracts for maturity
posture, owner wait states, surface growth stop-rules, and proof-gap visibility.

## Read before editing

Read root `AGENTS.md`, `mechanics/AGENTS.md`,
`mechanics/growth-cycle/AGENTS.md`, `mechanics/growth-cycle/PARTS.md`, the
target part `README.md`, `CONTRACT.md`, and `VALIDATION.md`, then read the
maturity docs, manifest, generated pack, schema, example, or validator being
changed.

## Boundaries

- Growth-cycle parts do not authorize new KAG surfaces by themselves.
- Owner wait states point outward to stronger owner repos instead of absorbing
  their unfinished work.
- Proof gaps stay weaker than `aoa-evals` verdicts.
- Repo-wide generated entrypoints may delegate or cross-check this route; they
  should not become the only owner of growth-cycle stop-rules.
- Do not reactivate `seed`, `wave`, `stub`, or `landing` names in active part
  paths or payload keys.

## Validation

Run the target part validation route, then:

```bash
python scripts/validate_mechanics_skeleton.py
python scripts/run_tests.py
```

## Closeout

Report the growth-cycle part changed, stop-rule effect, owner wait posture,
repo-wide generated compatibility status, checks run, skipped checks, and
remaining growth-cycle pressure.
