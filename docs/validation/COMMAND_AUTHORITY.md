# Validation Command Authority

`aoa-kag` stores validation lane commands in
`config/validation_lanes.json`.

The on-demand human route map is root [`VALIDATION.md`](../../VALIDATION.md);
this document remains the command-authority and topology reference.

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
| `scripts/ci_preflight_dag.py` | checkout/sentinel scheduler whose result never substitutes for owner proof |
| `scripts/prepare_landing.py` | isolated pre-push SCC preparation without validation-lane or caller-index authority |
| `scripts/prepare_owner_landing.py` | isolated owner-neutral repo-local family preparation without owner/release-proof or caller-index authority |
| `scripts/repo_local_kag_gate.py` | fail-fast owner-family component DAG with stable-candidate and complete-command receipts |
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
| `.github/actions/repo-local-kag-index/action.yml` | owner-callable incremental drift sentinel plus bounded full/contract/assembly DAG using explicit repo-scoped source-lineage and event-history boundaries |
| `.github/workflows/repo-validation.yml` | always-required source-fast and self owner-family proof, conditional full pinned-provider audit, and stable required summary |
| `.github/workflows/compatibility-canary.yml` | scheduled compatibility proof with exact `aoa-stats` provider pin and moving sibling inputs |

## Repo-local KAG History Boundaries

The repo-local KAG action keeps source lineage and repository-event history as
separate, explicit inputs. It resolves the `origin` default branch inside the
target `repo-root` and uses its merge base with `HEAD`; on the default branch
that boundary is `HEAD`. The builder combines this durable history with the
current repository snapshot, keeping a multi-commit branch and its squash-merged
default-branch snapshot on the same generated index family.

The action first runs incremental portable-family parity as a drift sentinel.
Only a clean candidate fans out the full parity check, family validator, and
deterministic v2 compatibility assembly. Two workers are the default; one is
the exact sequential rollback and three remains an explicit comparison input.
Scheduling never makes a command advisory: all four canonical components,
the changed-generated-bytes budget, and any explicit exceedance receipt remain
blocking, and a changed candidate identity rejects an otherwise green result.

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

Before the provider sweep, the process captures the complete packet identity.
After each provider home passes its full validation, coverage builds that
owner's canonical row from the exact decoded family already bound to the
active run, resolved root, and family digest. Only the compact row and timing
survive into the next owner. The first OS-wide coverage consumer requires all
owners exactly once in canonical order, rechecks the complete identity, and
only then schema-checks and writes the payload.
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
The same receipt carries additive `aoa-kag-validation-timing-v1` records for
canonical commands, provider-home proofs, and root repo-local index phases.
Each record includes pass/fail status, wall and CPU time, a peak-RSS
observation, and bounded component identity. Telemetry publication failure is
reported as degraded and never changes a validation verdict. The dependency
and experiment interpretation of these records is documented in
`docs/validation/CI_EVIDENCE_DAG.md`.

Repository-family payload validation may reuse a compiled JSON Schema
validator only for byte-identical schema content inside the same Python
process. Every owner payload and semantic cross-reference assertion remains
blocking, and changed schema bytes compile and meta-validate as a new input.
`AOA_KAG_FORCE_COLD_SCHEMA_COMPILATION=1` disables this reuse for comparison
or rollback.
For schemas using only the admitted vocabulary and local references, exactly
`jsonschema-rs==0.49.2` may evaluate payloads. The first valid instance for an
exact schema identity is shadowed by Python, accelerated rejections are always
confirmed by Python, and an unavailable or wrong version, unknown vocabulary,
non-local reference, engine error, or disagreement falls back to Python.
`AOA_KAG_FORCE_PYTHON_SCHEMA_VALIDATION=1` is the exact accelerated-path
rollback. The coverage receipt reports engine/version, fast, shadow, reject,
fallback-reason, and disagreement counters; these are execution telemetry and
cannot alter the blocking schema or semantic verdict.
During one OS-wide process, provider-home validation may pass the exact decoded
portable family forward only for the current owner. Coverage still proves
complete rebuilt-family equality and source parity; it removes the second
shard decode as well as the duplicate schema/semantic traversal. A missing
prebuild scope preserves the cold standalone path, while an incomplete or
mismatched active prebuild fails closed. Decoded-family retention is bounded to
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

## Landing Preparation Entry

