"""Compose complete local book prose and independently selected Aiko reactions."""

from __future__ import annotations

from ..pet.horoscope import HoroscopeCatalogue, HoroscopeEntry, SkySnapshot
from ..pet.mind.catalog import Reaction
from ..pet.mind.reaction_sequence import Cue, conversation_timing
from .horoscope_models import DailyReadingRequest, PreparedBookReading


def prepare_book_reading(
    request: DailyReadingRequest,
    entry: HoroscopeEntry,
    catalogue: HoroscopeCatalogue,
    sky: SkySnapshot,
    opening: Reaction,
    comment: Reaction | None,
    closing: Reaction,
) -> PreparedBookReading:
    beats: list[Cue] = list(opening.beats)
    for passage in entry.passages:
        beats.append(Cue.text(passage.text))
        if passage.comment_key is not None and comment is not None:
            beats.extend(comment.beats)
    beats.extend(closing.beats)
    reaction = Reaction(
        f"book:{request.date}:{request.sign}:{entry.id}:{entry.revision}",
        conversation_timing(tuple(beats)),
        "idle",
        "horoscope_reading",
        presentation="story",
    )
    return PreparedBookReading(
        request.date,
        request.sign,
        entry.id,
        entry.revision,
        catalogue.revision,
        reaction,
        comment.line_id if comment else "",
        sky,
    )
