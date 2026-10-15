# World investigation and consumption — practical retest

The first practical test found missing investigation/feedback, truncated drink
playback and Magenta item fringes. Corrections are implemented on
`feature/world-foundation`; native acceptance of this revised build is pending.
[Draft PR #10](https://github.com/Lexoniarus/aiko-desktop-pet/pull/10) remains
unmerged. See [delivery/evidence](WORLD_OBJECT_IMPLEMENTATION_PLAN.md) and
[behavior contracts](WORLD_OBJECT_CONTRACTS.md).

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
- [ ] Check taskbar/screen edges, scale changes, hand foregrounds, focus,
  click-through and stacking. Existing toolbar pin, settings and game controls
  stay usable. Ambient speech/notifications do not overwrite object-phase bubbles.

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
- [ ] Memory/inspection history starts fresh after reopening, as before. Restored
  objects can be investigated again. No World item is eaten while the app is closed.

## Automated evidence

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
- Current CI results are linked in the implementation ledger and
  [PR checks](https://github.com/Lexoniarus/aiko-desktop-pet/pull/10/checks)
  run Linux/Xvfb Python 3.11/3.13 and Windows, including real Tk flow tests.

`test_world_runtime_flow.py` runs actual timers and desktop gates: readable,
ordered bubbles, Onigiri at 76%, deferred reuse after hunger, staged drink with
full playback through Enter, interrupted inspection and restart. Component tests
separately exercise delayed/stale/duplicate completions and transaction recovery.
These checks do not replace native visual/input acceptance. Keep the checklist
open until the revised practical test is recorded; do not merge before then.
