"""Load only individually reviewed texts from the pinned external library."""

import hashlib
import json
from importlib import import_module
from importlib.metadata import version
from pathlib import Path

from ..application.social_content import (
    PreparedSocialContent,
    SocialCategory,
    SocialProvider,
    prepare_social_content,
)
from ..pet.catalog_validation import object_fields

REVIEW_PATH = Path(__file__).resolve().parents[1] / "data" / "pyjokes.de.review.json"


def load_local_jokes(path: Path = REVIEW_PATH) -> tuple[PreparedSocialContent, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    object_fields(raw, ("version", "package_version", "entries"), context="joke review")
    if (type(raw["version"]) is not int or raw["version"] != 1
            or raw["package_version"] != version("pyjokes")
            or not isinstance(raw["entries"], list) or len(raw["entries"]) > 128):
        raise ValueError("Unsupported local joke review/package version")
    jokes = import_module("pyjokes").get_jokes(language="de", category="neutral")
    if not isinstance(jokes, list) or not all(isinstance(j, str) for j in jokes):
        raise ValueError("Invalid local library contents")
    prepared = []
    seen = set()
    for row in raw["entries"]:
        object_fields(row, ("index", "fingerprint", "category", "delivery_at"),
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
