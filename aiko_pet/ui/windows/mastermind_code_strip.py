"""Readable public code projection, independent of the animated safe door."""
from __future__ import annotations

import math
import tkinter as tk

from ...games.mastermind import COLORS
from ...pet.content import GERMAN_TEXT
from ..common.mastermind_images import MastermindImages
from ..common.skin import AikoSkin
from ..view_models.mastermind_models import CodeView


class MastermindCodeStrip:
    def __init__(
        self, parent: tk.Misc, images: MastermindImages, skin: AikoSkin, width: int,
    ) -> None:
        self._skin = skin
        self._compact = width < 360
        size = 24 if self._compact else 32
        self._tokens = {}
        for color in COLORS:
            source = images.get(color)
            divisor = math.gcd(source.width(), size)
            self._tokens[color] = source.zoom(size // divisor).subsample(
                source.width() // divisor,
            )
        self.frame = tk.Frame(parent, bg='#E6E1F2', highlightthickness=1,
                              highlightbackground='#AEA1C6')
        self.canvas = tk.Canvas(self.frame, width=min(470, width - 12),
                                height=40 if self._compact else 64,
                                bg='#E6E1F2', bd=0, highlightthickness=0)
        self.canvas.pack()
        self.frame.bind('<Destroy>', self._destroyed, add='+')
        self.show(CodeView())

    def show(self, view: CodeView) -> None:
        canvas = self.canvas
        canvas.delete('all')
        heading = 52 if self._compact else 90
        step = (int(canvas.cget('width')) - heading) / 4
        canvas.create_text(heading / 2, 20 if self._compact else 25,
                           width=heading - 4, justify='center',
                           text=GERMAN_TEXT.format('mastermind.code'),
                           fill=self._skin.text,
                           font=(self._skin.font, 8 if self._compact else 10, 'bold'))
        for index, color in enumerate(view.slots):
            left = heading + index * step
            x = left + step / 2
            canvas.create_rectangle(left + 2, 2, left + step - 2,
                                    38 if self._compact else 62,
                                    fill='#F3EDF7', outline='#AEA1C6')
            y = 13 if self._compact else 23
            if color is None:
                canvas.create_text(x, y, text='?', fill=self._skin.muted,
                                   font=(self._skin.font, 18, 'bold'), tags='cover')
                label = str(index + 1)
            else:
                canvas.create_image(x, y, image=self._tokens[color], tags='solution')
                name = GERMAN_TEXT.format(f'mastermind.color.{color}')
                label = f'{index + 1}: {name}'
            canvas.create_text(x, 32 if self._compact else 52, text=label,
                               fill=self._skin.text,
                               font=(self._skin.font, 8 if self._compact else 9),
                               tags='caption')

    def _destroyed(self, event: tk.Event[tk.Misc]) -> None:
        if event.widget is self.frame:
            self._tokens.clear()
