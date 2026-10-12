"""Character-sheet-guided, offline speech and emotion rules for Aiko.

Every phrase is authored, not generated.  The dialogue book owns *what* may
be said, and AikoMind owns *when* an event is eligible to say something.
No Character-Chronicles story or outside-the-desktop commitments are modeled.
"""

from __future__ import annotations

import json
import random
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .adaptive import Behaviour
from .domain import PetState
from .routine import TimeContext
from .reaction_sequence import EMOTES
from .system_activity import ComputerSnapshot

CATALOGUE = Path(__file__).resolve().parent / "data" / "dialogues.de.json"
ANIMATIONS = frozenset({"idle", "waiting", "review", "failed", "waving", "jumping"})
EMOTIONS = frozenset({
    "asleep", "irritated", "tired", "hungry", "withdrawn", "warm", "playful", "calm",
    "lonely", "seeking_affection",
})
PERIODS = frozenset({"night", "breakfast", "quiet", "lunch", "free", "dinner", "evening"})

EMOTION_LABELS = {
    "asleep": "Schläfrig",
    "irritated": "Gereizt",
    "tired": "Müde",
    "hungry": "Hungrig",
    "withdrawn": "Nachdenklich",
    "warm": "Zugewandt",
    "playful": "Verspielt",
    "calm": "Gelassen",
    "lonely": "Vermisst Gesellschaft",
    "seeking_affection": "Wünscht Zuwendung",
}


@dataclass(frozen=True)
class Line:
    id: str
    event: str
    text: str
    animation: str
    moods: tuple[str, ...]
    periods: tuple[str, ...]
    weekdays: tuple[int, ...]
    weight: int
    cooldown_seconds: float
    followup_text: str | None = None
    followup_delay_ms: int = 1400
    emote_before: str | None = None
    emote_after: str | None = None

    @classmethod
    def parse(cls, raw: Any) -> Line:
        if not isinstance(raw, dict):
            raise ValueError("A dialogue line must be an object")
        required = ("id", "event", "text", "animation", "moods", "periods", "weekdays")
        if any(key not in raw for key in required):
            raise ValueError("Incomplete dialogue line")
        for key in ("id", "event", "text", "animation"):
            if not isinstance(raw[key], str) or not raw[key].strip():
                raise ValueError(f"Invalid dialogue {key}")
        if not 1 <= len(raw["text"]) <= 125:
            raise ValueError("Dialogue line is too long")
        if raw["animation"] not in ANIMATIONS:
            raise ValueError("No matching physical sprite animation")
        for key in ("moods", "periods", "weekdays"):
            if not isinstance(raw[key], list):
                raise ValueError(f"Invalid dialogue {key}")
        moods, periods, weekdays = raw["moods"], raw["periods"], raw["weekdays"]
        if any(m not in EMOTIONS for m in moods):
            raise ValueError("Unknown emotion")
        if any(p not in PERIODS for p in periods):
            raise ValueError("Unknown day period")
        if any(type(day) is not int or not 0 <= day <= 6 for day in weekdays):
            raise ValueError("Invalid weekday")
        weight = raw.get("weight", 1)
        cooldown = raw.get("cooldown_seconds", 120)
        if type(weight) is not int or not 1 <= weight <= 10:
            raise ValueError("Invalid line weight")
        if type(cooldown) not in (int, float) or not 0 <= cooldown <= 86400:
            raise ValueError("Invalid cooldown")
        followup = raw.get("followup_text")
        delay = raw.get("followup_delay_ms", 1400)
        if followup is not None and (
            not isinstance(followup, str) or not 1 <= len(followup) <= 125
        ):
            raise ValueError("Invalid follow-up text")
        if type(delay) is not int or not 600 <= delay <= 2600:
            raise ValueError("Invalid follow-up timing")
        before = raw.get("emote_before")
        after = raw.get("emote_after")
        if any(emote is not None and (
            not isinstance(emote, str) or emote not in EMOTES
        ) for emote in (before, after)):
            raise ValueError("Unknown or unavailable emote")
        return cls(
            id=raw["id"], event=raw["event"], text=raw["text"],
            animation=raw["animation"], moods=tuple(moods),
            periods=tuple(periods), weekdays=tuple(weekdays),
            weight=weight, cooldown_seconds=float(cooldown),
            followup_text=followup, followup_delay_ms=delay,
            emote_before=before, emote_after=after,
        )

    def matches(self, emotion: str, context: TimeContext) -> bool:
        return (
            (not self.moods or emotion in self.moods)
            and (not self.periods or context.period in self.periods)
            and (not self.weekdays or context.local.weekday() in self.weekdays)
        )

    def score(self, emotion: str, context: TimeContext) -> int:
        """Relevant, specific entries win more often than generic fallbacks."""
        return self.weight * (
            1 + 2 * bool(self.moods and emotion in self.moods)
            + 2 * bool(self.periods and context.period in self.periods)
            + 2 * bool(self.weekdays and context.local.weekday() in self.weekdays)
        )


