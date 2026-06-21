# AGENTS.md

## Applies to

This card applies to `mechanics/boundary-bridge/parts/` and every
boundary-bridge part.

## Role

Boundary-bridge parts own focused KAG-local operation contracts for bounded
crossing routes between source-owned exports, ToS surfaces, memo faces,
counterpart edges, federation entries, and derived projections.

## Read before editing

Read root `AGENTS.md`, `mechanics/AGENTS.md`,
`mechanics/boundary-bridge/AGENTS.md`, `mechanics/boundary-bridge/PARTS.md`,
the target part `README.md`, `CONTRACT.md`, and `VALIDATION.md`, then read the
source, manifest, generated, schema, example, or owner surface named by the
bridge route.

## Boundaries

- A bridge part does not transfer source authority.
- Source-owned exports remain owner-authored inputs; generated KAG outputs stay
  derived read models.
- Memo bridge faces do not become memory truth, routing activation, proof, or
  graph sovereignty.
- Repo-wide generated entrypoints may delegate or cross-check part routes; they
  should not become the only owner of bridge operation invariants.
- Do not reactivate `seed`, `wave`, `stub`, or `landing` names in active part
  paths or payload keys.

## Validation

Run the target part validation route, then:

```bash
python scripts/validate_mechanics_skeleton.py
python scripts/run_tests.py
```

## Closeout

Report the bridge part changed, source owners preserved, generated/read-model
compatibility status, checks run, skipped checks, and remaining bridge
pressure.
