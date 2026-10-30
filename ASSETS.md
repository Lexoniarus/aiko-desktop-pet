# Asset provenance, licensing, and acknowledgments

This repository includes original project content, AI-generated character artwork, and third-party Kenney game assets. Their origins are documented separately.

The new [VN menu icon sources](assets/ui-vn/v1/README.md) are generated
preparation artwork for the [approved UI direction](docs/UI_VN_DESIGN.md), not
runtime replacements. Their prompts and file provenance are recorded with the
sources. Existing playing cards/card frames and their Kenney attribution remain
unchanged. This preparation pass does not amend existing license terms.

## 1. Project source code — MIT

Unless a file identifies a different license, the project's own source code is distributed under the [MIT License](LICENSE). MIT permits copying, modification, redistribution, sublicensing, and commercial use, subject to preserving the required copyright and license notices. Public availability is not an additional usage restriction.

## 2. Aiko character artwork — distinct old and new terms

### Pickup and put-down source supplement

The approved `Aiko_Pick_Up_und_Hinlegen.zip` supplies eight 192x208 poses,
eight hand foregrounds and authoring metadata under `assets/aiko-pick-up/`.
`IMPORT_MANIFEST.json` records the archive and selected-file hashes. Only the
runtime source material is imported; large intermediate exports remain outside
the repository. These character derivatives follow the existing restricted
Aiko artwork terms, not the source-code MIT license.

### Current Aiko Anime assets — restricted reuse

Food/drink display copies under `aiko_pet/assets/items/display/` use the same
128-threshold binary alpha as character frames, preventing partial-alpha blends
with the Windows Magenta color key. Run
`python -m tools.prepare_item_display_assets` with Pillow to reproduce all 22
native 1x/2x copies. Original item PNGs, RGB colors, dimensions, pivots and picker
icons remain unchanged. `display/provenance.json` records input/output hashes;
the existing restricted item terms cover these technical display derivatives.
Cursor, ground and hand renderers share these manifest-referenced copies.

The runtime source export from `Aiko_Anime_8_Frames_Komplett.zip` is imported
under [assets/aiko-anime-8-frames/](assets/aiko-anime-8-frames/IMPORT_README.md).
Only the 134 original files needed to rebuild the selected character export
are tracked, byte-for-byte: catalogs, manifests, pose images and attack hand
layers. The other 813 archive members, including references, generation
attempts, prompts and QA material, are archived locally outside the repository.
Ignore rules also exclude them if the complete bundle is extracted here again.
According to the project creator, the artwork was generated with ChatGPT image
generation in an agent workflow.

The current desktop export has **120 character poses**: thirteen eight-frame
clips and sixteen cursor-gaze poses. Prepared full-width 192 × 208 copies live
in `aiko_pet/assets/frames/`, with timing/anchor metadata in
`aiko_pet/assets/animations.json` and hand foreground layers in
`aiko_pet/assets/hand-foreground/`. Attack assets remain reserved for future use; there is no attack trigger
or bundled magic graphic. One prepared sword is reserved as an asset for
future attack gameplay. The food-and-drink item catalog includes
**ten foods and one Energy Drink**: native transparent 1×/2× overlays and
64px picker icons under `aiko_pet/assets/items/`. Full-resolution source
artwork remains outside the repository. See
[Food system](docs/FOOD_SYSTEM.md) and
[item artwork terms](aiko_pet/assets/items/LICENSE.md).

The new artwork and associated asset data are **excluded from the MIT license**.
[The Aiko Anime asset terms](assets/aiko-anime-8-frames/LICENSE.md) permit
use in Aiko Desktop Pet; other reuse and redistribution, including distributed
forks carrying these assets, require Alex's prior, explicit, case-specific
consent. Application and preparation code remain MIT. Kenney graphics remain
CC0. Third-party rights and earlier licenses are not overridden.

`IMPORT_MANIFEST.json` in the source-export directory records the ZIP hash and
each included original file's path, byte size and SHA-256. The runtime provenance
manifest records prepared-file hashes, full image dimensions and the existing
128-threshold binary-alpha policy used for Windows color-key transparency.
Original imported artwork is not cropped or overwritten. Preparation uses
`python -m tools.prepare_character_assets`; Pillow is required only for that
build step, not for running the desktop app.

