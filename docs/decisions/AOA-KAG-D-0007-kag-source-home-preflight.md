# KAG Source Home Preflight

## Index Metadata

- Decision ID: AOA-KAG-D-0007
- Original date: 2026-06-19
- Surface classes: kag/source-home, root route, validation guard, docs/decisions
- KAG surfaces: source-home preflight, local KAG subtree protocol, federation stop-line
- Source lanes: aoa-kag, Agents-of-Abyss, Tree-of-Sophia, aoa-agents, aoa-playbooks, aoa-routing, aoa-sdk, aoa-skills, aoa-techniques, aoa-memo, aoa-evals
- Guard families: source-owned authority, local KAG protocol boundary, runtime-state exclusion, sibling rollout stop-line, generated output boundary, source-home symmetry
- Posture: accepted

## Context

AOA-KAG-D-0004 named future repo-local `/kag` subtrees as real pressure but
kept sibling rollout deferred until `aoa-kag` itself could define the contract.
The mechanics refactor then made the pressure visible as a KAG-only candidate
without activating a mechanics package.

The relevant sibling pattern is not the literal directory name `kag/`. The
relevant pattern is the source-home organ:

- `Tree-of-Sophia/ToS/` gathers ToS-authored meaning into a branch-owned home;
- `aoa-agents/agents/` keeps role source objects distinct from generated
  readers and runtime behavior;
- `aoa-playbooks/playbooks/` gives authored `PLAYBOOK.md` bundles strict
  canonical paths;
- `aoa-routing/routing/` keeps routing-local behavior separate from shared
  mechanics;
- `aoa-sdk/sdk/` owns SDK posture while implementation remains in `src/`;
- `aoa-skills/skills/`, `aoa-techniques/techniques/`, `aoa-memo/memo/`, and
  `aoa-evals/evals/` show source homes or source districts with local bundle
  truth and stronger-owner boundaries;
- the center organ contract says repositories need readable identity, owner
  boundary, validation, and handoff, not copied tree shapes.

`aoa-kag` therefore needs a KAG source-home preflight, not a copied future
payload tree.

## Decision

`aoa-kag` will use `kag/` as the source-home preflight for KAG-owned
local-subtree protocol law.

The home starts with route law, a human map, a machine-readable source-home
manifest, and a local-subtree protocol:

- `kag/AGENTS.md`
- `kag/README.md`
- `kag/source_home.manifest.json`
- `kag/LOCAL_SUBTREE_PROTOCOL.md`

The only active source families are:

- home route cards;
- the source-home manifest;
- the local-subtree protocol.

`manifest.json`, `nodes/`, `edges/`, `indexes/`, `projections/`, and
`receipts/` remain reserved protocol vocabulary. They are not active payload
directories yet.

Sibling repositories must not receive `/kag` homes from this preflight alone.
Current `generated/`, `manifests/`, `schemas/`, `examples/`, `scripts/`,
`tests/`, and `mechanics/` payloads stay in their current owner homes.

## Options Considered

- Keep `/kag` only as decision-language: smallest change, but future mechanics
  and federation work would still lack a local source-home route.
- Create the full future payload tree now: visually clear, but it would create
  empty record homes before schemas, examples, validators, and pilot owners
  exist.
- Create a thin source-home preflight now and reserve future record classes
  without active payload directories: enough structure for the next refactor,
  without pretending local graph artifacts are ready.

## Rationale

The chosen route fits the actual AoA home-directory pattern. A home is not a
decorative folder and not a symmetry copy. It is a place where a repository can
state what it owns, which source families are active, which generated or
implementation routes are weaker, which stronger owners receive adjacent
pressure, and which validators keep the topology honest.

Repo-local indexes, nodes, edges, and projections are real long-term OS Abyss
needs, but they need source refs, portable record classes, runtime-state
exclusions, freshness posture, and validation before they become files in every
repository.

## Consequences

Good consequences:

- `kag/` now matches the source-home pattern instead of implying that sibling
  home directories are named `kag/`;
- future local KAG organ work has one route entrypoint;
- sibling rollout remains blocked until schemas, examples, validation, and a
  pilot owner exist;
- current generated payloads and manifests do not move by symmetry;
- runtime graph, vector, embedding, and search state stays outside Git-tracked
  source-home truth.

Tradeoffs:

- `kag/` exists before active node or edge payloads exist;
- future work must still add schemas, examples, validators, and pilot owner
  decisions;
- mechanics still has no KAG-only package or part until repeatable payload
  operation pressure becomes concrete.

## Source Surfaces

- `AGENTS.md`
- `DESIGN.md`
- `DESIGN.AGENTS.md`
- `README.md`
- `docs/README.md`
- `mechanics/README.md`
- `mechanics/AGENTS.md`
- `mechanics/topology.json`
- `kag/AGENTS.md`
- `kag/README.md`
- `kag/source_home.manifest.json`
- `kag/LOCAL_SUBTREE_PROTOCOL.md`
- `docs/decisions/AOA-KAG-D-0004-federated-local-kag-preflight.md`
- `docs/decisions/AOA-KAG-D-0006-common-mechanics-home-map.md`

## Validation

Use `docs/validation/COMMAND_AUTHORITY.md` and the nearest `AGENTS.md` for executable validation commands.

Use `docs/validation/COMMAND_AUTHORITY.md` when the route-facing change is
ready for closeout.
