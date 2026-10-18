# Shared object search and investigation

Recorded: 18 October 2026. Branch: `feature/world-foundation`.
Status: stages 1–7 complete and automatically verified. Initial user smoke
feedback is positive; full manual acceptance open.
No merge authorized. Existing local work and the ordinary save are preserved.

This is the current delivery plan. It supersedes the exclusive single-subject
search rules in [the earlier search ledger](OBJECT_SEARCH_LIFECYCLE_PLAN.md).
Earlier verification remains historical evidence, not acceptance of this flow.

## Behavior and ownership

Noticing a portion does not identify it. First identification requires actual
hand inspection or deliberate continuous presentation at Aiko's face. A learned
portion is recognizable at its exact remembered place within notice distance.
Witnessed transport retains continuity; unseen relocation requires identification
again. Another known portion of the same type never replaces the missing one.

One search task collects confirmed missing learned portions, including losses
confirmed during the pass. It survives ordinary approach, pickup, inspection and
put-down. Unknown reachable resting finds are inspected as part of this task.
Verified hand or face evidence resolves the matching missing portion. Other
missing portions retain priority over appetite and ordinary curiosity. Finding
an unreachable but legitimately recognized portion needs no attempted pickup.

Only a complete physical pass with no pending local evidence or unexamined
eligible finds can finish unsuccessfully. A vanished unknown sighting is retired
without a patrol. Lost association alone is not confirmed absence. Unknown
occupancy can postpone a place decision; an identified different portion cannot
prove that the remembered portion is still there.

World owns physical objects/custody. Memory owns learned facts. Awareness owns
sensory evidence. The existing interaction coordinator owns the search task and
the current action; it does not add another coordinator or movement writer.
Route progress belongs to the task rather than a temporary walking phase.
Search data are session-local; the save format stays unchanged.

Readable cues follow evidence: unknown notice, approach, pickup, inspection,
identification, optional reunion, put-down, continuation. Identification does not
imply wanting to consume. Text never invents witnessed player actions.

## Stages

| Stage | Work | Verification | Status |
|---|---|---|---|
| 1 | Give search the lifetime of a task; gather multiple losses; reuse normal investigation and resume the same route. Remove the diagnostic search-position fallback and exclusive single-subject handoff. | Real owner tests for unknown candidate, multiple losses, true reunion, continuation and interruption; typing/lint. | Automatically verified |
| 2 | Align sensory evidence, place checking, face reunion, unreachable finds and final completion. Keep exact-place and witnessed-transport rules. | Combined owner scenarios and isolated native Tk flow; identity only by hands/face; endpoint evidence. | Automatically verified |
| 3 | Replace obsolete expectations and consolidate redundant route/feedback tests. Remove unused helpers/config only after repository usage search; preserve legacy save compatibility and meaningful custody/receipt checks. Align authored cues. | Restart with two close portions, several unseen relocations, face reunion, same-type distinction, both scales; resource tests and static gates. | Automatically verified |
| 4 | Update current contracts and architecture; run final verification and record practical limits. | Complete Windows suite with pinned Python/Pillow; Ruff, strict Mypy, Pyright, diff/docs checks. | Automatically verified; manual acceptance open |

After each stage record results here before continuing. Tests assert observable
rules and complete flows, avoiding duplicated checks of discarded intermediate
states. In particular replace tests that require ignoring an unknown find until
after an unsuccessful search. Keep native custody/frame and durable identity
evidence. Legacy `possible_sources`/`superseded` must not be removed by assumption:
the current codec and old saves still use them.

## Diagnostic baseline

Five in-memory reproductions on the previous implementation confirmed: unknown
finds are skipped; simultaneous losses cause separate full passes; endpoint
arrival can finish before local absence checking; a different known nearby
portion suppresses loss; ambiguous association starts a patrol without confirmed
absence. All 95 existing behavior/awareness/retrieval/perception/absence tests
passed despite these gaps. No live save was touched.

## Delivery ledger

Stage 1: SearchTask now retains the pass and immutable learned subjects across
ordinary candidate episodes. All currently accepted absences enter that task;
a verified reunion removes only its own subject. Candidate reach failure resumes
the same pass; explicit interruption discards it. SearchReadout/search_x and the
special AbsencePhase/FoundPhase classes were removed. Their readable cues use the
existing generic CuePhase. A found portion does not force another pickup or a
consumption decision. Nine duplicate/obsolete tests and one route helper were
removed; search expectations were adapted to real position input and candidate
inspection. A new shared-loss scenario verifies progress survives reunion.

