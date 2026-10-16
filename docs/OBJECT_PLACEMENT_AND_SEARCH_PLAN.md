# Recognized offers, movable supplies and visible object search

Agreed product behavior: 16 October 2026.
Code baseline: `e7ebe7e` on `feature/world-foundation`.
Status: implementation authorized; S0 records the agreed plan, T0 is next.
Rechecked against the same code baseline after the user's own-physics decision.

This is the complete follow-up plan for recognized cursor offers, moving resting
portions, impact-dependent settling hops and subjective search/reconciliation.
It follows
the [current architecture](ARCHITECTURE.md),
[World contracts](WORLD_OBJECT_CONTRACTS.md),
[persistent memory delivery](OBJECT_MEMORY_IMPLEMENTATION_PLAN.md) and
[World/dialogue cleanup review](WORLD_DIALOGUE_CLEANUP_REVIEW.md).
Current implementation reports remain historical evidence. Statements below
describe the agreed target behavior, not features already delivered.

## Scope and preserved behavior

- World remains the only owner of concrete portions, custody and positions.
  Moving a portion never creates another portion or changes its World ID.
- Aiko learns through perception and confirmed own actions. She does not learn
  hidden moves, removals, counts or identities by inspecting World records.
- Hunger, energy, food repetition and canonical consumption effects keep their
  existing owners and thresholds. Cursor willingness is not a permanent order
  to seek an item autonomously. In particular, handover willingness at energy
  65 does not lower the autonomous drink threshold of 60.
- `auto_walk` continues to control random walking only. Ordinary goal movement
  still requires actual arrival and reach, including revalidation at grasp.
- Release inside the handover area remains the only cursor-to-pet acquisition.
  Ground collection remains autonomous even if the user previously offered or
  moved that portion. Only actual accepted handover earns human care rewards.
- Pickup transfers custody at source frame 4. Consumption effects begin only
  after pickup completion and successful current-use validation. The full
  consumption clip remains visible and commits its effects once.
- Explicit interruptions retain safe holding and animated put-down before the
  queued user action. Item layering and existing character artwork are preserved.
- No extra mind tick, general physics engine, external service, asset generation
  or new runtime dependency is introduced.
- Tests and practical starters use separate temporary saves. Do not touch the
  normal save or merge the draft PR.

## Findings in the existing structure

| Existing owner / API | Present behavior | Required consequence |
| --- | --- | --- |
| `CursorItemGesture.observe_offer()` | Remembers preview feedback locally; recognized offers do not complete memory assessment | Record genuine assessment through a behavior/application boundary, not the renderer |
| `ObjectKnowledge.examined` | Gates intent, retrieval shortcut and incidental object gaze | Use one assessment fact consistently across those consumers |
| `DesktopWorldRuntime._offer_wanted()` | Combines need and temporary availability in one boolean | Separate willingness from the ability to accept now |
| `offer_on_release()` | Always enters `inspect`, even for known portions | Add a readable handover route without repeated inquiry |
| `ObjectAwareness` / `ObjectPerception` | Forward stable World instance tokens into perception and memory | Prevent technical identity from proving subjective identity after an unseen move |
| `ObjectMemory` / `ObjectGoal.token` | One record/goal directly identifies one World instance | Separate remembered records, current sightings and execution references |
| `CursorItemGesture.begin()` / `cancel()` | Creates new portions; cancellation removes them | Add acquisition of an existing resting portion and source-aware cancellation |
| `WorldState` | Has no `RESTING -> USER_HELD` operation | Add a revision-checked explicit user acquisition |
| `WorldView` / `make_object_window_passive()` | Object windows are click-through on Windows | Add selective resting-object input without changing the gesture owner |
| `advance_falls()` / `land()` | Vertical fall immediately becomes resting at the same x | Add explicit non-resting settling motion and account for contact time |
| `WorldObjectSnapshot.fall_speed` / `_commit()` | A downward fall scalar is retained only in `FALLING`, otherwise cleared | Introduce one immutable signed motion value and explicit transition/reset rules |
| `WorldPosition` / `WorldSurface.contains()` | Reject negative height and anchors beyond the supported surface | Resolve contact/boundary events before constructing validated positions |
| `remove()` / `change_footprint()` | Explicit allowed-state lists do not yet include bouncing | Update all lifecycle paths together when enabling `BOUNCING` |
| `TaskbarTrack` / `_capture_contact()` | Special edge grip and special ground-to-hand handling | Remove only after reachable placement is guaranteed |
| `_frame()` / `toggle_scale()` | Footprints refresh in a later callback; scale changes save immediately | Synchronize geometry before movement, acquisition and save snapshots |
| `encode_world()` | Normalizes transient portions to resting recovery records | Reuse this policy for hops; do not persist a running trajectory |
| `ObjectCustody._change()` / `restore_snapshot()` | Recover immutable World values after a failed joint operation | All runtime motion state must be captured and validated with the World checkpoint |
| Runtime search timer / `missing()` | Short local wait followed by forgetting and missing feedback | Introduce visible bounded search and distinguish a missing location from lost knowledge |

## Recognized and assessed offers

Known type, completed assessment, current willingness and current availability
are distinct concepts. An assessment does not mean that an item is wanted
forever, physically inspected or currently visible.

Use one domain-owned `assessed` fact instead of adding a cursor-only parallel
flag next to `examined`. Completed held inquiry and a genuinely recognized,
evaluated cursor offer can establish it. Mere proximity, a stale remembered
identity, a queued bubble or an old feedback receipt cannot establish it.
The preview requires current attentive perceptual evidence. Temporary inability
to accept must not masquerade as a need-based refusal.

