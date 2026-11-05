"""Window-free preference ownership and detached Credits link validation."""

import unittest
from dataclasses import replace
from typing import Any, cast
from unittest.mock import Mock, patch

from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_content import (
    PreparedSocialContent,
    SocialCategory,
    SocialProvider,
)
from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.ui.view_models.credits import project_credits
from aiko_pet.ui.view_models.projections import project_settings
from aiko_pet.ui.windows.settings_contracts import SettingsActions
from aiko_pet.ui.windows.settings_window import SettingsWindow
from tools.headless_widgets import Skin, Widget, widgets


class VnSettingsTests(unittest.TestCase):
    def test_sections_preserve_all_options_and_apply_only_explicit_commands(self):
        settings = PetSettings()
        events: list[str] = []

        def scale():
            settings.scale = 2 if settings.scale == 1 else 1
            events.append("scale")

        def option(key, value):
            setattr(settings, key, value)
            events.append(key)

        actions = SettingsActions(
            scale,
            option,
            lambda: events.append("forget"),
            lambda: events.append("reset"),
            lambda: events.append("center"),
            lambda: events.append("quit"),
            lambda: events.append("closed"),
        )
        with widgets(), patch("webbrowser.open") as browse:
            window = SettingsWindow(
                cast(Any, Widget()),
                100,
                100,
                snapshot=lambda: project_settings(settings),
                actions=actions,
                always_on_top=True,
                skin=cast(Any, Skin()),
            )
            self.assertEqual(
                set(window.values),
                {key for key, _ in project_settings(settings).options},
            )
            for section in window.SECTIONS:
                window.select_section(section)
            window.refresh()
            browse.assert_not_called()
            self.assertFalse(events)
            window.scale_buttons[2].invoke()
            window.scale_buttons[2].invoke()
            self.assertEqual(events, ["scale"])
            before = settings.auto_walk
            window.checkbuttons["auto_walk"].invoke()
            self.assertEqual(settings.auto_walk, not before)
            window.forget_button.invoke()
            window.reset_button.invoke()
            window.center_button.invoke()
            self.assertEqual(events[-3:], ["forget", "reset", "center"])
            window.close_button.invoke()
            window.close()
            self.assertEqual(events[-1], "closed")
            self.assertNotIn("quit", events)

    def test_credits_keep_provider_source_and_entry_distinct(
        self,
    ):
        content = PreparedSocialContent(
            SocialCategory.FACT,
            "fixture",
            "fingerprint",
            "Originalquelle",
            "https://example.test/source",
            "https://example.test/api-entry",
            Reaction.spoken("fixture", "Ein Fakt.", "idle", "talk"),
            SocialProvider.FACTS,
        )
        credit = project_credits(content)
        assert credit.accepted
        self.assertEqual(credit.accepted.provider, "Random Useless Facts")
        self.assertEqual(credit.accepted.source, "Originalquelle")
        current = [content]
        actions = SettingsActions(*(Mock() for _ in range(7)))
        with widgets(), patch("webbrowser.open") as browse:
            window = SettingsWindow(
                cast(Any, Widget()),
                100,
                100,
                snapshot=lambda: project_settings(PetSettings()),
                actions=actions,
                always_on_top=True,
                skin=cast(Any, Skin()),
                credits_snapshot=lambda: project_credits(current[0]),
            )
            window.select_section("credits")
            window.refresh_credits()
            browse.assert_not_called()
            window.credits.source_button.invoke()
            browse.assert_called_once_with("https://example.test/source")
            window.credits.entry_button.invoke()
            self.assertEqual(browse.call_args.args[0], "https://example.test/api-entry")
            current[0] = replace(content, source_url="", permalink="")
            window.refresh_credits()
            self.assertEqual(window.credits.source_button.cget("state"), "disabled")
            self.assertEqual(window.credits.entry_button.cget("state"), "disabled")
            window.close()
