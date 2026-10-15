"""Validated German copy resource, separate from pet policy and Tk views.

The content is loaded once from packaged JSON. Callers use semantic keys,
so future sources (including SQLite) can provide the same mapping.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from string import Formatter
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class TextCatalog:
    """Immutable authored copy and strictly named interpolation fields."""

    messages: Mapping[str, str]

    def format(self, key: str, **values: str) -> str:
        return self.messages[key].format_map(values)


def parse_text_catalog(raw: Any) -> TextCatalog:
    """Fail before runtime interaction on malformed or unsafe text schemas."""
    if (
        not isinstance(raw, dict) or type(raw.get("version")) is not int
        or raw["version"] != 1 or raw.get("locale") != "de"
    ):
        raise ValueError("Unsupported German text catalogue")
    texts = raw.get("messages")
    if not isinstance(texts, dict) or not texts:
        raise ValueError("Missing German text records")
    normalized: dict[str, str] = {}
    for key, message in texts.items():
        if (
            not isinstance(key, str) or not key
            or any(not part.isidentifier() for part in key.split("."))
            or not isinstance(message, str) or not message
        ):
            raise ValueError("Invalid text key or content")
        try:
            fields = list(Formatter().parse(message))
        except ValueError as error:
            raise ValueError(f"Invalid copy template: {key}") from error
        if any(
            field is not None and (
                not field.isidentifier() or conversion is not None
                or spec
            )
            for _, field, spec, conversion in fields
        ):
            raise ValueError(f"Unsafe copy placeholder: {key}")
        normalized[key] = message
    return TextCatalog(MappingProxyType(normalized))


def load_packaged_text_catalog(
    path: Path = Path(__file__).resolve().parent / "data" / "texts.de.json",
) -> TextCatalog:
    """Read local data once; never invoke network services or an AI model."""
    return parse_text_catalog(json.loads(path.read_text(encoding="utf-8")))


GERMAN_TEXT = load_packaged_text_catalog()
