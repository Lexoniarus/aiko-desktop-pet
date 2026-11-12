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

The room prepares the ordered walking frames before drawing the scene.
At a boundary between buffered updates, the next interval supplies the
pose at zero progress. If an update is late, Aiko holds the last confirmed
position and the last drawn walking frame while the simulation still
reports walking. The next update resumes distance-based playback. A stop
can finish the buffered travel, and a new action takes precedence.

The bearing determines the horizontal screen position. Ground contact,
scale and ground occlusion all use the same distance from the camera.
Routes continue across wall boundaries. At equal floor depth, an object
remains visible in front of Aiko.

When the user calls a visible Aiko, she approaches along her current
bearing. If she is offscreen, the target bearing is the camera's current
direction. The ordinary route reaches radius 131, followed by a checked
radial leg to radius 70. If that leg is obstructed, Aiko stops at the
reachable transition point. Calls take priority over autonomous object
interactions at all friendship levels. Aiko waits facing the user at
the destination.

The camera keeps its normal scale and horizon. On a confirmed approach
inside radius 100 it can pan horizontally once to center Aiko. Her
physical distance supplies the close view. The foreground character
projection limits the frontal silhouette to the viewport width and
places the lower body below the room viewport at arrival. A later trip
starts along the same ray back to the ordinary floor. A saved near
position is restored if that exit remains clear. Food placement uses
the ordinary clearance.
