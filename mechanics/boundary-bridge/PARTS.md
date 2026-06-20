# Boundary Bridge Parts

This file is the active map for KAG boundary-bridge part pressure.

No part directories are active yet.

## What a part means here

A part is a bounded crossing with named sides, owner roles, bridge mode,
allowed outputs, non-transfer rule, and validation. It should own only the
artifacts that are clearer inside the bridge boundary than in root KAG
technical districts.

## Candidate part pressure

| Candidate part | Use when | Current route |
| --- | --- | --- |
| `source-owned-export` | KAG consumes source-owned donor exports. | `docs/SOURCE_OWNED_EXPORT_DEPENDENCIES.md`, source export manifests, generated federation registry. |
| `tos-retrieval-axis` | ToS source routes need bounded retrieval handles. | ToS retrieval manifests, schemas, examples, generated packs, and docs. |
| `counterpart-edge` | KAG exposes support, tension, calibration, or analogy without identity. | counterpart docs, schemas, examples, and exposure review surfaces. |
| `cross-source-projection` | one-hop node-like projection needs source-first return. | cross-source node projection manifest, schema, generated output, and tests. |
| `federation-spine` | source-owned exports compose into a bounded federation spine. | federation spine manifest, schema, generated output, and docs. |

Do not create `parts/<part>/` until moving the owning artifacts would make the
bridge safer and easier to validate.
