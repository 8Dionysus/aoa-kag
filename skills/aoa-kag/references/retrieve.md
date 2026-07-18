# Retrieve mode

Use this mode to locate and read one or more canonical owner sources or one
complete owner capability contract.

1. If owners, record classes, strategies, or runtime bounds are unknown, call
   `kag_discover` once with `detail=compact`. Inspect its page and traversal
   bounds and projection timestamp. Do not return its catalog as the answer or
   treat target state `current` as current owner-ref parity.
2. Call `kag_search` with `strategy=auto`, `detail=compact`, and a small limit.
   Apply an owner, kind, path, or path-prefix filter only when the request or
   discovery supplies that signal. Stay within discovered bounds.
3. If `auto` selects `exact` and returns `empty`, refine once with `lexical` or
   `hybrid` plus the strongest verified owner or path signal. If results are
   noisy, refine once using that signal. Do not broaden indefinitely.
4. Select the smallest result set that can answer the request. Preserve its
   qualified ID, owner, URI, source refs, digest, freshness, trust, access,
   projection, and trace ID.
5. Call `kag_read` on every selected owner resource whose meaning supports the
   answer. A snippet, ranking, generated index row, or graph node alone is
   insufficient.
6. Inspect the read payload's `owner_return_route`, source refs, freshness,
   digests, and any commit or ref. If the source declares `superseded_by` or an
   equivalent successor, follow it and read the current owner source before
   relying on the claim.
7. If the route is degraded, fallback-backed, stale, source-unavailable, or
   ambiguous, call `kag_explain` with the trace ID. Return
   `partial_snapshot` unless current owner ref and digest parity are proven.
   A later `kag_read` status of `ok` does not erase earlier degradation.
8. Classify the owner source as `canonical_verified`, `snapshot_only`, or
   `source_unavailable`; keep every missing ref or digest explicit. Return the
   source handles and hand substantive work to their owners.

## Skill or capability retrieval

For a skill, read its canonical `SKILL.md`, `references/contract.yaml`, and
only the conditional procedure required by the request. Return every capability
field required by the common output ABI.

If KAG cannot return the canonical owner ref, path, digest, applicability,
input/output ABI, tools, effects, lifecycle health, relations,
compatibility/conflicts, source handle, or binding availability, return
`partial_contract` and `execution_posture: not_executable`. Do not fill missing
fields from a graph node, generated catalog, or similarly named legacy skill.
Use `empty` only when no capability identity survives one bounded refinement.
