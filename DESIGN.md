# aoa-kag System Design

## Role

`DESIGN.md` describes the system form of `aoa-kag`.

It is not the README, charter, roadmap, KAG model, source policy, decision
record, generated pack, manifest, schema, validator, or agent instruction card.

It answers one question:

What shape should the AoA derived knowledge substrate preserve as it grows?

## Design Thesis

`aoa-kag` is the provenance-aware derived knowledge substrate for AoA and Tree
of Sophia.

It makes graph-ready and retrieval-ready structures explicit without moving
authored meaning out of source repositories. The repository is strongest when
it keeps the difference between source, lift, projection, generated read model,
proof, memory, routing, and runtime state visible.

The source owner keeps authored meaning.
The manifest names the lift.
The generated surface carries the derived projection.
The schema and validator keep the projection reviewable.
The consumer returns to stronger owner refs when meaning must be changed.

## Design as Appearance

`aoa-kag` should appear as a compact substrate console:

- clear root entrypoints;
- source-first model, boundary, and policy docs;
- source-authored manifests for KAG pack intent;
- generated read models and compact outputs that point back to source inputs;
- schemas and examples that make payload claims inspectable;
- decision records for durable route rationale;
- local route cards near durable editable districts;
- KAG-local eval intake before proof adoption by `aoa-evals`;
- bridge, handoff, maturity, quarantine, and regrounding docs that return
  pressure to stronger owners.

A reader should be able to ask: what source owns this meaning, what was lifted,
what projection was built, what provenance remains visible, what validates it,
and where does a stronger claim return?

## Design as Anatomy

`aoa-kag` is composed of different authority classes.

| Surface | Role |
| --- | --- |
| root surfaces | public entry, charter boundary, system form, agent route law, current direction |
| `docs/` | authored explanation of KAG model, source policy, boundaries, bridge contracts, maturity, quarantine, regrounding, and consumer posture |
| `docs/decisions/` | durable rationale for KAG route, boundary, manifest, generated-pack, validator, and federation choices |
| `kag/` | source-home preflight for future repo-local KAG subtrees, portable record classes, rollout stop-lines, and runtime-state exclusions |
| `mechanics/` | repeatable KAG operation topology and future package routes around substrate work |
| `manifests/` | source-authored control surfaces for what should be lifted and what outputs should exist |
| `generated/` | derived KAG read models and compact payloads built from source surfaces |
| `schemas/` | machine-checkable contracts for KAG payloads, receipts, manifests, and examples |
| `examples/` | public-safe examples of payload shape, not private evidence or source truth |
| `scripts/` | deterministic builders, validators, decision-index helpers, and substrate checks |
| `tests/` | regression proof for contracts, parity, guardrails, and current routes |
| `evals/` | KAG-local eval pressure port before central proof acceptance |
| `.agents/`, `Spark/`, `.github/`, `config/` | companion, platform, and configuration lanes that support KAG work without becoming substrate truth |

Each class may support another. No class should silently steal another class's
authority.

## Design as Operation

A healthy KAG operation follows a bounded route:

1. Identify the stronger source owner for authored meaning.
2. Identify the KAG-owned surface that may derive from that source.
3. Preserve source refs, provenance, posture, and non-identity boundaries.
4. Change the manifest, docs, schema, builder, or test that owns the local
   contract.
5. Regenerate derived outputs when source-backed generated surfaces move.
6. Validate the narrow local contract first, then broader gates when the change
   is root-facing, generated, structural, release-facing, or cross-owner.
7. Return stronger meaning, proof, memory, routing, playbook, role, runtime, or
   Tree of Sophia claims to their owners.

The derived substrate is useful only while it remains inspectable and
returnable.

## Design as Aim

The long aim is a KAG layer that can support RAG, graph RAG, agentic RAG,
KAG, DAG, and later AoA knowledge routes without becoming a hidden warehouse or
framework lock-in.

The repository should support:

- source-linked graph and retrieval projections;
- stable KAG surface identifiers;
- manifest-driven generation;
- schema-checked payloads and examples;
- bounded bridge and handoff routes;
- maturity and owner-wait stop-rules;
- a repo-local `/kag` subtree protocol rooted in the `kag/` source-home
  preflight, without
  template-copying it into sibling repositories before schemas, examples, and
  validation exist;
