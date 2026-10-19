# World object behavior and ownership

This is the maintained contract for the current implementation. Follow the
[architecture](ARCHITECTURE.md) for module details, the
[practical checklist](WORLD_SMOKE_TEST.md) for acceptance and the
[documentation index](README.md) for current validation. Earlier plans and
superseded rules are [historical records](history/README.md).

## Independent facts and owners

| Concern | Owner and meaning |
| --- | --- |
| Objective portion | `world/state.py`: instance, revision, custody, position and motion |
| Acquired knowledge | `pet/mind/object_memory.py`: learned identity, last observed place, assessment and own placement |
| Current visual continuity | `application/object_tracking.py`: visible association and witnessed cursor transport |
| Current wish | `pet/mind/object_intentions.py`: whether Aiko currently wants or intends to investigate that portion |
| Attention and orientation | `application/object_behavior.py`: derive focus, admit observations and check learned places |
| Action phase and search | `application/object_interaction.py`: current episode, required feedback and enclosing SearchTask |
| Physical execution | `desktop/world_runtime.py` and the shared walk driver: movement, arrival and reach checks |
| Presentation | `ui/`: snapshots, sprites, controls and readable authored reactions |

Known, wanted, observed, missing and being investigated are different facts.
One does not substitute for another. World handles alone grant no subjective
identity. The same mutable PetState owns all need and friendship effects.

## Attention, noticing and identification

Free perception follows the rendered gaze, including walking direction or cursor
attention. Its ordinary near field is one body width, with forward visibility
up to the configured noticing range. It does not discover new items across the
whole taskbar.

A committed object interaction focuses on its subject from approach through
pickup, inspection, use or put-down and required feedback. Eating, petting,
conversation and other ongoing activities similarly exclude unrelated object
observations until their animation and complete dialogue sequence end. Sleep
and games exclude ambient object perception. Merely displaying or pinning the
idle toolbar is not a foreground action.

Unknown items can be noticed without learning their type. First identification
requires either actual inspection in Aiko's hand or continuous deliberate cursor
presentation before her face. Passing through the face region or being nearby
is insufficient. Durations and tolerances come from `data/balance.json`.

An identified portion can be recalled at its exact learned place through normal
perception or deliberate learned-place coverage. A different portion at that
place remains unknown, even if it has the same type. An unobserved move does not
update the remembered position or identify the new location.

If Aiko witnesses a known portion being picked up and follows its movement
continuously, knowledge follows that portion through cursor custody, release
and settling. It does not need identification again. A sensory interruption ends
tracking; it does not erase durable learned knowledge. A new offer gesture still
needs its own qualified presentation before offer assessment.

## Learned-place orientation and missing items

After an activity releases attention, Aiko deliberately looks left and right
before taking a new ordinary item goal. Start/restart, gesture completion and
new ordinary goals also request fresh coverage. Each side needs its own
continuous look. This covers already learned places across the taskbar without
revealing distant unknown items. No eligible learned places means no empty scan.

All eligible old places are checked before the initial missing-item feedback
seizes attention. Every confirmed missing known portion joins one SearchTask and
gets its own readable, named bubble before candidate investigation begins.
A continuing appetite wish cannot bypass that ordering.

A different occupant at an old learned place does not conceal the loss. The old
portion is missing and the replacement is unknown. There is no pending-occupant
exception that lets the replacement be investigated before the confirmed loss.
This check neither identifies the replacement nor reveals the old item's new
location. Fleeting unknown sightings may be retired without a learned-stock search.

## One search task, explicit action phases

SearchTask owns missing subjects and taskbar route coverage. It remains active
while a candidate goes through approach, pickup, inspection and put-down.
SearchPhase describes patrol movement, rather than the whole recovery task.

Aiko examines reachable unknown candidates through the ordinary hand-inspection
path during the search. Valid hand/face identification can reunite a missing
portion with its learned history and produce a grounded found bubble. During
this search, a newly identified portion of the same identity/kind can resolve
the oldest matching missing subject even when its physical instance differs.
Unknown or wrong-kind candidates cannot resolve it. Existing known stock is
excluded; a current observation is required, and each finding resolves at most
one subject. A newly confirmed loss can reopen a portion for a later search.

ObjectMemory transfers the missing subject's assessment and saved-for-later
intention, retires that subjective record and keeps the finding's actual World
reference, position and observation time. Ordinary stock recognition outside
a search remains strict. Existing memory v3 / outer save v1 fields suffice;
round-trip tests cover reference and source-association consistency.
Nonmatching candidates are safely put down or remain in player custody before
the same task continues. Unrelated appetite-driven consumption waits.

Further confirmed losses receive individual bubbles and join the same task;
they do not restart its route. Finding one subject does not reset the search for
the others. Actual endpoint coverage, completed local evidence and exhausted
eligible candidates allow a final unsuccessful-search reaction. Time alone or
one failed arrival does not manufacture confirmed absence or route completion.

## Hover, controls and busy replies

Passive hover may open the toolbar during search or inspection without changing
Aiko's activity or adding an incidental reaction. ContactCoordinator derives
action availability from existing activity owners. Care/game/feed buttons and
their callbacks, including stale menu callbacks, use that permission. Pin,
details and settings remain usable; wake and lifecycle termination retain their
existing explicit behavior.

A direct click can request a contextual busy bubble while the current action
continues. Optional contact speech does not block movement or phase progression.
Required missing/found/identification speech retains its priority and matching
completion receipt. Stale phase, aside and animation callbacks cannot acknowledge
a newer phase. There is no extra saved busy flag or second interaction owner.

## Custody, physics, consumption and persistence

Menu selection starts one player-held portion; it does not feed Aiko. A resting
item press carries the same instance. Only visible pixels of resting items accept
pickup input; moving items remain passive. Cancellation removes a new chooser
portion or returns an existing portion to safe source ground.

Release in the valid handover region may transfer an eligible unknown portion
for hand inspection. Previously identified explicit refusals remain effective.
Known approved offers use confirmation and full consumption playback. Unknown
ground finds retain inspection and decision, independent of current appetite.

Placement uses the intersection of item footprint, legal standing bounds and
ordinary reach at both scales. Falling and rebounds finish on reachable ground.
Acquisition is rechecked at the actual attachment frame; animation alone cannot
teleport a distant or moved item into Aiko's hand. Pickup is separate from
consumption. Safe interruption puts down an unconsumed held portion first.

ObjectCustody commits World/memory changes together. ObjectConsumption commits
canonical PetState, World and memory changes exactly once at consumption start,
with rollback and explicit autonomous/human origin. Autonomous use invents no
human care reward. Withholding applies only to a witnessed committed take and
uses its bounded, deduplicated social effects.

Outer save v1 contains World v1 and optional memory v3, with legacy memory v1/v2
readers. Learned facts survive restart; current observations, presentation clocks,
tracking and action receipts do not. Transient surviving portions recover safely
on ground without inventing witnessed positions. World consumption is not
simulated while closed. See [data and saves](DATA_AND_SAVES.md).
