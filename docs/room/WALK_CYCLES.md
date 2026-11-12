# Room walk cycles

The two depth walk cycles come from the approved private preview
`2026-11-11-raum-naehe-hochformat-vorschau`. The room export takes frames
00 through 07 from `frontalgang/zyklus` for `toward` and from
`rueckgang/zyklus` for `away`. The full-resolution sources are in the
local asset archive.

The export scales every frame by `312/1158` onto the 384 × 416 pixel runtime
canvas. The preview anchor `(608, 1240)` maps to `(190, 388)`, matching
the profile clips' logical anchor at `(95, 194)`. Alpha values of 1 were
removed before resizing. The authored shoe poses and their distances from
the common ground line are part of the animation.

Python sends the step length and duration in each motion snapshot. The
renderer uses both to interpolate travel and select frames from the
distance walked. A profile cycle covers one step and a depth cycle covers
two steps. The default duration is 620 ms per step.

Pathfinding uses arcs at a constant distance from the camera and straight
segments along a bearing. Both segments are checked against furniture
footprints. The renderer interpolates the same segments and changes the
walk cycle at the actual turn.

The bearing determines the horizontal screen position. Ground contact,
scale and ground occlusion all use the same distance from the camera.
Routes continue across wall boundaries. At equal floor depth, an object
remains visible in front of Aiko.

When the user calls a visible Aiko, her target lies on her current bearing
just outside the camera clearance, if the floor is reachable. Calls take
priority over autonomous object interactions at all friendship levels.
Aiko waits facing the user when she arrives.

The camera enters close framing only for a call that has started. Face,
shoulders and room for the speech bubble stay visible, and the lower
edge can crop the lower body. Cancelling the call, opening a game or
leaving close range ends the close framing.
