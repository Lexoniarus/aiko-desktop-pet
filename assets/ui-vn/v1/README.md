# Aiko VN menu icons — source set v1

**Moodlet addition (2026-10-25):** eight new transparent source icons and their
24–128 px exports complete coverage of the current 26 Moodlet families. The
[dated extension record](moodlets-2026-10-25/README.md) contains the inventory,
prompts and validation. The owner subsequently authorized immediate use; all eight
new symbols are now assigned through the shared runtime Moodlet icon mapping.
The older preparation notes below are historical.

**Implementation update (5C, 2026-10-20):** main status/menu, embedded selectors,
shared VN assets and settings/Credits are implemented on `feature/social-optimization`.
The preparation-only authorization statements below describe the historical
approval pass. The external reference bundle and original masters are unchanged.
The three gameplay layouts/artwork remain with their existing owners; native
Windows/DPI/input acceptance has not been executed in this headless delivery.

Prepared 2026-10-20 with the built-in Imagegen tool for the owner-approved
[VN interface direction](../../../docs/UI_VN_DESIGN.md). This folder contains
original transparent PNG source candidates and generation provenance. Nothing
in the running application references these files yet.

## Scope

Main hover menu first: readouts, adjacent interactions, detail headings, common
controls, game-selection emblems, all 18 documented Moodlet families and reusable
wish components. Reuse the same
icon across matching status/action roles. Preserve the existing playing cards
and their frames; Blackjack can use that existing artwork for its menu entry.
The owner also approved new source gameplay symbols for Tic-Tac-Toe (blue X,
pink O) and Schere–Stein–Papier (V-sign hand, blue stone, open palm), matching
the generated emblems. Existing runtime files, items and character sprites
are unchanged until separately authorized integration.

## Sources and review

- [Approved interface design](../../../docs/UI_VN_DESIGN.md) records the main menu,
  settings, separate Credits and three game surfaces approved on 2026-10-20.
  Design/asset preparation is complete; application integration is not authorized.
- [Shared local handoff](../../../docs/UI_PREVIEW_HANDOFF.md) locates the approved
  clickable references outside the checkout. Example pages and rejected image
  attempts are deliberately not versioned production resources.
- [Button, status-bar and panel sources](controls/README.md) document eight selected
  control sources, five button states, a shared panel/tooltip surface, dynamic
  green-to-red fill and fixed-blue friendship. Focus, scrolling and transitions
  are UI-rendered specifications. Original selected source pixels are unchanged.

- [Icon gallery](preview.html) displays originals on the chosen rose background,
  alongside small-size previews. It is a standalone asset-review document,
  not a replacement application UI.
- [Exact generation prompts](generation_prompts.json) records each subject and
  the prompt set used with the built-in tool.
- [Moodlet/wish extension](MOODLETS_AND_WISHES.md) maps all 18 Moodlet families
  and 11 wish forms. Its [additional prompt set](generation_prompts_moodlets_wishes.json)
  records the 19 added originals.
- [Provenance](provenance.json) records output hashes, dimensions, alpha and
  reference files.
