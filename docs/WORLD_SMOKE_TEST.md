# World desktop acceptance and repeatable smoke checks

## Three-game native acceptance — pending separately

The feature branch adds the Spielen selector, Blackjack and Tic-Tac-Toe.
Targeted rules, timer, Tk/Xvfb and cleanup checks are recorded in the
[minigame delivery plan](MINIGAME_IMPLEMENTATION_PLAN.md). Actual Tk/Xvfb
captures were inspected; those do not establish native Windows behavior.
The owner reported an acceptable initial playtest before requesting larger
Blackjack player cards, a draw pile and automatic next hands. The updated
player panel and restart timing require a subsequent practical playtest.
Do not run working-desktop windows or mouse probes without later authorization.

When native acceptance is authorized, use an isolated save and check:

- Spielen shows exactly the three games; Escape/outside dismissal starts no
  game, and repeat/deferred selection never opens two sessions.
- Click Spielen and leave the pointer on the opening button before moving
  into the selector. It stays open and each game remains selectable.
- RPS retains separate player/Aiko hands, its countdown and existing controls.
- Tic-Tac-Toe blocks input during Aiko's turn, highlights the winning line,
  alternates starts and restarts cleanly after a win or draw.
- Blackjack shows only player cards in its panel. Aiko's hand floats below her
  face, retains its card back through hover/click and flips only after the
  player's turn or an immediate natural/bust result. Speech never replaces it.
- Blackjack player cards are clearly larger, the clickable back pile draws
  exactly one card, and controls stay blocked during dealer/result playback.
  After 2.8 seconds the next hand starts automatically with a concealed hole
  card and the accumulated score. Closing during the pause prevents restart.
- At 1x/2x and both desktop edges, long hands stay readable above the taskbar;
  Windows color-key transparency leaves no Magenta frame. Show/flip/hover do
  not activate another window or trigger pet teasing, dragging or World pickup.
- Move/resize Aiko and toggle topmost while playing. Cards follow the existing
  owners and disappear on close, failed start and shutdown, including mid-flip.
- Close each game and the selector through the window manager as well as its
  Close/Escape controls. Pending turns/flips stop, cards and speech disappear,
  and another game opens normally without leaving Aiko in game mode.
- Only completed units affect care once; reopening has a fresh score, and
  closing an unfinished round gives no reward. The normal save stays untouched.

## Acceptance status

The maintainer reports that desktop acceptance for the current object-interaction
flow is **passed**, recorded on 2026-10-18 before the documentation consolidation.
The following test-only changes preserved that runtime. Local verification at
`5f1bdea` passed 1,146 tests; the final review at `65175f2` reran 126 targeted tests
and found no remaining findings in the three scoped cleanup items.

This is reported practical acceptance, not a claim that every historical matrix
cell has a separately recorded screenshot or exact-SHA sign-off. Earlier open
checklists and test totals are [history](history/README.md), not outstanding work
on the accepted flow. PR #10 remains draft and unmerged. CI for a new pushed
commit must be checked separately; see the [documentation index](README.md).

## Real-time foundation follow-up

The 2026-10-19 time/save foundation changes elapsed-time behavior after the
reported World acceptance. Automated coverage checks suspend-inclusive API
selection, simulated standby, source failure/recovery, long closed intervals,
save migration and replay prevention. It does not constitute a physical
standby/resume acceptance run. Current Windows interactive resume sign-off is
**pending**; do not reuse the earlier World sign-off for it.

Completed local checks for this stage on Windows/Python 3.11.9:

- The full working-tree suite passed **1,166 tests in 259.455 seconds**, with
  no unittest failures, errors or skips. Ruff 0.13.2, strict Mypy 1.18.2
  (188 source files) and Pyright 1.1.414 passed. This is local evidence for the
  foundation committed as `59cab63`, not a remote CI result or physical
  resume sign-off.
- Nineteen new elapsed-time/persistence cases cover source recovery, simulated
  standby, rollback, initialization, long gaps and optional-record migration.
- Both actual Windows uptime readers were exercised; the suspend-inclusive
  reader advanced a real short live interval independently of the active reader.
- Three native Tk launcher runs reused one isolated system-temp save. A
  substituted 12-hour closed interval was counted in full once, two real World
  portions survived, no catalogue meal appeared and the next reopening did not
  replay the interval. This is a launch/save/reopen check, not physical standby.

