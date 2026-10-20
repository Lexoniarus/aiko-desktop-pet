# Care, relationship and real-time implementation plan

> **Active implementation plan; stage 4 corrected and locally verified.** Requested on 2026-10-19
> on `feature/social-optimization`, reviewed against clean baseline `42de63a`.
> The owner accepted the latest discussed balance as a sufficient starting
> point for implementation planning. This document plans that first delivery.
> Stages 1–3, B1 and B2 are implemented and verified below.
> Stage 4 follows the corrected ownership and verification scope below.
> Stage 5's needs/progression/status foundation and menu/action/placement
> decoupling are delivered below. Moodlet/wish/emotion integration and stage 6
> remain pending; physical desktop acceptance is separately recorded.
> The owner subsequently expanded stage 5 to separate needs, Moodlets, numeric
> mood, emotional state, wishes and expression before changing dialogue wording.
> The first-version Moodlet/wish product rules are settled below. Stage 5B.1
> supplies typed definitions and JSON catalogues; 5B.2 adds aggregate-owned
> state and storage. 5B.3 delivers Moodlet lifetime/relief and numeric mood
> composition. 5B.4 now connects negative interaction experiences and targeted
> helpful-action relief. 5B.5 delivers prolonged-poor-care after-effects and
> accounted exposure. 5B.6 now delivers paced inner wishes, real-time expiry and
> actual spoken disclosure. 5B.7 delivers fulfillment, positive Moodlets and the
> shared-pot personal bonus for food, affection, games and social activities.
> Overall emotion and status UI remain for the following slices.

## Stage-4 correction delivery, 2026-10-19

The owner subsequently authorized implementation, saving the completed text
work first, local checks without visible windows or mouse control, review of
individual tests over ten seconds, and clean commits/pushes. No GitHub CI run
is authorized. The earlier planning-only restrictions below are historical.

Stage 4 includes adaptive live sleep, active autonomous care both with and
without the user present, and reconstruction of closed/standby time. User
absence alone never selects historical intake while the app keeps running.
Only unobserved elapsed intervals are reconstructed, using actual acquired
stock and the saved rhythm. Existing live search, movement, intake and custody
owners remain active; historical intake does not execute those animations.

- Preserve the completed dialogue/data/test updates separately as `643607c`.
- Replace the broad `CareTimeProgression` name/module with
  `SessionTimeProgression` in `application/session_time.py`. It coordinates
  one plan and existing owners; it adds no pet, clock or numeric model.
- Restore `ActiveSessionClock` to elapsed-time measurement only. Pass the
  existing typed time-progression port explicitly through application assembly,
  care/game/activity and consumption use cases. World's existing late-binding
  access port forwards to the single restored resource coordinator.
- Apply already planned steps through PetState's shared step operation; direct
  aggregate advancement uses that same internal application. No nested plans
  or repeated resetting of legacy relationship history remains. Finalize the
  first-save baseline once for the complete interval.
- Use one `sleep_care_complete()` decision and one application completion method
  for historical care and live safe-interruption callbacks. The live owner
  still safely releases an unconsumed held item before returning to sleep.
- Reuse `decide_object_use()` for reconstructed intake. An empty/unusable food
  supply no longer blocks an otherwise eligible known drink while awake.
- Name the sleep coefficient accessor `sleep_setting` and the pure manual
  transition `calculate_manual_sleep_transition`; remove its unused episode
  input. Production activity supplies SleepContext once; old permission fields
  remain compatibility inputs rather than a second production decision path.
- Add the explicit 59.99/60 early-wake energy boundary and the no-food/known-
  drink regression. Consolidate small-step and standby resource equivalence
  into one one-hour scenario; keep genuine paired-store restart coverage.

### Local verification and individual slow-test review

The first complete local Linux/Python 3.11/Xvfb run passed 1,272 tests in
189.946 seconds, with eight Windows-only skips. A frozen checkout was copied
into a disposable local container; testing used no network, user save, visible
Windows window or injected mouse input. The initial Windows-bind-mounted
collection was stopped before test execution to avoid measuring shared-file
I/O; the actual run used the container's own filesystem.
A temporary standard unittest result collector measured each test's setup,
body and cleanup using `perf_counter`; shared fixtures/runner overhead was
recorded separately (2.463 seconds). No test framework was added.

| Test ID suffix (`module.Class.method`) | Measured seconds | Investigation / disposition |
| --- | --- | --- |
| `test_elapsed_time.ElapsedAdvancementTests.test_long_routine_plan_streams_the_entire_duration` | 13.158 in initial Linux run; 12.028 for targeted Windows run after eliminating repeated aggregate endpoint evaluation | It combined planner streaming and thirty days of full domain calculation. Preserve the complete thirty-day planner check; verify aggregate time/no-food/absence over three days in a separate case. This reduces repeated work rather than partitioning the same expensive loop. The measured month-long domain cost remains documented, not hidden with mocks. |
| `test_world_runtime_flow.WorldRuntimeFlowTests.test_satiated_food_is_investigated_put_down_and_not_repeated` | 23.481 | Seven actual feedback phases must remain separated by more than 1.6 seconds, with pickup/inspection/put-down and a final idle check. Retain as a justified bounded scheduler integration case; shorten or mock ordinary component tests instead. |
| `test_world_runtime_flow.WorldRuntimeFlowTests.test_restored_food_uses_readable_recall_and_full_eat_without_reinspection` | 13.061 | Covers real restored recall, absence of reinspection and at least 3.4 seconds of actual eating playback. Distinct from numeric catch-up; retain one full timer integration case. |
| `test_world_runtime_flow.WorldRuntimeFlowTests.test_sleep_during_held_inspection_puts_down_and_restart_keeps_portion` | 10.591 | Verifies interruption during actual inspection, safe animated put-down before sleep and restart without accidental consumption. Retain the bounded real scheduling check; separate component cases already use injected time. |

The three retained GUI cases advance and terminate automatically under Xvfb;
they require no human click. They are explicit justified exceptions to the
review threshold. The separate frozen-frame/mouse probe is not reused.
The remaining Windows-only layered-window/setup cases are not run on the
working desktop because setup itself may create a Tk probe. Physical standby
and visible animation quality remain separate, unperformed acceptance; this
local delivery does not claim them.

Final validation passed **1,273 tests in 176.808 seconds** on the frozen local
Linux/Python 3.11/Xvfb checkout, with the same eight Windows-only skips and no
failures/errors. Shared fixtures/runner overhead was 2.501 seconds. The final
individual cases above ten seconds were the three justified runtime-flow cases:
satiated inspection/put-down **22.631s**, restored recall/eating **13.071s**,
and sleep interrupt/put-down/restart **10.604s**. No other final case exceeded
ten seconds. Existing Tcl theme-change teardown diagnostics appeared on stderr;
they did not produce Python test errors or imply visible desktop acceptance.

The final **130 affected headless Windows tests passed in 7.626 seconds**;
the slowest case took **1.237 seconds**. The initial shortened three-day fixture
incorrectly retained the default-bond-to-zero expectation from the old month
scenario. It now explicitly starts with a low bond of one, preserving the
complete-loss assertion without claiming that ordinary friendship vanishes
within three days. The final suite includes this correction.
Ruff 0.13.2, strict Mypy 1.18.2 (197 source files) and Pyright 1.1.414 passed.
No local GUI was launched and no mouse input was injected. No GitHub CI was
started. The manual full-matrix workflow additions from `4d404e4`/`2a12820`
and their guide were removed; the original main/PR workflow remains intact.
The agreed automated scope of stage 4 is complete; physical Windows acceptance
and stages 5–6 remain distinct. No merge is included.

## Stage-4 scope correction and effort audit, 2026-10-19

The owner requested a simpler account of closed-app/standby progression and
an audit of redundant implementation and verification. This section records
that direction; it does not authorize a runtime refactor, test changes or any
new test/CI execution. Current work is documentation and source inspection only.

### Simplified catch-up contract

1. Read the saved pet condition, elapsed-time anchor, expected sleep rhythm,
   actual World portions and Aiko's acquired object knowledge.
2. Determine the unobserved elapsed interval, from closing to reopening or
   across standby. No user interaction occurred during that interval.
3. Recalculate needs, mood, friendship and sleep using existing domain rules
   and the saved rhythm. Available known World portions can supply autonomous
   care at the relevant times; exhausted stock cannot supply further care.
4. Apply actual portion consumption through the existing World/Pet/memory
   transaction. It grants no personal contact or human-care reward.
5. Continue from the resulting condition, remaining stock and updated time
   anchor exactly once. Do not replay the absence as a live game sequence.

Chronological arithmetic may split at sleep/wake and intake boundaries. This
is a calculation detail, not a reason to execute movement, perception routes,
click handling or animation during absence. The same catch-up calculation
must serve reopening and standby without duplicating those two entry paths.
An active app continues using its normal gameplay owners. Decisions made by
real user interaction belong to that active interval, not to historical care.

### Existing plan versus implementation

| Area | Plan requirement | Observed implementation / correction |
| --- | --- | --- |
| Closed-time care | Advance from saved condition/rhythm and finite acquired stock | The basic requirement was already correct. No additional offline gameplay engine was requested. |
| Time planning | Reuse existing chronological progression and need rules | `CareTimeProgression._advance()` plans an interval and invokes `PetState.advance()`, which plans each section again. Remove this redundant orchestration; it is not evidence of double-charged needs. |
| Clock ownership | Measure/consume elapsed time once | `ActiveSessionClock.bind_progression()` makes the clock dispatch World care on ordinary ticks, care commands and game completion. This additional coupling is not required by the catch-up contract. |
| Care-break completion | One authoritative rule with safe live execution | Similar target/deadline completion checks exist in `_supply()` and `DesktopWorldRuntime.update()`. Share the decision; keep actual safe put-down in the existing live interaction owner. |
| Existing owners | PetState mutates the pet; World owns stock; consumption commits jointly | Preserve these owners and the common consumption transaction. Do not remove atomicity or move World access into the pet domain to reduce file count. |
| Application coordination | Coordinate finite resources with elapsed condition changes | Some shared coordination is needed. The present clock-bound `CareTimeProgression` is not required as designed. Copying it into the restorer alone would leave standby with a second implementation. Settle the smaller shared procedure before changing APIs. |
| Verification | Automated domain/integration evidence plus relevant Windows acceptance | The frozen-frame input probe, repeated desktop probes and extra CI dispatch infrastructure were agent choices, not product requirements. They should not have displaced architecture discussion. |

Offline code already avoids executing actual search routes/animations. The
identified excess is the coupling, repeated planning and shared live/historical
control logic. Do not describe it as an actual hidden rendered game loop.
Sleep priorities and rhythm learning remain agreed features for active use;
this correction does not cancel them or the previously agreed balance values.

### What consumed verification effort

The figures below are existing recorded results, not a fresh timing run or a
complete CPU/token profile. Exact two-hour token cost and per-test attribution
are unavailable; no invented cost estimate is claimed.

| Work / evidence | Assessment |
| --- | --- |
| Frozen idle sprite with a sleeping fixture, repeated real-input probes, one 123.5-second sustained-input observation | Avoidable test-harness effort; it confused the visible state and cannot establish sleep-animation acceptance. Do not repeat it. |
| Repeated complete local suites; last recorded full run 1,271 tests / 302.911 seconds | Broad regression evidence has a place after agreed runtime changes, but repeated full reruns were excessive for fixture/doc-only follow-ups. This is not the cost of 1,271 newly added step-4 tests. |
| Final focused batch of 91 tests | Includes existing object-behavior/session tests; it is not 91 new step-4 cases. The three new modules contain 43 cases: 15 sleep priorities, 16 resources and 12 rhythm cases. Their recorded runtimes total 2.718 seconds. |
| Existing long care/balance scenarios | `test_daily_need_schedules` samples two schedules over eight days in 15-second increments; `test_friendship_policy` includes 540-day equilibrium comparisons. These predate step 4. Re-running them as part of every complete suite increases total work; source inspection alone does not identify their exact share of runtime. |
| CI commits `4d404e4` and `2a12820` | Additional verification infrastructure, not implementation of sleep or catch-up. It was an unnecessary detour from the requested local discussion. No new CI use is authorized. |
| First CI matrix run `39237857302` | Linux jobs each ran 1,271 cases (eight skips); Windows full-suite setup lacked Pillow and ended with two module-import errors. The setup repair and subsequent repeat added further work. |
| Second CI matrix run `39238773891` | Cancelled at the owner's explicit request; cancellation was confirmed. No green completion is claimed. |

### Test disposition for discussion, without editing or running tests

- Retain observable guarantees: correct sleep/wake arithmetic, finite known
  supply, no invented food/contact, exactly-once catch-up/consumption, save
  compatibility and joint rollback. Use injected timestamps for elapsed time.
- Review overlap among `test_offline_progress`, `test_time_persistence`,
  `test_sleep_priorities` and `test_sleep_resources`. Similar restart/time
  assertions at different boundaries can protect different contracts; do not
  label every such test redundant or delete them by count.
- Consolidation candidates are the two eight-hour resource-equivalence cases
  and the one-hour paired-store restart case. Review their shared setup and
  repeated end-state assertions; keep distinct small-step, clock and store
  guarantees. They are not interchangeable tests. Shorter timelines may cover
  individual boundaries without repeating a whole night for each assertion.
- Keep live search and held-object safety checks with existing World tests.
  They cover active behavior, not a requirement to simulate searches offline.
  Assertions tied only to the current `bind_progression()` wiring should follow
  the agreed replacement, without preserving obsolete wiring for its own sake.
- Keep quiet-learning and sleep-boundary tests with short injected sequences.
  The new rhythm module's recorded 0.015-second run is not a demonstrated
  performance problem. Optimize measured excess, not simulated hours by name.
- Do not repeat visible mouse probes, run actual-time waits for arithmetic,
  add another test framework, or launch a full multi-platform matrix to answer
  an architecture/documentation question. Select later checks for the actual
  agreed change; reserve broad regression for a completed runtime change.

### Individual tests over ten seconds

For the next agreed local verification, record real wall-clock duration per
test, including per-test setup and cleanup. Account for shared class/module
setup separately. Measure actual execution time, not simulated pet time, and
reuse that run's timing rather than repeatedly running the entire suite.

Every test taking more than ten seconds requires explicit review. Record its
full test ID, measured duration, cause, protected behavior and proposed action.
The threshold triggers investigation, not automatic deletion, skipping or a
machine-dependent hard failure. Check for blocking input, real-time waits,
unbounded retries, redundant long scenarios, expensive fixture construction
and unexpectedly costly production calculations.

Use fixed input data and injected timestamps for boundary checks; mock external
services, OS reads or waiting when those are not the behavior under test. Keep
the actual domain rules for tests of needs, sleep, resource effects and
friendship. A persistence integration test must still exercise real isolated
storage. Do not replace the calculation being verified with its own mock result.

Split tests when they combine independent contracts, and shorten scenarios
when a smaller interval proves the same behavior. Splitting one expensive loop
into many tests merely to get below ten seconds is not an improvement. If the
production catch-up itself is unexpectedly expensive, investigate that path
instead of hiding its cost behind mocks. Retain a justified longer integration
case only when it provides distinct necessary evidence, with its reason recorded.

This criterion authorizes no test execution during planning and adds no new
test framework or CI job.

The next decision is the smaller catch-up ownership/entry-point design, then
which existing tests express that contract. No refactor, deletion, test run,
commit, push or CI dispatch is included in this documentation update.

## Goal and boundaries

Make Aiko's condition and relationship evolve coherently over real time,
including closed-app and standby intervals. Demanding, distributed care should
support level 10 with normal human sleep; four adequately supplied daily care
phases should support approximately levels 7–8. Needs can reach zero without
death. This foundation must give later conversations and games meaningful,
reliable context.

Use the latest sections of these documents as the planning baseline:

- [Needs, care, consumption modifiers and combined days](NEEDS_BALANCE_PROPOSAL.md).
- [Mood target, deficit limits and decline/recovery](MOOD_BALANCE_PROPOSAL.md).
- [Friendship gains, rolling ceilings, progressive loss and neglect](FRIENDSHIP_BALANCE_PROPOSAL.md).
- [Simple adaptive sleep, manual priority and food breaks](ADAPTIVE_SLEEP_PROPOSAL.md).

Earlier, explicitly superseded examples are not alternative requirements.
The proposals remain design evidence, not descriptions of the current runtime.
Record implementation decisions here and update maintained behavior guides
when the corresponding behavior actually ships.

The original stages 1–4 exclude content APIs, translation, jokes/facts, another
minigame, new cursor behavior, the full Moodlet/stacking system and durable
emotional memories. The subsequent stage-5 planning expansion below introduces
the proposed Moodlet, wish and emotional-state foundation before expression
integration. Its first-version behavior is now specified below; this does not
retroactively add that behavior to the completed stages. External content APIs,
new games and longer-term emotional memory remain outside the current defined
scope. Preserve the completed authored dialogue rewrite. Future resource types
may use the same contracts, but only existing food/drinks are implemented now.

## Baseline gaps and ownership

Follow [the canonical architecture](ARCHITECTURE.md). `PetState` remains the
single mutable pet aggregate, backed by immutable `PetValues`; pure policies
calculate changes. World owns actual portions and custody, object memory owns
acquired knowledge, application services coordinate their effects, and desktop
adapters own OS observations and Tk playback.

| Area | Current code to change | Required outcome |
| --- | --- | --- |
| Elapsed time | `application/active_time.py`, `infrastructure/active_time.py`, `pet/lifecycle.py` | The current live clock excludes suspension and catch-up is capped at eight hours. Replace those limits with exactly-once elapsed-time advancement, including standby and longer absences. |
| Restoration | `application/session.py`, `pet/state.py` | Restore currently advances pet state before coordinating World and can provide catalogue-based self-care. Reconstruct the paired state chronologically using finite, actually available resources. |
| Need consumption/care | `pet/need_decay.py`, `pet/food.py`, `pet/fun.py`, `pet/care_actions.py`, balance/food JSON | Apply the discussed rates, rewards and bounded consumption modifiers. Remove overlapping fasting/reserve accelerators from the new model. |
| Mood | `pet/mood.py` and its callers | Replace unequal weights, friendship/workload bonuses or penalties, exponential adjustment and instant care alignment with the discussed target and timed response. |
| Friendship | `pet/friendship.py`, care/game/consumption entry points | Replace calendar-day accounting with rolling shared ceilings; persist qualified contact, absence and bounded neglect history. |
| Sleep and learning | `pet/lifecycle.py`, `pet/mind/adaptive.py`, `adaptive_models.py`, `adaptive_policy.py` | Learn a simple recurring quiet window from actual input/unavailability, without hardware-driven sleep or weighted habit scoring. |
| Presentation | Read snapshots, status/view models, mind/click/emote policies and relevant dialogue filters | Keep needs, actual mood, relationship and observed situation distinct; positive expressions must be reachable below the need-only mood maximum of 80. |
| Persistence | `infrastructure/pet_codec.py`, `persistence.py`, paired World/object-memory codecs | Round-trip new histories and sleep episodes without resetting timers, replaying consumption or inventing old evidence. |

No second time simulator, relationship store or movement writer is introduced.
The application may coordinate chronological steps, but domain and World owners
remain authoritative for their respective changes.

The owner additionally requested [B2: subjective object reunion and natural
German object dialogue](history/OBJECT_RECOGNITION_DIALOGUE_FIX_PLAN.md). Its three
steps (memory/search association, grammatical phrases, integrated regression)
are a separately scoped follow-up. Preserve its Onigiri acceptance sequence;
do not fold its runtime or dialogue edits into unfinished stage 2.

### Implementation and review constraints

Follow [Contributing](../CONTRIBUTING.md) and the existing object boundaries.
Extend existing owners rather than introducing parallel services or stores:

| Responsibility | Canonical owner |
| --- | --- |
| Mutable pet state and applying calculated transitions | `PetState`, backed by frozen `PetValues` |
| Numeric pet progression | Pure `pet/progression.py`; returns separate need/mood/food/relationship results, reads no clocks and mutates no aggregate |
| Nutrition/reserve, fun and mood calculations | Existing pure `pet/food.py`, `pet/fun.py`, `pet/mood.py` |
| Coefficients and their validation | Existing packaged balance/food JSON and typed loaders |
| Elapsed-time planning and observation freshness | Existing time plan and application activity coordinator |
| Click admission and annoyance escalation | Existing desktop/application input path and mind click policy |

Each stage must audit obsolete callers and overlapping calculation paths,
preserve import/dependency and checkpoint contracts, and pass focused tests and
static checks appropriate to the changed contract before its implementation
commit. The owner explicitly requests small commits and targeted checks during
the refactor; the complete local suite and repository-wide static gates belong
to the final integrated candidate, not every intermediate commit. Record the
actual checks and remaining Windows acceptance separately. Commit and push each
coherent completed unit independently; do not mix unfinished later work into it.

### Remaining refactor: commit and verification sequence, 2026-10-20

This owner-requested workflow supersedes earlier instructions to run the full
suite before each stage commit. Stages 5A-5C describe responsibilities, not three
large commits. Keep each migration reviewable and leave one canonical owner
after each completed unit; do not retain a parallel implementation to make an
intermediate commit appear complete.

| Order | Coherent commit scope | Targeted verification |
| --- | --- | --- |
| 0 | Finish and separately commit the already ongoing object-investigation/test corrections and approved design documentation. Preserve their authors' work and establish the actual starting revision before overlapping edits. | Only the affected object/World contracts and the corrected failing cases; record their real outcome rather than inheriting an older green result. |
| 1 | Structural foundation: all five needs in `needs.py`; rename/move existing numeric progression and status hints with their callers. Preserve current numerical behavior and single clock/aggregate ownership. | Existing need, mood, progression, save/checkpoint and affected import-boundary tests; no new test for a mere rename. |
| 2 | Typed Moodlet/wish catalogue contracts, immutable owned values and focused codecs integrated with `PetValues`/the existing pet save. Product rules are settled; use the finer 5B slices below. | Catalogue references/validation, legacy-save defaults, bounded histories, elapsed deadlines and existing checkpoint/rollback cases. |
| 3 | Deliver the shared Moodlet lifetime/contribution policy first, then qualifying interaction evidence and transitions in small groups: direct negative experiences, poor-care after-effects and individual wish areas. Keep each event and its exactly-once application in one coherent change. | Existing care/contact/object/game/social owners and relevant policy/transaction cases; injected time, boundary-aware progression and actual semantic completion facts. |
| 4 | Complete final emotional interpretation and migrate dialogue context/schema and their consumers to the distinct typed layers together. This completes the relevant vocabulary work from 5A and builds on the shared expiry/relief/numeric composition policy. | Focused emotional-composition, catalogue-filter and status/dialogue projection checks; preserve authored wording unless explicitly required. |
| 5 | Export/package the approved artwork, root-local image ownership and shared VN skin/control rendering. | Required resource/mapping validation and focused image-lifecycle/export checks; do not regenerate approved sources or introduce preview HTML as runtime data. |
| 6 | Main status window, Moodlet strip, wish row, embedded selectors and details, split further by existing view ownership where useful. Preserve the delivered menu/action/placement separation. | Read projections, action ports, selector lifecycle, single window/capture ownership and focused rendering contracts. |
| 7 | Matching settings navigation and separate Credits view, preserving existing preference commands and accepted-content metadata. The now-approved game-screen restyling remains a separate UI unit, not a 5B prerequisite. | Existing settings actions and source projections, absent/available metadata, local navigation and image cleanup; no new source history. |
| 8 | Integrated completion, final OOP review and final full local suite/static gates. | The complete final candidate, with test durations and any remaining native acceptance explicitly reported. |

