# OOP refactoring: interaction state, behavior ownership and pet encapsulation

Recorded: 17 October 2026.
Baseline: `46ef08f` on `feature/world-foundation`.
Status: stages 1-7 automatically verified.
Practical native acceptance remains open.
No merge is authorized.

This is the accepted implementation plan following the OOP review. It extends
the current [architecture](ARCHITECTURE.md) and preserves the behavior contracts
in [World object contracts](WORLD_OBJECT_CONTRACTS.md) and the implemented
[perception correction](OBJECT_PERCEPTION_CORRECTION_PLAN.md).
The delivery ledger records those original stages as historical delivery
evidence. The later [World OOP follow-up](OOP_WORLD_FOLLOWUP_PLAN.md) supersedes
the earlier appetite-based search cancellation, search-stop result and
conditional missing-place search. Its newer World behavior contracts govern
current runtime decisions.

## Scope and invariants

- Preserve authored dialogue, timing, nutrition, friendship, settings and saves.
- World owns objective instances, custody, geometry and revisions. Perception
  supplies sensory evidence; ObjectMemory owns learned facts and confirmed own
  actions. World identity must not become subjective identification by shortcut.
- ObjectIntentions owns the selected wish. ObjectInteractionCoordinator owns the
  running episode, phase order, interruption and identified playback effects.
- ObjectCustody and ObjectConsumption retain joint commits and owner recovery.
  Consuming in World alone does not feed the pet. Actual handover and autonomous
  collection retain their distinct care origins.
- Keep the current owner thread, clocks, callback order and readable cue gates.
  Feedback callbacks may acknowledge or cancel synchronously.
- Retain read access to phase, record/instance identifiers and search progress.
  Production callers and existing tests must be inspected before removing APIs.
- Preserve version-one outer saves and optional World/object-memory sections.
  Ephemeral interaction state remains session-local.

No new gameplay, general event bus, state-machine library, runtime dependency,
configuration redesign or asset changes belong to this refactor. Success means
clearer ownership and preserved behavior, not a target class or line count.

## Target 1: explicit interaction state

Keep the existing coordinator as the transition owner. Add internal typed data
under `application/object_interaction_state.py` in two independently verified
steps: episode data first, phase-specific state second.

| Lifetime | Target contents | Constraints |
|---|---|---|
| Coordinator/session | Dependencies, configuration, increasing identity counters and contact cooldown | Counters and cooldowns keep their current lifetime; an episode restart must not make old receipts valid. |
| Episode | Record, confirmed instance where applicable, origin/use context, learned identity/kind, retrieval intent, queued interruption, withholding episode and effect history | A fresh episode resets its own data. Observed return retains the existing episode; actual release changes care origin to handover. |
| Phase | Phase key, cue/animation prerequisites and phase-specific data | Search has its own start/center; inspection has its own dwell; pickup/put-down have action/effect prerequisites; offer decisions retain the latest appraisal. |

Use a small union of typed phase records. Share records only where their
prerequisites match. Do not create one behavior subclass per phase or merely move
all optional flags into a single bag. A central phase-entry operation installs
the next valid state and invalidates earlier feedback before cancellation calls
back. Do not invent resets that change existing observable lifetimes.

`phase`, `memory_id`, `instance_id`, `search_x` and progress remain read-only
observations of the canonical state. Tests should drive goals, observations,
receipts, playback and injected time instead of setting private phase flags.

### Stage 2 implementation

`application/object_interaction_state.py` now defines InteractionEpisode, an
internal mutable record owned only by ObjectInteractionCoordinator. It groups
the interaction/record/instance identifiers, actual care origin, use context,
learned identity/kind, retrieval intent, queued interruption, withholding episode
and playback/effect histories. Fresh histories use independent default factories.

The coordinator creates a fresh record in _start. Observed takes and returns
retain it; an accepted returning handover updates its actual origin. _finish
drops the record before cancelling feedback, so ended object references and
queued episode state are no longer retained on the coordinator. The last
diagnostic feedback identity remains available while idle, derived from the
existing sequence counter without retaining an ended record.

memory_id and instance_id are read-only properties of that record, returning
None after completion. Repository source/test/tool consumers were searched:
no external assignments to these two attributes or dependencies on the moved
private fields were found. Existing readers keep their read interface.

At stage 2, dependencies, monotonic identity counters, contact cooldown, phase,
animation prerequisites, appraisal/cue flags and search/inspection timing kept
their existing lifetime and owner. Their subsequent phase-state extraction is
recorded below. Desktop behavior, PetState, persistence and catalogues remain
outside this concern.

