# Documentation

Use the maintained guides below for the current implementation. Completed plans
and earlier acceptance checklists are [history](history/README.md), not an active
backlog. There is no remaining implementation stage in the completed World/OOP
and test-cleanup plans.

## Maintained guides

| Topic | Document |
| --- | --- |
| Getting started, privacy and licensing | [Project README](../README.md) |
| Module owners, dependency rules and canonical imports | [Architecture](ARCHITECTURE.md) |
| Attention, identification, learned-place checks, search and custody | [World behavior](WORLD_OBJECT_CONTRACTS.md) |
| Desktop acceptance and repeatable isolated-save checks | [World smoke guide](WORLD_SMOKE_TEST.md) |
| Toolbar, action availability, details and native windows | [UI window contract](UI_WINDOW_CONTRACT.md) |
| Approved VN direction; main menu/settings delivered in 5C, native acceptance pending | [VN interface design](UI_VN_DESIGN.md) |
| Approved local preview bundle, cross-chat handoff and asset readiness | [UI reference handoff](UI_PREVIEW_HANDOFF.md) |
| Packaged JSON, SQLite saves, strict import, recovery and time | [Data and saves](DATA_AND_SAVES.md) |
| SQL-9 field preservation, timings and final OOP review | [SQLite acceptance](SQLITE_ACCEPTANCE_REVIEW.md) |
| Food, digestion, workload and item graphics | [Food system](FOOD_SYSTEM.md) |
| Adaptive sleep, input learning and finite closed-time care | [Sleep rules](SLEEP_SYSTEM.md) |
| Continuous friendship from mood/Moodlets, personal contact and neglect | [Friendship rules](FRIENDSHIP_SYSTEM.md) |
| Need rewards and overall mood | [Fun and mood](FUN_MOOD_SYSTEM.md) |
| Unterhalten, online sayings/jokes/facts and the local horoscope book | [Social content](SOCIAL_CONTENT.md) |
| Animation profile and playback timing | [Animation timing](ANIMATION_TIMING_PROFILE.md) |
| V3 Idle, facial reactions, mood and continuous sway | [V3 character expressions](V3_CHARACTER_EXPRESSIONS.md) |
| Numeric base mood, bounded emotional modifiers and spoken game reactions | [Emotional base and reactions](EMOTIONAL_BASE_AND_REACTIONS.md) |
| Source installation on Windows | [Windows setup](WINDOWS_SETUP.md) |
| Branches, reviews and CI | [Development workflow](GITHUB_WORKFLOW.md) |
| Existing media and its capture limitations | [Media gallery](MEDIA_GALLERY.md) |

[Contributing](../CONTRIBUTING.md) gives local test and quality commands;
[CHANGELOG](../CHANGELOG.md) summarizes current unreleased changes and milestones.

## Planned changes, not implemented

| Topic | Status and document |
| --- | --- |
| State-dependent Idle sequences, V3 reuse and grounded gestures | Implemented in six local commits; [Idle V3 behaviour plan](IDLE_V3_BEHAVIOUR_PLAN.md) records module owners, transitional assets, focused tests and 2,417 passing tests plus all local static gates. Assets unchanged; practical review pending. No push or merge. |

## Validation and acceptance

