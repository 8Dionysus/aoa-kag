# AGENTS.md

## Guidance for `config/`

`config/` holds build, projection, publication, and consumer-support inputs for KAG surfaces.

Config may shape derived projections, but it must not create new source meaning or bypass owner wait states.

Keep config explicit, provenance-aware, and reviewable. Avoid private corpora, hidden embeddings, secret tokens, and local-only assumptions.

When config changes generated projections, rebuild and inspect provenance, source refs, quarantine posture, and maturity governance.

Full validation command sequences live in `config/validation_lanes.json`.
The same manifest owns fail-closed impact rules. `source-fast` and the self
owner-family proof remain always required; new or uncertain surfaces default
to the full audit instead of widening the owner-local allowlist implicitly.
When generated projections are affected, select the generated lane followed by
the source-fast lane from root `VALIDATION.md`.

## Validation

Select the narrowest applicable lane or focused check from root `VALIDATION.md`; the manifest remains command authority.
