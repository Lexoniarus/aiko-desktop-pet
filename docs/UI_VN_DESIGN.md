# Aiko VN interface direction — 2026-10-20

## Approved Rock–Paper–Scissors identity and animation — 2026-10-28

The owner approved the Fingerduell revision at
`../design-previews/rps-animation-2026-10-28/preview.html`, relative to the checkout
root. Its README and `approval-record.json` retain the acceptance and file hashes.
This is the latest RPS visual/animation concept authority, extending the accepted
2026-10-27 direct-selection flow below; the older bundle remains unchanged.

- Keep the VN white title and rose shell. A small illustrated rose playmat has
  stitched edging, fabric patches, quiet stars and a cream round hand area with
  powder-blue trim. The unchanged hand illustrations determine the rounded,
  outlined visual language. Blue, peach and lavender hand tiles provide clear
  pressure depth; name and hint sit legibly below the mat. A fanned trio of
  existing signs forms the title emblem. Reveal adds one restrained glint.
- Choosing a sign still immediately starts a round and shows the player's hand.
  Aiko performs **three complete existing Attack cycles**, with **900 ms per
  movement** as the accepted calmer preview default. Words Schere, Stein and
  Papier coincide with frame 04, the forward moment, of their respective cycle.
  Her independently chosen sign and the result appear at that moment of cycle
  three: 2250 ms in the default preview; the final movement ends at 2700 ms.
  No 1–2–3 text, extra start or next-round action is introduced.
- Inputs lock until reveal and then enable. A new choice cancels the remaining
  arm movement or result reaction immediately, preserving exactly-once scoring.
  The character finishes the third move before her normal result response when
  not interrupted. Both revealed signs stay until the next choice.
- Existing V3 idle/gaze and compatible body poses support quiet selection waits
  and a short post-round board glance. Existing emotes and selected happy jumps
  express cheeky satisfaction, her own embarrassment or surprise at a draw.
  **Aiko's sign stays visible in the lower bubble area while only the reserved
  comment area above alternates text and emoji.** No extra taskbar object.
- All character/hand assets are unchanged copies. New mat/glint SVGs and CSS
  hand tiles are code-native preview artwork. A display-only four-source-pixel
  offset aligns the Attack floor with idle; jump movement remains intact.
  Closing, reset and scene changes cancel all pending presentation. Reduced
  motion keeps the same word/reveal schedule with still poses.

The selectable 750/850 ms alternatives, fixed outcome examples, controlled-clock
checks and mobile stacking are review affordances. The earlier animation-only
draft remains under `history/animation-only/` for comparison. Final native
animation/speech coordination, relationship variants and Windows input/placement
verification remain separate implementation work. No application changes,
production installation, game-rule changes or saves are authorized by approval.
The external HTML and source copies remain outside Git.

## Approved Quiz follow-up — 2026-10-28

The owner accepted the revised Quiz design and moderation concept at
`../design-previews/quiz-2026-10-27/preview.html`, relative to the checkout root.
Its README and `approval-record.json` retain the acceptance, reviewed file hashes
and the preview limitation below. This is design approval, not native execution
or animation-timing acceptance; application integration remains separate work.

- Keep the shared white title and near-white rose shell. The quiz has its own
  blue-violet miniature studio, curtain arcs, soft spotlights, cream/gold question
  board, rose answer podiums, question-mark/star emblem and ten progress bulbs.
  Answer text is centered on both axes, with independent left-middle A–D badges
  and bottom-center status labels. Short answers use two columns, long ones one;
  their reserved spaces prevent layout jumps as options appear.
- Aiko is the exaggerated host of her own small anime quiz show. Formal host
  announcements alternate with warm personal asides about her own performance,
  such as providing the applause herself. The question, choices and factual
  explanation come unchanged from the existing local catalogue. The ten sampled
  questions and example remarks demonstrate direction, not a final dialogue pool.
- She presents the full question, then A, B, C and D individually. **Each answer
  button becomes visible only when its own introduction begins.** Previously
  introduced answers remain visible. All inputs stay locked through the final
  release cue; unseen options are also hidden from accessibility. A fresh
  question resets visibility. There is no player response time limit.
- Choice immediately locks all answers and marks the selection without revealing
  correctness. Aiko acknowledges it, performs her suspense aside, then reveals
  the solution and current point. Her explanation and continuation cue finish
  before manual **Nächste Frage** becomes available. After ten questions her
  closing gates **Neue Quizrunde**. There is no opponent score against Aiko.
