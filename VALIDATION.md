# `aoa-kag` Validation Routes

This is the on-demand human map for validation. The machine command authority
remains `config/validation_lanes.json`, loaded by `scripts/validation_lanes.py`.
Route cards name a lane or focused owner check; they do not copy a command
sequence. A green lane proves only its declared source contract, not live KAG
runtime state, provider deployment, proof, owner acceptance, external CI,
review, or merge.

## Lane entries

Select the narrowest lane that covers the changed surface. These entrypoints
are exact; their full sequences are owned by the manifest.

| Lane | Entry | Use for |
| --- | --- | --- |
| `source-fast` | `python scripts/ci_gate.py --mode source-fast` | local source, route-card, docs, test, and committed KAG integrity |
| `generated` | `python scripts/ci_gate.py --mode generated` | generated parity and the explicit OS-wide provider/coverage audit |
| `release` | `python scripts/release_check.py` | release-prep stabilization and full release proof |
| `release-continuation` | `python scripts/ci_release_check.py` | CI-only exact same-run receipt continuation or fail-closed fallback |
| `compatibility-canary` | `python scripts/ci_gate.py --mode compatibility-canary` | scheduled floating-sibling compatibility |
| `advisory` | `python scripts/ci_gate.py --mode advisory` | non-blocking future-pressure inventory |

`source-fast` and self owner-family proof are always required for landing
routes. Impact routing may add the full audit, but never removes those proofs.
Unknown, mixed, or unavailable impact evidence fails closed to the full route.

## Focused checks

Use the nearest owner surface and run only the focused check needed for the
named claim before selecting a broader lane:

- agent cards: the nested-AGENTS validator and semantic-AGENTS validator;
- decision records: decision-index parity/check and the decision-record
  validator; regenerate indexes only through their canonical builder;
- mechanics topology: the mechanics skeleton validator and the active part's
  own `VALIDATION.md` route;
- KAG source, manifests, schemas, examples, or generated outputs: the local
  KAG validator, then the generated lane when a derived surface is affected;
- tests: the focused unittest selection or the repository test runner named by
  `docs/testing/test_inventory.json`;
- quests: the quest-store validator and its focused tests;
- local stats: the pinned central stats-port validation route;
- release support: the release lane and the exact artifact/trust checks named
  by `docs/RELEASING.md`.

The 28 active part-local `VALIDATION.md` files are the exact procedure homes
for their respective builders, validators, fixtures, generated parity, and
fail-closed warnings. Do not duplicate a manifest-owned lane sequence there.

## Generated and provider boundaries

Change authored manifests, source docs, or builder inputs first. Invoke the
canonical builder or the generated lane in check mode as owned by that source;
never hand-edit a generated/read-model projection. Preserve source refs,
provider pins, provenance, artifact trust, budgets, quarantine, maturity,
runtime, proof, and owner handoff stop-lines. If an external owner input is
unavailable, leave its projection untouched and report the exact blocker.

## Evidence and closeout

Record the lane or focused check, exact result, source/generated paths,
provider or generated residuals, skipped checks, and unresolved owner boundary.
Do not turn local validation, a preparation receipt, or a generated parity
check into proof, runtime health, owner acceptance, external CI, review, or
merge evidence.
