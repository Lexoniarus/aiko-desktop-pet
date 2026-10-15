# Persistent object knowledge and remembered supply retrieval

Accepted: 16 October 2026. Baseline: `257a176` on `feature/world-foundation`.
See the [current architecture](ARCHITECTURE.md),
[World contracts](WORLD_OBJECT_CONTRACTS.md) and
[existing delivery ledger](WORLD_OBJECT_IMPLEMENTATION_PLAN.md).

## Contract and ownership

World owns actual portions, positions and custody. `ObjectPerception` produces
current subjective observations. `ObjectMemory` owns learned identity, last
known location, successful inspection and confirmed own placement. A known
identity is distinct from a completed inspection and from an intentional
decision to keep a portion for later. Merely observing a relocation does not
erase learned identity or a successful inspection of the same instance.
Contradictory observed identity invalidates inspection and prior disposition.

Recognized knowledge remains until consumption or confirmed local absence.
Unidentified sightings expire after 600 active seconds without observation.
Unseen movement/removal never refreshes knowledge from World truth. The last
known location is a hypothesis; unsuccessful attentive local search invalidates
it. Closed time provides neither observations nor active memory aging.

Typed domain values and owner methods implement these rules. Packaged JSON
continues to own tuning and authored German text. An optional, separately
versioned `object_memory` section in the existing version-one save stores learned
facts and relative active ages alongside Pet and World in one atomic write.
Never persist raw session clocks, current visibility, sensory evidence, active
goals, animations or dialogue receipts. Old saves start with empty knowledge.
Invalid memory is backed up independently while valid Pet/World data survives;
missing/invalid World prevents attaching old instance memories to a new World.
Restoration does not join saved knowledge to authoritative current objects.

Application transactions update consumption in World, Pet and memory before any
save; failures restore all owners. Own placement is learned at confirmed detach,
with deliberate deferral distinguished from interruption. Recovery of a held or
falling portion never invents a subjective observation of its normalized pose.

## Behavior

New or unexamined portion: notice, approach, pickup, inspect/recognize, decide,
consume or put down. Remembered and successfully inspected supply: current need,
truthful recall bubble, approach, pickup, revalidation, full consumption animation.
The second route omits repeated visible inspection, recognition and desire cues.
Grasp still changes custody at source frame 4; nutrition still starts only on
consumption. Changed needs safely lead to put-down; missing targets use bounded
local search. Handover retains its separate entry, acceptance and care origin.
Restored unwanted supplies do not steal normal cursor attention or trigger
repeated inspection. Existing approach pacing remains a separate follow-up.

## Delivery steps

Each implementation step is a focused commit, with behavior tests, Ruff 0.13.2,
strict Mypy 1.18.2, Pyright 1.1.414 and the full unit/GUI suite before push.
Keep the existing draft PR unmerged until practical acceptance.

| Step | Reviewable result | Commit / verification |
| --- | --- | --- |
| P0 | Record this accepted plan and architecture link | This document's initial commit; baseline checks |
| P1 | Separate typed knowledge and snapshot values; retention, relocation and own-action facts | Pending |
| P2 | Coherent consumption and confirmed placement across owners | Pending |
| P3 | Versioned codec, joint save/restore and compatibility without fabricated sensing | Pending |
| P4 | Preserve retrieval purpose, skip redundant inspection, contextual JSON dialogue | Pending |
| P5 | Restart regression, isolated practical starter and acceptance checklist | Pending |

## Acceptance evidence

- New, recognized-but-unexamined and examined portions follow distinct routes.
- Known unwanted supply survives restart and lets normal interactions continue;
  a later need triggers recall and direct retrieval with the full eat clip.
- No hidden movement/removal updates knowledge, including across restart;
  observed relocation preserves learned facts and local absence clears a target.
- Fleeting sightings age by active time; known stock survives ten minutes and
  offline time. Restore has no current visibility or sensory dwell credit.
- Saves before/after grasp, inspection, detach and consumption are consistent;
  duplicate events and injected failures cannot duplicate effects or leave a
  consumed portion in durable memory.
- Legacy/corrupt/future sections preserve valid progress and original backups;
  replacement World never reuses old cognitive instance bindings.
- Handover rewards, autonomous origin, interruptions, cursor gaze and both edges
  at 1x/2x remain covered. Native user acceptance is recorded separately from
  automated tests; the real save remains untouched.