- Reuse installed V3 2X idle/gaze, compatible body-look/body-turn poses and
  existing emotes. Reading carries a sustained three-quarter stance toward the
  actual question-window position, with neutral looks between board and cue
  cards. Player address returns frontal; personal asides use deliberate side/up
  looks. Emotes replace text between beats. Selected existing happy jumps add
  emphasis after disclosure, never hint at the solution beforehand.
- While awaiting a choice, use occasional frontal hands-together/head-lowering
  poses from the existing V3 `waiting` sequence, side/up/down looks and sparse
  host comments, including occasional repetition of the actual question.
  **This waiting behavior starts automatically after release, without hover or
  other player input.** Answers remain enabled throughout. Choice immediately
  interrupts the waiting gesture/comment; closing, reset and scene changes
  cancel pending presentation. This gesture has no wish, care or state effect.
- Preview timing starts with a gesture at about 9 seconds and a comment at about
  24 seconds, then roughly 25–30 seconds between comments. These are review
  values, not final native timing. Fast review, frozen examples, controlled-clock
  checks and narrow-browser stacking are preview affordances. Reduced motion
  preserves moderation and input gates while showing appropriate still poses.

**Recorded preview limitation:** the owner observed that the waiting sequence
seemed to start or resume only after hovering answer buttons, then accepted the
design without requesting a preview fix. The cause has not been established.
Automated checks passed, but do not override that observation. Reliable automatic
start without hover and interruption under native Windows input must be verified
when implementation is separately authorized. Final pacing, speech/animation
priorities and relationship-sensitive dialogue variants also remain open.

The external bundle retains source provenance, unchanged asset copies, checks
and screenshots. The HTML examples stay outside Git. No application changes,
production-asset installation, catalogue, game-rule, World or save changes are
authorized by this approval.

## Approved Blackjack concept — 2026-10-27

The owner accepted the visual direction and basic flow of the separate Blackjack
preview at `../design-previews/blackjack-2026-10-27/preview.html`, relative to the
checkout root. **Animation pacing and sequencing still need refinement.** This
is approval of the basic concept, not final acceptance of the animation timing.
Its README and `approval-record.json` retain the statement, caveat and file hashes.

- Aiko theatrically plays an over-the-top Las Vegas casino dealer for her one
  VIP guest. Warm Chibi comments, exaggerated professionalism, dramatic reveal
  and brief flustered reactions carry the role. Existing artwork is reused.
- The VN window has a white title, near-white rose body, passive blue phase
  surface, emerald/cream/gold card table, own total, hit/stand actions and session
  tally. Only player cards appear inside the independent, freely draggable window.
- Preserve all existing 52 card faces and the back, including frames and colors.
  **Every card uses the same 128×128 display area**, including Aiko's hand, deck,
  flying cards and shuffle packets. This supersedes the older mixed-size reference.
- Aiko's bank hand stays **to her left**; the shared deck is **to her right**.
  Existing Attack frames act as a remote show gesture toward that deck. Shuffle
  packets move above the deck without touching her hands; the former pickup
  gesture and opposite-side arrangement remain local history.
- The sequence demonstrates gathering old cards, shuffling, alternating four
  individual initial deals, player hits and dealer draws from the same desktop
  deck. Flights retain card size and track the dragged player-window destination.
  Cards and totals appear in a hand on landing; the dealer hole card stays hidden
  during travel and until the normal reveal, including accessible descriptions.
- The fixed dealer policy and existing Blackjack rules remain the baseline.
  The current 2.8-second result pause leads into collection/shuffling/dealing;
  frozen review examples remain still. Exact pauses, movement curves, gesture
  transitions and speech coordination are explicitly **open refinements**.
- Close/reset/example changes cancel movement and pending callbacks. Reduced
  motion skips nonessential travel. Narrow-browser rearrangement is a preview
  affordance and retains the common card size.

The external bundle retains unchanged source copies, card provenance/license,
diagnostic comparisons, screenshots and validation. The concept approval does
not authorize application changes, production-asset replacement or native
integration. The complete dialogue catalogue and final native animation/speech
priorities remain separate work. Quiz has a separately approved follow-up above.

## Approved Mastermind follow-up — 2026-10-27

The owner approved the final clickable Mastermind revision at
`../design-previews/mastermind-2026-10-27/preview.html`, relative to the checkout
root, including the corrected safe opening and both snack endings. Its README
and `approval-record.json` retain the explicit approval and reviewed file hashes.
The earlier distorted/mirrored door projection remains rejected local history.

