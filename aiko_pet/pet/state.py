"""Mutable pet aggregate; rules commit effects without text or save formats."""

from __future__ import annotations

import time
from copy import deepcopy
from dataclasses import replace
from typing import Any

from .balance import BALANCE
from .care_actions import (
    CareTransition,
    plan_care_action,
    resolve_care_time,
)
from .care_result import CareResult
from .consumption import ConsumptionOrigin
from .food import (
    FoodActivity,
    FoodId,
    FoodState,
)
from .friendship import (
    calculate_friendship_reward,
    friendship_after_withholding,
)
from .fun import GameExperience, calculate_game_session_fun
from .lifecycle import (
    calculate_daily_routine,
    plan_pet_time,
)
from .need_decay import (
    NeedLevels,
    calculate_need_decay,
)
from .routine import TimeContext, context_at, due_meal
from .state_values import PetValues, PreparedItemConsumption
from .status_hints import MoodHint, choose_mood_hint
from .value_rules import clamp_need_value


class PetState:
    """Sole mutable aggregate, owning one immutable PetValues record."""

    __slots__ = ("_values", "__dict__")

    def __init__(
        self,
        satiety: float = BALANCE.number("initial", "satiety"),
        mood: float = BALANCE.number("initial", "mood"),
        energy: float = BALANCE.number("initial", "energy"),
        social: float = BALANCE.number("initial", "social"),
        affection: float = BALANCE.number("initial", "affection"),
        friendship: float = BALANCE.number("initial", "friendship"),
        friendship_day: str = "",
        friendship_gained_today: float = 0.0,
        care_types_today: list[str] | None = None,
        care_last_rewards: dict[str, float] | None = None,
        sleeping: bool = False,
        updated_at: float | None = None,
        meals_date: str = "",
        meals_today: list[str] | None = None,
        sleep_origin: str = "",
        auto_sleep_night: str = "",
        nap_until: float = 0.0,
        auto_nap_day: str = "",
        food: FoodState | None = None,
        fun: float = BALANCE.number("initial", "fun"),
        lived_seconds: float = 0.0,
    ) -> None:
        self._values = PetValues(
            satiety=satiety, mood=mood, energy=energy, social=social,
            affection=affection, friendship=friendship,
            friendship_day=friendship_day,
            friendship_gained_today=friendship_gained_today,
            care_types_today=tuple(care_types_today or ()),
            care_last_rewards=tuple((care_last_rewards or {}).items()),
            sleeping=sleeping,
            updated_at=time.time() if updated_at is None else updated_at,
            meals_date=meals_date, meals_today=tuple(meals_today or ()),
            sleep_origin=sleep_origin, auto_sleep_night=auto_sleep_night,
            nap_until=nap_until, auto_nap_day=auto_nap_day,
            food=FoodState() if food is None else food, fun=fun,
            lived_seconds=lived_seconds,
        )

    def __repr__(self) -> str:
        return f"PetState({self._values!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PetState):
            return NotImplemented
        return self._values == other._values

    def __deepcopy__(self, memo: dict[int, object]) -> PetState:
        copied = PetState()
        copied.restore_checkpoint(deepcopy(self._values, memo))
        memo[id(self)] = copied
        return copied

    def _change(self, **values: Any) -> None:
        """One aggregate-owned replacement, never a public field setter."""
        self._values = replace(self._values, **values)

    @property
    def care_types_today(self) -> list[str]:
        """Compatibility read: a detached list cannot mutate the aggregate."""
        return list(self._values.care_types_today)

    @property
    def care_last_rewards(self) -> dict[str, float]:
        """Compatibility read: return a detached mapping."""
        return dict(self._values.care_last_rewards)

    @property
    def meals_today(self) -> list[str]:
        """Compatibility read: a detached list cannot mutate the aggregate."""
        return list(self._values.meals_today)

    @property
    def satiety(self) -> float:
        return self._values.satiety

    @property
    def mood(self) -> float:
        return self._values.mood

    @property
    def energy(self) -> float:
        return self._values.energy

    @property
    def social(self) -> float:
        return self._values.social

    @property
    def affection(self) -> float:
        return self._values.affection

    @property
    def friendship(self) -> float:
        return self._values.friendship

    @property
    def friendship_day(self) -> str:
        return self._values.friendship_day

    @property
    def friendship_gained_today(self) -> float:
        return self._values.friendship_gained_today

    @property
    def sleeping(self) -> bool:
        return self._values.sleeping

    @property
    def updated_at(self) -> float:
        return self._values.updated_at

    @property
    def lived_seconds(self) -> float:
        """Durable elapsed axis for future histories, independent of wall jumps."""
        return self._values.lived_seconds

    @property
    def meals_date(self) -> str:
        return self._values.meals_date

    @property
    def sleep_origin(self) -> str:
        return self._values.sleep_origin

    @property
    def auto_sleep_night(self) -> str:
        return self._values.auto_sleep_night

    @property
    def nap_until(self) -> float:
        return self._values.nap_until

    @property
    def auto_nap_day(self) -> str:
        return self._values.auto_nap_day

    @property
    def food(self) -> FoodState:
        return self._values.food

    @property
    def fun(self) -> float:
        return self._values.fun

    @property
    def friendship_level(self) -> int:
        """Display level (1..10), derived from the durable 0..100 bond."""
        return min(10, 1 + int(self.friendship // 10))

    def _roll_meals(self, context: TimeContext) -> None:
        if self.meals_date != context.day_key:
            self._change(meals_date=context.day_key, meals_today=())

    def _set_needs(self, values: NeedLevels) -> None:
        """Commit validated need values together inside the pet aggregate."""
        self._change(
            satiety=values.satiety, mood=values.mood, energy=values.energy,
            social=values.social, affection=values.affection,
        )

    def update_daily_routine(
        self,
        context: TimeContext,
        *,
        allow_bedtime: bool = True,
        allow_nap: bool = False,
        interrupt_nap: bool = False,
        effort: float | None = None,
    ) -> None:
        """Apply an evaluated sleep transition without exposing private hooks."""
        self._roll_meals(context)
        transition = calculate_daily_routine(
            self,
            context,
            allow_bedtime=allow_bedtime,
            allow_nap=allow_nap,
            interrupt_nap=interrupt_nap,
            effort=effort,
        )
        self._change(
            sleeping=transition.sleeping, sleep_origin=transition.sleep_origin,
            nap_until=transition.nap_until,
            auto_sleep_night=transition.auto_sleep_night,
            auto_nap_day=transition.auto_nap_day,
        )

    def _decay(
        self,
        hours: float,
        effort: float | None = None,
        food_activity: FoodActivity | None = None,
    ) -> None:
        """Commit the pure policy's immutable result as one aggregate update."""
        progress = calculate_need_decay(
            self, hours, effort, food_activity=food_activity,
        )
        needs = progress.needs
        self._change(
            satiety=needs.satiety, mood=needs.mood, energy=needs.energy,
            social=needs.social, affection=needs.affection,
            food=progress.food, fun=progress.fun,
        )

    def record_game_experience(
        self,
        experience: GameExperience,
        *,
        now: float,
    ) -> float:
        """Commit one finished minigame, retaining no session statistics."""
        reward = calculate_game_session_fun(experience, self.fun)
        if experience.completed_units == 0:
            return 0.0
        before = self.fun
        self._change(
            fun=clamp_need_value(self.fun + reward.fun_points, 0.0),
            energy=clamp_need_value(self.energy - reward.energy_cost, 0.0),
            social=clamp_need_value(self.social + reward.social_gain, 0.0),
        )
        self._credit_friendship("play", now, before)
        return self.fun - before

    def advance(
        self,
        now: float,
        *,
        auto_routine: bool = False,
        allow_bedtime: bool | None = None,
        allow_nap: bool = False,
        interrupt_nap: bool = False,
        effort: float | None = None,
        elapsed_seconds: float | None = None,
        food_activity: FoodActivity | None = None,
    ) -> None:
        """Execute all elapsed time; only recent observations affect its tail."""
        steps = plan_pet_time(
            self.updated_at,
            now,
            auto_routine=auto_routine,
            effort=effort,
            elapsed_seconds=elapsed_seconds,
            food_activity=food_activity,
        )
        if steps is None:
            return
        if not auto_routine:
            for step in steps:
                self._decay(step.hours, step.effort, step.food_activity)
            self._roll_meals(context_at(now))
        else:
            for step in steps:
                if step.context is None:
                    continue
                self.update_daily_routine(
                    step.context,
                    allow_bedtime=not step.observed or allow_bedtime is not False,
                    allow_nap=step.observed and allow_nap,
                    interrupt_nap=step.observed and interrupt_nap,
                )
                self._decay(step.hours, step.effort, step.food_activity)
            self.update_daily_routine(
                context_at(now),
                allow_bedtime=allow_bedtime is not False,
                allow_nap=allow_nap,
            )
        self._change(
            updated_at=now,
            lived_seconds=self.lived_seconds + steps.elapsed_seconds,
        )

    def apply_object_withholding(self, loss: float) -> float:
        """Commit a bounded application decision without manufacturing care."""
        previous = self.friendship
        self._change(friendship=friendship_after_withholding(previous, loss))
        return previous - self.friendship

    def _credit_friendship(
        self,
        action: str,
        stamp: float,
        need_before: float,
    ) -> None:
        """Apply an immutable friendship decision to owned reward fields."""
        transition = calculate_friendship_reward(
            self,
            action,
            stamp,
            need_before,
        )
        if transition is None:
            return
        self._change(
            friendship=transition.friendship, friendship_day=transition.day,
            friendship_gained_today=transition.gained_today,
            care_types_today=transition.care_types,
            care_last_rewards=transition.last_rewards,
        )

    def interact(
        self,
        action: str,
        *,
        now: float | None = None,
        food_id: FoodId | None = None,
    ) -> CareResult:
        """Commit one care transition and its friendship reward atomically."""
        stamp = resolve_care_time(now)
        transition = plan_care_action(
            self,
            action,
            now=stamp,
            food_id=food_id,
        )
        return self._apply_care_transition(transition, stamp)

    def consume_item(
        self, item_id: str, origin: ConsumptionOrigin, *, now: float,
    ) -> CareResult | None:
        """Use canonical nutrition; autonomous intake is not human attention."""
        if self.sleeping:
            return None
        action = "energy_drink" if item_id == "energy_drink" else "feed"
        transition = plan_care_action(
            self, action, now=now,
            food_id=None if action == "energy_drink" else item_id,
        )
        if origin == ConsumptionOrigin.AUTONOMOUS:
            transition = replace(
                transition, reward_action=None,
                needs=replace(transition.needs, social=self.social),
            )
        return self._apply_care_transition(transition, now)

    def capture_checkpoint(self) -> PetValues:
        """The already immutable complete value is a safe independent capture."""
        return self._values

    def restore_checkpoint(self, checkpoint: PetValues) -> None:
        """Restore owned values without replacing this live PetState identity."""
        self._values = checkpoint

    def prepare_item_consumption(
        self, item_id: str, origin: ConsumptionOrigin, *, now: float,
    ) -> PreparedItemConsumption | None:
        """Plan a complete consumption transition without mutating this pet."""
        working = deepcopy(self)
        result = working.consume_item(item_id, origin, now=now)
        if result is None or result.consumed_item_id is None:
            return None
        return PreparedItemConsumption(working.capture_checkpoint(), result)

    def restore_values(self, snapshot: PetState) -> None:
        """Compatibility for existing callers until the stage-seven migration."""
        self.restore_checkpoint(snapshot.capture_checkpoint())

    def anchor_live_session(self, now: float) -> None:
        """Rebase wall time without resetting the durable elapsed axis."""
        self._change(updated_at=now)

    def _apply_care_transition(
        self, transition: CareTransition, stamp: float,
    ) -> CareResult:
        if not transition.changed:
            return transition.result
        self._set_needs(transition.needs)
        self._change(
            sleeping=transition.sleeping, sleep_origin=transition.sleep_origin,
            nap_until=transition.nap_until,
            auto_sleep_night=transition.auto_sleep_night,
        )
        if transition.food is not None:
            self._change(food=transition.food)
        if (
            self.meals_date != transition.meals_date
            or tuple(self.meals_today) != transition.meals_today
        ):
            self._change(
                meals_date=transition.meals_date,
                meals_today=transition.meals_today,
            )
        if transition.reward_action is not None:
            self._credit_friendship(
                transition.reward_action,
                stamp,
                transition.need_before,
            )
        return transition.result

    def due_meal(self, context: TimeContext) -> str | None:
        """Return the due meal ID, or None when only snacks remain."""
        return due_meal(
            context,
            meals_date=self.meals_date,
            meals_today=self.meals_today,
        )

    def mood_hint(self, context: TimeContext | None = None) -> MoodHint:
        """Return the semantic status hint, not a language-specific sentence."""
        return choose_mood_hint(self, context)
