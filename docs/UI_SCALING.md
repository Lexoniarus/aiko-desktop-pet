# Central UI scaling from the approved 4K layout

All forms use one immutable application-wide transform. `UiScale` is created
with the root UI context, before any form is built, and reused by every skin,
window and embedded view. A form never chooses its own scale.

The reference grid is 3840 × 2160. The factor is
`min(1, screen_width / 3840, screen_height / 2160)` in Tk screen coordinates:

| Display | Common factor |
| --- | --- |
| 3840 × 2160 | 1 |
| 2560 × 1440 | 2/3 |
| 1920 × 1080 | 1/2 |
| 3440 × 1440 | 2/3 |

Tk already reports coordinates in the process's OS/DPI coordinate space. Fonts
use negative pixel sizes derived from the same 96-DPI design grid, avoiding a
second multiplication by `tk scaling`. The factor stays fixed for the UI
context's lifetime, including when forms move; it is not recalculated from a
window's content, viewport, monitor work area or current size.

`scaled_widgets.py` applies this transform when submitting native widget
options, padding, grid/place geometry and canvas drawing commands. Later text,
image and animation updates use the same transform. Images are reduced in
memory with Pillow's Lanczos filtering; packaged PNGs and private originals
are unchanged. Shared fonts/images are cached and released with the Tk root.
There is no live unscale/measure/rescale pass and no bitmap screenshot of a form.

All game forms, care/status/details, wishes/Moodlets, selectors, settings,
credits and speech/game-comment surfaces use this path. Native screen
coordinates remain screen coordinates:
canvas hit tests invert the transform; Aiko's gaze and game-flight targets
apply it when converting authored points to the desktop. The character's
existing 1X/2X preference and World-item rendering remain separate from forms.

The old `ScrollRegion`, nested Mastermind viewports, per-screen compact layouts,
palette reduction and viewport-fitting timers are removed. `ContentRegion`
is a plain, naturally sized frame, without scrollbars, wheel hooks, clipping or
focus-driven repositioning. All ten Mastermind rows stay visible. Moodlets wrap
into six columns; embedded menus and details take their natural content height.
Care rows declare both their design width and height, so disabling geometry
propagation cannot collapse the action column. Native tests check complete
button bounds through the ancestor chain and real clicks at 4K/Full HD.
Game forms keep their natural content height as explanations/results appear;
placement clamping does not change the shared scale or crop content.
Quiz answer layout may still depend on answer length, never on screen width.

Tests cover the shared resolution policy, native initial mapping, filtered
images, stable canvas animation updates, pointer/drop coordinates, control
admission and complete content. Earlier tests requiring scrolling or a compact
variant have been removed or replaced. Run the local full suite and static
gates before committing; remote CI requires a separately authorized push.
