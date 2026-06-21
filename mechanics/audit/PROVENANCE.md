# Audit Provenance

Start from this package's `README.md` and `PARTS.md`. Use provenance when an
audit route needs evidence or source-owner trace.

## Center source

- `Agents-of-Abyss/mechanics/audit/README.md`
- `Agents-of-Abyss/mechanics/audit/PARTS.md`

## KAG source surfaces

- `mechanics/audit/parts/proof-expectation-refs/docs/kag-proof-expectations.md`
- `mechanics/audit/parts/exposure-review/docs/counterpart-federation-exposure-review.md`
- `mechanics/boundary-bridge/parts/source-owned-export/docs/federation-kag-readiness.md`
- `mechanics/boundary-bridge/parts/source-owned-export/docs/source-owned-export-dependencies.md`
- matching manifests, generated outputs, validators, and tests.

## Active part provenance

- `mechanics/audit/parts/proof-expectation-refs/` owns focused validation that
  KAG proof refs remain `aoa-evals` refs and never become proof verdicts.
- `mechanics/audit/parts/exposure-review/` owns focused validation for
  counterpart federation exposure review, planned-only AOA-K-0008 posture, and
  tiny-bundle review refs.
- `mechanics/audit/parts/exposure-review/` owns the review doc, manifest,
  schemas, example, and generated review read-model outputs for the
  counterpart federation exposure review artifacts.
- `scripts/kag_generation.py` and `scripts/validate_kag.py` remain root
  compatibility/read-model entrypoints for generated parity.

No package-local `legacy/` route is active yet.
