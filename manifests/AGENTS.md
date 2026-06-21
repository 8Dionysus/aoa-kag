# AGENTS.md Guidance for `manifests/`

## Purpose
`manifests/` holds root-publication control surfaces for repo-wide KAG
outputs. These files declare what root outputs should exist, which authority
surface owns the publication contract, and which generated read models must
stay aligned. They are not generated outputs.

## Owns
This directory is the source of truth for:
- root manifest definitions such as `kag_registry.json`
- root-publication manifests that compose part-local outputs without owning the
  part-local source controls
- explicit source refs, output refs, review refs, and activation posture that belong to a manifest
- authored ordering and field discipline that generators and validators may enforce

## Does not own
Do not treat `manifests/` as the source of truth for:
- donor meaning from `aoa-techniques`, `aoa-playbooks`, `aoa-evals`, `aoa-memo`, `aoa-agents`, or `Tree-of-Sophia`
- generated payloads in `generated/`
- part-local source controls under `mechanics/<package>/parts/<part>/manifests/`
- part-local schemas, examples, docs, or generated companions owned by a
  mechanic part
- general prose doctrine that belongs in `docs/`

## Editing rules
- Keep manifests source-authored control surfaces, not generated mirrors.
- Keep `kag_registry.json#/artifact_identity` synchronized with `scripts/kag_generation.py` and `docs/artifact-bundles/kag_registry.bundle.json` when the KAG registry ABI contract changes.
- Keep source refs, output refs, and status posture explicit and reviewable.
- Update matching docs and generated outputs together when a manifest contract
  changes. For part-local manifests, follow the nearest
  `mechanics/<package>/parts/<part>/AGENTS.md` route.
- Preserve naming, ordering, and field discipline unless a deliberate contract change is being made.
- Re-run `python scripts/generate_kag.py` and `python scripts/validate_kag.py` after any manifest change.

## Hard NO
Do not:
- hand-copy generated payloads into manifests
- hide provenance behind vague repo-level references
- let a manifest overclaim source authority
- add private, hidden, or non-reviewable donor inputs
