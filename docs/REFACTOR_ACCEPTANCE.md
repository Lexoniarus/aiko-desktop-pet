# Refactor acceptance — Aiko Desktop Pet

Target branch: refactor/oop-modular-architecture

This refactor is NOT merged into main until automated checks pass and
the desktop runtime has been exercised on Windows after the final commit.

## Automated checks (GitHub Actions)

- Python 3.11 and 3.13: complete unittest suite using Xvfb, including Tk GUI tests
- Ruff: existing project-wide lint rules
- Ruff E501: refactored domain, adaptive, dialogue and focused test modules
- Mypy: strict type checks of the full application and headless policies
- Pyright: mandatory checks of all application modules and all Python tests,
  with zero errors and warnings as the target
- Windows-hosted CI: import desktop modules and execute headless tests for
  taskbar placement, z-order, mouse input, gaze and related domain policies
- Headless application integration tests: command routing, notification
  validation, idempotent bounded queue, cross-thread care prohibition and
  non-interrupting Tk presentation. No local HTTP port exists yet.
- Desktop runtime tests cover tick ordering and shutdown timer cancellation,
  persistence and disk-error handling, taskbar/overlay check intervals and
  Tk/global-input dispatch.
- Startup tests verify that restored saves receive exactly one bounded
  catch-up, while fresh or corrupt saves keep their original defaults;
  settings and adaptive memory retain the version-one JSON contract.
- Application import guards prevent a direct dependency on `storage.py`.
- Work-episode regression tests cover confirmed versus missing activity,
  repeated interruption, unexpected work and one-time recovery reflections.
- Lifecycle tests cover the original startup, shutdown and repeated-close
  order without opening a real Windows desktop. Provider tests cover
  CPU deltas, optional NVIDIA measurements, GPU timeout and legacy imports.
- No state JSON schema changes or bundled runtime dependency changes

## Windows 10/11 manual smoke checks — still required

1. Launch with Aiko_starten.bat, then with python main.py in debug mode;
   ensure no startup exception and no unexpected black/opaque sprite box.
2. Hover: show the sci-fi panel, six needs and six care buttons;
   drag, hide, reopen and reset the panel. Check the standalone status
   window and settings popup, including toggles, backdrop clicks and
   the hover bridge beside the animated character.
3. Walk: confirm left/right movement, taskbar grounding, cursor gaze, and
   stopping while the panel is open. Disable and re-enable auto-walk.
4. Reactions: click slowly and in bursts; confirm deliberate silence is
   respected and old speech follow-ups do not reappear after a new reaction.
   Confirm emote -> speech -> optional follow-up -> emote order.
5. Care: try feeding, playing, petting, talking, energy drink and sleep/wake.
   Verify values, friendship rewards and cooldowns remain sane.
6. Activity: turn observation off/on and check Aiko's workload reaction,
   idle/working animations and overnight sleep behavior. Check that GPU
   readings remain optional on machines without NVIDIA tooling.
7. Windows overlays: move another application's foreground window over Aiko;
   check speech, panel and popup layers without unwanted focus stealing.
8. Save/load: record six need values, friendship progress and toolbar position;
   restart and confirm the saved values and preferences return.
9. Quit and restart several times; inspect console for callback exceptions
   or windows left open. A manual failure blocks merge.

Do not move, rewrite or delete the production save at
%LOCALAPPDATA%\AikoDesktopPet\state.json merely to run the smoke checks.

## Gate

Only the user can approve merging the Draft PR into main. Linux/Xvfb and
Windows-hosted headless CI do not replace the user's interactive Windows
check of actual taskbar APIs, focus behavior, window layering or GPU readings.
