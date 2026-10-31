"""Imported card completeness/provenance and actual Tk image lifetime."""

import hashlib
import json
import tkinter as tk
import unittest

from PIL import Image

from aiko_pet.asset_paths import PLAYING_CARDS_DIR
from aiko_pet.games.playing_cards import STANDARD_DECK, Card
from aiko_pet.ui.common.playing_card_images import PlayingCardImages


class PlayingCardAssetTests(unittest.TestCase):
    def test_full_deck_back_and_unmodified_source_hashes(self):
        manifest = json.loads((PLAYING_CARDS_DIR / "provenance.json").read_text())
        names = {card.asset_name for card in STANDARD_DECK} | {"card_back.png"}
        self.assertEqual(len(names), 53)
        self.assertEqual(set(manifest["files"]), names)
        self.assertEqual(manifest["license"], "CC0-1.0")
        for name in names:
            path = PLAYING_CARDS_DIR / name
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(), manifest["files"][name],
            )
            with Image.open(path) as image:
                self.assertEqual(image.size, (64, 64))
                rgba = image.convert("RGBA")
                pixel = rgba.getpixel((0, 0))
                assert isinstance(pixel, tuple)
                self.assertEqual(pixel[3], 0)
                self.assertIsNotNone(rgba.getbbox())

    def test_invalid_card_identity_cannot_escape_asset_directory(self):
        with self.assertRaises(ValueError):
            Card("../", "A")


class PlayingCardImageTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.images = PlayingCardImages(self.root)
        self.addCleanup(self.images.clear)

    def test_cache_native_integer_scale_flip_and_release(self):
        card = Card("hearts", "A")
        image = self.images.get(card)
        self.assertIs(image, self.images.get(card))
        self.assertEqual((image.width(), image.height()), (64, 64))
        name = str(image)
        self.assertEqual(self.images.get(card, 2).width(), 128)
        self.assertEqual(self.images.get(card, 2, 8).width(), 16)
        self.assertEqual(self.images.get(None).width(), 64)
        del image
        self.images.clear()
        self.assertNotIn(name, self.root.tk.call("image", "names"))
        with self.assertRaises(ValueError):
            self.images.get(card, 3)

    def test_draw_pile_reuses_back_preserves_transparency_and_releases(self):
        back = self.images.get(None, 2)
        pile = self.images.draw_pile()
        self.assertIs(pile, self.images.draw_pile())
        self.assertEqual((pile.width(), pile.height()), (144, 144))
        self.assertTrue(pile.transparency_get(0, 0))
        self.assertFalse(pile.transparency_get(23, 40))
        self.assertFalse(pile.transparency_get(115, 40))
        self.assertTrue(back.transparency_get(115, 40))
        name = str(pile)
        del pile
        self.images.clear()
        self.assertNotIn(name, self.root.tk.call("image", "names"))
