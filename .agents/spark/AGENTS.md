# AGENTS.md

## Applies to

This card applies to `.agents/spark/` and all descendants unless a nearer
`AGENTS.md` narrows the lane.

## Role

`.agents/spark/` is the real-time, interruptible Codex Spark lane for
`aoa-kag`.

The root `AGENTS.md` remains authoritative for repository identity, ownership
boundaries, reading order, and validation commands. This local file only
narrows how GPT-5.3-Codex-Spark should behave when used as the fast-loop lane.

Spark is an agent lane, not a KAG source home, mechanics package, generated
surface, proof surface, runtime graph, or framework adapter. Its core execution
rule is `done-or-handoff`.

Use `.agents/spark/SWARM.md` only when a Spark swarm is explicitly requested.

## Read before editing

Read root `AGENTS.md`, `DESIGN.AGENTS.md`, `.agents/AGENTS.md`, this card, and
the nearest owner surface for the files being changed.

## Default Spark Posture

- Use Spark for short-loop work where a small diff is enough.
- Start with a map: task, files, risks, and validation path.
- Prefer one bounded patch per loop.
- Keep one KAG seam per Spark loop.
- End as `done` or `handoff`; slower-model continuation must be explicit.
- Read the nearest source docs before editing.
- Use the narrowest relevant validation already documented by the repo.
- Report exactly what was and was not checked.
- Escalate instead of widening into a broad architectural rewrite.

## Spark Is Strongest Here For

- derived-structure docs, examples, schema, and test cleanup
- provenance wording refinement
- registry, projection, or capsule alignment
- tight audits of source-first discipline
- small retrieval-oriented surface repairs that do not alter source meaning

## Boundaries

Do not widen Spark here into:

- rewriting authored source meaning here
- making KAG outputs look more authoritative than source repos
- identity collapse with ToS or AoA
- framework-bound expansion that outruns the repo's bounded substrate role
- multi-hour architecture synthesis that belongs in a slower route
- proof, memo, routing, skill, technique, playbook, role, or runtime authority

## Validation

Use the narrowest validator named by the touched owner surface. For Spark-lane
route edits, run:

```bash
python scripts/validate_nested_agents.py
python scripts/validate_semantic_agents.py
```

## Local Done Signal

A Spark task is done here when:

- the derivation chain is clearer
- source-first wording remains explicit
- provenance is still reviewable
- generated outputs are aligned when touched
- the documented validation path ran when relevant

## Local Note

Spark should keep derived surfaces legible and bounded here: explicit lineage,
bounded lift, no graph-platform sprawl.

## Closeout

Always report:

- the restated task and touched scope
- which files or surfaces changed
- whether the change was semantic, structural, or clarity-only
- what validation actually ran
- what still needs a slower model or human review
