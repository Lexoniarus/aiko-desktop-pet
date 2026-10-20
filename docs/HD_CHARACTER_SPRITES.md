# True-resolution 2x Aiko sprites

This is a **2x-only image-quality improvement** on `feature/social-optimization`.
The application continues to use its unchanged **192 × 208** PNGs at 1x,
including all event, hand-grip and interaction coordinates and existing timing.
At 2x it loads **384 × 416**, independently rendered, correctly registered
PNGs from `aiko_pet/assets/frames_2x/`, not a 2x nearest-neighbor enlargement.

## Sources and reproducibility

120 frames: twelve eight-pose clips, eight pickup poses, and 16 gaze poses.
The export uses the owner-approved **Aiko Anime** Sailor-skin archives:
`Aiko_Anime_8_Frames_Komplett.zip` and `Aiko_Pick_Up_und_Hinlegen.zip`.
Original archive media do not belong to the public source repository;
only the reduced 2x **runtime assets** and their provenance are shipped.
They retain the project's restricted Aiko artwork terms, **not MIT**.

Every 2x output is listed by path, source image/crop and SHA-256 in
`aiko_pet/assets/frames_2x/manifest.json`. Regular clips preserve the original
1x sprite's alpha-128 silhouette bounds and baseline. Gaze poses use connected
figures from the native `decoded/look-row-9.png` and
`decoded/look-row-10-before-registration.png` sources. Their hair can cross
equal-width tile boundaries, so rectangular eight-way division is unsuitable.
Each extracted figure retains its original RGB and edge alpha, with neighboring
figures excluded.

The gaze exporter uses one base proportional scale per source row, calibrated
against the median shoe span of its 1x references. Each pose is translated to
its doubled 1x foot center (with the small lateral tuning below) and ground
baseline. Width and height are not
independently stretched to match the head silhouette. Integer image dimensions
introduce less than 0.4% aspect-ratio rounding; horizontal foot-anchor error is
at most half a 2x pixel against the tuned target, and vertical error is zero
for all 16 corrected poses.

The left gaze poses (`look/09` through `look/15`) additionally receive a small
proportional size adjustment before resizing from the native source. Left and
up-left use +2.3%; a smoothstep blend reduces this toward the unchanged down
pose (`look/08`): +0.36%, +1.15% and +1.94% for `09`, `10` and `11`.
The up-to-up-left height change is now one 2x pixel (309 to 310), previously
seven (309 to 302); neighboring left poses differ by at most three pixels.
This compensates for the inherited size discontinuity without equalizing
every head tilt. Both axes share the same factor, with integer rounding only;
foot centers and the ground baseline are registered after the adjustment.
The manifest records the adjustment and effective scale for each affected pose.
The rightward, up and down poses retain their previous PNG bytes.

Two inherited lateral foot jumps receive integer translations only: `look/10`
and `look/15` move one 2x pixel left; `look/11` and `look/14` move one pixel
right. Each targeted transition (`10` to `11`, `14` to `15`) now moves the
visible foot center by 0.5 instead of 2.5 pixels. Neighbor transitions,
including `15` to `00`, remain at most 1.5 pixels apart over the full loop.
The translation is applied after coordinate rounding and preserves every
RGBA pixel, silhouette size, proportional scale and foot baseline. The
manifest records the original reference anchor and horizontal adjustment
alongside the tuned target and its rounding error.

Color resampling uses Lanczos, followed by alpha thresholding at 128 for native
Windows transparent-window compatibility. The canvas stays 384 × 416;
application geometry and all 1x assets remain unchanged. Rebuilding an existing
export preserves encoded PNG bytes when the RGBA pixels match, so unrelated
assets are retained exactly.

To reproduce on a machine where both approved owner archives are available:

```console
python scripts/build_character_hd_2x.py \
  --source-archive "C:/Aiko/Aiko_Anime_8_Frames_Komplett.zip" \
  --pickup-archive "C:/Aiko/Aiko_Pick_Up_und_Hinlegen.zip" \
  --output-dir aiko_pet/assets/frames_2x
```

Pillow is used **only at export time**, not at application runtime.
The exported audit CSV identifies every source, a thresholded silhouette
comparison to its native counterpart and any aspect-ratio corrections.
The `review/01` and `eat/07` HD single files in the archived source are
truncated; the intact high-resolution contact grids from those same archives
supply both corresponding original poses. None of the shipped 2x frames is
merely a magnified 1x substitute.

