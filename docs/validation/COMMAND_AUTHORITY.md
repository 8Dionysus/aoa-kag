# Validation Command Authority

`aoa-kag` stores validation lane commands in
`config/validation_lanes.json`.

## Surfaces

| Surface | Function |
| --- | --- |
| `config/validation_lanes.json` | lane definitions and command sequences |
| `scripts/validation_lanes.py` | Python loader/API |
| `scripts/ci_gate.py` | CI lane executor |
| `scripts/release_check.py` | release entrypoint |
| `scripts/coverage_run.py` | run-scoped coverage packet, telemetry receipt, and lifecycle boundary shared by lane processes |
| `scripts/run_tests.py` | unittest discovery for root and active mechanics part tests |
| `scripts/run_part_local_checks.py` | discovered part-local builder `--check` and validator checks |
| `scripts/validate_kag.py` | repo-wide KAG validation entrypoint |
| `scripts/validate_local_stats_port.py` | owner-local stats port adapter to the pinned `aoa-stats` validator |
| `scripts/review_kag_mcp_result.py` | private KAG owner review of one exact, stack-attested `kag_discover` result against the source-pinned capture signer |
| `scripts/generate_repo_local_kag_index.py` | repo-local portable family builder, shard/budget gate, and logical source/artifact/anchor/entity/event/assertion/relation family builder |
| `scripts/assemble_repo_local_kag_family.py` | exact seven-file v2 compatibility assembler from the portable family |
| `scripts/validate_repo_local_kag_family.py` | schema and integrity validator for a repository-owned index family |
| `scripts/query_repo_local_kag.py` | validated exact, lexical, graph, and hybrid repo-local retrieval |
| `scripts/build_repo_local_kag_federation.py` | validated owner-qualified federation projection builder |
| `scripts/generate_repo_local_kag_coverage.py` | OS Abyss repo-local KAG coverage builder |
| `.github/actions/repo-local-kag-index/action.yml` | owner-callable full, incremental, and contract check using explicit repo-scoped source-lineage and event-history boundaries across the full owner validation job |
| `.github/workflows/repo-validation.yml`, `.github/workflows/compatibility-canary.yml` | exact provider checkouts with complete Git history for repository-event parity in coverage and canary lanes |

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
create one temporary coverage run scope outside the repository. The packet
identity binds the run and lane, provider registry and validation inputs, every
configured owner's expected pin, HEAD, Git index tree, dirty/untracked state,
portable manifest, family/source/event digests, and the active schemas and
builder bytes.

The first OS-wide coverage consumer builds and schema-checks the payload.
Later consumers reuse it only when the complete identity still matches and the
packet identity and payload digests remain intact. A valid identity change
starts a new input epoch and rebuilds the packet; malformed, tampered, missing,
or symlinked packet state fails closed. The packet and JSONL timing receipt are
deleted when the run exits. The final receipt reports build count, hit/miss
count, the verified provider-revision digest and match count, compact full-input
and payload identities, coverage and lane wall time, and per-owner timings.
Exact provider revisions remain visible in the preceding provider-checkout
verification log. Neither surface becomes a committed read model or owner
truth.

## Lane Entries

| Lane | Entry |
| --- | --- |
| `source-fast` | `python scripts/ci_gate.py --mode source-fast` |
| `generated` | `python scripts/ci_gate.py --mode generated` |
| `release` | `python scripts/release_check.py` |
| `compatibility-canary` | `python scripts/ci_gate.py --mode compatibility-canary` |
| `advisory` | `python scripts/ci_gate.py --mode advisory` |

## Inventories

| Inventory | Function |
| --- | --- |
| `docs/validation/validator_inventory.json` | validator module map |
| `docs/validation/script_inventory.json` | script surface map |
| `docs/testing/test_inventory.json` | test home map |

## Failure Route

Fix the owner surface named by the failing check, then rerun the focused check
and the nearest lane entrypoint.