Intention selection, retrieval eligibility and incidental gaze use the same
assessment semantics. A known assessed unwanted supply releases incidental
object gaze to normal cursor and ambient behavior. New unknown supplies retain
the full inquiry route, independently of current appetite.

The coordinator has a separate `handover` phase: accept on valid release, hold
the safe pose, show readable handover acknowledgement, then revalidate and use
the normal consumption path. It does not reuse `inspect` merely to delay an
already assessed item. Cancelled or stale feedback cannot advance a new phase.
No nutrition is granted by preview or acceptance alone.

Own `deferred` disposition remains a confirmed fact about Aiko deliberately
putting something down. Cursor refusal is assessment, not an invented own
placement. Existing saved-supply recall text must not claim she put an offered
item aside herself.

## Subjective identity, places and quantities

### Separate technical identity from recognition

World ID, catalog identity and subjective memory identity have different roles:

- World ID identifies the concrete portion for safe custody and consumption.
- Catalog identity identifies the recognized type, such as Onigiri or Energy
  Drink. Matching catalog identity does not establish the same physical portion.
- A subjective record identifies Aiko's remembered experience. It must not be
  keyed by an assumed permanent visual recognition of the World ID.

`ObjectAwareness` owns the application mapping between current perceptual tracks
and concrete execution references. Technical handles may be used to execute a
validated action; they are not recognition evidence. Intentions use subjective
records/places. Before acquisition, the application resolves a currently
observed eligible portion and validates its actual World state and revision.
No currently observed binding means no invisible remote acquisition.

Followed movement can preserve a perceptual track and its assessment. A new
observation after an unobserved relocation must not inherit continuity solely
because its World ID is unchanged. Define continuous observation, lost tracking
and plausible spatial continuity explicitly in S1. A teleport between distant
observations is not proof of followed movement. After restart, there are no
live bindings or retained sensory tracks; a familiar type at a remembered place
can support a local reunion hypothesis, not fresh global certainty.

### Remember facts and distinguish uncertain associations

The existing memory owner is extended with typed records for:

- learned type, assessment and confirmed own disposition;
- last observed place and relative active age;
- currently supported finds and unconfirmed remembered places;
- confirmed missing places and bounded search/retry status;
- possible same-type associations between a new find and an older record.

Relations and counts have one owner in `ObjectMemory`; use a small pure matching
policy if reconciliation warrants its own module. Do not create a second stock
inventory, independent count cache or generic confidence/AI subsystem. Derive
summaries from records and one-to-one associations. Unconfirmed older places
remain uncertain; they are not counted as additional confirmed current stock.

Rules for reconciliation:

1. Following a portion being moved updates its place without creating stock.
2. A disconnected same-type discovery is initially a new find with possible
   links to older unconfirmed records. It is neither automatically an extra
   portion nor automatically the old portion.
3. Repeated sightings on one continuous track never increase the count.
4. Distinct simultaneous observations establish distinct available portions.
   Only such evidence or equivalent observed history establishes a firm count.
5. A new find can explain at most one missing remembered portion. Multiple
   indistinguishable candidates retain ambiguity rather than an invented identity.
6. Absence at a checked place invalidates that place's availability. It does not
   erase a valid new find or automatically discard learned type/assessment.
7. A compatible find plus a confirmed missing old place can reconcile a presumed
   relocation. Treat it as a hypothesis, with suitable dialogue, not proof from
   the hidden World ID. Do not propagate special assessed/deferred experience
   across an unresolved alternative involving multiple portions.
8. Resolved old places cannot continuously generate fresh searches. Consuming
   an associated find updates that stock relation once, without consuming or
   forgetting other independently supported portions of the same type.
9. Reconciliation works in both event orders: missing then found, or found then
   missing. An adequate earlier find can satisfy the need without a pointless
   visit to the older place just to balance an inventory.
10. Confirmed consumption/absence resolves relevant records; unknown sightings
    retain the existing ten-active-minute expiry. Known facts do not acquire an
    arbitrary new time-to-live. Retire resolved history and obsolete links so
    that the model does not accumulate permanent duplicate records.

Do not announce exact missing quantities unless the remembered count and observed
evidence justify them. Aiko can say that a place is empty or that she found a
drink without claiming certainty about whether it is the same drink.

## Visible bounded search

Search is a coordinator phase, not another mind tick or a physics callback.
It has a correlated search/interaction identity, a time budget, normal bounded
movement, gaze cues and identified feedback completion/cancellation.

Replace the runtime's `_search_at` search budget when this phase is introduced;
do not keep two independent search timers. The current blocked/no-goal branch
clears walking goals and the current gaze assignment follows ordinary goals.
Both must respect an active search phase's explicit movement/gaze request.
Use the existing `WalkDriver` for short search steps, reporting actual bounded
arrival; no second movement controller is added. Perception remains active in
the existing cognition tick while a search owns presentation and movement.

| Situation | Visible behavior and memory result |
| --- | --- |
| Need and suitable currently observed stock | Prefer useful stock; no obligatory audit of an older uncertain place |
| Need and only a remembered place | Recall, approach the actual place, then inspect locally |
| Attentive arrival establishes an empty place | Announce uncertainty and enter visible search |
| Suitable find during search | Stop the old search, reconcile supported evidence, acknowledge the find and choose inquiry or retrieval |
| Suitable find was observed earlier | Reuse it when still eligible; do not restart the same failed search |
| Search exhausts its budget | Record the checked absence, give one outcome, release gaze and resume normal behavior |
| User interruption or changed need | Cancel the search and movement safely; cancellation alone proves no absence |

A search needs a visible sequence: pause at the expected place, look left/right
and, where useful, take short steps inside the ordinary track. Reuse the sixteen
gaze directions and existing walking/idle assets where they express this clearly.
Audit the asset manifest before promising a dedicated new character clip. Any
missing visual resource is an explicit design dependency, not permission to
generate or silently substitute artwork.

