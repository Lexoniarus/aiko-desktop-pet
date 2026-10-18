# Committed object attention and withholding corrections

> **Historical record, archived 2026-10-18.** This delivery/review snapshot is
> completed or superseded and is not an active plan. Its old pending checks,
> future proposals and push/merge restrictions describe that revision only.
> Use the [current documentation](../README.md) and
> [current World rules](../WORLD_OBJECT_CONTRACTS.md) for maintained guidance.

Accepted 2026-10-16; baseline `02ae098`. See [architecture](../ARCHITECTURE.md)
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

| Commit | Delivered behavior and targeted validation |
| --- | --- |
| `3ca01e4` | Accepted plan and architecture link; documentation only |
| `4b42c60` | Inherited reading-time CI failure corrected: 29 reaction/emote/follow-up/farewell tests, Ruff/Mypy/Pyright; configured timing preserved |
| `f025019` | Committed intentions across blockers: 7 intention and 11 interaction cases; changed native expectation checked separately; static checks |
| `abc5248` | Separate identified auxiliary receipts: 12 interaction and 4 presentation cases; static checks |
| `2968a35` | Selective perception/focus gaze: 30 awareness/tracking/native cases; static checks |
| `fc5f791` | Hover/click/other-gesture protection and authored wait copy: 47 interaction/catalogue/native cases; static checks |
| `daba031` | Observed successful target acquisition, stale grasp rejection: 49 focused cases; static checks |
| `e08e1bf` | Visible cursor tracking, settle/resume, genuine loss/search and actual handover origin: 43 focused cases plus extra retrieval cases; static checks. 31 native/runtime/origin cases also passed in 106.1 s |
| `f0d906c` | Pure withholding policy, validated JSON, authored copy and canonical state/mind mutations: 34 focused cases; static checks |
| `971a2b3` | Identified social effects, cooldown, return cue and saved friendship: 34 focused cases including isolated restart; static checks |
| `697eaed` | Shared movement still respects committed attention despite cursor/toolbar: 30 movement/native cases; static checks |
| `290a552` | CI correction: reset the two-scale fixture inside smaller desktops between scenarios; targeted native case and Ruff |
| `8480006` | Protect committed memory from unobserved-neighbour association: 28 awareness/memory/stock/tracking cases; static checks |
| `137b446` | Preserve assessment learned during a held offer when resuming original investigation: 29 interaction/retrieval cases; static checks |
| `4edbe49` | CI architecture correction: ordinary contact arbitration belongs to the desktop runtime; GUI stays within its existing composition-root guard. 40 architecture/input/interaction cases and static checks |

Static checks use Ruff 0.13.2, strict Mypy 1.18.2 and Pyright 1.1.414.
No complete local suite was run during these implementation steps. The final
combined regression and final CI are recorded below after completion.

CI monitoring found the inherited timing failure at `02ae098`, corrected in
`4b42c60`. Subsequent runs through `daba031` passed all three jobs. The new
two-scale fixture at `e08e1bf` exposed an out-of-bounds setup on smaller Linux and
Windows desktops; it was isolated to that fixture and corrected in `290a552`.
Older runs before that correction retain their historical failures.
After the fixture correction, CI exposed the existing 640-line GUI guard
(642 lines). `4edbe49` moves contact arbitration to the existing runtime owner;
the guard is unchanged. Final validation uses that corrected owner boundary.

## Final validation and handoff

Code commit `4edbe49` passed all three GitHub jobs in
[run 38968361032](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/38968361032):
Linux/Xvfb Python 3.11 and 3.13, plus Windows setup/desktop boundaries.

The first final local regression ran 986 tests in 218.553 s and found only that
already-corrected GUI guard. The corrected final tree passed **986 tests in
217.982 s** on Windows/Python 3.11. Ruff 0.13.2, strict Mypy 1.18.2 (178 source
files) and Pyright 1.1.414 pass. The handoff changes only documentation, owner
docstrings and layout of the same authored JSON records; no gameplay changes
follow this validation. The final documentation commit also receives PR CI.

The existing isolated starter created two portions under Python 3.14, closed
normally after 1.2 s, reopened the same temporary save and closed normally again.
The real save and existing user process were not modified. Automated native
component checks cover both scales, grab/cancel, gaze, hops, continuation,
friendship persistence and safe explicit interruption; existing real-timer flows
remain. No additional long timing test or duplicate edge matrix was added.

The updated [practical checklist](WORLD_SMOKE_TEST.md) is ready. Visual/input
acceptance by the user remains pending; draft PR #10 stays unmerged.
