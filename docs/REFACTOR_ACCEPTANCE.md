# Refactor acceptance — Aiko Desktop Pet

Target branch: refactor/oop-modular-architecture

This refactor is NOT merged into main until automated checks pass and
the desktop runtime has been exercised on Windows after the final commit.

## Automated checks (GitHub Actions)

- Python 3.11 and 3.13: complete unittest suite using Xvfb, including Tk GUI tests
- Ruff: existing project-wide lint rules
- Ruff E501: refactored domain, adaptive, dialogue and focused test modules
- Mypy: strict type checks of headless movement, reaction, click-event
  selection and adaptive-policy modules
- No state JSON schema changes or bundled runtime dependency changes

## Windows 10/11 manual smoke checks — still required

1. Launch with Aiko_starten.bat, then with python main.py in debug mode;
   ensure no startup exception and no unexpected black/opaque sprite box.
2. Hover: show the sci-fi panel, six needs and six care buttons;
   drag, hide, reopen and reset the panel.
3. Walk: confirm left/right movement, taskbar grounding, cursor gaze, and
   stopping while the panel is open. Disable and re-enable auto-walk.
4. Reactions: click slowly and in bursts; confirm deliberate silence is
   respected and old speech follow-ups do not reappear after a new reaction.
   Confirm emote -> speech -> optional follow-up -> emote order.
5. Care: try feeding, playing, petting, talking, energy drink and sleep/wake.
   Verify values, friendship rewards and cooldowns remain sane.
6. Activity: turn observation off/on and check Aiko's workload reaction,
   idle/working animations and overnight sleep behavior.
7. Windows overlays: move another application's foreground window over Aiko;
   check speech, panel and popup layers without unwanted focus stealing.
8. Save/load: record six need values, friendship progress and toolbar position;
   restart and confirm the saved values and preferences return.
9. Quit and restart several times; inspect console for callback exceptions
   or windows left open. A manual failure blocks merge.

Do not move, rewrite or delete the production save at
%LOCALAPPDATA%\AikoDesktopPet\state.json merely to run the smoke checks.

## Gate

Only the user can approve merging the Draft PR into main. A successful
Linux CI does not verify real Windows taskbar APIs, z-order or GPU readings.
