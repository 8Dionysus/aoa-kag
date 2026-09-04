# Historical Source Trees Outside Current KAG Navigation

## Index Metadata

- Decision ID: AOA-KAG-D-0050
- Original date: 2026-09-04
- Surface classes: agent lane, mechanics topology, provenance, validation guard
- KAG surfaces: source return, local agent mesh, repo-self family
- Source lanes: aoa-kag, source-owner repositories
- Guard families: source-owned authority, generated-output parity
- Posture: accepted historical-tree retirement; no substrate authority change

## Context

Spark companion instructions and four mechanics provenance scaffolds remain in
the active tree after their operational meaning has moved to current owner
cards and parts. Their presence increases navigation and generated source
surface without supplying an additional current contract.

## Decision

Retire the five source subtrees below. Preserve exact Git recovery and original
paths rather than creating a replacement archive directory. Each package's
PROVENANCE.md remains the bridge from current parts to historical indexes.
Bounded edits use current owner cards instead of a model-branded lane.

Regenerate repo-local source indexes through their canonical builder. Do not
keep source records for deleted files as if they still belonged to the current
checkout. Recovery links identify history; they do not make historical content
current source truth, proof, durable memory, runtime state, or owner acceptance.

This supersedes the Spark placement obligation in AOA-KAG-D-0008 and the
local archive-presence convention only. Existing decisions retain their
historical rationale; active KAG schema, protocol, provenance, provider, and
stronger-owner boundaries remain unchanged.

## Recovery

Exact source commit: `14ee1e33e43749d23c557b3ef526eca7edb36196`. All 18 tracked blobs were verified before retirement.

| Retired subtree | Historical source | Files |
| --- | --- | ---: |
| `.agents/spark/` | [Snapshot](https://github.com/8Dionysus/aoa-kag/tree/14ee1e33e43749d23c557b3ef526eca7edb36196/.agents/spark) | 2 |
| `mechanics/agon/legacy/` | [Snapshot](https://github.com/8Dionysus/aoa-kag/tree/14ee1e33e43749d23c557b3ef526eca7edb36196/mechanics/agon/legacy) | 4 |
| `mechanics/antifragility/legacy/` | [Snapshot](https://github.com/8Dionysus/aoa-kag/tree/14ee1e33e43749d23c557b3ef526eca7edb36196/mechanics/antifragility/legacy) | 4 |
| `mechanics/experience/legacy/` | [Snapshot](https://github.com/8Dionysus/aoa-kag/tree/14ee1e33e43749d23c557b3ef526eca7edb36196/mechanics/experience/legacy) | 4 |
| `mechanics/method-growth/legacy/` | [Snapshot](https://github.com/8Dionysus/aoa-kag/tree/14ee1e33e43749d23c557b3ef526eca7edb36196/mechanics/method-growth/legacy) | 4 |

Use `git show <full-source-commit>:<original-path>` to recover a file; resolve
its relative links within that same tree. Ordinary CI need not fetch history
or reconstruct the archive.

## Consequences

Current navigation loses the retired instruction and scaffold files. Historical
inspection becomes an explicit source-return operation. Decision and KAG
indexes remain derived; regenerate, validate locally, and check cross-owner
coverage before the final coordinated merge. No runtime deployment is implied.
