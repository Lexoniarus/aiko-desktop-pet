# Horoscope book artwork — V1

The owner approved the enchanted violet book design on 2026-10-25 after
requesting a more mystical purple palette and additional ornamentation in
Aiko's character drawing style. This V1 supplies four transparent book states,
1x/2x derivatives, Windows color-key display copies and menu icons.

## Selected appearance

Plum/violet covers, amethyst/lavender spine, cream pages, gold crescent around
an amethyst star, double gold border and ornamented outer corners. Half-open
and reading views share the rear-cover corner protectors and spine diamond.
The drawing retains fine anime contours and controlled shading. Full-resolution
native originals and rejected alternatives remain in the private authoring run;
the package contains prepared derivatives rather than large character sources.

## Asset package

Package: [horoscope_book/v1](../aiko_pet/assets/horoscope_book/v1/README.md).

| State | Use | 1x canvas | 1x book-local pivot |
| --- | --- | --- | --- |
| `closed_world` | Closed book placed on the desktop | 64x48 | 32,40 |
| `carry_closed` | Closed upright book for carrying | 96x80 | 48,64 |
| `half_open` | Intermediate opening/closing state | 96x80 | 48,64 |
| `open_reading` | Open book, reader behind it, exterior visible | 96x80 | 48,64 |

Every state has RGBA and binary-alpha display versions at 1x and 2x. The 2x
canvas and pivot are exactly double. Menu icons are supplied at 32 and 64 px.
The [manifest](../aiko_pet/assets/horoscope_book/v1/manifest.json) is the
machine-readable inventory; [provenance](../aiko_pet/assets/horoscope_book/v1/provenance.json)
records native hashes, optical crops, measured landmarks, preparation and
export hashes. [Prompt history](../aiko_pet/assets/horoscope_book/v1/prompts.json)
records the exact built-in Imagegen prompts and selected native filenames.

Carried states use a common physical size reference: a 42 px outer front-cover
edge at 1x, measured from the selected native drawing. This keeps the expected
opening-width change instead of forcing every bounding box to the same size.
The lower spine is registered to a common book-local grip pivot. Native manual
landmarks are approximate; subpixel placement is rounded by less than 0.5 px.
These pivots prepare attachment metadata; fitting the actual Aiko hand/reading
pose remains part of scene integration. Four state drawings are not a complete
frame-by-frame page-turn or character animation.

`rgba/` preserves the prepared smooth edges. `display/` copies keep the same
RGB pixels and convert alpha below 128 to 0 and alpha at/above 128 to 255, in
line with the existing item display preparation for Windows Magenta color key.
Full native originals stay unmodified. Icons retain normal RGBA transparency.

## Agreed object lifecycle

The latest owner decision is one physical book per day's entry. After the
first full reading and actual put-down, it remains for a fixed hour. Manual
handover replays the same frozen entry from the start, without another care
credit or extending the hour. It dissipates at that absolute deadline in any
custody; the next day needs a newly placed book. Interruption of the first
reading alone does not start the hour. This supersedes immediate single-use
retirement as well as the original floating-book/hat gate concept.

Runtime registration now uses the shared ItemCatalog readables declaration,
World READ capability and existing item overlay. The artwork/provenance itself
is unchanged; no generated character pose or new page-turn animation is claimed.

The original asset delivery prepared artwork and metadata. The subsequent local
feature now integrates World registration, menu availability, pickup/reading,
put-down and persistence. The book is registered separately under readables,
without food/weapon effects. No character artwork changed during integration.

## Authoring and validation

Private authoring run: `2026-10-25-horoskop-buch-v1-violett` under the shared
local `asset-generierung/` directory. It retains the frozen Aiko references,
native outputs, exact prompts, `prepare_v1.py`, `export-config.json`, selection
history and independent review. The preparer performs optical cropping,
proportional Lanczos resizing, pivot placement and alpha preparation; it does
not recolor, repaint or reshape book artwork. Changes to artwork use Imagegen.

The prior navy concepts remain preserved. Asset preparation grants no new
license or replacement rights; the existing [asset-origin and terms record](../ASSETS.md)
continues to apply.

Validation passed: all 18 PNGs load with native Tk; native/export hashes match;
all eight RGBA state derivatives reconstruct pixel-for-pixel from the recorded
sources and landmarks; display copies preserve RGB and apply exactly the
alpha-128 threshold. Borders are clear and pivots/sizes double correctly.
Independent review found no material asset blocker. The three held visible
heights are 54/58/56 px at 1x, retaining limited illustrated perspective
variation. The world view is smaller; this is not acceptance of a seamless
pickup animation or fitted hand contact. Ten repository asset/link checks
passed. The [validation summary](../aiko_pet/assets/horoscope_book/v1/validation.json)
identifies the retained private evidence.

### Runtime registration correction

Closed World/cursor display uses `world_registration.zoom = 2` (native 2x
source preferred), so a placed book is no longer a tiny prop. World and cursor
share its size and bottom support pivot. The held registration retains the
owner's middle +12px adjustment at 1x for pickup, catching and reading. The
four prepared PNG states and private originals are unchanged. Selection now
uses the same press/drag/release gesture as food, including existing-instance
relocation and handover.

### Closed carry alignment correction (2026-10-26)

The closed carry drawing's visible center lies to the right of its book-local
grip pivot. `held_registration.state_offsets_1x.carry_closed = [-13.5, 0]`
adds a horizontal attachment correction for this state only. The shared +12 px
vertical attachment and half-open/open-reading positions remain unchanged.
The loader validates optional per-state offsets; FoodOverlay applies them at
native 1x/2x scale. The prepared PNGs and book-local pivots are unchanged.
