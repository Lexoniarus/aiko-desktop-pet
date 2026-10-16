# Committed object attention and withholding corrections

Accepted 2026-10-16; baseline `02ae098`. See [architecture](ARCHITECTURE.md)
and the existing [placement/search plan](OBJECT_PLACEMENT_AND_SEARCH_PLAN.md).

## Contract

An accepted investigation commits attention to one subjective record until its
outcome. Other drops, relocations and cursor offers create no observations or
memory evidence during that commitment. Hover and ordinary clicks cannot cancel
it; clicks receive a bounded request to wait. Explicit care/game/sleep commands
retain safe interruption and put-down behavior.

Observed player acquisition of that exact item pauses approach/grasp before
ownership transfer. Follow the held item using existing cursor/gaze rendering,
then its visible fall/hops. Resume after resting, preserving the interaction and
acquired knowledge. Unrecognized items still require their original inspection.
Actual visual loss ends continuity and uses existing bounded subjective search;
World IDs alone never restore knowledge or reveal an unseen relocation.

Repeated/prolonged withholding produces spaced requests, temporary irritation
and bounded friendship loss after a grace period. Initial repositioning is free.
Apply loss once per escalation with an episode cap and a cross-episode cooldown;
returning an item creates no friendship bonus. Normal accepted human feeding
retains its existing care rules. Persist friendship through the existing save;
do not persist running attention/waiting episodes.

## Owners and states

- `ObjectInteractionCoordinator`: committed record, phases, identified feedback,
  resumption, pending ordinary-contact acknowledgement; no duplicate goal store.
- `ObjectAwareness`/`ObjectTracker`: selective sensory evidence and observed
  continuity. Existing `ObjectIntentions` retains committed goals while paused.
- `DesktopWorldRuntime`/`CursorItemGesture`: native input, successful observed
  acquisition, visible pointer positions, gaze routing and active-time updates.
- Existing feedback presenter/player: one speech surface, phase completion
  distinct from auxiliary feedback; stale receipts cannot advance phases.
- Pet domain: pure withholding/friendship policy, `PetMind` irritation,
  `PetState` sole friendship mutation. Validated `balance.json` owns tuning;
  `dialogues.de.json` owns German lines/emotes. Preserve baseline timing changes.
- Existing World custody states suffice. Add interaction `await_return` and
  `await_settle`; never reserve physical ownership merely because Aiko wants it.

## Small delivery steps

Each row is a separate commit, split further when necessary for a green change.

| Step | Delivery | Focused evidence |
| --- | --- | --- |
| 0 | Record plan; repair inherited CI timing assumption separately | Reaction playback |
| 1 | Committed focus lifecycle and planner hold distinct from cancellation | Interaction/intention policies |
| 2 | Auxiliary feedback without cancelling or completing phase feedback | Presenter/player callbacks |
| 3 | Filter other sensory changes and keep focused gaze | Awareness/tracking |
| 4 | Hover/click/other cursor gestures respect commitment | Desktop input/contact |
| 5 | Observed target acquisition pauses safely | Revision/frame-4 races |
| 6 | Follow, settle and resume; knowledge and actual care origin preserved | Held/falling/resting, identical items, visual loss |
| 7 | Spaced requests, irritation and bounded friendship consequences | Pure clock-driven policy, state, catalogue |
| 8 | Remove superseded expectations; document and hand off practical checks | Final regression and CI |

## Validation and practical acceptance

During development run targeted tests plus Ruff, strict Mypy and Pyright. Push
small commits and inspect preceding GitHub CI; stop feature work and correct red
runs. Run the complete local suite only at the end, then await final CI. Keep PR
#10 unmerged. Never use the real save or change artwork.

Practical checks at 1x/2x: distract with drops/other offers/hover/clicks; take the
target before grasp, hold/move/return it through hops, repeat withholding, inspect
unknown versus retrieve known items, lose actual visual contact, and explicitly
request sleep/play during held custody. Verify bubbles, gaze, anger/friendship,
normal behavior after completion, safe put-down and restart with durable knowledge
but no resumed waiting episode. Automated checks do not imply human acceptance.

## Delivery ledger

Implementation commits and evidence are recorded here as delivery progresses.
