# Separate MCP Source Identity From Acceptance

## Index Metadata

- Decision ID: AOA-KAG-D-0026
- Original date: 2026-08-01
- Surface classes: source identity, MCP handoff, owner evidence, acceptance boundary
- KAG surfaces: canonical source index, access-plane evidence, owner acceptance
- Source lanes: aoa-kag, abyss-stack, aoa-evals
- Guard families: clean committed source, exact identity, freshness, no proof inference, no acceptance inference
- Posture: accepted

## Context

An `abyss-stack` runtime observation can identify a deployed package, process,
endpoint, registry entry, consumer schema, and captured result without proving
which current KAG owner source that runtime represents. The existing KAG owner
review grounds one captured result and its source-index freshness, but it is
deliberately not source admission, central proof, owner acceptance, or organ
admission.

The organ-access maturity chain therefore needs an independently issued source
axis. Letting the stack infer owner source from deploy metadata, or letting a
central eval fill an absent owner identity, would move KAG authority into a
runtime or proof consumer. Combining source identity with acceptance would
also make a pre-proof observation appear accepted.

## Decision

KAG may issue one bounded MCP source-identity receipt only from a clean tracked
Git snapshot. The receipt binds the current committed revision to the canonical
KAG source-index identity already expressed by the repository's portable index
family. It may be projected into one private, short-lived `abyss-stack`
evidence overlay, but neither artifact can assert package deployment, runtime
compatibility, central proof, owner acceptance, admission, or rollback.

Source identity, captured-result review, central proof, and owner acceptance
remain separate transactions. The KAG acceptance transaction may run only
after a named, content-addressed `aoa-evals` proof has passed. It binds that
proof and packet to the exact accepted source revision, deployed package,
process identity, server schema, registered consumer, grounded canary, and
owner freshness watermark. Acceptance does not itself admit the organ or prove
rollback; those remain stack control and rollback-owner decisions.

## Options Considered

- Let `abyss-stack` infer KAG source identity from the deployed package or
  registry entry.
- Let central proof fill missing source identity or imply KAG acceptance.
- Combine KAG source identity and owner acceptance in one pre-proof receipt.
- Issue bounded source identity independently, then require separate result
  review, central proof, owner acceptance, admission, and rollback evidence.

## Rationale

The fourth route preserves the owner chain. KAG alone identifies its logical
source; the stack owns mutable deployment and serving state; `aoa-evals` owns
the bounded proof contract; KAG retains semantic acceptance; and stack control
surfaces own admission. Each receipt can expire or fail without silently
upgrading another maturity axis.

The canonical source-index digest is a better KAG identity than an ambient
worktree hash because it names the exact provenance-aware logical source
surface consumed by KAG projections. Requiring a clean tracked snapshot keeps
the revision and that identity reproducible. Untracked local files do not enter
the receipt because the issuer reads committed source at the named revision.

## Consequences

- A stack candidate can replace `source=unknown` with exact, owner-issued,
  expiring evidence without claiming that the runtime is accepted.
- Dirty tracked changes block source-identity issuance rather than producing a
  receipt whose revision omits active source changes.
- The source receipt and overlay remain private mode-0600 artifacts and carry
  no credentials or secret values.
- A green central eval cannot impersonate KAG acceptance, and a KAG acceptance
  cannot impersonate stack admission or rollback proof.
- The separate acceptance receipt is short-lived, private, content-addressed,
  and refuses an expired or drifting source, runtime, consumer, canary, owner
  review, proof report, or proof packet.
- Other organs must issue identity and acceptance through their own owner
  surfaces rather than reusing KAG semantics.

## Source Surfaces

- `kag/indexes/index_family.manifest.json`
- `schemas/kag-mcp-source-identity-receipt.schema.json`
- `examples/kag_mcp_source_identity_receipt.example.json`
- `scripts/issue_kag_mcp_source_identity.py`
- `tests/test_kag_mcp_source_identity.py`
- `schemas/kag-mcp-owner-acceptance-receipt.schema.json`
- `examples/kag_mcp_owner_acceptance_receipt.example.json`
- `scripts/accept_kag_mcp_owner_contour.py`
- `tests/test_kag_mcp_owner_acceptance.py`
- `scripts/review_kag_mcp_result.py`
- `docs/decisions/AOA-KAG-D-0023-review-captured-mcp-results-in-the-owner.md`
- `aoa-evals:evals/boundary/aoa-organ-access-admission-integrity/EVAL.md`
- `abyss-stack:mcp/services/abyss-stack-mcp/src/abyss_stack_mcp/overlay.py`

## Validation

Run the focused source-identity tests, schema/example validation, script/test
topology tests, decision-index generation/check, and the source-fast lane.
Cross-repository materialization must additionally validate the produced
overlay against the exact `abyss-stack` overlay schema.
