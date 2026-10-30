"""Flip width must not pull the moving card away from its flight centre."""
import math
import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from aiko_pet.games.blackjack import Phase, Table
from aiko_pet.games.playing_cards import Card
from aiko_pet.ui.common.playing_card_images import PlayingCardImages
from aiko_pet.ui.windows.blackjack_motion import BlackjackMotion
from aiko_pet.ui.windows.game_contracts import GameCardPorts
from aiko_pet.ui.windows.game_presentation import GamePresentation


class BlackjackMotionTests(unittest.TestCase):
    def test_visible_and_hidden_cards_keep_the_same_centred_flight_plane(self):
        root = tk.Tk()
        self.addCleanup(root.destroy)
        root.withdraw()
        owner = tk.Toplevel(root)
        owner.withdraw()
        images = PlayingCardImages(root)
        cards = GameCardPorts(images, Mock(), Mock(), Mock(), lambda _i, _n: (400, 300))
        presentation = GamePresentation(Mock(), Mock(), Mock(), lambda: (100, 100, 1))
        motion = BlackjackMotion(
            owner, cards, presentation, lambda _i, _n: (400, 300),
            lambda: Table((), (), 0, Phase.PLAYER, None), Mock(), Mock(), topmost=False,
        )
        self.addCleanup(motion.close)
        for face in (Card('hearts', 'A'), None):
            samples = []

            def tween(_ms, draw, done):
                for t in (.19, .3, .45, .49, .51, .6, .8, 1):
                    draw(t)
                    args = show.call_args.args
                    image, x, y = args[1:]
                    samples.append((t, image.width(), x + image.width() / 2, y))
                done()
            with patch.object(motion.effects, 'show') as show, \
                    patch.object(motion.effects, 'tween', side_effect=tween):
                motion.play('dealer', face, 0, Mock())
            for t, width, centre, y in samples:
                ease = t * t * (3 - 2 * t)
                self.assertAlmostEqual(centre, 268 + (400 - 268) * ease + 64)
                self.assertAlmostEqual(y, 138 + (300 - 138) * ease
                                       - 28 * math.sin(math.pi * t))
                if face is None:
                    self.assertEqual(width, 128)
            self.assertEqual(samples[-1][1], 128)