73 behavior/awareness/retrieval tests pass. Ruff 0.13.2, strict Mypy 1.18.2
(184 sources) and Pyright 1.1.414 pass. Sensory refinements and native integration
remain stages 2/3; this does not claim final acceptance. Manual visual/input
acceptance and Linux CI remain separate evidence.

Stage 2: Action commitment no longer erases unrelated local sensing. Unknown or
pending occupancy still delays absence; a positively recognized different
portion cannot hide the missing one. Lost local association releases its action
without starting a patrol. Losing an actually observed held target uses the same
loss cue/task path, replacing the artificial temporary approach and boolean
`confirmed_empty` entry. The search waits for notice/absence evidence and its
initial readable cue before selecting candidates or ending the pass.

Cursor gestures preserve an active search. Motion blocking pauses it; explicit
interruption still cancels safely. Hand/face identification writes ordinary
memory facts, which the task can resolve even after a busy action delays the
reunion response. Found cues require no appetite decision or unnecessary pickup.
Known spatial anchors are excluded from other candidates' nearest-match problem;
this allows a new unknown at an occupied known place to accumulate notice.

188 object tests and all 45 native World GUI tests pass on Python 3.11.9 /
Pillow 11.3.0. The combined native case restarts with two close Dangos and a
learned drink, moves all three during actual apple inspection, then identifies
and reunites each by real pickup/inspection in one search at 1x and 2x. A native
face case reunites a moved drink held at the eyes without taking or consuming it.
The previous pass-by/failure native tests and standalone same-type waiting test
were replaced by these complete flows; blindness and duplicated target-loss
expectations were removed. A tracking assertion about a private sighting token
was replaced with distinct-track behavior; different physical portions still
cannot borrow memory identity (covered by the memory and native scenarios).
Ruff, strict Mypy and Pyright pass. Native tests use temporary saves only.

Stage 3: Repository-wide usage search found no runtime consumer of StockSummary /
summarize_stock, search_seconds or search_stride_widths. They and their exclusive
tests/config contracts were removed. Real legacy reconciliation and its save
round trip remain tested through ObjectMemory, including consumed ambiguous
witnesses. The unused goal parameter on advance_search and another no-op branch
test were removed. Across stages, the object suite shrank from 196 to 185 tests;
the native World suite changes from 45 to 46 while covering the combined flow.

Candidate disappearance/reach failure resumes the existing task. Presenting a
candidate taken during approach now uses the same reunion outcome as presentation
during patrol, without offer/consumption detours. Both native presentation entries
pass. Identification of a missing hand-held portion emits one reunion result,
avoiding consecutive duplicate identification/reunion bubbles. Generic put-down
and failed-pass wording no longer invent future consumption, an empty map or a
witnessed player move. Identity gates and presentation receipts are unchanged.

185 object tests, all 46 native World GUI tests (28.727 s), 24 resource/dialogue
tests, Ruff 0.13.2, strict Mypy 1.18.2 and Pyright 1.1.414 pass. Original/live
save untouched; complete suite and current documentation remain stage 4.

Stage 4, integration: Current architecture/contracts and the isolated manual
checklist now describe shared search. Redundant contradictory search paragraphs
were removed from current contracts rather than adding another competing rule.
Historical delivery ledgers link to this plan. Local links in all five changed
documents resolve. A reconciled memory token cannot add the same learned physical
portion to the task twice; the existing multi-loss scenario checks this invariant.
Ordinary contact respects a committed search; explicit interruption still cancels.

The first complete run executed 1,101 tests in 238.515 seconds. Its only failure
was an obsolete literal "später" expectation in the real-timer put-down test;
the phase order, visible cues and physical result passed. The assertion now
requires a visible put-down cue rather than a particular word. The combined
native scenario additionally includes a genuinely new nonmatching cookie and,
at 2x, an actually removed learned drink. This checks successful investigation
followed by resumed search and one bounded failed pass, not only early success.
Both shared-search cases and both face-presentation entries pass on the user's
Python 3.14.0. A fresh complete pinned run will verify the final source/tests.