### Stage 3 implementation

The same state module now defines a closed PhaseState union. The coordinator
owns exactly one current variant and exposes its existing string phase name
through a read-only property. Variants share data shapes when their prerequisites
match; they do not implement a behavior inheritance hierarchy.

| Variant | Phase names | Owned prerequisites/data |
|---|---|---|
| IdlePhase | idle | No cue, animation or episode-phase prerequisites. |
| CuePhase | notice, recognize, handover, finish, missing | Current readable cue and optional aside. |
| ApproachPhase | approach | Fresh real-arrival acknowledgement and cue. |
| AnimationPhase | pick_up, eat | Identified playback, clip completion and independent cue completion. |
| PutDownPhase | put_down | Playback/cue prerequisites plus the reason permitting deliberate deferral; queued interruption still prevents it. |
| InspectionPhase | inspect | Current inspection start and cue; identification still comes from memory. |
| DecisionPhase | decide | Current use decision and readable cue. |
| WaitingPhase | await_return, await_settle, recognize_offer, decide_offer | Current/latest offer appraisal and a fresh cue per transition. |
| AbsencePhase | notice_absence | Whether the checked absence warrants a search and its readable cue. |
| SearchPhase | search | Immutable search location/start and current cue. |
| FoundPhase | found | Required replacement goal and its readable cue. |

PhaseFeedback owns each active phase's cue acknowledgement, pending aside and
auxiliary receipt. AnimationProgress exists only for animation phases.
OfferAppraisal is deliberately retained across waiting/offer transitions so
changed needs or motion cannot erase a pending appraisal. A new approach instead
gets a fresh arrival prerequisite. There are no coordinator-wide mutable phase
flags, sentinel action IDs, optional replacement goals or stale use decisions.

_set_phase installs a fully typed variant and increments the receipt identity
before cancel_feedback can synchronously report an obsolete cancellation. New
phase feedback starts incomplete; silent transitions supply completion explicitly.
Playback and cue completion remain separate gates. Inspection time is sampled
after cancellation, and source-frame acquisition/placement ordering is retained.

The existing search_x/search_progress reads retain their previous off-phase
values through an immutable SearchReadout. Current SearchPhase and the read side
share that value; control uses the current phase's start, not an unrelated old
timer. Goal/place updates retain the prior diagnostic timer until a fresh search
begins. This preserves the baseline's observable lifetime without retaining
irrelevant mutable flags on later phases.

## Target 2: application-owned object behavior

Introduce `application/object_behavior.py` with an ObjectBehaviorCoordinator
that coordinates the existing awareness, intentions and interaction owners.
It stores no duplicate goal, memory or running episode.

| Owner | Responsibility after the cutover |
|---|---|
| ObjectIntentions | Select and retain wishes from subjective knowledge. |
| ObjectInteractionCoordinator | Execute one episode, phases, receipts and interruption. |
| ObjectBehaviorCoordinator | Coordinate absence priority, search continuation/replacement, goal start/change and waiting for observed return. |
| DesktopWorldRuntime | Read host facts, translate geometry, drive native movement/rendering and report real arrival/reach. |

Move search replacement and appetite-driven cancellation first. Then move
absence reaction, approach start/change and return waiting. Define immutable
results with bounded movement requests such as Hold, Approach and Search, plus
an optional gaze target. Keep absolute screen placement, taskbar reach, capture,
Tk timers and native rendering in desktop adapters. Acquisition still requires
actual reach and source-frame revalidation.

The desktop must stop inspecting phase strings to choose behavior. It supplies
observed facts and executes the application result. Keep observation and
effect order, including synchronous feedback, without adding a frame of delay.
Retain the current single mind tick and separate motion/render callback.

### Stage 4 implementation

`application/object_behavior.py` now defines ObjectBehaviorCoordinator. It uses
the existing PetState, ObjectAwareness and ObjectInteractionCoordinator by
reference; it constructs no second memory, intentions, clock or running episode.
DesktopWorldRuntime composes this owner next to the existing interaction owner.

advance_search owns the search branch previously in DesktopWorldRuntime.update:
whether to adopt a different, currently wanted known supply; cancel for blocking;
cancel a known search whose need is satisfied; or continue bounded searching.
It uses canonical decide_object_use on subjective memory. A supplied goal's
identity alone never identifies a candidate. Unknown current stock still permits
curiosity even when the pet's needs are satisfied.

