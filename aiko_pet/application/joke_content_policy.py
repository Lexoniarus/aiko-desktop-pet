"""Conservative wording checks and lossless question/punchline boundaries.

This is a rejection filter, not a semantic safety classifier. Category labels
alone never establish suitability; the local library uses a separate review list.
"""

import re
import unicodedata

_UNSUITABLE = re.compile(
    r"\b(?:blondin\w*|neger\w*|zigeuner\w*|eskimo\w*|kanak\w*|schwuchtel\w*|"
    r"behindert\w*|juden\w*|muslim\w*|islam\w*|tuerk\w*|türk\w*|polen|pole|"
    r"russen\w*|russe|chines\w*|auslaender\w*|ausländer\w*|fluechtling\w*|"
    r"flüchtling\w*|nazi\w*|hitler\w*|holocaust\w*|trump\w*|bundestag\w*|"
    r"politiker\w*|partei\w*|wahlkampf\w*|kanzler\w*|afd|cdu|spd|"
    r"arsch\w*|scheiss\w*|scheiß\w*|fick\w*|hure\w*|nutte\w*|"
    r"vergewaltig\w*|sex\w*|porno\w*|penis\w*|vagina\w*|kondom\w*|"
    r"terror\w*|selbstmord\w*|suizid\w*|kannibal\w*|zuhaelter\w*|zuhälter\w*)\b"
)


def wording_allowed(text: str) -> bool:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return _UNSUITABLE.search(normalized) is None


def question_parts(text: str) -> tuple[str, str]:
    """Only infer a split for one explicit question followed by its answer."""
    if text.count("?") != 1:
        raise ValueError("No unambiguous question/punchline boundary")
    setup, delivery = text.split("?", 1)
    delivery = delivery.strip()
    if not setup.strip() or not delivery:
        raise ValueError("Incomplete question/punchline pair")
    return setup.strip() + "?", delivery
