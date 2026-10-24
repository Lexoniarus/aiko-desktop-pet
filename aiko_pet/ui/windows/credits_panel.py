"""Embedded credits: providers and the accepted item's original source stay distinct."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from functools import partial
from typing import Callable

from ...asset_paths import ASSET_ROOT
from ...pet.content import GERMAN_TEXT
from ..common.skin import AikoSkin
from ..view_models.credits import ContentCredit, CreditsSnapshot


class CreditsPanel:
    def __init__(
        self, parent: tk.Misc, skin: AikoSkin, snapshot: Callable[[], CreditsSnapshot]
    ) -> None:
        self.frame = tk.Frame(parent, bg=skin.background)
        self._snapshot = snapshot
        self._current: ContentCredit | None = None
        self._last_view: CreditsSnapshot | None = None
        self._skin = skin
        self._heading("vn.credits.apis")
        for name, url in (
            ("JokeAPI", "https://jokeapi.dev/"),
            ("Random Useless Facts", "https://uselessfacts.jsph.pl/"),
            ("Zitat-Service", "https://www.zitat-service.de/"),
            ("AstroWay", "https://api.astroway.info/en/free/"),
        ):
            skin.button(
                self.frame, name, partial(self._open_provider, url), size="wide"
            ).pack(anchor="w", pady=2)
        skin.button(
            self.frame, GERMAN_TEXT.format("social.quote_license"),
            partial(self._open_provider,
                    "https://creativecommons.org/licenses/by/4.0/"), size="wide",
        ).pack(anchor="w", pady=2)
        self._copy(GERMAN_TEXT.format("social.quote_collection_credit"))
        self.accepted = self._copy("")
        self.author_button = skin.button(
            self.frame, GERMAN_TEXT.format("social.author_entry"),
            self._open_author, size="wide",
        )
        self.author_button.pack(anchor="w", pady=2)
        self.source_button = skin.button(self.frame, "", self._open_source, size="wide")
        self.source_button.pack(anchor="w", pady=2)
        self.entry_button = skin.button(
            self.frame,
            GERMAN_TEXT.format("social.api_entry"),
            self._open_entry,
            size="wide",
        )
        self.entry_button.pack(anchor="w", pady=2)
        self._heading("vn.credits.graphics")
        self._copy(GERMAN_TEXT.format("vn.credits.graphics_copy"))
        project_root = ASSET_ROOT.parents[1]
        skin.button(
            self.frame,
            GERMAN_TEXT.format("vn.graphic_licenses"),
            partial(self._open_provider, (project_root / "LICENSES").as_uri()),
            size="wide",
        ).pack(anchor="w", pady=2)
        self._heading("vn.credits.project")
        self._copy(GERMAN_TEXT.format("vn.credits.project_copy"))
        skin.button(
            self.frame,
            GERMAN_TEXT.format("vn.project_files"),
            partial(self._open_provider, (project_root / "README.md").as_uri()),
            size="wide",
        ).pack(anchor="w", pady=2)
        self.refresh()

    def _open_provider(self, url: str) -> None:
        webbrowser.open(url)

    def _heading(self, key: str) -> None:
        tk.Label(
            self.frame,
            text=GERMAN_TEXT.format(key),
            bg=self._skin.background,
            fg=self._skin.text,
            font=(self._skin.font, 11, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(10, 4))

    def _copy(self, text: str) -> tk.Label:
        label = tk.Label(
            self.frame,
            text=text,
            bg=self._skin.background,
            fg=self._skin.text,
            font=(self._skin.font, 9),
            wraplength=450,
            justify="left",
            anchor="w",
        )
        label.pack(fill="x", pady=4)
        return label

    def refresh(self) -> None:
        view = self._snapshot()
        if view == self._last_view:
            return
        self._last_view = view
        source = view.accepted
        self._current = source
        text = (
            "\n".join(part for part in (
                source.provider, source.author, source.source, source.license_name,
            ) if part)
            if source is not None
            else GERMAN_TEXT.format("vn.credits.no_content")
        )
        if self.accepted.cget("text") != text:
            self.accepted.configure(text=text)
        self.source_button.configure(
            text=GERMAN_TEXT.format(
                "social.source", source=source.source if source else "—"
            ),
            state="normal" if source is not None and source.source_url else "disabled",
        )
        self.entry_button.configure(
            state="normal" if source is not None and source.entry_url else "disabled"
        )
        self.author_button.configure(
            state="normal" if source is not None and source.author_url else "disabled"
        )

    def _open_source(self) -> None:
        if self._current is not None and self._current.source_url:
            webbrowser.open(self._current.source_url)

    def _open_entry(self) -> None:
        if self._current is not None and self._current.entry_url:
            webbrowser.open(self._current.entry_url)

    def _open_author(self) -> None:
        if self._current is not None and self._current.author_url:
            webbrowser.open(self._current.author_url)