The baseline ordering is intentional: a suitable alternative precedes general
blocking; only then does blocking precede the appetite-based cancellation.
Interaction found/interrupt methods keep their existing cue, completion and
owner-recovery semantics. The application method adds no extra interaction tick.

| Result | Application effect | Desktop action in this stage |
|---|---|---|
| SearchMotion(center, progress) | Continue the current search; capture relative position and active-time progress. | Translate the immutable instruction to existing taskbar/scale bounds, stride and gaze; end this update. |
| SearchStopped | Known stock is no longer wanted; finish through the normal interaction completion callback. | End this update without adding another native action. Existing completion ports already clear movement/gaze and save. |
| None | No search branch applies, a replacement was announced, or blocking cancelled the search. | Continue the existing found/approach/blocking gates in the same update. |

The last case preserves synchronous feedback: an immediately acknowledged found
cue can start the replacement episode before advance_search returns. Returning
an unconditional hold there would change the original update ordering.

_show_search now renders SearchMotion instead of querying interaction state.
It still owns native geometry, edge clamping, scaling and gaze placement. Goal
selection and perception remain in their existing owners. Absence priority,
approach start/change, return waiting, eligibility facts and remaining desktop
phase checks are explicitly deferred to stage 5.

### Stage 5 implementation

ObjectBehaviorCoordinator now owns the remaining object-behavior decisions:
host eligibility and awareness inputs, checked-absence priority/acknowledgement,
subjective gaze selection, offer-observation eligibility, waiting for observed
return, passive held wishes, approach start/change and unreachable-goal
cancellation. It also owns continuing-wish appraisal, returning-offer assessment
and the behavioral half of acquisition eligibility. These use canonical memory,
intentions and interaction operations rather than copying their rules or state.

The desktop supplies immutable BehaviorFacts (game, controls, carrying, playback
and pending input) and native sensory geometry. The application returns immutable
BehaviorObservation, GazeTarget and motion instructions. It references the same
WorldState only to read the custody of a target resolved through the existing
subjective binding; it does not discover identities through World handles.

| Step/result | Application responsibility | Native adapter responsibility |
|---|---|---|
| observe | Update the existing awareness owner; accept an eligible absence before ordinary attention; choose committed/goal/nearest-unassessed gaze. | Supply filtered sensor snapshot, relative body/face data and current host facts; translate gaze to screen coordinates. |
| Accepted absence | Acknowledge only after the interaction accepts its notice; suppress ordinary offer/motion work this tick. | Clear movement/readiness, apply absent-place gaze, save and end the update. |
| Offer observation between observe/advance | Expose eligibility; returning appraisals can synchronously update the episode through assess_offer. | Retain the cursor gesture's observe_offer call at the existing point in the update. |
| Hold | Wait for notice/found feedback, a returning/moving target, blocking or passive held stock. | Clear native movement for this update. |
| Approach(target) | Start/change the existing episode only when eligible; permit a synchronous found acknowledgement to continue in this update. | Compute reachable standing position, set movement, check actual arrival and revalidate source reach; capture contact before reporting interaction.arrive. |
| SearchMotion / SearchStopped | Retain stage 4 search decisions and completion effects. | Render the bounded search, or end without another native action after completion. |
| unreachable(now) | Cancel the shared intention and interrupt through normal episode completion. | Report that native geometry found no reachable standing position. |

The attention/motion split is deliberate: applying a stale gaze result after a
synchronous completion would undo the completion port's gaze clearing. Likewise,
a waiting-target update returns Hold even if its return cue immediately restores
approach; a found replacement can instead approach in the same update. No second
interaction tick, timer, clock, goal, memory, episode or event queue is introduced.

DesktopWorldRuntime no longer inspects interaction phase names or decides hunger,
absence/search priority, return waiting or approach eligibility. Its remaining
small decision/offer callbacks delegate to the application owner; native reach
still comes from current World geometry, taskbar/scale bounds and cursor height.
Acquisition eligibility is checked again through the same port at the animation
source frame. Movement speed, authored cues, care origins, saves and assets are
unchanged. Stages 6-7 retain the PetState/protocol/checkpoint work.

## Target 3: PetState write boundaries

PetState remains the stable mutable aggregate. It will own an immutable PetValues
record in the pet package and expose read-only properties with existing names.
Keep named initialization arguments used by the codec and test scenarios.

1. Convert NeedValues, CareValues, RoutineValues and FriendshipRecord to genuinely
   read-only protocols. Use Sequence/Mapping interfaces for readable histories.
2. Define complete immutable PetValues, including immutable meal/reward histories.
   Keep FoodState and existing transition policies as their canonical owners.