- Shared white title, near-white rose body, passive blue phase surface and rose
  actions surround a lavender/silver console with restrained gold star details.
  Four code places, six color/symbol stones, repeated colors allowed and ten
  attempts. The active editable row stands out; previous guesses remain visible.
- Color selection or drag/drop edits only the active draft. Existing stones can
  be picked up and swapped; invalid drops preserve the draft. **Code prüfen**
  submits a complete row. Gold diamond markers mean correct color and place;
  light round markers mean correct color elsewhere. Their grouped order does
  not identify code positions. Input locks during evaluation and the ending.
- Aiko playfully guards her own snack, with exaggerated seriousness and warm
  Chibi curiosity. The player cracks the safe for her. Her comments respond to
  the ordinary visible feedback, without leaking extra secret information.
- The small lavender-blue anime safe stands **to Aiko's right**, in the accepted
  slight three-quarter view, with its feet on her straight floor baseline.
  Bubble and safe belong to her desktop presentation; the independent player
  window remains stationary and freely draggable.
- The corrected continuous opening uses both actual door drawings. The closed
  face narrows to the hinge view, then the real open face widens into the supplied
  open artwork. No negative-scale mirror of the closed face. Housing and feet
  stay fixed. The 1560 ms opening and nine sampled frames illustrate the accepted
  motion; final native timing and animation/speech priorities remain later work.
- On success Aiko thanks the player, the code is revealed, the safe opens and
  she eats the rescued donut. After ten failed attempts she uses her spare key,
  opens it herself and eats the donut too. Both outcomes intentionally end with
  the same playful snack moment, with different comments and result labels.
- Eating reuses existing character frames, food artwork and documented food
  anchors. This gag has **no satiety, need, wish, Moodlet, reward or World-object
  effect**. The result stays until manual **Nächste Runde**; close/reset/example
  changes cancel pending motion. Reduced motion uses a quiet alternative.
- Direct opening replay, example codes, fixtures, local counters and narrow-
  browser stacking are review affordances. The complete relationship-sensitive
  dialogue catalogue and native integration are separate implementation work.

The external bundle retains native artwork, exact built-in Imagegen prompts,
source provenance, animation samples, browser checks and screenshots. This is a
design/documentation approval, not authorization to change application code,
production assets, game rules or saves. The HTML examples remain outside Git.

## Approved Connect Four follow-up — 2026-10-27

The owner approved the final clickable Connect Four revision at
`../design-previews/connect-four-2026-10-27/preview.html`, relative to the checkout
root. Its README and `approval-record.json` record the approval and reviewed file
hashes. This is the visual authority for Connect Four; earlier geometric board
drafts and the two-part flight remain local comparison history.

- Shared white title, near-white rose body, pale-blue phase/result surface,
  manual **Nächste Runde** button and compact player/Aiko/draw session tally.
  The stationary player window remains freely draggable; Aiko's presentation
  stays with her.
- A distinctive saturated blue illustrated board with a curved top rail, rounded
  side pillars, painted highlights, dark outlines and small feet. An exact 7×6
  presentation mask supplies the openings. The matching custom yellow/player and
  red/Aiko discs replace the Kenney placeholders in this approved reference.
  Native artwork, exports, exact built-in Imagegen prompts and provenance remain
  in the external bundle; no production files are replaced by this approval.
- Aiko is a mischievous little trap-setter. Short Chibi comments respond to real
  wins, blocks and legally reachable threats, including double threats. Her
  bubble and a small red chip stack remain beside her on the desktop.
- Column selection immediately drops the player's yellow chip. Input stays
  locked during resolution. Aiko uses unchanged existing pickup frames: contact,
  lift, release, one upward parabolic arc over the board, then a vertical fall
  through the chosen column. Incoming downward speed carries into the fall;
  the board changes only when the chip lands.
- Results persist until **Nächste Runde**; the player starts the first round and
  subsequent starters alternate. Close, reset and example changes cancel motion
  without late moves. Reduced motion uses a quiet hold and direct placement.
- Review selectors, fixtures, local search and narrow-browser stacking are demo
  affordances. The illustrated direction and throw concept are approved; final
  native grip/release timing, trajectory tuning, animation/speech priorities and
  relationship-sensitive dialogue still require implementation work.

This approval is for the design and its documentation. Application code,
production assets, game rules, World objects and saves remain unchanged.
Mastermind has a separately approved follow-up above.

## Approved Tic-Tac-Toe follow-up — 2026-10-27