Keep the existing `search_seconds` and retry budget as the starting policy.
Readable speech uses the existing reaction sequence timing. Budget expiry stops
active searching; finishing a bounded readable outcome must not reset the search
or repeat the scan. New observations, bubbles and new render callbacks cannot
restart the same search budget. Alternative useful stock ends the old attempt.
Repeated checks of one resolved place are suppressed until meaningful new
evidence, rather than merely being repeated forever at the retry interval.

German cues belong to `data/dialogues.de.json`, for example:

- `Hier hatte ich doch noch einen Drink ...`
- `Ah, da steht einer!`
- `Vielleicht hast du jemand umgestellt.`
- `Ich finde ihn einfach nicht.`

Exact wording follows the available evidence and quantity. `missing()` may no
longer unconditionally forget a complete World-keyed memory before this search
and reconciliation have finished.

## Moving resting portions

One `CursorItemGesture` handles both creating a portion from the chooser and
acquiring an existing resting portion. Give the two entry operations distinct
names; subsequent movement, offer, release and cancellation share the same path.
Do not use utility-window `WindowDrag` to move World portions.

- Add explicit revision-checked `RESTING -> USER_HELD` custody. Preserve ID,
  enforce the single cursor slot and reject moving/pet-held/terminal portions.
- The native click carries the instance reference; it does not mutate World.
- Resolve interruption through the existing runtime/coordinator boundary. Check
  the pressed portion again after any delayed interruption. A released button or
  stale reference must not begin a delayed phantom gesture or steal a portion
  that Aiko has already grasped.
- The gesture owns only source metadata: chooser versus existing portion and
  the original resting position. It does not own a second mutable object copy.
- Escape, failed capture, lost capture or release outside the supported primary
  monitor removes a new chooser portion as before. For an existing portion,
  return it to its source position projected onto current valid ground bounds.
  A failed attempt must not lose or duplicate the portion.
- Successful release can still hand over inside the normal acceptance zone or
  fall elsewhere. The accepted handover, not previous ownership history,
  determines consumption origin.
- User acquisition/return does not call Aiko's own-action memory methods in
  `ObjectCustody`. Perception alone updates her knowledge of user movement.
- Starting, completing and cancelling the gesture leave coherent save points.
  Application shutdown uses existing transient recovery rather than resuming
  an input grab in the next process.

`WorldView` and `desktop/object_windows.py` expose resting portions to selective
left-button input. Moving/held windows remain click-through. Transparent pixels
must not become invisible hit rectangles. Preserve topmost and window stacking
rules, avoid unintended focus theft and do not synthesize pet contact/care from
object clicks. Include Tk global bindings, menu dismissal and capture fallback
in the Windows integration review; no global mouse hook is required.

## Decision: a small owned physics policy

The user selected the small own-physics solution after the concrete Pymunk/code
comparison. Do not add Pymunk, CFFI, a native solver or a generic physics-engine
adapter/factory for this scope. Runtime requirements remain standard library
plus Tk; installer and CI dependency setup need no physics-specific change.

The deciding boundary is one horizontal ground surface with independent upright
portions. Gravity, analytic contact times and damped rebounds are limited math;
reachable placement, source-aware custody and safe completion remain application
rules with either implementation. A solver would additionally require mutable
body mappings, fixed-step synchronization and checkpoint reconciliation without
removing those rules. This is an architecture/work-scope assessment, not a
benchmark or a claim that physics engines cannot integrate with Tk.

Choose `world/motion.py` as a small pure calculation module, with immutable
inputs/results. `WorldState` remains its caller and sole committer. Do not grow
the numerical code inside the desktop adapter or add a second mutable motion
dictionary. Reconsider the dependency decision only if scope later includes
item-to-item collision, rotation, stacking or multiple interacting surfaces.

## Reachable placement and impact-dependent settling hops

The latest user clarification replaces the earlier fixed three-hop sequence.
Fall height and impact speed determine rebound height, travel and subsequent
hop count. Reaching valid ground remains mandatory regardless of motion energy.

Keep Aiko's normal full-window walking bounds. Derive the valid support-anchor
interval from the union of ordinary reachable positions, intersected with the
item footprint fitting on the World surface. Respect rounding and actual grasp
validation. Derive it from track geometry, character width, reach and item size;
do not add hand-tuned left/right exceptions.

The desktop adapter converts screen coordinates to World coordinates once and
provides typed placement bounds. World applies the rule to every route that can
produce a resting portion: drop completion, scripted placement/movement, own
put-down, user cancellation, geometry updates and restart recovery. Scripted
APIs explicitly validate or project their inputs; they cannot silently leave
an unreachable `RESTING` instance. World imports no Tk or pet needs.

The states are `USER_HELD -> FALLING -> BOUNCING -> RESTING`, with `BOUNCING`
omitted when no visible rebound or inward settling is needed. The shared motion
policy applies to all drops, not just those outside normal reach:

1. Use the existing gravitational acceleration and actual release height/speed
   to determine speed at first ground contact. Higher comparable drops produce
   more energetic rebounds; do not select a preset sequence by frame count.
2. Resolve an inward path and valid final support anchor from impact energy,
   distance to reachable ground and the available surface. Energy can increase
   travel only within the geometric limits; no arc can leave the supported screen.
3. Derive rebound speed from impact speed and a restitution factor below one.
   Rebound height follows from that speed and gravity. Dampen horizontal speed
   as well, so successive hops lose height and travel until they settle.
4. Allow as many visible hops as the remaining energy warrants. Low drops can
   settle immediately or after a small hop; high drops can make more/larger hops.
   Valid-ground drops may rebound too, but must remain inside reachable bounds.
   Once an outside drop enters the reachable interval, later hops stay inside it.