Local horoscope completion (2026-10-26): 206 targeted integration checks pass,
including retired-book/clock coverage and actual Windows/Tk
drag, reading, replay, expiry and restart. Repository Ruff and strict Mypy pass
on an isolated Git-tree export. The [completion record](horoscope/LOCAL_HOROSCOPE_IMPLEMENTATION_PLAN.md#completion-verification-2026-10-26)
separates existing repository test/Pyright failures reproduced on the base
commit from the local book work. Parallel character files and the normal save
remain outside this completion.

Latest spontaneous-speech cleanup (PL-6C): **235 targeted tests in 8.699 s**,
zero failures/errors/skips, longest **0.648 s**, plus scoped Ruff, fresh strict
Mypy for three production modules and Pyright for twelve source/test files.
The [delivery record](CARE_TIME_IMPLEMENTATION_PLAN.md#pl-6c-delivery-grounded-spontaneous-comments-and-generic-removal)
records exact removal of fifty generic sequences, eight fatigue-only event
reassignments, all 992 protected event definitions unchanged, and silence when no
real short-comment topic fits. Spontaneous speech no longer enters requested
Plaudern. No windows, mouse control, personal-save access, live API or CI.
Final complete-suite/OOP acceptance remains PL-7.

Latest social/negative/long-term story slice (PL-6B): **309 targeted tests in
14.947 s**, zero failures/errors/skips, longest **1.687 s**, plus scoped Ruff,
fresh strict Mypy for three production modules and Pyright for seven source/test
files. The [delivery record](CARE_TIME_IMPLEMENTATION_PLAN.md#pl-6b-delivery-social-negative-and-long-term-story-families)
covers literal API references, incident attribution, poor-care after-effects and
all six modeled long-term feelings. Eleven other catalogue sources and 1,093
non-talk definitions are unchanged. PL-6C and final PL-7 acceptance remain.
No windows, mouse control, personal-save access, live API, CI or full-suite run.

Latest game/food/affection story slice (PL-6A): **240 targeted tests in 8.734 s**,
zero failures/errors/skips, longest **0.595 s**, plus scoped Ruff, fresh strict
Mypy for three production modules and Pyright for eight source/test files.
The [delivery record](CARE_TIME_IMPLEMENTATION_PLAN.md#pl-6a-delivery-game-food-and-affection-story-families)
covers concrete gameplay, original goals, intake/handover, welcome closeness and
relationship/emotional coloring. All ten other catalogue sources and 1,093
non-talk definitions remain unchanged. PL-6B/C and final PL-7 acceptance remain.
No windows, mouse control, personal-save access, live API, CI or full-suite run.

Latest Plaudern selection slice (PL-5): **202 targeted tests in 6.806 s**, zero
failures/errors/skips, longest **0.586 s**, plus scoped Ruff, fresh strict Mypy
for four production modules and Pyright for eight source/test files. The
[delivery record](CARE_TIME_IMPLEMENTATION_PLAN.md#pl-5-delivery-evidence-based-requested-plaudern)
records cause weighting, actual wish/result boundaries, requested/spontaneous
separation and the first 24 complete grounded stories replacing all 60 old talk
entries. All 1,093 non-talk definitions are unchanged; later text coverage and
spontaneous filler cleanup remain PL-6. No windows, mouse control, personal-save
access, live API, CI or full-suite run.

Latest social-content evidence slice (PL-4): **178 targeted tests in 4.831 s**,
zero failures/errors/skips, longest **0.539 s**, plus scoped Ruff, fresh strict
Mypy for ten changed production files and Pyright for twelve source/test files.
The [delivery record](CARE_TIME_IMPLEMENTATION_PLAN.md#pl-4-delivery-original-social-content-evidence)
covers original parts/attribution, full playback versus cancellation, qualified
causes, SQLite restart/cleanup and unchanged body-free repetition receipts.
No windows, mouse control, personal-save access, live API, CI or full-suite run.

Latest Blackjack result-evidence slice (PL-3): **107 targeted tests in 3.300 s**,
zero failures/errors/skips, longest **0.281 s**, plus scoped Ruff, fresh strict
Mypy for nine production roots and Pyright for eleven source/test files. The
[delivery record](CARE_TIME_IMPLEMENTATION_PLAN.md#pl-3-delivery-settled-blackjack-result-evidence)
covers all seven actual decisions, reveal/settlement ordering, cause propagation,
old/new SQLite snapshots and original cumulative progress. No windows, mouse
control, personal-save access, live API, CI or full-suite run.

Latest RPS result-evidence slice (PL-2): **91 targeted tests in 2.948 s**, no
failures/errors/skips, longest **0.261 s**, plus scoped Ruff, fresh strict Mypy
for ten changed source modules and Pyright for all twelve changed Python files.
The [delivery record](CARE_TIME_IMPLEMENTATION_PLAN.md#pl-2-delivery-revealed-rock-paper-scissors-result-evidence)
covers actual reveal, cause propagation, old/new SQLite snapshots and cleanup.
No windows, mouse control, personal-save access, live API, CI or full-suite run.

Latest dialogue-source cutover (PL-1B): **125 targeted tests in 2.743 s**, no
failures/errors/skips, longest **0.303 s**, plus scoped Ruff/strict Mypy/Pyright.
All 1,153 definitions and their global order match the PL-1A baseline; 1,776
seeded selections match the old source. The
[delivery record](CARE_TIME_IMPLEMENTATION_PLAN.md#pl-1b-delivery-indexed-catalogue-with-unchanged-sequences)
distinguishes this focused acceptance from the earlier full-suite results below.
No windows, mouse control, personal-save changes, live API or CI were used.

Latest complete acceptance after the Social change (2026-10-25): **1,865 reported
tests in 98.868 s**, zero failures/errors, **112 display-dependent skips**. No test
over ten seconds; longest **8.640 s**. Configured Ruff, strict Mypy (**343 sources**)
and repository Pyright pass. The [Social-change OOP review](SQLITE_ACCEPTANCE_REVIEW.md#social-change-full-acceptance-2026-10-25)
records owner/migration boundaries, parallel workspace scope and one corrected
codec duplicate fixture (four targeted cases rerun successfully). Native windows,
mouse control, personal-save access and CI remain outside this run.

Latest social follow-up (2026-10-25): restart-safe introduction rotation and
**100 receipts per category** passed **171 targeted tests in 7.261 s**, no skips,
longest **1.091 s**, plus scoped Ruff/Mypy and repository Pyright. The
[social delivery record](CARE_TIME_IMPLEMENTATION_PLAN.md#social-follow-up-persistent-introduction-rotation-and-100-receipts-2026-10-25)
includes the backed-up SQLite v1-to-v2 upgrade and legacy-history coverage.
The full-suite result above includes this follow-up; the earlier results below
apply only to their named baselines.

Earlier complete local acceptance (2026-10-25), after the time/save, wish-card and
game input corrections: **1,862 reported tests in 96.257 s**, zero failures/errors,
**112 display-dependent skips**. No test exceeded ten seconds; longest **8.847 s**.
Configured Ruff, fresh strict Mypy (**343 sources**) and repository Pyright pass.
The [post-correction OOP review](SQLITE_ACCEPTANCE_REVIEW.md#post-correction-local-acceptance-2026-10-25)
records the reviewed owners, parallel workspace scope, legacy exporter lint
findings and native Windows acceptance limits. No further product change was
required by that review; no native test windows, mouse control or CI were used.

Latest runtime correction (2026-10-24): [shared fractional time contract](CARE_TIME_IMPLEMENTATION_PLAN.md#time-contract-correction-after-sql-9-runtime-report).
The prior OOP acceptance missed inconsistent elapsed endpoints. Pet and World
now use the same plan-owned endpoint; strict storage bounds remain unchanged.
**226 affected-owner tests passed in 36.938 s**, no skips, longest **3.886 s**.
The existing personal save is not reset or reimported.

Historical SQLite acceptance (2026-10-24): **SQL-1 through SQL-9 delivered**.
The complete local workspace run reported **1,844 tests in 95.936 seconds**,
zero failures/errors and **112 display-dependent skips**. No test exceeded ten
seconds; longest **8.657 s**. Whole Ruff, strict Mypy and Pyright passed after
three stale horoscope test usages were corrected. The [SQL-9 review](SQLITE_ACCEPTANCE_REVIEW.md)
records owner/field preservation, parallel-work scope and native limitations.
No personal save, test windows, pointer automation or CI was used.

Earlier Social Optimization status (2026-10-24): the renewed wish/Moodlet
slices 1–8 passed [local step-8 acceptance](CARE_TIME_IMPLEMENTATION_PLAN.md#delivery-slice-8d-generated-care-acceptance-and-final-oop-review).
The isolated candidate completed 1,701 tests in 77.761 seconds with 111 explicit
native-display skips, plus whole Ruff, strict Mypy and Pyright. Generated care
scenarios support ordinary friendship level seven/eight and intensive level ten.
Native visual/input acceptance and the reported AppHang remain separate; this
no-window run does not verify them. [Earlier open-work reports](CARE_TIME_IMPLEMENTATION_PLAN.md#documentation-audit-and-open-work-2026-10-23)
are historical where superseded. The older results below apply to their named
baselines, not automatically to current HEAD.

- Social API delivery on 2026-10-19: frozen code `644c367` passed **1,371 native
  Windows tests in 301.549 seconds**, no failures/errors/skips, plus full pinned
  Ruff, strict Mypy (218 source files) and Pyright. Separate live API checks
  reached 2/2/2 ready buffers and exercised all three formats in an isolated
  native Tk host. The [delivery record](SOCIAL_CONTENT_IMPLEMENTATION_PLAN.md#final-verification)
  distinguishes focused checks, corrected failures and the final full gate.
  Maintainer visual acceptance remains separate; no merge was performed.

- Three-game delivery on 2026-10-19: the final `8dc61e7` snapshot passed
  **1,318 local Python 3.11/Xvfb tests in 177.825 seconds**, eight platform
  skips, no failures/errors. Full pinned Ruff/Mypy/Pyright passed (212 source
  files for Mypy), alongside per-commit targeted checks and 94 headless Windows
  cases. The [delivery record](MINIGAME_IMPLEMENTATION_PLAN.md#delivery-evidence)
  includes corrections and actual Tk capture review. Native Windows card
  transparency/focus/input acceptance remains separate; no merge was performed.

- Stage 3 on 2026-10-19 passed **1,226 native Windows tests in 282.452
  seconds**, no failures/errors/skips, plus pinned Ruff/Mypy/Pyright (193
  application/tool source files). Six production-policy daily comparisons,
  both actual care schedules, rolling caps, sustained neglect, migration and
  restart passed. The isolated [native return/input/care probe](WORLD_SMOKE_TEST.md#stage-3-friendship-contact-and-neglect-2026-10-19)
  also passed; the [active plan](CARE_TIME_IMPLEMENTATION_PLAN.md) records
  stage 3 complete. Sleep and physical-standby acceptance remain separate.

- B2 on 2026-10-19: `4757da7` adds subjective search reunion and `b984078`
  adds natural German object phrases and integrated regression. **1,203 native
  Windows tests in 271.518 seconds** passed without failures/errors/skips,
  alongside pinned Ruff/Mypy/Pyright (190 source files). The separate
  [real-timer Onigiri probe](WORLD_SMOKE_TEST.md#b2-subjective-reunion-and-german-dialogue-2026-10-19)
  passed in 70.520 seconds with 21 rendered text labels. All 138 object
  sequences were reviewed, 90 changed; the workbook preserves baseline copy
  and records delivered replacements. Save versions and menu names are unchanged.

- B1 direct-click verification on 2026-10-19 passed **1,185 tests in 269.433
  seconds**, without failures, errors or skips, plus pinned Ruff/Mypy/Pyright.
  Actual Windows-injected left-only and mixed-button bursts reached counts
  1–6 and the existing irritation response in isolated sessions; care/game/
  story/object exclusions remain covered by native Tk tests. See the
  [B1 smoke record](WORLD_SMOKE_TEST.md#b1-direct-click-escalation-2026-10-19).
- Stage-2 need/mood verification on 2026-10-19 passed **1,177 tests in 258.671
  seconds**, with no failures, errors or skips. Ruff 0.13.2, strict Mypy 1.18.2
  (188 application files) and Pyright 1.1.414 passed. Two isolated native Tk
  launches verified restored values, care and save/reopen without replay;
  [physical standby acceptance remains pending](WORLD_SMOKE_TEST.md#stage-2-numeric-balance-check-2026-10-19).
  These are local results; ordinary feature pushes do not trigger full remote CI.

- Local real-time/save-foundation verification on 2026-10-19 passed **1,166
  tests in 259.455 seconds**, Ruff, strict Mypy and Pyright. A native isolated
  launch/save/reopen check counted a substituted 12-hour absence once and
  preserved finite stock. Actual physical standby/resume acceptance remains
  [pending separately](WORLD_SMOKE_TEST.md#real-time-foundation-follow-up).
- Maintainer-reported desktop acceptance for the current World interaction flow
  is **passed**, recorded 2026-10-18. This does not invent individual sign-offs for
  every old matrix cell. Later time-foundation changes have their own
  [validation and resume checklist](WORLD_SMOKE_TEST.md#real-time-foundation-follow-up).
- Local full verification at `5f1bdea`: **1,146 tests in 258.742 seconds**, no
  failures, errors or skips, using Python 3.11.9, Pillow 11.3.0 and native Tk.
  Ruff 0.13.2, strict Mypy 1.18.2 (188 source files) and Pyright 1.1.414 passed.
- The final scoped OOP review at `65175f2` reran **126 targeted tests**. Menu
  selection, actual custody-guard reachability and the separate feedback
  integration were verified; no new scoped findings remained.
- CI portability follow-up: all 48 WorldGui cases pass on both 1,024- and
  1,280-pixel simulated taskbars with a neutral pointer inside the simulated
  desktop (31.900 and 31.536 seconds). The eight affected cases also pass on
  the normal wider desktop (6.183 seconds). Only four scene-helper starting
  positions changed; test methods, assertions and production code are unchanged.
- Remote CI must pass for the newly pushed commit. The
  [Tests workflow](https://github.com/Lexoniarus/aiko-desktop-pet/actions/workflows/tests.yml)
  runs Linux Python 3.11/3.13 and Windows jobs. Prior run links and local test
  results are not a green status for a different SHA.
- The maintainer authorized merging
  [PR #10](https://github.com/Lexoniarus/aiko-desktop-pet/pull/10) on 2026-10-18,
  subject to final review and green checks for its current head. Verify the
  resulting `main` push workflow separately after merging.

Detailed commit-specific evidence is in the
[completed test ownership record](history/TEST_OWNERSHIP_FOLLOWUP_PLAN.md).

## Optional design references

[Integration boundaries](INTEGRATION_ARCHITECTURE.md) document the existing
application contracts and explicitly unimplemented external transports.
[Minigame candidates](MINIGAME_CANDIDATES.md) are exploratory research, not an
approved roadmap or a dependency list for the running application.
The separate [three-game implementation plan](MINIGAME_IMPLEMENTATION_PLAN.md)
records the selected Blackjack/Tic-Tac-Toe scope, the Spielen submenu and the
player-window/desktop-card split, delivered on the current feature branch.
Its per-commit evidence distinguishes targeted checks, final validation and
separate native Windows acceptance. These additions are not merged into main.

## Preserved product concepts

The [selected social expansion plan](SOCIAL_EXPANSION_PLAN.md) records the
implemented short one-line jokes/quotations under Sprüche and shared timing,
including the final-text allowance and 800 ms punchline pause. The AstroWay
horoscope prototype is **rejected; full replacement is decided**, with no API
fallback or parallel mode. The [local book replacement plan](horoscope/LOCAL_HOROSCOPE_IMPLEMENTATION_PLAN.md)
defines module ownership, reuse/retirement, once-daily continuation, World book
use and save migration. Its [approved German content reference](horoscope/book-reading-reference.de.md)
shows Aiko remaining herself while reading a complete book entry and optionally
commenting. The old twelve pilots are rejected; the implemented catalogue has
96 newly authored entries. A hat is outside this version. Tarot remains planned.

The following owner-supplied concepts were recorded on 2026-10-19. They preserve
future product direction, with explicit comparisons against main after PR #10.
They describe proposed extensions rather than currently implemented behavior;
recording them does not select the next feature or approve a delivery schedule.

| Concept | Scope |
| --- | --- |
| [Social and entertainment](SOCIAL_ENTERTAINMENT_CONCEPT.md) | German jokes/facts, content APIs, local EN-to-DE translation, cache, initiative/settings and shared quiz preparation |
| [Adaptive cursor perception and interaction](ADAPTIVE_CURSOR_CONCEPT.md) | State-sensitive startle/trust, flight, curious approach/touch and reliable direct interaction through existing owners |

The social concept connects the [minigame catalogue](MINIGAME_CANDIDATES.md)
to the proposed content/translation pipeline. Cursor behavior shares attention
and presentation owners but does not depend on online sources or translation.

## Balance proposals

The latest discussed need, mood, friendship and simple sleep model has now been
accepted as the basis for [implementation planning](CARE_TIME_IMPLEMENTATION_PLAN.md).
The real-time/save foundation is committed and pushed (`59cab63`); stage 2
now implements need/mood balance, and stage 3 supplies progressive friendship.
Stage 4 supplies [adaptive sleep and finite unattended care](SLEEP_SYSTEM.md).
The original discussion disclaimers and superseded examples remain historical context; the plan identifies the latest baseline
and the small details to settle during delivery. Maintained guides distinguish
implemented rules from remaining expression/context tuning. Separate
fixes cover [idle repeated clicks](CARE_TIME_IMPLEMENTATION_PLAN.md#b1-restore-annoyance-from-repeated-direct-clicks-while-idle)
and [subjective object reunion/German phrases](history/OBJECT_RECOGNITION_DIALOGUE_FIX_PLAN.md),
both implemented and verified. The latter link is the completed delivery record.

The [friendship balance proposal](FRIENDSHIP_BALANCE_PROPOSAL.md) preserves the
candidate care gains, real-time absence losses and negative-interaction values
discussed on 2026-10-19, including the later progressive upkeep factor and timed
neglect rules. Its stage-3 revision used shared +0.75/two-hour and +5/24-hour gain ceilings,
gentler lower upkeep and comparisons from two to eight care visits. Those are
historical figures. Current [continuous friendship](FRIENDSHIP_SYSTEM.md) replaces
instant care/wish rewards with elapsed mood/Moodlet flow and progressive factors;
old reward fields survive only as save compatibility metadata.

The [need balance and daily care proposal](NEEDS_BALANCE_PROPOSAL.md) records
real-time need rates, care/food effects and an eight-period example day with
eight hours of sleep. It connects demanding level-10 maintenance with a good
relationship under average care. The arithmetic is illustrative, not a runtime
playtest; revised energy values and withdrawn suggestions are explicit. The
later consumption section records bounded hardware/input hunger surcharges,
weaker digestion protection, a smaller energy surcharge and repeated-day food
examples; normal elapsed time requires feeding independently of hardware load.
The [combined example day](NEEDS_BALANCE_PROPOSAL.md#combined-example-day-with-needs-mood-sleep-and-friendship)
now calculates the five needs, target/actual mood, normal sleep and individually
credited friendship together under the historical reward model, with explicit
assumptions and no current-runtime claim.
The later [four-phase combined day](NEEDS_BALANCE_PROPOSAL.md#combined-four-phase-average-care-day)
bundles sufficient care into four visits and settles around levels 7–8, with
need minima above 40 and actual mood around 48–79. Four visits with insufficient
food/talk do not produce the same result. The later generated-wish scenarios and continuous friendship passed the
[level-seven/eight versus level-ten acceptance](CARE_TIME_IMPLEMENTATION_PLAN.md#delivery-slice-8d-generated-care-acceptance-and-final-oop-review).
New positive experiences change the old mood-only reference values.

The [mood balance proposal](MOOD_BALANCE_PROPOSAL.md) records the equal need
contributions, deficit deductions and target limits, faster decline under severe
deficits, two-point-per-minute recovery and real-time examples. Its current numeric rules are implemented in [Fun and mood](FUN_MOOD_SYSTEM.md);
contextual Moodlets, wishes and the status UI are delivered. The master plan
separates completed local acceptance from later experience-based dialogue.

The [adaptive sleep proposal](ADAPTIVE_SLEEP_PROPOSAL.md) records the learned
quiet window, three/seven-phase learning milestones, 15-minute sleep onset,
nap/recovery rules, early-waking conditions and real-time continuation while
closed or suspended. Habit learning uses only actual repeated mouse/keyboard
input, inactivity and known off/standby state; app timestamps, manual commands
and weighted scoring are excluded. It also records conflict priority, 30-minute
manual-control protection and sleep-type wake thresholds. Food breaks use satiety thresholds
20/40, one bounded zero-hunger search and identified available stock while closed.
Expected rhythm remains distinct from observed activity, and remaining transition
details are resolved in the [stage-4 runtime guide](SLEEP_SYSTEM.md).

## Dialogue editorial review

PL-1B now loads the unchanged dialogue catalogue from explicit topic sources
under `aiko_pet/data/dialogues/de/` through one index and `DialogueBook`. The
[source format](DATA_AND_SAVES.md#character-copy) explains file/order validation;
the [PL-1A inventory](PLAUDERN_SOURCE_INVENTORY.md) records protected and later
removal scope. Generic bubble removal remains PL-5/PL-6C, not this source move.

The [bubble dialogue review workbook](DIALOGUE_REVIEW.md) is a historical
whole-sequence snapshot, preserving original rows and B2 review decisions.
It does not mean all current dialogue is unreviewed. The subsequent complete
German revision and schema migration are recorded in the
[dialogue revision plan](DIALOGUE_REVISION_PLAN.md); runtime JSON remains the
source of current text and filters. Future speech about concrete active Moodlet
causes is a separate planned conversation feature.

## Keeping documentation current

Maintain behavior in the World contract, ownership in the architecture guide and
practical instructions in the smoke guide. Add concise changes to the single
Unreleased changelog section. Archive completed delivery ledgers with their
original counts, proposals and baseline dates; do not promote their superseded
rules or pending wording back into current guidance.
