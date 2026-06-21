# AGENTS.md Guidance for `examples/`

## Purpose
`examples/` holds root-publication illustrative payloads when root `schemas/`
need a public-safe example. In the current topology, mechanic-owned examples
live under `mechanics/<package>/parts/<part>/examples/` with their owning part.

## Editing posture
- Keep every example illustrative, sanitized, and easy to review.
- Keep each example aligned to its corresponding root or part-local schema.
- Prefer bounded, minimal examples that surface provenance and contract posture without pretending to be exhaustive.
- No secrets, private corpora, hidden environment assumptions, or private infra details.
- Do not add part-owned examples to root `examples/` unless a
  root-publication or compatibility contract explicitly owns that proxy.

## Review rules
- Update examples when a paired schema or manifest contract changes.
- Preserve source-first wording and visible provenance cues.
- Do not let a convenience example drift into an unofficial canonical payload.
