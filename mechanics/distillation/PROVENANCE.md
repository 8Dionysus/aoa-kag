# Distillation Provenance

Start from this package's `README.md` and `PARTS.md`. Use provenance when a
lift route needs source-owner trace.

## Center source

- `Agents-of-Abyss/mechanics/distillation/README.md`
- `Agents-of-Abyss/mechanics/distillation/PARTS.md`

## KAG source surfaces

- `mechanics/distillation/parts/technique-lift/docs/technique-lift-pack.md`
- `mechanics/distillation/parts/tos-text-chunk-map/docs/tos-text-chunk-map.md`
- `mechanics/distillation/parts/tos-route-lift/docs/tos-zarathustra-route-pack.md`
- `mechanics/boundary-bridge/parts/tos-retrieval-axis/docs/tos-zarathustra-route-retrieval-pack.md`
- matching manifests, schemas, examples, generated outputs, builders, validators, and tests.

## Moved Root Families

- `docs/TECHNIQUE_LIFT_PACK.md` -> `mechanics/distillation/parts/technique-lift/docs/technique-lift-pack.md`
- `manifests/technique_lift_pack.json` -> `mechanics/distillation/parts/technique-lift/manifests/technique_lift_pack.json`
- `schemas/technique-lift-pack*.schema.json` -> `mechanics/distillation/parts/technique-lift/schemas/`
- `generated/technique_lift_pack*.json` -> `mechanics/distillation/parts/technique-lift/generated/`
- `docs/TOS_TEXT_CHUNK_MAP.md` -> `mechanics/distillation/parts/tos-text-chunk-map/docs/tos-text-chunk-map.md`
- `manifests/tos_text_chunk_map.json` -> `mechanics/distillation/parts/tos-text-chunk-map/manifests/tos_text_chunk_map.json`
- `schemas/tos-text-chunk-map*.schema.json` -> `mechanics/distillation/parts/tos-text-chunk-map/schemas/`
- `examples/tos_text_chunk_map.example.json` -> `mechanics/distillation/parts/tos-text-chunk-map/examples/tos_text_chunk_map.example.json`
- `generated/tos_text_chunk_map*.json` -> `mechanics/distillation/parts/tos-text-chunk-map/generated/`
- `docs/TOS_ZARATHUSTRA_ROUTE_PACK.md` -> `mechanics/distillation/parts/tos-route-lift/docs/tos-zarathustra-route-pack.md`
- `docs/TOS_RAW_TABLE_INTAKE_HOLD.md` -> `mechanics/distillation/parts/tos-route-lift/docs/tos-raw-table-intake-hold.md`
- `manifests/tos_zarathustra_route_pack.json` -> `mechanics/distillation/parts/tos-route-lift/manifests/tos_zarathustra_route_pack.json`
- `schemas/tos-zarathustra-route-pack*.schema.json` -> `mechanics/distillation/parts/tos-route-lift/schemas/`
- `examples/tos_zarathustra_route_pack.example.json` -> `mechanics/distillation/parts/tos-route-lift/examples/tos_zarathustra_route_pack.example.json`
- `generated/tos_zarathustra_route_pack*.json` -> `mechanics/distillation/parts/tos-route-lift/generated/`

## Active part provenance

- `mechanics/distillation/parts/technique-lift/` owns focused technique lift
  operation validation for AOA-K-0001 through AOA-K-0004.
- `mechanics/distillation/parts/tos-text-chunk-map/` owns focused chunk-map
  operation validation for AOA-K-0005.
- `mechanics/distillation/parts/tos-route-lift/` owns focused route-pack lift
  validation for AOA-K-0010.
- Part-owned Distillation artifact families should not remain active in root
  technical districts unless a separate root-publication/proxy exception is
  recorded.
- `scripts/kag_generation.py` and `scripts/validate_kag.py` remain root
  compatibility/read-model entrypoints for generated parity.

No package-local `legacy/` route is active yet.
