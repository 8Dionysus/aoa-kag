from __future__ import annotations

from .common import *
from .schema_surfaces import validate_top_level_schema

EXPECTED_DIRECT_REPOS = {
    "8Dionysus",
    "ATM10-Agent",
    "Agents-of-Abyss",
    "Dionysus",
    "Tree-of-Sophia",
    "aoa-agents",
    "aoa-evals",
    "aoa-kag",
    "aoa-memo",
    "aoa-playbooks",
    "aoa-routing",
    "aoa-sdk",
    "aoa-skills",
    "aoa-stats",
    "aoa-techniques",
}

OS_ABYSS_ROOT = Path(os.environ.get("OS_ABYSS_ROOT", "/srv/AbyssOS"))
HOME_SRC_ROOT = Path(os.environ.get("AOA_HOME_SRC_ROOT", "/home/dionysus/src"))
STRICT_OS_SURFACE_ROOTS = os.environ.get("CI") != "true"

EXPECTED_OS_SURFACE_ROOTS = {
    ".agents": OS_ABYSS_ROOT / ".agents",
    ".aoa": OS_ABYSS_ROOT / ".aoa",
    ".codex": OS_ABYSS_ROOT / ".codex",
    "abyss-stack-runtime-mirror": OS_ABYSS_ROOT / "abyss-stack",
    "bundles": OS_ABYSS_ROOT / "bundles",
    "bundles/aoa-session-memory": OS_ABYSS_ROOT / "bundles" / "aoa-session-memory",
    "connectors": OS_ABYSS_ROOT / "connectors",
    "connectors/aoa-4pda-connector": OS_ABYSS_ROOT / "connectors" / "aoa-4pda-connector",
    "connectors/aoa-discord-connector": OS_ABYSS_ROOT / "connectors" / "aoa-discord-connector",
    "connectors/aoa-stackoverflow-connector": OS_ABYSS_ROOT / "connectors" / "aoa-stackoverflow-connector",
    "connectors/aoa-telegram-connector": OS_ABYSS_ROOT / "connectors" / "aoa-telegram-connector",
    "connectors/aoa-xda-connector": OS_ABYSS_ROOT / "connectors" / "aoa-xda-connector",
    "src/abyss-machine": HOME_SRC_ROOT / "abyss-machine",
    "src/abyss-stack": HOME_SRC_ROOT / "abyss-stack",
}

EXPECTED_OS_SURFACE_CLASSES = {
    ".agents": "organ_home",
    ".aoa": "organ_home",
    ".codex": "organ_home",
    "abyss-stack-runtime-mirror": "runtime_mirror",
    "bundles": "collection_home",
    "bundles/aoa-session-memory": "bundle_repo",
    "connectors": "collection_home",
    "connectors/aoa-4pda-connector": "connector_repo",
    "connectors/aoa-discord-connector": "connector_repo",
    "connectors/aoa-stackoverflow-connector": "connector_repo",
    "connectors/aoa-telegram-connector": "connector_repo",
    "connectors/aoa-xda-connector": "connector_repo",
    "src/abyss-machine": "runtime_source_repo",
    "src/abyss-stack": "runtime_source_repo",
}

REQUIRED_RECORD_CLASSES = {"node", "edge", "index", "projection", "receipt"}
REQUIRED_MCP_SHAPE = {"resource", "root"}
EXPECTED_PROVIDER_READY_REPOS = {
    "8Dionysus",
    "ATM10-Agent",
    "Agents-of-Abyss",
    "Dionysus",
    "Tree-of-Sophia",
    "aoa-agents",
    "aoa-evals",
    "aoa-kag",
    "aoa-memo",
    "aoa-playbooks",
    "aoa-routing",
    "aoa-sdk",
    "aoa-skills",
    "aoa-stats",
    "aoa-techniques",
}

PROVIDER_RECORD_DIRS = {
    "nodes": "nodeRecord",
    "edges": "edgeRecord",
    "indexes": "indexRecord",
    "projections": "projectionRecord",
    "receipts": "receiptRecord",
}

PROVIDER_REPO_ROOTS = {
    repo: KNOWN_REPO_ROOTS[repo]
    for repo in EXPECTED_PROVIDER_READY_REPOS
}

AUTHORITY_PHRASES = (
    "source truth",
    "proof verdict",
    "memory acceptance",
    "routing authority",
    "canon authorship",
    "semantic sovereignty",
)

RUNTIME_STORAGE_PHRASES = (
    "live graph database",
    "vector database",
    "embedding cache",
    "runtime search index",
)


def _validate_payload_against_local_kag_schema(payload: object, *, label: str) -> None:
    schema = read_json(LOCAL_KAG_SUBTREE_SCHEMA_PATH)
    if not isinstance(schema, dict):
        fail("local KAG subtree schema must be a JSON object")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        path = format_schema_path(first.path)
        suffix = f" at {path}" if path else ""
        fail(f"{label} does not match local KAG subtree schema{suffix}: {first.message}")