Final verification: **1,101 tests passed in 237.518 seconds**, exit code 0, on
Windows / Python 3.11.9 / Pillow 11.3.0. This is the final source and strengthened
native scenarios, including the real-timer put-down assertion. Existing nonfatal
ttk ThemeChanged teardown messages preceded unittest OK. Ruff 0.13.2, strict
Mypy 1.18.2 (184 sources), Pyright 1.1.414, git diff --check and changed-document
links pass. The final 185 object tests also pass on Python 3.14.0, as do both
shared-search scales and both native face-reunion entries. No Linux CI was run.

Relative to the preceding 1,111-test state, 17 obsolete/duplicate tests were
removed and seven focused flow/rule tests added: a net reduction of ten. The
remaining legacy tests cover actual live compatibility, rather than an unused
stock-summary model. No production test gates or workflow files were relaxed.

The four behavior stages are delivered. The isolated human visual/mouse checklist in
[WORLD_SMOKE_TEST.md](WORLD_SMOKE_TEST.md) remains open; controlled native Tk
automation does not claim that acceptance. Restart the running Aiko application
to load the new source. No original save was edited and no commit, push or merge
was made.

## Bounded OOP follow-up

The user reports that the first practical impression is positive. A subsequent
read-only review found no architecture blocker, with 38 architecture/boundary
tests passing. The remaining work is a behavior-preserving refactor of two
maintenance points. The user subsequently authorized stages 5, 6 and 7 separately.
Their delivery and final validation are recorded below.
No merge is authorized.

### 5. Encapsulate SearchTask's own invariants

Current sites: `object_interaction_state.py:SearchTask` and the coordinator's
`can_investigate`, `abandon_candidate`, `search_destination`, `complete_search`,
`_resume_search`, `notice_absence`, `start_search` and `found` methods.

- Make missing subjects, route and excluded candidates private task data.
  Initialization must use the same validated add path as subsequent losses.
- Move matching/removal of one verified subject into a task operation such as
  `resolve(known)`. It must preserve physical-reference matching, legacy
  uncertainty, duplicate suppression and the other missing subjects.
- Let the task own candidate exclusion and actual-position route advancement,
  including changed bounds. Provide only the queries needed by current callers
  (next subject, candidate eligibility, progress/completion); return immutable
  values rather than mutable dictionaries or sets.
- The interaction coordinator continues to own task lifetime, action episodes,
  phase transitions, speech and safe interruption. The task gets no callbacks,
  UI access, world reads, timers or movement execution. Keep the existing file;
  introduce no new service layer or generic state-machine framework.

Acceptance: no caller mutates task collections or assigns its route directly.
Losing/releasing a candidate preserves coverage; reunion removes one subject;
explicit interruption discards the task. Check those rules using the existing
shared-loss, route, reach-failure and native scenarios. Adapt tests to the public
behavior rather than asserting the spelling of private fields. Run the affected
object tests, architecture checks, Ruff, strict Mypy and Pyright; record results
here before stage 6.

### 6. Share identification-result handling

Current sites: `observe_held_offer`, the inspection/recognition branches of
`update`, and the reunion branch of `ObjectBehaviorCoordinator.advance_search`.

- Share the decision whether a confirmed identified portion resolves a missing
  subject. All entries read the same canonical memory facts; none identifies
  from hidden World data or from a goal's claimed type.
- Use a small internal reunion operation for matching, task resolution and its
  one result cue. Reuse it for hand inspection, face presentation and already
  verified remembered findings. Avoid repeated ObjectGoal construction merely
  to announce a fact: goals remain for actual chosen actions.
- Keep identification and completion of a readable cue as distinct events.
  A loss accepted while a recognition bubble is being read must still be
  considered when that receipt completes. Factoring must not remove this
  necessary fresh evaluation or change the existing receipt order.
- Preserve the outcomes: matching find produces one reunion result; other finds
  produce ordinary recognition and safe placement/continuation; presentation
  keeps player custody. Search retains priority over appetite. Ordinary
  interactions keep their current decision and consumption flow.
- Extract only cohesive private methods from the dispatcher. Add no mutable
  "already handled" flags, new phases, result framework or hand/face strategy
  hierarchy. No dialogue catalogue or save-format changes belong to this step.

Acceptance: the same learned portion has the same matching semantics through
both identification paths, without forcing a pickup, duplicate result speech,
early consumption or route reset. Reuse the existing native shared-search tests
at both scales and both face-presentation entries. Retain the current real-timer
cue order/dwell and custody tests. Replace obsolete API-shaped assertions if a
fact-based reunion entry removes the synthetic goal; do not add another edge-case
matrix. Run affected tests and the same static gates; record results here.