@dataclass(frozen=True)
class Reaction:
    """An actual available animation plus a short German speech bubble."""

    line_id: str
    text: str
    animation: str
    event: str
    followup_text: str | None = None
    followup_delay_ms: int = 1400
    emote_before: str | None = None
    emote_after: str | None = None


class DialogueBook:
    """Filtered weighted rotation with no immediate repeats or rapid spam."""

    def __init__(self, lines: tuple[Line, ...], *, rng: random.Random | None = None):
        if len({line.id for line in lines}) != len(lines):
            raise ValueError("Duplicate dialogue IDs")
        if not lines:
            raise ValueError("Empty dialogue book")
        self.lines = lines
        self.rng = rng or random.Random()
        self.last_used: dict[str, float] = {}
        self.recent: deque[str] = deque(maxlen=6)

    @classmethod
    def from_file(cls, file: Path = CATALOGUE, *, rng: random.Random | None = None) -> DialogueBook:
        data = json.loads(file.read_text(encoding="utf-8"))
        if data.get("catalogue_version") != 1 or data.get("language") != "de":
            raise ValueError("Unsupported dialogue catalogue version")
        if not isinstance(data.get("lines"), list):
            raise ValueError("Dialogue book has no lines")
        return cls(tuple(Line.parse(item) for item in data["lines"]), rng=rng)

    def choose(
        self, event: str, emotion: str, context: TimeContext, now: float,
    ) -> Reaction | None:
        candidates = [line for line in self.lines if line.event == event and line.matches(emotion, context)]
        if not candidates:
            return None
        fresh = [
            line for line in candidates
            if line.id not in self.recent
            and now - self.last_used.get(line.id, float("-inf")) >= line.cooldown_seconds
        ]
        if not fresh:
            fresh = [line for line in candidates if line.id not in self.recent]
        if not fresh:
            fresh = [line for line in candidates if line.id != (self.recent[-1] if self.recent else "")]
        if not fresh:
            fresh = candidates
        weights = [line.score(emotion, context) for line in fresh]
        line = self.rng.choices(fresh, weights=weights, k=1)[0]
        self.last_used[line.id] = now
        self.recent.append(line.id)
        return Reaction(
            line.id, line.text, line.animation, event,
            line.followup_text, line.followup_delay_ms,
            line.emote_before, line.emote_after,
        )