The owner approved the final clickable revision at
`../design-previews/ttt-2026-10-27/preview.html` relative to the checkout root,
including Aiko's revised Chibi voice and existing character reactions. Its README
and `approval-record.json` retain the explicit approval and reviewed file hashes.
This supersedes the earlier Tic-Tac-Toe visual reference. The generic and dry
analyst drafts remain local history, not the approved character direction.

- White title, near-white rose body, stable pale-blue phase/result surface,
  large square board with nine recessed light cells, existing blue X for the
  player and rose O for Aiko, and a compact player/Aiko/draw session tally.
- A free-cell click immediately places X. Quiet hover/focus previews, temporary
  input lock while Aiko thinks, a brief last-move outline, and a highlighted
  winning line communicate the round. Occupied marks retain full contrast.
- The result stays visible. A rose **Nächste Runde** button keeps its reserved
  place, is disabled during play and enables after the result. The player starts
  the first round; subsequent starters alternate. No automatic round restart.
- Aiko is a small, curious, competitive Chibi desktop companion who thinks
  aloud, gets briefly flustered and enjoys a clever win. She discusses real
  winning paths and draw possibilities with playful seriousness, without
  percentage claims, bureaucratic analyst language or comments detached from
  the board. Her own mistake can prompt a sheepish correction.
- Board reading distinguishes immediate threats, double threats, a uniquely
  safe move and outcomes under best replies by both sides. This analysis is
  for commentary; the preview's existing opponent move policy is unchanged.
- Speech and existing character reactions remain beside Aiko. No extra taskbar
  item. Reuse unchanged gaze/Review poses, mild Failed poses and the existing
  happy jump. Reactions play once, can be interrupted and cancel on close;
  reduced motion and frozen examples use suitable existing stills. No new art.
- Review controls, local example scores, static scenarios and narrow-browser
  stacking are preview affordances. The 1.4-second thinking pause and selected
  reaction holds illustrate pacing; final native timing, relationship variants
  and animation/speech priority integration remain later work.

The approved HTML, copied images, provenance and review evidence remain outside
Git. This approval authorizes documentation only; application code, production
assets, dialogue catalogue, game rules and saves are unchanged. Player windows
retain the established stationary/free-drag contract; Aiko's bubble follows her.

## Approved Rock–Paper–Scissors follow-up — 2026-10-27

The owner approved the separate clickable follow-up at
`../design-previews/rps-2026-10-27/preview.html` relative to the checkout root.
Its README and `approval-record.json` retain the explicit approval and file hashes.
This is the base visual/interaction approval for Rock–Paper–Scissors; the
2026-10-28 Fingerduell follow-up above extends its identity and character timing.
The 2026-10-20 bundle remains the reference for surfaces without a newer approved
follow-up. No application code, production artwork or dialogue catalogue is
changed by this approval.

- Aiko is a spontaneous, slightly cheeky fellow player. Her revealed hand sign
  appears in her speech bubble with a short reaction. No extra taskbar item.
- White title, near-white rose body, a stable pale-blue phase/result area, a large
  central display of the player's own hand, three rose choice buttons, and one
  compact player/Aiko/draw tally. No duplicate Aiko-hand display in the player window.
- Choosing a sign immediately starts the round; no separate Los or next-round
  button. The player's chosen sign appears immediately, superseding the older
  previous-hand-during-countdown concept. Aiko's sign stays hidden until reveal.
- Lock input during the short countdown, then reveal Aiko's sign with the result.
  Both signs and the result remain until the player chooses again.
- Replace the literal rock illustration with a closed fist matching the existing
  paper/scissors hands. The approved new fist remains in the external preview;
  production export/registration still require a later implementation step.
- Review selectors, sample scores, local random rounds, reset and narrow-browser
  stacking belong to the preview. Sample dialogue is illustrative; relationship
  variants and final native timing remain to be developed. The preview's 650 ms
  beats do not prescribe final runtime pacing or change game rules.

The player window remains stationary and freely draggable; only Aiko's bubble
follows her, consistent with the existing window contract. This design approval
does not authorize native UI integration, character artwork or gameplay changes.

**Selector focus and Quiz frontend (2026-10-26):** ScrollRegion ignores FocusIn
events from ancestor frames and its own canvas before consuming a pressed
button's pointer-focus guard. Focusing the full content frame previously scrolled
the game selector to the bottom and moved choices before mouse release, losing
the first click. Button focus remains stationary during a pointer press; keyboard
focus still reveals offscreen choices.