### 7. Verify the unchanged practical behavior and close the follow-up

- Update architecture wording only where ownership or method contracts changed.
  Preserve stages 1–4 as evidence, without duplicating their behavior rules.
- Run the complete Windows suite with Python 3.11.9 / Pillow 11.3.0, Ruff
  0.13.2, strict Mypy 1.18.2 and Pyright 1.1.414. Check local documentation links
  and `git diff --check`. Run the combined native flows on Python 3.14.0 too.
- Use temporary saves; preserve the user's ordinary save and current local work.
  Human acceptance remains separate. Keep the existing practical checklist and
  ask for further user observations only after a concrete, verified result.
- No test-count target: remove a test only when its rule is obsolete or covered
  by an equivalent retained scenario. Preserve identity, custody, receipt and
  old-save compatibility guarantees. Do not relax test gates or workflows.

| Follow-up stage | Status | Exit evidence |
|---|---|---|
| 5 — Task encapsulation | Implemented and automatically verified | Existing task/route behavior and static boundaries pass; direct task writes eliminated. |
| 6 — Shared result handling | Implemented and automatically verified | Shared hand/face/remembered results, continuation, readable-cue timing and custody pass; synthetic reunion goals eliminated. |
| 7 — Final validation | Complete and automatically verified | 1,102 Windows tests, 52 additional Python 3.14 native tests, static gates and local file/heading links pass; documentation-only changes, no merge. |

Planning baseline: the named consumers and existing scenarios were checked
against source before implementation. The initial planning addition changed
documentation only. The implementation ledger below records authorized work.

### Stage 5 delivery and verification

SearchTask now owns private missing-subject, route and excluded-candidate data.
Its constructor uses `add` for the initial learned subject. `resolve` matches and
removes exactly one subject through the unchanged physical-reference/legacy
matching rule. `exclude_candidate` and `can_investigate` own candidate eligibility;
`destination` owns the same actual-arrival and changed-bounds route algorithm.
Read-only next-subject/progress/completion queries expose immutable facts only.

ObjectInteractionCoordinator uses those operations without touching the task's
collections or assigning its route. It still owns creation/disposal, action
episodes, cue receipts, phase changes and safe interruption. This stage changes
only the existing task/coordinator implementation and this ledger. The existing
ObjectGoal reunion entry and repeated identification-result handling remain for
stage 6. No new phase, service, timer, save field or movement writer was added.

Verification on Windows / Python 3.11.9 / Pillow 11.3.0:

- All **185 existing object tests** pass, including shared losses, duplicate
  physical references, reconciliation, route coverage/changed bounds, candidate
  failure, unknown-loss retirement, legacy history and interruption.
- All **38 architecture/boundary tests** pass.
- All **46 native World GUI tests** pass in **30.578 seconds**, exit code 0.
  These include the close-portion cold restart and shared-search flows at 1x/2x,
  a nonmatching find and actual missing portion, both face-reunion entries,
  observed transport, and physical pickup/put-down.
- Ruff 0.13.2, strict Mypy 1.18.2 (184 sources), Pyright 1.1.414 and
  `git diff --check` pass. Repository usage search confirms task internals are
  accessed only inside SearchTask; its two creation sites use the new constructor.
- Existing tests were reused unchanged; no test or gate was added, removed or
  relaxed for this encapsulation. The scoped diff against the stage-5 starting
  files confirms unchanged matching rules and route calculations, and no speech,
  perception, custody, consumption or desktop-input changes.

Native tests used temporary saves. No original save was edited; no commit, push
or merge was made. The complete-suite result above belongs to stages 1–4; a new
full-suite run and Python 3.14 native handoff remain scheduled for stage 7.
The user's positive initial practical feedback is not a claim of a new manual
test after stage 5. At this handoff, stage 6 had not started.

### Stage 6 delivery and verification

All identification entries now use the coordinator's `_reunite` operation for
task resolution and the single `object_found` cue. Hand inspection and face
presentation share `_announce_identification`; the readable recognition receipt
uses `_complete_recognition` to query current memory and reconsider losses
accepted during that cue. A nonmatching find is assessed and safely placed, or
released from the episode when the player owns it; ordinary use keeps its
existing decision path.