Landing preparation is deliberately separate from the blocking validation
lanes. It generates the root coverage, generated KAG, portable family, and
final digest-bound budget receipt in an isolated staged worktree, but its
receipt never substitutes for source-fast, the OS-wide owner proof, release
audit, or the stable landing verdict. Inside the SCC it rebuilds the `aoa-kag`
coverage row and reuses external rows only from the resolved history ref when
the canonical coverage runtime is byte-identical, owner order and roots remain
canonical, every external checkout matches its exact registry pin, and every
portable-family identity matches the pinned manifest. Any mismatch rejects the
shortcut and routes to the unchanged full owner build; no proof verdict is
reused.

The v2 family budget receipt is accepted only when its exact resolved base,
family digest, source snapshot, candidate file-inventory seal, and executing
producer procedure/action identity all match. The candidate seal excludes only
the receipt directory itself so publication can remain self-reference-safe;
the receipt reason and approver are context, not authority.

```bash
python scripts/prepare_landing.py --check
python scripts/prepare_landing.py --apply
python scripts/prepare_landing.py --verify-applied-seal <apply-receipt>
```

Both modes resolve the local default-branch merge base without a hidden network
call and require exact, clean, complete-history pinned provider roots. When a
candidate carries a refreshed preparation-only coverage payload,
`--coverage-seed-ref` names that exact ancestor without changing the separate
history, event-history, or budget-base refs required by AOA-KAG-D-0041. Use
`scripts/sync_provider_checkouts.py` as the explicit materialization route when
those roots are absent. `--check` leaves the caller worktree and index unchanged;
`--apply` changes only worktree files in the generated patch and verifies that
the caller index stayed byte-identical. Before returning success, apply restores
the caller's exact index partition in the already validated isolated candidate
and compares it with the actual caller result by byte, mode, directory,
hardlink, xattr, index, untracked, and nested-checkout identity. Filesystem
times are excluded from that final comparison because applying the patch must
change them; the caller is still checked for full-identity stability around
the comparison. After staging only the receipt-listed generated paths, run
`--verify-applied-seal` against that apply receipt. This cheap route requires
the worktree content and provider identities to remain exact and the staged
tree to equal the already proved fixed-point tree. A verified staging
transition therefore replaces only an immediate unchanged second preparation
check. Worktree or provider mutation, or any other index transition,
invalidates it; it never replaces source-fast, OS-wide proof, release, or
landing authority. A budget exceedance requires an explicit
`--budget-reason`, and that receipt is created only after the SCC has converged
to its final family digest.

Every other provider repository uses the owner-neutral preparation route from
an `aoa-kag` checkout. It copies the target candidate into a detached temporary
worktree, regenerates only `kag/indexes/` and any explicit family-budget
receipt, then runs the same canonical owner-family gate before reporting or
applying a patch. It does not require the target repository to vendor KAG
implementation code.

```bash
python scripts/prepare_owner_landing.py --repo-root /path/to/owner --check
python scripts/prepare_owner_landing.py --repo-root /path/to/owner --apply
```

Both owner modes preserve the target Git index. A budget exceedance still
requires `--budget-reason`; preparation never authors that owner judgment.

The CI-only preflight DAG overlaps a seed-only self-coverage sentinel with the
existing bounded provider checkout wave. A failed sentinel cancels only that
wave started by the same scheduler; a failed checkout cancels only its sentinel
peer. After successful fan-in it checks the generated projection, then the
unchanged release continuation still executes every canonical owner and
artifact proof. Seed/runtime mismatch is explicitly inapplicable and falls
through to that full proof rather than becoming success evidence.
For exact-head hosted admission, manual dispatch exposes `preflight_mode` with
`candidate` and `direct-control` values. The control retains the same checkout
command and every downstream proof while omitting only the sentinels; pull
requests and all non-manual defaults always select `candidate`.
Manual exact-head comparisons also pass the immutable PR-base commit through
`history_ref`; when it is omitted, the existing event-derived history boundary
remains unchanged. The CI preflight may additionally receive a
`coverage-seed-ref` pointing at the exact candidate head (or the checked-out
default-branch head). That ref is used only by the seed-only preparation
sentinels and reads the preparation-only payload at
`generated/repo_local_kag_preparation_seed.json`; it must be an ancestor of the
candidate and match the canonical coverage runtime inputs. The self sentinel
does not promote seeded external rows into the authoritative coverage read
model. Complete external-row parity remains blocking in the unchanged
OS-wide proof. The seed never changes the `history_ref`, source-fast donor
boundary, provider proof, release continuation, or landing authority.

The hosted admission evidence distinguishes success latency from failure
latency. The sentinel is not a green-path proof shortcut: successful fan-in
always proceeds to the unchanged release continuation. Its admitted benefit is
typed early rejection of self-coverage drift, with peer-only checkout
cancellation. The exact-head direct control remains available only for manual
comparison and never changes the pull-request/default candidate posture.

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
