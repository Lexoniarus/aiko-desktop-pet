# Persistent object knowledge and remembered supply retrieval

> **Historical record, archived 2026-10-18.** This delivery/review snapshot is
> completed or superseded and is not an active plan. Its old pending checks,
> future proposals and push/merge restrictions describe that revision only.
> Use the [current documentation](../README.md) and
> [current World rules](../WORLD_OBJECT_CONTRACTS.md) for maintained guidance.

Accepted: 16 October 2026. Baseline: `257a176` on `feature/world-foundation`.
Status: P0–P5 implemented and locally verified; native practical acceptance pending.
See the [current architecture](../ARCHITECTURE.md),
[World contracts](WORLD_OBJECT_CONTRACTS.md) and
[existing delivery ledger](WORLD_OBJECT_IMPLEMENTATION_PLAN.md).

The later [offer, placement and search plan](OBJECT_PLACEMENT_AND_SEARCH_PLAN.md)
records the implemented follow-up and pending combined practical acceptance.
It separates technical World IDs
from subjective reidentification, reconciles quantities and remembered places,
and adds visible bounded search. The delivery evidence below describes the
earlier instance-keyed memory implementation; the later plan records the current
subjective-record model and memory v2 conversion.

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
| P0 | Record this accepted plan and architecture link | `0ab36e0`; 9 documentation checks and pinned static gates; baseline 867 tests passed on Python 3.14 |
| P1 | Separate typed knowledge and snapshot values; retention, relocation and own-action facts | `1fcf742`; verification below |
| P2 | Coherent consumption and confirmed placement across owners | `cac4d24`; verification below |
| P3 | Versioned codec, joint save/restore and compatibility without fabricated sensing | `586c93b`; verification below |
| P4 | Preserve retrieval purpose, skip redundant inspection, contextual JSON dialogue | `6b615f3`; verification below |
| P5 | Restart regression, isolated practical starter and acceptance checklist | `b2168c5`; verification below |

P1 separates `ObjectKnowledge` from observations and introduces portable snapshot
values with relative active ages. Recognition survives absence and observed
relocation; conflicting recognition invalidates inspection/disposition. Unknown
sightings alone expire. Own-action records distinguish deferral and interruption.
Targeted object tests and all pinned static checks passed (168 source files).
Full Windows/Python 3.11 suite: 871 tests passed in 200.8 s.

P2 includes memory in the consumption transaction and rolls back World, Pet and
memory on injected failure. Acquisition and detach update own-action facts with
World checkpoints; failed events can retry, duplicate events cannot repeat
effects. Inspection is learned at its confirmed phase, deferral at detach,
independently of bubble/clip completion. Completion no longer invents observations.
Full Windows/Python 3.11 suite: 875 tests passed in 203.7 s; pinned Ruff,
strict Mypy (168 source files) and Pyright passed. P1 CI run
[38819187841](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/38819187841)
passed all three Linux/Windows jobs.

P3 adds strict `object_memory` version-one encoding in the same atomic save and
passes typed snapshots through session restoration and the desktop writer.
Relative active ages are reanchored; observations and sensory dwell start empty.
Current gaze/offer checks use actual observations, not the freshness of restored
knowledge. Legacy saves grant no knowledge; invalid/missing World drops paired
memory, invalid memory keeps valid Pet/World and requires an original backup.
Hidden movement/removal is not reconciled during load. Missing instance IDs can
be approached/searched without crashing. Codec, atomic-write interruption,
consumption-commit and held-recovery tests passed with all pinned static gates.
The desktop writer captures a single typed `WorldSessionSnapshot`; the composition
root remains within its existing architecture gate. Full Windows/Python 3.11
suite: 890 tests passed in 198.8 s; strict Mypy covers 169 source files. P2 CI
[38819674430](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/38819674430)
passed all three jobs.

P4 final Windows/Python 3.11 gate: 900 tests passed in 194.1 s; pinned Ruff,
strict Mypy (169 source files) and Pyright passed.

P4 preserves the consume purpose only for the same currently known, successfully
inspected instance. Its visible route uses three meaningful bubbles: need-based
recall, food/drink consumption and outcome. Confirmed deferral has distinct recall
copy; first inspection and handover keep their own routes. Pickup must finish
before consumption, whose clip must finish before the outcome. Changed needs
produce a readable refusal and put-down; conflicting evidence restores inquiry.
Attentive unsuccessful local search produces one missing reaction, without
confusing cancellation/busy state with observed absence. All copy stays in JSON.
The full gate exposed host-pointer-dependent notification fixtures (isolated
rerun passed). A controlled cursor-over-sprite reproduction deferred the note
with active hover controls and no object activity/memory. The fixtures now own
their pointer input and explicitly test hover deferral and release, preserving
the production notification gate. P3 CI
[38820660257](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/38820660257)
passed all three jobs.

## Acceptance evidence

P5 adds real desktop cold-restore cases at both edges and scales: actual inquiry
and placement, restart while unwanted, later energy-driven direct use, save during
consumption and another restart without ghost portions/knowledge. A missing saved
instance survives load until bounded local search confirms absence. A real-timer
food restore test checks readable recall and the entire consumption clip without
inspection. The isolated starter adds explicit `--needs` override for repeatable
later hunger while retaining the same World/memory; normal save paths stay blocked.
Repeated cold starts exposed character/item image caches left alive after quit,
allowing later worker-thread garbage collection to call Tk. The gate was stopped
to correct this lifetime gap: the existing lifecycle now closes the sprite owner,
which releases original/zoomed/warped images and the food overlay before destroying
Tk. A weak-reference regression proves immediate owner release with the app
still referenced, without forcing GC. World image cleanup retains its own owner.
The paired allocation counter also rejects old memories after a World reset,
backing them up without discarding valid Pet/World values. This checks technical
ID allocation only, never live object membership, identity or hidden positions.
The intermediate post-shutdown-fix full gate passed 906 tests in 210.8 s. Targeted
desktop component tests passed all 16 cases, including the four cold edge/scale
cases; the new real-timer food restore case passed in 12.4 s. The final gate also
includes the additional World-reset allocation-counter regression.

Separate-process launcher checks used one temporary save: a full restart retained
known deferred Onigiri, a later `--needs hungry` restart consumed it once with the
canonical food effect and unchanged friendship, and another default-launcher
Python 3.14 restart kept both portion and cognitive target absent. Python 3.11
handled the initial/known/hungry processes. No personal save was read or written.
These automated checks do not substitute for the user's visual/input acceptance.
Final Windows/Python 3.11 gate: 907 tests passed in 210.6 s; Ruff 0.13.2,
strict Mypy 1.18.2 (169 source files) and Pyright 1.1.414 passed. No background
Tk image-finalizer errors occurred after explicit image-owner shutdown. Existing
Tk theme-change diagnostics from probe teardown remain nonfatal.
P4 CI [38821588559](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/38821588559)
passed all three jobs. The implementation ends at `b2168c5`; current-head matrix
results are available in [PR checks](https://github.com/Lexoniarus/aiko-desktop-pet/pull/10/checks).
The PR stays draft and unmerged until the user's visual/input acceptance.

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
