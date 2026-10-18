# Object orientation and observed continuity plan

Recorded: 18 October 2026. Status: **Stages 1-5 implemented and automatically
verified. Human practical acceptance remains open. No merge authorized.**
Baseline: `feature/world-foundation`, HEAD `fb4f357`, including the existing local changes.

Subsequent practical feedback: the user reports that the core behavior matches
expectations, with occasional pre-approach pauses. The
[ownership cleanup](OBJECT_BEHAVIOR_CLEANUP_PLAN.md) preserves that behavior and
its timing. The original delivery evidence and remaining boundary checklist below
are retained; this feedback does not claim every checklist case was tested.

This plan follows the [architecture](ARCHITECTURE.md),
[contribution rules](../CONTRIBUTING.md), and
[development workflow](GITHUB_WORKFLOW.md). Technical documentation, identifiers,
and commit messages are English. Authored runtime dialogue remains German.

The change is a clearer decision order and better evidence handling, not a
collapse of distinct object states. After a committed activity, Aiko deliberately
looks left and right to check remembered places across the taskbar. Confirmed
losses and the ongoing search take precedence over ordinary novelty. A witnessed
relocation preserves learned identity whether or not Aiko currently wants the item.

This implementation supersedes the local-only post-action checks
in the [shared focus plan](SHARED_INTERACTION_FOCUS_PLAN.md) and
[earlier perception plan](ATTENTION_PERCEPTION_SIMPLIFICATION_PLAN.md).
Their exclusive interaction focus remains required. Historical green results
describe the old implementation, not acceptance of this new behavior.

## Independent state dimensions to preserve

These dimensions compose; they must not become one combined enum such as
"known and wanted", or several independently writable focus flags.

| Dimension | Existing source and owner | Required distinction |
| --- | --- | --- |
| Learned identity | [ObjectKnowledge.recognized](../aiko_pet/pet/mind/object_knowledge.py), owned by [ObjectMemory](../aiko_pet/pet/mind/object_memory.py) | Identified versus unidentified. Identity persists across absence, lack of appetite, and loss of the current execution binding. An observation with no new identity does not erase learned knowledge. |
| Previous appraisal | `assessed` and `disposition` on the memory record | Already appraised versus not yet appraised; deliberately deferred versus interrupted. Neither means "wanted now". An identified but unassessed item needs appraisal, not identification again. Both it and an unknown item can have goal purpose `investigate`; that purpose alone cannot classify identity. |
| Current wish | [ObjectUseDecision.consume and ObjectUseContext](../aiko_pet/pet/mind/object_decisions.py), [ObjectIntentions.goal](../aiko_pet/pet/mind/object_intentions.py) | Wanted versus not wanted now. Supply thresholds, explicit offers, and a continuing wish remain distinct. Recheck capacity when needed without forgetting identity or changing another goal. Unknown identity is not the same reason as a recognized refusal. |
| Place association | Remembered coordinates, `at_place`, and qualified Awareness execution bindings | Remembered place versus a currently supported association. A missing current binding proves neither forgetting nor an empty place. A known item elsewhere cannot be rebound from a hidden World handle. |
| Observed movement | [ObjectTracker](../aiko_pet/application/object_tracking.py), qualified by [ObjectAwareness.follow_taken](../aiko_pet/application/object_awareness.py) | Witnessed transport versus unobserved relocation or actual sensory loss. Following the cursor visually is not itself an item track. Tracking does not imply appetite or ownership. |
| Committed interaction | [InteractionEpisode and typed phases](../aiko_pet/application/object_interaction_state.py), owned by [ObjectInteractionCoordinator](../aiko_pet/application/object_interaction.py) | An exclusive chosen subject across approach, pickup, inspection, use, return, and put-down. This is execution commitment, not a second wish or knowledge store. |
| Confirmed absence | `place_status == "missing"`, established by [ObjectAbsencePerception](../aiko_pet/pet/mind/object_absence.py) | Confirmed empty remembered place versus an unchecked or occupied place. Missing does not erase identity, and does not depend on wanting to consume the item. |
| Search lifetime | `SearchTask`, `search_active`, `searching`, and `search_ready` | One ongoing recovery task can survive several candidate interactions. `search_active` remains true while the phase is approach/inspect; `searching` describes patrol phase only. These properties are not interchangeable. |
| Candidate versus ordinary novelty | Current observations, `ObjectGoal.purpose`, and the enclosing search task | A search may detect and inspect an unknown candidate. It must not turn that candidate into an unrelated ordinary "new object" goal or abandon the missing subjects. |
| Physical custody and feedback | World state; playback events; `FeedbackKey` and matching receipts | Seeing, wanting, holding, consuming, and finishing a readable cue are separate facts. A bubble grants neither custody nor nutrition. |

Simplification removes duplicated decisions, invalid fixtures, and proven dead
branches. It does not remove these distinctions or turn every distinction into
another persisted flag.

## Required decision order

