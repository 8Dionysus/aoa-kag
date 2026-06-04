# AGENTS.md

## Guidance for `docs/decisions/`

`docs/decisions/` is the durable decision-rationale lane for `aoa-kag`.

Use it when the repository needs to preserve why a derived-substrate boundary,
source-ref posture, manifest policy, generated-pack route, validator guard,
maturity stop-rule, quarantine posture, bridge handoff, or regrounding seam was
chosen.

Do not use this lane for source-authored meaning, proof verdicts, live runtime
logs, generated pack payloads, private evidence, broad planning notes, or
mutable status tracking. Source repositories own authored meaning. `aoa-evals`
owns proof claims. `generated/`, `manifests/`, `schemas/`, `examples/`,
`scripts/`, and `tests/` own their local contracts.

## Record Law

- Decision files use full canonical filenames:
  `AOA-KAG-D-####-short-slug.md`.
- Each decision has an `## Index Metadata` block with:
  `Decision ID`, `Original date`, `Surface classes`, `KAG surfaces`,
  `Source lanes`, `Guard families`, and `Posture`.
- Decision IDs are stable handles. Historical date-slug paths belong to git and
  PR history, not to a compatibility lookup layer.
- Generated indexes under `docs/decisions/indexes/` are read models only. Do
  not edit them by hand.
- Material changes to rationale should usually add a new decision with explicit
  supersession prose instead of silently rewriting an accepted route.

## Boundary

Decision notes explain why KAG chose a route. They are weaker than the surfaces
they describe:

- generated KAG payloads stay in `generated/`;
- source-controlled inputs stay in `manifests/`;
- schema contracts stay in `schemas/`;
- public examples stay in `examples/`;
- build and validation behavior stays in `scripts/`;
- regression evidence stays in `tests/`;
- source repos keep stronger truth for authored technique, skill, eval, memory,
  role, playbook, routing, center, runtime, and Tree of Sophia meaning.

## When To Add A Decision

Add or update a decision record when a change materially affects:

- which owner surface KAG follows or refuses to absorb;
- whether a generated `AOA-K-*` surface may widen;
- manifest-driven donor onboarding or source-ref freshness;
- maturity governance, owner wait states, proof expectations, or stop-rules;
- bridge, handoff, quarantine, or regrounding posture;
- validation/index policy for durable KAG rationale.

Small copy edits, generated-output refreshes, local schema fixes, and routine
test maintenance do not need a decision unless they change one of those routes.

## Verify

Run:

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_decision_records.py
```

When decision metadata changes, regenerate first:

```bash
python scripts/generate_decision_indexes.py
```

Also run the owning validator for the changed surface, usually:

```bash
python scripts/validate_kag.py
python scripts/validate_nested_agents.py
python -m unittest discover -s tests -p 'test_*.py'
```
