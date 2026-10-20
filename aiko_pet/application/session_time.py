"""Coordinate one elapsed-time plan with the existing pet and World owners."""

from __future__ import annotations

from dataclasses import replace

from ..pet.consumption import ConsumptionOrigin
from ..pet.lifecycle import plan_pet_time
from ..pet.mind.object_decisions import decide_object_use
from ..pet.mind.object_knowledge import ObjectKnowledge
from ..pet.mind.object_memory import ObjectMemory
from ..pet.sleep import SleepContext, sleep_care_complete, sleep_setting
from ..pet.state import PetState
from ..world.contracts import ObjectState
from ..world.state import WorldState
from .active_time import SessionInputs
from .object_consumption import ObjectConsumption


class SessionTimeProgression:
    """Apply elapsed time once; live World actions keep their existing owners."""

    def __init__(self, world: WorldState, memory: ObjectMemory) -> None:
        self.world, self.memory = world, memory

    def advance(
        self, state: PetState, inputs: SessionInputs, elapsed: float,
        *, reconstruct: bool = False,
    ) -> None:
        checkpoint = state.capture_checkpoint()
        physical, cognitive = self.world.snapshot(), self.memory.snapshot()
        try:
            self._apply_interval(state, inputs, elapsed, reconstruct=reconstruct)
        except Exception:
            state.restore_checkpoint(checkpoint)
            self.world.restore_snapshot(physical)
            self.memory.restore_snapshot(cognitive)
            raise

    def _apply_interval(
        self, state: PetState, inputs: SessionInputs, elapsed: float,
        *, reconstruct: bool,
    ) -> None:
        plan = plan_pet_time(
            state.updated_at, inputs.wall_time, auto_routine=True,
            elapsed_seconds=elapsed, effort=inputs.effort,
            food_activity=inputs.food_activity,
        )
        if plan is None:
            return
        end_elapsed = state.lived_seconds + plan.elapsed_seconds
        wall = inputs.wall_time - plan.elapsed_seconds
        context = inputs.sleep_context or SleepContext.permissions(
            inputs.allow_bedtime, inputs.allow_nap, inputs.interrupt_nap,
        )
        for step in plan:
            observed = not reconstruct and step.observed
            held = self._holding_item()
            self._update_care(
                state, wall=wall, observed=observed,
                can_finish=not held and not (observed and context.blocked),
            )
            wall += step.hours * 3600
            state.advance_time_step(
                replace(step, observed=observed), now=wall,
                auto_routine=inputs.auto_routine,
                sleep_context=(context.earlier(max(0, inputs.wall_time - wall))
                               if observed else replace(context.unobserved(),
                                                        blocked=held)),
            )
        state.finish_time_advance(
            inputs.wall_time, lived_seconds=end_elapsed,
            auto_routine=inputs.auto_routine,
            sleep_context=context.unobserved() if reconstruct else context,
        )
        self._update_care(
            state, wall=inputs.wall_time, observed=not reconstruct,
            can_finish=not (not reconstruct and context.blocked),
        )

    def _holding_item(self) -> bool:
        return any(item.state == ObjectState.PET_HELD
                   for item in self.world.snapshot().objects)

    def finish_sleep_care(self, state: PetState) -> bool:
        """Finish only after the live custody owner has safely released its item."""
        if not state.sleep_episode.care_break or self._holding_item():
            return False
        stock = ObjectConsumption.remembered_stock(self.world, self.memory)
        state.end_sleep_care(
            failed=state.satiety < sleep_setting("food_target"),
            sources=tuple(entry.token for entry in stock)[:4096],
        )
        return True

    def _update_care(
        self, state: PetState, *, wall: float, observed: bool, can_finish: bool,
    ) -> None:
        episode = state.sleep_episode
        stock = ObjectConsumption.remembered_stock(self.world, self.memory)
        if not episode.kind:
            if not observed and not state.sleeping:
                self._reconstruct_awake_intake(state, stock, wall)
            return
        if state.lived_seconds < episode.protect_until:
            return
        if not episode.care_break:
            sources = ObjectConsumption.remembered_sources(self.memory)
            if episode.food_failed and not any(
                entry.token not in episode.failed_food_sources for entry in stock
            ):
                return
            if state.satiety > sleep_setting("food_trigger"):
                return
            if not sources and (
                state.satiety > 0 or episode.food_failed or not observed
            ):
                return
            state.begin_sleep_care(search=True)
            episode = state.sleep_episode
        if sleep_care_complete(
            episode, satiety=state.satiety, elapsed=state.lived_seconds,
        ):
            if can_finish:
                self.finish_sleep_care(state)
            return
        if observed or state.lived_seconds < episode.intake_until:
            return
        self._consume_known_portion(state, stock, wall)

    def _reconstruct_awake_intake(
        self, state: PetState, food: tuple[ObjectKnowledge, ...], wall: float,
    ) -> None:
        if self._consume_known_portion(state, food, wall):
            return
        if state.energy > sleep_setting("exhaustion_energy"):
            self._consume_known_portion(
                state, ObjectConsumption.remembered_stock(
                    self.world, self.memory, kind="drink",
                ), wall,
            )

    def _consume_known_portion(
        self, state: PetState, stock: tuple[ObjectKnowledge, ...], wall: float,
    ) -> bool:
        for known in stock:
            if not decide_object_use(known, state).consume:
                continue
            assert known.instance_id is not None
            prepared = ObjectConsumption.apply_portion(
                state, self.world, self.memory, known.instance_id, known.token,
                ConsumptionOrigin.AUTONOMOUS, now=wall, collect=True,
            )
            if prepared is not None:
                return True
        return False
