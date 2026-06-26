# AGENTS.md

## Applies to

`scripts/generation/`.

## Role

This package contains the implementation modules for deterministic KAG
generation. `scripts/generate_kag.py` is the CLI entrypoint and
`scripts/kag_generation.py` is the compatibility facade.

## Function Map

| Surface | Function |
| --- | --- |
| `context.py` | repo roots, path constants, artifact identities, and static generation context |
| `common.py` | JSON/text helpers, path checks, list normalization, and shared payload utilities |
| `source_refs.py` | source-owned export, sibling repo, and Tree-of-Sophia source reference loading |
| `registry.py` | KAG registry payload construction |
| `technique.py` | technique-lift payload construction |
| `tos.py` | Tree-of-Sophia chunk, route, and retrieval payload construction |
| `markdown.py` | bounded markdown block extraction for source-derived snippets |
| `handoff.py` | reasoning-handoff payload construction |
| `federation.py` | federation export, spine, and cross-source projection payload construction |
| `regrounding.py` | return-regrounding payload construction |
| `governance.py` | KAG maturity governance payload construction |
| `consumer.py` | tiny-consumer bundle and counterpart exposure review payload construction |
| `writer.py` | generated output orchestration and output path contract |
| `__init__.py` | package re-export surface for the compatibility facade |

## Boundaries

Generation modules read repo-local manifests, schemas, docs, and allowed
source-owned sibling exports. They write only through `writer.py` and the
`scripts/generate_kag.py` entrypoint.

Keep builders deterministic, repo-relative, and source-owned. Do not add hidden
network calls, ambient credentials, local-only paths, or source-authoritative
claims to generated payloads.

## Route

Use `docs/validation/script_inventory.json` for the machine-readable generation
surface map. Use `generated/AGENTS.md` for generated-output boundaries.

## Validation

```bash
python -m unittest tests.test_kag_generation tests.test_script_topology
python scripts/ci_gate.py --mode generated
```