Native Tk printed `ThemeChanged` diagnostics while destroying test windows
during the full suite. The unittest result above is passed; those teardown
messages do not supply evidence for actual standby/resume behavior.

Use a temporary save or the isolated launcher below, never the normal save.
For that stage, new care/need/friendship/sleep balance was not active.
Stage 2 now supplies the numeric need/mood rules in the maintained guides;
stage 3 supplies friendship loss; stage 4 now supplies adaptive sleep and finite
stock care, recorded in the separate acceptance section below.

- Run briefly, save/close, wait and reopen the same isolated save. Check that
  needs/digestion and `pet.time.lived_seconds` include the closed interval and
  that a second reopen does not replay it.
- Keep the isolated app running across a real Windows standby/resume. Compare
  elapsed progress with the wall interval; World physics/perception must not
  acquire fictitious observations or replay hours of motion. Check toolbar,
  sleeping presentation, care callbacks and bubble timers after resuming.
- Compare a manual wall-clock correction during an active session against
  normal elapsed progression only in an appropriate test environment. Do not
  change the user's system clock merely to run this checklist. Automated injected
  clocks cover forward/backward changes without that machine-wide action.
- Confirm existing stock survives close/reopen unchanged. No catalogue meal
  should appear; closed-time consumption of actual stock is a later stage.

## Stage-2 numeric balance check, 2026-10-19

Two native `DesktopPet` launches used a separate system-temp save. A substituted
one-hour awake absence restored satiety approximately 67, energy 72 and mood
55.52 from the default needs with saved mood 30. Personal petting through
`DesktopPet.interact()` added 25 affection, with no instant energy/mood reward.
The normal save/close/reopen path retained progress without replaying that hour.
The regular user save was not used. This is an actual Tk lifecycle/care wiring
check, not a physical standby test or visual acceptance of the later click and
object-dialogue fixes. Those fixes remain planned.

The full validation totals for stage 2 are recorded in the implementation plan
and documentation index. Use the launcher below for later hands-on acceptance.

## B1: direct click escalation, 2026-10-19

Completed native Windows check: an isolated `DesktopPet` used a system-temp
save, observation/routine/random walking disabled, and ordinary non-cheerful
awake needs. After the sprite had rendered, a visible body pixel was verified
as belonging to that canvas. Both a left-only burst and a mixed left/right
burst of six actual Windows-injected button press/release pairs produced counts
**1, 2, 3, 4, 5, 6**, `click_boundary` and an active irritation deadline.
Pointer position was restored; the normal save was
not used. Preliminary message-only and transparent-area probes did not deliver
sprite clicks and are not counted as acceptance.

Native Tk regression tests additionally exercise the real canvas bindings:
care/game/sleep exclusion, left-story reading and right-story exclusion,
replacement by non-click feedback, and committed World object contact.
Reading and blocked input do not increase the teasing counter. Existing mood,
care and friendship state are not changed by idle teasing clicks; the original
temporary irritation remains in `PetMind`. This does not implement stage-3
friendship penalties or sign off the separate standby test.

The complete native Windows suite passed **1,185 tests in 269.433 seconds**;
Ruff, strict Mypy and Pyright passed with the repository's pinned versions.

Repeat with the isolated launcher: click idle Aiko repeatedly while her reply
is still visible, then repeat during petting, a game, a conversation story and
object inspection. Only the idle click-reply burst should escalate teasing;
left-story clicks advance reading and other active interactions remain exclusive.

## B2 subjective reunion and German dialogue, 2026-10-19

Implemented in `4757da7` (search/memory) and `b984078` (German phrases and
integration). Full Windows/Python 3.11.9 verification passed **1,203 tests in
271.518 seconds**, without unittest failures/errors/skips, plus Ruff 0.13.2,
strict Mypy 1.18.2 (190 source files) and Pyright 1.1.414.

A separate isolated native Tk probe reused
`WorldGuiTests.test_onigiri_subjective_reunion_keeps_new_world_identity`,
but retained real reaction-player `after` callbacks and bubble dwell. Each
selected text was checked against an actual visible native Label. The probe
passed in **70.520 seconds** with **21 displayed text bubbles**. The fixture
drove perception time, movement and animation frames; this is a native
playback/integration check, not a claim of manually dragging every item. Its
temporary save was cleaned up; the normal user save was never read or written.