- [Icon files](#inventory) are unmodified source outputs, not runtime-size exports.
  Soft antialiased alpha and low-alpha fringe pixels require review in the
  later export/integration step. Source filenames are semantic, not translated
  labels. Display text and tooltips must remain runtime text.

Visual QA considers recognizable subjects, consistent outline/shading/palette,
no baked labels or UI backgrounds, and readable silhouettes at 24/32/48/64 px.
The exact output size is whatever the built-in generator returned; do not
assume square masters are already the required button dimensions.
All source images must have real alpha, transparent margins and uncut visible
silhouettes. Technical checks do not establish native Windows/Tk acceptance.

## Inventory

The initial source preparation checks passed for 27 PNGs: RGBA, 1254 × 1254 pixels,
real transparent/opaque alpha, and all visible silhouettes (alpha >= 32)
inside the canvas. Documentation/gallery paths and expected inventory also
passed. The provenance file stores hashes and per-image measurements. Originals
have differing optical extents and faint low-alpha fringe; normalize those
deliberately during a later export pass, keeping these masters intact.

| File | Role / subject |
| --- | --- |
| [status_satiety.png](icons/status_satiety.png) | status — A single small triangular Japanese rice ball (onigiri), soft white rice body and a muted dark-navy rectangular nori patch. A tiny blush sparkle beside it. |
| [status_fun.png](icons/status_fun.png) | status — A single rounded powder-blue game controller with navy directional pad and three small dusty-rose buttons, with one tiny sparkle. |
| [status_energy.png](icons/status_energy.png) | status — A single small horizontal rechargeable battery, navy-blue outline, pale blue casing, three soft desaturated mint charge segments and a tiny dusty-rose energy mark. |
| [status_social.png](icons/status_social.png) | status — Two overlapping friendly rounded speech bubbles, one powder blue and one dusty rose, with three small navy dots in each. |
| [status_affection.png](icons/status_affection.png) | status — One rounded blush-pink heart, dark dusty-rose outline, tiny pale highlight and a single subtle sparkle. |
| [status_friendship.png](icons/status_friendship.png) | status — Two companion stars, a slightly larger soft warm-cream star and smaller dusty-rose star, both with a navy-blue outline. No faces. |
| [action_sleep.png](icons/action_sleep.png) | actions — One powder-blue crescent moon with a tiny small four-point star, rounded soft navy outlines. |
| [action_pet.png](icons/action_pet.png) | actions — One stylized friendly gently curved petting hand, pale blush skin tone and navy outline, with a tiny pink heart above. No arm, no animal, no person. |
| [detail_wellbeing.png](icons/detail_wellbeing.png) | details — One powder-white speech bubble with navy outline containing a small blush-pink heart. |
| [ui_sparkle.png](icons/ui_sparkle.png) | controls — One softly rounded four-point sparkle star, dusty rose fill and slightly darker dusty rose outline. Simple and elegant. |
| [ui_pin.png](icons/ui_pin.png) | controls — One small tilted pushpin, powder-blue head, navy outline and navy point. Soft rounded illustrated shape. |
| [ui_settings.png](icons/ui_settings.png) | controls — One single compact powder-blue settings cog with rounded teeth, navy outline and a clear central hole. |
| [detail_rhythm.png](icons/detail_rhythm.png) | details — One powder-blue crescent moon paired with a very small circular clock at lower right, navy outline, simple clock hands, no numbers. |
| [detail_next.png](icons/detail_next.png) | details — One small powder-blue desk calendar, navy rings and navy outline, a simple three-by-three grid of blue square date marks, no text or numerals. |
| [detail_objects.png](icons/detail_objects.png) | details — One small powder-blue archive box with lid and a short centered navy handle slot, slight illustrated depth and rounded navy outlines. |
| [system_computer.png](icons/system_computer.png) | details — One small clean powder-blue computer monitor with navy outline and short desktop stand, pale reflective screen, no text or interface inside. |
| [game_rps.png](icons/game_rps.png) | games — A coherent compact trio of symbols for rock-paper-scissors: one small peace-sign hand, one small rounded blue rock, one small open palm. Arranged as one balanced horizontal emblem. Soft blush and powder-blue palette, navy outlines. Only two hands, each anatomically readable. |
| [game_tic_tac_toe.png](icons/game_tic_tac_toe.png) | games — One small three-by-three tic-tac-toe board with thin navy grid, three blue X marks and three dusty-rose circle marks. The remaining cells empty. No letters or labels besides the X game marks. |
| [moodlet_secure.png](icons/moodlet_secure.png) | moodlets — Two small cupped hands holding a single blush-pink heart, conveying warmth and safety. Soft pale blush hands, navy contours, small subtle highlight. |
| [moodlet_pride.png](icons/moodlet_pride.png) | moodlets — One small trophy with warm muted cream-gold cup, powder-blue base and navy outline, one tiny dusty-rose sparkle. No text or numbers. |
| [moodlet_relief.png](icons/moodlet_relief.png) | moodlets — One small soft white and pale-blue cloud with a muted cream sun peeking from upper right, delicate blue outlines and three short sun rays. Calm gentle weather emblem. |
| [moodlet_annoyed.png](icons/moodlet_annoyed.png) | moodlets — One small gently annoyed round dusty-rose face, navy curved eyebrows and small frown, tiny dusty-coral lightning mark at upper right. Express mild irritation, not rage. No emoji gloss. |

Additional owner-approved gameplay source files:

| File | Role |
| --- | --- |
| [play_ttt_x.png](icons/play_ttt_x.png) | Blue X playing token |
| [play_ttt_o.png](icons/play_ttt_o.png) | Pink ring playing token |
| [play_rps_scissors.png](icons/play_rps_scissors.png) | V-sign hand |
| [play_rps_rock.png](icons/play_rps_rock.png) | Blue rock symbol |
| [play_rps_paper.png](icons/play_rps_paper.png) | Open palm |

The icon catalogue contains 54 PNG sources after the
[2026-10-25 Moodlet extension](moodlets-2026-10-25/README.md); the separate controls folder adds
eight selected control/panel sources. Four excluded exploratory drafts remain
in the external local reference bundle, with their hashes/prompts retained here.
The table above lists the initial 27 icons;
the [extension inventory](MOODLETS_AND_WISHES.md) maps the 14 additional Moodlet
motives and five wish components. Historical combined checks are in provenance.json;
the new extension records its prompts and validation separately.
The artwork covers the documented candidate catalogue without implementing
triggers, rewards, duration or stacking. Keep those decisions in the existing
care/time plan.

## Provenance and terms

Generated using OpenAI's built-in Imagegen tool from the project's approved UI
concept images and descriptive prompts. This is newly generated menu artwork,
not Kenney artwork and not a repackaged third-party icon set. Existing Kenney
card attribution and licenses remain with those unchanged files. This asset
pass records origin and does not amend the project's existing license terms
or assign an additional UI-specific license.
