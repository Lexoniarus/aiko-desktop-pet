# Test ownership follow-up

## Scope and acceptance

Address the three remaining findings from the review after the
[broader test-layer cleanup](TEST_LAYER_CLEANUP_PLAN.md). Follow the
[current architecture](ARCHITECTURE.md): test each owner's contracts directly and
use integration fixtures for the collaboration between owners.

The user reports that desktop acceptance is **passed** for the current working
behavior (2026-10-18). Preserve that accepted behavior. These stages change tests
and documentation only; do not change production modules, the normal save or
assets. Use a small local commit per stage after targeted tests and record the
results here. Do not push or merge.

Baseline: `e2e9af9`, clean working tree. Previous full verification: 1,147 tests
in 254.301 seconds, with no failures, errors or skips. The read-only follow-up
passed 143 targeted tests and instrumented the two misleading test fixtures.

## Findings and stages

| Stage | Evidence and change | Required protection | Status |
| --- | --- | --- | --- |
| 1 | `FoodGuiTests.test_full_energy_rejects_drink_without_eating_animation` only selects a menu item. The observed result is USER_HELD cursor custody, idle interaction and energy 100. Merge its full-energy case into the existing drink-selection test and remove the obsolete refusal claim. | Selection at energy 40 and 100 starts cursor custody without consumption, nutrition, friendship or an eating animation. Actual hand/face refusal remains in the existing World GUI tests. | Complete |
| 2 | `ObjectInteractionTests.test_take_notification_does_not_interrupt_pet_held_custody` finishes pickup and reaches eat; target_taken returns at its phase guard without reading custody. Stop at the actual attachment event while still in pick_up. | A late take notification cannot steal a PET_HELD item or change its committed episode. Actual World pickup and frame-bound reach checks remain unchanged. | Complete |
| 3 | The named-loss feedback test composes Coordinator, Presenter, ReactionPlayer and catalogue but reuses a grasp fixture and rewrites private callback fields. Move it into a dedicated headless integration module with its own minimal fixture and constructor-injected ports. | All named missing bubbles, readable delays, distinct completion receipts, stale callback protection and search readiness remain asserted. Keep separate behavior/orientation and native timer/input tests. | Pending |

The headless integration must not construct DesktopPet or Tk widgets, prepare an
unrelated apple pickup, mutate private callback fields, or import another test
class. Reuse the existing FakeScheduler. Its World and memory are the real
owners; already confirmed historical losses are legitimate input at this layer.
Unexpected physical-action ports should fail, rather than pretending a pickup
succeeded. No new production abstraction is needed.

Do not remove migration, negative API, stale receipt or rollback tests merely
because their inputs are not an ordinary UI action. They verify supported owner
contracts. SearchTask remains distinct from candidate inspection; focus,
identification, observed transport, missing-place orientation and custody retain
their current owners and rules.

## Verification

1. Stage 1: food-menu tests, object decisions and the native taken-drink/hand
   refusal tests in WorldGuiTests.
2. Stage 2: object interaction tests, pickup metadata and the native frame-four
   reach recheck. Verify that the corrected test fails if only the PET_HELD
   early return is removed in an isolated process; do not edit production files.
3. Stage 3: the new feedback integration, coordinator, behavior, object reactions
   and reaction player tests. Existing Windows CI uses `test_object*.py`, so the
   new module must retain that selection pattern.
4. Final: complete native unittest discovery with Python 3.11.9 and Pillow
   11.3.0, Ruff 0.13.2, strict Mypy 1.18.2, Pyright 1.1.414, documentation links,
   UTF-8/no-BOM, whitespace and a clean working tree. Use isolated temporary saves
   and sequential Tk tests. Preserve historical validation numbers above.

## Execution record

### Stage 1 completed

Removed the obsolete full-energy refusal test. The existing energy-drink menu
case now covers energy 40 and 100 in subtests, cancelling the first cursor
gesture through its public owner before the second selection. Both cases assert
USER_HELD custody, idle interaction, no eating animation/hand overlay and
unchanged energy, satiety, digestion, food history, fun and friendship. Only
elapsed-time accounting is isolated to avoid ordinary need decay in a selection
boundary test. No presentation, handover or refusal is claimed at this stage.

Validation: `tests.test_food_gui`, `tests.test_object_decisions`,
`WorldGuiTests.test_taken_unknown_drink_is_recognized_then_accepted_or_refused_at_cursor`
and `WorldGuiTests.test_recognized_drink_handover_then_unknown_full_drink_is_examined`:
8 tests in 2.850 seconds, no skips; Ruff passes. Actual cursor and hand refusal
remain covered by their existing physical interaction fixtures. No runtime change.

### Stage 2 completed

The custody test now stops after frame-three attachment, before clip completion.
It explicitly asserts pick_up and PET_HELD, then rejects the late notification
without changing phase, feedback key, World, memory, actions or completion.
It no longer relies on the unrelated eat-phase admission guard.

Validation: object interaction tests, pickup metadata and the native frame-four
reach recheck: 25 tests in 0.774 seconds, no skips; Ruff passes. An isolated
process removed only the PET_HELD early return from an in-memory copy of
`target_taken`: the corrected test then failed as expected, with no test errors.
The original method was restored; no production source was edited. This confirms
that the test protects the intended custody guard. Plan EOF whitespace is also
normalized.
