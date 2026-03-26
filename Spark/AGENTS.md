# Spark lane for aoa-kag

This file only governs work started from `Spark/`.

The root `AGENTS.md` remains authoritative for repository identity, ownership boundaries, reading order, and validation commands. This local file only narrows how GPT-5.3-Codex-Spark should behave when used as the fast-loop lane.

If `SWARM.md` exists in this directory, treat it as queue / swarm context. This `AGENTS.md` is the operating policy for Spark work.

## Default Spark posture

- Use Spark for short-loop work where a small diff is enough.
- Start with a map: task, files, risks, and validation path.
- Prefer one bounded patch per loop.
- Read the nearest source docs before editing.
- Use the narrowest relevant validation already documented by the repo.
- Report exactly what was and was not checked.
- Escalate instead of widening into a broad architectural rewrite.

## Spark is strongest here for

- derived-structure docs, examples, schema, and test cleanup
- provenance wording refinement
- registry, projection, or capsule alignment
- tight audits of source-first discipline
- small retrieval-oriented surface repairs that do not alter source meaning

## Do not widen Spark here into

- rewriting authored source meaning here
- making KAG outputs look more authoritative than source repos
- identity collapse with ToS or AoA
- framework-bound expansion that outruns the repo’s bounded substrate role

## Local done signal

A Spark task is done here when:

- the derivation chain is clearer
- source-first wording remains explicit
- provenance is still reviewable
- generated outputs are aligned when touched
- the documented validation path ran when relevant

## Local note

Spark should keep derived surfaces legible and humble here: explicit lineage, bounded lift, no magical graph halo.

## Reporting contract

Always report:

- the restated task and touched scope
- which files or surfaces changed
- whether the change was semantic, structural, or clarity-only
- what validation actually ran
- what still needs a slower model or human review
