from __future__ import annotations

from .core import *
from .recurrence_contracts import *
from .registry_contracts import *

ALLOWED_CONTRACT_STRENGTH = {
    "schema_backed",
    "doc_backed",
    "playbook_declared",
}

EXPECTED_REASONING_HANDOFF_SOURCE_ROOT_ENVS = {
    "aoa-playbooks": "AOA_PLAYBOOKS_ROOT",
    "aoa-evals": "AOA_EVALS_ROOT",
    "aoa-memo": "AOA_MEMO_ROOT",
    "aoa-agents": "AOA_AGENTS_ROOT",
}

EXPECTED_REASONING_HANDOFF_INPUTS = {
    (
        "reasoning_handoff_doc",
        "aoa-kag",
        REASONING_HANDOFF_GUARDRAIL_REF,
        "kag_guardrail_doc",
    ),
    (
        "reasoning_handoff_schema",
        "aoa-kag",
        REASONING_HANDOFF_GUARDRAIL_SCHEMA_REF,
        "kag_guardrail_schema",
    ),
    ("counterpart_consumer_contract_doc", "aoa-kag", COUNTERPART_CONSUMER_CONTRACT_DOC_REF, "kag_guardrail_doc"),
    ("counterpart_consumer_contract_schema", "aoa-kag", COUNTERPART_CONSUMER_CONTRACT_SCHEMA_REF, "kag_guardrail_schema"),
    ("counterpart_consumer_contract_example", "aoa-kag", COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_REF, "kag_guardrail_example"),
    (
        "counterpart_federation_exposure_review_doc",
        "aoa-kag",
        COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_REF,
        "kag_guardrail_doc",
    ),
    ("artifact_to_verdict_hook_schema", "aoa-evals", "mechanics/audit/parts/artifact-verdict-hooks/schemas/artifact-to-verdict-hook.schema.json", "eval_hook_schema"),
    ("aoa_p_0008_playbook", "aoa-playbooks", "playbooks/operations/orchestration/long-horizon-model-tier-orchestra/PLAYBOOK.md", "playbook_doc"),
    ("aoa_p_0008_hook", "aoa-evals", "mechanics/audit/parts/artifact-verdict-hooks/examples/artifact_to_verdict_hook.long-horizon-model-tier-orchestra.example.json", "eval_hook_fixture"),
    ("aoa_p_0009_playbook", "aoa-playbooks", "playbooks/continuity/session-growth/restartable-inquiry-loop/PLAYBOOK.md", "playbook_doc"),
    ("aoa_p_0009_hook", "aoa-evals", "mechanics/checkpoint/parts/restartable-inquiry/examples/artifact_to_verdict_hook.restartable-inquiry-loop.example.json", "eval_hook_fixture"),
    ("checkpoint_to_memory_contract", "aoa-memo", "mechanics/checkpoint/parts/checkpoint-to-memory-mapping/examples/checkpoint_to_memory_contract.example.json", "memo_contract_fixture"),
    ("inquiry_checkpoint_schema", "aoa-memo", "mechanics/checkpoint/parts/checkpoint-carry-contract/schemas/inquiry_checkpoint.schema.json", "memo_schema"),
    ("witness_trace_contract", "aoa-memo", "mechanics/recurrence-support/docs/WITNESS_TRACE_CONTRACT.md", "memo_doc"),
    ("witness_trace_schema", "aoa-memo", "mechanics/recurrence-support/parts/witness-trace-contract/schemas/witness-trace.schema.json", "memo_schema"),
}

EXPECTED_REASONING_HANDOFF_BINDINGS = {
    ("AOA-P-0008", "aoa_p_0008_playbook", "aoa_p_0008_hook", ("checkpoint_to_memory_contract",), None, ("witness_trace_contract", "witness_trace_schema")),
    ("AOA-P-0009", "aoa_p_0009_playbook", "aoa_p_0009_hook", ("checkpoint_to_memory_contract",), "inquiry_checkpoint_schema", ()),
}

EXPECTED_REASONING_HANDOFF_OUTPUT_PATHS = {
    "full": REASONING_HANDOFF_OUTPUT_REF,
    "min": REASONING_HANDOFF_MIN_OUTPUT_REF,
}

EXPECTED_REASONING_HANDOFF_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "routing_ownership": "forbidden",
    "memory_truth_ownership": "forbidden",
    "canon_authorship": "forbidden",
    "verdict_ownership": "forbidden",
}

EXPECTED_REASONING_HANDOFF_SCENARIOS = {"AOA-P-0008", "AOA-P-0009"}

EXPECTED_REASONING_HANDOFF_KAG_GUARDRAIL_REFS = [
    REASONING_HANDOFF_GUARDRAIL_REF,
    REASONING_HANDOFF_GUARDRAIL_SCHEMA_REF,
    COUNTERPART_CONSUMER_CONTRACT_DOC_REF,
    COUNTERPART_CONSUMER_CONTRACT_SCHEMA_REF,
    COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_REF,
    COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_REF,
]
