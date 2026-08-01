# Immutable Batch Owner Source Scan

## Index Metadata

- Decision ID: AOA-KAG-D-0024
- Original date: 2026-07-31
- Surface classes: validation guard, source reader, coverage telemetry, CI performance
- KAG surfaces: repo-local source index, repository index family, OS-wide provider coverage
- Source lanes: aoa-kag, provider repositories
- Guard families: staged-source authority, exact byte parity, fail-closed Git input, run-scoped observability
- Posture: accepted

## Context

AOA-KAG-D-0021 removed repeated OS-wide coverage builds within one validation
run, but each retained build still reread a provider's staged source separately
for source-index parity and structural-family reconstruction. The reader used
one `git show :path` process per file, while coverage counters issued another
tracked-file inventory. On a 1,251-record owner, source-index verification alone
created roughly 1,253 child processes and took 20.90 seconds locally.

The proof boundary cannot move to worktree bytes, a weaker freshness proxy, or
an unchecked cache. Staged files, staged symlink targets, tracked deletions,
object identity, source-index digests, structure extraction, and final provider
input identity must retain their existing meaning.

## Decision

Capture one immutable source epoch per owner scan and pass it explicitly to all
source consumers in that scan. A Git epoch consists of a strict stage-zero
`git ls-files -s -z --cached` inventory and one `git cat-file --batch` read of
the unique required blobs. Read-only maps bind each path to its staged mode,
object ID, and exact bytes. Source-index matching, repository-family
reconstruction, fallback source profiling, and source counts reuse that epoch.

Gitlinks retain their prior `git show :path` representation through a bounded
per-Gitlink fallback because raw commit-object bytes are not equivalent. A
non-Git root retains filesystem scanning. A declared Git worktree never falls
back to filesystem bytes when Git inspection, index parsing, or object loading
fails.

Record owner wall time, user/system CPU, process peak RSS, snapshot capture
time, Git invocation count, tracked/content-read files, unique objects, bytes,
and read-cache hits/misses in the ephemeral run receipt. Telemetry describes
execution cost and cannot substitute for output parity or a proof verdict.
GitHub-hosted lanes append the same schema-versioned receipt to a bounded step
summary. Missing, unwritable, or oversized summary output is explicitly
degraded but cannot turn a failed proof into success or become owner truth.

Within one active validation run, a successful provider-home validation may
record a process-local token keyed by the run scope, resolved owner root, and
exact portable-family content digest. The later coverage reconstruction still
loads and digest-checks the portable shards and compares the complete rebuilt
family to the owner family, but it may reuse the already completed schema and
semantic traversal when that exact token matches. A missing run, root mismatch,
family digest change, non-portable family, or failed provider validation keeps
the full traversal. The token is never persisted or accepted across runs.

Keep only the current owner's decoded portable bundle in the in-process LRU.
The ordered audit is sequential, so retaining all 23 decoded families adds no
proof and only inflates peak RSS. The receipt reports family-validation token
hits and misses alongside the source-byte cache counters.

## Options Considered

- Keep per-file `git show`: preserves semantics but makes process startup scale
  with every record and repeats identical reads across consumers.
- Read the worktree directly: faster, but breaks staged-source authority,
  tracked-deletion behavior, and exact index identity.
- Persist a cross-run blob cache: could reduce I/O further, but adds trust,
  invalidation, storage, and corruption boundaries before the local process
  storm is removed.
- Capture and share one strict owner epoch in process: removes redundant Git
  processes while keeping the existing staged bytes and final identity guard.

## Rationale

The shared epoch changes transport cost, not KAG meaning. Git object IDs bind
batch-returned bytes to the same staged entries previously addressed by
`git show :path`; every record still recomputes and compares its content hash,
and the logical family is still rebuilt from those exact bytes. The post-build
provider identity comparison remains the guard against input movement during a
run.

Loading one owner's required bytes at a time increases bounded process memory
but avoids retaining all owners together. Excluding portable-family control
shards from content loading preserves tracked-path accounting without caching
bytes that the canonical source corpus cannot consume. Receipt RSS and byte
telemetry makes that tradeoff visible in hosted validation.

## Consequences

- The normal Git owner scan has a constant three reader invocations before any
  bounded Gitlink handling, rather than one process per source record.
- Duplicate staged blobs are transferred once and reused by path.
- Source and structure consumers cannot observe different bytes inside one
  owner pass.
- Unmerged entries, malformed index data, invalid object IDs or types, missing
  objects, truncated batch output, unsafe paths, and unavailable Git fail
  closed.
- No persistent cache, cross-run trust claim, proof weakening, owner fragment,
  parallelism increase, or change to generated payload schemas is authorized.
- Further CI optimization must use hosted A/B evidence and preserve the same
  source, family, coverage, trust, budget, and fixed-point outputs.

## Source Surfaces

- `scripts/generate_repo_local_kag_index.py`
- `scripts/generate_repo_local_kag_coverage.py`
- `scripts/coverage_run.py`
- `docs/validation/COMMAND_AUTHORITY.md`
- `docs/validation/SCRIPT_TOPOLOGY.md`
- `docs/validation/script_inventory.json`
- `docs/testing/TEST_TOPOLOGY.md`
- `docs/testing/test_inventory.json`
- `tests/test_repo_local_kag_index.py`
- `docs/decisions/AOA-KAG-D-0021-run-scoped-coverage-proof-reuse.md`

## Validation

Run snapshot unit cases for staged versus worktree bytes, symlink bytes,
duplicate blobs, missing objects, malformed batch output, and telemetry. Run
the repo-local index, repository-family, command-authority, workflow, decision,
script-topology, and test-topology tests. Compare source and complete logical
family payloads on identical real owner inputs, then run one full 23-owner
release audit and compare coverage and proof identities with the accepted
baseline. Treat lower wall time without identical proof payloads as failure.
