#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from functools import lru_cache
from pathlib import Path

from kag_generation import (
    AOA_AGENTS_ROOT,
    AOA_EVALS_ROOT,
    AOA_MEMO_ROOT,
    AOA_PLAYBOOKS_ROOT,
    AOA_TECHNIQUES_ROOT,
    COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_PATH,
    COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_OUTPUT_PATH,
    COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATH,
    CROSS_SOURCE_NODE_PROJECTION_MANIFEST_PATH,
    CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH,
    CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATH,
    FEDERATION_SPINE_MANIFEST_PATH,
    FEDERATION_SPINE_MIN_OUTPUT_PATH,
    FEDERATION_SPINE_OUTPUT_PATH,
    REGISTRY_MANIFEST_PATH,
    REGISTRY_MIN_OUTPUT_PATH,
    REGISTRY_OUTPUT_PATH,
    REASONING_HANDOFF_MANIFEST_PATH,
    REASONING_HANDOFF_MIN_OUTPUT_PATH,
    REASONING_HANDOFF_OUTPUT_PATH,
    SOURCE_OWNED_EXPORT_DEPENDENCIES_MANIFEST_PATH,
    TECHNIQUE_LIFT_MANIFEST_PATH,
    TECHNIQUE_LIFT_MIN_OUTPUT_PATH,
    TECHNIQUE_LIFT_OUTPUT_PATH,
    TOS_TEXT_CHUNK_MAP_MANIFEST_PATH,
    TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH,
    TOS_TEXT_CHUNK_MAP_OUTPUT_PATH,
    TOS_RETRIEVAL_AXIS_MANIFEST_PATH,
    TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH,
    TOS_RETRIEVAL_AXIS_OUTPUT_PATH,
    TINY_CONSUMER_BUNDLE_MANIFEST_PATH,
    TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH,
    TINY_CONSUMER_BUNDLE_OUTPUT_PATH,
    TOS_REPO,
    TOS_ROOT_README_PATH,
    TOS_TINY_ENTRY_AUTHORITY_PATH,
    TOS_TINY_ENTRY_CAPSULE_PATH,
    TOS_TINY_ENTRY_DOCTRINE_PATH,
    TOS_TINY_ENTRY_FALLBACK_PATH,
    TOS_TINY_ENTRY_HOP_PATH,
    TOS_TINY_ENTRY_ROUTE_ID,
    TOS_TINY_ENTRY_ROUTE_PATH,
    build_cross_source_node_projection_payload,
    build_counterpart_federation_exposure_review_payload,
    build_federation_spine_payload,
    build_registry_payload,
    build_reasoning_handoff_pack_payload,
    build_technique_lift_pack_payload,
    build_tiny_consumer_bundle_payload,
    build_tos_text_chunk_map_payload,
    build_tos_retrieval_axis_pack_payload,
    encode_json,
    repo_ref,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def repo_root_from_env(env_name: str, default: Path) -> Path:
    override = os.environ.get(env_name)
    if not override:
        return default
    return Path(override).expanduser().resolve()


TREE_OF_SOPHIA_ROOT = repo_root_from_env(
    "TREE_OF_SOPHIA_ROOT", REPO_ROOT.parent / "Tree-of-Sophia"
)

SCHEMA_PATH = REPO_ROOT / "schemas" / "kag-registry.schema.json"
BRIDGE_SCHEMA_PATH = REPO_ROOT / "schemas" / "bridge-retrieval-surface.schema.json"
BRIDGE_EXAMPLE_PATH = REPO_ROOT / "examples" / "tos_retrieval_axis_surface.example.json"
BRIDGE_ENVELOPE_SCHEMA_PATH = REPO_ROOT / "schemas" / "bridge-envelope.schema.json"
BRIDGE_ENVELOPE_EXAMPLE_PATH = (
    REPO_ROOT / "examples" / "aoa_tos_bridge_envelope.example.json"
)
COUNTERPART_SCHEMA_PATH = REPO_ROOT / "schemas" / "counterpart-edge-surface.schema.json"
COUNTERPART_EXAMPLE_PATH = REPO_ROOT / "examples" / "counterpart_edge_view.example.json"
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "counterpart-federation-exposure-review-manifest.schema.json"
)
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "counterpart-federation-exposure-review.schema.json"
)
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_EXAMPLE_PATH = (
    REPO_ROOT / "examples" / "counterpart_federation_exposure_review.example.json"
)
COUNTERPART_CONSUMER_CONTRACT_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "counterpart-consumer-contract.schema.json"
)
COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH = (
    REPO_ROOT / "examples" / "counterpart_consumer_contract.example.json"
)
REASONING_HANDOFF_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "reasoning-handoff-guardrail.schema.json"
)
REASONING_HANDOFF_EXAMPLE_PATH = (
    REPO_ROOT / "examples" / "reasoning_handoff_guardrail.example.json"
)
TECHNIQUE_LIFT_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "technique-lift-pack-manifest.schema.json"
)
TECHNIQUE_LIFT_PACK_SCHEMA_PATH = REPO_ROOT / "schemas" / "technique-lift-pack.schema.json"
TOS_TEXT_CHUNK_MAP_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "tos-text-chunk-map-manifest.schema.json"
)
TOS_TEXT_CHUNK_MAP_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "tos-text-chunk-map.schema.json"
)
TOS_TEXT_CHUNK_MAP_EXAMPLE_PATH = (
    REPO_ROOT / "examples" / "tos_text_chunk_map.example.json"
)
TOS_RETRIEVAL_AXIS_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "tos-retrieval-axis-pack-manifest.schema.json"
)
TOS_RETRIEVAL_AXIS_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "tos-retrieval-axis-pack.schema.json"
)
TOS_RETRIEVAL_AXIS_EXAMPLE_PATH = (
    REPO_ROOT / "examples" / "tos_retrieval_axis_pack.example.json"
)
REASONING_HANDOFF_PACK_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "reasoning-handoff-pack-manifest.schema.json"
)
REASONING_HANDOFF_PACK_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "reasoning-handoff-pack.schema.json"
)
SOURCE_OWNED_EXPORT_DEPENDENCIES_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "source-owned-export-dependencies.schema.json"
)
FEDERATION_KAG_EXPORT_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "federation-kag-export.schema.json"
)
FEDERATION_KAG_EXPORT_EXAMPLE_PATH = (
    REPO_ROOT / "examples" / "federation_kag_export.example.json"
)
FEDERATION_SPINE_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "federation-spine-manifest.schema.json"
)
FEDERATION_SPINE_SCHEMA_PATH = REPO_ROOT / "schemas" / "federation-spine.schema.json"
CROSS_SOURCE_NODE_PROJECTION_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "cross-source-node-projection-manifest.schema.json"
)
CROSS_SOURCE_NODE_PROJECTION_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "cross-source-node-projection.schema.json"
)
CROSS_SOURCE_NODE_PROJECTION_EXAMPLE_PATH = (
    REPO_ROOT / "examples" / "cross_source_node_projection.example.json"
)
TINY_CONSUMER_BUNDLE_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "tiny-consumer-bundle-manifest.schema.json"
)
TINY_CONSUMER_BUNDLE_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "tiny-consumer-bundle.schema.json"
)
TINY_CONSUMER_BUNDLE_EXAMPLE_PATH = (
    REPO_ROOT / "examples" / "tiny_consumer_bundle.example.json"
)

ALLOWED_STATUS = {"active", "planned", "experimental", "deprecated"}
ALLOWED_SOURCE_CLASS = {
    "technique_bundle",
    "skill_bundle",
    "eval_bundle",
    "playbook_bundle",
    "memo_object",
    "tos_text",
    "review_surface",
}
ALLOWED_DERIVED_KIND = {
    "section_manifest",
    "metadata_spine",
    "relation_view",
    "provenance_view",
    "chunk_map",
    "node_projection",
    "edge_projection",
    "retrieval_surface",
}
ALLOWED_PROVENANCE = {
    "strict_source_linked",
    "bounded_source_linked",
    "derived_with_handles",
}
ALLOWED_FRAMEWORK = {
    "neutral",
    "hipporag_ready",
    "llamaindex_ready",
    "multi_consumer_ready",
}
ALLOWED_SOURCE_INPUT_ROLE = {"primary", "supporting"}
ALLOWED_COUNTERPART_MODE = {"analogy", "support", "tension", "calibration"}
ALLOWED_QUERY_MODES = {"local_search", "global_search", "drift_search"}
EXPECTED_AUTHORITATIVE_SOURCE_REFS = {
    "Tree-of-Sophia/docs/NODE_CONTRACT.md",
    "Tree-of-Sophia/docs/PRACTICE_BRANCH.md",
    "aoa-memo/docs/WITNESS_TRACE_CONTRACT.md",
}
EXPECTED_DERIVED_SURFACE_REFS = {
    "docs/BRIDGE_CONTRACTS.md#retrieval-axis-contract",
    "examples/tos_retrieval_axis_surface.example.json",
    "docs/COUNTERPART_EDGE_CONTRACTS.md",
    "docs/COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md",
    "examples/counterpart_edge_view.example.json",
    "docs/COUNTERPART_CONSUMER_CONTRACT.md",
    "examples/counterpart_consumer_contract.example.json",
}
EXPECTED_COUNTERPART_CONSUMER_CONTRACT_REFS = {
    "counterpart_contract_doc": "docs/COUNTERPART_EDGE_CONTRACTS.md",
    "counterpart_contract_schema": "schemas/counterpart-edge-surface.schema.json",
    "counterpart_contract_example": "examples/counterpart_edge_view.example.json",
}
EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS = [
    "docs/COUNTERPART_CONSUMER_CONTRACT.md",
    "examples/counterpart_consumer_contract.example.json",
    "docs/COUNTERPART_EDGE_CONTRACTS.md",
    "examples/counterpart_edge_view.example.json",
]
EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_REF = (
    "generated/counterpart_federation_exposure_review.min.json"
)
EXPECTED_COUNTERPART_CONSUMER_FORBIDDEN_INTERPRETATIONS = [
    "identity_proof",
    "routing_authority",
    "graph_sovereign_activation",
    "silent_federation_exposure",
]
EXPECTED_PROVENANCE_POSTURE = {
    "primary_source_required": True,
    "supporting_sources_allowed": True,
    "source_trace_required": True,
    "derived_summary_posture": "guide_to_source_not_source_replacement",
}
EXPECTED_BOUNDARY_GUARDRAILS = {
    "routing_owner": "aoa-routing",
    "memory_owner": "aoa-memo",
    "canon_owner": "Tree-of-Sophia",
    "direct_canon_authorship": "forbidden",
}
EXPECTED_RETURN_MUST_INCLUDE = {"source_refs", "axis_summary", "provenance_note"}
EXPECTED_RETURN_MAY_INCLUDE = {
    "lineage_refs",
    "conflict_refs",
    "practice_refs",
    "counterpart_refs",
}
EXPECTED_TECHNIQUE_LIFT_INPUTS = {
    ("technique_section_manifest", "generated/technique_section_manifest.min.json", "section_manifest"),
    ("technique_catalog", "generated/technique_catalog.json", "metadata_spine"),
    ("technique_evidence_note_manifest", "generated/technique_evidence_note_manifest.min.json", "provenance_handles"),
}
EXPECTED_TECHNIQUE_LIFT_BINDINGS = {
    (
        "AOA-K-0001",
        "technique-section-lift",
        "section_manifest",
        "section_lift",
        "technique_section_manifest",
    ),
    (
        "AOA-K-0002",
        "metadata-spine-projection",
        "metadata_spine",
        "metadata_spine",
        "technique_catalog",
    ),
    (
        "AOA-K-0003",
        "bounded-relation-view",
        "relation_view",
        "relation_view",
        "technique_catalog",
    ),
    (
        "AOA-K-0004",
        "provenance-note-view",
        "provenance_view",
        "provenance_view",
        "technique_evidence_note_manifest",
    ),
}
EXPECTED_TECHNIQUE_LIFT_OUTPUT_PATHS = {
    "full": "generated/technique_lift_pack.json",
    "min": "generated/technique_lift_pack.min.json",
}
EXPECTED_TECHNIQUE_LIFT_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "graph_sovereignty": "forbidden",
}
EXPECTED_TOS_TEXT_CHUNK_MAP_INPUTS = {
    ("tos_source_node", TOS_TINY_ENTRY_AUTHORITY_PATH, "authority_surface"),
    ("tos_tiny_entry_route_doc", TOS_TINY_ENTRY_DOCTRINE_PATH, "route_surface"),
    ("tos_zarathustra_capsule", TOS_TINY_ENTRY_CAPSULE_PATH, "capsule_surface"),
}
EXPECTED_TOS_TEXT_CHUNK_MAP_BINDINGS = {
    (
        "AOA-K-0005",
        "tos-text-chunk-map",
        "chunk_map",
        "chunks",
        "tos_source_node",
    ),
}
EXPECTED_TOS_TEXT_CHUNK_MAP_OUTPUT_PATHS = {
    "full": "generated/tos_text_chunk_map.json",
    "min": "generated/tos_text_chunk_map.min.json",
}
EXPECTED_TOS_TEXT_CHUNK_MAP_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "counterpart_projection": "forbidden",
    "federation_export_activation": "forbidden",
}
EXPECTED_TOS_RETRIEVAL_AXIS_INPUTS = {
    ("tos_text_chunk_map", "aoa-kag", "generated/tos_text_chunk_map.min.json", "chunk_map"),
    ("bridge_contract_doc", "aoa-kag", "docs/BRIDGE_CONTRACTS.md", "bridge_doctrine"),
    ("bridge_surface_example", "aoa-kag", "examples/tos_retrieval_axis_surface.example.json", "bridge_surface"),
    ("bridge_envelope_example", "aoa-kag", "examples/aoa_tos_bridge_envelope.example.json", "bridge_envelope"),
    ("memo_chunk_face", "aoa-memo", "examples/memory_chunk_face.bridge.example.json", "memo_chunk_face"),
    ("memo_graph_face", "aoa-memo", "examples/memory_graph_face.bridge.example.json", "memo_graph_face"),
    ("tos_node_contract", TOS_REPO, "docs/NODE_CONTRACT.md", "tos_contract"),
    ("tos_practice_branch", TOS_REPO, "docs/PRACTICE_BRANCH.md", "tos_contract"),
    ("tos_authority_surface", TOS_REPO, "examples/source_node.example.json", "authority_surface"),
    ("tos_lineage_hop", TOS_REPO, "examples/concept_node.example.json", "lineage_surface"),
}
EXPECTED_TOS_RETRIEVAL_AXIS_BINDINGS = {
    (
        "AOA-K-0007",
        "tos-retrieval-axis-surface",
        "retrieval_surface",
        "axes",
        "tos_text_chunk_map",
    ),
}
EXPECTED_TOS_RETRIEVAL_AXIS_OUTPUT_PATHS = {
    "full": "generated/tos_retrieval_axis_pack.json",
    "min": "generated/tos_retrieval_axis_pack.min.json",
}
EXPECTED_TOS_RETRIEVAL_AXIS_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "scoring_or_ranking": "forbidden",
    "routing_ownership": "forbidden",
    "graph_normalization": "forbidden",
}
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
    ("reasoning_handoff_doc", "aoa-kag", "docs/REASONING_HANDOFF.md", "kag_guardrail_doc"),
    ("reasoning_handoff_schema", "aoa-kag", "schemas/reasoning-handoff-guardrail.schema.json", "kag_guardrail_schema"),
    ("counterpart_consumer_contract_doc", "aoa-kag", "docs/COUNTERPART_CONSUMER_CONTRACT.md", "kag_guardrail_doc"),
    ("counterpart_consumer_contract_schema", "aoa-kag", "schemas/counterpart-consumer-contract.schema.json", "kag_guardrail_schema"),
    ("counterpart_consumer_contract_example", "aoa-kag", "examples/counterpart_consumer_contract.example.json", "kag_guardrail_example"),
    ("counterpart_federation_exposure_review_doc", "aoa-kag", "docs/COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md", "kag_guardrail_doc"),
    ("artifact_to_verdict_hook_schema", "aoa-evals", "schemas/artifact-to-verdict-hook.schema.json", "eval_hook_schema"),
    ("aoa_p_0008_playbook", "aoa-playbooks", "playbooks/long-horizon-model-tier-orchestra/PLAYBOOK.md", "playbook_doc"),
    ("aoa_p_0008_hook", "aoa-evals", "examples/artifact_to_verdict_hook.long-horizon-model-tier-orchestra.example.json", "eval_hook_fixture"),
    ("aoa_p_0009_playbook", "aoa-playbooks", "playbooks/restartable-inquiry-loop/PLAYBOOK.md", "playbook_doc"),
    ("aoa_p_0009_hook", "aoa-evals", "examples/artifact_to_verdict_hook.restartable-inquiry-loop.example.json", "eval_hook_fixture"),
    ("checkpoint_to_memory_contract", "aoa-memo", "examples/checkpoint_to_memory_contract.example.json", "memo_contract_fixture"),
    ("inquiry_checkpoint_schema", "aoa-memo", "schemas/inquiry_checkpoint.schema.json", "memo_schema"),
    ("witness_trace_contract", "aoa-memo", "docs/WITNESS_TRACE_CONTRACT.md", "memo_doc"),
    ("witness_trace_schema", "aoa-memo", "schemas/witness-trace.schema.json", "memo_schema"),
}
EXPECTED_REASONING_HANDOFF_BINDINGS = {
    ("AOA-P-0008", "aoa_p_0008_playbook", "aoa_p_0008_hook", ("checkpoint_to_memory_contract",), None, ("witness_trace_contract", "witness_trace_schema")),
    ("AOA-P-0009", "aoa_p_0009_playbook", "aoa_p_0009_hook", ("checkpoint_to_memory_contract",), "inquiry_checkpoint_schema", ()),
}
EXPECTED_REASONING_HANDOFF_OUTPUT_PATHS = {
    "full": "generated/reasoning_handoff_pack.json",
    "min": "generated/reasoning_handoff_pack.min.json",
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
    "docs/REASONING_HANDOFF.md",
    "schemas/reasoning-handoff-guardrail.schema.json",
    "docs/COUNTERPART_CONSUMER_CONTRACT.md",
    "schemas/counterpart-consumer-contract.schema.json",
    "examples/counterpart_consumer_contract.example.json",
    "docs/COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md",
]
EXPECTED_FEDERATION_SPINE_SOURCE_INPUTS = {
    ("kag_registry_manifest", "aoa-kag", "manifests/kag_registry.json", "registry_manifest"),
    ("aoa_techniques_kag_export", "aoa-techniques", "generated/kag_export.min.json", "source_owned_export"),
    ("tos_kag_export", TOS_REPO, "generated/kag_export.min.json", "source_owned_export"),
}
EXPECTED_FEDERATION_SPINE_SOURCE_INPUT_ORDER = [
    "kag_registry_manifest",
    "aoa_techniques_kag_export",
    "tos_kag_export",
]
EXPECTED_FEDERATION_SPINE_BINDINGS = {
    (
        "AOA-K-0009",
        "aoa-techniques",
        "source_owned_export_tiny",
        "aoa_techniques_kag_export",
    ),
    (
        "AOA-K-0009",
        TOS_REPO,
        "source_owned_export_tiny",
        "tos_kag_export",
    )
}
EXPECTED_FEDERATION_SPINE_REPO_ORDER = ["aoa-techniques", TOS_REPO]
EXPECTED_FEDERATION_SPINE_OUTPUT_PATHS = {
    "full": "generated/federation_spine.json",
    "min": "generated/federation_spine.min.json",
}
EXPECTED_FEDERATION_SPINE_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "routing_ownership": "forbidden",
    "canon_authorship": "forbidden",
    "full_federation_claim": "forbidden",
}
EXPECTED_FEDERATION_SPINE_REPOS = {"aoa-techniques", TOS_REPO}
EXPECTED_CROSS_SOURCE_NODE_PROJECTION_INPUTS = {
    ("aoa_techniques_kag_export", "aoa-techniques", "generated/kag_export.min.json", "primary_export"),
    ("tos_kag_export", TOS_REPO, "generated/kag_export.min.json", "supporting_export"),
    ("tos_retrieval_axis_pack", "aoa-kag", "generated/tos_retrieval_axis_pack.min.json", "retrieval_axis"),
    ("federation_spine", "aoa-kag", "generated/federation_spine.min.json", "federation_spine"),
}
EXPECTED_CROSS_SOURCE_NODE_PROJECTION_BINDINGS = {
    (
        "AOA-K-0006",
        "cross-source-node-projection",
        "node_projection",
        "projections",
        "aoa_techniques_kag_export",
    ),
}
EXPECTED_CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATHS = {
    "full": "generated/cross_source_node_projection.json",
    "min": "generated/cross_source_node_projection.min.json",
}
EXPECTED_CROSS_SOURCE_NODE_PROJECTION_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "counterpart_activation": "forbidden",
    "graph_expansion": "forbidden",
    "routing_ownership": "forbidden",
}
EXPECTED_TINY_CONSUMER_BUNDLE_INPUTS = {
    ("tos_text_chunk_map", "aoa-kag", "generated/tos_text_chunk_map.min.json", "generated_surface"),
    ("tos_retrieval_axis_pack", "aoa-kag", "generated/tos_retrieval_axis_pack.min.json", "generated_surface"),
    ("federation_spine", "aoa-kag", "generated/federation_spine.min.json", "generated_surface"),
    ("cross_source_node_projection", "aoa-kag", "generated/cross_source_node_projection.min.json", "generated_surface"),
    ("consumer_guide", "aoa-kag", "docs/CONSUMER_GUIDE.md", "consumer_doc"),
    ("counterpart_consumer_contract_doc", "aoa-kag", "docs/COUNTERPART_CONSUMER_CONTRACT.md", "counterpart_contract"),
    ("counterpart_consumer_contract_example", "aoa-kag", "examples/counterpart_consumer_contract.example.json", "counterpart_contract"),
}
EXPECTED_TINY_CONSUMER_BUNDLE_ORDER = [
    "tos_text_chunk_map",
    "tos_retrieval_axis_pack",
    "federation_spine",
    "cross_source_node_projection",
    "consumer_guide",
    "counterpart_consumer_contract_doc",
    "counterpart_consumer_contract_example",
]
EXPECTED_TINY_CONSUMER_BUNDLE_OUTPUT_PATHS = {
    "full": "generated/tiny_consumer_bundle.json",
    "min": "generated/tiny_consumer_bundle.min.json",
}
EXPECTED_TINY_CONSUMER_BUNDLE_DEFERRED_COUNTERPART = {
    "surface_id": "AOA-K-0008",
    "surface_status": "planned",
    "posture": "planned_contract_only",
    "federation_exposure_review_ref": EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_REF,
    "allowed_refs": EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS,
    "forbidden_active_payload_refs": ["examples/counterpart_edge_view.example.json"],
    "forbidden_interpretations": [
        "active_retrieval_payload",
        "active_projection_payload",
    ],
}
EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_INPUTS = {
    ("reasoning_handoff_pack", "aoa-kag", "generated/reasoning_handoff_pack.min.json", "reviewed_surface"),
    ("tiny_consumer_bundle", "aoa-kag", "generated/tiny_consumer_bundle.min.json", "reviewed_surface"),
    ("federation_spine", "aoa-kag", "generated/federation_spine.min.json", "reviewed_surface"),
    ("cross_source_node_projection", "aoa-kag", "generated/cross_source_node_projection.min.json", "reviewed_surface"),
    ("counterpart_consumer_contract_doc", "aoa-kag", "docs/COUNTERPART_CONSUMER_CONTRACT.md", "counterpart_contract"),
    ("counterpart_consumer_contract_example", "aoa-kag", "examples/counterpart_consumer_contract.example.json", "counterpart_contract"),
    ("counterpart_edge_contract_doc", "aoa-kag", "docs/COUNTERPART_EDGE_CONTRACTS.md", "counterpart_contract"),
    ("counterpart_edge_contract_example", "aoa-kag", "examples/counterpart_edge_view.example.json", "counterpart_contract"),
}
EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_ORDER = [
    "reasoning_handoff_pack",
    "tiny_consumer_bundle",
    "federation_spine",
    "cross_source_node_projection",
    "counterpart_consumer_contract_doc",
    "counterpart_consumer_contract_example",
    "counterpart_edge_contract_doc",
    "counterpart_edge_contract_example",
]
EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATHS = {
    "full": "generated/counterpart_federation_exposure_review.json",
    "min": "generated/counterpart_federation_exposure_review.min.json",
}
EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_CONTRACT = {
    "silent_federation_exposure": "forbidden",
    "generated_counterpart_payload_inference": "forbidden",
    "routing_ownership": "forbidden",
    "source_replacement": "forbidden",
}
EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_POSTURES = {
    "reasoning_handoff_pack": "contract_only_counterpart_refs",
    "tiny_consumer_bundle": "planned_contract_only",
    "federation_spine": "no_counterpart_exposure",
    "cross_source_node_projection": "counterpart_activation_forbidden",
    "counterpart_consumer_contract_doc": "contract_reference_surface",
    "counterpart_consumer_contract_example": "contract_reference_surface",
    "counterpart_edge_contract_doc": "planned_contract_surface",
    "counterpart_edge_contract_example": "planned_example_surface",
}
EXPECTED_AOA_K_0006_SOURCE_INPUTS = [
    {
        "repo": "aoa-techniques",
        "source_class": "technique_bundle",
        "role": "primary",
    },
    {
        "repo": TOS_REPO,
        "source_class": "tos_text",
        "role": "supporting",
    },
]
EXPECTED_AOA_K_0009_SOURCE_INPUTS = [
    {
        "repo": "aoa-techniques",
        "source_class": "review_surface",
        "role": "primary",
    },
    {
        "repo": TOS_REPO,
        "source_class": "tos_text",
        "role": "supporting",
    },
]
MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VISIBLE_ROOTS = (
    REPO_ROOT,
    AOA_TECHNIQUES_ROOT,
    AOA_PLAYBOOKS_ROOT,
    AOA_EVALS_ROOT,
    AOA_MEMO_ROOT,
    AOA_AGENTS_ROOT,
    TREE_OF_SOPHIA_ROOT,
)


class ValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def display_path(path: Path) -> str:
    for root in VISIBLE_ROOTS:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            continue
    return path.as_posix()


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing required file: {display_path(path)}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {display_path(path)}: {exc}")


def markdown_anchor(text: str) -> str:
    anchor = text.strip().lower()
    anchor = re.sub(r"[^\w\s-]", "", anchor)
    anchor = re.sub(r"\s+", "-", anchor)
    anchor = re.sub(r"-+", "-", anchor)
    return anchor.strip("-")


@lru_cache(maxsize=None)
def markdown_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    seen: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = MARKDOWN_HEADING.match(line)
        if not match:
            continue
        base = markdown_anchor(match.group(2))
        if not base:
            continue
        suffix = seen.get(base, 0)
        seen[base] = suffix + 1
        anchors.add(base if suffix == 0 else f"{base}-{suffix}")
    return anchors


def validate_top_level_schema(path: Path, label: str) -> None:
    schema = read_json(path)
    if not isinstance(schema, dict):
        fail(f"{label} schema file must contain a JSON object")
    required_top_level = {"$schema", "$id", "title", "type", "properties", "required"}
    missing = sorted(required_top_level - set(schema))
    if missing:
        fail(f"{label} schema is missing required top-level keys: {', '.join(missing)}")


def validate_schema_surface() -> None:
    validate_top_level_schema(SCHEMA_PATH, "registry")


def validate_bridge_schema_surface() -> None:
    validate_top_level_schema(BRIDGE_SCHEMA_PATH, "bridge")


def validate_bridge_envelope_schema_surface() -> None:
    validate_top_level_schema(BRIDGE_ENVELOPE_SCHEMA_PATH, "bridge envelope")


def validate_counterpart_schema_surface() -> None:
    validate_top_level_schema(COUNTERPART_SCHEMA_PATH, "counterpart")


def validate_counterpart_federation_exposure_review_manifest_schema_surface() -> None:
    validate_top_level_schema(
        COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_SCHEMA_PATH,
        "counterpart federation exposure review manifest",
    )


def validate_counterpart_federation_exposure_review_schema_surface() -> None:
    validate_top_level_schema(
        COUNTERPART_FEDERATION_EXPOSURE_REVIEW_SCHEMA_PATH,
        "counterpart federation exposure review",
    )


def validate_counterpart_consumer_contract_schema_surface() -> None:
    validate_top_level_schema(
        COUNTERPART_CONSUMER_CONTRACT_SCHEMA_PATH,
        "counterpart consumer contract",
    )


def validate_reasoning_handoff_schema_surface() -> None:
    validate_top_level_schema(REASONING_HANDOFF_SCHEMA_PATH, "reasoning handoff")


def validate_technique_lift_manifest_schema_surface() -> None:
    validate_top_level_schema(TECHNIQUE_LIFT_MANIFEST_SCHEMA_PATH, "technique lift manifest")


def validate_technique_lift_pack_schema_surface() -> None:
    validate_top_level_schema(TECHNIQUE_LIFT_PACK_SCHEMA_PATH, "technique lift pack")


def validate_tos_text_chunk_map_manifest_schema_surface() -> None:
    validate_top_level_schema(
        TOS_TEXT_CHUNK_MAP_MANIFEST_SCHEMA_PATH,
        "ToS text chunk map manifest",
    )


def validate_tos_text_chunk_map_schema_surface() -> None:
    validate_top_level_schema(TOS_TEXT_CHUNK_MAP_SCHEMA_PATH, "ToS text chunk map")


def validate_tos_retrieval_axis_manifest_schema_surface() -> None:
    validate_top_level_schema(
        TOS_RETRIEVAL_AXIS_MANIFEST_SCHEMA_PATH,
        "ToS retrieval axis manifest",
    )


def validate_tos_retrieval_axis_schema_surface() -> None:
    validate_top_level_schema(TOS_RETRIEVAL_AXIS_SCHEMA_PATH, "ToS retrieval axis pack")


def validate_reasoning_handoff_pack_manifest_schema_surface() -> None:
    validate_top_level_schema(
        REASONING_HANDOFF_PACK_MANIFEST_SCHEMA_PATH,
        "reasoning handoff pack manifest",
    )


def validate_reasoning_handoff_pack_schema_surface() -> None:
    validate_top_level_schema(
        REASONING_HANDOFF_PACK_SCHEMA_PATH,
        "reasoning handoff pack",
    )


def validate_source_owned_export_dependencies_schema_surface() -> None:
    validate_top_level_schema(
        SOURCE_OWNED_EXPORT_DEPENDENCIES_SCHEMA_PATH,
        "source-owned export dependency manifest",
    )


def validate_federation_kag_export_schema_surface() -> None:
    validate_top_level_schema(
        FEDERATION_KAG_EXPORT_SCHEMA_PATH,
        "federation KAG export",
    )


def validate_federation_spine_manifest_schema_surface() -> None:
    validate_top_level_schema(
        FEDERATION_SPINE_MANIFEST_SCHEMA_PATH,
        "federation spine manifest",
    )


def validate_federation_spine_schema_surface() -> None:
    validate_top_level_schema(
        FEDERATION_SPINE_SCHEMA_PATH,
        "federation spine",
    )


def validate_cross_source_node_projection_manifest_schema_surface() -> None:
    validate_top_level_schema(
        CROSS_SOURCE_NODE_PROJECTION_MANIFEST_SCHEMA_PATH,
        "cross-source node projection manifest",
    )


def validate_cross_source_node_projection_schema_surface() -> None:
    validate_top_level_schema(
        CROSS_SOURCE_NODE_PROJECTION_SCHEMA_PATH,
        "cross-source node projection",
    )


def validate_tiny_consumer_bundle_manifest_schema_surface() -> None:
    validate_top_level_schema(
        TINY_CONSUMER_BUNDLE_MANIFEST_SCHEMA_PATH,
        "tiny consumer bundle manifest",
    )


def validate_tiny_consumer_bundle_schema_surface() -> None:
    validate_top_level_schema(TINY_CONSUMER_BUNDLE_SCHEMA_PATH, "tiny consumer bundle")


