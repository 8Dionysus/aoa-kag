# Source-Owned Export Dependencies

This document records the current source-owned export dependency contract for
`aoa-kag`.

It keeps the current external tiny-export assumptions explicit instead of
leaving them hidden inside generator or validator code.

## Purpose

The current contract is intentionally narrow:

- declare exactly which external source-owned exports the current experimental
  KAG surfaces recognize as invariant-backed donors
- keep expected owner, kind, object id, and entry surface explicit
- keep live consumption separate from donor activation so widening remains
  reviewable

## Current pilot dependencies

The current bounded contract depends on:

- `aoa-techniques/generated/kag_export.min.json`
- `Tree-of-Sophia/generated/kag_export.min.json`
- `aoa-memo/mechanics/consumer-handoff/parts/kag-source-export/generated/kag_export.min.json`

`aoa-memo/mechanics/consumer-handoff/parts/kag-source-export/generated/kag_export.min.json` is now listed as an invariant-backed
donor export, but its `consumed_by` list is intentionally empty in this wave.
That keeps the donor contract explicit without pretending the live generated KAG
surfaces already consume it.
The donor object's source-memory relation points at
`aoa-memo/memo/objects/bridges/2026/tos-lineage-kag-candidate/object.json`, so
KAG can treat the memo donor as reviewed corpus while keeping the bridge
teaching fixture available only as support evidence.

`aoa-memo/mechanics/readiness-boundary/docs/MEMORY_READINESS_BOUNDARY.md` is a stronger memo-owned boundary
for future durable-consequence, retention, recall, and live-ledger pressure.
KAG may point back to that owner ref from regrounding surfaces, but it must not
treat the memo donor export as scar proof, retention proof, live memory-ledger
readiness, graph truth, or routing activation.

## Reviewed memo donor consumer boundary

`aoa-kag` is a read-only memory consumer in this route.

The memo donor is consumed through reviewed `aoa-memo` object ids, provenance,
lifecycle, and generated read models. Its active source-kind expectation is
`source_kind: reviewed_corpus`, with
`memo.bridge.2026-03-23.tos-lineage-kag-candidate` as the explicit object id
and `generated/memory-objects/memory_object_capsules.json` as the entry surface.

`aoa_memo_brief`, `aoa_memo_search`, and `aoa_memo_pending_exports` may help an
agent inspect reviewed recall context, central object status, and local-port
pressure. `aoa_memo_validate_port`, `aoa_memo_validate_candidate`, and
`aoa_memo_landing_plan` are access-plane or dry-run evidence only. They do not
make the donor live in the KAG spine, and they do not authorize `aoa-kag` to
write local memo candidates, reviewed-intake exports, or durable memory.

Session evidence remains `.aoa` or source-owner evidence until a reviewed
`aoa-memo` intake route lands it. KAG may derive graph-ready handles from a
reviewed donor export only when provenance, lifecycle, source refs, and
non-identity boundary stay visible. It must not treat the donor as normalized
graph truth, routing authority, proof, or memory ownership.

Those dependencies are declared in
`manifests/source_owned_export_dependencies.json`.

Live donor visibility is now declared separately in
`manifests/federation_export_registry.json`.
That registry decides whether a donor is only registry-visible or also live in
the spine and downstream routing.

They also anchor the first `source_export_reentry` mode in
`generated/return_regrounding_pack.min.json`.
Memo memory readiness is deliberately not part of that source-export reentry
mode while the memo donor stays registry-visible only.

## What the contract keeps

Each dependency keeps:

- one stable `dependency_id`
- the source-owned `repo` and `path`
- the expected `owner_repo`, `kind`, and `object_id`
- the required top-level export fields
- the expected `entry_surface`
- the current live `consumed_by` surface ids inside `aoa-kag`

## What this contract does not do

This contract does not:

- replace source-owned export doctrine in neighboring repositories
- claim that every declared donor is already live in the spine
- widen `aoa-kag` into source ownership

## Regeneration posture

Use:

```bash
python scripts/release_check.py
```

If you only need regeneration and drift validation, use:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
```
