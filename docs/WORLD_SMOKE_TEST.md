# World investigation and consumption — practical retest

The first practical test found missing investigation/feedback, truncated drink
playback and Magenta item fringes. Corrections are implemented on
`feature/world-foundation`. On 15 October 2026 the user reported that the revised
basic flow at `ea4361f` now looks correct; longer-term behavior remains to be
observed. Unreported boundary/restart cases below remain open.
[Draft PR #10](https://github.com/Lexoniarus/aiko-desktop-pet/pull/10) remains
unmerged. See [delivery/evidence](WORLD_OBJECT_IMPLEMENTATION_PLAN.md) and
[behavior contracts](WORLD_OBJECT_CONTRACTS.md).

On 16 October, the user confirmed successful edge pickup in the updated build.
They also reported slow approach/possible repeated loops. Keep that observation
open for separate behavior analysis; it is not claimed solved by the edge-grip
correction. The complete left/right 1x/2x native checklist remains to be checked.

## Isolated launcher

Close other Aiko instances. Double-click [Aiko_World_Test.bat](../Aiko_World_Test.bat)
for the hungry profile (satiety/energy 55). To reproduce the reported levels:

```powershell
.\Aiko_World_Test.bat --scenario curious
```

This starts at satiety 76 and energy 60. `--scenario full` starts at 100/100.
Every fresh run creates a different `aiko-world-smoke-*` directory in system
temp. The console prints its exact path and restart command. Existing explicit
save paths are reused without reseeding. The normal user save, including an
`AIKO_SAVE_PATH` override, is not used; selecting that path is rejected.

The launcher prefers `.venv`, otherwise the Python launcher. Runtime requires
Python/Tk only. Pillow is a development/build dependency. All profiles disable
random walks, automatic routine, hardware observation, rhythm learning and
spontaneous speech. Required object bubbles remain enabled. Normal need decay
continues; no World consumption happens while closed.

## Persistent memory and shortened retrieval — 16 October 2026

Start a fresh `--scenario full` session and keep the printed temporary save path.
Drop Onigiri and Energy Drink, one at a time. Let Aiko investigate and put both
down. Quit normally, then reopen that exact save without overrides. She should
retain their identity/inspection, release object gaze and continue normal
interaction without lifting them again just because of the restart.

To test later hunger immediately, quit and reopen the same isolated save with:

```powershell
.\Aiko_World_Test.bat --save-path "C:\exact\printed\temp-folder\state.json" --needs hungry
```

`--needs` explicitly sets only satiety/energy to the selected test profile
(`hungry`: 55/55, `curious`: 76/60, `full`: 100/100) and reanchors its pet time.
World, learned knowledge, food history and friendship remain intact. Omit the
option for ordinary restart; `--scenario` alone never reseeds an existing path.
The normal save path remains rejected, including with this override.

- [ ] Aiko names her current need and recalls the known supply. “Aufgehoben”
  belongs only to a confirmed deliberate reserve, not an interrupted action.
- [ ] Known inspected stock uses approach, pickup, full consumption and outcome.
  No repeated inspect/recognize/desire bubbles. Grasp alone changes no needs.
- [ ] First discovery and cursor handover still use their separate full routes.
- [ ] An unwanted known supply lets her follow the cursor normally, including
  after restart and at both sides/scales. A later need activates retrieval.
- [ ] Close during pickup/holding, after put-down or during consumption, then
  reopen the same path. Unconsumed items recover grounded; inspection knowledge
  remains, recovery invents no observed pose, and consumed items/effects do not
  return. Running actions are not resumed.
- [ ] A remembered missing portion gets a bounded local search and one missing
  bubble; it does not keep Aiko looking at or revisiting an absent target.

The existing 30-second pause after consumption still limits renewed seeking of
another already inspected supply. Allow that pause when testing both together;
first investigation of a different unknown item remains independent of it.
Approach pacing/possible repeated loops remains a separate observation.

## What the complete sequence should show

Use one object at a time initially. Bubbles normally remain readable for
1.8–3.5 seconds; this is a deliberate multi-step sequence, not an immediate
feeding click. Ground pickup/put-down lasts 1.41 s, held inspection at least
1 s, and the existing complete consumption clip lasts about 3.59 s.

Record commit, Windows version, primary-monitor/taskbar setup, display scaling
and sprite scale. Repeat visual/input checks at 1× and 2×.

- [ ] Press and hold a food/drink choice. One cursor portion appears; no needs
  change from selection or carrying. Cursor, ground and hand images have clean
  edges on both bright and dark desktop backgrounds, without a purple fringe.
- [ ] Hold near Aiko until recognition and a willingness/refusal bubble. Release
  in the handover area to offer; holding alone transfers nothing. You may release
  once willingness is signaled, without waiting for preview speech to disappear.
- [ ] Accepted handover visibly holds the item, examines/identifies it and
  announces use before consumption. Nutrition/energy changes once at the visible
  consumption start. Moving the pointer over Aiko after release must not cut
  the consumption clip short. Human handover retains normal care effects.
- [ ] Release elsewhere above the taskbar: the portion falls without bouncing
  and remains resting. Move away from Aiko/active controls to allow approach;
  keeping random walks off must not prevent object-directed walking.
- [ ] In `curious`, drop Onigiri within roughly 1–2 character widths. Aiko notices
  it, comments, approaches, picks up, holds/examines, identifies it and decides
  she does not need it now. She animates put-down and says she keeps it for later.
  Satiety does not gain meal effects, and the same item is not repeatedly lifted.
- [ ] In fresh `hungry`, drop Onigiri: the same investigation leads to a wanted
  decision and complete consumption. No human-care/friendship reward is granted
  for autonomous use. A known deferred portion can become wanted at later hunger
  without repeating the surprise/discovery story.
  Already inspected stock uses recall, pickup and consumption, followed by the
  outcome; it must not repeat inspect/recognize/desire bubbles. First-time
  investigation and accepted cursor handover retain their full separate routes.
- [ ] In fresh `curious`, drop Energy Drink: energy around 60 motivates use after
  investigation. Energy rises by up to ten; satiety and digestion do not gain food
  effects. Renewed supply seeking of examined items pauses for 30 seconds after
  consumption; a different unexamined ground item can still be investigated.
- [ ] Leave Onigiri and Energy Drink together, with hunger and energy around
  66. After finishing the Onigiri, Aiko investigates the drink without the
  former 30-second wait. At energy above 60 she puts it down for later; first
  investigation is independent of the consumption threshold.
- [ ] In `full`, offered food is visibly refused and falls. Ground food is still
  investigated and put down for later. Existing capacity limits remain food ≥96
  and drink at 100; even a small natural energy deficit permits a human drink
  offer, while autonomous drink use requires energy ≤60.
- [ ] During held inspection, request sleep, talk or a game. The unconsumed item
  is put down before the requested action. During pickup after grasp, Aiko first
  reaches the safe held pose, then puts down. No meal effect occurs from grasp
  or interruption. A deliberate action after consumption cannot recreate food.
- [ ] Escape/input-capture loss cancels a carry without consumption or a duplicate.
  Release outside the supported primary-monitor surface discards it with brief
  feedback. Sleeping/busy Aiko does not silently queue an accepted offer.
- [ ] Check taskbar/screen edges, scale changes, item layering, focus,
  click-through and stacking. Existing toolbar pin, settings and game controls
  stay usable. Ambient speech/notifications do not overwrite object-phase bubbles.
- [ ] Repeat at both extreme ground edges at 1x and 2x. First place Aiko within
  about two character widths of the tested edge so the item is observable.
  Aiko walks to the
  closest permitted standing position, bends, and the portion snaps into her
  hand at pickup frame 4. Her full window remains on-screen. In `full`, the
  drink is examined and put down at her feet, visibly inward from its original
  edge position; it remains recognized and releases gaze. In `hungry`, verify
  the same pickup leads to normal consumption. Moving Aiko away before grasp
  must prevent acquisition from the old standing position.
- [ ] During Onigiri consumption, the portion overlaps the fingers in front of
  the character at both scales. Compare the [grip calibration](media/world-eating-grip-comparison.png)
  (source composition, not a native capture). Consumables stay in front of the
  character during pickup, holding and put-down too; no extra hand mask is drawn
  over them. The eating calibration changes neither item pivots nor ground/cursor
  placement.
- [ ] After inspecting and deferring the drink at energy 65–66, Aiko releases
  object gaze and resumes normal cursor/ambient interaction. The recognized
  portion stays remembered at its observed location and is not picked up again
  until wanted (autonomous energy threshold 60, normal retry rules still apply).

Start a fresh profile when comparing need-specific outcomes; a previous meal or
drink changes desire. Missing desire must still permit first investigation.

## Save/restart the same session

Keep at least one unconsumed portion and quit normally. Reuse the exact printed
path, rather than creating another profile:

```powershell
.\Aiko_World_Test.bat --save-path "C:\exact\printed\temp-folder\state.json"
```

- [ ] Ground portions retain identity and valid position. Unconsumed cursor-held,
  falling or pet-held portions recover grounded, without resuming input/actions.
- [ ] Consumed portions do not return and effects do not repeat. Saving still
  writes Pet and World together atomically with outer schema version 1.
- [ ] Learned identity, inspection and confirmed own placement survive reopening.
  Known unwanted portions release gaze and do not trigger another investigation.
  Old saves without the optional memory section start without that knowledge;
  unidentified sightings stay unidentified. No World item is eaten while closed.
- [ ] A later need produces a truthful hunger/energy recall naming the known
  supply, then approach, pickup and the complete consumption clip. There is no
  repeated examination or "Das ist ..." recognition. If needs change before use,
  Aiko declines visibly and puts it down. A remembered missing target is searched
  locally for at most two seconds, then dismissed with one bubble.

## Automated evidence

16 October persistent-memory follow-up: 907 tests passed on Windows/Python 3.11
in 210.6 s, with pinned Ruff, strict Mypy (169 source files) and Pyright green.
Cold restoration covers both edges at 1x/2x, unwanted supplies releasing gaze,
later need-driven direct consumption, saved absence/local search and consumption
snapshots without ghost targets. The new actual-timer food restore test passed
in 12.4 s and preserves the complete eat clip. A weak-reference test verifies
immediate Tk image-owner shutdown without relying on later garbage collection.

Separate Python processes also exercised one temporary save: known deferred
Onigiri survived a full restart, `--needs hungry` consumed it once, and another
default-launcher Python 3.14 restart retained no portion/target or repeated care
effect. The typed memory codec, active ages, reset IDs, old saves, backups and
interrupted atomic writes have headless regression coverage. These are automated
checks; native visual/input acceptance for this follow-up remains pending.

Windows/Python 3.11, 15 October 2026:

- C1 `f902d20`: 830 tests; reproduce missing investigation and hover truncation.
- C2 `5730516`: 834 tests; curiosity, use decisions and subjective examined memory.
- C3 `ae12dd6`: 837 tests; identified phases/receipts and safe cancellation.
- C4 `1c0e95c`: 845 tests; full visible flow, handover holding and hover protection.
- C5 `bf2f562`: 848 tests; reproducible 22 binary-alpha copies, unchanged source
  hashes/RGB/geometry and shared cursor/ground/hand display paths.
- C6 `9dec641`: 850 tests passed in 157.4 s. Ruff 0.13.2, strict Mypy 1.18.2
  (167 source files) and Pyright 1.1.414 passed. The curious launcher and reopening
  its same temporary save both exited cleanly with `--auto-close-ms 1000`.
- C7 `416607c`: 851 tests passed in 178.0 s; a different first investigation
  bypasses the supply-seeking pause. CI run
  [38770173465](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/38770173465)
  passed all three jobs (Linux Python 3.11/3.13 and Windows).
- C8 `ea4361f`: 855 tests passed in 183.9 s with the same pinned static gates.
  Eating-grip coverage and pickup/hold/put-down top-layer assertions pass at both
  scales; complete asset preparation preserves decoded pixels/metadata, validates
  per-build file hashes and is repeatable with the same encoder. A follow-up
  corrects the cross-platform test's original assumption of identical PNG bytes.
  Deferred drink memory survives gaze release; cursor following and later
  need-driven return are verified.
- The test portability follow-up also passed 855 tests on Windows in 183.2 s
  plus the pinned static checks; the Linux matrix covers the different encoder.
- Current CI results are linked in the implementation ledger and
  [PR checks](https://github.com/Lexoniarus/aiko-desktop-pet/pull/10/checks)
  run Linux/Xvfb Python 3.11/3.13 and Windows, including real Tk flow tests.

16 October edge-grip follow-up: 867 tests passed locally in 205.5 s, with the
same static gates green. The four left/right 1x/2x component cases check actual
driver arrival, frame-4 custody/snap, refusal and placement at the feet, remembered
location and released gaze. Additional cases reject acquisition after Aiko moves
away and verify wanted edge consumption without early nutrition. Pure geometry
tests include an offset track, unchanged ordinary reach and unsupported poses.
Five real-timer tests passed in 100.7 s, including left 1x/right 2x edge flows.

`test_world_runtime_flow.py` runs actual timers and desktop gates: readable,
ordered bubbles, Onigiri at 76%, deferred reuse after hunger, staged drink with
full playback through Enter, interrupted inspection and restart. Component tests
and actual timers also check food consumption followed promptly by drink
investigation/defer at energy 66, preserved recognition and released gaze.
Component tests
separately exercise delayed/stale/duplicate completions and transaction recovery.
These checks do not replace native visual/input acceptance. The user's positive
retest covers the observed basic sequence; keep unreported checklist cases open.
The PR remains draft and unmerged for review; no merge was requested.
