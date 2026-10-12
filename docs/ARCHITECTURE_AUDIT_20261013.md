# Aiko architecture audit — 2026-10-13

**Status:** Incremental refactor, not final Windows acceptance. Work is
isolated to `refactor/oop-modular-architecture`.

## Ownership and module boundaries

| Responsibility | Implemented owner |
| --- | --- |
| Domain care and friendship | `application/controller.py` + domain rules |
| Incoming app/browser notifications | `application/router.py` and `inbox.py` |
| Comment timing and interruption | `application/attention.py` |
| Workload and adaptive routine | `application/activity.py` |
| Immutable view data | `application/view_models.py` and `read_models.py` |
| Animated character and walking | `ui/animated_pet.py` |
| Taskbar geometry and transparent root | `ui/desktop_window.py` |
| Hover, status and settings lifecycle | `ui/hover_ui.py` and UI views |
| Speech and ordered emotes | `ui/speech_presenter.py`, `reaction_playback.py` |
| Hover layout and drag rules | `ui/hover_geometry.py` |
| Legacy GUI method compatibility | `desktop/compatibility.py` |
| Component assembly and remaining tick | `gui.py` |

The original `gui.py` mixed all those responsibilities and measured 875
lines. It now has approximately 608 lines. The 278-line compatibility
adapter contains *only typed forwarding*, not another implementation of
care, dialogue, movement or presentation rules.

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

1. Move scheduled ticks, startup/shutdown and autosave cadence from the
   desktop composition root to cohesive desktop runtime services.
2. Split the 337-line `system_activity.py` along hardware-provider and
   sampler responsibilities. Keep Windows/Linux implementations testable
   without rewriting their published API.
3. Review the 322-line `dialogue.py` for behaviorally meaningful division.
   Preserve German authored phrases, event priority and quiet behavior.
4. Gradually package flat domain files. Because the import path
   `aiko_pet.domain` is in use, migrate only with an explicit compatibility
   cutover and regression tests; do not create decorative empty folders.
5. Review remaining widget construction in the 316-line `action_toolbar.py`.
   Pure geometry was extracted; further splits require cohesive widgets.

Do not introduce a new HTTP server, AI backend or speculative event bus
as a prerequisite for the code-structure refactor.

## Regression barriers

- Ruff and E501 source checks, strict Mypy, project-wide Pyright.
- GUI tests on Python 3.11 and 3.13 under Linux/Xvfb.
- Windows-hosted headless tests and desktop module imports.
- AST architecture checks prevent application-to-UI and UI-to-domain
  reverse imports. `gui.py` currently has an explicit 650-line limit.
- Manual real Windows tests remain a merge prerequisite.

**No merge, schema change, asset change or local save rewrite.**
