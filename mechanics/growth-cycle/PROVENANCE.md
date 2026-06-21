# Growth Cycle Provenance

Start from this package's `README.md` and `PARTS.md`. Use provenance when a
growth rule needs rationale trace.

## Center source

- `Agents-of-Abyss/mechanics/growth-cycle/README.md`
- `Agents-of-Abyss/mechanics/growth-cycle/PARTS.md`

## KAG source surfaces

- `mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-maturity-governance.md`
- `mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-owner-wait-states.md`
- `mechanics/audit/parts/proof-expectation-refs/docs/kag-proof-expectations.md`
- `mechanics/growth-cycle/parts/surface-growth-stop-rule/manifests/kag_maturity_governance.json`
- `docs/decisions/AOA-KAG-D-0001-kag-maturity-hardening.md`
- generated maturity outputs, validators, and tests.

## Active part provenance

- `mechanics/growth-cycle/parts/surface-growth-stop-rule/` owns the focused
  stop-rule validation route for maturity governance, owner wait states, and
  blocked new `AOA-K-*` growth.
- `mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-maturity-governance.md`, `mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-owner-wait-states.md`,
  `mechanics/growth-cycle/parts/surface-growth-stop-rule/manifests/kag_maturity_governance.json`,
  `mechanics/growth-cycle/parts/surface-growth-stop-rule/generated/kag_maturity_governance.min.json`, and
  `mechanics/growth-cycle/parts/surface-growth-stop-rule/examples/kag_maturity_governance.example.json` are part-owned source,
  manifest, generated read-model, and public example surfaces.
- `mechanics/audit/parts/proof-expectation-refs/` owns the local audit route
  for proof expectation references named by maturity governance; `aoa-evals`
  remains the proof-verdict owner.
- `scripts/kag_generation.py` and `scripts/validate_kag.py` remain root
  compatibility/read-model entrypoints until a later split moves implementation
  ownership without changing their public lane role.

No package-local `legacy/` route is active yet.
