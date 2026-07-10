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
| `scripts/generate_repo_local_kag_index.py` | repo-local source surface index builder |
| `scripts/generate_repo_local_kag_coverage.py` | OS Abyss repo-local KAG coverage builder |
| `.github/actions/repo-local-kag-index/action.yml` | owner-callable repo-local source index parity entrypoint |

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