During implementation, select the smallest existing test owners that establish
the changed behavior and its actual callers. Add a test only for a distinct
contract/regression that existing coverage cannot establish. Remove or merge a
redundant test only after identifying the surviving owner and coverage; do not
weaken a semantic assertion to make the refactor green. Track per-test runtime
in the selected batches, not only the batch total. Investigate each test over
ten seconds: explain the cause, then split unrelated scenarios, inject time or
mock slow external boundaries where appropriate. Keep domain calculations real
when those calculations are what the test is meant to verify. This review runs
alongside the small commits rather than being deferred to a final test explosion.

At completion, review package dependencies, class/function names, state and
timer ownership, obsolete callers, duplicated calculations, JSON-versus-policy
boundaries, transaction/codec consistency and passive UI contracts. Correct
findings in focused commits, then run the complete suite and full Ruff, strict
Mypy and Pyright gates on the final candidate. Use the established isolated
local environment for GUI-dependent cases; no test windows or mouse control on
the working desktop and no GitHub CI. If final checks uncover a defect, diagnose
and fix it with focused checks before repeating the affected final gate. Record
individual slow tests and their disposition, not merely a total pass count.
No merge or additional desktop acceptance is implied.

#### Readiness review against the current checkout and reference bundle

The refreshed read-only review on 2026-10-20 confirms that 5A has delivered
`needs.py`, `progression.py` and status-specific vocabulary. `PetMind.emotion()`
still mixes need/lifecycle facts with emotional labels, and
`DialogueContext.states` still merges those inputs. The 5B.1 Moodlet/wish
definitions/catalogue loaders and 5B.2 owned collections/codecs are delivered
below. 5B.3 now integrates Moodlet lifetime and numeric mood progression;
qualifying events and final emotional interpretation remain pending.
`PetState`/frozen `PetValues`, `SessionTimeProgression`,
existing World custody and the current application coordinators remain the
correct owners. The delivered menu/action/placement separation is the baseline
to retain, including the independent `place_item` capability.

The durable visual companion is now present outside the Git checkout at
`E:\aiko-desktop-pet\design-previews\vn-ui-2026-10-20\index.html`.
The earlier reference review verified the manifest's 229 file sizes/hashes and
found no missing local links in its six HTML pages. It includes 46 icon masters
and eight control/panel masters, covering 18 Moodlet families and 11 wish forms.
This establishes local reference availability, not runtime or rendered/native
acceptance. The refreshed check confirms the external index/main-menu files
remain present. The maintained UI design/handoff now records main menu,
settings/Credits and all three game surfaces as owner-approved. The full
interactive main menu supersedes the earlier image boards. The bundle is a
visual snapshot: its copied documentation does not supersede the maintained
plan and design documents in the checkout. It is not a runtime dependency.

The correction baseline and 5A are secured. The owner-confirmed wish-disclosure/
lifecycle, emotional composition, relief eligibility and wish friendship bonus
rules below close the previously listed 5B product decisions. Remaining work is
implementation contracts and delivery, as detailed under "5B readiness and
small implementation slices"; do not reopen hypothetical product cases or
interpret this readiness review as implementation authorization.
This review ran no application tests and changed no runtime behavior.

## Delivery order

Stage 1 now supplies the time/storage foundation. Keep commits reviewable, but integrate the complete
foundation before promoting it to main: changing numbers alone would leave
incompatible time, sleep and save behavior in place.

| Delivery | Status / evidence |
| --- | --- |
| Stage 1: time and storage | `59cab63`, pushed to `feature/social-optimization`; 1,166 tests and pinned static checks passed; physical suspend/resume remains pending |
| Stage 2: needs and mood | Implemented in the separate feature commit containing this record; 1,177 tests and pinned static checks passed; isolated native care/save/reopen passed |
| B1: idle repeated-click regression | Implemented in the separate fix commit containing this record; 1,185 tests, pinned static checks and native Windows clicks passed; no new friendship penalty |
| B2: object recognition and German dialogue | [Detailed plan](history/OBJECT_RECOGNITION_DIALOGUE_FIX_PLAN.md); Implemented as `4757da7` and `b984078`, pushed; 1,203 tests and pinned static checks passed; isolated real-timer native Onigiri flow passed (21 text bubbles); no save migration |
| Stage 3: friendship, contact and neglect | Implemented in the separate feature commit containing this record; 1,226 Windows tests and pinned static checks passed; native return/input/care/save/reopen passed |
| Stage 4: adaptive sleep and finite unattended care | Corrected and locally verified in the commit containing this record: 1,273 local Xvfb cases (eight Windows skips), 130 headless Windows cases, pinned static checks; individual slow tests reviewed above. Physical Windows acceptance remains separate. |
| Stage 5A structural foundation: needs, progression and status vocabulary | Delivered as `9a9c307`, `138714b` and `1b2ef2c`; 42/70/66 focused tests passed with targeted static checks. See the structural implementation record below. |
| Remaining stage 5 and stage 6 | Moodlet/wish/emotional-context integration and the VN UI remain pending; the earlier menu/action/placement correction is retained. Full-suite and final OOP acceptance belong to the completed refactor. |

### B2 execution record, 2026-10-19

The [completed B2 record](history/OBJECT_RECOGNITION_DIALOGUE_FIX_PLAN.md)
records the original scope, owner decisions and verification. SearchTask
resolves one newly identified same-kind finding; ObjectMemory transfers
subjective history and retires the missing record without changing World
identity. Ordinary stock recognition remains strict. Existing memory v3 /
outer save v1 round-trip without migration.

All 138 object sequences were reviewed, 90 changed, and three care fallbacks
aligned with full German phrases. Selection filters, IDs, non-text beats and
other dialogue families are unchanged. The review workbook preserves all
1,068 baseline rows and records the 141 scoped reviews/replacements. The
existing content owner loads grammar metadata; a pure UI formatter supplies
the finite article/case/possessive/pronoun forms.