def validate_unique_string_list(
    value: object,
    *,
    label: str,
    allow_empty: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        fail(f"{label} must be a list")
    if not value and not allow_empty:
        fail(f"{label} must be a non-empty list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or len(item) < 1:
            fail(f"{label} contains an invalid entry")
        result.append(item)
    if len(result) != len(set(result)):
        fail(f"{label} must not contain duplicates")
    return result


def iter_string_values(value: object):
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for nested_value in value.values():
            yield from iter_string_values(nested_value)
        return
    if isinstance(value, list):
        for nested_value in value:
            yield from iter_string_values(nested_value)


def resolve_relative_ref(root: Path, raw_ref: str, *, label: str) -> Path:
    path_text, _, anchor = raw_ref.partition("#")
    target = root / path_text
    if not target.exists():
        fail(f"{label} references a missing path: {raw_ref}")
    if anchor:
        if target.suffix.lower() != ".md":
            fail(f"{label} uses a markdown anchor on a non-markdown target: {raw_ref}")
        if anchor not in markdown_anchors(target):
            fail(f"{label} references a missing markdown anchor: {raw_ref}")
    return target


def resolve_authoritative_ref(raw_ref: str, *, label: str) -> Path:
    if raw_ref.startswith("Tree-of-Sophia/"):
        return resolve_relative_ref(
            TREE_OF_SOPHIA_ROOT,
            raw_ref.split("/", 1)[1],
            label=label,
        )
    if raw_ref.startswith("aoa-memo/"):
        return resolve_relative_ref(
            AOA_MEMO_ROOT,
            raw_ref.split("/", 1)[1],
            label=label,
        )
    fail(f"{label} must reference Tree-of-Sophia or aoa-memo: {raw_ref}")


def resolve_aoa_techniques_ref(raw_ref: str, *, label: str) -> Path:
    if not raw_ref.startswith("aoa-techniques/"):
        fail(f"{label} must reference aoa-techniques: {raw_ref}")
    return resolve_relative_ref(
        AOA_TECHNIQUES_ROOT,
        raw_ref.split("/", 1)[1],
        label=label,
    )


def resolve_aoa_playbooks_ref(raw_ref: str, *, label: str) -> Path:
    if not raw_ref.startswith("aoa-playbooks/"):
        fail(f"{label} must reference aoa-playbooks: {raw_ref}")
    return resolve_relative_ref(
        AOA_PLAYBOOKS_ROOT,
        raw_ref.split("/", 1)[1],
        label=label,
    )


def resolve_aoa_evals_ref(raw_ref: str, *, label: str) -> Path:
    if not raw_ref.startswith("aoa-evals/"):
        fail(f"{label} must reference aoa-evals: {raw_ref}")
    return resolve_relative_ref(
        AOA_EVALS_ROOT,
        raw_ref.split("/", 1)[1],
        label=label,
    )


def resolve_aoa_agents_ref(raw_ref: str, *, label: str) -> Path:
    if not raw_ref.startswith("aoa-agents/"):
        fail(f"{label} must reference aoa-agents: {raw_ref}")
    return resolve_relative_ref(
        AOA_AGENTS_ROOT,
        raw_ref.split("/", 1)[1],
        label=label,
    )


def resolve_known_ref(raw_ref: str, *, label: str) -> Path:
    if raw_ref.startswith("aoa-techniques/"):
        return resolve_aoa_techniques_ref(raw_ref, label=label)
    if raw_ref.startswith("aoa-playbooks/"):
        return resolve_aoa_playbooks_ref(raw_ref, label=label)
    if raw_ref.startswith("aoa-evals/"):
        return resolve_aoa_evals_ref(raw_ref, label=label)
    if raw_ref.startswith("aoa-memo/"):
        return resolve_relative_ref(
            AOA_MEMO_ROOT,
            raw_ref.split("/", 1)[1],
            label=label,
        )
    if raw_ref.startswith("aoa-agents/"):
        return resolve_aoa_agents_ref(raw_ref, label=label)
    if raw_ref.startswith("Tree-of-Sophia/"):
        return resolve_relative_ref(
            TREE_OF_SOPHIA_ROOT,
            raw_ref.split("/", 1)[1],
            label=label,
        )
    return resolve_relative_ref(REPO_ROOT, raw_ref, label=label)


def validate_exact_set(
    values: list[str] | set[str],
    expected: set[str],
    *,
    label: str,
) -> None:
    if set(values) != expected:
        fail(f"{label} must match the exact expected set")


def validate_tos_relative_surface(raw_ref: object, *, label: str) -> str:
    if not isinstance(raw_ref, str) or not raw_ref.strip():
        fail(f"{label} must be a non-empty Tree-of-Sophia-relative path")
    normalized = raw_ref.replace("\\", "/")
    if re.match(r"^[A-Za-z]:[/\\\\]", normalized) or normalized.startswith(("/", "\\")):
        fail(f"{label} must be Tree-of-Sophia-relative, not absolute")
    if ".." in Path(normalized).parts:
        fail(f"{label} must not traverse outside Tree-of-Sophia")
    if ":" in normalized:
        fail(f"{label} must stay Tree-of-Sophia-relative and must not use repo-qualified refs")
    if normalized.startswith(("aoa-kag/", "aoa-routing/")):
        fail(f"{label} must stay inside Tree-of-Sophia and must not point at downstream repos")
    resolve_relative_ref(TREE_OF_SOPHIA_ROOT, normalized, label=label)
    return normalized


def validate_tos_tiny_entry_route() -> dict[str, object]:
    route_label = repo_ref(TOS_REPO, TOS_TINY_ENTRY_ROUTE_PATH)
    payload = read_json(TREE_OF_SOPHIA_ROOT / TOS_TINY_ENTRY_ROUTE_PATH)
    if not isinstance(payload, dict):
        fail("Tree-of-Sophia tiny-entry route must be a JSON object")

    route_id = payload.get("route_id")
    if route_id != TOS_TINY_ENTRY_ROUTE_ID:
        fail(f"{route_label}.route_id must stay '{TOS_TINY_ENTRY_ROUTE_ID}'")

    root_surface = validate_tos_relative_surface(
        payload.get("root_surface"),
        label=f"{route_label}.root_surface",
    )
    if root_surface != TOS_ROOT_README_PATH:
        fail(f"{route_label}.root_surface must stay '{TOS_ROOT_README_PATH}'")

    if not isinstance(payload.get("node_kind"), str) or not payload["node_kind"]:
        fail(f"{route_label}.node_kind must be a non-empty string")
    if not isinstance(payload.get("node_id"), str) or not payload["node_id"]:
        fail(f"{route_label}.node_id must be a non-empty string")

    capsule_surface = validate_tos_relative_surface(
        payload.get("capsule_surface"),
        label=f"{route_label}.capsule_surface",
    )
    if capsule_surface != TOS_TINY_ENTRY_CAPSULE_PATH:
        fail(f"{route_label}.capsule_surface must stay '{TOS_TINY_ENTRY_CAPSULE_PATH}'")

    authority_surface = validate_tos_relative_surface(
        payload.get("authority_surface"),
        label=f"{route_label}.authority_surface",
    )
    if authority_surface != TOS_TINY_ENTRY_AUTHORITY_PATH:
        fail(f"{route_label}.authority_surface must stay '{TOS_TINY_ENTRY_AUTHORITY_PATH}'")

    lineage_or_context_hop = validate_tos_relative_surface(
        payload.get("lineage_or_context_hop"),
        label=f"{route_label}.lineage_or_context_hop",
    )
    if lineage_or_context_hop != TOS_TINY_ENTRY_HOP_PATH:
        fail(f"{route_label}.lineage_or_context_hop must stay '{TOS_TINY_ENTRY_HOP_PATH}'")

    fallback = validate_tos_relative_surface(
        payload.get("fallback"),
        label=f"{route_label}.fallback",
    )
    if fallback != TOS_TINY_ENTRY_FALLBACK_PATH:
        fail(f"{route_label}.fallback must stay '{TOS_TINY_ENTRY_FALLBACK_PATH}'")

    boundary = payload.get("non_identity_boundary")
    if not isinstance(boundary, str) or not boundary.strip():
        fail(f"{route_label}.non_identity_boundary must be a non-empty string")
    if "aoa-kag" not in boundary or "aoa-routing" not in boundary:
        fail(f"{route_label}.non_identity_boundary must explicitly keep aoa-kag and aoa-routing downstream")

    return payload


def validate_registry_payload(
    payload: object,
    *,
    label: str,
) -> dict[str, dict[str, object]]:
    if not isinstance(payload, dict):
        fail(f"{label} must be a JSON object")

    for key in ("version", "layer", "surfaces"):
        if key not in payload:
            fail(f"{label} is missing required key '{key}'")

    if not isinstance(payload["version"], int) or payload["version"] < 1:
        fail(f"{label} 'version' must be an integer >= 1")
    if payload["layer"] != "aoa-kag":
        fail(f"{label} 'layer' must equal 'aoa-kag'")

    surfaces = payload["surfaces"]
    if not isinstance(surfaces, list) or not surfaces:
        fail(f"{label} 'surfaces' must be a non-empty list")

    seen_ids: set[str] = set()
    required_seed = {
        "technique-section-lift",
        "metadata-spine-projection",
        "bounded-relation-view",
        "provenance-note-view",
        "tos-text-chunk-map",
        "cross-source-node-projection",
        "tos-retrieval-axis-surface",
        "counterpart-edge-view",
        "federation-readiness-spine",
    }
    seen_names: set[str] = set()
    surfaces_by_id: dict[str, dict[str, object]] = {}

    for index, surface in enumerate(surfaces):
        location = f"{label} surfaces[{index}]"
        if not isinstance(surface, dict):
            fail(f"{location} must be an object")

        for key in (
            "id",
            "name",
            "status",
            "summary",
            "source_class",
            "derived_kind",
            "provenance_mode",
            "normalization_scope",
            "framework_readiness",
            "source_repos",
        ):
            if key not in surface:
                fail(f"{location} is missing required key '{key}'")

        surface_id = surface["id"]
        name = surface["name"]
        status = surface["status"]
        summary = surface["summary"]
        source_class = surface["source_class"]
        derived_kind = surface["derived_kind"]
        provenance_mode = surface["provenance_mode"]
        normalization_scope = surface["normalization_scope"]
        framework_readiness = surface["framework_readiness"]
        source_repos = surface["source_repos"]
        source_inputs = surface.get("source_inputs")

        if not isinstance(surface_id, str) or len(surface_id) < 3:
            fail(f"{location}.id must be a string of length >= 3")
        if surface_id in seen_ids:
            fail(f"duplicate KAG surface id in {label}: '{surface_id}'")
        seen_ids.add(surface_id)
        surfaces_by_id[surface_id] = surface

        if not isinstance(name, str) or len(name) < 3:
            fail(f"{location}.name must be a string of length >= 3")
        if name in seen_names:
            fail(f"duplicate KAG surface name in {label}: '{name}'")
        seen_names.add(name)
        if status not in ALLOWED_STATUS:
            fail(f"{location}.status '{status}' is not allowed")
        if not isinstance(summary, str) or len(summary) < 10:
            fail(f"{location}.summary must be a string of length >= 10")
        if source_class not in ALLOWED_SOURCE_CLASS:
            fail(f"{location}.source_class '{source_class}' is not allowed")
        if derived_kind not in ALLOWED_DERIVED_KIND:
            fail(f"{location}.derived_kind '{derived_kind}' is not allowed")
        if provenance_mode not in ALLOWED_PROVENANCE:
            fail(f"{location}.provenance_mode '{provenance_mode}' is not allowed")
        if not isinstance(normalization_scope, str) or len(normalization_scope) < 3:
            fail(f"{location}.normalization_scope must be a string of length >= 3")
        if framework_readiness not in ALLOWED_FRAMEWORK:
            fail(f"{location}.framework_readiness '{framework_readiness}' is not allowed")
        if not isinstance(source_repos, list) or not source_repos:
            fail(f"{location}.source_repos must be a non-empty list")
        for repo in source_repos:
            if not isinstance(repo, str) or len(repo) < 2:
                fail(f"{location}.source_repos contains an invalid entry")

        if source_inputs is not None:
            if not isinstance(source_inputs, list) or not source_inputs:
                fail(f"{location}.source_inputs must be a non-empty list when present")

            primary_count = 0
            input_repos: set[str] = set()
            for input_index, source_input in enumerate(source_inputs):
                input_location = f"{location}.source_inputs[{input_index}]"
                if not isinstance(source_input, dict):
                    fail(f"{input_location} must be an object")
                for key in ("repo", "source_class", "role"):
                    if key not in source_input:
                        fail(f"{input_location} is missing required key '{key}'")

                input_repo = source_input["repo"]
                input_source_class = source_input["source_class"]
                input_role = source_input["role"]

                if not isinstance(input_repo, str) or len(input_repo) < 2:
                    fail(f"{input_location}.repo must be a string of length >= 2")
                if input_repo not in source_repos:
                    fail(f"{input_location}.repo '{input_repo}' must also appear in source_repos")
                if input_repo in input_repos:
                    fail(f"{input_location}.repo '{input_repo}' is duplicated")
                input_repos.add(input_repo)

                if input_source_class not in ALLOWED_SOURCE_CLASS:
                    fail(f"{input_location}.source_class '{input_source_class}' is not allowed")
                if input_role not in ALLOWED_SOURCE_INPUT_ROLE:
                    fail(f"{input_location}.role '{input_role}' is not allowed")
                if input_role == "primary":
                    primary_count += 1
                    if input_source_class != source_class:
                        fail(
                            f"{input_location}.source_class must match top-level source_class for the primary input"
                        )

            if primary_count != 1:
                fail(f"{location}.source_inputs must contain exactly one primary input")

        if len(source_repos) > 1 and source_inputs is None:
            fail(f"{location}.source_inputs is required when more than one source repo is declared")

    missing_seed = sorted(required_seed - seen_names)
    if missing_seed:
        fail(f"{label} is missing required seed surfaces: {', '.join(missing_seed)}")
    validate_special_registry_surfaces(surfaces_by_id, label=label)
    return surfaces_by_id


def validate_special_registry_surfaces(
    surfaces_by_id: dict[str, dict[str, object]],
    *,
    label: str,
) -> None:
    surface_0005 = surfaces_by_id.get("AOA-K-0005")
    if surface_0005 is None:
        fail(f"{label} is missing required surface 'AOA-K-0005'")
    if surface_0005.get("name") != "tos-text-chunk-map":
        fail(f"{label} AOA-K-0005 must keep name 'tos-text-chunk-map'")
    if surface_0005.get("status") != "experimental":
        fail(f"{label} AOA-K-0005 must be experimental in the current Wave 2 pilot")
    if surface_0005.get("source_class") != "tos_text":
        fail(f"{label} AOA-K-0005 must keep 'tos_text' as its primary source_class")
    if surface_0005.get("derived_kind") != "chunk_map":
        fail(f"{label} AOA-K-0005 must keep 'chunk_map' as its derived_kind")
    if surface_0005.get("provenance_mode") != "strict_source_linked":
        fail(f"{label} AOA-K-0005 must keep 'strict_source_linked' as its provenance_mode")
    if surface_0005.get("normalization_scope") != "text_chunks":
        fail(f"{label} AOA-K-0005 must keep 'text_chunks' as its normalization_scope")
    if surface_0005.get("framework_readiness") != "llamaindex_ready":
        fail(f"{label} AOA-K-0005 must keep 'llamaindex_ready' as its framework_readiness")
    if surface_0005.get("source_repos") != [TOS_REPO]:
        fail(f"{label} AOA-K-0005 must keep source_repos ['{TOS_REPO}']")

    surface_0006 = surfaces_by_id.get("AOA-K-0006")
    if surface_0006 is None:
        fail(f"{label} is missing required surface 'AOA-K-0006'")
    if surface_0006.get("name") != "cross-source-node-projection":
        fail(f"{label} AOA-K-0006 must keep name 'cross-source-node-projection'")
    if surface_0006.get("status") != "experimental":
        fail(f"{label} AOA-K-0006 must be experimental in the current Wave 5 pilot")
    if surface_0006.get("source_class") != "technique_bundle":
        fail(f"{label} AOA-K-0006 must keep 'technique_bundle' as its primary source_class")
    if surface_0006.get("derived_kind") != "node_projection":
        fail(f"{label} AOA-K-0006 must keep 'node_projection' as its derived_kind")
    if surface_0006.get("provenance_mode") != "derived_with_handles":
        fail(f"{label} AOA-K-0006 must keep 'derived_with_handles' as its provenance_mode")
    if surface_0006.get("normalization_scope") != "cross_source_nodes":
        fail(f"{label} AOA-K-0006 must keep 'cross_source_nodes' as its normalization_scope")
    if surface_0006.get("framework_readiness") != "multi_consumer_ready":
        fail(f"{label} AOA-K-0006 must keep 'multi_consumer_ready' as its framework_readiness")
    if surface_0006.get("source_repos") != ["aoa-techniques", TOS_REPO]:
        fail(f"{label} AOA-K-0006 must keep source_repos ['aoa-techniques', '{TOS_REPO}']")
    if surface_0006.get("source_inputs") != EXPECTED_AOA_K_0006_SOURCE_INPUTS:
        fail(f"{label} AOA-K-0006 must keep the current primary/supporting source_inputs mapping")

    surface_0007 = surfaces_by_id.get("AOA-K-0007")
    if surface_0007 is None:
        fail(f"{label} is missing required surface 'AOA-K-0007'")
    if surface_0007.get("name") != "tos-retrieval-axis-surface":
        fail(f"{label} AOA-K-0007 must keep name 'tos-retrieval-axis-surface'")
    if surface_0007.get("status") != "experimental":
        fail(f"{label} AOA-K-0007 must be experimental in the current Wave 3 pilot")
    if surface_0007.get("source_class") != "tos_text":
        fail(f"{label} AOA-K-0007 must keep 'tos_text' as its primary source_class")
    if surface_0007.get("derived_kind") != "retrieval_surface":
        fail(f"{label} AOA-K-0007 must keep 'retrieval_surface' as its derived_kind")
    if surface_0007.get("provenance_mode") != "derived_with_handles":
        fail(f"{label} AOA-K-0007 must keep 'derived_with_handles' as its provenance_mode")
    if surface_0007.get("normalization_scope") != "axis_bundles":
        fail(f"{label} AOA-K-0007 must keep 'axis_bundles' as its normalization_scope")
    if surface_0007.get("framework_readiness") != "hipporag_ready":
        fail(f"{label} AOA-K-0007 must keep 'hipporag_ready' as its framework_readiness")
    if surface_0007.get("source_repos") != [TOS_REPO, "aoa-memo"]:
        fail(f"{label} AOA-K-0007 must keep source_repos ['{TOS_REPO}', 'aoa-memo']")

    surface_0008 = surfaces_by_id.get("AOA-K-0008")
    if surface_0008 is None:
        fail(f"{label} is missing required surface 'AOA-K-0008'")
    if surface_0008.get("name") != "counterpart-edge-view":
        fail(f"{label} AOA-K-0008 must keep name 'counterpart-edge-view'")
    if surface_0008.get("status") != "planned":
        fail(f"{label} AOA-K-0008 must remain planned")
    if surface_0008.get("source_class") != "tos_text":
        fail(f"{label} AOA-K-0008 must keep 'tos_text' as its primary source_class")
    if surface_0008.get("derived_kind") != "edge_projection":
        fail(f"{label} AOA-K-0008 must keep 'edge_projection' as its derived_kind")

    source_inputs = surface_0008.get("source_inputs")
    if not isinstance(source_inputs, list):
        fail(f"{label} AOA-K-0008 must declare source_inputs")
    expected_inputs = {
        ("Tree-of-Sophia", "tos_text", "primary"),
        ("aoa-techniques", "technique_bundle", "supporting"),
        ("aoa-playbooks", "playbook_bundle", "supporting"),
        ("aoa-evals", "eval_bundle", "supporting"),
    }
    actual_inputs = {
        (item.get("repo"), item.get("source_class"), item.get("role"))
        for item in source_inputs
        if isinstance(item, dict)
    }
    if actual_inputs != expected_inputs:
        fail(f"{label} AOA-K-0008 source_inputs must match the current counterpart bridge source contract")

    surface_0009 = surfaces_by_id.get("AOA-K-0009")
    if surface_0009 is None:
        fail(f"{label} is missing required surface 'AOA-K-0009'")
    if surface_0009.get("name") != "federation-readiness-spine":
        fail(f"{label} AOA-K-0009 must keep name 'federation-readiness-spine'")
    if surface_0009.get("status") != "experimental":
        fail(f"{label} AOA-K-0009 must remain experimental")
    if surface_0009.get("source_class") != "review_surface":
        fail(f"{label} AOA-K-0009 must keep 'review_surface' as its primary source_class")
    if surface_0009.get("derived_kind") != "metadata_spine":
        fail(f"{label} AOA-K-0009 must keep 'metadata_spine' as its derived_kind")
    if surface_0009.get("provenance_mode") != "derived_with_handles":
        fail(f"{label} AOA-K-0009 must keep 'derived_with_handles' as its provenance_mode")
    if surface_0009.get("normalization_scope") != "repo_entry_surfaces":
        fail(f"{label} AOA-K-0009 must keep 'repo_entry_surfaces' as its normalization_scope")
    if surface_0009.get("framework_readiness") != "neutral":
        fail(f"{label} AOA-K-0009 must keep 'neutral' as its framework_readiness")
    if surface_0009.get("source_repos") != ["aoa-techniques", TOS_REPO]:
        fail(f"{label} AOA-K-0009 must keep source_repos ['aoa-techniques', '{TOS_REPO}']")
    if surface_0009.get("source_inputs") != EXPECTED_AOA_K_0009_SOURCE_INPUTS:
        fail(f"{label} AOA-K-0009 must keep the current two-repo source_inputs mapping")


def validate_technique_lift_manifest(
    surfaces_by_id: dict[str, dict[str, object]],
) -> None:
    payload = read_json(TECHNIQUE_LIFT_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("technique lift manifest must be a JSON object")

    for key in (
        "manifest_version",
        "pack_type",
        "source_repo",
        "source_root_env",
        "source_inputs",
        "surface_bindings",
        "output_paths",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"technique lift manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("technique lift manifest manifest_version must equal 1")
    if payload["pack_type"] != "technique_lift_pack":
        fail("technique lift manifest pack_type must equal 'technique_lift_pack'")
    if payload["source_repo"] != "aoa-techniques":
        fail("technique lift manifest source_repo must equal 'aoa-techniques'")
    if payload["source_root_env"] != "AOA_TECHNIQUES_ROOT":
        fail("technique lift manifest source_root_env must equal 'AOA_TECHNIQUES_ROOT'")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("technique lift manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str]] = set()
    seen_input_names: set[str] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"technique lift manifest source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, path, role)):
            fail(f"{location} must keep name, path, and role")
        if name in seen_input_names:
            fail(f"{location} duplicates source input '{name}'")
        seen_input_names.add(name)
        actual_source_inputs.add((name, path, role))
        donor_path = AOA_TECHNIQUES_ROOT / path
        if not donor_path.exists():
            fail(f"{location} references a missing donor path: aoa-techniques/{path}")
    if actual_source_inputs != EXPECTED_TECHNIQUE_LIFT_INPUTS:
        fail("technique lift manifest source_inputs must match the current bounded technique lift contract")

    surface_bindings = payload["surface_bindings"]
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("technique lift manifest surface_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, str, str]] = set()
    for index, binding in enumerate(surface_bindings):
        location = f"technique lift manifest surface_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")
        surface_id = binding.get("surface_id")
        surface_name = binding.get("surface_name")
        derived_kind = binding.get("derived_kind")
        derived_slot = binding.get("derived_slot")
        source_input = binding.get("source_input")
        if not all(
            isinstance(value, str) and value
            for value in (
                surface_id,
                surface_name,
                derived_kind,
                derived_slot,
                source_input,
            )
        ):
            fail(f"{location} must keep id, name, kind, slot, and source input")
        actual_bindings.add(
            (surface_id, surface_name, derived_kind, derived_slot, source_input)
        )

        surface = surfaces_by_id.get(surface_id)
        if surface is None:
            fail(f"{location} references unknown registry surface '{surface_id}'")
        if surface.get("name") != surface_name:
            fail(f"{location} does not match registry surface name")
        if surface.get("derived_kind") != derived_kind:
            fail(f"{location} does not match registry derived_kind")
        if surface.get("status") != "active":
            fail(f"{location} must only bind active registry surfaces")
        if surface.get("source_repos") != ["aoa-techniques"]:
            fail(f"{location} must point to aoa-techniques-only active surfaces in this first pack")

    if actual_bindings != EXPECTED_TECHNIQUE_LIFT_BINDINGS:
        fail("technique lift manifest surface_bindings must match the current bounded technique pack")

    output_paths = payload["output_paths"]
    if output_paths != EXPECTED_TECHNIQUE_LIFT_OUTPUT_PATHS:
        fail("technique lift manifest output_paths must match the committed generated output paths")

    if payload["bounded_output_contract"] != EXPECTED_TECHNIQUE_LIFT_CONTRACT:
        fail("technique lift manifest bounded_output_contract must match the current source-first guardrail")


def validate_tos_text_chunk_map_manifest(
    surfaces_by_id: dict[str, dict[str, object]],
) -> None:
    payload = read_json(TOS_TEXT_CHUNK_MAP_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("ToS text chunk map manifest must be a JSON object")

    for key in (
        "manifest_version",
        "pack_type",
        "source_repo",
        "source_root_env",
        "source_inputs",
        "surface_bindings",
        "output_paths",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"ToS text chunk map manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("ToS text chunk map manifest manifest_version must equal 1")
    if payload["pack_type"] != "tos_text_chunk_map":
        fail("ToS text chunk map manifest pack_type must equal 'tos_text_chunk_map'")
    if payload["source_repo"] != TOS_REPO:
        fail("ToS text chunk map manifest source_repo must equal 'Tree-of-Sophia'")
    if payload["source_root_env"] != "TREE_OF_SOPHIA_ROOT":
        fail("ToS text chunk map manifest source_root_env must equal 'TREE_OF_SOPHIA_ROOT'")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("ToS text chunk map manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str]] = set()
    seen_input_names: set[str] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"ToS text chunk map manifest source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, path, role)):
            fail(f"{location} must keep name, path, and role")
        if name in seen_input_names:
            fail(f"{location} duplicates source input '{name}'")
        seen_input_names.add(name)
        actual_source_inputs.add((name, path, role))
        resolve_known_ref(repo_ref(TOS_REPO, path), label=location)
    if actual_source_inputs != EXPECTED_TOS_TEXT_CHUNK_MAP_INPUTS:
        fail("ToS text chunk map manifest source_inputs must match the current bounded donor set")

    surface_bindings = payload["surface_bindings"]
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("ToS text chunk map manifest surface_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, str, str]] = set()
    for index, binding in enumerate(surface_bindings):
        location = f"ToS text chunk map manifest surface_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")
        surface_id = binding.get("surface_id")
        surface_name = binding.get("surface_name")
        derived_kind = binding.get("derived_kind")
        derived_slot = binding.get("derived_slot")
        source_input = binding.get("source_input")
        if not all(
            isinstance(value, str) and value
            for value in (
                surface_id,
                surface_name,
                derived_kind,
                derived_slot,
                source_input,
            )
        ):
            fail(f"{location} must keep id, name, kind, slot, and source input")
        actual_bindings.add(
            (surface_id, surface_name, derived_kind, derived_slot, source_input)
        )

        surface = surfaces_by_id.get(surface_id)
        if surface is None:
            fail(f"{location} references unknown registry surface '{surface_id}'")
        if surface.get("name") != surface_name:
            fail(f"{location} does not match registry surface name")
        if surface.get("derived_kind") != derived_kind:
            fail(f"{location} does not match registry derived_kind")
        if surface.get("status") != "experimental":
            fail(f"{location} must only bind experimental registry surfaces")
        if surface.get("source_repos") != [TOS_REPO]:
            fail(
                f"{location} must point to Tree-of-Sophia-only experimental surfaces in this Wave 2 pilot"
            )

    if actual_bindings != EXPECTED_TOS_TEXT_CHUNK_MAP_BINDINGS:
        fail("ToS text chunk map manifest surface_bindings must match the current bounded chunk-map contract")

    if payload["output_paths"] != EXPECTED_TOS_TEXT_CHUNK_MAP_OUTPUT_PATHS:
        fail("ToS text chunk map manifest output_paths must match the committed generated output paths")
    if payload["bounded_output_contract"] != EXPECTED_TOS_TEXT_CHUNK_MAP_CONTRACT:
        fail("ToS text chunk map manifest bounded_output_contract must match the current source-first guardrail")


def validate_tos_retrieval_axis_manifest(
    surfaces_by_id: dict[str, dict[str, object]],
) -> None:
    payload = read_json(TOS_RETRIEVAL_AXIS_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("ToS retrieval axis manifest must be a JSON object")

    for key in (
        "manifest_version",
        "pack_type",
        "source_inputs",
        "surface_bindings",
        "output_paths",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"ToS retrieval axis manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("ToS retrieval axis manifest manifest_version must equal 1")
    if payload["pack_type"] != "tos_retrieval_axis_pack":
        fail("ToS retrieval axis manifest pack_type must equal 'tos_retrieval_axis_pack'")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("ToS retrieval axis manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    seen_input_names: set[str] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"ToS retrieval axis manifest source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail(f"{location} must keep name, repo, path, and role")
        if name in seen_input_names:
            fail(f"{location} duplicates source input '{name}'")
        seen_input_names.add(name)
        actual_source_inputs.add((name, repo, path, role))
        resolve_known_ref(repo_ref(repo, path), label=location)
    if actual_source_inputs != EXPECTED_TOS_RETRIEVAL_AXIS_INPUTS:
        fail("ToS retrieval axis manifest source_inputs must match the current bounded donor set")

    surface_bindings = payload["surface_bindings"]
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("ToS retrieval axis manifest surface_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, str, str]] = set()
    for index, binding in enumerate(surface_bindings):
        location = f"ToS retrieval axis manifest surface_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")
        surface_id = binding.get("surface_id")
        surface_name = binding.get("surface_name")
        derived_kind = binding.get("derived_kind")
        derived_slot = binding.get("derived_slot")
        source_input = binding.get("source_input")
        if not all(
            isinstance(value, str) and value
            for value in (
                surface_id,
                surface_name,
                derived_kind,
                derived_slot,
                source_input,
            )
        ):
            fail(f"{location} must keep id, name, kind, slot, and source input")
        actual_bindings.add(
            (surface_id, surface_name, derived_kind, derived_slot, source_input)
        )
        surface = surfaces_by_id.get(surface_id)
        if surface is None:
            fail(f"{location} references unknown registry surface '{surface_id}'")
        if surface.get("status") != "experimental":
            fail(f"{location} must only bind experimental registry surfaces")
    if actual_bindings != EXPECTED_TOS_RETRIEVAL_AXIS_BINDINGS:
        fail("ToS retrieval axis manifest surface_bindings must match the current bounded retrieval contract")

    if payload["output_paths"] != EXPECTED_TOS_RETRIEVAL_AXIS_OUTPUT_PATHS:
        fail("ToS retrieval axis manifest output_paths must match the committed generated output paths")
    if payload["bounded_output_contract"] != EXPECTED_TOS_RETRIEVAL_AXIS_CONTRACT:
        fail("ToS retrieval axis manifest bounded_output_contract must match the current source-first guardrail")


def validate_reasoning_handoff_manifest() -> None:
    payload = read_json(REASONING_HANDOFF_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("reasoning handoff manifest must be a JSON object")

    for key in (
        "manifest_version",
        "pack_type",
        "source_root_envs",
        "source_inputs",
        "scenario_bindings",
        "output_paths",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"reasoning handoff manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("reasoning handoff manifest manifest_version must equal 1")
    if payload["pack_type"] != "reasoning_handoff_pack":
        fail("reasoning handoff manifest pack_type must equal 'reasoning_handoff_pack'")
    if payload["source_root_envs"] != EXPECTED_REASONING_HANDOFF_SOURCE_ROOT_ENVS:
        fail("reasoning handoff manifest source_root_envs must match the current donor root contract")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("reasoning handoff manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    seen_input_names: set[str] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"reasoning handoff manifest source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail(f"{location} must keep name, repo, path, and role")
        if name in seen_input_names:
            fail(f"{location} duplicates source input '{name}'")
        seen_input_names.add(name)
        actual_source_inputs.add((name, repo, path, role))
        resolve_known_ref(repo_ref(repo, path), label=location)
    if actual_source_inputs != EXPECTED_REASONING_HANDOFF_INPUTS:
        fail("reasoning handoff manifest source_inputs must match the current bounded donor set")

    scenario_bindings = payload["scenario_bindings"]
    if not isinstance(scenario_bindings, list) or not scenario_bindings:
        fail("reasoning handoff manifest scenario_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, tuple[str, ...], str | None, tuple[str, ...]]] = set()
    for index, binding in enumerate(scenario_bindings):
        location = f"reasoning handoff manifest scenario_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")
        scenario_ref = binding.get("scenario_ref")
        playbook_input = binding.get("playbook_input")
        eval_hook_input = binding.get("eval_hook_input")
        memo_contract_inputs = binding.get("memo_contract_inputs")
        continuity_input = binding.get("continuity_input")
        optional_trace_inputs = binding.get("optional_trace_inputs")
        if not all(isinstance(value, str) and value for value in (scenario_ref, playbook_input, eval_hook_input)):
            fail(f"{location} must keep scenario_ref, playbook_input, and eval_hook_input")
        if not isinstance(memo_contract_inputs, list) or not memo_contract_inputs:
            fail(f"{location}.memo_contract_inputs must be a non-empty list")
        if not all(isinstance(value, str) and value for value in memo_contract_inputs):
            fail(f"{location}.memo_contract_inputs contains an invalid entry")
        if continuity_input is not None and not isinstance(continuity_input, str):
            fail(f"{location}.continuity_input must be a string or null")
        if not isinstance(optional_trace_inputs, list):
            fail(f"{location}.optional_trace_inputs must be a list")
        if not all(isinstance(value, str) and value for value in optional_trace_inputs):
            fail(f"{location}.optional_trace_inputs contains an invalid entry")
        actual_bindings.add(
            (
                scenario_ref,
                playbook_input,
                eval_hook_input,
                tuple(memo_contract_inputs),
                continuity_input,
                tuple(optional_trace_inputs),
            )
        )
    if actual_bindings != EXPECTED_REASONING_HANDOFF_BINDINGS:
        fail("reasoning handoff manifest scenario_bindings must match the current bounded scenario contract")

    if payload["output_paths"] != EXPECTED_REASONING_HANDOFF_OUTPUT_PATHS:
        fail("reasoning handoff manifest output_paths must match the committed generated output paths")
    if payload["bounded_output_contract"] != EXPECTED_REASONING_HANDOFF_CONTRACT:
        fail("reasoning handoff manifest bounded_output_contract must match the current source-first guardrail")


def validate_source_owned_export_dependency_manifest(
    surfaces_by_id: dict[str, dict[str, object]],
) -> dict[tuple[str, str], dict[str, object]]:
    payload = read_json(SOURCE_OWNED_EXPORT_DEPENDENCIES_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("source-owned export dependency manifest must be a JSON object")

    for key in ("manifest_version", "contract_type", "dependencies"):
        if key not in payload:
            fail(f"source-owned export dependency manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("source-owned export dependency manifest manifest_version must equal 1")
    if payload["contract_type"] != "source_owned_export_dependencies":
        fail(
            "source-owned export dependency manifest contract_type must equal "
            "'source_owned_export_dependencies'"
        )

    dependencies = payload["dependencies"]
    if not isinstance(dependencies, list) or not dependencies:
        fail("source-owned export dependency manifest dependencies must be a non-empty list")

    dependencies_by_source: dict[tuple[str, str], dict[str, object]] = {}
    seen_dependency_ids: set[str] = set()
    for index, dependency in enumerate(dependencies):
        location = f"source-owned export dependency manifest dependencies[{index}]"
        if not isinstance(dependency, dict):
            fail(f"{location} must be an object")

        dependency_id = dependency.get("dependency_id")
        repo = dependency.get("repo")
        path = dependency.get("path")
        expected_owner_repo = dependency.get("expected_owner_repo")
        expected_kind = dependency.get("expected_kind")
        expected_object_id = dependency.get("expected_object_id")
        required_fields = dependency.get("required_fields")
        entry_surface = dependency.get("entry_surface")
        consumed_by = dependency.get("consumed_by")
        if not all(
            isinstance(value, str) and value
            for value in (
                dependency_id,
                repo,
                path,
                expected_owner_repo,
                expected_kind,
                expected_object_id,
            )
        ):
            fail(
                f"{location} must keep dependency_id, repo, path, expected_owner_repo, "
                "expected_kind, and expected_object_id"
            )
        if dependency_id in seen_dependency_ids:
            fail(f"{location}.dependency_id '{dependency_id}' is duplicated")
        seen_dependency_ids.add(dependency_id)
        if repo != expected_owner_repo:
            fail(f"{location}.expected_owner_repo must equal {location}.repo")
        if not isinstance(required_fields, list) or not required_fields:
            fail(f"{location}.required_fields must be a non-empty list")
        normalized_required_fields: list[str] = []
        for field_index, field_name in enumerate(required_fields):
            if not isinstance(field_name, str) or not field_name:
                fail(f"{location}.required_fields[{field_index}] must be a non-empty string")
            normalized_required_fields.append(field_name)
        if len(set(normalized_required_fields)) != len(normalized_required_fields):
            fail(f"{location}.required_fields must not contain duplicates")
        if not isinstance(entry_surface, dict):
            fail(f"{location}.entry_surface must be an object")
        entry_surface_repo = entry_surface.get("repo")
        entry_surface_path = entry_surface.get("path")
        entry_match_key = entry_surface.get("match_key")
        entry_match_value = entry_surface.get("match_value")
        if not all(
            isinstance(value, str) and value
            for value in (
                entry_surface_repo,
                entry_surface_path,
                entry_match_key,
                entry_match_value,
            )
        ):
            fail(
                f"{location}.entry_surface must keep repo, path, match_key, and match_value"
            )
        if entry_surface_repo != expected_owner_repo:
            fail(f"{location}.entry_surface.repo must equal {location}.expected_owner_repo")
        if entry_match_value != expected_object_id:
            fail(
                f"{location}.entry_surface.match_value must equal "
                f"{location}.expected_object_id"
            )
        if not isinstance(consumed_by, list) or not consumed_by:
            fail(f"{location}.consumed_by must be a non-empty list")
        normalized_consumed_by: list[str] = []
        for consumer_index, consumer_surface_id in enumerate(consumed_by):
            if not isinstance(consumer_surface_id, str) or not consumer_surface_id:
                fail(f"{location}.consumed_by[{consumer_index}] must be a non-empty string")
            if consumer_surface_id not in surfaces_by_id:
                fail(
                    f"{location}.consumed_by[{consumer_index}] references unknown "
                    f"registry surface '{consumer_surface_id}'"
                )
            normalized_consumed_by.append(consumer_surface_id)
        if len(set(normalized_consumed_by)) != len(normalized_consumed_by):
            fail(f"{location}.consumed_by must not contain duplicates")

        source_key = (repo, path)
        if source_key in dependencies_by_source:
            fail(f"{location} duplicates repo/path target '{repo_ref(repo, path)}'")

        export_path = resolve_known_ref(repo_ref(repo, path), label=location)
        entry_surface_ref = repo_ref(entry_surface_repo, entry_surface_path)
        resolve_known_ref(entry_surface_ref, label=f"{location}.entry_surface")
        export_payload = read_json(export_path)
        if not isinstance(export_payload, dict):
            fail(f"{location} target export must be a JSON object")
        for field_name in normalized_required_fields:
            if field_name not in export_payload:
                fail(
                    f"{location} requires target export '{repo_ref(repo, path)}' to keep "
                    f"'{field_name}'"
                )
        if export_payload.get("owner_repo") != expected_owner_repo:
            fail(f"{location} target export owner_repo must equal '{expected_owner_repo}'")
        if export_payload.get("kind") != expected_kind:
            fail(f"{location} target export kind must equal '{expected_kind}'")
        if export_payload.get("object_id") != expected_object_id:
            fail(f"{location} target export object_id must equal '{expected_object_id}'")

        export_source_inputs = export_payload.get("source_inputs")
        if not isinstance(export_source_inputs, list) or not export_source_inputs:
            fail(f"{location} target export source_inputs must be a non-empty list")
        primary_count = 0
        for source_input_index, source_input in enumerate(export_source_inputs):
            source_location = f"{location} target export source_inputs[{source_input_index}]"
            if not isinstance(source_input, dict):
                fail(f"{source_location} must be an object")
            source_repo = source_input.get("repo")
            source_role = source_input.get("role")
            source_class = source_input.get("source_class")
            if not all(
                isinstance(value, str) and value
                for value in (source_repo, source_role, source_class)
            ):
                fail(f"{source_location} must keep repo, role, and source_class")
            if source_repo != expected_owner_repo:
                fail(f"{source_location}.repo must equal '{expected_owner_repo}'")
            if source_role == "primary":
                primary_count += 1
            elif source_role != "supporting":
                fail(f"{source_location}.role must be 'primary' or 'supporting'")
        if primary_count != 1:
            fail(f"{location} target export must contain exactly one primary source input")

        export_entry_surface = export_payload.get("entry_surface")
        if not isinstance(export_entry_surface, dict):
            fail(f"{location} target export entry_surface must be an object")
        if export_entry_surface.get("repo") != entry_surface_repo:
            fail(f"{location} target export entry_surface.repo must equal '{entry_surface_repo}'")
        if export_entry_surface.get("path") != entry_surface_path:
            fail(f"{location} target export entry_surface.path must equal '{entry_surface_path}'")
        if export_entry_surface.get("match_key") != entry_match_key:
            fail(
                f"{location} target export entry_surface.match_key must equal "
                f"'{entry_match_key}'"
            )
        if export_entry_surface.get("match_value") != entry_match_value:
            fail(
                f"{location} target export entry_surface.match_value must equal "
                f"'{entry_match_value}'"
            )

        dependencies_by_source[source_key] = {
            "dependency_id": dependency_id,
            "consumed_by": normalized_consumed_by,
        }

    return dependencies_by_source


def validate_federation_spine_manifest(
    surfaces_by_id: dict[str, dict[str, object]],
    source_owned_export_dependencies: dict[tuple[str, str], dict[str, object]],
) -> None:
    payload = read_json(FEDERATION_SPINE_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("federation spine manifest must be a JSON object")

    for key in (
        "manifest_version",
        "pack_type",
        "source_inputs",
        "repo_bindings",
        "output_paths",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"federation spine manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("federation spine manifest manifest_version must equal 1")
    if payload["pack_type"] != "federation_spine":
        fail("federation spine manifest pack_type must equal 'federation_spine'")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("federation spine manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    seen_input_names: set[str] = set()
    source_input_order: list[str] = []
    source_inputs_by_name: dict[str, tuple[str, str, str]] = {}
    for index, source_input in enumerate(source_inputs):
        location = f"federation spine manifest source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail(f"{location} must keep name, repo, path, and role")
        if name in seen_input_names:
            fail(f"{location} duplicates source input '{name}'")
        seen_input_names.add(name)
        source_input_order.append(name)
        actual_source_inputs.add((name, repo, path, role))
        source_inputs_by_name[name] = (repo, path, role)
        resolve_known_ref(repo_ref(repo, path), label=location)
    if actual_source_inputs != EXPECTED_FEDERATION_SPINE_SOURCE_INPUTS:
        fail("federation spine manifest source_inputs must match the current bounded donor set")
    if source_input_order != EXPECTED_FEDERATION_SPINE_SOURCE_INPUT_ORDER:
        fail("federation spine manifest source_inputs must keep the current additive donor order")

    repo_bindings = payload["repo_bindings"]
    if not isinstance(repo_bindings, list) or not repo_bindings:
        fail("federation spine manifest repo_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, str]] = set()
    repo_binding_order: list[str] = []
    for index, binding in enumerate(repo_bindings):
        location = f"federation spine manifest repo_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")
        surface_id = binding.get("surface_id")
        repo_name = binding.get("repo")
        pilot_posture = binding.get("pilot_posture")
        export_input = binding.get("export_input")
        provenance_note = binding.get("provenance_note")
        non_identity_boundary = binding.get("non_identity_boundary")
        if not all(
            isinstance(value, str) and value
            for value in (
                surface_id,
                repo_name,
                pilot_posture,
                export_input,
                provenance_note,
                non_identity_boundary,
            )
        ):
            fail(
                f"{location} must keep surface_id, repo, pilot_posture, export_input, provenance_note, and non_identity_boundary"
            )
        if len(provenance_note) < 20:
            fail(f"{location}.provenance_note must be a string of length >= 20")
        if len(non_identity_boundary) < 20:
            fail(f"{location}.non_identity_boundary must be a string of length >= 20")

        surface = surfaces_by_id.get(surface_id)
        if surface is None:
            fail(f"{location} references unknown registry surface '{surface_id}'")
        if surface.get("status") != "experimental":
            fail(f"{location} must point to an experimental registry surface")
        repo_binding_order.append(repo_name)
        source_input_entry = source_inputs_by_name.get(export_input)
        if source_input_entry is None:
            fail(f"{location}.export_input references unknown source input '{export_input}'")
        input_repo, input_path, _ = source_input_entry
        dependency = source_owned_export_dependencies.get((input_repo, input_path))
        if dependency is None:
            fail(
                f"{location}.export_input must map to a declared source-owned export "
                "dependency"
            )
        dependency_id = dependency["dependency_id"]
        if surface_id not in dependency["consumed_by"]:
            fail(
                f"{location}.export_input dependency '{dependency_id}' must declare "
                f"'{surface_id}' in consumed_by"
            )

        actual_bindings.add((surface_id, repo_name, pilot_posture, export_input))
    if actual_bindings != EXPECTED_FEDERATION_SPINE_BINDINGS:
        fail("federation spine manifest repo_bindings must match the current bounded spine contract")
    if repo_binding_order != EXPECTED_FEDERATION_SPINE_REPO_ORDER:
        fail("federation spine manifest repo_bindings must keep the current stable repo order")

    if payload["output_paths"] != EXPECTED_FEDERATION_SPINE_OUTPUT_PATHS:
        fail("federation spine manifest output_paths must match the committed generated output paths")
    if payload["bounded_output_contract"] != EXPECTED_FEDERATION_SPINE_CONTRACT:
        fail("federation spine manifest bounded_output_contract must match the current source-first guardrail")


def validate_cross_source_node_projection_manifest(
    surfaces_by_id: dict[str, dict[str, object]],
    source_owned_export_dependencies: dict[tuple[str, str], dict[str, object]],
) -> None:
    payload = read_json(CROSS_SOURCE_NODE_PROJECTION_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("cross-source node projection manifest must be a JSON object")

    for key in (
        "manifest_version",
        "pack_type",
        "source_inputs",
        "surface_bindings",
        "projection_pairings",
        "output_paths",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"cross-source node projection manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("cross-source node projection manifest manifest_version must equal 1")
    if payload["pack_type"] != "cross_source_node_projection":
        fail("cross-source node projection manifest pack_type must equal 'cross_source_node_projection'")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("cross-source node projection manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    seen_input_names: set[str] = set()
    source_inputs_by_name: dict[str, tuple[str, str, str]] = {}
    for index, source_input in enumerate(source_inputs):
        location = f"cross-source node projection manifest source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail(f"{location} must keep name, repo, path, and role")
        if name in seen_input_names:
            fail(f"{location} duplicates source input '{name}'")
        seen_input_names.add(name)
        actual_source_inputs.add((name, repo, path, role))
        source_inputs_by_name[name] = (repo, path, role)
        resolve_known_ref(repo_ref(repo, path), label=location)
    if actual_source_inputs != EXPECTED_CROSS_SOURCE_NODE_PROJECTION_INPUTS:
        fail("cross-source node projection manifest source_inputs must match the current bounded donor set")

    surface_bindings = payload["surface_bindings"]
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("cross-source node projection manifest surface_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, str, str]] = set()
    for index, binding in enumerate(surface_bindings):
        location = f"cross-source node projection manifest surface_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")
        surface_id = binding.get("surface_id")
        surface_name = binding.get("surface_name")
        derived_kind = binding.get("derived_kind")
        derived_slot = binding.get("derived_slot")
        source_input = binding.get("source_input")
        if not all(
            isinstance(value, str) and value
            for value in (
                surface_id,
                surface_name,
                derived_kind,
                derived_slot,
                source_input,
            )
        ):
            fail(f"{location} must keep id, name, kind, slot, and source input")
        actual_bindings.add(
            (surface_id, surface_name, derived_kind, derived_slot, source_input)
        )
        surface = surfaces_by_id.get(surface_id)
        if surface is None:
            fail(f"{location} references unknown registry surface '{surface_id}'")
        if surface.get("status") != "experimental":
            fail(f"{location} must only bind experimental registry surfaces")
    if actual_bindings != EXPECTED_CROSS_SOURCE_NODE_PROJECTION_BINDINGS:
        fail("cross-source node projection manifest surface_bindings must match the current bounded projection contract")

    projection_pairings = payload["projection_pairings"]
    if not isinstance(projection_pairings, list) or not projection_pairings:
        fail("cross-source node projection manifest projection_pairings must be a non-empty list")
    if len(projection_pairings) != 1:
        fail(
            "cross-source node projection manifest projection_pairings must keep "
            "exactly one pairing in the current pilot"
        )
    seen_pairing_ids: set[str] = set()
    for index, pairing in enumerate(projection_pairings):
        location = f"cross-source node projection manifest projection_pairings[{index}]"
        if not isinstance(pairing, dict):
            fail(f"{location} must be an object")
        pairing_id = pairing.get("pairing_id")
        primary_export_input = pairing.get("primary_export_input")
        supporting_export_inputs = pairing.get("supporting_export_inputs")
        retrieval_axis_input = pairing.get("retrieval_axis_input")
        federation_spine_input = pairing.get("federation_spine_input")
        projection_summary = pairing.get("projection_summary")
        non_identity_boundary = pairing.get("non_identity_boundary")
        if not all(
            isinstance(value, str) and value
            for value in (
                pairing_id,
                primary_export_input,
                retrieval_axis_input,
                federation_spine_input,
                projection_summary,
                non_identity_boundary,
            )
        ):
            fail(
                f"{location} must keep pairing_id, primary_export_input, "
                "retrieval_axis_input, federation_spine_input, projection_summary, "
                "and non_identity_boundary"
            )
        if pairing_id in seen_pairing_ids:
            fail(f"{location}.pairing_id '{pairing_id}' is duplicated")
        seen_pairing_ids.add(pairing_id)
        if not isinstance(supporting_export_inputs, list) or not supporting_export_inputs:
            fail(f"{location}.supporting_export_inputs must be a non-empty list")
        if len(supporting_export_inputs) != 1:
            fail(
                f"{location}.supporting_export_inputs must keep exactly one "
                "supporting export in the current pilot"
            )
        supporting_input_name = supporting_export_inputs[0]
        if not isinstance(supporting_input_name, str) or not supporting_input_name:
            fail(f"{location}.supporting_export_inputs[0] must be a non-empty string")
        for label, input_name, expected_role in (
            ("primary_export_input", primary_export_input, "primary_export"),
            ("supporting_export_inputs[0]", supporting_input_name, "supporting_export"),
            ("retrieval_axis_input", retrieval_axis_input, "retrieval_axis"),
            ("federation_spine_input", federation_spine_input, "federation_spine"),
        ):
            source_input_entry = source_inputs_by_name.get(input_name)
            if source_input_entry is None:
                fail(f"{location}.{label} references unknown source input '{input_name}'")
            input_repo, input_path, input_role = source_input_entry
            if input_role != expected_role:
                fail(f"{location}.{label} must point to a {expected_role} source input")
            if expected_role in {"primary_export", "supporting_export"}:
                dependency = source_owned_export_dependencies.get((input_repo, input_path))
                if dependency is None:
                    fail(f"{location}.{label} must map to a declared source-owned export dependency")
                dependency_id = dependency["dependency_id"]
                if "AOA-K-0006" not in dependency["consumed_by"]:
                    fail(
                        f"{location}.{label} dependency '{dependency_id}' must declare "
                        "'AOA-K-0006' in consumed_by"
                    )
        if len(projection_summary) < 20:
            fail(f"{location}.projection_summary must be a string of length >= 20")
        if len(non_identity_boundary) < 20:
            fail(f"{location}.non_identity_boundary must be a string of length >= 20")

    if payload["output_paths"] != EXPECTED_CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATHS:
        fail("cross-source node projection manifest output_paths must match the committed generated output paths")
    if payload["bounded_output_contract"] != EXPECTED_CROSS_SOURCE_NODE_PROJECTION_CONTRACT:
        fail("cross-source node projection manifest bounded_output_contract must match the current source-first guardrail")


def validate_tiny_consumer_bundle_manifest(
    surfaces_by_id: dict[str, dict[str, object]]
) -> None:
    payload = read_json(TINY_CONSUMER_BUNDLE_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("tiny consumer bundle manifest must be a JSON object")

    for key in (
        "manifest_version",
        "bundle_type",
        "source_inputs",
        "bundle_order",
        "deferred_counterpart",
        "output_paths",
    ):
        if key not in payload:
            fail(f"tiny consumer bundle manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("tiny consumer bundle manifest manifest_version must equal 1")
    if payload["bundle_type"] != "tiny_consumer_bundle":
        fail("tiny consumer bundle manifest bundle_type must equal 'tiny_consumer_bundle'")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("tiny consumer bundle manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    seen_input_names: set[str] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"tiny consumer bundle manifest source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail(f"{location} must keep name, repo, path, and role")
        if name in seen_input_names:
            fail(f"{location} duplicates source input '{name}'")
        seen_input_names.add(name)
        actual_source_inputs.add((name, repo, path, role))
        resolve_known_ref(repo_ref(repo, path), label=location)
    if actual_source_inputs != EXPECTED_TINY_CONSUMER_BUNDLE_INPUTS:
        fail("tiny consumer bundle manifest source_inputs must match the current bounded donor set")

    bundle_order = validate_unique_string_list(
        payload["bundle_order"],
        label="tiny consumer bundle manifest bundle_order",
    )
    if bundle_order != EXPECTED_TINY_CONSUMER_BUNDLE_ORDER:
        fail("tiny consumer bundle manifest bundle_order must keep the current stable bundle order")
    if set(bundle_order) != {name for name, _, _, _ in EXPECTED_TINY_CONSUMER_BUNDLE_INPUTS}:
        fail("tiny consumer bundle manifest bundle_order must reference each declared source input exactly once")

    deferred_counterpart = payload["deferred_counterpart"]
    if not isinstance(deferred_counterpart, dict):
        fail("tiny consumer bundle manifest deferred_counterpart must be an object")
    if deferred_counterpart != EXPECTED_TINY_CONSUMER_BUNDLE_DEFERRED_COUNTERPART:
        fail("tiny consumer bundle manifest deferred_counterpart must match the contract-only posture")

    surface_id = deferred_counterpart["surface_id"]
    if surface_id not in surfaces_by_id:
        fail("tiny consumer bundle manifest deferred_counterpart.surface_id must exist in the registry")
    if surfaces_by_id[surface_id].get("status") != "planned":
        fail("tiny consumer bundle manifest deferred_counterpart.surface_id must remain planned in the registry")
    resolve_known_ref(
        deferred_counterpart["federation_exposure_review_ref"],
        label="tiny consumer bundle manifest deferred_counterpart.federation_exposure_review_ref",
    )
    for index, ref in enumerate(deferred_counterpart["allowed_refs"]):
        resolve_known_ref(
            ref,
            label=f"tiny consumer bundle manifest deferred_counterpart.allowed_refs[{index}]",
        )
    for index, ref in enumerate(deferred_counterpart["forbidden_active_payload_refs"]):
        resolve_known_ref(
            ref,
            label=(
                "tiny consumer bundle manifest "
                f"deferred_counterpart.forbidden_active_payload_refs[{index}]"
            ),
        )

    if payload["output_paths"] != EXPECTED_TINY_CONSUMER_BUNDLE_OUTPUT_PATHS:
        fail("tiny consumer bundle manifest output_paths must match the committed generated output paths")


def validate_counterpart_federation_exposure_review_manifest() -> None:
    payload = read_json(COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("counterpart federation exposure review manifest must be a JSON object")

    for key in (
        "manifest_version",
        "review_type",
        "source_inputs",
        "review_bindings",
        "output_paths",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(
                "counterpart federation exposure review manifest is missing required "
                f"key '{key}'"
            )

    if payload["manifest_version"] != 1:
        fail("counterpart federation exposure review manifest manifest_version must equal 1")
    if payload["review_type"] != "counterpart_federation_exposure_review":
        fail(
            "counterpart federation exposure review manifest review_type must equal "
            "'counterpart_federation_exposure_review'"
        )

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("counterpart federation exposure review manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    source_input_order: list[str] = []
    seen_input_names: set[str] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"counterpart federation exposure review manifest source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail(f"{location} must keep name, repo, path, and role")
        if name in seen_input_names:
            fail(f"{location} duplicates source input '{name}'")
        seen_input_names.add(name)
        source_input_order.append(name)
        actual_source_inputs.add((name, repo, path, role))
        resolve_known_ref(repo_ref(repo, path), label=location)
    if actual_source_inputs != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_INPUTS:
        fail(
            "counterpart federation exposure review manifest source_inputs must match "
            "the current reviewed donor set"
        )
    if source_input_order != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_ORDER:
        fail(
            "counterpart federation exposure review manifest source_inputs must keep "
            "the current reviewed surface order"
        )

    review_bindings = payload["review_bindings"]
    if not isinstance(review_bindings, list) or not review_bindings:
        fail("counterpart federation exposure review manifest review_bindings must be a non-empty list")
    actual_review_order: list[str] = []
    seen_review_names: set[str] = set()
    for index, binding in enumerate(review_bindings):
        location = f"counterpart federation exposure review manifest review_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")
        surface_name = binding.get("surface_name")
        surface_input = binding.get("surface_input")
        exposure_posture = binding.get("exposure_posture")
        review_note = binding.get("review_note")
        if not all(
            isinstance(value, str) and value
            for value in (surface_name, surface_input, exposure_posture, review_note)
        ):
            fail(
                f"{location} must keep surface_name, surface_input, exposure_posture, "
                "and review_note"
            )
        if surface_name in seen_review_names:
            fail(f"{location} duplicates review binding '{surface_name}'")
        seen_review_names.add(surface_name)
        actual_review_order.append(surface_name)
        if surface_name != surface_input:
            fail(f"{location}.surface_name must match surface_input in the current wave")
        if exposure_posture != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_POSTURES.get(surface_name):
            fail(
                f"{location}.exposure_posture must match the current reviewed posture "
                f"for '{surface_name}'"
            )

        allowed_counterpart_refs = binding.get("allowed_counterpart_refs")
        forbidden_refs = binding.get("forbidden_refs")
        if surface_name in {"reasoning_handoff_pack", "tiny_consumer_bundle"}:
            if allowed_counterpart_refs != EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS:
                fail(
                    f"{location}.allowed_counterpart_refs must match the current "
                    "contract-only counterpart refs"
                )
            for ref_index, ref in enumerate(allowed_counterpart_refs):
                resolve_known_ref(
                    ref,
                    label=f"{location}.allowed_counterpart_refs[{ref_index}]",
                )
            if forbidden_refs is not None:
                fail(f"{location}.forbidden_refs must stay absent when counterpart refs are allowed")
        elif surface_name in {"federation_spine", "cross_source_node_projection"}:
            if forbidden_refs != EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS:
                fail(
                    f"{location}.forbidden_refs must match the current forbidden "
                    "counterpart exposure set"
                )
            for ref_index, ref in enumerate(forbidden_refs):
                resolve_known_ref(
                    ref,
                    label=f"{location}.forbidden_refs[{ref_index}]",
                )
            if allowed_counterpart_refs is not None:
                fail(
                    f"{location}.allowed_counterpart_refs must stay absent for "
                    "non-exposing surfaces"
                )
        else:
            if allowed_counterpart_refs is not None or forbidden_refs is not None:
                fail(
                    f"{location} must not declare allowed_counterpart_refs or "
                    "forbidden_refs for contract/example review surfaces"
                )

    if actual_review_order != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_ORDER:
        fail(
            "counterpart federation exposure review manifest review_bindings must keep "
            "the current reviewed surface order"
        )
    if payload["output_paths"] != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATHS:
        fail(
            "counterpart federation exposure review manifest output_paths must match "
            "the committed generated output paths"
        )
    if payload["bounded_output_contract"] != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_CONTRACT:
        fail(
            "counterpart federation exposure review manifest bounded_output_contract "
            "must match the current review guardrail"
        )


def validate_tos_text_chunk_map_pack(
    payload: object,
    surfaces_by_id: dict[str, dict[str, object]],
    expected_payload: dict[str, object],
) -> None:
    if not isinstance(payload, dict):
        fail("ToS text chunk map pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_repo",
        "source_manifest_ref",
        "source_inputs",
        "surface_bindings",
        "surface_id",
        "surface_name",
        "node_id",
        "node_type",
        "source_anchor",
        "authority_surface_ref",
        "route_ref",
        "capsule_ref",
        "interpretation_layers",
        "chunk_count",
        "chunks",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"ToS text chunk map pack is missing required key '{key}'")

    if payload["pack_version"] != 1:
        fail("ToS text chunk map pack pack_version must equal 1")
    if payload["pack_type"] != "tos_text_chunk_map":
        fail("ToS text chunk map pack pack_type must equal 'tos_text_chunk_map'")
    if payload["source_repo"] != TOS_REPO:
        fail("ToS text chunk map pack source_repo must equal 'Tree-of-Sophia'")
    if payload["source_manifest_ref"] != "manifests/tos_text_chunk_map.json":
        fail(
            "ToS text chunk map pack source_manifest_ref must point to manifests/tos_text_chunk_map.json"
        )
    if payload["bounded_output_contract"] != EXPECTED_TOS_TEXT_CHUNK_MAP_CONTRACT:
        fail("ToS text chunk map pack bounded_output_contract must match the current source-first guardrail")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("ToS text chunk map pack source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str]] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"ToS text chunk map pack source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        role = source_input.get("role")
        ref = source_input.get("ref")
        if not all(isinstance(value, str) and value for value in (name, role, ref)):
            fail(f"{location} must keep name, role, and ref")
        resolve_known_ref(ref, label=location)
        actual_source_inputs.add((name, role, ref))
    expected_source_inputs = {
        (
            source_input["name"],
            source_input["role"],
            source_input["ref"],
        )
        for source_input in expected_payload["source_inputs"]
        if isinstance(source_input, dict)
    }
    if actual_source_inputs != expected_source_inputs:
        fail("ToS text chunk map pack source_inputs must match the manifest-driven donor set")

    surface_bindings = payload["surface_bindings"]
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("ToS text chunk map pack surface_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, str, str]] = set()
    for index, binding in enumerate(surface_bindings):
        location = f"ToS text chunk map pack surface_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")
        surface_id = binding.get("surface_id")
        surface_name = binding.get("surface_name")
        derived_kind = binding.get("derived_kind")
        derived_slot = binding.get("derived_slot")
        source_input = binding.get("source_input")
        if not all(
            isinstance(value, str) and value
            for value in (
                surface_id,
                surface_name,
                derived_kind,
                derived_slot,
                source_input,
            )
        ):
            fail(f"{location} must keep id, name, kind, slot, and source input")
        actual_bindings.add(
            (surface_id, surface_name, derived_kind, derived_slot, source_input)
        )
    if actual_bindings != EXPECTED_TOS_TEXT_CHUNK_MAP_BINDINGS:
        fail("ToS text chunk map pack surface_bindings must match the current bounded chunk-map contract")

    surface_id = payload["surface_id"]
    if surface_id != "AOA-K-0005":
        fail("ToS text chunk map pack surface_id must equal 'AOA-K-0005'")
    registry_surface = surfaces_by_id.get(surface_id)
    if registry_surface is None:
        fail("ToS text chunk map pack surface_id must exist in the generated registry")
    if registry_surface.get("status") != "experimental":
        fail("AOA-K-0005 must remain experimental in the generated registry")
    if payload["surface_name"] != "tos-text-chunk-map":
        fail("ToS text chunk map pack surface_name must equal 'tos-text-chunk-map'")
    if payload["node_id"] != expected_payload["node_id"]:
        fail("ToS text chunk map pack node_id must stay aligned with the current ToS authority surface")
    if payload["node_type"] != "source":
        fail("ToS text chunk map pack node_type must stay 'source'")
    if payload["source_anchor"] != expected_payload["source_anchor"]:
        fail("ToS text chunk map pack source_anchor must match the current ToS authority surface")

    for key in ("authority_surface_ref", "route_ref", "capsule_ref"):
        value = payload[key]
        if not isinstance(value, str) or not value:
            fail(f"ToS text chunk map pack {key} must be a non-empty string")
        resolve_known_ref(value, label=f"ToS text chunk map pack {key}")
        if value != expected_payload[key]:
            fail(f"ToS text chunk map pack {key} must stay aligned with the current bounded ToS route")

    interpretation_layers = validate_unique_string_list(
        payload["interpretation_layers"],
        label="ToS text chunk map pack interpretation_layers",
    )
    if interpretation_layers != expected_payload["interpretation_layers"]:
        fail("ToS text chunk map pack interpretation_layers must match the authority surface")

    chunks = payload["chunks"]
    if not isinstance(chunks, list) or not chunks:
        fail("ToS text chunk map pack chunks must be a non-empty list")
    chunk_count = payload["chunk_count"]
    if not isinstance(chunk_count, int) or chunk_count != len(chunks):
        fail("ToS text chunk map pack chunk_count must equal the number of chunks")

    expected_chunks = expected_payload["chunks"]
    if not isinstance(expected_chunks, list):
        fail("expected ToS text chunk map payload must declare chunks")
    expected_chunks_by_segment = {
        chunk["segment_id"]: chunk
        for chunk in expected_chunks
        if isinstance(chunk, dict) and isinstance(chunk.get("segment_id"), str)
    }
    if chunk_count != len(expected_chunks_by_segment):
        fail("ToS text chunk map pack chunk_count must equal the number of unique donor segment_ids")

    seen_segment_ids: set[str] = set()
    for index, chunk in enumerate(chunks):
        location = f"ToS text chunk map pack chunks[{index}]"
        if not isinstance(chunk, dict):
            fail(f"{location} must be an object")
        for key in (
            "chunk_id",
            "node_id",
            "segment_id",
            "source_anchor",
            "source_ref",
            "route_ref",
            "capsule_ref",
            "interpretation_layers",
            "witness_count",
            "witnesses",
        ):
            if key not in chunk:
                fail(f"{location} is missing required key '{key}'")
        segment_id = chunk["segment_id"]
        if not isinstance(segment_id, str) or not segment_id:
            fail(f"{location}.segment_id must be a non-empty string")
        if segment_id in seen_segment_ids:
            fail(f"{location}.segment_id '{segment_id}' is duplicated")
        seen_segment_ids.add(segment_id)
        expected_chunk = expected_chunks_by_segment.get(segment_id)
        if expected_chunk is None:
            fail(f"{location}.segment_id '{segment_id}' is not present in the bounded ToS authority surface")

        witnesses = chunk["witnesses"]
        if not isinstance(witnesses, list) or not witnesses:
            fail(f"{location}.witnesses must be a non-empty list")
        witness_count = chunk["witness_count"]
        if not isinstance(witness_count, int) or witness_count != len(witnesses):
            fail(f"{location}.witness_count must equal the number of witnesses")
        for witness_index, witness in enumerate(witnesses):
            witness_location = f"{location}.witnesses[{witness_index}]"
            if not isinstance(witness, dict):
                fail(f"{witness_location} must be an object")
            for key in ("language", "role", "text"):
                if key not in witness:
                    fail(f"{witness_location} is missing required key '{key}'")
                if not isinstance(witness[key], str) or not witness[key]:
                    fail(f"{witness_location}.{key} must be a non-empty string")

        translation_tension = chunk.get("translation_tension")
        if translation_tension is not None:
            if not isinstance(translation_tension, dict):
                fail(f"{location}.translation_tension must be an object when present")
            if translation_tension.get("segment_id") != segment_id:
                fail(f"{location}.translation_tension.segment_id must match the chunk segment_id")
            if not isinstance(translation_tension.get("note"), str) or not translation_tension["note"]:
                fail(f"{location}.translation_tension.note must be a non-empty string")

        if chunk != expected_chunk:
            fail(f"{location} must match the committed source-linked chunk payload for segment '{segment_id}'")

    if seen_segment_ids != set(expected_chunks_by_segment):
        fail("ToS text chunk map pack must cover every unique donor segment_id exactly once")


def validate_tos_text_chunk_map_example(
    expected_payload: dict[str, object],
) -> None:
    payload = read_json(TOS_TEXT_CHUNK_MAP_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("ToS text chunk map example must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_repo",
        "source_manifest_ref",
        "source_inputs",
        "surface_bindings",
        "surface_id",
        "surface_name",
        "node_id",
        "node_type",
        "source_anchor",
        "authority_surface_ref",
        "route_ref",
        "capsule_ref",
        "interpretation_layers",
        "chunk_count",
        "chunks",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"ToS text chunk map example is missing required key '{key}'")

    for key in (
        "pack_version",
        "pack_type",
        "source_repo",
        "source_manifest_ref",
        "surface_id",
        "surface_name",
        "node_id",
        "node_type",
        "source_anchor",
        "authority_surface_ref",
        "route_ref",
        "capsule_ref",
        "interpretation_layers",
        "bounded_output_contract",
    ):
        if payload[key] != expected_payload[key]:
            fail(f"ToS text chunk map example {key} must match the current bounded pilot payload")

    source_inputs = payload["source_inputs"]
    if source_inputs != expected_payload["source_inputs"]:
        fail("ToS text chunk map example source_inputs must match the current bounded donor set")
    surface_bindings = payload["surface_bindings"]
    if surface_bindings != expected_payload["surface_bindings"]:
        fail("ToS text chunk map example surface_bindings must match the current bounded chunk-map binding")

    chunks = payload["chunks"]
    if not isinstance(chunks, list) or len(chunks) != 1:
        fail("ToS text chunk map example must contain exactly one chunk")
    if payload["chunk_count"] != 1:
        fail("ToS text chunk map example chunk_count must equal 1")

    expected_chunks = expected_payload["chunks"]
    if not isinstance(expected_chunks, list):
        fail("expected ToS text chunk map payload must declare chunks")
    expected_chunk = next(
        (
            chunk
            for chunk in expected_chunks
            if isinstance(chunk, dict) and chunk.get("segment_id") == "prologue-overflow"
        ),
        None,
    )
    if expected_chunk is None:
        fail("expected ToS text chunk map payload must keep the prologue-overflow segment")
    if chunks[0] != expected_chunk:
        fail("ToS text chunk map example must mirror the bounded prologue-overflow chunk with translation tension")


def validate_tos_retrieval_axis_pack(
    payload: object,
    surfaces_by_id: dict[str, dict[str, object]],
    expected_payload: dict[str, object],
) -> None:
    if not isinstance(payload, dict):
        fail("ToS retrieval axis pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "source_inputs",
        "surface_bindings",
        "surface_id",
        "surface_name",
        "axis_count",
        "axes",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"ToS retrieval axis pack is missing required key '{key}'")

    if payload["pack_type"] != "tos_retrieval_axis_pack":
        fail("ToS retrieval axis pack pack_type must equal 'tos_retrieval_axis_pack'")
    if payload["bounded_output_contract"] != EXPECTED_TOS_RETRIEVAL_AXIS_CONTRACT:
        fail("ToS retrieval axis pack bounded_output_contract must match the current source-first guardrail")
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail("ToS retrieval axis pack source_inputs must match the manifest-driven donor set")
    if payload["surface_bindings"] != expected_payload["surface_bindings"]:
        fail("ToS retrieval axis pack surface_bindings must match the current bounded retrieval binding")

    surface_0007 = surfaces_by_id.get("AOA-K-0007")
    if surface_0007 is None or surface_0007.get("status") != "experimental":
        fail("ToS retrieval axis pack requires AOA-K-0007 to remain experimental in the generated registry")

    axes = payload["axes"]
    if not isinstance(axes, list) or len(axes) != 1:
        fail("ToS retrieval axis pack must contain exactly one axis in the current pilot")
    if payload["axis_count"] != 1:
        fail("ToS retrieval axis pack axis_count must equal 1 in the current pilot")
    axis = axes[0]
    if not isinstance(axis, dict):
        fail("ToS retrieval axis pack axis must be an object")
    for key in (
        "chunk_map_ref",
        "source_refs",
        "lineage_refs",
        "conflict_refs",
        "practice_refs",
        "bridge_surface_ref",
        "bridge_envelope_ref",
        "memo_face_refs",
    ):
        value = axis.get(key)
        if value is None:
            fail(f"ToS retrieval axis pack axis is missing required key '{key}'")
    resolve_known_ref(axis["chunk_map_ref"], label="ToS retrieval axis pack chunk_map_ref")
    resolve_known_ref(axis["bridge_surface_ref"], label="ToS retrieval axis pack bridge_surface_ref")
    resolve_known_ref(axis["bridge_envelope_ref"], label="ToS retrieval axis pack bridge_envelope_ref")
    for ref_list_key in ("source_refs", "lineage_refs", "conflict_refs", "practice_refs", "memo_face_refs"):
        refs = validate_unique_string_list(axis[ref_list_key], label=f"ToS retrieval axis pack {ref_list_key}")
        for ref in refs:
            resolve_known_ref(ref, label=f"ToS retrieval axis pack {ref_list_key}")

    if payload != expected_payload:
        fail("ToS retrieval axis pack must match the committed manifest-driven retrieval-axis payload")


def validate_tos_retrieval_axis_example(expected_payload: dict[str, object]) -> None:
    payload = read_json(TOS_RETRIEVAL_AXIS_EXAMPLE_PATH)
    if payload != expected_payload:
        fail("ToS retrieval axis example must match the current bounded retrieval-axis payload")


def validate_reasoning_artifact_descriptor(
    payload: object,
    *,
    label: str,
) -> dict[str, object]:
    if not isinstance(payload, dict):
        fail(f"{label} must be an object")
    for key in ("artifact_name", "contract_strength", "artifact_contract_refs"):
        if key not in payload:
            fail(f"{label} is missing required key '{key}'")
    artifact_name = payload["artifact_name"]
    contract_strength = payload["contract_strength"]
    artifact_contract_refs = payload["artifact_contract_refs"]
    if not isinstance(artifact_name, str) or not artifact_name:
        fail(f"{label}.artifact_name must be a non-empty string")
    if contract_strength not in ALLOWED_CONTRACT_STRENGTH:
        fail(f"{label}.contract_strength '{contract_strength}' is not allowed")
    refs = validate_unique_string_list(
        artifact_contract_refs,
        label=f"{label}.artifact_contract_refs",
    )
    for ref in refs:
        resolve_known_ref(ref, label=f"{label}.artifact_contract_refs")
    if contract_strength == "schema_backed" and not any(ref.endswith(".schema.json") for ref in refs):
        fail(f"{label} marked as schema_backed must include at least one schema ref")
    return payload


def validate_reasoning_handoff_pack(payload: object) -> None:
    if not isinstance(payload, dict):
        fail("reasoning handoff pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "source_inputs",
        "scenario_count",
        "scenarios",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"reasoning handoff pack is missing required key '{key}'")

    if payload["pack_version"] != 1:
        fail("reasoning handoff pack pack_version must equal 1")
    if payload["pack_type"] != "reasoning_handoff_pack":
        fail("reasoning handoff pack pack_type must equal 'reasoning_handoff_pack'")
    if payload["source_manifest_ref"] != "manifests/reasoning_handoff_pack.json":
        fail("reasoning handoff pack source_manifest_ref must point to manifests/reasoning_handoff_pack.json")
    if payload["bounded_output_contract"] != EXPECTED_REASONING_HANDOFF_CONTRACT:
        fail("reasoning handoff pack bounded_output_contract must match the current source-first guardrail")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("reasoning handoff pack source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"reasoning handoff pack source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        repo = source_input.get("repo")
        role = source_input.get("role")
        ref = source_input.get("ref")
        if not all(isinstance(value, str) and value for value in (name, repo, role, ref)):
            fail(f"{location} must keep name, repo, role, and ref")
        resolve_known_ref(ref, label=location)
        relative_ref = ref if repo == "aoa-kag" else ref.split("/", 1)[1]
        actual_source_inputs.add((name, repo, relative_ref, role))
    if actual_source_inputs != EXPECTED_REASONING_HANDOFF_INPUTS:
        fail("reasoning handoff pack source_inputs must match the manifest-driven donor set")

    scenarios = payload["scenarios"]
    if not isinstance(scenarios, list) or not scenarios:
        fail("reasoning handoff pack scenarios must be a non-empty list")
    scenario_count = payload["scenario_count"]
    if not isinstance(scenario_count, int) or scenario_count != len(scenarios):
        fail("reasoning handoff pack scenario_count must equal the number of scenarios")

    seen_scenarios: set[str] = set()
    for index, scenario in enumerate(scenarios):
        location = f"reasoning handoff pack scenarios[{index}]"
        if not isinstance(scenario, dict):
            fail(f"{location} must be an object")
        for key in (
            "scenario_ref",
            "playbook_ref",
            "artifact_spine",
            "eval_bridge",
            "memo_bridge",
            "compatible_query_modes",
            "authoritative_refs",
            "return_contract",
            "boundary_guardrails",
        ):
            if key not in scenario:
                fail(f"{location} is missing required key '{key}'")

        scenario_ref = scenario["scenario_ref"]
        playbook_ref = scenario["playbook_ref"]
        if not isinstance(scenario_ref, str) or not re.match(r"^AOA-P-[0-9]{4}$", scenario_ref):
            fail(f"{location}.scenario_ref must be an AOA playbook id")
        if scenario_ref in seen_scenarios:
            fail(f"{location}.scenario_ref '{scenario_ref}' is duplicated")
        seen_scenarios.add(scenario_ref)
        if not isinstance(playbook_ref, str) or not playbook_ref.startswith("aoa-playbooks/"):
            fail(f"{location}.playbook_ref must point to aoa-playbooks")
        resolve_known_ref(playbook_ref, label=f"{location}.playbook_ref")

        query_modes = validate_unique_string_list(
            scenario["compatible_query_modes"],
            label=f"{location}.compatible_query_modes",
        )
        validate_exact_set(
            query_modes,
            ALLOWED_QUERY_MODES,
            label=f"{location}.compatible_query_modes",
        )

        return_contract = scenario["return_contract"]
        if not isinstance(return_contract, dict):
            fail(f"{location}.return_contract must be an object")
        must_include = validate_unique_string_list(
            return_contract.get("must_include"),
            label=f"{location}.return_contract.must_include",
        )
        validate_exact_set(
            must_include,
            EXPECTED_RETURN_MUST_INCLUDE,
            label=f"{location}.return_contract.must_include",
        )
        may_include = validate_unique_string_list(
            return_contract.get("may_include"),
            label=f"{location}.return_contract.may_include",
            allow_empty=True,
        )
        validate_exact_set(
            may_include,
            EXPECTED_RETURN_MAY_INCLUDE,
            label=f"{location}.return_contract.may_include",
        )
        normalized_return_fields = validate_unique_string_list(
            return_contract.get("normalized_return_fields"),
            label=f"{location}.return_contract.normalized_return_fields",
        )
        if normalized_return_fields != ["axis_summary"]:
            fail(f"{location}.return_contract.normalized_return_fields must equal ['axis_summary']")

        if scenario["boundary_guardrails"] != EXPECTED_BOUNDARY_GUARDRAILS:
            fail(f"{location}.boundary_guardrails must match the current handoff guardrail contract")

        authoritative_refs = scenario["authoritative_refs"]
        if not isinstance(authoritative_refs, dict):
            fail(f"{location}.authoritative_refs must be an object")
        for key, prefix in (
            ("playbook_refs", "aoa-playbooks/"),
            ("eval_refs", "aoa-evals/"),
            ("memo_refs", "aoa-memo/"),
        ):
            refs = validate_unique_string_list(
                authoritative_refs.get(key),
                label=f"{location}.authoritative_refs.{key}",
            )
            for ref in refs:
                if not ref.startswith(prefix):
                    fail(f"{location}.authoritative_refs.{key} contains a ref outside {prefix}")
                resolve_known_ref(ref, label=f"{location}.authoritative_refs.{key}")
        guardrail_refs = validate_unique_string_list(
            authoritative_refs.get("kag_guardrail_refs"),
            label=f"{location}.authoritative_refs.kag_guardrail_refs",
        )
        if guardrail_refs != EXPECTED_REASONING_HANDOFF_KAG_GUARDRAIL_REFS:
            fail(f"{location}.authoritative_refs.kag_guardrail_refs must match the local KAG guardrail refs")
        for ref in guardrail_refs:
            resolve_known_ref(ref, label=f"{location}.authoritative_refs.kag_guardrail_refs")
        artifact_schema_refs = validate_unique_string_list(
            authoritative_refs.get("artifact_schema_refs"),
            label=f"{location}.authoritative_refs.artifact_schema_refs",
        )
        for ref in artifact_schema_refs:
            if not ref.endswith(".schema.json"):
                fail(f"{location}.authoritative_refs.artifact_schema_refs must only contain schema refs")
            resolve_known_ref(ref, label=f"{location}.authoritative_refs.artifact_schema_refs")

        artifact_spine = scenario["artifact_spine"]
        if not isinstance(artifact_spine, dict):
            fail(f"{location}.artifact_spine must be an object")
        verification_surface = validate_reasoning_artifact_descriptor(
            artifact_spine.get("verification_surface"),
            label=f"{location}.artifact_spine.verification_surface",
        )
        continuity_surface = artifact_spine.get("continuity_surface")
        if continuity_surface is not None:
            validate_reasoning_artifact_descriptor(
                continuity_surface,
                label=f"{location}.artifact_spine.continuity_surface",
            )
        supporting_artifacts = artifact_spine.get("supporting_artifacts")
        if not isinstance(supporting_artifacts, list):
            fail(f"{location}.artifact_spine.supporting_artifacts must be a list")
        supporting_names: list[str] = []
        for artifact_index, artifact in enumerate(supporting_artifacts):
            descriptor = validate_reasoning_artifact_descriptor(
                artifact,
                label=f"{location}.artifact_spine.supporting_artifacts[{artifact_index}]",
            )
            supporting_names.append(descriptor["artifact_name"])
        optional_trace_sidecars = artifact_spine.get("optional_trace_sidecars")
        if not isinstance(optional_trace_sidecars, list):
            fail(f"{location}.artifact_spine.optional_trace_sidecars must be a list")
        trace_sidecar_names: list[str] = []
        for artifact_index, artifact in enumerate(optional_trace_sidecars):
            descriptor = validate_reasoning_artifact_descriptor(
                artifact,
                label=f"{location}.artifact_spine.optional_trace_sidecars[{artifact_index}]",
            )
            trace_sidecar_names.append(descriptor["artifact_name"])

        eval_bridge = scenario["eval_bridge"]
        if not isinstance(eval_bridge, dict):
            fail(f"{location}.eval_bridge must be an object")
        eval_anchor_refs = validate_unique_string_list(
            eval_bridge.get("eval_anchor_refs"),
            label=f"{location}.eval_bridge.eval_anchor_refs",
        )
        for ref in eval_anchor_refs:
            resolve_known_ref(ref, label=f"{location}.eval_bridge.eval_anchor_refs")
        if eval_bridge.get("verification_surface") != verification_surface["artifact_name"]:
            fail(f"{location}.eval_bridge.verification_surface must match artifact_spine.verification_surface")
        trace_surfaces = validate_unique_string_list(
            eval_bridge.get("trace_surfaces"),
            label=f"{location}.eval_bridge.trace_surfaces",
            allow_empty=True,
        )
        for ref in trace_surfaces:
            resolve_known_ref(ref, label=f"{location}.eval_bridge.trace_surfaces")
        eval_contract_refs = validate_unique_string_list(
            eval_bridge.get("artifact_contract_refs"),
            label=f"{location}.eval_bridge.artifact_contract_refs",
        )
        for ref in eval_contract_refs:
            resolve_known_ref(ref, label=f"{location}.eval_bridge.artifact_contract_refs")
        report_expectation = eval_bridge.get("report_expectation")
        if not isinstance(report_expectation, dict):
            fail(f"{location}.eval_bridge.report_expectation must be an object")
        for key in ("report_format", "verdict_shape", "review_required"):
            if key not in report_expectation:
                fail(f"{location}.eval_bridge.report_expectation is missing '{key}'")

        memo_bridge = scenario["memo_bridge"]
        if not isinstance(memo_bridge, dict):
            fail(f"{location}.memo_bridge must be an object")
        memo_contract_refs = validate_unique_string_list(
            memo_bridge.get("memo_contract_refs"),
            label=f"{location}.memo_bridge.memo_contract_refs",
        )
        for ref in memo_contract_refs:
            resolve_known_ref(ref, label=f"{location}.memo_bridge.memo_contract_refs")
        memo_writeback_targets = validate_unique_string_list(
            memo_bridge.get("memo_writeback_targets"),
            label=f"{location}.memo_bridge.memo_writeback_targets",
        )
        delta_split = memo_bridge.get("delta_split")

        if scenario_ref == "AOA-P-0008":
            if verification_surface["artifact_name"] != "verification_result":
                fail(f"{location} must keep verification_result as the verification surface")
            if continuity_surface is not None:
                fail(f"{location} must not declare a continuity surface")
            if supporting_names != [
                "route_decision",
                "bounded_plan",
                "transition_decision",
                "distillation_pack",
            ]:
                fail(f"{location}.artifact_spine.supporting_artifacts must keep the bounded AOA-P-0008 route artifacts")
            if trace_sidecar_names != ["WitnessTrace"]:
                fail(f"{location}.artifact_spine.optional_trace_sidecars must keep WitnessTrace as the only optional sidecar")
            if trace_surfaces != ["aoa-memo/docs/WITNESS_TRACE_CONTRACT.md"]:
                fail(f"{location}.eval_bridge.trace_surfaces must keep the witness trace contract")
            if memo_writeback_targets != ["decision", "claim", "pattern"]:
                fail(f"{location}.memo_bridge.memo_writeback_targets must keep the bounded AOA-P-0008 writeback targets")
            if delta_split is not None:
                fail(f"{location}.memo_bridge.delta_split must stay null for AOA-P-0008")
            validate_exact_set(
                set(artifact_schema_refs),
                {
                    "aoa-agents/schemas/artifact.route_decision.schema.json",
                    "aoa-agents/schemas/artifact.bounded_plan.schema.json",
                    "aoa-agents/schemas/artifact.verification_result.schema.json",
                    "aoa-agents/schemas/artifact.transition_decision.schema.json",
                    "aoa-agents/schemas/artifact.distillation_pack.schema.json",
                    "aoa-memo/schemas/witness-trace.schema.json",
                },
                label=f"{location}.authoritative_refs.artifact_schema_refs",
            )
        elif scenario_ref == "AOA-P-0009":
            if verification_surface["artifact_name"] != "inquiry_checkpoint":
                fail(f"{location} must keep inquiry_checkpoint as the verification surface")
            if not isinstance(continuity_surface, dict) or continuity_surface.get("artifact_name") != "inquiry_checkpoint":
                fail(f"{location} must keep inquiry_checkpoint as the continuity surface")
            if supporting_names != [
                "decision_ledger",
                "contradiction_map",
                "memory_delta",
                "canon_delta",
                "next_pass_brief",
            ]:
                fail(f"{location}.artifact_spine.supporting_artifacts must keep the bounded AOA-P-0009 route artifacts")
            if trace_sidecar_names:
                fail(f"{location}.artifact_spine.optional_trace_sidecars must stay empty for AOA-P-0009")
            if trace_surfaces:
                fail(f"{location}.eval_bridge.trace_surfaces must stay empty for AOA-P-0009")
            if memo_writeback_targets != ["state_capsule", "decision"]:
                fail(f"{location}.memo_bridge.memo_writeback_targets must keep the bounded AOA-P-0009 writeback targets")
            if not isinstance(delta_split, dict):
                fail(f"{location}.memo_bridge.delta_split must be an object for AOA-P-0009")
            expected_delta_split = {
                "memory_delta": {
                    "artifact_name": "memory_delta",
                    "checkpoint_field": "memory_delta_refs",
                    "field_contract_ref": "aoa-memo/schemas/inquiry_checkpoint.schema.json",
                },
                "canon_delta": {
                    "artifact_name": "canon_delta",
                    "checkpoint_field": "canon_delta_refs",
                    "field_contract_ref": "aoa-memo/schemas/inquiry_checkpoint.schema.json",
                },
            }
            if delta_split != expected_delta_split:
                fail(f"{location}.memo_bridge.delta_split must keep the explicit inquiry checkpoint memory/canon split")
            validate_exact_set(
                set(artifact_schema_refs),
                {
                    "aoa-memo/schemas/inquiry_checkpoint.schema.json",
                    "aoa-memo/schemas/checkpoint-to-memory-contract.schema.json",
                },
                label=f"{location}.authoritative_refs.artifact_schema_refs",
            )
        else:
            fail(f"{location}.scenario_ref '{scenario_ref}' is not supported in this pack")

    validate_exact_set(
        seen_scenarios,
        EXPECTED_REASONING_HANDOFF_SCENARIOS,
        label="reasoning handoff pack scenarios",
    )


def validate_federation_spine_pack(
    payload: object,
    surfaces_by_id: dict[str, dict[str, object]],
    expected_payload: dict[str, object],
) -> None:
    if not isinstance(payload, dict):
        fail("federation spine pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "source_inputs",
        "repo_count",
        "repos",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"federation spine pack is missing required key '{key}'")

    if payload["pack_version"] != 1:
        fail("federation spine pack pack_version must equal 1")
    if payload["pack_type"] != "federation_spine":
        fail("federation spine pack pack_type must equal 'federation_spine'")
    if payload["source_manifest_ref"] != "manifests/federation_spine.json":
        fail("federation spine pack source_manifest_ref must point to manifests/federation_spine.json")
    if payload["bounded_output_contract"] != EXPECTED_FEDERATION_SPINE_CONTRACT:
        fail("federation spine pack bounded_output_contract must match the current source-first guardrail")
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail("federation spine pack source_inputs must match the manifest-driven donor set")
    forbidden_counterpart_refs = set(EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS) | {
        EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_REF,
        "AOA-K-0008",
    }
    if any(value in forbidden_counterpart_refs for value in iter_string_values(payload)):
        fail(
            "federation spine pack must not expose counterpart refs or AOA-K-0008 "
            "activation hints in the current review-closed posture"
        )

    for index, source_input in enumerate(payload["source_inputs"]):
        location = f"federation spine pack source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        ref = source_input.get("ref")
        if not isinstance(ref, str) or not ref:
            fail(f"{location}.ref must be a non-empty string")
        resolve_known_ref(ref, label=location)

    repos = payload["repos"]
    if not isinstance(repos, list) or not repos:
        fail("federation spine pack repos must be a non-empty list")
    repo_count = payload["repo_count"]
    if not isinstance(repo_count, int) or repo_count != len(repos):
        fail("federation spine pack repo_count must equal the number of repos")

    seen_repos: set[str] = set()
    repo_order: list[str] = []
    for index, repo_entry in enumerate(repos):
        location = f"federation spine pack repos[{index}]"
        if not isinstance(repo_entry, dict):
            fail(f"{location} must be an object")
        for key in (
            "repo",
            "pilot_posture",
            "export_ref",
            "kind",
            "object_id",
            "entry_surface_ref",
            "summary_50",
            "provenance_note",
            "non_identity_boundary",
        ):
            if key not in repo_entry:
                fail(f"{location} is missing required key '{key}'")

        repo_name = repo_entry["repo"]
        pilot_posture = repo_entry["pilot_posture"]
        export_ref = repo_entry["export_ref"]
        kind = repo_entry["kind"]
        object_id = repo_entry["object_id"]
        entry_surface_ref = repo_entry["entry_surface_ref"]
        summary_50 = repo_entry["summary_50"]
        provenance_note = repo_entry["provenance_note"]
        non_identity_boundary = repo_entry["non_identity_boundary"]

        if not isinstance(repo_name, str) or not repo_name:
            fail(f"{location}.repo must be a non-empty string")
        if repo_name in seen_repos:
            fail(f"{location}.repo '{repo_name}' is duplicated")
        seen_repos.add(repo_name)
        repo_order.append(repo_name)
        if not isinstance(pilot_posture, str) or not pilot_posture:
            fail(f"{location}.pilot_posture must be a non-empty string")
        if not isinstance(export_ref, str) or not export_ref:
            fail(f"{location}.export_ref must be a non-empty string")
        if not isinstance(kind, str) or not kind:
            fail(f"{location}.kind must be a non-empty string")
        if not isinstance(object_id, str) or not object_id:
            fail(f"{location}.object_id must be a non-empty string")
        if not isinstance(entry_surface_ref, str) or not entry_surface_ref:
            fail(f"{location}.entry_surface_ref must be a non-empty string")
        if not isinstance(summary_50, str) or len(summary_50) < 10:
            fail(f"{location}.summary_50 must be a string of length >= 10")
        if not isinstance(provenance_note, str) or len(provenance_note) < 20:
            fail(f"{location}.provenance_note must be a string of length >= 20")
        if not isinstance(non_identity_boundary, str) or len(non_identity_boundary) < 20:
            fail(f"{location}.non_identity_boundary must be a string of length >= 20")
        resolve_known_ref(export_ref, label=f"{location}.export_ref")
        resolve_known_ref(entry_surface_ref, label=f"{location}.entry_surface_ref")
        if not export_ref.startswith(f"{repo_name}/"):
            fail(f"{location}.export_ref must point to the same repo as the repo entry")
        if not entry_surface_ref.startswith(f"{repo_name}/"):
            fail(f"{location}.entry_surface_ref must point to the same repo as the repo entry")

        surface_0009 = surfaces_by_id.get("AOA-K-0009")
        if surface_0009 is None or surface_0009.get("status") != "experimental":
            fail("federation spine pack requires AOA-K-0009 to remain experimental in the generated registry")

    if repo_order != EXPECTED_FEDERATION_SPINE_REPO_ORDER:
        fail("federation spine pack repos must keep the current stable repo order")
    validate_exact_set(
        seen_repos,
        EXPECTED_FEDERATION_SPINE_REPOS,
        label="federation spine pack repos",
    )
    if payload != expected_payload:
        fail("federation spine pack must match the committed manifest-driven federation payload")


def validate_cross_source_node_projection_pack(
    payload: object,
    surfaces_by_id: dict[str, dict[str, object]],
    expected_payload: dict[str, object],
) -> None:
    if not isinstance(payload, dict):
        fail("cross-source node projection pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "source_inputs",
        "surface_bindings",
        "surface_id",
        "surface_name",
        "projection_count",
        "projections",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"cross-source node projection pack is missing required key '{key}'")

    if payload["pack_type"] != "cross_source_node_projection":
        fail("cross-source node projection pack pack_type must equal 'cross_source_node_projection'")
    if payload["bounded_output_contract"] != EXPECTED_CROSS_SOURCE_NODE_PROJECTION_CONTRACT:
        fail("cross-source node projection pack bounded_output_contract must match the current source-first guardrail")
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail("cross-source node projection pack source_inputs must match the manifest-driven donor set")
    if payload["surface_bindings"] != expected_payload["surface_bindings"]:
        fail("cross-source node projection pack surface_bindings must match the current bounded projection binding")
    forbidden_counterpart_refs = set(EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS) | {
        EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_REF,
        "AOA-K-0008",
    }
    if any(value in forbidden_counterpart_refs for value in iter_string_values(payload)):
        fail(
            "cross-source node projection pack must not expose counterpart refs or "
            "AOA-K-0008 activation hints in the current review-closed posture"
        )

    surface_0006 = surfaces_by_id.get("AOA-K-0006")
    if surface_0006 is None or surface_0006.get("status") != "experimental":
        fail("cross-source node projection pack requires AOA-K-0006 to remain experimental in the generated registry")

    projections = payload["projections"]
    if not isinstance(projections, list) or len(projections) != 1:
        fail("cross-source node projection pack must contain exactly one projection in the current pilot")
    if payload["projection_count"] != 1:
        fail("cross-source node projection pack projection_count must equal 1 in the current pilot")
    projection = projections[0]
    if not isinstance(projection, dict):
        fail("cross-source node projection pack projection must be an object")
    for input_key in ("primary_input",):
        input_payload = projection.get(input_key)
        if not isinstance(input_payload, dict):
            fail(f"cross-source node projection pack {input_key} must be an object")
        resolve_known_ref(input_payload["export_ref"], label=f"cross-source node projection pack {input_key}.export_ref")
    supporting_inputs = projection.get("supporting_inputs")
    if not isinstance(supporting_inputs, list) or len(supporting_inputs) != 1:
        fail("cross-source node projection pack supporting_inputs must contain exactly one supporting export in the current pilot")
    resolve_known_ref(
        supporting_inputs[0]["export_ref"],
        label="cross-source node projection pack supporting_inputs[0].export_ref",
    )
    resolve_known_ref(
        projection["retrieval_axis_ref"],
        label="cross-source node projection pack retrieval_axis_ref",
    )
    resolve_known_ref(
        projection["federation_spine_ref"],
        label="cross-source node projection pack federation_spine_ref",
    )
    if payload != expected_payload:
        fail("cross-source node projection pack must match the committed manifest-driven projection payload")


def validate_cross_source_node_projection_example(expected_payload: dict[str, object]) -> None:
    payload = read_json(CROSS_SOURCE_NODE_PROJECTION_EXAMPLE_PATH)
    if payload != expected_payload:
        fail("cross-source node projection example must match the current bounded projection payload")


def validate_tiny_consumer_bundle_pack(expected_payload: dict[str, object]) -> None:
    payload = read_json(TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH)
    if not isinstance(payload, dict):
        fail("tiny consumer bundle pack must be a JSON object")

    for key in (
        "bundle_version",
        "bundle_type",
        "source_manifest_ref",
        "source_inputs",
        "bundle_item_count",
        "bundle_items",
        "deferred_counterpart",
    ):
        if key not in payload:
            fail(f"tiny consumer bundle pack is missing required key '{key}'")

    if payload["bundle_version"] != 1:
        fail("tiny consumer bundle pack bundle_version must equal 1")
    if payload["bundle_type"] != "tiny_consumer_bundle":
        fail("tiny consumer bundle pack bundle_type must equal 'tiny_consumer_bundle'")
    if payload["source_manifest_ref"] != "manifests/tiny_consumer_bundle.json":
        fail(
            "tiny consumer bundle pack source_manifest_ref must point to "
            "manifests/tiny_consumer_bundle.json"
        )
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail("tiny consumer bundle pack source_inputs must match the manifest-driven donor set")

    bundle_items = payload["bundle_items"]
    if not isinstance(bundle_items, list) or not bundle_items:
        fail("tiny consumer bundle pack bundle_items must be a non-empty list")
    if payload["bundle_item_count"] != len(bundle_items):
        fail("tiny consumer bundle pack bundle_item_count must equal the number of bundle_items")

    observed_order: list[str] = []
    for index, bundle_item in enumerate(bundle_items):
        location = f"tiny consumer bundle pack bundle_items[{index}]"
        if not isinstance(bundle_item, dict):
            fail(f"{location} must be an object")
        for key in ("order", "name", "role", "ref"):
            if key not in bundle_item:
                fail(f"{location} is missing required key '{key}'")
        if bundle_item["order"] != index + 1:
            fail(f"{location}.order must keep the stable 1-based bundle order")
        if not isinstance(bundle_item["name"], str) or not bundle_item["name"]:
            fail(f"{location}.name must be a non-empty string")
        if not isinstance(bundle_item["role"], str) or not bundle_item["role"]:
            fail(f"{location}.role must be a non-empty string")
        if not isinstance(bundle_item["ref"], str) or not bundle_item["ref"]:
            fail(f"{location}.ref must be a non-empty string")
        resolve_known_ref(bundle_item["ref"], label=f"{location}.ref")
        observed_order.append(bundle_item["name"])

    if observed_order != EXPECTED_TINY_CONSUMER_BUNDLE_ORDER:
        fail("tiny consumer bundle pack bundle_items must keep the current stable bundle order")
    if payload["deferred_counterpart"] != EXPECTED_TINY_CONSUMER_BUNDLE_DEFERRED_COUNTERPART:
        fail("tiny consumer bundle pack deferred_counterpart must match the contract-only posture")
    resolve_known_ref(
        payload["deferred_counterpart"]["federation_exposure_review_ref"],
        label="tiny consumer bundle pack deferred_counterpart.federation_exposure_review_ref",
    )
    if payload != expected_payload:
        fail("tiny consumer bundle pack must match the committed manifest-driven bundle payload")


def validate_tiny_consumer_bundle_example(expected_payload: dict[str, object]) -> None:
    payload = read_json(TINY_CONSUMER_BUNDLE_EXAMPLE_PATH)
    if payload != expected_payload:
        fail("tiny consumer bundle example must match the current bundle payload")


def validate_counterpart_federation_exposure_review_pack(
    expected_payload: dict[str, object],
) -> None:
    payload = read_json(COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_OUTPUT_PATH)
    if not isinstance(payload, dict):
        fail("counterpart federation exposure review pack must be a JSON object")

    for key in (
        "review_version",
        "review_type",
        "source_manifest_ref",
        "source_inputs",
        "surface_id",
        "surface_status",
        "review_status",
        "reviewed_surface_count",
        "reviewed_surfaces",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(
                "counterpart federation exposure review pack is missing required key "
                f"'{key}'"
            )

    if payload["review_version"] != 1:
        fail("counterpart federation exposure review pack review_version must equal 1")
    if payload["review_type"] != "counterpart_federation_exposure_review":
        fail(
            "counterpart federation exposure review pack review_type must equal "
            "'counterpart_federation_exposure_review'"
        )
    if payload["source_manifest_ref"] != "manifests/counterpart_federation_exposure_review.json":
        fail(
            "counterpart federation exposure review pack source_manifest_ref must point "
            "to manifests/counterpart_federation_exposure_review.json"
        )
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail(
            "counterpart federation exposure review pack source_inputs must match the "
            "manifest-driven donor set"
        )
    if payload["surface_id"] != "AOA-K-0008":
        fail("counterpart federation exposure review pack surface_id must equal 'AOA-K-0008'")
    if payload["surface_status"] != "planned":
        fail("counterpart federation exposure review pack surface_status must equal 'planned'")
    if payload["review_status"] != "passed_for_planned_posture":
        fail(
            "counterpart federation exposure review pack review_status must equal "
            "'passed_for_planned_posture'"
        )
    if payload["bounded_output_contract"] != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_CONTRACT:
        fail(
            "counterpart federation exposure review pack bounded_output_contract must "
            "match the current review guardrail"
        )

    reviewed_surfaces = payload["reviewed_surfaces"]
    if not isinstance(reviewed_surfaces, list) or not reviewed_surfaces:
        fail("counterpart federation exposure review pack reviewed_surfaces must be a non-empty list")
    if payload["reviewed_surface_count"] != len(reviewed_surfaces):
        fail(
            "counterpart federation exposure review pack reviewed_surface_count must "
            "equal the number of reviewed_surfaces"
        )

    observed_order: list[str] = []
    for index, reviewed_surface in enumerate(reviewed_surfaces):
        location = f"counterpart federation exposure review pack reviewed_surfaces[{index}]"
        if not isinstance(reviewed_surface, dict):
            fail(f"{location} must be an object")
        for key in ("surface_name", "surface_ref", "exposure_posture", "review_note"):
            if key not in reviewed_surface:
                fail(f"{location} is missing required key '{key}'")
        surface_name = reviewed_surface["surface_name"]
        surface_ref = reviewed_surface["surface_ref"]
        exposure_posture = reviewed_surface["exposure_posture"]
        observed_order.append(surface_name)
        resolve_known_ref(surface_ref, label=f"{location}.surface_ref")
        expected_posture = EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_POSTURES.get(surface_name)
        if exposure_posture != expected_posture:
            fail(
                f"{location}.exposure_posture must match the current reviewed posture "
                f"for '{surface_name}'"
            )
        if surface_name in {"reasoning_handoff_pack", "tiny_consumer_bundle"}:
            if reviewed_surface.get("allowed_counterpart_refs") != EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS:
                fail(
                    f"{location}.allowed_counterpart_refs must match the current "
                    "contract-only counterpart refs"
                )
        elif surface_name in {"federation_spine", "cross_source_node_projection"}:
            if reviewed_surface.get("forbidden_refs") != EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS:
                fail(
                    f"{location}.forbidden_refs must match the current forbidden "
                    "counterpart exposure set"
                )

    if observed_order != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_ORDER:
        fail(
            "counterpart federation exposure review pack reviewed_surfaces must keep "
            "the current reviewed surface order"
        )
    if payload != expected_payload:
        fail(
            "counterpart federation exposure review pack must match the committed "
            "manifest-driven review payload"
        )


def validate_counterpart_federation_exposure_review_example(
    expected_payload: dict[str, object],
) -> None:
    payload = read_json(COUNTERPART_FEDERATION_EXPOSURE_REVIEW_EXAMPLE_PATH)
    if payload != expected_payload:
        fail(
            "counterpart federation exposure review example must match the current "
            "review payload"
        )


def validate_generated_text(path: Path, expected_text: str, *, label: str) -> None:
    try:
        actual_text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"{label} is missing at {display_path(path)}")
    if actual_text != expected_text:
        fail(f"{label} is out of date; run python scripts/generate_kag.py")


def validate_technique_lift_pack(
    payload: object,
    surfaces_by_id: dict[str, dict[str, object]],
) -> None:
    if not isinstance(payload, dict):
        fail("technique lift pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_repo",
        "source_manifest_ref",
        "source_inputs",
        "surface_bindings",
        "section_scope",
        "technique_count",
        "techniques",
    ):
        if key not in payload:
            fail(f"technique lift pack is missing required key '{key}'")

    if payload["pack_version"] != 1:
        fail("technique lift pack pack_version must equal 1")
    if payload["pack_type"] != "technique_lift_pack":
        fail("technique lift pack pack_type must equal 'technique_lift_pack'")
    if payload["source_repo"] != "aoa-techniques":
        fail("technique lift pack source_repo must equal 'aoa-techniques'")
    if payload["source_manifest_ref"] != "manifests/technique_lift_pack.json":
        fail("technique lift pack source_manifest_ref must point to manifests/technique_lift_pack.json")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("technique lift pack source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str]] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"technique lift pack source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        role = source_input.get("role")
        ref = source_input.get("ref")
        if not all(isinstance(value, str) and value for value in (name, role, ref)):
            fail(f"{location} must keep name, role, and ref")
        resolve_aoa_techniques_ref(ref, label=location)
        actual_source_inputs.add((name, ref.split("/", 1)[1], role))
    if actual_source_inputs != EXPECTED_TECHNIQUE_LIFT_INPUTS:
        fail("technique lift pack source_inputs must match the manifest-driven donor set")

    surface_bindings = payload["surface_bindings"]
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("technique lift pack surface_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, str, str]] = set()
    for index, binding in enumerate(surface_bindings):
        location = f"technique lift pack surface_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")
        surface_id = binding.get("surface_id")
        surface_name = binding.get("surface_name")
        derived_kind = binding.get("derived_kind")
        derived_slot = binding.get("derived_slot")
        source_input = binding.get("source_input")
        if not all(
            isinstance(value, str) and value
            for value in (
                surface_id,
                surface_name,
                derived_kind,
                derived_slot,
                source_input,
            )
        ):
            fail(f"{location} must keep id, name, kind, slot, and source input")
        actual_bindings.add(
            (surface_id, surface_name, derived_kind, derived_slot, source_input)
        )
        surface = surfaces_by_id.get(surface_id)
        if surface is None:
            fail(f"{location} references unknown registry surface '{surface_id}'")
        if surface.get("name") != surface_name:
            fail(f"{location} does not match the generated registry surface name")
        if surface.get("derived_kind") != derived_kind:
            fail(f"{location} does not match the generated registry derived_kind")
        if surface.get("status") != "active":
            fail(f"{location} must only point to active registry surfaces")
    if actual_bindings != EXPECTED_TECHNIQUE_LIFT_BINDINGS:
        fail("technique lift pack surface_bindings must match the current bounded technique lift bindings")

    section_scope = validate_unique_string_list(
        payload["section_scope"],
        label="technique lift pack section_scope",
    )

    techniques = payload["techniques"]
    if not isinstance(techniques, list) or not techniques:
        fail("technique lift pack techniques must be a non-empty list")
    technique_count = payload["technique_count"]
    if not isinstance(technique_count, int) or technique_count != len(techniques):
        fail("technique lift pack technique_count must equal the number of techniques")

    seen_technique_ids: set[str] = set()
    for index, technique in enumerate(techniques):
        location = f"technique lift pack techniques[{index}]"
        if not isinstance(technique, dict):
            fail(f"{location} must be an object")

        for key in (
            "technique_id",
            "technique_name",
            "source_ref",
            "section_lift",
            "metadata_spine",
            "relation_view",
            "provenance_view",
        ):
            if key not in technique:
                fail(f"{location} is missing required key '{key}'")

        technique_id = technique["technique_id"]
        technique_name = technique["technique_name"]
        source_ref = technique["source_ref"]
        if not isinstance(technique_id, str) or not re.match(r"^AOA-T-[0-9]{4}$", technique_id):
            fail(f"{location}.technique_id must be an AOA technique id")
        if technique_id in seen_technique_ids:
            fail(f"{location}.technique_id '{technique_id}' is duplicated")
        seen_technique_ids.add(technique_id)
        if not isinstance(technique_name, str) or not technique_name:
            fail(f"{location}.technique_name must be a non-empty string")
        if not isinstance(source_ref, str) or not source_ref.startswith("aoa-techniques/"):
            fail(f"{location}.source_ref must point to aoa-techniques")
        resolve_aoa_techniques_ref(source_ref, label=f"{location}.source_ref")

        section_lift = technique["section_lift"]
        if not isinstance(section_lift, dict):
            fail(f"{location}.section_lift must be an object")
        section_count = section_lift.get("section_count")
        sections = section_lift.get("sections")
        if not isinstance(sections, list) or not sections:
            fail(f"{location}.section_lift.sections must be a non-empty list")
        if not isinstance(section_count, int) or section_count != len(sections):
            fail(f"{location}.section_lift.section_count must equal the number of sections")
        seen_headings: set[str] = set()
        for section_index, section in enumerate(sections):
            section_location = f"{location}.section_lift.sections[{section_index}]"
            if not isinstance(section, dict):
                fail(f"{section_location} must be an object")
            heading = section.get("heading")
            order = section.get("order")
            if not isinstance(heading, str) or not heading:
                fail(f"{section_location}.heading must be a non-empty string")
            if heading not in section_scope:
                fail(f"{section_location}.heading '{heading}' must appear in section_scope")
            if heading in seen_headings:
                fail(f"{section_location}.heading '{heading}' is duplicated for {technique_id}")
            seen_headings.add(heading)
            if not isinstance(order, int) or order < 1:
                fail(f"{section_location}.order must be a positive integer")

        metadata_spine = technique["metadata_spine"]
        if not isinstance(metadata_spine, dict):
            fail(f"{location}.metadata_spine must be an object")
        for key in (
            "domain",
            "status",
            "summary",
            "maturity_score",
            "rigor_level",
            "reversibility",
            "review_required",
            "validation_strength",
            "export_ready",
        ):
            if key not in metadata_spine:
                fail(f"{location}.metadata_spine is missing '{key}'")
        if not isinstance(metadata_spine["domain"], str) or not metadata_spine["domain"]:
            fail(f"{location}.metadata_spine.domain must be a non-empty string")
        if not isinstance(metadata_spine["status"], str) or not metadata_spine["status"]:
            fail(f"{location}.metadata_spine.status must be a non-empty string")
        if not isinstance(metadata_spine["summary"], str) or len(metadata_spine["summary"]) < 10:
            fail(f"{location}.metadata_spine.summary must be a string of length >= 10")
        if not isinstance(metadata_spine["maturity_score"], int) or metadata_spine["maturity_score"] < 0:
            fail(f"{location}.metadata_spine.maturity_score must be a non-negative integer")
        if not isinstance(metadata_spine["review_required"], bool):
            fail(f"{location}.metadata_spine.review_required must be a boolean")
        if not isinstance(metadata_spine["export_ready"], bool):
            fail(f"{location}.metadata_spine.export_ready must be a boolean")

        relation_view = technique["relation_view"]
        if not isinstance(relation_view, dict):
            fail(f"{location}.relation_view must be an object")
        relation_count = relation_view.get("relation_count")
        relations = relation_view.get("relations")
        if not isinstance(relations, list):
            fail(f"{location}.relation_view.relations must be a list")
        if not isinstance(relation_count, int) or relation_count != len(relations):
            fail(f"{location}.relation_view.relation_count must equal the number of relations")
        for relation_index, relation in enumerate(relations):
            relation_location = f"{location}.relation_view.relations[{relation_index}]"
            if not isinstance(relation, dict):
                fail(f"{relation_location} must be an object")
            relation_type = relation.get("relation_type")
            target_ref = relation.get("target_ref")
            if not isinstance(relation_type, str) or not relation_type:
                fail(f"{relation_location}.relation_type must be a non-empty string")
            if not isinstance(target_ref, str) or not target_ref.startswith("aoa-techniques/AOA-T-"):
                fail(f"{relation_location}.target_ref must be an aoa-techniques technique ref")

        provenance_view = technique["provenance_view"]
        if not isinstance(provenance_view, dict):
            fail(f"{location}.provenance_view must be an object")
        reviewed_at = provenance_view.get("public_safety_reviewed_at")
        note_count = provenance_view.get("note_count")
        note_handles = provenance_view.get("note_handles")
        if not isinstance(reviewed_at, str) or not DATE_RE.match(reviewed_at):
            fail(f"{location}.provenance_view.public_safety_reviewed_at must be a YYYY-MM-DD string")
        if not isinstance(note_handles, list):
            fail(f"{location}.provenance_view.note_handles must be a list")
        if not isinstance(note_count, int) or note_count != len(note_handles):
            fail(f"{location}.provenance_view.note_count must equal the number of note handles")
        seen_note_refs: set[str] = set()
        for note_index, note_handle in enumerate(note_handles):
            note_location = f"{location}.provenance_view.note_handles[{note_index}]"
            if not isinstance(note_handle, dict):
                fail(f"{note_location} must be an object")
            kind = note_handle.get("kind")
            title = note_handle.get("title")
            note_ref = note_handle.get("note_ref")
            if not all(isinstance(value, str) and value for value in (kind, title, note_ref)):
                fail(f"{note_location} must keep kind, title, and note_ref")
            if note_ref in seen_note_refs:
                fail(f"{note_location}.note_ref '{note_ref}' is duplicated for {technique_id}")
            seen_note_refs.add(note_ref)
            resolve_aoa_techniques_ref(note_ref, label=f"{note_location}.note_ref")


def validate_bridge_example(surfaces_by_id: dict[str, dict[str, object]]) -> None:
    payload = read_json(BRIDGE_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("bridge example must be a JSON object")

    surface_id = payload.get("surface_id")
    if surface_id != "AOA-K-0007":
        fail("bridge example surface_id must equal 'AOA-K-0007'")
    if surface_id not in surfaces_by_id:
        fail("bridge example surface_id must exist in the generated registry")

    registry_entry = surfaces_by_id[surface_id]
    if registry_entry["derived_kind"] != "retrieval_surface":
        fail("AOA-K-0007 must remain a retrieval_surface")
    if registry_entry["source_class"] != "tos_text":
        fail("AOA-K-0007 must keep 'tos_text' as its primary source_class")

    for key in ("source_refs", "lineage_refs"):
        value = payload.get(key)
        validate_unique_string_list(value, label=f"bridge example '{key}'")

    for key in ("conflict_refs", "practice_refs"):
        value = payload.get(key)
        if value is None:
            continue
        validate_unique_string_list(value, label=f"bridge example '{key}'")

    axis_summary = payload.get("axis_summary")
    if not isinstance(axis_summary, str) or len(axis_summary) < 20:
        fail("bridge example 'axis_summary' must be a string of length >= 20")


def validate_bridge_envelope_example() -> None:
    payload = read_json(BRIDGE_ENVELOPE_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("bridge envelope example must be a JSON object")

    if payload.get("bridge_id") != "aoa-tos-bridge-envelope-v1":
        fail("bridge envelope example bridge_id must equal 'aoa-tos-bridge-envelope-v1'")
    if payload.get("source_class") != "tos_text":
        fail("bridge envelope example source_class must remain 'tos_text'")
    if payload.get("kag_lift_status") != "candidate":
        fail("bridge envelope example kag_lift_status must remain 'candidate'")

    source_inputs = payload.get("source_inputs")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("bridge envelope example source_inputs must be a non-empty list")
    expected_inputs = {
        ("Tree-of-Sophia", "tos_text", "primary"),
        ("aoa-memo", "memo_object", "supporting"),
    }
    actual_inputs: set[tuple[str, str, str]] = set()
    primary_count = 0
    for index, item in enumerate(source_inputs):
        location = f"bridge envelope example source_inputs[{index}]"
        if not isinstance(item, dict):
            fail(f"{location} must be an object")
        repo = item.get("repo")
        source_class = item.get("source_class")
        role = item.get("role")
        if not isinstance(repo, str) or not repo:
            fail(f"{location}.repo must be a non-empty string")
        if not isinstance(source_class, str) or not source_class:
            fail(f"{location}.source_class must be a non-empty string")
        if not isinstance(role, str) or not role:
            fail(f"{location}.role must be a non-empty string")
        if role == "primary":
            primary_count += 1
        actual_inputs.add((repo, source_class, role))
    if actual_inputs != expected_inputs:
        fail("bridge envelope example source_inputs must match the current strict bridge contract")
    if primary_count != 1:
        fail("bridge envelope example must keep exactly one primary source input")

    for index, ref in enumerate(
        validate_unique_string_list(payload.get("tos_refs"), label="bridge envelope example tos_refs")
    ):
        resolve_known_ref(ref, label=f"bridge envelope example tos_refs[{index}]")
    for index, ref in enumerate(
        validate_unique_string_list(payload.get("memory_refs"), label="bridge envelope example memory_refs")
    ):
        resolve_known_ref(ref, label=f"bridge envelope example memory_refs[{index}]")

    faces = payload.get("faces")
    if not isinstance(faces, dict):
        fail("bridge envelope example faces must be an object")
    expected_faces = {
        "retrieval_surface": "examples/tos_retrieval_axis_surface.example.json",
        "chunk_face": "aoa-memo/examples/memory_chunk_face.bridge.example.json",
        "graph_face": "aoa-memo/examples/memory_graph_face.bridge.example.json",
    }
    if set(faces) != set(expected_faces):
        fail("bridge envelope example faces must expose retrieval_surface, chunk_face, and graph_face")
    for key, expected_ref in expected_faces.items():
        value = faces.get(key)
        if value != expected_ref:
            fail(f"bridge envelope example faces.{key} must equal '{expected_ref}'")
        resolve_known_ref(value, label=f"bridge envelope example faces.{key}")


def validate_counterpart_example(surfaces_by_id: dict[str, dict[str, object]]) -> None:
    payload = read_json(COUNTERPART_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("counterpart example must be a JSON object")

    surface_id = payload.get("surface_id")
    if surface_id != "AOA-K-0008":
        fail("counterpart example surface_id must equal 'AOA-K-0008'")
    if surface_id not in surfaces_by_id:
        fail("counterpart example surface_id must exist in the generated registry")

    registry_entry = surfaces_by_id[surface_id]
    if registry_entry["derived_kind"] != "edge_projection":
        fail("AOA-K-0008 must remain an edge_projection")
    if registry_entry["status"] != "planned":
        fail("AOA-K-0008 must remain planned in the registry")
    if registry_entry["source_class"] != "tos_text":
        fail("AOA-K-0008 must keep 'tos_text' as its primary source_class")

    mappings = payload.get("mappings")
    if not isinstance(mappings, list) or not mappings:
        fail("counterpart example 'mappings' must be a non-empty list")

    seen_mapping_ids: set[str] = set()
    seen_modes: set[str] = set()
    source_inputs = registry_entry.get("source_inputs")
    supporting_repos = {
        item["repo"]
        for item in source_inputs
        if isinstance(item, dict) and item.get("role") == "supporting"
    }

    for index, mapping in enumerate(mappings):
        location = f"counterpart example mappings[{index}]"
        if not isinstance(mapping, dict):
            fail(f"{location} must be an object")
        for key in (
            "mapping_id",
            "concept_ref",
            "operational_ref",
            "counterpart_mode",
            "evidence_note",
            "non_identity_note",
        ):
            if key not in mapping:
                fail(f"{location} is missing required key '{key}'")

        mapping_id = mapping["mapping_id"]
        concept_ref = mapping["concept_ref"]
        operational_ref = mapping["operational_ref"]
        counterpart_mode = mapping["counterpart_mode"]
        evidence_note = mapping["evidence_note"]
        non_identity_note = mapping["non_identity_note"]
        supporting_refs = mapping.get("supporting_refs")

        if not isinstance(mapping_id, str) or len(mapping_id) < 1:
            fail(f"{location}.mapping_id must be a non-empty string")
        if mapping_id in seen_mapping_ids:
            fail(f"{location}.mapping_id '{mapping_id}' is duplicated")
        seen_mapping_ids.add(mapping_id)

        if not isinstance(concept_ref, str) or not concept_ref.startswith("Tree-of-Sophia/"):
            fail(f"{location}.concept_ref must point to a Tree-of-Sophia surface")
        if not isinstance(operational_ref, str) or "/" not in operational_ref:
            fail(f"{location}.operational_ref must be a non-empty repo-qualified string")
        operational_repo = operational_ref.split("/", 1)[0]
        if operational_repo not in supporting_repos:
            fail(f"{location}.operational_ref repo '{operational_repo}' must match a supporting source repo")

        if counterpart_mode not in ALLOWED_COUNTERPART_MODE:
            fail(f"{location}.counterpart_mode '{counterpart_mode}' is not allowed")
        seen_modes.add(counterpart_mode)

        if not isinstance(evidence_note, str) or len(evidence_note) < 20:
            fail(f"{location}.evidence_note must be a string of length >= 20")
        if not isinstance(non_identity_note, str) or len(non_identity_note) < 20:
            fail(f"{location}.non_identity_note must be a string of length >= 20")

        if supporting_refs is not None:
            refs = validate_unique_string_list(
                supporting_refs,
                label=f"{location}.supporting_refs",
            )
            for supporting_ref in refs:
                if "/" not in supporting_ref:
                    fail(f"{location}.supporting_refs contains an invalid repo-qualified ref")
                supporting_repo = supporting_ref.split("/", 1)[0]
                if supporting_repo not in supporting_repos:
                    fail(f"{location}.supporting_refs repo '{supporting_repo}' must match a supporting source repo")

    if seen_modes != ALLOWED_COUNTERPART_MODE:
        fail("counterpart example must cover all supported counterpart modes at least once")


def validate_counterpart_consumer_contract_example(
    surfaces_by_id: dict[str, dict[str, object]]
) -> None:
    payload = read_json(COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("counterpart consumer contract example must be a JSON object")

    for key in (
        "contract_type",
        "surface_id",
        "surface_status",
        "consumer_surface_type",
        "allowed_return_field",
        "federation_exposure_review_ref",
        "required_contract_refs",
        "allowed_refs",
        "forbidden_interpretations",
    ):
        if key not in payload:
            fail(f"counterpart consumer contract example is missing required key '{key}'")

    if payload["contract_type"] != "counterpart_consumer_contract":
        fail(
            "counterpart consumer contract example contract_type must equal "
            "'counterpart_consumer_contract'"
        )
    if payload["surface_id"] != "AOA-K-0008":
        fail("counterpart consumer contract example surface_id must equal 'AOA-K-0008'")
    if payload["surface_status"] != "planned":
        fail("counterpart consumer contract example surface_status must equal 'planned'")
    if payload["consumer_surface_type"] != "reasoning_handoff_guardrail":
        fail(
            "counterpart consumer contract example consumer_surface_type must equal "
            "'reasoning_handoff_guardrail'"
        )
    if payload["allowed_return_field"] != "counterpart_refs":
        fail(
            "counterpart consumer contract example allowed_return_field must equal "
            "'counterpart_refs'"
        )
    if (
        payload["federation_exposure_review_ref"]
        != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_REF
    ):
        fail(
            "counterpart consumer contract example federation_exposure_review_ref must "
            "point to the current review artifact"
        )
    resolve_known_ref(
        payload["federation_exposure_review_ref"],
        label="counterpart consumer contract example federation_exposure_review_ref",
    )

    registry_surface = surfaces_by_id.get("AOA-K-0008")
    if registry_surface is None:
        fail("counterpart consumer contract example requires AOA-K-0008 in the generated registry")
    if registry_surface.get("status") != "planned":
        fail("counterpart consumer contract example requires AOA-K-0008 to remain planned")

    required_contract_refs = payload["required_contract_refs"]
    if not isinstance(required_contract_refs, dict):
        fail("counterpart consumer contract example required_contract_refs must be an object")
    if required_contract_refs != EXPECTED_COUNTERPART_CONSUMER_CONTRACT_REFS:
        fail(
            "counterpart consumer contract example required_contract_refs must match the "
            "current counterpart contract surfaces"
        )
    for key, ref in required_contract_refs.items():
        resolve_known_ref(
            ref,
            label=f"counterpart consumer contract example required_contract_refs.{key}",
        )

    allowed_refs = validate_unique_string_list(
        payload["allowed_refs"],
        label="counterpart consumer contract example allowed_refs",
    )
    if allowed_refs != EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS:
        fail(
            "counterpart consumer contract example allowed_refs must keep the current "
            "contract/example-only posture"
        )
    for index, ref in enumerate(allowed_refs):
        resolve_known_ref(
            ref,
            label=f"counterpart consumer contract example allowed_refs[{index}]",
        )

    forbidden_interpretations = validate_unique_string_list(
        payload["forbidden_interpretations"],
        label="counterpart consumer contract example forbidden_interpretations",
    )
    if forbidden_interpretations != EXPECTED_COUNTERPART_CONSUMER_FORBIDDEN_INTERPRETATIONS:
        fail(
            "counterpart consumer contract example forbidden_interpretations must match "
            "the bounded contract"
        )


def validate_reasoning_handoff_example() -> None:
    payload = read_json(REASONING_HANDOFF_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("reasoning handoff example must be a JSON object")

    for key in (
        "surface_type",
        "handoff_id",
        "supported_query_modes",
        "authoritative_source_refs",
        "derived_surface_refs",
        "provenance_posture",
        "return_contract",
        "boundary_guardrails",
    ):
        if key not in payload:
            fail(f"reasoning handoff example is missing required key '{key}'")

    if payload["surface_type"] != "reasoning_handoff_guardrail":
        fail("reasoning handoff example surface_type must equal 'reasoning_handoff_guardrail'")

    handoff_id = payload["handoff_id"]
    if not isinstance(handoff_id, str) or len(handoff_id) < 3:
        fail("reasoning handoff example handoff_id must be a string of length >= 3")

    query_modes = validate_unique_string_list(
        payload["supported_query_modes"],
        label="reasoning handoff example supported_query_modes",
    )
    validate_exact_set(
        query_modes,
        ALLOWED_QUERY_MODES,
        label="reasoning handoff example supported_query_modes",
    )

    authoritative_source_refs = validate_unique_string_list(
        payload["authoritative_source_refs"],
        label="reasoning handoff example authoritative_source_refs",
    )
    validate_exact_set(
        authoritative_source_refs,
        EXPECTED_AUTHORITATIVE_SOURCE_REFS,
        label="reasoning handoff example authoritative_source_refs",
    )
    for ref in authoritative_source_refs:
        resolve_authoritative_ref(ref, label="reasoning handoff example authoritative_source_refs")

    derived_surface_refs = validate_unique_string_list(
        payload["derived_surface_refs"],
        label="reasoning handoff example derived_surface_refs",
    )
    validate_exact_set(
        derived_surface_refs,
        EXPECTED_DERIVED_SURFACE_REFS,
        label="reasoning handoff example derived_surface_refs",
    )
    for ref in derived_surface_refs:
        resolve_relative_ref(
            REPO_ROOT,
            ref,
            label="reasoning handoff example derived_surface_refs",
        )

    provenance_posture = payload["provenance_posture"]
    if provenance_posture != EXPECTED_PROVENANCE_POSTURE:
        fail("reasoning handoff example provenance_posture must match the bounded guardrail contract")

    return_contract = payload["return_contract"]
    if not isinstance(return_contract, dict):
        fail("reasoning handoff example return_contract must be an object")

    for key in ("must_include", "may_include"):
        if key not in return_contract:
            fail(f"reasoning handoff example return_contract is missing '{key}'")

    must_include = validate_unique_string_list(
        return_contract["must_include"],
        label="reasoning handoff example return_contract.must_include",
    )
    validate_exact_set(
        must_include,
        EXPECTED_RETURN_MUST_INCLUDE,
        label="reasoning handoff example return_contract.must_include",
    )

    may_include = validate_unique_string_list(
        return_contract["may_include"],
        label="reasoning handoff example return_contract.may_include",
    )
    validate_exact_set(
        may_include,
        EXPECTED_RETURN_MAY_INCLUDE,
        label="reasoning handoff example return_contract.may_include",
    )

    if set(must_include) & set(may_include):
        fail("reasoning handoff example return_contract must not overlap must_include and may_include")

    boundary_guardrails = payload["boundary_guardrails"]
    if boundary_guardrails != EXPECTED_BOUNDARY_GUARDRAILS:
        fail("reasoning handoff example boundary_guardrails must match the bounded guardrail contract")


def validate_federation_kag_export_example() -> None:
    payload = read_json(FEDERATION_KAG_EXPORT_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("federation KAG export example must be a JSON object")

    for key in (
        "owner_repo",
        "kind",
        "object_id",
        "primary_question",
        "summary_50",
        "summary_200",
        "source_inputs",
        "entry_surface",
        "section_handles",
        "direct_relations",
        "provenance_note",
        "non_identity_boundary",
    ):
        if key not in payload:
            fail(f"federation KAG export example is missing required key '{key}'")

    owner_repo = payload["owner_repo"]
    kind = payload["kind"]
    object_id = payload["object_id"]
    primary_question = payload["primary_question"]
    summary_50 = payload["summary_50"]
    summary_200 = payload["summary_200"]
    provenance_note = payload["provenance_note"]
    non_identity_boundary = payload["non_identity_boundary"]

    if owner_repo != "aoa-techniques":
        fail("federation KAG export example owner_repo must equal 'aoa-techniques'")
    if kind != "technique":
        fail("federation KAG export example kind must equal 'technique'")
    if not isinstance(object_id, str) or not re.match(r"^AOA-T-[0-9]{4}$", object_id):
        fail("federation KAG export example object_id must be an AOA technique id")
    for label, value, min_length in (
        ("primary_question", primary_question, 10),
        ("summary_50", summary_50, 10),
        ("summary_200", summary_200, 20),
        ("provenance_note", provenance_note, 10),
        ("non_identity_boundary", non_identity_boundary, 10),
    ):
        if not isinstance(value, str) or len(value) < min_length:
            fail(f"federation KAG export example {label} must be a string of length >= {min_length}")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("federation KAG export example source_inputs must be a non-empty list")
    primary_count = 0
    for index, source_input in enumerate(source_inputs):
        location = f"federation KAG export example source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        repo = source_input.get("repo")
        source_class = source_input.get("source_class")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (repo, source_class, role)):
            fail(f"{location} must keep repo, source_class, and role")
        if role == "primary":
            primary_count += 1
    if primary_count != 1:
        fail("federation KAG export example source_inputs must contain exactly one primary input")

    entry_surface = payload["entry_surface"]
    if not isinstance(entry_surface, dict):
        fail("federation KAG export example entry_surface must be an object")
    for key in ("repo", "path", "match_key", "match_value"):
        if key not in entry_surface:
            fail(f"federation KAG export example entry_surface is missing '{key}'")
    entry_repo = entry_surface["repo"]
    entry_path = entry_surface["path"]
    match_key = entry_surface["match_key"]
    match_value = entry_surface["match_value"]
    if not all(isinstance(value, str) and value for value in (entry_repo, entry_path, match_key, match_value)):
        fail("federation KAG export example entry_surface fields must be non-empty strings")
    resolve_known_ref(repo_ref(entry_repo, entry_path), label="federation KAG export example entry_surface")
    if match_value != object_id:
        fail("federation KAG export example entry_surface.match_value must equal object_id")

    section_handles = validate_unique_string_list(
        payload["section_handles"],
        label="federation KAG export example section_handles",
    )
    if not section_handles:
        fail("federation KAG export example section_handles must not be empty")

    direct_relations = payload["direct_relations"]
    if not isinstance(direct_relations, list):
        fail("federation KAG export example direct_relations must be a list")
    for index, relation in enumerate(direct_relations):
        location = f"federation KAG export example direct_relations[{index}]"
        if not isinstance(relation, dict):
            fail(f"{location} must be an object")
        relation_type = relation.get("relation_type")
        target_ref = relation.get("target_ref")
        if not all(isinstance(value, str) and value for value in (relation_type, target_ref)):
            fail(f"{location} must keep relation_type and target_ref")
        resolve_known_ref(target_ref, label=location)


def main() -> int:
    try:
        validate_schema_surface()
        validate_bridge_schema_surface()
        validate_bridge_envelope_schema_surface()
        validate_counterpart_schema_surface()
        validate_counterpart_federation_exposure_review_manifest_schema_surface()
        validate_counterpart_federation_exposure_review_schema_surface()
        validate_counterpart_consumer_contract_schema_surface()
        validate_reasoning_handoff_schema_surface()
        validate_technique_lift_manifest_schema_surface()
        validate_technique_lift_pack_schema_surface()
        validate_tos_text_chunk_map_manifest_schema_surface()
        validate_tos_text_chunk_map_schema_surface()
        validate_tos_retrieval_axis_manifest_schema_surface()
        validate_tos_retrieval_axis_schema_surface()
        validate_reasoning_handoff_pack_manifest_schema_surface()
        validate_reasoning_handoff_pack_schema_surface()
        validate_source_owned_export_dependencies_schema_surface()
        validate_federation_kag_export_schema_surface()
        validate_federation_spine_manifest_schema_surface()
        validate_federation_spine_schema_surface()
        validate_cross_source_node_projection_manifest_schema_surface()
        validate_cross_source_node_projection_schema_surface()
        validate_tiny_consumer_bundle_manifest_schema_surface()
        validate_tiny_consumer_bundle_schema_surface()

        registry_manifest_payload = read_json(REGISTRY_MANIFEST_PATH)
        registry_manifest_surfaces = validate_registry_payload(
            registry_manifest_payload,
            label="registry manifest",
        )
        validate_technique_lift_manifest(registry_manifest_surfaces)
        validate_tos_text_chunk_map_manifest(registry_manifest_surfaces)
        validate_tos_retrieval_axis_manifest(registry_manifest_surfaces)
        validate_reasoning_handoff_manifest()
        source_owned_export_dependencies = (
            validate_source_owned_export_dependency_manifest(
                registry_manifest_surfaces
            )
        )
        validate_federation_spine_manifest(
            registry_manifest_surfaces,
            source_owned_export_dependencies,
        )
        validate_cross_source_node_projection_manifest(
            registry_manifest_surfaces,
            source_owned_export_dependencies,
        )
        validate_tiny_consumer_bundle_manifest(registry_manifest_surfaces)
        validate_counterpart_federation_exposure_review_manifest()

        expected_registry_payload = build_registry_payload()
        expected_technique_lift_pack_payload = build_technique_lift_pack_payload(
            expected_registry_payload
        )
        expected_tos_text_chunk_map_payload = build_tos_text_chunk_map_payload(
            expected_registry_payload
        )
        expected_tos_retrieval_axis_payload = build_tos_retrieval_axis_pack_payload(
            expected_registry_payload
        )
        expected_reasoning_handoff_pack_payload = build_reasoning_handoff_pack_payload()
        expected_federation_spine_payload = build_federation_spine_payload(
            expected_registry_payload
        )
        expected_cross_source_node_projection_payload = (
            build_cross_source_node_projection_payload(expected_registry_payload)
        )
        expected_counterpart_federation_exposure_review_payload = (
            build_counterpart_federation_exposure_review_payload(expected_registry_payload)
        )
        expected_tiny_consumer_bundle_payload = build_tiny_consumer_bundle_payload(
            expected_registry_payload
        )

        validate_generated_text(
            REGISTRY_OUTPUT_PATH,
            encode_json(expected_registry_payload, pretty=True),
            label="generated registry",
        )
        validate_generated_text(
            REGISTRY_MIN_OUTPUT_PATH,
            encode_json(expected_registry_payload, pretty=False),
            label="generated compact registry",
        )
        validate_generated_text(
            TECHNIQUE_LIFT_OUTPUT_PATH,
            encode_json(expected_technique_lift_pack_payload, pretty=True),
            label="generated technique lift pack",
        )
        validate_generated_text(
            TECHNIQUE_LIFT_MIN_OUTPUT_PATH,
            encode_json(expected_technique_lift_pack_payload, pretty=False),
            label="generated compact technique lift pack",
        )
        validate_generated_text(
            TOS_TEXT_CHUNK_MAP_OUTPUT_PATH,
            encode_json(expected_tos_text_chunk_map_payload, pretty=True),
            label="generated ToS text chunk map",
        )
        validate_generated_text(
            TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH,
            encode_json(expected_tos_text_chunk_map_payload, pretty=False),
            label="generated compact ToS text chunk map",
        )
        validate_generated_text(
            TOS_RETRIEVAL_AXIS_OUTPUT_PATH,
            encode_json(expected_tos_retrieval_axis_payload, pretty=True),
            label="generated ToS retrieval axis pack",
        )
        validate_generated_text(
            TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH,
            encode_json(expected_tos_retrieval_axis_payload, pretty=False),
            label="generated compact ToS retrieval axis pack",
        )
        validate_generated_text(
            REASONING_HANDOFF_OUTPUT_PATH,
            encode_json(expected_reasoning_handoff_pack_payload, pretty=True),
            label="generated reasoning handoff pack",
        )
        validate_generated_text(
            REASONING_HANDOFF_MIN_OUTPUT_PATH,
            encode_json(expected_reasoning_handoff_pack_payload, pretty=False),
            label="generated compact reasoning handoff pack",
        )
        validate_generated_text(
            FEDERATION_SPINE_OUTPUT_PATH,
            encode_json(expected_federation_spine_payload, pretty=True),
            label="generated federation spine",
        )
        validate_generated_text(
            FEDERATION_SPINE_MIN_OUTPUT_PATH,
            encode_json(expected_federation_spine_payload, pretty=False),
            label="generated compact federation spine",
        )
        validate_generated_text(
            CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATH,
            encode_json(expected_cross_source_node_projection_payload, pretty=True),
            label="generated cross-source node projection pack",
        )
        validate_generated_text(
            CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH,
            encode_json(expected_cross_source_node_projection_payload, pretty=False),
            label="generated compact cross-source node projection pack",
        )
        validate_generated_text(
            COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATH,
            encode_json(expected_counterpart_federation_exposure_review_payload, pretty=True),
            label="generated counterpart federation exposure review",
        )
        validate_generated_text(
            COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_OUTPUT_PATH,
            encode_json(expected_counterpart_federation_exposure_review_payload, pretty=False),
            label="generated compact counterpart federation exposure review",
        )
        validate_generated_text(
            TINY_CONSUMER_BUNDLE_OUTPUT_PATH,
            encode_json(expected_tiny_consumer_bundle_payload, pretty=True),
            label="generated tiny consumer bundle",
        )
        validate_generated_text(
            TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH,
            encode_json(expected_tiny_consumer_bundle_payload, pretty=False),
            label="generated compact tiny consumer bundle",
        )

        generated_registry_payload = read_json(REGISTRY_MIN_OUTPUT_PATH)
        generated_surfaces_by_id = validate_registry_payload(
            generated_registry_payload,
            label="generated registry",
        )
        validate_technique_lift_pack(
            read_json(TECHNIQUE_LIFT_MIN_OUTPUT_PATH),
            generated_surfaces_by_id,
        )
        validate_tos_text_chunk_map_pack(
            read_json(TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH),
            generated_surfaces_by_id,
            expected_tos_text_chunk_map_payload,
        )
        validate_tos_retrieval_axis_pack(
            read_json(TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH),
            generated_surfaces_by_id,
            expected_tos_retrieval_axis_payload,
        )
        validate_reasoning_handoff_pack(
            read_json(REASONING_HANDOFF_MIN_OUTPUT_PATH),
        )
        validate_federation_spine_pack(
            read_json(FEDERATION_SPINE_MIN_OUTPUT_PATH),
            generated_surfaces_by_id,
            expected_federation_spine_payload,
        )
        validate_cross_source_node_projection_pack(
            read_json(CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH),
            generated_surfaces_by_id,
            expected_cross_source_node_projection_payload,
        )
        validate_counterpart_federation_exposure_review_pack(
            expected_counterpart_federation_exposure_review_payload
        )
        validate_tiny_consumer_bundle_pack(expected_tiny_consumer_bundle_payload)
        validate_bridge_example(generated_surfaces_by_id)
        validate_bridge_envelope_example()
        validate_counterpart_example(generated_surfaces_by_id)
        validate_counterpart_consumer_contract_example(generated_surfaces_by_id)
        validate_tos_text_chunk_map_example(expected_tos_text_chunk_map_payload)
        validate_tos_retrieval_axis_example(expected_tos_retrieval_axis_payload)
        validate_reasoning_handoff_example()
        validate_federation_kag_export_example()
        validate_cross_source_node_projection_example(
            expected_cross_source_node_projection_payload
        )
        validate_counterpart_federation_exposure_review_example(
            expected_counterpart_federation_exposure_review_payload
        )
        validate_tiny_consumer_bundle_example(expected_tiny_consumer_bundle_payload)
    except ValidationError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print("[ok] validated KAG registry schema surface")
    print("[ok] validated bridge retrieval surface schema")
    print("[ok] validated bridge envelope schema")
    print("[ok] validated counterpart edge surface schema")
    print("[ok] validated counterpart federation exposure review manifest schema")
    print("[ok] validated counterpart federation exposure review schema")
    print("[ok] validated counterpart consumer contract schema")
    print("[ok] validated reasoning handoff guardrail schema")
    print("[ok] validated technique lift manifest schema")
    print("[ok] validated technique lift pack schema")
    print("[ok] validated ToS text chunk map manifest schema")
    print("[ok] validated ToS text chunk map schema")
    print("[ok] validated ToS retrieval axis manifest schema")
    print("[ok] validated ToS retrieval axis pack schema")
    print("[ok] validated reasoning handoff pack manifest schema")
    print("[ok] validated reasoning handoff pack schema")
    print("[ok] validated source-owned export dependency manifest schema")
    print("[ok] validated federation KAG export schema")
    print("[ok] validated federation spine manifest schema")
    print("[ok] validated federation spine schema")
    print("[ok] validated cross-source node projection manifest schema")
    print("[ok] validated cross-source node projection schema")
    print("[ok] validated tiny consumer bundle manifest schema")
    print("[ok] validated tiny consumer bundle schema")
    print("[ok] validated manifests/kag_registry.json")
    print("[ok] validated manifests/technique_lift_pack.json")
    print("[ok] validated manifests/tos_text_chunk_map.json")
    print("[ok] validated manifests/tos_retrieval_axis_pack.json")
    print("[ok] validated manifests/reasoning_handoff_pack.json")
    print("[ok] validated manifests/source_owned_export_dependencies.json")
    print("[ok] validated manifests/federation_spine.json")
    print("[ok] validated manifests/cross_source_node_projection.json")
    print("[ok] validated manifests/counterpart_federation_exposure_review.json")
    print("[ok] validated manifests/tiny_consumer_bundle.json")
    print("[ok] validated generated registry outputs are up to date")
    print("[ok] validated generated technique lift pack outputs are up to date")
    print("[ok] validated generated ToS text chunk map outputs are up to date")
    print("[ok] validated generated ToS retrieval axis pack outputs are up to date")
    print("[ok] validated generated reasoning handoff pack outputs are up to date")
    print("[ok] validated generated federation spine outputs are up to date")
    print("[ok] validated generated cross-source node projection outputs are up to date")
    print("[ok] validated generated counterpart federation exposure review outputs are up to date")
    print("[ok] validated generated tiny consumer bundle outputs are up to date")
    print("[ok] validated generated technique lift pack structure")
    print("[ok] validated generated ToS text chunk map structure")
    print("[ok] validated generated ToS retrieval axis pack structure")
    print("[ok] validated generated reasoning handoff pack structure")
    print("[ok] validated generated federation spine structure")
    print("[ok] validated generated cross-source node projection structure")
    print("[ok] validated generated counterpart federation exposure review structure")
    print("[ok] validated generated tiny consumer bundle structure")
    print("[ok] validated bridge retrieval example")
    print("[ok] validated bridge envelope example")
    print("[ok] validated counterpart edge example")
    print("[ok] validated counterpart consumer contract example")
    print("[ok] validated ToS text chunk map example")
    print("[ok] validated ToS retrieval axis example")
    print("[ok] validated reasoning handoff guardrail example")
    print("[ok] validated federation KAG export example")
    print("[ok] validated cross-source node projection example")
    print("[ok] validated counterpart federation exposure review example")
    print("[ok] validated tiny consumer bundle example")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
