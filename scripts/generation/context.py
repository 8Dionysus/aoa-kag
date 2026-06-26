from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class GenerationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise GenerationError(message)


def repo_root_from_env(env_name: str, default: Path) -> Path:
    override = os.environ.get(env_name)
    if not override:
        return default
    return Path(override).expanduser().resolve()


AOA_TECHNIQUES_ROOT = repo_root_from_env(
    "AOA_TECHNIQUES_ROOT", REPO_ROOT.parent / "aoa-techniques"
)
AOA_PLAYBOOKS_ROOT = repo_root_from_env(
    "AOA_PLAYBOOKS_ROOT", REPO_ROOT.parent / "aoa-playbooks"
)
AOA_EVALS_ROOT = repo_root_from_env("AOA_EVALS_ROOT", REPO_ROOT.parent / "aoa-evals")
AOA_MEMO_ROOT = repo_root_from_env("AOA_MEMO_ROOT", REPO_ROOT.parent / "aoa-memo")
AOA_AGENTS_ROOT = repo_root_from_env("AOA_AGENTS_ROOT", REPO_ROOT.parent / "aoa-agents")
TREE_OF_SOPHIA_ROOT = repo_root_from_env(
    "TREE_OF_SOPHIA_ROOT", REPO_ROOT.parent / "Tree-of-Sophia"
)

