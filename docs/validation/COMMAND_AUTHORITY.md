# Validation Command Authority

`aoa-kag` stores validation lane commands in
`config/validation_lanes.json`.

## Surfaces

| Surface | Function |
| --- | --- |
| `config/validation_lanes.json` | lane definitions and command sequences |
| `scripts/validation_lanes.py` | Python loader/API |
| `scripts/impact_routing.py` | fail-closed changed-path classifier and required-summary evaluator |
| `scripts/ci_gate.py` | CI lane executor |
| `scripts/release_check.py` | release entrypoint |
| `scripts/source_fast_handoff.py` | strict same-run source-fast receipt issuer and verifier |
| `scripts/ci_release_check.py` | CI-only release continuation selector with complete-release fallback |
| `scripts/coverage_run.py` | run-scoped coverage packet, telemetry receipt, and lifecycle boundary shared by lane processes |
| `scripts/run_tests.py` | unittest discovery for root and active mechanics part tests |
| `scripts/run_part_local_checks.py` | discovered part-local builder `--check` and validator checks |
| `scripts/validate_kag.py` | scoped local, OS-wide, or full KAG validation entrypoint |
| `scripts/validate_local_stats_port.py` | owner-local stats port adapter to the pinned `aoa-stats` validator |
| `scripts/issue_kag_mcp_source_identity.py` | private source-identity receipt and stack overlay issuer for one clean committed KAG source-index identity |
| `scripts/review_kag_mcp_result.py` | private KAG owner review of one exact, stack-attested `kag_discover` result against the source-pinned capture signer |
| `scripts/project_kag_mcp_owner_review.py` | fail-closed projection of one still-live exact KAG owner review into grounded-canary and freshness overlay fields, without proof or acceptance |
| `scripts/accept_kag_mcp_owner_contour.py` | private KAG owner acceptance of one exact proved read contour, without registry admission, runtime mutation, or rollback claim |
| `scripts/generate_repo_local_kag_index.py` | repo-local portable family builder, shard/budget gate, and logical source/artifact/anchor/entity/event/assertion/relation family builder |
| `scripts/assemble_repo_local_kag_family.py` | exact seven-file v2 compatibility assembler from the portable family |
| `scripts/validate_repo_local_kag_family.py` | schema and integrity validator for a repository-owned index family |
| `scripts/query_repo_local_kag.py` | validated exact, lexical, graph, and hybrid repo-local retrieval |
| `scripts/build_repo_local_kag_federation.py` | validated owner-qualified federation projection builder |
| `scripts/generate_repo_local_kag_coverage.py` | OS Abyss repo-local KAG coverage builder |
| `.github/actions/repo-local-kag-index/action.yml` | owner-callable full, incremental, and contract check using explicit repo-scoped source-lineage and event-history boundaries across the full owner validation job |
| `.github/workflows/repo-validation.yml` | always-required source-fast and self owner-family proof, conditional full pinned-provider audit, and stable required summary |
| `.github/workflows/compatibility-canary.yml` | scheduled floating-provider compatibility proof with complete Git history |

## Repo-local KAG History Boundaries

The repo-local KAG action keeps source lineage and repository-event history as
separate, explicit inputs. It resolves the `origin` default branch inside the
target `repo-root` and uses its merge base with `HEAD`; on the default branch
that boundary is `HEAD`. The builder combines this durable history with the
current repository snapshot, keeping a multi-commit branch and its squash-merged
default-branch snapshot on the same generated index family.

The action checks both full and incremental portable-family parity, the
changed-generated-bytes budget against that history boundary, the explicit
receipt route for an exceedance, the family validator, and deterministic v2
compatibility assembly.

Explicit caller inputs keep precedence. The action exports the resolved
repository name and both boundaries through repo-scoped environment variables
so later release-audit commands
reuse the same model.

## Run-Scoped Coverage Proof Reuse

