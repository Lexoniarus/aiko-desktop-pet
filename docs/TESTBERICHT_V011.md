# Test report — Aiko Desktop Pet v0.11

## Baseline

The unmodified `Aiko_Desktop_Pet_Dialoge_und_Verhalten_v0_10.zip` was extracted with all 73 sprites and the previous **167 tests**. Earlier releases were not modified.

## Automated test command

```bash
xvfb-run -a python -m unittest discover -s tests -q
```

The v0.11 suite passed **195 tests** before final packaging, including the previous suite and new cases for:

- Migrating saves containing only the first three needs, validating new fields, friendship levels, malformed JSON, and atomic saves.
- Social need as a separate axis, talking, playing, petting, and feeding.
- Energy drinks restoring +10 per use, repeated use to the maximum, use at full energy, and manual wake-up at night without immediate automatic return to sleep.
- Gradual friendship with anti-spam cooldowns and daily award limits.
- High versus low measured live utilization; no phantom hours from missing telemetry.
- Disabling utilization monitoring and handling stale samples.
- Social deprivation, growing friendship, care-triggered dialogue, and sprite availability.
- Tkinter's five historical gauges, accurate 100% fill, care actions, movable panel, details, settings, and auto-hide.

## Visual inspection

The historical [v0.11 Tamagotchi screenshot](https://github.com/Lexoniarus/aiko-desktop-pet/blob/f41e8aab58e6a93bd2675d0fd1f1adc3bed9b345/vorschau/Aiko_v0_11_Tamagotchi.png) in Git history shows the actual Tkinter UI with its original sprites under a simulated 1366×768 Linux desktop. Illustrative status values were injected; it was **not** a capture of real Windows hardware metrics. The current screenshot gallery uses the new Aiko artwork and UI instead.

All five gauges used the same grid and filled the available width when at 100%.

## Not verified

Windows taskbar geometry at different DPI scales, browser/microphone Z-order, actual NVIDIA measurements, and subjective care balance over multiple days still required hands-on testing. The existing 167 regression tests were not claimed as evidence of these platform-specific effects.
