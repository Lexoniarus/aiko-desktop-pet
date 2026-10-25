"""Bounded source receipts round-trip without storing stories or buffers."""

import unittest
from copy import deepcopy

from test_social_content import joke_payload

from aiko_pet.application.social_content import (
    BUFFERED_CATEGORIES,
    SocialCategory,
    prepare_social_content,
)
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
        for category in BUFFERED_CATEGORIES:
            for i in range(102):
                prefix = ("uselessfacts:" if category == SocialCategory.FACT
                          else "jokeapi:")
                identifier = i + 1000 * list(SocialCategory).index(category)
                history = history.admitted(SocialContentReceipt(
                    category, f"{prefix}{identifier}", f"{identifier:064x}", i % 3,
                ))
        return history

    def test_each_category_keeps_one_hundred_without_full_content(self):
        history = self.history()
        self.assertEqual(len(history.entries), 300)
        for category in BUFFERED_CATEGORIES:
            entries = [e for e in history.entries if e.category == category]
            self.assertEqual(len(entries), 100)
            self.assertTrue(entries[0].identity.endswith("2"))
        raw = encode_social_history(history)
        self.assertEqual(decode_social_history(raw), history)
        self.assertEqual(set(raw["entries"][0]),
                         {"category", "identity", "fingerprint", "intro_variant"})
        self.assertEqual(decode_social_history(dict(version=1, entries=[])),
                         SocialContentHistory())

    def test_malformed_excessive_or_duplicate_receipts_are_rejected(self):
        raw = encode_social_history(self.history())
        invalid = []
        for field, value in (("category", "other"), ("identity", "uselessfacts:wrong"),
                             ("fingerprint", "bad"), ("identity", "jokeapi:x"),
                             ("fingerprint", "a" * 65), ("intro_variant", True),
                             ("intro_variant", -1), ("intro_variant", 3)):
            changed = deepcopy(raw)
            changed["entries"][0][field] = value
            invalid.append(changed)
        excessive = deepcopy(raw)
        excessive["entries"] = excessive["entries"][:100] + [dict(
            category="single", identity="jokeapi:999", fingerprint="f" * 64,
            intro_variant=0,
        )]
        invalid.append(excessive)  # 101 in one category, below the total cap.
        invalid += [dict(version=True, entries=[]), dict(version=2, entries=[]),
                    dict(version=1, entries=raw["entries"] + [raw["entries"][0]]),
                    dict(version=1, entries=[raw["entries"][0]] * 2)]
        for item in invalid:
            with self.subTest(value=item):
                with self.assertRaises(ValueError):
                    decode_social_history(item)

    def test_older_history_versions_keep_receipts_without_inventing_intro_state(self):
        raw = encode_social_history(SocialContentHistory((SocialContentReceipt(
            SocialCategory.SINGLE, "jokeapi:1", "a" * 64,
        ),)))
        for version in (1, 2, 3):
            legacy = deepcopy(raw)
            legacy["version"] = version
            del legacy["entries"][0]["intro_variant"]
            if version < 3:
                del legacy["horoscope"]
            if version < 2:
                del legacy["requests"]
            decoded = decode_social_history(legacy)
            self.assertIsNone(decoded.entries[0].intro_variant)
            self.assertEqual(decoded.entries[0].identity, "jokeapi:1")

    def test_equivalent_provider_text_deduplicates_across_part_boundaries(self):
        single = joke_payload(SocialCategory.SINGLE)
        two = joke_payload(SocialCategory.TWO_PARTS)
        single["joke"] = two["setup"] + " " + two["delivery"]
        first = prepare_social_content(SocialCategory.SINGLE, single)
        second = prepare_social_content(SocialCategory.TWO_PARTS, two)
        self.assertEqual(first.fingerprint, second.fingerprint)
