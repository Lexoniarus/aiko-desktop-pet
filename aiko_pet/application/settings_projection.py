"""Create immutable settings presentation values from persistence settings."""

from __future__ import annotations

from ..storage import PetSettings
from ..ui.settings_contracts import SettingsSnapshot


def project_settings(settings: PetSettings) -> SettingsSnapshot:
    return SettingsSnapshot(
        scale=settings.scale,
        options=(
            ("always_on_top", settings.always_on_top),
            ("auto_walk", settings.auto_walk),
            ("auto_routine", settings.auto_routine),
            ("follow_cursor", settings.follow_cursor),
            ("spontaneous_talk", settings.spontaneous_talk),
            ("observe_computer", settings.observe_computer),
            ("learn_rhythm", settings.learn_rhythm),
        ),
    )
