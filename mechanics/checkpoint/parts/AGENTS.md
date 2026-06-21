# AGENTS.md

## Applies to

This card applies to `mechanics/checkpoint/parts/` and every checkpoint part.

## Role

Checkpoint parts own focused KAG-local operation contracts for handoff and
return routes that preserve intermediate reasoning state without becoming owner
truth.

## Read before editing

Read root `AGENTS.md`, `mechanics/AGENTS.md`, `mechanics/checkpoint/AGENTS.md`,
`mechanics/checkpoint/PARTS.md`, the target part `README.md`, `CONTRACT.md`,
and `VALIDATION.md`, then read the handoff, return, generated, schema, example,
manifest, or owner surface named by the route.

## Boundaries

- Checkpoint parts do not own durable memory, proof verdicts, live routing, or
  runtime restart behavior.
- Handoff packets are derived guides to stronger source and owner surfaces.
- Memo checkpoint refs stay memo-owned. Eval hooks stay eval-owned. Playbooks
  stay playbook-owned.
- Repo-wide generated entrypoints may delegate or cross-check part routes; they
  should not become the only owner of checkpoint operation invariants.
- Do not reactivate `seed`, `wave`, `stub`, or `landing` names in active part
  paths or payload keys.

## Validation

Run the target part validation route, then:

```bash
python scripts/validate_mechanics_skeleton.py
python scripts/run_tests.py
```

## Closeout

Report the checkpoint part changed, owner state preserved, generated/read-model
compatibility status, checks run, skipped checks, and remaining checkpoint
pressure.