3. Replace the direct session-restoration timestamp write with a named operation
   for anchoring the live session after bounded offline progression.
4. Introduce explicit checkpoint capture, preparation and restore operations.
   ObjectConsumption keeps atomic preparation/commit/recovery without replacing
   the identity of the live PetState or leaking writable state references.
5. Move all writes behind care, time, game, withholding and checkpoint operations.
   Migrate codecs and tests; preserve value equality and independent checkpoints.

The existing application PetReadSnapshot remains a smaller immutable read
projection. It is not a full checkpoint and must not be imported into pet rules.
Serialization field names, validation/fallback behavior and existing gameplay
formulas remain unchanged. Inspect repository consumers before retiring
restore_values or relying on different dataclass/deepcopy behavior.

## Stage 1: current transition contract

The following table describes the baseline implementation. A matching phase cue
must be acknowledged unless an explicitly silent transition supplies completion.
Playback completion and cue acknowledgement can arrive in either order. Public
events below can redirect these ordinary transitions.

| Phase | Prerequisite / input | Effect and successor |
|---|---|---|
| idle | begin_goal on an inactive coordinator | Start a fresh episode; announce notice or known-stock recall; enter notice. A permitted release handover instead enters handover or inspect. |
| notice | Current cue complete | Enter approach; known assessed retrieval has a silent approach, otherwise announce approach. |
| approach | Real arrival and current cue complete | Resolve and revalidate instance; start pick_up, or finish unsuccessfully if acquisition is unavailable. |
| pick_up | Matching source-frame attachment | Commit World/memory acquisition once after revalidation. Stay until the clip and cue finish. |
| pick_up | Clip and cue complete | Queued interruption goes to put_down; known assessed retrieval attempts consumption; known identity goes to decide; otherwise inspect. |
| inspect | Cue complete, fresh inspection dwell elapsed and memory identifies the held item | Enter recognize and announce identification. No World-derived identity shortcut. |
| recognize | Cue complete | Reassess current use and mark valid assessment; enter decide with readable desire/refusal. |
| decide | Cue complete | Attempt consumption if wanted; otherwise put_down. Consumption revalidates appetite and pet custody. |
| handover | Cue complete | Attempt consumption with actual handover origin. Known handover does not repeat inspection. |
| await_return | Observed custody or valid assessed offer | Resume approach on observed resting return, wait for motion, search after actual loss, or enter offer recognition/decision. No acquisition while the player holds the item. |
| await_settle | Observed custody or valid assessed offer | Keep the same episode while moving; resting return resumes approach after cue/aside gates; actual loss starts search. |
| recognize_offer | Cue complete | Use the latest offer appraisal, enter decide_offer and announce willingness/refusal. Motion does not cut short this cue. |
| decide_offer | Cue complete | Changed appraisal announces a new decision; acceptance returns to await_return; refusal finishes unsuccessfully. |
| notice_absence | Checked local absence accepted; then cue complete | Search if investigating or currently wanted, otherwise finish. A repeated absence cannot restart this phase. |
| search | Fresh active-time search budget elapsed and cue complete | Enter missing and announce loss. A replacement find can enter found before timeout. |
| found | Cue complete | Start the selected replacement as a fresh episode via notice. Old search feedback cannot restart the prior search. |
| eat | Canonical consumption already committed; clip and cue complete | Enter finish and announce completion. Animation completion never applies nutrition again. |
| put_down | Matching detach frame | Commit World/memory placement once; interrupted placement does not claim deliberate deferral. |
| put_down | Clip and cue complete | Finish unsuccessfully; then execute the latest queued user action once. |
| finish | Cue complete, including cancellation acknowledgement | Finish successfully; preserve committed consumption. |
| missing | Cue complete | Finish unsuccessfully without erasing learned identity. |

### External events and ordering

