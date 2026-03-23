#!/usr/bin/env python3
from __future__ import annotations

from kag_generation import GenerationError, write_generated_outputs


def main() -> int:
    try:
        written_paths = write_generated_outputs()
    except GenerationError as exc:
        print(f"[error] {exc}")
        return 1

    for path in written_paths:
        print(f"[ok] wrote {path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
