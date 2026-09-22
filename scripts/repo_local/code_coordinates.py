"""Exact source coordinates shared by code-observation adapters.

Offsets are half-open UTF-8 byte offsets. Native line/column coordinates are
never interpreted without an explicit position encoding.
"""
from __future__ import annotations

import re


class CodeObservationError(ValueError):
    """An input cannot support an exact code observation."""


def source_path(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or "\x00" in value
        or ":" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise CodeObservationError("source path must be canonical and relative")
    return value


def nonnegative_int(value: object, label: str) -> int:
    if type(value) is not int or not 0 <= value <= 2147483647:
        raise CodeObservationError(f"{label} must be a nonnegative int32")
    return value


class SourceText:
    """One exact UTF-8 blob, including CRLF and a trailing empty line."""

    def __init__(self, content: str | bytes):
        if not isinstance(content, (str, bytes)):
            raise CodeObservationError("source must be UTF-8 bytes or text")
        try:
            self.raw = content.encode("utf-8") if isinstance(content, str) else content
            self.text = self.raw.decode("utf-8")
        except UnicodeError as exc:
            raise CodeObservationError("source is not valid UTF-8") from exc
        parts = re.split(r"(\r\n|\r|\n)", self.text)
        self.lines: list[str] = []
        self.starts: list[int] = []
        offset = 0
        for index in range(0, len(parts), 2):
            self.lines.append(parts[index])
            self.starts.append(offset)
            offset += len(parts[index].encode("utf-8"))
            if index + 1 < len(parts):
                offset += len(parts[index + 1].encode("utf-8"))
        self._boundaries: dict[tuple[int, str], dict[int, int]] = {}

    def offset(self, line: int, column: int, encoding: str) -> int:
        nonnegative_int(line, "line")
        nonnegative_int(column, "column")
        if encoding not in {"utf-8", "utf-16", "utf-32"}:
            raise CodeObservationError("position encoding must be explicit")
        if line >= len(self.lines):
            raise CodeObservationError("line is outside the source blob")
        key = (line, encoding)
        if key not in self._boundaries:
            units = byte_offset = 0
            boundaries = {0: 0}
            for character in self.lines[line]:
                size = len(character.encode("utf-8"))
                units += size if encoding == "utf-8" else (
                    2 if encoding == "utf-16" and ord(character) > 0xFFFF else 1
                )
                byte_offset += size
                boundaries[units] = byte_offset
            self._boundaries[key] = boundaries
        if column not in self._boundaries[key]:
            raise CodeObservationError("column is outside the line or splits a code point")
        return self.starts[line] + self._boundaries[key][column]

    def span(self, coordinates: list[int], encoding: str) -> dict[str, object]:
        if not isinstance(coordinates, list) or len(coordinates) not in {3, 4}:
            raise CodeObservationError("range must contain three or four coordinates")
        for value in coordinates:
            nonnegative_int(value, "range coordinate")
        if len(coordinates) == 3:
            start_line, start_column, end_column = coordinates
            end_line = start_line
        else:
            start_line, start_column, end_line, end_column = coordinates
        start = self.offset(start_line, start_column, encoding)
        end = self.offset(end_line, end_column, encoding)
        if end < start:
            raise CodeObservationError("range ends before its start")
        return {
            "start_byte": start,
            "end_byte": end,
            "native_range": list(coordinates),
            "position_encoding": encoding,
        }
