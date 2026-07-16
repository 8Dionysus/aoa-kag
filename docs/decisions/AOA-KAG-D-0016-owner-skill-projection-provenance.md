# Owner Skill Projection Provenance

## Index Metadata

- Decision ID: AOA-KAG-D-0016
- Original date: 2026-07-15
- Surface classes: kag/source-home, schema contract, generated projection, validation guard, owner return
- KAG surfaces: repo-local source surface index, artifact index, relation index, skill projection provenance
- Source lanes: owner-local skill homes, aoa-skills home-port contract, OS Abyss repo-local kag homes
- Guard families: source-owned authority, generated projection, byte parity, provenance material, owner return, relation evidence
- Posture: accepted

## Context

The repository home-port contract lets an OS Abyss owner keep an admitted skill
under `skills/<name>/` and expose an exact repo-scoped Codex copy under
`.agents/skills/<name>/`. A manual `aoa-stats` migration showed that the common
repo-local KAG generator classified both files as `authored_source`, pointed
the projection's provenance and owner return back to itself, and emitted no
typed relation to the canonical owner source.

That output was structurally valid but false about authority. It would let a
generated host copy compete with its canonical procedure in retrieval and
federation.

## Decision

When a tracked `skills/port.manifest.json` uses
`aoa_skill_home_port_v1`, the repo-local generator interprets only the exact
declared `generated-copy` projection. It requires every projected file to have
the declared canonical source with identical Git blob and executable mode.

The physical copy remains indexed, but its `surface_state` is
`generated_projection`. Its primary provenance ref and owner-return route point
to the canonical owner file, the port manifest is recorded as material, the
common `aoa-skills` builder and validator are named, and the repository
relation family carries a deterministic `derives_from` edge from copy to
source. Divergence blocks generation rather than falling back to
`authored_source`.

Paths under `.agents/skills/` without this explicit owner contract are not
guessed to be projections. Their disposition must be established by their
owner migration instead of by path-name inference.

## Options Considered

- Continue classifying every tracked file as authored unless it sits in a
  generic `generated/` directory: preserves old output but makes a known
  projection authoritative.
- Treat every `.agents/skills/` path as generated: removes the false source
  claim but misclassifies legacy or manually authored layouts without owner
  evidence.
- Interpret the admitted home-port manifest and require exact source/copy
  parity: uses the owner's explicit contract, keeps unknown layouts visible,
  and fails closed on declared drift.

## Rationale

KAG should derive authority from an owner contract, not from directory naming.
The manifest supplies applicability, source root, projection root, and bundle
identity; Git blob and mode equality supply deterministic evidence that the
tracked copy is the declared artifact. This is sufficient to preserve both the
physical host surface and the stronger canonical return route without making
KAG the owner of skill meaning.

## Consequences

- Source and projection remain separately addressable without equal authority.
- Retrieval and federation can filter `generated_projection` and follow the
  typed edge back to owner source.
- A drifted declared copy makes generation fail until the owner rebuilds it.
- Existing uncontracted `.agents/skills/` copies remain visible as migration
  debt; this decision does not silently classify or legitimize them.
- Green KAG validation proves the declared provenance relationship, not skill
  usefulness, routing quality, or behavioral equivalence across hosts.

## Source Surfaces

- `DESIGN.md`
- `docs/BOUNDARIES.md`
- `docs/SOURCE_POLICY.md`
- `kag/LOCAL_SUBTREE_PROTOCOL.md`
- `schemas/repo-local-kag-index.schema.json`
- `scripts/generate_repo_local_kag_index.py`
- `scripts/repo_local/indexes.py`
- `tests/test_repo_local_kag_index.py`
- `aoa-skills:schemas/skill-home-port.schema.json`
- `aoa-skills:docs/HOME_SKILL_PORT.md`

## Validation

Manual comparison uses a real staged owner home to inspect the current and
candidate source record, projection record, owner return, and relation. Focused
tests preserve the exact-copy, divergent-copy, and no-manifest negative cases.
Generated parity, the repo-local family validator, source-fast, and release
lanes remain structural evidence only.
