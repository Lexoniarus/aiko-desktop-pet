# Test report and acceptance notes — Aiko Desktop Pet v0.12

## Baseline and test execution

The unmodified v0.11 archive was extracted before changes. Baseline command:

```bash
xvfb-run -a python -m unittest discover -s tests -q
```

- **v0.11 baseline: 195 tests passed.**
- **v0.12: 220 tests passed**, including 25 additional affection, friendship, migration, dialogue, and GUI tests.

Existing GUI/window, dialogue, sprite, routine, and system-load coverage was retained. Separate checks confirmed the **73 unchanged PNG sprites**, a valid catalog of **404 dialogue entries**, and an actual Tkinter rendering under virtual Linux/X11 with six gauges.

## Covered cases

- Petting has a distinct function: **+25 affection, +6 mood, +2 social, no energy bonus**.
- Playing, talking, feeding, and energy drinks maintain separate primary needs.
- Verified CPU/GPU work affects ordinary consumption but **not** the direct affection or friendship rate.
- Affection decreases gradually while awake and at a smaller rate during sleep; low affection can influence Aiko's tone.
- Friendship rewards meaningful care and different helpful care types, not already-full stats or click spam.
- Cooldowns, local calendar-day reward caps, energy-drink repetition, and a new day.
- Migration from v0.11 saves without affection: preserve old stats/settings and initialize affection to 75.
- Malformed stored values are clamped or ignored safely.
- Two rows of six hover values and accurate 100%-width bars; detail UI and menus remain usable.
- New speech events use only available animation assets.

## Limits of verification

The tests ran under Linux/Xvfb. Real Win32 topmost behavior, microphone overlays, and NVIDIA telemetry could not be reproduced on actual Windows hardware in that environment. Those integrations remained unchanged and still need practical Windows verification.
