"""Pure care rules for Aiko, with an optional gentle daily rhythm."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any

from .friendship import (
    CARE_FRIENDSHIP_GAIN as CARE_FRIENDSHIP_GAIN,
    CARE_PRIMARY_NEED as CARE_PRIMARY_NEED,
    FRIENDSHIP_DAILY_CAP as FRIENDSHIP_DAILY_CAP,
    FRIENDSHIP_NEED_THRESHOLD as FRIENDSHIP_NEED_THRESHOLD,
    FRIENDSHIP_REWARD_INTERVAL as FRIENDSHIP_REWARD_INTERVAL,
    FRIENDSHIP_VARIETY_BONUS as FRIENDSHIP_VARIETY_BONUS,
    LEGACY_REWARD_ACTIONS as LEGACY_REWARD_ACTIONS,
    award_friendship_for_care,
)
from .routine import MEAL_NAMES, TimeContext, context_at
from .value_rules import bounded as bounded, clamp_saved_time as clamp_saved_time

MAX_CATCHUP_SECONDS = 8 * 60 * 60
SIMULATION_STEP_SECONDS = 300
# Live telemetry is never projected across a restart/suspend or offline gap.
MAX_LIVE_EFFORT_SECONDS = 30.0
@dataclass
class PetState:
    satiety: float = 75.0
    mood: float = 75.0
    energy: float = 75.0
    social: float = 75.0  # Conversation and shared activity.
    affection: float = 75.0  # Gentle attention and feeling cared for.
    friendship: float = 15.0  # Slow, durable bond; never an immediate need.
    friendship_day: str = ""
    friendship_gained_today: float = 0.0
    care_types_today: list[str] = field(default_factory=list)
    care_last_rewards: dict[str, float] = field(default_factory=dict)
    sleeping: bool = False
    updated_at: float = field(default_factory=time.time)
    meals_date: str = ""
    meals_today: list[str] = field(default_factory=list)
    sleep_origin: str = ""  # "routine" or "manual", manual sleep isn't auto-cancelled
    auto_sleep_night: str = ""  # prevents repeated bedtime after manual waking
    nap_until: float = 0.0
    auto_nap_day: str = ""

    @classmethod
    def from_dict(cls, value: Any, *, now: float | None = None) -> PetState:
        """Load old saves defensively, preserving existing needs and trust."""
        current = time.time() if now is None else now
        if not isinstance(value, dict):
            return cls(updated_at=current)
        timestamp = value.get("updated_at", current)
        try:
            timestamp = float(timestamp)
        except (TypeError, ValueError, OverflowError):
            timestamp = current
        if not math.isfinite(timestamp):
            timestamp = current
        meals = value.get("meals_today")
        if not isinstance(meals, list):
            meals = []
        allowed_meals = tuple(MEAL_NAMES)
        valid_meals = [m for m in allowed_meals if m in meals]
        meals_date = value.get("meals_date", "")
        if not isinstance(meals_date, str) or len(meals_date) != 10:
            meals_date = ""
        sleeping = value.get("sleeping") is True
        origin = value.get("sleep_origin")
        if origin not in ("routine", "manual", "nap"):
            origin = "manual" if sleeping else ""
        night_key = value.get("auto_sleep_night")
        if not isinstance(night_key, str) or len(night_key) > 10:
            night_key = ""
        return cls(
            satiety=bounded(value.get("satiety")),
            mood=bounded(value.get("mood")),
            energy=bounded(value.get("energy")),
            social=bounded(value.get("social")),
            affection=bounded(value.get("affection")),
            friendship=bounded(value.get("friendship"), 15.0),
            friendship_day=value.get("friendship_day", "")
            if isinstance(value.get("friendship_day"), str)
            and len(value.get("friendship_day", "")) == 10 else "",
            friendship_gained_today=min(
                FRIENDSHIP_DAILY_CAP,
                bounded(value.get("friendship_gained_today", 0.0), 0.0),
            ),
            care_types_today=cls._load_care_types(value.get("care_types_today")),
            care_last_rewards=cls._load_reward_times(value.get("care_last_rewards")),
            sleeping=sleeping,
            updated_at=timestamp,
            meals_date=meals_date,
            meals_today=valid_meals,
            sleep_origin=origin,
            auto_sleep_night=night_key,
            nap_until=clamp_saved_time(value.get("nap_until")),
            auto_nap_day=value.get("auto_nap_day", "")
            if isinstance(value.get("auto_nap_day"), str)
            and len(value.get("auto_nap_day", "")) == 10 else "",
        )

    @staticmethod
    def _load_care_types(raw: Any) -> list[str]:
        if not isinstance(raw, list):
            return []
        return [action for action in CARE_PRIMARY_NEED if action in raw]

    @staticmethod
    def _load_reward_times(raw: Any) -> dict[str, float]:
        if not isinstance(raw, dict):
            return {}
        return {
            action: clamp_saved_time(raw[action])
            for action in (*CARE_FRIENDSHIP_GAIN, *LEGACY_REWARD_ACTIONS)
            if action in raw and clamp_saved_time(raw[action]) > 0
        }

    @property
    def friendship_level(self) -> int:
        """Display level (1..10), derived from the durable 0..100 bond."""
        return min(10, 1 + int(self.friendship // 10))

    def to_dict(self) -> dict[str, Any]:
        return {
            "satiety": round(self.satiety, 4),
            "mood": round(self.mood, 4),
            "energy": round(self.energy, 4),
            "social": round(self.social, 4),
            "affection": round(self.affection, 4),
            "friendship": round(self.friendship, 4),
            "friendship_day": self.friendship_day,
            "friendship_gained_today": round(self.friendship_gained_today, 4),
            "care_types_today": list(self.care_types_today),
            "care_last_rewards": dict(self.care_last_rewards),
            "sleeping": self.sleeping,
            "updated_at": self.updated_at,
            "meals_date": self.meals_date,
            "meals_today": list(self.meals_today),
            "sleep_origin": self.sleep_origin,
            "auto_sleep_night": self.auto_sleep_night,
            "nap_until": self.nap_until,
            "auto_nap_day": self.auto_nap_day,
        }

    def _roll_meals(self, context: TimeContext) -> None:
        if self.meals_date != context.day_key:
            self.meals_date = context.day_key
            self.meals_today = []

    def _apply_clock(self, context: TimeContext, *,
                     allow_bedtime: bool = True,
                     allow_nap: bool = False,
                     interrupt_nap: bool = False,
                effort: float | None = None) -> None:
        self._roll_meals(context)
        stamp = context.local.timestamp()
        if self.sleep_origin == "nap" and (
            stamp >= self.nap_until or interrupt_nap
        ):
            self.sleeping = False
            self.sleep_origin = ""
            self.nap_until = 0.0
        if not allow_bedtime and self.sleep_origin == "routine":
            # Aiko cannot remain automatically asleep during real computer work.
            self.sleeping = False
            self.sleep_origin = ""
            self.auto_sleep_night = ""
        if context.night and allow_bedtime:
            if self.sleep_origin == "nap":
                self.sleep_origin = "routine"
                self.nap_until = 0.0
                self.auto_sleep_night = context.night_key
            if self.auto_sleep_night != context.night_key:
                self.auto_sleep_night = context.night_key
                if not self.sleeping:
                    self.sleeping = True
                    self.sleep_origin = "routine"
        elif self.sleeping and self.sleep_origin == "routine":
            self.sleeping = False
            self.sleep_origin = ""
        elif (not context.night and allow_nap and not self.sleeping
              and self.auto_nap_day != context.day_key):
            self.sleeping = True
            self.sleep_origin = "nap"
            self.nap_until = stamp + 45 * 60
            self.auto_nap_day = context.day_key

    def _decay(self, hours: float, context: TimeContext | None,
               effort: float | None = None) -> None:
        if self.sleeping:
            self.satiety = bounded(self.satiety - hours * 1.4)
            self.mood = bounded(self.mood + hours * 0.5)
            self.energy = bounded(self.energy + hours * 22.0)
            self.social = bounded(self.social - hours * 0.35)
            self.affection = bounded(self.affection - hours * 0.25)
            return
        # A relaxed rhythm; weekends are slightly gentler, no obligations.
        if context is None:
            satiety_rate, mood_rate, energy_rate = 3.0, -2.0, 2.2
        else:
            satiety_rate = 4.0 if context.meal is not None else 2.4
            mood_rate = (
                0.3 if context.weekend and context.period in ("free", "evening")
                else -0.4 if context.period == "quiet"
                else -0.9
            )
            energy_rate = (
                1.1 if context.weekend and context.period == "free"
                else 1.5 if context.period == "quiet"
                else 2.0
            )
        # CPU/GPU effort is *her* observed work. RAM use alone adds only
        # small pressure upstream. Missing telemetry means normal decay.
        intensity = 0.0 if effort is None else max(
            0.0, min(1.0, (effort - 0.15) / 0.85),
        )
        satiety_rate *= 1.0 + 0.95 * intensity
        mood_rate -= 2.1 * intensity
        energy_rate += 2.8 * intensity
        social_rate = 1.8 + 0.35 * intensity
        # Affection is emotional care, not CPU/GPU usage and not conversation.
        affection_rate = 1.35
        if self.social < 20:
            mood_rate -= 0.7
        if self.affection < 20:
            mood_rate -= 0.8
        self.satiety = bounded(self.satiety - hours * satiety_rate)
        self.mood = bounded(self.mood + hours * mood_rate)
        self.energy = bounded(self.energy - hours * energy_rate)
        self.social = bounded(self.social - hours * social_rate)
        self.affection = bounded(self.affection - hours * affection_rate)

    def advance(self, now: float, *, auto_routine: bool = False,
                allow_bedtime: bool | None = None,
                allow_nap: bool = False,
                interrupt_nap: bool = False,
                effort: float | None = None) -> None:
        """Catch up at most eight hours, including local day/night transitions.

        For old saves, plain time decay stays available. With a routine enabled,
        simulate the most recent eight hours in short intervals so time offline
        overnight does not behave like eight waking hours.
        """
        if not math.isfinite(now):
            return
        elapsed = max(0.0, min(MAX_CATCHUP_SECONDS, now - self.updated_at))
        if (type(effort) not in (int, float) or not math.isfinite(effort)
                or not 0.0 <= effort <= 1.0):
            effort = None
        known_since = now - min(elapsed, MAX_LIVE_EFFORT_SECONDS)
        if not auto_routine:
            if effort is None:
                self._decay(elapsed / 3600.0, None)
            else:
                unseen_seconds = max(0.0, known_since - (now - elapsed))
                self._decay(unseen_seconds / 3600.0, None)
                self._decay((now - known_since) / 3600.0, None, effort)
            self._roll_meals(context_at(now))
        else:
            cursor = now - elapsed
            while cursor < now:
                next_cursor = min(now, cursor + SIMULATION_STEP_SECONDS)
                if effort is not None and cursor < known_since < next_cursor:
                    next_cursor = known_since
                context = context_at((cursor + next_cursor) / 2)
                self._apply_clock(
                    context, allow_bedtime=allow_bedtime is not False,
                    allow_nap=allow_nap, interrupt_nap=interrupt_nap,
                )
                self._decay(
                    (next_cursor - cursor) / 3600, context,
                    effort if cursor >= known_since else None,
                )
                cursor = next_cursor
            self._apply_clock(
                context_at(now), allow_bedtime=allow_bedtime is not False,
                allow_nap=allow_nap,
            )
        self.updated_at = now

    def _credit_friendship(
        self, action: str, stamp: float, need_before: float,
    ) -> None:
        """Delegate relationship rewards without changing state semantics."""
        award_friendship_for_care(self, action, stamp, need_before)

    def interact(self, action: str, *, now: float | None = None) -> str:
        """Apply six distinct care effects; friendship rewards useful care."""
        stamp = time.time() if now is None else now
        if action == "sleep":
            self.sleeping = not self.sleeping
            self.sleep_origin = "manual" if self.sleeping else ""
            if not self.sleeping and context_at(stamp).night:
                self.auto_sleep_night = context_at(stamp).night_key
            return "Zzz ... gute Nacht." if self.sleeping else "Oh ... schon Morgen?"
        if action not in {"feed", "play", "pet", "talk", "energy_drink"}:
            raise ValueError(f"Unknown action: {action}")
        if action == "play" and self.energy < 8:
            return "Ich bin gerade zu müde zum Spielen."
        if action == "energy_drink" and self.energy >= 100:
            return "Ich bin schon voll. Mehr passt gerade nicht rein."
        if self.sleeping:
            self.sleeping = False
            self.sleep_origin = ""
            self.nap_until = 0.0
            context = context_at(stamp)
            if context.night:
                # Drinking/feeding at night shouldn't trigger auto-bedtime
                # again one GUI frame later.
                self.auto_sleep_night = context.night_key
        if action == "energy_drink":
            self.energy = bounded(self.energy + 10.0)
            return "...Oh. Das hat geholfen."
        need_before = getattr(self, CARE_PRIMARY_NEED[action])
        if action == "talk":
            self.social = bounded(self.social + 26)
            self.mood = bounded(self.mood + 5)
            self.energy = bounded(self.energy - 1)
            self._credit_friendship(action, stamp, need_before)
            return "...Du möchtest reden? Ich höre zu."
        if action == "feed":
            ctx = context_at(stamp)
            self._roll_meals(ctx)
            self.satiety = bounded(self.satiety + 27)
            self.social = bounded(self.social + 1)
            self._credit_friendship(action, stamp, need_before)
            if ctx.meal is not None and ctx.meal not in self.meals_today:
                self.meals_today.append(ctx.meal)
                self.mood = bounded(self.mood + 5)
                return f"Danke für das {MEAL_NAMES[ctx.meal].lower()}!"
            self.mood = bounded(self.mood + 3)
            return "Mhm ... ein kleiner Snack!"
        if action == "play":
            self.mood = bounded(self.mood + 23)
            self.energy = bounded(self.energy - 9)
            self.satiety = bounded(self.satiety - 4)
            self.social = bounded(self.social + 12)
            self._credit_friendship(action, stamp, need_before)
            return "Heh ... das war gut!"
        # Petting offers affection; it is neither a game nor an energy drink.
        self.affection = bounded(self.affection + 25)
        self.mood = bounded(self.mood + 6)
        self.social = bounded(self.social + 2)
        self._credit_friendship(action, stamp, need_before)
        return "... Das ist angenehm."

    def feed_label(self, context: TimeContext) -> str:
        if context.meal and (
            context.day_key != self.meals_date or context.meal not in self.meals_today
        ):
            return MEAL_NAMES[context.meal]
        return "Snack"

    def mood_hint(self, context: TimeContext | None = None) -> str:
        if self.sleeping:
            return "Aiko schläft gerade ... gute Nacht." if context and context.night else "Aiko ruht sich aus."
        if self.satiety < 20:
            return "Ein kleiner Snack wäre schön ..."
        if self.energy < 20:
            return "Ich könnte etwas Schlaf gebrauchen."
        if self.social < 20:
            return "...Etwas Gesellschaft wäre gerade schön."
        if self.affection < 20:
            return "...Eine kleine Geste wäre gerade schön."
        if self.mood < 20:
            return "Mir ist irgendwie langweilig ..."
        if context is not None:
            if context.meal and context.meal not in self.meals_today:
                return f"Es wäre Zeit für {MEAL_NAMES[context.meal].lower()}."
            if context.weekend:
                return "Heute geht alles etwas langsamer. Gut so."
            if context.night:
                return "Es ist schon spät ..."
            if context.period == "evening":
                return "Endlich ein gemütlicher Abend."
        if min(
            self.satiety, self.mood, self.energy, self.social, self.affection,
        ) > 85:
            return "Heute ist ein guter Tag."
        return "... Ich bin gern hier."
