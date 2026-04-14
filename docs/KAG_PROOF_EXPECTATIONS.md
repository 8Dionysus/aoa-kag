# KAG Proof Expectations

This note records the bounded claims that KAG-derived families expect the proof
layer to check.

It does not claim those proofs are already complete.
It names the right next proof lane so `aoa-kag` does not absorb verdict meaning.

## Core rule

`aoa-kag` may name proof expectations.
`aoa-evals` owns whether those expectations are satisfied.

## Family-level expectations

| KAG family | bounded claim to prove elsewhere | current proof anchors | proof gap if anchors are not enough |
| --- | --- | --- | --- |
| `AOA-K-0001` / `technique_section_lift` | stable source section lifts preserve authored meaning and stay source-first | `aoa-evals/bundles/aoa-local-text-contract-fit/EVAL.md` | dedicated proof for section-lift fidelity rather than broader local text fit |
| `AOA-K-0002` / `metadata_spine_projection` | identity and entry-spine lifts stay owner-fit and do not become routing ownership | `aoa-evals/bundles/aoa-owner-fit-routing-quality/EVAL.md` | dedicated proof for metadata-spine owner fit rather than broader routing-quality checks |
| `AOA-K-0003` / `bounded_relation_view` | lifted direct relations remain bounded hints and do not widen into graph sovereignty | `aoa-evals/bundles/aoa-local-text-contract-fit/EVAL.md`, `aoa-evals/bundles/aoa-candidate-lineage-integrity/EVAL.md` | direct proof that lifted relation hints never widen into hidden graph claims |
| `AOA-K-0004` / `provenance_note_view` | provenance handles remain returnable anchors and do not become authored memory or canon | `aoa-evals/bundles/aoa-return-anchor-integrity/EVAL.md` | dedicated proof for provenance-note recall fidelity rather than broader return-anchor checks |
| `AOA-K-0005` / `tos_text_chunk_map` | chunk-level lifts preserve source-linked retrieval units without source replacement | `aoa-evals/bundles/aoa-local-text-contract-fit/EVAL.md` | direct proof that chunk segmentation preserves source-first re-entry and does not widen into graph claims |
| `AOA-K-0007` / `tos_retrieval_axis_pack` | retrieval-axis returns stay bounded, source-linked, and bridge-aware without ranking or routing ownership | `aoa-evals/bundles/aoa-return-anchor-integrity/EVAL.md`, `aoa-evals/bundles/aoa-memo-recall-integrity/EVAL.md`, `aoa-evals/bundles/aoa-memo-contradiction-integrity/EVAL.md` | dedicated proof for bridge-axis fidelity across larger ToS families |
| `AOA-K-0006` / `cross_source_node_projection` | one-hop projections preserve primary-versus-supporting provenance and do not imply identity | `aoa-evals/bundles/aoa-owner-fit-routing-quality/EVAL.md`, `aoa-evals/bundles/aoa-candidate-lineage-integrity/EVAL.md` | direct proof for non-identity projection discipline at the KAG layer |
| `AOA-K-0009` / `federation_spine` | source-owned export entry remains derivative, bounded, and owner-fit for downstream routing | `aoa-evals/bundles/aoa-owner-fit-routing-quality/EVAL.md`, `aoa-evals/bundles/aoa-return-anchor-integrity/EVAL.md` | direct proof that wider donor activation still preserves owner-fit and source-first re-entry |
| `AOA-K-0010` / `tos_zarathustra_route_pack` | canonical route-local lifts preserve ToS authority and do not replace authored tree surfaces | `aoa-evals/bundles/aoa-local-text-contract-fit/EVAL.md` | route-pack-specific proof for canonical relation fidelity and bounded family shape |
| `AOA-K-0011` / `tos_zarathustra_route_retrieval_pack` | family-level handles stay subordinate to the ToS tiny-entry route and do not become a new starter or routing authority | `aoa-evals/bundles/aoa-return-anchor-integrity/EVAL.md`, `aoa-evals/bundles/aoa-owner-fit-routing-quality/EVAL.md` | direct proof that subordinate adjunct posture survives downstream consumer use |
| `reasoning_handoff_pack` | runtime-facing KAG returns remain guidance-to-source and do not absorb routing, memory, or proof ownership | `aoa-evals/bundles/aoa-long-horizon-depth/EVAL.md`, `aoa-evals/bundles/aoa-tool-trajectory-discipline/EVAL.md` | dedicated proof for KAG handoff guardrail adherence under wider runtime scenarios |
| `return_regrounding_pack` | degraded callers can return to stronger owner refs without false continuation or owner confusion | `aoa-evals/bundles/aoa-return-anchor-integrity/EVAL.md`, `aoa-evals/bundles/aoa-antifragility-posture/EVAL.md`, `aoa-evals/bundles/aoa-stress-recovery-window/EVAL.md` | direct proof for regrounding accuracy across multiple degraded surface families |

## Planned-only family

`AOA-K-0008` remains `planned_contract_only`.

Before any live payload exists, the minimum proof expectation would be:

- one owner-fit proof lane for non-identity discipline
- one return-anchor or stress-recovery lane for safe fallback
- one explicit proof that counterpart projection does not imply identity,
  routing authority, or canon activation

Until those proof lanes are named and owner inputs are stronger, contract-only
is the honest posture.
