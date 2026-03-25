# AGENTS.md

Guidance for coding agents and humans contributing to `aoa-kag`.

## Purpose

`aoa-kag` is the derived knowledge substrate layer of AoA.

It stores provenance-aware, source-first, derived structures and graph-ready projections that can support retrieval and downstream knowledge consumers without replacing authored meaning in source repositories.

This repository is for derived substrate meaning, not for authored source meaning.

## Owns

This repository is the source of truth for:

- derived substrate structure
- provenance-aware lifted surfaces
- graph-ready or retrieval-oriented projections at the substrate layer
- KAG-layer metadata and generated outputs
- doctrine about what a derived substrate is and is not

## Does not own

Do not treat this repository as the source of truth for:

- authored technique meaning in `aoa-techniques`
- authored skill meaning in `aoa-skills`
- authored eval meaning in `aoa-evals`
- explicit memory-object meaning in `aoa-memo`
- role contracts in `aoa-agents`
- scenario composition in `aoa-playbooks`
- routing and dispatch logic in `aoa-routing`

This repository derives from source-first repos.
It does not become a replacement for them.

## Core rule

Source repositories own authored meaning.
`aoa-kag` owns derived substrate structure built from those sources.

If a task requires changing canonical authored meaning, go to the source repository instead of rewriting it here.

## Read this first

Before making changes, read in this order:

1. `README.md`
2. any KAG/schema/lift docs referenced by the README
3. the target source file you plan to edit
4. any generated KAG registry, projection, or capsule surfaces affected by the task
5. the relevant source repo docs if the task touches lift rules or provenance assumptions

When working inside `manifests/`, `generated/`, `schemas/`, or `examples/`, also read the nested `AGENTS.md` in that directory.
Local guidance sharpens the handling of that surface, but it does not override this file's source-first doctrine.

## Primary objects

The most important objects in this repository are:

- KAG registry definitions
- derived object definitions
- provenance mapping docs
- projection docs
- generated substrate outputs
- docs that define lift posture and source-first discipline

## Allowed changes

Safe, normal contributions include:

- refining derived object structure
- tightening provenance wording
- improving projection or lift clarity
- fixing metadata drift between source files and generated outputs
- improving retrieval-oriented substrate surfaces
- adding a new bounded derived structure when it clearly belongs to the KAG layer

## Changes requiring extra care

Use extra caution when:

- changing derived-object classes
- changing generated registry or projection shape
- changing provenance semantics
- changing lift rules that downstream tooling may depend on
- adding graph-facing semantics that risk overclaiming source meaning
- changing wording in ways that make KAG appear more authoritative than the source repos

## Hard NO

Do not:

- rewrite authored source meaning here
- treat KAG projections as the canonical text
- collapse provenance into vague “derived from repo” gestures
- turn this repo into routing, memory, or eval doctrine
- store secrets, private infra details, or hidden internal corpora
- introduce framework-specific lock-in unless the repository canon explicitly chooses it

Do not let “graph-ready” become “source-replacing.”

## KAG doctrine

A good KAG-layer change should make it easier to answer:

- what was lifted
- from which source-owned surface
- with what provenance trace
- into what derived structure
- for what retrieval or downstream use
- without implying that the derived structure replaced the source meaning

A bad KAG change usually makes the derived structure too magical, too authoritative, too framework-bound, or too detached from provenance.

## Public hygiene

Assume everything here is public, inspectable, and challengeable.

Write for portability:

- keep provenance explicit
- keep source-first wording explicit
- keep framework assumptions visible
- sanitize examples
- prefer bounded derived structures over sweeping graph claims
- avoid private or hidden lift dependencies

## Default editing posture

Prefer the smallest reviewable change.

Preserve canonical wording unless the task explicitly requires semantic change.
If semantic change is made, report it explicitly.

## Contribution doctrine

Use this flow:

`PLAN -> DIFF -> VERIFY -> REPORT`

### PLAN

State:

- what KAG surface is changing
- what provenance or lift risk exists
- what source repos are affected
- whether the change is semantic or metadata-only

### DIFF

Keep the change focused.

Do not mix unrelated cleanup into a KAG-layer change unless it is necessary for repository integrity.

### VERIFY

Confirm that:

- source-first ownership is still preserved
- provenance remains visible and reviewable
- derived objects still match bounded substrate intent
- the change does not overclaim graph semantics or source authority
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

If registries, projections, capsules, or other generated KAG surfaces changed, regenerate and validate them before finishing.
The canonical validator also checks the local guidance surfaces in `manifests/`, `generated/`, `schemas/`, and `examples/`.

Do not claim checks you did not run.

## Cross-repo neighbors

Use these neighboring repositories when the task crosses boundaries:

- `aoa-techniques` for source technique meaning
- `aoa-skills` for source execution meaning
- `aoa-evals` for source proof meaning
- `aoa-memo` for explicit memory objects
- `aoa-routing` for smallest-next-object navigation
- `Agents-of-Abyss` for ecosystem-level map and boundary doctrine

## Output expectations

When reporting back after a change, include:

- which derived surfaces changed
- whether semantics changed or only metadata changed
- whether provenance, lift posture, or projection shape changed
- whether generated outputs changed
- what validation was run
- any neighboring repo follow-up likely needed

## Default editing posture

Prefer the smallest reviewable change.
Preserve canonical wording unless the task explicitly requires semantic change.
If semantic change is made, report it explicitly.
