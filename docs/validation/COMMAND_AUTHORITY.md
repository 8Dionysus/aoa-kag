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
| `scripts/run_tests.py` | unittest discovery for root and active mechanics part tests |
| `scripts/run_part_local_checks.py` | discovered part-local builder `--check` and validator checks |
| `scripts/validate_kag.py` | repo-wide KAG validation entrypoint |
| `scripts/validate_local_stats_port.py` | owner-local stats port adapter to the pinned `aoa-stats` validator |
| `scripts/generate_repo_local_kag_index.py` | v3/v4 owner-family builder, corpus/distribution identity, Git-hot and artifact-cold placement, CAS/pack publication, shard and budget gate, and logical compatibility family builder |
| `scripts/build_repo_local_kag_release.py` | explicit owner-family release builder/check route; generated lanes use a bounded transient artifact root when no persistent root is supplied |
| `scripts/validate_repo_local_kag_release.py` | complete CAS release and exact compatibility parity validator |
| `scripts/export_repo_local_kag_bundle.py`, `scripts/import_repo_local_kag_bundle.py` | offline and air-gapped owner-family transfer |
| `scripts/prepare_repo_local_kag_externalization.py` | explicit isolated-worktree mutation route for canary and rollout externalization; stops before the owner commit and exact-source release |
| `scripts/run_repo_local_kag_rollout.py` | non-mutating 24-owner shadow, canary, rollout, and post-merge publication proof through the abyss-machine trust plane |
| `scripts/classify_repo_local_kag_impact.py` | deterministic impact class, affected views, validation lane, and full-fanout reason |
| `scripts/assemble_repo_local_kag_family.py` | exact seven-file v2 compatibility assembler from Git-hot plus CAS objects |
| `scripts/validate_repo_local_kag_family.py` | schema and integrity validator for a repository-owned index family |
| `scripts/query_repo_local_kag.py` | validated exact, lexical, graph, and hybrid repo-local retrieval |
| `scripts/build_repo_local_kag_federation.py` | validated owner-qualified federation projection builder |
| `scripts/generate_repo_local_kag_coverage.py` | OS Abyss repo-local KAG coverage builder |
| `.github/actions/repo-local-kag-index/action.yml` | owner-fast classifier, v3/v4 full and incremental parity, bounded scratch CAS release, family validation, and exact v2 assembly |
| `.github/workflows/repo-validation.yml` | owner-fast PR gate plus conditional 24-owner fan-out for central changes, main, weekly, and manual release audit |
| `.github/workflows/compatibility-canary.yml` | floating full-provider compatibility audit with complete Git history |

## Repo-local KAG History Boundaries

The repo-local KAG action keeps source lineage and repository-event history as
separate, explicit inputs. It resolves the `origin` default branch inside the
target `repo-root` and uses its merge base with `HEAD`; on the default branch
that boundary is `HEAD`. The builder combines this durable history with the
current repository snapshot, keeping a multi-commit branch and its squash-merged
default-branch snapshot on the same generated index family.

The action classifies the change and checks both full and incremental
owner-family parity, the changed-generated-bytes and Git-hot budgets, the
explicit receipt route for an exceedance, a complete bounded artifact release,
the family validator, and deterministic v2 compatibility assembly. A normal
owner PR does not checkout or scan 24 source trees. Central schema, builder,
partition, MCP loader, trust, access, or membership changes route to the full
24-owner audit.

Within one generated/full-audit run, `scripts/ci_gate.py` creates a temporary
`AOA_KAG_COVERAGE_PACKET`. The first coverage rebuild reads each pinned owner;
later generators and validators reuse the packet only when its owner Git-tree,
builder digest, schema epoch, canonicalization epoch, and distribution epoch
still match exactly. A mismatch fails the run instead of silently rescanning a
different snapshot. The compatibility canary uses the same run-scoped rule.
The generated lane validates the complete committed state before regeneration;
its final per-builder checks plus the before/after drift snapshot replace a
redundant second full provider validation.

Explicit caller inputs keep precedence. The action exports the resolved
repository name and both boundaries through repo-scoped environment variables
so later release-audit commands
reuse the same model.

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