```text
finish the committed activity or continue its own observed transport
  -> check learned places on the left
  -> check learned places on the right
  -> submit every confirmed loss to the existing shared search task
  -> present one readable loss bubble per portion
  -> resume search, or select an ordinary goal if no search remains
  -> investigate or use the permitted subject
  -> reorient when the activity has finished
```

1. **Exclusive activity:** Approach to a chosen item, pickup, inspection, eating,
   put-down, play, petting, and conversation exclude unrelated environmental
   evidence. Completion includes the actual animation and whole feedback sequence.
   Observing the current subject, its return, and its own feedback remains allowed.
2. **Deliberate orientation:** Orient after activity release, on start/restart,
   and before binding a new ordinary item goal when a fresh check is required.
   Do not restart orientation every idle tick or interrupt a tracked transport.
   With no eligible learned places, the check completes immediately.
3. **Different sensory scopes:** Ordinary unknown-item discovery keeps its local
   near field and directed notice range. Deliberate checks of learned places
   cover the whole taskbar through left/right gaze, without walking to each place
   or asking the user to move the cursor. This grants no global unknown-item
   identification and no access to an unseen relocated item's new position.
4. **Fresh loss evidence:** Check a learned portion at its exact remembered place.
   A genuinely empty place still requires fresh uninterrupted evidence; retain
   the existing 0.5-second duration initially. Time spent in another focus cannot
   count toward it. Own custody and out-of-World places cannot generate floor loss.
5. **Complete the check before choosing:** Accumulate confirmed facts at the
   existing Awareness owner while both sides are checked. The first loss cue
   must not replace orientation with an exclusive item episode halfway through.
   Then hand all confirmed portions to the existing search task and receipt queue.
6. **Search precedes ordinary novelty:** Raw local sightings may be retained.
   They are search candidates, not ordinary foreign-object announcements or new
   free curiosity goals while recovery is active. After orientation and loss
   feedback, search may pick up or accept deliberate presentation of a candidate
   to identify it and resolve the appropriate missing portion. A nonmatching
   candidate is safely put down and the same route resumes. Satisfied appetite
   must not cancel that task. Search completes on verified recovery or actual
   coverage of the bounded route, not merely because a candidate was inspected.
   Route exhaustion does not erase unresolved learned missing records.
7. **No identification during the initial check:** Do not start an unknown
   hand/face examination before orientation finishes. A new presentation can wait;
   a previously committed own handover/return phase can finish. Avoid accumulating
   recognition evidence behind this gate and emitting it on the first free tick.
8. **Observed relocation:** If Aiko witnesses taking a known portion at the learned
   place and follows its transport, keep the same learned record through holding,
   dragging, release, motion, and settling. Update the remembered resting place
   from the observed sequence. No missing, ordinary notice, reinspection, or
   `object_recognized` loop is needed, regardless of current desire. Feedback
   about that same tracked item must not break continuity.
9. **Unobserved relocation:** Retain the old learned place until permitted
   perception supplies new evidence. Confirm an empty old place during orientation
   before ordinary new identification starts. Learned identity remains stored;
   associating a new location requires a valid observed path or hand/face evidence.
   "Not missing" alone is not proof of that association.

Updated by the user's replacement-rule correction in the
[ownership cleanup follow-up](OBJECT_BEHAVIOR_CLEANUP_PLAN.md): an unidentified
replacement does not conceal the learned portion's absence. Complete the place
checks and announce each confirmed loss before investigating the replacement.
A different same-type portion must not silently inherit the old identity.

Sleep, play, or an explicit new activity may interrupt orientation. Restart its
fresh evidence after release. An item moved again after its side was checked
needs later evidence; orientation is a visible sequence, not an atomic World poll.

## Baseline code and OOP audit

This audit describes the starting snapshot at `fb4f357` plus the then-local work.
The delivery ledger below records the implemented corrections and current status.

