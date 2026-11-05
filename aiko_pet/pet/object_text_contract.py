"""Object speech fields and immutable grammatical metadata, without UI rules."""

from dataclasses import dataclass
from typing import Literal, Mapping

GrammaticalGender = Literal["masculine", "feminine", "neuter"]
OBJECT_CASES = ("nom", "acc", "dat")
OBJECT_FORMS = tuple(
    f"item_{form}_{case}"
    for form in ("indef", "def", "poss", "pron") for case in OBJECT_CASES
)
OBJECT_TEXT_FIELDS = frozenset((
    "item", *OBJECT_FORMS, *(field[0].upper() + field[1:] for field in OBJECT_FORMS),
))


@dataclass(frozen=True, slots=True)
class ObjectGrammar:
    gender: GrammaticalGender
    spoken_name: str | None = None


@dataclass(frozen=True, slots=True)
class ObjectGrammarCatalog:
    entries: Mapping[str, ObjectGrammar]