5. End the sequence when rebound speed/height falls below a visible threshold,
   or when a finite safety budget is reached. Apply the remaining bounded inward
   settling displacement before becoming `RESTING`; exhausted energy outside
   reach must never leave an unreachable resting portion.

This is damped drop motion with an explicit placement guarantee, not an entirely
unconstrained physical simulation. For a low-energy drop outside normal reach,
the remaining inward correction is a short continuous settling movement; do not
invent a large vertical rebound or visibly teleport to satisfy the guarantee.
An upper hop/time budget prevents numerical tails, but is not the normal fixed
hop count. The release gesture does not gain a new throwing mechanic in scope.

### Motion values and event-based advancement

Replace the fall-only scalar with one immutable motion value owned by the World
snapshot. Define horizontal velocity as signed and vertical velocity as positive
upward in the existing positive-height coordinate system. Positions still require
nonnegative height; velocity validation requires finite values, not nonnegative
values. Do not keep independently writable `fall_speed` and vertical velocity.
S1 names the exact fields for velocity, final anchor, flight/ground-completion
mode and cumulative settling progress/budget; S9 implements them.

Chooser/user release starts from rest, preserving the current no-throw gesture.
Pointer speed is not silently introduced as a launch impulse. Rebound speed is
derived from actual simulated ground-impact speed. Resolve the initial inward
travel response explicitly: a vertical drop does not by itself generate lateral
motion on flat ground. Keep this directed response and low-energy completion
distinct from gravitational acceleration and dissipative rebound calculations.

Advance analytically to the next ground contact or horizontal boundary, then
continue with the remaining supplied elapsed time. Handle zero-height initial
release, the top of a flight, exact contact and a zero-time contact without a
non-progressing loop. Do not integrate below the floor and then feed that value
to `WorldPosition`, or hide overshoot by a frame-dependent position clamp.
Bound transition processing and small-bounce tails with visible thresholds and
the cumulative budget. The terminal ground-completion mode is also timed and
bounded; it cannot restart a bounce budget or grant pickup before completion.

`WorldState._commit()` must preserve or clear motion according to the explicit
transition. `RESTING`, `USER_HELD`, `PET_HELD` and terminal states have no stale
flight. Include `BOUNCING` in applicable removal/footprint/geometry paths while
keeping both pet and user collection restricted to `RESTING`. A free-flight
impact with rebound is not an intermediate resting state or collectible event.
Replace the production `advance_falls()` entry with one complete motion advance
operation and update its callers/tests directly; no permanent forwarding alias
or independent fall/bounce loop remains. Audit the public `land()` transition
so it cannot bypass the resting-position invariant.

Pure calculations validate their inputs and return immutable updated values.
The World prepares updates before committing an advance, so an invalid input
cannot advance some portions and then fail on another. Revisions track actual
World changes; a zero interval or an already settled portion is a no-op.
Partitioned elapsed intervals must produce equivalent physical results within
numerical tolerance, including across contact. Revision counts need not match
between different numbers of advances.

### Clock, units, configuration and geometry

Reuse `_frame()`'s supplied active elapsed time and the existing 33 ms rendering
schedule. Its Windows active-uptime source already excludes suspend; preserve
the existing fallback-clock policy. No new wall clock, fixed-step accumulator,
physics thread or timer is required. Cognition remains in its existing tick.
Large supplied intervals are handled by analytic events and finite completion,
not thousands of nominal render steps.

Gravity, restitution, horizontal damping, travel response, visible stopping
thresholds and a finite settling budget belong in validated `data/balance.json`,
scaled consistently at 1x/2x. Reuse the existing gravity key rather than adding a
second acceleration owner. Require finite positive gravity and thresholds,
restitution/damping strictly between zero and one, and bounded travel/budgets.
Height and flight time are derived from velocity and gravity, not independent
authored arc timings that contradict the fall. Numeric starting values are
calibrated and recorded during S9 rather than claimed to be already approved.

World coordinates remain logical desktop-distance units, not sprite-local
coordinates: height in distance units, velocity in units/second, gravity in
units/second squared, and restitution/damping dimensionless. Keep the existing
`fall_gravity` meaning; selecting 2x does not double World positions or silently
double gravity/velocity. Scale the item footprint and normal reach through
their existing owners. Declare any visual-size-relative threshold explicitly
before applying scale to it; geometry changes do not add motion energy.

Build immutable motion parameters from the existing `BALANCE` catalogue at the
desktop/application boundary and pass them to World math, extending today's
injected gravity pattern. `world/` imports neither the pet balance singleton nor
the JSON loader. Add keys and cross-field checks to `pet/balance_contract.py`
and `pet/balance.py` along with the values in JSON; their current generic
positive-value check alone does not enforce damping below one or integer budgets.

Surface/scale changes recompute footprints and placement bounds coherently
before stepping motion, acquiring an object or capturing a save. Rebase a moving
trajectory from its current valid pose toward the updated target without a new
endless fresh-energy restart. A resting portion made unreachable by a live
geometry change becomes settling rather than remaining collectible outside reach.
If there is no valid placement because the character/item cannot fit, reject the
operation safely; do not fabricate reach. Resolve this through the same geometry
policy, not another edge grip.

Own animated put-down ends at a valid foot-area anchor without gratuitous hops.
User cancellation returns to a valid source anchor without replaying drop arcs.
No special migration for pre-existing out-of-range objects is required by the
user's development-state clarification.

Remove `GroundApproach.edge_grip`, its exceptional grasp branch and the matching
`_capture_contact()` branch only after all normal placement routes obey this
contract. Retain ordinary actual arrival, normal ground-to-hand blending and
grasp-event reach revalidation.

## Ownership and module boundaries

