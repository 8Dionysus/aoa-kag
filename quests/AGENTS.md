# AGENTS.md

## Applies to

This card applies to `quests/` and all descendants unless a nearer
`AGENTS.md` narrows the path.

## Role

`quests/` is the source quest record district for durable KAG-layer obligations.
It keeps `aoa-kag` follow-through public-safe, lane-first, and lifecycle-aware:

Quest records use `quests/<lane>/<state>/<quest-file>` paths.


`QUESTBOOK.md` is the human open-obligation index. `mechanics/questbook/` owns
questbook operation law, schemas, examples, validators, and focused tests.

## Read before editing

Read root `AGENTS.md`, `QUESTBOOK.md`, this card, and the nearest lane route
before changing quest records. Consult the quest-store README only when the
named task needs its human contract.

## Boundaries

- Do not put source quest records inside mechanics parts.
- Do not keep active source records as root `quests/AOA-KAG-Q-*.yaml` aliases.
- Do not store private scratch, raw transcripts, hidden graph state, secrets,
  source corpus bodies, or runtime evidence here.
- Do not use quests as a second roadmap or as proof of owner acceptance.
- Route proof to `aoa-evals`, memory truth to `aoa-memo`, routing authority to
  the `aoa-sdk` control plane, and authored source meaning to the owning source
  repo.

## Validation

After changing quests or quest route docs, select the quest-store on-demand route
in root `VALIDATION.md`.

## Closeout

Report quest IDs changed, lane/state paths, whether `QUESTBOOK.md` changed,
whether quest catalog or dispatch examples changed, checks run, skipped checks,
and any stronger-owner acceptance still missing.
