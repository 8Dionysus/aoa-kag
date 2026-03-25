# AGENTS.md Guidance for `generated/`

## Purpose
`generated/` holds derived KAG outputs emitted from manifests, docs, and source-first lift rules. These files are reviewable artifacts, but they are not hand-authored truth.

## Core rule
Do not hand-edit files in `generated/`. Regenerate them with `python scripts/generate_kag.py` and validate them with `python scripts/validate_kag.py`.

## Editing posture
- Expect paired `.json` and `.min.json` surfaces when a pack publishes both full and compact forms.
- Review every diff against the corresponding manifest, docs, and donor-source refs before accepting it.
- Keep provenance fields, posture flags, review gates, and output refs intact.
- Treat drift between a manifest and its generated pack as a validation problem, not as permission for manual patching.

## Hard NO
Do not:
- repair a generated surface by hand
- use a generated file as a substitute for source-owned meaning
- strip provenance, review posture, or activation gates just to simplify a payload
- introduce framework-specific lock-in here unless the repository canon explicitly chooses it