| Baseline code | Verified baseline behavior or gap | Implementation target and preserved boundary |
| --- | --- | --- |
| [choose_object_attention](../aiko_pet/application/object_behavior.py) and [ObjectAttention](../aiko_pet/pet/mind/object_attention.py) | Object phases win over free movement, but release returns directly to free gaze. New sightings and empty known places share the same bounded spatial test. | Add explicit orientation precedence and separate learned-place coverage from local discovery. Keep sleeping/game and exclusive-item priorities. The identical `pick_up` dispatch branch can be removed without removing its phase. |
| [ObjectBehaviorCoordinator.observe](../aiko_pet/application/object_behavior.py) | Repeated `checking_absence`/`absences` conditions delay goals. The first accepted loss immediately changes the interaction phase; no full left/right barrier exists. | Own one orientation progress value and one decision gate for dispatch. Keep sensory pending evidence separate from accepted facts and readable feedback. Do not implement the same gate in Intentions, UI, and SearchTask independently. |
| [ObjectIntentions.choose](../aiko_pet/pet/mind/object_intentions.py) | A committed goal is retained before generic blocking. A valid `CONTINUING_WISH` can also be returned before that blocking branch. Other blocked selection can cancel a goal. | Gate execution and classification centrally, including continuing wishes; do not accidentally cancel a legitimate wish to pause orientation, or assume `blocked=True` alone handles all goals. Preserve context-specific need/capacity checks. |
| [ObjectAwareness.update and follow_taken](../aiko_pet/application/object_awareness.py) | Item focus restricts candidates. Acquisition requires a current binding and completed observation; after a look away these can be absent even when learned memory remains. | Qualify an actual acquisition event at the exact learned place before World mutation, including between-tick acquisition. Retain focused-neighbor exclusion and no handle-only recovery after real sensory loss. |
| [DesktopWorldRuntime.update and begin_relocate](../aiko_pet/desktop/world_runtime.py) | Attention is sampled before Awareness; the gaze target is written afterward. Offer observation occurs between behavior observation and motion. | Prepare orientation before sampling and use one immutable decision for gaze and sensing. Recheck execution eligibility at the relevant boundary; preserve same-tick offer effects and existing acquisition validation. |
| [ObjectFeedbackPresenter](../aiko_pet/ui/pet_view/object_feedback_presenter.py), [ReactionPlayer](../aiko_pet/ui/pet_view/reaction_player.py), and [GUI activity port](../aiko_pet/gui.py) | `ObjectFeedback` has a record/key, but general activity is reduced to playback deadline, sequence timer, or bubble presence. An idle-phase offer cue has no retained readable subject scope at that port. | Let the existing presentation owner expose the live cue's subject and valid lifecycle. Only feedback for the already tracked subject may continue its tracking. A stale offer marker must not exempt a later unrelated action. |
| [ObjectTracker](../aiko_pet/application/object_tracking.py) and [ObjectMemory](../aiko_pet/pet/mind/object_memory.py) | The tracker owns transient continuity; memory owns identity, appraisal, and remembered place. Empty input drops the track, not learned identity. | Keep both responsibilities. Do not fix a lost track by forgetting learned memory or globally rebinding from `instance_id`. |
| [ObjectInteractionCoordinator](../aiko_pet/application/object_interaction.py) and [SearchTask](../aiko_pet/application/object_interaction_state.py) | Search task, current candidate episode, and queued loss receipts already have separate lifetimes. Candidate selection uses `begin_goal`, whose unrecognized case currently emits ordinary `object_notice`. | Keep the single search, episode, and queue. Use enclosing search context to select candidate feedback and priority, without inventing another curiosity queue or parallel search phase machine. |
| [ObjectAbsencePerception](../aiko_pet/pet/mind/object_absence.py) and [object_stock](../aiko_pet/pet/mind/object_stock.py) | Continuous evidence, unknown-place occupancy, same-type ambiguity, and evidence-order reconciliation remain independent mechanisms. | The later replacement correction removes unknown occupancy as protection for an absent learned portion. Preserve unknown-place presence evidence and reconciliation. |
| [DesktopVisualObservation](../aiko_pet/desktop/visual_observation.py), [WorldRuntimeAccess](../aiko_pet/desktop/world_access.py), and [object status](../aiko_pet/application/object_status.py) | Geometry, late-bound reads, and diagnostics are already separate from mutable domain owners. | Reuse these ports for gaze; preserve read-only status counts. The status box must never trigger orientation, identification, or hidden reconciliation. |

### Previously reproduced continuity failures

The preceding read-only investigation used native components and temporary saves:

- **Free cursor, no bubble:** Learned Cookie memory survived a look away, but
  current bindings did not. Between-tick acquisition failed to start an item track.
  A later location became unidentified `memory_2`; the old record still existed,
  and missing remained zero.
- **Own offer feedback:** A tracked known Cookie remained associated until its
  own `object_refuse` cue caused general `unavailable` attention. The next update
  dropped the track; the old record stayed non-resting and the new place became
  unidentified.
- **Control:** A longer drag without presentation retained record and identity
  through the complete physical settling sequence.

These reproduce particular gaps, not every detail of the user's live session.
They need focused regressions in their owning implementation commits.

### Orientation ownership

The existing behavior coordinator owns one transient typed progress value.
`application/object_orientation.py` holds its data and pure transitions. It stores
only the current side and uninterrupted-dwell timestamps; coverage and readiness
are derived, without parallel active/pending/done flags. No new coordinator,
timer, movement writer, saved schema, or substitute Item/SearchTask state machine.

The same sampled decision must control the visible gaze and evidence admission.
Do not infer a completed look from a request to render a frame, or from elapsed
time while a different action was displayed. Subject-scoped presentation metadata
belongs to the existing presenter/player lifecycle, not to a second GUI focus store.

### Existing state that must not be removed as duplication

- `ObjectKnowledge`, `ObjectGoal`, and `InteractionEpisode` carry some similarly
  named identity fields. They serve learned knowledge, a selected goal, and an
  episode/feedback snapshot respectively. Field-name overlap alone does not
  justify removing them or allowing the episode to mutate learned identity.
- `Awareness._absences` contains confirmed facts not yet acknowledged by the
  application; `_missing_feedback` contains accepted search losses awaiting
  presentation. Keep the handoff and acknowledgement rather than merging them
  into a second unowned list.
