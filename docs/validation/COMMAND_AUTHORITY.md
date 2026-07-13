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
| `scripts/generate_repo_local_kag_index.py` | repo-local source/artifact/anchor/entity/event/assertion/relation index-family builder |
| `scripts/validate_repo_local_kag_family.py` | schema and integrity validator for a repository-owned index family |
| `scripts/query_repo_local_kag.py` | validated exact, lexical, graph, and hybrid repo-local retrieval |
| `scripts/build_repo_local_kag_federation.py` | validated owner-qualified federation projection builder |
| `scripts/generate_repo_local_kag_coverage.py` | OS Abyss repo-local KAG coverage builder |
| `.github/actions/repo-local-kag-index/action.yml` | owner-callable full, incremental, and contract check using explicit repo-scoped source-lineage and event-history boundaries across the full owner validation job |
| `.github/workflows/repo-validation.yml`, `.github/workflows/compatibility-canary.yml` | exact provider checkouts with complete Git history for repository-event parity in coverage and canary lanes |

## Repo-local KAG History Boundaries

The repo-local KAG action keeps source lineage and repository-event history as
separate, explicit inputs. On a pull request, both `history-ref` and
`event-history-ref` default to `github.event.pull_request.base.sha`; the builder
combines that durable base history with the current repository snapshot. This
keeps a multi-commit pull request and its squash-merged `main` snapshot on the
same generated index family.

On the default branch, `history-ref` resolves to `HEAD`. A feature-branch push
resolves both history boundaries to its merge base with the repository default
branch. Explicit caller inputs keep precedence. The action resolves the refs
inside `repo-root` and exports the resolved repository name and both boundaries
through repo-scoped environment variables so later release-audit commands
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
