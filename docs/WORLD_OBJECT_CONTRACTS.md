# World object contracts and behavior rules — Stage 1

Status: Stage 1 specified; headless Stage 2 foundation implemented separately.
Recorded: 15 October 2026.
Baseline: `1753266db0dafc94024913cb281b80e7abe289a0` (merged PR #9).

This is the detailed contract for Stage 1 of the
[implementation plan](WORLD_OBJECT_IMPLEMENTATION_PLAN.md). It describes the
planned first feature. The [current architecture](ARCHITECTURE.md) remains the
reference for existing behavior. Names below describe semantic contracts, not
newly implemented classes or fixed Python signatures.

## Confirmed product decisions

### Implementation update — 15 October 2026

The accepted end-to-end implementation plan supersedes the earlier narrow
first-version restrictions below where they conflict:

- Cursor pickup/release replaces direct feeding, including the energy drink.
- Food seeking starts at satiety 70; drink seeking starts at energy 60.
- Ground pickup transfers custody at source frame 4, then consumes only after
  the eight-frame pickup completes. Interrupted held items are put down with
  reverse playback before a queued care/game/sleep action.
- Pet-held objects may therefore return to resting. This replaces the earlier
  assumption of immediate acquisition and consumption in one operation.
- Use the approved `Aiko_Pick_Up_und_Hinlegen.zip` runtime frames, hand layers
  and metadata. Release during reverse playback occurs after source frame 4.
- Preserve the outer save version 1 with an optional versioned World section;
  restore nonterminal carried/falling items to valid ground locations.

The stage ledger in the implementation plan records the small delivery commits.

| Decision | Rule | Evidence |
| --- | --- | --- |
| Handover gesture | Aiko may notice and assess user-held food, but takes it only when the user releases it inside the handover area and she accepts it at that moment | User decision, 15 October 2026 |
| Random versus goal movement | `auto_walk` controls random walks. A perceived, wanted food target can cause goal movement even when random walks are disabled. Without an eligible goal, the existing random-walk setting applies | User decision, 15 October 2026 |
| Care attribution | Successful direct handover uses the existing direct-feeding care and friendship rules. Autonomous collection grants nutrition without those human-care rewards | User decision, 15 October 2026 |

These decisions supersede the corresponding open choices in the initial plan.
Additional rules below make the first version concrete; numeric tuning and
remaining stage-specific choices are listed at the end.

## State owners and read contracts

| Contract/owner | Required information | Restrictions |
| --- | --- | --- |
| Object definition | Stable type ID, supported interactions, canonical food ID and visual asset reference | Reference existing food/asset data; do not duplicate nutrition or German labels |
| World instance | Unique instance ID, definition ID, revision, lifecycle/custody state and spatial values appropriate to that state | The World alone mutates this record; IDs are never reused during a session |
| Objective World snapshot | Current immutable instance values, active surface bounds and snapshot/revision context | Available to application coordination, perception input and presentation; not unrestricted planner input |
| Pet spatial observation | Read-only current position, footprint, handover anchor, scale and actual reachable track | Derived from existing desktop owners; no second writable pet position in World |
| Object observation | Continuity token, observed position/motion, observation time and information actually noticed or recognized | No newly recognized identity before the recognition condition succeeds |
| Object memory | Learned identity if any, last-known position, last observation time and freshness | No lookup that silently refreshes an unseen object |
| Intention | Goal kind, target token, last observed/remembered target location and reason | Owned by the mind; no Tk callbacks or custody mutations |
| Interaction execution | Interaction ID, selected instance, origin, current step and terminal result | Owned by application coordination; at most one foreground object interaction |
| Confirmed effect/result | Interaction ID, instance ID, action origin, outcome/reason and committed consumption/care effect | Language-neutral; presenters do not re-evaluate acceptance or effects |

An instance revision changes when authoritative custody or spatial state changes.
An old revision invalidates a prepared mutation, not the object's stable identity.
Subjective continuity tokens do not themselves reveal item identity or location.

Application bridges map World data into mind-owned observation contracts. World
does not import pet needs, and mind planners do not import concrete World stores.
Display and effect adapters receive only the capabilities they need. All mutation
requests run on the application owner thread.

## Instance lifecycle and custody

| State | Meaning and spatial authority | Allowed next states |
| --- | --- | --- |
| User-held | One portion is attached to the active pointer gesture; the input adapter supplies its pose to World | Falling; pet-held on accepted release; removed on explicit gesture cancellation |
| Falling | World owns free fall toward the active ground; no carrier | Resting; removed by explicit removal |
| Resting | World owns a stable ground position | Pet-held on accepted collection; removed by explicit removal |
| Pet-held | Aiko owns the portion; presentation follows her hand anchor | Consumed; resting after interrupted animated put-down |
| Consumed | Terminal instance, no collectible position | None |
| Removed | Terminal explicit removal/cancellation, with no nutritional effect | None |

- Offering is context around a user-held instance, not a duplicate instance or
  separate custody state. Only one cursor-carried portion is active at a time.
- A pickup gesture creates one instance. Repeated pointer samples do not create
  portions. Successful handover invalidates the gesture's ownership immediately.
- A rejected, unnoticed or busy handover release starts falling. It does not
  queue a later handover or leave an invisible portion attached to the cursor.
- Acquisition and consumption are separate: source frame 4 acquires during
  pickup, then completion begins eating. An intervening user action requests
  animated put-down before it executes. No nutrition is granted for acquisition.
- Falling food can be observed, but is collected only after it is resting.
  User-held food can be examined, but is acquired only through release/handover.
- Explicit removal changes availability without granting Aiko knowledge of an
  unseen removal. Terminal identity/receipt records prevent duplicate effects;
  their retention and persistence are finalized in Stages 6 and 8.
- Taking an already resting object back onto the cursor is not required by this
  first scenario. A later gesture must use the same custody authority if added.

## Space, anchors and reach

The first World has one active horizontal surface corresponding to the current
primary taskbar track, including its existing work-area fallback. It does not
add cross-monitor paths or alternate walking surfaces.

- World coordinates use logical desktop units independent of Aiko's selected
  1x/2x sprite scale. Origin is the active track's left ground point; positive
  horizontal values go right and positive height goes up. Resting anchors have
  height zero. The desktop adapter maps native/Tk coordinates into this space.
- The active ground width and supported height are supplied as geometry values.
  Desktop/OS DPI conversion stays in the adapter. Changing Aiko's sprite scale
  does not multiply every World object's position or move a resting portion.
- The object position denotes its ground/support anchor. Its graphic pivot and
  cursor grip are separate offsets. World receives a resolved object pose from
  input; it does not read sprite pixels or pointer APIs.
- Pet position is a read-only body/foot anchor derived from the existing desktop
  position and character geometry. The existing desktop placement path remains
  its single writer and returns actual clamped displacement.
- Perception distances and reach are expressed in body-relative units using
  current character geometry. Conversion occurs once at the boundary, without
  copying the character's dimensions into a second catalog.
- A handover area is a stable body/hand-relative area, scaled with Aiko. It is
  independent of transparent window margins and does not oscillate per frame.
- Ground collection requires a reachable standing position within interaction
  distance. Choose the closest feasible approach side; at an edge, the other
  side is allowed. If no position fits the actual track, the target is unreachable.
- Reaching a clamped boundary is not arrival unless interaction distance is met.
  Item footprints and allowed ground bounds are validated before resting.
- Changed screen/track geometry is an explicit World update. Reproject/clamp
  resting items through the World owner and cancel invalid prepared operations.
  Update Aiko's subjective position knowledge only through new observations.

Unsupported-display release, input capture loss and shutdown recovery are
resolved before Stage 7 input and Stage 8 persistence. No implementation may
silently teleport a portion between monitors to make a target reachable.

## Perception, recognition, interest and intention

| Step | Preconditions | Result |
| --- | --- | --- |
| Notice | Observable candidate inside notice range, sufficient attention and elapsed observation time | A located appearance/motion is known; food identity need not be known |
| Recognize | Candidate can be examined inside recognition range for the required observed duration | Canonical food identity becomes available to memory and interest |
| Remember | Information was actually acquired | Last-known location and observation age remain available after loss of sight |
| Want | Recognized edible food, appetite/interest criteria and canonical food acceptance allow it | An interested candidate; no custody or nutrition change |
| Select | Wanted resting food or its remembered location, reachable known position, no blocking activity and cooldown satisfied | A stable approach/search intention |
| Acquire | Fresh final check of identity, custody, distance, activity and acceptance succeeds | Coordinated custody transfer; no independent care effect |
| Consume | Acquisition and prepared pet nutrition transition can commit together | Instance and pet effect complete exactly once |

The application perception bridge may inspect objective definition data to
resolve authored recognition; there is no image-recognition service. Only the
perception result crosses into memory, interest and goal selection.

Notice range is at least recognition range; collection reach is narrower than
the general perception area. Exact distances and durations are validated balance
parameters in Stage 3. Observation duration advances only while the corresponding
conditions hold. Losing sight stops new evidence; knowledge ages rather than
being refreshed from the World. Recognition evidence can decay under explicit
Stage 3 rules instead of depending on update count.

An asleep Aiko does not acquire new observations or wake just because food
exists. During games or care, available attention may be reduced; new locomotion
and food acquisition remain blocked. Body orientation/attention contributes to
perception without depending on the renderer's current look-frame ID.

The first sensor uses known object-display availability and geometric/attention
rules. It does not inspect foreign window content or add native occlusion
detection. A hidden/unmapped Aiko object layer supplies no visual observations.

Hunger-driven seeking has a distinct threshold from the existing fullness
rejection rule. Repetition and mood reuse existing nutrition information. No
new permanent dislike or learned-preference system is introduced in this stage.

For equally suitable ground foods, prefer the shortest known reachable path,
then a stable instance ordering. Keep the chosen goal across minor score changes.
Known user-held/falling items may attract gaze; translational pursuit of held
or airborne items is deferred beyond the first ground-food scenario.

After loss of sight, walking may continue toward a remembered location, never
toward an unseen updated position. At the last-known location, missing fresh
confirmation causes a bounded observation attempt, then goal cancellation and
a retry cooldown. An authoritative failed availability check gives a local
interaction failure, not an omniscient replacement target position.

## Handover, autonomous eating and care origin

Direct handover requires a live user-held instance released in the handover
area, current recognition of that instance, willingness to accept it, canonical
food acceptance and an available interaction slot. Hold duration can provide
recognition time; it never itself transfers the portion.

Release outside the area, lack of recognition, refusal or a blocking activity
starts falling. No click-through feeding, sleep interruption, deferred invisible
handover or care reward occurs. Normal later perception may select the resting
portion autonomously.

| Origin | Food effects | Human-care effects |
| --- | --- | --- |
| Existing direct feed | Existing unchanged behavior | Existing unchanged behavior |
| Successful release into Aiko's hand | Existing satiety, digestion, repetition, food mood and meal rules | Existing feed social/adaptive/dialogue and friendship rules, including their limits; once at successful consumption |
| Autonomous ground collection | Same canonical satiety, digestion, repetition, food mood and meal rules | No feed social gain, human-contact/adaptive interaction credit or friendship reward |
| Failed offer, refusal or mere placement | None | None |

Food-related mood effects and meal credit remain nutritional effects; they do
not disappear just because consumption was autonomous. Spontaneous commentary
can acknowledge autonomous eating without recording human contact. No energy
drink behavior is inferred from hunger; its separate rules need explicit scope
before it becomes a World consumable.

## Arbitration and interruptions

These are application behavior rules. Preserve the current render-priority
contract while supplying explicit active actions; do not independently reorder
game, sleep or existing one-shot playback in this feature.

| Situation/event | Before eating commit | After eating commit |
| --- | --- | --- |
| Explicit talk, petting or direct feeding | Stop object movement and cancel its execution; process user action, then reevaluate later | Nutrition remains committed; present user action according to existing playback rules |
| User starts a game | Cancel object execution; no acquisition while game is open | No rollback; game playback follows existing rules |
| Sleep begins | Cancel object execution; no seeking or handover while asleep | No rollback; sleep playback follows existing rules |
| Existing care/one-shot animation or explicit active controls | Defer new object execution; do not reset the active action | Existing playback/arbitration governs display |
| Intentional pet hover/contact | Stop an autonomous approach; resume only after fresh arbitration and cooldown | No rollback; preserve the confirmed eating result |
| User-held item enters offer area | Treat as offer context; allow recognition, with no transfer before release | The completed instance cannot become user-held again |
| Pinned toolbar merely remains visible | No permanent block; actual control use still blocks | No new effect |
| Cursor gaze or gaze toward own goal | Gaze alone does not cancel goal movement | No new effect |
| Observed busy workload/insufficient movement energy | Defer movement using existing trusted readings; do not invent workload | No new effect |
| `auto_walk` disabled | Disable random departures; a wanted perceived/remembered food goal may still move under other gates | No new effect |
| Target moves while observed | Update the known target and validate reach; no teleportation | Consumed objects no longer move in World |
| Target disappears outside perception | Preserve only last-known information; resolve by observation or final availability check | No recreation or extra effect |
| Track/scale changes | Recompute geometry and reach, invalidate stale prepared operations | Do not reverse nutrition; reanchor presentation |

Distinguish user attention from goal-directed gaze in the movement inputs. Reusing
a generic attention-blocking flag for Aiko looking at her own target would stop
her approach. The offering context must likewise avoid accidental ordinary pet
clicks and duplicate greeting/care actions.

Interruption normally cancels execution while retaining subjective knowledge.
After the blocker clears, reevaluate rather than resuming stale callbacks.
Ground food remains where it was. A user-held release that cannot be accepted
falls; it is not reserved while Aiko finishes another activity.

## Consumption boundary, failures and repeated requests

1. Check a completed interaction receipt first. An identical repeated request
   returns its previous result with no new effect or repeated time consumption.
2. Advance shared pet session time once as appropriate. This normal time progress
   is separate from food effects; rejection does not rewind elapsed time.
3. Read current World/Pet values. Validate instance, revision/custody, location,
   recognition, origin, activity slot and current food acceptance.
4. Prepare the complete nutrition/care transition and World transition without
   mutation. Resolve all fallible lookup/validation work before commit. For a
   failed handover, prepare only the normal release-to-falling transition.
5. Commit acquisition/consumption and the pet transition in one non-reentrant
   owner-thread operation. Publish the receipt only after both owners agree.
   No timer, UI callback, await, file write or externally supplied function runs
   between the related commits.
6. Deliver the confirmed result to presentation and normal saving. The eater's
   hand sprite is a visual continuation of the consumed portion, not a new
   collectible World instance.

Ordinary validation failures leave the target and nutrition unchanged, except
for a user release's specified transition to falling. Use explicit outcomes
such as deferred, refused, unavailable, out-of-reach, stale or consumed. These
outcomes do not automatically reveal unseen identity/location information.

An unexpected partial commit restores both owners to their prepared before-state
through owner-controlled recovery, then reports failure without an automatic
retry. Recovery preserves aggregate identity and already advanced session time.
If consistency cannot be restored, stop further mutation/autosave of that session
rather than persist a half-applied operation. Stage 6 must verify this boundary
with failure injection; it need not introduce a generic transaction framework.

The same interaction ID with conflicting input is invalid. A new interaction ID
against an already consumed/removed instance is unavailable. This contract
guarantees in-session effects; crash/restart consistency is designed in Stage 8
using a joint durable pet/World snapshot, not assumed from an in-memory receipt.

## Stage 1 review scenarios

| Scenario | Required result |
| --- | --- |
| Two identical Onigiri | Distinct instance IDs; consuming one leaves the other unchanged |
| Hold recognized wanted food near Aiko | She may look/react; custody stays with the user until release |
| Release recognized wanted food into her hand while free | One consumption plus canonical direct-feed care effects |
| Release while full, unrecognized, sleeping or busy | Food falls; no nutritional or care effect |
| Drop wanted food at a distance | Observe/recognize, approach when eligible, collect once after ground contact |
| Disable random walks, then perceive wanted food | Goal approach allowed; no random fallback departure while disabled |
| Move/remove a target unseen | Memory retains the old location; no tracking of hidden truth |
| Turn head toward the selected food | Goal gaze does not block the approach |
| Start a game or care action during approach | Cancel movement/execution; ground portion remains unchanged |
| Interrupt eating presentation after commit | No rollback, recreated food or second reward |
| Replay completion or change request ID after consumption | Prior receipt or unavailable outcome; no second effect |
| Fail before commit or inject partial commit failure | No half-applied food effect; owner-controlled recovery for the latter |
| Change sprite scale | Objects retain logical positions; reach/anchors update |

These are specifications, not tests already run. Stages 2–8 supply automated
and native Windows evidence for their corresponding scenarios.

## Remaining implementation-stage decisions

- Stage 3: exact notice/recognition ranges, attention rules, dwell durations,
  evidence decay and memory freshness. Define validated body-relative units.
- Stage 4: exact appetite thresholds, interest differences, switch hysteresis,
  bounded search duration and cooldowns. Capacity to eat is not desire to seek.
- Stage 5: exact stable handover/foot anchors and approach tolerances from
  character geometry; preserve the movement semantics confirmed above.
- Stage 6: concrete prepared-transition/receipt contracts and retention bounds,
  with the failure behavior above and an interruptible pickup/put-down phase;
  no user reward policy remains open.
- Stage 7: short-click versus hold discrimination, visual offer/refusal feedback,
  release outside the active surface and capture-loss/Escape behavior. The
  confirmed release-to-accept gesture itself is settled.
- Stage 8: save format/migration and recovery of carried/falling/transient items;
  retain existing save compatibility and no offline World consumption.

No code, new balance values, executable tests or persistence changes are part
of Stage 1. Its completion records these contracts, the confirmed product
decisions, scenario review and the remaining stage-specific tuning.

## Stage 2 implementation boundary

The following headless APIs now implement World ownership; no DesktopPet,
perception, UI, nutrition or save integration is installed by Stage 2.

| Owner/API | Implemented behavior |
| --- | --- |
| `world/contracts.py` | Frozen definitions, surface, support-anchor positions, horizontal footprints, lifecycle enum and objective snapshots |
| `WorldState.place_resting` | Create a distinct portion directly on the ground for scripted sources |
| `WorldState.create_held` / `move_held` | Create/update the single user-held instance without feeding Aiko |
| `WorldState.move_resting` | Explicit ground relocation without updating any subjective memory |
| `WorldState.release` / `land` | Mark falling and record scripted ground contact at the same horizontal anchor; no timed physics yet |
| `WorldState.accept_handover_on_release` / `collect_resting` | Record a custody change already authorized by a caller; no implicit perception/reach/appetite decision |
| `WorldState.consume` | Mark a pet-held edible instance consumed; no pet changes or interaction receipt |
| `WorldState.remove` | Terminal cancellation/removal of user-held, falling or resting instances |
| `WorldState.get` / `snapshot` | Owner-thread access to frozen values; snapshots can subsequently cross threads |
| `infrastructure.world_catalog.build_food_object_definitions` | Reference food/asset identities from the existing validated catalogs, excluding the energy drink |

Named mutations require the expected instance revision. State/spatial changes
increment it and the World revision; identical position updates are no-ops.
Creation allocates monotonically increasing IDs scoped to one World session.
Terminal identities remain in snapshots so they cannot be reused. At most one
portion is user-held and at most one is pet-held.

The first core rejects out-of-bounds anchors/footprints rather than deciding an
unsupported-drop policy. Footprints are explicit logical extents supplied by the
caller; resolving them from actual scaled graphics is later adapter work.
The surface is fixed for this stage; geometry updates follow in desktop
integration. No external clock, filesystem, taskbar or image reader is used by
the World core.

Application-level validation, release-on-refusal, joined pet/World commits,
recovery and idempotent interaction receipts remain Stage 6 responsibilities.
Callers must not mistake the World-only `consume` operation for that use case.