- `SearchTask._missing` owns unresolved recovery subjects and its route. It is
  not interchangeable with a fresh query of every Memory record marked missing,
  which would lose task progress and candidate exclusions.
- `focus_record`, `inspection_record`, `searching`, and `search_active` are
  derived views or views of different lifetimes, not four redundant stored modes.
  Offer appraisal during a readable cue and a later capacity recheck are also
  separate, as the existing retrieval tests demonstrate.

## Test audit and reachability decisions

A passing isolated input combination is not proof of a reachable desktop state.
Conversely, a low-level safety test is not redundant just because it bypasses the
GUI. Classify the exact setup, asserted contract, production entry, and replacement
proof before deleting a test or its guarded production branch.

| Existing test or setup | Code and reachability assessment | Required action |
| --- | --- | --- |
| [test_object_absence](../tests/test_object_absence.py): `test_unidentified_place_stays_within_local_notice_range` | The original shared-range test actually used an unidentified `PLACE` fixture. Its local-range assertion remains valid; its old general name overstated the contract. | Renamed in Stage 1 and retained. New explicit learned-place cases in `test_object_orientation_awareness` cover distant checking separately. |
| Same module: `test_hidden_boundary_missing_and_own_custody_places_supply_no_loss` | Its far-place fixture is also unidentified, so that exclusion remains valid alongside custody, bounds, and already-missing checks. | Retain these assertions; do not turn an unknown sighting into globally checkable knowledge to satisfy the new learned-place rule. |
| [test_object_awareness](../tests/test_object_awareness.py): `test_close_learned_pair_survives_restart_and_repeated_focus_changes` | Fresh instrumentation observed 120 calls combining non-null `committed` with `survey`. Live committed item attention is `object`, or unavailable under an overriding activity. The focused candidate filter is not exercised. | Replace the unreachable production-context combination with inputs derived from the common attention policy. Keep restart, close/coincident pairs, and distinct same-type portions. |
| Same module: `test_focused_empty_place_waits_for_unnoticed_occupant` | Fresh instrumentation observed the same mismatch on three committed calls. | Repair the fixture and name/claims as needed; preserve occupied-place protection without declaring this free-survey setup a valid focused path. |
| [test_object_behavior](../tests/test_object_behavior.py): `test_changed_approach_finishes_old_episode_before_new_notice` | Directly injects a different goal into `advance` while an approach is active, bypassing committed Intentions selection. The live runtime normally passes `observe(...).goal`. Synchronous offer effects also exist between the two calls. | Removed in Stage 4a after auditing all production callers. DesktopWorldRuntime passes the immutable observation goal; synchronous offer appraisal rejects approach, and presentation cannot replace its episode. Committed Intentions returns only the same subject. Native no-hijack and pair/restart coverage remains. |
| Awareness: `test_unseen_relocation_is_a_new_find_and_both_discovery_orders_reconcile` | The ordinary "identify first, inspect old places later" ordering is no longer the desired behavior. This is not proof all low-level reversed fact orders are impossible. | Rewrite the regular flow as orientation, confirmed loss, search candidate, permitted identification, reunion. Keep low-level order tolerance only where a reachable protected boundary requires it. |
| [test_object_memory](../tests/test_object_memory.py): `test_found_before_or_after_missing_resolves_one_old_place` | Memory is an evidence consumer; occupied unresolved places, an already committed examination, or supported recovery can yield different fact order. | Retain until a caller/recovery audit proves a branch unnecessary. Do not weaken same-type ambiguity or erase learned experience to shorten the suite. |
| Awareness: `test_ground_focus_excludes_neighbours_and_their_cursor_take`, `test_hand_focus_defers_unrelated_sightings_and_losses_to_a_fresh_look` | Distinct floor-focus and hand-focus boundaries remain reachable. | Preserve both; update the post-release part to the explicit orientation sequence. |
| [test_object_intentions](../tests/test_object_intentions.py): `test_offer_wish_survives_observed_drop_but_rechecks_capacity_and_identity`, `test_commitment_survives_blocking_carry_and_more_attractive_find` | Protect current wish, context thresholds, and commitment independently of identity. | Preserve; ensure the orientation execution gate does not cancel the wish or let its early-return path bypass the check. |
| Same module: `test_satiated_food_is_investigated_once_then_reconsidered_when_hungry`; [test_object_retrieval](../tests/test_object_retrieval.py): `test_known_but_unassessed_item_decides_without_identifying_again` | Appraisal, appetite, and identification are demonstrably different states. | Preserve. Do not merge them into a "known/wanted" state or reidentify an already known portion. |
| Behavior: `test_satisfied_need_does_not_abort_an_ongoing_missing_item_search`, `test_search_investigates_unknown_find_and_resumes_its_route`, `test_other_same_type_portion_cannot_end_physical_subject_search` | Active recovery is independent of appetite and survives candidate phases. | Preserve all three contracts; add assertions that candidate feedback is search-related and cannot start ordinary novelty or reset the route. |
| Behavior: `test_fresh_place_check_keeps_its_look_before_turning_to_a_new_find`, `test_place_check_precedes_a_continuing_consumption_wish` | Valid priorities, but current coverage is local. | Share setup and replace local waiting with complete orientation; retain both distinct assertions. |
| Behavior: `test_endpoint_waits_for_local_evidence_and_collects_another_loss` | A loss already detectable before patrol now belongs to initial orientation. A genuinely later loss during patrol remains reachable. | Move the former proof into orientation coverage; retain the latter with an actual post-start change. |
| Behavior: formerly `test_unclear_occupied_place_does_not_block_other_loss_or_investigation` | Its learned-place occupancy assumption was rejected by the user in the later replacement correction. | Replaced by `test_replacement_waits_for_both_missing_bubbles_before_investigation`: both learned losses are reported before approaching the unknown replacement. |
| [test_world_gui](../tests/test_world_gui.py): shared relocated-portion search at scale one/two | Current old places initially fit the near field; that does not prove whole-taskbar orientation. | Extend the existing main scenario to both sides and distant places. Do not keep a duplicate scenario solely for its convenient old near-field arrangement. |
| Same module: `test_absent_remembered_instance_requires_deliberate_place_check` | Correct confirmed-loss/restart boundary with an outdated local-only assumption. | Rename/adapt to deliberate remembered-place checks; preserve bounded search and no search from a missing handle alone. |
| Same module: fast observed cursor relocation at scale one/two | Valid fast path misses between-tick reacquisition after a look away, longer drag, and own-feedback interruption. | Extend a shared helper with these concrete paths and real release/settling. Cover wanted and unwanted known portions without multiplying every unrelated state combination. |
| Same module: petting/conversation focus; [test_world_runtime_flow](../tests/test_world_runtime_flow.py): `test_conversation_focus_ends_only_after_native_sequence_completion` | Fast component checks and real sequence timers verify different boundaries. | Keep both layers. Assert actual release, visible left/right orientation, then losses before ordinary new identification. |
| Retrieval: `test_restored_conflicting_knowledge_requires_hand_inspection`; [test_object_consumption](../tests/test_object_consumption.py): `test_place_hypothesis_cannot_consume_a_different_catalog_item` | Reachable saved-data conflict and consumption safety boundaries; not pet-hand teleport fixtures. | Preserve both guards and tests. |
| [Tracking](../tests/test_object_tracking.py), [persistence](../tests/test_object_memory_persistence.py), [status](../tests/test_object_status.py), World/physics/receipt tests | Real sensory gaps, independent custody, recovery, projection purity, and stale callbacks remain valid. | Preserve; delete only a specifically proven duplicate assertion after its replacement proof is named. |

