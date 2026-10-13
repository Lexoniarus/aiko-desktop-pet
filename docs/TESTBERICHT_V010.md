# Test report — Aiko Desktop Pet v0.10

## Starting point

The archived `Aiko_Desktop_Pet_Adaptiver_Rhythmus_v0_9.zip` release was extracted in isolation and retained its files and save structure. Other project repositories were not changed.

## Automated tests

```text
xvfb-run -a python -m unittest discover -s tests -q
----------------------------------------------------------------------
Ran 167 tests in 10.281s

OK
```

Pure domain tests can run without a display. Tk GUI tests need a graphical display server.

The suite covered:

- Regression of v0.9 behavior and old-save compatibility.
- 72-hour and multi-week usage simulations, local clock, and nighttime computation.
- Progressive click reactions in neutral, high, and low moods.
- Repeated interruption during observed high workload and contextual callbacks afterward.
- No invented history after a brief workload spike.
- A one-time delayed reflection after confirmed extended work, followed by ordinary rest.
- Unexpected activity only when a sufficiently trained rhythm baseline exists.
- Two-part speech bubbles, cancellation on interruption, and intentional silence.
- Existing animation assets, window management, and status panel interaction.

The **73 PNG sprites remained SHA-256-identical** to v0.9.

The edited dialogue catalog contained **339 primary entries across 67 event categories**, of which 109 supported an optional second line. Forty less-specific earlier entries were removed and core lines revised; new contextual reactions were handwritten, not generated at runtime.

## Visual verification

The real Tk application was launched under a virtual Linux display. The original [v0.10 click reaction](https://github.com/Lexoniarus/aiko-desktop-pet/blob/f41e8aab58e6a93bd2675d0fd1f1adc3bed9b345/vorschau/Aiko_v0_10_Klickreaktion.png) and [follow-up](https://github.com/Lexoniarus/aiko-desktop-pet/blob/f41e8aab58e6a93bd2675d0fd1f1adc3bed9b345/vorschau/Aiko_v0_10_Nachsatz.png) remain available in Git history. They show the authentic historical sprite and were not mockups. The active preview directory now shows the current character; these old captures are not presented as modern UI. A native Windows taskbar was not part of the original test display.

## Not verified on Windows

- Win32 stacking during browser microphone input.
- Real NVIDIA telemetry or sustained GPU-intensive computation.
- Subjective dialogue quality after days of ordinary use.
- Timing and readability at different Windows DPI scale factors.

Automated Linux tests do not establish that these Windows-specific cases have passed.
