"""Legacy routine imports, backed by the canonical pet time model."""

from __future__ import annotations

from .pet.routine import (
    WEEKDAYS as WEEKDAYS,
    WEEKDAY_SLOTS as WEEKDAY_SLOTS,
    WEEKEND_SLOTS as WEEKEND_SLOTS,
    SUNDAY_SLOTS as SUNDAY_SLOTS,
    MEAL_NAMES as MEAL_NAMES,
    TimeContext as TimeContext,
    context_at as context_at,
    slots_for_day as slots_for_day,
)
