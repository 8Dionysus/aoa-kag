# Checkpoint Provenance

Start from this package's `README.md` and `PARTS.md`. Use provenance when a
checkpoint-like handoff route needs source trace.

## Center source

- `Agents-of-Abyss/mechanics/checkpoint/README.md`
- `Agents-of-Abyss/mechanics/checkpoint/PARTS.md`

## KAG source surfaces

- `mechanics/checkpoint/parts/reasoning-handoff/docs/reasoning-handoff.md`
- `mechanics/checkpoint/parts/reasoning-handoff/docs/reasoning-handoff-pack.md`
- `mechanics/checkpoint/parts/reasoning-handoff/manifests/reasoning_handoff_pack.json`
- reasoning handoff schemas, examples, generated outputs, validators, and tests.

## Active part provenance

- `mechanics/checkpoint/parts/reasoning-handoff/` owns focused handoff guardrail
  validation: counterpart contract refs, owner-state stop-lines, generated
  handoff pack contract, and local example posture.
- The reasoning-handoff source docs, manifest, schemas, examples, and generated
  handoff outputs live under
  `mechanics/checkpoint/parts/reasoning-handoff/` as the active part home.
- `scripts/kag_generation.py` and `scripts/validate_kag.py` remain root
  compatibility entrypoints that build and validate the part-local surfaces
  without owning a second root copy.

No package-local `legacy/` route is active yet.
