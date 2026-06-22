from __future__ import annotations

try:  # Supports package imports and direct `python scripts/validate_kag.py`.
    from scripts import kag_generation as _kag_generation
    from scripts import validate_mechanics_skeleton, validate_nested_agents
except ImportError:  # pragma: no cover - exercised by direct script execution
    import kag_generation as _kag_generation
    import validate_mechanics_skeleton
    import validate_nested_agents


def _is_generation_export(name: str) -> bool:
    return (
        name.isupper()
        or name.startswith("build_")
        or name in {"encode_json", "repo_ref"}
    )


__all__ = [
    "validate_mechanics_skeleton",
    "validate_nested_agents",
    *sorted(name for name in dir(_kag_generation) if _is_generation_export(name)),
]

globals().update(
    {
        name: getattr(_kag_generation, name)
        for name in __all__
        if hasattr(_kag_generation, name)
    }
)
