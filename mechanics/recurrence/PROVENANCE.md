# Recurrence Provenance

Start from this package's `README.md` and `PARTS.md`. Use provenance when a
recurrence or regrounding route needs source-owner trace.

## Center source

- `Agents-of-Abyss/mechanics/recurrence/README.md`
- `Agents-of-Abyss/mechanics/recurrence/PARTS.md`
- `Agents-of-Abyss/mechanics/recurrence/parts/reentry-routing/README.md`
- `Agents-of-Abyss/mechanics/recurrence/parts/proof-gates/README.md`

## KAG source surfaces

- `mechanics/recurrence/parts/return-regrounding/docs/recurrence-regrounding.md`
- `mechanics/recurrence/parts/return-regrounding/docs/recurrence-projection-inputs.md`
- `mechanics/recurrence/parts/return-regrounding/manifests/return_regrounding_pack.json`
- `mechanics/recurrence/parts/return-regrounding/examples/return_regrounding_pack.example.json`
- projection health, recurrence projection, and regrounding schemas, examples,
  generated outputs, validators, and tests.

## Active part provenance

- `mechanics/recurrence/parts/return-regrounding/` owns focused return
  validation: mode order, stronger refs, memo readiness ownership, and
  source-first return stop-lines.
- The return-regrounding source doc, manifest, schemas, examples, recurrence
  projection companion, and generated pack live under
  `mechanics/recurrence/parts/return-regrounding/` as the active part home.
- `mechanics/recurrence/parts/return-regrounding/docs/recurrence-projection-inputs.md`
  records the recurrence-projection input posture inside the active
  return-regrounding part until that pressure earns a separate part route.
- `scripts/kag_generation.py` and `scripts/validate_kag.py` remain root
  compatibility entrypoints that build and validate the part-local surfaces
  without owning a second root copy.

No package-local `legacy/` route is active yet.