REGISTRY_MANIFEST_PATH = REPO_ROOT / "manifests" / "kag_registry.json"
TECHNIQUE_LIFT_PART_ROOT = (
    REPO_ROOT / "mechanics" / "distillation" / "parts" / "technique-lift"
)
TECHNIQUE_LIFT_MANIFEST_PATH = (
    TECHNIQUE_LIFT_PART_ROOT / "manifests" / "technique_lift_pack.json"
)
TECHNIQUE_LIFT_MANIFEST_REF = (
    "mechanics/distillation/parts/technique-lift/manifests/technique_lift_pack.json"
)
TECHNIQUE_LIFT_OUTPUT_REF = (
    "mechanics/distillation/parts/technique-lift/generated/technique_lift_pack.json"
)
TECHNIQUE_LIFT_MIN_OUTPUT_REF = (
    "mechanics/distillation/parts/technique-lift/generated/technique_lift_pack.min.json"
)
TOS_TEXT_CHUNK_MAP_PART_ROOT = (
    REPO_ROOT
    / "mechanics"
    / "distillation"
    / "parts"
    / "tos-text-chunk-map"
)
TOS_TEXT_CHUNK_MAP_MANIFEST_PATH = (
    TOS_TEXT_CHUNK_MAP_PART_ROOT / "manifests" / "tos_text_chunk_map.json"
)
TOS_TEXT_CHUNK_MAP_MANIFEST_REF = (
    "mechanics/distillation/parts/tos-text-chunk-map/manifests/tos_text_chunk_map.json"
)
TOS_TEXT_CHUNK_MAP_OUTPUT_REF = (
    "mechanics/distillation/parts/tos-text-chunk-map/generated/tos_text_chunk_map.json"
)
TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_REF = (
    "mechanics/distillation/parts/tos-text-chunk-map/generated/tos_text_chunk_map.min.json"
)
TOS_RETRIEVAL_AXIS_PART_ROOT = (
    REPO_ROOT / "mechanics" / "boundary-bridge" / "parts" / "tos-retrieval-axis"
)
TOS_RETRIEVAL_AXIS_MANIFEST_PATH = (
    TOS_RETRIEVAL_AXIS_PART_ROOT / "manifests" / "tos_retrieval_axis_pack.json"
)
TOS_RETRIEVAL_AXIS_MANIFEST_REF = (
    "mechanics/boundary-bridge/parts/tos-retrieval-axis/manifests/"
    "tos_retrieval_axis_pack.json"
)
TOS_RETRIEVAL_AXIS_OUTPUT_REF = (
    "mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/"
    "tos_retrieval_axis_pack.json"
)
TOS_RETRIEVAL_AXIS_MIN_OUTPUT_REF = (
    "mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/"
    "tos_retrieval_axis_pack.min.json"
)
TOS_ROUTE_LIFT_PART_ROOT = (
    REPO_ROOT / "mechanics" / "distillation" / "parts" / "tos-route-lift"
)
TOS_ZARATHUSTRA_ROUTE_PACK_MANIFEST_PATH = (
    TOS_ROUTE_LIFT_PART_ROOT / "manifests" / "tos_zarathustra_route_pack.json"
)
TOS_ZARATHUSTRA_ROUTE_PACK_MANIFEST_REF = (
    "mechanics/distillation/parts/tos-route-lift/manifests/tos_zarathustra_route_pack.json"
)
TOS_ZARATHUSTRA_ROUTE_PACK_OUTPUT_REF = (
    "mechanics/distillation/parts/tos-route-lift/generated/tos_zarathustra_route_pack.json"
)
TOS_ZARATHUSTRA_ROUTE_PACK_MIN_OUTPUT_REF = (
    "mechanics/distillation/parts/tos-route-lift/generated/"
    "tos_zarathustra_route_pack.min.json"
)
TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MANIFEST_PATH = (
    TOS_RETRIEVAL_AXIS_PART_ROOT
    / "manifests"
    / "tos_zarathustra_route_retrieval_pack.json"
)
TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MANIFEST_REF = (
    "mechanics/boundary-bridge/parts/tos-retrieval-axis/manifests/"
    "tos_zarathustra_route_retrieval_pack.json"
)
TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_OUTPUT_REF = (
    "mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/"
    "tos_zarathustra_route_retrieval_pack.json"
)
TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MIN_OUTPUT_REF = (
    "mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/"
    "tos_zarathustra_route_retrieval_pack.min.json"
)
REASONING_HANDOFF_PART_ROOT = (
    REPO_ROOT / "mechanics" / "checkpoint" / "parts" / "reasoning-handoff"
)
REASONING_HANDOFF_MANIFEST_PATH = (
    REASONING_HANDOFF_PART_ROOT / "manifests" / "reasoning_handoff_pack.json"
)
REASONING_HANDOFF_MANIFEST_REF = (
    "mechanics/checkpoint/parts/reasoning-handoff/manifests/"
    "reasoning_handoff_pack.json"
)
REASONING_HANDOFF_OUTPUT_REF = (
    "mechanics/checkpoint/parts/reasoning-handoff/generated/reasoning_handoff_pack.json"
)
REASONING_HANDOFF_MIN_OUTPUT_REF = (
    "mechanics/checkpoint/parts/reasoning-handoff/generated/"
    "reasoning_handoff_pack.min.json"
)
SOURCE_OWNED_EXPORT_DEPENDENCIES_MANIFEST_PATH = (
    REPO_ROOT
    / "mechanics"
    / "boundary-bridge"
    / "parts"
    / "source-owned-export"
    / "manifests"
    / "source_owned_export_dependencies.json"
)
SOURCE_OWNED_EXPORT_PART_ROOT = SOURCE_OWNED_EXPORT_DEPENDENCIES_MANIFEST_PATH.parents[1]
SOURCE_OWNED_EXPORT_DEPENDENCIES_MANIFEST_REF = (
    "mechanics/boundary-bridge/parts/source-owned-export/manifests/"
    "source_owned_export_dependencies.json"
)
FEDERATION_EXPORT_REGISTRY_MANIFEST_PATH = (
    SOURCE_OWNED_EXPORT_PART_ROOT / "manifests" / "federation_export_registry.json"
)
FEDERATION_EXPORT_REGISTRY_MANIFEST_REF = (
    "mechanics/boundary-bridge/parts/source-owned-export/manifests/"
    "federation_export_registry.json"
)
FEDERATION_EXPORT_REGISTRY_OUTPUT_REF = (
    "mechanics/boundary-bridge/parts/source-owned-export/generated/"
    "federation_export_registry.json"
)
FEDERATION_EXPORT_REGISTRY_MIN_OUTPUT_REF = (
    "mechanics/boundary-bridge/parts/source-owned-export/generated/"
    "federation_export_registry.min.json"
)
CROSS_SOURCE_NODE_PROJECTION_PART_ROOT = (
    REPO_ROOT
    / "mechanics"
    / "boundary-bridge"
    / "parts"
    / "cross-source-projection"
)
CROSS_SOURCE_NODE_PROJECTION_MANIFEST_PATH = (
    CROSS_SOURCE_NODE_PROJECTION_PART_ROOT
    / "manifests"
    / "cross_source_node_projection.json"
)
CROSS_SOURCE_NODE_PROJECTION_MANIFEST_REF = (
    "mechanics/boundary-bridge/parts/cross-source-projection/manifests/"
    "cross_source_node_projection.json"
)
CROSS_SOURCE_NODE_PROJECTION_DOC_REF = (
    "mechanics/boundary-bridge/parts/cross-source-projection/docs/"
    "cross-source-node-projection.md"
)
CROSS_SOURCE_NODE_PROJECTION_OUTPUT_REF = (
    "mechanics/boundary-bridge/parts/cross-source-projection/generated/"
    "cross_source_node_projection.json"
)
CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_REF = (
    "mechanics/boundary-bridge/parts/cross-source-projection/generated/"
    "cross_source_node_projection.min.json"
)
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_PART_ROOT = (
    REPO_ROOT / "mechanics" / "audit" / "parts" / "exposure-review"
)
COUNTERPART_EDGE_PART_ROOT = (
    REPO_ROOT / "mechanics" / "boundary-bridge" / "parts" / "counterpart-edge"
)
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_PATH = (
    COUNTERPART_FEDERATION_EXPOSURE_REVIEW_PART_ROOT
    / "manifests"
    / "counterpart_federation_exposure_review.json"
)
TINY_CONSUMER_BUNDLE_PART_ROOT = (
    REPO_ROOT
    / "mechanics"
    / "boundary-bridge"
    / "parts"
    / "tiny-consumer-bundle"
)
TINY_CONSUMER_BUNDLE_MANIFEST_PATH = (
    TINY_CONSUMER_BUNDLE_PART_ROOT / "manifests" / "tiny_consumer_bundle.json"
)
RETURN_REGROUNDING_PART_ROOT = (
    REPO_ROOT / "mechanics" / "recurrence" / "parts" / "return-regrounding"
)
RETURN_REGROUNDING_MANIFEST_PATH = (
    RETURN_REGROUNDING_PART_ROOT / "manifests" / "return_regrounding_pack.json"
)
RETURN_REGROUNDING_MANIFEST_REF = (
    "mechanics/recurrence/parts/return-regrounding/manifests/"
    "return_regrounding_pack.json"
)
RETURN_REGROUNDING_OUTPUT_REF = (
    "mechanics/recurrence/parts/return-regrounding/generated/"
    "return_regrounding_pack.json"
)
RETURN_REGROUNDING_MIN_OUTPUT_REF = (
    "mechanics/recurrence/parts/return-regrounding/generated/"
    "return_regrounding_pack.min.json"
)
SURFACE_GROWTH_STOP_RULE_PART_ROOT = (
    REPO_ROOT / "mechanics" / "growth-cycle" / "parts" / "surface-growth-stop-rule"
)
PROOF_EXPECTATION_REFS_PART_ROOT = (
    REPO_ROOT / "mechanics" / "audit" / "parts" / "proof-expectation-refs"
)
KAG_MATURITY_GOVERNANCE_MANIFEST_PATH = (
    SURFACE_GROWTH_STOP_RULE_PART_ROOT
    / "manifests"
    / "kag_maturity_governance.json"
)
KAG_MATURITY_GOVERNANCE_MANIFEST_REF = (
    "mechanics/growth-cycle/parts/surface-growth-stop-rule/manifests/"
    "kag_maturity_governance.json"
)
KAG_MATURITY_GOVERNANCE_DOC_REF = (
    "mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/"
    "kag-maturity-governance.md"
)
KAG_OWNER_WAIT_STATES_DOC_REF = (
    "mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/"
    "kag-owner-wait-states.md"
)
KAG_PROOF_EXPECTATIONS_DOC_REF = (
    "mechanics/audit/parts/proof-expectation-refs/docs/"
    "kag-proof-expectations.md"
)
KAG_MATURITY_GOVERNANCE_OUTPUT_REF = (
    "mechanics/growth-cycle/parts/surface-growth-stop-rule/generated/"
    "kag_maturity_governance.json"
)
KAG_MATURITY_GOVERNANCE_MIN_OUTPUT_REF = (
    "mechanics/growth-cycle/parts/surface-growth-stop-rule/generated/"
    "kag_maturity_governance.min.json"
)
FEDERATION_SPINE_PART_ROOT = (
    REPO_ROOT / "mechanics" / "boundary-bridge" / "parts" / "federation-spine"
)
FEDERATION_SPINE_MANIFEST_PATH = (
    FEDERATION_SPINE_PART_ROOT / "manifests" / "federation_spine.json"
)
FEDERATION_SPINE_MANIFEST_REF = (
    "mechanics/boundary-bridge/parts/federation-spine/manifests/"
    "federation_spine.json"
)
FEDERATION_SPINE_OUTPUT_REF = (
    "mechanics/boundary-bridge/parts/federation-spine/generated/"
    "federation_spine.json"
)
FEDERATION_SPINE_MIN_OUTPUT_REF = (
    "mechanics/boundary-bridge/parts/federation-spine/generated/"
    "federation_spine.min.json"
)
REASONING_HANDOFF_GUARDRAIL_PATH = (
    REASONING_HANDOFF_PART_ROOT / "docs" / "reasoning-handoff.md"
)
REASONING_HANDOFF_GUARDRAIL_SCHEMA_PATH = (
    REASONING_HANDOFF_PART_ROOT / "schemas" / "reasoning-handoff-guardrail.schema.json"
)
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_PATH = (
    COUNTERPART_FEDERATION_EXPOSURE_REVIEW_PART_ROOT
    / "docs"
    / "counterpart-federation-exposure-review.md"
)
COUNTERPART_CONSUMER_CONTRACT_DOC_PATH = (
    COUNTERPART_EDGE_PART_ROOT / "docs" / "counterpart-consumer-contract.md"
)
COUNTERPART_CONSUMER_CONTRACT_SCHEMA_PATH = (
    COUNTERPART_EDGE_PART_ROOT / "schemas" / "counterpart-consumer-contract.schema.json"
)
COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH = (
    COUNTERPART_EDGE_PART_ROOT / "examples" / "counterpart_consumer_contract.example.json"
)
EVAL_CATALOG_PATH = AOA_EVALS_ROOT / "generated" / "eval_catalog.min.json"

