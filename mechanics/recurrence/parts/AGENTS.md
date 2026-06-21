# AGENTS.md

## Applies to

This card applies to `mechanics/recurrence/parts/` and every recurrence part.

## Role

Recurrence parts own focused KAG-local operation contracts for returning from
derived substrate drift to stronger source, owner, proof, memory, or routing
refs.

## Read before editing

Read root `AGENTS.md`, `mechanics/AGENTS.md`, `mechanics/recurrence/AGENTS.md`,
`mechanics/recurrence/PARTS.md`, the target part `README.md`, `CONTRACT.md`,
and `VALIDATION.md`, then read the regrounding, recurrence, generated, schema,
example, manifest, or owner surface named by the route.

## Boundaries

- Recurrence parts do not own live recurrence law, routing dispatch, proof
  verdicts, memory truth, or runtime recovery.
- Rerouting to stronger refs is not source replacement.
- Memo readiness refs stay memo-owned. Eval refs stay eval-owned. Routing refs
  stay routing-owned.
- Repo-wide generated entrypoints may delegate or cross-check part routes; they
  should not become the only owner of recurrence operation invariants.
- Do not reactivate `seed`, `wave`, `stub`, or `landing` names in active part
  paths or payload keys.

## Validation

Run the target part validation route, then:

```bash
python scripts/validate_mechanics_skeleton.py
python scripts/run_tests.py
```

## Closeout

Report the recurrence part changed, stronger return refs preserved,
generated/read-model compatibility status, checks run, skipped checks, and
remaining recurrence pressure.
