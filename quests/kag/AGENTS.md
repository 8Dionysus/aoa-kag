# AGENTS.md

## Applies to

This card applies to `quests/kag/` and all lifecycle state directories under
it.

## Role

`quests/kag/` holds schema-backed `AOA-KAG-Q-*.yaml` source quest records for
KAG-local derived-substrate obligations.

Use lifecycle state directories:


The state directory must match the YAML `state` field.

## Read before editing

Read root `AGENTS.md`, `QUESTBOOK.md`, `quests/AGENTS.md`, this card, and
`mechanics/questbook/parts/quest-store/CONTRACT.md`. Consult the local README
only when the named task needs its human contract.

## Boundaries

- Keep these records KAG-local.
- Do not claim source-owner acceptance or proof closure here.
- Do not use `kag/` quest records to activate live graph, retrieval, index,
  vector, embedding, or runtime state.
- Keep each source path lane/state accurate when a quest changes state.

## Validation

Run the quest-store validation route from `quests/AGENTS.md`.

## Closeout

Report the quest ID, old path, new path when moved, state, index visibility,
and validation result.
