# Aiko VN interface direction — 2026-10-20

**Main-menu refinement (2026-10-20):** the owner authorized bringing the native
main menu closer to the approved reference. The menu now fits its content up to
the available-height cap, keeps the footer accessible, hides scrollbars when
content fits, and releases empty context/row space. The six care rows retain a
354 px interaction column; selector changes keep the same outer geometry.
Moodlets use individual illustrated halos and wrapped tags. Wishes show three
separate target/objective/time cards with the prepared panel artwork. That same
panel source frames embedded selectors, in-window descriptions and the shared
expanded-details region; details use separators rather than separate blue boxes.
Main-menu buttons align their icons and text together, with navigation marks on
the right. Separate derived button sizes serve food, game, social and back choices.
The original source PNGs and approved external previews are unchanged.

The actual Tk widgets were inspected in a disposable native review window with
illustrative read snapshots and an additional system title bar for capture.
Native regression checks cover fit/overflow/removal, three-wish layout, selector
geometry, details with limited height, panel resizing and enabled/disabled input.
This is not acceptance of every Windows DPI/monitor configuration or of the
production borderless window stack. Game windows and their movement are explicitly
outside this refinement; they remain a separate owner-requested next step.
Validation passed: 1,616 tests in the complete Windows suite, 66 additional
menu/UI regression checks on the final refinement, Ruff, strict Mypy and Pyright.

**Implementation update (5C, 2026-10-20):** main status/menu, embedded selectors,
shared VN assets and settings/Credits are implemented on `feature/social-optimization`.
The preparation-only authorization statements below describe the historical
approval pass. The external reference bundle and original masters are unchanged.
The three gameplay layouts/artwork remain with their existing owners; native
Windows/DPI/input acceptance has not been executed in this headless delivery.