## Runtime behavior and verification

- The native 1x frames remain canonical, unchanged and supported.
- `CharacterSpriteCache` inspects the **complete manifest** once. It rejects
  incomplete or invalid HD exports instead of silently mixing sprite sets.
- When the HD manifest is present, only 2x frames actually displayed are
  loaded into Tk, cached and released during shutdown. Older installs without
  HD assets retain the original `PhotoImage.zoom(2)` fallback.
- Image dimensions, alpha, completeness, SHA-256 and true-vs-zoom difference
  have dedicated tests. The current 1x sprite hashes are verified separately.
- Gaze regressions cover cross-cell hair, near-transparent source bridges,
  proportional row scaling, tuned size and lateral transitions, pixel-exact
  translations and the shipped sprites' measured foot anchors.
  Sleep regressions cover the stationary bed, pillow and character, all eight
  blanket phases, the loop join, mirrored breathing phases and native timing.
- The 2026-10-20 gaze correction was reproduced into an empty export folder:
  all 120 outputs matched the shipped RGBA pixels. All 16 gaze PNGs changed;
  all 120 native PNGs and the other 104 HD PNGs remained byte-identical.
  Native Windows Tk loaded all 16 gaze directions at both scales and released
  their cache successfully. This loading check does not replace the practical
  animation and overlay acceptance below.
  The isolated Linux/Xvfb suite passed 1,390 tests (eight skipped); Ruff, strict
  Mypy and repository-wide Pyright also passed.
- The gameplay engine, frame events, head micro-sway, food/weapon overlays and
  1x/2x item windows still use their existing contracts. Their visual alignment
  should be checked at 2x on **native Windows** before considering the feature
  fully accepted.

### Visual acceptance still required on native Windows

Verify idle/blinking, both walks, jumping, greeting/waving, waiting, review,
sleep, petting, eating, attack reserve, the full pickup/put-down sequence, all
16 cursor-gaze directions, overlay hand anchors and sprite feet at 1x/2x.
Look direction 022.5° (`look/01`) now uses the same proportional registration
as its neighbors. Its old rectangular crop included part of another figure,
which compressed Aiko horizontally and shifted her foot anchor right. The
original and 1x pose are valid: no regeneration is needed. The corrected 2x
silhouette IoU is 0.9644 against 1x, with a 0.5-pixel horizontal anchor error
and no vertical error. Compare its transition against the adjacent gaze frames.
Do **not** claim this practical acceptance solely from green CI.

### Approved stationary sleep cycle at 2x

Owner approval on **2026-10-20** replaces the earlier temporary hold on HD
`sleep/02` and `sleep/05`. Inspection found that the old HD export used whole
generated intermediates, while the pixel version already composited a fixed
character. The HD originals also differed in bed geometry between poses.
No new image generation was needed for the approved correction.

`tools/character_sleep_export.py` now builds the approved smoothed preview
directly from two complete archive originals. `sleep/frames-native/01.png`
supplies the stationary bed, pillow, head, body and hands; the blue blanket
from `sleep/frames-native/04.png` supplies its raised phase. Both are registered
against their existing 1x reference poses before composition. The blanket joins
ease into the stationary shoulder and bed. Eight cosine samples interpolate
the contour and existing texture, preserving the approved preview's RGBA pixels.
All pixels outside the blanket envelope, and the character and wooden bed
within it, stay identical to the rest frame. No whole-character scaling occurs.

The measured maximum contour movements over `00→01→…→07→00` are
**2, 6, 6, 3, 3, 6, 6, 2 HD pixels**. The former `02→03` jump is reduced from
17 to six pixels; the loop join moves at most two. The eight discrete poses
retain their existing durations (4,000 ms total), order and `(96, 195)` native
anchor. Mirrored phases `01/07`, `02/06` and `03/05` match exactly.
`sleep/00` retains its PNG bytes; the other seven HD sleep PNGs are replaced.
All 120 1x PNGs and every other HD PNG remain byte-identical to the pre-change
checkout. The 1x sleep artwork is intentionally unchanged; its older appearance
does not indicate a pending HD regeneration requirement.

