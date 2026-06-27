# AGENTS.md Guidance for `generated/`

## Purpose
`generated/` holds root/publication derived KAG outputs emitted from manifests, docs, and source-first lift rules. These files are reviewable artifacts, but they are not hand-authored truth. Mechanic-owned generated companions may live under `mechanics/<package>/parts/<part>/generated/` when the part owns the operation contract.

## Core rule
Do not hand-edit files in `generated/`. Regenerate them with `python scripts/generate_kag.py` and validate them with `python scripts/validate_kag.py`.

## Editing posture
- Expect paired `.json` and `.min.json` surfaces when a pack publishes both full and compact forms.
- Keep `generated/kag_registry*.json` aligned with the `artifact_identity` declared in `manifests/kag_registry.json`; it is the ABI subject for `docs/artifact-bundles/kag_registry.bundle.json`.
- Keep `generated/local_kag_provider_map*.json` aligned with `manifests/local_kag_readiness.json` and validated repo-local `kag/` provider homes; it is the MCP handoff read model.
- Do not pull part-local generated companions back into root unless a root-publication or compatibility contract explicitly owns that proxy.
- Review every diff against the corresponding manifest, docs, and donor-source refs before accepting it.
- Keep provenance fields, posture flags, review gates, and output refs intact.
- Treat drift between a manifest and its generated pack as a validation problem, not as permission for manual patching.

## Hard NO
Do not:
- repair a generated surface by hand
- use a generated file as a substitute for source-owned meaning
- strip provenance, review posture, or activation gates just to simplify a payload
- introduce framework-specific lock-in here unless the repository canon explicitly chooses it
