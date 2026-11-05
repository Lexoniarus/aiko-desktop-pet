"""Pure German object phrases; names and gender come from canonical resources."""

from ...pet.content import GERMAN_OBJECT_GRAMMAR, GERMAN_TEXT
from ...pet.object_text_contract import (
    OBJECT_CASES,
    GrammaticalGender,
    ObjectGrammarCatalog,
)

_ARTICLES: dict[str, dict[GrammaticalGender, tuple[str, str, str]]] = {
    "indef": {
        "masculine": ("ein", "einen", "einem"),
        "feminine": ("eine", "eine", "einer"),
        "neuter": ("ein", "ein", "einem"),
    },
    "def": {
        "masculine": ("der", "den", "dem"),
        "feminine": ("die", "die", "der"),
        "neuter": ("das", "das", "dem"),
    },
    "poss": {
        "masculine": ("mein", "meinen", "meinem"),
        "feminine": ("meine", "meine", "meiner"),
        "neuter": ("mein", "mein", "meinem"),
    },
    "pron": {
        "masculine": ("er", "ihn", "ihm"),
        "feminine": ("sie", "sie", "ihr"),
        "neuter": ("es", "es", "ihm"),
    },
}


def object_phrases(
    identity: str | None, label: str | None, *,
    grammar: ObjectGrammarCatalog = GERMAN_OBJECT_GRAMMAR,
) -> dict[str, str]:
    """Format known identity only; unknown possession becomes definite reference."""
    entry = grammar.entries.get(identity) if identity is not None and label else None
    gender: GrammaticalGender = entry.gender if entry is not None else "masculine"
    noun = ((entry.spoken_name or label) if entry is not None else
            GERMAN_TEXT.format("world.unknown_item"))
    assert noun is not None
    values = {"item": noun}
    for form, genders in _ARTICLES.items():
        # An unidentified sighting is "der Gegenstand", never an invented name
        # or an unsupported claim that it was already her personal possession.
        articles = _ARTICLES["def"][gender] if entry is None and form == "poss" else (
            genders[gender]
        )
        for case, article in zip(OBJECT_CASES, articles):
            phrase = article if form == "pron" else f"{article} {noun}"
            field = f"item_{form}_{case}"
            values[field] = phrase
            values[field[0].upper() + field[1:]] = phrase[0].upper() + phrase[1:]
    return values
