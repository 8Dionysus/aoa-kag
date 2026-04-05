# AGENTS.md

Guidance for coding agents and humans contributing to `aoa-kag`.

## Purpose

`aoa-kag` is the derived knowledge substrate layer of AoA. It stores provenance-aware, source-first derived structures and graph-ready projections that can support retrieval and downstream knowledge consumers without replacing authored meaning in source repositories.

## Owns

This repository is the source of truth for:

- derived substrate structure
- provenance-aware lifted surfaces
- graph-ready or retrieval-oriented projections at the substrate layer
- KAG-layer metadata and generated outputs
- doctrine about what a derived substrate is and is not

## Does not own

Do not treat this repository as the source of truth for:

- authored technique, skill, or eval meaning
- explicit memory-object meaning in `aoa-memo`
- routing and dispatch logic in `aoa-routing`
- role contracts in `aoa-agents`
- scenario composition in `aoa-playbooks`
- source-authored Tree of Sophia meaning

This repository derives from source-first repos. It does not become a replacement for them.

## Core rule

Source repositories own authored meaning. `aoa-kag` owns derived substrate structure built from those sources.

If a task requires changing canonical authored meaning, go to the source repository instead of rewriting it here.

## Read this first

Before making changes, read in this order:

1. `README.md`
2. the relevant model, bridge, or pack docs referenced there
3. the target source file you plan to edit
4. any affected generated registry, pack, or capsule surfaces
5. the relevant source repo docs if the task touches lift rules or provenance assumptions

If you are editing inside `manifests/`, `generated/`, `schemas/`, or `examples/`, also follow the nested `AGENTS.md` in that directory.

## Primary objects

The most important objects in this repository are:

- KAG registry and pack definitions
- provenance mapping docs and bridge contracts
- generated substrate outputs
- manifests, schemas, and examples that make those outputs reviewable
- docs that define lift posture, source-first discipline, and consumer boundaries

## Hard NO

Do not:

- rewrite authored source meaning here
- treat KAG projections as canonical text
- collapse provenance into vague “derived from repo” gestures
- turn this repo into routing, memory, or eval doctrine
- introduce framework-specific lock-in unless the repository canon explicitly chooses it
- let “graph-ready” become “source-replacing”

## Contribution doctrine

Use this flow: `PLAN -> DIFF -> VERIFY -> REPORT`

### PLAN

State:

- what KAG surface is changing
- what provenance or lift risk exists
- what source repositories are affected
- whether the change is semantic or metadata-only

### DIFF

Keep the change focused. Do not mix unrelated cleanup into a KAG-layer change unless it is necessary for repository integrity.

### VERIFY

Confirm that:

- source-first ownership is still preserved
- provenance remains visible and reviewable
- derived objects still match bounded substrate intent
- the change does not overclaim source authority
- generated outputs remain aligned if metadata surfaces changed

### REPORT

Summarize:

- what derived surfaces changed
- whether semantics changed or only metadata changed
- whether provenance or projection posture changed
- what validation was run
- any neighboring repo follow-up likely needed

## Validation

Run the validation commands documented in `README.md`.

For a read-only current-state pass, use:

```bash
python scripts/validate_kag.py
python scripts/validate_nested_agents.py
python -m unittest discover -s tests -p 'test_*.py'
```

If registries, packs, or other generated KAG surfaces changed, regenerate them and rerun the read-only pass above.

For release-prep parity, use:

```bash
python scripts/release_check.py
git status -sb
```

The validators also check the local guidance surfaces in `manifests/`, `generated/`, `schemas/`, and `examples/`.

Do not claim checks you did not run.
