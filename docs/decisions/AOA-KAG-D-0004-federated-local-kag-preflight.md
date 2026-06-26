# Federated Local KAG Preflight

## Index Metadata

- Decision ID: AOA-KAG-D-0004
- Original date: 2026-06-19
- Surface classes: docs/decisions
- KAG surfaces: federation readiness, local KAG subtree, derived-substrate boundary
- Source lanes: aoa-kag, sibling repositories, aoa-routing, aoa-memo, aoa-evals, Tree-of-Sophia
- Guard families: source-owned authority, federation protocol, local KAG stop-line, generated output boundary
- Posture: accepted

## Context

`aoa-kag` currently publishes a bounded derived-substrate portfolio: source-owned
export dependencies, a donor registry, a two-repo federation spine pilot,
maturity governance, regrounding surfaces, and narrow generated packs.

The next architectural pressure is larger than the current pilot. OS Abyss is
expected to grow toward repo-local KAG subtrees: each repository may eventually
own a local `/kag` organ with indexes, nodes, edges, local graph projections,
provenance, and compact generated read models for that repository.

That future shape must not be confused with the current `kag_export.min.json`
pilot. The current export is a narrow source-owned ingress capsule. The future
`/kag` subtree is a repo-local knowledge organ whose contract should be defined
only after `aoa-kag` itself is refactored.

The durable repository trace should stay here, in the decision lane, rather
than spreading future intent across current route docs.

## Decision

`aoa-kag` will treat repo-local `/kag` as a future federated local-subtree
contract, not as the current active export shape.

Until the `aoa-kag` refactor lands, sibling repositories should not receive new
`/kag` directories by template copying. Current `kag_export.min.json` donors
remain a pilot ingress format. They may inform the future contract, but they do
not define the final local KAG subtree.

The future role of `aoa-kag` is:

- protocol root for local KAG subtree contracts;
- federation registry for repo-local KAG organs;
- validator and composer for derived cross-repo graph projections;
- owner of framework-neutral KAG schemas, manifest rules, and compact read
  models;
- handoff point to later `aoa-kag-mcp` and `aoa-kag-skills` layers.

`aoa-kag` remains weaker than source repositories for authored meaning and does
not become the physical warehouse for every graph, embedding, vector index, or
runtime cache.

## Options Considered

- Keep widening the current `kag_export.min.json` pilot until it becomes the
  de facto local KAG contract.
- Start adding `/kag` directories to sibling repositories now and retrofit the
  protocol later.
- Record a preflight boundary now, keep current generated surfaces stable, and
  defer the local-subtree contract until the `aoa-kag` core refactor.

## Rationale

The chosen route keeps the current repository honest. `aoa-kag` already has a
strong stop-rule for new `AOA-K-*` growth and a source-first boundary. Turning a
tiny export capsule into the final repo-local KAG contract by inertia would
weaken both rules.

The future local-subtree shape needs its own protocol vocabulary: local graph
manifest, source refs, node and edge identity, generated read models, optional
sidecars, freshness, storage posture, and cross-repo composition. That work
belongs in the `aoa-kag` refactor first, then in `aoa-kag-mcp`, then in
`aoa-kag-skills`, and only after that in sibling repos.

## Consequences

Good consequences:

- current federation exports stay valid without pretending to be final `/kag`;
- future `/kag` rollout gets a named stop-line before sibling sprawl begins;
- `aoa-kag-mcp` and `aoa-kag-skills` remain downstream of the core protocol;
- future intent has one durable route instead of being scattered across current
  route docs.

Tradeoffs:

- the OS-wide graph forest waits on a real `aoa-kag` refactor;
- some current donor vocabulary will likely be renamed or nested later;
- sibling repositories cannot yet use `/kag` as a reviewed local knowledge
  organ.

## Source Surfaces

- `AGENTS.md`
- `DESIGN.md`
- `DESIGN.AGENTS.md`
- `mechanics/README.md`
- `mechanics/AGENTS.md`
- `mechanics/topology.json`
- `README.md`
- `ROADMAP.md`
- `CHARTER.md`
- `docs/KAG_MODEL.md`
- `mechanics/boundary-bridge/parts/source-owned-export/docs/federation-kag-readiness.md`
- `mechanics/boundary-bridge/parts/federation-spine/docs/federation-spine.md`
- `mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-maturity-governance.md`
- `mechanics/boundary-bridge/parts/source-owned-export/docs/source-owned-export-dependencies.md`

## Validation

Use `docs/validation/COMMAND_AUTHORITY.md` and the nearest `AGENTS.md` for executable validation commands.
