# AGENTS.md Guidance for `schemas/`

## Purpose
`schemas/` holds contract surfaces for manifests, generated packs, bridge envelopes, retrieval surfaces, consumer contracts, and other bounded KAG objects.

## Contract posture
Treat every schema edit as a contract change.
- Preserve the top-level keys expected by validation, including `$schema`, `$id`, `title`, `type`, `properties`, and `required`.
- Update the paired example in `examples/`, any affected manifest or generated surface, and validator coverage together.
- Keep schemas bounded and source-first. A schema may describe a KAG object, but it must not quietly absorb meaning that belongs in donor repositories.

## Review rules
- Make compatibility posture explicit when required fields or enums change.
- Prefer additive, reviewable contract changes over silent breaking rewrites.
- Keep naming aligned with the corresponding docs and manifest language.

## Hard NO
Do not:
- remove provenance-related fields without an explicit contract decision
- widen a schema until it can no longer express bounded KAG intent
- let a schema imply that derived substrate meaning replaced authored source meaning
