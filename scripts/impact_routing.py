#!/usr/bin/env python3
"""Fail-closed KAG CI impact routing and required-summary evaluation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Sequence

try:  # Supports direct script execution and package-style imports.
    from scripts import validation_lanes
except ImportError:  # pragma: no cover - exercised by direct script execution
    import validation_lanes  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[1]
PULL_REQUEST_EVENT = "pull_request"
FULL_AUDIT_ROUTE = "full-audit"
OWNER_LOCAL_ROUTE = "owner-local"
JOB_RESULTS = {"success", "failure", "cancelled", "skipped"}


@dataclass(frozen=True)
class PathImpact:
    path: str
    route: str
    rule_id: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "route": self.route,
            "rule_id": self.rule_id,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ImpactClassification:
    route: str
    changed_paths: tuple[str, ...]
    path_impacts: tuple[PathImpact, ...]
    reason_ids: tuple[str, ...]
    reasons: tuple[str, ...]
    diagnostic: str = ""

    @property
    def full_audit_required(self) -> bool:
        return self.route == FULL_AUDIT_ROUTE

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "aoa-kag-impact-classification-v1",
            "route": self.route,
            "changed_paths": list(self.changed_paths),
            "path_impacts": [impact.as_dict() for impact in self.path_impacts],
            "reason_ids": list(self.reason_ids),
            "reasons": list(self.reasons),
            "always_required_proofs": list(
                validation_lanes.IMPACT_ROUTING["always_required_proofs"]
            ),
            "source_fast_required": True,
            "owner_family_required": True,
            "full_audit_required": self.full_audit_required,
            "os_wide_audit_disposition": (
                "required" if self.full_audit_required else "not-required"
            ),
            "diagnostic": self.diagnostic,
        }


@dataclass(frozen=True)
class LandingSummary:
    event_name: str
    source_fast_result: str
    full_audit_result: str
    full_audit_required: bool
    source_fast_status: str
    owner_family_status: str
    full_audit_status: str
    verdict: str
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "aoa-kag-impact-summary-v1",
            "event_name": self.event_name,
            "source_fast_result": self.source_fast_result,
            "full_audit_result": self.full_audit_result,
            "full_audit_required": self.full_audit_required,
            "source_fast_status": self.source_fast_status,
            "owner_family_status": self.owner_family_status,
            "full_audit_status": self.full_audit_status,
            "verdict": self.verdict,
            "errors": list(self.errors),
        }


def _normalized_path(value: str) -> str:
    if not value or "\0" in value:
        raise ValueError("impact path must be a non-empty repository-relative path")
    normalized = value.removeprefix("./")
    path = PurePosixPath(normalized)
    if path.is_absolute() or normalized in {"", "."} or ".." in path.parts:
        raise ValueError(f"impact path must be repository-relative: {value!r}")
    return path.as_posix()


def _rule_matches(path: str, rule: dict[str, Any]) -> bool:
    if path in rule["exact_paths"]:
        return True
    if any(path.startswith(prefix) for prefix in rule["prefixes"]):
        return True
    parts = set(PurePosixPath(path).parts)
    if any(segment in parts for segment in rule["segments"]):
        return True
    return any(path.endswith(suffix) for suffix in rule["suffixes"])


def _impact_for_path(path: str) -> PathImpact:
    routing = validation_lanes.IMPACT_ROUTING
    for rule in routing["full_audit_rules"]:
        if _rule_matches(path, rule):
            return PathImpact(
                path=path,
                route=FULL_AUDIT_ROUTE,
                rule_id=rule["id"],
                reason=rule["reason"],
            )
    for rule in routing["owner_local_rules"]:
        if _rule_matches(path, rule):
            return PathImpact(
                path=path,
                route=OWNER_LOCAL_ROUTE,
                rule_id=rule["id"],
                reason=rule["reason"],
            )
    return PathImpact(
        path=path,
        route=FULL_AUDIT_ROUTE,
        rule_id=routing["default_reason"],
        reason="path is not covered by an owner-local allow rule",
    )


def _ordered_unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def forced_full_classification(reason_id: str, reason: str, *, diagnostic: str = "") -> ImpactClassification:
    return ImpactClassification(
        route=FULL_AUDIT_ROUTE,
        changed_paths=(),
        path_impacts=(),
        reason_ids=(reason_id,),
        reasons=(reason,),
        diagnostic=diagnostic,
    )


def classify_changed_paths(changed_paths: Iterable[str]) -> ImpactClassification:
    normalized_paths: set[str] = set()
    invalid_impacts: list[PathImpact] = []
    for raw_path in changed_paths:
        try:
            normalized_paths.add(_normalized_path(raw_path))
        except ValueError as exc:
            invalid_impacts.append(
                PathImpact(
                    path=raw_path,
                    route=FULL_AUDIT_ROUTE,
                    rule_id="invalid-path",
                    reason=str(exc),
                )
            )
    if not normalized_paths and not invalid_impacts:
        return forced_full_classification(
            "empty-change-set",
            "no changed path could be proven",
        )

    impacts = tuple(
        [
            *sorted(invalid_impacts, key=lambda impact: impact.path),
            *(_impact_for_path(path) for path in sorted(normalized_paths)),
        ]
    )
    full_impacts = tuple(
        impact for impact in impacts if impact.route == FULL_AUDIT_ROUTE
    )
    decisive = full_impacts or impacts
    return ImpactClassification(
        route=FULL_AUDIT_ROUTE if full_impacts else OWNER_LOCAL_ROUTE,
        changed_paths=tuple(impact.path for impact in impacts),
        path_impacts=impacts,
        reason_ids=_ordered_unique(impact.rule_id for impact in decisive),
        reasons=_ordered_unique(impact.reason for impact in decisive),
    )


def _resolved_commit(repo_root: Path, ref: str) -> str:
    if not ref or ref.startswith("-"):
        raise ValueError(f"unsafe or empty Git ref: {ref!r}")
    result = subprocess.run(
        ("git", "rev-parse", "--verify", f"{ref}^{{commit}}"),
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def git_changed_paths(repo_root: Path, base_ref: str, head_ref: str) -> tuple[str, ...]:
    base_commit = _resolved_commit(repo_root, base_ref)
    head_commit = _resolved_commit(repo_root, head_ref)
    merge_base = subprocess.run(
        ("git", "merge-base", base_commit, head_commit),
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    result = subprocess.run(
        (
            "git",
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            merge_base,
            head_commit,
            "--",
        ),
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    return tuple(
        path.decode("utf-8", errors="surrogateescape")
        for path in result.stdout.split(b"\0")
        if path
    )


def classify_event(
    *,
    event_name: str,
    repo_root: Path,
    base_ref: str,
    head_ref: str,
    explicit_paths: Sequence[str],
) -> ImpactClassification:
    if event_name != PULL_REQUEST_EVENT:
        return forced_full_classification(
            "non-pull-request-event",
            "main, scheduled, and manual events require the full OS-wide audit",
        )

    paths = list(explicit_paths)
    if base_ref:
        try:
            paths.extend(git_changed_paths(repo_root, base_ref, head_ref))
        except (OSError, ValueError, subprocess.CalledProcessError) as exc:
            return forced_full_classification(
                "unprovable-change-set",
                "Git change identity could not be proven; full audit is required",
                diagnostic=str(exc),
            )
    if not paths:
        return forced_full_classification(
            "missing-change-set",
            "pull request paths or a base ref were not supplied",
        )
    return classify_changed_paths(paths)


def evaluate_landing_summary(
    *,
    event_name: str,
    source_fast_result: str,
    full_audit_result: str,
    full_audit_required: bool,
) -> LandingSummary:
    errors: list[str] = []
    if source_fast_result not in JOB_RESULTS:
        errors.append(f"invalid source-fast job result: {source_fast_result!r}")
    if full_audit_result not in JOB_RESULTS:
        errors.append(f"invalid full-audit job result: {full_audit_result!r}")

    local_verified = source_fast_result == "success"
    source_fast_status = "verified" if local_verified else f"failed:{source_fast_result}"
    owner_family_status = "verified" if local_verified else f"failed:{source_fast_result}"
    if not local_verified:
        errors.append(f"source-fast and owner-family proof did not succeed: {source_fast_result}")

    if event_name != PULL_REQUEST_EVENT and not full_audit_required:
        errors.append("non-pull-request event was not routed to the full audit")

    if full_audit_required:
        if full_audit_result == "success":
            full_audit_status = "verified"
        else:
            full_audit_status = f"failed:{full_audit_result}"
            errors.append(f"required full audit did not succeed: {full_audit_result}")
    elif full_audit_result == "skipped":
        full_audit_status = "correctly-not-required"
    else:
        full_audit_status = f"unexpected:{full_audit_result}"
        errors.append(
            "full audit ran or failed even though the classifier marked it not required: "
            f"{full_audit_result}"
        )

    return LandingSummary(
        event_name=event_name,
        source_fast_result=source_fast_result,
        full_audit_result=full_audit_result,
        full_audit_required=full_audit_required,
        source_fast_status=source_fast_status,
        owner_family_status=owner_family_status,
        full_audit_status=full_audit_status,
        verdict="passed" if not errors else "failed",
        errors=tuple(errors),
    )


def _write_github_output(path: Path, classification: ImpactClassification) -> None:
    lines = (
        f"route={classification.route}\n",
        f"full-audit-required={'true' if classification.full_audit_required else 'false'}\n",
        f"reason-ids={','.join(classification.reason_ids)}\n",
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.writelines(lines)


def _write_step_summary(path: Path, summary: LandingSummary) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write("## KAG validation impact summary\n\n")
        handle.write(f"- source-fast: {summary.source_fast_status}\n")
        handle.write(f"- owner-family: {summary.owner_family_status}\n")
        handle.write(f"- full OS-wide audit: {summary.full_audit_status}\n")
        handle.write(f"- verdict: {summary.verdict}\n")
        if summary.errors:
            handle.write(f"- errors: {'; '.join(summary.errors)}\n")


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    if not normalized:
        return True
    raise argparse.ArgumentTypeError(f"expected boolean, got {value!r}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    classify = subparsers.add_parser("classify")
    classify.add_argument("--repo-root", default=".")
    classify.add_argument("--event-name", default=PULL_REQUEST_EVENT)
    classify.add_argument("--base-ref", default="")
    classify.add_argument("--head-ref", default="HEAD")
    classify.add_argument("--path", action="append", default=[])
    classify.add_argument("--github-output", type=Path)

    summarize = subparsers.add_parser("summarize")
    summarize.add_argument("--event-name", required=True)
    summarize.add_argument("--source-fast-result", required=True)
    summarize.add_argument("--full-audit-result", required=True)
    summarize.add_argument("--full-audit-required", type=_parse_bool, required=True)
    summarize.add_argument("--github-step-summary", type=Path)

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "classify":
        classification = classify_event(
            event_name=args.event_name,
            repo_root=Path(args.repo_root).resolve(),
            base_ref=args.base_ref,
            head_ref=args.head_ref,
            explicit_paths=args.path,
        )
        print(json.dumps(classification.as_dict(), indent=2, sort_keys=True))
        if args.github_output is not None:
            _write_github_output(args.github_output, classification)
        return 0

    summary = evaluate_landing_summary(
        event_name=args.event_name,
        source_fast_result=args.source_fast_result,
        full_audit_result=args.full_audit_result,
        full_audit_required=args.full_audit_required,
    )
    print(json.dumps(summary.as_dict(), indent=2, sort_keys=True))
    if args.github_step_summary is not None:
        _write_step_summary(args.github_step_summary, summary)
    return 0 if summary.verdict == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
