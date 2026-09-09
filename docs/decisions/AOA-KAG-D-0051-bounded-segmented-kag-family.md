# Bounded Segmented KAG Family

## Index Metadata

- Decision ID: AOA-KAG-D-0051
- Original date: 2026-09-09
- Surface classes: KAG source-home, schema contract, generated projection, validation guard
- KAG surfaces: segmented repository-local family, deterministic partitioning, compatibility assembly, migration boundary
- Source lanes: aoa-kag, owner-family consumers, Tree-of-Sophia repository-local KAG
- Guard families: source-owned authority, content identity, bounded reads, explicit provider pin, rollback
- Posture: proposed owner contract

Status: proposed owner contract, implemented in `segmented_family.py`

## Decision

An owner whose canonical repository family exceeds the v3/v4 materialised
48 MiB surface may publish a segmented v1 family.  The segmented builder uses
the same canonical portable rows and stable record keys, but writes directly to
independently addressable JSONL segments.  It never builds a complete v3 or v4
family as an intermediate artifact.

Each segment has a deterministic hash range, byte limit, record count and
content digest.  The control manifest has separate source, producer, candidate,
and family identities.  A complete compatibility view is an explicit assembly,
not the storage contract.  Bounded readers must select and verify one segment at
a time under `request_bytes_max`; a reader that cannot prove the budget fails
closed.

## Compatibility and migration

v3 and v4 readers do not implicitly consume this family.  The manifest declares
an explicit provider pin and a dual-read migration from either predecessor.
Rollback is selection of the last-good control manifest by digest; it does not
delete new segments or rewrite source history.  Existing v3/v4 consumers remain
valid when their provider is pinned to a matching predecessor.  A provider that
supports segmented v1 must verify the schema, family digest, source snapshot,
segment digests, record counts, and request/part budgets before returning rows.

The legacy 48 MiB ceiling remains a compatibility limit.  It is not silently
raised.  The segmented family instead bounds each independently read part while
declaring a larger logical-corpus ceiling and a finite control-plane budget.

## Limits

The default part limit is 16 MiB and the default one-request limit is 4 MiB;
both are configurable only within the legacy owner hard ceiling.  The current
non-streaming reader additionally requires each materialised JSONL segment to
fit the request limit; a future streaming reader needs its own ABI.  A logical
family is rejected above the declared 8 GiB v1 ceiling.  These are admission
limits, not performance claims; owner-specific latency and storage evidence
must be measured by the consumer route.
