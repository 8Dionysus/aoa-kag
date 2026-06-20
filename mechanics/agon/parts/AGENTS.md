# AGENTS.md

## Applies to

This card applies to `mechanics/agon/parts/` and every Agon part below it.

## Role

Agon parts own active KAG-side sub-mechanics for candidate review routes. They
hold part-local source configs, focused builders, validators, tests, and route
docs when keeping those artifacts in root districts would hide the operation
owner.

## Read before editing

Read root `AGENTS.md`, `mechanics/AGENTS.md`, `mechanics/agon/AGENTS.md`,
`mechanics/agon/PARTS.md`, `mechanics/agon/PROVENANCE.md`, this card, and the
target part `README.md`, `CONTRACT.md`, and `VALIDATION.md`.

## Boundaries

- Generated registries remain root published read models under `generated/`.
- Repo-wide schemas and examples remain under `schemas/` and `examples/` until a
  part-local contract proves they should move.
- Part-local source configs use functional `.source.json` names, not `seed`
  names.
- Historical wave or landing names stay in `mechanics/agon/legacy/` accounting,
  not active part paths or active payload keys.
- No part may claim verdict, proof, memory, ToS canon, source truth, runtime
  execution, rank mutation, or scheduler effects.

## Validation

Run the target part validator and focused test named in `VALIDATION.md`, then:

```bash
python scripts/validate_mechanics_skeleton.py
python scripts/run_tests.py
```

## Closeout

Report the part, source config, generated registry, validation commands, whether
legacy accounting changed, skipped checks, and the next owner route.
