# INDEXED code-intelligence direction — G61 completion

Status is `review_required` / `submit_for_review` for the G61 whole-continuation ABI. The authored aoa-kag source and its generated repository-family refresh are ready for master review. Source readiness, producer validation, registry promotion, consumer admission, deployment/runtime evidence, proof/eval verdicts, landing, owner acceptance, and human acceptance remain separate claims.

## Fresh whole-direction work

- Added provider-neutral source-local code observations for Python AST, plus deterministic lexical JavaScript and TypeScript fallback explicitly limited to source-local indexing and not semantic portability.
- Integrated the exact G59 Universal Ctags 6.2.1 binding as caller-supplied JSON only. The candidate archive digest is `sha256:fa8a609bc834286a9c9b2e32e2b78791072cefe7956ba7a838b02004b29b0845`; the subject digest is `sha256:03e503df1a06356c5db39ce589d07ad161099746b1a0b7e178fbb0feb42cf5`. Its posture remains unsigned, unpromoted, unadmitted, uninstalled, and unexecuted.
- Preserved Git-derived observation lineage across rename and move, source-epoch provenance, incremental/full observation parity, add/delete/modify/rename/move delta planning, and bounded reverse-dependency affected closure.
- Retained split, merge, symbol-rename, and ambiguity alternatives as `selected=false` candidates requiring owner/provider review.
- Propagated qualification, provider, language, roles, confidence, currentness, source path, and trust metadata through structure extraction, repository indexes, incremental rehydration, generated family profiles, and query results.
- Added compact handles for definitions, references, callers, callees, imports, inheritance, ownership, changed-since, affected-by-change, lineage, ambiguity, freshness, proof status, and MCP source readiness. The proof handle routes to `aoa-evals`; it is not a proof verdict. MCP readiness is source-declared; it is not transport or runtime evidence.
- Preserved the current v4 capability-graph path and refreshed the committed repository-local generated family: corpus `sha256:33c5fd243eca78bbb106a044ef460d8a3b30440b2c63fce9dcbf3a89588fcf03`, distribution `sha256:fa05344967a8a50c263bbbd1769ea939615b191c04c10480e4f5e84fd8a9c416`, 13,766 canonical records, and 487 generated objects.

## Validation

Passed:

- The focused repository-index unit suite passed 166 tests with 1 optional test skipped.
- Focused observation, delta, lineage, affectedness, transformation, machine-envelope, fallback, and query-handle tests.
- Repository-family generation and its parity check were stable; the second check reused all 487 generated objects.
- The local KAG validation lane passed schema, generated-index, rebuild, payload, parity, and family checks; cross-repo checks were skipped because sibling roots were unavailable.
- Nested AGENTS, mechanics skeleton, decision index, decision records, semantic AGENTS, Python compilation, and whitespace checks.

Not green, with exact residuals retained:

- The source-fast lane exited 1 after 699 tests: 4 failures, 25 errors, 1 skipped. The residuals were unavailable abyss-stack, aoa-sdk, Tree-of-Sophia, and sibling generated fixtures, host-temp authority, and the known absolute-path assertion. Portable repository-family validation passed in that run.
- The generated lane exited 1 at external coverage prebuild because the observed provider revision did not match the expected pinned revision.
- Part-local checks lacked the sibling KAG export fixture.
- Local stats-port validation lacked the sibling aoa-stats validator.
- The release lane exited 1 because it invoked the same non-green source-fast prerequisite and retained those external residuals.

These failures are not represented as local passes and do not establish a provider, runtime, proof, or acceptance claim.

## Changed surfaces and claim boundaries

The authored delta is in the observation schemas/examples, `scripts/repo_local` structure/index/query surfaces, repository generator, validator inventory, and repository-index tests. The generated delta refreshes the four committed family manifests and all anchor shards.

Semantics changed: the source now defines bounded code-observation, lineage, delta, affectedness, qualification, and compact-handle behavior. Metadata changed: source epochs, provider/language/role/currentness/confidence/trust fields and generated profiles are carried through the KAG projections. No authored meaning in a sibling repository was replaced.

- Source readiness: established for this aoa-kag authored surface.
- Producer validation: focused and local KAG validation passed; full source-fast/generated gates retain the external residuals above.
- Registry promotion: not claimed; generated distribution remains `candidate`.
- Consumer admission: not claimed; G59 remains unsigned/unpromoted/unadmitted.
- Deployment/runtime: not claimed; no provider, service, MCP transport, deployment, or runtime evidence was produced.
- Proof/eval: not claimed; `proof-status` is only an owner route to `aoa-evals`.
- Landing: blocked before remote mutation. A pre-final-report-annotation candidate commit was prepared as `b9e986d656b33e329b9cfc64bf6ac20377c56690` with parent `578e4cea9a04b76a881bde240d5479efceea4926` in a writable temporary object store, but the linked worktree could not install its ref because `/srv/AbyssOS/aoa-kag/.git` is read-only. Push then failed because `github.com` could not be resolved; `gh auth status` also reports the configured token invalid. No PR, checks, or merge was created or observed.
- Owner and human acceptance: not claimed.

The landing attempt made no remote mutation and did not install a local branch ref.

## Runtime return ABI

```text
task_id: actor-task:code-intelligence.indexed-code-intelligence-direction.01a02fec-b609-7120-b11c-fa80d34ee86a.g61.whole-continuation
incarnation_id: incarnation:code-intelligence.indexed-code-intelligence-direction.01a02fec-b609-7120-b11c-fa80d34ee86a.g61.whole-continuation
continuation_id: continuation:code-intelligence.indexed-code-intelligence-direction.01a02fec-b609-7120-b11c-fa80d34ee86a.g61.whole-continuation
correlation_id: actor-route:code-intelligence.indexed-code-intelligence-direction.01a02fec-b609-7120-b11c-fa80d34ee86a.g61.whole-continuation
target_owner: aoa-kag
return_owner: codex-goal
status: review_required
decision: submit_for_review
external_effects_claimed: false
owner_acceptance_claimed: false
transition: active -> review_required; approval: master_review_required; rollback: master:01a02fec-b609-7120-b11c-fa80d34ee86a
```

The fixed validation commands named by `runtime-task.json` follow this update and are the final commands, with no later mutation.
