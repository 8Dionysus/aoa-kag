# AGENTS.md

## Applies to

This card applies to `kag/` and every nested path until a nearer `AGENTS.md`
narrows the lane.

## Role

`kag/` is the KAG source-home preflight for `aoa-kag`.

It owns the route law for KAG-owned local-subtree protocol posture: what a
future repo-local KAG organ would need to make indexes, nodes, edges,
projections, receipts, source refs, and owner-return routes reviewable.

It does not own current generated payloads, root manifests, live graph stores,
vector indexes, embedding caches, runtime databases, proof verdicts, memory
truth, routing policy, source-authored meaning, or sibling repository `/kag`
directories.

## Read before editing

1. root `AGENTS.md`
2. `DESIGN.md`
3. `DESIGN.AGENTS.md` when route-card form or local guidance changes
4. `kag/README.md`
5. `kag/source_home.manifest.json`
6. `kag/LOCAL_SUBTREE_PROTOCOL.md`
7. `docs/decisions/AOA-KAG-D-0004-federated-local-kag-preflight.md`
8. nearest decision record when source-home, protocol, or rollout status changes
9. affected source-owner, manifest, generated, schema, script, test, mechanics,
   or runtime-owner surfaces named by the protocol route

## Boundaries

- Keep this home source-home-preflight-first until reviewed KAG record schemas,
  examples, validators, and a pilot owner exist.
- Keep `source_home.manifest.json` aligned with the active source families in
  this directory.
- Do not create `nodes/`, `edges/`, `indexes/`, `projections/`, `receipts/`, or
  sibling `/kag` directories by template copying.
- Do not move current `manifests/`, `generated/`, `schemas/`, `examples/`,
  `scripts/`, `tests/`, or `mechanics/` payloads here by symmetry.
- Do not store live graph databases, vector stores, embedding indexes, runtime
  caches, benchmark outputs, or mutable search state in this repository home.
- Do not treat local subtree records as authored source truth; every future
  record must remain source-linked and returnable to the owning repository.
- Do not treat indexes as proof, ranking truth, routing authority, or memory
  acceptance.

## Validation

For `kag/` source-home or protocol changes, run:

```bash
python scripts/validate_nested_agents.py
python -m unittest tests.test_kag_home tests.test_nested_agents_docs
```

For structural, decision, or release-facing changes, also run:

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_decision_records.py
python scripts/ci_gate.py --mode source-fast
```

Do not claim sibling `/kag` rollout readiness until a future protocol validator,
schema/example lane, and pilot owner exist.

## Closeout

Report whether the `kag/` source-home manifest, protocol, stop-line, generated
payload posture, mechanics posture, or sibling rollout posture changed; which
checks ran; which checks were skipped; and which owner route should handle the
next local-subtree step.
