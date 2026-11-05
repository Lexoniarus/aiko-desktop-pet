"""Load only individually reviewed texts from the pinned external library."""

import hashlib
from importlib import import_module
from importlib.metadata import version
from pathlib import Path
from typing import Literal

from ..application.social_content import (
    PreparedSocialContent,
    SocialCategory,
    SocialProvider,
    prepare_social_content,
)
from ..pet.catalog_validation import load_json, object_fields

REVIEW_PATH = Path(__file__).resolve().parents[1] / "data" / "pyjokes.de.review.json"
PYJOKES_VERSION = "0.8.3"
CatalogFailure = Literal["dependency", "review", "content"]


class LocalJokeCatalogError(ValueError):
    """Expected resource failure, without exposing library text to the UI."""

    def __init__(self, kind: CatalogFailure) -> None:
        super().__init__(f"Local joke catalogue failure: {kind}")
        self.kind = kind


def load_local_jokes(path: Path | None = None) -> tuple[PreparedSocialContent, ...]:
    try:
        raw = load_json(REVIEW_PATH if path is None else path)
        object_fields(raw, ("version", "package_version", "entries"),
                      context="joke review")
        if (type(raw["version"]) is not int or raw["version"] != 1
                or raw["package_version"] != PYJOKES_VERSION
                or not isinstance(raw["entries"], list)
                or not 1 <= len(raw["entries"]) <= 128):
            raise ValueError("Unsupported local joke review")
    except (ValueError, OSError, UnicodeError) as error:
        raise LocalJokeCatalogError("review") from error
    try:
        if version("pyjokes") != PYJOKES_VERSION:
            raise ValueError("Unsupported pyjokes version")
        library = import_module("pyjokes")
        library_error = import_module("pyjokes.exc").PyjokesError
        if (not isinstance(library_error, type)
                or not issubclass(library_error, Exception)):
            raise TypeError("Invalid pyjokes error contract")
    except (ImportError, AttributeError, ValueError, TypeError) as error:
        raise LocalJokeCatalogError("dependency") from error
    try:
        jokes = library.get_jokes(language="de", category="neutral")
        if (not isinstance(jokes, list) or not jokes
                or not all(isinstance(j, str) for j in jokes)):
            raise ValueError("Invalid local library contents")
    except (AttributeError, ValueError, TypeError, library_error) as error:
        raise LocalJokeCatalogError("content") from error
    try:
        return _prepare_reviewed(raw["entries"], jokes)
    except (ValueError, TypeError) as error:
        raise LocalJokeCatalogError("content") from error


def _prepare_reviewed(
    entries: list[object], jokes: list[str],
) -> tuple[PreparedSocialContent, ...]:
    prepared: list[PreparedSocialContent] = []
    seen = set()
    for entry in entries:
        row = object_fields(entry, ("index", "fingerprint", "category", "delivery_at"),
                            context="reviewed joke")
        index, split = row["index"], row["delivery_at"]
        if type(index) is not int or not 0 <= index < len(jokes) or index in seen:
            raise ValueError("Invalid reviewed library index")
        seen.add(index)
        original = jokes[index]
        fingerprint = hashlib.sha256(" ".join(original.split()).casefold().encode())
        if fingerprint.hexdigest() != row["fingerprint"]:
            raise ValueError("Library content changed since editorial review")
        category = SocialCategory(row["category"])
        parts: tuple[str, ...]
        if category == SocialCategory.SINGLE and split is None:
            parts = (original,)
        elif (category == SocialCategory.TWO_PARTS and type(split) is int
              and 0 < split < len(original)):
            parts = (original[:split], original[split:])
        else:
            raise ValueError("Invalid reviewed presentation boundary")
        prepared.append(prepare_social_content(
            category, dict(language="de", parts=parts), provider=SocialProvider.PYJOKES,
        ))
    return tuple(prepared)