The exporter records both anchor sources, their registration measurements and
each breathing factor in the manifest. Rebuilding requires the owner archives,
not local preview files. All eight shipped outputs match the approved smoothed
preview exactly and can be reproduced into an empty output directory.
The shipped cycle also completed two full passes plus a loop restart through
the native Windows Tk sprite cache, with all eight HD frames loaded and the
cache released afterward. Dedicated sleep, gaze and HD/cache tests pass, as do
Ruff, strict Mypy and Pyright. These checks cover this asset change; the broader
interactive desktop acceptance listed above remains separate.

The truncated `review/01` and `eat/07` source PNGs described above have intact
original-sheet recovery sources. Recovery resolves their file-corruption
issue; the separate visual-cohesion backlog for eating is recorded below.

### Eating source restored after comparison

On **2026-10-20**, the owner requested restoration of the previous eight HD
eating PNGs after reviewing Idle, pickup, holding and eating together. The
alternative Library strip was a different drawing version: its smaller head
and longer body changed the proportions at the clip boundaries. Global width
and height adjustments were rejected and remain external previews only.

The previous archive-derived eating PNGs and manifest records are restored
exactly. The exporter again uses the two archives above; it does not require
the alternative Library image. Its temporary HD-only food-anchor overrides
are removed with that source change. Original food anchors, animation events,
timing and pickup's held final pose retain their existing behavior.

This restoration adds no scale or position corrections. The larger head and
shorter body of the eating drawing remain visible relative to idle and pickup,
as they do in the original 1x artwork. The full chain must therefore be judged
as a sequence; matching feet or outer bounds alone does not establish visual
continuity. All 1x assets and the other HD clips remain unchanged.

Native Windows Tk playback verifies all eight pickup and eight eating phases,
the held final pickup image, direct handover using that same image, attachment
and bite events, and the final idle pose with the food hidden. The measured
shoe baseline is 388 throughout. Existing lateral shoe-center variation and
the head-width changes (idle 178, final pickup 180, eating endpoints 200 and
208 HD pixels) are retained rather than corrected in this restoration. All
120 outputs reproduce from the original archives into an empty export folder.

### Open artwork task: regenerate a cohesive eating sequence

**Status: regeneration required; current artwork accepted for continued use.**
On **2026-10-20**, the owner accepted the restored eating sequence with its
visible drawing differences and requested that the remaining artwork work be
recorded. The affected set is `eat/00` through `eat/07`; review and regenerate
the inconsistent poses together as one animation sequence.

The compact impression is primarily inherited from the generated artwork:
larger head, shorter torso and very short legs relative to idle and pickup.
The archived generation prompt explicitly requests these proportions. Direct
source checks reproduce all eight shipped HD frames and match all eight native
1x poses after their established alpha conversion. The HD exporter changes
width relative to height by only -0.13% to -1.84%; it does not vertically
compress the character. Global width/height stretching did not resolve the
drawing differences and is not an accepted correction.

For the future generation pass, use the canonical idle pose and pickup's
final held pose as shared character/proportion references. Check the complete
`idle -> pick_up -> hold -> eat -> idle` chain, including direct handover,
instead of accepting isolated frames on matching height or shoe baseline.
Keep head/body/leg proportions, costume, foot placement and food-grip contact
consistent through the eight eating poses and their entry/exit transitions.
Retain the existing event/timing and overlay contracts when integrating the
replacement art.

This is an open visual-quality task, not a runtime or file-corruption defect.
The restored assets remain in use without further size adjustments. No image
generation or 1x/2x asset changes are part of this documentation decision.

### Forward gaze and empty-hand offer preview

The sixteen direction images are complemented by the existing neutral
`idle/00` pose when the cursor is within 17 native pixels of the eye anchor
(34 at 2x). Entering this region clears the previous direction and holds a
forward gaze instead of keeping a sideways look or choosing an ambient glance.
Normal gaze timeout and sleep, game, action and movement priorities still apply.

For an identified, wanted cursor item that currently satisfies the established
handover/reach checks, the passive renderer uses the final `pick_up/07` pose
with empty hands only when the displayed item center is within 24 native pixels
of that frame's authored food/hand anchor (48 at 2x). Holding an item directly
in front of her face retains the forward gaze; other positions retain directional
gaze. Cursor-item gaze follows the displayed center, accounting for the item's
pivot and size, rather than its bottom edge. Moving between face and hands
changes the pose without releasing the item.

This preview emits no pickup events, transfers no custody and
awards no nutrition; release still performs the existing handover. The preview
disappears when eligibility is lost. It cannot show a stale food overlay from
a previous action. Both scales reuse their existing PNGs without asset changes.
