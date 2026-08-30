# AOA-KAG-D-0048 Portable Budget Producer Runtime Contract

## Index Metadata

- Decision ID: AOA-KAG-D-0048
- Original date: 2026-08-26
- Surface classes: schema contract, validation guard, generated budget receipt
- KAG surfaces: repo-local family budget receipt, producer runtime inputs, owner-family validation
- Source lanes: aoa-kag, owner-family validation
- Guard families: source-owned authority, reproducible execution contract, fail-closed budget admission
- Posture: accepted

`AOA-KAG-D-0047` remains current for AST closure, dynamic-import rejection,
and descriptor-confined receipt I/O. This decision supersedes only its
host-bound runtime-input representation.

## Context

The v3 producer identity recorded absolute checkout and temporary paths, the
exact interpreter binary, and installed dependency artifacts. Those values are
useful observations of one process, but they are not stable identity for the
same approved owner procedure in a fresh checkout. The committed receipt
therefore failed the hosted owner-family sentinel even though the source
closure, action, refs, and declared dependency versions were unchanged.

## Decision

Advance the producer manifest, runtime-input, and producer-identity contracts
to their portable v2/v4 forms. Bind receipt identity to:

- the reviewed AST import closure, schemas, manifest, and composite action
  bytes, including their Git blob identities;
- logical action and command values, exact history boundaries, output path,
  family mode, and artifact-root role; scheduler fan-out and job count are
  deliberately unbound because they change execution scheduling, not
  generated content;
- the declared dependency contract, while still requiring every required
  dependency to be installed at its declared version and every supported
  Python runtime to satisfy the declared minimum; and
- the two validator rollback switches whose values can change validation
  behavior.

Absolute repository, temporary, interpreter, and installed-package paths are
not semantic producer identity. Their fields carry stable logical descriptors
instead. Optional dependencies use `declared` state because their absence is
an admitted fallback, while required dependency availability and exact
versions remain fail-closed checks. History environment variables are not
captured a second time: the explicit action/command refs are the authority.

## Options Considered

- Commit a receipt from one runner and require every validator to use its
  paths and binaries: rejected because fresh hosted checkouts are approved
  execution environments, not the original machine.
- Drop all runtime binding: rejected because action values, history
  boundaries, validator rollback switches, required dependency versions, and
  source closure still need machine-checked identity.
- Bind only the current local package artifacts: rejected because wheel and
  interpreter paths and binaries vary across approved environments.
- Use logical descriptors plus required-version checks: chosen because it
  preserves the fail-closed semantic inputs while making the receipt
  reproducible across clean approved checkouts.

## Consequences

- Existing v1 and pre-portable identity receipts remain retained historical
  data and cannot authorize the current family; the current producer must
  regenerate its exact digest receipt.
- A changed required dependency version, unsupported Python runtime, action
  input, history boundary, validator rollback switch, local import, schema,
  action, or source epoch fails closed.
- A checkout relocation, runner temp relocation, or equivalent approved
  interpreter/package installation does not create false producer drift.
- Source/CI, generated parity, hosted admission, merge, release, runtime,
  delivery, closure, and owner/human acceptance remain separate claims.

## Source Surfaces

- `config/repo-local-kag-budget-producer.json`
- `schemas/repo-local-kag-budget-producer-manifest.schema.json`
- `schemas/repo-local-kag-budget-receipt.schema.json`
- `scripts/repo_local/portable_family.py`
- `tests/test_repo_local_kag_repository_indexes.py`
- `.github/actions/repo-local-kag-index/action.yml`

## Validation

Validate both producer and receipt schemas, run the portable runtime-contract
and receipt-replay regressions, regenerate the owner family, then record the
hosted owner-family and Repo Validation results separately from local proof.
