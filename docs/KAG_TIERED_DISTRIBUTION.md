# Tiered KAG Distribution

This document is the public architecture contract for portable KAG family
storage. Durable rationale lives in
[`AOA-KAG-D-0019`](decisions/AOA-KAG-D-0019-tiered-content-addressed-kag-distribution.md).

## Invariant

The cost of changing a derived read model should be approximately
proportional to the authored material that changed. Total knowledge may grow;
mandatory Git-hot material, PR diff, checkout, and ordinary owner CI must not
grow in lockstep with the complete corpus.

## Three Identities

| Identity | Depends on | Must not depend on |
| --- | --- | --- |
| corpus | owner, source snapshot, schema/canonicalization epochs, ordered logical records, shard contents, compatibility digests | URL, mirror, pack layout, cache path, signature location |
| distribution | hot/cold placement, packs, locators, provenance, signature and lifecycle state | runtime query frequency or mutable projection layout |
| runtime projection | admitted corpus digest, projection kind, model/config/epoch, local build state | authored authority |

Relocation and repacking may change distribution identity without changing
corpus identity. Any logical record-content change must change corpus identity.

## Physical Planes

### Git-hot bootstrap

Git keeps:

- corpus and distribution manifests;
- schemas, builder identity, source snapshot, and compatibility digests;
- the deterministic hot profile and bounded bootstrap shards;
- artifact locators and rebuild routes;
- owner-return/provenance coordinates;
- durable release and budget receipts.

Committed hot selection is deterministic and based on bootstrap, discovery,
audit, and owner-return needs. Runtime LRU/LFU information cannot churn the
committed hot set.

### Content-addressed artifact plane

Cold canonical shards are stored by SHA-256 object identity. Deterministic,
bounded multi-shard packs are transport optimizations with a separate
shard-to-pack index and byte-range descriptors. Repacking does not alter the
corpus digest. Unchanged objects are reused across owner releases.

An owner-family release binds the owner and source snapshot to the corpus,
distribution, ordered objects, packs, compatibility digests, provenance,
signature, verification, lifecycle, rollback, and supersession coordinates.
Source-bound lifecycle states additionally bind the exact owner commit in the
external immutable release. The committed generated manifest uses a stable
source-tree marker instead of recursively embedding the commit that contains
it.

### OS composition

An OS snapshot is a small signed composition of 24 verified owner releases. An
ordinary owner update replaces that owner entry and the affected cross-owner
relations; it does not create a mandatory monolithic OS archive or reread every
unchanged source tree.

### Runtime projection

`abyss-stack` admits verified owner releases into a local CAS and materializes
only requested exact, graph, vector, or cache projections. These stores are
mutable, regenerable, freshness-bearing, and never canonical source truth.
Owner-qualified retrieval inputs preserve both corpus and distribution
identities, while the logical projection digest excludes distribution-only
coordinates. Physical relocation therefore cannot masquerade as a semantic
projection change.

## Owner Split

| Owner | Authority |
| --- | --- |
| source repository | authored meaning and canonical owner records |
| `aoa-kag` | record model, canonicalization, schemas, manifests, compatibility assembly, federation semantics and validators |
| `abyss-machine` | signing, verification, promotion, subject store, retention, revocation and artifact admission |
| `abyss-stack` | local CAS, materialization, projection invalidation, last-good state and service lifecycle |
| `aoa-kag-mcp` | read-only `discover`, `search`, `read`, `traverse`, `explain` access |
| `aoa-evals` | retrieval, degradation, compatibility and effect regression proof |
| `aoa-stats` | shared cross-owner measurement grammar |

Artifact storage, runtime projection, federation, and MCP cannot replace the
authored owner.

## Consumer Routes And States

Bounded consumers try explicit routes rather than hiding an unbounded fetch:

1. Git-hot read;
2. verified local CAS;
3. trusted remote artifact read;
4. deterministic rebuild from the source snapshot.

The result state is one of `complete`, `git_hot_complete`, `hot_only`,
`artifact_required`, `artifact_unavailable`, `rebuild_available`,
`rebuild_required`, `stale`, `digest_mismatch`, `revoked`, or
`access_denied`. Partial data is never labelled complete.

## Budgets

The immutable aggregate Git-hot ceiling is 335,544,320 bytes (320 MiB). The
post-migration operating target is at most 234,881,024 bytes (70 percent).

| Utilization | State |
| --- | --- |
| below 70% | normal |
| 70-80% | warning and growth forecast required |
| 80-90% | offload required |
| 90-100% | no new hot growth except repair or migration |
| 100% or more | hard failure |

The per-owner hard ceiling remains 48 MiB and the default changed-generated
budget remains 1 MiB. A one-change owner receipt cannot raise a standing
budget or bypass the OS ceiling. Repeated receipts trigger topology review and
then block further exceptions.

## CI Split

The deterministic impact classifier selects owner-local, distribution-only,
incremental-federation, or full-24-owner lanes. Ordinary owner changes build
and validate one owner, exact compatibility views, and the artifact delta.
Incremental federation changes run release/distribution-manifest-only
composition and affected relation/projection checks without a 24-owner source
checkout. Aggregate physical measurements are accepted only after the signed
owner release is bound to the referenced distribution digest and summary.
Shared schema, canonicalization, partitioning, federation, MCP loader, trust
root, access, or owner-membership changes trigger full fan-out. Weekly,
release, recovery, rollback, revocation, and topology-review audits also run
the full lane.

## Security Boundary

Public releases are scanned for private/session/runtime leakage. Admission is
fail-closed for digest, signature, owner, source-ref, schema/ABI, revocation,
and access-policy failures. Restricted knowledge, if introduced, uses a
separate trust domain and registry rather than the public release plane.
