# Owner Route Catalog Refresh

## Index Metadata

- Decision ID: AOA-KAG-D-0002
- Original date: 2026-05-22
- Surface classes: generated/source-refs, manifests, scripts/generation, validation
- KAG surfaces: owner route catalog, derived packs, source refs, eval catalog
- Source lanes: aoa-memo, aoa-playbooks, aoa-evals
- Guard families: source-owned authority, owner route freshness, generated output parity
- Posture: accepted

## Context

`aoa-kag` consumes source-owned memory, playbook, and eval surfaces as derived
KAG inputs. `aoa-memo`, `aoa-playbooks`, and `aoa-evals` exposed more convex
owner topology than the older flat paths that KAG still referenced.

The stale refs caused KAG generation to fail before it could inspect the real
derived bridge contracts.

## Decision

`aoa-kag` will follow current owner route surfaces instead of preserving legacy
consumer paths:

- memo bridge refs point to the current `aoa-memo` mechanic part and
  `generated/memory-objects/` read models;
- playbook memo contract refs point to current `examples/recall/` and
  checkpoint part paths;
- eval anchors are resolved through `aoa-evals/generated/eval_catalog.min.json`
  before falling back to older bundle paths;
- generated KAG packs emit current owner refs.

## Options Considered

- Preserve old flat dependency refs for compatibility.
- Copy owner topology knowledge into KAG as independent doctrine.
- Resolve through current owner surfaces and catalogs, keeping KAG derived.

## Rationale

KAG is a derived substrate. Its references should help consumers return to the
owner surface that currently carries the stronger truth.

Using the eval catalog keeps KAG from hard-coding the old eval bundle layout and
lets `aoa-evals` own its own topology.

## Consequences

Good consequences:

- KAG generation follows current memory, playbook, and eval owner topology;
- generated handoff, retrieval, regrounding, and maturity packs point at live
  source-owned surfaces;
- future eval path movement can be absorbed through the owner catalog.

Tradeoffs:

- KAG validation now depends on the sibling owner-generated eval catalog being
  present and current;
- older dependency snapshots are only compatibility inputs, not emitted KAG
  truth.

## Source Surfaces

- `scripts/kag_generation.py`
- `scripts/validate_kag.py`
- `mechanics/checkpoint/parts/reasoning-handoff/generated/reasoning_handoff_pack.min.json`
- `mechanics/recurrence/parts/return-regrounding/generated/return_regrounding_pack.min.json`
- `mechanics/growth-cycle/parts/surface-growth-stop-rule/generated/kag_maturity_governance.min.json`
- `aoa-evals/generated/eval_catalog.min.json`

## Validation

Run:

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_decision_records.py
python scripts/release_check.py
```
