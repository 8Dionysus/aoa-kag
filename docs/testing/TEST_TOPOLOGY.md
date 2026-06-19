# Test Topology

This map keeps `aoa-kag` tests readable as a topology authority for the KAG
substrate. Tests should answer what boundary is protected, which owner surface
is authoritative, where the test lives, which execution authority covers it,
and where a failure routes next.

The machine inventory is `test_inventory.json`. Update it when adding,
deleting, renaming, splitting, folding, or changing the home of a test file.
Dependency checkouts under `.deps/` are external evidence context and must not
be counted as `aoa-kag` test homes.

## Route Shape

Use the compact route shape:

```text
family -> protects -> owner surface -> home scope -> coverage authority -> focused target -> failure route
```

Test files are not command authority. Blocking command sequences live in
`config/validation_lanes.json`; release execution enters through the lane
system. `scripts/run_tests.py` owns unittest discovery for the current root test
home.

## Home Scopes

| Home Scope | Homes | Protects | Coverage Authority | Failure Route |
|---|---|---|---|---|
| `root` | `tests/` | Repo-wide route, docs, generated projection, validator, CI, mechanics skeleton, and release contracts. | `scripts/run_tests.py` | Fix the root-owned source or validator before changing future mechanic-local tests. |

## Families

| Family | Protects | Owner Surface |
|---|---|---|
| `AGENTS/route` | Nested and semantic route-card shape. | AGENTS cards and semantic validators. |
| `docs/root-surface` | Root/docs routing, roadmap parity, and public KAG posture. | `README.md`, `ROADMAP.md`, `docs/`. |
| `decision-lane` | Decision record metadata and generated lookup indexes. | `docs/decisions/`. |
| `generated/read-model` | Generated KAG read models and downstream feed contracts. | `manifests/`, `generated/`, builders, and `scripts/validate_kag.py`. |
| `release/ci-lane` | CI lane composition, release stabilization, and workflow posture. | `config/validation_lanes.json`, `.github/workflows/*`, `scripts/release_check.py`. |
| `mechanics/root-topology` | Current mechanics root skeleton and no-package stop-line. | `mechanics/`. |
| `test-topology/authority` | Test inventory, home classification, and runner coverage. | `docs/testing/*` and `scripts/run_tests.py`. |
| `script-topology/authority` | Script inventory completeness, lane inclusion, side-effect boundaries, and safe import smoke. | `docs/validation/script_inventory.json` and `docs/validation/SCRIPT_TOPOLOGY.md`. |
| `validation/command-authority` | Lane manifest, loader, CI gate, workflow posture, and release command storage. | `config/validation_lanes.json` and `docs/validation/COMMAND_AUTHORITY.md`. |

## Lane Rules

- Inventory entries must name `focused_target`, not commands.
- Root unittest homes must be discoverable from `scripts/run_tests.py`.
- Release command order belongs in `config/validation_lanes.json`; tests may
  assert lane coverage but must not replay the release sequence as a local
  command store.
- Future mechanic part-local pytest homes should be covered through a dedicated
  lane after an active mechanic package exists.
