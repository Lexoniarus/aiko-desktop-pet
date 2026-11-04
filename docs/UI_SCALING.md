# Central UI scaling from the approved 4K layout

All forms share one root-local `UiScale`. A view never chooses its own factor.
Aiko's 1X/2X character size and World-item rendering stay independent.

## Automatic size and the user's preference

The automatic factor is `min(1, physical_width / 3840, physical_height / 2160)`.
Windows DPI-unaware processes receive virtualized Tk screen dimensions. Only in
that case, `display_metrics.virtualization_factor()` restores physical dimensions
using Windows' reported scale factor. It reads awareness without changing it.
The native adapter uses Microsoft's
[GetProcessDpiAwareness](https://learn.microsoft.com/en-us/windows/win32/api/shellscalingapi/nf-shellscalingapi-getprocessdpiawareness)
and [GetScaleFactorForMonitor](https://learn.microsoft.com/en-us/windows/win32/api/shellscalingapi/nf-shellscalingapi-getscalefactorformonitor)
for the primary monitor, matching Tk's screen-dimension scope.
For example, 4K at Windows 150% reports 2560 × 1440 to Tk; its automatic UI factor
is **1**, rather than the previous incorrect 2/3. A DPI-aware process is not
multiplied again. Other platforms retain their reported screen dimensions.

Settings → Darstellung separates **Aiko-Größe** (1X/2X) from **UI-Größe**
(75%, 100%, 125%, 150%, 175%, 200%). UI size multiplies the automatic factor.
It applies immediately to every existing view and to subsequently opened views.
`DesktopDisplaySettings.ui_scale_percent` owns the preference; the existing
settings snapshot/command path projects and changes it. SQLite migration 5 adds
it with default 100 while preserving existing settings and checkpoint revisions.
Legacy JSON import supplies the same default. Migration uses the existing
transactional migration/backup mechanism; no external live-save edits are needed.

## Live updates and native input

`scaled_widgets.py` retains authored widget options and layout distances.
Changing UI size updates those values, shared pixel fonts and cached images in
place. Hidden pages stay hidden. Canvas coordinates and line widths change by
the common ratio; pointer hit tests continue to invert the current transform.
Image buttons receive styles for the new factor, retaining selected/disabled
state, focus and commands. Games, rounds, windows, speech timers and application
models are not destroyed or recreated. Window positions are clamped after layout
settles; the character root is not resized.

There is no temporary unscale/measure/rescale pass or screenshot of a form.
Pillow filters images from their original runtime source data on every size
change, avoiding cumulative resizing. Fonts use negative pixel sizes from the
96-DPI design grid, avoiding a second `tk scaling` multiplier. Caches are released
with their root.

## Menus and speech

Snack, games and conversation choices use three rows, then additional columns.
The selector remains in the toolbar, with status/context preserved. Back stays
at the start of the interaction column so collapsing a wide selector leaves
the pointer inside the toolbar rather than triggering an outside-hover hide.
Growing a selector keeps the current toolbar side/position, clamping at screen
edges instead of switching to Aiko's opposite side underneath a click. Following
Aiko's movement and explicitly saved toolbar positions retain their existing
owners. Admission and selector cancellation semantics do not change.

Conversation text and game comments use the same `PanelSurface` bubble artwork,
colors and tail. Emoji graphics already contain a bubble and tail and therefore
receive no extra shell. RPS side-hand panels use the same prepared surface.
Binary source alpha masks stay binary after image filtering: Windows color-key
transparency cannot remove partially transparent pixels blended with magenta.
This prevents new cutout fragments without editing packaged PNGs or character
assets. Originally fractional source alpha is preserved.

The old `ScrollRegion`, nested Mastermind viewports, compact board variants and
per-view scale fitting remain removed. `ContentRegion` is naturally sized.
The owner now permits sensible scrolling where needed; the current finite
selector lists fit a multi-column arrangement without restoring old viewports.
Mastermind retains all ten rows; Moodlets and wishes retain their wrapped layout.

Native tests cover repeated live changes, hidden-page and selected-button
preservation, actual clicks, canvas hit testing during an existing game, DPI
virtualization, binary image transparency, selector geometry and save migration.
Use `python tools/local_test_suite.py` for local automated checks: native Tk
creation is blocked and native-only cases are reported as skips. Full GUI
coverage runs on GitHub's isolated Linux/Xvfb and Windows runners. Do not open
automated test windows on the user's primary display. A necessary local visible
check belongs on the designated secondary display. Keep headless, CI and visual
acceptance evidence distinct.
