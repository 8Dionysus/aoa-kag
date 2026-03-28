# AGENTS.md Guidance for `manifests/`

## Purpose
`manifests/` holds source-authored control surfaces for KAG-layer packs. These files declare what should be lifted, which donor surfaces are referenced, which derived outputs are expected, and which docs explain the pack. They are not generated outputs.

## Owns
This directory is the source of truth for:
- manifest definitions such as `kag_registry.json`, `technique_lift_pack.json`, `tos_text_chunk_map.json`, `tos_retrieval_axis_pack.json`, `reasoning_handoff_pack.json`, `federation_spine.json`, `cross_source_node_projection.json`, `source_owned_export_dependencies.json`, `counterpart_federation_exposure_review.json`, and `tiny_consumer_bundle.json`
- explicit source refs, output refs, review refs, and activation posture that belong to a manifest
- authored ordering and field discipline that generators and validators may enforce

## Does not own
Do not treat `manifests/` as the source of truth for:
- donor meaning from `aoa-techniques`, `aoa-playbooks`, `aoa-evals`, `aoa-memo`, `aoa-agents`, or `Tree-of-Sophia`
- generated payloads in `generated/`
- general prose doctrine that belongs in `docs/`

## Editing rules
- Keep manifests source-authored control surfaces, not generated mirrors.
- Keep source refs, output refs, and status posture explicit and reviewable.
- Update matching docs and `generated/` outputs together when a manifest contract changes.
- Preserve naming, ordering, and field discipline unless a deliberate contract change is being made.
- Re-run `python scripts/generate_kag.py` and `python scripts/validate_kag.py` after any manifest change.

## Hard NO
Do not:
- hand-copy generated payloads into manifests
- hide provenance behind vague repo-level references
- let a manifest overclaim source authority
- add private, hidden, or non-reviewable donor inputs
