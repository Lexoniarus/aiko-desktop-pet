# Aiko VN interface direction — 2026-10-20

Status: owner-approved visual direction and menu concept. Documentation and
asset preparation are authorized; application/UI implementation is not.
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
- Almost-white rose body; pure-white title bar with Aiko, pin and settings.
- Flat pale-blue information surfaces with delicate blue outlines.
- Compact, narrower pale-rose action buttons with a defined rose outline,
  restrained upper highlight and shallow shadow. Buttons remain recognizably
  different from readouts even without relying only on color.
- Dark blue-gray readable text, gently rounded sans serif. The exact font is
  still open: check German diacritics, text length, small-size readability,
  consistent installation/bundling and existing repository font rules before
  selecting one. The mockup font is not an acquired font asset.
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

1. White title bar and compact global emotion/mood summary.
2. Separate Moodlet strip immediately below the summary.
3. Six need/relationship displays stacked vertically on the left. A narrower
   interaction button sits to the right of the corresponding display.
4. Quiet computer-information strip.
5. Keep-open control and detail disclosure.
6. Expanded details inside the same window.

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
The wish panel extends the reference boards, which do not yet show its layout.
Keep it in the same main window and visible while using embedded selectors;
the UI does not create wishes or interpret Moodlet rules. This records the
integration scope; application/UI implementation remains pending authorization.

Before implementation, settle overflow when many impressions coexist, long
localized tags, tooltip placement at screen edges, and tooltip access without
a mouse. The resting icons and tags must remain understandable independently
of tooltip presence. No exact maximum Moodlet count is agreed yet.

## Preserved visual evidence

These are generated design references, not screenshots of the running app:

- [Approved rose/blue menu, embedded selector and compact buttons](media/ui-vn-2026-10-20/compact-buttons.png)
- [Moodlet placement, hover description and rose-versus-blue comparison](media/ui-vn-2026-10-20/moodlets-tints.png)
- [Expanded details in the selected rose direction](media/ui-vn-2026-10-20/rose-details.png)

The expanded-details reference is the color/detail reference. Earlier boards
show the navigation concept. The approved compact-button proportions remain
the target when later generation varies slightly.

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
