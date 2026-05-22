# Owner Route Catalog Refresh

## Context

`aoa-kag` consumes source-owned memory, playbook, and eval surfaces as derived
KAG inputs. `aoa-memo`, `aoa-playbooks`, and `aoa-evals` now expose more convex
owner topology than the older flat paths that KAG still referenced.

The stale refs caused KAG generation to fail before it could inspect the real
derived bridge contracts.

## Decision

`aoa-kag` will follow current owner route surfaces instead of preserving legacy
consumer paths:

- memo bridge refs point to the current `aoa-memo` mechanic part and
  `generated/memory-objects/` read models
- playbook memo contract refs point to current `examples/recall/` and
  checkpoint part paths
- eval anchors are resolved through `aoa-evals/generated/eval_catalog.min.json`
  before falling back to older bundle paths
- generated KAG packs emit current owner refs

## Why

KAG is a derived substrate. Its references should help consumers return to the
owner surface that currently carries the stronger truth.

Using the eval catalog keeps KAG from hard-coding the old eval bundle layout and
lets `aoa-evals` own its own topology.

## Consequences

Good consequences:

- KAG generation follows current memory, playbook, and eval owner topology
- generated handoff, retrieval, regrounding, and maturity packs point at live
  source-owned surfaces
- future eval path movement can be absorbed through the owner catalog

Tradeoffs:

- KAG validation now depends on the sibling owner-generated eval catalog being
  present and current
- older dependency snapshots are only compatibility inputs, not emitted KAG
  truth

