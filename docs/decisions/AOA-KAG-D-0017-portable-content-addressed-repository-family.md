# Portable Content-Addressed Repository Family

## Index Metadata

- Decision ID: AOA-KAG-D-0017
- Original date: 2026-07-17
- Surface classes: kag/source-home, schema contract, generated readmodel, validation guard, compatibility view, federation input
- KAG surfaces: portable record corpus, adaptive hash shards, family manifest, generated-change budget, v2 compatibility assembly
- Source lanes: aoa-kag, OS Abyss repo-local kag homes, abyss-stack runtime materializers, federation and MCP consumers
- Guard families: source ownership, offline portability, content identity, shard locality, tracked-byte budget, generated-delta budget, explicit exceedance receipt, compatibility parity
- Posture: accepted

## Context

AOA-KAG-D-0014 established a normalized seven-file v2 repository knowledge
kernel. That semantic split remains useful, but its physical Git form grew into
seven whole-corpus JSON files per owner. Across the 24 canonical OS Abyss
providers those files reached roughly 387 MiB, and 17 owners had at least one
file larger than 2 MiB. Ordinary source changes repeatedly rewrote every
monolith, while GitHub could no longer render most large family files in the
normal review surface.

Freshness and source ownership were not the failure. The missing invariant was
that the physical cost of changing a derived read model should remain
approximately proportional to the authored material that changed. The v2
family had no executable tracked-size budget, generated-delta budget, stable
shard identity, or explicit exceedance route.

## Decision

The canonical Git form becomes a v3 portable record corpus rooted at
`kag/indexes/index_family.manifest.json`. It stores source records, normalized
structural anchors, outbound declarations, and repository-history events once
in content-addressed JSONL shards. Artifact, entity, assertion, and relation
indexes remain logical canonical views but are rebuilt deterministically from
that corpus. The complete seven-file v2 family remains an exact compatibility
view assembled on demand and verified by its original content digests; it is
not tracked as seven monoliths.

Record keys are partitioned by adaptive SHA-256 prefixes. Existing partitions
may split but do not merge automatically, so unrelated records keep stable
paths as the corpus grows. The target shard size is 128 KiB, the hard shard
limit is 192 KiB, and an individual portable record may not exceed 128 KiB.
Oversized anchor and event lists are stored as bounded content chunks.

Every manifest carries an owner-local tracked-byte baseline, a 1 MiB default
changed-generated-bytes budget per change, and a 48 MiB global per-owner
ceiling. A change above the default delta budget requires a digest-bound,
base-ref-bound owner receipt under
`kag/receipts/index_family_budget/`. The initial v2-to-v3 migration uses the
same explicit receipt route. Crossing the standing tracked-byte baseline also
requires a digest-bound receipt; that receipt authorizes only the measured
family and cannot raise either standing limit. CI checks full build parity,
incremental parity, shard and record limits, family digests, compatibility
assembly, tracked size, and generated change amplification.

Consumers use a dual reader during migration. The five-operation MCP ABI,
qualified identities, v2 schemas, query semantics, federation projection, and
runtime materialization ownership do not change. `abyss-stack` may continue to
materialize large mutable stores; Git keeps only the portable corpus needed to
audit and reconstruct the logical family offline.

Generated OS coverage identifies an external owner's published family digest.
For `aoa-kag` itself it records `digest_state: self-manifest` and routes to the
local manifest without copying that digest into a generated file indexed by
the same family. This explicit self-reference break keeps generation
deterministic instead of seeking an impossible digest fixed point.

## Options Considered

- Keep the seven monoliths and add only a total-size warning: preserves the
  current paths but does not restore review locality or constrain change
  amplification.
- Shard all seven materialized views independently: restores smaller files but
  keeps redundant derived views in Git and still charges every owner for
  whole-family storage.
- Move the complete family to an external artifact store: reduces Git weight
  but weakens offline portability and makes external availability part of the
  canonical audit path.
- Store one source/structure/history corpus and deterministically assemble the
  seven logical views: preserves portability and exact compatibility while
  making the Git unit of change local and budgeted.

## Rationale

Source, structure, and repository history are the smallest portable materials
needed to reproduce the v2 logical family without reclassifying authored
meaning. The other four record classes are deterministic projections from
those materials. Keeping their contracts while removing their tracked
duplication separates semantic normalization from physical storage.

Adaptive content-addressed prefixes keep paths stable without selecting a
fixed shard count that is either too coarse for large owners or excessively
fragmented for small ones. Split-only evolution avoids broad path churn.
Digest-bound receipts make a deliberate large projection change visible
without weakening the default budget.

## Consequences

- D-0014 continues to own the logical repository knowledge kernel; this
  decision supersedes only its seven-monolith Git representation.
- A small source change normally rewrites a bounded set of shards instead of
  seven whole-corpus files.
- GitHub review, checkout, federation input, and CI can operate on bounded
  records while exact v2 consumers remain supported.
- The manifest and shards, not an assembled v2 directory, are the tracked
  canonical portable family.
- Shard count increases, and consumers that bypass the shared loader must
  migrate before v2 monoliths are removed.
- A budget receipt authorizes one measured exceedance; it does not raise the
  standing budget or prove that the underlying source change is desirable.
- Existing Git history is not rewritten. Historical monolith cost remains in
  old commits, while new commits stop adding whole-family rewrites.

## Source Surfaces

- `schemas/repo-local-kag-family-manifest.schema.json`
- `schemas/repo-local-kag-index.schema.json`
- `schemas/repo-local-kag-repository-index.schema.json`
- `scripts/generate_repo_local_kag_index.py`
- `scripts/assemble_repo_local_kag_family.py`
- `scripts/repo_local/portable_family.py`
- `scripts/validators/repo_local_kag_index.py`
- `.github/actions/repo-local-kag-index/action.yml`
- `config/validation_lanes.json`
- `kag/indexes/index_family.manifest.json`
- `kag/indexes/shards/`
- `kag/receipts/index_family_budget/`
- `tests/test_repo_local_kag_repository_indexes.py`
- `abyss-stack:mcp/services/aoa-kag-mcp/`

## Validation

Validation follows `docs/validation/COMMAND_AUTHORITY.md`, exact portable-to-v2
round-trip tests, full and incremental family parity, schema and digest
validation, shard and record limits, generated-delta budget checks, on-demand
compatibility assembly, canary consumers, and each adopting owner's canonical
landing route.
