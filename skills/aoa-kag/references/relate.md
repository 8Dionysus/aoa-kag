# Relate mode

Use this mode when the task asks how owner-qualified objects connect, whether
their contracts can compose, or which downstream surfaces a change may affect.

1. If endpoint IDs are absent, use one bounded `kag_search` per endpoint and
   read the canonical owner resource for each selected endpoint. Follow any
   explicit supersession before fixing the endpoint identity.
2. Prefer an artifact or entity ID that participates in owner relations.
   Anchors are evidence locators and may have no traversable edges. If one
   verified anchor returns no path, retry once with its exact
   `source_record_ids`; do not broaden into a new search.
3. Call `kag_traverse` with the verified `source_ids`. Start at depth `1` or
   `2`; use a relation-kind filter when the request names the relation, and
   stay within the bounds returned by `kag_discover`.
4. Expand toward the maximum depth only when the shorter path is insufficient
   and the returned evidence justifies the expansion.
5. Preserve every endpoint, intermediate owner-qualified ID, relation kind,
   direction, evidence ref, and trace ID.
6. For compatibility or task-local composition, also read each owner contract
   and compare input/output ABI, effects, tool bindings, lifecycle, versions,
   trust, and explicit conflicts. A `produces`/`consumes` edge is only a
   candidate seam.
7. Use `kag_explain` when the path depends on degraded adapters, fallback
   projections, or source-unavailable owners. Keep such a result
   `partial_snapshot` and non-executable even when a later read succeeds.
8. If no evidence-bearing path is returned, report `empty`; do not substitute
   semantic similarity or co-occurrence.

Return an evidence-bearing relationship result. A path is not compatibility,
causality, impact completeness, or execution proof until the relevant owner
contracts independently establish the claim.
