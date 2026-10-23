# UI window contract — care controls and passive World items

The main-menu and settings scope of the [approved VN interface](UI_VN_DESIGN.md)
is implemented in stage 5C on `feature/social-optimization`. Its local approved
references are identified in [the handoff](UI_PREVIEW_HANDOFF.md). Validation in
this delivery is headless; native Windows/DPI/input acceptance remains separate.

## Window behavior

Aiko exposes one `ActionToolbar`: white Aiko/settings header, shared emotional
summary and numeric mood, horizontal `MoodletStrip`, dedicated `WishPanel`,
six vertical readouts on the left and a narrower interaction column on the right.
Computer/context lines and one Offen-halten/detail footer complete the menu.
The scrollable expanded `ToolbarDetails` stays inside that window. There is no second
status/actions window. The F2 status action reveals and pins the existing
toolbar. Clicking `Offen halten` keeps it visible when the pointer leaves or
a foreign window receives a click; `Pin lösen` restores automatic hiding.
Position pinning, visibility pinning, and `Immer im Vordergrund` remain
independent concepts.

These seven readouts are presentation values, not seven care needs. The semantic
snapshot exposes five-field `NeedLevels` separately from numeric mood and
friendship. UI projections combine them as `status_values`; the toolbar uses
`READOUTS`/`readouts` and the existing shared status-hint policy. This vocabulary
change preserves bar order, labels, care availability and window behavior.

The pin affects only the current session; it does not add keys to the
version-one JSON save. Existing draggable toolbar position persistence and
reset behavior remain unchanged.

`SettingsWindow` is a persistent, nonmodal, independently movable window
styled with the shared rose/blue VN controls. Its Darstellung, Verhalten,
Lokale Daten and Credits navigation stays available beside a scrolling page.
Scale uses two projected 1×/2× segments. Existing eight native checkboxes show
An/Aus and apply immediately; there is no new preference store or Save action. Outside clicks, changing an option,
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

`Unterhalten` replaces the right interaction column with an embedded selector
for Plaudern, API Single, API Two Parts and facts. `HoverUi` still owns its
lifetime and admission. Loading/error/opt-out text uses the existing social
snapshot, without another request queue. Zurück/Escape/outside dismissal cancels
pending content, not an already accepted story. Provider, source and API-entry
links now live in the independently movable settings window's Credits page.
`project_credits()` detaches only the latest accepted metadata; there is no
second source history or content request.

An empty API buffer uses the existing speech/player surface for one holding
line. The application exposes this holding state through a narrow contact port:
deliberate care may replace it, while incidental hover/click replies do not.
Actual conversation playback retains the normal care lock and reading-click
behavior. Deferred start rechecks permission after World releases its own
pending-action marker. See [social content](SOCIAL_CONTENT.md).

### Games

`Spielen` opens an embedded right-column selector for RPS, Blackjack and Tic-Tac-Toe.
Escape/outside dismissal closes the selector without starting play. Selection
uses the existing contact admission and World interruption; one pending token
prevents duplicate starts. The resumed callback rechecks sleep readiness without
rejecting World's own pending-action reservation. Settings remain independent.
The toolbar belongs to the selector's interaction area: delayed focus checks
and global polling of the opening click must leave the selector open while
the pointer is still on the toolbar. A click outside both dismisses it.

`HoverUi` owns the one active game through `GameWindow`. Embedded selectors
are frames in the toolbar, not extra control windows. Their geometry leaves
the summary, Moodlets, wishes and left readouts in place. Game
sequences cancel timers before closing; one summary is credited before final
save. Scores, boards and decks never enter the save.
The three player windows retain their `WM_DELETE_WINDOW` handlers. Embedded
selectors use their existing close callbacks through Zurück/Escape instead. Failed
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


## Passive emotional presentation and shared assets

`MoodletStrip` shows every active impression (horizontal overflow), its own icon
and wrapped tag. Hover/focus/tap reads cause, intensity, individual contribution,
known attribution, remaining stage/total decay work, paused decay and recovery
wait. The existing episode retains the latest real causes up to its current
intensity: one at level one, two at level two, three at level three. Renewing level
three drops the oldest cause; decay trims the list to the latest causes fitting
the lower level. Hover rows number these reasons, without claiming each event
belongs to a historical stage. A stronger initial event or incomplete old save
does not fabricate missing events. Old receipts retain all available real causes
up to the current limit; obsolete per-cause stage metadata is ignored. No widget runs creation, aging, relief
or emotional selection.
`WishPanel` shows the concrete food/game/social/care target, objective scope and
bounded progress, remaining original deadline, inner/spoken marker and temporary
unavailability. Left-click anywhere on a wish card pins the wish; repeating
left-click keeps it pinned. Right-click unpins a pinned wish; a further
right-click dismisses the now unpinned wish. Current domain unpinning after the
original deadline can retire it immediately; supplied food/affection can also
retire once unprotected. Reconciling that automatic retirement with the two-click
expectation is an [open decision](CARE_TIME_IMPLEMENTATION_PLAN.md#documentation-audit-and-open-work-2026-10-23), not a newly approved UI rule.
There is no pin button: a passive pin symbol is visible only while pinned.
Hover/focus and Enter/Space retain description access; card clicks take precedence
over description tapping. Both panels retain widget identity and scroll position
while read-side time changes.
Descriptions use an in-window, clamped passive overlay, not another Toplevel.
Its width is bounded by 420 pixels and its parent's available width. Hover ownership
includes the current icon/card and description so overlapping content does not
hide and reopen itself. Leaving both regions or dismissing by keyboard closes it.

Readouts layer the prepared track, dynamic rounded/clipped fill and transparent
rim. All of the filled portion changes green/yellow/orange/red with the value;
friendship remains blue. Numbers remain visible. Focus outlines are independent
of button selection. The one pin is rendered from HoverUi's existing state.
The shared root-local `IconImages` owns packaged art and composed icon/buttons;
widget destruction drops button references and root destruction releases the
cache on the owner thread. No Pillow dependency was added to runtime.

Scroll regions use local bind tags, wheel/keyboard access and automatic reveal
of focused overflow; they do not install a global input hook. Content and details
scroll without extra windows. UI feedback is immediate, with no added animation
timers or continuous effects.

### Remaining native acceptance (not executed during 5C)

Stage 6 subsequently runs the complete automated native-widget suite on an
isolated Linux/Xvfb display for candidate `b72ed21`, including game placement,
selector ownership, completion and cleanup. It does not establish the physical
Windows/DPI/input checks below or validate subsequent parallel UI refinements.

- Compare the live menu to the approved main/settings references at 100/125/150%
  Windows DPI, including German wrapping and actual icon/tag sizes.
- Check clamping, pin/drag/topmost, details scrolling and all three embedded
  selectors on the user's screen; inspect empty and all-family overflow states.
- Check Tab/arrows/wheel/Space/Enter/Escape, focused overflow reveal and tooltip
  placement without obscuring its entry or care controls.
- Check placement while sleeping/acting/in a game, and ordinary game-close flow
  using an isolated save. Verify settings remain independently movable.
- Check image cleanup on shutdown and multiple reopenings. These native tests
  remain distinct from the green headless owner/command and pixel-export checks.
