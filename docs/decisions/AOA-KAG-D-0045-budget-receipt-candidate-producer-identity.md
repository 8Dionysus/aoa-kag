# AOA-KAG-D-0045 Budget Receipt Candidate and Producer Identity

## Index Metadata

- Decision ID: AOA-KAG-D-0045
- Original date: 2026-08-24
- Surface classes: schema contract, validation guard, generated budget receipt
- KAG surfaces: repo-local family budget receipt, candidate seal, producer action identity
- Source lanes: aoa-kag, provider repositories, abyss-stack owner-family consumers
- Guard families: content identity, producer provenance, self-reference safety, fail-closed budget admission
- Posture: superseded

`AOA-KAG-D-0046` supersedes the producer allowlist, broad receipt-prefix
exclusion, and unstaged source-epoch assumptions recorded here. This file
remains the historical rationale for the first v2 identity-bound receipt.

## Context

The original repo-local family budget receipt bound a resolved base reference
and generated family digest, but it did not bind the candidate whose generated
delta was measured or the procedure and action that produced it. A free-text
reason and approver label cannot recover either identity. A receipt copied to a
different source candidate could therefore retain the same apparent budget
exceedance while changing the material being admitted.

The receipt itself is generated output under the family receipt directory. Any
identity that includes the containing candidate tree or producer commit must
therefore account for the fact that publishing the receipt changes that tree
or commit.

## Decision

Budget receipts use
`aoa-repo-local-kag-budget-receipt-v2`. At the owner validator boundary a
receipt is accepted only when all of these independently match the current
candidate and executing owner procedure:

- the exact resolved base commit, measured family digest, and source snapshot;
- a domain-separated SHA-256 canonical file-inventory seal over the current
  Git worktree's tracked and non-ignored untracked candidate files; regular
  file permission bits are normalized to Git-compatible `0644` or `0755`
  while executable intent remains part of the identity; and
- a content-addressed producer identity containing the fixed owner procedure
  file set, their bytes and Git blob identities, plus the exact composite
  action blob.

The candidate seal excludes only
`kag/receipts/index_family_budget/`, because the receipt projection is the
object being published. The exclusion is explicit in the candidate identity;
all other candidate files, including authored source and generated family
files, remain in the seal. The validator also checks the receipt's closed
field set and the published receipt schema.

Producer commit and tree references are deliberately not an authority in this
contract. For the `aoa-kag` self-owner they would create a receipt/commit fixed
point. The producer content seal and exact action Git blob provide the needed
producer identity without that cycle. The receipt's reason and approver remain
owner context and do not substitute for machine-checked identity.

## Options Considered

- Bind the receipt to the containing candidate commit or tree: rejected because
  publishing or replacing the receipt changes the same identity and creates a
  circular contract.
- Bind only a predecessor receipt or a two-phase commit transition: rejected
  because it adds mutable transition state and still does not identify the
  current source candidate at the acceptance boundary.
- Bind only the source snapshot, family digest, and base reference: rejected
  because those fields do not prove that the current candidate bytes or
  producer procedure are the ones measured.
- Bind the producer commit alone: rejected for the self-owner for the same
  cycle reason; a producer commit remains review context rather than receipt
  authority.
- Use the domain-separated candidate seal plus producer procedure/action
  content identities: chosen because it is reproducible before and after
  receipt publication, portable to downstream owner worktrees, and directly
  replayable by the validator.

## Rationale

The receipt authorizes one measured generated-budget exceedance; it does not
approve authored meaning, source quality, hosted CI, merge, release, runtime,
or human acceptance. The seal closes the candidate replay gap at the same
boundary that measures the generated delta. The producer identity closes the
procedure/action substitution gap while preserving the self-owner's
content-addressed generation model.

## Consequences

- A v1 receipt fails closed and must be regenerated through the current owner
  builder.
- Changing candidate source, generated family bytes, base binding, receipt
  family binding, or producer procedure/action bytes rejects the receipt.
- Receipt publication does not change the candidate seal, so the generated
  receipt can be committed atomically with the family it authorizes.
- Checkout-specific restrictive permission bits do not change the seal for the
  same Git candidate; executable intent and symlink identity remain bound.
- Hosted review, consumer regeneration, admission, deployment, runtime
  delivery, merge, and owner/human acceptance remain separate successor
  claims.

## Source Surfaces

- `schemas/repo-local-kag-budget-receipt.schema.json`
- `scripts/repo_local/portable_family.py`
- `scripts/repo_local/tiered_family.py`
- `scripts/generate_repo_local_kag_index.py`
- `scripts/repo_local_kag_gate.py`
- `.github/actions/repo-local-kag-index/action.yml`
- `tests/test_repo_local_kag_repository_indexes.py`
- `docs/validation/COMMAND_AUTHORITY.md`

## Validation

Run the focused budget receipt replay tests, schema-surface validation,
source-fast, the owner-family DAG, the generated lane, and the proportional
release checks. Record hosted PR checks separately; local generated and
source-fast results do not prove hosted admission or merge.
