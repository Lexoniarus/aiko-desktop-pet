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
`aiko_pet/assets/frames_2x/manifest.json`. The build preserves the original
1x sprite's alpha-128 silhouette bounds and baseline, uses Lanczos-resampled
color data from the higher-resolution source, then thresholds alpha at 128 for
native Windows transparent-window compatibility. The rendering canvas stays
384 × 416; no application geometry is changed.

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
- The gameplay engine, frame events, head micro-sway, food/weapon overlays and
  1x/2x item windows still use their existing contracts. Their visual alignment
  should be checked at 2x on **native Windows** before considering the feature
  fully accepted.

### Visual acceptance still required on native Windows

Verify idle/blinking, both walks, jumping, greeting/waving, waiting, review,
sleep, petting, eating, attack reserve, the full pickup/put-down sequence, all
16 cursor-gaze directions, overlay hand anchors and sprite feet at 1x/2x.
Look direction 022.5° (`look/01`) is a source-outline outlier (silhouette IoU
0.678 versus the old 1x), though it is higher-resolution and holds the same
canvas bounds; compare its real transition against the adjacent gaze frames.
Do **not** claim this practical acceptance solely from green CI.
