# AGENTS.md Guidance for `examples/`

## Purpose
`examples/` holds public-safe illustrative payloads that show how KAG schemas are expected to look. These files help readers and validators, but they are not live generated state and they are not hidden corpus extracts.

## Editing posture
- Keep every example illustrative, sanitized, and easy to review.
- Keep each example aligned to its corresponding schema in `schemas/`.
- Prefer bounded, minimal examples that surface provenance and contract posture without pretending to be exhaustive.
- No secrets, private corpora, hidden environment assumptions, or private infra details.

## Review rules
- Update examples when a paired schema or manifest contract changes.
- Preserve source-first wording and visible provenance cues.
- Do not let a convenience example drift into an unofficial canonical payload.