Status: full interactive main-menu design approved by the owner on 2026-10-20,
including the wish area, filled embedded selectors and expanded details.
The matching settings and separate Credits design was also visually approved by
the owner on 2026-10-20; see the [accepted settings reference](UI_PREVIEW_HANDOFF.md#reference-entry-points).
The three game surfaces were subsequently approved on the same date, completing
design/asset preparation for the agreed scope. No additional preview is required.
Documentation and asset preparation are authorized; application/UI implementation
is not. The [approved interactive reference](UI_PREVIEW_HANDOFF.md#reference-entry-points)
is the main-menu visual authority; earlier boards remain supporting history.
The current runtime remains described by [UI window contract](UI_WINDOW_CONTRACT.md).

## Scope and preserved assets

Start with the main hover/status menu, its embedded Snack/Spielen/Unterhalten
selectors, expandable details, and space for forthcoming Moodlets. Adapt the
other utility/game screens to this visual language later, respecting each
screen's actual content.

Keep existing Blackjack artwork that the owner likes, explicitly the current
playing cards/card frames, faces and backs. A menu game icon is distinct from
the game's assets. The owner subsequently approved preparing new gameplay
symbols for Tic-Tac-Toe (individual blue X and pink O) and Schere–Stein–Papier
(individual V-sign hand, blue stone and open palm matching the new emblem).
These are additional source assets; current runtime artwork is not overwritten
or wired in during preparation. Aiko's character sprites and item overlays remain
outside this asset pass. No game-rule, balance, save or Moodlet-domain change
is authorized.

## Approved appearance

- Smooth illustrated anime/VN with cozy JRPG/life-sim influence; no pixel UI.
- Almost-white rose body; pure-white title bar with Aiko and settings. One
  keep-open control sits in the footer; do not duplicate the pin in the title bar.
- Flat pale-blue information surfaces with delicate blue outlines.
- Compact, narrower pale-rose action buttons with a defined rose outline,
  restrained upper highlight and shallow shadow. Buttons remain recognizably
  different from readouts even without relying only on color.
- Dark blue-gray readable text, gently rounded sans serif. The approved
  interactive reference uses Segoe UI. Check German
  diacritics, text length, small-size readability, installation/bundling and
  existing repository font rules during implementation. Approval of the
  reference appearance does not acquire or bundle a font asset.
- Original small illustrations: rounded contours, powder blue, dusty rose,
  subtle cream accents and restrained sparkles. Maintain coherent stroke weight
  and readable silhouettes at actual UI size.

Provisional color tokens, sampled from the design brief rather than guaranteed
pixel values in generated images:

| Role | Candidate |
| --- | --- |
| Title surface | `#FFFFFF` |
| Main rose surface | `#FCF7F9` |
| Passive readout surface | `#EDF4FA` |
| Readout outline | `#B8CDDF` |
| Progress accent | `#94B5CF` |
| Action surface | `#F3DAE3` |
| Action outline | `#C68FA5` |
| Primary text | `#3E4C61` |

## Main-menu structure

The approved [control/panel source contract](../assets/ui-vn/v1/controls/README.md)
prepares five blank rose button states, a shared passive panel/tooltip surface,
and an empty status track plus transparent rim.
Labels/icons remain separate. Need and numeric-mood fills change smoothly with
value (green at high values through yellow/orange to red at low values); the
whole filled portion changes color, not a fixed rainbow. Friendship keeps a
fixed blue fill. The detailed source document defines intended use, layering,
resizing, candidate visual colors and later export/Windows validation boundaries.
The older all-blue mockup bars are historical illustrations of layout, not the
latest approved semantic-fill specification.

1. White title bar and compact global emotion/mood summary.
2. Separate Moodlet strip immediately below the summary.
3. Dedicated wish row between Moodlets and the care columns, with up to three
   wishes showing concrete targets, objective scope/progress and remaining time.
4. Six need/relationship displays stacked vertically on the left. A narrower
   interaction button sits to the right of the corresponding display.
5. Quiet computer-information/context strips.
6. One keep-open control and detail disclosure.
7. Expanded details inside the same window, with their own scroll region.

| Readout | Adjacent interaction |
| --- | --- |
| Sättigung | Snack; opens embedded selection |
| Spaß | Spielen; opens embedded selection |
| Energie | Schlafen / appropriate current sleep action |
| Sozial | Unterhalten; opens embedded selection |
| Zuwendung | Streicheln; direct action |
| Freundschaft | Passive context, no invented direct friendship action |

Only actual submenu buttons get a navigation chevron. Keep direct actions
visually direct. Preserve authoritative runtime availability and refusal rules.

### Embedded selectors

Snack, Spielen and Unterhalten replace only the right interaction column with
their selection view and a Zurück control. Keep the same outer window, stable
geometry, left readouts, global summary and Moodlets visible. Do not open a
separate native selector window. Fit longer labels by deliberate wrapping.
Food choices may require a scrollable right region; exact dimensions require
native Tk verification rather than inference from the concept images.

Use current food choices and social categories; do not invent content. Current
game selection is Schere–Stein–Papier, Blackjack and Tic-Tac-Toe. Choosing a game
and the eventual game-screen/window design remain separate implementation work.
No decision in this document changes game rules or requires the gameplay screen
itself to fit into the right selection column.

### Expanded details

Reveal a full-width passive section below the existing menu content. Use small
illustrations, readable headings and fine separators, not another action grid.

- Befinden: existing emotion and contextual hint.
- Tagesrhythmus: current activity/rhythm description, strain and uptime where
  actually available.
- Als Nächstes: the existing next-activity/time projection.
- Gegenstände: desktop, known, assigned and missing counts.

Mockup times, Moodlets, quantities and values are examples, not runtime evidence.
If height is constrained, make the expanded region scrollable and keep essential
controls reachable; final geometry and focus/hover behavior need Windows testing.

## Shared surfaces, focus and restrained effects

Use the same near-white blush panel with a delicate powder-blue edge for expanded
details, embedded submenu content and the wish information area. Reuse its surface
for Moodlet/wish tooltips, with more compact padding and a small local shadow.
Text, icons, separators and any placement-dependent tooltip pointer remain separate.
Preserve the pure-white title bar. Tooltip placement must stay inside screen bounds
and support keyboard access; it must not cover the interaction being explained.

The fifth button state, **active**, represents a persistent selection such as
Offen halten. A stronger rose edge and inner accent distinguish it from the
momentary pressed state. Derive it from the existing authoritative selection;
do not add a parallel state owner. Keep the pin/label or equivalent textual state
cue separate. Disabled controls do not show enabled hover/press feedback.

Keyboard focus is an independent UI-drawn blue-gray outline, provisionally 2 px
with a small gap. It can coexist with an active button and must remain visible
without relying on rose color differences. Scrolling regions use a quiet near-white
rose track and a sufficiently visible blue-gray thumb, with clearer hover/drag
feedback. Preserve wheel, keyboard and direct dragging access. Focus outlines and
scrollbars need no additional raster assets.

Keep motion brief and local: provisional hover crossfades of 80–140 ms, immediate
press feedback and 120–180 ms soft appearance for newly revealed content where
the renderer supports it. These are tuning candidates, not acceptance constants.
Keep embedded-selector geometry stable and do not delay input for an animation.
Avoid bouncing, constant glow, sparkles or pulsing status bars. Respect reduced
motion and use an immediate state change where fading is unavailable. Render these
effects in the UI; no animation-frame asset set or global dimming overlay is needed
for the agreed menu flows. Native Windows/Tk feasibility remains part of integration.

## Moodlets — UI provision, not domain implementation

Reserve a distinct row of individual icons with a short textual tag below each.
Hover exposes a readable description of the impression/cause, with relevant
strength and remaining time when supplied by the authoritative projection.
These are passive impressions, not action buttons or extra need bars. The strip
remains visible while an embedded selector is open.

The reference tags Geborgen, Stolz, Erleichtert and Genervt are initial artwork
examples, not a complete/final Moodlet catalogue. The candidate rules and open
domain decisions remain in
[the care/time plan](CARE_TIME_IMPLEMENTATION_PLAN.md#5c-connect-status-expression-and-interaction-decisions).
The subsequent approved [artwork extension](../assets/ui-vn/v1/MOODLETS_AND_WISHES.md)
now prepares sources for all 18 documented Moodlet families and components for
the 11 wish forms. This expands graphic coverage only, not domain implementation.
Do not infer a Moodlet from a low need or invent expiry/reward logic in the UI.
A wish and an active Moodlet remain separate concepts.

The owner subsequently requested integrating this main-menu direction into the
[care/time refactor's stage 5C](CARE_TIME_IMPLEMENTATION_PLAN.md#5c-connect-status-expression-and-interaction-decisions).
That plan now specifies `MoodletStrip` and a separate embedded `WishPanel` for
up to three active wishes, with shared read projections and image ownership.
The wish panel extends the original generated reference boards, which do not show
its layout. The owner-approved [full interactive concept](UI_PREVIEW_HANDOFF.md#reference-entry-points)
places the dedicated row between Moodlets and care columns.
Keep it in the same main window and visible while using embedded selectors;
the UI does not create wishes or interpret Moodlet rules. This records the
integration scope; application/UI implementation remains pending authorization.

The approved concept uses horizontal Moodlet overflow, wrapped tags and
screen-clamped descriptions available by hover, focus or tap. Narrow review
viewports also allow horizontal wish-row scrolling. Keep the resting icons/tags
understandable independently of tooltips; verify the behavior at native sizes
and with keyboard input during implementation. No domain maximum Moodlet count
is established by the ten-icon overflow example.

## Preserved visual evidence

The [full main-menu review](UI_PREVIEW_HANDOFF.md#reference-entry-points) combines the
prepared artwork with three illustrative wishes, all 11 current food choices,
three games, four conversation choices, status areas and expanded details.
It also exposes empty/overflow, loading/error/opt-out and unavailable-action
examples. The owner inspected this concept and approved it as matching the intended
design on 2026-10-20. Wish placement, one footer pin, selector composition, reference
proportions/typography and shown visual states are the accepted design target.
Example values/times/descriptions remain illustrative; native geometry, font
delivery and runtime behavior still require implementation and validation.
This approval does not authorize application changes or settle domain rules.
Application code and original source images are unchanged by this design pass.

These are generated design references, not screenshots of the running app:

- [Approved rose/blue menu, embedded selector and compact buttons](media/ui-vn-2026-10-20/compact-buttons.png)
- [Moodlet placement, hover description and rose-versus-blue comparison](media/ui-vn-2026-10-20/moodlets-tints.png)
- [Expanded details in the selected rose direction](media/ui-vn-2026-10-20/rose-details.png)

The full interactive reference takes precedence for the main-menu composition.
The generated expanded-details board remains supporting color/detail evidence;
earlier boards show the navigation concept. Preserve the approved compact buttons.

## Approved settings and separate Credits

The owner subsequently requested a matching clickable settings preview and a
separate Credits area for API/content information on 2026-10-20. The
[approved settings reference](UI_PREVIEW_HANDOFF.md#reference-entry-points) covers the existing eight
Boolean options, the two scale choices and the existing local actions. Its four
areas are Darstellung, Verhalten, Lokale Daten and Credits. The owner inspected
and approved the layout, controls, appearance and separate Credits organization
on 2026-10-20. Together with the approved main menu, this is the design target.
Reference proportions remain subject to native sizing/DPI and interaction validation;
sample content metadata remains illustrative. This approval authorizes no
application implementation and changes no existing license or domain rules.

| Settings area | Accepted controls |
| --- | --- |
| Darstellung | Size 1×/2×; Immer im Vordergrund; An der Taskleiste laufen; Maus beobachten |
| Verhalten | Automatischer Tagesrhythmus; Von selbst sprechen; Rechnerauslastung beobachten; Meinen Rhythmus kennenlernen; Onlinequellen für Witze und Fakten verwenden |
| Lokale Daten | Tagesmuster löschen; Leiste zu Aiko; Aiko zentrieren |
| Credits | APIs & Inhalte; Grafik & Lizenzen; Projekt |

Use styled native checkboxes with a visible checkmark, An/Aus text and keyboard
focus; the size choice is segmented. Preserve immediate setting application rather
than adding a Save action. Settings remains independently movable and nonmodal.
Its content scrolls while navigation/footer remain available. The accepted reference
uses approximately 752 px outer width and a 484 px content viewport; these are
visual proportions, not verified native dimensions. Close/Escape closes settings,
while Aiko beenden remains a distinct action. Review-only example/reset controls
do not become product settings.

Credits is a distinct view reachable from settings, not a panel inside a game.
Group API/provider information, the last accepted content's source/API-entry
links, graphic/license notices and project credits there. Preserve the distinction
between an API provider and the original source of an individual content item.
The online-content opt-in remains in behavior settings. This new placement
instruction supersedes the inline source-link area from the earlier main-menu
review; the preview now links to central Credits instead. Main-menu geometry,
need/Moodlet/wish presentation and game artwork are unchanged.

This is presentation design only: preserve the existing preference and social
metadata owners, optional source fields and authoritative action rules. No new
source history, save fields, API requests or application changes are authorized.
Existing attribution/license notices remain intact; the current runtime is not
changed by documenting their future presentation location.

## Approved game surfaces and completed preparation

The owner next requested matching clickable game surfaces, keeping the existing
Blackjack cards and continuing to exclude application changes. The
[three game concepts](UI_PREVIEW_HANDOFF.md#reference-entry-points) cover Schere–Stein–Papier,
Tic-Tac-Toe and Blackjack with their existing distinct flow, session counts,
turn/result feedback and character-side hands/cards. The owner inspected the
external reference bundle and explicitly approved all three game designs on
2026-10-20, separately from the earlier main/settings approvals.
Existing card PNGs/frames, the character and application code are not modified.

- Shared game surfaces: white title bar, rose body, compact rose actions, blue
  passive information, visible phase/result, temporary player/Aiko/draw/round
  counts and Close/Escape. Character-side reactions stay with Aiko on the desktop.
- RPS: three prepared signs; previous revealed player hand remains labeled during
  countdown; reveal the new hands together, with Aiko's sign outside the player
  window. Disable choices while busy; choosing another sign starts the next round.
- Tic-Tac-Toe: one shared 3×3 board, prepared blue X for the player and rose O for
  Aiko; disable occupied fields and all input during Aiko's turn. Highlight the
  winning line and enable Nächste Runde only after settlement; starters alternate.
- Blackjack: player-only hand/total inside the window, 128×128 card canvases at
  integer 2× scale in the existing 480 px bounded-overlap area. Karte ziehen uses
  a pile of the unchanged backs; Bleiben is separate. Aiko's masked/revealed hand
  stays at her desktop figure; hidden identities/totals never appear before reveal.
  Hover may lift a card but clicking cannot reveal it. After a result, preserve
  the existing 2.8-second automatic next hand, not a new next-round button.

Game tabs, frozen example-state selectors and local fixture logic belong only to
the external review bundle. Production keeps its existing game/sequence owners,
rules, admission, timer cancellation and reward behavior. Reference controls do
not add stakes, chips, difficulty settings, new save fields or runtime game logic.

The owner then stated that these are enough preview examples and need not be
committed, provided they remain accessible to other chats. The
[shared local handoff](UI_PREVIEW_HANDOFF.md) identifies the durable bundle outside
the checkout, design approvals, source readiness and later implementation checks.
No further example screen or concrete missing generated asset remains for the
agreed scope. With explicit game approval, these design/asset preparations are
complete. Native exports, font/DPI checks and integration belong to later
implementation and remain unauthorized in this design pass.

## Asset preparation

Sources and generation prompts live in
[assets/ui-vn/v1](../assets/ui-vn/v1/README.md), outside the runtime asset tree.
Generate individual transparent original icons rather than treating whole
screen mockups as usable UI assets. Reuse an icon across roles where suitable:
onigiri for satiety/Snack, controller for fun/Spielen, bubbles for social/talk,
and heart for affection. Blackjack menu imagery should reuse the existing
playing-card artwork; no new card deck is requested.

The initial pack covers status, direct actions, common controls, detail sections,
two additional game-selection emblems, their five individual gameplay symbols,
all 18 documented Moodlet families, and five reusable wish components. Keep
semantic labels and tooltips as text rendered by the UI, not baked into PNGs.
Source images are not yet runtime-sized exports or proof of native integration.
Track output hashes, dimensions, alpha checks, subjects and exact prompts.

## Later implementation and acceptance

Implement only after separate authorization. Retain existing ownership:
HoverUi owns visibility/window lifetime, views render snapshots and invoke
ports, and domain/application owners retain state and rules. A shared skin can
own visual tokens and root-local images; do not create a second state owner.

Acceptance must include actual-size icon/text review, keyboard/focus/hover
behavior, on-screen bounds, integrated selectors, detail scrolling, topmost/
pin semantics and image cleanup in native Windows/Tk with an isolated save.
Apply relevant repository gates at that implementation stage. Documentation
and image preparation alone are not a runtime verification.
