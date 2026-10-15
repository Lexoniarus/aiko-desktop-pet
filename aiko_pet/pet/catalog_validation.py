"""Strict local resource decoding; schemas remain with their typed owners."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON number: {value}")


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"Non-finite JSON number: {value}")
    return number


def load_json(path: Path) -> Any:
    """Report the resource path and reject silent key/number corruption."""
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
            parse_float=_finite_float,
        )
    except (ValueError, OSError, UnicodeError) as error:
        raise ValueError(f"{path}: {error}") from error


def object_fields(
    raw: Any,
    required: Iterable[str],
    *,
    optional: Iterable[str] = (),
    context: str,
) -> dict[str, Any]:
    """Reject unknown fields as well as missing fields before interpretation."""
    if not isinstance(raw, dict) or any(not isinstance(k, str) for k in raw):
        raise ValueError(f"{context}: expected an object")
    missing = set(required) - raw.keys()
    unknown = raw.keys() - (set(required) | set(optional))
    if missing or unknown:
        raise ValueError(
            f"{context}: missing fields {sorted(missing)}; "
            f"unknown fields {sorted(unknown)}"
        )
    return raw