| Event | Existing contract to preserve |
|---|---|
| Phase entry | Change phase/receipt identity and clear obsolete phase/aside gates before cancel_feedback may synchronously report cancellation. |
| Feedback receipt | Accept only the current phase or current auxiliary key. An auxiliary receipt releases its aside, never a phase. Duplicate/stale receipts do nothing. Cancelling ordinary phase speech safely interrupts; put_down and finish retain their special completion behavior. |
| Playback | Match current action and phase; deduplicate envelopes and attachment/detachment effects separately. Failed joint effects restore owners and allow the same event to retry. |
| Observed target take | Before confirmed pet custody, keep episode/record but invalidate pending grasp, clear approach arrival and enter await_return. A take cannot steal established pet custody. |
| Motion/return/loss | Falling/bouncing waits for settlement; resting return resumes the same episode. Loss starts bounded subjective search without fabricating confirmed empty-place evidence. |
| Held-offer appraisal | Accept only the focused, identified record with a valid current appraisal. Recognition/decision cues remain readable as appraisal or motion changes. |
| Release handover | Revalidate reach/custody; commit World/memory together. A returning target retains the episode and changes actual consumption origin to handover. |
| User interruption | Before custody, finish and execute the action. After grasp, wait for safe pickup completion and detach before action; while putting down, retain the latest requested action. Already committed consumption stays committed. |
| Absence/found | Absence can redirect only an eligible episode; a found goal can replace only an active search. Desktop eligibility and search replacement move in stages 4-5. |
| Ordinary contact | Respect committed focus and the existing contact cooldown; use at most one pending aside without replacing unread phase speech. |

### Existing coverage and focused additions

Reuse the existing suites rather than duplicate their complete scenarios:

- test_object_interaction: arrival/cue gates, custody before consumption,
  deduplication, joint rollback/retry, readable inspection and safe interruption.
- test_object_retrieval: known-stock shortcuts, changing needs, player return,
  offer recognition/refusal, bounded search and replacement finds.
- test_object_absence and test_object_withholding: sensory absence and social
  episode rules; test_world_gui/runtime_flow: actual component/native wiring.
- test_object_consumption: nutrition origin, receipts and recovery of all owners.

Stage 1 adds five focused cases: synchronous cancellation of the previous cue;
old phase/playback events targeting the same item in a new episode; stale
auxiliary feedback across episodes; cancellation of completion speech after
consumption; and fresh search dwell plus current feedback in a new episode.
These are behavioral guards for the state extraction, not tests of future types.

## Delivery stages and acceptance

| Stage | Deliverable | Gate / acceptance | Status |
|---|---|---|---|
| 1 | Record this plan and baseline transitions; fill focused behavioral gaps. | Tests pass on unchanged production behavior; complete local suite and pinned quality gates; inspect diff. | Verified |
| 2 | Extract episode data. | Same episode identity across take/return, fresh data for restart, no old action/feedback leakage. | Verified |
| 3 | Introduce typed phase state. | Current readable phase API retained; invalid cross-phase data removed; callback order, cue/dwell and effect gates preserved. | Verified |
| 4 | Move search continuation, cancellation and replacement to application. | Pure application tests cover appetite changes, blocking, alternate supply and stale search receipts; desktop executes results. | Verified |
| 5 | Move remaining behavior coordination and connect desktop. | Absence priority, approach, waiting and gaze preserved; native reach and actual arrival retained; no desktop phase-based behavior policy. | Automatically verified; practical native acceptance open |
| 6 | Prepare read-only pet protocols and explicit checkpoints. | Current policies accept read-only contracts; consumption preparation/recovery preserves values and live identity. | Automatically verified; practical native acceptance open |
| 7 | Encapsulate PetState; migrate callers and architecture documentation. | External field/collection writes cannot change state; save compatibility and all transitions retain parity. | Automatically verified; practical native acceptance open |

Run the affected suites after every stage and record actual results below.
Stages 2-3, 4-5 and 6-7 each complete one of the three reviewed concerns.
Before closing each concern, run the full suite, Ruff 0.13.2, strict Mypy 1.18.2
and Pyright 1.1.414. Stage 1 also takes this full baseline after its added tests.

```powershell
uv run --no-project --python 3.11 --with Pillow==11.3.0 python -m unittest discover -s tests -q
uvx --from ruff==0.13.2 ruff check aiko_pet tests main.py tools
uvx --from mypy==1.18.2 --with Pillow==11.3.0 mypy --python-version 3.11 --strict --no-incremental aiko_pet main.py tools
python -m pyright --project pyrightconfig.json
```

Native Windows acceptance is required when later stages change window/input,
movement, timer or feedback wiring: handover, source-frame pickup/put-down,
return while moving, bounded search, readable bubbles and care/game/sleep
interruption. Use the isolated [World smoke checklist](WORLD_SMOKE_TEST.md).
Automated Tk tests and manual/native acceptance are recorded separately.

Keep stages reviewable, inspect each diff and preserve unrelated local work.
No merge is authorized; later stages must not be marked complete from design
alone. A stage that exposes a behavior defect records it explicitly rather than
silently changing the accepted baseline under a structural refactor.

## Verification ledger

### Interpreter audit during stage 4

