# Boundary Bridge Parts

This file is the active map for KAG boundary-bridge part pressure.

## What a part means here

A part is a bounded crossing with named sides, owner roles, bridge mode,
allowed outputs, non-transfer rule, and validation. It should own only the
artifacts that are clearer inside the bridge boundary than in root KAG
technical districts.

## Candidate part pressure

| Candidate part | Use when | Current route |
| --- | --- | --- |
| `source-owned-export` | KAG consumes source-owned donor exports. | `mechanics/boundary-bridge/parts/source-owned-export/docs/source-owned-export-dependencies.md`, source export manifests, generated federation registry. |
| `tos-retrieval-axis` | ToS source routes need bounded retrieval handles. | ToS retrieval manifests, schemas, examples, generated packs, and docs. |
| `counterpart-edge` | KAG exposes support, tension, calibration, or analogy without identity. | active part route in `parts/counterpart-edge/`. |
| `cross-source-projection` | one-hop node-like projection needs source-first return. | cross-source node projection manifest, schema, generated output, and tests. |
| `federation-spine` | source-owned exports compose into a bounded federation spine. | federation spine manifest, schema, generated output, and docs. |
| `tiny-consumer-bundle` | the current bounded consumer chain needs a compact generated bundle. | active part route in `parts/tiny-consumer-bundle/`. |

## Active part routes

| Active part | Owns | Validation |
| --- | --- | --- |
| `source-owned-export` | focused source-owned export dependency, memo donor registry-only, and owner-primary ingress checks | `parts/source-owned-export/VALIDATION.md` |
| `tos-retrieval-axis` | AOA-K-0007 and AOA-K-0011 retrieval handle bridge contracts | `parts/tos-retrieval-axis/VALIDATION.md` |
| `cross-source-projection` | AOA-K-0006 one-hop projection and non-identity boundary contracts | `parts/cross-source-projection/VALIDATION.md` |
| `federation-spine` | AOA-K-0009 source-owned export spine and artifact identity contracts | `parts/federation-spine/VALIDATION.md` |
| `counterpart-edge` | AOA-K-0008 planned-only counterpart contract and example refs | `parts/counterpart-edge/VALIDATION.md` |
| `tiny-consumer-bundle` | bounded consumer-chain bundle and deferred counterpart posture | `parts/tiny-consumer-bundle/VALIDATION.md` |

The current active counterpart exposure review remains audit-owned by
`mechanics/audit/parts/exposure-review/`.
