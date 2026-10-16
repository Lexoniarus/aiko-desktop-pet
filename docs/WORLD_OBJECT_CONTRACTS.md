# World object contracts and behavior rules

## Current observed-continuity correction — 16 October 2026

The [continuity correction plan](OBJECT_CONTINUITY_CORRECTION_PLAN.md) separates
observed motion, learned identity and current desire. Aiko may recognize and
want a portion during holding. An observed pickup and continuously followed
placement preserve its subjective record, with or without a prior intention.
Known identity does not require another recognition dwell; unknown identity does.
Known but unassessed portions require a use decision, not another identification.

A wish expressed while the player already holds a portion is ordinary interest,
not withholding. Only taking an existing committed target invokes the rules
below. A continuing wish survives observed placement independently of normal
seeking thresholds; current capacity/activity must still permit consumption.
Release in the handover area remains required for human care. Later ground
collection always has autonomous origin. Knowledge and assessment persist using
the existing save format; live tracking, current wishes and actions do not.

## Current committed-attention correction — 16 October 2026

The [focus correction plan](OBJECT_FOCUS_CORRECTION_PLAN.md) supersedes older
ordinary-contact priority rules during an accepted object episode. The interaction
owns one subjective focus until its outcome. Other drops, moves and offers do not
enter perception/memory. Hover and ordinary clicks cannot interrupt; clicks ask
for a short wait without care rewards. Explicit commands retain safe put-down.

An observed successful take of the target pauses before frame-4 custody. Existing
cursor geometry and sixteen-direction gaze follow that exact visible portion.
`await_return` waits for the player; `await_settle` waits through fall/hops.
Resume the same episode after resting, preserving knowledge/assessment and actual
care origin. Unknown objects still need their original investigation. Visual loss
discards continuity and activates existing bounded subjective search, without
tracking through a hidden World ID or merging unobserved identical neighbours.

Repeated requests are at least 10 active seconds apart. A first repositioning is
free; frustration begins after 18 seconds held or the third observed take in one
episode. Eligible loss requests are at least 30 seconds apart, 0.15 friendship
points each and at most 0.6 requested per episode. Actual losses additionally have
a 120-active-second session cooldown across episodes. Suppressed loss requests are
not replayed later. Return stops escalation and adds no friendship reward;
temporary irritation expires normally without clearing unrelated irritation.
Validated JSON owns all these start values and authored dialogue. Persist actual
friendship through the existing save; restart no running focus/waiting episode.

## Earlier implementation record

