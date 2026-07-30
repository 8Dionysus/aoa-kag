from __future__ import annotations

import json
import os
import secrets
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator


COVERAGE_PACKET_ENV = "AOA_KAG_COVERAGE_PACKET"
COVERAGE_RECEIPT_ENV = "AOA_KAG_COVERAGE_RECEIPT"
COVERAGE_SCOPE_ACTIVE_ENV = "AOA_KAG_COVERAGE_SCOPE_ACTIVE"
COVERAGE_SCOPE_DIR_ENV = "AOA_KAG_COVERAGE_SCOPE_DIR"
COVERAGE_SCOPE_ID_ENV = "AOA_KAG_COVERAGE_SCOPE_ID"
COVERAGE_SCOPE_LANE_ENV = "AOA_KAG_COVERAGE_SCOPE_LANE"
COVERAGE_SCOPE_MARKER = ".aoa-kag-coverage-scope.json"
COVERAGE_EVENT_SCHEMA_VERSION = "aoa-kag-coverage-run-event-v1"
COVERAGE_RECEIPT_SCHEMA_VERSION = "aoa-kag-coverage-run-receipt-v1"
VALIDATION_ARTIFACT_PARENT_ENV = "AOA_KAG_VALIDATION_ARTIFACT_PARENT"
REPO_ROOT = Path(__file__).resolve().parents[1]

_SCOPE_ENV_NAMES = (
    COVERAGE_PACKET_ENV,
    COVERAGE_RECEIPT_ENV,
    COVERAGE_SCOPE_ACTIVE_ENV,
    COVERAGE_SCOPE_DIR_ENV,
    COVERAGE_SCOPE_ID_ENV,
    COVERAGE_SCOPE_LANE_ENV,
)


@dataclass(frozen=True)
class CoverageRun:
    scope_dir: Path
    packet_path: Path
    receipt_path: Path
    run_scope_id: str
    lane: str


def _scope_marker_path(scope_dir: Path) -> Path:
    return scope_dir / COVERAGE_SCOPE_MARKER


def _read_scope_marker(scope_dir: Path) -> dict[str, Any]:
    marker_path = _scope_marker_path(scope_dir)
    if marker_path.is_symlink() or not marker_path.is_file():
        raise RuntimeError(f"coverage run scope marker is unavailable: {marker_path}")
    try:
        payload = json.loads(marker_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, IsADirectoryError) as exc:
        raise RuntimeError(f"coverage run scope marker is unreadable: {marker_path}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"coverage run scope marker must be an object: {marker_path}")
    if set(payload) != {"run_scope_id", "lane"}:
        raise RuntimeError(f"coverage run scope marker shape is invalid: {marker_path}")
    return payload


def current_coverage_run(*, required: bool = False) -> CoverageRun | None:
    active = os.environ.get(COVERAGE_SCOPE_ACTIVE_ENV) == "1"
    if not active:
        if required:
            raise RuntimeError("coverage run scope is not active")
        return None

    values = {
        name: os.environ.get(name, "").strip()
        for name in (
            COVERAGE_SCOPE_DIR_ENV,
            COVERAGE_PACKET_ENV,
            COVERAGE_RECEIPT_ENV,
            COVERAGE_SCOPE_ID_ENV,
            COVERAGE_SCOPE_LANE_ENV,
        )
    }
    missing = sorted(name for name, value in values.items() if not value)
    if missing:
        raise RuntimeError(
            "coverage run scope is incomplete; missing " + ", ".join(missing)
        )

    scope_dir = Path(values[COVERAGE_SCOPE_DIR_ENV]).expanduser().resolve()
    packet_path = Path(values[COVERAGE_PACKET_ENV]).expanduser().resolve()
    receipt_path = Path(values[COVERAGE_RECEIPT_ENV]).expanduser().resolve()
    run_scope_id = values[COVERAGE_SCOPE_ID_ENV]
    lane = values[COVERAGE_SCOPE_LANE_ENV]
    if packet_path.parent != scope_dir or receipt_path.parent != scope_dir:
        raise RuntimeError("coverage run packet and receipt must stay inside the run scope")
    if packet_path.name != "coverage.packet.json":
        raise RuntimeError("coverage run packet path has an unexpected name")
    if receipt_path.name != "coverage.receipt.jsonl":
        raise RuntimeError("coverage run receipt path has an unexpected name")

    marker = _read_scope_marker(scope_dir)
    if marker.get("run_scope_id") != run_scope_id or marker.get("lane") != lane:
        raise RuntimeError("coverage run scope marker does not match the active environment")
    return CoverageRun(
        scope_dir=scope_dir,
        packet_path=packet_path,
        receipt_path=receipt_path,
        run_scope_id=run_scope_id,
        lane=lane,
    )


def record_coverage_event(event: dict[str, Any]) -> None:
    run = current_coverage_run()
    if run is None:
        return
    if not isinstance(event.get("event"), str) or not event["event"]:
        raise ValueError("coverage event must name a non-empty event")
    payload = {
        **event,
        "schema_version": COVERAGE_EVENT_SCHEMA_VERSION,
        "run_scope_id": run.run_scope_id,
        "lane": run.lane,
    }
    if run.receipt_path.is_symlink():
        raise RuntimeError(f"coverage run receipt must not be a symlink: {run.receipt_path}")
    with run.receipt_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        )


