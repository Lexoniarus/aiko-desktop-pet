# Asset provenance, licensing, and acknowledgments

This repository includes original project content, AI-generated character artwork, and third-party Kenney game assets. Their origins are documented separately.

## 1. Project source code — MIT

Unless a file identifies a different license, the project's own source code is distributed under the [MIT License](LICENSE). MIT permits copying, modification, redistribution, sublicensing, and commercial use, subject to preserving the required copyright and license notices. Public availability is not an additional usage restriction.

## 2. Aiko character artwork — distinct old and new terms

### Current Aiko Anime assets — restricted reuse

The runtime source export from `Aiko_Anime_8_Frames_Komplett.zip` is imported
under [assets/aiko-anime-8-frames/](assets/aiko-anime-8-frames/IMPORT_README.md).
Only the 134 original files needed to rebuild the selected character export
are tracked, byte-for-byte: catalogs, manifests, pose images and attack hand
layers. The other 813 archive members, including references, generation
attempts, prompts and QA material, remain local and are ignored by Git.
According to the project creator, the artwork was generated with ChatGPT image
generation in an agent workflow.

The current desktop export has **112 character poses**: twelve eight-frame
clips and sixteen cursor-gaze poses. Prepared full-width 192 × 208 copies live
in `aiko_pet/assets/frames/`, with timing/anchor metadata in
`aiko_pet/assets/animations.json` and hand foreground layers in
`aiko_pet/assets/hand-foreground/`. Attack assets remain reserved for future use; there is no attack trigger
or bundled weapon or magic graphic. The five **food overlay/menu PNGs**
are now included in `aiko_pet/assets/food/`, prepared from the creator's
separately retained transparent high-resolution food artwork at 98% of the
intended hand-object size. See [Food system](docs/FOOD_SYSTEM.md).

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
`python tools/prepare_character_assets.py`; Pillow is required only for that
build step, not for running the desktop app.

All twelve normal clips retain exactly **eight source PNGs** each. The
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

The project uses artwork from these Kenney asset packs:

- **Kenney Emote Pack (1.0):** pixel emotes under `aiko_pet/assets/emotes/`.
- **Kenney UI Pack: Sci-fi (2.0):** source and adapted panel/button graphics under `aiko_pet/assets/kenney_ui/`.

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

The active `vorschau/` directory now contains **only captures of the current
Aiko Anime/Tk UI and minigame**, plus a GIF preview of all 112 current runtime
sprite poses. Real UI screenshots and reaction GIFs are captured on Linux/Xvfb
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
The third-party Kenney design sample is preserved separately under
[`docs/references/`](docs/references/Kenney_SciFi_Sample_Referenz.png).
The new captures retain the original sprite and UI asset licenses.
See the [current media gallery](docs/MEDIA_GALLERY.md).

All inputs needed to rebuild the prepared runtime frames are included in the
selected source export. Unused archive material is excluded from the public
repository. The older source spritesheet was not shipped with the earlier
73-frame release.

## 6. Language

Documentation is maintained in **English**. UI strings, dialog entries, and runtime labels deliberately remain in **German** for the current game release.