class AikoMind:
    """Situational reactions with a short, decaying social memory.

    Aiko is the personification of this computer, not a technical narrator.
    Load is *her* effort; the same click can mean something different after
    work, in a quiet evening, or during an interrupted calculation.
    """

    RETURN_AFTER_SECONDS = 25 * 60
    CLICK_WINDOW_SECONDS = 7.5
    MAX_CLICKS_IN_BURST = 20

    def __init__(
        self, book: DialogueBook | None = None, *,
        rng: random.Random | None = None, started_at: float = 0.0,
    ) -> None:
        self.rng = rng or random.Random()
        self.book = book or DialogueBook.from_file(rng=self.rng)
        self.clicks: deque[float] = deque(maxlen=self.MAX_CLICKS_IN_BURST)
        self.irritated_until = -1.0
        self.warm_until = -1.0
        self.last_contact = started_at
        self.situation: Behaviour | None = None
        self._work_interruptions = 0
        self._last_work_duration = 0.0
        self._recovery_until = -1.0
        self._last_recovery_comment = -1.0
        self._last_work_finished_at = -1.0
        self._postwork_thought_spoken = False
        self._last_care_action = ""
        self._last_care_at = -1.0
        self._last_social_comment = float("-inf")
        self._last_affection_comment = float("-inf")

    def set_situation(self, situation: Behaviour | None, *, now: float | None = None) -> None:
        """Remember an observed work session, never infer unseen work."""
        previous = self.situation
        self.situation = situation
        if situation is None:
            self._work_interruptions = 0
            self._recovery_until = -1.0
        elif previous is not None and previous.focused and not situation.focused:
            self._last_work_duration = previous.prolonged_work_seconds
            if now is not None:
                self._recovery_until = now + 110.0
                self._last_work_finished_at = now
                self._postwork_thought_spoken = False
        elif previous is not None and not previous.focused and situation.focused:
            # New work, new episode. Old clicks cannot count as interruptions.
            self._work_interruptions = 0
            self._recovery_until = -1.0
            self._postwork_thought_spoken = False

    def emotion(self, state: PetState, now: float) -> str:
        if state.sleeping:
            return "asleep"
        if now < self.irritated_until:
            return "irritated"
        if self.situation is not None and self.situation.strain >= 75 and state.energy <= 55:
            return "tired"
        if self.situation is not None and self.situation.strain >= 60 and state.mood <= 48:
            return "withdrawn"
        if state.energy <= 25:
            return "tired"
        if state.satiety <= 25:
            return "hungry"
        if state.mood <= 28:
            return "withdrawn"
        if state.social <= 23:
            return "lonely"
        if state.affection <= 23:
            return "seeking_affection"
        if now < self.warm_until:
            return "warm"
        if state.mood >= 82 and state.energy >= 45:
            return "playful"
        return "calm"

    def say_event(
        self, event: str, state: PetState, context: TimeContext, now: float,
        *, tone: str | None = None,
    ) -> Reaction | None:
        return self.book.choose(event, tone or self.emotion(state, now), context, now)

    def click(
        self, button: str, state: PetState, context: TimeContext, now: float,
    ) -> Reaction | None:
        if button not in ("left", "right"):
            raise ValueError("Unknown mouse button")
        self.last_contact = now
        if self.clicks and now - self.clicks[-1] > self.CLICK_WINDOW_SECONDS:
            self.clicks.clear()
        self.clicks.append(now)
        count = len(self.clicks)
        if state.sleeping:
            return self.say_event("sleep_click", state, context, now)

        busy = self.situation is not None and self.situation.focused
        cheerful = state.mood >= 82 and state.energy >= 45 and not busy
        withdrawn = state.mood <= 28 and not busy
        tired = state.energy <= 26 or (
            self.situation is not None and self.situation.strain >= 72
        )
        if busy:
            self._work_interruptions += 1
            if count <= 2:
                event = "click_during_work"
            elif count <= 4:
                event = "click_work_repeat"
            elif count <= 6:
                event = "click_work_boundary"
            elif count == 7:
                event = "click_last_word"
            else:
                return None  # Not every provocation deserves a speech bubble.
        elif count == 1 and now < self._recovery_until:
            event = "click_after_work"
        elif count <= 2:
            if withdrawn:
                event = "click_withdrawn"
            elif tired:
                event = "click_sleepy"
            elif self._last_care_action == "pet" and now - self._last_care_at < 50:
                event = "click_flustered"
            elif state.social <= 23:
                event = "click_lonely"
            elif state.affection <= 23:
                event = "click_affection_low"
            elif context.night and not cheerful:
                event = "click_night"
            elif (state.friendship >= 72 and state.mood >= 60
                  and state.affection >= 40):
                event = "click_close"
            elif (state.affection >= 85 and state.friendship >= 40
                  and state.mood >= 60):
                event = "click_at_ease"
            elif state.friendship < 12:
                event = "click_reserved"
            else:
                event = "click_left" if button == "left" else "click_right"
        elif count == 3:
            event = ("click_notice_playful" if cheerful else
                     "click_notice_withdrawn" if withdrawn else "click_notice")
        elif count <= 5:
            event = ("click_tease" if cheerful else
                     "click_withdrawn_boundary" if withdrawn else
                     "click_weary" if tired else "rapid_click")
        elif withdrawn and count >= 7:
            return None
        elif withdrawn and count == 6:
            event = "click_last_word"
        elif count <= 7:
            event = "click_tease_more" if cheerful else "click_boundary"
        elif count == 8:
            event = "click_last_word"
        else:
            return None
        if count >= 4 and not cheerful:
            self.irritated_until = max(self.irritated_until, now + 13.0)
        return self.say_event(event, state, context, now)

    def care_event(
        self, action: str, state: PetState, context: TimeContext, now: float,
    ) -> tuple[str, str]:
        """Return an event and the PRE-action tone of the care interaction."""
        self.last_contact = now
        tone = self.emotion(state, now)
        if action == "feed":
            if state.satiety >= 95:
                return "feed_full", tone
            if context.meal and (
                context.day_key != state.meals_date or context.meal not in state.meals_today
            ):
                return "feed_meal", tone
            return "feed_snack", tone
        if action == "play":
            if state.energy < 8:
                return "play_tired", tone
            return ("play_close" if state.friendship >= 72 else "play"), tone
        if action == "talk":
            if self.situation is not None and self.situation.focused:
                return "talk_busy", tone
            if state.social <= 27:
                return "talk_lonely", tone
            return ("talk_close" if state.friendship >= 72 else "talk"), tone
        if action == "energy_drink":
            return ("energy_drink_full" if state.energy >= 100
                    else "energy_drink"), tone
        if action == "sleep":
            return ("wake" if state.sleeping else "sleep"), tone
        if action == "pet":
            if self.situation is not None and self.situation.focused:
                return "pet_during_work", tone
            if state.affection <= 24:
                return "pet_needs_affection", tone
            return ("pet_close" if state.friendship >= 72 else "pet"), tone
        raise ValueError(f"Unknown care event: {action}")

    def after_care(self, action: str, now: float) -> None:
        self._last_care_action = action
        self._last_care_at = now
        if action in ("pet", "feed", "play", "talk"):
            self.warm_until = now + (70 if action == "pet" else 45)
        if action == "sleep":
            self.irritated_until = -1.0
            self.clicks.clear()

    def computer_event(
        self, event: str, state: PetState, context: TimeContext, now: float,
    ) -> Reaction | None:
        """Interpret meaningful work transitions in the lived context."""
        situation = self.situation
        if event in ("computer_effort_rising", "computer_effort_heavy",
                     "computer_effort_peak") and situation is not None:
            if (situation.expectation_confident
                    and situation.expected_effort is not None
                    and situation.expected_effort < 0.3
                    and (situation.effort or 0.0) >= 0.5):
                event = "work_unexpected"
        if event.startswith("computer_effort_recovered"):
            if self._work_interruptions >= 2 and self._last_work_duration >= 18:
                event = "work_finished_interrupted"
            elif self._last_work_duration >= 20 * 60:
                event = "work_finished_long"
            self._recovery_until = now + 110.0
            self._last_recovery_comment = now
            self._last_work_finished_at = now
            self._postwork_thought_spoken = False
            self._work_interruptions = 0
        if event == "computer_uptime":
            event = "computer_uptime_grounded"
        return self.say_event(event, state, context, now)

    def return_to_pet(
        self, state: PetState, context: TimeContext, now: float,
    ) -> Reaction | None:
        elapsed = now - self.last_contact
        self.last_contact = now
        if state.sleeping or elapsed < self.RETURN_AFTER_SECONDS:
            return None
        if self.situation is not None and self.situation.focused:
            event = "return_working"
        elif now < self._recovery_until:
            event = "return_after_work"
        else:
            event = "return_close" if state.friendship >= 72 else "return"
        return self.say_event(event, state, context, now)

    def spontaneous_event(
        self, state: PetState, context: TimeContext, now: float,
    ) -> Reaction | None:
        """Choose an observed situation; no imagined apps or off-screen story."""
        if state.sleeping:
            return None
        tone = self.emotion(state, now)
        situation = self.situation
        if tone == "hungry":
            event = "hungry"
        elif tone == "lonely" and not (situation and situation.focused):
            # Missing company matters, but a permanently running PC must not
            # nag the user every five minutes for social attention.
            if now - self._last_social_comment >= 20 * 60:
                event = "social_low"
                self._last_social_comment = now
            else:
                event = "idle"
        elif tone == "seeking_affection" and not (situation and situation.focused):
            # A need for reassurance is distinct from wanting to talk.
            if now - self._last_affection_comment >= 25 * 60:
                event = "affection_low"
                self._last_affection_comment = now
            else:
                event = "idle"
        elif tone == "tired" and not (situation and situation.focused):
            event = "tired"
        elif situation is not None and situation.focused:
            if context.night and (situation.strain >= 35 or state.energy <= 45):
                event = "work_late"
            elif situation.prolonged_work_seconds >= 20 * 60:
                event = "work_long_thought"
            else:
                event = "work_concentrating"
        elif (situation is not None and self._last_work_duration >= 20 * 60
              and not self._postwork_thought_spoken
              and 60 <= now - self._last_work_finished_at <= 480):
            event = "after_work_thought"
            self._postwork_thought_spoken = True
        elif situation is not None and situation.mode == "resting":
            event = "quiet_alone" if situation.present is False else "quiet_together"
        elif tone in ("withdrawn", "irritated"):
            event = "low_mood"
        else:
            events = ["idle", "idle", "idle", "idle"]
            if state.friendship >= 78 and state.mood >= 55:
                events.append("close_thought")
            if context.period in ("breakfast", "quiet"):
                events.append("morning")
            if context.period == "lunch":
                events.append("midday")
            if context.period == "evening":
                events.append("evening")
            if context.night:
                events.append("night")
            if context.weekend:
                events.append("weekend")
            if context.local.weekday() == 0:
                events.append("monday")
            if context.local.weekday() == 4:
                events.append("friday")
            event = self.rng.choice(events)
        return self.say_event(event, state, context, now)


