# Source Policy

This document records how authoritative sources and derived KAG surfaces should relate.

## Source-first rule

All KAG surfaces in this repository should remain derived from authoritative upstream sources.

Examples of authoritative sources include:
- `aoa-techniques` markdown bundles
- `aoa-skills` markdown bundles and manifests
- `aoa-evals` markdown bundles and manifests
- `aoa-memo` memory-layer sources
- `aoa-playbooks` scenario-layer sources
- authored Tree of Sophia texts and structured surfaces

## Derived-not-authored rule

A KAG surface may normalize, lift, or project the source.
It should not quietly become a hand-authored replacement for the source.

## Provenance rule

Every meaningful KAG surface should preserve enough provenance to answer:
- what source class fed this?
- what source repository or corpus fed this?
- what kind of transformation happened?

## Bounded readiness rule

If a KAG surface claims graph or retrieval readiness, that claim should stay bounded.
Do not imply a full graph platform when only direct lifts or bounded projections exist.

## Framework-neutral rule

Framework adapters should remain downstream.
HippoRAG, LlamaIndex, and future systems may consume the KAG layer, but they should not define the layer's source policy.

## Compact rule

The KAG layer should make derived knowledge surfaces portable without weakening source-of-truth discipline.
