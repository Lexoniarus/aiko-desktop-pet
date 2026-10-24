# Care, relationship and real-time implementation plan

> **Latest positive lifetime proposal, 2026-10-23:**
> [60/45/45 minutes](#revised-positive-after-effect-proposal-604545-minutes)
> replaces the earlier uniform 45-minute base for positive multi-tier families.
> The [single-tier food timing proposal](#proposed-single-tier-food-moodlet-lifetime-and-renewal)
> and [full-need wish rules](#proposed-full-need-food-and-affection-wishes)
> are recorded separately as proposals, not implemented behavior.
>
> **Latest wish proposal, 2026-10-23:** the
> [ten-minute rotation and additional objectives](#proposal-ten-minute-wish-rotation-and-additional-objectives-2026-10-23)
> below are discussion proposals, not implemented behavior. They propose replacing
> the current four-hour lifetime, twelve-minute vacancy delay and one-per-area cap.
>
> **Current documentation audit, 2026-10-23:** see the
> [open-work register](#documentation-audit-and-open-work-2026-10-23) before
> treating earlier delivery records as complete acceptance. This documentation
> update authorizes no runtime change. Slices 1–8 have delivery evidence;
> concrete negative/poor-care cause recording and two product conflicts remain
> open, and slice 9 is pending. Earlier reward-pot rules below are historical.
>
> **Active implementation plan; stage 4 corrected and locally verified.** Requested on 2026-10-19
> on `feature/social-optimization`, reviewed against clean baseline `42de63a`.
> The owner accepted the latest discussed balance as a sufficient starting
> point for implementation planning. This document plans that first delivery.
> Stages 1–3, B1 and B2 are implemented and verified below.
> Stage 4 follows the corrected ownership and verification scope below.
> Stage 5's needs/progression/status foundation and menu/action/placement
> decoupling are delivered below. Moodlet/wish/emotion integration is delivered
> through 5B.8 and the 5C VN status/menu implementation is delivered. Stage 6's
> full local suite and OOP review pass for baseline `b72ed21`. The owner requested
> the completed UI refinements and the later practical wish/disruption corrections
> in the final candidate. Their final integrated gate remains pending; only the
> explicitly recorded baseline has full-suite evidence. Physical desktop acceptance
> is separately recorded.
> The 2026-10-21 need-aware wish and staged-petting amendments are delivered
> below; the UI/menu amendments are delivered in slice 7. The social/API
> amendment is delivered in slice 8. The final integrated tests remain slice 9.
> The latest 2026-10-21 continuous-friendship amendment replaces the earlier
> capped care/wish reward model. Its 30-second
> balance values are approved; their incremental runtime delivery is recorded below.
> The later corrections are delivered incrementally below. Slices 1–8 supply
> definitions/storage, need-aware eligibility, weighted selection, lifecycle and
> game/food completion with concrete Moodlet causes, and staged petting
> boundaries, the carried-item absence correction and continuous friendship/status
> cadence, menu admission, wish controls and status details, plus playful API
> presentation and persisted ten-content repetition protection. The final
> integrated suite, slow-test audit and OOP review remain slice 9.
> Existing game goals retain their original meaning and progress, as approved
> by the owner.
> The owner subsequently expanded stage 5 to separate needs, Moodlets, numeric
> mood, emotional state, wishes and expression before changing dialogue wording.
> The first-version Moodlet/wish product rules are settled below. Stage 5B.1
> supplies typed definitions and JSON catalogues; 5B.2 adds aggregate-owned
> state and storage. 5B.3 delivers Moodlet lifetime/relief and numeric mood
> composition. 5B.4 now connects negative interaction experiences and targeted
> helpful-action relief. 5B.5 delivers prolonged-poor-care after-effects and
> accounted exposure. 5B.6 now delivers paced inner wishes, real-time expiry and
> actual spoken disclosure. 5B.7 delivers fulfillment, positive Moodlets and the
> then-current shared-pot personal bonus for food, affection, games and social
> activities; that bonus is superseded by the delivered continuous-friendship amendment.
> 5B.8 delivers full emotional interpretation, typed dialogue schema 3 and
> immutable emotional/wish read contracts. 5C now delivers the VN status/menu,
> embedded selectors and settings/Credits; native visual acceptance remains separate.

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

Historical basis: the 2026-10-21 practical review supersedes immediate refusal
as the intended first response to sufficient affection. The agreed intermediate
stages and repetition counts are recorded in the amendment below; runtime is unchanged.

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

The witnessed-relocation trigger below is superseded by the owner-approved
practical correction at the end of this plan. Only confirmed learned-place
absence admitted to search now qualifies this Moodlet; witnessed transport alone
does not. Existing withholding remains a separate interaction.

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

Historical: the 2026-10-21 game-objective amendment below supersedes single-
session/streak assumptions for total goals and makes explicit next-round wins
non-retryable. Do not infer a cumulative-win target from the old majority block.

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

Historical: consult the 2026-10-21 amendment for explicit next-round failure,
cross-session total-play progress, disappointment after a failed non-loss wish
and precise lasting cause records. Silent retirement alone is no longer the
intended response to a witnessed defeat that violates a non-loss wish.

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

Implementation conventions for 5B.8: compare complete direction intensity sums
within the winning polarity. Equal direction sums prefer the most recently
triggered cause, then the strongest individual impression, then the stable
EmotionalDirection declaration order. No active impression is discarded by a
numeric contribution cap. Attribution describes the last qualifying cause's
known origin (user, autonomous or unknown); old episodes without that optional
fact remain unknown. Neither reading nor migration fabricates attribution.

Status: implemented in 5B.8; see the implementation record below. Derive one overall
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

The creation-spacing rows below are historical. The owner-approved practical
correction at the end of this plan replaces them with normal three-wish stock
and a twelve-minute refill pause; independent expression rules remain valid.
The 2026-10-21 amendment also supersedes the unrestricted need-independent
selection described below, including food/affection wishes despite full needs.

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

The later 2026-10-21 food-avoidance wish amendment introduces an explicit
handover-based exception for that new objective, including subsequent refusal.
It does not silently migrate every existing positive food wish to that boundary.

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


### 5B.8 implementation record: interpretation and dialogue contracts

The first unit derives an immutable `EmotionalComposition` from every active
Moodlet's intensity, preserving all causes, directions and known attribution.
It has no clock, stored emotional score or interaction lock. No-Moodlet numeric
thresholds live in the existing balance catalogue. Legacy cause attribution
remains unknown; newly observed interaction/fulfillment facts supply their origin.

The second unit replaces the mixed mind/dialogue vocabulary coherently:
`PetMind.emotional_state()` derives the overall composition;
`reaction_tone()` exposes only short-lived reactions;
`DialogueContext` carries `mood_value`, `emotions`, `need_conditions`,
`situational_conditions`, sleep, presence and relationship facts separately.
`record_accepted_care()` records accepted timing and delegates the existing short
care reaction; a sleep command never removes lasting Moodlets.

Dialogue catalogue schema 3 uses explicit `conditions`: alternatives are OR,
fields within a clause are AND. Typed fields distinguish emotional states,
secondary emotional directions, need conditions, reaction tones and situational
conditions. All 1,082 identities and authored text/emote beats are unchanged.
The canonical status-label consumer is migrated with the schema; the new VN
layout remains 5C. Existing interaction admission/locks are unchanged.

Validation is targeted and headless. Focused strict Mypy uses silent dependency
following because unrestricted dependency checking reports the pre-existing
`world/state.py:291` local-variable narrowing error (also present at `871d050`).
That unrelated World code is unchanged. Pyright checks the migrated production
and test contracts normally. No windows, pointer control or CI are used.


The third 5B.8 unit extends `application/read_snapshot.py` with frozen
`MoodletRead`, `WishRead` and bounded `GameWishRead` values. Both hover and status
contracts share an `EmotionalSnapshot`: complete composition, independent need
conditions, localized Moodlet details and inner/spoken wish details. The status
label is a property of that same snapshot, not a second editable interpretation.
All eighteen families and eleven objective forms use the existing catalogues.

Snapshots measure remaining time only against the aggregate's `lived_seconds`.
Moodlets report current-stage/total decay work, pause state and any remaining
stable-recovery wait; paused work is not a promised expiry timestamp. Wishes
report their original remaining deadline, concrete target, expression flag,
bounded round counters and the existing `wish_restriction()` result.
`DesktopPresentation` now injects `AttentionCoordinator.wish_context()` to reuse
current care/API acceptance and prepared-category reads. It no longer needs a
Mind reference or reads a clock. Reading never expires/creates/expresses a wish,
commits care, reserves content, changes friendship or advances an impression.
The main-menu layout, new icon strips and wish panels remain the separate 5C.


### 5B.8 completion and focused OOP review, 2026-10-20

Delivered on `feature/social-optimization` in three coherent feature units:
`d6a6046` (pure composition and known source retention), `eafb567` (atomic
catalogue/Mind/caller vocabulary migration) and `8a05227` (passive application
and presentation reads). The final audit tightens the parser rejection fixture
to start from a valid line, removes an unused specificity argument and updates
maintained documentation. The UI architecture guard now inspects Python
attribute access instead of rejecting `.label` in legitimate resource-key strings.

OOP review: `PetState`/`PetValues` remain the sole mutable/persisted Pet owner;
`emotions.py` is pure interpretation, reused by Mind and snapshots. No second
emotional score, store, time axis, scheduler, wish manager or interaction lock
was added. Read projections hold frozen values, not live aggregate handles.
Current wish availability is supplied by the existing attention read port;
World truth/knowledge, content preparation and playback keep their own owners.
The composition root remains within its existing 640-line limit (638 lines).

5B.8 is complete. The next UI work is **5C**, using the prepared VN plan and
references. The full suite and final overall OOP review remain **stage 6**,
after the complete refactor. Native visual/input acceptance stays manual and
separate; this delivery launches no windows, uses no pointer control, and
starts no GitHub CI. All commits use `[skip ci]`.


Final local verification for 5B.8: **253 targeted headless tests passed in
6.437 seconds**. Slowest individual case was the existing 72-hour adaptive
scenario at **2.338 seconds**; no selected case exceeded ten seconds.
Ruff passed all changed Python files since `871d050`; Pyright reported zero
errors/warnings for those files; strict Mypy passed all 23 changed production
files with `--follow-imports=silent` (the known unchanged World dependency
limitation is recorded above). A direct baseline comparison confirms all
1,082 authored dialogue identities/beats are unchanged. Legacy production/test
call searches and `git diff --check` are clean. No full-suite, native-window,
pointer-control or GitHub-CI run was performed.


### 5C implementation sequence, 2026-10-20

Owner-authorized implementation starts from clean `3071033`. The approved local
bundle is available at `../design-previews/vn-ui-2026-10-20/`; main-menu,
settings/Credits and control references were read together with the canonical
VN guide. Original source artwork stays untouched. No new preview is required.

Deliver small coherent commits: (1) deterministic runtime exports/root-local
image ownership and shared control primitives; (2) passive Moodlet/wish and
status presentation; (3) embedded selectors, preserving admission/placement;
(4) matching settings and central Credits; (5) emotional expression audit,
focused integration checks and documentation. Preserve existing game flow,
Blackjack cards, preference/content owners and all authored dialogue beats.

Tests are targeted, local and headless, including fake-widget integration where
needed. No Tk interpreter/window, browser preview, mouse control or GitHub CI
is launched. Inspect selected test durations; the full suite remains stage 6.
Native DPI/font/geometry/input acceptance remains a separate manual checklist.


### 5C delivery and scoped review, 2026-10-20

Implemented the approved main-menu and settings/Credits scope against the local
reference bundle and recorded source pack. No additional preview or asset
regeneration was needed. The existing gameplay layouts, rules, sequence owners,
Blackjack card originals and live World/placement path were preserved.

| Commit | Delivered unit |
| --- | --- |
| `9820d15` | Deterministic exports for 46 icons and eight selected control masters; source hashes, common sizes, cap-preserving controls and root-local image ownership |
| `269a141` | Combined VN status window: emotional summary and numeric mood, full Moodlet strip, inner wishes, care columns, passive details and shared controls |
| `fd6a19f` | Embedded Snack/Spielen/Unterhalten frames in the existing right column; rechecked placement/care admission and retained deferred game owner |
| `8f6c434` | Four-page nonmodal settings, immediate native checkboxes and projected size segments; central detached provider/original-source/API-entry Credits |
| `bf31e05` | Shared emotional expression for dialogue/click/idle; reachable ordinary positives and removal of hardware-only sleepy conclusions |
| `3f0568f` | Keyboard overflow reveal, compact spoken/inner wish metadata, matched care/action rows, redraw suppression, targeted tests and migrated native-view test contracts |

The toolbar keeps its one existing native window, position/pin/visibility owner
and topmost semantics. Summary, Moodlets, wishes and readouts remain in the same
window while selectors replace only the interaction column. Friendship has no
invented direct action. Moodlet descriptions expose cause, current intensity,
individual contribution, known origin, stage/total decay work and paused recovery.
Wishes expose concrete target/art, win/non-loss badges, bounded round progress,
original remaining time, disclosure state and temporary restriction. The UI does
not infer fulfilled wishes, stock, emotional events or expiry from its display.

`PetReadSnapshot` additionally carries the existing pure numeric target, actual
sleep reason, relationship stage and known contact age. Reads do not advance
clocks or apply effects. UI caches hold only render state and frozen projections;
PetState remains the sole pet aggregate. Current credits come from the existing
accepted-content snapshot with no second source history, requests or save fields.

The common skin selects installed Segoe UI with a system fallback, and does not
bundle fonts. Runtime stays standard-library-only; Pillow is confined to the
reproducible development export/tests. Original UI masters are unchanged. The
root-local image cache and per-widget destruction release assets on the owner
thread. Local scroll tags, focus reveal and passive in-window descriptions add
no global input hook, native tooltip window, animation timer or domain clock.
Disabled/hover/pressed/active visuals and keyboard focus remain distinct. Numeric
fills use one continuously varying value color; friendship stays blue. Care and
action rows share height; wished-for targets reuse the existing food/card assets.

The expression audit enables ordinary positive story/idle behavior at numeric
mood 70, provided the shared composition supports it. Deliberate extended playful
clicking retains its higher 82 threshold and existing escalation/boundaries.
Negative or ambivalent composition cannot be mislabeled as cheerful because the
bar is high. Click withdrawal uses the shared subdued/downcast interpretation;
physical exhaustion remains an energy fact, not a hardware-only feeling. Four
unused mixed/old threshold keys were removed with their consumers. A full JSON comparison confirms that all 1,082
authored dialogue sequences are unchanged; no editorial workbook update was needed. Moderate mood/lower friendship creates no invented offense.

Three obsolete mock-only checks were consolidated into stronger window-free
status/embedded-selector coverage. Remaining affected native fixtures were
migrated to frame ownership, new readout contracts, segmented size controls and
root-local images, but were **not executed**. These migrations do not turn
headless checks into native visual acceptance.

Final verification: **230 targeted headless tests passed in 1.781 seconds**;
slowest individual test **0.293 seconds**, none over ten seconds. Tests cover
asset/source hashes, rounded/color semantics, full-family passivity, original
wish reads, real command/selector ownership through widget doubles, stale
admission and pending game cancellation, settings/Credits, emotional expression,
existing contact/placement policies, persistence and architectural boundaries.
Ruff and Pyright pass every changed Python file since `3071033`; strict Mypy
passes all **29 changed production files** with `--follow-imports=silent`.
The previously recorded unchanged World dependency diagnostic remains outside
that scoped Mypy claim. The composition root remains **638 lines**; checked
World/game rules and authored dialogue are unchanged. `git diff --check` passes.

No test window, native Tk interpreter, browser, mouse control, CI workflow or
full-suite run was launched. All commits use `[skip ci]` and are pushed to the
social-optimization branch. The actual-size Windows/DPI/font/geometry/input and
shutdown acceptance checklist is in `UI_WINDOW_CONTRACT.md`; it remains manual.
The broad final OOP review and complete suite remain the next **stage 6**, not
part of this targeted implementation delivery. 5C implementation is complete
within this explicitly headless verification scope.

## Stage-6 integrated review, 2026-10-20

The owner authorized the full local suite, individual timing review and final
OOP audit, with small correction commits and pushes. This record applies to
the frozen implementation baseline `b72ed21`, including corrections below.
The owner subsequently requested the completed parallel UI refinements in the
final candidate. Their inclusion requires an integrated final check, rather
than inheriting the baseline's validation result.

### Ownership and dependency review

| Responsibility | Reviewed owners and conclusion |
| --- | --- |
| Mutable pet state | `pet/state.py` alone replaces `PetValues`. Needs, relationship history, sleep, Moodlets and wishes remain immutable aggregate-owned values; widgets/coordinators do not write `_values`. |
| Numeric progression | `pet/progression.py` integrates the existing need, food, mood, relationship and emotional rules chronologically. `NeedLevels` contains exactly five needs. Numeric mood, relationship, emotional composition and immediate reaction tone remain separate. |
| Time and offline resources | `ActiveSessionClock` measures and consumes intervals; `SessionTimeProgression` coordinates the existing Pet/World/memory owners with rollback. `PetSessionRestorer` reconstructs only unobserved time. Live search, movement, pickup, inspection and consumption retain their existing owners. There is no animation/gameplay replay or second resource inventory while closed. |
| Moodlets and recovery | `interaction_rules.py` qualifies semantic experiences; `moodlets.py` handles stages, stacking and relief. `poor_care.py` reads the existing bounded care history and accounts handled exposure. Persistent friendship penalties remain separate from lasting emotional modifiers. |
| Wishes and completion | `wishes.py` owns pure creation, deadlines, expression eligibility and bounded objective progress. Application attention, care, game and playback owners provide actual evidence. PetState commits retirement, fulfillment Moodlets and personal reward through the existing capped reward ledger. Reads/queueing do not grant rewards. |
| Emotional interpretation | `emotions.py` derives the overall feeling from all active impressions without another mutable emotional store. Numeric caps do not hide emotional influences. Physical hints and short reaction tone do not substitute for overall emotion. |
| Persistence | Existing version-one storage uses focused codecs for immutable values and the paired World/memory save. No second save format, clock or preference store was introduced. Legacy/malformed sections, checkpoints and repeated loads retain separate coverage. |
| Presentation | `application/read_snapshot.py` copies immutable semantic data; `ui/view_models/` localizes it. Toolbar, Moodlet strip, wishes and embedded selectors present snapshots/capabilities, without advancing pet time or fulfilling desires. UI keyboard-engagement timing is presentation-only. |
| Dependencies and composition | The complete resolved import graph is acyclic. Pet rules share only immutable `games/contracts.py` IDs/outcome types, not game implementations or scores. The root remains 638 lines. Existing Mind, World, application and UI boundaries require no additional aggregate, manager or event bus. |

The architecture gate previously rejected any parent-relative Pet import,
including the intended canonical immutable game contracts. It now checks
resolved dependencies and explicitly rejects all game implementation imports
from Pet. Existing forbidden UI/application/World/OS boundaries remain intact;
there is no parallel list of game IDs to satisfy an import-spelling rule.

### Corrections and focused verification

- `a5f6892`: annotate World's broad motion-update state and distinguish scalar
  icon size from surface dimensions in the development exporter. This resolves
  all repository-wide strict Mypy diagnostics, including the previously scoped-out
  World diagnostic, without changing motion or exported pixels.
- `8b61ce8`: remove the old image-header pixel width from GamePanel's now textual
  header. Tk interpreted 360 as characters, making native game windows several
  thousand pixels wide. The existing right-edge Blackjack placement regression
  verifies the correction. Migrate stale VN label/details expectations, retaining
  distinct emotional state and physical sleep-hint assertions.
- `85c96e2`: use the existing controlled Tk clock for click/RPS/Tic-Tac-Toe effect
  assertions. Keep actual widgets, application completion and temporary saves;
  do not replace domain effects with mock results. Initialize calendar state
  before exact click checkpoints and assert the intentional boundary receipt.
  Accepted-petting fixtures start below refusal tolerance. The mood-recovery
  fixture supplies enough energy/fun for its target to rise. Learned-object
  orientation is requested after its fixture history is installed; unknown
  targets remain outside the near field but inside the radial eye-level sight
  range, with background stock placed within desktop bounds. Withholding uses
  an actually recognized wanted portion. No production perception, refusal,
  friendship or mood rule was weakened to satisfy these old assumptions.
- `b72ed21`: enforce the resolved shared-contract boundary and document it.

The first full run found 21 assertion failures and three errors among 1,607
tests. The above corrections passed all **176 affected tests in 27.774 seconds**
on local Linux/Python 3.11/Xvfb; no individual case exceeded one second. Existing
domain cases remained responsible for daily arithmetic, while native cases
retained distinct widget, scheduling, custody and persistence responsibilities.
No new test framework, duplicated scenario matrix or production module was added.

### Intermediate local validation before concurrent UI completion

The frozen candidate passes **1,607 discovered tests in 95.133 seconds**:
**1,599 successful, eight Windows-only skips, zero failures/errors**. The skipped
cases are seven Windows installer/environment checks and one native layered-window
hit-test. They were not run on the working desktop, where setup can create native
probes. Shared fixture/runner overhead is **3.271 seconds**, outside per-test
setup/body/cleanup timings. The longest individual cases are:

| Test ID (`module.Class.method`) | Seconds | Review |
| --- | --- | --- |
| `test_offline_progress.OfflineProgressTests.test_long_absence_is_complete_and_backward_clock_does_not_decay` | 6.891 | Thirty-day production restoration and backward-clock case, with real isolated storage; no wall-clock waiting. |
| `test_friendship_neglect.FriendshipNeglectTests.test_long_gaps_keep_bounded_history_and_reference_consistency` | 6.091 | Thirty-day bounded relationship history and codec round-trip; distinct from the restoration use case. |
| `test_daily_need_schedules.DailyNeedScheduleTests.test_settled_eight_and_four_phase_days_match_discussion` | 5.760 | Both approved eight-day settling schedules through real care/need rules; preserve their numerical baseline. |

**No individual test exceeds ten seconds**, in either complete run. The three
historically slow stage-4 native runtime cases now use the existing controlled
clock: satiated investigation/put-down **0.587s**, restored recall/eating **0.538s**,
and held-inspection sleep/restart **0.822s**. They still execute actual native
widget callbacks and custody transitions without human clicks or real reading/
animation waits. No further splitting, deletion or mock substitution was needed.

Repository-wide pinned **Ruff 0.13.2**, **strict Mypy 1.18.2** (250 source files,
`--no-incremental`, without silenced imports) and **Pyright 1.1.414** pass on the
same frozen candidate. Static checks run locally on Windows/Python 3.11.9; the
full suite runs locally on Linux/Python 3.11.2 with real Tk and Xvfb. Existing
Tcl theme-change teardown diagnostics still appear on stderr without Python
test/callback failures; these are not visual acceptance evidence.

The container uses its own extracted checkout and filesystem, `--network none`,
an unexposed Xvfb display and temporary saves. It has no host display, mouse
injection or user-save mount. A temporary standard unittest result collector
measures setup/body/cleanup per test with `perf_counter`, records shared fixture
and runner overhead separately, and aborts with a traceback after a 90-second
individual stall. The complete run also has a bounded timeout. Timing artifacts
stay in ignored local data; there is no permanent additional runner/framework.

Windows DPI/font appearance, actual desktop input, suspend/resume and visual
animation acceptance remain the separate manual checklist in
`UI_WINDOW_CONTRACT.md`. Offscreen native-widget success does not establish
physical Windows acceptance. No GitHub CI, visible desktop window, browser,
mouse control, merge or live user-save test was used.

This establishes the reviewed baseline. Completed parallel UI refinements and
the additional native button-input regression are to join the final source
candidate and integrated validation record.

## Practical acceptance corrections: inner wish stock, 2026-10-20

The owner explicitly approved **three inner wishes as the normal stock**, with
a **10–15-minute refill pause**. The implemented fixed value is twelve minutes
(`wishes.refill_delay_seconds = 720`), replacing the old global sixty-minute and
same-area ninety-minute creation locks. `maximum_active = 3` is the normal target
as well as the cap; one wish per area, current plausible candidates, original
four-hour deadlines, separate speech conditions and existing reward caps remain.

`replenish_wishes()` fills free slots at the first awake live endpoint. Retiring
a wish through fulfillment or game-goal failure starts a single aggregate-owned
refill deadline; later retirements do not push it back. When ready, the next
awake live evaluation fills the available areas together. Expiry starts the
same pause from the earliest expired original deadline, not from application
restart. Sleep/closed/standby time advances deadlines but creates no wishes;
return fills only the current stock, never a historical sequence. If current
capability leaves fewer candidates, keep the valid wishes and fill later when
an area becomes eligible. Wanting, filling and speaking still grant no reward.

`WishState.refill_not_before` is an optional field in existing wish storage v1.
Existing records lacking it retain their active IDs, deadlines, progress and
expression evidence; empty/part-filled legacy stock may replenish immediately.
The bounded creation anchors remain evidence, not a second generation clock.
The relationship codec's maximum event count includes three completions per
refill interval plus carried wishes; actual friendship point caps are unchanged.

Verification uses injected elapsed timestamps and isolated save round-trips:
three-slot startup/return, exact refill boundary, multiple vacancies without
delay extension, original-deadline expiry, no offline generation, legacy decoding,
all fulfillment areas, speech separation and capped rewards. Native Tk/Toplevel
construction is prohibited in the local test process. The final full-suite
stage-6 gate remains pending rather than being inherited from the old baseline.

Local verification for this correction: **109 targeted tests passed in 1.233s**;
the slowest case was **0.310s**, none exceeded ten seconds. These include all
wish lifecycle/fulfillment areas, expression, storage and passive reads, the
desktop attention seam, shared friendship policy, resources and public docs.
Ruff passes the configured source/test/tool scope; strict Mypy passes the changed domain/application/
codec owners with silent dependency traversal. The full-suite gate is not claimed.

## Practical acceptance correction: disrupted familiar place, 2026-10-20

The owner clarified that "Vertauschter Platz" describes discovering an unseen
change that requires search, rather than disliking every observed rearrangement.
The sole production trigger remains `ObjectBehaviorCoordinator._notice_absences()`:
the existing perception owner must confirm a missing learned place, and the
existing interaction owner must admit it to its missing-object SearchTask.
Ordinary observation/take/placement updates acquired knowledge without producing
this Moodlet or a relocation friendship penalty. Unknown portions cannot establish
a missing familiar place. Mere lack of visibility, a drag, World coordinates,
stock exhaustion or an acute hunger search do not substitute for that evidence.

Remove the obsolete relocation-origin field, its witnessed-move event collection,
its extra application dispatch and the withholding-specific exclusion hook.
Keep the existing visual tracker, perception, memory continuity, safe custody,
live searches, handovers and wanted-object withholding unchanged. There is no
replacement tracking subsystem. The admitted absence is acknowledged once;
continued search and subsequent finding do not add stacks or instantly erase
the impression. Existing saved episodes and relationship history remain valid
and age normally, without inventing a retroactive refund or clearing memory.

Coverage now lives with the existing headless behavior/perception owners:
observed transport preserves learned identity/place without emotional or
friendship consequences; a fresh confirmed absence creates one level-one Moodlet
and a real SearchTask, with no duplicate on repeated updates. The obsolete raw
observed-move event test is consolidated into those behavioral checks. Existing
domain stacking/capped-attribution and separate withholding regressions remain.

Local verification: **113 targeted tests passed in 0.251s**, longest **0.080s**,
none over ten seconds. Tk/Toplevel construction is explicitly prohibited. The
target includes behavior, awareness, interaction, withholding, placement admission
and German object-reaction contracts. Scoped strict typing and the configured
Ruff/Pyright checks accompany these targeted checks; no GUI, mouse control,
CI workflow or new full-suite run is part of this correction request.

### Combined correction verification

The combined targeted set passes **226 tests in 1.829s**, with a longest case of
**0.307s** and no case over ten seconds. The local runner prohibits Tk/Toplevel
construction. Ruff passes the configured `aiko_pet tests main.py tools` scope;
strict non-incremental Mypy passes all **255** application/tool source files and
Pyright reports zero errors or warnings. Two inherited native ttk button calls
need explicit callable casts for the pinned Mypy stubs; these annotations preserve
the same widget methods, arguments and behavior without another state owner.

Both behavior corrections are committed and pushed on `feature/social-optimization`.
This is targeted regression evidence; the final integrated stage-6 full-suite gate
remains pending after the completed UI changes and these practical corrections.

## Practical behavior planning amendment, 2026-10-21

Status: owner-approved rules to record, **not implementation authorization**.
The current runtime does not yet implement this amendment. No tests are run for
this documentation step. Complete these behavior decisions and their later
authorized corrections before the final integrated stage-6 suite.

### Need-aware wish creation, relevance and replacement

Use the corresponding current need as candidate eligibility for food and
affection, in addition to existing capabilities, boundaries and target selection.
The owner's subsequent clarification exempts games and social wishes from
need-level gating, including creation and the 90-point relevance retirement:

| Wish area | Corresponding need | New candidate eligible at |
| --- | --- | --- |
| Food | Satiety | 70 or below |
| Games, including outcome goals | Fun | Any value; no need-level gate |
| Social conversation/content | Social | Any value; no need-level gate |
| Affection | Affection | 70 or below |

These are relevance gates, not automatic wish triggers or automatic emotional
effects. Existing Mind RNG still chooses among suitable concrete objectives.
Retain at most one wish per area and at most three overall. Three is the normal
target **when enough appropriate areas are eligible**, rather than a mandatory
stock filled with incompatible wishes. Fewer wishes is valid when eligible
areas are unavailable; full food/affection must not force those areas into the
stock. Games/social can remain candidates even when their needs are full.
Low friendship does not itself remove inner wishes;
comfort/trust, temporary availability and speech pacing still gate disclosure.

For food/affection only, at existing live wish evaluation, retain an active wish
below 90 on its corresponding need, subject to its original deadline and
objective rules. If another activity supplies that need to 90 or above, retire the now
inappropriate wish without a fulfillment Moodlet, friendship bonus or penalty.
Distinguish this from actual fulfillment: when the concrete desired activity
qualifies, resolve its existing wish normally, including when that very activity
raises the need to 90 or above. Relevance cleanup must not preempt its earned
completion, and must not erase already earned fulfillment Moodlets.

Retain the shared persisted twelve-minute refill pause. Relevance retirement
joins the existing vacancy/retirement policy; later vacancies do not postpone
an already started pause. When due, choose only currently eligible areas.
Do not randomly exchange still-relevant wishes, renew original four-hour
deadlines, manufacture retrospective offline wishes or substitute another
game goal midway through its progress. Existing objective failure and expiry
remain separate ways to end a wish. The 70/90 separation avoids churn around
one threshold and does not introduce another mutable need or desire score.
Games and social wishes retain their original deadlines, fulfillment/failure
rules and other actual capability constraints regardless of their need values;
do not silently retire them just because fun/social reaches 90 or 100.
The subsequently agreed pin override also protects pinned food/affection wishes
from automatic 90-point relevance retirement; actual care boundaries still apply.

### Separate menu navigation from action admission and incidental speech

Opening the Snacks, Spielen or Unterhalten selector is navigation, not care,
gameplay or social playback. A currently displayed comment, click reply or
character action must not impose its action-admission lock on opening those
selectors. Keep valid menu/window lifecycle constraints, including prevention
of duplicate game sessions, separate from eligibility of concrete selections.
Snack placement retains its existing cursor/World admission and remains
available independently of Aiko's action playback.

Starting a concrete permitted interaction may cancel incidental spontaneous
comments and simple click replies through the existing cancellable reaction
player. Playback being active is not sufficient evidence of an exclusive action.
Deliberate social/story playback, active games, actual care and object custody
retain their own applicable admission/completion/cancellation rules. Do not
globally unlock every playback or bypass World handover/consumption safety.
Opening a selector itself creates no care contact, reward or wish fulfillment.

### Ownership and focused verification for the later implementation

Keep `PetState` as the sole mutable pet aggregate. Put wish relevance and
retirement policy in existing `pet/wishes.py`, with need values from canonical
read contracts and tuning in the existing JSON balance owner. Attention provides
live context; passive UI reads do not mutate wishes. Extend existing immutable
values/codecs only where actual new durable evidence is needed; add no parallel
wish manager, clock or reward ledger.

Refine existing `ContactCoordinator` admission and `HoverUi`/toolbar navigation
seams, using the semantic ownership of actual actions and the existing reaction
player cancellation path. Avoid a second UI busy flag or duplicate playback
state. Keep accepted care, semantic boundaries and persistent petting evidence
in the existing care/interaction owners when its revised rules are settled.

Later targeted checks should cover 70/90 relevance boundaries, valid fewer-than-
three stock, silent retirement versus actual fulfillment, preserved objectives
and refill pacing; independently check selector navigation, interruption of
incidental speech and protection of actual committed actions. Reuse existing
headless contract tests with injected time. No windows, mouse control or CI.

### Friendship investigation remains separate

The reported friendship plateau needs a separate gain/loss balance diagnosis;
no friendship tuning change or save modification is approved by this record.

### Agreed staged petting boundary, 2026-10-21

The owner accepted the following proposal while adding the UI/social points
below. This records product rules, not implementation authorization.

Retain the pre-action affection tolerance of 60 at friendship levels 1–2,
80 at levels 3–5 and 90 at levels 6–10. Below that tolerance, petting is welcome
and grants ordinary accepted care. An otherwise welcome stroke that crosses
the tolerance remains welcome and is not retroactively counted as excess.

| Additional attempt while affection is already sufficient | Response | Consequence |
| --- | --- | --- |
| First | Accept the stroke with friendly "enough" feedback | No Moodlet or direct friendship loss |
| Second | Accept the stroke with firmer "really enough" feedback | No Moodlet or direct friendship loss |
| Third | Refuse this stroke and explicitly ask for no further petting | Clear boundary, still no Moodlet or direct friendship loss |
| Next attempt after the expressed boundary | Refuse; acknowledge disregard | Create crowded Moodlet level one and apply the separate boundary-loss policy |

Only semantic additional attempts count, never welcome care, UI reads or input
blocked before delivery. The warning sequence resets after ten minutes without
another additional attempt; within that window it continues. The actual display
of the clear boundary is authoritative for subsequent disregard, not selection
of a response that has not yet been shown. Persist the required bounded evidence
with existing pet-owned interaction memory so reopening cannot bypass it.

Retain three further boundary violations per Moodlet-level increase, capped at
three. Refusal lasts five/ten/twenty minutes at levels one/two/three, renewed by
the resulting level on each perceived violation rather than accumulating time.
Each disregard after the explicit boundary costs 0.25 friendship, capped at one
point per rolling ten minutes. Quiet-time decay remains one Moodlet level per
twenty minutes without another violation, including closed/standby time.

After the current response ends, the petting control becomes technically
operable again; a semantic refusal must be expressed by Aiko rather than a
permanent disabled button. During actual refusal there is no petting animation,
affection gain, accepted-care credit or wish completion. Expiry of a refusal
reassesses current willingness rather than erasing the emotional impression.
An affection wish also requires willingness below the applicable tolerance;
the general need threshold must not create a desire for already unwelcome care.

### Toolbar movement and compact footer controls

Extend dragging from the name label to the complete top bar, including its
empty background and title contents. Move Settings out of that bar into the
footer, next to Pin/Unpin. Both controls use matching compact, narrower button
dimensions with a centered icon and no adjacent visible pin text. Show pin
state through the existing selected/artwork treatment; retain meaningful
tooltips/accessibility labels for both actions. Keep the existing Details
control and other navigation rather than treating the footer change as removal.

Current code attaches `WindowDrag` only to `ActionToolbar.today`. Reuse its
existing multi-handle support for the title container and child surfaces;
do not install another movement controller or global pointer bindings. Keep
existing position persistence, drag callbacks, speech placement and hover
lifecycle. `set_pinned()` must retain selected-state feedback without restoring
a visible text label. Reuse the existing button/icon styling owner.

### Object details: discovery is distinct from identification

The current `ObjectStatusSnapshot` exposes actual desktop count and remembered
known/assigned/missing counts, filtering out unrecognized sightings. Add clear
read-only reporting for these different stages:

- Not discovered: actual desktop objects Aiko has not yet observed.
- Discovered but unidentified: she has observed a thing but has not identified it.
- Identified/known: acquired identity knowledge, with assignment and missing
  status retaining their separate meanings.

World stock and subjective knowledge are different dimensions, not one set of
interchangeable totals. Do not compute "undiscovered" as desktop minus known:
known can include missing memories and observed unknowns are not identified.
Use existing World/perception/memory evidence in the application read projection;
verify associations before claiming exact current-object counts. Ambiguous
associations must not silently become identified or undiscovered objects.
This diagnostic display must neither reveal hidden identity to Mind nor discover
objects, check remembered places, trigger searches or alter emotional state.
Keep one read model and localized labels, not an extra discovery inventory.

### API entertainment framing and last-ten repetition protection

Make all three API categories playful authored presentations around unchanged
provider content, through the existing `Reaction`/`Cue` sequence:

| Category | Framing direction |
| --- | --- |
| Spruch / Single | For example, "Hey, ich hab neulich folgenden Spruch gehört." |
| Witz / Two Parts | For example, "Hey, ich hab folgenden Witz für dich." followed by setup and punchline with suitable timing |
| Kurioser Fakt | For example, "Das hab ich neulich im Internet gesehen ..." followed by the complete provider fact |

Use restrained varied reactions such as a suitable emote or "hihi" where it fits
the actual content; do not insert the same laugh into every sequence or spoil a
punchline. These are framing examples, not final approved catalogue wording.
Do not fabricate authored replacement jokes/facts, translate/rewrite provider
content, create personal memories from the intro, truncate text to make room,
or duplicate need/reward/wish effects for extra presentation beats. Review the
current five-text-beat limit alongside framing; retain content validation and
bounded playback rather than silently dropping provider words.

`SocialContentCoordinator` already checks namespaced provider identity and a
normalized text fingerprint against offered, buffered and recent entries. Its
recent window is currently only two delivered items per category. Extend the
target to the **last ten admitted contents per API category**, retaining the
cross-category identity/fingerprint comparison and existing reservation rules.
An incrementing local counter would identify fetches, not repeated content, and
is not a substitute for this existing content-identity comparison.

Record history only when playback is actually admitted, not when warming or
merely selecting content. Keep this anti-repeat history distinct from full-
sequence wish fulfillment. Preserve at most three additional duplicate fetch
attempts per refill and stop with the existing recoverable error if uniqueness
cannot be obtained; no unbounded retry loop or repeated-item fallback.
Plan a bounded persistence extension in the existing local save path for recent
provider IDs/fingerprints so restart does not routinely replay the same window;
do not persist warm buffers/full API stories or create another save store.

Later focused checks belong to existing drag/button, object read-projection,
social preparation/coordinator and save contracts. Test these headlessly with
controlled callbacks and fake API responses after implementation is authorized;
no test windows, mouse control, live API requests or CI during planning.

### Game objectives, failed non-loss wishes and precise causes, 2026-10-21

Status: owner-requested planning additions, not implemented. The owner subsequently
accepted the cumulative quantities and defeat-Moodlet values below, then clarified
active-only cause storage and manual wish pinning/dismissal. No post-expiry
experience archive is wanted; do not expand this into a future conversation system.

#### Total progress versus an explicitly next-round goal

Total-play and total-win goals accumulate qualifying progress in the named game
within the original wish window across sessions, game-window closes and saved
restarts. They do not require one uninterrupted session or a consecutive-win
streak. An intervening loss/draw does not reset accumulated wins for a total-win
count. A total-play count includes completed rounds regardless of result.
Only concrete qualifying post-creation rounds count, once each, from Aiko's
perspective; opening menus, abandoned rounds and rounds in another game do not.

Keep the exact objective visible and stored, including its target and progress.
The earlier three-round majority definition is not automatically a cumulative
win-count goal, and the old two-round same-session play rule is superseded for
total-play wishes. The owner agreed the following quantities:

| Cumulative wish | Required progress within the original four-hour lifetime |
| --- | --- |
| Play the named game together in total | Two completed rounds, independent of result, across sessions |
| Win at the named game in total | Three wins from Aiko's perspective, across sessions; intervening losses/draws do not reset wins |

For example, win/loss/win/draw/win fulfills the three-win objective. This is not
two wins out of a fixed three-round block. Use explicit visible wording rather
than the ambiguous "win overall" alone. Qualifying progress survives restarts
without extending the deadline; the game/social need-level exemption remains.

"Win the next round of game X" resolves on that next qualifying completed
round: win fulfills it, loss/draw ends it unsuccessfully. It must not retry
until an eventual win under the same identity. "Do not lose the next round of
game X" fulfills on win/draw and fails on a loss. A cumulative/block non-loss
goal must separately state its scope; do not equate it with a next-round goal.

#### A lost game can violate a concrete wish

If Aiko actually loses the qualifying round that her active non-loss wish
concerned, retire that wish as failed and create an appropriate negative
disappointment/lost-despite-hoping-not-to Moodlet. This is a specific emotional
experience, not merely absence of a positive reward. Preserve the named game,
failed objective, relevant round and actual result as its cause. Do not apply
this failure effect to simple expiry, quitting before a result, a technical
cancellation, an unrelated game's loss or every ordinary loss without that wish.

Fair defeat is not user mistreatment and adds no automatic friendship penalty.
Deliver failure and its Moodlet exactly once through the existing game-event
and Pet aggregate boundary, including across saves. General repeated-loss
emotions and failure effects for other objective forms remain separate.

The owner accepted the working label **"Doch verloren"** and these values:

| Intensity | Qualifying experience | Total numeric mood-target modifier | Quiet decay from this tier |
| --- | --- | --- | --- |
| 1 | A concrete non-loss wish fails through its qualifying defeat | -5 | Expires after 30 minutes |
| 2 | Another such wish fails while the episode is active | -10 | 30 minutes to level one, then 30 more to expiry |
| 3 | Another such wish fails while level two is active | -15 | One tier per 30 minutes; 90 minutes to expiry |

Each newly qualifying failed wish increases the current tier by one, capped at
three, and resets the current tier's remaining time to 30 minutes. At tier
three it refreshes that stage only; do not add an unbounded duration backlog.
One failed wish contributes once, not once per round/callback/reload. Ordinary
later losses without a corresponding new non-loss wish do not refresh or stack
this episode. Decay continues in real elapsed closed-app/standby time.

Its emotional direction is disappointed/downcast, not anger at the user. The
listed modifiers affect the target under existing shared numeric caps; they
are not instant deductions or an extra friendship loss. A later fulfilled win
wish may create a positive impression alongside it, without instantly erasing
the disappointment. Preserve the concrete failed objective, game and result
in every tier's cause display and append subsequent real qualifying causes
when stacking. Passive decay does not invent new experiences.

#### Agreed food-avoidance wish

Status: owner-approved planning rules, not implemented. Aiko may want **not to
eat a particular named food** when satiety is at most 70 and there is an actual
reason for variety, such as repeated consumption of that food. Choose a concrete
food from existing evidence rather than inventing a random dislike. This is
an objective in the existing food area, not another concurrent food slot.
The normal deadline, pinning, shared refill, disclosure and applicable food
relevance rules remain authoritative.

The owner explicitly confirmed that **a targeted acknowledged personal food
handover fulfills this wish**, even if the food is the named unwanted food,
and even if Aiko subsequently refuses to eat it. An alternative food also
qualifies. Mere desktop placement, no feeding at all or a selection/drag that
never reaches a perceived handover does not fulfill it. Preserve the boundary
as an application/World interaction fact, not a widget click or invented intake.

| What happens after the qualifying handover | Wish and care consequence |
| --- | --- |
| Aiko declines the food | The wish stays fulfilled; no nutrition without intake |
| Aiko eats an alternative food | The wish stays fulfilled; commit normal real intake once |
| Aiko eats the named unwanted food | The wish stays fulfilled; independently evaluate actual intake under existing food-monotony rules |

Use the existing ordinary food-wish fulfillment impression and shared personal
wish bonus policy, once per wish. A refusal must not masquerade as ordinary
successful feeding, nutrition or its care credit. Actual later consumption
retains its own ordinary effects and does not replay the wish reward. An active
positive handover-fulfillment impression may coexist with a food-monotony
impression justified by actual eating. No additional negative family or automatic
friendship loss is introduced by handover alone; the separately agreed policy
for repeatedly ignoring a communicated variety request remains unchanged.

The Moodlet cause records the food to avoid, actual food handed over, and that
handover fulfilled the wish. A subsequent real intake is a separate fact with
its own evidence; do not retroactively convert the retired wish into failure.
No additional experience archive or future speech behavior is part of this rule.

#### Preserve precise emotional and wish evidence

The owner explained that wishes and Moodlets are intended future conversation
inputs. Current runtime values do not yet meet that precision requirement:
active wishes store concrete targets/progress but are removed at retirement;
Moodlet episodes store family, tier, times and broad user/autonomous/unknown
attribution without the originating wish/game/food or detailed result.
The current read/UI descriptions therefore cannot reconstruct a precise cause.

Keep structured, language-neutral cause evidence through creation, refresh,
stacking and 3-to-2-to-1 decay. Relevant fields include the originating wish
instance and objective, concrete game/food/social target, qualifying event ID,
event time, actual outcome and acquired actor/source attribution. Display the
specific reason at every active tier, for example "Wish to win at Blackjack
fulfilled", rather than only the generic family or its numeric strength.
Keep family meanings accurate: successful victory/pride is distinct from shared
play enjoyment even if both involve Blackjack.

Stacking must not overwrite all earlier contributing causes with the newest
target. Retain the actual qualifying causes for the active episode, distinguish
refresh/strengthening from passive decay, and never invent another event merely
because a tier changes. UI wording is a projection of these facts, not the
canonical evidence itself. Old saves lacking detailed causes must retain an
explicit unknown/legacy cause rather than fabricated wish or game evidence.

The owner rejected the proposed additional retention/history layer. Store the
relevant wish/objective and actual trigger details **directly with the active
Moodlet** for exactly its active lifetime. Ended wishes need no independent
archive: their necessary cause details remain as a small immutable snapshot in
the resulting Moodlet, not a reference requiring a deleted ActiveWish to exist.
When the Moodlet ends, its conversational cause details end with it. There is
no seven-day retention period, separate ended-wish journal or longer-lived
emotional-memory subsystem in this scope.

For a three-tier episode raised by three qualifying experiences, retain the
three real cause records, rather than only the newest game/wish. This provides
future speech with the Moodlet itself, a concrete trigger, or their combination
as context. Do not pre-generate dialogue variants or store rendered sentences.
The current clarification limits causes to active intensity: decay keeps the
newest one/two causes at level one/two. Renewal at level three retains only the
latest three. Decay never invents another cause or keeps a separate event log.

Extend existing immutable episode values in `pet/moodlets.py` with the small
typed cause data needed for the actual trigger, and extend the existing codec,
checkpoint and read projection together when implementation is authorized.
Keep `PetState` as the only mutable owner. Save/reload preserves active causes,
including across closed/standby time; normal elapsed expiry still removes them.
Existing technical duplicate protection and relationship/care histories retain
their own rules and are not replaced by conversational cause storage.

This cause information does not extend an emotional effect, replay rewards or
change friendship. Future speaking behavior is explicitly a later task.

#### Manual wish pinning and removal

The current card controls (corrected on 2026-10-21) are left-click to pin and
right-click to unpin a pinned wish or dismiss an already unpinned wish,
with a passive pin symbol only for pinned wishes and no pin button. Repeated left-click keeps the wish pinned. The owner explicitly
confirmed that **pinning prevents expiry**:
a pinned wish can remain beyond the normal four-hour deadline until fulfilled
or manually dismissed. Preserve the same identity, concrete target and real
progress rather than creating a replacement wish. An actually failed explicit
next-round objective still resolves as failed; pinning must not turn it into
retry-until-success or undo the agreed failure Moodlet.

Plan a persisted pin flag on the existing ActiveWish value and use the existing
wish panel for pin/dismiss controls. Pinned wishes still occupy their ordinary
slot and area; they are not extra hidden wishes. Manual dismissal ends
the wish without fulfillment reward or an invented disappointment Moodlet and
uses the existing twelve-minute vacancy/refill policy. Never remove or erase
an already active Moodlet just because its source wish is dismissed.

The owner subsequently confirmed that pinning also prevents automatic
food/affection relevance retirement at 90. Preserve the chosen wish until actual
resolution or manual removal, while current care willingness/refusal and real
fulfillment conditions remain authoritative. Pinning cannot force acceptance.
Game/social wishes already have the separately agreed need-level exemption.
No additional permanent wish archive or independent pin store is needed.

Focused later checks should cover cross-session total progress, exact next-round
resolution, one-shot failure Moodlets, preserved cause evidence at all tiers,
multiple real stacking causes, legacy unknown causes and save/retention bounds.
The retention boundary is now active Moodlet lifetime only, not an archive horizon.
Include pin persistence, protected time expiry, explicit dismissal/refill and
source-wish retirement without losing an active Moodlet's cause snapshot.
The game/social exemption also needs full-needs creation/retention checks;
food/affection retain their narrower need and willingness rules. No tests or
runtime changes are authorized by this planning amendment.

### Remaining decisions and implementation readiness, 2026-10-21

This check applies to the latest practical amendments, not historical proposal
sections whose old open questions were settled in later delivery records.
The food-avoidance rules above are now settled. Creation/relevance thresholds,
game/social exemptions, refill timing, cumulative quantities, explicit next-
round resolution, defeat Moodlet tuning, staged petting, basic pin/dismiss
controls and active-only cause lifetime are already recorded.

The owner approved the three remaining proposals; these are now settled
planning rules, not implementation authorization:

1. **Pinning versus need-based retirement.** Pinning protects the chosen wish
   from expiry and automatic 90-point relevance retirement until actual
   resolution or manual removal. Current care willingness/refusal and real
   fulfillment conditions remain unchanged.
2. **Bounded cause selection.** Keep the latest real trigger records up to
   current intensity: one/two/three at level one/two/three. Each new qualifying
   event appends its actual cause and drops the oldest beyond that limit.
   Decay trims to the lower level. There is no fixed slot per historical stage
   or rendered dialogue archive; missing old events must not be fabricated.
3. **Intensity versus trigger count.** Retain the existing weighted strength:
   one fulfilled larger game goal may directly create level two with one real
   cause. Intensity and cause count are distinct. Never fabricate extra causes
   merely to make their count equal the displayed intensity.

### Read-only friendship-balance review, 2026-10-21

Historical runtime diagnosis: the owner subsequently clarified that this capped
model omits the desired ongoing emotional relationship effects. The continuous
friendship amendment below supersedes it as the next implementation contract.

The owner requested diagnosis without implementation, tests or save mutation.
Source inspection and a read-only current save review establish the following:

- There is no level-six-specific ceiling. Points remain 0–100; display level
  is `min(10, 1 + floor(points / 10))`, so level seven starts at 60. The numeric
  UI readout rounds to a whole point and can hide smaller real changes.
- Ordinary rewards and personal wish bonuses share 0.75 points per rolling
  two hours and five per rolling 24 hours. Above 80 in the corresponding
  pre-action need, ordinary rewards are reduced to 25 percent. Autonomous
  eating, sleep and ordinary menu activity cannot manufacture personal credit.
- An otherwise same-type-eligible action sets its two-hour reward anchor even
  when the shared pot is empty. Repetition within its existing interval does
  not renew that anchor. Accepted care still renews contact independently of
  whether any reward is credited. This behavior matches the existing recorded
  policy; changing it would be a separate balancing decision, not a bug fix.
- Passive absence loss starts after four hours without qualified care contact,
  includes sleep/standby and uses the existing progressively scaled rates.
  Neglect can also charge under its recorded conditions. Neither Moodlet
  existence nor fair game defeat independently adds relationship loss.
- The current saved reward window and action anchors explain a short-term
  plateau through an exhausted shared pot plus same-type intervals. A single
  snapshot cannot establish a multi-day equilibrium or reconstruct every
  past interaction and loss. Saved rewards are not a net daily balance.
- Passive losses update points directly rather than creating an itemized loss
  ledger; direct penalties are retained only for their own rolling windows.
  Missing penalty entries therefore do not prove an entire day had no losses.

No rebalance or gameplay telemetry/archive is introduced by this diagnosis.
Keep private per-action save details out of repository documentation. Report
the observed values to the owner with their snapshot/time limitations rather
than claiming a frozen relationship value or inventing historical losses.

Remaining implementation checks are engineering work under existing owners:
precise unknown/discovered/identified read projections; native title/footer
bindings; admitted handover versus intake; bounded progress for a pinned
cumulative goal despite arbitrarily many unsuccessful attempts; save migration
and accurate per-tier causes; API framing and last-ten duplicate protection.
Do not turn these into more hypothetical product scenarios. Technical duplicate
receipts, reward caps and needed care histories remain separate from short-lived
conversational cause data. Future dialogue generation remains out of scope.

No Python, JSON catalogue, save or test is changed by this readiness record.
The three remaining decisions are now settled; implementation still requires
the owner's next authorization. Deliver small coherent commits with targeted
headless local checks and duration
review. The integrated full suite and final OOP acceptance remain the last step;
no desktop test windows, mouse control or GitHub CI.

## Continuous friendship and 30-second status balance, 2026-10-21

Status: owner-approved values to record, **not implementation authorization**.
Replace ordinary instantaneous care/wish friendship credits and their two-hour/
24-hour reward pools with a time-based relationship balance. Wish fulfillment
still creates its defined Moodlet; it must not also replay the old 0.25 wish
bonus or ordinary feed/play/pet/talk reward. Existing explicit boundary-violation
effects remain separate once-only event consequences, not repeated tick charges.
The earlier bonus references, including the food-avoidance paragraph, are
superseded only for friendship accounting. Nutrition, contact, emotional effects
and actual objective-fulfillment boundaries retain their agreed meanings.

### Contributions per 30 seconds of actual elapsed time

Use existing numeric mood as the bounded baseline. Do not add the previously
suggested per-need supply bonus as another source; supply already affects mood.

| Numeric mood | Raw friendship contribution per 30 seconds |
| --- | --- |
| 0–20 | -0.004 |
| Between 20 and 40 | Linear from -0.004 to zero |
| 40–60 | Zero |
| Between 60 and 80 | Linear from zero to +0.002 |
| 80–100 | +0.002 |

The positive baseline requires real accepted personal-care contact within the
preceding four hours. App startup, hover, ordinary input or menu operation do
not renew it. Negative baseline mood remains effective without recent contact.
This is a bounded baseline contribution, not an exhausted relationship budget.

| Active Moodlet tier | Positive raw contribution | Negative raw contribution |
| --- | --- | --- |
| 1 | +0.003 | -0.006 |
| 2 | +0.006 | -0.012 |
| 3 | +0.009 | -0.018 |

Sum all active families at their actual intensity; do not truncate them using
the separate numeric-mood contribution caps. Preserve the defined family
lifetimes, escalation, quiet decay and relief rules. Cause snapshots are evidence,
not a second bonus source. A fair defeat has no instantaneous friendship penalty;
its qualifying active disappointment Moodlet now has this ongoing influence.

### Progressive factors and passive losses

Interpolate linearly between these friendship-point anchors:

| Current friendship points | 0 | 35 | 50 | 70 | 90–100 |
| --- | --- | --- | --- | --- | --- |
| Positive factor | 1 | 1 | 1 | 0.60 | 0.35 |
| Negative factor | 0.05 | 0.15 | 0.35 | 0.75 | 2 |

Multiply positive baseline plus positive Moodlets by the positive factor.
Multiply negative baseline magnitude, negative Moodlet magnitudes and the
passive-loss reference by the negative factor, then subtract that total.
Reevaluate from current friendship rather than freezing a factor for the day.
Keep the numeric relationship scale 0–100; no ordinary reward cooldown or daily
point pot suppresses these ongoing effects.

Retain the previously agreed reference absence schedule: zero for the first
four hours after accepted care, 0.5 points/hour after four through twelve hours,
1/hour after twelve through twenty-four, 1.5/hour after twenty-four through
forty-eight, and 2/hour thereafter. Convert the applicable elapsed portion to
30-second units. Retain neglect qualification/reference rates and actual-sleep
energy exemption; use the stronger of absence and neglect for the passive
reference, not their sum. Negative emotional impressions remain additional.

Update needs, numeric mood and friendship on a shared 30-second status cadence
with immediate actual-action feedback. Keep unrounded internal values. Split
or proportionately account for any expiry, creation, tier or contact threshold
inside an interval, including closed/standby catch-up; do not charge only the
effects visible at its end or replay offline gameplay. Use the existing pet
aggregate/progression/elapsed clock, not another simulator, store or timer owner.
Friendly level-ten petting must not be rejected solely because affection is
full; need saturation and willingness to enjoy trusted contact remain distinct.

### Isolated arithmetic evidence and its limits

The discussion calculation iterated 160 repeated 24-hour model days in
30-second steps, including an eight-hour 23:00–07:00 night. Average-care contact
times were 07:00, 13:00, 19:00 and 23:00; intensive times were 07:00, 09:30,
12:00, 14:30, 17:00, 19:00, 21:00 and 23:00. Numeric mood was deliberately held
at 65 or 75 respectively. Each assumed simple fulfillment supplied an independent
two-hour tier-one positive contribution, without outcome weighting or stacking.
No neglect, negative Moodlets or direct negative actions were assumed.

| Model scenario | Assumed simple fulfillments/day | Settled within-day friendship range |
| --- | --- | --- |
| Four contacts, mood 65 | Four, one per phase | 65.059–66.388 (level seven) |
| Four contacts, mood 65 | Eight, two per phase | 72.371–74.284 (level eight) |
| Eight contacts, mood 75 | Eight, one per phase | 85.198–88.820 (level nine) |
| Eight contacts, mood 75 | Twelve, alternating two/one per phase | 96–100 (level ten) |

The four-fulfillment scenario converged to the same range from starts of 15
and 95. The twelve-fulfillment scenario also reached the same final range from
both starts. At 70 friendship and mood 80, two negative tier-one Moodlets give
+0.0012 baseline minus 0.009 emotional influence: **-0.0078 per 30 seconds**.
This establishes the intended direction despite good numeric mood.

These are scenario arithmetic, not application tests, a simulated wish generator
or practical gameplay acceptance. Reaching 100 clips surplus positive gain at
the numeric bound; it is not another time-budget cap. Actual wishes, failures,
stacking and varying numeric mood can change the results substantially. No
implementation, catalogue, live save, test window, mouse control or CI was used.

### Wish-fulfillment feasibility review

The existing selection policy chooses an area first, then a definition within
that area and then a concrete target; game forms are currently equally weighted.
With the planned exemptions, games and social remain candidate areas at full
fun/social. Ordinary food/affection candidates require needs at most 70 and
applicable willingness, so they cannot be counted as guaranteed extras each visit.
All three slots are shared, with one per area; unavailable or pinned objectives
can occupy a slot and reduce practical turnover.

The twelve-minute refill pause is much shorter than the example two-to-six-hour
daytime visit gaps and does not impose a four/eight/twelve daily limit. It does
matter within a short phase: dismissing/failing a wish does not immediately
provide another easy replacement. Four-hour expiry means an unfinished goal
cannot automatically carry over a six-hour average-care gap unless pinned.
No closed/sleep backlog generates extra success opportunities on return.

An entire matching chat/content sequence is controllably fulfillable, subject
to real availability. An inner wish can be fulfilled without spoken disclosure;
the thirty-minute expression interval is not a fulfillment limit. API failures
can leave a particular social objective temporarily unavailable; offline opt-out
still leaves ordinary chat as a candidate. Menus/introductions are not completion.
Games require the named game and actual qualifying results. Two completed rounds
are planable; next-round wins/non-losses and three accumulated wins are not
guaranteed by an arbitrary short game visit. Playing only RPS cannot fulfill a
Blackjack or Tic-Tac-Toe objective.

For scale only, an exact independent fair-RPS benchmark with a fresh equally
selected game form and three completed rounds has success probabilities 1,
1/3, 2/3, 1/27 and 17/27 for play-two, win-next, avoid-next-loss, total-three-wins
and the existing three-round overall-non-loss block respectively. Its mean is
8/15, about 53 percent. Pairing one such opportunity with one completed social
wish per visit gives about 6.1 successes at four visits or 12.3 at eight visits.
This is not a forecast for Blackjack/Tic-Tac-Toe, random target availability,
fixed/pinned goals carried over multiple phases or actual wish generation.
Failed non-loss wishes can also create a negative Moodlet, while larger goals
can create stronger positive tiers: success count alone does not fix the balance.

Conclusion: four daily fulfillments are plausible, eight are achievable with
wish-aware care, and twelve are feasible for an intensive day but not guaranteed
merely by eight visits. Preserve this distinction in acceptance criteria. Before
claiming practical balance, use actual generated objectives and their timing,
real outcomes, slot occupancy and failure impressions in the later targeted
checks; do not silently assume every visited slot becomes a positive tier-one
impression. This review itself approved no new weighting rule; the subsequent
owner-approved wish mix below now supplies that rule for future implementation.

## Approved wish selection mix, 2026-10-21

Status: approved for documentation, not implementation. Preserve area-first
selection; these weights apply only when selecting a new definition within the
eligible game area. They are not daily quotas or weights for all wish areas.

| Game wish form | Selection weight | Objective |
| --- | --- | --- |
| Play the named game | 60% | Complete two rounds across sessions, with any result |
| Win the next round | 10% | Win the next qualifying round of the named game |
| Avoid losing the next round | 15% | Win or draw the next qualifying round |
| Accumulate wins | 10% | Accumulate three wins across sessions; losses/draws do not reset progress |
| Avoid an overall loss | 5% | Finish the defined three-round block with wins at least equal to losses |

This produces 60% activity, 25% short outcome and 15% larger objectives within
games. Social wishes remain activity/completion objectives under existing
eligibility and online opt-in; no new distribution between social content forms
is approved here. With one game opportunity and one social opportunity, the
illustrative combined mix is 80% activity and 20% outcome objectives. Actual
area availability, occupied slots and pinned wishes can change that mixture.

Keep at most three suitable wishes, one per area, four-hour unpinned lifetimes
and the shared twelve-minute refill pause. Food/affection eligibility remains
need/context dependent; games/social remain exempt from the need-90 rule.
Do not automatically replace difficult wishes with easier ones or manufacture
enough successes to meet a daily target. Preserve stronger fulfillment tiers
for larger objectives.

For comparison only, the earlier independent fair-RPS, fresh-goal, three-round
benchmark gives approximately 77% game-goal success under these weights instead
of 53% under equal selection. One such game opportunity plus one completed
social wish per visit gives approximately 7.1 fulfillments at four visits or
14.1 at eight visits. These figures exclude carryover, slot blocking, target
availability and actual gameplay ability. They are not a generator simulation
or a promise of daily friendship gain. Stronger positive tiers occur less often:
the benchmark's integrated positive impression increases by only about five
percent, despite the larger increase in fulfillment count. Verify actual
weighted generation and friendship effects together during implementation.

## Carried food is not a displaced familiar object, 2026-10-21

The owner observed a known Teriyaki portion being picked up for personal
handover while Aiko may have been making an incidental comment. Before it was
put down elsewhere, Aiko treated its former place as missing and produced the
disruption Moodlet. This is a planning-only correction to the earlier practical
acceptance record, not evidence that the new case has already been fixed.

Source inspection identifies the relevant gap: `WorldRuntime.begin_relocate()`
uses attention-qualified `ObjectAwareness.witness_take()`. An unobserved take
can leave the remembered resting place intact. `ObjectAbsencePerception`
confirms an empty remembered place without a custody exclusion supplied by its
application caller; `ObjectBehaviorCoordinator._notice_absences()` can then
admit the search and emit `ArrangementDisrupted`. No runtime reproduction was
performed, and the particular incidental comment is not established as the
actual cause of this reported occurrence.

Required behavior:

- Picking up, carrying or presenting that portion must not start a new
  missing-place search, absence complaint or disruption Moodlet for it, even
  when the take was not witnessed or incidental speech is active. A previously
  queued absence for the same portion must not become a delayed false reaction
  during or after a successful offer.
- Cancelling back to its original place, accepted handover and actual intake
  must not manufacture relocation evidence. A positive food wish still needs
  the already agreed actual matching intake; holding food near Aiko alone is
  not fulfillment.
- Only actual placement at a different resting location can make this gesture
  eligible for the existing unseen-displacement case. The later covered check
  of the old learned place and admission of a real search remain necessary;
  neither release nor a World position change directly creates the Moodlet.
  Observed transport/placement continues to update knowledge without it.
- Genuine observed withholding of an already wanted object retains its own
  trigger, timing and consequences. Offering food is not itself withholding.

Reuse World custody and the existing gesture lifecycle in application-level
absence/search admission. Physical custody may exclude an invalid reaction; it
must not grant Aiko unseen identity, a new learned location or user blame.
Keep subjective memory/perception in `pet/mind`, custody in `world`, and their
coordination in the existing awareness/behavior/runtime owners. Do not add a
second relocation tracker, global perception shutdown or UI Moodlet filter.

Extend existing headless awareness/behavior tests with explicit sensor times
and simulated custody: an unnoticed take during incidental speech, a carried
offer, cancellation, accepted intake, and subsequent genuine unseen placement
and search. Include a pending absence through handover and the unaffected
withholding path. No native window, mouse, real-time wait or full-suite rerun
is needed for this targeted correction.

## Implementation readiness and small delivery steps, 2026-10-21

The latest approved product rules are sufficient to implement the correction
set after authorization. One concrete migration decision remains: saved active
game goals currently have older meanings. In particular, `win_overall` means
a majority in three rounds, rather than three accumulated wins, and `win_round`
currently permits retries. Do not silently reinterpret their saved progress.

Owner-approved migration: retain each valid active
wish's original objective and progress until resolution/expiry, and use the
new objective rules for newly created wishes. Express objective semantics in
the same typed wish model and codec, not a parallel legacy wish service.
Do not neutrally retire/refill these old goals and discard valid progress.
New friendship policy
must preserve actual points and contact/neglect history without retroactive
refunds or replay of old positive credits; record its transition boundary in
the existing progression/save contract.

| Slice | Existing owners and concrete delivery | Focused local verification |
| --- | --- | --- |
| 1. Definitions and durable data | `pet/wishes.py`, `pet/moodlets.py`, existing catalog loaders/JSON and infrastructure codecs: weights, objective semantics, pin state, avoidance/defeat definitions and bounded causal snapshots. Separate catalogue and storage commits. | Strict catalogue contracts, old/new save round trips, valid progress preservation and atomic checkpoint restore. Keep import dependencies acyclic. |
| 2. Wish eligibility and lifecycle | Existing wish rules and `application/attention.py`: need-aware food/affection, unrestricted game/social needs, weighted game forms, pin/dismiss, expiry/relevance and refill. | Deterministic eligible selection, exact weight boundaries, pinning and explicit elapsed-time expiry/refill; disclosure remains separate from creation. |
| 3. Completion and emotional evidence | Existing game/social/food coordinators and pure wish resolution: cumulative objectives, strict next-round outcomes, disappointment and detailed real causes. Separate game and food commits, including the special acknowledged-handover avoidance goal. | Actual round/receipt fixtures, cross-session progress, failed outcomes, duplicate delivery and intake-versus-handover distinctions; bounded evidence even for long-pinned goals. |
| 4. Petting boundaries | Existing care/interaction rules and Mind feedback: staged warnings/refusal, repeated boundary violations and friendship-dependent willingness, including trusted full-affection level ten. | Accepted care versus warning/refusal, exact repetition counts, quiet reset and one-time direct consequences; technical locks cannot count as attempts. |
| 5. Carried-object absence correction | Existing World custody, awareness, behavior and gesture owners, as specified above. Keep search/withholding responsibilities separate. | Targeted existing awareness/behavior regressions for carried offers, queued absences, actual unseen placement and unchanged withholding. |
| 6. Continuous friendship and status cadence | Existing `pet/friendship.py`, decay/progression and aggregate: approved mood/Moodlet/passive balance and shared elapsed time. Remove replaced ordinary instantaneous rewards/pots only after checking callers. | Fixed-time rate/boundary examples, positive/negative coexistence, contact gating, save transition and live/offline equivalence; no duplicate clock or historical gameplay replay. |
| 7. Admission and status UI | Separate commits for navigation versus action start/incidental-speech interruption; wish pin/dismiss and Moodlet causes/readouts; full titlebar drag, footer icons and discovered/unidentified object projections. Existing application read models and UI owners remain canonical. | Headless admission/callback/read-model checks; navigation alone starts no interaction. No native widget construction or desktop automation. |
| 8. API entertainment | Existing social preparation/coordinator/persistence: playful category-specific framing and ten admitted provider-key/fingerprint entries per category. Separate framing/history commits. | Fake responses and explicit admission receipts, bounded duplicate retries, cancellation and restart persistence; no live API calls or authored fallback jokes/facts. |
| 9. Integrated acceptance | Check generated wish opportunities, outcome strengths and actual friendship progression together; complete final OOP/dependency review and the integrated local suite/static gates. | Full suite at the end, inspect individual tests exceeding ten seconds and consolidate redundant coverage. Native visual/input acceptance remains a separate user check. |

Each authorized implementation slice uses small coherent English commits and
pushes on `feature/social-optimization` with CI skipped. Use existing targeted
headless checks with fake clocks/data and review their durations; do not rerun
the full suite after each small commit. No test windows, mouse control or
GitHub CI. These are extensions of canonical owners, not authorization for
new managers, duplicate stores, conversational archives or a second simulator.
This readiness update changes documentation only; no implementation or tests
have been performed for these amendments.

### Slice 1 delivery: catalogue definitions

The owner authorized definitions and storage only, with small commits and
targeted local checks. `WishGoal`/`WishObjective` now distinguish stable goal
meanings from catalogue IDs. The catalogue declares the new cumulative/next-
round meanings and the approved 60/10/15/10/5 game weights. Existing runtime
selection and game resolution are not switched to those meanings in this slice.
The new food-avoidance definition is present with zero selection weight until
its need-aware lifecycle and acknowledged-handover completion are wired in the
later slices. A zero-weight definition is never selected by the existing path.
The negative `disappointed` family is defined as downcast, -5/-10/-15, with
thirty-minute quiet stages and no direct relationship penalty or relief rule.
It has no gameplay trigger yet. German resource keys are complete and validated.

The catalogue/lifecycle/content target passes **32 tests in 0.116 seconds**,
longest **0.036 seconds**, with Tk/Toplevel construction explicitly blocked.
Scoped pinned Ruff and strict Mypy pass. No desktop windows, full suite or CI.

### Slice 1 delivery: original goals, pins and active cause storage

`ActiveWish` now carries its immutable original `WishGoal` and persisted pin flag.
Missing goal data explicitly migrates to the original delivered meanings:
single-session shared play, retryable win and a three-round majority. Neither
loading nor a catalogue count change rewrites stored original progress, target,
identity or deadline. Existing game completion reads the original required count.
The new generator/completion semantics and pin controls remain for later slices;
current generation still creates the delivered original goal variants.

`GameWishProgress` separates total completed-round count from bounded receipt
storage. The codec accepts large cumulative attempt counts with at most one
hundred recent round identities, without a saved session/score archive. Future
cumulative matching and technical duplicate admission remain the existing game
coordinator/domain owners' responsibility, not the cause history's job.

`MoodletEpisode` now retains immutable `MoodletCause`/`MoodletWishCause` snapshots:
source wish identity and original objective/count/target, actual outcome, concrete
target/object where relevant, event identity, elapsed timestamp and attribution.
Stable wish keys are validated in infrastructure without a circular pet-domain
import. This slice originally retained the latest three distinct real receipts;
the later per-stage correction supersedes that rolling selection. Normal elapsed
decay retains the bounded snapshots until the episode ends. One weighted
level-two success can still have one cause. Old episodes get a single explicitly
unknown/legacy record, not an invented wish, game, food or historical event.
Actual trigger wiring remains pending in the later completion/interaction slices.

The existing version-one codecs store these optional additions in the same
atomic save. `PetValues` checkpoint/restore owns them; `PetReadSnapshot` exposes
the same frozen causes, original objective and pin data passively. There is no
separate mutable store, ended-wish archive, reward replay, clock or UI behavior
change. Corrupt new evidence uses the existing section rejection and original-file
backup behavior. The user's live save was not opened or changed.

Combined targeted verification: **87 tests pass in 0.693 seconds**, longest
**0.220 seconds**, none over ten seconds. Coverage includes old/new save and
temporary-file store round trips, original-goal continuation, pinned progress
data, cause bounds/retention, atomic checkpoints, immutable reads and the existing
dependency/import boundary gates. After centralizing receipt/cause bounds in
their domain owners, the **22 storage tests pass in 0.037 seconds** as well.
Tk/Toplevel construction was explicitly blocked in both processes. Scoped
pinned Ruff, strict Mypy and Pyright pass; no full suite, desktop automation,
live API call or GitHub CI was used. Slice 1 is complete; slice 2 remains pending
the owner's authorization.

### Slice 2 delivery: need-aware eligibility and weighted selection

The owner authorized slice 2 with small commits and targeted local checks only.
`PetState.evaluate_wishes()` passes the aggregate's current immutable `NeedLevels`
to the existing pure wish policy. The balance catalogue owns the inclusive
creation threshold of 70 and live relevance threshold of 90; validation requires
the latter to be larger and at most 100. New food/affection wishes respect their
own need and existing affection willingness/boundaries. Games/social have no
fun/social gate; a temporary game-energy restriction suppresses disclosure,
not the inner desire. API opt-in still gates creation of API wishes.

At live evaluation, supplied unpinned food/affection wishes retire neutrally
through the existing shared twelve-minute refill deadline. Actual matching
intake/accepted petting resolve first through their existing care transaction;
subsequent relevance cleanup cannot remove the earned impression. No new
offline creation or relevance pass is added to reconstruction. Relevant wishes
keep their original target, progress and deadline; unavailable activities do
not cause random replacement. A due refill with no eligible candidate keeps
its original deadline until actual refill, instead of starting a new wait.

Selection remains area-first, then applies 60/10/15/10/5 weights only within
games, then chooses a supported target. Social definitions remain equally
selected. Existing and newly generated game instances still use the delivered
original goal meanings in this intermediate slice: slice 3 switches new goal
snapshots together with their corresponding completion rules. Food avoidance
also stays at zero weight until its acknowledged-handover completion is wired.
Its candidate rule already requires a concrete repetitive-food reason/target.
This prevents unsupported goal semantics from becoming live during the sequence.

The focused lifecycle/catalogue/disclosure target passes **30 tests in 0.188
seconds**, longest **0.035 seconds**, none over ten seconds. Checks cover exact
weight intervals, 70/90 boundaries, fewer appropriate areas, temporary restrictions,
neutral retirement and matching-intake ordering with fake time. Pinned wishes
already bypass relevance cleanup; complete pin/expiry/manual-removal behavior
follows in the next small commit. Scoped Ruff, strict Mypy and Pyright pass.
Tk/Toplevel creation was blocked; no full suite, mouse control, live save or CI.

### Slice 2 delivery: pinning, neutral dismissal and protected lifetime

`ActiveWish.is_active_at()` supplies one eligibility check for completion and
actual disclosure/acknowledgment. Pinning keeps the original deadline unchanged,
but protects the instance from expiry and live 90-point relevance retirement.
The same expiry policy runs through existing live, closed and standby time paths;
there is no special pin clock, replacement instance or additional persistence.
Slots and areas remain occupied normally. Pinning cannot force actual intake or
petting acceptance, and a qualifying next-round non-loss failure still retires
its identity. Its disappointment trigger belongs to the separate slice 3.

`PetState.set_wish_pinned()` and `dismiss_wish()` commit the existing pure
transitions through the sole pet aggregate. Commands neither replenish desires
nor grant care, contact, emotional effects or friendship rewards. Dismissal
leaves all existing Moodlets/causes intact and shares the existing twelve-minute
refill deadline; stale instance callbacks cannot affect another wish. Expired
unpinned wishes cannot be revived. Unpinning before the original deadline
restores ordinary expiry; unpinning after it closes the protected wish now and
starts the current vacancy pause, without retroactively pretending it expired
while protected. Other genuinely expired unpinned wishes retain their earlier
shared deadline.

A pinned wish can first be spoken after its original deadline. The existing
codec now validates that real expression time against current elapsed time for
pinned instances, while retaining the original bounded four-hour deadline and
ordinary checks for unpinned ones. Save/reload preserves actual disclosure
spacing and cannot replay it. Mind renders a stored goal's original round count
rather than replacing it with today's catalogue count. Pin/dismiss UI controls
remain the separately planned slice 7; this delivery provides their domain API.

Combined targeted verification passes **108 tests in 1.029 seconds**, longest
**0.206 seconds**, none over ten seconds. Existing suites cover wish eligibility,
catalogue balance, disclosure callbacks, all fulfillment areas, saved/checkpoint
state, immutable reads, attention integration and acyclic dependency boundaries.
The closed-versus-standby test also covers pins with and without desktop stock.
Tests use explicit time, temporary saves and fake callbacks with Tk/Toplevel
construction blocked. Scoped pinned Ruff, strict Mypy and Pyright pass. No full
suite, test window, mouse control, live save mutation or GitHub CI was used.
Slice 2 is complete. Slice 3 activates the new game-goal snapshots together with
their completion/failure/cause rules and the food-avoidance handover objective;
these are not silently enabled ahead of their matchers in the current runtime.

### Slice 3 delivery: reinforcement retains concrete outcome evidence

The owner authorized game/food fulfillment, failure and precise causes. The first
small commit extends existing Moodlet reinforcement with an optional qualified
cause. A duplicate semantic receipt cannot raise or refresh the episode. Receipts
include the original wish identity so distinct wishes do not overwrite each other
merely because source session labels repeat. Real stacking retains the latest
three actual causes; weighted level two still needs only one real success.

`MoodletGameResult` distinguishes the final actual round from the objective's
outcome and retains completed/won/lost counts from Aiko's perspective, without
keeping boards, decks or round histories. The existing v1 codec validates these
optional snapshots and continues accepting earlier causes without that detail.
The targeted progression/storage checks pass **35 tests in 0.033 seconds**,
longest **0.010 seconds**. Scoped Ruff, strict Mypy and Pyright pass. Native
window construction was blocked; no full suite, mouse control or CI. Gameplay
activation follows in the separate game and food commits below.

### Slice 3 delivery: original-goal game resolution and outcome causes

New game wishes now snapshot the current catalogue goal together with its
working matcher. Two total rounds and three total wins accumulate across
sessions/restarts; losses/draws do not reset cumulative wins. Next-round victory
resolves on the first result. Previously stored retry/session/majority goals
continue to resolve their original meanings. Original deadlines/pins, precise
round admission and pre-existing-wish capture remain unchanged.

Failed next-round/block non-loss wishes create `disappointed` exactly once,
including a lost block whose final round itself was a draw. The cause preserves
both objective outcome and actual final-round outcome/counts. Expiry, abandoned
rounds, missing starts and unrelated results do not create disappointment. No
instant relationship deduction accompanies fair defeat. Reinforcement uses the
existing 30-minute stage, maximum three tiers and bounded three actual causes;
positive victory impressions can coexist with the disappointment.

`WishResolution` carries the qualified cause into `PetState`, which commits
retirement, impression and any already-existing positive wish allowance. Shared
activity fulfillment also retains its real target/objective rather than a
deleted-wish reference. Cumulative progress keeps total counts and at most one
hundred recent receipts; the application still admits actual start/result pairs,
not historical game replays. No game score store or second event dispatcher exists.

Minimal existing presentation contracts now distinguish cumulative versus legacy
goal wording and display wins as wins. `GameWishRead.required_count` replaces the
misleading `required_rounds` name at all repository callers. Full cause/pin UI
presentation remains slice 7. Disappointment reuses the existing negative game
icon; no artwork was generated or replaced and no native fixture was opened.

The focused game/lifecycle/disclosure/read/progression/storage set passes
**86 tests in 0.357 seconds**, longest **0.070 seconds**, including 150 unsuccessful
cumulative attempts, saved progress, legacy continuation, one-shot failure,
stacking/decay and objective/result distinction. Scoped Ruff, strict Mypy and
Pyright pass; no full suite or GitHub CI. The following food commit activates
acknowledged-handover avoidance and adds acquired portion identities to intake
causes through the existing World/Pet transaction.

### Slice 3 delivery: acknowledged food handover and actual intake causes

Food avoidance now participates in selection only with an actual repetitive-food
reason and the existing food need gate. The original unwanted food remains in
the wish snapshot. A personally perceived release near Aiko fulfills the wish
even when the offered food is that unwanted food or she refuses it. The cause
records the actual offered food, portion, handover outcome and original objective.
Ordinary matching food wishes still require actual intake. Actual eating and
food-monotony effects remain independent and can coexist with fulfillment.

The existing cursor release owns the gesture and save. Recognized refusal is
acknowledged at that release; accepted handover is acknowledged by the existing
object interaction episode, after physical custody succeeds or after an unknown
food is identified in Aiko's hands. One transient episode flag prevents repeated
phase callbacks. `ObjectConsumption` validates existing custody and acquired
identity, advances the shared time owner and delegates to `PetState`. No accepted
care, contact, nutrition or consumption is fabricated by a refused handover.
Preview, cancellation, ground placement and unperceived release do not fulfill it.
Autonomous intake cannot fulfill the personal handover objective or earn its bonus.

The existing prepared World/Pet/Memory intake transaction supplies the actual
portion ID to positive intake causes, including offline intake without personal
credit. Its rollback covers wish retirement and causes together with existing
pet and World effects. Duplicate completion after save/reload has no second
reward or impression. Full cause tooltips and pin/dismiss controls remain slice 7;
the existing capped positive reward policy remains until its slice 6 replacement.

The combined targeted wish, progression, persistence, object interaction/intake,
headless gesture, offline/restoration and dependency checks pass **232 tests in
9.505 seconds**. No individual test exceeds ten seconds; the longest is the
existing complete long-absence/backward-clock check at **8.017 seconds**. Native
Tk/Toplevel constructors were blocked, while fake-root callback fixtures retained
their actual production gesture/coordinator paths. Scoped Ruff, strict Mypy and
Pyright pass. No full suite, native test window, mouse control, user-save mutation,
live API request or GitHub CI was used.

Slice 3 is complete. Slices 4–8 retain their separate scopes above, particularly
petting boundaries, carried-item absence, continuous friendship, UI admission and
cause presentation, and API framing/history. The integrated suite and final OOP
gate remain slice 9 after those authorized changes; this targeted pass does not
replace that final gate.

### Slice 4 delivery: bounded petting warning storage

The owner authorized staged petting boundaries. The first small commit adds the
two accepted additional strokes and the level-ten trust exception to the existing
typed Moodlet catalogue. Existing pet-owned interaction memory gains a bounded
additional-attempt count and its last elapsed timestamp. The v1 codec validates
and checkpoints both, without another store or clock. Older saves without these
fields retain an already communicated boundary as a completed warning sequence;
existing refusal deadlines and emotional episodes remain unchanged.

This foundation does not yet activate the new reaction sequence. The targeted
catalogue, interaction, storage and checkpoint checks pass **46 tests in 0.070
seconds**; scoped Ruff, strict Mypy and Pyright pass. Native window constructors
were blocked; no full suite, mouse control or CI was used. Activation and actual
feedback follow in the next commit.

### Slice 4 delivery: staged acceptance, communicated refusal and trust

The existing pure interaction policy now distinguishes genuinely welcome
petting, two tolerated extra strokes, explicit refusal and disregard of a
communicated boundary. Pre-action affection tolerances remain 60/80/90 by
friendship group; crossing a threshold with a welcome stroke is not excess.
The first two extra strokes are accepted care with distinct gentle/firm feedback.
The third refuses without care, Moodlet or penalty. Further attempts still only
repeat that refusal until its text is actually displayed. The existing reaction
player's text receipt (or the presenter's displayed fallback) communicates the
boundary; selecting or cancelling a reaction does not. Only later disregard
creates/reinforces crowded and its separate capped direct penalty.

Additional-attempt evidence advances only on delivered semantic care. After
600 seconds without another such attempt, a new warning sequence starts when
needed; an existing refusal deadline is still binding. Violations renew the
deadline by current tier (300/600/1200 seconds), not by accumulated duration;
three further violations raise a tier, at most three. Direct losses remain
0.25 per violation and at most one point per rolling 600 seconds. Existing
quiet-time Moodlet ageing continues one tier per 1200 seconds, including closed
time; refusal expiry does not erase the impression. Level-ten trust permits
full-affection contact but cannot bypass an unexpired refusal.

`InteractionConsequences` derives refusal from its semantic petting effect;
`CareResult` exposes accepted/refused categories for the existing aggregate,
controller, Mind and presenter. `PetState` commits warning evidence with care
and keeps refusal free of affection gain, accepted-care credit and wish rewards.
The two accepted extra strokes can fulfill a still-active or pinned wish because
they really are accepted contact. `AttentionCoordinator` reads the separate pure
`petting_is_welcome()` policy, so tolerating an extra stroke cannot manufacture a
new affection wish. UI reads/input blocked before care delivery cannot spend a
warning. The existing contact/playback gate re-enables the button when feedback
ends, letting Aiko express ongoing refusal instead of permanently disabling it.

New zero-cooldown catalogue events and localized fallback text distinguish the
three boundary responses. Existing accepted-petting lines that explicitly
refused touch at low friendship, tiredness or irritation now communicate cautious
acceptance; the domain's separate refusal events carry the actual refusal. No
new module, UI layout, mutable aggregate, timer or history service was introduced.
Continuous friendship and the general menu/admission amendment remain separate
slices; existing ordinary accepted-care rewards are unchanged here.

The targeted headless set passes **172 tests in 1.877 seconds**, with no test
over ten seconds (longest **0.568 seconds**). It covers exact stages, original
thresholds, persisted warnings/budgets, cancelled text receipts, rolling loss
limits, timed refusal versus offline decay, level-ten willingness, wish
eligibility/fulfillment, controller/presenter callbacks and acyclic ownership.
Scoped Ruff, strict Mypy and Pyright pass. The accepted-dialogue correction is
also checked through the affected catalogue/feedback tests. No full suite,
test windows, mouse control, user-save mutation, live APIs or GitHub CI.

Slice 4 is complete. Slice 5 remains the carried-object absence correction;
the remaining relationship, UI and API work precedes the final slice 9 gate.

### Slice 5 delivery: custody excludes premature learned-place absence

The owner authorized the carried-item search correction. The existing awareness
owner now excludes learned portions in user/pet custody or unsettled motion from
empty-place checks. It uses already acquired instance references or current
sensory bindings only; no definition/type matching grants hidden identity or a
new remembered position. An optional physical snapshot can supply custody when
the desktop's sensory snapshot hides an off-screen cursor item.

`suspend_absence()` discards only that portion's transient dwell and queued loss.
If its loss was still pending admission and the remembered place is unchanged,
the existing memory owner withdraws just the missing flag. It does not rewrite
identity, coordinates, observation time or admitted search history. After actual
settlement elsewhere a new covered check is required before loss can be queued
again. An admitted missing state remains intact. No save format, tracker or
Moodlet/UI filter is added.

The focused awareness, perception, memory, behavior and reunion checks pass
**100 tests in 0.035 seconds**; scoped Ruff, strict Mypy and Pyright pass. Native
window constructors were blocked. The next small commit connects full custody
and between-frame gesture admission and covers practical callback sequences;
no full suite, test windows, mouse control or CI was used.

### Slice 5 delivery: gesture and full-custody integration

`ObjectBehaviorCoordinator` supplies the existing full World snapshot as custody
evidence independently of sensory candidates. Hiding an off-screen cursor item
cannot therefore turn its old place into a loss. The native gesture's bounded
`existing_taken` callback suspends that portion's pending absence immediately
after successful acquisition and before its first save. Failed/stale takes do
not call it. This covers take/cancel or take/handover between perception frames;
no new gesture history, object tracker or mutable owner is introduced.

The focused callbacks use actual World, awareness, behavior, custody and intake
owners with fake native ports. They verify an unnoticed take during incidental
speech, off-screen carry, between-frame cancellation with no stale missing flag
in the first save, a queued loss followed by face recognition/handover/intake,
and the real later unseen-placement path. Holding/presentation does not fulfill
a positive food wish; matching intake still does. Neither release nor settlement
directly creates disruption: the later covered old-place check and admitted
search do. Existing observed transport, search/reunion, finite intake and wanted-
object withholding regressions remain green. No existing admitted search or
persisted emotional consequence is rolled back by this correction.

The combined targeted set passes **180 tests in 1.196 seconds**, longest
**0.221 seconds**, none over ten seconds. Scoped Ruff, strict Mypy (six production
files) and Pyright pass; dependency/import checks retain acyclic OOP boundaries.
Tk/Toplevel construction was blocked and native gesture positions were injected.
No test windows, mouse control, live API calls, user-save changes, full suite or
GitHub CI was used. Both delivery commits use `[skip ci]` and are pushed on the
existing social-optimization branch.

Slice 5 is complete. Continuous friendship/status cadence remains slice 6;
the UI/admission and API amendments follow separately before the final integrated
suite and OOP review in slice 9.

### Slice 6 delivery: balance values and durable policy boundary

The owner authorized continuous relationship accounting and a shared 30-second
status cadence. The first commit stores the agreed mood bands, uncapped per-tier
Moodlet rates, progressive positive factors and cadence in the existing balance
catalogue. The existing negative-factor anchors remain canonical. The pure
friendship decay owner integrates simultaneous positive/negative flow across
those linear segments, including equilibrium, level crossings and scale bounds;
the reference-only passive projection reuses that same solver.

An optional `continuous_since` field in the existing relationship save/checkpoint
records the new policy's elapsed boundary. Old saves without it remain valid;
no history, contact or points are rewritten by decoding. Actual runtime migration,
reward removal and cadence activation follow in the next delivery.

Four focused rate/flow/migration tests pass, as do forty selected existing
neglect, catalogue and persistence checks. Scoped Ruff, strict Mypy and Pyright
pass. This commit does not activate the new balance or run the full suite; no
test window, mouse control or CI was used.

### Slice 6 delivery: continuous runtime relationship accounting

The existing progression now accounts for mood before/after, all actual Moodlet
tiers and passive absence/neglect in one progressive flow. Positive baseline
requires accepted care within four hours; negative mood and Moodlets do not
require it. Passive loss uses the stronger reference, not an added supply bonus.
Contact/absence boundaries and existing need/neglect subdivisions retain their
actual portions. Moodlet expiry/tier/recovery changes remain owned by the existing
chronology. The common solver handles positive/negative effects simultaneously,
including point-anchor crossings and saturation without an exhausted daily pot.

`record_accepted_contact()` replaces ordinary reward calculation; `CareTransition`
uses `contact_action`, with the unused pre-reward need removed. Wish resolution
commits only the impression. Bare play, refusal and autonomous consumption do
not manufacture contact, and direct boundary penalties still occur separately.
The unused gain/fraction/wish-bonus settings and calculators are removed after
checking production, codecs, tests and tools. Historical reward fields and their
bounded validation/pruning remain solely for existing v1 data compatibility.

New pets start with the continuous boundary at their current elapsed origin.
Older saves finish their already elapsed catch-up using the existing reference
loss rules, then record `continuous_since` once at that endpoint. Reopening or
wall rebasing cannot reapply it, refund points, replay old credits or invent
contact. Full status floats now survive the existing atomic save/checkpoint;
there is no separate migration ledger or background simulation.

The updated core ownership/care/wish/precision tests pass **218 selected checks
in 3.319 seconds**, longest **0.528 seconds**. Another focused time/neglect/food/
sleep-storage set passes 78 checks; its longest is the existing 30-day bounded-
history case at **8.542 seconds**, below the ten-second review threshold.
Obsolete instant-bonus/daily-pot scenarios are removed or rewritten around actual
contact and continuing impressions. The approved four/eight-contact reference
arithmetic now verifies average levels seven/eight and intensive level ten using
event boundaries, not thousands of artificial GUI ticks. It remains arithmetic,
not a promise of generated wishes or practical daily gameplay acceptance.

Scoped Ruff, strict Mypy and Pyright pass. The next delivery connects normal
30-second sampling and visible fractional readouts; full-suite/OOP acceptance
remains slice 9. No test windows, mouse control, live APIs or GitHub CI.

### Slice 6 delivery: shared status cadence and visible precision

Normal lifecycle sampling now uses the existing clock's 30-second minimum.
Subthreshold reads retain both anchors, including wall fallback initialization
when uptime is unavailable. Actual care, game/object commits and persistence
continue to force complete elapsed consumption. There is no secondary accumulator,
timer, movement cadence or new pet state. Input/rhythm observations continue at
their existing cadence; needs, numeric mood and friendship advance together.
Suspend/closed-time reconstruction still uses the same chronological policies
and actual existing finite stock, with no retrospective user interaction.

The current passive readout shows small real changes with up to two decimal
places for needs/mood and three for friendship, localized with a decimal comma.
Whole values stay compact. Full gameplay floats survive save/reopen; the status
view does not round or write state. No native layout, pin controls or general
menu admission work is included in this slice.

The final selected cadence/readout/scheduler, offline/restoration, wish lifecycle,
Moodlet/poor-care and dependency checks pass **99 tests in 12.049 seconds**.
The longest individual case is the existing full long-absence/backward-clock
check at **9.593 seconds**; none exceeds ten seconds. Existing 30-day neglect
coverage was separately timed at 8.542 seconds. Both remain complete arithmetic
checks without real waits or UI; no production cutoff or weakened fixture was
introduced to hide their runtime. Two old VN fixture assumptions (family count
and an avoidance wish without its explicit goal) now use the current catalogue
contracts. Scoped Ruff, strict Mypy and Pyright pass.

A final narrow resource/wish/Moodlet/withholding catalogue check passes another
31 tests in 0.137 seconds, including rejection of the retired wish-bonus setting.

All slice-6 delivery uses targeted local tests with Tk/Toplevel construction
blocked. No full suite, native test window, mouse control, live API, user-save
mutation or GitHub CI was used. Slice 6 is complete; slice 7 retains general
admission/menu behavior, wish controls and remaining status details, followed by
API work and the final integrated suite/OOP gate in slice 9.

### Slice 7 delivery A: navigation and deliberate admission

Selectors open independently of character playback; selecting food, a game or
social content still checks the existing capability at the point of execution.
The game window/pending-session owner still prevents duplicates and rechecks
admission after deferred World release. Opening selectors earns no care/contact.

ReactionPlayer retains incidental provenance with its own sequence lifecycle;
short attention comments and click replies may yield, stories never do.
ContactCoordinator combines this read with foreground, sleep and game ownership.
Care cancellation uses the existing player/action owners; real care, social
completion and object custody are not globally unlocked.

Selected window-free contact, menu/placement, playback and VN checks pass
43 tests in 0.302 seconds (longest 0.059 seconds, none over ten).
Ruff, scoped strict Mypy and Pyright pass. Native Tk/Toplevel constructors
were blocked; no test windows, pointer control, live APIs or CI were used.

### Slice 7 delivery B: individual wish controls and concrete cause readouts

This slice originally provided a selected pin button and right-click dismissal;
that gesture is superseded by the wish-card correction recorded below.
WishPanel projects saved pin state and no-expiry wording
without replacing cards on time/pin refresh. Callbacks cross HoverUi's explicit
ports, DesktopCareRuntime and the existing application router/controller;
PetState remains the sole writer. Actual elapsed time is accounted before the
command and the result is saved/refreshed, without recording care/contact.

Moodlet descriptions localize their stored original wish, target, goal count,
actual offered/consumed food and settled game result. Overall objective result
and last-round result stay separate. Each real cause is shown at every current
tier; a higher initial tier does not fabricate extra causes. Legacy unknown
causes stay explicit, and all data still expires with its existing episode.

Selected command/persistence, emotional readout, catalogue, VN and application
checks pass 30 tests in 0.190 seconds (longest 0.033 seconds, none over ten).
Tests block native constructors and use widget doubles, isolated in-memory
saves and actual router/domain transitions. Scoped Ruff, strict Mypy and Pyright
pass. No native windows, pointer automation, live APIs or CI were used.

### Slice 7 delivery C: toolbar movement, footer and discovery details

The whole title surface and its label share the existing WindowDrag. Pin and
Settings now sit beside each other in the footer, using the same 40-by-40 source
button art, symmetric padding and centered icons. Selected state represents
pinning without restoring visible text. Keyboard-focus/hover descriptions and
the Details control remain available. Position persistence and speech movement
still use the existing callbacks; no new pointer hook or movement owner exists.

ObjectStatusSnapshot adds undiscovered stock, unidentified sightings and
explicit unresolved associations. The projection uses acquired instance
bindings and the current awareness tracker, never desktop-minus-known,
geometry-based identification or catalogue identity. Old unbound sightings
can make unmatched stock uncertain; that stock is reported as unresolved rather
than falsely undiscovered. Learned/missing knowledge remains an independent
dimension and can outnumber current desktop portions. Diagnostics do not poll
perception, discover items, check places, start searches or write memory.

The deferred game callback rechecks actual admission after the World's own
pending marker clears. The existing interrupt owner provides this explicit
after-release ordering; normal care retains its protected ordering and social
waiting retains its existing scheduling. Game opening otherwise keeps its
existing synchronous callback behavior and one pending reservation. Headless
tests cover both the marker ordering and rejection of a no-longer-valid choice.

A focused architecture check caught the composition root's size boundary.
Font selection now belongs to the existing shared AikoSkin, and cursor-motion
delivery binds directly to DesktopAttentionRuntime after checking all callers.
The remaining native test caller follows that canonical owner. The unchanged
640-line guard passes; no exception or second feature owner was added.

Final selected step-7 verification passes **126 tests in 0.995 seconds**.
The longest individual test is the import-cycle check at **0.217 seconds**;
none exceeds ten seconds. Scoped Ruff, strict Mypy (19 source/helper files),
Pyright (all changed Python files), dependency and UI architecture checks pass.
Existing native assertions were migrated for icon-only pinning, available
navigation, interruptible click feedback and the World callback signature;
those native tests were inspected and statically checked, not executed.

All executed UI tests use widget doubles with native Tk/Toplevel construction
blocked. No test window, mouse control, live API, normal save mutation, full
suite or GitHub CI was used. Physical layout/input acceptance is still manual.

Slice 7 is complete. Slice 8 is the separate API entertainment framing and
last-ten repetition protection; slice 9 remains the final integrated suite,
slow-test audit and OOP review after the authorized changes are complete.

### Slice 8 delivery A: playful API presentation

The existing social preparation owner now selects one of three localized,
category-specific introductions. Stable provider-content fingerprints vary the
prepared framing without another dialogue history or mutable playback selector.
Some complete sequences finish with a restrained happy/idea emote; none adds a
laugh before delivery, replaces provider words or manufactures personal memory.

The existing five-text-beat budget remains explicit: one introduction plus
up to four complete provider text segments, at most 125 characters per segment.
A two-part joke retains the setup/delivery boundary and 700 ms pause.
Optional final emotes consume no text slot. Oversized/incomplete content is
still rejected rather than truncated or replaced with authored jokes/facts.

Selected preparation, accepted-care, whole-sequence wish completion, playback
and text-catalogue checks pass 33 tests in 0.218 seconds (longest 0.066 seconds).
Scoped Ruff, strict Mypy and Pyright pass. All executed checks block native
Tk/Toplevel construction; no live API, test window, mouse control or CI.
Persistence and the ten-content history remain the next slice-8 commit.

### Slice 8 delivery B: ten admitted receipts and bounded codec

SocialContentCoordinator now owns one immutable SocialContentHistory value
instead of retaining two full prepared stories per category. Each admission
keeps the ten latest receipts for that category (at most thirty total), storing
only category, namespaced provider identity and normalized text fingerprint.
Offers, buffers and all categories still share identity/fingerprint checks.
Normalized whitespace, case and setup/delivery boundaries cannot disguise the
same text. Provider identity lengths are bounded at preparation as well.

Warming, selecting and cancellation leave admission history unchanged.
Opt-out/re-enable retains receipts while clearing only transient buffers.
An older item becomes eligible after ten later admissions in its category;
duplicates still receive only three additional fetch attempts per fill.
The version-one receipt codec rejects invalid namespaces/digests, duplicates,
unknown fields and excessive per-category or total counts.

Selected receipt codec, coordinator, preparation and cancellation checks pass
31 tests in 0.004 seconds (longest below 0.001 seconds). Scoped Ruff, strict Mypy
and Pyright pass. Native constructors were blocked, and no APIs were called.
The next commit wires this bounded value into the existing session/save path;
this commit does not yet claim restart persistence.

### Slice 8 delivery C: existing atomic save and admission wiring

The optional outer version-one `social_history` section is decoded independently
of pet/world state and passed through the existing loaded/restored session
contracts. DesktopCareRuntime supplies it to the content coordinator before
warming begins. DesktopPersistence reads the current immutable history through
an explicit callback and writes it in the same StateStore atomic save as pet,
settings, adaptive memory and the optional paired World/object-memory snapshot.

API admission defers its ordinary care save until the content coordinator
accepts the actual offered content. The existing social-runtime port then saves
care and its receipt together once. Warming, cancellation, stale callbacks and
rejected starts do not persist a receipt. A later full-sequence completion can
fulfill the real social wish and save that event separately. Opt-out/close retain
admitted receipts while clearing transient stock; no second store or full API
story archive was introduced. Legacy saves start empty. Invalid/future history
leaves valid pet/world data intact and uses the existing backup-before-replace
path, including when a writer encounters the invalid file without a prior load.

Final selected slice-8 checks pass **103 tests in 0.711 seconds**, longest
**0.205 seconds** (import-cycle guard), with no test over ten seconds.
Coverage includes provider-shaped responses, five-bubble content preservation,
framing, cross-category provider/text matching, ten-per-category eviction,
three additional duplicate attempts, cancellation and rejected admission,
legacy/corrupt recovery, restart duplicate protection and an actual isolated
care/playback/save flow. That flow checks one care-plus-receipt write at
admission and the separate actual whole-sequence wish-completion write.

Scoped Ruff, strict Mypy (11 changed source files), Pyright (all changed source
and test files), dependency and the unchanged UI/composition architecture guards
pass. Executed tests block native Tk/Toplevel construction. HTTP data is faked
and local file writes use temporary saves. No test windows, mouse control,
normal user-save mutation, live API requests, GitHub CI or full-suite run.

Slice 8 is complete in separate framing, history-definition/coordinator and
persistence-integration commits. Slice 9 remains the final integrated local
suite, explicit investigation of tests over ten seconds and final OOP review;
there is no claim of that full-suite gate or manual desktop acceptance here.

## Practical corrections before slice 9, 2026-10-21

The owner reported a Windows-unresponsive menu with changing dimensions, a
missing poking Moodlet after final click silence, and no withholding escalation
for an unidentified object already selected for investigation. The menu had no
Python traceback; a specific native crash cause is not established. Slice 9
remains deferred until these corrections/investigations are recorded.

### Poking: final warning before silence

The cheerful click path reaches click_last_word without the earlier boundary
events. That actual warning now belongs to the shared POKING_BOUNDARY_EVENTS
contract used by click policy bookkeeping and delivered-text acknowledgement.
The next continuing poke creates the existing impression even when no further
dialogue is selected. Selecting/cancelling an unshown line still grants no
delivered boundary; stacking and direct penalty limits remain separate.

Selected real contact/player, negative-interaction and playback checks pass
41 headless tests in 0.266 seconds (longest 0.022 seconds). Scoped Ruff, strict
Mypy and Pyright pass. Native constructors were blocked; no windows, pointer
control, CI or full suite. Withholding and the menu investigation follow
separately; this record does not claim them fixed.

### Withholding: committed curiosity is distinct from wanting to consume

Both take admission and continued observed withholding previously required a
positive consumption decision. Unknown objects correctly cannot have that
decision, so withholding a committed investigation target silently ended its
emotional episode. ObjectInteractionCoordinator now checks its existing focus
and subjective memory: an unidentified committed target retains curiosity;
an identified target still uses the ordinary current use decision. Unrelated
unknown items never acquire withholding interest. No identity is inferred from
World, and no new interest manager or second episode/timer was introduced.

The real unknown-memory regression keeps Aiko fully fed and the item USER_HELD:
requests remain gentle at ten seconds, become irritated with a level-one
Moodlet at twenty, and reinforce at fifty/eighty observed seconds. Identity,
consumption and handover remain absent. Returning it releases paused decay.
Known unwanted items and repeated-take accounting retain their existing rules.
Selected interaction, withholding and event checks pass 34 tests in 0.035
seconds, longest 0.015 seconds; none exceeds ten seconds. Native constructors
are blocked. Scoped Ruff, strict Mypy and Pyright pass. No windows, pointer
control, CI, normal-save writes or full suite.

### Menu hang: bounded investigation, native cause remains open

No app, debug launcher, test window or native input was started. The investigation
followed ActionToolbar.refresh/place, WishPanel, ToolbarDetails, PanelSurface,
ScrollRegion and the object-feedback/animation idle-event path. Panel artwork is
placed rather than packed, and retained images are view-owned; no second object
loop or new movement writer was found in these paths.

A window-free probe separated requested content dimensions from allocated canvas
dimensions (the ordinary widget doubles equate them). With content growing from
100 to 160 pixels, fit_content requests height 160 while _sync_scrollbar still
reads allocated height 100 and shows the vertical bar. After allocation reaches
160, the same bar hides. This demonstrates an unnecessary width/geometry
transition, not a self-sustaining loop or the reported Windows hang.

Two additional contributors require focused layout work: WishPanel.refresh
invalidates layout on every snapshot even when rendered text/identity is unchanged;
ActionToolbar.place synchronously calls update_idletasks on every visible refresh.
That call drains all idle work, including World playback-event delivery, inside
presentation refresh. The code evidence makes this an investigation target, but
neither reentrant runaway nor causation by unknown-object discovery has been
reproduced. No speculative runtime layout rewrite is included in these Moodlet
fixes. A future correction must retain actual constrained-viewport scrolling and
initial placement, not hide the symptom by removing overflow protection.

Read-only Windows application-event checks found a Python 3.14 AppHangB1 record
and older Python 3.11 Tcl failures. This checkout's venv uses Python 3.11.9. Those
records do not identify this session/script or establish its hang stack; no WER
report, machine identifier or user save was copied into Git. There is no reliable
Python stack trace for the reported occurrence.

The existing headless VN status, menu admission/decoupling, object feedback,
placement geometry and UI/dependency guards pass 53 tests in 0.638 seconds
(longest 0.222 seconds). Three additional existing behavior checks cover unknown
discovery, return waiting and unpresented-object inspection in 0.004 seconds.
Native constructors were blocked in each run. No test exceeded ten seconds;
native geometry tests were deliberately not run. These checks establish owner
contracts, not Windows/Tk visual acceptance or a repaired native hang.

Both Moodlet defects are corrected in separate pushed commits. The menu hang
remains an explicit open item before slice 9; the full-suite/final review gate
has not started and is not represented by these selected checks.

### Menu correction 1: stable vertical scrollbar geometry

Autohiding vertical ScrollRegion bars now live in a fixed ten-pixel gutter.
The gutter remains packed while only its scrollbar child is hidden. Therefore
neither transient overflow against an old allocation nor genuine overflow can
change the parent's requested width or the canvas width and feed another text
reflow. A hidden bar leaves that narrow gutter empty; horizontal rows retain
ordinary overflow/height behavior. The existing ScrollRegion still owns fit,
actual viewport measurement, scrolling and destruction; no domain/runtime owner
or extra scheduler was introduced. This corrects the demonstrated width change,
not a proven native AppHang cause. A temporary bar decision during allocation
may still occur, but it cannot resize its parent or its viewport.

The new requested-versus-allocated geometry regressions fail against the old
code with 686 != 676 and pass with the gutter. They retain capped-content and
actual parent-clipping scrolling, plus horizontal removal/offset reset. These
are explicit pack-request doubles, not a claimed native geometry simulation.
Selected scrolling, VN status and menu admission checks pass 21 tests in 0.095
seconds (longest 0.070); scoped Ruff, strict Mypy and Pyright pass. No test exceeds
ten seconds. Native constructors are blocked; no windows, native input or CI.
The next small correction examines synchronous idle draining during placement.

### Menu correction 2: recurring placement does not drain World idle events

A second headless regression now demonstrates the ordering defect with the real
DesktopWorldRuntime event queue: a queued pick-up completion is delivered inside
ActionToolbar.refresh because place calls update_idletasks. Before this change
the assertion that delivery remains pending fails. This proves nested idle work,
not the original native AppHang or an infinite loop.

ActionToolbar.place now only reads current geometry and sets changed coordinates.
A guarded Toplevel Configure handler corrects position when Tk allocates a new
size; child Configure events are ignored, equal placements are not reissued,
and the existing drag/visibility guards remain authoritative. No additional timer,
layout controller or World event writer was added. The initial show still settles
geometry once before mapping. Explicit Details expansion still settles once to
reveal the new scroll extent; these user operations no longer indirectly re-enter
idle draining through recurring placement. These bounded explicit operations
retain their previous layout contract and are not claimed completely asynchronous.

The before/after regression keeps the World event pending across normal refresh,
then delivers it once when the fake event loop is explicitly advanced. Further
checks cover initial size settlement, screen clamping after resize, child-event
filtering, no duplicate placement, hidden windows and active dragging. Selected
placement, VN status, object feedback and geometry checks pass 14 tests in 0.082
seconds (longest 0.041). Scoped Ruff, strict Mypy and Pyright pass. Native
constructors are blocked; no windows, native input, live saves, CI or full suite.
The original Windows hang remains unconfirmed until native runtime evidence
exists; slice 9 remains deferred.

### Menu correction 3: invalidate wish layout only for visible changes

WishPanel still refreshes its current immutable items for descriptions and pin
commands on every snapshot. It now requests layout only when card identity or
rendered target/objective/meta text changes. Unchanged snapshots and precise
rest-time updates within the same displayed minute do not enqueue layout work.
Actual minute, pin, restriction/progress text, additions and removals retain
invalidation through the same ScrollRegion. No second UI state model or timer
was added, and retained cards/scroll position remain intact.

The new regression fails before the change with four unnecessary refresh_layout
calls. It verifies no calls for identical/sub-minute display updates while current
item values remain available, and one call each for a changed displayed minute,
pinning and card removal. Empty unchanged rows also remain passive. Selected
placement, wish-control and UI/dependency checks pass 35 tests in 0.455 seconds
(longest 0.213). Scoped Ruff, strict Mypy and Pyright pass. No test exceeds ten
seconds. All executed tests are local and window-free; native constructors are
blocked. No mouse control, CI, normal-save changes or full-suite run occurred.

The isolated evidence now covers a repaired geometry-feedback source and repaired
nested idle delivery during recurring menu refresh, plus redundant wish layout
requests. It still does not identify a native stack for the owner's original
Windows-unresponsive occurrence. Initial show and explicit Details changes retain
a one-time idle settlement; tooltip show also retains its existing settlement.
These paths no longer recurse through recurring place, but native Windows/Tk
acceptance is outstanding. Slice 9 is deliberately not started by this work.

### Wish-card control correction, 2026-10-21

The owner's final gesture is left-click to pin; right-click unpins a pinned wish
or dismisses an already unpinned wish.
There is no separate pin button. A passive 24-pixel pin symbol is drawn only
for a pinned wish; repeated left-click leaves it pinned rather than toggling
it off. Right-click first removes the pin; another right-click dismisses the
unpinned wish. Bind these controls to the whole
card subtree, including passive artwork/padding, content and the pin symbol.
Return break so the gesture does not also toggle the description or propagate
as another action. Hover/focus and Enter/Space keep description access.

WishPanel renders the existing saved pin state and invokes the same application
commands. No additional pin state, expiry timer or persistence path was added.
Manual dismissal remains neutral, preserves existing Moodlets, and retains the
existing twelve-minute refill. Text catalog, current UI contract and planning
rules now describe the corrected gestures; older delivery wording is explicitly
marked superseded.

Selected window-free controls, placement, VN status and German text-catalog checks
pass 18 tests in 0.064 seconds (longest 0.029). The real command/codec regression
checks pin persistence, idempotent repeat pinning, pinned dismissal, neutral
Moodlet/friendship history and harmless stale callbacks. A card-subtree regression
rejects button construction and checks the same gestures on every surface. Passive
marker states are asserted without native drawing. Ruff, scoped strict Mypy and
Pyright pass. No test exceeds ten seconds; no test windows, native input, CI or
full suite. Slice 9 and the original native-hang acceptance remain outstanding.

Final gesture clarification: left-click pins; right-click first unpins a pinned
wish. Another right-click removes the now unpinned wish from the active wishes. Passive pin
artwork remains unchanged. The callback regression and all current control
wording use that final assignment. Eight selected command/persistence and German
catalog tests pass in 0.057 seconds (longest 0.036); scoped Ruff, strict Mypy and
Pyright pass. No native windows, input automation, CI or full-suite run.

Two-stage right-click correction: WishPanel._unpin_or_dismiss routes a pinned
wish only to the existing unpin command; a right-click on an already unpinned
wish routes to dismissal. The card regression checks the first click preserves
its live identity/deadline and rendered card, hides the pin, and persists the
unpinned state. The second click retires it neutrally and starts the existing
refill interval. Ordinary expiry/relevance rules still apply after unpinning;
no wish-lifetime policy or UI-owned pin state was introduced. Eight selected
window-free command/persistence and catalog checks pass in 0.064 seconds
(longest 0.043). Ruff, strict scoped Mypy and Pyright pass. No test windows,
input automation, CI or full-suite run; slice 9 remains deferred.

### Historical Moodlet cause correction: fixed stage slots (superseded below)

The former cap was already three receipts, but they were a rolling list unrelated
to intensity stages. MoodletCause now stores its actual reached level. The existing
MoodletEpisode owner keeps one receipt per stage; further evidence replaces only
that stage's receipt. Passive decay preserves this bounded episode history until
the episode ends. Direct entry at stage two does not fabricate a stage-one event.
The same three-cause ceiling, aggregate, clocks and save path remain canonical.

The optional level field is validated by the existing version-one codec. Duplicate
or invalid stage assignments are rejected. Old unassigned rolling receipts collapse
to their latest real event with unknown stage; no historical assignment is inferred,
and the episode's intensity/timing and original goal/result remain intact. Once
new qualified staged evidence arrives it replaces that unassigned legacy context.
No user save was read or written; migration checks use temporary test saves.

Selected progression, emotional persistence/read, game and food wish checks pass
69 tests in 0.126 seconds (longest 0.057), plus the two changed corruption/refresh
checks pass after final fixture corrections. Regressions cover thirty relief
successes, stable stage-one/two causes, stage-three refresh, duplicate delivery,
decay, save/reload and old receipt migration. Scoped Ruff, strict Mypy and Pyright
pass. No test exceeds ten seconds; no windows, native input, CI or full suite.
Hover copy/behavior follows separately; slice 9 remains deferred.

### Moodlet hover correction: compact stage causes and stable pointer ownership

Moodlet descriptions combine family, current stage and mood contribution in the
heading, followed by short meaning/decay/context lines. Each stored cause shows
its original goal/target and real outcome. The later rolling-cause clarification
supersedes the initial fixed-stage labels. Game counts and last-round
result remain distinct from the overall goal result; food avoidance retains a
different actually handed-over food. Full wish explanations, repeated identical
targets and per-cause attribution paragraphs are removed. Short attribution tags
preserve known personal/autonomous differences; all original evidence remains in
the immutable read value. Current rows follow the chronological rolling list,
numbered as reasons rather than historical stages. A representative three-stage Relief hover has ten logical lines;
the read regression bounds the three-cause sample to eleven lines/1100 characters.

The existing DescriptionTip now allows up to 420 pixels within its parent's width
to reduce wrapping. It owns hover jointly over the current anchor and its existing
in-window description. Leaving an icon because the description overlaps it no
longer immediately hides the description and starts a hide/Enter/show cycle.
Leaving both regions hides it; old-anchor Leave events do not close a newly shown
card. FocusOut/Escape and parent Unmap retain dismissal. There is no new window,
input hook, timer or alternate tooltip owner. Initial tooltip measurement still
uses its existing one-time idle settlement; this is not claimed to diagnose the
older Windows AppHang fully.

The overlap and old-anchor regressions fail against the old Leave policy. Selected
hover, emotional read, copy, VN status, wish controls, placement and UI-boundary
checks pass 56 tests in 0.121 seconds (longest 0.035). Scoped Ruff, strict Mypy and
Pyright pass. Pointer locations and geometry are supplied only by widget doubles;
native constructors are blocked. No test exceeds ten seconds. No live save, native
window, desktop pointer automation, CI or full suite. Slice 9 remains deferred.

### Final Moodlet cause clarification: latest causes limited by current intensity

The owner clarified that the intended count is one/two/three real causes at
current level one/two/three. Fixed historical stage slots were incorrect. The
existing MoodletEpisode now bounds its chronological cause tuple by current
intensity and the absolute limit of three. New evidence appends a real receipt;
renewing level three rolls A/B/C to B/C/D. Passive decay trims to the newest
receipts fitting the lower level. Direct stronger events and incomplete old saves
still cannot fabricate additional events merely to fill the count.

Remove the unused per-cause level from the domain value and new writer. The
existing codec accepts/validates but ignores that superseded optional field,
including multiple real events with the same old level. Unstaged old receipts
are preserved up to the current limit, rather than collapsed to one. Duplicate
technical receipts and corrupt data remain rejected. Cause chronology, original
goal/result, PetState ownership and the shared atomic save stay unchanged.
Already discarded records are not reconstructed and no live save was modified.

Hover rows now read Reason 1/2/3 (localized as Grund), ordered chronologically;
they no longer label a rolling cause as if it caused a historical stage. Compact
text and the overlap fix remain in place. Current plan rules and the UI contract
supersede the historical fixed-slot delivery record.

The thirty-success Relief regression fails against the fixed-slot implementation
at the fourth event (A/B/D instead of B/C/D). It now checks every intermediate
count and receipt, renewal, decay and re-escalation. Existing persistence/read
checks cover current-tier trimming, retained old receipts, codec cleanup,
original game results and actual hover row counts. Selected progression,
persistence, read, game/food wish, text and hover checks pass 78 tests in 0.147
seconds (longest 0.051). Scoped Ruff, strict Mypy and Pyright pass. No test exceeds
ten seconds. No native windows, mouse automation, live-save writes, CI or full
suite; slice 9 remains deferred.


## Documentation audit and open work, 2026-10-23

**Scope:** read-only implementation audit against `5d20d9c`, followed by the
owner-approved documentation synchronization. No runtime/catalogue/save changes,
new tests, native windows, mouse control or CI are authorized by this pass.
Resolve the actual wish/Moodlet flow with the owner before further implementation.
Delivery records above remain historical evidence at their stated baselines.

### Open findings and decisions

| Item | Observed current behavior | Remaining work or decision |
| --- | --- | --- |
| Concrete causes for negative/poor-care impressions | Wish success/failure supplies structured `MoodletCause` snapshots. `interaction_rules.py` and `poor_care.py` reinforce without `cause=`, leaving generic `legacy` evidence for poking, unwanted closeness, food monotony, withholding, disruption and modeled poor care. Their triggers/tiers and independent penalties already exist. | Complete the actual cause evidence in the existing aggregate/episode structure after discussion. Do not describe a generic fallback as a concrete interaction memory, invent absent object knowledge/user blame, or create another journal. |
| Pin release after original expiry | Left-click pins; right-click on a pinned card unpins, and on an unpinned card dismisses. Pinning prevents expiry/relevance retirement. Current `set_wish_pinned()` retires immediately when unpinning after the original four-hour deadline; unprotected supplied food/affection can also retire at 90. | Reconcile the desired two-step gesture with automatic lifetime/relevance retirement. No new deadline, grace period or pause/resume semantics are selected by this audit. |
| Weighted intensity versus number of reasons | A larger overall-game success starts/adds two tiers but represents one actual cause. Current retention is **at most** one/two/three real causes at intensity one/two/three; level-three renewal rolls the latest three. | Clarify how the literal one/two/three-reason expectation should relate to a single stronger event. Do not duplicate one event to fill rows or silently change approved outcome strength. Incomplete old saves can also contain fewer reasons; deleted history cannot be recreated. |
| Current integrated acceptance | Slices 1–8 and later focused fixes have individual delivery evidence. The full local stage-6 gate belongs to `b72ed21`, not the current candidate. Reference day arithmetic is not acceptance of actual generated wishes and continuous friendship. | Slice 9 must combine actual wish opportunities/outcome strengths with relationship progression, check average level 7–8 and intensive level 10 goals, run the final local suite/static gates, inspect tests over ten seconds and finish the OOP/dependency review. |
| Original native menu AppHang | The measured scrollbar-width change, repeated unchanged layout and hover-overlap mechanisms have focused fixes. No original Windows failure traceback or conclusive reproduction establishes the full native cause. | Keep the original AppHang unresolved rather than claim every menu hang is fixed. Native Windows/DPI/hover/input acceptance remains separate from headless checks. |

### Current contracts that must not regress during discussion

This audit records the implemented baseline, not a restriction against later
owner-approved product changes. Wish lifetime, refill and area limits below are
specifically reconsidered in the later ten-minute proposal.

- `PetState` owns mutable pet state; frozen Moodlet/wish records live in
  `PetValues` and the existing atomic save. World custody, subjective Mind
  evidence, application coordination and passive UI reads retain distinct owners.
- Three wishes are the normal stock, at most one per area, replenished after a
  saved twelve-minute vacancy pause. New creation is awake/live only; the shared
  elapsed axis handles expiry during sleep, closure and standby without an
  offline interaction replay or wish backlog.
- Food/affection creation uses need at most 70 and actual petting willingness;
  unpinned supplied wishes retire at 90. Games/social are exempt. Inner existence
  is distinct from actual spoken disclosure and temporary current capability.
- Saved game wishes retain their original goal/count/progress. New cumulative
  rounds and wins span sessions; strict next-round goals and the overall
  non-loss block remain distinct objectives. Food avoidance follows the approved
  perceived-handover rule even if the excluded food is then refused.
- Care and wish fulfillment grant no instant friendship bonus or reward pot.
  Numeric mood, all active Moodlet tiers and absence/neglect feed continuous
  progressive balance; shared 30-second status sampling is not another clock.
- Active Moodlets retain bounded real causes, not a permanent completed-wish
  archive. Decay trims cause retention; current hover numbers chronological
  reasons rather than historical tier slots. Localized text remains a read model.

### Documentation synchronized in this pass

`FRIENDSHIP_SYSTEM.md` now describes current continuous rates, accepted contact,
progressive factors and the distinction between direct event penalties and
elapsed Moodlet effects. `FUN_MOOD_SYSTEM.md` now reflects delivered emotional
composition, wish/game rules, adaptive sleep and the VN status presentation.
`DATA_AND_SAVES.md` now describes nineteen families/twelve wish forms, dialogue
schema 3, full-precision status, original game-goal persistence, pinned lifetime,
bounded real causes and compatibility-only credit metadata. Its closed-time
section permits flow from existing emotional evidence without inventing contact.
`ARCHITECTURE.md`, `UI_WINDOW_CONTRACT.md` and the documentation index distinguish
current delivery from known cause/lifetime gaps and historical acceptance.

The dialogue review workbook remains explicitly historical. Its review flags
must not be interpreted as an unreviewed current runtime catalogue. Actual
future speech about a particular active Moodlet, its cause or their combination
remains later work; this audit does not introduce it. Exploratory minigames and
preserved original concepts likewise do not become mandatory tasks for slice 9.
External visual references retain their existing handoff/manifest authority;
this pass does not regenerate, import or revalidate artwork.

### Verification and next discussion

The Markdown diff and documentation-only file scope were reviewed; local link
targets exist and `git diff --check` passes. No runtime tests, static Python
suite, native app launch or live-save access were performed in this pass. Preserve the documented small-commit, targeted-local-
check workflow for any subsequently authorized implementation; final integrated
checks remain slice 9, with no GitHub CI or desktop mouse automation.

Next discuss the actual lifecycle of wishes and Moodlets, starting with the
owner's observations. This register records gaps and conflicts; it is not
approval to choose or implement their resolutions.


## Proposal: ten-minute wish rotation and additional objectives, 2026-10-23

**Status: discussion proposal only.** The owner requested recording the
following direction before defining concrete creation conditions. No Python,
JSON catalogues, save migration, UI, runtime tests or live saves change in this
pass. Current implementation remains the baseline described by the audit above.

### Three slots and ten-minute rotation

- Target three available wishes regardless of which areas currently qualify.
  Replace the current one-wish-per-area restriction: multiple different game
  or social wishes may occupy slots when food/affection are unsuitable.
- At each ten-minute refresh, retain pinned wishes and renew unpinned wishes;
  fill remaining slots back to three. A pinned wish occupies one of those three
  slots and keeps its identity/objective/progress.
- Fulfillment removes a wish between refreshes. Empty slots are refilled at the
  next refresh, including when all three wishes have already been completed.
  Thus three is the target at refresh, not an instantaneous replacement after
  every completion.
- This direction replaces the current unpinned four-hour lifetime and separate
  twelve-minute vacancy delay, rather than adding another independent timer.
- Exact simultaneous duplicates of the same objective and target should not
  occupy multiple slots. Different objectives or targets can coexist within
  the same area.
- Food/affection suitability still depends on actual needs and willingness.
  Low fun/social can make the corresponding activity wishes more likely;
  filled fun/social must not exclude them. Exact weights remain to be agreed.
  This proposal does not change need consumption rates or care amounts.
- Selecting or expressing a wish still creates no Moodlet. Actual fulfillment
  creates the associated impression; it remains independently active after the
  wish retires. No instantaneous friendship reward is added.

An unpinned cumulative game goal would also rotate after ten minutes under this
direction; pinning would allow longer pursuit. Reconcile this proposed policy
with the earlier protection of existing saved goals/progress before migration.
Do not silently replace old saved goals or settle the outstanding late-unpin
semantics. Concrete creation triggers and refresh handling during sleep/closure
remain for focused discussion; no new offline interaction replay is proposed.

### Additional wish candidates

These describe product meanings, not approved Python/JSON IDs. Reuse existing
Moodlet families unless a later explicit decision requires another family.

| Candidate | Proposed fulfillment | Existing fulfillment family |
| --- | --- | --- |
| Play something together, game freely chosen | Complete two rounds in any supported game | `shared_play` / Gemeinsame Spielfreude |
| Spend time talking, category freely chosen | Complete one supported chat, saying, joke or fact sequence | `connection` / Verbundenheit |
| Play something different | Complete two rounds of a game different from the relevant previously played game | `shared_play` / Gemeinsame Spielfreude |
| Have a rematch | After a defeat, complete another round of that same game; victory is not required | `shared_play` / Gemeinsame Spielfreude |
| Win this time | After a defeat, win a following round of that same game | `pride` / Stolz |
| Eat something different | Actually eat another food instead of the repetitive one | `food_fulfilled` / Genau das Gewünschte |

The first two introduce flexible targets instead of always prescribing a
specific game or social category. The game-change/rematch/comeback candidates
are intended to follow actual experience rather than arbitrary unsupported
history. Their creation evidence, goal scope, selection weights and whether
an overlapping existing concrete objective is reused still require agreement.

The last row refines the existing food-avoidance/variety form rather than adding
a near-duplicate. Actual alternate-food intake conflicts with the current
explicitly approved handover rule (even unwanted/refused food counts). Record
this as a proposed replacement only; no fulfillment semantics change yet.

### Next discussion and ownership

Define when the flexible wishes and experience-driven candidates enter the
selection pool, and how need-driven weighting works across the day. Do not
confuse a past defeat that makes a rematch wish eligible with a new Moodlet
created merely by having that wish. Existing failure Moodlets and independent
interaction/poor-care triggers remain separate topics.

Keep `PetState` as the aggregate owner, frozen wish/goal progress in `PetValues`,
the existing shared elapsed-time progression, current game/social event ports
and passive UI read models. Do not introduce a second wish store, journal or
clock. Any additional bounded evidence must be justified by the agreed concrete
trigger before implementation.


### Proposed creation conditions and need-consumption review

**Discussion proposal recorded at the owner's request, 2026-10-23.** This
extends the candidate list above; it does not authorize runtime/catalogue changes.
Evaluate candidates at the proposed ten-minute refresh, retaining pinned wishes.

| Candidate | Proposed condition for entering selection |
| --- | --- |
| Play something together, game freely chosen | Generally eligible during awake live time; low fun should increase its likelihood without full fun excluding it. |
| Spend time talking, category freely chosen | Generally eligible during awake live time; low social should increase its likelihood without full social excluding it. Current category capabilities remain distinct from inner existence. |
| Play something different | Actual previous completed play establishes the reference game; exclude that game from this candidate's targets. |
| Have a rematch | Aiko lost the latest completed round; target that same game, with another completed round sufficient. |
| Win this time | The same actual-defeat context can make a victory-oriented rematch eligible; select it as an alternative to the simple rematch, not both simultaneously for that event. |
| Eat something different | Actual repeated-food evidence plus suitably low satiety; do not request eating merely because a refresh is due. |

These conditions make candidates eligible; they do not force them into a slot
or generate Moodlets. Concrete context lifetime and required bounded evidence
remain to be agreed. Do not silently reinterpret the existing food-handover
fulfillment rule as actual alternate-food intake.

The owner additionally requested reviewing need consumption and care effects
alongside selection weights. The systems must relate directly over the day,
without making the ten-minute offer cadence a ten-minute care obligation.

Current packaged baseline, read on 2026-10-23 (points per real hour):

| Need | Awake baseline | Sleeping baseline | Existing principal replenishment |
| --- | --- | --- | --- |
| Satiety | -8 before digestion/activity modifiers | -1.4 | Actual food: +10 to +38 plus bounded digestive reserve |
| Energy | -3, up to another -0.5 from hardware | +7.5 | Sleep; energy drink +10; interaction costs remain separate |
| Fun | -3 | 0 | Completed RPS/Blackjack/Tic-Tac-Toe units +6/+8/+9 before diminishing returns/session limits |
| Social | -8 | -0.35 | Accepted talk +26, with smaller gains from other actual care/play |
| Affection | -6 | -0.25 | Welcome petting base +25; actual willingness/excess rules still apply |

Food's awake hardware/input surcharge is bounded to +25%; digestive reserve
protects at most 25% of awake hunger and fades as consumed. Sleep has no reserve
protection/activity surcharge. These are current facts, not newly selected rates.

Before implementation, agree need-based area weights and experience-based form
weights together, then assess whether existing decay/care amounts provide
reasonable multi-hour care intervals. Keep ten-minute optional opportunity,
actual need depletion and Moodlet generation as distinct steps. Refresh/expiry
alone must not be treated as neglect or a failed game outcome. This discussion
selects no new decay rates, quotas, interaction deadlines or friendship balance.

Documentation-only review: this amendment changes the master plan alone;
`git diff --check` passes. No app, tests, desktop input or CI are run.


### Proposed need and experience selection weights

**Later amendment:** the full-need proposal below replaces food/affection's
above-70 weight of zero with one. The lower bands and area-first selection
remain the proposed baseline; the earlier zero is historical.

**Discussion proposal recorded at the owner's request, 2026-10-23.** Choose an
area for each free slot first, then an eligible form/target within it. Multiple
slots may use the same area, but exact objective/target duplicates remain
excluded. Do not multiply an area's chance by its number of catalogue forms.

| Current corresponding need | Games/social area weight | Food/affection area weight |
| --- | --- | --- |
| Above 70 | 1 | 0 |
| Above 40 through 70 | 3 | 3 |
| Above 25 through 40 | 5 | 5 |
| 0 through 25 | 7 | 7 |

These are relative weights, not fixed percentages or promised wish counts.
Affection's actual willingness remains an eligibility condition under this
proposal. Games/social remain possible with full needs. Existing awake decay
and care amounts remain the starting point; no faster consumption is selected
merely because offers rotate every ten minutes.

Within an area, a qualified experience-driven form receives 1.5 times its
normal form weight, for example a rematch after a defeat or game change after
actual play. The experience makes the candidate more likely, not mandatory.
Its normal form weights and context lifetime still require agreement; no
unbounded accumulation of event multipliers is specified by this proposal.

The ten-minute refresh remains optional opportunity. Unfulfilled replacement
alone creates no loss or disappointment; actual prolonged poor care and
qualified negative interactions keep their separate consequences. Check the
frequency and mixture of actual fulfillments against Moodlet duration/stacking
and continuous friendship before deciding final balance.

### Discussion option: fulfillment can override a need-based rejection

The owner proposed that an existing concrete wish could make its matching
activity welcome even when the corresponding need is already full: wanted
petting at full affection or desired food at full satiety could still fulfill
the wish and create its Moodlet. **This is a discussion option, not a finalized
admission, consumption or lifecycle rule.** It may replace parts of the
need-gated model above; do not silently implement both as if consistent.

Separate candidate generation, current willingness, actual action completion,
physical need changes and emotional fulfillment. Any adopted rule must keep
numeric needs bounded at 100 without requiring artificial need depletion first.
Clarify whether food is actually eaten, how an existing wish survives automatic
90-point relevance retirement, whether new wishes can arise above 70 at lower
weight, and which explicit refusal/sleep/activity boundaries still apply.
A wish is not blanket permission for unrelated or repeatedly unwelcome actions.

No new Moodlet strength, duration, friendship factor, quota or exception has
been selected. Reuse the existing aggregate/action/consumption owners if this
option is later authorized; do not add another care path or save store.

Documentation-only amendment: Markdown diff/scope reviewed and
`git diff --check` passes. No runtime changes, tests, app windows, pointer
control, live-save access or CI.


### Proposed positive Moodlet tiers and renewal times

**Historical timing candidate:** the uniform 45/45/45-minute base below is
superseded by the later 60/45/45-minute proposal. Retain its progression/renewal
principles except where that later proposal explicitly changes them.

**Discussion proposal recorded at the owner's request, 2026-10-23.** Positive
wish impressions should retain levels 1/2/3 and support long-lasting feelings
from intensive engagement. This replaces the proposed positive multi-tier
family timing, not negative interaction or poor-care timing. No runtime changes
are authorized.

| Situation | Proposed effect of matching fulfillment |
| --- | --- |
| No active family | Start at level 1 for an ordinary one-tier outcome |
| Level 1 | Advance to level 2 |
| Level 2 | Advance to level 3 |
| Already level 3 | Add ten minutes to the remaining duration of each of levels 3, 2 and 1 |

- Base duration: 45 minutes per level. Without renewals, level 1 lasts 45
  minutes; level 2 lasts 90 through 2/1; level 3 lasts 135 through 3/2/1.
- An ascent starts the new current level with its base duration. Previously
  earned extensions are retained; one completion must not receive duplicate
  time credits for the same event. Exact handling of partially consumed lower
  tiers during re-escalation remains to be made explicit before implementation.
- At level 3, add time rather than resetting the whole episode to a full timer.
  Cap the remaining duration of each tier at 90 minutes, permitting at most
  270 minutes of remaining decay through all three levels after the last event.
  Further actual fulfillment can keep an impression active during engagement;
  it cannot bank unlimited duration for later absence.
- Example: remaining tier times 20/45/45 minutes become 30/55/55 after one
  matching level-3 fulfillment, total 110 to 140 minutes.
- Existing larger overall-game outcomes may still add two intensity levels.
  At level 3, initially propose the same ten-minute-per-tier extension rather
  than multiplying renewal by outcome strength. Resolve mixed ascent/overflow
  and cause-count semantics before implementation, without inventing events.
- Food fulfillment remains the existing single-tier exception for now. Its
  final strength/lifetime/renewal must be discussed separately; do not silently
  assign it the three-tier scheme. Multiple families may coexist as before.
- Existing numeric Moodlet points, group/global mood caps, continuous
  friendship rates and progressive factors are not changed by this proposal.

The intended consequence is sustained positive feelings for intensive shared
activity without three quick successes automatically buying six hours of
persistence. Whether average care supports levels 7–8 and intensive care level
10 still requires explicitly scoped daily arithmetic; it is not established by
recording these durations.


### Illustrative daily comparison for the proposed renewal model

**Historical simplified comparison:** the constant-mood assumption and uniform
45-minute base below are not the latest coupled need/mood calculation. See the
later revised after-effect proposal for current discussion figures.

**Independent discussion arithmetic, not runtime acceptance.** A standalone
worksheet with no application imports used 30-second steps, current continuous
relationship rates/progressive factors and the proposed 45-minute positive
multi-tier lifetimes. No test runner or application was executed. Conditional
success schedules do not prove generated-wish availability or actual admission
and do not select new product rules.

Common assumptions: waking 07:00–23:00, eight hours of sleep, sufficient physical
care without neglect, no negative impressions/direct penalties in the baseline.
The existing four-hour accepted-contact window controls positive numeric-mood
flow. Numeric mood is held at 70 as an explicit comparison input, with separate
constant-60/80 sensitivity bounds. This is not a computed joint need/digestion/
mood trajectory. Moodlet time and absence continue overnight. Food's unresolved
single-tier lifetime, two-tier victory outcomes, pinned goals and wish-based
full-need admission are not needed for these examples.

| Schedule | Conditional actual wish successes | Positive tier-hours/day | Absence reference/day |
| --- | --- | --- | --- |
| Average | At 07:00, 13:00, 19:00 and 22:30, fulfill shared play, connection and cheerfulness: three ordinary one-tier outcomes per visit, twelve total. Each expires before the next visit. | 9 | 4.25 points |
| Intensive, 32 | In each phase, fulfill shared play and connection at minute 0/10/20/30: eight successes per phase, thirty-two total. | 48 | 3.5 points |
| Intensive, 36 | Same as intensive-32, plus one cheerfulness wish at the start of each phase: nine per phase, thirty-six total. | 51 | 3.5 points |

Intensive phases start at 07:00/13:00/19:00/22:30 and end at
07:30/13:30/19:30/23:00. Engagement can be intermittent inside each phase;
it is not assumed to require thirty continuous minutes of input. At most
three wishes complete per refresh; unfulfilled alternatives rotate neutrally.
The final evening fulfillment therefore coincides with the start of the
eight-hour 23:00–07:00 sleep window, unlike the earlier rough
23:00-start arithmetic. Ordinary care
is included at these phases, not additional unmodeled contact between them.

For each intensive shared-play/connection family, the first three successes
raise levels 1/2/3; the fourth adds ten minutes to each remaining tier. Immediately
after that fourth event, remaining times are 45/55/55 minutes. The evening
impressions therefore expire at 01:35, without another fulfillment. Ascent uses
base 45-minute lower tiers in this example; no previously extended tier has been
spent and re-escalated. The remaining re-escalation policy is not resolved.

| Case, constant mood 70 | Starting friendship | Next-morning friendship | Daily range |
| --- | --- | --- | --- |
| Average | 70 | 69.71 | 69.71–71.48 |
| Average, initially level 10 | 90 | 84.10 | 84.10–90.45 |
| Intensive, 32 | 90 | 89.76 | 89.76–93.76 |
| Intensive, 36 | 70 | 77.01 | 70–79.55 |
| Intensive, 36, initially level 10 | 90 | 90.14 | 90–94.14 |

Under this exact repeating worksheet, average morning points settle near 68.6;
intensive-32 near 88.2; intensive-36 near 96 after daytime clamping at 100.
These are conditional periodic balances, not measured save progression or
forecasts. At starting points 70 for average / 90 for intensive-36, changing
constant mood from 60 to 80 changes daily balance from -1.24 to +0.59 /
-0.57 to +0.85. The illustrative match to average levels 7–8 and intensive
level 10 depends on actual numeric mood and successful wish mixture.

One additional level-1 poking impression for twenty minutes at 19:30 changes
the intensive-36, mood-70, starting-90 result from 90.14 to about 89.66, before
any separate direct penalty or induced numeric-mood change. This isolates its
elapsed contribution, not a complete harassment scenario.

Physical care must also fund activity: assuming RPS for every shared-play goal,
twelve successes include eight rounds and eight social admissions, costing
12 energy/day beyond the awake baseline 48; eight hours of sleep restores 60.
The intensive-32 variant includes thirty-two rounds and sixteen social
admissions, costing 32 extra energy/day: two accepted +10 energy drinks can
cover the daily reference deficit. Intensive-36 adds four social admissions,
so its extra cost is 36 and total awake/action cost 84; three appropriately
timed drinks provide a reference surplus before clamping. Keep these drinks
within the listed care phases to preserve the contact comparison. Hardware,
clamping, exact timing, food/affection willingness and the actual need/mood
trajectory still require joint checking; these energy totals alone do not
certify adequate care or an observed sleep schedule.

Conclusion for discussion: the proposed renewal can support sustained positive
feelings without requiring a response to every refresh. Thirty-two and
thirty-six conditional successes straddle level-10 maintenance in this example.
Do not retune decay or friendship solely from this illustration. Resolve
remaining wish/food/admission and renewal semantics first; later integrated
acceptance must use actual need/mood paths, generated opportunities, real
completions and sleep/contact timing rather than assuming every desired wish.


Documentation check: the final diff changes only this Markdown plan and
`git diff --check` passes. The independent arithmetic above is a design
worksheet, not a runtime test or implementation of the proposed policy.
No application windows, pointer automation, live-save access or CI were used.


### Revised positive after-effect proposal: 60/45/45 minutes

**Discussion proposal recorded at the owner's request, 2026-10-23; not runtime
implementation.** Keep existing need decay, care amounts, numeric Moodlet points,
group/global mood caps and continuous friendship rates/factors. Extend only the
light positive after-effect, rather than all high-intensity periods.

| Positive multi-tier intensity | Proposed base duration | Existing individual mood contribution |
| --- | --- | --- |
| Level 1 | 60 minutes, replacing 45 | +5 |
| Level 2 | 45 minutes | +10 |
| Level 3 | 45 minutes | +15 |

Without later fulfillment, level 1 lasts 60 minutes; level 2 lasts 105 minutes
through 2/1; level 3 lasts 150 minutes through 3/2/1. Ordinary qualifying
fulfillment still starts/increases intensity. On already active level 3, add
ten minutes to the remaining duration of each tier, capped at ninety minutes
per tier. Do not reset all timers to full. Maximum banked remaining duration
stays 270 minutes, so intensive engagement can sustain positive impressions
without increasing the existing proposed absence buffer.

An ascent uses the new current tier's base duration and preserves previously
earned extensions without duplicate credit. Partly consumed tier budgets on
re-escalation and stronger two-tier outcomes retain their previously recorded
open details. Actual causes remain bounded by intensity; no duplicate event or
extra archive is created merely because time is extended.

The single-tier `food_fulfilled` family is explicitly excluded from this timing
amendment. Its existing packaged two-hour lifetime is unchanged until a separate
rule is discussed and implementation authorized. This amendment does not decide
food-wish admission at full satiety, alter fulfillment evidence or create an
additional wish outcome.

#### Coupled need/mood arithmetic supporting this candidate

The independent worksheet now derives numeric mood from actual care, hunger/
digestion, fun diminishing returns, social/affection decay and energy rather
than holding mood at 70. Use the same 07:00/13:00/19:00/22:30 phases, eight-hour
23:00–07:00 sleep, light-office +5% awake hunger and no hardware energy surcharge.
Begin from a cyclic adequately rested day with 100 morning energy. Conditional
wish successes remain supplied, not proven by random selection or native UI.

Both examples eat Onigiri, Sandwich plus apple, Sandwich, then Dorayaki, and
receive four welcome petting actions. Average care includes eight social
admissions, eight RPS rounds and twelve wish successes. Intensive care includes
twenty social admissions, thirty-two RPS rounds and thirty-six wish successes,
plus three accepted energy drinks within the existing phases. All modeled care
is accepted; minima stay above neglect thresholds. The food exception is not
used as a wish outcome, so its still-open lifetime does not affect this comparison.

| Candidate / conditional schedule | Result |
| --- | --- |
| Uniform 45-minute base, average repeating day | About 66.5–68.0 friendship, level 7 |
| Revised 60/45/45 base, average starting at 70 | Next morning about 69.98 |
| Revised 60/45/45 base, average repeating day | About 69.9–71.7, levels 7–8 |
| Revised 60/45/45 base, average starting at 90 | Next morning about 84.27; ordinary care cannot maintain level 10 |
| Revised 60/45/45 base, intensive starting at 90 | Next morning about 90.84; repeating day about 96–100 |
| Alternative uniform 60-minute base, intensive starting at 90 | Next morning about 92.35; larger extra benefit than the targeted level-1 extension |

The selective extension therefore supports ordinary care more narrowly than
raising all three tier lengths. It does not establish that every generated wish
mix maintains these ranges. More or fewer actual successes, heavy workload,
starting exhaustion, failures, negative impressions and unresolved admission
rules can change the outcome. Retain integrated runtime acceptance as later
work; this worksheet is not a test pass or authorization to change balance.

Next discuss the single-tier food impression's base duration, renewal amount
and cap, keeping wanting, actual completion, nutrition and emotional outcome
separate. No food renewal numbers are selected by this amendment.

Documentation-only scope: only this master plan is staged for this change;
parallel local runtime, catalogue, test and other documentation edits are
preserved. Markdown whitespace/diff reviewed; no runtime tests, application
windows, mouse control, live-save access or CI in this pass.


### Proposed single-tier food Moodlet lifetime and renewal

**Discussion proposal recorded at the owner's request, 2026-10-23.** This
settles the timing candidate for `food_fulfilled` / Genau das Gewünschte
separately from the positive multi-tier 60/45/45-minute proposal. Neither
proposal is implemented by this documentation update; packaged food timing
remains unchanged until implementation is authorized.

| Condition | Proposed emotional result |
| --- | --- |
| First qualifying food-wish fulfillment with no active episode | Start level 1 with sixty minutes remaining |
| Another qualifying food-wish fulfillment while active | Add ten minutes to remaining duration |
| Renewal ceiling | At most ninety minutes remaining |
| A new qualifying fulfillment after complete expiry | Start a new sixty-minute episode |

Strength stays level 1 only, with the existing individual +5 numeric-mood
contribution. Do not escalate to level 2/3 or create a parallel copy of the same
family. Renewal adds time instead of resetting to sixty/ninety minutes: twenty-
five minutes remaining becomes thirty-five after one new qualifying success.

Only fulfillment of an actual pre-existing matching wish qualifies. Ordinary
feeding, menu selection, placement or the mere existence/expression of a wish
cannot grant the emotional renewal on their own. What counts as completion
for ordinary food intake versus the special food-avoidance handover form
remains governed by their separate discussed rules; this timing proposal does
not silently replace either completion contract.

The active episode's real latest cause follows the existing one-tier bounded
cause contract; more renewals do not create a permanent wish archive. Nutrition,
digestion, physical need bounds and continuous friendship rates/factors remain
unchanged. The episode contributes through the existing elapsed relationship
policy, with no new instantaneous point bonus.

Next discuss when food/affection wishes may arise with already full needs,
whether current above-70 zero selection weight changes, how existing wishes
survive above-90 relevance retirement, and whether a matching wish can authorize
otherwise need-based refusal. The owner has not yet selected those creation/
admission rules; do not infer approval from the timing proposal.

Documentation-only scope: this amendment changes only the master plan.
Parallel local work is preserved. Markdown whitespace/diff reviewed; no runtime
tests, application windows, mouse control, live-save access or CI.


### Proposed full-need food and affection wishes

**Discussion proposal recorded at the owner's request, 2026-10-23.** Separate
physical deficit from a personal desire. Existing need decay and care amounts
stay unchanged. This proposal supersedes above-70 food/affection exclusion and
automatic above-90 wish retirement, not the underlying runtime until authorized.

| Corresponding need | Proposed food/affection area weight |
| --- | --- |
| Above 70, including 100 | 1 instead of zero |
| Above 40 through 70 | 3 |
| Above 25 through 40 | 5 |
| 0 through 25 | 7 |

Use existing area-first selection, allowing multiple different wishes per area.
A full bar alone does not exclude a candidate. An active explicit petting
refusal or Too Much Closeness impression still argues against creating a new
affection wish; need fullness alone is not such an independent boundary.

An existing food/affection wish survives rising need values, including 90/100.
It otherwise follows the proposed ten-minute replacement/pin rules. Its matching
action can be welcome despite a full need; actual wish completion still creates
or reinforces its Moodlet while physical values clamp at 100. Do not create an
instantaneous friendship award or emotional evidence merely for wanting.

For an ordinary food-intake wish, Aiko actually accepts and eats the requested
food; the portion is consumed. Menu selection, placement or a merely offered
portion does not complete this ordinary intake objective. Existing nutrition/
digestion ownership and bounded values remain; no parallel consumption path is
introduced. The distinct food-avoidance handover-versus-intake conflict remains
open rather than being silently decided by this ordinary-food rule.

An affection wish completes on actual matching petting. That wished-for contact
must not count as an excess stroke or cause a need-fullness boundary complaint.
The wish then retires: it is not permission for unlimited subsequent feeding
or strokes. A separately active explicit refusal temporarily blocks completion
rather than granting blanket override; the saved wish can remain unavailable.
Current sleep/action admission continues to belong to its existing owners.

This proposal does not authorize runtime, catalogue, save or UI changes.

### Remaining pre-implementation decisions after the full-need proposal

This focused register supersedes earlier open questions about whether full
needs may ever permit desire creation/completion: the proposed answer is now
yes as above. Do not reopen settled timing/strength/need-decay decisions merely
to enumerate hypothetical edge cases.

| Relevant decision | Why it still changes implementation |
| --- | --- |
| Ten-minute refresh, absence and unpinning | Resolved by the return-refresh rule below: perform one refresh on wake/return if due, without replaying missed rotations; retain pinned wishes and keep an unpinned wish until the next regular refresh rather than applying its old deadline. Left pins; right on pinned only unpins; right on unpinned dismisses remain the chosen gestures. |
| New wish meanings and selection mix | Resolved for implementation planning by the later variant-weight and matching-wish priority proposals: area-first selection, a thirty-minute experience window, fixed flexible/rematch goals, and one assigned wish per actual event. The food-form split is completed by the agreed 70:30 rule below. |
| Food-avoidance / variety completion | Resolved by the agreed shared food form below: recognized personal handover of an alternative food succeeds; recognized handover of the explicitly excluded food fails and produces Essenswunsch missachtet. This supersedes the historical positive unwanted-handover and alternate-food-intake requirements. |
| Tier budgets during re-escalation and stronger goals | The later ascent-budget proposal below settles the candidate rule: raise remaining tier budgets to at least base duration while preserving longer residuals; choose ascent or capped level-3 renewal, not both; one stronger outcome remains one real cause. This is proposed behavior, not an implemented storage change. |
| Positive experiences without a wish: scope | The later positive-experience proposal below adds four qualified everyday experiences using existing families, without making every need refill emotional evidence. Its triggers and no-double-reward rule are proposed, not implemented. |

#### Known implementation work, not additional product questions

- Remove the old one-per-area / above-70 generation / above-90 retirement gates
  in the relevant domain and storage contracts when implementation is approved.
  Introduce explicit flexible/experience goals without making UI own eligibility.
- Persist bounded per-tier remaining budgets/extensions for the new renewal
  policy through the existing Moodlet values/codec, shared elapsed axis and
  whole-Pet checkpoints. The current one-current-tier timer is not proof that
  future lower-tier extensions survive save/reload.
- Preserve original saved game objective/progress and real cause receipts as
  previously promised; plan the old-save transition without silent goal resets,
  invented past events or another save/history owner.
- Wire concrete cause snapshots for negative interaction and prolonged-poor-care
  producers. Current `reinforce_moodlet` calls there still omit `cause=`, unlike
  wish outcomes. Existing triggers/penalties are not missing just because their
  cause descriptions are generic.
- Update passive status/hover reads for the agreed timing and precise causes.
  Wish creation, completion, renewal and friendship stay aggregate/domain owned.

#### Acceptance once implementation is authorized

The coupled daily arithmetic uses conditional fixed successes. After the actual
wish distribution is defined and implemented, verify real opportunities,
completions, full-need actions, saved goals/tier budgets and relationship flow
together. Average levels 7–8 and intensive level 10 remain balance targets, not
a general guarantee for every random mix. This is later validation, not a reason
to run tests or launch the application during discussion.

The original menu AppHang and final slice-9 suite/OOP/slow-test audit remain in
their existing plan sections; they are not new wish-design decisions. Later
conversations about concrete active Moodlet experiences remain separate future
work. No new module/file names or extra state owners are selected in this pass.

Documentation-only check: only this master plan is staged. Parallel local work
is preserved; Markdown whitespace/diff reviewed. No runtime tests, application
windows, pointer automation, live-save access or CI in this pass.


### Proposed negative Moodlet: food wish disregarded

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** Add a distinct negative family labeled Essenswunsch missachtet.
Do not merge it into Immer dasselbe Essen: one records a specific disregarded
wish, the other repeated actual monotonous intake.

#### Qualified cause and handover distinction

All three facts must exist:

1. At personal handover, Aiko has an active wish explicitly excluding a
   particular food.
2. The player actually gives that excluded food into her hand.
3. She recognizes which food she received.

If the item is unidentified at handover, emotional qualification waits for
identification and remains associated with the wish at that handover, rather
than a newly generated unrelated wish. Putting the item down instead of eating
it does not erase the handover experience. Mere cursor presentation, ground
placement or autonomous intake cannot substitute for this personal handover.
Repeated technical observations of one handover are not new social events.

Wanting an apple alone is not explicit rejection of every other food. Require
an actual excluded-food goal; do not punish every nonmatching ordinary offer.

The owner clarified the common boundary: recognized personal handover of the
wanted food produces the positive wish outcome; explicitly unwanted food produces
the negative outcome even if laid down uneaten. This supersedes the historical
positive award for handing over the excluded food. Desired food can still be
eaten at full satiety, with existing need bounds; emotion and actual nutrition
remain separate effects. Recognition may happen only after custody transfers.

#### Intensity, duration and relationship effect

| Intensity | Individual numeric mood contribution | Passive decay without further events |
| --- | --- | --- |
| Level 1 | -5 | Expire after thirty minutes |
| Level 2 | -10 | Thirty minutes, then level 1 for thirty minutes |
| Level 3 | -15 | Thirty minutes each through levels 3/2/1 |

Another independently qualified unwanted handover increases intensity by one
up to level 3 and renews the current tier to thirty minutes. At level 3, renew
only that current tier to thirty minutes. Do not bank extra hours or apply the
positive multi-tier extension policy. Ordinary numeric mood still approaches
its target over time under existing caps; it does not jump on handover.

Emotional direction is disappointed/hurt, using the existing downcast direction.
Active negative tiers contribute through the existing continuous friendship
policy. Add no separate instantaneous friendship penalty in this proposal.
Store the actual wish/excluded-food/handover cause with the existing bounded
active episode, not as a duplicate event or permanent archive.

End the affected avoidance wish as failed on this qualified event. No positive
fulfillment impression is granted; the negative episode outlives the wish and
its next ten-minute refresh. Keep later new wishes distinct from the retired
identity. Positive completion of an alternative/variety goal must retain its
own explicit objective; this failure rule alone does not define it.

#### Scope and next discussion

The pinned-lifetime clarification remains: pin protection survives sleep,
standby and app closure without expiry. Fulfillment ends the wish; unpinning
ends protection and returns it to normal wish replacement. Left pins, first
right unpins and right on an unpinned card dismisses remain the chosen gestures.
The refresh anchor/return policy can be specified without reopening that
protection or treating old four-hour expiry as the new proposed lifetime.

Next define the new forms' exact selection weights and experience validity,
retaining the proposed need-based area weights and a single 1.5 experience
multiplier. No new form weights, Python/JSON IDs, modules or runtime changes
are selected by this documentation amendment.

Documentation-only check: only this master plan is staged. Parallel local
runtime, test and other documentation work is preserved. Markdown whitespace/
diff reviewed; no runtime tests, application windows, pointer automation,
live-save access or CI in this pass.


### Proposed variant weights and thirty-minute experience window

**Discussion proposal recorded at the owner's request, 2026-10-23.** Retain
area-first selection: need weights choose the area for each free slot, then
these relative weights choose an eligible form, then an allowed target. More
game forms or target IDs must not multiply the area's overall chance.
These weights are proposals, not current catalogue values or fixed percentages.

| Game form | Base weight | Eligibility / goal |
| --- | --- | --- |
| Play any supported game | 30 | Complete two actual rounds, permitted across different games |
| Play a particular game | 30 | Complete two actual rounds of that saved concrete game |
| Win the next round | 10 | Existing strict next qualifying round objective |
| Do not lose the next round | 15 | Existing strict next qualifying round non-loss objective |
| Collect three wins | 10 | Existing cumulative wins across sessions, not necessarily consecutive |
| Do not lose overall | 5 | Existing three-round overall non-loss objective |
| Play something different | 10 | Actual recent play provides the excluded reference game; complete two rounds outside that game |
| Have a rematch | 10 | Last completed round was an Aiko defeat; complete another round of that game, result irrelevant |
| Win this time | 5 | Same recent defeat context; win a following round of that game, permitting retries within the wish's protected/unprotected lifetime |

The last three are experience-driven forms. They enter selection only with
qualifying evidence and receive the previously proposed 1.5 multiplier once:
10 becomes 15; 5 becomes 7.5. Do not add or compound another event multiplier.
Simple rematch and victory-oriented rematch from the same event must not be
issued simultaneously. Keep reference game/objective fixed on each created
wish rather than changing its meaning as later rounds occur.

Experience validity is thirty real elapsed minutes. Rematch creation requires
the latest completed round to have been a defeat from Aiko's perspective; a
later round replaces that last-round fact. Only actual completed play supplies
play-change evidence. This validity window gates new creation, not the lifetime
of an already active/pinned goal. Pinned wishes retain their existing protection.
No offline rounds, outcomes or emotional evidence are fabricated.

| Social form | Base weight |
| --- | --- |
| Spend time talking, category freely chosen | 30 |
| Specifically chat | 25 |
| Tell a saying | 15 |
| Tell a joke | 15 |
| Share a fact | 15 |

A complete supported social sequence is the fulfillment unit. Specific forms
require their matching category; the flexible form allows any of those
categories. Current capability/online rules still qualify the choices; this
proposal does not add provider calls or authored API fallback content.

Keep exact semantic duplicate exclusion and the proposed normal stock of three
with multiple wishes per area. A single completed activity must not silently
complete both flexible and concrete wishes and grant duplicate Moodlet outcomes.
The weight tables themselves do not select a priority. The later matching-wish
priority proposal below records the subsequent decision separately.

The coupled daily balance examples still use supplied actual successes. These
weights alone do not prove the frequency or mix of generated, pursued and
completed wishes, nor authorize a rebalance of need decay or friendship.
No new Python/JSON IDs, modules, persistent history owners or implementation
are selected here.

Documentation-only scope: only the master plan is staged; parallel local work
is preserved. Markdown whitespace/diff reviewed; no runtime tests, app windows,
mouse control, live-save access or CI.


### Proposed priority among matching wishes

**Discussion proposal recorded at the owner's request, 2026-10-23.** Resolve
simultaneously matching positive goals deterministically rather than randomly.
This governs assigning actual activity evidence, not the independent weighted
creation of wishes or the known treatment of expressly unwanted food.

| Priority | Proposed selection rule |
| --- | --- |
| 1 | A matching pinned wish takes precedence |
| 2 | Prefer a more specific matching objective/target over a flexible alternative |
| 3 | Among otherwise equal candidates, prefer an already-started objective with actual saved progress |
| 4 | Otherwise prefer the oldest matching wish; retain stable identity order for equal creation timestamps |

Examples: an unpinned concrete Blackjack play wish outranks unpinned free-choice
play. Pinning the free-choice goal gives it precedence instead. Among equally
specific goals, actual existing progress wins over an unstarted alternative.
Pinning changes pursuit priority as well as protection; it does not create an
extra completion or physical care effect.

Assign the wish before the outcome: at round start, social-sequence admission,
or the actual handover/petting boundary. Preserve that assignment through the
existing action/round identity. A lost round cannot be retrospectively reassigned
to an easier play objective. For an unidentified personally handed-over item,
retain the handover's original wish context until recognition permits a matching
judgment; do not infer unknown food identity or choose from later-created wishes.

One actual event advances at most one wish and fulfills at most one wish. Other
matching goals remain active without receiving that same progress or completion.
A multi-round goal therefore receives only its assigned real round receipts,
not duplicated progress from another wish's attempt. Actual accepted care and
its need changes remain independent from this one-wish emotional accounting.
If the selected attempt does not meet its goal, apply that goal's own previously
agreed progress/failure rule, without fallback completion of another wish.

Expressly unwanted personal food remains a separate negative treatment event.
Do not suppress Essenswunsch missachtet merely because a flexible positive goal
could also match the activity. Preserve its explicit avoidance snapshot and
failed-wish handling; priority is not a way to convert an unwanted handover into
a positive reward. No positive or negative technical receipt may be applied twice.

Next discuss positive Moodlet remaining times on renewed ascent and on stronger
two-tier outcomes. The 60/45/45 base, ten-minute-per-tier level-3 extension and
ninety-minute-per-tier cap are already the proposed baseline; treatment of
partially consumed/extended lower tiers and ascent overflow remains open.
Food's one-tier timing and negative family decay policies remain separate.

Documentation-only scope: only this master plan is staged; parallel local work
is preserved. Markdown whitespace/diff reviewed; no runtime tests, app windows,
pointer automation, live-save access or CI. No implementation is authorized.


### Proposed ascent budgets and two-tier wish outcomes

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** Apply this to positive multi-tier wish families only. Food's
single-tier policy and negative family timing remain separate.

#### Ascent and remaining budgets

On an actual qualifying ascent, replenish each remaining tier up to at least
its base duration, preserving any longer actual remaining duration:

- Level 1: sixty minutes.
- Level 2: forty-five minutes.
- Level 3: forty-five minutes.

For every tier through the newly reached intensity, the proposed rule is
`new_remaining = min(90 minutes, max(old_remaining, base_duration))`, treating
a genuinely new or fully spent upper tier as zero before this update. Keep
longer residuals rather than resetting them down to base; do not reset every
tier to its ninety-minute ceiling. Previously spent extension time is not
separately credited again. Passive decay still spends the current tier, then
uses the actual stored remaining duration of the next lower tier.

Example: active level 2 has fifteen minutes remaining and level 1 has seventy.
A one-tier success returns the family to level 3 with 45/45/70 minutes remaining
in order 3/2/1. This rewards renewed activity while preserving the lower tier's
longer residual, without inventing another event or restoring a full maximum.

#### Stronger outcomes and overflow

| Before a two-tier fulfillment | Proposed result |
| --- | --- |
| No active family | Start at level 2: 45 minutes at level 2 plus 60 at level 1 |
| Level 1 | Ascend to level 3 using the same base-floor / longer-residual rule |
| Level 2 | Ascend to level 3; discard excess intensity rather than adding another time bonus |
| Already level 3 | Same renewal as an ordinary fulfillment: add ten minutes per remaining tier, each capped at ninety |

A fulfillment causes either an ascent or renewal at an already reached level 3,
not both. One-tier outcomes use the same ascent rule for their actual increase.
There is no double application of an intermediate tier or overflow gift.
Maximum remaining duration stays 270 minutes across the three tiers.

A two-tier fulfillment is one actual experience and stores one concrete cause.
Intensity is not a receipt count: keep up to one/two/three available real causes
at current intensity, without duplicating a stronger event to fill every row.
This explicitly resolves that earlier strength-versus-cause-count conflict as
a proposal. No discarded past event is reconstructed.

The prior conditional daily examples use this base-floor ascent sequence;
recording it does not establish generated-wish availability or a runtime test
pass. Persist actual tier budgets through the existing aggregate/checkpoint/
codec owners when implementation is later authorized.

Next discuss the scope and qualified triggers for positive emotional experiences
without a pre-existing wish. No additional family, spontaneous trigger, strength,
cooldown or duplicate-reward exception is selected by this amendment.

Documentation-only check: only the master plan is staged; parallel local work
is preserved. Markdown whitespace/diff reviewed; no runtime tests, app windows,
mouse control, live-save access or CI.


### Proposed positive experiences without a prior wish

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** Permit four qualified positive experiences without requiring a
pre-existing matching wish. Use existing families and precise real cause facts.

| Actual experience | Proposed qualifying condition | Existing positive family |
| --- | --- | --- |
| Playing together again | After at least two hours without play, complete a session with at least two actual rounds | Gemeinsame Spielfreude / `shared_play` |
| Overcoming a losing streak | After two consecutive defeats in the same game, Aiko actually wins | Stolz / `pride` |
| Time to talk again | After at least four hours without a completed conversation/entertainment sequence, finish a full such sequence | Verbundenheit / `connection` |
| Welcome closeness | After at least four hours without petting, actually receive welcome petting | Geborgen / `secure` |

Each qualifies one intensity level in its existing family, using the proposed
60/45/45 base, ascent floors and capped level-3 renewal. Full/empty need values
alone are not emotional events. Petting willingness/friendship and other
ordinary action admission still apply. Merely opening a game, incomplete social
playback or refused petting does not provide the required event.

The two/four-hour gaps refer to actual activities, not to how long ago a Moodlet
was last awarded. Record actual completed activity even when its positive
outcome is already accounted for by a wish. Do not turn technical notifications
or repeated callbacks into another episode, chance or time credit.

If the exact same event already grants a wish fulfillment Moodlet, use that
wish outcome instead of granting a second positive everyday outcome. Existing
other positive/negative episodes may coexist. The no-double-reward rule is per
actual event: a comeback on a first round can be distinct from a shared-play
wish completed by a subsequent second round. Retain distinct semantic receipts,
not multiple labels for one physical event.

### Additional effect on the coupled daily examples

**Independent conditional discussion arithmetic, not runtime acceptance.** The
same worksheet retains current need/food/care formulas, light-office assumptions,
07:00/13:00/19:00/22:30 care, eight-hour sleep and proposed 60/45/45 timing. No
application imports or tests are run. Physical care, action counts and supplied
wish-success schedules are unchanged: twelve successes in the average case,
thirty-six in the intensive case. The actual weighted wish generator remains
outside the worksheet.

Shared-play and social return events already complete wishes in these examples,
so their everyday positives add nothing on those exact receipts. Four ordinary
welcome strokes are not wish completions. Strokes at 07:00/13:00/19:00 qualify
for Geborgen; 22:30 does not because only 3.5 hours have elapsed since the last
stroke. This adds three level-1 sixty-minute impressions, not four extra wishes.

| Same conditional daily schedule | Average: start 70 to next morning | Intensive: start 90 to next morning |
| --- | --- | --- |
| Before the four everyday triggers | 69.98 | 90.84 |
| Add the three qualified closeness events | 70.51 | 91.21 |
| Also assume one actual qualifying comeback win that does not itself fulfill a wish | 70.67 | 91.34 |

With closeness alone and the same repeating physical day, average friendship
settles around 71.7–73.8 (level 8); intensive remains around 96–100 (level 10).
With the illustrative one-comeback-per-day outcome pattern, average settles
around 72.3–74.4; intensive still around 96–100. Average care starting at 90
ends around 84.60 with closeness / 84.70 with the extra comeback, so this
ordinary schedule still does not maintain level 10.

For that optional comeback example, set the first two morning RPS rounds to
Aiko losses and a later session's first round to a win (13:00 average / 07:10
intensive). That first round supplies the comeback; a separate second round
completes the shared-play wish. Other outcomes do not create another losing
streak. This is an explicit conditional outcome pattern, not an assumed win
rate or a claim that every game session grants Stolz.

Mean numeric mood changes from about 65.03 to 65.67 in the average example.
The intensive example stays near 73.95 because its existing global numeric-mood
cap and timed recovery already absorb the extra contribution at those times.
Active tiers still contribute to friendship independently of that numeric cap.
Needs, nutrition, play costs and the existing three intensive energy drinks are
unchanged; no additional care is invented to produce these extra feelings.

The additional triggers shift ordinary care toward level 8 without making its
reference day maintain level 10. Actual random wish mixes and win/loss patterns
can still change the outcome; no further decay/friendship adjustment is selected
from this conditional arithmetic. Preserve integrated acceptance as later work.

Documentation-only check: only this master plan is staged; concurrent work and
existing commits are preserved. Markdown whitespace/diff reviewed; no runtime
tests, application windows, mouse control, live-save access or CI in this pass.


### Agreed wish refresh on wake and return

**Planning decision recorded at the owner's request, 2026-10-23; no runtime
implementation.** Use the shared ten-minute wish refresh schedule. On waking
or reopening the application, perform one refresh if that schedule is due;
otherwise retain the current wishes until the next regular refresh. Do not
replay missed rotations or generate a backlog of offline wishes or events.

At that refresh, retain pinned wishes with their identities, goals and progress,
replace unpinned wishes and fill available slots back to three. Pin protection
continues through sleep, standby and application closure. Unpinning returns a
wish to normal rotation: it remains until the next regular refresh rather than
being removed immediately because of an obsolete four-hour deadline. Existing
fulfillment and explicit dismissal rules still apply.

Left-click pins; right-click on a pinned wish only unpins; a further right-click
on the now unpinned wish dismisses it. Keep scheduling and eligibility in the
existing pet/domain owners and persistence on the shared elapsed-time axis;
add no UI timer or separate offline wish engine. Preserve the previously
promised migration of existing saved game objectives and progress.

This resolves the return/unpin policy in the remaining-decisions register above.
Next discuss positive completion and relative form weights for food avoidance
and variety. Recognized handover of explicitly unwanted food already has its
separate negative outcome; no positive alternative-food rule or food-form
weight is selected by this amendment.

Documentation-only scope: only this master plan changes. No Python/JSON changes,
runtime tests, application windows, pointer automation, live-save access or CI.


### Agreed shared food-avoidance / variety wish and 70:30 selection

**Planning decision recorded at the owner's request, 2026-10-23; no runtime
implementation.** Treat food avoidance and food variety as one semantic wish
form, for example "Something other than donut, please." Actual repeated-food
experience supplies the explicitly excluded food. Do not create two simultaneous
equivalent objectives merely by wording one as avoidance and one as variety.

Within the food area, use these relative form weights:

| Eligible food form | Relative weight |
| --- | --- |
| Request a particular food | 70 |
| Request something other than the explicitly excluded repetitive food | 30 |

The variety form requires actual qualifying repeated-food evidence. Without
that evidence, select from concrete-food requests. Choose the area first using
the agreed need-based area weights, then its eligible form, then the target;
70:30 does not mean seventy/thirty percent of all wishes. Full satiety does not
by itself exclude either form under the previously agreed full-need rules.

#### Recognized personal handover determines the wish outcome

| Actual personal handover | Outcome |
| --- | --- |
| An alternative food is handed over and recognized | Fulfill the shared avoidance/variety wish and award Genau das Gewuenschte / `food_fulfilled` |
| The explicitly excluded food is handed over and recognized | Fail the wish and apply Essenswunsch missachtet, even if the item is put down uneaten |
| The food is not yet identified | Wait for identification and retain the wish context from the original handover |

Actual eating is not required for the positive handover outcome. Subsequent
consumption and nutrition remain separate and must not award the same wish
again. Preserve one assigned wish/outcome per actual event and the agreed
specificity/pin/progress priority. Mere cursor presentation, desktop placement
or autonomous intake does not substitute for the personal handover.

Use the existing single-tier positive food family: +5 for sixty minutes;
another qualified fulfillment adds ten minutes of remaining duration, capped
at ninety. No instantaneous friendship bonus is added. Ordinary nonmatching
food offers are not explicit rejection violations: the negative outcome needs
the saved excluded-food goal. Its previously agreed negative tiers/timing stay
unchanged. This decision supersedes the earlier alternate-food-intake proposal
and the historical positive award for handing over the excluded food.

### Implementation readiness after the food-form decision

The return/unpin rule and the positive food-form outcome/weights close the two
remaining product decisions identified in the latest review. The agreed design
is sufficiently specified to begin implementation when separately authorized.
This records readiness, not runtime delivery or acceptance of the current code.
Earlier chronological "next discuss" passages are superseded by their later
specific decisions; do not reopen settled rules as new blockers.

Use the following small delivery slices, with separate commits within a slice
where catalogue, storage or interaction areas can be reviewed independently:

1. Typed goal/Moodlet definitions and JSON catalogues, including flexible goals
   and the negative food-wish family; validate catalogue contracts.
2. State and existing codecs: multiple wishes per area, refresh scheduling,
   per-tier remaining budgets and bounded activity/cause evidence. Preserve
   original saved game goals/progress and real causes; verify old-save reads,
   round trips and whole-Pet checkpoint restoration.
3. Pure Moodlet progression: positive ascent budgets, two-tier outcomes,
   capped renewals and single-tier food timing; preserve negative-family rules.
4. Wish eligibility, area/form weights, three-slot rotation, return refresh and
   pin/unpin lifecycle; check deterministic selection and elapsed boundaries.
5. Shared matching/assignment and game/social completion, in separate commits:
   bind the selected wish before the outcome and prevent duplicate progress.
6. Food and affection integration, in separate commits: recognized handover,
   full-need wish permission, explicit refusal and independent actual nutrition.
7. The four qualified positive experiences without wishes and concrete causes
   for negative/poor-care producers; keep bounded real evidence and prevent
   duplicate emotional outcomes for the same event.
8. Passive status/hover reads, then integrated generated-wish/day-balance
   acceptance, the complete local suite, final OOP review and investigation of
   tests exceeding ten seconds. Use targeted local checks during earlier slices.

Keep Pet/domain state and rules, application interaction coordination,
infrastructure persistence and UI projections with their existing owners.
Exact migration mechanics and helper boundaries are engineering work within
these owners, not reasons to create another history/reward engine or reopen
product decisions. Old saves must not invent past qualifying experiences.

The coupled day worksheets use supplied successes. Validate the actual weighted
generator and interaction availability before claiming that average care reaches
levels 7-8 and intensive care can maintain level 10. Need decay and friendship
rates remain unchanged unless later evidence warrants a separate decision.

Documentation-only scope: only this master plan is changed and committed here.
Parallel documentation work is preserved. No Python/JSON changes, runtime tests,
application windows, mouse control, live-save access or CI in this pass.


### Scope extension: longer-term emotional impressions and overall feelings

The owner subsequently added longer-term psychological impressions derived
from repeated care/interaction patterns, plus a review of the overall emotional
labels and their composition rules. The implementation-readiness statement
above applies to the previously discussed wish/experience changes only; it does
not settle this additional scope. Define these new impressions before extending
the delivery plan. They remain Moodlets within the existing Pet aggregate,
not random awards, another personality score or a second relationship store.

### Proposed longer-term Moodlet: Vertrauensvoll

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** Meaning: "I can rely on you." Derive this impression from
reliable care and respectful personal experiences over time. Friendship level
or full needs alone do not qualify it, and it does not require a prior wish.

#### Qualifying twenty-four-hour period

All of the following must hold for a qualifying period of twenty-four real
elapsed hours:

| Evidence | Proposed qualification |
| --- | --- |
| Distributed positive contact | At least three positive personal encounters, each separated from the next by at least two hours, with at least eight hours between the first and last |
| Different shared experiences | At least two interaction kinds across those encounters: a completed conversation/entertainment sequence, actual shared play, welcome petting or a positively received personal food handover |
| Sufficient care | No individual need spends a total of two hours below twenty-five, or one hour at zero, within the period |
| Respectful treatment | No confirmed disregard of an explicitly communicated boundary during the period |

Several actions in one encounter are not separate encounters: repeated strokes
cannot manufacture distributed contact. A food handover counts as positive
contact only when actually received positively. Use the existing poor-care
threshold meanings; normal need fluctuations and normal eight-hour sleep are
compatible with qualification. Available items can support care while absent,
but application closure does not create fictional personal encounters.

Account for each qualifying period once. The same care day must not increase
intensity at every recalculation; subsequent increases require another actual
qualifying twenty-four-hour period. Do not fabricate prior qualifying periods
when loading a save without the required evidence.

#### Strength, stacking and decay

| Intensity | Qualified buildup | Numeric mood-target contribution |
| --- | --- | --- |
| Level 1 | First qualifying twenty-four-hour period | +5 |
| Level 2 | Another qualifying twenty-four-hour period | +10 |
| Level 3 | A third qualifying twenty-four-hour period | +15 |

Keep one active episode with three intensity levels. Use current emotional
intensity one/two/three in the overall feeling composition; numeric mood still
follows existing caps and timed response. Active intensity participates in the
existing continuous friendship balance, without an additional instant bonus.
Trust does not override current petting refusal, personal boundaries or ordinary
action admission. Its precise direction/overall-label mapping belongs to the
upcoming emotional-composition discussion.

Each stage lasts thirty-six real hours. Without a fresh qualifying period,
level three falls to two after thirty-six hours, then to one after another
thirty-six hours, then expires after another thirty-six. A new qualified period
raises intensity by one, capped at three, and starts that current stage's
thirty-six hours. At level three it renews only the current thirty-six hours.
Do not accumulate additional duration or apply the wish-fulfillment 60/45/45
ascent/extension policy to this longer-term family.

Elapsed time includes standby and application closure. A nonqualifying care
period provides no reinforcement; it does not instantly erase existing trust.
Negative impressions can coexist and outweigh it in the present overall mood.
The proposed three-day buildup can therefore have a multi-day after-effect.

Presentation example: "Vertrauensvoll - Stufe 2: Bei dir fuehle ich mich sicher."
Retain the actual qualifying-period cause through the existing bounded Moodlet
evidence owners, without exposing the care formula in player-facing wording or
adding a permanent event archive. Distinguish it from Geborgen: that existing
family describes an immediate welcome-closeness experience; Vertrauensvoll
describes longer-term reliability.

Before accepting balance, recalculate the average/intensive day examples with
this additional long-lived positive contribution. The earlier day worksheets
do not include it and do not establish that its strength preserves the desired
level-seven/eight versus level-ten distinction.

Next discuss Wertgeschaetzt: qualifying experiences, strength, stacking and
decay. Its concrete thresholds and the other longer-term families/overall-label
extensions remain discussion work, not approved catalogue/runtime additions.

Documentation-only scope: only this master plan is changed and committed here.
Parallel runtime, tests, text and documentation changes are preserved. No runtime
tests, application windows, mouse control, live-save access or CI in this pass.


### Proposed longer-term Moodlet: Wertgeschaetzt

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** Meaning: "What I want matters to you." Derive this impression
from repeated personal attention to Aiko's wishes. Distinguish it from
Vertrauensvoll, which represents longer-term reliability of care and treatment.

#### Qualifying twenty-four-hour period

All of the following must hold within a period of twenty-four real elapsed hours:

| Evidence | Proposed qualification |
| --- | --- |
| Wishes considered | At least three actually fulfilled wishes |
| Different kinds of attention | Fulfilled wishes from at least two areas: food, games, social or affection |
| Distributed attention | Fulfillments in at least two encounters separated by at least two hours |
| Boundaries respected | No confirmed disregard of an explicitly communicated boundary during the period |

Both inner and expressed wishes count. A wish at an already full need counts
when the interaction is welcome and actually fulfills that wish. A fair game
defeat is not a boundary violation. Pinning, viewing, expressing, expiring or
dismissing a wish does not count as fulfillment.

Individual fulfillments still produce their own short-term impressions.
Wertgeschaetzt qualifies once from the whole longer-term pattern; it is not an
additional immediate award on every wish completion. Account for each period
once, requiring another actual qualifying twenty-four-hour period for another
increase. Re-reading a window or replaying a completion callback cannot award
another level.

#### Strength, stacking and decay

| Intensity | Qualified buildup | Numeric mood-target contribution |
| --- | --- | --- |
| Level 1 | First qualifying twenty-four-hour period | +5 |
| Level 2 | Another qualifying twenty-four-hour period | +10 |
| Level 3 | A third qualifying twenty-four-hour period | +15 |

Keep one active episode with a maximum of three intensity levels. It supports
warmth toward the user in the emotional composition; its exact overall-label
mapping remains part of the later composition review. Use emotional intensity
one/two/three and existing numeric caps/response timing. Active intensity affects
friendship through the normal continuous balance, with no extra instant bonus.

Each stage lasts thirty real hours. Without reinforcement, lose one level after
each thirty hours until the episode expires. A new qualifying period raises
intensity by one, capped at three, and starts the current stage's thirty hours.
At level three, renew only the current thirty hours. Do not bank further time
or apply the positive wish-family 60/45/45 renewal policy to this family.
Application closure and standby count toward decay.

A period without sufficient confirmation does not instantly erase the feeling;
it simply provides no reinforcement. Negative impressions can coexist. Existing
boundaries and action admission remain in force even while feeling appreciated.
Retain the qualifying-period cause with the existing bounded Moodlet evidence,
not in a second permanent wish or relationship archive.

Presentation example: "Wertgeschaetzt - Stufe 2: Es tut gut, dass meine Wuensche
bei dir zaehlen." Keep player-facing wording about the feeling, rather than
the numeric qualification formula.

Recalculate the daily friendship examples with Wertgeschaetzt and Vertrauensvoll
together before accepting their proposed strength. The prior day worksheets
include neither longer-term family; do not claim their old level-seven/eight
versus level-ten result remains established after these additions.

Next discuss Zuversichtlich: qualifying experiences, strength, stacking and
decay. Its thresholds and the remaining longer-term/overall-state additions are
not selected by this documentation amendment.

Documentation-only scope: only this master plan is changed and committed here.
Parallel runtime, tests, text and documentation changes are preserved. No runtime
tests, application windows, mouse control, live-save access or CI in this pass.


### Proposed longer-term Moodlet: Zuversichtlich

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** Meaning: "Good things can happen, even when something goes
wrong along the way." Derive it from repeated pleasant shared experiences and
actual success. Distinguish it from Stolz, the immediate impression of a
particular achievement. A previous setback is not required.

#### Qualifying twenty-four-hour period

All of the following must hold within twenty-four real elapsed hours:

| Evidence | Proposed qualification |
| --- | --- |
| Positive shared experiences | At least three actually pleasant activities |
| Different experiences | Activities in at least two areas: games, social, affection or personal food handover |
| Distributed experience | At least two encounters separated by at least two hours |
| Something succeeds | At least one own success: a won game round or an actually fulfilled game goal |

Pleasant activities include two completed rounds of actual shared play, a full
conversation/entertainment sequence, welcome petting or a positively received
personal food handover. Count each activity kind at most once per encounter;
repeated clicks or several consecutive strokes cannot manufacture multiple
qualifying experiences. A success may belong to one of these activities; it
does not by itself count the same activity twice.

Do not require a prior defeat or encourage deliberately creating setbacks.
Later actual success and pleasant encounters after defeats can qualify the
same rule. Individual losses or active negative impressions do not automatically
exclude optimism. Only real activity qualifies; no offline successes or positive
encounters are invented. Existing action admission and willingness still apply.

#### Strength, stacking and decay

| Intensity | Qualified buildup | Numeric mood-target contribution |
| --- | --- | --- |
| Level 1 | First qualifying twenty-four-hour period | +5 |
| Level 2 | Another qualifying twenty-four-hour period | +10 |
| Level 3 | A third qualifying twenty-four-hour period | +15 |

Keep one active episode with at most three levels. Each period is accounted
for once; another increase requires another actual qualifying twenty-four-hour
period. Do not turn repeated window reads or completion callbacks into extra
reinforcement. Individual short-term impressions remain independent: the
longer-term qualification is one evaluation of the overall period pattern.

Use current emotional intensity one/two/three and existing numeric mood caps
and response timing. Active intensity participates in the normal continuous
friendship balance, with no additional instant bonus. Its precise emotional
direction and overall-label mapping remain part of the later composition review.

Each stage lasts thirty real hours. Without new confirmation, lose one level
after each thirty hours until expiry. A qualifying period raises intensity by
one, capped at three, and starts the current stage's thirty hours. At level
three renew only the current thirty hours. Bank no additional duration and do
not apply the positive wish-family 60/45/45 extension policy. Standby and
application closure count toward decay.

A later defeat does not instantly remove optimism. Aiko may be disappointed
about a particular round while still feeling broadly optimistic. Preserve the
real qualifying-period cause within existing bounded Pet/Moodlet evidence;
do not introduce another score or permanent game-history owner.

Presentation example: "Zuversichtlich - Stufe 2: Ich glaube, da kommen noch
schoene Sachen auf uns zu." The player-facing description communicates the
feeling rather than the underlying counters.

Before accepting balance, evaluate all three proposed longer-term positive
families together. Their contributions can accumulate; the earlier daily
worksheets do not establish the friendship targets after these additions.

Next discuss Verunsichert: qualifying patterns, strength, stacking and decay.
Its thresholds and the remaining longer-term/overall-state additions are not
selected by this documentation amendment.

Documentation-only scope: only this master plan is changed and committed here.
Parallel runtime, tests, text and documentation changes are preserved. No runtime
tests, application windows, mouse control, live-save access or CI in this pass.


### Proposed longer-term Moodlet: Verunsichert

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** Meaning: "I am not sure where I stand with you." Derive this
impression from repeated inconsistent treatment: pleasant personal attention
followed by actual disregard of boundaries or qualified upsetting treatment.
One bad moment alone does not establish the longer-term pattern.

#### Qualifying twenty-four-hour pattern

All of the following must hold within twenty-four real elapsed hours:

| Evidence | Proposed qualification |
| --- | --- |
| Positive encounters | At least two actually pleasant personal encounters |
| Repeated negative experience | Each of those encounters is followed by a confirmed boundary violation or a qualified upsetting interaction |
| Distributed incidents | The two negative incidents are at least two hours apart |
| Independent incidents | Two separate situations; escalation messages from one incident count only once |

Example: shared play in the morning followed by continued poking despite a
clear request to stop; welcome petting later followed by repeated withholding
of a requested object. Qualified negative evidence can use the already defined
repeated-poking, communicated petting-boundary, withholding and expressly
unwanted-food-handover events. Use the real semantic incidents, not callback,
speech or timer counts, and do not reuse one incident as both negative cases.

A fair game defeat, ordinary absence or an isolated click does not qualify as
negative treatment for this pattern. Positive attention alone does not create
uncertainty: the repeated subsequent negative incidents are required. Application
closure does not fabricate personal encounters or boundary violations.

#### Strength, stacking and decay

| Intensity | Qualified buildup | Numeric mood-target contribution |
| --- | --- | --- |
| Level 1 | First qualifying twenty-four-hour period | -5 |
| Level 2 | Another qualifying twenty-four-hour period | -10 |
| Level 3 | A third qualifying twenty-four-hour period | -15 |

Keep one active episode with a maximum of three levels. Account for each
period once; old incidents cannot provide further levels through repeated
window reads. The immediate upsetting-interaction Moodlets remain independent:
Verunsichert represents their longer-term inconsistent relationship pattern.

Its emotional influence supports cautious, reserved or tense reactions; exact
direction/overall-label mapping belongs to the upcoming composition discussion.
Use current intensity one/two/three, normal numeric caps and timed mood response,
and the existing continuous friendship balance. Add no separate instant
friendship deduction and no new blanket interaction lock.

Each stage lasts thirty real hours. Without another qualifying pattern, lose
one level after each thirty hours until expiry. A new qualifying period raises
intensity by one, capped at three, and starts the current stage's thirty hours.
At level three renew only the current thirty hours; do not bank extra duration
or apply the positive wish-family extension policy. Standby and application
closure count toward decay.

A friendly action does not instantly remove uncertainty. It may create its
own positive impression and contribute to a future reliable-care pattern.
Positive and negative long/shorter-term impressions may coexist. Keep the real
qualifying-period cause in existing bounded Moodlet evidence, without creating
another permanent interaction or relationship archive.

Presentation example: "Verunsichert - Stufe 2: Manchmal bist du so lieb ... und
dann verstehe ich dich wieder nicht." Describe the feeling rather than exposing
the qualification formula.

Include this additional long-lived negative family in the later joint daily
balance review. The prior worksheets do not include the new longer-term scope.
Next discuss Uebersehen: qualification, strength, stacking and decay, with a
clear distinction from the existing need-based loneliness after-effect.

Documentation-only scope: only this master plan is changed and committed here.
Parallel runtime, tests, text and documentation changes are preserved. No runtime
tests, application windows, mouse control, live-save access or CI in this pass.


### Proposed longer-term Moodlet: Uebersehen

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** Meaning: "I miss our shared moments." Represent longer-term
lack of personal attention, even when available objects maintain physical care.
Distinguish this from the existing loneliness after-effect, which qualifies
through prolonged unmet needs. Neither full needs nor poor needs alone decides
this personal-contact pattern.

#### Qualifying twenty-four-hour period

Both conditions must hold within twenty-four real elapsed hours:

| Evidence | Proposed qualification |
| --- | --- |
| Little personal attention | At most one shared encounter in the entire period |
| Long contact gap | At least eight hours without such an encounter while Aiko is awake |

A shared encounter can include a full conversation/entertainment sequence,
actual shared play with at least two rounds, welcome petting or a positively
received personal food handover. Several actions within one care visit remain
one encounter. Opening menus, placing food on the desktop or autonomous care
does not replace personal contact.

Sleep pauses accumulation of the eight-hour awake contact gap; it does not
erase already accumulated awake time. Four contactless awake hours before
sleep and four afterward therefore reach eight. An actual qualifying encounter
ends the gap. Standby/application closure may contain contactless awake time
according to Aiko's calculated sleep rhythm; do not invent personal encounters
or assume the owner was actively ignoring her.

Normal overnight absence alone does not qualify. Personal encounters in both
the morning and evening also fail the "at most one encounter" condition, so
this family does not automatically penalize that care pattern. This sleep rule
belongs to this Moodlet's qualification; it does not silently change existing
friendship absence rules.

#### Strength, stacking and decay

| Intensity | Qualified buildup | Numeric mood-target contribution |
| --- | --- | --- |
| Level 1 | First qualifying twenty-four-hour period | -5 |
| Level 2 | Another qualifying twenty-four-hour period | -10 |
| Level 3 | A third qualifying twenty-four-hour period | -15 |

Keep one active episode with at most three levels. Each period counts once;
already accounted contact gaps cannot create more levels through repeated
window evaluation. Use actual qualifying-period evidence and the existing
bounded Pet/Moodlet persistence owners, not a second neglect/history store.

Emotionally it supports loneliness and feeling downcast; its precise direction
and overall-label mapping remain part of the later composition review. Use
intensity one/two/three, existing numeric caps and timed mood response, and
normal continuous friendship effects. Add no extra instant friendship deduction.

Each stage lasts thirty real hours. Without another qualifying period, lose
one level after each thirty hours until expiry. A new qualifying period raises
intensity by one, capped at three, and starts the current stage's thirty hours.
At level three renew only the current thirty hours; bank no additional duration.
All real time, including sleep, standby and application closure, counts toward
decay. This differs deliberately from pausing the awake contact-gap accumulator.

A return with actual shared activity ends the contact gap and may create
positive impressions; it does not instantly erase the longer-term feeling.
Presentation example: "Uebersehen - Stufe 2: Ein bisschen gemeinsame Zeit mit
dir waere schoen." Describe the feeling without asserting deliberate rejection.

Review its additional effect jointly with existing loneliness and friendship
absence losses before accepting balance. The earlier daily worksheets do not
include this family. Next discuss Auf der Hut: qualifying incidents, strength,
stacking and decay, distinct from uncertainty after inconsistent treatment.

Documentation-only scope: only this master plan is changed and committed here.
Parallel runtime, tests, text and documentation changes are preserved. No runtime
tests, application windows, mouse control, live-save access or CI in this pass.


### Proposed longer-term Moodlet: Auf der Hut

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** Meaning: "I am cautious because my boundaries have repeatedly
not been respected." Distinguish it from Verunsichert, which requires a pattern
of inconsistent pleasant/upsetting treatment. Repeated upsetting interactions
can qualify Auf der Hut without friendly encounters in between.

#### Qualifying twenty-four-hour period

All of the following must hold within twenty-four real elapsed hours:

| Evidence | Proposed qualification |
| --- | --- |
| Repeated upsetting treatment | At least three independent qualified upsetting-interaction or boundary-violation incidents |
| Distributed incidents | At least four hours between the first and last incident |
| Actual interaction evidence | Real user actions meeting the already defined negative-experience rules |

Examples include repeated poking that qualifies as an upsetting experience,
continued petting despite an explicitly communicated boundary, or escalated
withholding of a requested object. The same kind may recur in separate incidents.
One continuous incident counts once: escalation levels during a single prolonged
withholding episode do not become three independent incidents. Nor do repeated
technical callbacks or speech updates supply new evidence.

Isolated clicks, fair game defeats and ordinary absence do not qualify. Do not
infer another user's intent or fabricate upsetting interactions during closure.
Use bounded real semantic evidence through existing Pet/Moodlet owners.

#### Strength, stacking and decay

| Intensity | Qualified buildup | Numeric mood-target contribution |
| --- | --- | --- |
| Level 1 | First qualifying twenty-four-hour period | -5 |
| Level 2 | Another qualifying twenty-four-hour period | -10 |
| Level 3 | A third qualifying twenty-four-hour period | -15 |

Keep one active episode with at most three levels. Account for each period
once; further levels require new incidents rather than reuse of old evidence.
Immediate upsetting-interaction impressions remain active independently.
Auf der Hut describes the longer-term cautious attitude toward the user.

Emotionally it supports reserved/tense reactions; its precise direction and
overall-label mapping remain part of the upcoming composition review. Use
intensity one/two/three, existing numeric caps and timed mood response, and the
normal continuous friendship balance. Add no extra instant deduction or new
blanket interaction lock. Specific refusals remain with their interaction rules.

Each stage lasts thirty-six real hours. Without another qualifying pattern,
lose one level after each thirty-six hours until expiry. A new qualifying
period raises intensity by one, capped at three, and starts the current stage's
thirty-six hours. At level three renew only the current thirty-six hours; bank
no extra duration and do not apply the positive wish-family extension policy.
Standby and application closure count toward decay.

A friendly action may create a positive impression but does not instantly erase
this longer-term caution. Positive longer-term episodes, including residual
Vertrauensvoll, can coexist. Keep the actual qualifying-period cause within
existing bounded episode evidence, without another permanent interaction log.
Presentation example: "Auf der Hut - Stufe 2: Ich moechte erst mal ein bisschen
vorsichtig sein."

Next review all six longer-term families together for overlap, overall-emotion
composition and combined friendship balance. Their per-family proposals do not
settle mutual exclusion, compound-state thresholds or the integrated balance.

Documentation-only scope: only this master plan is changed and committed here.
Parallel runtime, tests, text and documentation changes are preserved. No runtime
tests, application windows, mouse control, live-save access or CI in this pass.


### Agreed distinctions and overlap review for the six longer-term families

**Planning direction recorded at the owner's request, 2026-10-23; no runtime
implementation.** Retain the six distinct meanings below and allow concurrent
episodes, including residual opposing feelings. These distinctions do not settle
the combined strength or the upcoming overall-state selection thresholds.

| Longer-term family | Distinct meaning | Principal overlap |
| --- | --- | --- |
| Vertrauensvoll | I can rely on you | A good care day may also build appreciation and optimism |
| Wertgeschaetzt | My wishes matter | Wish successes can also be positive encounters supporting trust/optimism |
| Zuversichtlich | Good things can happen | Success and pleasant activities often occur on the same good days |
| Verunsichert | I do not know where I stand with you | Its negative incidents may also support a guarded attitude |
| Uebersehen | I miss shared moments | Can coexist with need-based loneliness and existing absence losses |
| Auf der Hut | I must be cautious about my boundaries | Repeated upsetting incidents can also occur within inconsistent treatment |

The same real experiences may contribute to different, independently qualifying
longer-term patterns. This is distinct from reusing already accounted evidence
to award another level of the same family. Do not count repeated evaluation,
callbacks or escalation messages as fresh incidents or qualifying periods.

Preserve the existing per-family qualification conditions. Vertrauensvoll and
Wertgeschaetzt require periods without confirmed boundary disregard, whereas
the inconsistent/guarded patterns require upsetting incidents. Some opposing
families therefore cannot newly qualify from the same period but can coexist
through residual lifetimes. Similar contact-count constraints distinguish
Uebersehen from families requiring several personal encounters. Do not add
blanket mutual exclusion or erase an episode merely because its opposite
appears. A previously trusting Aiko can now also feel cautious.

The current overall-state algorithm compares complete positive/negative
intensity totals, chooses the strongest direction of the winning side and uses
Zwiegespalten only for an exact nonzero tie. This retains all influences but
provides limited visible distinction for mixed feelings. Review that selection
explicitly rather than assuming six new catalogue entries will diversify it.

The previously discussed extension from thirteen to seventeen overall labels
remains a candidate for the next selection-rule discussion:

| Candidate additional overall state | Intended composition |
| --- | --- |
| Unbeschwert | Joy and safety with little emotional burden |
| Zuversichtlich | Actual success and longer-term positive expectation |
| Reserviert | Caution/uncertainty toward the user, possibly alongside warmth |
| Angespannt | Combined uncertainty, pressure, irritation or frustration |

An overall state is derived from the full composition. A same-named Moodlet is
one input, not an unconditional label override. Preserve actual reasons and
opposing influences for later expression without creating an independent
mutable emotion score or a new event store.

The three positive longer-term families at level three sum to a nominal +45
numeric contribution and nine positive emotional-intensity points. Existing
numeric caps limit mood contributions but do not truncate emotional composition
or eliminate their continuous friendship influence. Analogous negative overlaps
need joint review, including need-based loneliness and absence losses.

The earlier average/intensive daily worksheets do not establish balance after
these six additions. Define overall-state selection, including mixed feelings,
then jointly review their strength against the level-seven/eight versus level-ten
targets. This amendment changes neither contribution values nor friendship rates.

Documentation-only scope: only this master plan is changed and committed here.
Parallel documentation work is preserved. No runtime tests, application windows,
mouse control, live-save access or CI in this pass.


### Proposed overall-state selection including mixed feelings

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** Retain all active short/longer-term impressions in the
composition and derive one primary overall label. Other feelings remain
available for expression and independently defined interaction boundaries.
This proposal supersedes the earlier exact-tie-only mixed-state selection when
later implemented; it does not modify runtime emotion selection in this pass.

#### Complete intensity totals and mixed-feeling band

Each active Moodlet contributes its current intensity one/two/three once.
Longer-term families receive no additional multiplier: their persistence already
provides their sustained influence. Numeric mood points and emotional intensity
remain distinct, and numeric contribution caps do not truncate emotional inputs.

Let P be total positive intensity, N total negative intensity and T = P + N.
For T greater than zero:

| Composition | Primary selection branch |
| --- | --- |
| P is more than sixty percent of T | Positive side determines the main label |
| N is more than sixty percent of T | Negative side determines the main label |
| Each side is at least forty percent of T | Mixed overall feeling, including the exact forty/sixty boundaries |

For a mixed composition, choose Reserviert when caution/uncertainty makes up at
least half of the negative intensity. Otherwise choose Zwiegespalten. Thus P=3,
N=2 is mixed, whereas P=5,N=1 has a positive primary label without deleting the
negative influence. The band replaces the exact equality requirement.

#### Dominant-side directions and qualified compound labels

Within a clearly dominant side, normally use its strongest combined direction.
The additional compounds below qualify within that side's branch:

| Overall state | Proposed compound qualification |
| --- | --- |
| Unbeschwert | Positive branch; joy and safety both present, together at least sixty percent of positive intensity; negative intensity at most twenty percent of T; numeric mood at least seventy |
| Zuversichtlich | Positive branch; positive expectation and pride both present, together at least sixty percent of positive intensity |
| Angespannt | Negative branch; uncertainty plus at least one direction among irritation, crowding and frustration, together at least sixty percent of negative intensity |

Use the contributing intensity only once in P/N/T. Evaluating a compound does
not add another Moodlet or another emotional contribution. Safety can come from
Vertrauensvoll or existing Geborgen; the same-named optimism Moodlet does not
unconditionally override the complete composition.

For a prevailing individual longer-term direction, use these mappings:

| Longer-term influence | Individual-direction label |
| --- | --- |
| Vertrauensvoll / Wertgeschaetzt | Zugewandt |
| Zuversichtlich | Zuversichtlich |
| Verunsichert | Angespannt |
| Uebersehen | Einsam |
| Auf der Hut | Reserviert |

Without a qualifying compound, retain the strongest-direction labels Froehlich,
Stolz, Erleichtert, Zugewandt, Gereizt, Bedraengt, Frustriert, Niedergeschlagen
and Einsam, together with the longer-term mappings above. Equal-ranked
directions prefer the most recently triggered cause, then the strongest
individual intensity, then stable declared order, as in the existing policy.

#### No-impression fallback and scope

If T is zero, retain the existing numeric-mood fallback:

| Numeric mood | Overall state |
| --- | --- |
| Below forty | Gedrueckt |
| Forty to below seventy | Gelassen |
| Seventy or above | Zufrieden |

This retains seventeen overall labels including the four additions Unbeschwert,
Zuversichtlich, Reserviert and Angespannt. A reserved Aiko can still enjoy play;
a warm Aiko can retain irritation. The primary label does not erase other
influences, create another friendship effect or impose new interaction locks.
Keep the full composition derived through existing Pet/domain and read-model
owners, not as an independently mutable emotion store.

Next calculate the six longer-term families' combined effects on numeric mood
and progressive friendship using existing caps, rates and response timing.
Their proposed strengths and the overall daily balance remain subject to that
joint review. Recording these selection rules does not select a new rate.

Documentation-only scope: only this master plan is changed and committed here.
Parallel runtime, text and documentation work is preserved. No runtime tests,
application windows, mouse control, live-save access or CI in this pass.


### Proposed joint mood limits and friendship rates for longer-term Moodlets

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** Apply the following shared policy to Vertrauensvoll,
Wertgeschaetzt, Zuversichtlich, Verunsichert, Uebersehen and Auf der Hut. This
supersedes using ordinary short-term Moodlet friendship rates for these six
families and adds limits to their previously proposed numeric contributions.

| Joint policy for the six longer-term families | Proposed value |
| --- | --- |
| Combined positive numeric mood contribution | At most +5 points |
| Combined negative numeric mood contribution | At most -10 points |
| Positive friendship contribution per intensity level per thirty seconds | +0.00005 |
| Negative friendship contribution per intensity level per thirty seconds | -0.00010 |

Sum their nominal positive/negative mood contributions separately, apply the
respective longer-term limits, then combine with other Moodlet contributions
under the existing global positive/negative caps and final need-deficit limits.
Do not net opposing longer-term feelings before applying these separate limits.
Keep normal timed mood recovery/decline; no instantaneous jump on qualification.

The six families retain their proposed one/two/three emotional intensities,
nominal per-family mood values, qualification patterns, causes, stage durations
and reinforcement rules. The shared cap limits their contribution to the mood
bar; it does not remove episodes or reduce their full emotional influence in
the proposed overall-state selection. Stronger levels still have stronger
continuous friendship influence within the smaller rate schedule.

Use the new friendship rates instead of, not in addition to, the current
+0.003/-0.006 short-term rates. They are one sixtieth of those rates. Continue
to apply existing progressive gain/loss factors, mood-based friendship flow,
absence and neglect rules. Add no instant bonus/deduction and no friendship
effect for the selected emotional label. Do not change short-term wish/negative
experience rates, need decay, care gains or sleep behavior in this amendment.

At maximum intensity in all three positive families, the longer-term direct
raw gain is 1.296 points per twenty-four hours. For all three negative families
at maximum intensity the arithmetic raw loss is 2.592 points per twenty-four
hours. These are contribution bounds before progressive factors, not promised
net daily balances or a claim that all opposing patterns freshly qualify together.

#### Conditional balance comparison

Independent arithmetic retained the earlier four-phase average/intensive care
schedules, eight-hour sleep, existing need/care formulas and supplied wish
successes. No application imports, runtime tests or actual random generator were
used. The following repeating-day comparisons assume all three positive
longer-term families are maintained at level three:

| Conditional comparison | Without longer-term families | With the proposed reduced policy |
| --- | --- | --- |
| Average care: repeating friendship range | 71.7-73.8 | 74.4-76.8 |
| Intensive care: repeating friendship range | 96-100 | 96.1-100 |
| Average care: mean numeric mood | 65.7 | 70.0 |
| Intensive care: mean numeric mood | 73.9 | 77.3 |

With average care starting at seventy, and each completed care day qualifying
the three positive patterns, the illustrative successive morning values are
70.5, 71.3, 72.1, 72.8 and 73.3. For a single good average-care day starting
at seventy with Auf der Hut already at level three and a full remaining stage,
the comparison ends near 69.6. Existing short-term impressions and absence
effects are included; no fresh bad treatment is assumed in that recovery day.

These conditional examples support average friendship level eight while
intensive care can maintain level ten. Preserve validation of generated wish
opportunities and real completion availability as later integrated acceptance;
the worksheet is not proof of the implemented distribution or runtime behavior.

### Readiness after the longer-term and overall-state extension

The six per-family proposals, overlap distinctions, seventeen-state selection
and reduced joint numeric/friendship policy now specify the added product scope
sufficiently for implementation planning. No further mandatory product decision
has been identified in this review. This is not an implementation authorization
or a claim that current runtime already follows the proposals.

Extend the existing eight delivery slices to include this scope: longer-term
catalogue/policy definitions in slice one; bounded qualification evidence and
compatible persistence in slice two; their independent stage clocks, numeric
subtotals and friendship rates in slice three; per-family pattern qualification
in slice seven, split into small reviewable commits; and full emotional
composition, passive status/hover reads and integrated acceptance in slice eight.
Keep wish lifecycle and interaction matching work in their existing slices.

During implementation, establish deterministic single-accounting of qualified
twenty-four-hour periods and semantic encounters/incidents on the shared elapsed
axis. Preserve actual saved wish goals, progress, stage budgets and causes.
Missing historical evidence is unknown; do not invent past qualifying periods
or interactions. These are engineering/verification obligations within the
existing Pet, application and infrastructure owners, not another history engine.

Use targeted local checks per small commit. At completion run the full local
suite, review OOP ownership and redundant tests, and investigate tests exceeding
ten seconds. No test windows, mouse control or GitHub CI. The actual wish mix,
joint long/shorter-term balance and old-save behavior remain acceptance work,
not additional hypothetical product-design scenarios to enumerate now.

Documentation-only scope: only this master plan is changed and committed here.
Parallel runtime, tests, text and documentation changes are preserved. No runtime
tests, application windows, mouse control, live-save access or CI in this pass.


### Agreed data and dialogue-source organization

**Planning direction recorded at the owner's request, 2026-10-23; no runtime
implementation.** Keep authored content/definitions as versioned JSON sources
and adopt SQLite as the planned persistence backend for personal state and
bounded history. Python continues to own domain rules and state transitions.
Design the shared data model before adding the next catalogue extensions.

#### Dialogue files follow their conversational purpose

Split the current monolithic dialogue source by topic/occasion, rather than
creating a separate catalogue for each overall emotional state. Suggested
organization under `aiko_pet/data/dialogues/de/`:

```text
social/
  chat.json
  wish_expression.json
  experience_reflections.json
care/
  food.json
  petting.json
  sleep.json
objects/
  discovery.json
  searching.json
games/
  blackjack.json
  rock_paper_scissors.json
```

This is the agreed organizing principle with illustrative file names, not a
new runtime layout already in use. Each sequence has one canonical location
and a stable ID. Its conditions determine the applicable friendship stage,
overall feeling, needs and concrete experience; its ordered beats retain the
complete text/emote sequence. Do not duplicate the same sequence in files for
every matching mood or combination of Moodlets.

The file answers "What is this conversation about?"; its conditions answer
"When does this wording fit?" Extend the typed dialogue context/conditions for
actual wishes, Moodlets and retained causes as needed. The current state/need
filters alone cannot identify a particular fulfilled Blackjack wish. Keep
unknown-object knowledge limits, placeholder validation and the single dialogue
selection owner intact. File splitting alone is not the semantic integration.

Plan an automatically generated readable view of occasion, conditions and full
bubble sequence, filterable by such facts as Reserviert or a Moodlet family.
Edit the canonical dialogue sources; do not maintain a second editable copy of
the same wording in the review view. Load/validate the sources through one
catalogue boundary and expose immutable content to consumers.

#### SQLite direction and stable model boundaries

The private database remains outside Git in the user's application-data folder.
Version schema/migration source with the application. First use creates the
database; an existing JSON save is backed up and imported once transactionally.
Updates migrate the user's database rather than replacing it with a fresh file.
There must be one active persistence owner, not permanent dual writing to JSON
and SQLite. Preserve the existing save-location override contract during design.

Model all already planned systems together before selecting the first SQLite
schema. Moodlet episodes share structures for instances, stage budgets and
bounded causes. Wishes share structures for instance identity, original goal,
target and progress. New supported families, sentences or objective variants
should normally be data additions within those structures, not new tables or
one column per Moodlet. Genuine new data relationships may still require a
versioned migration; do not promise a schema that can never evolve.

Stable IDs connect definitions to personal instances. Authored catalogues remain
the editable source of definitions; any derived database registry must have a
one-way source/update path, not a second content editor. Preserve original
wish/target facts in Moodlet causes after the active wish ends. Database
relations must not erase those causes when an active wish is removed.

#### Historical preparation order (superseded by the later delivery-order decision)

The later "Agreed delivery order: features before SQLite and final OOP work"
section supersedes the execution order in this historical proposal. The data
model remains agreed preparation; implementing SQLite is no longer a prerequisite
for the wish/Moodlet feature slices.

Add a data-model/persistence preparation step before the earlier slice one:
agree vocabulary, logical tables, relationships and retention; then implement
the SQLite adapter/migrations and legacy import, and reorganize dialogue sources
in small separately reviewable changes after explicit implementation approval.
Concrete table/column and adapter names remain the next discussion, not selected
by this organization amendment. Preserve existing domain owners and behavior;
do not move care, offline progression, wish matching or dialogue selection into
SQL. Subsequently continue the previously planned feature slices against that
foundation, with targeted local checks and the final suite/OOP/slow-test review.

The earlier readiness statement covers the agreed product behavior; the newly
added storage/source-organization scope still needs its concrete model review.
This amendment authorizes documentation only. Parallel runtime, tests, text and
documentation work is preserved. No runtime tests, application windows, mouse
control, live-save access, database creation/migration or CI in this pass.


### Proposed logical SQLite tables, relationships and owners

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** Use one private database per save. This is the logical model
for discussion, not executed DDL or a completed field-level schema contract.
Authored dialogue, definitions and balance remain versioned JSON sources.

| Proposed table group | Stored responsibility |
| --- | --- |
| `schema_migrations` | Applied structural migrations |
| `save_state` | Save revision, last UTC checkpoint and the shared elapsed-time axis |
| `pet_state`, `sleep_state` | Needs, mood, friendship, digestion reserve and current sleep state |
| `app_settings` | Behavior preferences and persisted window geometry |
| `world_state`, `world_objects` | Desktop surface, actual object instances, position, custody and lifecycle |
| `object_memories`, `object_memory_sources` | Subjective knowledge, remembered places and possible associations |
| `wish_state`, `wish_instances`, `wish_round_receipts` | Refresh schedule, active wishes, original goals, progress and bounded round evidence |
| `moodlet_state`, `moodlet_episodes`, `moodlet_stage_state`, `moodlet_causes` | Active impressions, stage budgets, consumed relief allowances and concrete causes |
| `interaction_state`, `food_intake_receipts` | Communicated boundaries, refusal deadlines and bounded repeated-food evidence |
| `relationship_state`, `relationship_entries`, `need_exposure_buckets` | Contact anchors, existing relationship budgets and deficient-need durations |
| `care_encounters`, `care_evidence`, `long_term_progress` | Bounded shared encounters, semantic evidence and already evaluated longer-term periods |
| `adaptive_state`, `adaptive_hour_slots` | Learned rhythm and existing aggregate hour-of-week evidence |
| `social_receipts`, `social_requests`, `provider_pauses` | Recent-content suppression and durable API request limits |

Before switching storage, include the parallel daily-horoscope persistence
contract, including daily status and continuation position. The table/field
details for that feature must follow its actual owning application contract;
this review does not alter or authorize the parallel implementation.

#### Instance relationships and lifetime boundaries

- A wish instance owns its bounded round receipts.
- A Moodlet episode owns its stage values and bounded causes. Ending the episode
  removes those dependent values; the existing one/two/three real-cause limit
  remains a domain obligation.
- Object memory may refer to an actually acquired World instance identity.
  Unknown or merely possible identity remains open; a database join must not
  grant subjective knowledge from World truth.
- Each longer-term family has its own progress/processing record using the
  shared evidence and elapsed axis, rather than an independent care history.
- A complete persisted session is captured under one save revision.

Use foreign keys for actual local instance relationships and enable their
enforcement on each database connection. Catalogue IDs in external JSON remain
validated through typed catalogue contracts; this proposal does not require a
second editable catalogue database. New families use existing instance tables,
not new tables/columns for each individual Moodlet or wish.

A cause's original wish identity is historical evidence, not a required live
foreign key into `wish_instances`. Preserve original target/objective/result
facts after the active wish retires. Deleting an active wish must not cascade
into the longer-lived cause. An unresolved food identification after personal
handover likewise needs a bounded receipt retaining the wish context from that
handover; exact fields/placement are part of the next detailed model review.

#### Domain ownership and transaction boundary

`PetState` and pure pet policies continue to calculate needs, friendship, wishes
and Moodlets. `WorldState` owns physical objects; `ObjectMemory` owns acquired
knowledge; application coordinators own semantic interaction assignment and
closed-time reconstruction. Existing settings/adaptive/social owners retain
their respective values. Tables do not become new independently mutable domain
objects, and one table does not require one new service/repository class.

The SQLite persistence adapter reads/writes a complete coherent snapshot behind
the existing session/save boundary. Commit related changes in one transaction;
UI widgets and the HTTP worker do not independently update individual tables.
Loading values does not run care or offline progression inside SQL.

The logical schema must preserve original goals, progress, stage budgets, relief
usage and bounded semantic receipts during JSON import. Keep wall-clock restart
anchors distinct from lived-time deadlines. A new content entry is normally a
data change; a genuinely new persisted relationship may require a migration.

Next discuss concrete fields, keys, optional values and retention for wish
instances, Moodlet causes and longer-term evidence. Those field-level choices
are not selected by recording this table model. Personal databases, source
JSON and parallel runtime changes are untouched by this documentation pass.

Documentation-only scope: only this master plan is changed and committed here.
No runtime tests, application windows, mouse control, live-save access, database
creation/migration or CI in this pass.


### Proposed fields for wishes, Moodlet causes and longer-term evidence

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** Separate active goals, resulting emotional memories and
bounded qualification evidence. Use shared elapsed seconds for domain times;
retain the restart UTC anchor separately. The following names/meanings describe
the field-level proposal, not executed SQL types or completed migration code.

#### Active wish instances

| Proposed `wish_instances` field | Meaning |
| --- | --- |
| `instance_id` | Stable wish identity, never reused |
| `definition_id`, `area` | Wish variant and domain area |
| `objective_id`, `required_count` | Original goal rule and quantity |
| `target_kind` | Food, game, social or affection target kind |
| `target_mode` | Concrete target, free choice or explicitly excluded target |
| `target_id` | Concrete/reference target; empty for free choice |
| `created_elapsed_seconds` | Actual creation time |
| `last_expressed_elapsed_seconds` | Actual last expression; empty means not yet expressed |
| `pinned` | Protection from regular rotation |
| `completed_rounds`, `wins`, `losses` | Actual game-goal progress |

The original objective, required count and target meaning are immutable after
creation. Catalogue changes do not rewrite a started wish. Concrete Blackjack,
any-game and other-than-Blackjack goals use these shared fields, not independent
tables. Preserve original legacy goals/progress through import.

The shared ten-minute due time belongs once in `wish_state`, rather than adding
another independent expiry timer to each newly created wish. The bounded
`wish_round_receipts` children belong to the active wish and retire with it.
Pinned protection and unpin/next-refresh behavior remain as already agreed.

#### Moodlet causes and bounded snapshots

| Proposed `moodlet_causes` field | Meaning |
| --- | --- |
| `cause_id` | Technical row identity |
| `episode_id` | Foreign key to the owning Moodlet episode |
| `receipt_id` | Stable receipt of the actual semantic event |
| `occurred_elapsed_seconds` | Actual event time |
| `cause_kind` | Wish fulfilled/failed, interaction, poor care or longer-term pattern |
| `attribution` | User, autonomous or unknown |
| `target_kind`, `target_id` | Actual affected game, food or other target |
| `outcome` | Such as won, lost, handed over or completed |
| `source_wish_instance_id` | Original wish identity as historical evidence |
| `wish_snapshot` | Original definition, objective, required count and target meaning |
| `details_snapshot` | Additional real result/qualification facts |

The original wish identity is not a required foreign key into active wishes.
Keep enough source facts to describe the event after its wish ends. Explicitly
permit small typed, versioned JSON snapshots inside SQLite for variant-specific
details. Stable identity, relationships and common selection fields stay
relational; these bounded snapshots are not an arbitrary state blob or another
editable catalogue. Appropriate details include actual game counts or the
qualifying care-period facts.

Persist facts, not rendered recollection sentences. Dialogue sources later
formulate those facts. Retain at most one/two/three available real causes at
current episode intensity; a stronger single event is not duplicated. Ending
the episode removes its causes. Duplicate-event handling must still respect
independent patterns: the same real event may contribute to different families.

#### Shared encounters, semantic evidence and per-family processing

| Proposed table | Core fields/meaning |
| --- | --- |
| `care_encounters` | `encounter_id`, beginning and last qualified activity of a shared care visit |
| `care_evidence` | `evidence_id`, stable semantic receipt, elapsed event time, optional encounter reference, event kind, area, outcome and actual target |
| `long_term_progress` | Family identity, start of reliable evidence, current period start and fully processed period endpoint |

The progress record also retains a small typed intermediate value where needed,
for example accumulated contactless awake time for Uebersehen. Read deficient-need
durations from the existing `need_exposure_buckets`; do not record another copy
of that timeline. Use the common valid measurement baseline for twenty-four-hour
periods and complete them once per family.

Do not put a shared consumed flag on an encounter/evidence row. One encounter
can support trust and appreciation independently; each family records which
period it has already processed. Do not consume the same period repeatedly to
raise the same family's intensity.

Retain raw evidence only while needed for bounded qualification. An awarded
longer-term episode receives its own bounded qualifying-period cause snapshot,
which can outlive the underlying short-lived evidence. Exact row limits,
cleanup sequencing and remaining pending-handover details belong to the next
storage-contract review, not a permanent event archive.

Pet/domain owners and application semantic-event paths decide fulfillment and
qualification. SQLite enforces relationships and saves coherent results; SQL
does not execute care or emotion rules. Remaining database constraints, full
mapping of other persisted owners, import/path policy and recovery details still
need a focused schema review before implementation.

Documentation-only scope: only this master plan is changed and committed here.
Parallel runtime, tests, text and documentation work is preserved. No runtime
tests, application windows, mouse control, live-save access, database creation,
migration or CI in this pass.


### Proposed save paths, JSON import and persistence error handling

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** Give SQLite its own file, preserve source JSON and make an
existing supported database authoritative after successful import.

| Configuration | Planned database | Legacy import candidate |
| --- | --- | --- |
| No `AIKO_SAVE_PATH` | `%LOCALAPPDATA%/AikoDesktopPet/state.sqlite3` on Windows | Previous `state.json` in that directory |
| Custom path ending in `.json` | Same directory/stem with `.sqlite3` suffix | Exactly the configured JSON file |
| Custom path ending in `.sqlite3`, `.sqlite` or `.db` | Exactly the configured database path | Same-stem `.json` beside it, only if the database does not exist |
| Existing custom filename without a customary extension | Configured filename with `.sqlite3` appended | Exactly the old file, only if it is a supported JSON save |

Continue platform-specific user-data directories elsewhere. Preserve OS
environment precedence over optional `.env`, project-relative path resolution,
user-directory/environment expansion and quoted paths. Existing `.json`
configuration remains a compatibility alias; recommend a direct SQLite path
for new configurations. A custom path selects only that save: do not search
the default directory as another source or silently choose another destination.

#### One-time legacy import

1. Check the selected database first. If it is a supported Aiko database, load
   only that database and ignore an older neighbouring JSON file.
2. Without a database, validate the designated legacy source. Missing optional
   sections in a supported older format are allowed; present invalid sections
   must not be silently dropped. Reject unsupported formats.
3. Create an unchanged backup of the source before import. Backup failure stops
   the import; the original remains untouched.
4. Build a temporary database and import all related values transactionally.
   Validate relationships and complete domain values before publication.
5. Publish only a successfully completed database as the active save. Preserve
   the original JSON without overwriting or subsequently updating it. Record
   import provenance including source format and import time in the database.

Preserve instance identities, original wish goals/progress, Moodlet causes,
stage budgets, settings and saved time anchors. Import itself advances no pet
time. The existing application restorer subsequently performs ordinary offline
progression once from those anchors; migration is not another simulation owner.
If neither the database nor its designated legacy source exists, create a new
save. An incomplete temporary import is never a valid active database, and an
already existing database must not be overwritten by a competing import.

#### Error and recovery policy

| Failure | Proposed behavior |
| --- | --- |
| Damaged JSON or unsupported source format | Stop import, preserve the source and explain the affected path |
| Import or post-import validation fails | Discard the incomplete temporary import; never activate a partial save |
| Database belongs to a newer Aiko schema | Refuse opening for play; no downgrade or overwrite |
| Damaged database or file is not an Aiko database | Stop; do not automatically load possibly stale JSON instead |
| Missing permissions or locked database | Report the error; do not silently select another storage location |
| Saving fails during play | Retain the last successfully committed save, visibly report unsaved state and retry persistence of the snapshot without replaying care actions |

Before later schema migrations, create a consistent database backup through
SQLite's backup interface. A failed migration must not leave a partially
migrated active schema. Restore an older backup only through a deliberate
choice because it can discard intervening progress; never silently pick an old
save. The existing successful database remains the single active persistence
source, not one side of permanent JSON/SQLite dual writing.

Next define the bounded receipt for a real personal food handover whose identity
is not yet known, including original wish context and one-time resolution after
recognition. This amendment does not yet select that receipt's concrete fields.

Documentation-only scope: only this master plan is changed and committed here.
Parallel runtime, assets, tests, text and documentation work is preserved. No
runtime tests, application windows, mouse control, personal-save reads, database
creation/migration or CI in this pass.


### Proposed durable receipt for unidentified personal food handovers

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** Add a bounded `food_handover_receipts` record for an actual
personal transfer into Aiko's custody. Cursor presentation or placement nearby
does not create this receipt. Known food can complete the same path immediately.

| Proposed field | Meaning |
| --- | --- |
| `handover_id` | Stable identity of this actual handover |
| `object_instance_id` | Exactly the transferred World instance |
| `handed_over_elapsed_seconds` | Actual custody-transfer time |
| `wish_context_snapshot` | Food wishes present at handover, with original goals and selection-priority facts |
| `recognized_food_id` | Empty until actual identification |
| `recognized_elapsed_seconds` | Actual identification time |
| `status` | Awaiting identification, evaluated or cancelled |
| `resolved_wish_instance_id` | Historical identity of the affected original wish, if any |
| `accounted_wish_ids` | Bounded marker of snapshot wishes already settled elsewhere |

Unknown identity prevents choosing a matching concrete food wish at handover.
Capture at most the three then-existing food-wish candidates, including original
target/goal, pin state and required priority facts. After recognition, match
within this frozen context using the already agreed priority. Wishes created
later cannot qualify for the old handover. Do not inspect World definition
truth to grant Aiko knowledge before identification.

#### One-time resolution

1. Confirm the actual transfer and persist its identity/original wish context.
2. Wait for genuine recognition to supply the food ID and recognition time.
3. Evaluate matching original candidates, respecting already settled goals and
   the existing explicit-unwanted-food negative rule.
4. Apply the qualified desired/alternative-food positive outcome or the
   expressly unwanted-food negative outcome once, even if the food is put down
   uneaten after recognition.
5. Save the receipt status, wish resolution and Moodlet cause coherently.

The original handover time establishes which wish context applies. Recognition
starts the new Moodlet's lifetime; the preserved cause retains both relevant
facts. Regular wish rotation in between does not substitute a newer wish.
Already accounted fulfillment must not be rewarded again: retain/update the
bounded accounted-wish markers while related handovers remain pending.

Nutrition remains a separate actual-consumption effect. Eating later changes
satiety/digestion, not the same wish a second time. This extends the existing
handover/recognition/consumption boundary rather than creating a second food
interaction engine.

#### Restart, cancellation and retention

An open receipt survives restart. Loading alone grants no identity and replays
no gift. Allow at most one open receipt per physical instance; a genuinely new
handover has its own receipt identity, unlike repeated technical callbacks.

If the transfer is actually withdrawn before recognition or the object is
permanently removed, cancel without a wish Moodlet. Technical recovery placement
during save/restore is not a user withdrawal. In particular, preserve this
distinction when adapting the current World codec's safe-on-ground restoration.

Keep evaluated receipts only while the handover/subsequent processing still
needs their one-time marker. Transfer the relevant immutable facts into the
Moodlet cause; do not build a permanent handover archive. Pending original-wish
context must not require the active wish row to remain alive.

Application coordination confirms the physical transfer and recognition through
existing World/Memory paths. PetState owns wish/Moodlet evaluation and its
durable values. SQLite persists a coherent result and runs no recognition or
care logic. Next map the remaining existing persisted fields to the proposed
tables before finalizing the first schema.

Documentation-only scope: only this master plan is changed and committed here.
Parallel runtime, assets, tests, text and documentation work is preserved. No
runtime tests, application windows, mouse control, personal-save reads, database
creation/migration or CI in this pass.


### Proposed mapping of the remaining persisted fields to SQLite tables

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** Extend the logical table model with the remaining existing
save fields. Wish instances, Moodlet causes, longer-term evidence and personal
food handover receipts retain their preceding proposed contracts. This mapping
does not yet select all primary keys, optional foreign keys or deletion rules.

| Existing persisted area | Proposed destination | Values to preserve |
| --- | --- | --- |
| Shared save/time foundation | `save_state` | Save revision, UTC checkpoint and shared lived seconds |
| Needs and mood | `pet_state` | Satiety, energy, fun, social, affection, mood and current friendship |
| Nutrition | `pet_state`, `food_intake_receipts` | Digestion reserve, awake time since food/main meal, meal-day bookkeeping and existing ordered food history/eating evidence |
| Sleep | `sleep_state` | Sleep kind/start, slept duration, wake/protection times, care break, search/intake deadlines, failed food sources and still-used legacy sleep markers |
| Relationship progression | `relationship_state`, `relationship_entries` | Contact/continuous-care anchors, calculation baseline, eligibility bookkeeping and bounded direct reward/penalty entries |
| Deficient-need exposure | `need_exposure_buckets`, additional `poor_care_cursors` | Existing per-need critical/zero durations and already-accounted/handled processing positions |
| Interaction boundaries | `interaction_state` | Poke/petting boundaries, refusal deadline, excess attempts and food-variety request state |
| Settings | `app_settings` | Pet/window geometry, toolbar coordinates, behavior switches, online permission and optional zodiac sign |
| Actual World stock | `world_state`, `world_objects` | Surface, revision, allocation counter and saved object identity/definition/revision/ground position/footprint |
| Subjective object knowledge | `object_memories`, `object_memory_sources`, additional `object_memory_state` | Acquired identity, remembered place, knowledge/missing state, possible associations, record allocation and World allocation provenance |
| Learned habits | `adaptive_state`, `adaptive_hour_slots`, additional `adaptive_quiet_phases` | Existing learning scalars, hour-of-week aggregates, learned quiet window and bounded recent daily quiet phases |
| API repetition suppression | `social_receipts` | Category, provider identity, fingerprint and existing order of the last ten contents per category |
| API limits | `social_requests`, `provider_pauses` | Request timestamps and provider pause deadlines |
| Current daily horoscope | Additional `horoscope_days` | Day, attempt count, optional reading, continuation position, admitted/completed flags |

Include the actual parallel horoscope working contract before switching storage;
this documentation does not modify that work. Retain its bounded current-day
record rather than introducing a growing daily archive. Admission/continuation
state must prevent duplicate participation credit after restart.

#### Preserve existing meanings during the storage change

- An acquired object-memory instance identity is historical knowledge. The
  physical object may already be consumed/removed and absent from saved World
  stock. Do not require a live `world_objects` row or delete knowledge merely
  because stock disappears. Possible-source associations still relate
  subjective records and must not reveal hidden World identity.
- Preserve distinct time meanings: shared elapsed-domain deadlines, actual
  wall-clock timestamps, durations, local days and minute-of-day quiet windows.
  Object-memory active age must not silently become elapsed real time. API
  limits retain their wall-clock meaning.
- Ordered nutrition food IDs do not contain the same facts as timestamped
  food-monotony intake evidence. Preserve their separate meanings and order;
  do not invent event times or merge entries based only on matching food IDs.
- Social repetition receipts likewise preserve order without inventing event
  timestamps where the existing format provides none.
- Preserve still-used meal/sleep bookkeeping and legacy relationship fields
  during import. Storage conversion must not reactivate obsolete instant-care
  reward rules or remove compatibility values without a separate usage review.
- Keep the current World save/restore semantics: terminal objects are omitted
  and nonterminal objects restore safely at ground level. Do not introduce
  motion/animation continuation as an incidental SQLite feature. Technical
  placement does not invalidate a pending real handover receipt.

`PetState`, World, Memory and the existing settings/adaptive/social owners keep
their responsibilities. Tables are persistence mappings, not another domain
hierarchy; one table does not imply one new service class. Retain typed, bounded
variant snapshots where appropriate rather than creating a table per small list.

Overall emotion, display text, tooltips and status projections remain derived.
Do not add a permanent row per thirty-second tick, raw input/hardware archive,
ordinary animation/bubble playback state or a duplicate editable catalogue.

Next discuss concrete keys, optional relationships and cleanup/retention rules
for this model. Those additional choices are not approved by recording this
field mapping, and no SQLite schema or database is created in this pass.

Documentation-only scope: only this master plan is changed and committed here.
Parallel runtime, assets, tests, text and documentation work is preserved. No
runtime tests, application windows, mouse control, personal-save reads, database
creation/migration or CI in this pass.


### Proposed SQLite keys, optional relationships and deletion rules

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** One private database represents one save. Do not add account
management or a repeated multi-save identifier to every table. The save revision
identifies a coherent checkpoint, not a permanent archive of whole snapshots.

| Proposed table/group | Proposed key |
| --- | --- |
| Singleton state/settings records, including `save_state`, `pet_state`, `sleep_state`, `wish_state` and other owner bookkeeping | One fixed row with `id = 1` per table |
| `schema_migrations` | Unique structural migration version |
| `wish_instances`, `moodlet_episodes` | Preserve existing numeric instance identities; never reuse them |
| `world_objects`, `object_memories` | Preserve existing text object identity and subjective memory identity respectively; keep their namespaces distinct |
| `wish_round_receipts` | Wish identity plus unique round signature including its session context |
| `moodlet_stage_state` | Episode identity plus stage |
| `moodlet_causes` | Technical row identity, with event receipt unique within the same episode |
| `object_memory_sources` | Pair of associated subjective memory identities |
| `care_encounters`, `care_evidence`, `food_handover_receipts` | Stable individual identity for each encounter, evidence item or handover |
| `long_term_progress`, `poor_care_cursors` | Long-term family identity or need identity respectively |
| `need_exposure_buckets` | Need identity plus interval beginning |
| `adaptive_hour_slots`, `adaptive_quiet_phases` | Hour-of-week slot, or local day plus phase beginning respectively |
| `relationship_entries`, `food_intake_receipts`, `social_requests`, `social_receipts` | Technical entry identity; retain ordering separately where meaningful |
| `provider_pauses`, `horoscope_days` | Provider identity or local calendar date respectively |

An event timestamp alone is not an identity: different events can share a time.
Duplicate processing is constrained within the appropriate semantic consumer;
one real event can still support different Moodlet/long-term families.

#### Required, optional and historical relationships

- A round receipt requires its owning active wish. Stage values and causes
  require their owning Moodlet episode. Enforce these actual ownership links
  with foreign keys.
- A care-evidence row may reference a shared encounter, or have no encounter
  when none occurred. Do not remove a referenced encounter while retained
  evidence still needs it.
- A cause's source wish identity and an object's acquired physical identity
  are historical facts, not required live-instance foreign keys. Preserve
  their original facts after the wish/object disappears. A pending handover
  likewise retains original wish context independently of active wish rows.
- Catalogue identities remain validated through the typed JSON contracts;
  do not introduce a second editable catalogue database to enforce these IDs.
- Use absent values only for genuinely absent facts: unknown food identity,
  a wish not yet expressed, or no concrete target under a free-choice rule.
  Required goals, progress counters and pin flags remain non-null values.

#### Cleanup follows domain lifetimes

| Domain transition | Proposed deletion/retention behavior |
| --- | --- |
| Wish fulfilled, dismissed or regularly rotated | Remove the active wish and its round receipts; preserve existing independent Moodlet causes |
| Wish pinned | No time-based expiration or rotation |
| Moodlet drops to a lower stage | Retain at most the latest one/two/three real causes according to current stage; do not invent missing causes |
| Moodlet ends | Remove the episode and its dependent stages/causes together |
| Physical object consumed/removed | Remove it from saved World stock; preserve acquired memories and existing causes |
| Subjective memory forgotten | Remove its association edges without deleting other memories |
| Handover evaluated/cancelled | Remove the receipt only after processing and any required duplicate-effect protection have finished |
| Care/long-term evidence ages out | Evaluate all required windows first; preserve required intermediate progress in `long_term_progress`, then prune obsolete raw evidence |
| API history/limits | Keep the last ten contents per category; prune request receipts and provider pauses according to their existing time windows |

Use cascading deletion only for unambiguously owned child records or association
edges. Domain owners decide wish retirement, episode ending, forgetting and
handover cancellation; SQL does not make these care decisions or run timers.
Persist the coordinated outcome in one transaction so cleanup cannot leave
half-applied effects or broken relationships.

Next review the complete proposed SQLite model for concrete implementation
gaps. Recording these keys/relationships does not implement the schema, select
every SQL column type/index, or authorize runtime/database changes.

Documentation-only scope: only this master plan is changed and committed here.
Parallel runtime, assets, tests, text and documentation work is preserved. No
runtime tests, application windows, mouse control, personal-save reads, database
creation/migration or CI in this pass.


### Proposed final technical contracts before SQLite implementation

**Discussion proposal recorded at the owner's request, 2026-10-23; no runtime
implementation.** The preceding logical model covers the agreed persisted
domains. Record these three technical decisions before dividing implementation
into small, locally verified changes.

#### Preserve the two food-history meanings explicitly

Keep the short ordered list of recently eaten food IDs as a bounded list in
`pet_state`. Store timestamped portions used by food-repetition processing in
`food_intake_receipts`. These are distinct existing facts. Preserve original
order, valid timestamps and existing limits through import; do not synthesize
timestamps or merge records merely because their food ID matches. This uses
the already permitted small typed list/snapshot representation within SQLite.

#### Reject stale writes to the same save

Use the shared save revision as an expected-revision guard. When saving a
coherent snapshot, compare its expected persisted revision with the current
database revision inside the same transaction as the write. Advance the
revision only with a successful commit. Reject a stale write without changing
the newer database state; do not retry by blindly overwriting the other
session's progress. This also covers competing first saves/import publication
through the already required no-overwrite initialization boundary.

Distinct database paths remain independent saves. This decision adds no account
model, permanent save-history table, automatic state merge or second domain
writer. A failed/rolled-back write must not advance the caller's expected
revision as though it had committed.

#### Route storage failures through one application-facing contract

The current desktop persistence path catches `OSError`. Introduce one typed
application-facing storage failure contract covering access/I/O failures,
database locks, stale revisions, invalid data and database/schema failures.
The infrastructure adapter translates backend errors without exposing SQL
exception handling to UI/domain owners. Preserve the already agreed distinct
startup/import/save failure behavior; a read/import failure must not silently
start a replacement game.

On save failure, report unsaved state and retain the last successful database
checkpoint. Retry only appropriate persistence failures using a coherent
current snapshot; do not replay interactions, grant effects again, or override
a stale-revision conflict. Preserve the existing autosave responsibility and
separate domain progression from writing.

Concrete SQL types, checks, indexes and versioned detail formats can be derived
from these contracts during implementation. Existing Pet/World/Memory and
application owners keep their rules; the SQLite adapter replaces persistence
behind the existing session boundary. Legacy JSON becomes a one-time import
path rather than a permanent parallel writer.

Next discuss the implementation slices and targeted local validation for each.
This amendment records only the three agreed technical contracts; it does not
implement the adapter, create a database, run tests, or approve the next slices.

Documentation-only scope: only this master plan is changed and committed here.
Parallel runtime, assets, tests, text and documentation work is preserved. No
runtime tests, application windows, mouse control, personal-save reads, database
creation/migration or CI in this pass.


### Agreed delivery order: features before SQLite and final OOP work

**Planning direction recorded at the owner's request, 2026-10-23; no runtime
implementation.** First implement the already discussed wish/Moodlet behavior
on the current games and social features. Move SQLite implementation into the
closing architecture/OOP refactor phase, followed by the final OOP review and
complete local suite. This supersedes the earlier requirement to implement
SQLite before the feature slices; the preceding data model/contracts remain
the intended migration target.

#### Build on the actual current activities

The current working tree's `GameId` includes Rock Paper Scissors, Tic-Tac-Toe,
Blackjack, Connect Four and Mastermind. At this review, `data/wishes.json` still
lists only the first three games for game wishes. The social working contracts
also include horoscope and provider-aware sayings, jokes and facts. Some of
these additions are parallel, uncommitted work: preserve them and reconcile the
finished baseline before feature implementation, without treating this planning
pass as a runtime acceptance test or permission to rewrite parallel work.

At feature kickoff, recheck the actual available activities, supported round
events and social completion boundaries. Extend eligible targets and shared
matching through the existing owners. New game IDs must not be silently excluded
by old target lists; a menu/category entry alone must not imply that every wish
variant is available or has a valid completion path. Retain result attribution
from Aiko's perspective and the existing game/social event coordinators. No
new minigame implementation or new horoscope-specific wish is implied here.

#### Ordered work

1. Reconcile the completed game/social baseline and map existing wish/Moodlet
   delivery gaps against it. Preserve all valid parallel work and original
   saved wish goals/progress.
2. Resume the eight feature slices recorded under implementation readiness,
   including their longer-term/overall-state extension: definitions, typed
   state, progression/renewal, wish lifecycle/weights, shared activity matching,
   food/affection integration, qualified positive/negative experiences and
   longer-term patterns, then overall feelings and passive status/hover reads.
   Split each area into small reviewable commits with targeted local checks.
3. Verify the integrated feature behavior and actual generated wish opportunities
   with deterministic targeted checks. In the earlier feature slice eight,
   defer the complete-suite/final-OOP portion to the closing phase below.
4. Perform the closing architecture/OOP refactor, source-organization cleanup
   and SQLite migration using the agreed ownership, model, import and error
   contracts. Split persistence work into its own small steps and verify the
   final feature state survives migration. Keep dialogue-source organization
   aligned with the existing single content owner.
5. Finish with the final OOP/duplicate-structure review, complete local suite,
   redundant-test review and investigation of tests exceeding ten seconds.
   Correct findings in scoped commits and push the completed work.

Clear OOP ownership and understandable function/module names apply throughout
the feature work. Make necessary local extractions with the affected feature;
do not postpone required domain boundaries until the final review. The deferred
work is the cross-cutting refactor/storage conversion and final review.

Until SQLite cutover, extend existing JSON codecs only as needed to preserve
the new typed domain values. Use the already agreed stable identities, bounded
causes, tier budgets and receipts so they map directly to the later schema.
Keep one active writer; do not build a second state aggregate, permanent
parallel backend or a disposable alternate history format. The feature-first
order entails adapting the current codecs before the later adapter migration;
keep those adaptations narrow rather than introducing new storage machinery.

All implementation remains separately authorized. Continue with small commits,
targeted local tests and scoped pushes; no test windows, mouse control or
GitHub CI. This amendment changes only the plan and runs no runtime tests.


### Delivery slice 1A: existing game wishes include Connect Four and Mastermind

The five existing game wish definitions now include `connect_four` and
`mastermind` alongside Rock Paper Scissors, Tic-Tac-Toe and Blackjack. This
changes eligible targets only: original objectives, saved progress, selection
weights and fulfillment Moodlet families remain unchanged.

Use the existing game-round coordinator and per-game round events. Catalogue
coverage now checks every supported game for each game-wish form; the existing
coordinator regression exercises every `GameId`, including start-before-result,
player-to-Aiko result translation and duplicate-result rejection. No additional
state owner, game-specific wish processor or UI change is introduced.

Targeted local worktree validation: **28 tests passed** across
`test_wish_catalog` (7), `test_wish_games` (14) and `test_game_experience` (7).
Reported test runtimes were 0.006, 0.092 and 0.097 seconds respectively; the
slowest individual case took 0.073 seconds. Changed-test Ruff and focused
Pyright passed. No test windows, mouse control, full-suite run or CI.

After securing the baseline, the exact staged 1A snapshot independently passed
the same **28 tests in 0.178 seconds**, with native Tk creation blocked. The
slowest case took 0.066 seconds; focused Ruff and Pyright passed again. This
checks delivery without relying on the remaining parallel working-tree changes.

The completed Mastermind implementation is secured separately in baseline
commit `5602726`, including its assets and game-host wiring. Shared horoscope
and character-asset changes remain outside that baseline and this slice.
The new flexible wish forms, ten-minute lifecycle, Moodlet timing/longer-term
families and SQLite migration remain separate subsequent slices.

The existing status renderer still uses its Blackjack-card fallback for the
two new game targets; target-specific status icons belong to the planned
passive status/UI slice. Their localized game names and cause text are already
resolved through the existing game-name keys.


### Delivery slice 1B: typed flexible wish definitions

The existing Pet-domain definition model now distinguishes target kind from
`WishTargetMode` (`exact`, `any`, `exclude`). A frozen `WishTarget` binds a
concrete/excluded reference or retains an empty reference for free choice;
matching never silently fixes a free goal to the first chosen game. Definition
binding validates the supported target pool. These are values, not another
mutable wish collection, timer or progression owner. The first small type-only
commit is `6e5b140`.

The version-two authored wish catalogue defines seventeen forms, including:

| Added form | Typed target | Original goal | Base form weight | Creation prerequisite |
| --- | --- | --- | --- | --- |
| `play_any_game` | Any supported game | Two total rounds, potentially across games | 30 | None |
| `play_other_game` | Exclude the saved reference game | Two total rounds outside that game | 10 | Recent completed play |
| `rematch_game` | Exact reference game | One completed round regardless of result | 10 | Last completed round was Aiko's loss |
| `comeback_game` | Exact reference game | One victory, allowing retries | 5 | Last completed round was Aiko's loss |
| `social_any` | Any supported ordinary social category | One complete conversation/entertainment sequence | 30 | None |

Experience prerequisites are frozen typed data: thirty-minute validity and a
one-time 1.5 form-weight multiplier. Definitions do not claim that such an event
actually happened. Social free choice covers chat, saying, joke and fact, and
does not invent a horoscope wish or a provider-specific duplicate wish. Reuse
`shared_play`, `pride` and `connection` for the new forms' future completion.
Food avoidance is explicitly typed as an excluded target; this amendment does
not change its existing handover outcome or introduce the new negative family.

Keep the new forms' own label/description/utterance keys, including flexible
wording rather than the concrete-game wording of a shared round-count goal.
German templates and strict placeholder contracts accompany the definitions.
The catalogue rejects incompatible modes, prerequisites, goals, sources and
malformed windows/multipliers. Catalogue version two does not change the saved
game format; existing explicit/legacy goals retain their original semantics.
New forms have no invented legacy objective when an original goal is absent.

Activation remains in the already planned lifecycle/matching slices. The current
single-target picker declines flexible game/social definitions and experience
prerequisites it cannot yet resolve, rather than creating a misleading exact
wish. Existing live form weights and care values remain unchanged; the complete
area/form weighting, including the 30/30 concrete/free play split and social
weights, belongs to the selection slice. No generic enable flag, second catalogue
or duplicate active-wish store is added.

Targeted local worktree validation passed **82 tests in 0.258 seconds** across
wish targets/catalogue/lifecycle/games, emotional persistence and text catalogue.
The slowest case took 0.068 seconds. Native Tk creation was blocked for the run.
Focused Ruff, strict Mypy for four affected source files and focused Pyright
passed. Preserve parallel horoscope/character edits; verify the isolated staged
delivery before publishing. No full suite, test windows, mouse control or CI.

The isolated staged delivery additionally passed **100 targeted tests in 0.370
seconds**, including existing wish expression and emotional read-model tests.
Its slowest individual case took 0.063 seconds, and native Tk creation remained
blocked. Focused Ruff, strict Mypy and Pyright also passed on that isolated
snapshot, independently of parallel uncommitted horoscope/character changes.


### Delivery slice 1C: food-wish setback and longer-term definitions

The immutable type foundation is committed as `1f639f6`. The existing authored
Moodlet catalogue now has twenty-six families; all nineteen previous rows retain
their original values. Authored catalogue version two adds `long_term_policy`;
it does not change the saved-game version or import existing personal evidence.

| Added family | Direction | Nominal mood points by level | Time per stage |
| --- | --- | --- | --- |
| `food_wish_disregarded` / Essenswunsch missachtet | Downcast | -5 / -10 / -15 | 30 minutes |
| `trusting` / Vertrauensvoll | Safety | +5 / +10 / +15 | 36 hours |
| `appreciated` / Wertgeschaetzt | Affection | +5 / +10 / +15 | 30 hours |
| `optimistic` / Zuversichtlich | Optimism | +5 / +10 / +15 | 30 hours |
| `uncertain` / Verunsichert | Uncertainty | -5 / -10 / -15 | 30 hours |
| `overlooked` / Uebersehen | Loneliness | -5 / -10 / -15 | 30 hours |
| `guarded` / Auf der Hut | Caution | -5 / -10 / -15 | 36 hours |

The food setback has its own `food_setback` group and no direct friendship-loss
parameters. Its later trigger must use the recognized personal handover and
original explicitly excluded food context, even when put down uneaten; ordinary
nonmatching food, autonomous intake or an unidentified transfer is insufficient.

The six longer-term definitions share the `long_term` group and a twenty-four-hour
qualification period. Frozen pattern values in `pet/moodlet_patterns.py` retain:

- Trust: three encounters, two-hour gaps, eight-hour span, two activity kinds,
  no first-level poor-care exposure and no communicated boundary violation.
- Appreciation: three fulfilled wishes, two wish areas, two encounters separated
  by two hours and no communicated boundary violation.
- Optimism: three pleasant activities, two areas, two encounters separated by
  two hours, one actual success and at most one activity of each kind per encounter.
- Uncertainty: two independent pleasant-then-upsetting pairs with a two-hour
  minimum gap between the upsetting incidents.
- Overlooked: at most one encounter and an eight-hour accumulated awake contact
  gap. Sleep pauses this gap; it does not erase earlier awake time.
- Guarded: three independent upsetting incidents spanning at least four hours.

Trust's exclusive `care_exposure_level_limit = 1` reuses the existing first
poor-care exposure threshold meanings rather than duplicating their durations.
Pattern values describe prerequisites, not observed incidents. The strict decoder
in `pet/moodlet_pattern_catalog.py` rejects unknown fields, invalid counts, missing
or crossed prerequisites and encounter schedules that cannot fit the period.

The immutable shared policy records the agreed separate +5/-10 joint mood limits
and +0.00005/-0.00010 per-intensity friendship rates per existing thirty-second
interval. The negative limit/rate are stored as magnitudes. These are the future
longer-term rates, replacing rather than adding ordinary short-term rates.

German labels/descriptions and existing icon reuse make every definition readable
through the current passive views. Individual safety, uncertainty and caution
directions project to the agreed baseline labels affectionate, tense and reserved;
optimism has its own label. Existing families' selection behavior is preserved.
The later compound-selection rules, including carefree and mixed-feeling bands,
remain pending. Psychological descriptions do not disclose care thresholds.

**Scope boundary:** no new runtime trigger, qualifying-period evidence, timer,
mutable collection, interaction lock or instant friendship adjustment is added.
Activation, once-per-period qualification, stage reinforcement and applying the
shared limits/rates remain in their planned subsequent slices. No SQLite or live
save changes are included.

The isolated staged delivery passed **94 targeted local tests in 0.670 seconds**
across Moodlet catalogues, progression, mood, emotional composition/read models,
existing persistence, wish catalogue and text contracts. The slowest individual
case took **0.389 seconds**; none exceeded ten seconds. Native Tk creation was
blocked throughout. Focused Ruff, strict Mypy and Pyright passed. Parallel
horoscope/character work is preserved outside these commits. No full suite,
test windows, mouse control or CI was used.


### Delivery slice 2: owned state and compatible JSON persistence

The feature-first order continues with typed state and the existing JSON codecs;
SQLite remains in the closing architecture phase. The type foundation is
`3d714b9`, wish/transfer storage is `a09cb42`, and bounded care-evidence decoding
is `512a81f`. The final integration adds Moodlet stage/cause persistence and
whole-Pet checkpoint tests. These changes prepare storage, not the subsequent
wish-selection, renewal or long-term qualification algorithms.

#### Wishes and original transfer context

Active wishes can retain an explicit frozen target kind/mode/reference, including
free choice and exclusion. Preserve original goals, quantities, progress, pins
and identity. Legacy instances without the new target value keep their original
concrete reference. Several distinct goals in one area can round-trip within
the existing three-slot total; duplicate identities or identical original goals
remain invalid. An area's last creation anchor may be newer than its older
surviving wishes.

`WishState.refresh_at` is the single stored refresh deadline. Read the old
`refill_not_before` key into that same value; never write both clocks. Reject
conflicting supplied deadlines. Existing vacancy/refill behavior uses the renamed
field without a pacing change. The authored ten-minute interval is now available
in the balance catalogue; regular rotation and its new generation policy remain
slice four. Existing original expiry dates and game progress are not rewritten.

Personal food transfers have bounded immutable receipts: transfer identity,
physical object identity, original time and up to three original food-wish
snapshots with goals, target meanings and priority facts. Recognition identity/time,
pending/evaluated/cancelled status and accounted/resolved wish identities remain
distinct. At most one pending transfer references a physical instance; the
overall bound is thirty-two retained receipts, not a permanent transfer archive.
Pending original wishes need not remain active. Load never identifies food,
replays a transfer, grants a reward or interprets technical ground placement as
a user withdrawal. Actual creation/resolution/cancellation remains slice six.

#### Moodlet budgets, causes and care evidence

`MoodletEpisode.remaining_seconds` remains the current stage's single time value.
`lower_stage_seconds` stores the lower levels in ascending order, excluding the
current stage. Explicit positive lower-stage budgets are bounded at ninety
minutes each. Empty lower-stage data denotes the old implicit schedule; loading
does not invent earned extensions or truncate the existing saved current stage.
Actual ascent, decay and renewal of these budgets remains slice three.

Causes retain original typed wish targets separately from actual outcomes, the
original food-transfer time separately from later recognition, and versioned
long-term period summaries separately from short-lived raw evidence. The existing
one/two/three-real-cause limit still applies. A stronger event remains one cause;
no event is copied to fill missing rows. Historical positive unwanted-handover
records remain historical facts; new explicit negative handover records have
their own validated cause contract.

`MoodletState.care_evidence` owns immutable encounters, semantic receipts and
per-family period watermarks on the existing elapsed-time axis. Bounds are 128
retained encounters and 512 real experience receipts, with one progress record
per supported long-term family. Receipts reference real retained encounters;
independent families can retain different processed endpoints for shared evidence.
There is no shared consumed flag or copy of the need-exposure timeline. The
future producer/evaluator must finish required processing before pruning evidence;
the codec rejects overflow instead of silently dropping qualification facts.
Missing legacy evidence remains unknown (`None`), with no invented encounters or
processed care days. A bounded period summary can outlive its raw evidence while
its owning Moodlet cause remains active.

Shared wish snapshot validation and Moodlet cause serialization have dedicated
infrastructure modules; PetState remains the sole mutable Pet aggregate. Existing
save sections retain version one with optional extensions. Coherent whole-Pet
capture/restore and the existing section-corruption recovery path remain in use.
No extra backend, timer, UI writer, qualification engine or live-save migration
is introduced.

The isolated staged integration passed **162 targeted tests in 1.179 seconds**
covering wish storage/lifecycle/activities, emotional persistence, care evidence,
Moodlet progression/mood, passive reads and text contracts. The slowest case took
**0.402 seconds**; none exceeded ten seconds. Native Tk creation was blocked.
Focused Ruff, strict Mypy and Pyright passed for the affected production files.
Earlier isolated commits passed their own focused checks. Parallel horoscope,
character, UI and documentation edits remain outside these commits. No full suite,
test windows, mouse control, live-save access or CI was used.


### Delivery slice 3: Moodlet stage progression and bounded renewal

Positive wish-family timing is delivered in `01b5ccd`, independently verified
with one hundred targeted tests before adding the long-term contribution policy.
The existing `PetState`/progression path still owns time and commits results.
`pet/moodlet_timing.py` provides pure stage-budget operations used by the existing
Moodlet rules and passive duration reads; it is not a timer or another simulator.

New positive multi-tier episodes receive sixty minutes for level one and
forty-five minutes each for levels two and three. An ascent raises each remaining
budget to its base floor while preserving longer residuals, capped at ninety
minutes each. Already-level-three reinforcement adds ten minutes per remaining
tier, capped at 270 minutes total. Two-tier outcomes use ascent or capped renewal,
never both; overflow intensity grants no extra extension. Food remains one tier:
sixty minutes initially, ten-minute renewals and a ninety-minute ceiling.
These values belong to the shared balance catalogue, with validation against
the stage cap. Family strengths and ordinary friendship rates remain unchanged.

Ageing spends the actual current budget and then the actual stored lower budgets,
trims causes to the new intensity and expires an episode once. The operation
visits at most three tiers, including across a long elapsed gap. A stronger
single outcome remains one actual cause; duplicate receipts do not extend time.
No spent upper-tier extension is banked for a later ascent. Passive duration
reads now sum the same actual budgets without mutating the Pet.

Compatibility is deliberate: existing current-stage time and old implicit lower
stages retain their original fixed catalogue duration until an actual qualified
reinforcement applies the new bounded rule. The fixed positive family durations
in the Moodlet catalogue therefore remain the v1-save read contract, rather than
silently shortening old impressions during loading. New positive stages use the
shared 60/45/45 balance profile and explicit lower budgets. Existing JSON codecs
and whole-Pet checkpoints preserve these values without another save format.

The six long-term families retain their own thirty-/thirty-six-hour stage clocks.
One newly qualified period raises one level, up to three, and resets only the
current fixed stage. They receive no wish-family duration banking or renewal.
Their positive and negative numeric subtotals are independently capped at +5
and -10 before existing global caps; opposite long-term feelings never cancel
before those limits. Their reduced +0.00005/-0.00010 per-intensity friendship
rates replace ordinary +0.003/-0.006 rates for those families. Full emotional
intensities remain available to the overall feeling model.

The existing progression boundary splitting applies mood and friendship effects
until the actual stage endpoint, including an expiry inside a thirty-second
status interval. Sleep, standby and closed time use that same path. Existing
negative-family decay, withholding resolution, poor-care recovery qualification
and relief allowances are preserved. No need decay, care gains, sleep policy,
wish selection or action admission is changed. Actual long-term qualification
and the new experience producers remain in slice seven; elapsed time alone
does not manufacture positive encounters or bad treatment.

The isolated staged integration passed **136 targeted tests in 1.161 seconds**,
covering stage budgets/renewal, long-term caps/rates, existing negative/poor-care
rules, actual time-path boundaries, persistence, passive reads, friendship-rate
regressions and current game/food/social/affection completion. The slowest test
took **0.433 seconds**; none exceeded ten seconds. Native Tk creation was blocked.
Focused Ruff, strict Mypy and Pyright passed for the affected production files.
The current system document was updated alongside this plan. Generated-wish/day
acceptance and the final full suite/OOP review remain in their planned later
steps. Parallel horoscope, UI, character and documentation work is preserved.
No test windows, mouse control, live-save access, full suite or CI was used.


### Delivery slice 4A: one shared wish rotation and pin lifecycle

The awake picker now schedules one refresh every 600 elapsed seconds. New
unpinned wishes share that deadline; fulfillment/dismissal keeps the deadline
rather than starting another vacancy timer. Offline and sleep progression can
expire wishes but cannot generate replacements. The next awake endpoint runs
one due refresh and schedules the next deadline from that endpoint, with no
backlog. All-pinned stock still advances this same schedule.

Pins preserve identity, objective and progress across closure/sleep. Unpinning
keeps the wish until the next refresh, including after its obsolete four-hour
deadline; the codec accepts that bounded future deadline after a late unpin.
Existing saved concrete game wishes retain their original objective, progress
and original expiry. Old non-game wishes join the shared schedule. No care,
Moodlet, friendship or speech credit is manufactured by these commands.

Selection now lives in `pet/wish_selection.py`; immutable wish values and
completion/disclosure rules remain in `pet/wishes.py`. `PetState` is still the
only mutable owner. No forwarding API, UI clock or second wish store was added.
Area/form weighting and flexible eligibility follow in the next small commit.

Targeted local lifecycle, controls, storage and catalogue checks passed:
28 tests in 0.060 seconds, slowest 0.029 seconds. Focused Ruff, strict Mypy and
Pyright passed. Native Tk creation was blocked. No windows, mouse, live-save
access, full suite or CI was used. Parallel changes are excluded from staging.


### Delivery slice 4B: weighted eligibility and flexible three-slot stock

The canonical selector now chooses an eligible area by the corresponding need's
1/3/5/7 weight (above 70 / above 40 / above 25 / at most 25), then a form by its
catalogue weight, then one supported original target. More forms/targets do not
multiply area weight. The area limit and obsolete food/affection creation and
retirement thresholds were removed, rather than left as competing policies.
Multiple different game/social goals can fill all three slots. Full needs alone
exclude no area and do not retire existing wishes. Current explicit petting
refusal and Too Much Closeness still block new affection wishes; willingness
based on fullness is a different fact. API capability gates specific forms;
content readiness and energy remain temporary disclosure/action restrictions.

Catalogue form weights now implement the agreed game and social tables, plus
70:30 concrete-food/shared-variety selection when repetitive-food evidence
exists. Flexible ANY/EXCLUDE references bind their original typed meaning.
Exact goal/target duplicates are excluded, including against pinned goals.
Recent actual completed play enables game change. Only a latest round defeat
from Aiko's perspective enables rematch/comeback alternatives; a later non-loss
replaces that fact. These experience forms require evidence younger than 1800
elapsed seconds and apply their 1.5 multiplier once. Already created/pinned
references and progress do not change when later rounds occur.

`GameExperienceCoordinator` records a valid completed round, even without a
wish, through `PetState.record_completed_game_round()`. This uses the bounded
`MoodletState.care_evidence` already introduced in slice two, not a new history
or clock. Missing history remains unknown; results without an observed start
and repeated callbacks cannot invent receipts. These factual receipts grant no
emotional reward, encounter qualification or instantaneous friendship bonus.
The later positive/long-term producers will use this same owned evidence store.

The legacy four-hour lifetime and twelve-minute refill configuration remain
strict old-save/history read bounds in infrastructure only. Runtime creation
and retirement use the shared 600-second refresh, not those legacy values.
`PetState` remains the only mutable owner and UI commands keep their existing
two-step right-click behavior. No UI timer, API request or offline wish engine
was added. Shared matching/assignment for newly selectable flexible forms is
slice five; actual full-need food/affection permission and revised handover
outcomes are slice six. This delivery does not claim those integrations or
whole-day balance acceptance are complete.

Verification covers deterministic area/form weights, need-band edges, full
needs, capability/refusal separation, multiple goals per area and duplicates,
experience-window boundaries, single rematch selection, original saved game
progress, refresh/return/pins, bounded actual receipts and save round trips.
Focused lifecycle/storage/catalogue/expression and existing game/food/social/
affection regression checks use a native-Tk creation guard. The final measured
result is recorded after the isolated staged integration below. Full-suite,
generated-wish/day acceptance and closing OOP review remain in slice eight.


Isolated staged integration result for slice four: **115 targeted tests passed
in 0.572 seconds**, slowest **0.067 seconds**; none exceeded ten seconds.
Focused Ruff, strict Mypy and Pyright passed for all nine affected production
files and the changed tests (Ruff). Native Tk creation was blocked throughout
loading and execution. No windows, mouse control, live-save access, full suite
or CI was used. Only this delivery's paths/hunks are committed; parallel
horoscope, UI, character assets and related documentation remain untouched.


### Delivery slice 5A: shared assignment and fulfillment ownership

`pet/wish_matching.py` owns pure pre-outcome matching/priority. It checks the
saved exact/any/excluded target against supported activities, then prefers a
pin, a more constrained target (exact, exclusion, free choice), real saved
progress, age and stable identity. Equally concrete outcome goals acquire no
invented win-first ordering. Expired/future wishes and unsupported activities
cannot match. Application admission will capture this returned identity before
outcomes; no random selection, physical care effect or extra state is involved.

Pure completion rules were moved from `pet/wishes.py` to
`pet/wish_fulfillment.py`, with actual callers updated and no forwarding shim.
Immutable wish values, lifecycle and disclosure keep their existing owner;
`PetState` remains the only mutable aggregate. Game/social adapters follow in
separate small commits; food/affection behavior is unchanged by this extraction.

Eight priority/matching tests and existing lifecycle/game/food/affection checks
passed (46 targeted tests in 0.172 seconds; slowest 0.073 seconds). Focused
strict Mypy/Pyright passed. Native Tk creation was blocked. No test windows,
mouse control, live-save access, full suite or CI was used.


### Delivery slice 5B: assigned game rounds and flexible completion

`GameExperienceCoordinator` now uses shared matching at actual round start and
carries that exact identity through the round. Later pin changes, dismissal,
expiry or newly created wishes do not reassign the result. A failed win/non-loss
attempt cannot fall back to another play goal. Existing original objectives,
including legacy session/block goals and cumulative saved progress, retain their
own success/failure rules and no instantaneous friendship bonus.

Completion matches the saved exact/any/exclusion meaning against supported game
IDs. Free-choice total rounds can span games/sessions; game-change excludes its
saved reference; simple rematch accepts a completed result; comeback permits
retrying until a victory. Moodlet causes retain both the original typed wish
and the actual completing game/result. Existing stage/failure rules apply once.

The already bounded actual-round evidence now also reports whether the receipt
is new. A replayed start/result cannot advance another wish after retirement or
reload. It uses the existing Pet-owned evidence store, not a second receipt log.
Ordinary game/session care remains separate and unchanged.

Eight new round-assignment checks plus existing matching, game, selection and
storage tests passed: 56 targeted tests in 0.361 seconds, slowest 0.071 seconds.
Focused Ruff, strict Mypy/Pyright passed. Native Tk creation was blocked; no
windows, mouse control, live-save access, full suite or CI was used. Social
admission/completion follows in its own commit; parallel work is preserved.


### Delivery slice 5C: assigned social completion and technical receipts

Social admission now uses the same deterministic matching rule and carries the
selected wish identity plus an actual sequence ID/elapsed start through the
existing immutable `SocialCompletion` and Reaction playback. No UI timer or
provider call was added. A complete chat/saying/joke/fact can fulfill a free
social wish; specific wishes still require their category. The assigned wish's
catalogue determines the Moodlet family (free social uses connection). No
completion is inferred from starting, an individual bubble or interrupted text.

Completion resolves only the captured live identity, checks its original target
and start, and never adopts a wish created during playback or falls back after
dismissal/expiry. Moodlet causes retain the original goal/target and actual
category and sequence receipt. Fulfillment/retirement preserves the shared
refresh; actual need effects remain with admission and do not repeat at finish.

Actual social completion records one bounded receipt in the existing
`MoodletState.care_evidence`. A single aggregate append rule now serves actual
rounds and social completion. Duplicate callbacks, including after reload and
a relief cooldown, cannot repeat the wish outcome or helpful relief. These
receipts qualify no positive encounter or long-term period by themselves;
those producers remain slice seven. Legacy direct `SocialCompletion` value
callers may omit both new admission fields; all production admissions supply
both. No old interaction is fabricated during reading/migration.

Nine new social admission/completion checks cover all four supported categories,
priority changes, interruption/stale callbacks, no fallback or late adoption,
distinct sequence identity, persistent duplicate protection and metadata bounds.
Together with shared matching, game assignment, existing food/affection, care,
negative relief, lifecycle, storage, catalogue and disclosure regressions:
150 targeted tests passed in 0.988 seconds (slowest 0.073 seconds). Focused Ruff,
strict Mypy and Pyright passed. The staged integration is checked separately
before commit. Native Tk creation was blocked throughout discovery/execution;
no windows, mouse control, live-save access, full suite or CI was used.

Step five is delivered through shared domain matching/fulfillment, application
admission and the existing Pet aggregate/evidence owner. Full-need food/affection
permission and recognized handover semantics remain step six; qualified positive
and long-term producers remain step seven; passive reads, actual generated-wish
balance acceptance and the closing full-suite/OOP review remain step eight.
Parallel horoscope/UI/assets changes are preserved and excluded from staging.


Final isolated staged integration for step five: **150 targeted tests passed in
0.989 seconds**, slowest **0.078 seconds**, none above ten seconds. Focused Ruff,
strict Mypy and Pyright passed for all eight affected production files, with
Ruff also checking all changed tests. The staged controller/test versions exclude
the parallel horoscope hunks; their working copies retain those hunks. No live
saves, test windows, mouse control, full suite or GitHub CI were used.


### Delivery slice 6A: wished-for affection at full needs

Care admission captures one matching affection wish before applying petting.
That actual wished-for stroke is welcome even at affection 100, clamps physical
needs and fulfills its captured identity without incrementing excess strokes or
communicating a fullness boundary. Completion is not continuing permission:
subsequent unrequested strokes follow normal friendship/tolerance rules.

An active explicit refusal still blocks the wish. Too Much Closeness is not
bypassed by wish permission; normal independent recovery/willingness remains
with the existing interaction rules. Sleep/manual care routing is unchanged.
The existing pure care transition carries the assigned identity; PetState
commits the same care/Moodlet path, with no extra store or instantaneous bonus.

40 targeted affection, care-action and helpful-relief tests passed in 0.249
seconds, slowest 0.041 seconds. Focused Ruff, strict Mypy and Pyright passed.
Native Tk creation was blocked; no test windows, mouse, live-save access,
full suite or CI was used. Food/recognition follows in separate commits.


### Delivery slice 6B: original food-transfer context and recognition outcomes

Pure `pet/food_wishes.py` captures up to three original food wishes at a confirmed
handover, settles the snapshot on actual recognition and retains both handover
and recognition times in the Moodlet cause. Wish rotation need not keep the old
active row alive. Later wishes cannot be adopted. Cross-receipt accounted IDs
prevent a goal settled elsewhere from being awarded again. Pending context and
results reuse the existing bounded values/codecs and whole-Pet checkpoint.

Recognized wanted/alternative food grants the original wish's positive outcome;
explicitly excluded food fails that original wish and grants food-wish-disregarded
(+one negative tier, thirty minutes each through three). Explicit exclusion takes
precedence over a competing positive pin. Ordinary nonmatching food is neutral.
These handover outcomes do not change nutrition, needs or instantaneous friendship.
Repeated observations are neutral, while genuinely distinct gifts can stack.
Withdrawal cancels pending context. The pure shared priority now also accepts
original food snapshots; there is no separate priority or reward engine.

Seven new handover tests plus matching/storage/food/persistence regressions passed:
51 tests in 0.042 seconds, slowest 0.009 seconds. Native Tk creation was blocked.
Application custody/recognition and full-need consumption wiring follows in the
next commit; the old live handover entry point is replaced there as one coherent
adapter change. No windows, mouse, personal-save access, full suite or CI.


### Delivery slice 6C: actual handover, recognition and full-need consumption

The existing World interaction now reports actual custody begin, genuine
recognition and completed put-down through application ports. The old desktop
pre-transfer acknowledgment path and superseded generic handover-completion
entry point are removed. Cursor presentation, placement and autonomous pickup
cannot fabricate personal food transfers. Known food may enter the hand for
inspection/put-down without conflating appetite with custody; freshness, reach,
visibility, action/game and sleep admission guards remain.

`ObjectConsumption` captures the original context only after real transfer,
including unknown items, and validates recognition against acquired Memory
facts. A failed transfer rolls back its World/Memory/Pet effects. Original
context survives technical safe-on-ground restore; actual withdrawal cancels
pending receipts, and removed/consumed objects release their markers. Completed
physical put-down releases evaluated records without removing the lasting cause.
No permanent transfer archive, second recognition engine or hidden-World identity
inference was introduced. Existing save codecs remain the persistence owner.

Pure food permission is read by the existing care decision and object-use path.
Wanted personal food is actually eaten at full satiety using the same nutrition,
digestion and consumption transaction, clamped at 100. Explicitly excluded gifts
are not eaten. Recognition has already settled that gift's emotional outcome;
later intake cannot award another wish for the same processing. An alternative
food can satisfy variety even when full satiety leads to put-down instead of
intake. Ordinary nonmatching offers remain neutral. No need-decay/care amount,
friendship bonus, offline user interaction or menu state was invented.

Eight headless physical-flow checks cover presentation versus transfer, desired
full-need consumption, alternatives without intake, unknown-then-identified food,
unwanted put-down, rollback/retry and paired save/restore plus withdrawal.
Existing tests were updated where the approved rules supersede positive awards
for unwanted food or appetite-based custody rejection. Affection, shared
assignment, persistence, ordinary food, finite offline resources and existing
game/social outcomes remain in the targeted regression selection.

257 targeted tests passed in 3.193 seconds, slowest 0.454 seconds. Focused Ruff,
strict Mypy and Pyright passed for all fourteen affected production files.
The exact staged integration is verified below before commit. Native Tk
creation is blocked during discovery/execution. No test windows, mouse control,
live-save access, full suite or GitHub CI; parallel UI/horoscope/assets work is
preserved. System/data documentation now describes the delivered behavior.

Step six is complete. Qualified independent positive/long-term experience
producers remain step seven. Passive reads, generated-wish/day-balance
acceptance and the final full-suite/OOP/slow-test review remain step eight.


Final isolated staged integration for step six: **257 targeted tests passed in
3.156 seconds**, slowest **0.453 seconds**; none exceeded ten seconds. Focused
Ruff, fresh strict Mypy and Pyright passed for all fourteen affected production
files; Ruff also checked the changed tests. The index export excludes parallel
horoscope, UI, character assets and related text/documentation edits. Native Tk
creation was blocked during test discovery and execution. No test windows,
mouse control, live-save access, full suite or GitHub CI was used.
