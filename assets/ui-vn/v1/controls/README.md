# Button, status-bar and panel source artwork

Prepared 2026-10-20 with the built-in Imagegen tool for
[the approved VN design](../../../../docs/UI_VN_DESIGN.md).
This is documentation and asset preparation only. Nothing is connected to
the running application.

## What each file is for

| Selected source | Purpose | Later composition |
| --- | --- | --- |
| [button_normal.png](button_normal.png) | Resting clickable control | Add the separately rendered icon and label |
| [button_hover.png](button_hover.png) | Pointer hover on an enabled control | Same label/icon; slightly clearer edge and surface |
| [button_pressed.png](button_pressed.png) | Temporary pressed feedback | Inset depth cues; do not confuse with a persistent toggle |
| [button_disabled.png](button_disabled.png) | Unavailable action | Muted appearance; actual admission remains application-owned |
| [button_active.png](button_active.png) | Persistent selection, e.g. Offen halten | Stronger rose edge and inner accent; separate pin/label; not temporary pressed feedback |
| [panel_surface.png](panel_surface.png) | Shared passive container for details, embedded selectors, wishes and tooltips | Separate text/icons/separators; adjust padding and local shadow for tooltip use |
| [status_track.png](status_track.png) | Empty passive readout trough | Background below the dynamic value fill |
| [status_frame_overlay.png](status_frame_overlay.png) | Thin rounded frame with transparent interior | Above the dynamic fill; never obscure it with an opaque surface |

There is deliberately no precolored full progress-bar image. The amount and
the current fill color must remain dynamic. This distinguishes these passive
readouts from the rose clickable buttons.

## Button usage

The blank rose surfaces serve Snack, Spielen, Unterhalten, Streicheln, Schlafen,
Zurück, Offen halten and the detail disclosure, plus later matching utility
controls where appropriate. Keep each actual action's existing availability
and label semantics. Only submenu navigation gets a chevron.

Text, icon, chevron and keyboard focus are separate layers; do not bake them
into PNGs. Keyboard focus can coexist with hover or press and needs an
independent visible outline. Disabled artwork alone must not decide whether
an action is admitted.

For different widths, retain end/corner caps and border thickness while
stretching the quiet middle region. The generated sources are wide source
materials; they do not prescribe a long banner-shaped runtime button.
Do not distort the whole image to fit each label. Before integration, align
the state images to a common crop/canvas, choose shared caps and content
insets, and review normal compact button sizes.

## Status-bar usage and layer order

1. Empty recessed track.
2. Dynamic rounded/clipped fill.
3. Transparent frame overlay, in front of that fill.
4. Separate label/value text where needed.

Only fill width changes with value; frame width stays fixed. At zero, no colored
fill remains; at maximum, the full inner slot is filled. Clip the fill inside
the actual rounded inner slot rather than drawing over the rim.

As the value falls, **the entire filled part changes smoothly from green through
yellow and orange to red**. Do not use a stationary horizontal rainbow where
low values still show a green left edge. Optional subtle highlight/shading must
preserve the perceived value color.

Provisional presentation colors used by the preview:

| Normalized value | Color |
| --- | --- |
| 100 | Green `#8EBD9C` |
| 50 | Yellow `#E0CD86` |
| 25 | Orange `#E5B080` |
| 0 | Red `#D98897`; no visible fill at exactly zero |

Interpolate between these anchors. They are a starting point for visual tuning,
not new gameplay/balance thresholds. Retain readable numeric/text information;
color must not be the sole cue.

This treatment applies to needs and numeric overall mood. **Friendship uses a
fixed blue fill (`#94B5CF`)**, because low friendship progress is an ordinary
relationship stage rather than a critical care warning. These colors do not
replace the separate qualitative emotion or Moodlet meaning.

Preserve full antialiased/partial alpha. The 128-threshold character-sprite
transparency policy is not a control-image export instruction.

## Panels, tooltips and UI-rendered effects

Reuse `panel_surface.png` for passive content grouping and smaller tooltips.
Its almost-white rose interior is opaque, its exterior transparent, and its
powder-blue border distinguishes it from the raised rose action surfaces.
Preserve corners/border thickness with a later nine-slice export. Content insets,
separators and any tooltip pointer are separate UI elements. Tooltip placement
must account for screen edges and keyboard access. It does not introduce a
separate native submenu window. The main title bar stays pure white.

The active button follows authoritative persistent selection, such as keep-open.
Use its stronger edge together with the separate pin/label state cue. Pressed
remains transient; disabled controls do not react as enabled controls. Active
hover/press combinations need later export review; do not replace a selected
surface with the unselected normal artwork during pointer movement.

The following effects are **later UI rendering**, not missing PNGs:

- Independent keyboard focus: visible blue-gray outline, provisionally 2 px
  with a small gap, including on an active control.
- Scrollbars: near-white rose track, visible blue-gray thumb and clearer
  hover/drag feedback; wheel, keyboard and dragging remain available.
- Restrained transitions: provisional 80–140 ms hover fade, immediate press
  feedback and 120–180 ms soft content reveal where supported. No input delay,
  geometry jump, bounce or continuous glow. Respect reduced motion; use instant
  state changes when fading is unsupported. No sprite-frame animation or global
  dimming overlay is required for the agreed menu flows.

These values are visual tuning candidates. Native Windows/Tk support and actual
focus, scrolling and transition behavior must be reviewed during integration.

## Files and evidence

- The composition preview in the [external reference bundle](../../../../docs/UI_PREVIEW_HANDOFF.md)
  shows five states with separately rendered
  example labels, shared panels/tooltips, focus, green-to-red examples and fixed-blue friendship.
- [Machine-readable usage contract](usage_contract.json): purpose, states,
  layer order, color role, exception and export constraints.
- [Exact prompts and attempts](generation_prompts.json): built-in generation.
- [Source provenance](provenance.json): selected source hashes, dimensions,
  transparency, visible bounds and retained-file verification.

Eight source PNGs are selected and versioned. Four exploratory drafts are kept
only in the external reference bundle under `assets/ui-vn/v1/controls/drafts/`,
not in this checkout or for implementation: an excessive glowing
button, an overlay with a rough pale cutout edge and two panel attempts with excessive
exterior glow. The later selected sources
supersede those attempts.

Generated originals are unchanged. They may contain faint low-alpha fringe;
the later export pass must normalize optical bounds and inspect edge quality
at actual size. Source preparation and a standalone composition illustration
do not establish pixel-aligned runtime exports or native Windows/Tk acceptance.

The selected panel is deliberately flat, without the broad baked exterior halo
of its excluded attempts. Its generated proportions differ from the prompt;
they do not prescribe tooltip or detail-container proportions. Split corners,
edges and the quiet center during export rather than stretching the full PNG.
The active state shares the other button canvases, while optical bounds still
need alignment. All generation attempts are retained in the prompt manifest;
[the surface extension record](generation_record_surfaces.json) identifies this pass.