| Owner | Target responsibility |
| --- | --- |
| `world/contracts.py`, `world/state.py` | Concrete portions, user/pet custody, placement bounds and immutable motion snapshots |
| `world/motion.py` | Small pure analytic fall/contact/rebound/completion calculations; no independently owned mutable state |
| `pet/mind/object_perception.py` | Current sensory evidence and explicit continuity/lost-track rules |
| `pet/mind/object_knowledge.py`, `object_memory.py` | Subjective records, assessment, places, own dispositions and stock associations |
| Pure mind matching policy, if extracted | Deterministic one-to-one reconciliation; no access to World or Tk |
| `pet/mind/object_intentions.py` | Need-driven choice from subjective stock and places, with stable goals and bounded retries |
| `application/object_awareness.py` | Objective-to-subjective boundary and ephemeral execution-reference bindings |
| `application/object_interaction.py`, `object_feedback.py` | Handover/search phases, receipts, visible ordering, interrupts and event deduplication |
| `application/object_custody.py` | Joint confirmed pet acquisition/placement and subjective own-action facts |
| `application/object_consumption.py` | Joint once-only World/Pet/memory consumption with explicit origin |
| `desktop/geometry.py`, `world_runtime.py` | Host geometry conversion, synchronized updates and existing owner wiring |
| `desktop/cursor_item_gesture.py` | One source-aware gesture, native capture and pointer/release/cancel handling |
| `ui/world_view.py`, `desktop/object_windows.py` | Passive rendering and selective native input, without decisions or stock state |
| JSON catalogues | Authored German cues and validated tuning, not transition algorithms |
| Existing codecs and `WorldSessionSnapshot` | One atomic durable snapshot, schema validation and safe recovery |

Avoid mechanical class-per-method extraction. New modules are justified only by
a distinct responsibility and a meaningful typed interface. Update public
callers directly; do not restore removed forwarding APIs or parallel state.

## Persistence and compatibility

The outer save and durable World section remain version 1. Continue saving only
nonterminal portions at valid resting recovery anchors. A running hop recovers
at its resolved valid ground target; no input capture, search animation,
trajectory clock or active action is resumed. Recovery does not update memory
as if Aiko witnessed it. Pet, World and memory are still written atomically.

Distinguish exact runtime checkpoints from durable recovery. `snapshot()` and
`restore_snapshot()` retain/validate complete immutable motion and placement
values so a failed `ObjectCustody` or consumption transaction restores the same
motion state. `WorldSessionSnapshot` carries a coherent World/knowledge pair
after geometry synchronization. The JSON World codec resolves a moving portion's
valid final anchor rather than merely clamping its current x to surface edges,
as `encode_world()` currently does. Supply that anchor through typed World values;
the codec must not import desktop geometry or infer Aiko's wishes. No velocity,
trajectory or new physics-library state is added to durable World v1.

The later subjective-identity/count requirement supersedes the earlier idea
that merely renaming `examined` could leave all memory serialization unchanged.
Plan a separately versioned `object_memory` v2 for subjective record IDs,
assessment, remembered places, resolved absence and supported associations.
Persist facts needed to avoid repeated old-place searches after restart; do not
persist current visibility, transient World bindings or process-local timestamps.
Use relative active ages. Closed time produces no new search or observations.

Design and test a v1 reader/conversion before writing v2. Existing `examined`
maps to assessment; old identities, locations and own dispositions remain learned
history. An old World token must not become a live visual identity certificate.
Validate association references and cardinality, reject malformed structures
with the existing backup policy and retain protection against attaching old
knowledge to a replacement World. Technical save provenance is permitted for
consistency checks, never as evidence for subjective recognition or quantity.

## Small delivery steps

Each row is one reviewable commit; split further when needed for an independently
green boundary. Keep the feature branch and existing draft PR. Do not merge.
S0 records this plan only. The user has authorized T0 followed by S1-S15 in
small pushed commits. T0 is the first implementation step, before S1. Existing
S identifiers remain stable so contracts and physics references do not move.