`source-fast`, `generated`, compatibility-canary, and release entrypoints
create one temporary coverage run scope outside the repository. `source-fast`
uses only the local validator scope, so its standalone receipt may correctly
contain zero coverage builds. Generated and compatibility lanes run one
explicit OS-wide validator scope before fixed-point generation; release
inherits that audit through the generated lane. The packet identity binds the
run and lane, provider registry and validation inputs, every configured
owner's expected pin, HEAD, Git index tree, dirty/untracked state, portable
manifest, family/source/event digests, and the active schemas and builder
bytes.

The first OS-wide coverage consumer builds and schema-checks the payload.
Later consumers reuse it only when the complete identity still matches and the
packet identity and payload digests remain intact. A valid identity change
starts a new input epoch and rebuilds the packet; malformed, tampered, missing,
or symlinked packet state fails closed. The packet and JSONL timing receipt are
deleted when the run exits. The final receipt reports build count, hit/miss
count, the verified provider-revision digest and match count, compact full-input
and payload identities, coverage and lane wall time, and per-owner timings.
Each owner timing also reports user/system CPU, process peak RSS, and the
owner-source snapshot backend, capture wall time, Git invocation count, tracked
and content-read file counts, unique object count, bytes read, and in-process
read-cache hits/misses. These are execution telemetry, not proof results.
During one OS-wide process, provider-home validation may issue an ephemeral
token for the exact run scope, owner root, and portable-family digest. Coverage
still reloads and digest-checks the shards and proves complete rebuilt-family
equality; only the duplicate schema/semantic traversal is reused. Any token
miss performs the full traversal, and decoded-family retention is bounded to
the current sequential owner.
On GitHub Actions the same schema-versioned receipt is appended to the bounded
step summary; an unavailable or oversized summary is reported as degraded and
does not alter the blocking proof verdict recorded by the lane.
Exact provider revisions remain visible in the preceding provider-checkout
verification log. Neither surface becomes a committed read model or owner
truth.

## Exact Source-Fast Job Handoff

The high-impact GitHub workflow performs source-fast and owner-family proof in
its first job. That job issues one ephemeral
`aoa_kag_source_fast_handoff_v1` receipt only after both proofs succeed. The
receipt binds exact `HEAD`, Git index tree and entry digest, command-authority
and source-fast sequence digests, validator and builder input digests, donor
names with expected and observed registry pins, owner-family and source-index
identities, explicit history boundaries, and GitHub run, attempt, workflow,
SHA, repository, and producer-job identity.

The independent full-audit checkout recomputes the entire typed receipt.
Strict schema shape, digest, clean checkout, pin, family, command, input, and
workflow equality are all required. An accepted receipt selects the
`release-continuation` command sequence, which still runs the generated lane,
OS-wide provider/coverage audit, generated fixed point, machine-registry
bundle proof, and workflow generated-output cleanliness check. Missing,
malformed, ambiguous, stale, tampered, cross-run, or otherwise mismatched
receipts select the complete `release` sequence instead.

The receipt is not persisted and has no cross-run authority. Standalone
`scripts/release_check.py` always runs the full release sequence. Source-fast
checkout refs use the same exact pins as `manifests/provider_registry.json`,
and the owner-family action receives explicit event history refs.

## Immutable Owner Source Scans

An OS-wide coverage build captures one owner-local source epoch before it
validates that owner's source index, reconstructs the logical repository index
family, derives coverage counts, or falls back to a source-tree profile. For a
Git owner, the epoch is the staged index: one strict `git ls-files -s -z`
inventory plus one `git cat-file --batch` read of the unique required blobs.
All consumers receive the same read-only path, mode, object-id, and byte maps.
Repeated per-file `git show` calls are not the owner-scan authority.

Staged bytes and staged symlink targets remain authoritative even when the
worktree differs or a tracked path is deleted locally. Unmerged entries,
malformed index records, missing or wrong-type objects, truncated batch output,
unsafe paths, and a Git worktree without a usable Git reader fail closed. A
non-Git directory retains the explicit filesystem-source fallback. Portable
family control shards remain in tracked-path accounting but their bytes are not
loaded because they are excluded from the canonical source corpus.

The run still compares the complete provider input identity after the build.
Snapshot reuse therefore removes repeated reads inside one owner pass; it does
not authorize cross-owner, cross-run, or changed-input reuse.

