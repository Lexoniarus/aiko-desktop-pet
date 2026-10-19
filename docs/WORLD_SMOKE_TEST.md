# World desktop acceptance and repeatable smoke checks

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
friendship loss and adaptive sleep remain pending.

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
