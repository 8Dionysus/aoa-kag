# AGENTS.md

## Applies to

This card applies to `kag/` and every nested path until a nearer card narrows
the lane.

## Role

`kag/` is the KAG source home and local provider home for `aoa-kag`.

It owns the operating route for repo-local KAG subtrees: manifest shape,
portable record classes, source refs, owner-return routes, validation receipts,
registry/composition readiness, and MCP-readable resource shape.

## Operating Card

| Field | Route |
| --- | --- |
| input | local subtree schema, example packet, readiness matrix, provider records |
| output | active local provider packet, protocol docs, validation receipt, registry/composition inputs |
| owner | `kag/AGENTS.md`, `kag/README.md`, `kag/source_home.manifest.json`, `kag/manifest.json` |
| next route | source surface -> local provider record -> readiness matrix -> registry/composition -> runtime/MCP consumer |
| validation | local subtree validator, source-fast lane, touched sibling owner checks |

## Source Routes

- `schemas/local-kag-subtree.schema.json`
- `examples/local_kag_subtree.example.json`
- `manifests/local_kag_readiness.json`
- `scripts/validators/local_kag_subtree.py`
- `tests/test_validate_kag.py`

## Provider Records

| Surface | Role |
| --- | --- |
| `manifest.json` | local provider manifest |
| `nodes/` | source-linked contract and readiness nodes |
| `edges/` | bounded relation records between local nodes |
| `indexes/` | lightweight inventory records |
| `projections/` | MCP/resource-facing compact views |
| `receipts/` | validation and freshness receipts |

## Boundary Routes

| Pressure | Route |
| --- | --- |
| authored meaning in a source repository | owning source repository |
| proof verdicts and scoring | `aoa-evals` |
| durable memory truth | `aoa-memo` |
| dispatch and route authority | `aoa-routing` |
| runtime graph, vector, cache, worker, or deployment state | `abyss-stack` and `.aoa` runtime stores |
| portable KAG protocol, registry, composition, and provider validation | `aoa-kag` |

## Validation

For this home:

```bash
python -m unittest tests.test_kag_home tests.test_validate_kag
```

For source-fast coverage:

```bash
python scripts/ci_gate.py --mode source-fast
```

For provider-ready sibling checkouts, run each touched owner route after the
`aoa-kag` validator names the provider packet clean.

## Closeout

Report changed provider records, readiness rows, registry/composition surfaces,
validation run, sibling checks, and the next consumer route for `aoa-kag-mcp`.