REGISTRY_OUTPUT_PATH = REPO_ROOT / "generated" / "kag_registry.json"
REGISTRY_MIN_OUTPUT_PATH = REPO_ROOT / "generated" / "kag_registry.min.json"
TECHNIQUE_LIFT_OUTPUT_PATH = (
    TECHNIQUE_LIFT_PART_ROOT / "generated" / "technique_lift_pack.json"
)
TECHNIQUE_LIFT_MIN_OUTPUT_PATH = (
    TECHNIQUE_LIFT_PART_ROOT / "generated" / "technique_lift_pack.min.json"
)
TOS_TEXT_CHUNK_MAP_OUTPUT_PATH = (
    TOS_TEXT_CHUNK_MAP_PART_ROOT / "generated" / "tos_text_chunk_map.json"
)
TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH = (
    TOS_TEXT_CHUNK_MAP_PART_ROOT / "generated" / "tos_text_chunk_map.min.json"
)
TOS_RETRIEVAL_AXIS_OUTPUT_PATH = (
    TOS_RETRIEVAL_AXIS_PART_ROOT / "generated" / "tos_retrieval_axis_pack.json"
)
TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH = (
    TOS_RETRIEVAL_AXIS_PART_ROOT / "generated" / "tos_retrieval_axis_pack.min.json"
)
TOS_ZARATHUSTRA_ROUTE_PACK_OUTPUT_PATH = (
    TOS_ROUTE_LIFT_PART_ROOT / "generated" / "tos_zarathustra_route_pack.json"
)
TOS_ZARATHUSTRA_ROUTE_PACK_MIN_OUTPUT_PATH = (
    TOS_ROUTE_LIFT_PART_ROOT / "generated" / "tos_zarathustra_route_pack.min.json"
)
TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_OUTPUT_PATH = (
    TOS_RETRIEVAL_AXIS_PART_ROOT
    / "generated"
    / "tos_zarathustra_route_retrieval_pack.json"
)
TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MIN_OUTPUT_PATH = (
    TOS_RETRIEVAL_AXIS_PART_ROOT
    / "generated"
    / "tos_zarathustra_route_retrieval_pack.min.json"
)
REASONING_HANDOFF_OUTPUT_PATH = (
    REASONING_HANDOFF_PART_ROOT / "generated" / "reasoning_handoff_pack.json"
)
REASONING_HANDOFF_MIN_OUTPUT_PATH = (
    REASONING_HANDOFF_PART_ROOT / "generated" / "reasoning_handoff_pack.min.json"
)
FEDERATION_EXPORT_REGISTRY_OUTPUT_PATH = (
    SOURCE_OWNED_EXPORT_PART_ROOT / "generated" / "federation_export_registry.json"
)
FEDERATION_EXPORT_REGISTRY_MIN_OUTPUT_PATH = (
    SOURCE_OWNED_EXPORT_PART_ROOT
    / "generated"
    / "federation_export_registry.min.json"
)
FEDERATION_SPINE_OUTPUT_PATH = FEDERATION_SPINE_PART_ROOT / "generated" / "federation_spine.json"
FEDERATION_SPINE_MIN_OUTPUT_PATH = (
    FEDERATION_SPINE_PART_ROOT / "generated" / "federation_spine.min.json"
)
CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATH = (
    CROSS_SOURCE_NODE_PROJECTION_PART_ROOT
    / "generated"
    / "cross_source_node_projection.json"
)
CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH = (
    CROSS_SOURCE_NODE_PROJECTION_PART_ROOT
    / "generated"
    / "cross_source_node_projection.min.json"
)
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATH = (
    COUNTERPART_FEDERATION_EXPOSURE_REVIEW_PART_ROOT
    / "generated"
    / "counterpart_federation_exposure_review.json"
)
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_OUTPUT_PATH = (
    COUNTERPART_FEDERATION_EXPOSURE_REVIEW_PART_ROOT
    / "generated"
    / "counterpart_federation_exposure_review.min.json"
)
TINY_CONSUMER_BUNDLE_OUTPUT_PATH = (
    TINY_CONSUMER_BUNDLE_PART_ROOT / "generated" / "tiny_consumer_bundle.json"
)
TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH = (
    TINY_CONSUMER_BUNDLE_PART_ROOT / "generated" / "tiny_consumer_bundle.min.json"
)
RETURN_REGROUNDING_OUTPUT_PATH = (
    RETURN_REGROUNDING_PART_ROOT / "generated" / "return_regrounding_pack.json"
)
RETURN_REGROUNDING_MIN_OUTPUT_PATH = (
    RETURN_REGROUNDING_PART_ROOT / "generated" / "return_regrounding_pack.min.json"
)
KAG_MATURITY_GOVERNANCE_OUTPUT_PATH = (
    SURFACE_GROWTH_STOP_RULE_PART_ROOT
    / "generated"
    / "kag_maturity_governance.json"
)
KAG_MATURITY_GOVERNANCE_MIN_OUTPUT_PATH = (
    SURFACE_GROWTH_STOP_RULE_PART_ROOT
    / "generated"
    / "kag_maturity_governance.min.json"
)

