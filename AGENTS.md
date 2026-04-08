# AGENTS.md

Guidance for coding agents and humans contributing to `aoa-kag`.

## Purpose

`aoa-kag` is the derived knowledge substrate layer of AoA.
It stores provenance-aware, source-first derived structures and graph-ready
projections that can support retrieval and downstream knowledge consumers
without replacing authored meaning in source repositories.

This repository owns the derived substrate.
It does not become a replacement for the texts, techniques, skills, memories,
or proofs it lifts from.

## Owns

This repository is the source of truth for:

- derived substrate structure
- provenance-aware lifted surfaces
- graph-ready or retrieval-oriented projections at the substrate layer
- normalized node, edge, chunk, section, and route packs when explicitly defined here
- KAG-layer metadata and generated outputs
- doctrine about what a derived substrate is and is not
- reasoning-handoff and regrounding adjuncts when those seams are explicitly defined in repo-owned docs

## Does not own

Do not treat this repository as the source of truth for:

- authored technique, skill, or eval meaning
- explicit memory-object meaning in `aoa-memo`
- routing and dispatch logic in `aoa-routing`
- role contracts, progression policy, or self-agent checkpoint doctrine in `aoa-agents`
- scenario composition in `aoa-playbooks`
- source-authored Tree of Sophia meaning
- framework-specific application code that belongs elsewhere

## Core rules

Source repositories own authored meaning.
`aoa-kag` owns derived substrate structure built from those sources.

If a task requires changing canonical authored meaning, go to the source
repository instead of rewriting it here.

Graph-ready does not mean source-replacing.
Reasoning-handoff and regrounding adjuncts stay bounded.
They do not authorize open-ended world-model sprawl.

## Read this first

Before making changes, read in this order:

1. `README.md`
2. `CHARTER.md`
3. `docs/KAG_MODEL.md`
4. `docs/BOUNDARIES.md`
5. `docs/SOURCE_POLICY.md`
6. the target source file you plan to edit
7. any affected generated registry, pack, or capsule surfaces

Then branch by task:

- source-owned dependencies, bridge posture, or reasoning handoff:
  `docs/SOURCE_OWNED_EXPORT_DEPENDENCIES.md`,
  `docs/BRIDGE_CONTRACTS.md`, and
  `docs/REASONING_HANDOFF.md`
- recurrence, regrounding, or projection quarantine:
  `docs/RECURRENCE_REGROUNDING.md`,
  `docs/KAG_STRESS_REGROUNDING.md`, and
  `docs/KAG_PROJECTION_QUARANTINE.md`
- consumer or federation posture:
  `docs/CONSUMER_GUIDE.md`,
  `docs/COUNTERPART_CONSUMER_CONTRACT.md`,
  `docs/FEDERATION_KAG_READINESS.md`, and
  `docs/FEDERATION_SPINE.md`
- technique or ToS lift packs:
  `docs/TECHNIQUE_LIFT_PACK.md` and the relevant `docs/TOS_*` pack docs

If you are editing inside `manifests/`, `generated/`, `schemas/`, or
`examples/`, also follow the nested `AGENTS.md` in that directory.

## Primary objects

The most important objects in this repository are:

- KAG registry and pack definitions
- provenance mapping docs and bridge contracts
- generated substrate outputs
- manifests, schemas, and examples that make those outputs reviewable
- docs that define lift posture, source-first discipline, consumer boundaries, and regrounding posture

## Hard NO

Do not:

- rewrite authored source meaning here
- treat KAG projections as canonical text
- collapse provenance into vague “derived from repo” gestures
- turn this repo into routing, memory, or eval doctrine
- introduce framework-specific lock-in unless the repository canon explicitly chooses it
- let “graph-ready” become “source-replacing”
- let regrounding or projection-health adjuncts become hidden runtime truth

## Contribution doctrine

Use this flow: `PLAN -> DIFF -> VERIFY -> REPORT`

### PLAN

State:

- what KAG surface is changing
- what provenance or lift risk exists
- what source repositories are affected
- whether the change is semantic or metadata-only
- whether bridge, consumer, handoff, or regrounding posture is changing

### DIFF

Keep the change focused.
Do not mix unrelated cleanup into a KAG-layer change unless it is necessary for
repository integrity.

### VERIFY

Run the validation commands documented in `README.md`.

For a read-only current-state pass, use:

```bash
python scripts/validate_kag.py
python scripts/validate_nested_agents.py
python -m unittest discover -s tests -p 'test_*.py'
```

If registries, packs, or other generated KAG surfaces changed, regenerate them
and rerun the read-only pass above.

For release-prep parity, use:

```bash
python scripts/release_check.py
git status -sb
```

Confirm that:

- source-first ownership is still preserved
- provenance remains visible and reviewable
- derived objects still match bounded substrate intent
- bridge, handoff, and regrounding surfaces remain adjunct-only
- the change does not overclaim source authority
- generated outputs remain aligned if metadata surfaces changed

### REPORT

Summarize:

- what derived surfaces changed
- whether semantics changed or only metadata changed
- whether provenance, projection posture, bridge posture, or regrounding posture changed
- what validation was run
- any neighboring repo follow-up likely needed

## Validation

Do not claim checks you did not run.
