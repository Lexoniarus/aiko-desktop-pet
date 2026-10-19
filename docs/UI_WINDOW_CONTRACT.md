# UI window contract — care controls and passive World items

## Window behavior

Aiko exposes one `ActionToolbar` with a wide overall mood bar above six individual
indicators (satiety, fun, energy, social, affection, friendship), care buttons,
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
| `ui/windows/hover_ui.py` | One owner of the toolbar pin, automatic visibility, settings/game instances and live interaction detection |
| `ui/windows/action_toolbar.py` | One cohesive toolbar view and pin-button rendering, including expandable local details |
| `ui/windows/toolbar_details.py` | Detached status display inside the toolbar; no duplicate care actions |
| `ui/windows/settings_window.py` | Window geometry and controls, reading snapshots and invoking callbacks |
| `ui/common/skin.py` | Shared colors, Kenney image ownership, font selection, common control factories |
| `ui/common/window_drag.py` | Reusable title-only drag behavior and screen bounds without pet state |
| `desktop/preferences.py` | Effects of preference actions; no new settings owner |
| `ui/view_models/read_models.py` | Detached snapshots for hover, settings and status details |
| `desktop/lifecycle.py` | Ordered cleanup of the existing window owners |
| `application/contact.py` | Preserve intentional hover and click priority without owning widgets |
| `ui/pet_view/care_presenter.py` | Present care results without owning nutrition or friendship |
| `ui/pet_view/attention_presenter.py` | Render approved spontaneous speech and notification cues |

No new general event bus, global window manager, inference backend or
additional domain aggregate is introduced.

## Presence versus interaction

### Conversations

`Unterhalten` opens one transient selector for Plaudern, API Single, API Two Parts
and facts. `HoverUi` includes it in control stacking, topmost propagation,
hover detection and outside/Escape dismissal. Closing cancels pending content,
not an already accepted story. Source controls reserve their layout space so
revealing attribution does not move the menu outside the screen.

An empty API buffer uses the existing speech/player surface for one holding
line. The application exposes this holding state through a narrow contact port:
deliberate care may replace it, while incidental hover/click replies do not.
Actual conversation playback retains the normal care lock and reading-click
behavior. Deferred start rechecks permission after World releases its own
pending-action marker. See [social content](SOCIAL_CONTENT.md).

### Games

`Spielen` opens one transient submenu for RPS, Blackjack and Tic-Tac-Toe.
Escape/outside dismissal closes the selector without starting play. Selection
uses the existing contact admission and World interruption; one pending token
prevents duplicate starts. The resumed callback rechecks sleep readiness without
rejecting World's own pending-action reservation. Settings remain independent.
The toolbar belongs to the selector's interaction area: delayed focus checks
and global polling of the opening click must leave the selector open while
the pointer is still on the toolbar. A click outside both dismisses it.

`HoverUi` owns the one active game through `GameWindow` and includes the selector
in interaction detection, topmost propagation, stacking and cleanup. Game
sequences cancel timers before closing; one summary is credited before final
save. Scores, boards and decks never enter the save.
The selector and all three player windows route `WM_DELETE_WINDOW` through
their existing close handlers, just like explicit Close/Escape. Failed
Tic-Tac-Toe construction destroys its partial panel without reporting a
completed session; `HoverUi` still owns releasing the pending/mode state.

In Blackjack the player panel contains only player cards/total and controls.
Player cards use 2x integer scaling, with bounded overlap in a 480-pixel hand
area. The native draw button displays a cached pile composed from the existing
back and supports ordinary button focus/activation. It owns no deck state.
Aiko's masked/revealed hand is a separate anchored desktop overlay, lower in
front of her so her face and speech remain readable. Hover raises a visible
card; clicks do not reveal, feed, pick up or count as pet teasing. The hand
persists across speech changes and disappears on close/failure/shutdown.
It is not a World item. Tic-Tac-Toe has one shared board and desktop reactions.
Blackjack keeps each result visible for 2.8 seconds, then automatically starts
the next hand with a freshly masked dealer and the same session score. Its
sequence owns this delay through its existing cancellable timer; close cancels
the restart and preserves only completed units. `GamePanel` offers an optional
next-round button, used by Tic-Tac-Toe. RPS keeps its existing flow.

### Contact and ordinary controls

Direct sprite clicks may interrupt an earlier **click reply**, allowing repeated
left/right clicks to reach the existing teasing/irritation policy. This does
not unlock toolbar actions during playback. Care, games, sleep and committed
World interactions retain their admission rules. Left clicks that advance a
story are reading, not teasing; right clicks do not interrupt that story.

`ReactionPlayer.event` exposes only the current sequence's semantic event and
clears on completion/cancellation. `ContactCoordinator` reads it through the
typed `ContactPorts.reaction_event` callback to distinguish click replies from
other playback. World still admits object contact upstream; `PetMind.clicks`
and the existing click policy remain the only click-history/escalation owners.

Expanded details show a detached `ObjectStatusSnapshot`: **Auf dem Desktop**
counts resting World portions; **Bekannt** counts identified memory portions,
excluding superseded history; **Zugeordnet** counts those remembered at a place
or in custody without open association ambiguity; **Vermisst** counts identified
memories with confirmed missing-place status. Same-type portions count separately.
The application projection reads World and memory snapshots; rendering these
numbers never identifies a sighting, checks a hidden place or changes memory.
An unseen relocation therefore changes objective location before subjective
assignment, exactly as it does without the diagnostics. These totals are current
owner-thread reads, including while the toolbar is pinned and details are open.

A pinned toolbar standing idle on screen, or an open settings window without
pointer/keyboard interaction, must not permanently suppress spontaneous
dialogue, emotes or noninterrupting notifications. The host supplies actual
UI engagement to the attention coordinator. Game activity maintains its
existing independent suppression rules. Settings refresh never calls a
preference setter or takes focus.

## Passive World presentation

World item windows are read-only projections owned by `ui/world_view.py`, with
Windows no-activate/click-through styling in `desktop/object_windows.py`. They
add no care toolbar, status panel or independent domain state. Item stacking
follows the existing always-on-top preference; showing/moving items must not
steal focus. Pet-held items and foreground hands render on the character canvas.

The food picker starts one cursor portion on press. The application root owns
a temporary local Tk input grab during that gesture and releases it on drop,
handover, Escape, capture loss or shutdown. This deliberate gesture capture is
separate from passive item windows. Native behavior, DPI and grip alignment
are covered by [the World practical checklist](WORLD_SMOKE_TEST.md).

## Tests and Windows acceptance

Unit tests cover shared drag geometry, window isolation, idempotent cleanup,
option callbacks, seven progress bars, pin and timeout behavior, focus/reopen
semantics, notification delivery and preservation of saved toolbar location.
CI must pass the Linux/Xvfb Tk suite, Windows headless checks, Ruff, strict
Mypy and Pyright. Maintainer-reported desktop acceptance is recorded as passed
in the [current smoke guide](WORLD_SMOKE_TEST.md#acceptance-status). Repeat
relevant native checks after changes affecting DPI,
transparent windows, focus and z-order, multiple displays and taskbar behavior.
The World feature adds approved pickup resources and an optional save section;
earlier window consolidation preserved the existing character and save values.

Gallery screenshots may show earlier settings/status layouts. Their historical
illustration scope is stated in the [media gallery](MEDIA_GALLERY.md); the
maintained behavior contract is this document.
