"""The lifecycle surface required by the utility-window owner."""

import tkinter as tk
from typing import Protocol


class GameWindow(Protocol):
    @property
    def window(self) -> tk.Toplevel: ...

    def greet(self) -> None: ...

    def close(self) -> None: ...

    def set_topmost(self, enabled: bool) -> None: ...
