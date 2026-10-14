"""Care presentation must preserve authored visuals without mutating needs."""

import unittest
from datetime import datetime
from unittest.mock import Mock

from aiko_pet.application.controller import CareOutcome
from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.pet.routine import context_at
from aiko_pet.ui.pet_view.care_presenter import CarePresenter, CareViewPorts


class CarePresenterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.set_item = Mock()
        self.cancel_action = Mock()
        self.start_action = Mock()
        self.cancel_followup = Mock()
        self.react = Mock()
        self.show_text = Mock()
        self.refresh_toolbar = Mock()
        self.refresh_status = Mock()
        self.presenter = CarePresenter(CareViewPorts(
            set_item=self.set_item,
            cancel_action=self.cancel_action,
            start_action=self.start_action,
            cancel_followup=self.cancel_followup,
            react=self.react,
            show_text=self.show_text,
            refresh_toolbar=self.refresh_toolbar,
            refresh_status=self.refresh_status,
        ))
        self.context = context_at(datetime(2026, 10, 12, 13).timestamp())

    def outcome(
        self, *, reaction: Reaction | None = None,
        item: str | None = None,
    ) -> CareOutcome:
        return CareOutcome(
            fallback_text="Okay", reaction=reaction, context=self.context,
            consumed_item_id=item,
        )

    def test_food_overlay_only_appears_after_consumption(self) -> None:
        self.presenter.present(
            "feed", self.outcome(item="dango"), now=100.0, sleeping=False,
        )
        self.set_item.assert_called_once_with("dango")
        self.start_action.assert_called_once_with("eat", 0.0)
        self.show_text.assert_called_once_with("Okay", 2450)
        self.refresh_status.assert_called_once()
        self.refresh_toolbar.assert_called_once()

    def test_rejected_food_does_not_animate_or_set_item(self) -> None:
        self.presenter.present(
            "feed", self.outcome(), now=100.0, sleeping=False,
        )
        self.set_item.assert_not_called()
        self.start_action.assert_not_called()

    def test_sleep_cancels_current_animation_without_starting_another(self) -> None:
        self.presenter.present(
            "sleep", self.outcome(), now=100.0, sleeping=True,
        )
        self.cancel_action.assert_called_once_with(100.0)
        self.start_action.assert_not_called()

    def test_existing_reaction_reuses_original_text_with_eat_animation(
        self,
    ) -> None:
        reaction = Reaction(
            line_id="test-care", event="feed", text="Hallo", animation="idle",
        )
        self.presenter.present(
            "energy_drink", self.outcome(reaction=reaction, item="energy_drink"),
            now=100.0, sleeping=False,
        )
        displayed, duration = self.react.call_args.args
        self.assertEqual((displayed.animation, duration), ("eat", 2900))
        self.assertEqual(displayed.text, "Hallo")
        self.assertEqual(reaction.animation, "idle")
        self.cancel_followup.assert_not_called()


if __name__ == "__main__":
    unittest.main()
