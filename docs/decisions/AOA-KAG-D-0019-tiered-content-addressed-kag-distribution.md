# Tiered Content-Addressed KAG Distribution

## Index Metadata

- Decision ID: AOA-KAG-D-0019
- Original date: 2026-07-18
- Surface classes: kag/source-home, schema contract, artifact distribution, runtime materialization, federation input, validation guard
- KAG surfaces: corpus identity, distribution identity, Git-hot bootstrap, content-addressed cold shards, owner-family release, OS composition, transport packs, offline recovery
- Source lanes: aoa-kag, OS Abyss repo-local kag homes, abyss-machine artifact trust, abyss-stack runtime materializers, federation and MCP consumers, aoa-evals, aoa-stats
- Guard families: source ownership, identity separation, offline portability, Git-hot ceiling, artifact admission, bounded hydration, rollback, public safety, compatibility parity
- Posture: accepted

## Context

AOA-KAG-D-0017 replaced seven whole-corpus JSON files with one normalized
portable record corpus and adaptive content-addressed shards. That migration
restored local generated diffs. The central rollout snapshot reported
283,751,563 tracked bytes, while a later recomputation directly from all 24
immutable `origin/main` manifests measured 284,890,209 bytes. The 1,138,646
byte drift comes from final `abyss-stack`, `aoa-skills`, and `aoa-stats`
owner-manifest values that postdate the values embedded in the central
coverage snapshot; it is recorded in
`docs/validation/kag_tiered_baseline.evidence.json`. The live v3 surface is
therefore 84.9 percent of the 320 MiB ceiling. It still does not separate
logical corpus identity from Git placement. Every canonical shard remains
tracked by every owner.

The remaining pressure is architectural rather than a stale-output defect.
Knowledge can continue to grow while Git-hot review and bootstrap material
must remain bounded. Artifact storage, mirrors, pack layouts, and runtime
caches also change for operational reasons that do not change authored
knowledge. Treating those changes as one family identity would cause false
semantic churn and make relocation, repacking, failover, and rollback unsafe.

Measurements of the v3 corpus show that source shards plus manifests occupy
about 58 MiB across all 24 owners, while anchor, event, and chunk shards account
for most of the remaining bytes. Source records retain discovery coordinates,
provenance, access posture, owner-return routes, and deterministic rebuild
inputs. They therefore form a stable bootstrap surface without using runtime
popularity to decide what Git tracks.

## Decision

The repository family advances to a tiered distribution contract with two
independent identities. Corpus identity covers the ordered logical records,
source snapshot, canonicalization and schema epochs, shard contents, and exact
compatibility-view digests. Distribution identity covers Git-hot placement,
artifact-cold placement, locators, deterministic transport packs, signatures,
and lifecycle state. Moving an unchanged shard between Git, a verified local
CAS, or a remote mirror changes distribution identity but never corpus
identity.

All `source` shards are the deterministic Git-hot bootstrap profile. Anchor,
event, anchor-chunk, and event-chunk shards are content-addressed cold objects.
The profile is declarative and owner-qualified; committed LRU or LFU selection
is forbidden. A small corpus manifest, distribution manifest, hot profile,
schemas, digests, provenance coordinates, release coordinates, and required
receipts remain in Git. Full owner families are immutable signed releases in
the `abyss-machine` artifact trust plane. An OS snapshot is a composition of
24 owner release digests rather than one mandatory OS-wide archive.

Shard digests remain the minimum content identity. Bounded deterministic packs
are transport optimizations with a shard-to-pack range index; repacking cannot
change corpus identity. Consumers use a dual v3/v4 reader during rollout and
may resolve cold objects from Git-hot files, a verified local CAS, a trusted
remote artifact route, or a deterministic source rebuild. Partial, stale,
revoked, unavailable, and degraded states are explicit. The five-operation
read-only MCP ABI remains unchanged and cannot hide unbounded hydration inside
one request.

The 320 MiB aggregate ceiling is reinterpreted as the non-growing hard limit
for mandatory Git-hot KAG material, not total OS knowledge. It cannot be
overridden by an ordinary owner receipt. The migration must finish at or below
234,881,024 bytes (70 percent), retain the 48 MiB per-owner hard ceiling, and
preserve the 1 MiB default generated-delta budget.

## Options Considered

- Keep every v3 shard in Git and raise the aggregate ceiling: postpones the
  failure while preserving corpus-size-proportional checkout, history, and CI.
- Select hot shards by query frequency: optimizes one runtime workload but
  creates unrelated committed churn, weakens reproducibility, and can erase
  rare audit and owner-return routes.
