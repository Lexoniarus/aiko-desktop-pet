# Readable World objects

Readable items use the existing World/cursor/custody flow, with READ capability
instead of EAT/DRINK. Selection does not award nutrition or complete a wish.
`ObjectInteractionCoordinator` owns the held reading phase and legal put-down;
a reader declines with false or reports completion through its episode callback.
Unexpected reader exceptions unwind the physical phase and remain visible to
the caller. The desktop reader is responsible for expected availability errors.

`WorldState.can_place_definition` permits at most one live instance of each
readable definition. This includes cursor-held, falling/bouncing, resting and
pet-held states, before a daily reading is admitted. Terminal instances do not
block future stock; relocation retains the existing ID. Foods remain finite
portions that may have multiple instances.

The shared ItemCatalog has readables with four approved book states, unchanged
source PNGs and explicit native-scale metadata. World and cursor use the same
closed image and support pivot; held-state registration is separate. WorldView
prefers a native larger source before integer zoom. The current book has World
zoom 2 and the owner's +12px 1x middle held offset.

READ pose selection uses the existing animation composition. Passive body poses
have no held-item overlay and are owned by AnimatedPet; World must not resolve
them through the canonical held-action catalogue. The World heartbeat reschedules
in finally while surfacing errors, so a presentation failure cannot disable drag.

Local daily selection, one-time care credit and persistence of a frozen reading
belong to the horoscope coordinator, not to these generic object contracts.
The retired API is replaced in the following integration slice.

Verification for this slice: 76 staged-tree tests, including readable uniqueness,
physical failure/put-down, body-pose drag regression, food, World and SQLite
round trips. Tests use disposable saves, never the user's normal save.