def read_coverage_events(run: CoverageRun) -> list[dict[str, Any]]:
    if not run.receipt_path.exists():
        return []
    if run.receipt_path.is_symlink() or not run.receipt_path.is_file():
        raise RuntimeError(f"coverage run receipt is not a regular file: {run.receipt_path}")
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        run.receipt_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"coverage run receipt line {line_number} is invalid JSON"
            ) from exc
        if not isinstance(event, dict):
            raise RuntimeError(
                f"coverage run receipt line {line_number} must be an object"
            )
        if (
            event.get("schema_version") != COVERAGE_EVENT_SCHEMA_VERSION
            or event.get("run_scope_id") != run.run_scope_id
            or event.get("lane") != run.lane
        ):
            raise RuntimeError(
                f"coverage run receipt line {line_number} has incompatible identity"
            )
        events.append(event)
    return events


def coverage_run_summary(run: CoverageRun) -> dict[str, Any]:
    events = read_coverage_events(run)
    builds = [event for event in events if event.get("event") == "build"]
    hits = [event for event in events if event.get("event") == "hit"]
    misses = [event for event in events if event.get("event") == "miss"]
    rejects = [event for event in events if event.get("event") == "reject"]
    failures = [event for event in events if event.get("event") == "build-failed"]
    identity_digests = sorted(
        {
            str(event["identity_digest"])
            for event in events
            if isinstance(event.get("identity_digest"), str)
        }
    )
    payload_digests = sorted(
        {
            str(event["payload_digest"])
            for event in events
            if isinstance(event.get("payload_digest"), str)
        }
    )
    owner_execution_events = [
        event
        for event in events
        if isinstance(event.get("owner_timings"), list)
    ]
    owner_receipts = [
        timing
        for event in owner_execution_events
        for timing in event.get("owner_timings", [])
        if isinstance(timing, dict)
    ]
    owner_worker_counts = sorted(
        {
            int(event["owner_worker_count"])
            for event in owner_execution_events
            if isinstance(event.get("owner_worker_count"), int)
            and not isinstance(event.get("owner_worker_count"), bool)
        }
    )
    input_identities = [
        event["input_identity"]
        for event in builds
        if isinstance(event.get("input_identity"), dict)
    ]
    return {
        "schema_version": COVERAGE_RECEIPT_SCHEMA_VERSION,
        "run_scope_id": run.run_scope_id,
        "lane": run.lane,
        "coverage_build_count": len(builds),
        "packet_hit_count": len(hits),
        "packet_miss_count": len(misses),
        "packet_reject_count": len(rejects),
        "build_failure_count": len(failures),
        "owner_scan_count": len(owner_receipts),
        "build_wall_ms": sum(
            int(event.get("duration_ms", 0))
            for event in builds
            if isinstance(event.get("duration_ms", 0), int)
        ),
        "identity_digests": identity_digests,
        "payload_digests": payload_digests,
        "input_identities": input_identities,
        "owner_worker_counts": owner_worker_counts,
        "owner_receipts": owner_receipts,
        "owner_timings": owner_receipts,
    }


def emit_coverage_run_summary(
    run: CoverageRun,
    *,
    lane_wall_ms: int,
) -> None:
    try:
        summary = coverage_run_summary(run)
        summary["lane_wall_ms"] = lane_wall_ms
    except (OSError, RuntimeError, UnicodeDecodeError) as exc:
        summary = {
            "schema_version": COVERAGE_RECEIPT_SCHEMA_VERSION,
            "run_scope_id": run.run_scope_id,
            "lane": run.lane,
            "receipt_error": str(exc),
        }
    print(
        "[aoa-kag-coverage-run-receipt] "
        + json.dumps(
            summary,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
        file=sys.stderr,
        flush=True,
    )


@contextmanager
def coverage_run_scope(*, lane: str, force_new: bool = False) -> Iterator[CoverageRun]:
    if not lane:
        raise ValueError("coverage run scope requires a lane")
    existing = current_coverage_run()
    if existing is not None and not force_new:
        yield existing
        return

    previous = {name: os.environ.get(name) for name in _SCOPE_ENV_NAMES}
    selected_parent = (
        os.environ.get(VALIDATION_ARTIFACT_PARENT_ENV)
        or os.environ.get("RUNNER_TEMP")
        or os.environ.get("TMPDIR")
    )
    parent = Path(selected_parent).expanduser().resolve() if selected_parent else None
    if parent is not None and not parent.is_dir():
        raise OSError(f"coverage run temporary parent does not exist: {parent}")
    if parent is not None and (parent == REPO_ROOT or REPO_ROOT in parent.parents):
        raise OSError(
            f"coverage run temporary parent must stay outside the repository: {parent}"
        )

    with tempfile.TemporaryDirectory(
        prefix="aoa-kag-coverage-run-",
        dir=parent,
    ) as tmpdir:
        started = time.perf_counter()
        scope_dir = Path(tmpdir).resolve()
        run_scope_id = secrets.token_hex(16)
        run = CoverageRun(
            scope_dir=scope_dir,
            packet_path=scope_dir / "coverage.packet.json",
            receipt_path=scope_dir / "coverage.receipt.jsonl",
            run_scope_id=run_scope_id,
            lane=lane,
        )
        _scope_marker_path(scope_dir).write_text(
            json.dumps(
                {"run_scope_id": run_scope_id, "lane": lane},
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        os.environ.update(
            {
                COVERAGE_PACKET_ENV: run.packet_path.as_posix(),
                COVERAGE_RECEIPT_ENV: run.receipt_path.as_posix(),
                COVERAGE_SCOPE_ACTIVE_ENV: "1",
                COVERAGE_SCOPE_DIR_ENV: run.scope_dir.as_posix(),
                COVERAGE_SCOPE_ID_ENV: run.run_scope_id,
                COVERAGE_SCOPE_LANE_ENV: run.lane,
            }
        )
        try:
            yield run
        finally:
            emit_coverage_run_summary(
                run,
                lane_wall_ms=max(
                    0,
                    round((time.perf_counter() - started) * 1000),
                ),
            )
            for name, value in previous.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