The observed flow was unknown notice → real pickup/hand identification
(“Ah, ein Onigiri!”) → full/defer/put-down → checked missing place
(“Moment, mein Onigiri ist nicht mehr da. Eben lag es noch hier.”) → search
→ inspect a different physical Onigiri → one found cue
(“Ah, mein Onigiri. Ich hatte dich schon abgeschrieben.”) → safe deferred
placement → rediscover/identify the original portion as an ordinary new
exemplar (“Oh, ein Onigiri! Jetzt erkenne ich es.”). Both physical portions
remained real, resting World objects; no food was consumed while full.

Owner regressions additionally cover unknown/wrong-kind exclusion, one finding
per missing subject, multiple missing portions, currently observed evidence,
existing-stock exclusion, save/restart and ordinary strict stock matching. All
138 object sequences were reviewed, including every full beat sequence, and
rendered for all eleven consumables plus unknown identity. The
[review workbook](DIALOGUE_REVIEW.md) retains baseline copy and implemented
proposals. This record completes B2 and does not sign off later sleep or
physical standby work.

Repeat practically with the isolated launcher below: let a full Aiko identify
and save an Onigiri, move it away outside her attention, let her check the old
place, then place a new Onigiri in reach. Identification during search should
produce one possessive found response; another identification after that
search is an indefinite new-portion response. Unknown sightings alone must
not produce a named found response.

## Stage-3 friendship, contact and neglect, 2026-10-19

The completed stage passed **1,226 Windows tests in 282.452 seconds** and
pinned Ruff, strict Mypy (193 application/tool source files) and Pyright.
The direct-canvas regression separately verifies the rolling one-point click
cap, continuing after the prior reply animation ends, and preserves blocked
care/game/story input. Claimed-object native coverage verifies -0.5, receipt
idempotence, return without refund, actual save and restart.

A separate native probe created its own system-temp save with genuine
accepted petting followed by manual sleep eight hours earlier. Normal desktop
restoration produced approximately **95 → 91** friendship and energy 100.
Closing/reopening the same save deducted only the short new interval, not
another eight hours. Explicit waking did not renew care contact.

For stable injected-input verification the probe then stopped background
render/greeting timers, selected an opaque visible sprite pixel and checked
`WindowFromPoint` against the actual canvas before sending Windows mouse
button events. Seven delivered clicks reached counts 1–7: count 6 displayed
`click_boundary` with no loss, and count 7 deducted **0.25**. The contact clock
remained unchanged. A preliminary run with rendering active missed one
injected click and is not counted as completed input acceptance.

Actual accepted petting then awarded the high-need reduced **0.25**, renewed
contact and displayed native German speech. The toolbar showed
`Freundschaft  91% · Lv 10`. Save/reopen retained the histories; an immediate
accepted repeat renewed contact without another award. The pointer was
restored and all probe windows closed. Only the isolated save was read/written.