The default `python` was explicitly identified as Python 3.14.0 during stage 4;
the installed project-baseline interpreter is Python 3.11.9. Earlier stage 1-3
entries incorrectly labelled default-interpreter runs as Python 3.11 without
capturing their version. Those version labels are withdrawn below; the measured
test counts and times are unchanged. Stage 4 records explicit versions and adds
a full Python 3.11 run covering all cumulative changes. Future baseline commands
above select Python 3.11 and Mypy's Python 3.11 target explicitly.

### Stage 1

- Before stage 1 edits: 45 interaction/retrieval/withholding/absence tests passed.
- Stage 1: five regression cases added to the existing interaction/retrieval
  suites. The same four focused suites now pass all 50 tests.
- Full local Windows suite (default python): 1,025 tests passed in 222.527 seconds.
- Ruff 0.13.2: passed across application, tests, entry point and tools.
- Strict Mypy 1.18.2: passed for all 179 source files. The first isolated uvx
  environment lacked Pillow; rerunning with CI's Pillow 11.3.0 dependency passed.
- Pyright 1.1.414: zero errors and zero warnings, including tests.
- Every current InteractionPhase is documented; local Markdown links resolve;
  git diff --check passed. Runtime source, catalogues and assets are unchanged.
- No new manual Windows acceptance was performed for this documentation/test
  stage. Later runtime changes still require the native checks above.
- No commit, push or merge was made during stage 1; its changes remain local.

### Stage 2

- Extracted the episode record and migrated its accesses; retained the existing
  phase transitions, guards, callback order and session counters/cooldowns.
- Added behavioral regressions for contact cooldown across episodes and for
  autonomous retrieval after an interrupted handover, including one-time queued
  action execution, cleared idle object references and diagnostic identity.
- Focused interaction/retrieval/withholding/absence/consumption/dependency suites:
  61 tests passed in 0.379 seconds, including the stage 1 callback/event guards
  and existing same-episode return, rollback/retry and consumption-origin cases.
- Full local Windows suite (default python): 1,027 tests passed in 221.052 seconds.
- Ruff 0.13.2: passed across application, tests, entry point and tools.
- Strict Mypy 1.18.2 with Pillow 11.3.0: passed for all 180 source files.
- Pyright 1.1.414: zero errors and zero warnings, including tests.
- Diff/source review found no coordinator shadow copies of the extracted fields.
  Plan links resolve and git diff --check passed. Desktop/timer wiring, PetState,
  authored catalogues, save codecs and assets are unchanged.
- No new manual native acceptance was performed. This stage changes episode
  storage without changing native window/input/timer wiring; full automated Tk
  scenarios passed. Later wiring changes still require the native checks above.
- Existing uncommitted stage 1 work is preserved. No commit, push or merge was
  made during stage 2. Stage 3 remains the next structural implementation step.

### Stage 3

- Implemented the typed phase union and migrated transitions, playback, feedback,
  inspection, search and offer-appraisal prerequisites. Session counters and
  contact cooldown remain on the coordinator; episode ownership is unchanged.
- Added behavioral coverage for fresh arrival after observed return; cue-before-
  clip completion plus stale playback in the next phase; and the existing search
  read values across idle/new-goal/fresh-search boundaries.
- Focused interaction/retrieval/withholding/absence/consumption/dependency suites:
  64 tests passed in 0.381 seconds.
- All 45 interaction/retrieval tests, including the three new cases, also passed
  against an isolated in-memory load of the saved stage 2 coordinator. This checks
  their baseline contracts without modifying source or relaxing expectations.
- Ruff 0.13.2 passed; strict Mypy 1.18.2 passed all 180 source files; Pyright
  1.1.414 reported zero errors/warnings, including tests.
- Full local Windows suite (default python): 1,030 tests passed in 223.419 seconds.
- Source review confirms all 19 public phase names are represented by 11 data
  variants, with no retired coordinator flag writes. Repository-wide assignment
  search found no external writers of phase/search_x. Plan links resolve and
  git diff --check passed.
- The first OOP concern is automatically verified through stages 2-3. Existing
  native Tk scenarios passed; no new manual native acceptance was performed.
  Window/input/timer wiring, Desktop behavior policy, PetState, save codecs,
  catalogues and assets remain unchanged. Later wiring changes still require
  the native checks above.
- Existing stage 1-2 work is preserved. No commit, push or merge was made during
  stage 3. Search/application behavior ownership remains stage 4.

### Stage 4

