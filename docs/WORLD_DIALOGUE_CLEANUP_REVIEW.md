# World and dialogue cleanup review

Reviewed against the completed dialogue-v2 implementation on
`feature/world-foundation`, including its previously uncommitted changes.
See [architecture](ARCHITECTURE.md), [resource/save ownership](DATA_AND_SAVES.md)
and [practical World checks](WORLD_SMOKE_TEST.md).

## Responsibilities and data

- World owns objective instances, custody, geometry and revisions. Perception
  owns current evidence; ObjectMemory owns learned facts and confirmed own
  actions. Their similar immutable values represent different knowledge and
  clock boundaries and are intentionally separate.
- ObjectIntentions chooses goals; ObjectInteractionCoordinator owns phases,
  interruption, identified animation effects and feedback receipts. ObjectCustody
  applies confirmed handover, pickup and placement to World and memory together,
  recovering both on failure. ObjectConsumption.commit applies canonical Pet,
  World and memory effects once at consumption start, before the visual clip ends.
- CursorItemGesture owns the current cursor portion, capture, pointer geometry,
  offer-preview identity and release/cancel handling. Its named ports leave
  appetite, interaction phases, movement and feedback selection with their owners.
  DesktopWorldRuntime connects those owners and retains the existing single mind
  tick and separate rendering/physics callback.
- DialogueBook filters and rotates immutable authored Lines. PetMind supplies
  current relationship/need facts; ReactionPlayer plays the selected beats.
  Embedded games share that session mind. Standalone games own a GameDialogue
  instance instead of sharing an import-time mutable dialogue book.
- Nutrition, German copy, visual metadata and tuning keep their existing JSON
  owners. Story quiet time/probability now come from validated balance keys,
  retaining 600 seconds and 0.2. Reading time comes from formatted text beats and
  the balance catalogue, without a second object-specific duration.
  Types, transition rules, supported semantic IDs and native scheduling constants
  remain Python responsibilities. Save format and offline progression are unchanged.

## Confirmed cleanup

Removed the write-only coordinator examined flag, the test-only begin_pickup
entry point, unused recovering context and three obsolete object event families
(nine unreachable authored entries). Inspection knowledge still has one owner.
The remaining catalogue has 1,019 entries including the original 48 stories.
Named selection_weight has no unused context arguments; default Line values use
Balance. The consumption method name distinguishes the effect commit from visual
completion. The former rock_paper_scissors_text_de module is replaced by the
responsibility-named rock_paper_scissors_dialogue module; callers use its owned
GameDialogue rather than unused score/round parameters or forwarding helpers.

## Test review

Tk component fixtures close animation/cache owners before destroying their root.
The original failure was reproduced with a retained image after teardown; the
corrected fixture releases it immediately. No forced collection, global GC
changes or broad worker suppression is used.

The complete edge/scale/placement matrix lives in the existing cold-retrieval
component test. Four identical standalone invocations were removed. The long
food/known-retrieval/new-drink real-time scenario now has one real-time inquiry;
post-consumption curiosity uses controlled application time and real component
wiring. Full-clipped remembered retrieval, handover, sleep interruption, real
left/right movement and readable bubbles retain native timer tests. Fast
perception, memory, codec, transaction and story tests cover different contracts.

The object placeholder regression previously supplied old-format text instead
of beats and could pass on the wrong validation failure. It now uses valid v2
structure and requires the placeholder error. Non-default reading time and
story cadence tests prove that JSON settings reach their actual consumers.
A failed handover checks joint recovery and safe retry alongside existing
pickup, put-down, stale-event and duplicate-effect coverage.

## Delivery evidence

Every source step ran Ruff 0.13.2, strict Mypy 1.18.2, Pyright 1.1.414 and the
complete Windows/Python 3.11 suite before its commit/push. Save tests use temporary
paths. The measured reduction describes these local runs, not a timing promise.

| Change | Commit | Full suite |
| --- | --- | --- |
| Image-owner fixture shutdown | `8cd7801` | 907 passed in 220.8 s on isolated original baseline |
| Preserve reviewed dialogue-v2 implementation | `9a3d011` | 926 passed in 222.2 s |
| Remove obsolete state, entry points and event families | `b6d97eb` | 926 passed in 222.1 s |
| JSON story pacing and effective template/readability regressions | `891ba22` | 927 passed in 220.2 s |
| Consolidate duplicate and long World tests | `8561629` | 924 passed in 192.7 s |
| Joint custody application service | `4fac271` | 925 passed in 193.7 s |
| Per-instance standalone game dialogue | `5d04cbb` | 925 passed in 191.9 s |
| Cursor gesture ownership and maintained architecture links | This revision | 925 tests; complete source/native gate before push |

[PR #10 checks](https://github.com/Lexoniarus/aiko-desktop-pet/pull/10/checks)
provide the Linux Python 3.11/3.13 and Windows matrix for the pushed head.
The PR remains draft and unmerged. Existing nonfatal ttk ThemeChanged diagnostics
from Tk probe teardown are separate from image finalizer/thread failures.
