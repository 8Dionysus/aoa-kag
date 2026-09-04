# AGENTS.md

## Applies to

Everything under `stats/` in `aoa-kag`.

## Role

This directory owns KAG-local statistical questions, their embedded
measurement contracts, and evidence-linked reference packets. Shared
statistical grammar and cross-owner composition remain owned by `aoa-stats`.

## Read before editing

1. Root `AGENTS.md` and `DESIGN.md`.
2. `stats/port.manifest.json`.
3. The referenced source or generated KAG evidence.
4. The central measurement and packet contracts under `aoa-stats/stats/`.

## Boundaries

- `port.manifest.json` owns the KAG-local question and measurement meaning.
- Reference packets are derived snapshots and remain weaker than their named
  KAG source, manifest, schema, builder, and generated evidence.
- A pass ratio describes the named canonical family check only. It does not
  become source meaning, proof quality, retrieval quality, or runtime state.
- Keep packet refs repository-relative and keep raw source content out of the
  packet.

## Validation

Inspect the owner evidence before selecting the central owner validation route
through root `VALIDATION.md`.
## Closeout

Report the question or contract changed, the owner evidence inspected, whether
the reference packet was refreshed, and which validation route ran.
