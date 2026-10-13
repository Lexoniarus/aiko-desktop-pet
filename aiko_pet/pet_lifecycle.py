"""Legacy lifecycle imports; the pet aggregate applies canonical time rules."""

from __future__ import annotations

from .pet.lifecycle import (
    MAX_CATCHUP_SECONDS as MAX_CATCHUP_SECONDS,
    MAX_LIVE_EFFORT_SECONDS as MAX_LIVE_EFFORT_SECONDS,
    SIMULATION_STEP_SECONDS as SIMULATION_STEP_SECONDS,
    RoutineValues as RoutineValues,
    RoutineTransition as RoutineTransition,
    SimulationStep as SimulationStep,
    PetTimeline as PetTimeline,
    RoutineActor as RoutineActor,
    calculate_daily_routine as calculate_daily_routine,
    plan_pet_time as plan_pet_time,
    apply_daily_routine as apply_daily_routine,
    advance_pet_time as advance_pet_time,
)