The patrol entry `found(record)` reads canonical memory and reports whether it
resolved a subject. Behavior no longer constructs or adopts an ObjectGoal merely
to announce reunion. Chosen investigations still adopt an actual goal; that
method's docstring now describes its remaining caller. The redundant matching
queries were removed after repository-wide usage search; SearchTask's matching,
resolution, subject collection and route algorithms are unchanged. No new
mutable flag, phase, timer, service, movement writer, catalogue or save field
was introduced.

Verification on Windows / Python 3.11.9 / Pillow 11.3.0:

- All **186 object tests** pass. Two obsolete goal-shaped assertions now use
  the record entry. One focused sequence additionally verifies a loss accepted
  during the recognition cue: wait for its receipt, emit one reunion result,
  retain hand custody, put down without consumption and resume the other loss.
  That sequence also passes with the pre-stage-6 coordinator and task matching
  API, confirming preserved behavior. No other test was removed or relaxed.
- All **38 architecture/boundary tests** pass.
- All **46 existing native World GUI tests** pass in **31.687 seconds**, exit
  code 0, including close-portion cold restart and shared-search flows at 1x/2x,
  both face-reunion entries, same-type physical distinction and custody.
- Ruff 0.13.2, strict Mypy 1.18.2 (184 sources), Pyright 1.1.414 and
  `git diff --check` pass. A scoped comparison against the stage-5 starting files
  confirms the unchanged task algorithms and that the intention-owner change
  is a docstring correction only.
- All **6 existing real-timer World flow tests** pass in **96.801 seconds**,
  exit code 0. They retain actual Tk timers, readable cue order/dwell, animation
  completion, ordinary investigation and consumption, handover, safe sleep
  interruption and restart custody. The known non-failing Tk `ThemeChanged`
  teardown messages appeared; no test was skipped or failed.

Native tests used temporary saves; the ordinary save was untouched and existing
local work was preserved. No commit, push or merge was made. The full-suite run,
Python 3.14 native handoff and final architecture wording remain stage 7 work.
No new manual acceptance was claimed. At this handoff, stage 7 had not started.

### Stage 7 final validation

Architecture wording now describes SearchTask's private invariants and route
operations, the coordinator's task/phase/receipt ownership, the shared fact-based
reunion entries and fresh evaluation after a readable recognition cue. Stale
focus-blindness, single-subject and blocking language was aligned with the
existing shared search. Two stale links in older ledgers now point to their
renamed historical checklist/evidence sections. Historical stages 1–6 and the
human smoke checklist remain intact. This stage changes documentation only;
application code, tests, catalogues, save formats and workflows are preserved.

Verification completed on 18 October 2026:

- Ruff **0.13.2**, strict Mypy **1.18.2** (184 sources) and Pyright **1.1.414**
  pass. All **190 local Markdown file targets** and **15 heading anchors** across
  31 root/docs Markdown files resolve. `git diff --check` passes.
- Complete Windows suite: Python **3.11.9**, Pillow **11.3.0**, Tk **8.6**;
  all **1,102 tests** pass in **240.569 seconds**, exit code 0, with no skipped
  tests. This includes the architecture, memory/save compatibility, identity,
  custody, feedback-receipt and actual-timer checks.
- Combined native World GUI and real-timer flows on the installed Python
  **3.14.0**, Pillow **12.3.0**, Tk **8.6** runtime: all **52 tests** pass in
  **127.438 seconds**, exit code 0, with no skipped tests. These include the
  close-pair cold restart and shared multi-loss search at 1x/2x, both face-reunion
  entries, witnessed transport, physical pickup/put-down, readable cue order/dwell,
  consumption, interruption and restored custody.
- The complete Python 3.11 run emitted the already known, non-failing Tk
  `ThemeChanged` teardown messages; the final test result was successful.
- A SHA-256 comparison of all 788 repository files present at stage-7 start
  confirms only four documentation files changed: this ledger, architecture
  wording and the two older ledgers' broken anchors. The other 784 files,
  including application code, tests, resources, workflows and the manual
  checklist, are byte-identical. No new repository file was introduced and
  no test or gate was added, removed or relaxed in this stage.

Native scenarios used temporary saves; the ordinary save was not edited and
existing local work was preserved. Human visual/input acceptance
remains separate from automated results, using the existing
[practical checklist](WORLD_SMOKE_TEST.md). No new manual acceptance or remote
CI run is claimed. Stages 5–7 are complete; no commit, push or merge was made.
