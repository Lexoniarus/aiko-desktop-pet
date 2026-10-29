"""Read-only, versioned gameplay parameters, separate from transition rules."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .balance_contract import BALANCE_FIELDS
from .catalog_validation import load_json, object_fields


@dataclass(frozen=True, slots=True)
class BalanceCatalog:
    sections: Mapping[str, Mapping[str, int | float]]

    def number(self, section: str, key: str) -> float:
        return float(self.sections[section][key])

    def integer(self, section: str, key: str) -> int:
        value = self.sections[section][key]
        if type(value) is not int:
            raise ValueError(f"{section}.{key} must be an integer")
        return value


def parse_balance(raw: Any) -> BalanceCatalog:
    data = object_fields(raw, ("version", *BALANCE_FIELDS), context="balance")
    if type(data["version"]) is not int or data["version"] != 1:
        raise ValueError("Unsupported balance version")
    sections: dict[str, Mapping[str, int | float]] = {}
    for section, fields in BALANCE_FIELDS.items():
        row = object_fields(data[section], fields, context=f"balance.{section}")
        values: dict[str, int | float] = {}
        for key, kind in fields.items():
            value = row[key]
            if (
                type(value) not in (int, float)
                or (kind == "integer" and type(value) is not int)
                or not math.isfinite(value)
                or not 0 <= value <= 10_000_000
            ):
                raise ValueError(f"Invalid balance.{section}.{key}")
            normalized_weight = (section == "mood" and key.endswith("_weight")) or (
                section,
                key,
            ) == ("food_activity", "short_window_weight")
            if ("fraction" in key or normalized_weight) and value > 1:
                raise ValueError(f"balance.{section}.{key} must be within 0..1")
            if key.endswith(("_probability", "_effort", "_decay")) and value > 1:
                raise ValueError(f"balance.{section}.{key} must be within 0..1")
            if section == "initial" and value > 100:
                raise ValueError(f"balance.{section}.{key} must be within 0..100")
            values[key] = value
        for key, value in values.items():
            upper = key.replace("_minimum_", "_maximum_")
            if upper != key and upper in values and value > values[upper]:
                raise ValueError(f"balance.{section}: {key} exceeds {upper}")
        sections[section] = MappingProxyType(values)
    catalog = BalanceCatalog(MappingProxyType(sections))
    if any(value <= 0 for key, value in sections["idle_behaviour"].items()
           if not key.endswith("_probability")):
        raise ValueError("Idle behaviour requires positive durations and cadence")
    if (catalog.integer("ambient", "body_glance_every") < 1
            or catalog.integer("ambient", "body_outing_every") < 1
            or catalog.number("ambient", "body_hold_minimum_seconds") <= 0):
        raise ValueError("Invalid ambient body hold balance")
    if not (0 < catalog.number("emotions", "subdued_below_mood")
            < catalog.number("emotions", "satisfied_at_mood") <= 100):
        raise ValueError("Invalid emotional base thresholds")
    if not (0 < catalog.number("emotions", "long_term_modifier_cap")
            < catalog.number("emotions", "noticeable_modifier_intensity") <= 3):
        raise ValueError("Invalid emotional modifier balance")
    sleep = sections["sleep"]
    if (any(value <= 0 for key, value in sleep.items()
            if key not in ("default_start_minute", "default_end_minute"))
            or not 3600 <= sleep["nap_seconds"] <= 5400
            or not 0 <= sleep["default_start_minute"] < 1440
            or not 0 <= sleep["default_end_minute"] < 1440
            or not sleep["minimum_phase_seconds"] <= (
                sleep["default_end_minute"] - sleep["default_start_minute"]
            ) % 1440 * 60 <= sleep["maximum_phase_seconds"] <= 86400
            or sleep["portion_seconds"] > sleep["search_seconds"]
            or not 2 <= sleep["minimum_input_events"] <= 128
            or not 0 < sleep["nap_wake_energy"] <= sleep["wake_energy"]
            or not sleep["exhaustion_energy"] < sleep["nap_energy"]
            < sleep["wake_energy"] <= sleep["early_main_energy"] <= 100
            or not sleep["food_trigger"] < sleep["food_target"] <= 100
            or not 2 <= sleep["tendency_phases"] < sleep["learned_phases"] <= 7
            or sleep["maximum_daily_shift_minutes"] > 30
            or sleep["sample_gap_seconds"] > 60
            or sleep["input_gap_seconds"] > sleep["return_seconds"]):
        raise ValueError("Invalid sleep priorities or quiet-window balance")
    withholding = sections["object_withholding"]
    if (any(value <= 0 for value in withholding.values())
            or withholding["friendship_loss"] > 100
            or withholding["request_interval_seconds"] > withholding["grace_seconds"]
            or withholding["request_interval_seconds"]
            > withholding["loss_interval_seconds"]):
        raise ValueError("Invalid object withholding balance")
    relationship = sections["friendship"]
    thresholds = [relationship[key] for key in (
        "mood_negative_floor", "mood_neutral_low", "mood_neutral_high",
        "mood_positive_ceiling",
    )]
    positive_factors = [relationship[f"positive_{name}_factor"]
                        for name in ("zero", "lower", "middle", "higher", "peak")]
    if (not 0 <= thresholds[0] < thresholds[1] <= thresholds[2]
            < thresholds[3] <= 100
            or any(a < b for a, b in zip(positive_factors, positive_factors[1:]))
            or sections["simulation"]["status_interval_seconds"] <= 0):
        raise ValueError("Invalid continuous relationship thresholds or cadence")
    points = [0., *(relationship[f"{name}_points"]
                    for name in ("lower", "middle", "higher", "peak")), 100.]
    factors = [relationship[f"{name}_factor"]
               for name in ("zero", "lower", "middle", "higher", "peak")]
    times = [relationship[f"absence_{name}_seconds"]
             for name in ("grace", "middle", "long", "extended")]
    if (any(a >= b for a, b in zip(points, points[1:]))
            or any(a > b for a, b in zip(factors, factors[1:]))
            or any(a >= b for a, b in zip(times, times[1:]))
            or any(value <= 0 for value in relationship.values())
            or not relationship["short_cap"] <= relationship["daily_cap"] <= 100
            or relationship["short_window_seconds"]
            > relationship["history_window_seconds"]
            or not 15 <= relationship["history_bucket_seconds"] <= 60
            or relationship["history_window_seconds"]
            % relationship["history_bucket_seconds"]
            or not (relationship["zero_allowance_seconds"]
                    <= relationship["critical_allowance_seconds"]
                    < relationship["strong_neglect_seconds"]
                    <= relationship["history_window_seconds"])
            or relationship["critical_need"] > 100
            or relationship["click_loss"] > relationship["click_cap"]
            or withholding["friendship_loss"] > relationship["withholding_cap"]):
        raise ValueError("Invalid progressive friendship balance")
    objects = sections["object_behavior"]
    wishes = sections["wishes"]
    if (any(value <= 0 for value in wishes.values())
            or wishes["maximum_active"] != 3
            or not 1 <= wishes["disclosure_friendship_level"] <= 10
            or wishes["disclosure_mood_threshold"] > 100
            or not wishes["need_low_threshold"] < wishes["need_medium_threshold"]
            < wishes["need_high_threshold"] <= 100
            or not wishes["area_weight_satisfied"] <= wishes["area_weight_moderate"]
            <= wishes["area_weight_low"] <= wishes["area_weight_critical"]
            or wishes["refill_delay_seconds"] > wishes["lifetime_seconds"]
            or wishes["disclosure_interval_seconds"] > wishes["lifetime_seconds"]):
        raise ValueError("Invalid wish pacing or disclosure")
    impressions = sections["moodlets"]
    critical = [impressions[f"critical_level_{name}_seconds"]
                for name in ("one", "two", "three")]
    zero = [impressions[f"zero_level_{name}_seconds"]
            for name in ("one", "two", "three")]
    if (any(value <= 0 for value in impressions.values())
            or max(impressions["positive_level_one_seconds"],
                   impressions["positive_upper_stage_seconds"],
                   impressions["positive_renewal_seconds"])
            > impressions["positive_stage_cap_seconds"]
            or any(value > 100 for key, value in impressions.items()
                   if key.endswith("_points"))
            or impressions["game_wish_cap_points"] > impressions["positive_cap_points"]
            or impressions["social_wish_cap_points"]
            > impressions["positive_cap_points"]
            or impressions["poor_care_cap_points"] > impressions["negative_cap_points"]
            or not relationship["critical_need"]
            <= impressions["recovery_need_threshold"] <= 100
            or any(a >= b for a, b in zip(critical, critical[1:]))
            or any(a >= b for a, b in zip(zero, zero[1:]))
            or any(a > b for a, b in zip(zero, critical))
            or critical[-1] > relationship["history_window_seconds"]):
        raise ValueError("Invalid Moodlet caps or poor-care recovery balance")
    if (
        objects["reach_widths"] >= objects["notice_widths"]
        or objects["notice_seconds"] > objects["recognize_seconds"]
        or objects["notice_seconds"] > objects["absence_seconds"]
        or objects["notice_seconds"] > objects["presentation_seconds"]
        or objects["presentation_jitter_widths"] >= min(
            objects["presentation_horizontal_widths"],
            objects["presentation_vertical_widths"],
        )
        or objects["seek_food_satiety"] > 100
        or objects["seek_drink_energy"] > 100
        or objects["bounce_restitution_fraction"] >= 1
        or objects["bounce_horizontal_damping_fraction"] >= 1
        or objects["bounce_maximum_contacts"] > 32
        or any(value <= 0 for value in objects.values())
    ):
        raise ValueError("Invalid object perception/interest balance")
    for section, low, high in (
        ("walk", "pause_min_seconds", "pause_max_seconds"),
        ("walk", "quiet_pause_min_seconds", "pause_max_seconds"),
        ("walk", "minimum_cycles", "maximum_cycles"),
        ("fun", "full_reward_units_per_session", "middle_reward_units_per_session"),
        ("food_activity", "short_window_minutes", "long_window_minutes"),
    ):
        if catalog.number(section, low) > catalog.number(section, high):
            raise ValueError(f"balance.{section}: {low} exceeds {high}")
    for section, key in (
        ("food", "digest_minutes_for_full_hunger_reduction"),
        ("food", "maximum_recent_foods"),
        ("food", "consecutive_repeats_before_dislike"),
        ("food_activity", "bucket_seconds"),
        ("food_activity", "short_window_minutes"),
        ("food_activity", "long_window_minutes"),
        ("simulation", "needs_step_seconds"),
        ("needs", "hardware_intensity_span"),
        ("adaptive_learning", "effort_smoothing_seconds"),
        ("walk", "minimum_cycles"),
    ):
        if catalog.number(section, key) <= 0:
            raise ValueError(f"balance.{section}.{key} must be positive")
    dialogue = sections["dialogue"]
    if (
        not 1 <= dialogue["default_weight"] <= 10
        or dialogue["default_cooldown_seconds"] > 86400
        or dialogue["recent_line_history"] < 1
        or not 250 <= dialogue["minimum_text_ms"] <= dialogue["maximum_text_ms"] <= 8000
        or any(
            not 250 <= dialogue[key] <= 8000
            for key in (
                "emote_ms",
                "pause_ms",
                "contact_reaction_ms",
                "greeting_reaction_ms",
            )
        )
    ):
        raise ValueError("Invalid dialogue defaults or presentation timing")
    if (
        not 250 <= dialogue["conversation_minimum_text_ms"]
        <= dialogue["conversation_maximum_text_ms"] <= 10000
        or dialogue["conversation_orientation_ms"] > 10000
        or dialogue["conversation_reading_ms_per_character"] <= 0
        or dialogue["conversation_final_text_ms"] > 10000
        or not 250 <= dialogue["conversation_punchline_pause_ms"] <= 8000
    ):
        raise ValueError("Invalid conversation reading timing")
    mood = sections["mood"]
    names = ("zero", "critical", "low", "healthy")
    thresholds = [mood[f"{name}_need_threshold"] for name in names]
    deductions = [mood[f"{name}_need_deduction"] for name in names]
    limits = [mood[f"{name}_need_target_limit"] for name in names]
    declines = [mood[f"{name}_decline_points_per_minute"] for name in names]
    if (not 0 < mood["need_weight"] <= 0.2
            or thresholds[0] != 0 or thresholds[-1] > 100
            or any(a >= b for a, b in zip(thresholds, thresholds[1:]))
            or deductions[-1] != 0 or deductions[0] > 100
            or any(a < b for a, b in zip(deductions, deductions[1:]))
            or limits[-1] != 100 or limits[0] > 100
            or any(a > b for a, b in zip(limits, limits[1:]))
            or declines[-1] <= 0
            or any(a < b for a, b in zip(declines, declines[1:]))
            or mood["recovery_points_per_minute"] <= 0):
        raise ValueError("Invalid mood curve or response rates")
    if catalog.number("simulation", "needs_step_seconds") > 60:
        raise ValueError("Need integration steps must not exceed one minute")
    if not math.isclose(
        catalog.number("needs", "hardware_intensity_baseline")
        + catalog.number("needs", "hardware_intensity_span"), 1.0,
    ):
        raise ValueError("Hardware threshold and span must cover 0..1")
    food = sections["food"]
    for key in ("maximum_combined_activity_bonus", "maximum_hardware_hunger_bonus",
                "maximum_user_input_hunger_bonus", "maximum_digest_hunger_reduction"):
        if food[key] > 1:
            raise ValueError(f"balance.food.{key} must be within 0..1")
    if catalog.number("fun", "high_fun_threshold") >= 100:
        raise ValueError("High-fun reduction must start below 100")
    cursor = sections["cursor_behaviour"]
    if (not 0 < cursor["velocity_filter_seconds"] <= 1
            or not 0 < cursor["stationary_override_seconds"] <= 1
            or not 0 < cursor["slow_speed"] < cursor["attention_fast_speed"]
            < cursor["very_fast_speed"]
            or not 0 < cursor["gaze_release_below"] < cursor["noticed_at"]
            < cursor["far_attention_cap"] < cursor["body_release_below"]
            < cursor["focused_at"] < cursor["strong_release_below"]
            < cursor["strong_at"] <= 100
            or not 0 < cursor["side_required_seconds"] <= cursor["side_window_seconds"]
            or not 0 < cursor["warning_candidate_seconds"]
            < cursor["warning_window_seconds"] < cursor["warning_repeat_seconds"]
            or not 0 < cursor["curiosity_level_two_seconds"]
            < cursor["curiosity_level_three_seconds"]
            or not 0 < cursor["play_grace_seconds"] < cursor["play_attempt_seconds"]
            or not 0 < cursor["play_pause_seconds"] < cursor["play_attempt_seconds"]
            or not 0 < cursor["run_release_distance"] < cursor["run_distance"]
            or not 0 <= cursor["playful_minimum_mood"] <= 100
            or not 0 < cursor["playful_score"] <= 100
            or not 0 < cursor["playful_friendship_weight"] <= 10
            or not 0 < cursor["curiosity_refresh_seconds"]
            or not 250 <= cursor["warning_duration_ms"] <= 8000
            or any(cursor[k] <= 0 for k in (
                "normal_gain", "fast_gain", "very_fast_gain", "slow_loss_per_second",
                "still_loss_per_second", "release_hold_seconds",
                "opposite_hold_seconds",
                "positive_observation_seconds", "warning_distance", "warning_speed",
                "warning_closing_speed",
            ))):
        raise ValueError("Invalid cursor attention bands, stages or warning timing")
    return catalog


def load_balance(path: Path | None = None) -> BalanceCatalog:
    source = path or Path(__file__).resolve().parents[1] / "data/balance.json"
    return parse_balance(load_json(source))


BALANCE = load_balance()
