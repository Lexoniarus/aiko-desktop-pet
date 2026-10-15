"""Required object phase dialogue is complete, safe and names only known items."""

import unittest
from typing import get_args

from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.pet.mind.catalog import DialogueBook, Line, Reaction
from aiko_pet.pet.mind.object_events import ObjectEvent
from aiko_pet.ui.view_models.object_reactions import format_object_reaction


class ObjectReactionTests(unittest.TestCase):
    def test_every_phase_event_has_unconditional_authored_copy(self):
        book = DialogueBook.from_file()
        for event in get_args(ObjectEvent):
            self.assertTrue(any(line.event == event and not line.moods
                                and not line.periods and not line.weekdays
                                for line in book.lines), event)

    def test_formatter_uses_canonical_names_and_unknown_does_not_reveal_identity(self):
        items = load_item_catalog()
        reaction = Reaction("id", "Das ist {item}.", "idle", "object_recognized")
        self.assertEqual(format_object_reaction(reaction, "onigiri", items).text,
                         "Das ist Onigiri.")
        self.assertEqual(format_object_reaction(reaction, None, items).text,
                         "Das ist etwas.")

    def test_object_templates_reject_attribute_access_and_format_expressions(self):
        for text in ("{item.secret}", "{other}", "{item!r}", "{item:100}"):
            with self.assertRaises(ValueError):
                Line.parse(dict(id="one", event="object_recognized", text=text,
                                animation="idle", moods=[], periods=[], weekdays=[]))
