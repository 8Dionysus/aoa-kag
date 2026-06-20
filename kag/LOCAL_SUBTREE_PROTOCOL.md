# Local KAG Subtree Protocol

## Status

This is a preflight protocol surface.

It is one active source family inside `kag/`, the `aoa-kag` source-home
preflight. It defines the first local-subtree contract shape for future KAG
organs, but it does not authorize sibling repositories to create `/kag` homes
yet.

## Purpose

A repo-local KAG organ is a repository-owned derived knowledge home for that
repository's source-linked indexes, graph nodes, graph edges, projections, and
freshness receipts.

Its job is to make local knowledge structure reviewable while preserving source
ownership.

## Context Map

| Context | Owns | Does not own |
| --- | --- | --- |
| source repository | authored source meaning and local source refs | cross-repo KAG protocol law |
| repo-local `/kag` organ | portable source-linked local records and local generated projections | proof verdicts, memory truth, routing authority, runtime graph state |
| `aoa-kag/kag/` | source-home preflight, shared local-subtree protocol, stop-lines, and future validation contract | sibling payloads and live stores |
| `aoa-kag/generated/` | current derived read models built from existing manifests | local-subtree protocol law |
| runtime graph/vector stores | mutable serving state owned by runtime/storage layers | Git-tracked source truth or portable protocol authority |

## Future Required Route

A future repo-local `/kag` organ should not be accepted until it has:

1. a local `AGENTS.md` route card;
2. a local `README.md` operating card;
3. a manifest contract for source refs and storage posture;
4. schemas and examples for every record class it stores;
5. a validator that rejects missing source refs, forbidden runtime state, and
   overclaiming;
6. a generated parity route when projections are produced;
7. a decision record when the rollout changes owner or federation posture.

## Reserved Future Surfaces

These names are reserved as protocol vocabulary. They are not active
directories until a future decision and validator activate them.

| Surface | Record class | Contract |
| --- | --- | --- |
| `manifest.json` | local KAG organ manifest | names repo, source refs, record classes, builders, validators, storage posture, and freshness mode |
| `nodes/` | portable KAG node records | source-linked; no node without a source ref; no source-authored meaning replacement |
| `edges/` | portable edge records | direct or explicitly derived; no silent multi-hop inference, ranking, or proof |
| `indexes/` | lightweight lookup indexes | inventory and lookup only; no embeddings, vector DBs, or runtime search state |
| `projections/` | compact local read models | generated from manifest-backed records; consumer-facing but weaker than sources |
| `receipts/` | generation, validation, freshness, and regrounding receipts | explains freshness and fallback; does not become proof verdict |

## Minimum Record Invariants

Every future portable local KAG record must make these fields or equivalents
reviewable:

- `schema_version`
- `repo`
- `local_id`
- `record_class`
- `source_refs`
- `provenance_mode`
- `generated_or_authored`
- `status`
- `owner_return_route`

Edges must additionally name `from_id`, `to_id`, and `edge_kind`.

Indexes must additionally name the indexed record class and the source records
used to build the index.

Receipts must additionally name the command or builder route, freshness result,
and fallback route.

## Storage Posture

Git may hold compact, portable, reviewable records and generated read models
when a future schema and validator make them safe.

Git must not hold:

- live graph databases;
- vector databases;
- embedding caches;
- runtime search indexes;
- benchmark outputs;
- large mutable generated stores;
- host-specific absolute paths;
- secrets or private evidence.

Runtime stores may consume local KAG records later, but they remain downstream
and must have their own owner route.

## Rollout Order

The intended order is:

1. define the source-home preflight and protocol in `aoa-kag/kag/`;
2. add schemas, examples, and validators in `aoa-kag`;
3. pilot one local KAG organ in a source repository with owner consent;
4. add `aoa-kag-mcp` only after the portable contract exists;
5. add `aoa-kag-skills` only after MCP/tool behavior is downstream of the
   protocol;
6. compose cross-repo graph projections from source-linked local organs.

## Stop-Lines

- Do not create sibling `/kag` directories from this preflight alone.
- Do not convert current `kag_export.min.json` capsules into the full local
  subtree contract by inertia.
- Do not treat a local index as ranking, proof, memory acceptance, or routing
  authority.
- Do not infer graph edges without an explicit source ref or declared derived
  method.
- Do not use runtime store availability as evidence that a portable KAG record
  is valid.

## Current Relationship to Mechanics

The `kag/` home is a source-home preflight and protocol surface, not an active
KAG-only mechanic package.

Mechanics may later grow a KAG-only package or part when repeatable operation
pressure has a stable payload class, local contract, stop-lines, and validation
route. Until then, `mechanics/` routes the pressure and `kag/` owns the protocol
language.
