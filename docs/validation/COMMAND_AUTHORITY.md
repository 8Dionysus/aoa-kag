# Validation Command Authority

`aoa-kag` uses a lane-owned command model:

- `config/validation_lanes.json` is the canonical storage surface for active
  lane definitions, blocking command sequences, generated drift paths, and
  advisory boundary notes.
- `scripts/validation_lanes.py` is the loader/API for Python callers.
- `scripts/ci_gate.py` executes CI lane modes.
- `scripts/release_check.py` remains the release entrypoint and worktree
  stabilizer, but it asks the loader for the `release` lane from the manifest.
- `scripts/run_tests.py` owns root unittest discovery for the current test
  home.
- `scripts/validate_kag.py` remains the transitional validator monolith for
  KAG source, schema, example, and generated parity checks.
- `docs/validation/script_inventory.json` describes every active script's
  owner, lane, side effects, and focused test target. It is inventory only, not
  a place to store executable lane sequences.
- GitHub workflow YAML calls lane entrypoints or the release entrypoint. It
  must not rebuild lane meaning inline.
- Active docs and route cards should name lane ids, focused local checks, or
  entrypoints rather than copying full command sequences.
- Decision records, changelogs, receipts, and review ledgers may preserve
  command evidence. They are not active lane authority.

## Lane Commands

Use these active entrypoints:

| Lane | Entry |
|---|---|
| `source-fast` | `python scripts/ci_gate.py --mode source-fast` |
| `generated` | `python scripts/ci_gate.py --mode generated` |
| `release` | `python scripts/release_check.py` |
| `compatibility-canary` | `python scripts/ci_gate.py --mode compatibility-canary` |
| `advisory` | `python scripts/ci_gate.py --mode advisory` |

## Promotion Rule

Advisory boundary notes become hard gates only when a current source owner,
runtime owner, or decision record proves that `aoa-kag` owns the behavior being
checked.

Until then, future mechanic part-local routes, live graph/vector/index state,
RAG runtime behavior, eval verdicts, memory truth, and source-authored meaning
stay as route boundaries. This repository can check portable KAG contracts,
generated parity, route cards, manifests, schemas, examples, and decision
records; it does not become the runtime graph store, embedding cache, or source
authoring layer.

## Failure Route

When a lane fails:

1. Fix the source owner that the failing command names.
2. Rebuild generated companions only from their source builders.
3. Keep `config/validation_lanes.json` as the command store if the command
   route itself moved.
4. Update `docs/validation/script_inventory.json` when a script is added,
   moved, removed, or changes owner, lane, side-effect posture, CI inclusion,
   or focused test target.
5. Update `docs/testing/test_inventory.json` when a test file is added, moved,
   removed, split, folded, or changes owner/failure route.
