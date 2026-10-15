# First complete World practical test

Status: implementation and automated integration available on
`feature/world-foundation`; native user acceptance pending. Do not merge
[draft PR #10](https://github.com/Lexoniarus/aiko-desktop-pet/pull/10) yet.
See [delivery commits](WORLD_OBJECT_IMPLEMENTATION_PLAN.md) and
[behavior contracts](WORLD_OBJECT_CONTRACTS.md).

## Start with an isolated save

Close any other Aiko instance to avoid confusing overlapping characters.
From the repository, double-click [Aiko_World_Test.bat](../Aiko_World_Test.bat).
It prefers the installed `.venv`, otherwise the Python launcher. Normal runtime
requires only Python with Tk; Pillow is a test/asset-build dependency.

The default hungry profile starts at satiety/energy 55. For the full profile:

```powershell
.\Aiko_World_Test.bat --scenario full
```

Each fresh run creates a separate `aiko-world-smoke-*` folder in the system temp
directory. Its console prints the exact save path and restart command. It does
not load, seed or overwrite the normal user save, including an `AIKO_SAVE_PATH`
override. An explicit path matching the normal save is rejected. Keep the temp
folder until testing and restart are finished; it is not deleted on exit.

Both profiles disable random walks, automatic routine, hardware observation,
rhythm learning and spontaneous dialogue. Object-directed walking stays enabled.
Normal need decay still runs. Existing food fullness/energy-drink acceptance
limits remain unchanged: food refuses at satiety ≥96; drink refuses at energy
100. Even a small energy deficit after time passes permits an offered drink.
Autonomous drink seeking still requires energy ≤60.

Start a fresh hungry profile for each autonomous food/drink scenario. A prior
handover may already raise the relevant need above the seeking threshold; the
30-second pause expiring alone does not make Aiko hungry again. Reuse the same
save path specifically for the restart checks.

## Practical checklist

Record Windows version, primary-monitor/taskbar arrangement, display scaling,
sprite scale and tested commit. Repeat the relevant checks at 1× and 2×.

- [ ] Hover Aiko, open food selection, press and hold Onigiri. Exactly one
  portion follows the cursor; no immediate satiety/care gain occurs.
- [ ] Hold near her body/hand for about one second. She can recognize it but
  does not take it while the button stays down. Release inside the handover
  area while she is awake/free: it is consumed once with normal human care.
- [ ] Start another portion and release away from her above the taskbar. It
  falls without bouncing, rests at ground height and remains visible.
- [ ] In a fresh hungry profile, drop within roughly 1–1.5 character widths. Move
  the pointer away from Aiko and controls. She recognizes it, approaches despite
  random walking being off, picks it up and eats. Wait through the 30-second
  consumption pause before expecting another autonomous meal.
- [ ] Watch pickup: the object changes hands at source pose 4; satiety/energy
  changes only after pickup completes. Foreground fingers appear above the item.
- [ ] In the full profile, offer food: it is refused and falls. A resting food
  stays untouched while she has no appetite. Sleeping/busy Aiko also declines
  offers; releasing does not create a deferred invisible handover.
- [ ] Repeat carrying, offering and ground consumption with Energy Drink in
  the hungry profile. Energy rises by up to ten; satiety/digestion do not gain
  food effects. Ground use grants no human-care/friendship credit.
- [ ] During pickup after grasp but before eating, request sleep, talk or the
  game. She first reaches the safe held pose, plays reverse put-down, releases
  at source 4→3 and then performs the requested action without meal effects.
- [ ] Press Escape during a carry. The portion disappears without consumption
  or a falling duplicate. Verify interruption/loss of input capture also cancels.
- [ ] Release outside the supported primary-monitor surface. The cursor portion
  is discarded with brief feedback; no remote-monitor ghost object remains.
- [ ] Check edges, taskbar alignment, changed sprite scale, hand grips,
  transparency and stacking. Passive object windows must not steal focus or
  interfere with desktop clicks. Existing toolbar pin, settings and game rules
  should remain usable.

## Save and reopen the same session

Leave at least one portion on the ground. Quit normally, then use the **same**
printed path rather than starting another fresh profile:

```powershell
.\Aiko_World_Test.bat --save-path "C:\exact\printed\temp-folder\state.json"
```

- [ ] Nonconsumed ground portions return with the same identities/positions.
- [ ] Exit during carrying/falling/unconsumed pickup, then reopen: the portion
  returns on valid ground, with no resumed cursor ownership or animation.
- [ ] Previously consumed portions do not return and meals are not awarded twice.
- [ ] Needs continue under the existing closed-time rules; no World meal occurs
  while closed. Perception/memory starts afresh and must recognize restored food.

## Recorded automated evidence

Windows, Python 3.11, 15 October 2026:

- Through `bac23e0`: final full suite 828 tests, `OK`, 108.0 s.
- Capture cancellation follow-up `f4f18fd`: six real Tk World tests passed.
- Ruff 0.13.2, strict Mypy 1.18.2 (161 source files), Pyright 1.1.414 passed.
- Asset regeneration `f4ed371`: 120 poses, original runtime PNGs unchanged;
  source hashes, foot anchor and forward/reverse playback tests passed.
- Isolated launcher start and reopening the same temporary path both exited
  cleanly with `--auto-close-ms 1500`; this checks startup/shutdown, not manual
  cursor, visual alignment or native focus behavior.
- PR evidence: [checks for PR #10](https://github.com/Lexoniarus/aiko-desktop-pet/pull/10/checks)
  run Linux/Xvfb Python 3.11/3.13 and Windows, including the new World tests.
  Check the tested head before relying on a result; local green is separate.
- [CI run 38759905855](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/38759905855)
  passed all three jobs at `ffbffc2`: Linux 3.11 and 3.13 each discovered 828
  tests and finished `OK` (seven platform-specific skips); Windows boundary
  checks, including the new World suites, passed. Subsequent documentation-only
  updates do not change the tested runtime; current-head CI is linked above.

Real Tk integration tests cover actual goal-driver arrival, release handover,
refusal, nutrition timing, animated put-down before sleep, lost capture and
restart. Domain tests cover unseen changes, repeated/stale events, origin,
partial-commit recovery, old saves and failed atomic replacement. These tests
do not establish native visual/interaction acceptance; checklist results above
must be recorded after the practical test.