Quiz answers now use the shared atomic ImageButton and existing rose button
artwork, with a window-specific wrap length cached independently of other button
styles. Correct answers retain their selected artwork and full text contrast
while input is disabled; the chosen incorrect answer remains explicitly labeled.
Questions and revealed explanations use the existing passive blue cards.
The question catalogue, ten-question flow, timing, moderation, scoring, fun and
wish rules are unchanged.

Validation: 84 focused automated selector/button/quiz/menu/layout tests pass,
including the ancestor-focus first-click regression, narrow answer wrapping,
locked answer feedback, ten-question completion and stable style-cache reuse.
Repository Ruff and strict Mypy pass; the two previously recorded Pyright
findings in the unrelated Rock-Paper-Scissors sequence test remain. Normal saves,
horoscope behavior and parallel character work are outside this correction.

**Atomic button rendering (2026-10-20):** the owner accepted the overall visual
appearance and reported delayed/missing Snack labels while scrolling. The
shared `ImageButton` now uses one native ttk button window. Prepared rose frame
states, icon, multiline text, right-hand submenu arrow and keyboard focus are
drawn together by its native style layout. Separate overlaid Label windows,
manual hover repainting and forwarded pointer events have been removed.
`IconImages` owns a lazy, root-local `ButtonStyles` cache shared by menus,
settings and game controls. Native disabled/pressed/hover/selected state drives
both input and appearance; callers still own commands and permission snapshots.
Repeated scrolling/reopening reuses styles and leaves no independently mapped
text/icon children. Original artwork, game rules and wish scheduling are unchanged.

Validation passed: 1,627 complete Windows tests, 84 targeted menu/settings/game
checks, Ruff, strict Mypy and Pyright. Native Windows inspection of the real
Snack selector covered scrolling down to lower entries and back to the top
without hovering the rows. Text and icons remained visible together. A separate
native check confirmed compact frame sizing and crisp disabled game symbols.

**Game-window refinement (2026-10-20):** the owner authorized implementing the
three approved game surfaces after the main-menu refinement. All three now use
the shared white title, near-white rose body, blue passive readouts, rose action
buttons, phase/result area and separate Du/Aiko/Remis/Runden counters. Credits
remain in settings. Existing sequences, rules, rewards and save format are unchanged.

- Schere–Stein–Papier uses the prepared stone, palm and V-hand in the choices,
  player reveal and Aiko's own bubble. The previous player hand remains during
  the next countdown. Choosing another sign starts the next round.
- Tic-Tac-Toe uses the prepared blue X and rose O on a square board with a
  legend and winning-field highlights. Occupied marks retain full-color art
  despite disabled native input. Nächste Runde and alternating starters remain.
- Blackjack retains every original card face/back/frame. Its 128 px player
  cards overlap inside the existing 480 px hand; a narrow window scrolls that
  hand horizontally. The original pile is the draw control; Bleiben is a
  separate rose button. Only player cards and points are in the game window.
  Aiko's concealed/revealed cards remain with her figure; the automatic
  next hand after 2.8 seconds is unchanged.

**Movement contract:** each player window is placed once beside Aiko, preferring
the right side, then the left, and clamped to the monitor's usable work area.
It subsequently stays where opened or dragged, including when Aiko moves or
changes scale. Dragging is available across the custom title and its text/icon,
excluding the close control and game content. The Windows monitor adapter
accounts for taskbar insets and negative monitor origins; pointer position
selects the work area during dragging. Only Aiko's own hand/cards and speech
follow her. Window position is session-local, without new save settings.

The shared game frame owns placement, dragging, passive status/counters and
the accessible footer. Each game view owns its content; existing sequence
objects retain gameplay/timer ownership. The desktop injects the work-area
query. Native horizontal/vertical scrolling keeps content available on small
work areas without shrinking the original Blackjack card assets. Derived
button sizes are exported from the approved sources; masters and the external
clickable references remain unchanged.

Native Windows inspection used disposable real Tk game widgets with mocked
output ports and an extra system title bar for capture. It covered all three
layouts and custom-title dragging. Regression checks cover stationary player
geometry while Aiko moves/scales, following Aiko overlays, work-area placement,
negative origins, narrow layouts, square tokens and existing game sequences.
This does not establish acceptance for every Windows DPI/multimonitor setup
or the complete production borderless focus/z-order stack.

Validation: the complete Windows run exercised 1,626 tests. One older headless
ImageButton fixture required the new optional artwork-label member; after that
fixture-only correction, all 87 VN/game/menu/window-architecture regression
checks passed together. Ruff, strict Mypy and Pyright passed. All 393 exported
UI images/catalog files reproduce byte-for-byte from the unchanged masters.

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