The old R1–R3 teleport/forced-binding tests and `_replace_recalled_portion`
helper were already removed in the earlier plan. They are not new removal work.
Physics does not eliminate legitimate release-to-hand acquisition.

The implementation removed the audited injected goal-switch test and its fallback,
and the ordinary identify-before-orientation permutation from Awareness. It repaired
focus contexts rather than deleting their safety assertions. Low-level Memory
evidence-order tolerance remains, because already committed examinations and
deferred preinspection loss receipts can supply that order legitimately.

## Acceptance cases that protect the state distinctions

| Case | Required behavior |
| --- | --- |
| Known and wanted, observed relocation | Preserve identity and update place; a valid continuing wish may resume after required orientation and capacity recheck. No second identification. |
| Known and unwanted, observed relocation | Preserve identity and update place; no consumption pursuit, loss, or reinspection merely because it moved. |
| Known and wanted, unobserved relocation | Retain old memory; orient, announce confirmed loss, recover before ordinary novelty. Existing wish cannot bypass the check. |
| Known and unwanted, unobserved relocation | The same confirmed-loss recovery occurs even though consumption is not wanted. |
| Identified but not appraised | Appraise without claiming a new identification. |
| Unknown item, no missing subjects | After the required check, ordinary curiosity may inspect it; use is decided only after identification. |
| Unknown candidate during recovery | Detect and inspect only as part of the active search; matching evidence resolves one appropriate subject, nonmatching evidence resumes the same route. |
| Another known item moves during exclusive interaction | No borrowed observation or position update; after release, check all old places before ordinary novelty. |
| Actual sensory gap or occupied old place | No fabricated transport continuity or false empty-place fact; retain learned knowledge and use permitted later evidence. |
| Multiple same-type portions after restart | Preserve distinct physical subjects, one readable loss per confirmed portion, and one shared bounded route. |

## Small commits and targeted verification

Local implementation commits are part of the workflow. The previous blanket
"no commits" restriction is withdrawn for the planned implementation; **no merge**
remains. Implementation is now authorized. The ledger separates new orientation
work from the previously approved but uncommitted prerequisites.

Preserve the current dirty baseline. Before committing, account for required
pre-existing changes and untracked modules; do not mix all pending work into a
single snapshot or discard it. Stage only the relevant complete files or hunks,
review `git diff --cached`, and verify that the commit includes its dependencies.
Tests on a dirty working tree must not be reported as isolated commit verification
if they depended on unrelated uncommitted files.