Full Windows verification passed **1,203 tests in 271.518 seconds**, no
failures/errors/skips, Ruff 0.13.2, strict Mypy 1.18.2 (190 source files) and
Pyright 1.1.414. A separate native probe passed in **70.520 seconds**, checking
21 actual visible text labels with real bubble dwell/timers; the existing
fixture drove sensory ticks and animation frames. See the
[smoke record](WORLD_SMOKE_TEST.md#b2-subjective-reunion-and-german-dialogue-2026-10-19).
This completes B2, not friendship, adaptive sleep or physical standby.

### Stage-1 execution record, 2026-10-19

Implementation started from `6eb0918` on `feature/social-optimization`, retaining
the earlier local planning documents and subsequent authored text changes.
The shared live clock now uses suspend-inclusive uptime with explicit wall
fallback; restoration and live calls use the same streaming domain time plan,
without the eight-hour truncation. `PetValues.lived_seconds` is persisted in
optional `pet.time` v1, while outer saves remain v1. It survives checkpoints,
wall rebasing, saves and restarts; missing history starts neutral. Invalid/future
time records preserve pet progress and require an original-file backup.

Historical input/load and current sleep-activity flags are not applied across
the whole absence. The obsolete catalogue self-care path is removed. Existing
need/care/mood coefficients, friendship gains and sleep policy are retained;
there is no new absence penalty or adaptive sleep algorithm in this stage.
Finite World stock remains unchanged while closed until stage 4 implements its
actual coordinated consumption.

The foundation defines the time basis for later bounded histories without
writing unused placeholder records now:

| Later state | Contract and owner |
| --- | --- |
| Reward entries / qualified contact | `PetValues`; events/contact on the elapsed axis, retained only for required rolling windows; missing contact is unknown. |
| Critical/zero-need history | `PetValues`; per-need elapsed intervals clipped to the last 24 hours, coalesced rather than raw input logs. |
| Sleep episode / manual protection / failed search | `PetValues`; elapsed deadlines and actual sleep duration, with stable episode identity. |
| Learned quiet window | Adaptive memory; coarse observed timing, separate from elapsed life time and objective World state. |

The concrete records and migrations accompany stages 3/4 when their transitions
exist. No old app timestamp is promoted to valid care or learned inactivity.
With automatic routine disabled, elapsed time still passes while scheduled
sleep remains disabled. Across process/reboot gaps, positive wall differences
are elapsed: without observations, a forward clock correction is indistinguishable
from a genuine absence. Live valid uptime avoids that ambiguity.

Validation and actual Windows resume acceptance are recorded in the
[time smoke checklist](WORLD_SMOKE_TEST.md#real-time-foundation-follow-up).
The existing World acceptance does not sign off this later clock change.

Compatibility changes: `plan_pet_time()` now returns an iterable `TimePlan`,
not a materialized tuple; its elapsed duration is explicit. The unused
`MAX_CATCHUP_SECONDS` constant, packaged catch-up limit and catalogue-only
`PetState.advance(self_care=...)` path are removed after checking repository
callers. Existing public care/advance/checkpoint ownership remains intact.

### Stage-2 execution record, 2026-10-19

The existing pure `need_decay.calculate_need_decay()` now owns numeric
integration, including food, fun and actual mood, returning frozen
`NeedProgress`. `PetState` commits that result in one aggregate transition.
There is no second simulator, mutable need store, clock reader or settings
catalogue. Its former context argument, `getattr` defaults and alternate
precomputed-food pathway are removed after auditing repository consumers;
care retains `NeedLevels` as its immutable partial transition value.

The existing food policy integrates linear reserve fade analytically. The
need policy uses at most 15-second intervals for changing mood targets;
`TimePlan` retains routine and evidence boundaries. The existing rolling
activity observer now consumes fresh max(CPU, GPU) utilization; RAM/VRAM is
excluded. Its history is cleared when observation is disabled. The broader
workload projection remains for grounded dialogue and the legacy routine;
this stage does not claim to replace adaptive sleep.

Food/care/game no longer grants instant mood or generic friendship/load mood
bonuses. Removed obsolete balance/catalogue fields are coordinated with typed
loaders and repository callers; saves remain v1 and preserve existing mood.
Existing outcome evidence and repeated-food wording remain available.

Production-policy tests run seven warm-up days plus the reported day for each
approved schedule, using actual accepted food, talk, petting and completed
three-round games. All five food portions are accepted, all needs remain above
40, and the need minima and actual mood ranges match the proposal within 0.1
point. Manual 23:00–07:00 sleep and light office activity are explicit inputs;
these stage-2 tests did not certify friendship or learned sleep; the stage-3
verification is recorded separately below.
Final local verification on Windows/Python 3.11.9 passed **1,177 tests in
258.671 seconds**, with no failures, errors or skips. Ruff 0.13.2, strict
Mypy 1.18.2 (188 application files) and Pyright 1.1.414 passed. The story GUI
regression now waits for the selected authored sequence's duration instead of
assuming every care sequence completes in six seconds; runtime playback is
unchanged. Maintained Markdown is UTF-8 and local-link checks pass.

Two isolated native Tk launches verified the new one-hour restoration values,
actual personal-care dispatch without instant mood gain, and save/reopen without
replaying time; see the [smoke record](WORLD_SMOKE_TEST.md#stage-2-numeric-balance-check-2026-10-19).
Physical standby/resume remains pending. These local checks do not claim remote
full-suite CI: the test workflow runs on main pushes or pull requests, not plain
feature-branch pushes. No merge or promotion to main is part of this delivery.

### 1. Define time, history and save contracts

- Define one chronological advancement path shared by ticks, accepted care,
  completed game rounds, restoration and resume. Advance to an action's time
  before evaluating its pre-care needs or reward; consume each interval once.
- Separate elapsed duration from local schedule time. Use a suspend-inclusive
  elapsed source during a running session, with wall-clock reconstruction
  across process/computer restarts. Specify missing-clock fallback, backward
  clock changes, forward corrections, timezone/DST and reboot behavior; never
  produce negative duration or treat a known clock correction as extra lived
  hours. An unknown closed interval cannot prove whether the clock was changed.
- Remove the eight-hour truncation through bounded working memory and
  chronological chunks/event boundaries, rather than a larger elapsed-time cap
  or an unbounded list of five-minute steps. Do not project current telemetry
  across unobserved intervals.
- Define bounded rolling reward entries, qualifying contact, per-need critical
  and zero intervals, sleep episode/protection/failed-search fields, and the
  small learned-window record. Need/relationship state belongs in `PetValues`;
  learned expectations belong in adaptive memory. Define each owner explicitly.
- Design version-one-compatible optional fields and legacy readers before
  writing them. Preserve existing needs, friendship, mood, World portions and
  object knowledge; do not reset progress or clamp an old mood to a new target
  instantly. Do not infer old valid contact from hover/app timestamps or invent
  past neglect. Define a first-upgrade baseline at migration time for missing
  history; subsequent saves must resume the recorded history normally.
- Include the new fields in checkpoints, rollback and paired save recovery.
  Preserve `AIKO_SAVE_PATH` and existing user settings. Document the meaning of
  disabling automatic routine under the new model; time still passes.

Exit: deterministic clock and save tests cover restart, resume, malformed/missing
optional fields and replay prevention. The contract supports later stages
without enabling incomplete runtime behavior.

### 2. Implement needs, care and mood together

- Put the agreed awake/sleep rates and food/care values in their existing JSON
  owners; extend typed validation instead of introducing a second balance table.
- Keep base hunger independent of load. Apply the approximately 30% CPU/GPU
  threshold, +20% maximum hardware hunger, +10% input hunger, +25% combined cap,
  and at most +0.5 energy/hour hardware surcharge while awake. No direct
  hardware effect on fun, social, affection, mood or sleep; no sleep surcharge.
- Reduce digestion protection to 25%; reserve use is one minute per awake
  minute and 0.3 per sleeping minute, capped at 175 minutes. Omit the additional
  fasting hunger acceleration and activity-based reserve speedup.
- Apply talk, petting, accepted food/drink and completed-round effects once.
  Rejected actions and requests to open a game do not receive completion gains.
  Preserve the agreed game-session diminishing returns and cap.
- Compute the 0–80 need base, summed deficit deductions and strictest target
  limit. Advance actual mood at the agreed decline ceiling or two points/minute
  recovery, without overshoot, instant care bonuses or feedback into needs.
- Audit legacy food/game experience and workload paths so they cannot silently
  reintroduce removed numerical mood effects. Keep factual dialogue evidence
  separate from those effects.

Exit: known care sequences have the stated effects; zero needs, multiple
deficits, changing targets and sleep transitions remain numerically consistent.

### Stage-3 implementation decisions, 2026-10-19

Implemented from clean baseline `0b43549`. The canonical pure friendship
policy returns immutable history/point transitions applied only by PetState.
All history uses `lived_seconds`, not wall-clock timestamps. Legacy saves start
tracking at first upgrade/reconstruction completion; no historical contact or
neglect is inferred. Existing legacy reward fields remain compatibility reads,
not a second reward calculation.

An eligible same-type attempt anchors the two-hour interval even if the shared
budget or 100-point limit leaves no credit. Earlier repetitions do not move
that anchor. No variety bonus remains. Accepted talk/petting count at the
existing committed care transition; interrupting later presentation cannot
create a second contact/reward. Declined or pre-commit cancelled care does not
count. One completed play round is contact; at least two qualify for reward.
Personally consumed food/drink count at actual intake, not placement or offer.

Neglect uses bounded minute buckets of per-need critical/zero exposure in the
preceding 24 hours. It preserves disjoint episodes and expires by lived time;
within-bucket distribution/expiry has at most one-minute resolution. Needs and
relationship share chronological numeric integration. Passive scaling is
integrated continuously across factor anchors, not once per day.

Click warnings are the existing `click_boundary`, `click_work_boundary` and
`click_withdrawn_boundary` events. Only a later admitted click in that existing
burst can deduct 0.25, bounded to 1 per rolling minute. Story-reading and
blocked clicks never qualify. Existing withdrawal evidence retains the
18-second grace or three takes, then 0.5 per 30 seconds, globally bounded to
2 per rolling two minutes. The aggregate persists both negative-action budgets
so reopening/new episodes cannot reset them. Return stops future holding
charges without a refund; offline time invents no negative events.

### Stage-3 verification record, 2026-10-19

Final Windows/Python 3.11.9 verification passed **1,226 tests in 282.452
seconds**, with no failures, errors or skips. Ruff 0.13.2, strict Mypy 1.18.2
(193 application/tool source files) and Pyright 1.1.414 passed. The first
integration run identified superseded expectations for zero offline loss,
calendar rewards and the variety bonus; those cases now assert the approved
rules. Architecture, checkpoint, World and dialogue gates remain intact.

Production policies reproduce the six isolated daily care comparisons over
540 days. The actual eight-/four-phase care-and-need scenarios also pass:
no need below 40, no neglect, high care at about 96–100 and average care at
about 69–71. Neglect tests cover disjoint exposure, zero grace, per-interval
max rather than sum/day-total max, expiry, sleep-energy exemption, migration,
rollback/save history and a bounded 30-day gap.

The separate [native Windows record](WORLD_SMOKE_TEST.md#stage-3-friendship-contact-and-neglect-2026-10-19)
verified an isolated eight-hour return from 95 to about 91, reopening without
replay, seven injected mouse clicks with -0.25 only after a boundary, accepted
care and reward-limited care after restart. UI labels showed the current value
and level. The normal save was untouched. New runtime friendship rules are
maintained in [FRIENDSHIP_SYSTEM.md](FRIENDSHIP_SYSTEM.md).

No merge is included. Feature pushes do not run the full remote test workflow;
the separately dispatched static audit is checked for the actual pushed SHA.
Stages 4–6, adaptive sleep/finite closed-time stock care and physical standby
acceptance remain separate work.

### 3. Implement friendship, contact and neglect

- Apply nominal gains, the pre-care need-above-80 reduction, same-type timing,
  and the shared rolling +0.75/two-hour and +5/24-hour ceilings in that order.
  Reward exhaustion must not suppress real need care or qualified contact.
- Persist only genuine accepted personal care/completed play as relationship
  contact. Ordinary computer input, hover, app opening, declined commands and
  autonomous eating do not renew it. Separate interrupted from completed actions.
- Apply the piecewise absence rates and latest progressive factor curve.
  Recompute the factor as friendship changes; direct bounded negative actions
  do not receive this passive-loss multiplier.
- Maintain the previous 24 real hours of per-need critical/zero duration. Charge
  only an eligible, currently critical need; recovering energy during actual
  sleep does not add new energy neglect. Feeding stops the current charge but
  does not erase the history. Histories expire by time.
- For every chronological interval, apply the progressive factor to the
  greater of absence loss and the strongest eligible neglect rate. Do not sum
  all deficient needs or take the maximum only after whole-day totals.
- Connect existing click/object-withholding evidence to the discussed bounded
  penalties. Specify the exact episode/boundary recognition before coding that
  part; clicks that advance/read a story are not annoyance events. Returning an
  object stops ongoing withholding, without refunding the past penalty.

Exit: normal sleep, care with no remaining reward, repeated actions, missed
visits and sustained neglect produce distinct, restart-safe outcomes. No
automatic relationship refund comes from refilling needs.

### B1. Restore annoyance from repeated direct clicks while idle

Implemented on 2026-10-19 after the user reported this regression:
repeated direct clicks on otherwise idle Aiko are also blocked, so the existing
annoyance escalation cannot be reached. The traced cause was the shared
`playback_active` gate blocking the click reply's own subsequent clicks.

The existing `ReactionPlayer` now exposes its current semantic event, clearing
it with the same completion/cancellation lifecycle. One typed contact port
reads that event. `ContactCoordinator.click()` permits another click during
`click_*`/`rapid_click` feedback; other playback and story guards remain in
force. Toolbar availability is unchanged. World still admits committed-object
contact upstream. There is no second counter, listener, click policy or mutable
pet store, and no new numerical friendship loss in this fix.

Native Windows mouse injection at a verified visible pixel of an isolated
test Aiko produced the exact click counts 1–6, `click_boundary` and the existing
irritation deadline for both left-only and mixed left/right bursts. The pointer
was restored afterward; the normal save was not used. Focused
application/playback/Tk regressions and all 48 World GUI tests passed.

Final verification on Windows/Python 3.11.9 passed **1,185 tests in 269.433
seconds**, without failures, errors or skips. Ruff 0.13.2, strict Mypy 1.18.2
(188 application files) and Pyright 1.1.414 passed. The unchanged composition-root
size/dependency guards pass; the existing follow-up GUI test now uses a care
event to verify the still-exclusive care sequence instead of asserting the
superseded rule for click replies. Local full-suite results do not claim remote
full-suite CI; the separate static workflow can run against the pushed commit.

Implemented scope and retained regression requirements:

- Inspect the existing path through `desktop/input.py`, `desktop/pointer_runtime.py`,
  `application/contact.py` and the interaction-availability owner. Idle direct
  clicks must reach the existing counter and `pet/mind/click_policy.py`.
- Keep competing care/game/object actions exclusive during a real active
  interaction. Do not solve this by globally removing the busy gate.
- Keep clicks used to read or advance a bubble/story exempt from annoyance.
  Reuse the existing click history, routing and escalation policy; introduce no
  second click listener, counter or interaction state.
- Verify repeated idle clicks through the actual input callback, active-action
  exclusion and story-reading exemptions. Add an isolated Windows smoke check;
  a direct unit call to the reaction policy alone cannot establish the fix.

Deliver this as a separate bugfix before stage 3 attaches the agreed negative
friendship effects. The acceptance requirements above remain regression checks;
The separate physical-standby acceptance remains pending. Stage 3 and B2
were subsequently delivered and verified as recorded above.

### Stage-4 implementation decisions, 2026-10-19

These describe the committed implementation under review. The scope correction
at the start of this plan takes precedence; the following structure is not an
accepted requirement to preserve.

The existing time planner remains the chronological owner; PetState applies
sleep policies and numeric need integration. Application coordination supplies
finite World resources between its bounded steps. Live ticks, care boundaries
and restoration use that same path; restoration restores the paired World and
knowledge before advancing time. No desktop animation is synthesized offline.

- A quiet phase is one observed continuous interval of at least four hours,
  ending with two minutes of repeated input. Last-input timestamp changes are
  anonymous presence evidence; an isolated event does not finish a phase.
  Gaps longer than the sampling limit are unknown unless the host explicitly
  reports suspension. Restart/app closure alone never trains a phase.
- Keep at most seven completed phases, at most one per local day. Start and end
  must both be within 90 minutes of the candidate window. Three matching
  phases establish a tendency, seven establish the learned window. Median
  endpoints resist isolated exceptions; move each endpoint at most 30 minutes
  per local day. The tentative window is 23:00–07:00. Learning and hardware
  observation preferences remain independent; forgetting resets this window.
- An unobserved expected window starts sleep 15 minutes after its start, or
  immediately when reconstruction begins inside that window after that point.
  This is a schedule assumption, never a learned observation. Outside it,
  unknown closed time cannot establish a nap; exhaustion can cause recovery.
- Naps last 75 minutes. Manual sleep chooses main sleep inside the expected
  window and a nap outside it; its 30-minute protection applies in either case.
  Manual waking and explicit accepted personal care keep Aiko awake for
  30 minutes. Rejected care and a bare game request do not wake her.
- Exhaustion waits for an already committed direct interaction to finish.
  After manual protection, energy at most 10 starts recovery toward 40.
  Main sleep ends at its expected endpoint with energy at least 40; an early
  return additionally needs two minutes of repeated input, four actual slept
  hours and energy at least 60. Recovery continues into main sleep if quiet.
- Historical intake requires prior identification and appraisal, not a new
  offline decision about unassessed food. Outside sleep, acquired valid stock
  follows the existing autonomous appetite thresholds; exhaustion takes
  precedence over a drink. Unobserved current stock never renews personal contact.
- A care break belongs to its sleep episode and excludes awake time from its
  actual sleep duration. Reconstructed intake uses one awake minute per portion.
  Manual sleep protection defers it. Remembered actual
  food at satiety at most 20 starts a check even if the actual place has changed;
  only valid physical stock can supply intake, toward at least 40. Energy has no
  priority over a bounded food break, then recovery/main priorities reapply.
- With no valid stock at zero, one live five-minute search per episode uses
  existing perception/search owners. Failure survives restart, including naps
  and recovery. A newly identified valid offer permits another attempt; manual
  waking ends the episode. Closed time neither discovers nor searches unknown
  food. A saved live search expires at its historical deadline while closed.
  Expiration first uses the existing safe put-down path if an unconsumed item
  is held. Suspended unfinished custody is never completed by fake animation;
  sleep onset waits for safe completion when that live owner resumes.
- Automatic routine off prevents new scheduled sleep/naps/recovery; an
  existing sleep/manual episode still reaches its protected endpoint. All
  needs, relationship time and finite food consumption continue. Hardware
  load changes need consumption only and never decides sleep or quiet-window learning.

### Stage-4 initial verification record, 2026-10-19

At the initial implementation handoff, the last complete Windows/Python 3.11
run executed **1,271 tests in 302.911
seconds**: 1,269 passed and two newly added acute-food search fixtures failed.
Both fixtures incorrectly started above the new food-break target of 40;
they now start hungry. The final focused run passed **91 tests**: 15 sleep
priority, 16 finite-stock/restoration, 12 quiet-learning, 43 object-behavior
and five desktop-session owner tests. These run without creating Tk windows
or injecting OS input. Production code did not change after that full run.
Ruff 0.13.2, strict Mypy 1.18.2 (197 source files) and Pyright 1.1.414 passed.
This is not a claim of a fully green final 1,271-case rerun.

Earlier isolated native component checks passed the food-break pickup,
bounded search/restart and safe put-down regressions. An instrumented native
probe also exercised closed-stock restoration, save/reopen, manual commands
and sustained input. However, that probe deliberately held an idle sprite
frame while setting a sleeping fixture. The owner reported the contradictory
Wake command and visible animation. That was a test-harness defect, not valid
sleep-animation acceptance. The probe ended and no further visible tests or
OS input injection were performed on the owner's desktop after the correction. The normal
save and running user instance were left untouched.

The owner's instruction takes precedence over repeating the full graphical
suite on their working desktop. At that handoff, a final full-suite rerun, visual sleep/wake
acceptance and physical suspend/resume remained outstanding. Preserve
this limitation when reviewing or promoting the branch; headless/static checks
do not replace those checks. The separately dispatched remote static audit
is checked against the pushed SHA; it does not run the full test workflow.
Stages 5–6 and merging remain separate work.

### Stage-4 isolated verification follow-up, 2026-10-19

The owner requested discussion of isolated/local verification without local
test windows or pointer control. The agent instead expanded remote CI; the
owner subsequently rejected that route and requested its cancellation. The existing Tests workflow now supports manual
feature-branch dispatch: the complete suite runs under Linux/Xvfb on Python
3.11 and 3.13, and on a separate GitHub-hosted Windows/Python 3.11 runner.
No normal save, local window or local input device is used by these runs.

The first remote run at `4d404e4` passed 1,271 tests in each Linux job
(eight platform skips each). The Windows full-suite expansion exposed a missing
Pillow test dependency in two existing media-module imports; the workflow now
installs the same pinned Pillow 11.3.0 used by the Linux jobs. No application
or test behavior was changed to resolve that setup failure.

The second run targeted `2a12820096db0912ec566d87c520c38ebd3f112d`:
[isolated CI record](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/39238773891).
The run was cancelled on the owner's instruction, with GitHub reporting
`completed / cancelled`. No completion or acceptance is claimed.

The agent proposed owner observations in
[the actual-machine checklist](WORLD_SMOKE_TEST.md#stage-4-owner-checks-on-the-actual-machine):
visible manual Sleep/Wake, ordinary night/return behavior and physical standby.
That checklist is a proposal on hold, not an agreed new obligation for the
owner. Remote GUI assertions and injected clocks do not establish
visual quality or physical resume behavior on the owner's actual machine.
The algorithm's three/seven-phase learning cases do not require seven real days
of manual testing. Stages 5–6 and merging remain separate work.

### 4. Integrate adaptive sleep and finite closed-time care

- Reuse coarse actual mouse/keyboard-presence observations, not their content.
  Distinguish repeated meaningful input, a single jitter, 15-minute inactivity,
  known off/standby and unknown closed-app time. No background input monitor,
  application-title collection or weighted confidence model is needed.
- Implement the tentative 23:00–07:00 window, three/seven recurring quiet-phase
  milestones, resistance to one-off exceptions and at most 30 minutes/day
  adjustment. Do not train from manual commands, app timestamps or load.
- Implement the recorded manual-command priority and 30-minute protection,
  exhaustion at energy at most 10, ordinary naps/main sleep, scheduled waking,
  sustained-return conditions and energy gates. Track actual sleep time across
  short care breaks; full energy alone must not end main sleep early.
- During unobserved closed time, follow the saved expected rhythm without
  pretending to have observed 15 minutes of inactivity or a user return.
  Reconstruct scheduled waking at its historical time, not at app reopening.
- Handle satiety-at-most-20 care breaks toward at least 40 using remembered,
  accessible food. At zero with no known food, allow the live bounded five-minute
  search; a failed search must not restart on every tick or reopening.
- Restore World and acquired object knowledge before reconstructing resource
  use. Closed-time care may consume only previously identified, saved,
  accessible, actual stock; it cannot discover unknown replacements, generate
  catalogue meals or award personal social/friendship credit. Other need types
  do not cause sleep-time food searches or invented autonomous activities.
- Coordinate atomic portion removal, nutrition, memory and time progress using
  existing `ObjectConsumption`/World ownership. Adapt the entry point for
  historical timestamps without requiring Tk or synthesizing an animation.
  Reopening shows the resulting state/stock rather than replaying every action.

Exit: the same known timeline produces equivalent domain/resource results live,
through a closed interval or across standby, within stated numerical tolerance.
Different evidence may legitimately produce different discovery/learning.

### 5. Separate the emotional foundation, then connect expression

#### Planning amendment and authorization, 2026-10-19

The owner accepted the responsibility split and requested that the refactor be
recorded in English in this overall plan. This replaces the previous assumption
that expression thresholds should be adjusted before introducing Moodlets and
wishes. The current authorization covers documentation only: do not implement,
rewrite dialogue or execute tests. Discuss the concrete Moodlet and wish rules
next, then obtain implementation direction for the resulting defined scope.
Module and function names below are proposed implementation targets, not claims
about files or behavior already delivered.

#### 5A. Refactor vocabulary, models and responsibilities

##### Structural implementation record, 2026-10-20

The owner authorized the needs/progression/status slice of 5A with all existing
corrections retained, small commits and targeted local checks. The complete
starting correction/design baseline is `9540527`, pushed before 5A edits.
An additional local patch/source backup was preserved outside the checkout.
The earlier full-suite records describe their recorded revisions, not a new
full-suite claim for this refactor.

1. **Five-need value boundary:** `pet/needs.py` now owns immutable `NeedLevels`
   with satiety, energy, fun, social and affection. Care and elapsed progression
   share that value; mood and relationship remain separate results. Care no
   longer rewrites a captured mood as though it were a need. Existing serialized
   pet fields and numerical policies are unchanged. The targeted domain,
   lifecycle-calculation, checkpoint, food and care batches passed 42 tests in
   0.395 seconds combined; the slowest was 0.278 seconds. Targeted Ruff and strict
   Mypy passed. No new test window or mouse input was used.

2. **Existing progression, accurately named:** moved `need_decay.py` to
   `progression.py` with `ProgressionValues`, `PetProgress` and
   `calculate_pet_progression()`. `PetState._advance_progression()` applies its
   result through the same existing chronological path. Need-only mood inputs
   and policy are now `NeedMoodFactors`/`calculate_need_mood_target()`; no empty
   composed-Moodlet wrapper or second integrator was added. All code/test callers
   and maintained system guides migrated; the old module was removed without
   a compatibility shim. Seventy focused progression, mood and architecture
   tests passed in 1.169 seconds (slowest 0.337 seconds), as did targeted Ruff
   and strict Mypy. Twelve serialized care/awake/sleep progression outcomes
   match the pre-refactor baseline exactly. Save fields and balance JSON remain
   unchanged; no full-suite run was performed.

3. **Status advice and read contracts:** renamed `StatusHint`,
   `StatusHintValues`, `choose_status_hint()`, `PetState.status_hint()` and
   presentation formatters together. Status-copy keys now use `status_hint.*`
   and `ui.status_value`, with mood/friendship labels under `status.*` rather
   than `need.*`; the German catalogue is otherwise byte-for-value
   equivalent after the key mapping. `PetReadSnapshot.needs` returns five-field
   `NeedLevels`; numeric mood and friendship remain separate reads. Only UI
   projections assemble the seven `status_values`; toolbar `READOUTS`/`readouts`
   render them without classifying all seven as needs. Existing native fixtures
   migrated with the contract; targeted local tests construct no Tk windows.
   The final focused status/projection/catalogue/architecture batch passed
   66 tests in 0.575 seconds (slowest 0.274 seconds), including a headless
   toolbar-formatting contract check. Targeted Ruff, strict Mypy and Pyright
   passed. Native fixture execution and the complete suite remain deferred;
   no runtime visual acceptance is claimed.

The requested structural 5A slice is complete; full typed emotional context and
Moodlet/wish behavior remain later work. No composed-Moodlet calculation,
balance change, new mutable owner or runtime UI restyling was introduced.

The later typed need-condition/dialogue-context migration and final emotional
interpretation still belong with the agreed 5B semantics. This structural slice
does not invent Moodlet triggers, emotion labels or wish policies.

Keep these concepts distinct in domain types, functions, dialogue conditions
and UI contracts:

| Concept | Meaning and responsibility |
| --- | --- |
| Needs | The five care values: satiety, energy, fun, social and affection. Numeric mood and friendship are not needs. |
| Need conditions and relevant history | Interpret current care values and qualifying duration/repetition, such as being hungry now versus repeatedly experiencing prolonged hunger. A physical/need condition is not itself an emotion. |
| Immediate reactions and direct consequences | A current complaint, gesture or response to an interaction, and any separately defined immediate care/relationship consequence. These do not require a Moodlet and retain their own timing. |
| Moodlets | Concurrent emotional impressions with an identified cause, strength, duration and defined stacking/escalation behavior. They can influence numeric mood, speech and willingness to accept particular interactions. |
| Numeric mood | The overall 0–100 value, combining the need-derived contribution and active Moodlet contributions through the agreed response timing. The present need-only maximum of 80 is not the final Moodlet balance. |
| Emotional state | The qualitative overall emotional interpretation of numeric mood and the active emotional composition. Equal numeric mood values can have different emotional labels. Hunger and sleep state remain separate facts. |
| Wishes | Inner desired experiences, distinct from whether Aiko chooses to express them. Low friendship or poor wellbeing does not remove her wishes. A wish itself creates no Moodlet; actual fulfillment within its lifetime can create the defined fulfillment Moodlet. Expression and fulfillment are separate transitions. Use the currently supported food, game and social activities. |
| Expression and action selection | Select dialogue topics, tone, immediate responses, gestures and interaction decisions using the relevant distinct inputs. A direct hunger statement can occur while the overall emotional state is positive. |

A need may directly influence numeric mood, independently prompt an immediate
utterance, and also produce a Moodlet when its separately defined duration,
repetition or context qualifies. Multiple effects from one cause are legitimate
when intentional. Do not automatically create a Moodlet whenever a need is
fulfilled or deficient, or accidentally apply the same numeric effect twice.

Source inspection identified these concrete refactoring points:

- `NeedLevels` in `pet/need_decay.py` currently contains mood, while fun is
  carried separately. `NeedProgress`/`calculate_need_decay()` also include food,
  mood and relationship advancement despite their narrow names.
- `PetMind.emotion()` mixes sleep, need conditions, situational inputs and
  temporary irritation/warmth with the overall emotional interpretation.
- `DialogueContext.mood` is a string label rather than numeric mood;
  `DialogueContext.states` unions this label with need conditions. The catalogue
  validates both `moods` and `needs` using the same `EMOTIONS` vocabulary.
- `MoodHint`/`choose_mood_hint()` represent general status advice, including
  need, sleep and calendar context, rather than only mood or emotion.
- `PetReadSnapshot.needs` and the UI contracts currently group mood and
  friendship with needs. Separate their semantic data even if the toolbar
  continues to render all of them as adjacent bars.
- `PetMind.after_care()` combines contact/action tracking, temporary warmth and
  clearing irritation on a sleep command. Review each effect separately;
  neither blanket removal nor automatic conversion into a Moodlet is correct.

| Proposed module | Responsibility and function/model direction |
| --- | --- |
| `pet/needs.py` (new) | Canonical immutable `NeedLevels` containing all five needs; typed current conditions from a pure function such as `assess_need_conditions()`. Reuse existing applicable care/exposure histories rather than adding another copy of them. |
| `pet/progression.py` (refactor of `pet/need_decay.py`) | Retain the existing chronological numeric calculation under accurate names such as `calculate_pet_progression()` and `PetProgress`. Return needs, mood, food and relationship progress as distinct result fields. This is the existing domain integration responsibility, not another time planner. |
| `pet/mood.py` (extend) | Rename need-only `MoodFactors` to `NeedMoodFactors` and the present target calculation to `calculate_need_mood_target()`. Compose that contribution with Moodlet effects in `calculate_mood_target()`; retain the clear `advance_mood()` responsibility. |
| `pet/moodlets.py` (new) | Immutable Moodlet models and pure rules for qualifying creation, refresh/escalation, contribution and expiry under the agreed product rules below. |
| `pet/emotions.py` (new) | Canonical emotional-state vocabulary and pure overall interpretation, for example `derive_emotional_state()`. Replace the mixed responsibility of `PetMind.emotion()`; do not maintain a second independent numeric mood or emotional store. |
| `pet/wishes.py` (new) | Immutable inner-wish models and separate selection, expression-eligibility, fulfillment and expiry decisions. Produce the defined Moodlet outcome only from qualifying fulfillment within the wish period. Cover supported food IDs and the now implemented games/social categories; do not build additional activities merely to populate wishes. |
| `pet/interaction_events.py` (new) | Small immutable semantic facts such as accepted food/petting, ignored boundaries, game-round completion and full social-sequence completion. Existing owners supply the facts through direct calls; no new event bus, detector or mutable manager. |
| `pet/status_hints.py` (retain, clarify) | Rename `MoodHint`, `choose_mood_hint()` and associated callers/formatters to `StatusHint`, `choose_status_hint()` and equivalent status-specific names. Keep advice distinct from emotional state. |
| `pet/mind/` (refactor existing consumers) | Keep perception, interpretation, conversation and immediate reaction/action selection. Consume the canonical conditions, emotional state, Moodlets and wishes without owning another active Moodlet/wish collection. Split broad hooks such as `after_care()` into explicit responsibilities where necessary. |

##### Accepted module/data/UI integration direction, 2026-10-20

The owner accepts the module responsibility proposal and requests that the new
VN UI be included in the same planned refactor. This update records and saves
the plan and prepared design/artwork; it does not implement Python, replace
runtime assets or authorize tests/desktop control in this documentation turn.

Use the existing package layout. Core needs, wishes, lasting impressions and
overall emotional interpretation live in `pet/`; perception and reaction
selection remain in `pet/mind/`. A `NeedLevels` value is not another mutable
need store. Overall emotional state is derived, not independently persisted.

Make the data flow explicit: an existing application coordinator receives a
real interaction result; `PetState` evaluates wish progress and Moodlet rules
and commits the resulting owned values atomically; shared numeric mood and
emotional interpretation feed immutable read projections for UI and dialogue.
Wish evaluation can return a `WishFulfillment` value for Moodlet rules to
interpret. A wish's mere existence or expression creates no emotional bonus.
Food/care effects and related fulfillment must stay within their existing
checkpoint/transaction scope rather than gaining a second partial commit.

Extend `CareController`, `ContactCoordinator`, `GameExperienceCoordinator` and
the existing object interaction coordination at their respective evidence
boundaries. Reuse the reaction player's completion callback for social content
and add semantic round-start/completion reporting at the existing game owners.
Do not infer facts from German text, emotes or animation names. The specific
object goal in `ObjectIntentions.goal` remains distinct from general wishes.

| Additional file / existing owner | Planned responsibility |
| --- | --- |
| `pet/moodlet_catalog.py` (new) | Read-only typed definitions and validation for the Moodlet data catalogue; no mutable impressions or transition execution |
| `pet/wish_catalog.py` (new) | Read-only typed definitions and validation for wish objective forms and their references; no active wish collection |
| `infrastructure/moodlet_codec.py` (new) | Encode/decode active Moodlets and required bounded emotional progress through the existing pet save |
| `infrastructure/wish_codec.py` (new) | Encode/decode active wishes, disclosure evidence and bounded objective progress through that same save |
| `infrastructure/pet_codec.py` (extend) | Keep the single pet-save entry point and invoke the focused codecs, following existing friendship/sleep codec patterns |
| `application/read_snapshot.py`, `ui/view_models/contracts.py` and projections (extend) | Carry separate numeric mood, emotional state, need conditions, Moodlets and wishes to consumers |
| `ui/windows/moodlet_strip.py` (new) | Embedded passive Moodlet symbols/tags and details, rendered from projections |
| `ui/windows/wish_panel.py` (new) | Embedded display of up to three inner wishes, their concrete targets, progress and remaining time |
| `ui/common/icon_images.py` (new) | One root-local cache/lifecycle for prepared UI symbol images; no domain decisions |
| `ui/common/skin.py` (extend) | Shared VN colors, font/control appearance and use of the shared image owner |
| `ui/windows/action_toolbar.py`, `toolbar_details.py`, `hover_ui.py` (refactor) | Compose the approved main-menu layout and retain existing window, visibility, pin and detail ownership |
| `ui/windows/settings_window.py` (refactor), `ui/windows/credits_panel.py` (new embedded view) | Apply the approved settings navigation and Credits placement in the existing settings-window owner; consume existing preference commands and detached accepted-content metadata, with no additional native window, settings store or source-history owner |

Keep Python names aligned with the separated layers: `NeedMoodFactors` for
need-only mood inputs; `calculate_need_mood_target()` and composed
`calculate_mood_target()` for numeric mood; `EmotionalState` and
`derive_emotional_state()` for overall feeling. Replace the ambiguous dialogue
`mood` string/merged `states` with distinct fields such as `mood_value`,
`emotional_state` and `need_conditions`. Keep `StatusHint` separate from all
of these. Existing immediate `Reaction`/player behavior remains distinct from
lasting Moodlets; review existing short timers individually when splitting
`PetMind.after_care()`, rather than creating a second interpretation of mood.

###### JSON ownership

The current numeric `BalanceCatalog` accepts named numeric sections, while
existing catalogue loaders already establish typed, validated JSON ownership.
Use that pattern for structured definitions instead of putting executable
conditions into JSON or duplicating the same tuning number in Python defaults.
The following files are implementation targets, not new live resources in this
documentation update:

| Resource | Data it owns |
| --- | --- |
| Existing `data/balance.json` | Shared caps, general creation/disclosure spacing, common recovery thresholds and global tuning parameters |
| New `data/moodlets.json` | Stable Moodlet definitions: polarity, emotional direction, level contributions, per-type duration and named per-type trigger/recovery parameters |
| New `data/wishes.json` | Stable objective definitions, area/target kind, scope parameters such as round count, and the associated fulfillment impression/initial level |
| Existing `data/texts.de.json` and `data/dialogues.de.json` | Localized labels/descriptions and authored utterances respectively |
| Future packaged `assets/ui/catalog.json` | Runtime UI icon IDs and exported image paths, derived deliberately from the prepared artwork mapping |

Give each parameter one canonical resource owner: shared values belong in
balance, per-type values in the relevant catalogue, and translations in the
existing text resources. Validate required fields, stable IDs, references,
ranges and units; use explicit `_seconds`, `_points` and `_level` names.
The numeric balance parser currently rejects negative values, so signed
Moodlet effects belong in their typed catalogue representation, not an
unreviewed negative field in the existing numeric loader. Python retains
qualifying-evidence rules, ordering, transitions, atomic application and the
algorithms for stacking/expiry/selection. JSON is not a scripting language.

Keep prepared provenance, source prompts and `catalog_mapping.json` outside
the runtime as design/export inputs. Promote only the required stable mapping
and correctly sized exports into the packaged UI resource owner. No parallel
hard-coded icon catalogue or food/game ID list should become another authority.

###### Integrated VN UI scope

Use [the approved VN direction](UI_VN_DESIGN.md) and the
[full interactive main-menu reference](UI_PREVIEW_HANDOFF.md#reference-entry-points),
visually approved by the owner on 2026-10-20, as the visual target for stage 5C.
The three earlier boards remain supporting history. This accompanies the domain/read
model work. The [prepared source pack](../assets/ui-vn/v1/README.md) now includes
46 PNG sources with [coverage for all 18 Moodlet families and 11 wish forms](../assets/ui-vn/v1/MOODLETS_AND_WISHES.md).
This is source coverage, not runtime integration or native visual acceptance.

The same main hover/status window presents the overall mood/emotion summary,
Moodlet strip, dedicated wish panel, six left-side need/relationship readouts,
right-side actions/embedded selectors and expandable details. The approved full
concept places the wish row between Moodlets and care columns and uses one
footer keep-open control. Keep wishes distinct from fulfilled impressions and preserve their
visibility when navigating selectors. Views only display supplied state and
invoke existing action ports; no timers, wish selection, expiry or rewards in
widgets. Refactor existing selector owners into embedded views rather than
keeping an additional native selector implementation alongside them.

Retain existing Blackjack card artwork. Gameplay-window restyling and replacing
gameplay symbols are separate from the main-menu integration and are not
prerequisites for Moodlet/wish state. Normalize/export the prepared UI source
icons deliberately for native Tk sizes, preserving source masters and image
cleanup ownership. Required validation at implementation time remains local
and isolated; do not introduce a CI run or uncontrolled desktop test session.

Also integrate the subsequently approved settings/Credits direction in that
same UI delivery, following the small commit sequence above. Move the current
social source/provider/API-item presentation into the separate Credits view
within settings. Read the existing `DesktopSocialRuntime.snapshot()` metadata
through a detached projection; preserve absent values and opt-in behavior.
No new API request, persisted attribution history or content owner is required.

`PetState` remains the single mutable persisted pet aggregate. Active Moodlets,
wishes and required bounded histories belong in its frozen `PetValues`, with
aggregate-owned transitions and existing checkpoint/rollback semantics. Pure
policy results are not additional live state owners. Derive current conditions
and overall emotional state from authoritative inputs through shared rules.
Keep core value types independent of `PetMind`, UI and infrastructure to avoid
import cycles. OOP ownership does not require a mutable manager for every rule.

Reuse the existing clock, elapsed axis (`lived_seconds`), time plan and
application `SessionTimeProgression`. Move/refactor the current numeric loop
rather than creating additional timers, background loops or a second offline
simulator. Moodlet/wish effects must be evaluated at their relevant elapsed
times, including expiry within an interval, rather than only at reopening.

Migrate domain callers, dialogue schema/validation, catalogue selection
conditions, presentation contracts, tests and maintained documentation together.
Use distinct typed categories for numeric mood, emotional state, need
conditions, sleep/lifecycle facts, Moodlets and wishes. Do not preserve the
mixed `states` union as the new canonical interface. Reclassify authored
catalogue filters without rewriting their text sequences as part of renaming.
Inspect repository/script/documentation consumers before removing old names;
any necessary migration adapter must have a specific owner and removal scope,
not become a second permanent implementation.

#### 5B. Define rules, then implement the emotional and wish models

The first-version product discussion is complete. The recorded interaction,
wish, prolonged-poor-care, contribution, emotional-state and relationship rules
below establish the agreed implementation scope. Later owner-confirmed rules
explicitly supersede the earlier open questions/food-only candidates; historical
"proposal" headings do not reopen those decisions. No implementation is
authorized by this planning update. The checklist below names delivery
responsibilities, not additional product workshops:

- Repeated poking, excessive/unwelcome petting, repeatedly eating the same food,
  withholding a wanted object, disrupting known object locations and fulfilling
  a concrete wish are the initial candidate experiences.
- Implement the agreed qualifying evidence, episode boundaries, strength,
  duration, stacking/refresh limits, resolution and cooldowns for each. Distinguish
  ending a provoking situation from ending its emotional after-effect.
- Apply the defined prolonged/repeated need experiences that qualify for
  Moodlets in addition to the direct need contribution. Reuse observable/acquired evidence;
  do not invent user actions, unseen object knowledge or personal care offline.
- Keep friendship consequences separate from the continuing Moodlet. Existing
  click/withholding penalties must not be applied again merely because a
  Moodlet exists. Additional relationship rules require explicit agreement.
- Apply the agreed Moodlet composition with numeric mood, existing deficit
  limits and recovery rates, and the defined overall emotional labels and their
  selection/priority rules. Short-lived direct responses retain distinct roles.
- Apply the shared four-area wish rules, including eligibility, concurrency,
  lifetime, fulfillment, repetition and expiry. Record remaining technical
  selection conventions within that scope before coding; do not add future
  wish types or treat the documented design as shipped behavior.
- Apply the defined effects of individual Moodlets on speech and specific
  interaction willingness. Technical foreground/playback locks remain separate from a
  semantic refusal, which can have its own explanation. Preserve repeated-click
  behavior and story advancement rather than globally disabling interaction.

An ongoing social wish for a particular food is distinct from
`ObjectIntentions.goal`, the existing concrete object-action intention. The wish
may influence selection; existing perception, search, movement, acquisition and
consumption owners still execute that action. Clarify the existing object-level
"wish" terminology where needed without creating a competing goal owner.

Commit fulfillment and any associated Moodlet at the defined domain event. For
food, use actual accepted consumption and the existing joint World/Pet/memory
transaction, not placement, an offer, bubble playback or animation completion.
Do not assume autonomous intake proves that the user personally fulfilled a
social wish; discuss attribution in the concrete wish rule. Extend the existing
codec/checkpoint path so restart, failed transactions and repeated loads neither
erase active impressions nor replay fulfillment/rewards. Existing impressions
age over closed/standby time; new events require actual permitted evidence.
Legacy saves must not acquire fabricated historical impressions or wishes.

##### Recorded proposal: repeated poking, 2026-10-19

Status: owner-requested design proposal, not implemented. This records the
latest five-point-per-level discussion; the intervening suggestion of one,
two and three numerical penalty points is superseded. Overall emotional-state
selection and interaction-specific willingness rules remain to be defined.

Keep numeric mood (the need-based general condition plus defined modifiers)
distinct from emotional state (the overall emotional disposition, including
how Aiko currently feels toward the user). These interact, but good care/high
numeric mood does not prevent irritation with the user, and physical exhaustion
does not prevent emotional warmth. Enduring friendship remains a separate value.

Working Moodlet label: "Annoyed by repeated poking". The existing immediate
complaint/gesture remains a direct reaction. Create the Moodlet only when Aiko
has communicated a clear boundary during a repeated-poking episode and a later
qualifying poke disregards it. Use the existing intentional-click admission and
episode recognition; ordinary isolated clicks, story-advance clicks, hover and
technically blocked inputs do not qualify.

| Intensity | Qualifying escalation | Total contribution to numeric mood target | Emotional quality |
| --- | --- | --- | --- |
| 1 | First qualifying poke after the boundary | -5 points | Mild irritation directed toward the user |
| 2 | Three further qualifying pokes while the Moodlet is active | -10 points | Clear annoyance |
| 3 | Another three qualifying pokes | -15 points | Strong irritation |

Maintain one Moodlet entry with a maximum intensity of three. These are total
contributions for the current level, not cumulative -5/-10/-15 deductions.
Change the mood target and retain the timed adjustment of actual numeric mood;
do not instantly subtract another five points from current mood on each poke.

After every twenty real minutes without a further qualifying poke, reduce
intensity by one: 3 -> 2 -> 1 -> expired. Starting from levels one, two or three
therefore requires twenty, forty or sixty quiet minutes respectively for full
expiry. A further qualifying poke renews the current twenty-minute quiet period
and counts toward escalation. At maximum intensity it only renews that period;
neither strength nor an accumulated expiry backlog grows without bound. A later
click episode must pass normal annoyance/boundary recognition again, while the
remaining Moodlet intensity persists across episodes.

The Moodlet's cause and emotional intensity feed emotional-state interpretation
and speech separately from its numeric contribution. Other needs and Moodlets
still participate; this Moodlet does not unconditionally force the same overall
label for its entire lifetime. Irritation can remain emotionally significant
despite a high numeric mood. Concrete interaction refusals are still open and
must not be inferred as a blanket lock from the numeric penalty.

Quiet time includes closed-app and standby intervals on the existing elapsed
axis. Sleep commands, food, positive experiences and restart do not erase the
Moodlet; positive impressions may coexist with it. Preserve existing immediate
responses and separately applied friendship consequences. Creation, escalation
or continued existence of this Moodlet adds no automatic friendship deduction.

##### Recorded proposal: excessive/unwelcome petting, 2026-10-19

Status: owner-requested design proposal, not implemented. Working Moodlet label:
"Too much closeness". Distinguish unwelcome proximity from the irritation caused
by poking. Friendship affects tolerance, but does not remove personal boundaries.

Evaluate affection before the requested action, using the current display
friendship level:

| Friendship level | Petting becomes unwelcome at pre-action affection |
| --- | --- |
| 1–2 | 60 or higher |
| 3–5 | 80 or higher |
| 6–10 | 90 or higher |

An otherwise welcome stroke that raises affection across a threshold does not
retroactively become unwanted. The first unwelcome attempt produces a direct
verbal refusal/boundary without a Moodlet or friendship loss. Another unwelcome
attempt within ten real minutes disregards that boundary and creates intensity
one. Technical input locks do not constitute perceived petting attempts.

| Intensity | Escalation | Total contribution to numeric mood target | Emotional quality | Refuse petting for |
| --- | --- | --- | --- | --- |
| 1 | First unwelcome attempt after the boundary | -5 points | Discomfort and wanting distance | 5 minutes |
| 2 | Three further unwelcome attempts while active | -10 points | Feeling crowded/pressured | 10 minutes |
| 3 | Another three unwelcome attempts | -15 points | Strong annoyance at ignored proximity boundaries | 20 minutes |

Keep one entry capped at intensity three. Apply the total target contribution
for the current intensity, not repeated instant deductions. Emotional quality
and intensity independently inform the overall emotional interpretation and
relevant speech. Friendship consequences below remain a separate event effect.

Start the refusal deadline at the boundary-violating attempt. Each subsequent
perceived request during refusal remains unwelcome, renews the deadline using
the resulting intensity and counts toward escalation. Do not add successive
refusal durations together. Once the deadline expires, reassess normal petting
willingness from friendship and current affection; expiry is not guaranteed
acceptance when the ordinary threshold is still met. Refusal can end before the
emotional impression has fully faded. Other actions retain their own rules.

After every twenty real minutes without a further unwelcome attempt, reduce
Moodlet intensity by one, then expire after intensity one. Each such attempt
renews the twenty-minute quiet period. Maximum-intensity quiet time is sixty
minutes; no stacked expiry backlog accumulates. Moodlet ageing and refusal
deadlines continue through closed-app time, standby and sleep. Commands or
restart do not erase the impression or refund prior friendship loss.

Separate relationship consequence:

- The first boundary/refusal costs no friendship.
- Each perceived attempt that ignores the expressed boundary or active refusal
  costs 0.25 friendship points, including the attempt creating the Moodlet.
- Limit these petting-boundary losses to one point per rolling ten minutes.
  Use the existing elapsed axis and persisted relationship-budget ownership;
  do not reset the allowance on a new episode or restart.
- Creation, intensity changes, passive existence and expiry of the Moodlet do
  not apply an additional loss. Respecting the boundary stops new violations;
  subsequently accepted care does not automatically refund losses.

A rejected attempt grants no affection increase, care reward or qualified care
contact. Count a semantic refusal as a perceived boundary interaction; exclude
requests blocked before delivery by technical playback/foreground admission.
These rules do not impose a global action lock and do not alter story clicks or
the separate repeated-poking proposal.

##### Recorded proposal: repetitive food and requesting variety, 2026-10-19

Status: owner-requested design proposal, not implemented. Working Moodlet label:
"Always the same food". Existing code detects the third consecutive identical
food intake using bounded food-ID history; it does not currently timestamp that
history or implement the following Moodlet/request rules.

Create intensity one on the third actually consumed portion of the same food
in succession within twenty-four real hours. A different consumed food breaks
the sequence. Energy drinks neither count as food nor break the sequence as
variety. Placement, offers, refused portions and repeated presentation do not
count as intake. Emotional monotony can arise from autonomous consumption as
well as personal feeding; it does not itself establish human responsibility.

| Intensity | Total contribution to numeric mood target | Emotional quality |
| --- | --- | --- |
| 1 | -5 points | Mild food weariness and wanting variety |
| 2 | -10 points | Clear dissatisfaction with the repetitive food |
| 3 | -15 points | Strong food weariness |

Each further actual intake continuing the same sequence while the Moodlet is
active increases current intensity by one, capped at three. Renew the current
four-hour quiet period. If the Moodlet has expired, a new qualifying repetitive
intake starts at one rather than restoring the previous intensity. Contributions
are total values per level; actual mood follows its normal timed response.

After every four real hours without another qualifying repetition, reduce
intensity by one: 3 -> 2 -> 1 -> expired. Full recovery from intensity three
therefore takes twelve hours without reinforcement. Different food ends the
repetition sequence but does not instantly erase the emotional after-effect.
Use the existing elapsed axis through sleep, standby and closed-app time;
restart does not reset history or timers. Do not add reduced satiety gains or
automatic food refusal to this proposal. Hungry Aiko can eat while expressing
displeasure about the lack of variety.

At initial Moodlet creation, Aiko explicitly requests a different food next
time. If creation occurs during autonomous/unattended or closed-app care,
communicate the request at the next suitable user contact. It becomes a
communicated request when the relevant bubble is visibly presented during
that contact; no reading confirmation is required. An internally queued line
alone does not establish that the user has received the request.

The request remains active until a different food is actually consumed, or
twenty-four real hours after communication, whichever occurs first. A later
request must be communicated again before renewed penalties qualify. Its
lifetime is distinct from Moodlet decay. This general request for variety is
not a concrete food wish and does not automatically grant a wish reward.

Separate relationship consequences during a communicated, active request:

- Count actual personally supplied/consumed portions of the same food that
  prompted the request. Mere placement, rejected offers and autonomous intake
  do not count as ignored personal requests; do not infer handover origin from
  historical self-care.
- The first such intake prompts a reminder in its normal eating reaction and
  costs no friendship. Each subsequent such intake costs 0.25 points.
- Cap these food-variety-request losses at one point per rolling twenty-four
  hours, independently of Moodlet intensity/refresh. Preserve the relevant
  request, counter and relationship allowance across restart using existing
  aggregate/history ownership; do not invent older uncommunicated requests.
- Consuming a different food fulfills the request and ends its ignored-request
  count. The rolling loss allowance is not refunded/reset, previous losses
  remain and the Moodlet continues its separate decay.
- Do not deduct friendship on Moodlet creation, passive existence, escalation
  or expiry alone, or on request expiry/no further feeding. Existing neglect
  rules remain separately responsible for inadequate care.

##### Recorded proposal: withholding a wanted object, 2026-10-19

Status: owner-requested design proposal, not implemented. Working Moodlet label:
"You are keeping it from me". Reuse the existing observed-object interaction and
withholding episode rather than creating another goal or independent detector.
The qualifying subject is a concrete object Aiko actually wants, which she
observes the user take away or continue holding back. Moving an arbitrary object
is not automatically a withholding event.

Keep the immediate request for return distinct from the emotional after-effect.
Existing recognition becomes irritated after eighteen seconds of withholding or
three takes within the same episode, evaluated at the next eligible reaction
(the present request interval is ten seconds and feedback admission also applies).
Create the Moodlet immediately when that first qualified irritation occurs,
without an additional Moodlet-specific waiting period.

| Intensity | Escalation | Total contribution to numeric mood target |
| --- | --- | --- |
| 1 | First qualified withholding irritation | -5 points |
| 2 | Thirty further seconds of observed withholding after irritation starts | -10 points |
| 3 | Another thirty observed seconds | -15 points |

During an active Moodlet, a fresh observed take after return also raises the
current intensity by one if Aiko still wants that object. Cap intensity at three
and maintain one Moodlet entry, not one negative entry per reaction or object.
The numeric values are total level contributions to the target; retain timed
actual-mood adjustment. Emotional quality is frustration directed toward the
user for deliberately denying a wanted object, separately considered when
deriving emotional state and selecting relevant speech.

While the provoking, observed withholding continues, do not start the quiet-time
decay. Making the object accessible again ends that provocation and further
withholding-related loss from it; it does not instantly remove the Moodlet.
After every twenty quiet real minutes, reduce intensity by one:
3 -> 2 -> 1 -> expired. Full after-effects therefore last twenty, forty or sixty
minutes according to the intensity at resolution. A subsequent qualifying take
can reactivate the provocation and escalate as above. Merely discovering an
object at another place belongs to the separately discussed relocation case.

Closed-app and standby time advance Moodlet decay. They do not establish further
observed provocation, escalation or retrospective friendship charges. Preserve
the distinction between existing live object behavior and elapsed-time ageing
of an emotional impression; no historical user-interaction replay is introduced.
Restart, sleep commands and unrelated care do not simply erase the impression.

Preserve the existing separate friendship rule: qualifying withholding can cost
0.5 points per thirty seconds, bounded to two points per rolling two minutes.
Reuse its existing episode eligibility, transaction receipts and persisted
aggregate-owned loss budget. Moodlet creation, escalation or continued existence
does not add another deduction. Return stops future withholding loss from the
resolved situation without refunding previously applied points. Exact emotional
effects on willingness to accept other interactions remain open; this proposal
does not create a blanket action lock.

##### Recorded proposal: relocating objects and disrupting familiar places, 2026-10-19

Status: owner-requested design proposal, not implemented. Working Moodlet label:
"My familiar arrangement has been disturbed". Require a learned object and a
familiar location, then a relevant perceived disruption of that expectation:

- Aiko confirms that the known place is empty and must search for the object.
- Or she observes the user relocate the known object to a clearly different
  place. Reuse subjective observation/association rather than polling hidden
  World positions or treating an opaque object handle as recognition.

Normal handovers, Aiko's own put-down actions and minor movement within the same
placement area do not automatically qualify. Unknown objects do not yet have a
familiar place for this purpose. The exact spatial qualification should use the
existing perception/place model; no new fixed pixel distance is approved here.

| Intensity | Qualifying escalation | Total contribution to numeric mood target | Emotional quality |
| --- | --- | --- | --- |
| 1 | First confirmed disruption | -5 points | Irritation or uncertainty about the changed arrangement |
| 2 | Another independent relocation/disruption while active | -10 points | Clear annoyance about disorder |
| 3 | Another independent disruption | -15 points | Strong annoyance about repeated changes |

Keep one entry capped at three. A completed relocation/disruption is one
experience: do not count every drag-motion update, repeated perception check,
missing-place cue or subsequent reunion as a new event. Multiple independently
perceived relocation events may stack. Apply the total contribution for the
current level to the mood target, retaining actual-mood response timing and
separate emotional interpretation.

After each thirty real minutes without a newly confirmed disruption, reduce
intensity by one: 3 -> 2 -> 1 -> expired. Full after-effects from intensity three
last ninety minutes without reinforcement. A new qualifying event renews the
current quiet period and can escalate to the cap. Ongoing search alone does not
produce additional stacks. Finding an object resolves the relevant search and
updates acquired place knowledge; it does not instantly clear the impression.
Decay continues through sleep, standby and closed-app time. Do not manufacture
unobserved relocation events or blame from a restored World snapshot.

Separate emotional disturbance from attribution: an empty familiar place can
justify the Moodlet without proving that the user caused it. A personal
accusation or relationship loss needs a supported user connection, such as an
observed take-and-relocate sequence. Finding an object elsewhere alone does not
establish that connection or grant unsupported physical identity knowledge.

For a qualifying user-attributed event, propose a separate 0.25-point friendship
loss, capped at one point per rolling hour. Preserve the rolling budget across
restart/new episodes through existing aggregate/history ownership. There is no
additional loss for Moodlet existence, repeated search, reunion, refresh or
expiry. Finding/returning an object does not automatically refund past losses.
Do not automatically charge a single take as both withholding and relocation;
a later independent rearrangement may qualify as a separate event.

##### Recorded distinction: inner wishes and expressed wishes, 2026-10-20

Status: owner-requested planning clarification, not implemented. Wishes remain
part of Aiko's inner experience regardless of friendship or current wellbeing.
Feeling comfortable and having sufficient trust govern whether she expresses
a wish to the user, not whether she can have it. Do not suppress inner wishes
merely because she is unwell, irritated, unfamiliar with the user or currently
unwilling to ask for something. Urgent needs can take priority in action and
speech without deleting or denying an existing desire.

Separate these facts and transitions:

| Layer | Meaning |
| --- | --- |
| Inner wish | Aiko wants a concrete experience, whether or not she communicates it. |
| Wish expression | A context-dependent communication decision, governed by wellbeing, friendship/trust and the current interaction. Speaking does not create a second wish. |
| Wish fulfillment | The desired activity actually occurs under its own completion rule within the wish period, independently of prior expression. |
| Fulfillment Moodlet | The defined emotional after-effect is created only after that qualifying fulfillment, not from having, displaying or expressing the wish. |

The wish itself grants no anticipation/longing Moodlet, numeric mood modifier
or relationship reward. A wish describes "I want to do X"; completing X within
the wish period is the trigger for the defined positive impression. This applies
equally to unspoken and spoken wishes. No preparatory Moodlet is replaced or
rewarded again at completion, because none is created by the wish's existence.

Keep one canonical wish record with its communication status/evidence rather
than separate mutable inner and spoken wish collections. `PetState`/`PetValues`
own persistent wish state, emotional effects and transitions. Pure wish rules
assess creation/selection separately from readiness to express. Mind/application
consumers arrange an appropriate utterance and record actual communication;
queueing a line alone is not an expressed wish. The existing user-visible status
UI may show the inner wish and whether Aiko has voiced it. Opening that UI or
the user reading it is not evidence that Aiko spoke or perceived communication.

An unspoken wish may still be fulfilled. Recognize the actual event and its
origin; do not require prior expression for satisfaction. Lack of fulfillment
of an unspoken wish does not establish deliberate ignoring by the user. Prior
general requests, such as the communicated request for food variety, retain
their own evidence and consequences; do not confuse them with an inner wish.

The food-only pacing candidates below are superseded by the later recorded
shared wish-creation/concurrency proposal. Keep inner-wish pacing separate from
expression frequency and cooldowns. Do not reinterpret creation limits as a ban
on having wishes at low friendship or poor wellbeing. This historical
clarification itself introduced no numerical expression thresholds; later
wish-specific proposals define their own candidate disclosure rules.

The current checkout now supports RPS, Blackjack and Tic-Tac-Toe, and Plaudern,
API Single/Two Parts and facts. See [minigames](MINIGAME_IMPLEMENTATION_PLAN.md)
and [social content](SOCIAL_CONTENT.md). This clarification therefore supersedes
the earlier food-only future-activity assumption. Capability/online-source
availability remains distinct from social trust. Wish-specific fulfillment
Moodlets and completion rules for those activities are specified below.
Preserve API-only entertainment, opt-in and source ownership; neither unavailable API
content nor an unplayed UI selection proves an ignored or fulfilled wish.

##### Recorded proposal: food wishes and fulfillment, 2026-10-19

Status: owner-requested design proposal, not implemented, subject to the
2026-10-20 inner/expression clarification above. A food wish represents specific
appetite, such as wanting an apple later; it need not require low satiety.
Immediate hunger or exhaustion can take priority in action/speech without
preventing inner desire. Wishes are opportunities for additional positive
experiences, distinct from care requirements and general requests for variety.

| Rule | Candidate value |
| --- | --- |
| Concurrent active wishes | Earlier one-wish candidate superseded by the shared proposal: up to three across areas, at most one food wish |
| New-wish limit | Earlier two-per-day candidate superseded; shared proposal adds no daily counter |
| Minimum interval between wish creation | Earlier six-hour candidate superseded by shared sixty-minute global / ninety-minute same-area spacing |
| Wish lifetime | Four real hours |
| Wish creation | While Aiko is awake and the application is running |
| Target | A specific implemented food ID; a matching portion need not currently exist on the desktop |
| Presentation | Specific inner wish and remaining time in status, distinguished from an actual context-qualified spoken request |

Choose from suitable existing food types with variety in mind; do not request
the food whose repetition is currently upsetting her. A wish does not prove
that any matching World object exists, is visible or has been identified.
Do not generate a backlog of hypothetical wishes while the app is closed.
Save an existing wish and advance its deadline through sleep, standby and
closed-app time instead of renewing it on restart.

Fulfill the wish once when a matching portion is actually accepted and consumed
within its active lifetime. Placement, an offer, a selected menu item or bubble
playback alone does not fulfill it. Preserve ordinary satiety/acceptance rules.
Other food remains consumable under its own rules; it does not satisfy the
specific wish, which remains until fulfillment or expiry.

Working fulfillment Moodlet label: "Exactly what I wanted". Propose a total
five-point positive contribution to numeric mood target for two real hours,
with actual mood following its normal timed response. Emotional quality is joy
and satisfaction; personal fulfillment can additionally support warmth toward
the user. The immediate happy response at intake remains distinct from the
lasting impression. Positive and negative impressions coexist; fulfillment
does not erase irritation, prior losses or other Moodlets.

Initially do not stack the intensity of this fulfillment Moodlet. Another
genuinely fulfilled wish would renew its two-hour duration rather than create
multiple copies or a larger bonus. Repeated portions after one wish's completion
are not additional fulfillments. Shared wish-creation limits remain independent
of emotional duration; reaching another wish is not an excuse to bypass them.

Autonomous consumption can satisfy the active food wish and create the positive
impression, without implying that the user personally supplied it. This also
applies to valid, finite known-stock intake reconstructed before the wish's
deadline. Do not invent handovers, personal gratitude or relationship credit
from self-care. Use the existing consumption origin and joint World/Pet/memory
transaction to apply fulfillment, impression and any eligible reward once.

For a personal handover fulfilling the wish, the later agreed common bonus
confirms a nominal additional 0.25 friendship points within the existing shared
rolling reward ceilings:
0.75 points per two hours and five points per twenty-four hours. It does not
create another independent reward allowance. Ordinary food credit still follows
its existing rules; effective additional wish credit depends on remaining
allowance. Exhausted friendship reward capacity does not prevent fulfillment
or the positive Moodlet. Persist completion and reward accounting so repeated
loads/retries cannot replay either effect.

An unfulfilled wish expires without a negative Moodlet or friendship deduction.
It is not an additional mandatory care task. Detailed candidate-selection
tie-breaks remain implementation conventions; the later agreed common bonus
resolves reward qualification without changing the shared care reward ceilings.

##### Recorded proposal: game-wish variants, 2026-10-20

Status: owner-requested design proposal, not implemented. Aiko can want the
shared activity itself or a particular outcome in RPS, Blackjack or Tic-Tac-Toe.
These are distinct motives, each defined by game ID, objective and round scope
when the wish becomes active. Preserve the distinction between having a wish
and expressing it; low friendship or poor wellbeing does not erase the desire.
The later shared wish-creation proposal specifies the four-hour lifetime and
creation/expression pacing. These remain design candidates, not implementation
authorization.

| Wish variant | Qualifying fulfillment within the wish window | Candidate emotional after-effect |
| --- | --- | --- |
| Play the named game together | Complete the agreed round count in that game; initial candidate is two completed rounds in one session, regardless of winner | Enjoyment of shared play |
| Win a round in the named game | Win at least one qualifying round before the wish expires | A sense of achievement / pride |
| Do not lose the next round in the named game | The next qualifying completed round is a win or draw | Relief |
| Win overall in the named game | In a predetermined round block, Aiko has more wins than losses; initial block candidate is the next three completed rounds | Satisfaction with the overall success |
| Do not lose overall in the named game | In that block, Aiko has at least as many wins as losses; an all-draw block qualifies | Relief about the overall result |

Evaluate results from Aiko's perspective. Existing `SessionSummary` counts are
from the player's perspective; the application adapter already reverses wins
and losses into `GameExperience`. A completed Blackjack hand is one round;
draws are completed rounds. Opening a menu/window, selecting a move or leaving
a round unfinished does not qualify. Other games do not satisfy the named-game
goal. The lifecycle proposal below further requires rounds to start after wish
creation; no round already underway at that point qualifies.

Fix the scope before play rather than letting a convenient window-close time
define an overall victory. For block goals, evaluate the predetermined completed
block, not a favorable prefix. The next-round goal is distinct from eventually
finding a non-loss later in the window. Apply the recorded lifecycle proposal
below; never silently change the goal after an unfavorable result.

Use the actual qualifying round/block completion time to determine whether it
falls within the wish window. A later window close must not invalidate a goal
already fulfilled in time. Ordinary care currently receives a brief game
summary on close. Immediate wish resolution therefore needs a semantic round
completion signal from the existing game owners through application
coordination; do not infer outcomes from speech, animation or UI labels.
Keep only the bounded wish progress needed by its scope, not saved decks,
boards, full game sessions or another score owner. Session totals alone cannot
prove an ordered win/loss streak; such future goals need explicit evidence.

Having, displaying or expressing the wish creates no Moodlet. Exactly one
qualifying fulfillment creates the Moodlet appropriate to that wish's motive,
including when the wish was unspoken. Do not award all variant Moodlets just
because one winning round happens to satisfy their abstract conditions. Ordinary
round reactions remain separate from the lasting fulfillment impression.

Strength, duration, stacking and cross-family combination are specified in the
following recorded proposal, separately from the wish variants above.
Keep ordinary fun/care gains independent of victory. An unfavorable fair game
result is not user mistreatment and does not itself justify relationship loss.
Any disappointment or repeated-loss Moodlet requires its own separately agreed
rule rather than automatic punishment for an unfulfilled game wish. Existing
shared friendship reward limits must not be bypassed by changing game or goal.

##### Recorded proposal: game-wish failure, retries and cross-session progress, 2026-10-20

Status: owner-requested design proposal, not implemented. Distinguish retryable
attempts from a goal bound to one specific round or fixed block. Keep each
wish's original four-real-hour deadline and evaluate from Aiko's perspective.

| Wish | Fulfillment or unsuccessful end | Retry under the same wish |
| --- | --- | --- |
| Play the named game together | Fulfilled by two completed rounds in one session; otherwise expires at its deadline | Yes. A session with only one round does not end the wish, but another session must itself contain two completed qualifying rounds |
| Win a round in the named game | Fulfilled by the first qualifying win; otherwise expires at its deadline | Yes. Losses/draws leave the wish active, across sessions within its lifetime |
| Do not lose the next round in the named game | The next qualifying completed round resolves it: a win/draw fulfills it; a loss immediately ends it unfulfilled | No. A later round is not the originally desired next round |
| Win overall in the named game | Evaluate after the next three completed qualifying rounds: more wins than losses fulfills it; any other result ends it unfulfilled | No fresh three-round block within that wish |
| Do not lose overall in the named game | Evaluate after the next three completed qualifying rounds: at least as many wins as losses fulfills it; any other result ends it unfulfilled | No fresh three-round block within that wish |

Draws count as completed rounds. An all-draw block satisfies the overall
non-loss goal, but not the overall win goal. Always evaluate the whole fixed
three-round block, even when its eventual outcome becomes certain earlier.
An incomplete block expires if its original deadline arrives first.

Fixed-block progress spans sessions, game-window closes and application
restarts. For example, one win and one loss in the first session plus a win
in the second produce a 2:1 block and fulfill the overall win wish. Other
games do not alter it. Do not reset finished wish rounds or choose a favorable
prefix by closing/reopening the window. Preserve only bounded canonical wish
progress, not another game score owner or reconstructed boards/decks.

Only rounds started after wish creation qualify, and they must finish no later
than its deadline, including equality at that time. Interrupted/abandoned
rounds count as neither wins nor losses; completed qualifying progress remains.
Closing a window later does not invalidate fulfillment already achieved in
time. Closed-app and standby time continue to age the wish; do not replay games.

An unsuccessful end or expiry is initially neutral: no fulfillment Moodlet and
no additional friendship loss. Ordinary game reactions and fun/care effects
remain separate. A later win cannot retrospectively fulfill an ended wish.
Aiko can continue playing and may later have a genuinely new similar wish,
subject to regular selection, the sixty-minute global spacing and ninety-minute
game-area spacing, measured from their respective previous wish creation times.
Ending a wish frees a slot without automatically generating a replacement or
resetting those intervals. The same-wish retry rule creates no extra rewards.

##### Recorded proposal: game-wish fulfillment Moodlets, 2026-10-20

Status: owner-requested design proposal, not implemented. Distinguish three
emotional families: enjoyment of shared time, pride/achievement, and relief.
The fulfilled wish determines its one appropriate family; do not grant all
families or an additional generic fulfillment Moodlet for the same wish.

| Fulfilled wish | Emotional family | Initial level / total mood-target contribution | Decay without another fulfillment |
| --- | --- | --- | --- |
| Play the named game together | Enjoyment of shared time | Level 1 / +5 points | Two real hours |
| Win a round in the named game | Pride/achievement | Level 1 / +5 points | Two real hours |
| Win overall in the named game | Pride/achievement | Level 2 / +10 points | Four real hours |
| Do not lose the next round in the named game | Relief | Level 1 / +5 points | Two real hours |
| Do not lose overall in the named game | Relief | Level 2 / +10 points | Four real hours |

Each family has at most one active Moodlet with three intensity levels, whose
total contributions are +5, +10 and +15 points respectively. Numeric mood
follows its existing timed response to the composed target; fulfillment is not
an immediate jump in the mood bar. The emotional qualities remain distinct
inputs to the overall emotional state and attitude toward the user.

After each two-real-hour interval without another qualifying fulfillment in
that family, reduce its level by one; remove it after level one expires. Thus
levels one, two and three last at most two, four and six hours respectively
without another fulfillment. Age the same persisted state through normal
running, standby and closed-app time using the shared elapsed-time foundation.

Another genuinely fulfilled, separate wish in the same family raises its
current level by one for a shared-play or single-round goal, or by two for an
overall-result goal, capped at level three. Start a new two-hour interval at
that fulfillment rather than appending an unbounded duration backlog. Apply
elapsed decay before the new fulfillment; an already expired impression starts
again at the goal's initial level. Changing games does not create a separate
copy of pride, relief or shared enjoyment. Replaying a completion signal,
ordinary later rounds and repeated clicks do not fulfill an already completed
wish again. Wish creation/expression pacing remains a separate design rule.

The three families can coexist. Cap their combined numeric mood-target bonus
at +15 points, while retaining each family's own intensity and emotional
quality for overall-state composition. This is a game-wish group cap, not a
new global cap for every positive Moodlet. Existing food-wish rules remain
separate. Positive fulfillment does not erase negative impressions, refund
losses or bypass an unrelated interaction boundary; joy about a win can
coexist with irritation toward the user.

Moodlet creation, stacking, refresh and decay do not themselves grant or repeat
a friendship reward. Any separately eligible wish/care reward retains the
existing shared friendship accounting and ceilings. Ordinary immediate game
reactions and need effects remain separate from the lasting impression.

##### Recorded proposal: social wishes and fulfillment Moodlets, 2026-10-20

Status: owner-requested design proposal, not implemented. Use the four existing
social choices, with authored contextual dialogue for Plaudern and API-only
content for Single, Two Parts and facts. Preserve online-source opt-in and the
existing source/preparation owners; do not introduce authored fallback jokes
or facts. Wish fulfillment is distinct from ordinary talk care admission.

| Inner wish | Qualifying fulfillment within its lifetime | Working fulfillment impression / emotional quality |
| --- | --- | --- |
| Chat with the user | A complete ordinary Plaudern dialogue sequence is played | Glad we talked / connection |
| Tell the user a Spruch (API Single) | The complete API Single sequence is played | Shared something funny / cheerfulness |
| Tell the user a joke (Witz) | The complete API Two Parts sequence, including setup and punchline, is played | Shared something funny / cheerfulness |
| Tell the user a curious fact | The introduction and complete API fact sequence are played | Shared something interesting / enthusiasm |

Propose a four-real-hour wish lifetime. Having, displaying or expressing a
wish creates no Moodlet. Initial expression thresholds are friendship level
three or higher and numeric mood at least fifty; urgent needs and ongoing
reactions take precedence in speech. These are disclosure thresholds, not
eligibility requirements for the inner wish or its fulfillment. Actual spoken
expression still requires evidence; queueing a line is insufficient.

Resolve each wish once on actual full-sequence completion within its lifetime,
including an unspoken wish. Opening the menu, fetching/preparing content, a
holding line and interrupted playback do not fulfill it. Do not infer that the
user laughed, learned something or approved from clicks, elapsed time or a
completed sequence. The activity wish is to share the content, not to prove
an unobservable audience reaction. Target existing content categories rather
than unsupported topic-specific fact retrieval.

Ordinary accepted talk care continues to commit at playback admission under
its existing rules. A later interruption does not undo those effects, but
cannot grant the separate completion-based wish impression. Use the existing
playback lifecycle through application coordination for completion evidence;
do not create another conversation player or reward owner. Technical failure,
unavailable content and wish expiry produce no penalty or invented evidence
of user mistreatment. Source settings remain authoritative.

Each qualifying fulfillment starts its emotional family at level one: a total
+5-point mood-target contribution for two real hours. Spruch and Witz share
one cheerfulness family, not separate additive copies. Connection, cheerfulness
and enthusiasm remain distinct emotional impressions. Another genuinely
fulfilled, separate wish in the same family adds one intensity level, capped
at three (+5 / +10 / +15 total), and renews the current two-hour interval.
Reduce intensity by one every two real hours without another fulfillment;
apply elapsed decay before a later fulfillment, including standby/closed time.
An expired impression starts again at level one. Ordinary subsequent talk,
reading clicks and duplicate completion delivery do not create another wish
fulfillment or stack. Numeric mood retains its normal timed response.

Any friendship reward is separate from the lasting impression and remains
within the existing shared care/reward limits. No additional amount is fixed
by this proposal. Completion, stacking and each bubble/punchline must not
repeat ordinary talk credit. Apply the later common-contribution-cap proposal
when balancing these families, alongside the later shared wish-creation and
concurrency proposal.

##### Recorded proposal: affection wish and fulfillment Moodlet, 2026-10-20

Status: owner-requested design proposal, not implemented. Initially use one
concrete affection wish: "I want to be petted." Desired closeness can arise
while the affection need is adequately supplied; a deficit is not required.
Do not create several nominally different wishes for the same existing action.

| Rule | Candidate value |
| --- | --- |
| Inner wish lifetime | Four real hours |
| Expression | Friendship level at least three and numeric mood at least fifty, with petting currently welcome |
| Fulfillment | One actually accepted petting interaction within the wish lifetime, including when the wish was unspoken |
| Working fulfillment Moodlet | Feeling secure / warmth and connection (German working label: Geborgen) |
| Initial strength and duration | Level one, a total +5-point mood-target contribution for two real hours |
| Stacking | Another genuinely fulfilled, separate affection wish adds one level, capped at three (+5 / +10 / +15 total) |
| Decay | Reduce by one level every two real hours without another qualifying fulfillment |

Expression readiness does not determine whether Aiko can have the inner wish.
Keep it separate from fulfillment and current action willingness. A wish does
not override a refusal, an active petting boundary or ordinary friendship/
affection acceptance thresholds. Rejected or technically blocked attempts do
not fulfill it. Urgent needs and ongoing reactions retain speech priority.
Opening status or queueing a request is not actual spoken expression.

Apply ordinary affection care at its existing accepted interaction transition,
then resolve the qualifying wish once with its lasting emotional impression.
Repeated petting after that wish was fulfilled does not create another wish
bonus or stack; a later independent wish must actually exist and be fulfilled.
Renew the current two-hour interval on a qualifying additional fulfillment,
without appending an unbounded expiry backlog. Apply elapsed decay first; an
expired impression starts at level one. Advance wish deadlines and Moodlet
ageing through standby and closed-app time on the existing elapsed axis.

Numeric mood follows its normal timed response. Positive and negative
impressions can coexist. A separate targeted mitigation rule may shorten an
eligible negative impression, but this wish does not itself erase a boundary
violation or refund friendship losses. Keep friendship reward accounting
separate under existing shared limits; the later agreed wish friendship bonus
section fixes the additional amount. Apply the common-contribution-cap and
shared wish-creation proposals before implementation, rather than silently
assigning another reward allowance.

##### Design reference: positive experiences and negative Moodlets, 2026-10-20

The owner requests explicit consideration of whether playing, social activity
and welcome affection can mitigate relevant negative impressions. Distinguish
numeric positive/negative contributions, overall emotional interpretation,
addressing the original cause, and actual recovery of the negative Moodlet.
Coexistence alone does not define a targeted recovery effect. Do not use the
earlier no-automatic-erasure rule to preclude a separately agreed, cause-specific
mitigation rule. The recorded proposal below now specifies candidate mappings
and numerical reductions; implementation remains unauthorized.

The owner identifies The Sims 3 and The Sims 4 as the general product reference
for this design. Use concrete named impressions, identifiable causes, strengths,
and understandable remaining durations in status, with multiple impressions
contributing to the overall emotional state. The official
[The Sims 3 manual](https://eaassets-a.akamaihd.net/eahelp/manuals/the-sims-3-manual_PC.pdf)
describes temporary Moodlets affecting mood and behavior and displaying their
duration. The official
[The Sims 4 manual](https://eaassets-a.akamaihd.net/eahelp/manuals/the-sims-4-xbox-one-anz.pdf)
distinguishes predetermined durations from condition-dependent effects and
explains both emotional contributions and actions that shorten negative
Moodlets. These are reference mechanics, not evidence that Aiko's candidate
numbers, three-level decay or wish rewards reproduce Sims rules exactly.
Keep those candidate values explicit; discuss any change between fixed-duration
and phased-decay models rather than silently replacing the recorded proposals.

Preserve existing care-driven recovery, explicit interaction boundaries and
separate friendship accounting. A positive wish must not silently bypass a
refusal or treat a laugh, gift or win as proof that prior mistreatment was
forgiven. Interpret the following targeted reductions alongside the earlier
decay rules; they do not authorize a general automatic cleansing effect.

##### Agreed rules: targeted shortening of negative Moodlets, 2026-10-20

Status: owner-confirmed design rules, not implemented. Deduct the listed
credit from the remaining duration of the current intensity/decay stage, not
from every remaining stage or directly from intensity/numeric mood.

| Negative impression | Qualifying helpful interaction and prerequisite | Reduction of the current stage |
| --- | --- | --- |
| Annoyed by repeated poking | After five minutes without another provocation: complete Plaudern, shared play, or welcome accepted petting | Five minutes |
| Too much closeness / feeling crowded | After five minutes of respected distance: complete Plaudern or shared play | Five minutes |
| Always the same food | Actually accept and consume a different food | Sixty minutes |
| A wanted object was withheld | Object is accessible again, followed by complete Plaudern or shared play | Five minutes |
| Familiar arrangement was disturbed | Search is complete or the new position is recognized, followed by complete Plaudern or shared play | Five minutes |
| Feeling alone after prolonged lack of contact | Complete one social interaction: Plaudern, API Single, API Two Parts, or fact | Thirty minutes |
| Frustrated after prolonged lack of stimulation | Shared play | Thirty minutes |
| Missing closeness | One accepted petting interaction | Thirty minutes |
| Worn down by prolonged hunger | One actually consumed meal | Thirty minutes |
| Irritated by exhaustion | Actual sleep and stable energy recovery | No additional flat credit; preserve existing recovery |

For these rules, shared play means at least two completed rounds in one
session, regardless of winner. Social completion means the whole sequence,
including the punchline or fact introduction as applicable. Menu selection,
waiting, interrupted sequences, rejected actions and duplicate event delivery
do not qualify. Petting retains its ordinary willingness/acceptance rules.

Grant at most one reduction per intensity level within one continuous Moodlet
episode. An episode lasts from creation until the impression fully ends,
including timer extensions, escalation and recovery pauses. Each Moodlet keeps
its own used-level allowances; revisiting a level does not create a new one.

| Situation during the same episode | Renewed relief eligibility |
| --- | --- |
| Another helpful interaction on a level already shortened | None |
| Provocation refreshes the timer, including at maximum intensity | No reset |
| Intensity changes to a level not yet shortened in this episode | One reduction, after that impression's prerequisites are satisfied |
| Intensity returns to a previously shortened level | Its allowance remains used |
| Recovery pauses and later resumes | Allowances remain unchanged |
| Sleep, app closure, standby or save reload | Preserve allowances; elapsed ageing still applies |
| Impression fully ends and a later qualifying event creates a genuinely new episode | Fresh per-level allowances |

A new episode still requires the existing trigger and exposure rules. Previously
accounted-for poor-care history must not recreate an ended impression or renew
its allowances. A new provocation must satisfy the existing quiet-time rules
again before relief can qualify, even on a previously unused level.

One completed qualifying interaction shortens only the currently active level
of each eligible Moodlet. Further clicks, changing social categories or
switching games do not renew a used allowance. If the level has less time left
than the credit, end that stage and discard the excess; do not carry credit
into the next stage. That next stage starts with its normal duration and needs
another completed qualifying interaction if its allowance is still unused.
Apply ordinary elapsed ageing before the interaction so an already expired
impression cannot be credited.

For prolonged-poor-care impressions, first require the affected need to have
remained at forty or above for thirty continuous real minutes, as already
proposed. Only subsequent qualifying care can accelerate that impression's
emotional recovery. Do not accumulate credits before this recovery gate opens.
Actual sleep restores energy under existing rules without a new flat emotional
credit. Need recovery and emotional recovery remain distinct.

Shortening the crowded/closeness impression does not shorten its separate
petting-refusal deadline. Renewed boundary violations follow their existing
escalation/quiet-time rules. Returning an object ends the provoking situation;
the additional shortening requires the subsequent qualifying interaction.

No active or expressed wish is required for targeted relief. An interaction
can independently fulfill a genuine wish and mitigate an eligible negative
impression under these rules. Keep ordinary care, the positive wish impression,
negative-duration relief and any relationship effect distinguishable. Relief
neither refunds previous friendship losses nor creates another reward budget.

Example: poking irritation at level two has fourteen minutes left in its
current twenty-minute stage. A qualifying conversation after respected quiet
reduces that remainder to nine minutes and uses level two's allowance. Renewed
poking escalates it to level three; that level can receive its first reduction
after the required quiet time. A later return to level two keeps its allowance
used. Level one can still receive one reduction if it has not been shortened
during this episode. Reloading the save does not reset any used allowance.

##### Recorded proposal: prolonged/repeated poor care, 2026-10-19

Status: owner-requested design proposal, not implemented. Reuse the existing
per-need critical/zero exposure over the preceding twenty-four elapsed hours,
rather than another independent neglect history. A briefly low value is not
enough to create an emotional impression. Current need condition, direct
need-derived mood impact and emotional after-effects remain separate layers.

| Source need | Working emotional impression |
| --- | --- |
| Satiety | Worn down by prolonged hunger |
| Energy | Irritated by exhaustion |
| Fun | Frustrated by prolonged lack of stimulation |
| Social | Feeling alone |
| Affection | Missing closeness |

These are working labels, not new names for the immediate hungry/tired need
conditions. They describe an emotional experience left by prolonged or repeated
poor care; they do not prove deliberate neglect by the user.

| Intensity | Accumulated time below 25 within the preceding twenty-four hours | Or accumulated time at zero in that window | Total mood-target contribution for this impression |
| --- | --- | --- | --- |
| 1 | Two hours | One hour | -5 points |
| 2 | Four hours | Two hours | -10 points |
| 3 | Six hours | Three hours | -15 points |

Disjoint deficient periods accumulate. Zero exposure already contributes to
critical exposure; use the qualifying intensity from the alternative thresholds,
not their sum. Newly qualifying exposure creates/escalates an impression once;
repeated status reads or time steps do not reapply the same transition.
Maintain at most one impression per need, capped at intensity three.

Propose a combined extra numeric mood-target deduction of at most fifteen points
for this poor-care Moodlet group, rather than adding five maximum fifteen-point
deductions. Multiple emotional impressions and their individual strengths remain
available to emotional interpretation even when this group cap applies. The
cap does not change the direct need-based calculation or silently define a
global cap for the separately proposed interaction/food Moodlets.

Start emotional recovery after the affected need has remained at forty or above
for thirty continuous real minutes. Then lower the impression by one intensity
level every two hours of recovery. A single accepted care action does not
instantly erase it. Preserve the actual exposure history; unchanged old history
alone must not recreate the impression after recovery. Additional poor exposure
must be distinguished from repeated evaluation of an already handled threshold.
The following recovery proposal specifies interruption and renewed exposure.

While actual sleep restores energy, it adds no new exhaustion exposure or stack.
Other needs follow their existing sleep rules. Closed-app/standby reconstruction
uses the actual modeled need trajectory and finite, known consumed resources;
it is not evidence of deliberate user behavior. Emotional recovery/ageing uses
the same elapsed axis, including sleep and closed intervals. Old saves must not
acquire fabricated emotional history on migration.

Add no separate friendship penalty for these Moodlets: existing absence and
neglect policies already own that consequence. Creating, keeping, escalating
or recovering an impression must not charge the existing loss a second time.
These impressions alone must not block needed care. Aiko can accept help while
still emotionally affected; improving needs and recovering emotionally have
distinct timing and implications.

##### Recorded proposal: poor-care recovery interruption and renewed exposure, 2026-10-20

Status: owner-requested design proposal, not implemented. Apply these rules
independently to each affected need and its existing poor-care impression.

| Situation | Candidate recovery behavior |
| --- | --- |
| Initial thirty-minute qualification has not completed | Require thirty continuous real minutes at forty or above; a drop below forty restarts that qualification |
| Recovery is already running and the need drops below forty | Pause emotional decay, retaining earned progress in the current two-hour stage |
| Need reaches forty or above again after an interruption | Require another thirty stable minutes, then resume the retained stage progress |
| Need is at least twenty-five but below forty | No emotional recovery and no new critical exposure |
| Need is below twenty-five, or at zero | Accumulate new critical/zero exposure under the existing thresholds; do not escalate immediately merely for crossing forty |

The thirty-minute qualification does not itself count toward the two-hour
decay stage. Pausing and resuming does not renew a relief allowance already
used for that intensity level during the continuous Moodlet episode. Example:
after eighty minutes of earned recovery, a drop
to thirty-eight pauses the stage. Following renewed supply and thirty stable
minutes, forty minutes remain, rather than a new two-hour stage.

Retain the existing twenty-four-hour exposure history for care and friendship
rules. Track which exposure has already been accounted for emotionally; that
same burden cannot recreate or restore an impression merely because it remains
in the history. Reuse existing bounded history ownership, not a second neglect
simulation or an independently reset copy of the care history.

New, not-yet-accounted-for deficient periods still accumulate within twenty-four
real hours even when separated by care. Thirty stable minutes do not discard
such unaccounted exposure. Determine renewed burden from new exposure only:
level one after two hours below twenty-five or one hour at zero; level two
after four/two hours respectively; level three after six/three hours. Zero
already contributes to critical duration; use the qualifying alternative
level rather than adding the two routes.

If the impression has expired, create it at the newly qualifying level. If it
still exists, raise it only when that newly qualifying level exceeds current
intensity; do not add the levels together. A genuine increase restarts the
current recovery stage. A brief renewed deficit pauses recovery and contributes
new exposure without restoring the historical maximum. These are emotional
rules; they do not erase care evidence or add/refund friendship effects.

##### Agreed rules: overall emotional-state selection, 2026-10-20

Status: owner-confirmed rules for implementation, not implemented. Derive one overall
emotional interpretation from numeric mood, the active Moodlet composition and
relevant interaction context. Do not create another care bar, mutable emotion
score or independently persisted collection. Physical need conditions, sleep,
immediate reactions and enduring friendship remain distinct inputs/facts.

Numeric mood combines the need-derived contribution and defined Moodlet
modifiers under the agreed caps and response timing. Emotional interpretation
also retains each impression's cause, direction, intensity and user attribution.
Equal positive and negative numeric contributions do not erase those facts:
+10 pride and -10 irritation have zero net numeric contribution while both
remain emotionally relevant. Numeric contribution caps must not discard active
impressions or lower their emotional intensity merely to match the bar.

The confirmed emotional directions and their family assignments are listed
below. Group impressions by the direction they actually support. In each direction, start
with the complete set of active impressions, not only the strongest one.
The owner subsequently clarified that every active Moodlet must contribute to
the resulting overall emotional composition. There is no fixed global count
limit on active Moodlets; catalogue-specific stacking/copy rules still apply.
The limit of three concurrent wishes is unrelated to Moodlet concurrency.
Numeric mood-contribution caps do not truncate this emotional evidence.

The owner confirms the following aggregation in place of the earlier strongest-
impression/support-cap candidate:

1. Each active Moodlet contributes its current emotional intensity, one, two
   or three. This is distinct from its numeric mood-target point contribution.
   Count the active impression's intensity once; do not count its stacking
   occurrences again as independent impressions.
2. Sum all positive intensities, all negative intensities, and contributions
   within each emotional direction. Every active impression participates;
   numeric mood caps do not cap these emotional sums.
3. If one polarity has the greater total, select the primary label from that
   side's strongest combined direction. Losing-side impressions remain relevant
   to wording, attitude and any independently defined interaction boundaries.
4. If positive and negative totals are equal and nonzero, use **Zwiegespalten**
   (ambivalent), retaining the concrete directions on both sides. With no active
   Moodlets, use the numeric-mood fallback table below instead.

| Primary emotional label | Contributing documented Moodlet families |
| --- | --- |
| Fröhlich (cheerful) | Specific food-wish fulfillment; shared-play enjoyment; social cheerfulness; social enthusiasm |
| Stolz (proud) | Achievement/pride from fulfilled game-success goals |
| Erleichtert (relieved) | Fulfilled game non-loss goals |
| Zugewandt (warm toward the user) | Social connection; affection fulfillment/feeling secure |
| Gereizt (irritated) | Repeated poking; repetitive food; prolonged-exhaustion after-effect |
| Bedrängt (crowded) | Excessive/unwelcome closeness |
| Frustriert (frustrated) | Withholding; disrupted familiar arrangement; prolonged lack of stimulation |
| Niedergeschlagen (downcast) | Prolonged-hunger emotional after-effect |
| Einsam (lonely) | Prolonged lack of social contact; prolonged lack of affection |

This assigns all eighteen documented families, not eighteen independent stores.
The German labels and English explanations above define presentation meaning;
English Python identifiers and localized keys belong to the coordinated schema change.
Equal-ranked directions within the winning side require a deterministic tie
convention using retained cause/time evidence, recorded during implementation;
it must not override the agreed polarity totals or require another emotion store.

| Numeric mood with no active Moodlets | Fallback label |
| --- | --- |
| Less than 40 | Gedrückt (subdued) |
| At least 40 and less than 70 | Gelassen (calm) |
| At least 70 | Zufrieden (satisfied) |

With active impressions, their full composition sets the emotional label while
numeric mood continues to describe general wellbeing. Four independent positive
level-one impressions can outweigh one negative level-three impression; the
negative impression still colors the response and retains its specific boundary.
The same numeric mood can produce different emotional labels. Need statements,
care priorities and specific boundaries remain independently effective. This
approval introduces no additional blanket interaction refusals or new reward.

Positive experiences can both change the emotional composition and shorten
eligible negative impressions through the separately recorded relief rules.
An overall label alone must not erase Moodlets, reset their clocks, refund
relationship losses or grant wish/care rewards.

##### Recorded proposal: common Moodlet contribution caps, 2026-10-20

Status: owner-requested design proposal, not implemented. Cap positive and
negative numeric mood-target contributions separately, preserving individual
and group limits before applying their common limits.

| Scope | Candidate numeric contribution limit |
| --- | --- |
| One stackable Moodlet | Up to +15 or -15 points under its own rules |
| Food-wish fulfillment | +5 points, with no intensity stacking, as already proposed |
| All game-wish fulfillment families | +15 points combined, as already proposed |
| All social-wish fulfillment families | +15 points combined |
| Affection-wish fulfillment | Up to +15 points |
| All prolonged-poor-care impressions | -15 points combined, as already proposed |
| All positive Moodlets across groups | +20 points combined |
| All negative Moodlets across groups | -30 points combined |

First assess each Moodlet under its own intensity and stacking rules, then
apply the relevant group caps. Sum the resulting positive contributions and
cap at +20; separately sum negative magnitudes and cap at thirty. Only then
combine positive and negative contributions with the need-derived mood value.
Do not net unlimited positive/negative sums before applying the two common
caps. These caps are not new rolling reward budgets or friendship rules.

Clamp the resulting target to 0-100 and retain the existing need-deficit target
limits on that final value. In particular, one need at zero still limits the
target to at most thirty even with many positive impressions. Actual numeric
mood retains its existing timed response; reaching or leaving a cap does not
cause an independent instant bar change. Need-only mood reaches at most eighty,
so very good care and up to twenty positive points can together reach one
hundred. Negative impressions can have a larger combined effect, while the
thirty-point limit prevents unbounded deductions merely from parallel entries.

| Need-derived mood | Positive contribution after caps | Negative contribution after caps | Target before any stricter need limit |
| --- | --- | --- | --- |
| 80 | +20 | 0 | 100 |
| 70 | +15 | -10 | 75 |
| 80 | +20 | -30 | 70 |
| 50 | +5 | -30 | 25 |

The limits affect numeric contributions only. Retain every active impression's
own intensity, cause, remaining duration and emotional relevance even when
its group/common numeric cap is reached. Aiko can therefore have numeric mood
seventy and still feel strongly crowded or irritated. Do not truncate the
active collection, suppress wish fulfillment, change emotional-state ranking,
clear an interaction boundary or refund friendship losses to enforce a numeric
cap. Positive experiences can still fulfill wishes and affect interpretation
when no additional numeric bonus is available.

##### Recorded proposal: shared wish creation and concurrency, 2026-10-20

Status: owner-requested design proposal, not implemented. This replaces the
earlier food-only candidates of one active wish, two new wishes per day and
six-hour creation spacing. It does not authorize changes to runtime behavior.

| Rule | Candidate value |
| --- | --- |
| Concurrent inner wishes | At most three in total |
| Area distribution | At most one each from food, games, social activity and affection |
| Lifetime | Four real hours from each wish's creation |
| Global creation spacing | At least sixty real minutes between new wishes, across all areas |
| Same-area creation spacing | At least ninety real minutes since the last wish created in that area |
| Additional daily creation limit | None initially; spacing and occupied slots already constrain frequency |
| Creation availability | Aiko is awake and the app is running |
| Closed app, standby or sleep | Existing wishes age; do not generate retrospective wish sequences |
| Expression pacing | At most one newly voiced wish per thirty real minutes, with one expression per wish initially |

With an available slot and both creation intervals satisfied, choose among
currently plausible candidates. Context defines suitable possibilities; some
random selection provides variety. Do not roll an unconditional creation chance
on every input or require a deficient need as the automatic trigger.

- Food: appetite for a concrete implemented food ID, including while adequately
  supplied. Prefer variety when repetitive food is upsetting her. A matching
  portion need not exist on the desktop, and a wish proves no object knowledge.
- Games: desire for a particular game or an outcome/achievement. Actual recent
  results may inform selection, for example wanting a success after a loss;
  do not invent prior results or create an automatic punishment for losing.
- Social: desire to chat or share funny/interesting content through supported
  choices. API candidates respect enabled online sources and actual capability.
- Affection: desire for closeness even with an adequately filled affection
  need. Recently feeling crowded favors another activity during selection.

Low friendship or poor numeric mood does not prevent inner wishes. Expression
retains the separately recorded comfort/trust conditions, plus the shared
thirty-minute disclosure spacing and current speech priority. All active wishes
remain visible in status, whether spoken or unspoken; reading status is not
actual expression. Speaking neither duplicates a wish nor restarts its lifetime.

Fulfillment frees a slot without resetting or bypassing creation spacing. An
active positive fulfillment Moodlet does not prevent a later independent wish
in that area; otherwise the agreed intensity stacking would be artificially
disabled. Generate no wish retroactively to match a just-completed action.
Keep creation, disclosure, actual fulfillment and emotional after-effects
distinct. Existing deadlines continue through closed/standby time, without
restart renewal or offline generation/backlog.

The following consistency review records how the remaining decisions were
resolved by the owner-confirmed rules. It authorizes no implementation.

##### Agreed wish disclosure and temporary unavailability, 2026-10-20

Status: owner-confirmed rules for implementation, not implemented. This resolves
the previously open food/game disclosure thresholds and common temporary-
unavailability policy. Keep the existing four-hour lifetime, inner-wish pacing,
semantic fulfillment rules and independent relationship accounting.

- Food and game wishes use the same initial disclosure conditions as social
  and affection wishes: friendship level at least three and numeric mood at
  least fifty. Aiko must be awake with a free speaking opportunity. Urgent care
  and ongoing reactions take priority. An unavailable desired activity is not
  announced as an immediately actionable request.
- Each wish is initially voiced at most once; distinct wish utterances are at
  least thirty real minutes apart. Count disclosure only when the concrete
  wish text is actually presented, not when queued or merely shown in status.
  Speaking does not restart a wish or grant a Moodlet/reward.
- Food wishes require no hunger, and game wishes require no fun deficit.
  Express game wishes before a round or in a suitable pause without interrupting
  ongoing gameplay or changing an existing objective's scoring rules. A matching
  food portion need not already exist on the desktop; the user may supply it.
- Low friendship, low mood or a temporary activity restriction does not remove
  an inner wish or prevent otherwise qualifying fulfillment. All active inner
  wishes remain visible in status regardless of disclosure.
- A temporarily unfulfillable wish keeps its original deadline and occupied
  slot. Do not pause, extend, replace or renew it. This includes a previously
  created API wish after online content is disabled/unavailable, or an affection
  wish during a temporary petting refusal. Preserve creation-time capability
  rules: disabled APIs do not become candidates for new API wishes.
- If the activity becomes available before expiry, the wish can be fulfilled
  normally. An unspoken wish may then be voiced if all disclosure conditions
  hold. A previously voiced wish is not automatically repeated. Show a known
  temporary restriction readably in status; absence of a desktop food portion
  alone is not such a restriction.
- Unfulfilled expiry is neutral: no negative Moodlet and no friendship loss.
  Existing dissatisfaction, neglect or boundaries retain their own independent
  rules; wish expiry creates no additional penalty. Sleep, closed-app time and
  standby continue to age the original deadline without generating utterance
  backlogs or personal interactions.

##### Design consistency review: Moodlets and wishes, 2026-10-20

Scope: read-only review of the recorded design and its existing ownership
constraints, not a runtime audit, test result or implementation sign-off.
The model consistently separates needs, immediate reactions, inner wishes,
expression, fulfillment, lasting impressions, numeric mood, overall emotional
interpretation and relationship consequences. Shared limits do not discard
emotional evidence; positive fulfillment can coexist with targeted negative
relief. Persisted elapsed-time ownership does not require replaying offline
personal interactions or building another active simulation.

The obsolete food-only concurrency/creation limits have been explicitly
superseded above. The later recovery-interruption/renewed-exposure proposal now
resolves that previously open policy. No conflicting new values are approved
by this review.

Game-goal failure, retries, cross-session progress and eligible game-round
timing are now specified in the later recorded lifecycle proposal. Remaining
completion conventions below concern other event types or simultaneous events.

Wish disclosure, temporary unavailability, emotional aggregation/labels/mood
thresholds, relief eligibility across refresh/escalation and the separate wish
friendship reward below are now resolved. Initial creation/candidate selection,
equal-ranked direction ties and equal-time completion ordering remain
implementation conventions within the recorded scope, not
additional product workshops. Resolve semantic completion once so duplicate
delivery cannot replay relief, fulfillment or rewards.

##### Agreed rules: wish fulfillment friendship bonuses, 2026-10-20

Status: owner-confirmed design rules, not implemented. A qualifying personal
fulfillment may add a nominal 0.25 friendship points once per wish, independently
of its positive Moodlet. This confirms the earlier personal food-handover bonus
and extends the same amount to the other three wish areas.

| Wish area | Qualifying fulfillment | Nominal additional friendship reward |
| --- | --- | --- |
| Food | Personal handover actually consumed under the food-wish rules | +0.25 points |
| Games | Actual shared play or the specified round/overall result under the game-wish rules | +0.25 points |
| Social | The desired complete conversation/content sequence | +0.25 points |
| Affection | Actually accepted petting fulfilling the active wish | +0.25 points |

The wish must already exist and be fulfilled within its lifetime. Expression is
not required. All game objective forms use the same relationship bonus; larger
goals retain their separately agreed stronger/longer fulfillment Moodlets.
Rejected attempts, interrupted social sequences, failed/expired wishes, later
ordinary rounds and Moodlet stacking/ageing alone grant no additional reward.
Autonomous food intake can still fulfill a wish/create its impression, but does
not imply personal user care or grant this friendship bonus, including offline.

Ordinary care rewards and wish bonuses share the existing rolling ceilings of
0.75 points per two hours and five points per twenty-four hours. Do not create
a separate wish budget or increase those caps. When the same completion grants
both, account for ordinary care first and grant the wish bonus only from the
remaining allowance and room below friendship 100. An ordinary action's reward
interval can suppress its ordinary reward without disqualifying the distinct
wish bonus; all common ceilings still apply. Keep ordinary qualification and
its interval anchors unchanged.

An exhausted allowance can reduce the effective bonus or make it zero without
blocking fulfillment or its positive Moodlet. Persist the completion and reward
accounting atomically with the existing action transaction; no later top-up,
retry, duplicated callback or repeated load may replay that wish's bonus.
Example: an eligible ordinary +0.25 action plus a +0.25 wish bonus yields +0.50
when both budgets have room. If ordinary care already fills the two-hour cap,
the wish's effective extra reward is zero, while its emotional outcome remains.

##### Documented inventory and decisions before implementation, 2026-10-20

Counts below originally inventoried the agreed design; 5B.1 now supplies its
typed catalogue definitions. 5B.2 now stores owned collections; automatic
creation, progression and fulfillment remain unimplemented.
Count wish objectives before substituting individual food IDs or game IDs;
count lasting Moodlet types/families, not intensity levels, emotional labels,
immediate reactions, requests or separate copies for each qualifying activity.

| Wish area | Documented objective forms | Count |
| --- | --- | --- |
| Food | Want a specific implemented food | 1 |
| Games | Play a named game; win a round; do not lose the next round; win overall; do not lose overall | 5 |
| Social | Chat; tell an API Single; tell an API Two Parts; share a fact | 4 |
| Affection | Be petted | 1 |
| Total | Four areas; up to three concurrent wishes and at most one per area | 11 |

There can be many concrete targets within those forms. For example, the five
game objectives can target each of the three implemented games. This does not
create fifteen independent positive Moodlet families or reward allowances.

| Moodlet group | Documented distinct types/families | Count |
| --- | --- | --- |
| Positive food-wish fulfillment | Exactly what I wanted | 1 |
| Positive game-wish fulfillment | Shared-play enjoyment; pride/achievement; relief | 3 |
| Positive social-wish fulfillment | Connection; cheerfulness shared by Single/Two Parts; enthusiasm | 3 |
| Positive affection-wish fulfillment | Feeling secure / Geborgen | 1 |
| Positive subtotal | Fulfillment impressions | 8 |
| Negative interaction/food impressions | Repeated poking; excessive closeness; repetitive food; withholding; disrupted arrangement | 5 |
| Negative prolonged-poor-care impressions | Hunger; exhaustion; lack of stimulation; loneliness; missing closeness, each as an emotional after-effect rather than the immediate need condition | 5 |
| Negative subtotal | Interaction and prolonged-poor-care impressions | 10 |
| Total | Positive and negative types/families | 18 |

Eighteen is a catalogue count, not a three-entry Moodlet display/storage cap.
The three-concurrent limit applies to wishes. Existing rules already bound
copies and intensity per Moodlet; numeric caps do not delete parallel entries.
The eight positive versus ten negative types do not by themselves prove or
disprove balanced daily outcomes, which also depend on triggers and duration.

No previously listed product decision remains unresolved for the first 5B
version. The owner-confirmed common wish bonus closes the final open reward
question; disclosure, temporary unavailability, game-goal lifecycle, emotional
composition/thresholds, recovery and relief eligibility are specified above.
This is readiness of the design, not evidence of implemented or balanced runtime
behavior and not authorization to begin coding during this documentation turn.

First-creation timing, a simple selection method consistent with agreed context
and pacing, exact equal-time event ordering, bounded progress/exposure records,
save migration and exactly-once application also require concrete implementation
contracts. They need no new emotional subsystem or separate product workshop
for every internal field. Record reasonable conventions within the agreed scope
before coding, preserving canonical owners and the no-invented-history rules.
Detailed selection probabilities, final display wording and later numerical
fine-tuning can follow the first coherent version; no additional wish or Moodlet
catalogue is required just to begin implementing the agreed foundation.

Before implementation, walk through a few explicit timelines for stacking,
simultaneous positive/negative impressions, recovery interruption and reopen
behavior. This review does not establish observed frequency or balanced
day-to-day outcomes from the candidate selection rules. Keep that review
proportionate and local; no GUI tests, timing runs or CI were performed here.

##### 5B readiness and small implementation slices, 2026-10-20

###### 5B.6 implementation conventions

- Evaluate creation once at the current endpoint of each live desktop lifecycle
  tick, after elapsed progression and sleep transitions. The first awake live
  evaluation may create one wish immediately; no separate startup clock or
  persisted random schedule is required. Closed/standby reconstruction only
  expires existing wishes. A return may create one current wish, never a backlog.
- Expire deadlines at `elapsed >= expires_at` before selection or disclosure.
  Creation uses the saved global/area anchors and allocates at most one identity
  per evaluation. Future fulfillment at the exact deadline is too late (5B.7).
- Randomly choose an eligible area, then an objective form and concrete target,
  using the existing Mind RNG. This avoids weighting games by their five forms
  or food by its ten targets. Exclude the food currently causing monotony and
  favor another area while the crowded/petting-boundary impression is active.
  Low friendship, mood or adequate needs do not exclude other inner wishes.
- Online opt-in admits supported API objectives for creation. Disclosure also
  requires an already prepared item in that category's existing warm buffer;
  inspecting readiness neither fetches nor reserves content. Petting uses the
  existing pure acceptance decision; games use the existing energy threshold.
  These temporary restrictions never alter an existing wish or its deadline.
- At a free speaking opportunity, urgent care takes priority, then the oldest
  eligible unspoken wish (instance ID breaks equal-time ties), then ordinary
  commentary. A wish is one concrete text cue with its instance ID attached.
  Actual text presentation acknowledges that ID on the canonical elapsed axis;
  selection, cancellation before text and stale/expired receipts do not count.
  Expression has no care, contact, friendship or Moodlet effects.

The pre-5B.1 read-only code comparison found no existing Moodlet/wish files or
collections. The 5B.1 delivery record below supersedes that file-status snapshot.
`PetValues` already owns immutable care/relationship/sleep state;
extend it and the single `pet_codec.py` entry point, not a second pet save.
`PetState` applies pure policy results, and `progression.py`/the existing session
time plan remain responsible for numeric elapsed advancement. Do not introduce
another clock, active simulation or mutable Moodlet/wish manager.

Concrete integration work remains, rather than further product decisions:

- `GameExperienceCoordinator.complete()` currently receives a game summary at
  session close. Add actual round-start/result evidence through the existing
  game owners for time-bound objectives; retain ordinary session care accounting
  once. Translate player-perspective results to Aiko's perspective once.
- The existing reaction player already reports completion/cancellation. Connect
  complete social sequences to semantic fulfillment/relief, not menu selection
  or care admission. Leave ordinary talk-care timing under its existing owner.
- Existing care/contact/object owners must supply accepted intake/petting,
  boundary violations, observed withholding and reacquired/relocated objects.
  Preserve acquired knowledge and the joint World/Pet transaction, including
  autonomous food fulfillment without invented personal gratitude.
- `PetMind.emotion()` and dialogue context/catalogue filters still combine
  need/lifecycle facts with emotions. Migrate their callers to distinct typed
  reads, preserving immediate reactions and authored sequences rather than
  duplicating that interpretation in the UI.

The following refines orders 2-4 above. Each row is a focused delivery slice;
split the explicitly grouped integrations into separate small commits. Commit
and push each completed unit with its actual targeted checks recorded. This
sequence is a plan only; no Python, JSON, runtime asset or test is changed here.

| Slice | Implementation scope and canonical owners | Targeted verification after implementation is authorized |
| --- | --- | --- |
| 5B.1 Definitions | Add `pet/moodlet_catalog.py`, `pet/wish_catalog.py`, their typed value definitions in `moodlets.py`/`wishes.py`, and packaged `data/moodlets.json`/`data/wishes.json`. Put shared tuning, including the common wish bonus, in the existing balance owner. Keep conditions/algorithms in Python and labels in existing localization resources. | Catalogue validity, references to actual foods/games/social categories, units/ranges and resource packaging; no live sessions. |
| 5B.2 Owned storage | Add immutable active collections/bounded episode and objective progress to `PetValues`, focused `moodlet_codec.py`/`wish_codec.py` codecs and aggregate access through `PetState`. Extend the existing save/checkpoint entry points. | Existing checkpoint/rollback and save cases: legacy saves start without invented experiences, round-trip preserves deadlines and used relief/reward evidence. |
| 5B.3 Shared Moodlet progression | Implement creation/refresh/stacking/expiry and per-episode relief policies in `moodlets.py`; compose numeric effects in `mood.py` and advance them at the relevant boundaries in the existing progression/time path. Keep pure lifecycle and numeric integration as separate coherent commits if needed. | Injected timelines for 3-2-1 decay, refresh/escalation, used-level relief, group/global caps, zero-need limits and expiry within a closed/standby interval; no real-time waiting. |
| 5B.4 Direct negative experiences | Add small immutable semantic facts in `interaction_events.py`; integrate poking, unwelcome petting, food repetition, withholding and disturbed arrangement through existing owners. Separate contact/care and object integrations into commits. | Affected admission, actual evidence, persistence and transaction cases; direct friendship penalties occur once, independently of continuing Moodlets. |
| 5B.5 Poor-care after-effects | Reuse existing bounded exposure and chronology for hunger, exhaustion, stimulation, social and affection impressions; implement stable recovery, pause/resume and accounted-for exposure. | Focused production-policy cases for threshold crossing, recovery interruption, no replay of old burden and reopen; no second neglect history or offline action replay. |
| 5B.6 Wish lifecycle | Implement creation/selection, expiry and separate disclosure eligibility in `wishes.py`; use `PetState` and existing speaking owners for actual disclosure evidence. Record simple first-evaluation, selection and simultaneous-event conventions before this slice. | Three-slot/one-per-area limits, creation/disclosure spacing, unspoken wishes, actual displayed speech, temporary unavailability and expiry through closed time without offline generation. |
| 5B.7 Wish fulfillment by area | Deliver food, affection, games and social as separate commits using their existing owners and transactions. Include the area's positive Moodlet and once-per-wish friendship bonus with its real fulfillment boundary. Games require round evidence; social requires the whole sequence. | Selected area-specific acceptance/completion cases, ordinary care plus wish budget clipping, no bonus replay or invented offline personal care; finite-stock food and retained game-objective progress where applicable. |
| 5B.8 Emotional interpretation and reads | Add `emotions.py`/`derive_emotional_state()`, replace mixed mind/dialogue vocabulary and migrate schema, catalogue filters and actual consumers together. Extend immutable snapshots/view-model contracts for the 18 families and 11 wish forms. Keep schema/caller migration coherent; split passive read projections where independent. | All active Moodlets influence the label; polarity/direction and no-Moodlet thresholds, independent need/sleep facts, existing catalogue selection and read projections. Preserve authored wording and existing locks. |

5B completion means the domain, save, time, semantic events and shared emotional
reads agree under targeted local checks. The approved VN layout, icon exports,
Moodlet strip, wish panel, embedded selectors and settings/Credits remain 5C;
their ownership/read contracts are considered during 5B, without a provisional
UI or another source of truth. The approved game surfaces remain a separate UI
unit. No visual/native acceptance follows from domain readiness.

Use existing tests where they own the contract, add only distinct missing
behavior, inject time and isolate saves. Track individual durations and review
anything exceeding ten seconds during each slice. Run the complete local suite
and full static gates only after the complete refactor, including 5C and the
final OOP review, as already agreed. No GitHub CI, visible test windows or mouse
control is authorized; this planning turn runs no tests at all.

###### 5B.1 delivery record: Moodlet catalogue foundation

The first implementation unit adds immutable definitions for all eighteen
Moodlet families, typed per-trigger parameters and a strict read-only loader
for `data/moodlets.json`. Shared caps/recovery settings extend the existing
balance owner; German labels/descriptions extend the existing text resource.
The food repetition count and initial withholding/direct-loss values remain
with their existing owners. No active episodes, save fields, progression,
interaction handling or UI behavior are introduced in this unit.

Focused local verification: nine Moodlet catalogue cases, ten existing resource
validation cases and six existing text catalogue cases passed (25 total).
The slowest individual case took 0.034 seconds; none exceeded ten seconds.
Scoped Ruff, strict Mypy and Pyright passed for the six affected source modules.
No GUI, mouse, CI or full-suite run was used. This unit was committed and pushed
as `0b4bd62`.

###### 5B.1 completion: wish catalogue and shared tuning

The second implementation unit adds immutable definitions for all eleven wish
forms and strict `data/wishes.json` loading. Validate food targets against the
existing food catalogue, game targets against `GameId`, and social targets
against their objective contracts; a focused test also checks the actual
application `SocialCategory` values without introducing a pet-to-application
import. Validate each positive fulfillment Moodlet's group and initial level,
round scope, immutable targets and localized label/description keys.

The `wishes` balance section owns creation/concurrency/disclosure settings and
the common 0.25-point nominal bonus. Existing care parameters, rolling friendship
ceilings, saves and runtime behavior remain unchanged. No active wish creation,
selection, completion, UI rendering or reward transition is enabled here.

Final selected local batch: 31 tests passed (nine Moodlet catalogue, six wish
catalogue, ten existing resource validation and six existing text catalogue
cases). The slowest individual test took 0.033 seconds in that batch; none
exceeded ten seconds. Scoped Ruff, strict Mypy and Pyright passed. These checks
read packaged JSON through production loaders and use malformed-data fixtures;
no desktop instance, external API, save migration, GUI, mouse or CI was used.
The full suite remains deferred to the completed refactor. Architecture and
changelog now describe definitions as delivered, separately from active state.

5B.1 is complete. Continue with 5B.2 only on the owner's next implementation
instruction: owned immutable state, focused codecs and existing save/checkpoint
integration. Do not add another aggregate, save or clock.

###### 5B.2 first unit: owned Moodlet state and storage

`MoodletEpisode` and `MoodletState` are frozen values in `PetValues`, exposed
read-only by `PetState`. Each episode retains its stable instance/family IDs,
level, cause time, remaining current-stage seconds, used relief levels, bounded
pending repetition count and pause/recovery qualification. Remaining time is
anchored to the owning pet's existing `lived_seconds`; no new clock is added.
The per-section ID counter survives ended episodes. At most one episode per
supported family is stored, not an artificial three-Moodlet display cap.

Technical migration contract: absent/invalid sections create empty emotional
state at the current saved elapsed baseline, never from older care history.
The focused `moodlet_codec.py` validates the optional version-one section;
`pet_codec.py` remains the single pet entry point and the outer save stays v1.
Existing StateStore backup and atomic replacement handle invalid new sections,
including replacement without first loading. Loading performs no ageing,
triggering, relief or relationship change. Evidence-specific trigger/exposure
bookkeeping remains with the later 5B.4/5B.5 policies, using the existing owners.

32 focused local tests passed: seven new emotional persistence cases, six
checkpoint, three repository, eight consumption/rollback and eight elapsed-time
persistence cases. The slowest case took 0.680 seconds; none exceeded ten seconds.
Scoped Ruff, strict Mypy and Pyright passed for the six affected source modules.
No GUI, mouse, external API or CI was used. This unit was committed and pushed
as `a3e120a`; wish state/codecs follow in the next unit.

###### 5B.2 completion: owned wishes, bounded progress and joint rollback

`ActiveWish`, `GameWishProgress` and `WishState` now belong to the same immutable
PetValues checkpoint. The focused `wish_codec.py` extends the existing pet/save
entry point with another optional version-one section. Store stable instance
IDs, concrete targets, original elapsed deadlines, actual expression evidence
and at most the objective's round count of unique completed-round identities
with Aiko's win/loss counts. Shared play also retains its session token; no
board, deck, ordinary game session score or API payload is saved.

Keep at most three active wishes and one per area. Persist the bounded four-area
creation anchors and last actual expression even after wishes end. Derive the
global last creation time from those anchors rather than storing it twice.
Monotonic instance allocation survives an empty active collection; a removed
wish is not resurrected on load. This supplies identity/pacing evidence for later
once-only fulfillment; it does not yet implement or claim reward execution.
Relationship amounts and rolling budgets remain solely in friendship history.

Codecs strictly reject invalid IDs/targets, duplicate instances/areas/rounds,
unbounded or inconsistent counters, invalid types/nonfinite numbers and
impossible timelines. Original deadlines are preserved, including already past
deadlines: loading does not expire wishes, reset timers, generate wishes,
speak, reconstruct play or grant emotional/friendship effects. Missing legacy
wish data is empty. One invalid optional section does not discard other valid
pet state. Existing StateStore corruption checks share one validation path for
relationship, sleep, Moodlet and wish sections before atomic replacement.

The existing handover-failure test now seeds both collections and changes them
before the injected failure, proving full Pet/World/memory rollback without a
second transaction or a parallel aggregate. Captures/deep copies remain frozen
and detached through the existing checkpoint owner.

Final selected local checks: 43 tests passed (14 emotional persistence, eight
consumption/rollback, six checkpoint, three repository, eight elapsed-time and
four World persistence cases). Slowest individual test: 0.697 seconds; none
exceeded ten seconds. Scoped Ruff, strict Mypy and Pyright passed for the eight
affected source modules and the selected tests where applicable. Only injected
times and temporary saves were used; no GUI, mouse, external API or GitHub CI.
No full suite was run; that remains the agreed integrated completion gate.

5B.2 is complete. Next is 5B.3's pure Moodlet lifetime/relief rules and numeric
composition in the existing progression path. Trigger-specific evidence and
poor-care exposure accounting follow in 5B.4/5B.5; wish decisions follow in
5B.6/5B.7. No extra clock, manager, save or active simulation was introduced.

###### 5B.3 first unit: pure Moodlet lifetime, stacking and relief

The existing `pet/moodlets.py` owner now calculates immutable episode transitions
from explicit elapsed intervals and catalogue definitions: bounded tier decay,
refresh/escalation, positive fulfillment strength, absolute newly-qualified
poor-care intensity, cause resolution and once-per-level relief. It creates no
clock, mutable manager, relationship effect or interaction detector.

Technical contracts: callers advance the pet before applying newly qualified
trigger/relief facts; later 5B.4/5B.7 owners match actual accepted/completed actions
and suppress duplicate event delivery. Quiet tier decay clears pending escalation
counts but retains used relief levels and the episode identity. Refresh and
escalation never reset relief usage. One helpful completion shortens only the
current tier and discards surplus time; complete expiry retires the episode ID.

Existing poor-care impressions require thirty continuous healthy minutes before
recovery, retain current-tier progress through interruptions and requalify after
a new drop. Linear need segments identify the healthy portion of an interval.
Unobserved time ends an observed withholding pause and ages its after-effect;
it never synthesizes additional withholding/escalation. Exposure-trigger creation
and target-specific helpful-action matching remain later-stage responsibilities.

26 targeted local cases passed: twelve new pure timeline cases and fourteen
existing emotional storage cases. Slowest individual test: 0.008 seconds; none
over ten seconds. Scoped Ruff, strict Mypy and Pyright passed. No GUI, mouse,
external API, CI or full-suite run. This unit was committed and pushed as
`1e650cc`; numeric integration follows in the next unit.

###### 5B.3 completion: numeric composition and existing time-path integration

`calculate_moodlet_contributions()` applies per-family strengths, game/social
and poor-care group caps, then separate common +20/-30 limits. It retains all
active emotional evidence. `calculate_mood_target()` composes those signed
contributions with the existing need-derived target and reapplies the final
need-deficit ceiling and 0-100 clamp. Existing timed decline/recovery rates
remain the sole adjustment of actual mood; no instant mood or friendship award.

The existing `calculate_pet_progression()` loop now returns the owned Moodlet
state alongside needs/mood/food/relationship progress. `PetState` commits the
result in its existing single update. The numerical need update is factored
once for evaluation at shorter boundaries, not duplicated in another integrator.
Intervals split at Moodlet tier/expiry boundaries, stable recovery qualification
and need crossings of forty. Each preceding interval uses its previous emotional
effect; a later expiry is not retroactively applied to the whole interval.
Remaining stage time and recovery qualification stay on `lived_seconds`.

Both restoration paths explicitly mark reconstructed time unobserved, including
a short closed interval inside the ordinary observation-freshness tail. That
ages a previously observed withholding after-effect without inventing continued
provocation. SessionTimeProgression retains its paired World/Pet/memory owner;
no offline action player, extra timer or separate simulation is added. Live
intervals retain the existing observation boundaries. Storage still only decodes;
application/domain time advancement consumes the interval once.

Targeted verification covered 111 distinct local cases across: twelve pure
Moodlet timelines, ten composition/integration cases, fourteen emotional saves,
eight need/mood balance, ten domain transitions, ten pet lifecycle, eight elapsed
persistence, eight offline progression, sixteen sleep priorities, eight joint
consumption/rollback and seven session restoration cases. Selected cases were
rerun only after relevant fixes. Scoped Ruff, strict Mypy and Pyright passed.
The slowest case was the existing long-absence/backward-clock scenario at 5.332
seconds; none exceeded ten seconds. A full-day scenario with all eighteen
families took 0.314 seconds and retained only the still-unrecovered poor-care
impressions. The existing full-week numeric scenario took 1.403 seconds.

Updated the older exact save-key assertion to include the already delivered
5B.2 optional Moodlet/wish sections, preserving all old field assertions. The
restart comparison respects the existing four-decimal numeric save rounding
while checking exact elapsed time and emotional state. No GUI windows, mouse,
external API or GitHub CI; no full-suite run. All saves are temporary/injected.

5B.3 is complete. Qualifying direct experiences, cause-specific evidence and
completed helpful-action matching remain 5B.4; poor-care trigger/exposure
accounting remains 5B.5. Wishes and final emotional labels follow their own
slices. The pure trigger/relief APIs require already-qualified semantic facts
at an already-advanced pet endpoint; they do not independently detect clicks,
intake, play, speech, refusal or user responsibility.

#### 5C. Connect status, expression and interaction decisions

- Implement the main-menu scope of [the VN UI plan](UI_VN_DESIGN.md) together
  with the following read-model integration, using the recorded source pack
  and the module/data ownership above. This is part of stage 5C rather than a
  separate provisional menu with another state owner.
- Extend `PetReadSnapshot`, presentation projections and toolbar contracts with
  distinct needs, numeric mood, emotional state, active Moodlets and wishes.
  Show Moodlets and wishes in the existing status UI alongside the care values;
  include understandable causes/targets and relevant strength/remaining time.
  UI formatting must not own expiry, reward or emotional calculations.
- Project target/actual mood, friendship stage, sleep reason and genuine
  absence/contact context through existing typed reads where required.
- Use the same emotional interpretation for status, conversation and behavior.
  Direct need statements must remain available independently of that label.
- Audit cheerful/playful filters and idle emotes against the final composition.
  Ordinary positive behavior must be reachable under normal good care; reserve
  any higher thresholds for deliberately defined positive emotional experiences.
  Do not settle these thresholds before the Moodlet/emotion rules are agreed.
- Remove hardware-only emotional conclusions while preserving statements about
  genuinely observed desktop load. Moderate numeric mood or friendship 10-to-9
  alone is not evidence of relationship offense.
- Keep toolbar availability, sleep handling, game completion and bubble playback
  consistent. Preserve the authored German sequences; change individual wording
  only when approved semantics require it. Update the review workbook only for
  actual text edits.

##### Menu, character action and item-placement decoupling, 2026-10-20

Initial review: corrections planned, not implemented at that point. The owner
reports that object discovery appears to stall while the pointer is over the
menu and that Snacks is disabled during character actions. No runtime freeze
was reproduced, no tests were executed and no desktop input was generated for
this review. Include these corrections in stage 5C and its integrated VN menu.

Confirmed coupling in the existing code:

- `HoverUi.interaction_active` combines pointer/menu engagement and settings
  engagement. `gui.py` passes it as `controls_active` to `DesktopWorldRuntime`
  and under the misleading name `toolbar_visible` to animation/walk assembly.
  `ObjectBehaviorCoordinator.observe` blocks autonomous object selection when
  controls are engaged and no object interaction is active. This can hold the
  transition into discovery/approach while the menu is being used.
- Existing committed object interactions already bypass that particular
  controls gate, and `WalkRuntime.step` exempts committed goals from toolbar
  suppression. `choose_animation_priority` has no menu input, and the World
  motion/cursor frame loop is not gated by menu engagement. Therefore the
  reported apparent animation stall is not yet evidence of a frozen clip
  timer. Preserve these distinctions when implementing and diagnosing it.
- The Snack button, `HoverUi._interact`, `open_food_menu` and `_food_selected`
  use the generic `can_interact("feed")` admission path; the latter two also
  reject an open game. `ContactCoordinator.can_interact` rejects foreground
  object actions, games, sleep and busy playback as appropriate for direct
  character interactions. However, the Snack callback actually calls
  `DesktopWorldRuntime.begin_carry`, creating a held World item for placement.
  Supplying an item is incorrectly subject to direct-care admission.
- `begin_carry` also uses `_request_gesture`. With an active object interaction,
  that helper starts the cursor gesture directly. Otherwise it calls
  `interrupt`, cancelling intentions, the walk goal and object gaze. Thus
  simply preparing new stock can unnecessarily interrupt an uncommitted object
  intention. Review this path separately from taking an existing wanted item.
- `CursorItemGesture.release` already separates attempted handover from
  ordinary World release: when handover does not occur, an inside drop places
  the finite item in the World. Reuse this custody path rather than adding a
  second placement implementation.

Required ownership and behavior:

1. Separate menu engagement, actual character-action admission and cursor item
   placement. Use explicit port/fact names such as `menu_engaged` and
   `can_place_item` rather than overloading `toolbar_visible`, `controls_active`
   or `feed`. Update the existing callers together. Menu engagement can govern
   menu lifetime and incidental chatter without holding object discovery,
   recognition, committed movement or action completion. Preserve independently
   justified sleep, game and exclusive-action rules for Aiko's behavior.
2. Keep Snacks available while Aiko acts, sleeps or plays. Use the same
   placement capability for the button, selector opening and selection
   callback; remove character-state and game admission from these placement
   paths. Retain valid World geometry and single cursor-capture ownership.
   Availability must not silently replace an already held item or steal an
   unrelated input gesture.
3. Preparing and dropping a new portion must not cancel Aiko's unrelated
   intention, restart her discovery or interrupt her current animation/action.
   Keep actual handover/consumption subject to the existing perception,
   willingness, interaction and atomic custody rules. Deliberately taking or
   withholding an existing wanted object retains its separate consequences.
4. Keep the existing owners: `HoverUi`/toolbar and embedded selectors present
   capabilities; application policies decide character admission;
   `DesktopWorldRuntime` and `CursorItemGesture` coordinate World placement;
   object interaction and animation owners complete their own actions. Add no
   parallel action manager, World writer or timer loop. Audit each consumer of
   the broad engagement flags rather than removing every guard indiscriminately.

Implementation verification must be local and headless, using existing test
seams and injected pointer/clock/action facts. Cover menu engagement during
object selection and committed approach, uninterrupted action completion,
placement during a busy action/sleep/game, exactly-once item creation/release,
and unchanged rejection/handover and capture ownership. Keep these checks
focused; investigate any test exceeding ten seconds. No native test windows,
desktop mouse control or GitHub-CI run is part of this work. A later visual
confirmation of the originally reported stall must be distinguished from
these deterministic policy checks.

###### Delivery record

The owner subsequently authorized this correction package. Implemented in the
existing owners without new production modules, timers or mutable managers:

- Renamed menu engagement ports separately from actual character playback.
  World behavior no longer reads menu engagement. Idle wandering and incidental
  chatter retain their menu-use suppression; committed object movement remains
  independent of it.
- The toolbar and food-selector entry/selection use `place_item` and
  `can_place_item`, independent of care, sleep and games. Cursor capture is
  rechecked at execution; repeated requests preserve the already held portion.
- Preparing stock bypasses the old intention/animation interruption route.
  Post-gesture orientation refresh only starts when idle; it does not reset
  an ongoing look, goal or interaction.
  Relocating existing objects retains its explicit interaction path and checks
  capture availability before interruption.
- Busy character speech, sleep and games still prevent unsolicited offer
  previews and intake. The offer's own preview does not block its authorized
  handover. Cancelling a cursor gesture cancels only offer/refusal feedback,
  preserving unrelated care dialogue and object episodes.
- Updated existing internal callers and native-test expectations together;
  documented the renamed contracts in [Architecture](ARCHITECTURE.md).

Local verification: 169 focused policy, coordination, playback, movement and
architecture tests passed with Tk/Toplevel construction explicitly prohibited.
The complete run took about one second; no individual test exceeded ten
seconds. Repository-wide Ruff, strict Mypy (221 source files) and Pyright passed.
Native tests were updated but not executed. No test windows, desktop mouse
control or GitHub CI were used. The reported visual stall still needs separate
owner-observed confirmation; these checks establish the corrected code paths,
not a native visual acceptance claim. The rest of stage 5 remains pending.

Exit: the code and UI expose separate, clearly named layers; immediate reactions,
need effects, lasting Moodlets, wishes, numeric mood, overall emotional state and
relationship consequences remain distinguishable and share the existing owners.

### 6. Verify integrated behavior and document the delivered system

Turn the arithmetic scenarios into tests of production policies with injected
time and isolated saves. The discussion calculations are expected behavior,
not a substitute for these tests. Keep schedule inputs/assumptions visible;
use tolerance and event assertions rather than brittle rounded-table snapshots.
The existing numerical examples below describe the care foundation without
new Moodlet/wish effects. Preserve that baseline coverage and add separately
specified emotional scenarios after stage-5 rules are agreed; do not silently
change the reference outcomes to accommodate unapproved bonuses or penalties.

| Scenario | Required evidence |
| --- | --- |
| Eight distributed care phases, 23:00–07:00 sleep | All needs stay above 40; mood roughly 57–78; the selected 95-start friendship day earns 5 and loses 4 overnight, maintaining level 10. Energy reaches 100 around 06:40 without premature waking. |
| Four sufficiently supplied care phases | The [bundled schedule](NEEDS_BALANCE_PROPOSAL.md#combined-four-phase-average-care-day) settles near 69–71 friendship, levels 7–8, with +3/-3 daily. All needs remain above 40 and actual mood is roughly 48–79. |
| Four visits with insufficient food/talk | Visit count alone cannot guarantee the target relationship. The shorter comparison reaches hunger/social deficits and neglect; do not award adequate-care results from contact frequency alone. |
| Morning/evening care and prolonged absence | The lower curve softens ordinary sparse care; there is no guaranteed level floor. Verify the absence/neglect maximum, resource exhaustion and zero needs without death or hidden supply. |
| Empty/limited/unknown food stock | Consume only valid finite portions once. Unknown items remain unknown while closed; failed searches, rejected food and rollback do not create nutrition/contact. |
| Manual sleep/wake, early return, exhaustion and hunger | Check each priority collision, manual protection expiry, cumulative actual sleep, nap/recovery endpoints and food-break return. |
| Three/seven recurring quiet phases and one exception | Learn from permitted observations only; no jitter, heavy background computation or app restart substitutes for actual human input. |
| Restart, standby, 8+ hours, multi-day gaps and clock changes | No truncated needs/relationship time, replayed rewards/food or invented activity; histories remain bounded and advancement stays practical. |
| Legacy/new saves, repeated loads and failed joint commits | Preserve valid progress and portion custody; no invented historical neglect, timer reset or partial World/Pet update. |

Build on `test_active_time`, `test_pet_lifecycle`, `test_offline_progress`,
`test_session_restoration`, `test_food`, `test_fun_mood`,
`test_friendship_policy`, adaptive/care/game tests, checkpoints and paired
World/object-memory persistence tests. Add focused new test owners where the
new behavior does not fit an existing responsibility. Keep architecture/import,
resource validation and UI projection coverage intact.

During implementation, use the focused checks in the small-commit sequence
above. Once the complete refactor and final OOP review are finished, run the
complete local suite and repository-wide static gates in
[Contributing](../CONTRIBUTING.md#development-workflow). Retain
the owner's restrictions: no GitHub CI execution, visible test windows or mouse
control on the working desktop. Use injected time, isolated saves and focused
policy/projection/transaction checks; use the established isolated local GUI
environment only when actual scheduling integration needs it. Review individual
tests exceeding ten seconds, recording their cause and disposition rather than
automatically deleting them or masking their domain work with mocks. This
documentation amendment itself does not authorize test execution.

Record physical Windows acceptance separately: meaningful input versus jitter,
sleep/manual wake, actual suspend/resume, finite-stock close/reopen and native
playback/input behavior cannot be claimed from arithmetic or headless checks.
Do not launch such desktop checks without a later change to the owner's scope.

Update architecture, food, fun/mood, saves and relevant World/smoke guides when
the behavior is implemented. Record the migration and actual validation in the
changelog; archive this plan only after delivery. No merge is implied here.

## Small decisions to settle inside the relevant stage

The stages 1–4 care foundation is sufficiently specified. The existing bounded
details below remain separate from the newly required stage-5 Moodlet, wish and
emotional-state discussion; that expanded behavior is not yet fully specified.

| Detail | Starting approach / decision needed |
| --- | --- |
| Reserve fade and high-fun saturation | Start with the calculated linear reserve fade (full protection from 80 reserve minutes, now capped at 25%) and retain the existing high-fun reward reduction. Verify both schedules with those choices. |
| Same-type rewards and old variety bonus | Resolved in stage 3: no variety bonus; early repetitions do not move the anchor; eligible attempts consume the interval even without remaining reward; qualified contact is independent. |
| Input/load normalization | Reuse available coarse observations; validate the approximately 30% CPU/GPU threshold and input range with idle, office and heavy-load cases. Do not interpret RAM occupancy as evidence of human presence. |
| Quiet-phase grouping and nap duration | Choose one simple main quiet phase per day, an explicit timing-similarity rule and one deterministic duration within the discussed 60–90-minute nap range. Preserve the three/seven milestones and adjustment limit; avoid extra scoring, weekday models or new sensors. |
| Episode boundaries and conflicting care | Specify when a sleep phase ends, when a genuinely new offer permits another search, and the low-energy hunger-break collision after manual protection. Keep acute care bounded and return to needed recovery. Specify when an explicit care command wakes Aiko versus being deferred. |
| Negative-interaction episodes | Resolved in stage 3: existing selected boundary events warn within the current click burst; only later admitted clicks qualify. Existing claimed-object episode evidence retains 18-second/three-take escalation. Durable rolling caps survive episode/restart boundaries. |
| Positive expressions and old settings | Resolve after stage-5 Moodlet/emotional-state rules: choose reachable thresholds without forcing routine care to maximum mood; record how current routine/preferences map to behavior. |

If one of these changes the accepted care burden or relationship outcome,
bring that specific tradeoff back for discussion. Routine contract and
implementation choices do not require reopening the agreed balance.


##### 5B.4 delivery: contact boundaries (2026-10-20)

Implemented poking and unwelcome petting through immutable facts in
`pet/interaction_events.py` and pure decisions in `pet/interaction_rules.py`.
The latter separates trigger qualification from the existing lifetime rules in
`moodlets.py`; neither module owns mutable state or a clock. `PetState` commits
consequences and retains all durable boundary/refusal evidence inside its
existing Moodlet value. The optional codec extension accepts earlier 5B saves.

A first actually displayed text cue acknowledges the boundary; selected,
queued or cancelled-before-text reactions do not. Accepted click admission
advances the existing session clock before qualifying pokes. Existing direct
click penalties remain separate. Unwelcome petting grants no care/contact,
friendship reward or petting animation. Refusal deadlines and the separate
rolling ten-minute loss budget survive restart; penalties prune by their own
window, rather than retaining short-window click history for longer budgets.

Validation: 83 scoped headless tests passed (contact, care results/presentation,
negative interactions, persistence, friendship, reaction playback and resource
contracts); longest individual test 0.259 s. Scoped Ruff, strict Mypy and
Pyright passed. No windows, mouse control, CI or full-suite execution.
Food and object integrations remain in this same 5B.4 slice.


##### 5B.4 delivery: food repetition and communicated variety (2026-10-20)

Canonical accepted intake now supplies `FoodConsumed`, including explicit
personal/autonomous origin inside the existing joint consumption transaction.
A bounded timestamp sequence (using the existing repetition count) qualifies
food monotony within 24 elapsed hours; drinks do not count or break it. Actual
different food breaks the sequence/request and applies existing tier-limited
relief, without deleting the Moodlet or changing nutrition rules.

Request, delivery timestamp and bounded ignored-portion count live inside the
same aggregate-owned interaction evidence. Personal meal reactions and the next
eligible pointer contact can present the pending request. Only a text receipt
marks communication. The first ignored personal portion reminds without loss;
subsequent ones use the existing relationship ledger with a separate rolling
24-hour cap. Autonomous or reconstructed intake never blames the user. A new
request/different food cannot refund that ledger; restart preserves both.

Validation: 81 scoped headless tests passed, including actual intake origin,
World transaction rollback, corruption/legacy storage, request delivery,
expiry, bounded evidence and budget preservation. Longest test 0.258 s.
Scoped Ruff, strict Mypy and Pyright passed. Object integration remains next.


##### 5B.4 delivery: withholding and familiar arrangement (2026-10-20)

The existing withholding episode now qualifies initial irritation and separate
30-observed-second reinforcement. Its existing direct-loss receipts/budget are
unchanged. A fresh take can reinforce an existing impression once; the next
complaint does not count that same take twice. Reappraisal requires the concrete
object still to be wanted. Return, interrupted ownership or no longer wanting
it resolves the cause without erasing the impression. Unobserved elapsed time
ages it without manufacturing further provocation or direct loss.

ObjectAwareness retains only the current witnessed take's learned origin until
observed settling or loss of continuity. It emits one semantic relocation fact
when that same recognized subject settles outside the existing placement area;
no new pixel threshold or hidden-position lookup was added. Minor moves,
unknown objects and Aiko's own custody/put-down do not qualify. The native
adapter excludes the same take when the existing interaction has claimed it as
withholding. A checked empty familiar place independently creates an unattributed
impression when its existing notice is accepted; continued search does not stack.
Only witnessed relocation charges the separately persisted rolling hourly budget.

Validation: 137 scoped headless tests passed, including subjective continuity,
small/unknown/excluded moves, actual withholding admission/escalation/return,
request clocks, independent loss budgets, save reload and World transaction
rollback. Longest individual test 0.275 s. Scoped Ruff, strict Mypy and Pyright
passed. Targeted helpful-action matching and final documentation follow next.


##### 5B.4 completion: helpful actions and ownership review (2026-10-20)

Completed matching uses the same immutable facts and pure interaction policy.
Accepted petting, actual main meals and sessions with at least two completed
rounds supply helpful facts through the existing care/consumption/game owners.
Personal chat and prepared API conversations carry explicit completion metadata
only after accepted care. ReactionPlayer reports that fact once after the whole
sequence; cancellation, stale callbacks, waiting and ambient dialogue cannot
claim completion. Chat/shared play can shorten resolved withholding; arrangement
relief additionally reads resolved live search/place evidence through the existing
World port. The lifetime owner still enforces quiet/stable-recovery gates and
one allowance per intensity for the entire episode. No helpful action refunds
friendship or shortens the separate petting-refusal deadline.

Final ownership review keeps petting admission in `plan_care_action`, returning
immutable interaction consequences even for a refusal with no care changes.
PetState commits those consequences through one named helper. Presentation event
names are translated into domain facts by `application/contact.py`, not by the
pet aggregate. No event bus, manager, parallel clock/history store or second
numeric mood writer was introduced. Care tests that assumed unlimited petting
now explicitly seed welcome affection/trust or assert refusal without reward.
A continuing food sequence whose request expired must communicate a fresh
request before further ignored-request charges can qualify.

5B.4 is implemented. Negative interaction families are now live; 5B.5 remains
responsible for prolonged-poor-care exposure/triggering, followed by wish,
overall emotion and status UI slices. Existing stored poor-care episodes can
already receive qualified relief under their established recovery gate.
The complete-suite and final overall OOP audit remain the planned end-of-refactor
gates. No visible desktop acceptance is claimed by these local headless checks.


Final 5B.4 verification: 361 selected headless cases across the affected care,
Moodlet, storage, dialogue/playback, object, friendship and architecture modules
passed in 4.219 s. The longest individual test was 0.376 s; no case required
investigation under the ten-second threshold. The selection explicitly checks
that every requested test module contains cases, and excludes GUI tests and the
full suite. Ruff passed for all changed Python files; strict Mypy and Pyright
passed for all 31 changed production modules. The pure care-plan/aggregate parity
and existing dependency/composition-root limits are preserved. The final full
suite and broader OOP audit remain the agreed end-of-refactor tasks, not a gate
silently substituted for these targeted checks. No GitHub CI was requested or
started; commits carry the CI skip marker.


Code delivery commits on `feature/social-optimization`:

| Commit | Coherent change |
| --- | --- |
| `2f333f1` | Poking, communicated boundaries and unwelcome petting |
| `e7bc487` | Actual food repetition, variety request and personal loss budget |
| `c175195` | Observed withholding, familiar arrangement and attribution |
| `ada8209` | Helpful-action completion, pure care admission and final ownership corrections |

Each commit was locally checked and pushed with `[skip ci]`. The following
documentation commit records this completed slice and updates the system guides.


##### 5B.5 delivery: shared exposure reader and durable processing markers (2026-10-20)

`pet/need_exposure.py` now owns the original rolling-window read calculation,
extracted unchanged from friendship decay. Its watermark reader excludes already
handled emotional burden while retaining exact offsets in a partially filled
minute; the existing history can still coalesce full minutes. It neither records
another need timeline nor integrates another simulation.

Frozen `PoorCareEvidence` and five `PoorCareCursor` values belong to the existing
Moodlet aggregate value. Two watermarks per need distinguish the previously
accounted burden from thresholds handled in the current deficient stretch.
The optional existing-save extension has strict decoding in
`infrastructure/poor_care_codec.py`; missing old evidence remains uninitialized,
so the later progression integration can start at the current elapsed endpoint
without replaying legacy care history. Loading/checkpointing never ages or
creates impressions. Friendship history, its loss rules and ownership are retained.

Validation: 30 focused exposure, friendship-neglect and emotional-storage tests
passed in 6.714 s. The existing 30-day bounded-history case took 5.961 s; no case
exceeded ten seconds. Scoped Ruff, strict Mypy and Pyright passed. These checks
were local and headless; no full suite, windows, mouse control or GitHub CI.
Trigger/recovery integration is the next commit within this same 5B.5 slice.


##### 5B.5 delivery: qualification and accounted burden (2026-10-20)

Pure `pet/poor_care.py` qualifies the five catalogued after-effects from that
same history. Alternative critical/zero thresholds select the maximum eligible
level; they are never added. It records a newly handled threshold once and raises
an existing impression only when the genuinely new level exceeds its current
intensity. At the maximum, additional burden is represented by that active
impression, without timer refresh or a backlog of future stacks.

The accounting cycle includes disjoint deficits until recovery actually
qualifies. Merely crossing 25, remaining between 25 and 40, or briefly reaching
40 cannot consume handled burden or reset its escalation cycle. After 30 stable
minutes at 40+, handled thresholds are closed while the not-yet-qualified
remainder survives in the canonical history. Stable recovery, stage progress
through interruption and once-per-level relief remain owned by `moodlets.py`.
No separate friendship loss, contact or care rejection is introduced.

Fifteen focused reader/accounting/policy cases passed within the targeted
selection, including fresh residual burden through reload and recovery.
The new exact chronology also exposed a pre-existing minute coalescing edge:
a near-full minute could merge before its final nanosecond, then overlap its
own tiny tail on the next update. Full-minute merging now additionally requires
actual arrival at the minute end; the unchanged split/reload history test and a
small direct regression case pass. Watermark offsets are bounded against floating
round-off before storage. Scoped Ruff, strict Mypy and Pyright passed.


##### 5B.5 completion: existing chronology and isolated verification (2026-10-20)

`calculate_pet_progression()` now prepares processing markers, advances the one
friendship/care history and qualifies poor-care impressions at the actual numeric
endpoint. Its existing loop splits at zero/25/40 crossings and newly reachable
emotional thresholds. Crossings read the canonical need calculation, including
clamped-zero arrival, rather than counting a whole partly depleted step as zero.
Threshold search only reads the bounded history; no second time progression or
historical user-action playback was added. Pure numeric calls without relationship
evidence still age existing impressions without inventing a missing care history.
PetState continues to commit the combined frozen result once.

Both closed-app and standby paths use this integration. Actual finite, acquired
food consumption can prevent prolonged hunger; unrecognized stock cannot. Sleep
restoring energy adds no exhaustion exposure. Existing stable recovery, retained
stage progress, relief allowances and checkpoint/World rollback are preserved.
No new direct relationship penalty, qualified care contact or care lock is added.

The unchanged 30-day regression initially took 12.241 s after integration. Review
found repeated emotional work after all five zero needs were already represented
by five paused maximum impressions. This constant tail now bypasses redundant
emotional qualification/ageing only while there are no other Moodlet families;
canonical need/history/mood advancement continues. A separate regression proves
that other positive impressions still expire and needed food is accepted. The
month scenario is retained rather than shortened or replaced with a mock.

Final targeted local validation: 171 cases passed in 15.702 s across the three
new poor-care modules and affected lifetime/composition, friendship, numeric
progression, persistence, finite resources/rollback, relief and architecture
modules. The existing 30-day test took 8.111 s; the week case took 2.467 s.
No final individual test exceeded ten seconds. Ruff passed for all changed Python
files, and strict Mypy/Pyright passed for all seven changed production modules.
No windows, mouse steering, GitHub CI or full-suite run was performed.

5B.5 is complete. The next slice is 5B.6 (inner wish lifecycle and disclosure);
wish fulfillment, overall emotional interpretation and status UI remain in their
recorded later slices. The full suite and final overall OOP audit remain the
agreed end-of-refactor checks.


5B.5 code delivery commits on `feature/social-optimization`:

| Commit | Coherent change |
| --- | --- |
| `f51519a` | Shared bounded exposure reader and optional durable processing markers |
| `67582fc` | Pure qualification/recovery accounting and exact minute coalescing |
| `f927c9c` | Integration into existing numeric/closed-time progression and resource checks |

Each unit was locally checked and pushed with `[skip ci]`. The documentation
follow-up updates the ownership, storage and mood/friendship guides to this state.


##### 5B.6 completion: live wish lifecycle and actual disclosure (2026-10-20)

The implementation conventions above were recorded before coding. Pure
`wishes.py` policies now apply creation/area spacing, three slots, four-hour
original deadlines, contextual selection, temporary restrictions, oldest-first
eligible disclosure and exactly-once actual expression. Definitions are
injected into policy; the existing catalogue and balance remain authoritative.

PetState owns all changes. Its existing progression and endpoint finalization
expire wishes on both direct and World-coordinated time paths. Neither decoding
nor closed/standby reconstruction creates wishes or personal interactions.
The existing desktop attention endpoint separately evaluates at most one
current awake opportunity, including while menus/actions occupy presentation.
Creation uses Mind's RNG across eligible areas, forms and concrete targets.

Attention reuses existing pure petting admission and game energy rules. Online
opt-in admits supported API candidates; a read-only view of the existing warm
buffers gates immediate API disclosure without fetching/reserving content.
Disabled sources, unavailable prepared content and temporary petting/game
restrictions retain the original wish and deadline. Urgent needs, existing
reactions, foreground actions and gameplay retain speech priority.

PetMind renders all eleven objective forms with canonical targets and round
counts through validated German resources. The existing immutable Reaction
carries a wish instance ID; ReactionPlayer reports it after actual text display.
Selection/status are not disclosure. Cancellation before text, stale callbacks,
duplicate receipts and expired/missing identities cannot replay expression.
The existing optional v1 save fields persist the result and expression spacing.
Creation, expiry and speech do not grant need, friendship or Moodlet effects.

| Commit | Coherent change |
| --- | --- |
| `2fbb8de` | Recorded conventions, pure lifecycle/disclosure rules and aggregate time ownership |
| `0048e49` | Live attention integration, concrete requests, actual playback receipts and closed/standby checks |

Final targeted local verification: **146 headless tests passed in 2.541 seconds**.
The longest individual case took **0.329 seconds**; no selected test exceeded
10 seconds. The selected modules cover wish lifecycle/catalogue/expression,
emotional persistence and mood progression, attention decisions/desktop wiring,
reaction playback, social readiness, text/Mind catalogues, architecture guards,
session restoration and finite-stock sleep resources. Ruff passed for changed
Python files; strict Mypy and Pyright passed for all ten changed production
modules. Pyright also checked the affected/new test modules.

Focused ownership review found no extra mutable Pet owner, clock, save store,
conversation player, wish queue, offline generation loop or reward ledger.
The GUI composition root remains within its existing 640-line gate. Tests use
explicit timestamps, temporary stores and FakeScheduler callbacks; none opens
a window, controls the mouse, calls an API or waits for gameplay time. Both
code commits were locally checked and pushed with `[skip ci]`. No GitHub CI,
full-suite run, merge or physical desktop acceptance was performed.

5B.6 is complete. Next is **5B.7**, split into food, affection, games and social
fulfillment with their real completion boundaries, positive Moodlets and
independent capped friendship bonus. Overall emotional reads (5B.8), combined
status UI (5C), the final full suite and final broad OOP review remain planned.


##### 5B.7 completion: actual fulfillment and shared-budget bonus (2026-10-20)

All four areas now resolve pre-existing, spoken or unspoken wishes through their
actual accepted/completed boundaries. Pure `fulfill_activity_wish()` and
`progress_game_wish()` return frozen `WishResolution` values. PetState retires the
identity and commits the catalogue's positive Moodlet/strength and eligible
personal friendship credit together. Creation/disclosure anchors are retained.
Existing Moodlet reinforcement, elapsed ageing, tier durations and group/global
caps remain authoritative; no direct numeric mood jump is introduced.

| Area | Actual boundary and retained ownership |
| --- | --- |
| Food | Matching accepted consumption inside the existing care/World/Pet/Memory transaction. Handover may grant the personal bonus after ordinary credit. Autonomous live or reconstructed finite known-stock intake grants the impression without personal credit/contact. Wrong food, placement, unused offers and rejected intake cannot fulfill. Food fulfillment remains a one-level refresh. |
| Affection | Actually accepted petting, after ordinary care credit. Existing refusal/acceptance policy remains authoritative. Rejection does not fulfill or override a boundary. Distinct later fulfilled wishes stack the existing security family. |
| Games | Actual started and settled round facts from RPS, Blackjack and Tic-Tac-Toe sequences through the existing router/coordinator. Capture the current wish at start, translate player results once, and resolve immediately at the real qualifying result. Ordinary session care remains once on close. |
| Social | Actual whole-sequence completion through the existing ReactionPlayer. Frozen SocialCompletion carries the admitted category and optional pre-existing wish ID; menu choice, fetching, intro/first bubble and interrupted playback do not qualify. Ordinary talk care remains at admission. |

Round-win wishes allow unsuccessful retries within the original lifetime.
Next-round non-loss resolves on that one round; losing ends it neutrally. Fixed
three-round win/non-loss blocks wait for the whole block, including draws, and
retain only bounded progress across sessions/reloads. Shared play requires two
qualifying rounds in one session; changing session resets its partial progress.
Only rounds whose start captured that wish can count. The existing game
coordinator owns one transient pending attempt; no game replay, saved deck/board,
second score, event bus or clock is added. Canceled/unplayed rounds do not count.
Completed/failed wish identities cannot be rewarded again after close/reload.

Deadline precedence follows the later recorded **5B.6 endpoint convention**:
expire at `elapsed >= expires_at` before applying completion. Thus equality is
too late, superseding the older game proposal's inclusive-deadline sentence.
New round starts can capture only an already-existing wish; a round underway
when it was created, or a wish first created during a social sequence, does not
retrospectively adopt that activity. Old playback metadata cannot fulfill a
newer replacement wish. Original deadlines and neutral failure are preserved.

The nominal personal bonus is 0.25 from the **existing** 0.75/two-hour and
five/day reward pot, with room below friendship 100. The ordinary action's
eligibility interval is unchanged and cannot suppress an otherwise valid wish
bonus. Same-transition food/petting applies ordinary credit first; social care
precedes its later completion. Game round/block wish credit and ordinary
session-close credit are separate real boundaries sharing the same pot.
Budget exhaustion may clip credit to zero without preventing retirement or the
Moodlet; no top-up is queued. Autonomous food has no personal credit. The existing
relationship codec accepts the `wish` reward kind and keeps a bounded list sized
for ordinary events, maximum wish creation cadence and three carried-in wishes.
Outer save v1, full-Pet checkpoints and existing corruption backups are retained.

| Commit | Coherent change and targeted local check |
| --- | --- |
| `e448bfc` | Food fulfillment, common reward allowance and persisted wish-credit kind; 46 selected tests passed in 0.670s |
| `dbee93a` | Accepted affection fulfillment and unchanged refusal boundaries; 21 selected tests passed in 0.072s |
| `347fa07` | Bounded game objectives, actual round evidence and existing sequence/window wiring; 69 selected tests passed in 0.389s |
| `e73de5b` | Typed admitted social completion metadata and full-sequence fulfillment; 60 selected tests passed in 0.222s |
| `0293976` | Carried-in wish allowance in bounded shared history, daily/100-point clipping and finite-stock offline fulfillment checks |

Final combined **targeted local** verification passed **214 tests in 3.663s**.
The longest individual test was **0.340s**; no selected case exceeded ten seconds.
This covers all four wish areas, lifecycle/disclosure, catalogue/persistence,
consumption and rollback, ordinary friendship/care, actual game sequence phases,
social playback and API preparation fixtures, finite-stock sleep resources,
Moodlet response and architecture guards. Only the three relevant codec/history
cases were selected from the broader neglect module; its unrelated month-long
simulation was not repeated for this slice. Ruff passed across changed Python
files; strict scoped Mypy passed all **18** changed production modules; Pyright
passed those modules and all **10** affected/new test modules.

Focused ownership review confirms one Pet aggregate, unchanged time/resource
owners, one Moodlet progression path, one friendship budget/history and the
existing reaction player. Game attempt and social completion metadata are
transient activity evidence; only the agreed bounded wish progress is saved.
The GUI composition root stays within its existing architecture limit. All
checks used explicit timestamps, injected callbacks and temporary stores: no
visible test window, mouse control, network/API fetch or GitHub CI run. All
implementation units were committed/pushed with `[skip ci]`; no merge or full
suite was run. Physical Windows acceptance is not claimed by these checks.

5B.7 is complete. Next is **5B.8: emotional interpretation and immutable reads**,
followed by 5C's combined status/UI implementation. The final complete suite,
slow-test review and broad final OOP review remain part of the full refactor's
closing stage, as requested.