- downstream `aoa-kag-mcp` and `aoa-kag-skills` layers that remain downstream
  of core substrate contracts.

The substrate grows well when every new surface makes source ownership,
provenance, validation, consumer return, or federation posture clearer than
before.

## Design Principles

### 1. Source before substrate

KAG surfaces may lift, normalize, project, and return context. They must not
replace authored source meaning.

### 2. Manifest before generated

Generated outputs should be reproducible from source-authored controls. When a
generated surface is wrong, fix the owner input or builder, then regenerate.

### 3. Provenance before graph theater

Graph-ready language is honest only when source refs, lift mode, projection
scope, and non-identity boundaries remain visible.

### 4. Retrieval returns to owners

Retrieval surfaces should hand consumers back to stronger source refs instead
of becoming ranking, routing, proof, or memory authority by convenience.

### 5. Framework-neutral before adapter lock-in

HippoRAG, LlamaIndex, MCP, skills, runtimes, and other consumers may sit
downstream. They should not define the core KAG ontology too early.

### 6. Proof, memory, routing, roles, and scenarios stay separate

KAG may support these layers. It does not own their doctrine, verdicts,
objects, dispatch, identities, or live state.

### 7. Federation before warehouse

The `kag/` source-home preflight should let future repositories own their local
indexes, graph nodes, graph edges, and projections through a shared protocol.
`aoa-kag` should define and compose the protocol, not absorb every mutable
graph artifact.

### 8. Agent guidance is route law

Agent-facing cards should tell an agent where it is, what owns the claim, what
to read, how to verify, and where to hand off. They should not become KAG
source truth by repetition.

### 9. Validation before confidence

Every meaningful change should have a local check, generated parity when
derived outputs move, and a closeout that names skipped checks and remaining
risk.

## Good Design Feels Like

- a public reader can find the KAG model and boundary;
- an agent can find the nearest route card;
- a generated payload can find its manifest or builder;
- a manifest can name source refs and output refs;
- a schema can constrain reviewable shape;
- a consumer can return to stronger owner refs;
- a future contributor can find why a route exists.

## Bad Design Smells Like

- root inflation;
- generated files cited as source truth;
- vague repository-level provenance;
- graph claims without bounded source refs;
- retrieval packs becoming routing policy;
- KAG surfaces becoming proof, memory, role, playbook, or runtime doctrine;
- framework adapters defining substrate ontology;
- sibling `/kag` directory plans scattered across current docs instead of kept
  behind the explicit `kag/` protocol stop-line.

## Relationship to Other Root Surfaces

[`README.md`](README.md) introduces the repository.
[`CHARTER.md`](CHARTER.md) names the repository authority boundary.
[`AGENTS.md`](AGENTS.md) routes agent work.
[`DESIGN.AGENTS.md`](DESIGN.AGENTS.md) holds the design form of the
agent-facing route mesh.
[`ROADMAP.md`](ROADMAP.md) names current direction.
[`kag/`](kag/README.md) holds the local-subtree source-home and protocol
preflight.
[`docs/KAG_MODEL.md`](docs/KAG_MODEL.md) defines the conceptual KAG model.
[`docs/BOUNDARIES.md`](docs/BOUNDARIES.md) names owner boundaries.
[`docs/SOURCE_POLICY.md`](docs/SOURCE_POLICY.md) defines source-first posture.
[`mechanics/README.md`](mechanics/README.md) routes repeatable KAG operation
topology.
[`docs/decisions/`](docs/decisions/README.md) preserves durable route
rationale.

`DESIGN.md` holds the system form of the KAG layer.

## Use by Agents

Agents should consult this file when a change alters:

- repository shape;
- root surfaces;
- source versus derived authority;
- mechanics topology or package posture;
- local `/kag` protocol posture or sibling local-subtree rollout stop-lines;
- manifest and generated-surface posture;
- KAG owner boundaries;
- federation or local `/kag` protocol posture;
- bridge, handoff, maturity, quarantine, or regrounding routes;
- downstream adapter boundaries;
- agent-facing layer design.

This file does not override local owner truth. It tells agents what kind of
shape `aoa-kag` is preserving.