Each behavior change and its corrected regression test belong in the same small
commit. Do not postpone broken expectations until a later cleanup commit.
After focused tests, run the pinned Ruff, strict Mypy, and Pyright gates for each
implementation commit, as required by the existing OOP workflow. Record results
before continuing. Existing CI must be green for each pushed commit; push only
within the authorized branch workflow. Run the full regression at completion,
rather than replacing focused development checks with repeated full local runs.

| Stage and commit | Reviewable change | Focused verification before commit |
| --- | --- | --- |
| P0 `docs: define orientation and independent object states` | Finalize this plan, baseline, protected contracts, test audit, and ledger. Planning only. | Document references, named test existence, diff review; no production diff. |
| 1a `refactor: separate learned place coverage from item discovery` | Split qualified learned-place coverage from local discovery at the attention/absence boundary, preserving existing defaults until wired. | `test_object_attention`, `test_object_absence`, affected Awareness cases, architecture boundaries. |
| 1b `refactor: model deliberate orientation progress` | Add the single transient orientation value and pure transitions, including empty memory, interruption, and both-side completion. | Pure transition tests plus attention and typed-port checks; no claims of native integration yet. |
| 2a `fix: preserve known identity on witnessed between-tick pickup` | Qualify the acquisition event before mutation; reuse learned exact-place evidence without handle-only recognition. | Focused Awareness/Tracking/Memory tests and native fast-take regression; known wanted/unwanted, unknown replacement, and genuine gaps. |
| 2b `fix: keep tracked item continuity during its own feedback` | Scope live item feedback by subject/lifecycle through existing presentation ownership. | Reaction/feedback lifecycle, own versus unrelated bubble, stale completion, longer drag and full settling, both scales. |
| 3a `feat: check remembered places before free item actions` | Wire visible left/right progress before attention sampling and block ordinary action execution/recognition until completion. Retain legitimate wishes while paused. | Focused behavior, Intentions, adapter, World-access, and native post-activity cases; explicitly test the continuing-wish early return. |
| 3b `fix: retain missing-item search priority over ordinary novelty` | Batch confirmed losses after both sides, preserve individual receipts, and classify unknown investigations under the enclosing search task. | Multi-loss, unknown candidate, matching/nonmatching portions, unwanted missing stock, later losses, route resumption, and real readable timer checks. |
| 4a `test: replace invalid focus fixtures and retire proven dead paths` | Complete the reachability ledger and remaining shared setup cleanup. Remove the injected goal-switch fallback only if the callback audit proves it dead. | Every deletion names its surviving behavioral proof. Run affected object suites and native restart/pair scenarios. |
| 4b `refactor: remove duplicate attention dispatch and visual cancellation` | Remove identical `pick_up` dispatch and the second renderer cancellation at game transition. Keep canonical playback cancellation and game state. | Attention, game GUI, reaction playback, and architecture tests. Split further if either change needs independent review. |
| 5 `docs: record orientation validation and acceptance` | Update actual architecture/contracts/smoke instructions and close the ledger around the implemented result. | Fresh full suite, static gates, documentation links, Windows native acceptance, restart and both scales. No merge. |

Stages can span these commits; a stage is not a mandate to make one large commit.
The ledger records commit hash, scope, exact tests and results, replacement proof
for removed tests, CI when pushed, and remaining native acceptance. Stop and fix
a failing required check before extending the implementation.

### Verification commands

Use the repository-pinned environment: Python 3.11 with Pillow 11.3.0 locally,
Ruff 0.13.2, Mypy 1.18.2, and Pyright 1.1.414. The existing CI also covers Python
3.13 and Windows boundaries. For a focused selection, load only the modules
relevant to the current commit, for example:

```powershell
@'
import sys, unittest
sys.path.insert(0, 'tests')
names = ['test_object_attention', 'test_object_absence']
result = unittest.TextTestRunner(verbosity=1).run(
    unittest.defaultTestLoader.loadTestsFromNames(names))
sys.exit(not result.wasSuccessful())
'@ | uv run --no-project --python 3.11 --with Pillow==11.3.0 python -B -
```

Run Tk suites sequentially with temporary saves. Reuse the established main-thread
Tk cleanup harness where required; do not introduce a new repository test runner
or hide skips/errors. The final full suite and static commands follow
[CONTRIBUTING](../CONTRIBUTING.md) and the
[existing CI configuration](../.github/workflows/tests.yml).
Also check local document links and `git diff --check`.

For range coverage, pure tests use a sufficiently wide World/taskbar geometry.
Native 1x/2x checks stay within the actual reachable display. Do not invent
off-screen placements to make a small display fit a test assumption.

## Protected scope and planning status

- Keep separate World custody, subjective knowledge, wish selection, committed
  action, and search lifetime. Do not create a combined mega-state machine.
- Keep hand inspection and deliberate face presentation as first-identification
  routes; known exact-place recall and valid observed continuity are separate.
