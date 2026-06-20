# Common Mechanics Home Map

## Index Metadata

- Decision ID: AOA-KAG-D-0006
- Original date: 2026-06-19
- Surface classes: mechanics/topology, docs/decisions, validation guard
- KAG surfaces: mechanics common homes, KAG-only pressure, part-local stop-line
- Source lanes: aoa-kag, Agents-of-Abyss, sibling mechanics
- Guard families: source-owned authority, mechanics topology, part-local stop-line, local KAG protocol boundary
- Posture: accepted

## Context

`aoa-kag` already had a mechanics root skeleton, validation lanes, and a
federated-local KAG preflight decision. The next refactor pressure is not just
to create a `mechanics/` directory, but to align KAG with the common mechanics
homes that start in `Agents-of-Abyss` and run through the OS Abyss repo family.

Sibling repositories show the same pattern: top-level mechanics packages use
common AoA vocabulary, while each repository adapts the local authority through
package cards, `PARTS.md`, `PROVENANCE.md`, and owner stop-lines. Part
directories appear only when a sub-mechanic owns a real payload slice, contract,
validation route, and nearest artifact home.

## Decision

`aoa-kag` will carry KAG-local route homes for the common center mechanics:
`agon`, `antifragility`, `audit`, `boundary-bridge`, `checkpoint`,
`distillation`, `experience`, `growth-cycle`, `method-growth`, `questbook`,
`recurrence`, `release-support`, and `rpg`.

These packages are local route cards. They do not import center doctrine, move
artifacts by symmetry, or claim proof, memory, routing, runtime, skill,
technique, playbook, role, or Tree of Sophia authority.

No `mechanics/<package>/parts/<part>/` directories are active yet. Package
`PARTS.md` files may name candidate part pressure, but a real part appears only
when it has a stable payload class, owner split, stop-lines, local contract,
and validation.

No KAG-only mechanics package is active yet. The local `/kag` subtree
source-home and protocol pressure routes through AOA-KAG-D-0004 and the `kag/`
source-home preflight when that home exists, but it remains outside mechanics
packages until indexes, graph
nodes, edges, local projections, freshness, and composition rules have schemas,
examples, payload contracts, and validation.

## Options Considered

- Keep only the root mechanics skeleton: smallest diff, but future mechanics
  work would continue without the common AoA route homes that sibling repos
  already use.
- Copy center packages and part directories mechanically: visually symmetric,
  but it would create empty part homes and imply authority that KAG does not
  own.
- Add common package route homes now, keep parts deferred, and record KAG-only
  pressure as inactive protocol work: larger than docs-only, but gives agents a
  real map without artifact churn.

## Rationale

The chosen route matches `aoa-kag` as a provenance-aware derived substrate.
Common mechanics names help agents route pressure consistently across OS
Abyss, but KAG must still speak from its own authority: derived projections,
source refs, generated parity, bridge posture, maturity, regrounding, and
consumer return.

`parts` need stricter discipline than package names. A part is a functioning
sub-mechanic, not a placeholder. Creating part directories before contracts and
validators would make future artifact moves look safer than they are.

The future `/kag` protocol is real KAG-only pressure, but not an active
mechanic yet. Treating it as deferred keeps the long graph/RAG direction
visible without spreading unreviewed local subtree templates across sibling
repositories.

## Consequences

Good consequences:

- agents can enter KAG mechanics through the same common homes used across the
  repo family;
- KAG-local cards name what this repository owns without importing stronger
  owner authority;
- candidate part pressure is visible without creating empty part directories;
- the local `/kag` future remains discoverable through a decision stop-line.

Tradeoffs:

- mechanics now has more files, but they are route cards rather than payload
  migrations;
- package docs must stay short and local, or they will become duplicate
  doctrine;
- future artifact moves still need separate part-local contracts and
  validators.

## Source Surfaces

- `mechanics/README.md`
- `mechanics/AGENTS.md`
- `mechanics/topology.json`
- `scripts/validate_mechanics_skeleton.py`
- `tests/test_mechanics_skeleton.py`
- `DESIGN.md`
- `DESIGN.AGENTS.md`
- `docs/decisions/AOA-KAG-D-0004-federated-local-kag-preflight.md`
- `kag/README.md`
- `kag/source_home.manifest.json`
- `kag/LOCAL_SUBTREE_PROTOCOL.md`
- `docs/decisions/AOA-KAG-D-0005-validation-command-authority-preflight.md`
- `Agents-of-Abyss/mechanics/README.md`
- `Agents-of-Abyss/mechanics/AGENTS.md`

## Validation

Run:

```bash
python scripts/validate_mechanics_skeleton.py
python -m unittest tests.test_mechanics_skeleton
python scripts/generate_decision_indexes.py
python scripts/generate_decision_indexes.py --check
python scripts/validate_decision_records.py
```

For release-facing closeout, also run:

```bash
python scripts/release_check.py
```
