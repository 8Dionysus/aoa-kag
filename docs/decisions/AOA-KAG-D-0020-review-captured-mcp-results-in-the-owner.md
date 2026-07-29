# Review Captured MCP Results In The Owner

## Index Metadata

- Decision ID: AOA-KAG-D-0020
- Original date: 2026-07-28
- Surface classes: schema contract, MCP handoff, owner evidence
- KAG surfaces: capability discovery, owner grounding, freshness review
- Source lanes: aoa-kag, aoa-sdk, abyss-stack, aoa-evals
- Guard families: owner boundary, exact capture binding, freshness, no acceptance inference
- Posture: accepted

## Context

The KAG runtime now returns tiered-distribution and degradation posture from
`kag_discover`, while the public KAG capability schema still rejected those
fields. More importantly, an authenticated runtime canary could show that one
call returned structured data but could not prove that the data still matched
the KAG owner contract or current source-index identity.

The runtime owner can preserve exact private bytes, but it does not own KAG
payload meaning. Central evals can compose evidence, but they cannot infer the
KAG owner's grounding or freshness judgment.

## Decision

Keep capture and owner review separate.

`abyss-stack` captures one bounded, untrusted `kag_discover` result and issues
only runtime evidence. `aoa-kag` validates the exact content-addressed artifact
against `schemas/kag-mcp-capabilities.schema.json`, requires the requested
`aoa-kag` owner row, compares runtime and canonical source-index digests, and
materializes the shared SDK owner-review receipt.

The capability schema additively admits the runtime-owned `distribution` and
`degradation` handoff fields while keeping their bounded top-level shape. The
owner review is valid only within the capture expiry and keeps owner
acceptance, central proof, admission, cross-organ proof, and rollback
structurally false.

## Options Considered

- Let the stack validate KAG meaning during capture.
- Let central evals infer grounding from a successful call.
- Preserve exact capture bytes, then issue a separate KAG-owner review.

## Rationale

The third route preserves the accepted KAG/stack split: KAG owns capability
and source-freshness meaning; stack owns mutable serving state and capture.
The SDK supplies only the shared transport-neutral receipt shape, and evals
remain consumers rather than sources of owner truth.

## Consequences

- Schema drift now produces an explicit rejected owner review.
- Matching runtime and canonical owner digests can support exact freshness.
- The reviewer independently resolves the canonical source-index digest from
  the owner source. It rejects self-reported equality that conflicts with that
  digest and never compares a portable-family digest to a runtime
  source-index digest.
- Stale or missing owner digests remain readable only under an explicit
  non-exact state or block the review.
- A valid owner review is still not KAG acceptance or organ admission.
- Other KAG operations need their own owner payload review before they can
  claim result grounding.

## Source Surfaces

- `schemas/kag-mcp-capabilities.schema.json`
- `examples/kag_mcp_capabilities.example.json`
- `scripts/review_kag_mcp_result.py`
- `tests/test_kag_mcp_owner_review.py`
- `docs/decisions/AOA-KAG-D-0015-kag-mcp-retrieval-contract.md`
- `aoa-sdk:schemas/organ-access/organ-owner-result-review.schema.json`
- `abyss-stack:mcp/services/abyss-stack-mcp/src/abyss_stack_mcp/canary.py`

## Validation

Run the focused owner-review tests, KAG schema/example validation,
decision-index generation/check, script/test topology checks, and the
source-fast lane. Cross-repository integration must additionally validate a
produced receipt against the exact SDK schema.