- Preserve same-type ambiguity, occupied-place guards, legacy save safety,
  valid receipts, physical reach, and exactly-once consumption.
- Do not let a candidate-identification goal become an ordinary novelty goal
  while a search task remains active. Do not erase wishes to enforce priority.
- No save-format migration, real-save cleanup, balance change, artwork change,
  new autonomous movement writer, or new focus timer is planned.
- Local small commits and their focused checks are expected during implementation.
  Implementation has started with staged-tree verification; no merge is authorized.

The planning audit covered the initial dirty baseline, not just the then-committed
HEAD. Its focused verification passed 143 tests; the full suite was deliberately
not rerun for that planning-only revision. Temporary instrumentation confirmed the
invalid focus contexts without changing repository source. The implementation
ledger below records subsequent per-commit tests and final regression separately.

| Stage | Status | Commit and verification |
| --- | --- | --- |
| P0 planning revision | Recorded with Stage 1 delivery | English state/ownership/reachability audit and staged-tree commit discipline. |
| 1 coverage and orientation value | Complete at policy/sensor level | `f1fc8a6`, `dbb8b80`, `3f422f9`; live behavior wiring delivered in Stage 3. |
| 2 witnessed acquisition and own feedback | Complete | `a148296` acquisition and `62c161a` live feedback scope; verification below. |
| 3 orientation and search integration | Complete | `90a754a` and `37c4365`; both-side loss collection, current-wish pause, and search-related candidate feedback verified. |
| 4 proven cleanup | Complete | `8fe556b` and `946d590`; repaired focus fixtures and removed audited duplicate/dead paths. |
| 5 final regression and native acceptance | Complete (automated) | 1,143 tests pass; pinned static and documentation gates pass. Native restart/1x/2x/timer checks pass; human visual/input acceptance remains open. |

## Implementation ledger

- Prerequisite `ad33c8a`: commit the already approved learned portion references,
  memory encoding, and acquired tracking anchors while retaining legacy lookup
  for callers not migrated yet. Verified the staged tree in a temporary checkout:
  178 object tests, Ruff, strict Mypy (184 sources), and Pyright pass. One stale
  persistence expectation was advanced from memory schema 2 to the already
  implemented schema 3; no new save migration was introduced by this plan.
- Stage 1 foundation `f1fc8a6`: immutable `KnownPlaceCoverage` checks the deliberate
  side over World bounds without widening local unknown discovery. Three focused
  tests plus Ruff, strict Mypy (185 sources), and Pyright pass against staged
  contents. Existing runtime defaults remain in force until integration.
- Stage 1 foundation `dbb8b80`: one immutable `OrientationProgress` value with
  fresh left/right dwell, interruption, empty-memory completion, and no appetite
  coupling. Five focused tests plus Ruff, strict Mypy (186 sources), and Pyright
  pass against staged contents. No second interaction/search state was added.
- Prerequisite `a968313`: commit the existing pure desktop/known/assigned/missing
  status projection separately from UI wiring. Its focused test, Ruff, strict
  Mypy (187 sources), and Pyright pass in a staged-tree checkout. Reading counts
  still performs no perception or memory mutation.
- Prerequisite `db003e6`: separately wire the approved object diagnostics and
  need-bar layout. The staged tree passes 65 UI/status tests in 36.152 seconds,
  Ruff, strict Mypy (187 sources), and Pyright. No perception behavior is granted
  by reading the details panel.
- Prerequisite `7ceee64`: preserve independent wish/knowledge semantics when a
  committed subject is forgotten. The staged tree passes 185 object tests and
  all three static gates.
- Prerequisite `7050688`: introduce the already approved recovery subject/route
  model without yet switching its consumers. A direct physical-subject and
  actual-arrival probe, 185 object tests, and all static gates pass.
- Prerequisite `ed7e4db`: migrate the coupled perception/search APIs and their
  existing callers from the previously approved working baseline. This larger
  prerequisite includes the coordinated removal of old signatures; it is not
  a new orientation behavior change or a blanket snapshot of unrelated work.
  The exact staged tree passes 201 object tests and 65 native World/game tests
  in 167.232 seconds, plus Ruff, strict Mypy (187 sources), and Pyright.
- Stage 1 integration `3f422f9`: Awareness and Absence accept explicit learned-place
  coverage. Distant exact-place recall preserves an identified portion, distant
  unknown neighbours remain unidentified, and occupied old places prevent false
  loss. Defaults remain local until Stage 3 supplies the orientation request.
  Four added sensor scenarios cover both sides, 1x/2x, unknown occupancy, and fresh
  evidence after actual exclusion. The old range test was renamed rather than
  deleted after its unknown fixture was verified. The staged tree passes 205
  object tests, Ruff, strict Mypy (187 sources), and Pyright.
- Prerequisite `152a7c5`: separately commit the previously approved grounded
  German item dialogue. Only authored strings changed; 59 focused catalogue,
  dialogue, resource, and object-reaction tests pass against the staged tree.