Status: initial implementation through Stage 8; first practical test found
behavior gaps. The investigation/feedback revision below is agreed behavior,
implemented with practical follow-ups and verified with 855 tests at `ea4361f`;
the user reports the revised basic flow looks correct. Extended native checks
and longer-term behavior remain open.
Recorded: 15 October 2026.
Baseline: `1753266db0dafc94024913cb281b80e7abe289a0` (merged PR #9).

This is the detailed contract for Stage 1 of the
[implementation plan](WORLD_OBJECT_IMPLEMENTATION_PLAN.md). It describes the
accepted first feature. The [current architecture](ARCHITECTURE.md) maps these
semantic contracts to their implemented owners and Python APIs.

## Confirmed product decisions

### Current offers, placement and search contracts — 16 October 2026

The complete [follow-up plan](OBJECT_PLACEMENT_AND_SEARCH_PLAN.md) records the
agreed behavior, delivery commits and verification. It covers assessed cursor offers,
moving resting portions, impact-dependent damped settling hops, subjective
identity and quantity, and visible bounded search. Technical World IDs must not prove that
an unobserved new find is the old portion. Found-before-missing and
missing-before-found must both avoid repeated searches and double-counting.

The latest hop clarification replaces the fixed three-hop proposal: fall height
and impact speed determine rebound height, travel and the number of damped hops.
Motion must terminate on reachable ground, including low-energy outside drops;
there is no mandatory hop count. See the follow-up plan for bounded inward
settling, safe trajectories and the corresponding verification cases.

The selected implementation approach is a small own-physics policy, not Pymunk.
The follow-up plan records pure analytic motion, signed immutable state,
state-dependent cleanup, exact runtime rollback versus durable ground recovery,
and substeps S9a-S9d. These are implemented on the feature branch; practical
acceptance of the combined changes remains pending.

Its assessment/handover, subjective reidentification, reachable placement and
search rules supersede the
older inspected-only, World-token memory, bounded-edge-grip and missing-object
rules below. Older dated sections remain historical where superseded.

- Assessment belongs to subjective memory and can happen during a recognized
  cursor offer. Release-time willingness is rechecked; a readable handover cue
  precedes full consumption without repeated inspection.
- Current geometric tracks map to execution handles only at the application
  boundary. Disconnected finds use type/place hypotheses and one-to-one stock
  associations, not technical identity. Checked missing places and unresolved
  consumed-find witnesses persist in memory v2; v1 history still loads.
- Search has one active-time budget, visible gaze/short ordinary walking and
  identified feedback. Currently useful stock can replace a stale-place search.
- Resting portions can become user-held without changing ID. Cancellation or
  off-monitor release returns existing portions to valid source ground; new
  chooser portions are removed. Moving portions cannot be collected.
- Free motion is falling, optionally bouncing, then resting. Impact energy
  drives damped hops with a finite tail and continuous inward completion.
  Shared bounds apply to scripted placement, put-down, cancellation, geometry
  updates, settlement and durable recovery. The special edge grip is removed.
- Runtime checkpoints preserve signed velocities and progress. Durable World
  v1 stores valid ground targets; actions, capture and motion are not resumed.
- Food/drink thresholds, care origin, frame-4 acquisition, reverse detach and
  complete consumption playback remain unchanged.

### Remembered supplies — 16 October 2026

Recognized knowledge, successful inspection and confirmed own deferral survive
restart until consumption or confirmed local absence. Fleeting unidentified
sightings alone expire after ten active minutes. World truth, current perception
and learned knowledge remain separate; a saved location is not current sight.

A wanted, previously inspected supply follows need-based recall, approach,
pickup and full consumption, then outcome. It skips repeated examination,
recognition and desire bubbles. Recognized-but-unexamined objects retain the
first investigation; cursor handover retains its own entry. Changed needs or
contradictory evidence still revalidate before use. This supersedes mandatory
reinspection for that known-ground route only. The
[persistent knowledge plan](OBJECT_MEMORY_IMPLEMENTATION_PLAN.md) records owners,
atomic save/recovery rules and delivery evidence.

### Practical-test clarification — 15 October 2026

Investigation is a distinct intention independent of current hunger/energy.
New noticed reachable ground objects lead through visible orientation,
approach, pickup, held examination/identification and a consumption decision.
No immediate desire to consume means animated put-down with a later-use bubble,
not permanent gaze-only behavior. Relevant phases require readable authored
bubbles. Record examined/deferred knowledge to avoid repeated inspection loops.

Latest practical clarification: after put-down, an examined deferred portion
keeps its known identity/location but releases object gaze to normal cursor and
ambient behavior. It becomes a goal again when wanted. Consumables render in
front of the character without additional hand-mask layers during pickup,
holding, consumption and put-down; imported hand assets remain preserved.

These rules supersede the original requirement for recognized, wanted food as
the only approach goal, and pickup completion must no longer automatically
consume before inspection/decision. Physical World custody states, canonical
consumption effects and the release-to-accept requirement stay in force.
Required phase feedback uses identified completion/cancellation receipts and
readable lifetimes through the existing reaction player. Ground inspection
holds for at least one active second. A willing recognized offer may be released
without waiting for preview speech to disappear; accepted custody then enters
held inspection, identification and a readable decision before visible use.
Passive hover cannot truncate that use; explicit user actions still arbitrate.
See the [architecture-aligned correction plan](WORLD_OBJECT_IMPLEMENTATION_PLAN.md#practical-test-correction-plan)
for state ownership, handover entry, completion/interrupt rules and small steps.
The later sections retain the initial implementation contract as baseline where
it is not superseded by this clarification.

### Implementation update — 15 October 2026

The accepted end-to-end implementation plan supersedes the earlier narrow
first-version restrictions. The rules below incorporate those decisions:

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
  durable saves omit terminal instances while preserving the next instance ID.
  In-session consumption receipts retain the latest 4096 completed requests.
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
- Ground collection resolves the closest legal full-window standing position
  on the active track. Ordinary reach remains one quarter of the current window
  width. When an in-bounds ground item lies beyond that radius at either screen
  edge, a bounded edge grip requires actual arrival within two desktop pixels
  of the closest clamped standing position. An off-track item/pet or a track
  narrower than the full character window cannot use this exception.
- Planning and the frame-4 availability/reach recheck use the same geometry
  rule. Edge acquisition snaps to the authored hand anchor at that event;
  pre-grasp ground position and nutrition remain unchanged. Aiko's window stays
  inside the active track throughout. The existing pickup/inspection/decision
  phases and handover rules remain in their owners.
- After refusal or pre-consumption interruption, reverse playback releases the
  portion in front of Aiko's feet at source frame 4→3, clamped for its footprint.
  Confirm the new location in subjective memory through her own completed action.
  Item footprints and allowed ground bounds are validated before resting.
- Changed screen/track geometry is an explicit World update. Reproject/clamp
  resting items through the World owner and cancel invalid prepared operations.
  Update Aiko's subjective position knowledge only through new observations.

Unsupported-display release removes the cursor portion with brief feedback.
Escape or loss of the gesture's Tk input capture removes it without consumption.
Shutdown saves nonterminal items for ground recovery; it does not resume input.
No portion is silently transferred between monitors to make a target reachable.

## Perception, recognition, interest and intention

| Step | Preconditions | Result |
| --- | --- | --- |
| Notice | Observable candidate inside notice range, sufficient attention and elapsed observation time | A located appearance/motion is known; food identity need not be known |
| Recognize | Candidate can be examined inside recognition range for the required observed duration | Canonical food identity becomes available to memory and interest |
| Remember | Information was actually acquired | Last-known location and observation age remain available after loss of sight |
| Want | Recognized edible food, appetite/interest criteria and canonical food acceptance allow it | An interested candidate; no custody or nutrition change |
| Select | Wanted resting food or its remembered location, reachable known position, no blocking activity and cooldown satisfied | A stable approach/search intention |
| Acquire | Fresh final check of identity, custody, distance, activity and acceptance succeeds | Coordinated custody transfer; no independent care effect |
| Consume | Pet-held portion and prepared pet transition can commit together after pickup completion or accepted handover | Instance and pet effect complete exactly once |

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
and food acquisition remain blocked. Available attention contributes without
depending on the renderer's look-frame ID; there is no facing-angle filter.

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
| Successful release into Aiko's hand | Existing satiety, digestion, repetition, food mood and meal rules | Existing feed social/adaptive/dialogue and friendship rules, including their limits; once at successful consumption |
| Autonomous ground collection | Same canonical satiety, digestion, repetition, food mood and meal rules | No feed social gain, human-contact/adaptive interaction credit or friendship reward |
| Failed offer, refusal or mere placement | None | None |

Food-related mood effects and meal credit remain nutritional effects; they do
not disappear just because consumption was autonomous. Spontaneous commentary
can acknowledge autonomous eating without recording human contact. Energy Drink
is a distinct drink interaction, sought at energy ≤60 and accepted under the
existing energy-drink rules. It restores up to ten energy without nutrition.
The old direct-feeding UI is removed; canonical care policies remain reusable.

## Arbitration and interruptions

These are application behavior rules. Preserve the current render-priority
contract while supplying explicit active actions; do not independently reorder
game, sleep or existing one-shot playback in this feature.

| Situation/event | Before eating commit | After eating commit |
| --- | --- | --- |
| Explicit talk, petting or a new carried choice | Cancel approach; if already acquired, finish safe hold and animate put-down before action | Nutrition remains committed; present user action according to existing playback rules |
| User starts a game | Cancel approach or put down acquired item before opening game | No rollback; game playback follows existing rules |
| Sleep requested | Cancel approach or put down acquired item before sleeping; automatic routine waits during object execution | No rollback; sleep playback follows existing rules |
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

Interruption cancels approach while retaining subjective knowledge. After grasp,
pickup reaches source pose 8, then reverse playback detaches at 4→3; the latest
queued user action runs after put-down. No nutrition is granted for grasp.
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
5. Commit consumption of the pet-held item and the pet transition in one non-reentrant
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

Automated evidence and commit references are in the implementation ledger.
Native Windows interaction acceptance is tracked separately in
[the practical checklist](WORLD_SMOKE_TEST.md).

## Resolved implementation parameters

- Notice: 3 body widths, 0.2 s; recognize: 1.5 widths, 0.6 s of attention.
  Losing visibility clears current evidence, while learned memory persists.
- Only unidentified sightings expire after 600 active seconds. Recognized identity
  and completed inspection persist until consumption or confirmed local absence;
  no offline aging or knowledge refresh. Own confirmed deferral is a separate fact.
- Seek food at satiety ≤70, drink at energy ≤60. Check at most once per second
  plus relevant changes. Retain eligible goals; tie-break by need urgency,
  food repetition, path length and stable instance token.
- Search at last-known position for 2 s, then forget that presence and retry
  after 10 s. Interruption also waits 10 s; renewed supply seeking of examined
  portions waits 30 s after consumption. This pause does not block the first
  investigation of a different, unexamined portion.
- Handover: horizontal distance ≤0.3 body widths, height 0.05–0.9 widths;
  recognition observed within 0.5 s, no conflicting action, canonical capacity.
  Ground reach is 0.25 widths, with actual arrival checked within 2 desktop units.
- Press starts one portion immediately; even a quick release only offers/drops.
  A local Tk grab spans the gesture, Escape cancels, lost capture cancels, and
  release outside supported primary-surface bounds removes with feedback.
- Fall acceleration is 900 desktop units/s², integrated analytically without
  bouncing. Presentation runs at about 33 ms; cognition stays in the existing tick.
- Save schema stays outer v1, with optional `world.version=1`. Ground recovery
  normalizes falling/user-held/pet-held objects, keeps IDs and the next ID,
  drops terminal objects and never restores actions or capture. A separately
  versioned optional `object_memory` section preserves learned facts and relative
  active ages in the same atomic file; current observations/evidence start empty.

Perception/interest/fall parameters are validated in `data/balance.json`.
Grip/pointer and native appearance still need the practical calibration review.

## Stage 2 implementation boundary

Historical foundation boundary (`069923c`): these headless APIs established World
ownership before desktop integration. Later stages added `advance_falls`,
`put_down`, `change_surface`, `change_footprint`, snapshot recovery and drink
definitions. World-only operations still never mutate pet needs.

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
recovery and idempotent receipts are implemented by the application coordinator.
Callers must not mistake the World-only `consume` operation for that use case.
