#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from kag_generation import GenerationError, check_generated_outputs, write_generated_outputs


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate root KAG read-model outputs.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check generated output parity without writing files.",
    )
    return parser.parse_args(argv)


def run_check() -> int:
    drifted_paths = check_generated_outputs()
    if drifted_paths:
        for path in drifted_paths:
            print(f"[generate-kag] drift in {path.as_posix()}", file=sys.stderr)
        return 1
    print("[ok] generated KAG outputs are up to date")
    return 0


def run_write() -> int:
    written_paths = write_generated_outputs()
    for path in written_paths:
        print(f"[ok] wrote {path.as_posix()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.check:
            return run_check()
        return run_write()
    except GenerationError as exc:
        print(f"[error] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