| Step | Result and principal owners | Required evidence | Status / commit |
| --- | --- | --- | --- |
| S0 | Record this complete plan, current-code findings and links | Documentation consistency, valid local links, no code edits | `092906b`; local links and diff checks passed |
| T0 | Inventory existing behavior coverage and consolidate only tests already redundant on the current baseline | Coverage-to-contract map, unchanged production behavior, retained unique timing/custody cases, targeted gates | `874db92`; inventory below, 11 targeted tests passed |
| S1 | Fix typed contracts for assessment, subjective records/tracks, matching, search outcomes, execution bindings and v2 conversion | Scenario table for continuous/unseen moves, multiple identical portions, both discovery orders and restart | `2c00657`; contracts and scenario table recorded |
| S2 | Unify assessment in memory, intentions and gaze; record recognized cursor assessment through a domain/application operation | Known refusal does not trigger repeated inquiry/gaze; temporary unavailability is separate | `0eeab14`; 66 object + 13 World GUI tests, Ruff/Mypy/Pyright green |
| S3 | Add readable handover shortcut using the existing consumption and interruption machinery | No repeated inspect/recognize/decide; no instant use, stale-receipt progression or extra care origin | `1ddc11c`; 10 retrieval + 13 component + 1 real-time handover test; Ruff/Mypy/Pyright green |
| S4 | Introduce and test subjective record values and ephemeral perceptual bindings before switching durable runtime callers | Changing only technical IDs cannot change recognition; unseen relocation is not followed movement | `7bfd7c7`; spatial tracker prepared, 3 targeted tests and Ruff/Mypy/Pyright green; runtime switches in S6 |
| S5 | Add and test stock/place reconciliation for the memory owner, ready for the v2 integration | Repeated sightings, one/two/many identical portions, ambiguous matching and order symmetry | `69e3da9`; 4 stock + 4 codec tests and Ruff/Mypy/Pyright green; production integration S6 |
| S6 | Add memory v2 reader/writer and v1 conversion, then switch runtime callers and paired snapshots coherently | Learned facts/absence survive restart; no live bindings or invented identity; malformed references backed up | S6a `678c6d2`; S6b/S6c `75e1b2c`: runtime bindings and explicit custody references, 80 object + 13 GUI + 6 real-time flow tests, Ruff/Mypy/Pyright green; all three CI jobs green for S6b. S6a Windows setup timed out twice; failed job rerun requested, no feature assertion failed. |
| S7 | Add visible bounded search, useful-alternative selection and German feedback | Found-before-missing and missing-before-found stop appropriately; no repeated resolved-place loops; cancel proves no absence | This revision: coordinator-owned active-time search, existing gaze/walk presentation and negative-place evidence. 82 object + 13 GUI tests and Ruff/Mypy/Pyright green. |
| S8 | Introduce shared placement bounds and synchronized scale/surface/snapshot handling | Fast geometry matrix, 1x/2x, both sides, footprint and invalid narrow surface | Planned |
| S9 | Deliver the selected own-physics policy through S9a-S9d below | Low/high falls, variable hops, time partition equivalence, finite termination, reachable rest, non-collectibility and restart | Planned |
| S10 | Add existing-portion user acquisition and source-aware cancellation to the shared gesture | Same ID, exclusive custody, stale revision, failed/lost capture and delayed/released input | Planned |
| S11 | Add selective Windows resting-object input and connect the gesture | Visible-pixel targeting, no focus/contact regression, normal release/capture behavior | Planned |
| S12 | Connect every production placement route and remove the special edge grip | Normal arrival/grasp still checked at frame 4; own put-down and gesture return remain reachable | Planned |
| S13 | Finish residual cleanup after the behavior-specific replacements already delivered in their owning stages | No orphan fixtures/helpers or redundant flow combinations; unique grasp/clip/interruption and save coverage retained | Planned |
| S14 | Update architecture, contracts, save docs, changelog and isolated smoke scenarios | Documentation matches delivered APIs and actual verification; practical checklist below | Planned |
| S15 | Run final regression and hand over a fully pushed practical-test build | Full gates/CI, real Windows evidence and explicit test readiness; PR remains unmerged | Planned |

S4/S5 prepare the typed model and policies without exposing a half-converted
durable runtime. S6 switches production consumers only when conversion, writing
and restoration are available together. Split preparation further if necessary;
do not add a permanent old/new dual-memory mode. Temporary scaffolding must not
present technical identity as cognitive evidence in a supposedly complete step.
S2/S3's assessment tests must still pass after the switch. S8/S9 precede S12,
so removing the fallback cannot leave a production placement path broken.

S6a introduces the validated v2 codec, allocation provenance, subjective-ID
allocation and memory operations before activating tracked production sightings.
S6b switches the application bindings, custody/consumption references and desktop
callers together. S6c verifies native restoration and the new observation routes.
These are small independently checked commits within S6, not a permanent dual
runtime. The v1 reader remains only at the persistence boundary.

S9 is split into these small commits. S9a/S9b prepare calculations before the
full new lifecycle is enabled; do not ship bouncing with incompatible recovery
or leave a second production motion path active.

| Substep | Independently reviewable result | Completion evidence |
| --- | --- | --- |
| S9a | Extract pure fall/contact calculations while retaining the existing production fall behavior | Existing falling behavior plus zero/exact-contact and time-partition cases |
| S9b | Add immutable motion/parameter values and pure damped rebound/inward-completion policy | Low/high drops, decreasing rebound energy, variable hop counts, finite large-delta completion and bound checks |
| S9c | Switch World lifecycle, runtime advance, snapshot restoration and durable target recovery together | All state-list callers updated; grip/custody unchanged; rollback and interrupted-motion restart safe |
| S9d | Complete geometry-rebase, JSON validation and rendering/perception integration checks | Immediate scale-save, no energy reset, visual/observed position agreement and required full gates |

S9c includes baseline parameter validation and synchronized geometry safety;
S9d deepens their tests and visual calibration rather than postponing correctness.

## Test cleanup first, with remaining removal owned by each stage

### S1 implementation contracts

- Rename the internal experience fact to `assessed`; keep the v1 stored
  `examined` spelling only in the codec until the v2 switch. The assessment
  operation requires recognized knowledge. A transient acceptance block is
  availability, not an assessment rejection. Acknowledgement receipts order
  visible phases; they do not grant custody or permanent willingness.
- A subjective record has its own ID, recognized catalog identity/kind,
  last observed pose/active age, resting evidence, assessment, own disposition,
  checked-absence status and possible source-record links. Association links
  are one-to-one explanations, not extra counted portions. No independent
  writable count is added. Current observations/execution bindings are ephemeral.
- Perceptual continuity matches successive spatial observations within explicit
  distance/time limits, not stable World IDs. Current World handles remain only
  at the application boundary. A disconnected recognized find can join one
  uniquely compatible remembered place, or remain a new finding with possible
  links; ambiguity never transfers private own-deferral experience.
- Search retains a subjective record/place even when no live World handle is
  available. Acquisition needs a currently observed binding, actual arrival,
  eligible resting state and revision revalidation at frame 4. The coordinator
  owns the search budget; its movement requests use the existing walk driver.
- Checked absence marks the old place unavailable. An already usable finding
  wins over a stale-place search. New findings during search end that attempt;
  found-before-missing and missing-before-found converge on the same available
  stock. Repeated empty-place checks do not replenish search budgets.
