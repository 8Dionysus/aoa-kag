# Additive Fail-Closed Impact Routing

## Index Metadata

- Decision ID: AOA-KAG-D-0022
- Original date: 2026-07-29
- Surface classes: validation guard, GitHub landing, command authority, impact classifier, required summary
- KAG surfaces: local integrity, owner portable family, OS-wide provider coverage, generated fixed point
- Source lanes: aoa-kag, provider registry
- Guard families: source-fast stop-line, owner-family parity, fail-closed impact, owner completeness, trust admission, typed skip
- Posture: accepted

## Context

AOA-KAG-D-0021 removed repeated OS-wide coverage builds and separated local
validation from the explicit provider audit. A stable release still performs a
complete 23-owner audit, which is necessary for changes that can alter provider
membership, shared schemas, portable-family behavior, federation inputs,
artifact trust, budgets, compatibility assembly, or release topology.

Running that audit for every owner-authored documentation, quest, skill,
mechanic, or stats change makes CI cost independent of impact. Selective
execution is safe only if it cannot replace the always-required local proofs
and if an unknown path escalates rather than receiving a cheap default.

## Decision

Every pull request runs the repository-local `source-fast` lane and the
repo-local KAG family action, including full/incremental family parity and the
exact seven-file compatibility assembly. Impact classification is additive:
it decides only whether the full OS-wide release audit must also run.
The local validator receives the seven pinned source donors it actually reads,
including `aoa-sdk` for source-pinned owner-review schema verification, plus
the pinned `aoa-stats` owner; it does not materialize the other fourteen
provider repositories or the private session-memory checkout.

The classifier uses versioned rules stored with validation command authority.
Provider membership and registry inputs, shared schemas and KAG ABI surfaces,
builders/loaders/validators, federation or projection inputs, generated
OS-wide coverage, trust artifacts, receipts, budgets, pack/blob paths,
validation topology, and release topology require the full audit. A mixed
change inherits its strongest route. An invalid, empty, unavailable, or
unclassified change set also requires the full audit.

Only explicitly allowed owner-authored surfaces and their self portable-family
manifest/shards may receive the owner-local route. Generated self-family files
do not prove their own correctness: the always-required owner-family action
must reproduce them, validate their budgets, compare full and incremental
results, and assemble compatibility output.

The stable `Repo Validation` context is a required summary. It reports the
local proofs as `verified` and reports the OS-wide audit as either `verified`
or `correctly-not-required`. A skipped required audit, a skipped local proof,
an unexpected audit result, or a non-pull-request event without a full audit
fails the summary. Pushes to `main` and manual runs always require the full
audit; scheduled compatibility proof supplements this route and does not
replace pre-merge classification.

Workflow concurrency may cancel only a superseded head of the same pull
request. Its group identity is workflow-qualified and stable by pull-request
number; push and manual runs receive unique run identities. The controller's
cancellation switch is unconditional because isolation is carried entirely by
that group identity, avoiding event-condition ambiguity without widening the
cancellation scope. Cancellation is a scheduling result, not proof: only the
replacement head's complete typed summary may satisfy landing. Main, manual,
other pull-request, and scheduled compatibility runs remain independent.

## Options Considered

- Keep the full audit on every change: simplest and strongest operationally,
  but retains high runner cost for changes that cannot affect sibling proof.
- Let an owner-fast job replace source-fast: cheaper, but loses repository
  tests, route checks, decision guards, and other local blocking evidence.
- Default unknown paths to owner-local: increases the apparent hit rate while
  turning classifier drift into silent proof loss.
- Always run local and owner-family proof, then allow only explicit safe paths
  to omit the additional full audit: preserves the local stop-line and makes
  uncertainty expensive rather than trusted.

## Rationale

Impact routing is a proof-plan decision, not a proof result. Keeping
`source-fast` and owner-family parity outside classifier discretion prevents a
classification bug from removing the minimum landing evidence. A small
owner-local allow surface is inspectable, while full-audit rules and an
unknown-path fallback preserve fail-closed behavior as the repository grows.

Typed summary states prevent a skipped job from masquerading as a successful
audit. Main and compatibility runs retain complete independent coverage, but
they are redundancy and drift detection rather than substitutes for a required
high-impact pull-request audit.

## Consequences

- Owner-local pull requests avoid materializing all provider repositories and
  omit the OS-wide release audit after local and self-family proof succeeds.
  Their local job checks out only seven pinned source donors plus `aoa-stats`.
- High-impact, mixed, unknown, malformed, or unprovable changes retain the full
  provider audit and generated fixed point.
- Classifier, workflow, command-authority, schema, test, decision, trust,
  receipt, and budget changes classify themselves as full-audit changes.
- New safe surfaces require an explicit reviewed allow rule; repository growth
  does not silently widen the cheap route.
- Pack and opaque blob additions under an otherwise owner-local tree still
  require the full route, and trusted import code is never owner-local.
- The classifier receipt and required summary are machine-readable execution
  evidence. They do not become owner truth or prove the underlying KAG
  invariants by themselves.
- A newer head stops obsolete work for the same pull request without changing
  which proofs the newer head must complete. It cannot cancel main, manual,
  another pull request, or the compatibility canary.
- Bounded parallel owner execution and cross-run caching remain separate
  decisions with separate equivalence and pressure evidence.

## Source Surfaces

- `config/validation_lanes.json`
- `.github/workflows/repo-validation.yml`
- `.github/workflows/compatibility-canary.yml`
- `.github/actions/repo-local-kag-index/action.yml`
- `docs/validation/COMMAND_AUTHORITY.md`
- `docs/validation/SCRIPT_TOPOLOGY.md`
- `scripts/impact_routing.py`
- `scripts/validation_lanes.py`
- `scripts/ci_gate.py`
- `scripts/release_check.py`
- `tests/fixtures/impact_routing_corpus.json`
- `tests/test_impact_routing.py`
- `tests/test_repo_validation_workflow.py`
- `tests/test_validation_command_authority.py`

## Validation

Regenerate and validate decision indexes. Run the positive owner-local and
negative fail-closed classifier corpus, Git rename and unprovable-ref cases,
required-summary state tests, workflow topology tests, command-authority tests,
the complete source-fast lane with only its eight pinned external dependencies
and all unrelated provider roots made unavailable, and one full release gate
on the exact pinned providers. Compare proof payloads on identical inputs
rather than treating a digest change caused by this repository's new family as
proof drift.

For concurrency changes, also push two successive heads to one test pull
request after the first full audit has started. Confirm that the older run is
cancelled, the replacement head completes all required proofs, and unrelated
main, manual, pull-request, and compatibility runs remain unaffected.