The eight 2x Idle slots now use a modular blink on the unchanged Idle reference.
Three existing eye phases are reused; all pixels outside the eye masks, body
and silhouette remain fixed. The source artwork is preserved 2x material,
not newly generated large originals. Native 1x files and common animation
timing remain unchanged. See the
[modular Idle export](docs/HD_CHARACTER_SPRITES.md#v3-modular-idle-blink-at-2x).

The eight 2x `waiting` slots contain the V3 question/request gesture: hands
rise, meet, hold briefly and lower back to Idle. Three large individual
arm-pose originals cover the distinct A/B/C poses; matching return phases
reuse the same artwork. Idle endpoints and existing eye modules are reused.
The originals are 1205x1305, 1205x1306 and 1205x1305, preserved outside Git.
Native 1x frames, timing and reaction triggers remain unchanged. See the
[question/request export](docs/HD_CHARACTER_SPRITES.md#v3-questionrequest-gesture-at-2x).

The eight 2x eating poses now use the V3 sequence, visually accepted by the
owner on 2026-10-23. Seven large generated individual originals cover eight
positions; the final holding pose reuses the first. Private originals and
prompts remain outside Git. Native 1x artwork remains unchanged. See the
[V3 eating export](docs/HD_CHARACTER_SPRITES.md#v3-eating-replacement-at-2x).

All sixteen 2x gaze directions now use the reviewed modular V3 sequence:
one shared Idle body, individual head cutouts, corrected heads 00/14/15,
the final crown/ahoge correction on 15 and subsequent joint head/neck
calibration against Idle. Native head sources are scaled proportionally;
jaw/neck placement is set separately, with the unchanged collar in front of
neck ends. All visible body pixels are preserved, and the body below y260 is
pixel-identical to Idle throughout; the foot center is x191 and sole baseline y388. The
head sources, masks and reviewed composition package remain outside Git.
`tools.character_gaze_modular_export` installs that package without rescaling;
the superseded full-figure exporter is preserved only in the private archive.
See the [V3 gaze export](docs/HD_CHARACTER_SPRITES.md#v3-gaze-replacement-at-2x).
The existing 1x catalogue and accepted V3 eating PNGs remain unchanged.

The prepared eating anchors move six source pixels downward relative to the
imported overlay hints, allowing native-size Onigiri to overlap the fingers
instead of ending above them. Preparation records this calibration in runtime
provenance and reproduces it; source manifests, PNGs, timing and item pivots
stay unchanged. See the [before/after grip composition](docs/media/world-eating-grip-comparison.png)
(source sprites composited at 2x for diagnosis, not a desktop screenshot).
Consumables remain above the character in eating, pickup, holding and put-down.
The latest practical feedback explicitly removes additional hand-mask occlusion
from this renderer. Approved hand masks remain preserved in the imported and
prepared asset catalogs. Native visual acceptance of the revision is pending.
The preparation check compares decoded RGBA pixels, dimensions and authoring
metadata across platforms: PNG compression can produce different file bytes.
Each build's provenance hashes must match its actual files; repeated preparation
with the same encoder must still be byte-identical.

All thirteen normal clips retain exactly **eight source PNGs** each. The
runtime can assign different hold times to each pose and replay selected
source poses without creating duplicate PNGs. Ordinary waving uses eight
steps; the separate greeting/farewell replay uses fourteen steps for two
friendly hand waves, using the same eight PNGs. Walking uses 190 ms per frame (a
1.52-second stride cycle), and its real desktop travel remains synchronized.
Waiting and review have longer neutral holds; sleep has a four-second
breathing cycle. Attack timing is unchanged for future gameplay. Each idle
blink finishes all eight frames and then rests on a neutral pose for a
short randomized 3–8-second gap. During that gap, a cached Tk-only image
warp sways Aiko's head and upper shoulders by at most one source pixel while
keeping her lower legs and feet perfectly stationary. The same subtle sway
is applied **relative to whichever of the sixteen look directions is currently
displayed** (including mouse-selected gaze), so it does not snap between
different head orientations. The technique produces no new source artwork,
does not use Pillow at runtime, and does not alter the real eight-frame
blinking sequence.

All pose tempos and optional replay orders are configured centrally in
[`aiko_pet/assets/animation_timing.json`](aiko_pet/assets/animation_timing.json)
and validated by the exporter and runtime loader. Historical durations
are retained as `source_duration_ms` for provenance. Artwork, anchors,
frame events and PNGs are unchanged.

OpenAI assigns its rights in generated output, if any, to the user to the extent
permitted by applicable law. This does not establish that every generated image
is unique or copyright-protected. The asset notice covers only licensable rights
Alex actually controls. See the [European Terms of Use, Content section](https://openai.com/de-DE/policies/eu-terms-of-use/)
and [service terms](https://openai.com/policies/service-terms/).

### Previous 73-frame Aiko sprite set — earlier MIT release

The previous sprite set was generated through a Codex-based OpenAI image
workflow and prepared as 128 × 208 frames. It was explicitly released under
MIT for the rights the creator controls. Replacing it with the new artwork
**does not change that earlier MIT release**. The old files and notices remain
available in Git history, for example the
[pre-replacement source commit](https://github.com/Lexoniarus/aiko-desktop-pet/tree/3125ce1527e14390d4ae59f03a1891fdf5789ca6).

## 3. Kenney game assets — CC0 1.0

The **Playing Cards Pack (1.0)** contributes exactly 52 standard card faces and
one back from `PNG/Cards (large)`, unmodified 64×64 PNG canvases under
`aiko_pet/assets/playing_cards/`. The bundled
[license](LICENSES/KENNEY_PLAYING_CARDS_CC0.txt) states CC0 and voluntary credit.
`provenance.json` records the source pack, bundle, source subdirectory and
SHA-256 for each selected original. No runtime Dropbox access is needed.
The large 64×64 canvases are the largest PNG variant in this pack. Blackjack
player cards use 2x integer scaling (128×128 canvases); the draw control layers
the same scaled back at runtime. Aiko's hand retains its own 1x/2x scale.
No additional asset export or modified source bitmap is distributed.

The project uses artwork from these Kenney asset packs:

- **Kenney Emote Pack (1.0):** pixel emotes under `aiko_pet/assets/emotes/`.
- **Kenney UI Pack: Sci-fi (2.0):** source and adapted panel/button graphics under `aiko_pet/assets/kenney_ui/`.
- **Kenney Boardgame Pack (1.0):** unmodified transparent yellow/red pieces for
  Vier gewinnt under `aiko_pet/assets/connect_four/`. The red source is
  orange-toned. Pack-relative source paths and SHA-256 hashes are recorded in
  [provenance.json](aiko_pet/assets/connect_four/provenance.json); the original
  pack [license](aiko_pet/assets/connect_four/LICENSE.txt) is included. The board
  and highlights are drawn with Tk; runtime needs no Dropbox access.

Mastermind reuses those red/yellow Boardgame pieces. Five additional unmodified
64×64 PNGs from the same CC0 pack (blue, green, purple, white and black) are
packaged under `aiko_pet/assets/mastermind/`, with their source paths and SHA-256
hashes in [provenance.json](aiko_pet/assets/mastermind/provenance.json) and the
supplied [license](aiko_pet/assets/mastermind/LICENSE.txt). License text whitespace
is normalized; its legal wording is unchanged. The board, feedback marks,
white-piece backing and cover labels are drawn in Tk. No new character artwork,
paid dependency or online asset fetch is involved.

The creator obtained the assets through a **paid Kenney Game Assets All-in-1 3.4.0 bundle**. The license files supplied with the packs identify the artwork as **Creative Commons Zero (CC0 1.0)**. Purchasing the bundle does not change those CC0 terms.

**Credit: Game assets by [Kenney](https://kenney.nl/).** Attribution is not required under the included CC0 license, but is voluntarily provided and appreciated.

See [LICENSES/KENNEY_CC0.md](LICENSES/KENNEY_CC0.md) and the [CC0 1.0 legal text](https://creativecommons.org/publicdomain/zero/1.0/).

The repository's MIT notice does **not** replace Kenney's CC0 designation.

### Twemoji hand icons — CC BY 4.0

The Rock–Paper–Scissors input buttons and Aiko's game reveal bubble use
three light-skin-tone Unicode emoji illustrations (U+270A U+1F3FB,
U+270B U+1F3FB, U+270C U+1F3FB) from [Twemoji](https://github.com/jdecked/twemoji).
The original SVG graphics were rasterized into optimized 72×72 PNGs to avoid
monochrome and incomplete glyph rendering in Tkinter. No additional runtime
renderer is required.

Artwork is licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
Attribution: **Twemoji, by Twitter and contributors**. The graphics are not
relicensed under the project's MIT license. Original graphics and license:
[Twemoji graphics license](https://github.com/jdecked/twemoji/blob/main/LICENSE-GRAPHICS).
See [LICENSES/TWEMOJI_CC_BY_4.md](LICENSES/TWEMOJI_CC_BY_4.md).

## 4. Optional fonts

The user-supplied `Kenney Mini.ttf` is **not distributed** with the project. Aiko uses a compatible font already installed on the user's computer when available, or falls back to Segoe UI. Third-party fonts remain subject to their own terms; the project's MIT license does not relicense a font installed separately.

## 5. Screenshots and previews

The active `vorschau/` directory contains **six README media files**: two real
UI stills and four GIFs covering reactions, ambient behavior, the minigame and
all 112 runtime sprite poses. Real UI screenshots and reaction GIFs were captured on Linux/Xvfb
from the running application by
[`tools/capture_current_gallery.py`](tools/capture_current_gallery.py) and
[`tools/capture_rock_paper_scissors_media.py`](tools/capture_rock_paper_scissors_media.py).
All application screenshots are freshly captured from the complete desktop,
then cropped to the bounding union of the real mapped Tk windows with a
24-pixel border; no content is rescaled. Animated UI previews use one fixed
union crop throughout their frames. This avoids previous clipped hover
controls, unnecessary black desktop space and moving GIF viewports.

The sprite-only GIF composites the current prepared PNG assets using their
checked-in frame timings and is identified separately from live UI footage.

The older v0.7–v0.13 screenshots, previous 73-frame animation GIF, and original
maintainer-provided Windows image remain accessible in Git history, including
[`main` at f41e8aa](https://github.com/Lexoniarus/aiko-desktop-pet/tree/f41e8aab58e6a93bd2675d0fd1f1adc3bed9b345/vorschau).
Unused Kenney bitmaps, the third-party design sample and historical food
exports are archived locally outside the repository. They are not runtime inputs.
The new captures retain the original sprite and UI asset licenses.
See the [current media gallery](docs/MEDIA_GALLERY.md).

All inputs needed to rebuild the prepared runtime frames are included in the
selected source export. Unused archive material is excluded from the public
repository. The older source spritesheet was not shipped with the earlier
73-frame release.

## 6. Language

### Approved game frontend artwork (2026-10-30)

`aiko_pet/assets/game_frontends/` contains selected project UI artwork from the
owner-approved local game references. `provenance.json` records source/export
hashes, sizes and the rasterization method. The retained SVGs are the editable
sources of the Fingerduell mat and Denkbrett frame. RPS hand icons in `assets/ui/`
are size exports of the approved illustrated hand signs, including the closed
fist; character originals and the external HTML preview bundles are not imported.
These project illustrations are separate from the Kenney card pack. All existing
Blackjack card faces, backs and their license are preserved.

The Connect Four frame/chips and Mastermind symbol gems/safe follow their
separate approved references. The safe's 33 prepared door phases are rasterized
from the accepted continuous source transform, not newly generated artwork.
For floating Windows color-keyed props only, `tools/prepare_game_prop_alpha.py`
prepares binary alpha while asserting unchanged RGB; `native-prop-alpha.json`
records pre/post hashes. Opaque board/control artwork retains antialiased alpha.

Documentation is maintained in **English**. UI strings, dialog entries, and runtime labels deliberately remain in **German** for the current game release.