- Stage 2a `a148296`: a successful acquisition at the exact learned place can
  establish notice and tracking between sensor ticks. The event does not grant
  identification, borrow a neighbour, or override a foreign focus. Current desire
  is tested independently. The staged tree passes 209 object tests, seven native
  take/return/face/capture scenarios, Ruff, strict Mypy, and Pyright.
- Stage 2b `62c161a`: the existing ReactionPlayer owns the live feedback subject, clearing
  it on cancellation/completion before callbacks. Matching item feedback preserves
  the already observed transport; unrelated activity remains unavailable. The
  existing native relocation helper now covers loss of old sensor bindings,
  a longer real gesture, its own refusal cue, and incremental physical settling
  at 1x/2x. A real ground press precedes the move to the face; the test does not
  simulate taking an out-of-view floor item while the pointer is already at the
  face. The staged tree passes 256 focused object/presentation/architecture tests,
  five native transport/Care scenarios, and all three static gates.

- Stage 3a: live orientation now precedes free selection/identification after
  restart, completed activities, and cursor gestures. The behavior coordinator
  owns the sole transient progress value; visual ports expose its current side
  before sensing, and the existing walk driver holds while looking. Empty learned
  memory adds no presentation delay. Committed episodes and witnessed transport
  retain their distinct attention; waiting preserves the canonical current wish.
  Both sides finish even if the final left-side record becomes missing. Confirmed
  losses accumulate before receipts begin. Existing component fixtures now drive
  the public sequence, including a real restored-place check before acquisition.
  The staged tree passes 256 focused tests and 65 native World/runtime/game tests
  (174.482-second combined run; its sole read-port fixture typo was corrected and
  the 256-test selection rerun successfully). Ruff, strict Mypy (187 sources), and
  Pyright pass on the corrected staged snapshot. No merge or user-save change.

- Stage 3b: an unknown recovery candidate now begins the existing approach phase
  and cue inside its enclosing SearchTask. It does not announce ordinary novelty;
  candidate inspection, readable identification/reunion, rejection, and route
  resumption retain their existing owners. The restart scenario now checks old
  places on both sides, with the far 1x place beyond local discovery range, and
  requires every old portion to be missing before the first loss bubble. At 2x,
  historical setup reuses an already noticed record rather than inventing a second
  record for the same portion. Actual conversation timers prove left/right looks
  before loss, and actual multi-bubble timers preserve each named receipt.
  The staged tree passes 214 object tests plus six native restart/face/timer cases
  in 37.237 seconds, and all three static gates. No merge.

- Stage 4a `8fe556b`: correct committed/free attention fixtures through the shared
  policy, including close/coincident learned portions, selected-place occupancy,
  actual hand inspection, and observed transport. A free curiosity-after-gap test
  no longer fabricates a committed action. Ordinary unobserved recovery now tests
  actual empty-place evidence before candidate inspection, rather than injecting
  a missing flag or running the reverse ordinary order. Memory's lower-level
  order tolerance and readable preinspection-loss reconciliation remain covered.
  A genuinely later patrol loss now comes from moving real learned stock after
  route start. The injected goal-switch test and its two-line fallback are removed
  following the caller/callback proof above. The exact staged tree passes 213
  object tests and three native commitment/restart checks (216 total, 5.447 seconds),
  plus all three static gates.
- Stage 4b: remove the identical pickup-attention dispatch, the unused boolean
  World-access wrapper (the subject read remains), and the renderer's second action
  cancellation during game transitions. Canonical ActionPlayback cancellation stays
  in the shell. Native game coverage now explicitly asserts one renderer cancellation
  on close, alongside deadline release and restored gaze. Isolated renderer setup
  models that owner cancellation before its mode change. The staged tree passes
  88 attention/access/animation/reaction/game/architecture checks in 13.098 seconds,
  Ruff, strict Mypy (187 sources), and Pyright. No merge.

- Stage 5: the complete committed application/test snapshot passes **1,143 tests
  in 299.856 seconds**, with no failures, errors, or skips, on Windows using the
  pinned Python 3.11.9/Pillow 11.3.0 environment. This includes real Tk timer,
  cursor, custody, restart, close-portion, same-type, and 1x/2x coverage. No source
  correction was required by the final full run. Ruff 0.13.2, strict Mypy 1.18.2
  (187 sources), and Pyright 1.1.414 pass on that same exported snapshot.
  Architecture, current World contracts, the supersession note, and the practical
  checklist now describe deliberate whole-taskbar learned-place checks separately
  from local new-item discovery. Documentation verification passes 260 local file
  targets and 15 heading anchors; UTF-8 decoding and diff whitespace checks pass.
  Every implementation commit was checked through an exported index snapshot.
  Commits remain local: no push, remote CI run, or merge was performed. The normal
  user save was not readjusted; native tests use temporary saves. Human visual/input
  acceptance is intentionally not claimed: restart Aiko and use the current
  [practical checklist](WORLD_SMOKE_TEST.md) for the next feedback round.
  Optional deletion of temporary verification exports was rejected by automatic
  approval review as "blocked by policy"; those exports remain outside the repo.
