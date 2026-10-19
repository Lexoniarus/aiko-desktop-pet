"""Chronological coordination of existing pet time and finite object intake."""

from __future__ import annotations

from dataclasses import replace

from ..pet.balance import BALANCE
from ..pet.consumption import ConsumptionOrigin
from ..pet.lifecycle import plan_pet_time
from ..pet.mind.object_knowledge import ObjectKnowledge
from ..pet.mind.object_memory import ObjectMemory
from ..pet.sleep import SleepContext, setting
from ..pet.state import PetState
from ..world.contracts import ObjectState
from ..world.state import WorldState
from .active_time import SessionInputs
from .object_consumption import ObjectConsumption


class CareTimeProgression:
    """Bind the existing paired owners, without owning needs or a second clock."""

    def __init__(self, world: WorldState, memory: ObjectMemory) -> None:
        self.world, self.memory = world, memory

    def advance(
        self,
        state: PetState,
        inputs: SessionInputs,
        elapsed: float,
        *,
        live: bool = True,
    ) -> None:
        checkpoint = state.capture_checkpoint()
        physical, cognitive = self.world.snapshot(), self.memory.snapshot()
        try:
            self._advance(state, inputs, elapsed, live=live)
        except Exception:
            state.restore_checkpoint(checkpoint)
            self.world.restore_snapshot(physical)
            self.memory.restore_snapshot(cognitive)
            raise

    def _advance(
        self,
        state: PetState,
        inputs: SessionInputs,
        elapsed: float,
        *,
        live: bool,
    ) -> None:
        plan = plan_pet_time(
            state.updated_at,
            inputs.wall_time,
            auto_routine=True,
            elapsed_seconds=elapsed,
            effort=inputs.effort,
            food_activity=inputs.food_activity,
        )
        if plan is None:
            return
        legacy_relationship = state.friendship_history.baseline is None
        wall = inputs.wall_time - plan.elapsed_seconds
        context = inputs.sleep_context or SleepContext.permissions(
            inputs.allow_bedtime,
            inputs.allow_nap,
            inputs.interrupt_nap,
        )
        for step in plan:
            observed = live and step.observed
            if legacy_relationship:
                state.begin_relationship_migration()
            held = any(
                item.state == ObjectState.PET_HELD
                for item in self.world.snapshot().objects
            )
            self._supply(
                state,
                wall=wall,
                live=observed,
                finish_allowed=not held and not (observed and context.blocked),
            )
            wall += step.hours * 3600
            state.advance(
                wall,
                elapsed_seconds=step.hours * 3600,
                auto_routine=inputs.auto_routine,
                sleep_context=context.earlier(max(0, inputs.wall_time - wall))
                if observed
                else replace(context.unobserved(), blocked=held),
                effort=step.effort,
                food_activity=step.food_activity,
            )
        self._supply(
            state,
            wall=inputs.wall_time,
            live=live,
            finish_allowed=not (live and context.blocked),
        )

    def _supply(
        self,
        state: PetState,
        *,
        wall: float,
        live: bool,
        finish_allowed: bool = True,
    ) -> None:
        episode = state.sleep_episode
        stock = ObjectConsumption.remembered_stock(self.world, self.memory)
        if not episode.kind:
            if not live and not state.sleeping:
                if state.satiety <= BALANCE.number(
                    "object_behavior", "seek_food_satiety"
                ):
                    self._eat(state, stock, wall)
                elif (
                    setting("exhaustion_energy")
                    < state.energy
                    <= BALANCE.number("object_behavior", "seek_drink_energy")
                ):
                    self._eat(
                        state,
                        ObjectConsumption.remembered_stock(
                            self.world,
                            self.memory,
                            kind="drink",
                        ),
                        wall,
                    )
            return
        if state.lived_seconds < episode.protect_until:
            return
        sources = ObjectConsumption.remembered_sources(self.memory)
        if not episode.care_break:
            if episode.food_failed and not any(
                entry.token not in episode.failed_food_sources for entry in stock
            ):
                return
            if state.satiety > setting("food_trigger"):
                return
            if not sources and (state.satiety > 0 or episode.food_failed or not live):
                return
            state.begin_sleep_care(search=True)
            episode = state.sleep_episode
        episode = state.sleep_episode
        if state.lived_seconds < episode.intake_until:
            return
        if (
            state.satiety >= setting("food_target")
            or state.lived_seconds >= episode.search_until
        ):
            if not finish_allowed or any(
                item.state == ObjectState.PET_HELD
                for item in self.world.snapshot().objects
            ):
                return
            state.end_sleep_care(
                failed=state.satiety < setting("food_target"),
                sources=tuple(entry.token for entry in stock)[:4096],
            )
            return
        if live:
            # Existing perception, movement and animation own all live intake.
            return
        if stock:
            known = stock[0]
            assert known.instance_id is not None
            ObjectConsumption.apply_portion(
                state,
                self.world,
                self.memory,
                known.instance_id,
                known.token,
                ConsumptionOrigin.AUTONOMOUS,
                now=wall,
                collect=True,
            )
        # Without valid stock, the saved break expires at its historical
        # deadline. There is no unknown discovery or new zero-food offline search.

    def _eat(
        self, state: PetState, stock: tuple[ObjectKnowledge, ...], wall: float
    ) -> None:
        if not stock:
            return
        known = stock[0]
        assert known.instance_id is not None
        ObjectConsumption.apply_portion(
            state,
            self.world,
            self.memory,
            known.instance_id,
            known.token,
            ConsumptionOrigin.AUTONOMOUS,
            now=wall,
            collect=True,
        )
