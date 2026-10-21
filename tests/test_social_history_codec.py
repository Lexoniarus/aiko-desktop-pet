"""Bounded source receipts round-trip without storing stories or buffers."""

import unittest
from copy import deepcopy

from test_social_content import joke_payload

from aiko_pet.application.social_content import SocialCategory, prepare_social_content
from aiko_pet.application.social_history import (
    SocialContentHistory,
    SocialContentReceipt,
)
from aiko_pet.infrastructure.social_history_codec import (
    decode_social_history,
    encode_social_history,
)


class SocialHistoryCodecTests(unittest.TestCase):
    def history(self):
        history = SocialContentHistory()
        for category in SocialCategory:
            for i in range(12):
                prefix = ("uselessfacts:" if category == SocialCategory.FACT
                          else "jokeapi:")
                identifier = i + 100 * list(SocialCategory).index(category)
                history = history.admitted(SocialContentReceipt(
                    category, f"{prefix}{identifier}", f"{identifier:064x}",
                ))
        return history

    def test_each_category_keeps_ten_without_full_content(self):
        history = self.history()
        self.assertEqual(len(history.entries), 30)
        for category in SocialCategory:
            entries = [e for e in history.entries if e.category == category]
            self.assertEqual(len(entries), 10)
            self.assertTrue(entries[0].identity.endswith("2"))
        raw = encode_social_history(history)
        self.assertEqual(decode_social_history(raw), history)
        self.assertEqual(set(raw["entries"][0]),
                         {"category", "identity", "fingerprint"})
        self.assertEqual(decode_social_history(dict(version=1, entries=[])),
                         SocialContentHistory())

    def test_malformed_excessive_or_duplicate_receipts_are_rejected(self):
        raw = encode_social_history(self.history())
        invalid = []
        for field, value in (("category", "other"), ("identity", "uselessfacts:wrong"),
                             ("fingerprint", "bad"), ("identity", "jokeapi:x"),
                             ("fingerprint", "a" * 65)):
            changed = deepcopy(raw)
            changed["entries"][0][field] = value
            invalid.append(changed)
        excessive = deepcopy(raw)
        excessive["entries"] = excessive["entries"][:10] + [dict(
            category="single", identity="jokeapi:99", fingerprint="f" * 64,
        )]
        invalid.append(excessive)  # Eleven in one category, below the total cap.
        invalid += [dict(version=True, entries=[]), dict(version=2, entries=[]),
                    dict(version=1, entries=raw["entries"] + [raw["entries"][0]]),
                    dict(version=1, entries=[raw["entries"][0]] * 2)]
        for item in invalid:
            with self.subTest(value=item):
                with self.assertRaises(ValueError):
                    decode_social_history(item)

    def test_equivalent_provider_text_deduplicates_across_part_boundaries(self):
        single = joke_payload(SocialCategory.SINGLE)
        two = joke_payload(SocialCategory.TWO_PARTS)
        single["joke"] = two["setup"] + " " + two["delivery"]
        first = prepare_social_content(SocialCategory.SINGLE, single)
        second = prepare_social_content(SocialCategory.TWO_PARTS, two)
        self.assertEqual(first.fingerprint, second.fingerprint)