- Introduced ObjectBehaviorCoordinator with immutable search results and moved
  the existing search decision branch from desktop into the application layer.
  Native search rendering consumes the returned center/progress; other behavior
  coordination and desktop eligibility remain stage 5.
- Added 10 headless tests using the real awareness, memory and interaction owners:
  non-search handoff, active progress, unknown curiosity, changed needs, blocking,
  replacement priority, delayed/stale feedback, synchronous replacement, same
  target, forged/unidentified knowledge and unwanted alternate supply.
- Focused behavior/interaction/retrieval/withholding/absence/consumption/dependency
  suites: 74 tests passed in 0.392 seconds.
- The same 10 new tests passed against the original stage 3 desktop search branch,
  extracted into an isolated in-memory adapter with result conversion. No source
  or test expectations were changed for that baseline comparison.
- Ruff 0.13.2 passed; strict Mypy 1.18.2 with Pillow 11.3.0 passed all 181 source
  files, also with explicit --python-version 3.11; Pyright 1.1.414 reported zero
  errors/warnings, including tests, with its configured Python 3.11 target.
- Full Windows/Python 3.14.0 suite: 1,040 tests passed in 223.259 seconds.
- Full Windows/Python 3.11.9 suite: 1,040 tests passed in 224.129 seconds, using
  a temporary uv environment with CI's Pillow 11.3.0. No global package
  installation was needed. The existing ttk ThemeChanged teardown diagnostics
  were printed; unittest finished OK with exit code 0.
- Source/diff review confirms the desktop update no longer decides search
  appetite and the renderer consumes SearchMotion. Plan links resolve and
  git diff --check passed.
- Automated native Tk scenarios passed on both interpreters. No new manual
  visual/input acceptance was performed; the existing practical checklist stays
  open. Native geometry, taskbar clamping, timing parameters, care origin,
  persistence, catalogues and assets remain unchanged.
- Existing stage 1-3 work is preserved. No commit, push or merge was made during
  stage 4. Stage 5 remains the next implementation step.

### Stage 5

- Moved absence/attention, return waiting, passive held wishes, approach
  start/change/cancellation and behavioral eligibility into the existing
  application behavior owner. Desktop consumes immutable attention/motion
  results and retains native geometry, actual arrival and source-frame reach.
- Added 13 headless behavior cases using the real application owners: pending
  and accepted absences, busy commitment, nearest visible gaze under blocking,
  host eligibility, passive held wishes, readable notice/real-arrival gating,
  approach replacement, synchronous found/return handling, lost return binding,
  unreachable cancellation, current offer/reach evidence and continuing wishes.
- Focused behavior/interaction/retrieval/withholding/absence/consumption/dependency
  suites: 87 tests passed on Windows/Python 3.11.9 in 0.395 seconds.
- All 30 native Tk World GUI scenarios passed in 17.718 seconds on Python 3.11.9.
  The same scenarios also passed in 17.446 seconds with the saved stage 4 desktop
  update/acquisition/offer/decision methods loaded only in memory. Production
  source and test expectations were not changed for that baseline comparison.
- All 23 headless behavior cases also passed on Python 3.14.0 in 0.002 seconds.
- Ruff 0.13.2 passed; strict Mypy 1.18.2 with Pillow 11.3.0 and explicit Python
  3.11 target passed all 181 source files; Pyright 1.1.414 reported zero errors
  and warnings, including tests.
- Full Python 3.11.9 Windows suite: 1,053 tests passed in 224.086 seconds, using
  an isolated uv environment with Pillow 11.3.0. Existing ttk ThemeChanged teardown
  diagnostics were printed; unittest finished OK with exit code 0.
- Source review confirms no desktop interaction-phase-name behavior branches
  and no duplicate behavior-owned goal, memory, clock or episode. Existing
  motion/render timer, reach formulas, native contact capture and animation-frame
  revalidation remain in place. No PetState, persistence, catalogues or assets
  were changed during this stage. Local plan/architecture Markdown links resolve,
  touched files use LF line endings and git diff --check passed.
- Automated Tk evidence is separate from manual Windows visual/input acceptance.
  No new manual acceptance has been performed; the isolated World smoke
  checklist (both scales, native input/layering/readable bubbles and interruption)
  remains open before final acceptance of this wiring change.
- The second OOP concern is implemented and automatically verified through
  stages 4-5; practical native acceptance remains a separate outstanding gate.
- Existing stage 1-4 work is preserved. No commit, push or merge was made during
  stage 5. At that handoff, stages 6-7 had not yet started; stage 6 is
  documented below.

### Stage 6

