# Broader test-layer cleanup

## Scope and evidence

Preserve the working behavior while removing unnecessary whole-application
fixtures and duplicated real-time waits. Use small local commits, targeted tests
after every stage and a complete final verification. Do not push or merge.
Production behavior and the normal save are outside this change.

Baseline: `d4aea01`, 1,149 tests in 344.913 seconds, no skips, Python 3.11.9 and
Pillow 11.3.0. Fourteen test classes construct DesktopPet for 160 methods; this
count is an audit boundary, not a deletion target. An instrumented sample of 50
World GUI/runtime tests recorded 41 acquisitions, all admitted by the actual
reach predicate before custody changed. The reported visible jump has therefore
not been established as an illegal long-distance World pickup. Rendering tests
that directly select a hand overlay are component fixtures, not physical scenes.

The sampled right-edge full investigation took 22.924 seconds and the authored
conversation scenario 18.514 seconds. Their geometry, dialogue policy and phase
contracts already have faster owner-level coverage. Native scheduling and wiring
still need focused integration coverage.

## Rules that must remain

- World custody, subjective memory, identification and observed transport remain
  separate. Unknown identification requires the hand or cursor presentation.
- Focus blocks unrelated perception; after focus, known-place orientation and
  every required missing-item bubble precede candidate investigation. Search
  remains active during candidate inspection.
- Pickup admission is rechecked at the attachment frame. Real movement, both
  scales, surface bounds, attachment/release metadata and safe custody remain
  covered; no forced successful reach predicate replaces this coverage.
- Required feedback needs its matching completion receipt. Stale or optional
  replies cannot advance it. Multiple losses retain distinct names and receipts.
- Hover UI remains available during search without changing Aiko's activity;
  action buttons stay disabled and direct busy replies do not interrupt search.
- Consumption and origin effects remain exactly once. Sleep, restart, handover
  and explicit low-level playback replacement remain covered.

## Stages and coverage mapping

| Stage | Change | Protection retained | Status |
| --- | --- | --- | --- |
| 1 | Move six asset/overlay tests from FoodGuiTests to standalone Tk/AnimatedPet fixtures. | All icon alpha, authored anchors, stacking, scale and timer assertions; four real menu/carry tests stay in FoodGuiTests. Canonical display assets retain their asset tests and direct view-cache coverage. | Complete |
| 2 | Shorten the conversation focus integration scenario using a short test-only reaction with actual Tk timers. | Real care dispatch, silent cue focus, unobserved relocation and missing-first orientation; authored story/sequence semantics retain scheduler tests. | Complete |
| 3 | Replace two complete edge investigation timer replays with one real-motion right-edge scale-two pickup smoke. | Both-scale/edge geometry matrix, full ordinary native investigation, reach recheck at attachment and frame/release tests remain. | Complete |
| 4 | Replace duplicated long multi-loss bubble replays with deterministic presenter/player/coordinator coverage and fast physical search integration. | All named missing bubbles and matching receipts before candidate investigation; same-type replacement, multi-relocation, native hover and busy-reply cases remain covered. | Complete |

Do not remove a test merely because it sets up state directly: owner-level
fixtures may start with known memory or held custody. Remove or relocate a fixture
when it claims to exercise a physical transition that it bypasses, or duplicates
an already protected rule at a needlessly expensive level. Keep native input,
rendering, timer and custody boundaries where those boundaries are the subject.

## Verification and execution record

Run the affected tests sequentially with native Tk and temporary saves after each
stage. Commit only passing stages and record commands/results here. Final gates:
full unittest discovery with Pillow, Ruff 0.13.2, strict Mypy 1.18.2, Pyright
1.1.414, documentation links and Git whitespace. Compare duration on the same
environment; timing is descriptive, not a flaky test threshold.

### Stage 1 completed

Six rendering tests now construct AnimatedPet and WorldView directly on a
withdrawn Tk root. They no longer construct DesktopPet, a World scene, monitor,
persistence or toolbar. All original assertions remain, including the shared
WorldView display-image path. Selecting an overlay is now explicitly a renderer
operation rather than an apparent application pickup. Four menu/cursor-custody
tests retain DesktopPet. No production change.

Validation: `tests.test_food_gui`, `tests.test_food_rendering` and
`tests.test_item_display_assets`: 13 tests, 4.347 seconds, no skips. Ruff passes
for both changed Python modules. Python 3.11.9/Pillow 11.3.0; native Tk, isolated
saves, cyclic collection after each test.

