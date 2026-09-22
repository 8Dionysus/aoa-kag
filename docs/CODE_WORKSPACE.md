# Source-bound code workspace observations

`scripts.repo_local.code_scip.normalize_scip_workspace` normalizes a **supplied** SCIP
workspace into an unreleased KAG observation snapshot. It never launches an
indexer, reads ambient source paths, changes a repository, verifies admission,
publishes an owner family, or produces an eval verdict.

This additive v1 surface is separate from the seven-view repository family and
its segmented/tiered distribution. Existing builders and consumers are not
migrated implicitly. The API is an explicit submodule import, not an eager
package-facade import that expands the existing builder's reviewed execution
closure. It replaces neither their source truth nor their trust
gates. The earlier task-local file-at-a-time prototype was not a published ABI.

## Input and identity

The caller supplies the complete decoded SCIP index, exact UTF-8 source blobs,
repository/epoch label, and the captured provider name/version plus artifact,
configuration and dependency-environment SHA-256 digests. A content-derived
source manifest is independent from the analysis identity. An epoch label alone
never stands in for the bytes. Include resolver/build context in the source
manifest and configuration identity; input completeness is the capturing owner's
responsibility, not something the adapter can infer from a successful parse.

The snapshot additionally binds the complete native index. Handles are scoped
to that exact input/source/analysis combination, **not semantic lineage IDs**.
Native symbol keys are opaque and case-sensitive; display names cannot join
symbols. `local N` is scoped to its document. Occurrences and symbol metadata
are collected across all documents before definitions/references are joined.

## SCIP behavior

The [SCIP protocol](https://github.com/scip-code/scip/blob/db62094c7f9d464d0a6d9fd7815fcf3c9214b4c2/scip.proto) makes
an occurrence's symbol optional and does not require an enclosing symbol for
references. Definition role bits establish definitions; symbol documentation
alone does not. External metadata and unresolved targets remain explicit.
Multiple definitions are exposed together instead of selecting one silently.
Highlight-only occurrences and native relationship flags are retained. A
reference is not promoted to a call or inheritance relation. The bounded query
currently returns direct occurrences only, without relationship expansion.

Position encoding must come from the document or an **explicit caller-bound
legacy ABI fallback**. It is never guessed from the language or confused with
file text encoding. UTF-8/16/32 native columns convert against the same source
blob into half-open UTF-8 byte offsets. CRLF, supplementary characters, empty
ranges and typed SCIP ranges are supported. Typed ranges take precedence over
legacy arrays. A mid-code-point offset, wrong source, unsafe/duplicate path,
conflicting field aliases or unspecified/unsupported encoding fails closed.

## Read boundary

The normalizer returns a `CodeWorkspace`, whose `to_dict()` is the full
schema-bound transport payload. `read(handle, source=exact_blob)` verifies the
source digest and returns at most 4096 source characters. `query(symbol_handle,
"definitions" | "references")` returns at most ten occurrences and a cursor
bound to snapshot, symbol, query kind and page size. Compact responses omit the
whole source manifest and bulky native metadata; the complete snapshot retains
those bytes. Returned objects are copies.

Obtain instances through the normalizer. The constructor accepts internal
normalized rows; it is not a validator or loader for an untrusted persisted
snapshot. A future capture/materialization consumer must validate the transport
schema and cross-record bindings before accepting stored input.

Every read distinguishes exact-snapshot freshness, unassessed admission,
unreleased publication, and absent semantic proof. Coverage is explicitly
`supplied_index_only`; additional source files and unresolved targets stay
visible. This does not establish current working-tree freshness, provider
correctness, a complete project index or independent proof.

## Validation and next owner

The code-workspace family in the [test inventory](testing/test_inventory.json)
checks the contract and its public illustrative example. Expected fixture facts
are authored separately from the normalizer. These regressions protect continuing
protocol and source boundaries; they are not the independent `aoa-evals` semantic
benchmark.

STACK remains responsible for capture/execution/materialization and LIVE
sessions; MACHINE owns exact provider artifacts and admission; EVALS owns
reviewed semantic claims. Runtime integration and published MCP capability
exposure are subsequent owner changes, not consequences of importing this API.
