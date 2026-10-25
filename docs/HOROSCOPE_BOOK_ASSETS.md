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

The current owner direction is a physical, single-use book for one available
entry: the player places it, Aiko walks to it, picks it up, opens and reads from
it, closes it and puts it down; it may then dissipate. The next available entry
requires a newly placed book. This supersedes the earlier floating-book prop
direction and the briefly discussed reusable-book variant. The separate hat
gift idea is outside this asset delivery.

This delivery prepares book artwork and metadata. World registration, menu
availability, pickup/reading orchestration, consumption, persistence and a
fitted character reading pose belong to the subsequent feature implementation.
The book is deliberately not inserted into the food/weapon item catalogue.
No care, reward, wish, horoscope content or save behavior changes here.

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
