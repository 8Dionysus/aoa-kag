# KAG Model

This document defines the conceptual model of the AoA KAG layer.

## Why a KAG layer exists

AoA needs more than reusable practice, bounded execution, bounded proof, memory, routing, explicit agents, and scenario playbooks.
It also needs a derived knowledge substrate that can support graph-shaped and retrieval-shaped work across authoritative sources.

The KAG layer exists to make lifted knowledge surfaces explicit rather than hiding them inside source repos or binding them too early to one framework.

## What counts as a KAG surface here

Within `aoa-kag`, a KAG surface should mean a derived knowledge-ready structure described through surfaces such as:
- primary source class
- full source inputs when more than one repo contributes
- derived kind
- provenance mode
- normalization scope
- framework readiness
- source repo linkage

## KAG classes

The first useful distinction is between KAG surface archetypes such as:

### Repository self-knowledge kernel

Every OS Abyss repository publishes a canonical repo-self family from its own
`/kag`. The family distinguishes tracked artifacts, internal anchors, logical
entities, repository events, quality-gated assertions, and evidence-bearing
relations. Repository
namespace, Git lineage, source digest, ABI/sign posture, provenance, temporal
state, trust, freshness, access, and owner-return routes preserve each organ's
identity through federation.
Federation resolves source links through current and historical Git locators,
while external web, owner, and GitHub-object references remain typed evidence.

Native domain indexes remain product surfaces of their owners and appear in
repo-self KAG through a domain-index catalog.

### Metadata spine projection

A bounded projection of source metadata that supports lookup, identity, and routing without replacing authored meaning.

### Section or chunk map

A derived surface that makes section-level or chunk-level retrieval targets explicit while keeping the authoritative source intact.

### Relation view

A bounded edge-oriented surface that preserves direct adjacency and provenance without pretending to be a full graph engine.

### Provenance view

A derived surface that makes source linkage and origin handles visible for retrieval and review.

### Node or edge projection

A graph-friendly normalization of source-derived units into node-like or edge-like forms without claiming that the projected form is the new source of truth.

The current bounded example is `AOA-K-0010`, a direct canonical-tree-derived
route-local Zarathustra bundle that projects reviewed ToS route nodes and the
canonical ToS relation pack without widening source ownership or activating raw
intake.

### Retrieval surface

A bounded retrieval-facing surface that returns handles back to stronger source
or owner refs without taking ranking, routing, or graph-normalization
ownership.

Runtime materializers consume a deterministic retrieval bundle. Its manifest
binds canonical input digests to line-addressable owners, nodes, relations,
external references, and retrieval documents with stable vector point
identities, without placing large runtime stores in source Git.

The current bounded examples are `AOA-K-0007`, the tiny-entry retrieval-axis
pilot, and `AOA-K-0011`, the standalone route-family handles surface derived
from `AOA-K-0010`.

### Counterpart edge view

A bounded edge-oriented projection that links a ToS concept ref to an AoA operational ref through a named mode such as `analogy`, `support`, `tension`, or `calibration`.

This kind of view remains:

- derived
- optional
- source-linked
- explicitly non-identity

## Owner routing

Authored meaning returns to its source repository. Proof routes to `aoa-evals`,
routing policy to `aoa-routing`, durable memory meaning to `aoa-memo`, session
history to `aoa-session-memory`, and runtime materialization to `abyss-stack`.
KAG records preserve the handles needed for each return.

## KAG posture

A good KAG surface should make it easier to answer:
- what source did this primarily come from?
- what supporting sources also shaped it?
- what was lifted or normalized?
- what provenance remains visible?
- what graph or retrieval readiness is real right now?
- what is still explicitly deferred?

## Bridge contracts

The first bridge rule is:

**KAG may return bounded retrieval context, but it does not replace authored source truth**

Bridge-ready retrieval surfaces should preserve source refs and, where relevant:

- lineage refs
- conflict refs
- practice refs
- bounded axis summary

See [BRIDGE_CONTRACTS](BRIDGE_CONTRACTS.md) for the compact contract.

The counterpart rule is:

**KAG may project counterpart edges, but the projection does not prove conceptual and operational identity**

See
[counterpart-edge-contracts](../mechanics/boundary-bridge/parts/counterpart-edge/docs/counterpart-edge-contracts.md)
for the compact contract.

## Relationship to neighboring layers

- `aoa-techniques` stores reusable practice
- `aoa-skills` stores bounded execution
- `aoa-evals` stores bounded proof
- `aoa-routing` stores navigation and dispatch
- `aoa-memo` stores memory and recall surfaces
- `aoa-agents` stores reusable role-bearing actors
- `aoa-playbooks` stores reusable scenario compositions
- `Tree-of-Sophia` stores authored knowledge-architecture content
- `aoa-kag` stores derived knowledge substrate surfaces

## Compact principle

The KAG layer should make knowledge lift explicit without pretending the ecosystem is already a finished graph civilization.
