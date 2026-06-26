# Test Topology

This map keeps `aoa-kag` tests readable by function: family, protected
surface, owner, home, coverage authority, focused target, and failure route.

The machine inventory is `test_inventory.json`. Update it when a test file is
added, removed, renamed, split, folded, or moved to another home.

## Route Shape

```text
family -> protects -> owner surface -> home scope -> coverage authority -> focused target -> failure route
```

Test files describe coverage. Command sequences live in
`config/validation_lanes.json`. `scripts/run_tests.py` owns unittest discovery
for root and active mechanics part test homes.

## Coverage Kinds

Each inventory file entry names one or more `coverage_kinds`.

| Coverage Kind | Function |
|---|---|
| `topology/inventory` | route, inventory, lane, discovery, or module-topology authority |
| `source/route-contract` | authored route, source-policy, contract, or boundary wording |
| `generated/parity` | generated/read-model parity, builder output, or compact payload contract |
| `mechanics/part-behavior` | one active mechanics part's local behavior or part-owned contract |
| `release/artifact-trust` | release, CI, workflow, artifact bundle, or trust-gate behavior |
| `sibling/live-dependency` | explicit sibling-source compatibility or optional live dependency posture |

## Home Scopes

| Home Scope | Homes | Protects | Coverage Authority | Failure Route |
|---|---|---|---|---|
| `root` | `tests/` | Repo-wide route, docs, `kag/` source-home preflight, generated projection, validator, CI, mechanics skeleton, and release contracts. | `scripts/run_tests.py` | Route through the repo-wide source, owning part source, or validator. |
| `mechanics-part` | `mechanics/<package>/parts/<part>/tests/` | Active mechanic-owned payload builders, validators, source configs, and generated read-model companions for that part. | `scripts/run_tests.py` | Route through the owning part contract, validation route, source config, builder, validator, or generated companion. |

## Families

| Family | Protects | Owner Surface |
|---|---|---|
| `AGENTS/route` | Nested and semantic route-card shape. | AGENTS cards and semantic validators. |
| `docs/root-surface` | Root/docs routing, roadmap parity, and public KAG posture. | `README.md`, `ROADMAP.md`, `docs/`. |
| `decision-lane` | Decision record metadata and generated lookup indexes. | `docs/decisions/`. |
| `generated/read-model` | Generated KAG read models and downstream feed contracts. | repo-wide and part-local manifests/generated companions, builders, and `scripts/validate_kag.py`. |
| `kag/source-home-preflight` | Local `/kag` source-home manifest, protocol topology, reserved surface map, and source-home evidence map. | `kag/`. |
| `release/ci-lane` | CI lane composition, release stabilization, and workflow posture. | `config/validation_lanes.json`, `.github/workflows/*`, `scripts/release_check.py`. |
| `mechanics/root-topology` | Mechanics package map, KAG-only ownership shape, and part-directory readiness. | `mechanics/`. |
| `test-topology/authority` | Test inventory, home classification, and runner coverage. | `docs/testing/*` and `scripts/run_tests.py`. |
| `script-topology/authority` | Script inventory completeness, lane inclusion, side-effect map, and import smoke. | `docs/validation/script_inventory.json` and `docs/validation/SCRIPT_TOPOLOGY.md`. |
| `validation/command-authority` | Lane manifest, loader, CI gate, workflow posture, and release command storage. | `config/validation_lanes.json` and `docs/validation/COMMAND_AUTHORITY.md`. |
| `validation/validator-topology` | Validator owner modules, adapter thinness, validator inventory sync, and source/projection split. | `docs/validation/validator_inventory.json` and `scripts/validators/`. |

## Lane Rules

- Inventory entries name `focused_target`.
- Root and active mechanics part unittest homes are discoverable from
  `scripts/run_tests.py`.
- Part-local builder and validator scripts are discovered by
  `scripts/run_part_local_checks.py`; tests keep that runner in the
  `source-fast` lane and aligned with the script inventory.
- Release command order lives in `config/validation_lanes.json`.
- Mechanic part-local test homes enter runner coverage through an active part
  route.