class ComputerVoice:
    """Translate measured effort into Aiko's *subjective* working rhythm.

    CPU/GPU/RAM are inputs only. Speech never identifies a component or an
    imagined task. A proper 'that was hard' response requires sustained load.
    """

    MIN_SECONDS_BETWEEN = 370.0
    MIN_CHANGE_SECONDS = 18.0
    STRESS_SECONDS = 18.0

    def __init__(self, *, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.last_voice_at = float("-inf")
        self.last_change_at = float("-inf")
        self._last_sample: ComputerSnapshot | None = None
        self._stressed_since: float | None = None
        self._peak_effort = 0.0
        self._milestone_spoken = False
        self._last_high_at: float | None = None

    def reset_samples(self) -> None:
        self._last_sample = None
        self._stressed_since = None
        self._peak_effort = 0.0
        self._milestone_spoken = False
        self._last_high_at = None

    def observe_change(self, snapshot: ComputerSnapshot, now: float) -> str | None:
        """Emit meaningful transitions only once per fresh hardware reading."""
        from .system_activity import workload_intensity

        if snapshot.measured_at <= 0 or now - snapshot.measured_at > 25:
            return None
        previous = self._last_sample
        if previous is not None and snapshot.measured_at <= previous.measured_at:
            return None
        self._last_sample = snapshot
        current = workload_intensity(snapshot)
        if current is None:
            self._stressed_since = None
            self._peak_effort = 0.0
            self._milestone_spoken = False
            self._last_high_at = None
            return None
        before = workload_intensity(previous) if previous is not None else None
        event: str | None = None
        if current >= 0.70:
            self._last_high_at = now
            if self._stressed_since is None:
                self._stressed_since = now
                self._peak_effort = current
                self._milestone_spoken = False
            self._peak_effort = max(self._peak_effort, current)
            duration = now - self._stressed_since
            if duration >= self.STRESS_SECONDS and not self._milestone_spoken:
                self._milestone_spoken = True
                event = ("computer_effort_peak" if self._peak_effort >= 0.90
                         else "computer_effort_heavy")
        elif self._stressed_since is not None:
            duration = now - self._stressed_since
            was_recent = (
                self._last_high_at is not None
                and now - self._last_high_at <= 90
            )
            if current < 0.42 and duration >= self.STRESS_SECONDS and was_recent:
                event = ("computer_effort_recovered_peak"
                         if self._peak_effort >= 0.90
                         else "computer_effort_recovered")
            elif current < 0.42 and duration >= 7:
                event = "computer_effort_easing"
            if current < 0.42 or not was_recent:
                self._stressed_since = None
                self._peak_effort = 0.0
                self._milestone_spoken = False
                self._last_high_at = None
        if event is None and before is not None:
            if current - before >= 0.23 and current >= 0.32:
                event = "computer_effort_rising"
            elif before - current >= 0.27 and current < 0.55:
                event = "computer_effort_easing"
        elif event is None and before is None and current >= 0.70:
            event = "computer_effort_rising"
        if event is None:
            return None
        # Recovery after hard work is a meaningful ending, even if her earlier
        # remark was recent. All other transitions respect the quiet period.
        recovery = event.startswith("computer_effort_recovered")
        if not recovery and now - self.last_change_at < self.MIN_CHANGE_SECONDS:
            return None
        self.last_change_at = now
        return event

    @staticmethod
    def classify(snapshot: "ComputerSnapshot") -> str | None:
        from .system_activity import ComputerSnapshot, workload_intensity
        if not isinstance(snapshot, ComputerSnapshot):
            return None
        effort = workload_intensity(snapshot)
        if effort is None:
            return None
        if effort >= 0.70:
            return "computer_effort_steady"
        if effort <= 0.20:
            return "computer_effort_rest"
        if snapshot.uptime_hours is not None and snapshot.uptime_hours >= 8:
            return "computer_uptime"
        return None

    def maybe_event(self, snapshot: "ComputerSnapshot", now: float) -> str | None:
        if now - max(self.last_voice_at, self.last_change_at) < self.MIN_SECONDS_BETWEEN:
            return None
        if snapshot.measured_at <= 0 or now - snapshot.measured_at > 65:
            return None
        event = self.classify(snapshot)
        if event is None:
            return None
        if event == "computer_effort_rest" and (snapshot.uptime_hours or 0) >= 8:
            if self.rng.random() < 0.18:
                event = "computer_uptime"
        if self.rng.random() >= (0.56 if event == "computer_effort_steady" else 0.25):
            return None
        self.last_voice_at = now
        return event