- Converted NeedValues, CareValues, RoutineValues and FriendshipRecord to
  read-only protocol properties. Policy input histories use Sequence and Mapping,
  not mutable list/dict requirements. The existing policy implementations retain
  their pure calculations and their mutable PetState caller remains compatible.
- Added `pet/state_values.py`: a frozen, slotted PetValues record covering every
  PetState field. Meal and friendship histories are captured as tuples (including
  reward key/value pairs); the nested FoodState was already immutable.
  PreparedItemConsumption couples one accepted canonical care result with its
  full proposed checkpoint. No second live pet owner or save schema is introduced.
- PetState now owns `capture_checkpoint`, `prepare_item_consumption` and
  `restore_checkpoint`. Preparation evaluates the existing consumption policy
  against a separate working PetState; neither accepted nor rejected preparation
  mutates the live aggregate. Commit and rollback restore values into the same
  live object and reconstruct independent mutable history collections.
  `restore_values` remains as a compatibility wrapper until stage 7.
- `ObjectConsumption.commit` uses these explicit checkpoints instead of
  application-level deep copies of the live PetState. World, pet and memory
  remain one recoverable transaction; care origin, receipt deduplication and
  playback boundaries are unchanged. PetSessionRestorer uses the named
  `anchor_live_session` operation after bounded closed-time progression.
- Five new checkpoint tests verify full field coverage, immutable snapshots,
  independent repeated restoration, accepted/rejected canonical preparation
  for both origins, and live session anchoring. A new handover rollback test
  verifies retained PetState identity and complete pet/World/memory recovery.
  Existing persisted value and nutrition tests remain in the full suite.
- Final code revision `f4652d9` passed [CI 39039540687](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/39039540687):
  **1,059 tests** on Linux/Python 3.11 and **1,059 tests** on Linux/Python
  3.13; Windows setup/native-boundary checks passed. Ruff 0.13.2, strict
  Mypy 1.18.2 and Pyright 1.1.414 passed. The first code revision exposed
  formatting/name defects; those were corrected before final CI.
  No separate full local Windows regression was run in this environment.
- No asset, JSON catalogue, gameplay formula, save field or version was changed.
  The existing practical World checklist remains open, and draft PR #10 stays
  unmerged. Stage 7 (encapsulate live PetState and migrate external writers)
  has not been started.

### Stage 7

- Replaced the writable public PetState dataclass with a stable mutable
  aggregate that owns one frozen PetValues record. Every named constructor
  argument from the v1 codec and prior tests remains supported, with
  independent immutable histories. Live identity and value equality persist.
- Public scalar properties are read-only. Public meal, reward and care-history
  reads return detached lists/dictionaries; modifying them cannot change the
  aggregate. The internal `_change` operation commits a replacement PetValues
  only from owner-controlled care, routine, time, game, withholding, checkpoint
  and session-anchoring paths. There are no new public field setters.
- Existing canonical nutrition and friendship transitions, exact-time updates,
  explicit checkpoint preparation/restoration, persistent v1 fields and rollback
  origins remain unchanged. A compatible `__deepcopy__` reconstructs an
  independent owner, and the aggregate retains an instance dictionary solely
  for existing method-spy/mock compatibility; it does not expose mutable values.
- Read-only desktop animation, walk and sprite protocols now accept the
  protected PetState. Isolated World smoke overrides and regression fixture
  mutations use the test-only `tools/pet_test_support.py` checkpoint adapter,
  preserving the identity required by desktop services. Developer media
  captures use the real sleep command rather than direct field assignment.
- Replaced dynamic test assignments, `vars()` comparisons and direct history
  writes; added an explicit regression proving public assignments fail and
  modifications of detached collection reads leave the live checkpoint intact.
  The prior stage-six checkpoint/consumption tests and v1 persistence parity
  still run in the full suite.
- Code revision `a2bf97b` passed
  [CI 39045634303](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/39045634303):
  Linux Python 3.11 **1,060 tests**, Linux Python 3.13 **1,060 tests**,
  and the Windows setup/native-boundary matrix. Ruff 0.13.2, strict
  Mypy 1.18.2, and Pyright 1.1.414 all passed. The test fixture
  migrations exposed expected early red CI runs; their failures were fixed
  before the final green revision. No separate local full Windows suite was run.
- No gameplay, balancing, assets, JSON catalogue, persistence schema or
  application event/timer contract was changed. This finishes the structural
  stages 6-7 of the PetState write-boundary concern. Native manual visual/input
  acceptance remains a separate requirement; PR #10 stays draft and unmerged.