QUERY_MODE_HEADING = re.compile(r"^###\s+`([^`]+)`\s*$")
KAG_REPO = "aoa-kag"
TOS_REPO = "Tree-of-Sophia"
FEDERATION_SPINE_ARTIFACT_IDENTITY = {
    "artifact_class": "derived_kag_readmodel",
    "surface_state": "public_generated_federation_spine",
    "owner_repo": "aoa-kag",
    "authority_ref": "mechanics/boundary-bridge/parts/federation-spine/docs/federation-spine.md",
    "producer": (
        "scripts/generate_kag.py from "
        "mechanics/boundary-bridge/parts/federation-spine/manifests/"
        "federation_spine.json and source-owned exports"
    ),
    "consumer_expectation": (
        "consumers verify pack_version, source_inputs, bounded_output_contract, "
        "source-owned export refs, and validate_kag before using the spine as "
        "derived federation readiness"
    ),
    "privacy_boundary": (
        "public derived refs only; no private session, memo, runtime, source "
        "payload body, or local host evidence"
    ),
    "content_identity": (
        "mechanics/boundary-bridge/parts/federation-spine/generated/"
        "federation_spine.json and "
        "mechanics/boundary-bridge/parts/federation-spine/generated/"
        "federation_spine.min.json rebuilt from the federation spine manifest "
        "and compared by release_check"
    ),
    "abi_epoch": "aoa_kag_federation_spine_v1",
    "contract_version": "federation-spine.schema.json@aoa_kag_federation_spine_v1#artifact_identity",
    "trust_layer": ["abi_contract_signature", "w3c_prov_lineage"],
    "verification": ["python scripts/validate_kag.py", "python scripts/release_check.py"],
    "action": "ADD_CONSUMER_EXPECTATION",
}
KAG_REGISTRY_ARTIFACT_IDENTITY = {
    "artifact_class": "derived_kag_registry_readmodel_bundle",
    "surface_state": "public_generated_kag_registry",
    "owner_repo": "aoa-kag",
    "authority_ref": "docs/KAG_MODEL.md",
    "producer": "scripts/generate_kag.py from manifests/kag_registry.json",
    "consumer_expectation": (
        "consumers verify artifact_identity, version, layer, schema conformance, "
        "generated parity, validate_kag, and OS Abyss ABI/SBOM-lite/SLSA "
        "sidecars before using the registry as a derived KAG surface catalog"
    ),
    "privacy_boundary": (
        "public derived refs and compact summaries only; no private session, memo "
        "payload body, source corpus body, secrets, live runtime state, or local "
        "host evidence"
    ),
    "content_identity": (
        "generated/kag_registry.json and generated/kag_registry.min.json rebuilt "
        "from manifests/kag_registry.json and compared by validate_kag"
    ),
    "abi_epoch": "aoa_kag_registry_readmodel_v1",
    "contract_version": "schemas/kag-registry.schema.json@aoa_kag_registry_readmodel_v1#artifact_identity",
    "trust_layer": ["abi_contract_signature", "sbom", "slsa_in_toto"],
    "verification": [
        "python scripts/validate_kag.py",
        "python scripts/ci_gate.py --mode generated",
        "python scripts/validate_abyss_machine_kag_registry_bundle.py",
    ],
    "action": "ADD_RELEASE_PROVENANCE",
}
KNOWN_REPO_ROOTS = {
    KAG_REPO: REPO_ROOT,
    "aoa-techniques": AOA_TECHNIQUES_ROOT,
    "aoa-playbooks": AOA_PLAYBOOKS_ROOT,
    "aoa-evals": AOA_EVALS_ROOT,
    "aoa-memo": AOA_MEMO_ROOT,
    "aoa-agents": AOA_AGENTS_ROOT,
    TOS_REPO: TREE_OF_SOPHIA_ROOT,
}
COMPATIBILITY_REF_ALIASES = {
    "aoa-evals": {
        "mechanics/audit/parts/artifact-verdict-hooks/schemas/artifact-to-verdict-hook.schema.json": (
            "schemas/artifact-to-verdict-hook.schema.json",
        ),
        "mechanics/audit/parts/artifact-verdict-hooks/examples/artifact_to_verdict_hook.long-horizon-model-tier-orchestra.example.json": (
            "examples/artifact_to_verdict_hook.long-horizon-model-tier-orchestra.example.json",
        ),
        "mechanics/audit/parts/artifact-verdict-hooks/docs/TRACE_EVAL_BRIDGE.md": (
            "docs/TRACE_EVAL_BRIDGE.md",
        ),
        "mechanics/checkpoint/parts/restartable-inquiry/examples/artifact_to_verdict_hook.restartable-inquiry-loop.example.json": (
            "examples/artifact_to_verdict_hook.restartable-inquiry-loop.example.json",
        ),
        "evals/boundary/aoa-approval-boundary-adherence/EVAL.md": (
            "bundles/aoa-approval-boundary-adherence/EVAL.md",
        ),
        "evals/boundary/aoa-local-text-contract-fit/EVAL.md": (
            "bundles/aoa-local-text-contract-fit/EVAL.md",
        ),
        "evals/boundary/aoa-owner-fit-routing-quality/EVAL.md": (
            "bundles/aoa-owner-fit-routing-quality/EVAL.md",
        ),
        "evals/capability/aoa-candidate-lineage-integrity/EVAL.md": (
            "bundles/aoa-candidate-lineage-integrity/EVAL.md",
        ),
        "evals/comparison/longitudinal-window/aoa-stress-recovery-window/EVAL.md": (
            "bundles/aoa-stress-recovery-window/EVAL.md",
        ),
        "evals/stress/aoa-antifragility-posture/EVAL.md": (
            "bundles/aoa-antifragility-posture/EVAL.md",
        ),
        "evals/workflow/aoa-bounded-change-quality/EVAL.md": (
            "bundles/aoa-bounded-change-quality/EVAL.md",
        ),
        "evals/workflow/aoa-long-horizon-depth/EVAL.md": (
            "bundles/aoa-long-horizon-depth/EVAL.md",
        ),
        "evals/workflow/aoa-long-horizon-depth/checks/eval-integrity-check.md": (
            "bundles/aoa-long-horizon-depth/checks/eval-integrity-check.md",
        ),
        "evals/workflow/aoa-long-horizon-depth/notes/proof-surface-contract.md": (
            "bundles/aoa-long-horizon-depth/notes/proof-surface-contract.md",
        ),
        "evals/workflow/aoa-long-horizon-depth/notes/restart-contract.md": (
            "bundles/aoa-long-horizon-depth/notes/restart-contract.md",
        ),
        "evals/workflow/aoa-memo-contradiction-integrity/EVAL.md": (
            "bundles/aoa-memo-contradiction-integrity/EVAL.md",
        ),
        "evals/workflow/aoa-memo-recall-integrity/EVAL.md": (
            "bundles/aoa-memo-recall-integrity/EVAL.md",
        ),
        "evals/workflow/aoa-return-anchor-integrity/EVAL.md": (
            "bundles/aoa-return-anchor-integrity/EVAL.md",
        ),
        "evals/workflow/aoa-tool-trajectory-discipline/EVAL.md": (
            "bundles/aoa-tool-trajectory-discipline/EVAL.md",
        ),
        "evals/workflow/aoa-tool-trajectory-discipline/checks/eval-integrity-check.md": (
            "bundles/aoa-tool-trajectory-discipline/checks/eval-integrity-check.md",
        ),
        "evals/workflow/aoa-tool-trajectory-discipline/notes/bounded-promotion-review.md": (
            "bundles/aoa-tool-trajectory-discipline/notes/bounded-promotion-review.md",
        ),
        "evals/workflow/aoa-tool-trajectory-discipline/notes/proof-surface-contract.md": (
            "bundles/aoa-tool-trajectory-discipline/notes/proof-surface-contract.md",
        ),
    },
    "aoa-memo": {
        "examples/recall/recall_contract.object.working.return.json": (
            "examples/recall_contract.object.working.return.json",
        ),
        "examples/recall/recall_contract.router.semantic.json": (
            "examples/recall_contract.router.semantic.json",
        ),
        "generated/memory-objects/memory_object_capsules.json": (
            "generated/memory_object_capsules.json",
        ),
        "generated/memory-objects/memory_object_catalog.min.json": (
            "generated/memory_object_catalog.min.json",
        ),
        "mechanics/checkpoint/parts/checkpoint-carry-contract/schemas/inquiry_checkpoint.schema.json": (
            "mechanics/checkpoint/schemas/inquiry_checkpoint.schema.json",
        ),
        "mechanics/checkpoint/parts/checkpoint-to-memory-mapping/examples/checkpoint_to_memory_contract.example.json": (
            "mechanics/checkpoint/examples/checkpoint_to_memory_contract.example.json",
        ),
        "mechanics/checkpoint/parts/checkpoint-to-memory-mapping/schemas/checkpoint-to-memory-contract.schema.json": (
            "mechanics/checkpoint/schemas/checkpoint-to-memory-contract.schema.json",
        ),
        "mechanics/consumer-handoff/parts/kag-source-export/generated/kag_export.min.json": (
            "mechanics/consumer-handoff/generated/kag_export.min.json",
        ),
        "mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/bridge.kag-lift.example.json": (
            "mechanics/consumer-handoff/examples/bridge.kag-lift.example.json",
        ),
        "mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/claim.tos-bridge-ready.example.json": (
            "mechanics/consumer-handoff/examples/claim.tos-bridge-ready.example.json",
        ),
        "mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/episode.tos-interpretation.example.json": (
            "mechanics/consumer-handoff/examples/episode.tos-interpretation.example.json",
        ),
        "mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/memory_chunk_face.bridge.example.json": (
            "mechanics/consumer-handoff/examples/memory_chunk_face.bridge.example.json",
        ),
        "mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/memory_graph_face.bridge.example.json": (
            "mechanics/consumer-handoff/examples/memory_graph_face.bridge.example.json",
        ),
        "mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/provenance_thread.kag-lift.example.json": (
            "mechanics/consumer-handoff/examples/provenance_thread.kag-lift.example.json",
        ),
        "mechanics/recurrence-support/parts/witness-trace-contract/schemas/witness-trace.schema.json": (
            "mechanics/recurrence-support/schemas/witness-trace.schema.json",
        ),
    },
}
TOS_ROOT_README_PATH = "README.md"
TOS_TINY_ENTRY_DOCTRINE_PATH = "ToS/zarathustra/public-entry/TINY_ENTRY_ROUTE.md"
TOS_TINY_ENTRY_ROUTE_PATH = "ToS/public-compatibility/tos_tiny_entry_route.example.json"
TOS_TINY_ENTRY_ROUTE_REF = f"{TOS_REPO}/{TOS_TINY_ENTRY_ROUTE_PATH}"
TOS_TINY_ENTRY_ROUTE_ID = "tos-tiny-entry.zarathustra-prologue"
TOS_TINY_ENTRY_CAPSULE_PATH = "ToS/zarathustra/prologue-1/TRILINGUAL_ENTRY.md"
TOS_TINY_ENTRY_AUTHORITY_PATH = "ToS/public-compatibility/source_node.example.json"
TOS_TINY_ENTRY_PRIMARY_HOP_FIELD = "bounded_hop"
TOS_TINY_ENTRY_LEGACY_HOP_FIELD = "lineage_or_context_hop"
TOS_TINY_ENTRY_HOP_PATH = "ToS/public-compatibility/concept_node.example.json"
TOS_TINY_ENTRY_FALLBACK_PATH = "ToS/doctrine/KNOWLEDGE_MODEL.md"
TOS_ZARATHUSTRA_ROUTE_ID = "thus-spoke-zarathustra/prologue-1"
TOS_ZARATHUSTRA_ROUTE_CAPSULE_PATH = "ToS/zarathustra/prologue-1/TRILINGUAL_ENTRY.md"
TOS_ZARATHUSTRA_ROUTE_SOURCE_NODE_PATH = (
    "ToS/canon/source/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1/node.json"
)
TOS_ZARATHUSTRA_ROUTE_BECOMING_CONCEPT_PATH = "ToS/canon/concept/becoming/node.json"
TOS_ZARATHUSTRA_ROUTE_OVERCOMING_CONCEPT_PATH = "ToS/canon/concept/overcoming/node.json"
TOS_ZARATHUSTRA_ROUTE_LINEAGE_NODE_PATH = (
    "ToS/canon/lineage/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1/"
    "becoming-to-overcoming/node.json"
)
TOS_ZARATHUSTRA_ROUTE_PRINCIPLE_ROOT = (
    "ToS/canon/principle/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1"
)
TOS_ZARATHUSTRA_ROUTE_EVENT_ROOT = (
    "ToS/canon/event/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1"
)
TOS_ZARATHUSTRA_ROUTE_STATE_ROOT = (
    "ToS/canon/state/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1"
)
TOS_ZARATHUSTRA_ROUTE_SUPPORT_ROOT = (
    "ToS/canon/support/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1"
)
TOS_ZARATHUSTRA_ROUTE_ANALOGY_ROOT = (
    "ToS/canon/analogy/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1"
)
TOS_ZARATHUSTRA_ROUTE_SYNTHESIS_ROOT = (
    "ToS/canon/synthesis/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1"
)
TOS_ZARATHUSTRA_ROUTE_RELATION_PACK_PATH = (
    "ToS/canon/relations/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1/edges.csv"
)
TOS_ZARATHUSTRA_ROUTE_PACK_INPUT_REF = TOS_ZARATHUSTRA_ROUTE_PACK_MIN_OUTPUT_REF
TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_ID = (
    f"AOA-K-0011::{TOS_ZARATHUSTRA_ROUTE_ID}"
)
TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER = [
    "source",
    "concept",
    "principle",
    "lineage",
    "event",
    "state",
    "support",
    "analogy",
    "synthesis",
]
TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS = {
    "source": 1,
    "concept": 2,
    "principle": 13,
    "lineage": 1,
    "event": 18,
    "state": 9,
    "support": 46,
    "analogy": 1,
    "synthesis": 1,
}
TOS_ZARATHUSTRA_ROUTE_EDGE_KIND_COUNTS = {
    "source_edge": 92,
    "bridge_edge": 11,
    "principle_edge": 22,
}
TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_SUMMARY = (
    "This surface returns family-level handles for the canonical Zarathustra "
    "prologue-1 route pack so consumers can traverse source, concept, "
    "principle, lineage, event, state, support, analogy, synthesis, and "
    "relation surfaces without ranking or replacing ToS authority."
)
TOS_STANDALONE_ADJUNCT_BUDGET = {
    "max_adjunct_surfaces": 1,
    "max_route_families": 1,
    "numbered_tiny_path_inclusion": "forbidden",
    "default_activation": "opt_in_only",
}
TOS_STANDALONE_ADJUNCT_SUBORDINATE_POSTURE = {
    "adjunct_role": "standalone_handles_only",
    "entry_order": "source_owned_tiny_entry_before_adjunct",
    "source_first_reentry_ref": TOS_TINY_ENTRY_ROUTE_REF,
    "routing_ownership": "forbidden",
    "canon_authorship": "forbidden",
}
REASONING_HANDOFF_GUARDRAIL_REF = "mechanics/checkpoint/parts/reasoning-handoff/docs/reasoning-handoff.md"
REASONING_HANDOFF_GUARDRAIL_SCHEMA_REF = (
    "mechanics/checkpoint/parts/reasoning-handoff/schemas/reasoning-handoff-guardrail.schema.json"
)
COUNTERPART_EDGE_CONTRACT_DOC_REF = (
    "mechanics/boundary-bridge/parts/counterpart-edge/docs/"
    "counterpart-edge-contracts.md"
)
COUNTERPART_EDGE_SCHEMA_REF = (
    "mechanics/boundary-bridge/parts/counterpart-edge/schemas/"
    "counterpart-edge-surface.schema.json"
)
COUNTERPART_EDGE_EXAMPLE_REF = (
    "mechanics/boundary-bridge/parts/counterpart-edge/examples/"
    "counterpart_edge_view.example.json"
)
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_REF = (
    "mechanics/audit/parts/exposure-review/docs/"
    "counterpart-federation-exposure-review.md"
)
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_REF = (
    "mechanics/audit/parts/exposure-review/manifests/"
    "counterpart_federation_exposure_review.json"
)
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_REF = (
    "mechanics/audit/parts/exposure-review/generated/"
    "counterpart_federation_exposure_review.min.json"
)
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_REF = (
    "mechanics/audit/parts/exposure-review/generated/"
    "counterpart_federation_exposure_review.json"
)
COUNTERPART_CONSUMER_CONTRACT_DOC_REF = (
    "mechanics/boundary-bridge/parts/counterpart-edge/docs/"
    "counterpart-consumer-contract.md"
)
COUNTERPART_CONSUMER_CONTRACT_SCHEMA_REF = (
    "mechanics/boundary-bridge/parts/counterpart-edge/schemas/"
    "counterpart-consumer-contract.schema.json"
)
COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_REF = (
    "mechanics/boundary-bridge/parts/counterpart-edge/examples/"
    "counterpart_consumer_contract.example.json"
)
TINY_CONSUMER_BUNDLE_MANIFEST_REF = (
    "mechanics/boundary-bridge/parts/tiny-consumer-bundle/manifests/"
    "tiny_consumer_bundle.json"
)
TINY_CONSUMER_BUNDLE_OUTPUT_REF = (
    "mechanics/boundary-bridge/parts/tiny-consumer-bundle/generated/"
    "tiny_consumer_bundle.json"
)
TINY_CONSUMER_BUNDLE_MIN_OUTPUT_REF = (
    "mechanics/boundary-bridge/parts/tiny-consumer-bundle/generated/"
    "tiny_consumer_bundle.min.json"
)
RETURN_REGROUNDING_MODE_ORDER = [
    "source_export_reentry",
    "bridge_axis_reentry",
    "projection_boundary_reentry",
    "handoff_guardrail_reentry",
    "owner_boundary_reentry",
]
RETURN_REGROUNDING_EXPECTED_INPUT_REFS = {
    "boundaries_doc": "docs/BOUNDARIES.md",
    "bridge_contract_doc": "docs/BRIDGE_CONTRACTS.md",
    "reasoning_handoff_doc": "mechanics/checkpoint/parts/reasoning-handoff/docs/reasoning-handoff.md",
    "source_owned_export_dependencies_manifest": SOURCE_OWNED_EXPORT_DEPENDENCIES_MANIFEST_REF,
    "federation_spine_pack": FEDERATION_SPINE_MIN_OUTPUT_REF,
    "retrieval_axis_pack": "mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_retrieval_axis_pack.min.json",
    "cross_source_projection_pack": CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_REF,
    "reasoning_handoff_pack": "mechanics/checkpoint/parts/reasoning-handoff/generated/reasoning_handoff_pack.min.json",
    "aoa_techniques_kag_export": "aoa-techniques/generated/kag_export.min.json",
    "tos_kag_export": "Tree-of-Sophia/ToS/derived-exports/kag_export.min.json",
    "tos_node_contract": "Tree-of-Sophia/ToS/doctrine/NODE_CONTRACT.md",
    "tos_source_node": "Tree-of-Sophia/ToS/public-compatibility/source_node.example.json",
    "memo_checkpoint_contract": "aoa-memo/mechanics/checkpoint/parts/checkpoint-to-memory-mapping/examples/checkpoint_to_memory_contract.example.json",
    "memo_memory_readiness_boundary": "aoa-memo/mechanics/readiness-boundary/docs/MEMORY_READINESS_BOUNDARY.md",
}
RETURN_REGROUNDING_ALLOWED_SAME_RUN_INPUTS = {
    FEDERATION_SPINE_MIN_OUTPUT_REF,
    "mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_retrieval_axis_pack.min.json",
    CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_REF,
    "mechanics/checkpoint/parts/reasoning-handoff/generated/reasoning_handoff_pack.min.json",
}
RETURN_REGROUNDING_EXPECTED_REGISTRY_POSTURE = {
    "AOA-K-0006": "experimental",
    "AOA-K-0007": "experimental",
    "AOA-K-0008": "planned",
    "AOA-K-0009": "experimental",
}
RETURN_REGROUNDING_MODE_DETAILS = {
    "source_export_reentry": {
        "primary_input": "federation_spine_pack",
        "supporting_inputs": [
            "source_owned_export_dependencies_manifest",
            "aoa_techniques_kag_export",
            "tos_kag_export",
        ],
        "dependency_refs": [
            "aoa-techniques-kag-export",
            "tree-of-sophia-kag-export",
        ],
        "used_when": (
            "Use this mode when a caller needs the strongest current federation "
            "entry back to source-owned export capsules before wider derived "
            "synthesis resumes."
        ),
        "query_mode_hint": "local_search",
        "trigger_surface_refs": [
            FEDERATION_SPINE_MIN_OUTPUT_REF,
            "mechanics/checkpoint/parts/reasoning-handoff/generated/reasoning_handoff_pack.min.json",
        ],
        "stronger_refs": [
            "aoa-techniques/generated/kag_export.min.json",
            "Tree-of-Sophia/ToS/derived-exports/kag_export.min.json",
        ],
        "supporting_surface_refs": [
            "mechanics/boundary-bridge/parts/source-owned-export/manifests/source_owned_export_dependencies.json",
            "mechanics/boundary-bridge/parts/source-owned-export/docs/source-owned-export-dependencies.md",
        ],
        "preserved_fields": [
            "provenance_note",
            "non_identity_boundary",
            "entry_surface_ref",
        ],
        "reentry_note": (
            "Return through the source-owned export capsule and its declared "
            "entry surface before asking the derived layer for broader synthesis."
        ),
        "non_identity_boundary": (
            "The federation spine is a guide to source-owned export entry and "
            "does not replace authored technique meaning or ToS authority."
        ),
        "prohibited_promotions": [
            "source_replacement",
            "routing_ownership",
            "canon_authorship",
        ],
    },
    "bridge_axis_reentry": {
        "primary_input": "retrieval_axis_pack",
        "supporting_inputs": [
            "bridge_contract_doc",
            "tos_node_contract",
            "tos_source_node",
        ],
        "dependency_refs": [],
        "used_when": (
            "Use this mode when retrieval drift appears in the ToS bridge path "
            "and the caller needs explicit source, lineage, conflict, practice, "
            "or memo-linked handles again."
        ),
        "query_mode_hint": "global_search",
        "trigger_surface_refs": [
            "mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_retrieval_axis_pack.min.json",
            "mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/tos_retrieval_axis_surface.example.json",
            "docs/BRIDGE_CONTRACTS.md",
        ],
        "stronger_refs": [
            "Tree-of-Sophia/ToS/public-compatibility/source_node.example.json",
            "Tree-of-Sophia/ToS/doctrine/NODE_CONTRACT.md",
            "Tree-of-Sophia/ToS/doctrine/PRACTICE_BRANCH.md",
        ],
        "supporting_surface_refs": [
            "mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/aoa_tos_bridge_envelope.example.json",
            "aoa-memo/mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/memory_chunk_face.bridge.example.json",
            "aoa-memo/mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/memory_graph_face.bridge.example.json",
        ],
        "preserved_fields": [
            "source_refs",
            "lineage_refs",
            "conflict_refs",
            "practice_refs",
            "axis_summary",
        ],
        "reentry_note": (
            "Return through the retrieval-axis pack so the next pass keeps "
            "bounded handles back to stronger authored surfaces instead of "
            "inventing a wider hidden synthesis."
        ),
        "non_identity_boundary": (
            "The retrieval axis remains a derived bridge surface and does not "
            "replace authored ToS meaning, routing, or proof."
        ),
        "prohibited_promotions": [
            "source_replacement",
            "routing_ownership",
            "graph_normalization",
        ],
    },
    "projection_boundary_reentry": {
        "primary_input": "cross_source_projection_pack",
        "supporting_inputs": [
            "federation_spine_pack",
            "retrieval_axis_pack",
            "bridge_contract_doc",
        ],
        "dependency_refs": [
            "aoa-techniques-kag-export",
            "tree-of-sophia-kag-export",
        ],
        "used_when": (
            "Use this mode when a cross-source projection is being mistaken for "
            "identity, ontology merger, counterpart activation, or graph "
            "expansion."
        ),
        "query_mode_hint": "drift_search",
        "trigger_surface_refs": [
            CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_REF,
            CROSS_SOURCE_NODE_PROJECTION_DOC_REF,
        ],
        "stronger_refs": [
            "aoa-techniques/generated/kag_export.min.json",
            "Tree-of-Sophia/ToS/derived-exports/kag_export.min.json",
        ],
        "supporting_surface_refs": [
            FEDERATION_SPINE_MIN_OUTPUT_REF,
            "mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_retrieval_axis_pack.min.json",
            COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_REF,
        ],
        "preserved_fields": [
            "primary_input",
            "supporting_inputs",
            "retrieval_axis_ref",
            "federation_spine_ref",
            "non_identity_boundary",
        ],
        "reentry_note": (
            "Return through the one-hop projection boundary, then step back to "
            "the source-owned exports and the retrieval axis before any broader "
            "cross-source claim is allowed."
        ),
        "non_identity_boundary": (
            "A cross-source projection is a one-hop pairing, not identity, "
            "counterpart activation, ontology merger, or graph sovereignty."
        ),
        "prohibited_promotions": [
            "counterpart_activation",
            "graph_expansion",
            "source_replacement",
        ],
    },
    "handoff_guardrail_reentry": {
        "primary_input": "reasoning_handoff_pack",
        "supporting_inputs": [
            "reasoning_handoff_doc",
            "boundaries_doc",
            "memo_checkpoint_contract",
            "memo_memory_readiness_boundary",
        ],
        "dependency_refs": [],
        "used_when": (
            "Use this mode when runtime-to-KAG handoff begins to overreach into "
            "routing, memory truth, memory readiness, proof, or canon authorship instead of "
            "staying a guide to stronger refs."
        ),
        "query_mode_hint": "global_search",
        "trigger_surface_refs": [
            "mechanics/checkpoint/parts/reasoning-handoff/docs/reasoning-handoff.md",
            "mechanics/checkpoint/parts/reasoning-handoff/examples/reasoning_handoff_guardrail.example.json",
            "mechanics/checkpoint/parts/reasoning-handoff/generated/reasoning_handoff_pack.min.json",
        ],
        "stronger_refs": [
            "aoa-playbooks/playbooks/operations/orchestration/long-horizon-model-tier-orchestra/PLAYBOOK.md",
            "aoa-playbooks/playbooks/continuity/session-growth/restartable-inquiry-loop/PLAYBOOK.md",
            "aoa-evals/evals/workflow/aoa-long-horizon-depth/EVAL.md",
            "aoa-memo/mechanics/checkpoint/parts/checkpoint-to-memory-mapping/examples/checkpoint_to_memory_contract.example.json",
            "aoa-memo/mechanics/readiness-boundary/docs/MEMORY_READINESS_BOUNDARY.md",
        ],
        "supporting_surface_refs": [
            "mechanics/checkpoint/parts/reasoning-handoff/schemas/reasoning-handoff-guardrail.schema.json",
            "docs/BOUNDARIES.md",
        ],
        "preserved_fields": [
            "source_refs",
            "axis_summary",
            "provenance_note",
            "boundary_guardrails",
        ],
        "reentry_note": (
            "Return to the stronger scenario, eval, and memo refs already named "
            "by the handoff pack rather than extending KAG guidance into "
            "someone else's ownership."
        ),
        "non_identity_boundary": (
            "Reasoning handoff stays a derived guide to source and owner "
            "surfaces, not a new owner of routing, proof, memory truth, scar "
            "or retention readiness, live ledger behavior, or canon."
        ),
        "prohibited_promotions": [
            "routing_ownership",
            "memory_truth_ownership",
            "scar_retention_readiness",
            "live_memory_ledger_ownership",
            "canon_authorship",
            "proof_ownership",
        ],
    },
    "owner_boundary_reentry": {
        "primary_input": "reasoning_handoff_doc",
        "supporting_inputs": [
            "bridge_contract_doc",
            "boundaries_doc",
            "memo_checkpoint_contract",
            "memo_memory_readiness_boundary",
            "tos_node_contract",
        ],
        "dependency_refs": [],
        "used_when": (
            "Use this mode when a caller reaches writeback, memory commitment, "
            "future scar or retention pressure, live ledger pressure, or "
            "canon-facing mutation and KAG must stop at the owner boundary."
        ),
        "query_mode_hint": "consumer_read_path",
        "trigger_surface_refs": [
            "docs/BRIDGE_CONTRACTS.md",
            "mechanics/checkpoint/parts/reasoning-handoff/docs/reasoning-handoff.md",
            "docs/BOUNDARIES.md",
        ],
        "stronger_refs": [
            "aoa-memo/mechanics/checkpoint/parts/checkpoint-to-memory-mapping/examples/checkpoint_to_memory_contract.example.json",
            "aoa-memo/mechanics/readiness-boundary/docs/MEMORY_READINESS_BOUNDARY.md",
            "Tree-of-Sophia/ToS/doctrine/NODE_CONTRACT.md",
            "Tree-of-Sophia/ToS/public-compatibility/source_node.example.json",
        ],
        "supporting_surface_refs": [
            "mechanics/checkpoint/parts/reasoning-handoff/generated/reasoning_handoff_pack.min.json",
            "mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/aoa_tos_bridge_envelope.example.json",
        ],
        "preserved_fields": [
            "source_refs",
            "provenance_note",
            "boundary_guardrails",
        ],
        "reentry_note": (
            "KAG may prepare bounded guidance, but when the next move becomes "
            "memory writeback, memory readiness, or canon mutation "
            "the caller must return to the owner surface instead of extending "
            "derived synthesis."
        ),
        "non_identity_boundary": (
            "Derived bridge substrate does not own memory truth or canon "
            "authorship; it also does not prove scar, retention, or live memory-ledger "
            "readiness and must stop at the owner boundary."
        ),
        "prohibited_promotions": [
            "memory_truth_ownership",
            "scar_retention_proof",
            "live_memory_ledger_ownership",
            "canon_authorship",
            "source_replacement",
        ],
    },
}
