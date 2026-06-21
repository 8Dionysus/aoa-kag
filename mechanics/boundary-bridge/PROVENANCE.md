# Boundary Bridge Provenance

Start from this package's `README.md` and `PARTS.md`. Use provenance when a
bridge needs source trace or owner-boundary review.

## Center source

- `Agents-of-Abyss/mechanics/boundary-bridge/README.md`
- `Agents-of-Abyss/mechanics/boundary-bridge/PARTS.md`
- `Agents-of-Abyss/mechanics/boundary-bridge/parts/derived-projection/README.md`
- `Agents-of-Abyss/mechanics/boundary-bridge/parts/non-identity-guard/README.md`

## KAG source surfaces

- `docs/BRIDGE_CONTRACTS.md`
- `mechanics/boundary-bridge/parts/federation-spine/docs/federation-spine.md`
- `mechanics/boundary-bridge/parts/counterpart-edge/docs/counterpart-edge-contracts.md`
- `mechanics/boundary-bridge/parts/cross-source-projection/docs/cross-source-node-projection.md`
- `mechanics/boundary-bridge/parts/source-owned-export/docs/source-owned-export-dependencies.md`
- matching manifests, schemas, examples, generated outputs, builders, validators, and tests.

## Moved Root Families

- `docs/TOS_RETRIEVAL_AXIS_PACK.md` -> `mechanics/boundary-bridge/parts/tos-retrieval-axis/docs/tos-retrieval-axis-pack.md`
- `docs/TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK.md` -> `mechanics/boundary-bridge/parts/tos-retrieval-axis/docs/tos-zarathustra-route-retrieval-pack.md`
- `manifests/tos_retrieval_axis_pack.json` -> `mechanics/boundary-bridge/parts/tos-retrieval-axis/manifests/tos_retrieval_axis_pack.json`
- `manifests/tos_zarathustra_route_retrieval_pack.json` -> `mechanics/boundary-bridge/parts/tos-retrieval-axis/manifests/tos_zarathustra_route_retrieval_pack.json`
- `schemas/tos-retrieval-axis-pack*.schema.json` -> `mechanics/boundary-bridge/parts/tos-retrieval-axis/schemas/`
- `schemas/tos-zarathustra-route-retrieval-pack*.schema.json` -> `mechanics/boundary-bridge/parts/tos-retrieval-axis/schemas/`
- `schemas/bridge-retrieval-surface.schema.json` -> `mechanics/boundary-bridge/parts/tos-retrieval-axis/schemas/bridge-retrieval-surface.schema.json`
- `schemas/bridge-envelope.schema.json` -> `mechanics/boundary-bridge/parts/tos-retrieval-axis/schemas/bridge-envelope.schema.json`
- `examples/tos_retrieval_axis*.json` -> `mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/`
- `examples/tos_zarathustra_route_retrieval_pack.example.json` -> `mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/tos_zarathustra_route_retrieval_pack.example.json`
- `examples/aoa_tos_bridge_envelope.example.json` -> `mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/aoa_tos_bridge_envelope.example.json`
- `generated/tos_retrieval_axis_pack*.json` -> `mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/`
- `generated/tos_zarathustra_route_retrieval_pack*.json` -> `mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/`

## Active part provenance

- `mechanics/boundary-bridge/parts/source-owned-export/` owns focused
  source-owned donor ingress validation: owner-primary source inputs, memo donor
  registry-only activation, and memo consumer stop-lines.
- `mechanics/boundary-bridge/parts/tos-retrieval-axis/` owns focused ToS
  retrieval bridge validation for AOA-K-0007 and AOA-K-0011.
- `mechanics/boundary-bridge/parts/cross-source-projection/` owns focused
  one-hop projection validation for AOA-K-0006 and its non-identity boundary.
- `mechanics/boundary-bridge/parts/federation-spine/` owns focused federation
  spine validation for AOA-K-0009, artifact identity, and counterpart exclusion.
- `mechanics/boundary-bridge/parts/counterpart-edge/` owns planned-only
  counterpart consumer contract docs, schemas, examples, and `AOA-K-0008`
  non-activation guardrails.
- `mechanics/boundary-bridge/parts/tiny-consumer-bundle/` owns the tiny bundle
  manifest, schemas, example, and generated read-model outputs for the current
  bounded consumer chain.
- `mechanics/boundary-bridge/parts/source-owned-export/` owns the
  source-owned export dependency docs, federation KAG readiness docs,
  federation export registry manifests, schemas, examples, and generated
  registry read-model outputs for the source-owned export part.
- Counterpart exposure review is currently audit-owned by
  `mechanics/audit/parts/exposure-review/`.
- `scripts/kag_generation.py` and `scripts/validate_kag.py` remain root
  compatibility/read-model entrypoints until a later split moves implementation
  ownership without changing their public lane role.

No package-local `legacy/` route is active yet.
