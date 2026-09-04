# AGENTS.md

Root route card for `aoa-kag`.

## Applies to

This card applies to the whole repository unless a nearer `AGENTS.md` narrows
the lane.

## Role

This card keeps work inside the provenance-aware derived knowledge substrate
lane. It owns repository identity, broad owner boundaries, task-conditional
route choice, validation posture, and closeout.

It does not replace `CHARTER.md`, `DESIGN.md`, `DESIGN.AGENTS.md`, KAG model and
source-policy docs, local cards, manifests, schemas, builders, validators,
tests, decisions, or generated-source owners.

## Read before editing

1. Start with this card, then read the nearest nested `AGENTS.md` for every
   touched path.
2. Read only the source surface that owns the touched claim. `README.md` is for
   public or human orientation when the named task needs it, not an inherited
   prerequisite.
3. Classify the work as authored source, derived projection, generated output,
   protocol, runtime evidence, legacy material, or sibling-owned meaning.
4. Use `ROADMAP.md` only when repository-wide direction or a future trigger may
   change.

## Owner-specific routes

- repository authority or source ownership -> `CHARTER.md`,
  `docs/BOUNDARIES.md`, and `docs/SOURCE_POLICY.md`
- KAG system form, source/derived authority, federation, or local `/kag`
  protocol posture -> `DESIGN.md`
- agent-card form, inheritance, validation posture, or closeout shape ->
  `DESIGN.AGENTS.md`
- repeatable KAG operation topology -> `mechanics/AGENTS.md`
- local `/kag` source-home or protocol work -> `kag/AGENTS.md`,
  `kag/source_home.manifest.json`, and `kag/LOCAL_SUBTREE_PROTOCOL.md`
- repository-owned callable KAG procedure -> `skills/AGENTS.md` and
  `skills/port.manifest.json`

Follow the local owner from there; do not reproduce its inventory in this
root card.

## Boundaries

`aoa-kag` owns provenance-aware derived substrate structure, lifted and
normalized packs, manifests, schemas, generated read models, source-first graph
and retrieval projections, and explicitly defined bridge, handoff, federation,
quarantine, regrounding, and local `/kag` protocol seams.

It does not own authored source meaning, proof, durable memory, routing, roles,
playbooks, reusable skills or techniques, shared statistical grammar, runtime,
Tree of Sophia meaning, or live graph, vector, embedding, index, and cache
state. Route those claims to their canonical owners.

Generated outputs, compact packs, exported capsules, receipts, and
retrieval-ready wording remain subordinate to authored sources and provenance.

## Validation

Use the nearest card to select the focused owner lane. Exact procedures and
arguments live on demand in root `VALIDATION.md`, the nearest local
`VALIDATION.md`, and machine authority `config/validation_lanes.json`. Route
cards keep lane meaning and stop-lines, not command sequences.

Regenerate derived outputs from their source builder. Run broader gates when a
change is root-facing, structural, generated, cross-owner, or release-facing.
Report only checks actually run.

## Closeout

Report changed KAG surfaces; semantic versus metadata impact; provenance,
bridge, handoff, federation, quarantine, regrounding, proof-pressure, and local
`/kag` impact; generated refreshes; checks run and skipped; remaining risk;
decision-review result; and the next owner route.

## Repository-wide stop-lines

- Authored sources own meaning; derived and generated surfaces do not replace
  them.
- Do not hand-edit a generated surface as source truth.
- Do not claim proof, memory, routing, role, playbook, skill, technique, stats,
  runtime, or sibling authority from this repository.
- Do not treat future local `/kag` pressure as an active sibling protocol before
  its schema, examples, validation, and owner handoff exist.
- Keep self-agency, recurrence, quest, progression, checkpoint, graph,
  retrieval, and growth claims bounded, reviewable, evidence-linked, and
  reversible.

## Post-change route review

Update only the owner surface whose contract moved:

- KAG system form or source/derived authority -> `DESIGN.md`
- agent-facing form or inheritance -> `DESIGN.AGENTS.md`
- repository authority or source policy -> `CHARTER.md`,
  `docs/BOUNDARIES.md`, or `docs/SOURCE_POLICY.md`
- package, manifest, schema, builder, validator, generated output, or protocol
  meaning -> its nearest local owner
- durable rationale -> `docs/decisions/`
- repository-wide direction -> `ROADMAP.md`
- release-visible behavior -> `CHANGELOG.md`

## GitHub landing workflow

When landing is authorized, use `docs/RELEASING.md` for branch, PR, CI, merge,
and post-landing procedure. If required status or merge authority cannot be
observed, stop and report the exact blocker rather than inferring success.

## Historical reference

`docs/AGENTS_ROOT_REFERENCE.md` preserves former detailed root guidance for
audit only. It is not current route law; lift any surviving rule into this card
or the nearest owner surface before relying on it.
