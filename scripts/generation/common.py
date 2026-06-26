from __future__ import annotations

from .context import *

def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing required file: {path.as_posix()}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.as_posix()}: {exc}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.as_posix()}")


def encode_json(payload: object, *, pretty: bool) -> str:
    if pretty:
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n"


def write_json(path: Path, payload: object, *, pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encode_json(payload, pretty=pretty), encoding="utf-8")


def ordered_unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def repo_ref(repo: str, path: str) -> str:
    clean_path = path.lstrip("/")
    if repo == "aoa-kag":
        return clean_path
    return f"{repo}/{clean_path}"


def resolve_repo_path(repo: str, path: str) -> Path:
    root = KNOWN_REPO_ROOTS.get(repo)
    if root is None:
        fail(f"unsupported repository '{repo}'")
    target = root / path
    if target.exists():
        return target
    for alias in COMPATIBILITY_REF_ALIASES.get(repo, {}).get(path, ()):
        alias_target = root / alias
        if alias_target.exists():
            return alias_target
    return target


def path_matches_current_or_alias(repo: str, current_path: str, observed_path: object) -> bool:
    if observed_path == current_path:
        return True
    return observed_path in COMPATIBILITY_REF_ALIASES.get(repo, {}).get(current_path, ())


def canonical_repo_path(repo: str, path: str) -> str:
    if path in COMPATIBILITY_REF_ALIASES.get(repo, {}):
        return path
    for current_path, aliases in COMPATIBILITY_REF_ALIASES.get(repo, {}).items():
        if path in aliases:
            return current_path
    return path


def manifest_input_path(source_input: dict[str, str]) -> Path:
    return resolve_repo_path(source_input["repo"], source_input["path"])


def manifest_input_ref(source_input: dict[str, str]) -> str:
    return repo_ref(source_input["repo"], source_input["path"])


def load_eval_paths_by_name() -> dict[str, str]:
    if not EVAL_CATALOG_PATH.exists():
        return {}
    payload = read_json(EVAL_CATALOG_PATH)
    if not isinstance(payload, dict):
        fail("aoa-evals generated eval catalog must be a JSON object")
    evals = payload.get("evals")
    if not isinstance(evals, list):
        fail("aoa-evals generated eval catalog must declare evals")
    paths_by_name: dict[str, str] = {}
    for index, entry in enumerate(evals):
        if not isinstance(entry, dict):
            fail(f"aoa-evals generated eval catalog evals[{index}] must be an object")
        name = entry.get("name")
        if not isinstance(name, str):
            fail(f"aoa-evals generated eval catalog evals[{index}] must keep name and eval_path")
        eval_path = ensure_repo_relative_path(
            entry.get("eval_path"),
            label=f"aoa-evals generated eval catalog evals[{index}].eval_path",
        )
        paths_by_name[name] = eval_path
    return paths_by_name


def eval_path_for_anchor(eval_anchor: str) -> str:
    catalog_path = load_eval_paths_by_name().get(eval_anchor)
    if catalog_path is not None:
        eval_path = resolve_repo_path("aoa-evals", catalog_path)
        if eval_path.exists():
            return canonical_repo_path("aoa-evals", catalog_path)

    legacy_path = Path("bundles") / eval_anchor / "EVAL.md"
    legacy_path_text = legacy_path.as_posix()
    for current_path, aliases in COMPATIBILITY_REF_ALIASES.get("aoa-evals", {}).items():
        if legacy_path_text in aliases and (AOA_EVALS_ROOT / legacy_path).exists():
            return current_path
    if (AOA_EVALS_ROOT / legacy_path).exists():
        return legacy_path_text
    fail(f"missing eval bundle for anchor '{eval_anchor}'")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        fail(f"missing required file: {path.as_posix()}")


def require_string_list(value: object, *, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        fail(f"{label} must be a non-empty list")
    normalized: list[str] = []
    for index, item in enumerate(value):
        normalized.append(require_string(item, label=f"{label}[{index}]"))
    return normalized


def require_string(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string")
    return value


def require_optional_string(value: object, *, label: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        fail(f"{label} must be a string when present")
    return value


def ensure_repo_relative_path(raw_path: object, *, label: str) -> str:
    value = require_string(raw_path, label=label).replace("\\", "/")
    if re.match(r"^[A-Za-z]:[/\\\\]", value) or value.startswith(("/", "\\")):
        fail(f"{label} must be repo-relative")
    if ".." in Path(value).parts:
        fail(f"{label} must not traverse outside the repository root")
    return value


def ensure_tos_relative_surface_path(raw_path: object, *, label: str) -> str:
    relative_path = ensure_repo_relative_path(raw_path, label=label)
    if ":" in relative_path:
        fail(f"{label} must stay Tree-of-Sophia-relative and must not use repo-qualified refs")
    if relative_path.startswith(("aoa-kag/", "aoa-routing/")):
        fail(f"{label} must stay inside Tree-of-Sophia and must not point at downstream repos")
    if not (TREE_OF_SOPHIA_ROOT / relative_path).exists():
        fail(f"{label} target is missing inside Tree-of-Sophia: {relative_path}")
    return relative_path


def ensure_local_ref_exists(
    raw_ref: object,
    *,
    label: str,
    allow_missing_refs: set[str] | None = None,
) -> str:
    relative_ref = ensure_repo_relative_path(raw_ref, label=label)
    target = REPO_ROOT / relative_ref
    if not target.exists() and (
        allow_missing_refs is None or relative_ref not in allow_missing_refs
    ):
        fail(f"{label} target is missing: {relative_ref}")
    return relative_ref