- Memory v2 stores subjective records and relative active ages; v1 conversion
  preserves learned history without treating legacy tokens as recognition.
  Validate missing association references, self-links and invalid cardinality;
  preserve replacement-World provenance separately from visual identity.
- Motion uses immutable signed velocity, target x, cumulative active elapsed,
  contact count and flight/ground-completion mode. Parameters are immutable
  injected values from Balance. Contact math consumes residual elapsed time;
  only final completion produces collectible resting state. Snapshot rollback
  is exact; durable recovery stores valid ground, without observing that recovery.

| Scenario | Required subjective/action result |
| --- | --- |
| Watched offered portion is dropped and moved continuously | Keep assessment, follow observed place, use short known route when needed |
| The same World ID reappears after an unseen distant move | Treat as a disconnected find; ID alone grants no reunion |
| A different World ID occupies the same observed trajectory | Technical renaming alone does not change cognitive evidence |
| Two identical portions are visible | Two distinct sightings; one new find cannot explain two missing portions |
| Old place is checked empty, then a compatible find appears | Resolve/suppress the old search once a usable find satisfies the need |
| A compatible find is known before the need arises | Prefer available supply without an inventory-balancing detour |
| A held/falling portion is restored on restart | Valid physical recovery; no live binding or fabricated location knowledge |
| User interrupts or needs change before a search finishes | Stop safely; no absence inferred solely from cancellation |

### T0 inventory at `092906b`

| Coverage owner | Distinct contract retained | Later replacement |
| --- | --- | --- |
| `test_ground_approach.py` | Fast left/right/scale reach and rejected-position matrix | S8/S12 replace the exception, retain normal reach |
| `test_world_gui.py` | Controlled-time component wiring, actual grasp event, overlay and cold save/restore | Update each altered route at its implementation stage |
| `test_world_runtime_flow.py` | Real timers, readable bubbles and complete native clip ordering | Keep a small set of real-time integration flows |
| `test_object_memory.py` | Known/unknown retention, compatible versus contradictory observation and own placement | S2/S4-S6 evolve the facts and continuity rules |
| `test_object_awareness.py` | World-to-subjective boundary, hidden move and restored evidence | S4-S6 keep boundary assertions with new bindings |
| `test_object_retrieval.py` | Pure coordinator receipts, known route, changed needs and interruption | S3/S7 replace specific old handover/search expectations |
| `test_object_interaction.py` / `test_object_consumption.py` | Exactly-once events and joint rollback; consume and custody differ | Preserve while updating memory references |
| Memory codec/persistence tests | Schema validation versus actual atomic disk recovery | S6 adds v1 conversion and v2 relation validation |
| World state/extensions/falling/persistence tests | Custody, geometry, elapsed physics and durable normalization | S8/S9/S10 evolve their own contracts |

No further whole test or expensive matrix is demonstrably redundant after the
earlier cleanup. In particular, cold restore versus real timers, compatible
known-identity retention versus an unidentified observation, and current edge
grasp versus ordinary reach are distinct. T0 removes no coverage artificially.
Targeted baseline checks: seven object-memory tests and four ground-approach
tests passed. The user-requested full local suite is reserved for the end.

T0 reviews the actual current tests and the prior
[cleanup evidence](WORLD_DIALOGUE_CLEANUP_REVIEW.md). That earlier cleanup already
removed duplicate edge invocations and shortened a long native scenario; do not
repeat those changes or assume their former duplicates still exist.

Map each relevant test to its behavior, owner, variants and use of controlled or
native time. Consolidate only demonstrated overlap with another retained test
of the same contract and relevant conditions. A shared fixture or similar test
name does not establish redundancy. In particular, handover and autonomous use,
runtime rollback and durable recovery, and fake-time policy versus real animation
completion cover different rules. Native GUI cases are reduced only when their
distinct integration/timing evidence is preserved elsewhere.

T0 may simplify duplicate assertions, parameterize an already duplicated matrix
or remove an orphan helper after confirming its consumers. It changes no
production code or behavior and does not delete current edge-grip or mandatory
handover-inspection contracts in anticipation of later changes. Record which
retained test carries each removed case. No test-count/runtime reduction is a
quota; if no further current duplication is demonstrated, record that finding
and preserve the tests. Apply the development verification policy below.

The remaining replacements are delivered with their implementation stages:

| Stage | Test replacement/removal that belongs in that commit |
| --- | --- |
| S2 | Replace physical-inspection-only assessment/gaze expectations with the single assessment contract; retain unseen/unrecognized-offer and unavailable-acceptance cases |
| S3 | Replace mandatory reinspection of known handovers; keep readable acknowledgement, full consumption, care origin and stale-receipt/interrupt coverage |
| S4-S6 | Update identity-bound fixtures for subjective records; preserve hidden-move, quantity, paired-save and v1-conversion coverage rather than treating them as obsolete |
| S7 | Replace the old runtime search-timer/forgetting assumptions with visible bounded search; retain cancellation, no omniscience and both discovery-order cases |
| S8 | Centralize the fast side/scale/reach geometry matrix; keep unique native actual-arrival coverage |
| S9a-S9d | Evolve the existing fall tests into contact/rebound/completion tests; keep valid old-fall cases and add timing partitions/rollback/recovery without a second duplicate suite |
| S10-S11 | Share new/existing-portion gesture fixtures where appropriate, while preserving their different cancellation outcomes and the Windows input checks |
| S12 | Remove edge-grip-only expectations/helpers when the exception is removed; update edge fixtures to valid drops/placements and retain frame-4 reach revalidation plus ordinary contact blending |
| S13 | Remove only remaining unused helpers/fixtures, stale names and duplicated combinations after those replacements; do not defer earlier stages' test correctness here |

