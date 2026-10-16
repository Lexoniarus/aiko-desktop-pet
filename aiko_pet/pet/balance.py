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
    withholding = sections["object_withholding"]
    if (any(value <= 0 for value in withholding.values())
            or withholding["friendship_loss"] > withholding["maximum_episode_loss"]
            or withholding["maximum_episode_loss"] > 100
            or withholding["request_interval_seconds"] > withholding["grace_seconds"]
            or withholding["request_interval_seconds"]
            > withholding["loss_interval_seconds"]):
        raise ValueError("Invalid object withholding balance")
    objects = sections["object_behavior"]
    if (
        objects["reach_widths"] >= objects["notice_widths"]
        or objects["notice_seconds"] > objects["recognize_seconds"]
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
        ("food", "internal_simulation_step_minutes"),
        ("food", "digest_minutes_for_full_hunger_reduction"),
        ("food", "maximum_recent_foods"),
        ("food", "consecutive_repeats_before_dislike"),
        ("food_activity", "bucket_seconds"),
        ("food_activity", "short_window_minutes"),
        ("food_activity", "long_window_minutes"),
        ("simulation", "step_seconds"),
        ("needs", "hardware_intensity_span"),
        ("adaptive_learning", "effort_smoothing_seconds"),
        ("walk", "minimum_cycles"),
    ):
        if catalog.number(section, key) <= 0:
            raise ValueError(f"balance.{section}.{key} must be positive")
    if catalog.integer("simulation", "step_seconds") > 300:
        raise ValueError("Simulation steps must not exceed five minutes")
    if catalog.integer("simulation", "maximum_catchup_seconds") > 7 * 86400:
        raise ValueError("Catch-up must not exceed seven days")
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
    if not math.isclose(
        sum(
            value for key, value in sections["mood"].items() if key.endswith("_weight")
        ),
        1.0,
    ):
        raise ValueError("Mood weights must add up to one")
    return catalog


def load_balance(path: Path | None = None) -> BalanceCatalog:
    source = path or Path(__file__).resolve().parents[1] / "data/balance.json"
    return parse_balance(load_json(source))


BALANCE = load_balance()