## Validator Scopes

| Scope | Claim |
| --- | --- |
| `local` | repository-local schemas, manifests, provenance, routes, examples, portable family, and generated-structure integrity without loading every provider family |
| `os-wide` | provider-home completeness plus committed coverage parity against the complete current provider build; lane execution reuses one fully identified run-scoped packet for coverage consumers |
| `full` | local plus OS-wide validation; the no-argument compatibility default |

The source-fast command sequence always requests `local`. Generated and
compatibility sequences request exactly one `os-wide` scope before their first
coverage generation consumer. All scopes remain blocking where their owning
lane invokes them; a skipped OS-wide scope is not a successful audit.

## Fail-Closed Impact Routing

Pull-request impact routing is additive. The `Source Fast and Owner Family`
job always runs `source-fast` and the repo-local family action, including full
and incremental family parity, budgets, validation, and exact compatibility
assembly. The classifier cannot replace either proof; it decides only whether
the additional full OS-wide release audit is required.

That job materializes only the seven pinned source donors required by local KAG
validation (`Tree-of-Sophia`, `aoa-memo`, `aoa-playbooks`, `aoa-evals`,
`aoa-agents`, `aoa-techniques`, and `aoa-sdk`) plus pinned `aoa-stats`.
`aoa-sdk` supplies the source-pinned owner-review schema; the remaining
provider repositories, including private session memory, belong only to the
full OS-wide audit.

Rules live under `impact_routing` in `config/validation_lanes.json`. Provider
membership, registry and federation inputs, shared schemas, KAG ABI,
builders/loaders/validators, generated OS-wide coverage, trust artifacts,
receipts, budgets, pack/blob paths, and validation or release topology require
the full route. Full rules take precedence over owner-local rules. Invalid,
empty, unavailable, mixed high-impact, or unknown change sets also route to
full audit.

The stable `Repo Validation` job is a typed summary. It accepts only:

- `source-fast=verified`, `owner-family=verified`, and
  `full-audit=verified`; or
- for an explicitly owner-local pull request, the same two local proofs plus
  `full-audit=correctly-not-required`.

Push and manual events always require the full audit. The scheduled
compatibility canary remains supplementary evidence and cannot replace a
required pull-request audit.

The repository workflow uses a file-owned stable concurrency prefix. First
attempts share a stable group only with later first-attempt heads of the same
pull request; push, manual, and re-run attempts include their unique run and
attempt identity. A workflow display-name change cannot split the PR group,
and a stale re-run cannot collide with or cancel the current head. Although the
concurrency controller is enabled unconditionally, only successive first heads
of one pull request can share a group and therefore cancel in-progress work. A
cancelled superseded run is saved runner work, not validation evidence for its
replacement, and it cannot cancel main, manual, another pull request, a stale
re-run, or the compatibility canary. Jobs on the expensive and required-summary
path use `!cancelled()` rather than `always()`, so ordinary failures still reach
the typed summary while a superseded workflow can actually release its runner.

## Lane Entries

| Lane | Entry |
| --- | --- |
| `source-fast` | `python scripts/ci_gate.py --mode source-fast` |
| `generated` | `python scripts/ci_gate.py --mode generated` |
| `release` | `python scripts/release_check.py` |
| `release-continuation` | `python scripts/ci_release_check.py` (CI-only, exact receipt or full fallback) |
| `compatibility-canary` | `python scripts/ci_gate.py --mode compatibility-canary` |
| `advisory` | `python scripts/ci_gate.py --mode advisory` |

Impact classification and summary evaluation are support commands rather than
validation lanes:

- `python scripts/impact_routing.py classify ...`
- `python scripts/impact_routing.py summarize ...`

## Inventories

| Inventory | Function |
| --- | --- |
| `docs/validation/validator_inventory.json` | validator module map |
| `docs/validation/script_inventory.json` | script surface map |
| `docs/testing/test_inventory.json` | test home map |

## Failure Route

Fix the owner surface named by the failing check, then rerun the focused check
and the nearest lane entrypoint.