- Move each complete family to one artifact archive: reduces Git bytes but
  recreates the monolith as the delivery and update unit.
- Keep source bootstrap shards in Git and distribute all remaining immutable
  shard objects through a content-addressed trust plane: bounds Git while
  retaining deterministic discovery, audit, exact reconstruction, selective
  hydration, and mirror-independent identity.

## Rationale

Corpus identity must answer whether the knowledge changed. Distribution
identity must answer how a specific immutable corpus is available. Keeping
these questions separate allows mirrors, packs, signatures, promotion state,
and cache topology to evolve without rewriting semantic federation identity.

All-source Git-hot selection is deliberately simple. It is stable under
unrelated runtime demand, carries the routes required to discover and rebuild
the rest of the family, and provides substantial measured headroom. Cold
canonical shards remain portable records rather than opaque runtime databases.
Exact, graph, vector, embedding, and query-cache projections continue to be
regenerable `abyss-stack` runtime artifacts with their own identities.

Content-addressed shard objects preserve incremental cost: an owner update
publishes only new objects and reuses unchanged ones. Bounded packs improve
transport without becoming canonical storage units. Per-owner releases and a
small OS composition avoid making all 24 owners the minimum update boundary.

An owner-generated readmodel must not embed the exact digest, byte size, or
object count of the family that contains that readmodel. Its self row is
explicitly `self-excluded` and points to the immutable owner release
measurement packet. Exact owner-inclusive and OS-wide measurements belong to
the signed release/composition plane outside corpus identity. This keeps a
missing self measurement visible without creating a numeric or digest fixed
point during regeneration.

## Consequences

- D-0017 continues to own normalization, adaptive shard identity, record
  limits, exact v2 assembly, and the logical portable corpus.
- This decision supersedes D-0017 only where it implied that the entire
  canonical portable corpus must be physically tracked in Git.
- Owner repositories keep authored meaning and a bounded auditable bootstrap;
  `aoa-kag` does not become the source owner.
- `abyss-machine` must admit, sign, retain, revoke, and garbage-collect KAG
  release objects fail-closed.
- `abyss-stack` must materialize selected verified objects, preserve last-good
  projections, and report degradation without claiming runtime state as truth.
- Federation may update one owner manifest and affected cross-owner relations
  without scanning unchanged source trees; central semantic changes still
  require a full 24-owner audit.
- Offline consumers require either a pre-exported verified bundle or the source
  snapshot and deterministic builder route. Artifact unavailability alone
  cannot make knowledge irrecoverable.
- Existing Git history is not rewritten. Cold shards are removed from current
  trees only after 24-owner shadow publication, five-owner canary proof, offline
  proof, rollback proof, and live runtime/MCP verification.
- Public releases must exclude private session, memory, host, query, secret,
  and runtime material. Restricted KAG requires a separate trust domain.

## Source Surfaces

- `schemas/repo-local-kag-corpus-manifest.schema.json`
- `schemas/repo-local-kag-distribution-manifest.schema.json`
- `schemas/repo-local-kag-hot-profile.schema.json`
- `schemas/kag-owner-family-release.schema.json`
- `schemas/kag-os-composition.schema.json`
- `schemas/kag-artifact-locator.schema.json`
- `schemas/kag-pack-index.schema.json`
- `schemas/kag-owner-change-receipt.schema.json`
- `schemas/kag-receipt-governance.schema.json`
- `scripts/repo_local/tiered_family.py`
- `scripts/repo_local/kag_impact.py`
- `scripts/build_repo_local_kag_release.py`
- `scripts/validate_repo_local_kag_release.py`
- `scripts/classify_repo_local_kag_impact.py`
- `kag/indexes/index_family.manifest.json`
- `kag/indexes/corpus.manifest.json`
- `kag/indexes/hot_profile.json`
- `abyss-machine:schemas/artifact-bundle-v1.schema.json`
- `abyss-stack:Configs/mcp/services/aoa-kag-mcp/`

## Validation

Validation follows `docs/validation/COMMAND_AUTHORITY.md` and must prove:
corpus/distribution identity separation; byte-exact shard and pack round trips;
v2 compatibility parity; v3/v4 dual-reader parity; deterministic source-only
Git-hot selection; exact owner/source/trust admission; offline export/import
and source rebuild; corruption, revocation, outage, GC, and last-good rollback;
one-owner selective CI; full-fanout semantic triggers; 24-owner shadow and
release reconstruction; five-owner externalization canary; aggregate Git-hot
usage at or below 70 percent; and live runtime/MCP behavior after merge.