Ownership reference: [current architecture](ARCHITECTURE.md).

Related history: [scoped interaction cleanup](OBJECT_INTERACTION_CLEANUP_PLAN.md)
and [interaction availability](OBJECT_INTERACTION_AVAILABILITY_PLAN.md).

### Stage 2 completed

The conversation integration test now supplies a short test-only pause/text/pause
reaction through the real care command. Actual Tk callbacks finish it; no manual
completion or mocked focus predicate is used. Its silent opening verifies focus
without a visible bubble. Relocation remains unobserved, memory stays unchanged,
and both orientation sides precede the first missing-place event. Long authored
story pacing remains in the deterministic story/player tests.

Validation: native conversation test plus object attention, story playback and
reaction playback: 25 tests in 2.729 seconds, no skips. The previous sampled
conversation test alone took 18.514 seconds. Ruff passes. Existing Tk teardown
ThemeChanged stderr appeared without test failure.

### Stage 3 completed

Two complete edge investigation timer replays and their helper are replaced by
one right-edge scale-two smoke ending at actual PET_HELD attachment. It verifies
initial inadmissibility, actual approach/pickup phases, the geometric reach at
attachment, on-track movement and unchanged energy. No acquisition is forced.

The new assertion exposed a fixture timing issue: the old test placed the item
before syncing World geometry after changing scale. A later tick reclamped it.
The replacement synchronizes geometry before placement, as the fast geometry
fixture already does. This is a test setup correction, not a runtime change or
proof of the user's reported visible jump.

Validation: new native pickup, ground geometry, playback metadata and the native
frame-four negative reach test: 7 tests in 8.443 seconds. Retained full native
satiated investigation and fast deferred-drink/restart retrieval: 2 tests in
24.185 seconds. No skips; Ruff passes. The same-boundary left/right scale matrix
remains in GroundApproachTests, alongside native left-scale-two round-trip and
left-scale-one negative reach coverage.

### Stage 4 completed

Removed the two long native `each_missing_portion` and `same_type_replacement`
replays after their replacement checks passed. A headless integration now uses
real ObjectInteractionCoordinator, ObjectFeedbackPresenter, ReactionPlayer and
unconditional authored catalogue lines. It checks Dango/Energy/Onigiri text,
readable delays, distinct completion keys, blocked search readiness, stale
receipts and stale callbacks. The existing fake scheduler moved unchanged into a
shared test-support module; there is no new production abstraction or state.

The fast physical multi-relocation/restart cases at both scales additionally
check every completed loss receipt before search approach/pickup/inspection.
They retain all learned-place checks, actual gestures, full search/reunion,
distinct portions and an unrelated unknown candidate. Initial orientation must
finish before the first search approach; subsequent movement can request a new
orientation for after the committed action, so a pending side during pickup is
not treated as a failed initial survey. Existing same-type replacement admission
remains in ObjectBehaviorTests; native unknown-replacement inspection remains in
WorldGuiTests. The two native hover/busy regressions are retained unchanged.

Validation: object interaction, behavior, reaction formatting/playback,
orientation awareness and all WorldGui tests: 133 tests in 32.718 seconds, no
skips. Ruff passes on changed modules. Windows CI now explicitly selects the
new renderer module, preserving the native coverage moved in Stage 1. The food
system guide points to both menu and renderer coverage.

Compared with the original 160 DesktopPet test methods, nine whole-application
fixtures are removed (six moved renderer tests and three fewer runtime cases).
The runtime suite goes from eleven methods to eight, retaining one complete
ordinary investigation plus sleep/restart, handover, hover and busy boundaries.
No production behavior changed. Complete final verification is pending.

### Final-gate correction

Pyright found that the new reach assertion passed a float-typed width to an
integer sprite-width parameter. The test now uses `int(world.width)`, matching
the production call. The focused native pickup passes again (1 test, 7.026
seconds), and Pyright reports zero errors/warnings. The initial complete run was
stopped before completion to avoid validating the superseded snapshot; a fresh
committed export will receive the final full run.

A repository-wide acquisition/overlay search finds no remaining native
DesktopPet test that forces `_can_acquire` or directly selects a hand overlay.
Direct `collect_resting` fixtures remain in headless custody, awareness,
consumption and persistence tests, where the owner transition or held-state
invariant is the subject, rather than desktop reach. These are retained.