def _validate_payload_against_schema_def(payload: object, *, def_name: str, label: str) -> None:
    schema = read_json(LOCAL_KAG_SUBTREE_SCHEMA_PATH)
    if not isinstance(schema, dict):
        fail("local KAG subtree schema must be a JSON object")
    wrapper = {
        "$schema": schema.get("$schema"),
        "$id": f"{schema.get('$id', 'local-kag-subtree')}.{def_name}.validator.json",
        "$defs": schema.get("$defs", {}),
        "$ref": f"#/$defs/{def_name}",
    }
    Draft202012Validator.check_schema(wrapper)
    errors = sorted(Draft202012Validator(wrapper).iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        path = format_schema_path(first.path)
        suffix = f" at {path}" if path else ""
        fail(f"{label} does not match local KAG {def_name}{suffix}: {first.message}")


def _strings_in(value: object):
    yield from iter_string_values(value)


def _validate_language_posture(payload: object, *, label: str) -> None:
    lowered = [value.lower() for value in _strings_in(payload)]
    for phrase in AUTHORITY_PHRASES:
        if any(phrase in value for value in lowered):
            fail(f"{label} carries authority posture phrase '{phrase}'")
    for phrase in RUNTIME_STORAGE_PHRASES:
        if any(phrase in value for value in lowered):
            fail(f"{label} carries runtime storage phrase '{phrase}'")


def _record_groups(packet: dict[str, object]) -> dict[str, list[dict[str, object]]]:
    records = packet.get("records")
    if not isinstance(records, dict):
        fail("local KAG example records must be an object")
    groups: dict[str, list[dict[str, object]]] = {}
    for group_name in ("nodes", "edges", "indexes", "projections", "receipts"):
        group = records.get(group_name)
        if not isinstance(group, list) or not group:
            fail(f"local KAG example records.{group_name} must be a non-empty list")
        normalized: list[dict[str, object]] = []
        for index, item in enumerate(group):
            if not isinstance(item, dict):
                fail(f"local KAG example records.{group_name}[{index}] must be an object")
            normalized.append(item)
        groups[group_name] = normalized
    return groups


def _validate_record_links(packet: dict[str, object]) -> None:
    groups = _record_groups(packet)
    all_records = [record for group in groups.values() for record in group]
    ids = [record.get("local_id") for record in all_records]
    if not all(isinstance(record_id, str) and record_id for record_id in ids):
        fail("local KAG example records must keep local_id strings")
    if len(ids) != len(set(ids)):
        fail("local KAG example record local_id values must be unique")
    id_set = {str(record_id) for record_id in ids}

    classes = {record.get("record_class") for record in all_records}
    if classes != REQUIRED_RECORD_CLASSES:
        fail("local KAG example must cover node, edge, index, projection, and receipt records")

    node_ids = {str(record["local_id"]) for record in groups["nodes"]}
    for edge in groups["edges"]:
        for key in ("from_id", "to_id"):
            if edge.get(key) not in node_ids:
                fail(f"local KAG edge {edge.get('local_id')} {key} must point to a local node")
        if not edge.get("edge_trace"):
            fail(f"local KAG edge {edge.get('local_id')} must keep edge_trace")

    for group_name in ("indexes", "projections"):
        for record in groups[group_name]:
            source_ids = record.get("source_record_ids")
            if not isinstance(source_ids, list) or not source_ids:
                fail(f"local KAG {group_name} record {record.get('local_id')} must keep source_record_ids")
            missing = sorted(str(record_id) for record_id in source_ids if record_id not in id_set)
            if missing:
                fail(f"local KAG {group_name} record {record.get('local_id')} references unknown records: {', '.join(missing)}")

    for receipt in groups["receipts"]:
        if not receipt.get("fallback_route"):
            fail(f"local KAG receipt {receipt.get('local_id')} must keep fallback_route")


def _validate_registry_entries(packet: dict[str, object]) -> None:
    entries = packet.get("registry_entries")
    if not isinstance(entries, list) or not entries:
        fail("local KAG example must keep registry_entries")
    for entry in entries:
        if not isinstance(entry, dict):
            fail("local KAG registry entry must be an object")
        if entry.get("provider_status") == "provider_ready":
            coverage = set(entry.get("record_class_coverage", []))
            if coverage != REQUIRED_RECORD_CLASSES:
                fail(f"provider-ready entry {entry.get('repo')} must cover every local KAG record class")
        access_shape = set(entry.get("mcp_access_shape", []))
        if not REQUIRED_MCP_SHAPE <= access_shape:
            fail(f"registry entry {entry.get('repo')} must expose resource and root MCP shapes")


def _validate_readiness_matrix(payload: dict[str, object]) -> None:
    repos = payload.get("repos")
    if not isinstance(repos, list):
        fail("local KAG readiness matrix repos must be a list")
    repo_names = [entry.get("repo") for entry in repos if isinstance(entry, dict)]
    if set(repo_names) != EXPECTED_DIRECT_REPOS:
        fail("local KAG readiness matrix must cover every direct OS Abyss repo")
    if len(repo_names) != len(set(repo_names)):
        fail("local KAG readiness matrix must keep one row per repo")

    adoption_order = [entry.get("adoption_order") for entry in repos if isinstance(entry, dict)]
    if len(adoption_order) != len(set(adoption_order)):
        fail("local KAG readiness matrix adoption_order values must be unique")

    ready_repos: set[str] = set()
    for entry in repos:
        if not isinstance(entry, dict):
            fail("local KAG readiness matrix repo entries must be objects")
        repo = entry["repo"]
        if entry["provider_status"] == "provider_ready":
            ready_repos.add(str(repo))
            if set(entry.get("first_record_classes", [])) != REQUIRED_RECORD_CLASSES:
                fail(f"provider-ready repo {repo} must name every first record class")
            if not REQUIRED_MCP_SHAPE <= set(entry.get("mcp_access_shape", [])):
                fail(f"provider-ready repo {repo} must expose resource and root MCP shapes")
        if not entry.get("candidate_source_surfaces"):
            fail(f"local KAG readiness row {repo} must keep candidate_source_surfaces")
        if not entry.get("owner_return_routes"):
            fail(f"local KAG readiness row {repo} must keep owner_return_routes")

    if not EXPECTED_PROVIDER_READY_REPOS <= ready_repos:
        missing = sorted(EXPECTED_PROVIDER_READY_REPOS - ready_repos)
        fail(
            "local KAG readiness matrix must include every current source-ready "
            f"provider repo as provider-ready: {', '.join(missing)}"
        )

    _validate_os_surfaces(payload)


def _validate_surface_path(root: Path, relative_path: str, *, label: str) -> None:
    if not isinstance(relative_path, str) or not relative_path:
        fail(f"{label} must be a path string")
    normalized = relative_path.rstrip("/")
    target = root / normalized
    if relative_path.endswith("/"):
        if not target.is_dir():
            fail(f"{label} must point to an existing directory: {relative_path}")
        return
    if not target.exists():
        fail(f"{label} must point to an existing surface: {relative_path}")


def _validate_os_surfaces(payload: dict[str, object]) -> None:
    surfaces = payload.get("os_surfaces")
    if not isinstance(surfaces, list):
        fail("local KAG readiness matrix os_surfaces must be a list")
    surface_ids = [entry.get("surface_id") for entry in surfaces if isinstance(entry, dict)]
    if set(surface_ids) != set(EXPECTED_OS_SURFACE_ROOTS):
        fail("local KAG readiness matrix must cover every OS surface class")
    if len(surface_ids) != len(set(surface_ids)):
        fail("local KAG readiness matrix must keep one row per OS surface")

    adoption_order = [entry.get("adoption_order") for entry in surfaces if isinstance(entry, dict)]
    if len(adoption_order) != len(set(adoption_order)):
        fail("local KAG readiness matrix OS surface adoption_order values must be unique")

    connector_rows = 0
    for entry in surfaces:
        if not isinstance(entry, dict):
            fail("local KAG readiness matrix OS surface entries must be objects")
        surface_id = str(entry.get("surface_id"))
        expected_root = EXPECTED_OS_SURFACE_ROOTS[surface_id]
        expected_class = EXPECTED_OS_SURFACE_CLASSES[surface_id]
        if entry.get("surface_class") != expected_class:
            fail(f"OS surface {surface_id} must keep surface_class {expected_class}")
        if entry.get("root") != expected_root.as_posix():
            fail(f"OS surface {surface_id} must keep root {expected_root.as_posix()}")
        root_available = expected_root.is_dir()
        if STRICT_OS_SURFACE_ROOTS and not root_available:
            fail(f"OS surface {surface_id} root must exist: {expected_root.as_posix()}")

        if expected_class == "connector_repo":
            connector_rows += 1
        if not entry.get("candidate_source_surfaces"):
            fail(f"OS surface {surface_id} must keep candidate_source_surfaces")
        if not entry.get("owner_return_route"):
            fail(f"OS surface {surface_id} must keep owner_return_route")
        if not REQUIRED_MCP_SHAPE <= set(entry.get("mcp_access_shape", [])):
            fail(f"OS surface {surface_id} must expose resource and root MCP shapes")

        if not root_available:
            continue
        for key in ("source_home_surfaces", "source_owned_exports", "candidate_source_surfaces", "document_surfaces", "event_surfaces"):
            values = entry.get(key)
            if not isinstance(values, list):
                fail(f"OS surface {surface_id} {key} must be a list")
            for relative_path in values:
                _validate_surface_path(expected_root, relative_path, label=f"OS surface {surface_id} {key}")

    if connector_rows != 5:
        fail("local KAG readiness matrix must cover every connector repo")


def _validate_source_refs_exist(repo: str, repo_root: Path, payload: object, *, label: str) -> None:
    for source_ref in _source_refs_in(payload):
        source_repo = source_ref.get("repo")
        source_path = source_ref.get("path")
        if source_repo != repo:
            fail(f"{label} source ref must stay inside provider repo {repo}")
        if not isinstance(source_path, str) or not source_path:
            fail(f"{label} source ref must keep a path")
        if not (repo_root / source_path).is_file():
            fail(f"{label} source ref is missing: {repo}/{source_path}")


def _source_refs_in(payload: object):
    if isinstance(payload, dict):
        maybe_refs = payload.get("source_refs")
        if isinstance(maybe_refs, list):
            for item in maybe_refs:
                if isinstance(item, dict):
                    yield item
        maybe_surfaces = payload.get("source_surfaces")
        if isinstance(maybe_surfaces, list):
            for item in maybe_surfaces:
                if isinstance(item, dict):
                    yield item
        for value in payload.values():
            yield from _source_refs_in(value)
        return
    if isinstance(payload, list):
        for item in payload:
            yield from _source_refs_in(item)


def _validate_provider_home(repo: str, repo_root: Path) -> None:
    kag_root = repo_root / "kag"
    label = f"{repo} local KAG provider"
    for filename in ("AGENTS.md", "README.md", "manifest.json"):
        if not (kag_root / filename).is_file():
            fail(f"{label} must keep kag/{filename}")

    manifest = read_json(kag_root / "manifest.json")
    _validate_payload_against_schema_def(manifest, def_name="localManifest", label=f"{label} manifest")
    if not isinstance(manifest, dict):
        fail(f"{label} manifest must be an object")
    if manifest.get("repo") != repo:
        fail(f"{label} manifest repo must be {repo}")
    if set(manifest.get("record_classes", [])) != REQUIRED_RECORD_CLASSES:
        fail(f"{label} manifest must name every local KAG record class")
    _validate_source_refs_exist(repo, repo_root, manifest, label=f"{label} manifest")

    groups: dict[str, list[dict[str, object]]] = {}
    for group_name, def_name in PROVIDER_RECORD_DIRS.items():
        directory = kag_root / group_name
        if not directory.is_dir():
            fail(f"{label} must keep kag/{group_name}/")
        files = sorted(directory.glob("*.json"))
        if not files:
            fail(f"{label} kag/{group_name}/ must contain JSON records")
        records: list[dict[str, object]] = []
        for path in files:
            record = read_json(path)
            _validate_payload_against_schema_def(
                record,
                def_name=def_name,
                label=f"{label} {path.relative_to(repo_root).as_posix()}",
            )
            if not isinstance(record, dict):
                fail(f"{label} {path.relative_to(repo_root).as_posix()} must be an object")
            _validate_source_refs_exist(
                repo,
                repo_root,
                record,
                label=f"{label} {path.relative_to(repo_root).as_posix()}",
            )
            records.append(record)
        groups[group_name] = records

    _validate_record_links({"records": groups})


def _validate_provider_ready_surfaces(readiness: dict[str, object]) -> None:
    repos = readiness.get("repos")
    if not isinstance(repos, list):
        fail("local KAG readiness matrix repos must be a list")
    for entry in repos:
        if not isinstance(entry, dict) or entry.get("provider_status") != "provider_ready":
            continue
        repo = str(entry.get("repo"))
        repo_root = PROVIDER_REPO_ROOTS.get(repo, REPO_ROOT.parent / repo)
        if repo == KAG_REPO or repo_root.exists():
            _validate_provider_home(repo, repo_root)


def validate_local_kag_subtree_contract() -> None:
    validate_top_level_schema(LOCAL_KAG_SUBTREE_SCHEMA_PATH, "local KAG subtree")

    example = read_json(LOCAL_KAG_SUBTREE_EXAMPLE_PATH)
    readiness = read_json(LOCAL_KAG_READINESS_MANIFEST_PATH)
    for label, payload in (
        ("local KAG subtree example", example),
        ("local KAG readiness matrix", readiness),
    ):
        if not isinstance(payload, dict):
            fail(f"{label} must be a JSON object")
        _validate_payload_against_local_kag_schema(payload, label=label)
        _validate_language_posture(payload, label=label)

    assert isinstance(example, dict)
    assert isinstance(readiness, dict)
    _validate_record_links(example)
    _validate_registry_entries(example)
    _validate_readiness_matrix(readiness)
    _validate_provider_ready_surfaces(readiness)