New checks follow the same rule: test numerical policies and variant matrices
with controlled time, component boundaries with focused integration cases, and
actual clipping/capture/window behavior with a small set of native GUI flows.
Do not replace behavior assertions with source-text checks or permissive mocks
merely to shorten the suite. Every behavior-changing commit includes its test
changes and targeted verification, not a promise to repair tests at S13.

## Verification strategy

Latest user instruction supersedes the earlier per-commit full-suite rule:
run targeted behavior tests during development, with Ruff 0.13.2, strict Mypy
1.18.2 and Pyright 1.1.414 checks appropriate to each change. Push small commits
and inspect the preceding GitHub run after subsequent work, without waiting
after every push. A failed CI run stops further feature work until corrected.
GitHub continues its existing Linux Python 3.11/3.13 and Windows checks. Run the
complete local unit/GUI suite only at final integration, plus all final static
gates. Record actual commands, results and commit references in the delivery
table, not predicted test counts; green targeted tests are not full-suite proof.

Use controlled active time and deterministic observations for perception,
matching, search budgets and trajectories. No long sleep-based search tests.
Use a single fast left/right x 1x/2x geometry matrix, then a small number of real
Tk/Windows integration cases. Rework rather than simply delete current tests in
`test_ground_approach.py`, `test_world_gui.py` and `test_object_retrieval.py`:
the edge exception and mandatory known-handover inspection cease to be contracts,
but actual grasp-time revalidation, complete consumption and independent care
origin remain essential.

Required behavior cases include:

- Recognized/assessed versus merely noticed offers, positive/negative preview,
  stale receipts and a later change of needs; full handover use remains visible.
- Preview then observed placement, followed relocation, lost-track relocation,
  unseen movement and a same-type new physical portion. No hidden-ID shortcut.
- One remembered portion, two distinct identical portions, one missing of two,
  two missing with one find, repeated sightings and ambiguous new finds.
- Both discovery orders; a newly found or previously known usable alternative
  satisfies the need without completing an obsolete search.
- No transfer of special own-deferral claims across unresolved associations;
  one consumed find does not clear unrelated same-type stock.
- Empty-place checks, visible search/gaze/short movement, bounded budgets,
  cancellation, stable resolved absence and normal mouse-follow resumption.
- Restart before/after assessment, discovery, confirmed absence, reconciliation
  and consumption; no replayed meal, phantom extra stock or endless old search.
- User/pet acquisition contention, stale action events, duplicate releases,
  capture failure, Escape, focus/capture loss and release off the primary monitor.
- Zero/low/high falls at either edge and both scales: impact-dependent heights,
  travel and variable hop counts; energy decreases at each bounce. No fixed
  three-hop assertion. Check stopping thresholds, the finite safety budget and
  low-energy inward completion without unreachable rest or visible teleportation.
- Reachable drops can rebound without leaving their safe interval; outside drops
  stay inside after entering it. Cover delayed frames, partitioned elapsed time,
  scale change during motion and immediate save after a scale change. Moving
  portions cannot be collected and geometry updates do not replenish energy.
- Compare zero/exact ground contact, an ascending apex, several contacts in one
  large advance and the timed final ground correction. No invalid negative
  `WorldPosition`, zero-time contact loop or unbounded render-step catch-up.
- Invalid elapsed/parameters leave the World unchanged; already settled advances
  are idempotent. Check velocity signs, state-dependent clearing, active-motion
  snapshot restoration and preserved ID/revision rules without demanding equal
  revision counts from differently partitioned time intervals.
- Extend existing `test_world_falling.py`, `test_world_state.py`,
  `test_world_extensions.py` and `test_world_persistence.py` around their owners;
  test the pure motion policy separately if useful. Preserve fixed-height
  old-fall cases where meaningful rather than duplicating a second full suite.
- Joint transaction rollback, interrupted writes and existing save backup rules;
  snapshots include enough motion state for runtime rollback.
- Window transparency, stacking, pointer grip, no accidental pet care, coherent
  input teardown and image-owner cleanup in real Windows checks.

## Isolated practical acceptance

Extend [the existing smoke starter/checklist](WORLD_SMOKE_TEST.md); do not create
a second starter or touch the real save. Provide hungry and supplied states,
plus one/two-identical-portion arrangements. Use the same isolated save for the
restart cases and report what was observed rather than only automated results.

1. Offer food and a drink, hear the decision, then place them while Aiko watches.
   Check later known retrieval and complete consumption without re-identification.
2. Repeat accepted release into her hand; check readable handover and full use,
   with the correct human care origin.
3. Pick up a resting portion, offer it again, move it and cancel the gesture.
   Check that the same portion survives and native clicks/focus behave correctly.
4. Move a known portion while observed, then repeat while unobserved. Check
   different recognition claims rather than technical-ID certainty.
5. Create need with the old place empty. Watch search animation and its bounded
   outcome; introduce or reveal a useful find during search.
6. Reverse the order: reveal the find first, then trigger need. Check that Aiko
   uses it without an unnecessary old-place search.
7. Repeat with two identical portions and only one moved/missing. Check truthful
   quantities, no double-counting and no single find satisfying two deficits.
8. Drop from low and high positions beyond both normal reach limits at 1x/2x.
   Check stronger/higher drops produce a visibly different damped response and
   a variable number of hops, with all cases ending on reachable ground. Repeat
   inside the interval to check rebounds stay safe, then normal pickup and
   foot-area put-down.
9. Restart while carrying, falling/hopping and after a missing-place resolution.
   Check valid recovery, retained subjective facts and no resumed search loop.
10. Interrupt pickup/use/search with ordinary user actions and confirm safe
    ordering, one consumption effect and normal interactions afterward.

Delivery remains incomplete until automated checks, Windows interaction evidence
and the user's practical review have been recorded. Implementation proceeds in
the authorized order; merge still requires practical acceptance.
