# KAG Layer Boundaries

This document records the most important ownership boundaries for `aoa-kag`.

## Rule 1: KAG owns derived knowledge substrate, not authored source meaning

`aoa-kag` should own KAG-layer meaning such as:
- lifted knowledge units
- normalized node and edge projections
- provenance-aware derived surfaces
- retrieval-ready section and chunk maps
- framework-neutral substrate posture

It should not become the default home for authored source material.

## Rule 2: KAG is not source truth

A lifted or normalized surface may be useful.
That does not make it the authored source of meaning.

Authored source meaning still belongs to the originating repository or corpus.

## Rule 3: KAG is not proof

A graph-ready or retrieval-ready surface may support reasoning.
That does not make it bounded proof.

Proof still belongs to `aoa-evals`.

## Rule 4: KAG is not routing

A derived knowledge surface may support navigation.
That does not make the KAG layer the owner of dispatch.

Navigation still belongs to `aoa-routing`.

## Rule 5: KAG is not memory truth

A provenance-aware KAG surface may help recall.
That does not make the KAG layer the owner of memory objects or memory truth.

Memory still belongs to `aoa-memo`.

## Rule 6: framework adapters stay downstream

HippoRAG, LlamaIndex, and future consumers may sit on top of `aoa-kag`.
They should not define the ontology of the KAG layer itself too early.

## Rule 7: keep KAG surfaces reviewable

If KAG surfaces become giant opaque graph machinery with unclear provenance, the layer will stop being trustworthy.
Compactness and explicit source linkage matter.

## Rule 8: bridge returns stay derived and explicit

If `aoa-kag` returns lineage-aware or conflict-aware retrieval bundles to AoA, those surfaces should stay explicitly derived.

They should guide AoA toward stronger authored sources rather than claiming to be the new home of truth.

## Rule 9: counterpart mappings stay suggestive and non-identity

If `aoa-kag` materializes counterpart edges between ToS concepts and AoA operational forms, those edges stay derived and optional.

They should not:
- claim philosophical proof
- imply every concept needs an operational twin
- rewrite authored operational meaning into KAG-owned doctrine

## Compact rule

`aoa-kag` should help AoA and ToS lift knowledge without letting the derived layer quietly replace the sources that feed it.