This is native restoration, input, visible-label and care/save acceptance.
The eight-hour gap was constructed in the isolated fixture; it is not a claim
of waiting eight hours or physically suspending Windows. Physical standby and
adaptive sleep remain separate. See [current friendship rules](FRIENDSHIP_SYSTEM.md)
and the [stage-3 plan record](CARE_TIME_IMPLEMENTATION_PLAN.md#stage-3-verification-record-2026-10-19).

## Isolated launcher

Close other Aiko instances when doing a practical smoke run. Use
[Aiko_World_Test.bat](../Aiko_World_Test.bat), which selects a temporary test save:

```powershell
.\Aiko_World_Test.bat --scenario curious --stock two
```

A fresh run creates an `aiko-world-smoke-*` directory in system temp and prints its
exact save path and restart command. Profiles are `hungry` (55/55 satiety/energy),
`curious` (76/60) and `full` (100/100). `--stock one` or `--stock two` only seeds
a fresh save; an existing save is not reseeded.

To restart the same isolated session, use the printed path:

```powershell
.\Aiko_World_Test.bat --save-path "C:/exact/printed/temp-folder/state.json"
```

Add `--needs hungry` to change only the selected need values while retaining
World, learned memory, history and friendship. Omit it for an ordinary restart.
The normal save path, including an `AIKO_SAVE_PATH` override, is rejected. The
launcher disables random walks, automatic routine, hardware observation, rhythm
learning and spontaneous speech; required object bubbles and need decay remain.

## Repeat checks after relevant future changes

These are repeatable regression instructions, not an uncompleted acceptance plan.
Use both 1x and 2x when changing geometry, scaling or native item rendering.
The maintained [World rules](WORLD_OBJECT_CONTRACTS.md) define expected behavior.

1. Drop an unknown portion. Aiko notices, approaches, picks up and inspects it
   before identifying it. Depending on appetite she consumes it or safely puts it
   down. Full energy does not prevent selecting a drink into cursor custody.
   With identified stock already present, repeat with two new unknown portions
   to her left, then to her right. The selected investigation survives both
   orientation looks; she looks back and confirms the item before approaching.
   This must not start a missing-stock search or identify the new portion early.
2. Present an unknown portion deliberately before her face. Verify identification
   and assessment, then actual release for handover. Passing through the face
   region must not identify; a deliberate known refusal must remain effective.
3. While Aiko is free and following the cursor, move a known portion continuously.
   It retains its identity and observed place without repeated inspection or a
   phantom missing-item bubble.
4. While she approaches, eats, plays, is petted or is talking, relocate several
   known portions. On attention release she checks learned places left and right,
   announces every confirmed loss individually, then searches. An unknown
   replacement at an old place must not hide the known loss.
5. During that search, verify pickup/inspection of reachable unknown candidates,
   a grounded found bubble for each matching portion and continued route progress
   for the others. A genuinely new candidate must not steal search priority.
6. Hover over Aiko during patrol and candidate inspection. The toolbar opens,
   action buttons remain disabled and movement continues. A direct click may
   produce a busy reply without cancelling the current action. Pin/details and
   settings remain usable.
7. Test both taskbar edges. An item must be reachable before attachment, and a
   portion moved away before the attachment frame must stay out of her hand.
   Falling/rebounding items are not collectible until settled.
8. Restart with two nearby learned portions in the same temporary save. They
   remain distinct and are not reidentified solely because of restart. Later
   hunger recalls known assessed supply without repeating first identification.
9. Check safe sleep/termination during held inspection, complete consumption
   playback and exactly-once nutrition/removal after same-save restart. Original
   user saves must remain untouched.

## Automated protection

Headless owner tests cover perception, memory, orientation, search, custody,
receipts, consumption, migration and rollback. Separate native fixtures cover
actual reach/attachment, input, hover, animation timers, handover and restart.
Renderer tests use standalone Tk components rather than fictional World pickup.
See [tests and current evidence](README.md#validation-and-acceptance) and
[contribution commands](../CONTRIBUTING.md).

## Stage-4 adaptive sleep and finite stock, 2026-10-19

Stage 4 uses the maintained [sleep rules](SLEEP_SYSTEM.md) and
[active plan](CARE_TIME_IMPLEMENTATION_PLAN.md). This partial evidence is separate
from the earlier World flow and from physical machine suspension.

The isolated native Windows probe used a system-temp StateStore, real Tk,
Windows last-input reads and injected mouse movement at a verified opaque
sprite point. The pointer was restored and the normal save was untouched.

- Reconstruct an overnight-to-midday interval from two identified/appraised
  sandwiches and one unknown Onigiri. Both real sandwiches were consumed once;
  the unknown portion remained. The midday state was already awake, with no
  renewed personal contact, reward or autonomous social gain.
- Save, close and reopen the same native app. No portion or interval replayed;
  subsequent need change matched the short real interval.
- Execute manual Sleep/Wake through the native application command path.
  Verify its durable 30-minute protection and no fabricated personal contact.
- Supply already-slept duration only as an explicit isolated fixture. Poll real
  OS input and real clocks: a single brief movement did not wake main sleep.
  Twenty-five repeated injected movements produced a real sustained return;
  instrumented domain waking occurred after **123.5 seconds** of activity,
  with sufficient energy and four fixture sleeping hours. The visible toolbar
  then displayed **Schlafen**. This does not claim four hours of smoke-test time.

The probe deliberately held an idle sprite frame while applying its sleeping
fixture. The owner reported the contradictory visible animation and Wake
command. This was a test-harness defect: the timing observations above do not
establish correct visible sleep animation. Two other probe attempts did not
complete; no repeated successful acceptance is claimed. The test instance ended,
and further visible probes and OS input injection stopped after the owner's
correction. Visual sleep/wake acceptance remains pending.

The native component regressions additionally drive real pickup/inspection/
consumption frames during a sleep food break, one existing search route and
restart after failure. Expiration with an unconsumed held item completes real
put-down before returning to sleep. Component fixtures acknowledge bubble
receipts directly; the separate input probe above used actual real timers.

The first full run exposed superseded fixed-night/permanent-manual-sleep test
expectations and a real unappraised-stock restoration gap. The final code
preserves unappraised portions and requires previous appraisal for historical
intake. Focused cases verify safe custody, wrong remembered places, valid stock
return, bounded failure and exact paired rollback. Automated results and platform limits
are recorded with stage 4 in the active plan.

Physical standby/resume remains **pending**. Injected suspend-inclusive clocks,
paired-stock equivalence and both actual Windows uptime readers are automated
coverage, not permission to suspend the user's working computer or a claim of
physical resume acceptance. Stages 5–6 and promotion to main remain separate.

## Stage-4 owner checks on the actual machine

> **Proposed checklist on hold.** The owner requested architecture and
> verification-scope discussion first. These are not agreed mandatory owner
> tasks, and they do not authorize any new run. The active plan's stage-4
> scope correction takes precedence.

Do these at the owner's chosen time. The agent must not launch local test
windows, inject mouse/keyboard input, suspend the computer or rewrite save
values to create a scene. Use ordinary app controls and real time; do not
freeze rendering or change the system clock. Check the feature-branch build,
not an older process that was already running before the code changed.
A separate save selected through `AIKO_SAVE_PATH` can keep these observations
independent of normal progress; the agent must not create a visible instance
without a new explicit request.

Record the branch revision, approximate start/end times, observed state and
pass/fail for each check. No private input trace is needed.

| Check | Owner action and expected observation | Status |
| --- | --- | --- |
| Visible manual Sleep/Wake | When Aiko is free, choose Sleep. After transient feedback, the actual sleeping pose and Wake control must agree. Choose Wake; normal awake animation and the Sleep control must return, without a permanent idle frame or contradictory command. | Pending owner observation |
| Ordinary main sleep and return | With automatic routine enabled, leave the app running during the expected night window. After 15 minutes of real quiet, Aiko should sleep. One brief input is insufficient. After at least four actual sleeping hours and energy at least 60, two minutes of repeated ordinary input can end sleep early; otherwise the saved expected endpoint requires energy at least 40. A real food break may briefly show awake behavior. Observe the visible transition, without fixture timestamps. | Pending owner observation |
| Physical standby/resume | At a convenient break, note time, needs and any placed stock, then suspend the machine with Aiko running. Resume after at least 15 minutes, or use a normal overnight suspension. Needs and sleep must reflect elapsed time once; energy may recover during sleep. The app must remain responsive with consistent animation/controls. An immediate save/close/reopen must not replay the absence or consume the same stock twice. | Pending owner observation |

A closed-app overnight observation with a few already identified/appraised
portions and a separate unknown portion is an additional useful integration
check: only actual eligible saved portions may be consumed, and reopening must
show the resulting stock without playback. Automated restoration and native
component tests cover this path; it does not require another injected desktop
probe. The three/seven-phase learning milestones and long-duration priority
collisions are covered with injected policy time, so accepting the algorithm
does not require waiting seven real days. Its personal fit can be observed
later during normal use.

## Stage-4 correction: local automated verification, 2026-10-19

The corrected application graph retains live autonomous care and adaptive
sleep. Clock measurement, shared time application and reconstructed resource
use now have explicit owners; active movement/intake remains in World.

A frozen checkout ran locally under Linux/Python 3.11 and Xvfb in a disposable,
network-disabled container: **1,273 tests in 176.808 seconds**, eight Windows-
only skips, no failures/errors. **130 affected headless Windows tests** also
passed in **7.626 seconds**. Static checks passed. No visible test windows,
mouse injection, normal-save writes or GitHub CI were used for this correction.
The three real-timer cases above ten seconds are individually justified in
[the active plan](CARE_TIME_IMPLEMENTATION_PLAN.md#local-verification-and-individual-slow-test-review).
All cases terminate automatically; the frozen-frame desktop probe was not used.

This verifies automatic domain/application and virtual-display behavior.
Physical suspend/resume and visible Windows animation remain unperformed,
separate acceptance. The earlier owner checklist remains a proposal on hold.

## Controlled Tk test time, 2026-10-20

The automated World runtime-flow tests now execute scheduled callbacks with
[ControlledTkTime](../tools/tk_test_time.py), while retaining real Tk widgets,
native geometry, movement, speech, pickup and intake wiring. Their reading and
animation budgets are unchanged; virtual time reaches each deadline without
waiting for that duration on the host. Phase ordering, complete playback,
cancellation and exactly-once effects remain assertions rather than shortcuts
through private phase-completion methods.

Speech/emote, story, functional GUI, menu-focus and Blackjack timer tests use
the same scoped clock. Short standalone animation checks retain native Tk
event-loop timer delivery. Physical standby, user input and visible acceptance
still follow the separate owner checklist above. All automated pet instances
continue to use temporary saves.

The local Windows/Python 3.11 checkout passed **1,437 tests in 215.901 seconds**;
the preceding real-delay run took 319.446 seconds for 1,424 tests. This measured
run was about 32% shorter despite the added clock and concurrent feature cases.
Ruff, strict Mypy and Pyright passed. Installer/process-start and CPU-heavy
policy simulations remain part of the suite; this change does not shorten
application playback durations or replace separate physical acceptance.

## Remaining suite cost and duplicate review, 2026-10-20

A per-test wall/CPU profile of 1,436 tests measured 231.487 seconds, including
fixture setup and cleanup. The groups below are disjoint; class fixtures and
runner/report overhead account for the remaining 2.001 seconds.

| Test group | Wall seconds | Test-interpreter CPU seconds |
| --- | ---: | ---: |
| Integrated GUI, World flows and animation | 106.694 | 101.781 |
| Windows installer and launchers | 70.144 | 1.719 |
| Daily schedules, friendship neglect and offline progress | 18.226 | 18.109 |
| Other domain, asset, component and architecture checks | 34.422 | 33.203 |

Child-process CPU is excluded from the interpreter column. Installer time
includes actual PowerShell, venv, pip, import and launcher work in disposable
copies. The same seven installer tests took 45.450 seconds in the preceding
profile; host/process-start variability prevents a reliable overall speedup
claim against the earlier 215.901-second run. GUI profiling attributes most of
a simple wiring case to application setup, especially Tk roots and real images.

The duplicate full-bar assertion is consolidated with its Level-10 assertion
preserved. Canonical-owner assertions share one application setup; Tk display
probes run once per class in the World/story fixtures. Download repair/reboot
cases exercise the real installer helper without repeating full venv/pip setup;
one automatic-install integration, explicit installation/repeat, broken-venv
recovery, shortcut and both launcher checks remain. All eight download/error
scenarios retain their checks. The disabled-monitor loop is driven directly
instead of waiting for its half-second retry, with a separate real-thread test.

GUI fixtures now use
[create_test_desktop](../tools/desktop_test_support.py), composing the real pet
with a threadless monitor. Two earlier profiling attempts exposed sensor-thread
GC disposing old Tk interpreters on the wrong thread; general widget tests do
not need real GPU subprocesses. Dedicated hardware/provider and worker tests
still cover that boundary. The carried-item hop test also keeps its synthetic
pointer active through perception, preserving both scale checks independently
of the user's actual pointer location.

No slow gameplay scenario was proven unreachable. Month-long absence,
friendship-history bounds and eight-day schedules check distinct behaviors and
remain. The two short native frame-timer checks and bounded thread/process
readiness polling remain; they do not wait through gameplay reading/cooldowns.

The profiled run passed 1,435 cases and found one stale mock-call
expectation for the concurrently extended optional `cursor_gaze_point` input.
After updating that exact expectation, 41 animation/runtime, cursor-pose,
World-flow and hardware tests passed in 10.973 seconds. The separate 54-case
World GUI run also passed. Ruff, strict Mypy (223 source files) and
Pyright passed. Only test fixtures/checks and test guidance changed in this
audit; existing production work, the running pet and personal save were retained.

A later documentation-only rerun reported missing UI-preview targets in four
documents after parallel local asset relocation (`controls/drafts`,
`controls/preview.html`, `main-menu/preview.html`, `games/README.md`). The current
documents now refer to [the shared local handoff](UI_PREVIEW_HANDOFF.md), which
locates the external bundle without requiring private examples in a public
checkout. The archive entry points, drafts directory and handoff section anchor
were verified on disk; all nine repository/documentation tests passed. Existing
local asset relocation and design work were preserved.

After the reference cleanup, a fresh full Windows/Python 3.11 run passed all
**1,436 tests in 181.734 seconds**, including the installer and documentation
checks. Every test pet used a temporary save; the live process and personal
save remained untouched. This final run also confirms the corrected optional
gaze-input expectation and controlled-pointer World checks together.
