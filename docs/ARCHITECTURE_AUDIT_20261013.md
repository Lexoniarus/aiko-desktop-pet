# Aiko architecture audit — 2026-10-13

**Status:** Incremental refactor, not final Windows acceptance. Work is
isolated to `refactor/oop-modular-architecture`.

## Ownership and module boundaries

| Responsibility | Implemented owner |
| --- | --- |
| Domain care and friendship | `application/controller.py` + domain rules |
| Incoming app/browser notifications | `application/router.py` and `inbox.py` |
| Comment timing, cursor/walk decisions and presentation interruption | `application/attention.py` |
| Workload, adaptive routine and pet time advancement | `application/activity.py` |
| Verified work episode/recovery memory for dialogue | `work_episode.py` |
| Immutable view data | `application/view_models.py` and `read_models.py` |
| Animated character and walking | `ui/animated_pet.py` |
| Taskbar geometry and transparent root | `ui/desktop_window.py` |
| Hover, status and settings lifecycle | `ui/hover_ui.py` and UI views |
| Speech and ordered emotes | `ui/speech_presenter.py`, `reaction_playback.py` |
| Hover layout and drag rules | `ui/hover_geometry.py` |
| Legacy GUI method compatibility | `desktop/compatibility.py` |
| Tick timers and update phases | `desktop/runtime.py` |
| State serialization and autosave cadence | `desktop/persistence.py` |
| Taskbar/window stack checks | `desktop/maintenance.py` |
| Tk/global mouse and focus input | `desktop/input.py` |
| Desktop startup/shutdown resource sequence | `desktop/lifecycle.py` |
| Hardware readings and effort | `infrastructure/hardware/metrics.py` |
| Windows/Linux OS sensors | `infrastructure/hardware/os_sensors.py` |
| NVIDIA discovery and CSV parsing | `infrastructure/hardware/nvidia.py` |
| CPU/GPU smoothing and bounded GPU call | `infrastructure/hardware/sampler.py` |
| Background worker and cached readings | `infrastructure/hardware/monitor.py` |
| Legacy sensor import compatibility | `system_activity.py` |
| Component composition and remaining GUI adapters | `gui.py` |

The original `gui.py` mixed all those responsibilities and measured 875
lines. The composition shell is now about 576 lines. The legacy
compatibility adapter remains separate; these forwards are not removed
complexity. Timers, serialization, taskbar/stack polling, and input binding
now belong to testable, cohesive desktop services. Domain time advancement
is owned by `ActivityCoordinator`, including the pre-save catch-up.
Startup and shutdown
are now ordered by `DesktopLifecycle` rather than duplicated in the
composition root.

## Dependency rule

    future authenticated integration adapter
                   |
                   v
       application commands / events
              |              |
           domain          immutable read contracts
              ^              |
              |              v
       local providers     UI presenters
                               |
                           Tk desktop

Application code must not import Tk or UI implementations. UI widgets
must not access `DesktopPet` or mutable game/persistence classes. The
animated character and native window now use structural typing protocols
instead of importing specific domain models. Old UI snapshot imports
re-export the exact application view-model classes.

Only the `gui.py` bootstrap connects these components. The typed legacy
adapter is **not** a destination for new features.

## Remaining work, by priority (not yet implemented)

1. **Implemented:** timer scheduling, autosave, taskbar/stack inspection,
   mouse/focus binding and ordered desktop startup/shutdown. The lifecycle
   owns existing resources but contains no care/dialogue policy.
2. **Implemented:** the former 337-line `system_activity.py` is now
   only the compatibility façade. The implementation lives in
   `infrastructure/hardware/`, separated into immutable readings,
   Windows/Linux OS sensors, NVIDIA discovery/parsing, CPU/GPU sampling
   and the independent background monitor. Public imports are preserved.
3. **Implemented:** `dialogue.py` now delegates observed work episode
   transitions, counted interruptions, unusual workload classification and
   one-time recovery commentary to `work_episode.py`. `AikoMind` retains
   dialogue coordination, mood priorities, click/care selections and the
   separately testable spontaneous topic policy. No dialogue text was edited.
4. Gradually package flat domain files. Because the import path
   `aiko_pet.domain` is in use, migrate only with an explicit compatibility
   cutover and regression tests; do not create decorative empty folders.
5. Review remaining widget construction in the 320-line `action_toolbar.py`.
   Pure geometry was extracted; further splits require cohesive widgets.

Do not introduce a new HTTP server, AI backend or speculative event bus
as a prerequisite for the code-structure refactor.

## Regression barriers

- Ruff and E501 source checks, strict Mypy, project-wide Pyright.
- GUI tests on Python 3.11 and 3.13 under Linux/Xvfb.
- Windows-hosted headless tests and desktop module imports.
- AST architecture checks prevent application-to-UI and UI-to-domain
  reverse imports. `gui.py` now has an explicit 600-line limit.
- Manual real Windows tests remain a merge prerequisite.

**No merge, schema change, asset change or local save rewrite.**
