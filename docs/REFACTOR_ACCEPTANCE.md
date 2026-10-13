# Historical OOP refactor acceptance — October 2026

> **Archived acceptance record.** The architecture refactor was merged into
> `main` via [PR #2](https://github.com/Lexoniarus/aiko-desktop-pet/pull/2)
> on 2026-10-13 at commit
> [073e7a4](https://github.com/Lexoniarus/aiko-desktop-pet/commit/073e7a43551f0b29abe5d04b760c6324230e4be8).
> See [the current architecture](ARCHITECTURE.md) and the
> [latest CI](https://github.com/Lexoniarus/aiko-desktop-pet/actions/workflows/tests.yml)
> for living documentation.

The following checks describe the completed refactor validation.
The project maintainer reported successful native Windows operation
on 2026-10-13. Detailed item-by-item manual test logs were not collected.

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
- Desktop runtime tests cover typed phase ordering, exact timer cancellation,
  persistence and disk-error handling, taskbar/overlay check intervals and
  Tk/global-input dispatch.
- Desktop preference tests validate original window z-order, centering, scale,
  toolbar position and feature toggles against the existing owners.
- FocusOut regression tests verify all deferred input callbacks are cancelled
  before Tk teardown, including simulated callbacks that fire too late.
- Startup tests verify that restored saves receive exactly one bounded
  catch-up, while fresh or corrupt saves keep their original defaults;
  settings and adaptive memory retain the version-one JSON contract.
- Application import guards prevent a direct dependency on `storage.py`.
- Desktop module ownership tests verify exact legacy class identity, pure
  taskbar geometry, and native-provider isolation from sprite policies.
- Canonical personality package tests protect authored catalogue discovery,
  workload detector naming and legacy class identity, along with separation
  of dialogue policy from concrete desktop/UI/storage dependencies.
- Infrastructure persistence tests verify original StateStore class
  identity, JSON schema version one and unchanged absolute/relative
  save-directory resolution.
- Canonical pet package tests check exact identity of old imports and
  verify no outer-layer dependencies or duplicate PetState implementations.
- Domain-transition tests check immutable policies, pet-owned mutations,
  backwards-compatible care and timeline APIs, old friendship rewards,
  sleep behavior, rejected actions and bounded work telemetry.
- Presentation parity tests compare the new German hover/status formatting
  against legacy projections across needs, moods, times and optional hardware.
  Immutable pet/telemetry contracts and SettingsKey routing stay compatible.
- New architecture guards check live presentation ownership, absence of
  concrete infrastructure imports from application coordinators and
  separation of localized text from the production pet read path.
- Work-episode regression tests cover confirmed versus missing activity,
  repeated interruption, unexpected work and one-time recovery reflections.
- Lifecycle tests cover the original startup, shutdown and repeated-close
  order without opening a real Windows desktop. Provider tests cover
  CPU deltas, optional NVIDIA measurements, GPU timeout and legacy imports.
- Import-cycle, package-layer and legacy presentation compatibility checks
- No state JSON schema changes or bundled runtime dependency changes

## Windows 10/11 manual smoke checks — user-reported acceptance

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
   or windows left open.

These items remain the regression reference checklist. The user confirmed
that Aiko operates normally under Windows on 2026-10-13. This is not a
claim that each item was individually witnessed or logged by the assistant.

Do not move, rewrite or delete the production save at
%LOCALAPPDATA%\AikoDesktopPet\state.json merely to run the smoke checks.

## Completed merge gate

The maintainer gave explicit approval, and PR #2 was merged on
2026-10-13. The post-merge `main` CI run
[38382796398](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/38382796398)
completed successfully: 486 Linux/Xvfb tests on each of Python 3.11 and 3.13,
plus 257 Windows-headless tests.

This historical record is not an instruction to reopen or merge PR #2 again.
Future changes need their own review and, where relevant, Windows testing.
