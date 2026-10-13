# UI window contract — single care toolbar and persistent settings

## Window behavior

Aiko exposes one `ActionToolbar` with six care indicators, care buttons,
local computer status, and expandable `ToolbarDetails`. There is no second
status/actions window. The F2 status action reveals and pins the existing
toolbar. Clicking `Offen halten` keeps it visible when the pointer leaves or
a foreign window receives a click; `Pin lösen` restores automatic hiding.
Position pinning, visibility pinning, and `Immer im Vordergrund` remain
independent concepts.

The pin affects only the current session; it does not add keys to the
version-one JSON save. Existing draggable toolbar position persistence and
reset behavior remain unchanged.

`SettingsWindow` is a persistent, nonmodal, independently movable window
styled with the same Kenney Sci-Fi visual controls as the care toolbar and
the existing Rock-Paper-Scissors game. Outside clicks, changing an option,
moving Aiko, hiding the hover toolbar, and resizing Aiko do not close or move
settings. Explicitly invoking settings again focuses its one existing instance.
Close or Escape only closes settings. Reopening it in the same running session
uses its last position and clamps it to the available screen; no save-file
migration is needed.

## OOP responsibilities

| Component | Responsibility |
| --- | --- |
| `ui/hover_ui.py` | One owner of the toolbar pin, automatic visibility, settings/game instances and live interaction detection |
| `ui/action_toolbar.py` | One cohesive toolbar view and pin-button rendering, including expandable local details |
| `ui/toolbar_details.py` | Detached status display inside the toolbar; no duplicate care actions |
| `ui/settings_window.py` | Window geometry and controls, reading snapshots and invoking callbacks |
| `ui/skin.py` | Shared colors, Kenney image ownership, font selection, common control factories |
| `ui/window_drag.py` | Reusable title-only drag behavior and screen bounds without pet state |
| `desktop/preferences.py` | Effects of preference actions; no new settings owner |
| `presentation/read_models.py` | Detached snapshots for hover, settings and status details |
| `desktop/lifecycle.py` | Ordered cleanup of the existing window owners |

No new general event bus, global window manager, inference backend or
additional domain aggregate is introduced.

## Presence versus interaction

A pinned toolbar standing idle on screen, or an open settings window without
pointer/keyboard interaction, must not permanently suppress spontaneous
dialogue, emotes or noninterrupting notifications. The host supplies actual
UI engagement to the attention coordinator. Game activity maintains its
existing independent suppression rules. Settings refresh never calls a
preference setter or takes focus.

## Tests and Windows acceptance

Unit tests cover shared drag geometry, window isolation, idempotent cleanup,
option callbacks, six progress bars, pin and timeout behavior, focus/reopen
semantics, notification delivery and preservation of saved toolbar location.
CI must pass the Linux/Xvfb Tk suite, Windows headless checks, Ruff, strict
Mypy and Pyright. Real Windows smoke testing is still required for DPI,
transparent windows, focus and z-order, multiple displays and taskbar behavior.
No approved character images, dialogue or save data are modified.

Existing gallery screenshots of settings and status must be refreshed to show
the new behavior; previously captured screenshots are historical until then.
