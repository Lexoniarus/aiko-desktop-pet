# Object investigation and taskbar search delivery plan

> **Historical record, archived 2026-10-18.** This delivery/review snapshot is
> completed or superseded and is not an active plan. Its old pending checks,
> future proposals and push/merge restrictions describe that revision only.
> Use the [current documentation](../README.md) and
> [current World rules](../WORLD_OBJECT_CONTRACTS.md) for maintained guidance.

Historical delivery ledger. The current
[shared search/investigation plan](OBJECT_SEARCH_SIMPLIFICATION_PLAN.md)
supersedes the exclusive single-subject, phase-owned-route and ignored-candidate
rules below. Earlier green tests did not establish the combined desired flow.

Recorded: 18 October 2026. Baseline: `fb4f357`, `feature/world-foundation`.
Status: stages 1–8 automatically verified. Manual native acceptance open.
No merge authorized.

This implements the agreed distinction between a fleeting unidentified sighting
and learned object identity. It supersedes the two-second local-search and
alternate-supply replacement rules in [World contracts](WORLD_OBJECT_CONTRACTS.md)
and the historical [World OOP follow-up](OOP_WORLD_FOLLOWUP_PLAN.md). The ledger
below separates delivered behavior from the remaining targets.

## Accepted behavior

- An investigation needs a current executable association. A remembered unknown
  place alone cannot retain an approach indefinitely. Pending notice evidence
  may settle; an ambiguous or forgotten target releases the old action.
- Confirmed loss of an unidentified sighting ends its investigation and retires
  the fleeting record after a short readable loss response. It starts no patrol.
- An identified target retains its learned identity after loss. Its search takes
  priority over ordinary new-object investigation, independently of appetite.
- A search starts at the nearer reachable taskbar end and then walks to the other
  end. Only actual arrival at both ends completes the pass; elapsed time alone
  never means searched. Search movement uses ordinary speed and reach bounds.
- New objects can be noticed during the search but cannot replace its subject.
  Only a currently observed, identified matching target is a successful find.
  A different/unknown candidate cannot inherit the searched identity by location.
- A completed unsuccessful pass leaves known history missing/unresolved and
  releases ordinary curiosity. It does not immediately restart the same pass.
- Sleep, games, explicit user interruption and safe custody retain their existing
  precedence. No movement continues behind a blocked interaction. Native input,
  source-frame reach, real holding, handover origin and cue receipts stay intact.
- Hidden World identity/existence never supplies subjective recognition or loss.
  Ending an unexecutable action is distinct from claiming a place is empty.

## Ownership and phase contract

| Owner | Responsibility |
|---|---|
| ObjectAwareness | Current sensory association, unresolved local sightings and confirmed empty-place evidence. |
| ObjectMemory | Learned identity/history and retiring fleeting unidentified records. |
| ObjectIntentions | Eligible ordinary wishes; never retain a vanished memory as a committed goal. |
| ObjectInteractionCoordinator | One episode/phase owner, receipt gates, search subject and route progress, completion/interruption. |
| ObjectBehaviorCoordinator | Resolve executable approach targets, keep search priority and translate application facts into instructions. |
| DesktopWorldRuntime | Supply reachable route bounds/current position; execute walking/gaze and report real arrival. |

No second live memory, target queue, clock or state machine is introduced.
The search route is ephemeral phase data; save schema and PetState are unchanged.
Phases and authored feedback must match actual work: notice, approach, real grasp,
held inspection; or loss notice, route search, verified find/unsuccessful completion.

## Delivery stages

| Stage | Deliverable | Required verification | Status |
|---|---|---|---|
| 1 | Resolve orphaned approaches through explicit sensory target evidence; release invalid unknown targets; keep pending observations and learned identity safe. | Close unknown pairs after a tracking gap, forgotten committed memory, pending recognition and existing acquisition/continuity suites. | Automatically verified |
| 2 | Replace timed/local searching with phase-owned taskbar route and fixed subject priority. | Both actual endpoint arrivals, no timer completion, stationary/blocked search, different/unknown discoveries, genuine matching find and interrupted route. | Automatically verified |
| 3 | Finish unknown-loss lifetime, native phase/feedback integration and current documentation. | Three-object relocation with real Tk at 1x/2x, unknown loss versus known search, cue/animation order, full suite and quality gates. | Automatically verified; manual acceptance open |

After each stage run affected tests plus Ruff 0.13.2, strict Mypy 1.18.2 and
Pyright 1.1.414. Record results before continuing. Run the full Windows suite on
explicit Python 3.11 with Pillow 11.3.0 at final integration. CI Python 3.13/Linux
and manual native interaction remain separate evidence; do not claim them from
local checks. Preserve existing repository work; no merge or main-branch changes.

## Diagnostic baseline

A controlled native Tk reproduction with three portions demonstrated the orphan:
while Aiko inspected the first, two nearby unknown memories lost their tracks.
The physical portions acquired new records; the old selected record retained
approach with no instance binding, while local occupancy prevented absence.
The same fault occurred with stationary nearby portions after focused inspection;
more widely separated portions resumed pickup. A headless continuation still
retained the goal after its original unknown memory expired beyond 700 seconds.
The existing 106 focused tests passed without detecting this combined case.

## Verification ledger

### Stage 1

Added current target evidence to the existing awareness owner. Completed local
sightings with different records can invalidate an unknown action; pending
notice alone cannot. Learned ambiguous targets retain identity and enter the
existing search owner without claiming that their old place is empty. Intentions
release a committed goal whose memory no longer exists.

- 130 focused awareness/tracking/stock/memory/absence/intentions/behavior/
  retrieval/interaction tests passed on Python 3.11.9, including three new cases.
- All 34 native World GUI tests passed in 21.597 seconds.
- Ruff 0.13.2 passed; strict Mypy 1.18.2 passed 184 source files; Pyright 1.1.414
  reported zero errors/warnings. Existing source-frame acquisition stayed intact.
- Search still uses the historical route until stage 2; unknown confirmed-loss
  lifetime changes remain stage 3. No commit, push or merge was made.

### Stage 2

SearchPhase owns an immutable two-leg route, initialized from current native
body-center bounds. Actual position observations advance it; changed geometry
rebases coverage. Search progress now means endpoint coverage (0, 0.5, 1), not
elapsed seconds, and is zero outside the active route. Constructor search_seconds
was removed from all repository callers after usage search. Historical balance
keys remain readable but no longer drive route duration or stride.

Search priority no longer accepts arbitrary alternate supply. Only currently
observed matching learned identity can announce a find; full needs do not prevent
recognizing a reunion. The canonical intention owner adopts that verified goal.
Unknown/different finds remain observations. Blocking still safely interrupts.
The desktop translates the route endpoint directly to its standing goal; search
counts as committed movement for the existing walk adapter.

- 137 focused tests passed on Python 3.11.9, including route coverage, right-side
  start, geometry changes, stationary search and matching-but-unwanted reunion.
- All 34 native World GUI tests passed in 19.775 seconds. Existing known-loss
  component cases now supply actual native endpoint arrival rather than time.
- Ruff 0.13.2, strict Mypy 1.18.2 (184 sources) and Pyright 1.1.414 passed.
- Unknown confirmed loss still has its historical response pending stage 3.
  No commit, push or merge was made.

### Stage 3

Unknown ordinary wishes now require current observation. Missing bindings hold
movement while pending perception settles; completed unresolved unknown places
release their old action. ObjectMemory retires superseded unidentified local
records only for new completed sightings, preserving currently observed and
learned neighbours. Confirmed unknown loss finishes its readable notice and then
forgets the record without patrol. Known pending losses are handled first.

The three existing search dialogue lines now describe a complete taskbar pass.
The current architecture and World contract document the revised phase/lifetime
rules; older dated plans remain historical. Source-frame pickup, physical custody,
PetState, save schemas, balance values and image/animation assets are unchanged.

- 141 focused owner/dependency/World-access tests passed on Python 3.11.9.
- Four new native cases cover the original three-object relocation and full
  search walking with a novel discovery at both 1x and 2x. They exercise actual
  native placement and the existing WalkDriver with controlled elapsed input,
  random walking disabled and incidental attention active. The first overall
  run passed all 38 World GUI cases but exposed an outdated World-access test
  double lacking the new searching read. Its protocol fixture was corrected;
  the final full run includes that correction and the memory-cleanup changes.
- Final Ruff 0.13.2, strict Mypy 1.18.2 (184 sources) and Pyright 1.1.414 passed.
- Final complete Windows/Python 3.11.9 suite with isolated Pillow 11.3.0:
  1,091 tests passed in 230.277 seconds, exit code 0. This includes all 38 native
  World GUI scenarios and existing actual-timer playback/runtime cases. Known
  nonfatal ttk ThemeChanged teardown diagnostics were printed before unittest OK.
- Local documentation links and git diff --check passed. New CI Python 3.13/Linux
  runs were not dispatched; no remote green result is claimed for these changes.
- Manual Windows visual/input acceptance remains open: use an isolated save at
  both scales, move several unknown portions during inspection, verify the
  known-item route really traverses both ends, readable bubbles, interruption,
  sleep/game safety and resumption of ordinary curiosity after failed search.
- No commit, push or merge was made. Main is untouched.

## Restart association correction (18 October 2026)

The previous green checks missed repeated identification of already learned,
nearby portions after restart. Read-only inspection confirmed the active default
save retained and decoded all 40 records. A controlled Tk replay identified the
same two physical portions four times each, growing memory from 40 to 48.
A minimal saved pair with one learned record each was stable at 108 px spacing
but looped at 40 px, growing two records to ten. A moved-pair snapshot still
looped. Ground observations also borrowed an incorrect old type at an occupied
remembered place. These are association/lifecycle failures, not missing JSON.

### Binding identification and recognition rule (user clarification)

First identification is possible only in Aiko's hands or through deliberate,
sustained cursor presentation directly in front of her face. An already learned
physical portion can be recognized at the ordinary notice distance and after
restart only at its exactly remembered place. An unobserved relocation requires
hand/face identification again at the new place. Remembering a catalog type is not enough
to recognize an arbitrary new portion of that type.

- ObjectPerception remains the sole first-identification policy (hand/face).
- ObjectMemory stores an optional learned physical reference alongside identity,
  assessment and last observed place. That reference is acquired only from a
  completed identifying observation, never by matching a position or catalog ID.
- ObjectAwareness supplies references only for candidates that actually pass
  attention, range and notice-time gates. Recognition of a learned reference can
  restore its binding only at the exactly remembered place. Observed custody
  and placement can update that place; an unseen move cannot. Saved World data
  alone cannot refresh unseen locations or establish absence.
- Unidentified sightings cannot borrow learned identity by proximity. The
  spatial tracker still owns unknown continuity; it does not become an identity
  oracle or a second durable memory. Known bindings no longer depend on one
  focused spatial track surviving every inspection phase.
  At exactly coincident known places, acquired references may anchor surviving
  tracks so geometric ties do not reset notice dwell forever. Unknown ties and
  real sensory gaps still create fresh tracks; references cannot bypass dwell.
- ObjectInteractionCoordinator remains the only phase/receipt/custody owner.
  First identification and later recognition remain distinct: learned portions
  do not restart inspection merely because focus or process state changed.
- The memory codec writes v3 with validated learned references, reads v1/v2
  without inventing them, and retains allocation provenance. Legacy ambiguous
  history remains until evidence resolves it; old saves may need one hand/face
  identification per physical portion to acquire the previously absent link.

No blanket deduplication or edit of the user's live save is part of the fix.
Replays must show bounded records and eventual idle even with accumulated legacy
history. PetState, movement ownership and World mutation contracts stay intact.

### Correction stages

| Stage | Deliverable | Verification | Status |
|---|---|---|---|
| 4 | Add learned physical references to the memory owner and v3 codec; block identity inheritance by place. | Hand/face-only acquisition; distinct same-type portions; unknown replacements; save/load, legacy migration, invalid/duplicate references and rollback. | Verified |
| 5 | Integrate gated recognition and focused phase continuity using learned references. | Close pairs, exact-place recognition inside/outside notice range, unseen relocation and reidentification, focus changes, unknown replacements and search reunions. | Verified |
| 6 | Add saved-session native restart regressions and update current contracts. | Two nearby learned portions at 1x/2x; full clips/receipts; same-type pair; moved/replaced portion; repeated save/load; isolated real-save replays; complete Python 3.11/Pillow suite and static gates. | Automatically verified; manual acceptance open |

After each stage record checks and outcome below before proceeding. Controlled
native replay and manual visual acceptance are separate evidence. No commit,
push, merge or original-save modification is part of this delivery.

### Correction verification ledger

Planning baseline: existing local changes preserved. Diagnostic snapshots and
replay scripts are outside the repository; no live-save data enters fixtures.

Stage 4: ObjectMemory stores the acquired reference in its existing immutable
knowledge/checkpoint; v3 serialization validates allocation and uniqueness.
V1/v2 retain history with no invented reference. Unknown observations cannot
borrow learned types or acquire references. A verified same-portion reunion can
transfer history while preserving the active episode record. Unknown relocation
does not refresh the old learned place. All 70 memory/codec/persistence/stock/
perception/interaction tests passed on Python 3.11.9/Pillow 11.3.0, including
failure-injected custody rollback. Ruff 0.13.2, strict Mypy 1.18.2 (184 sources)
and Pyright 1.1.414 passed. Runtime integration follows in stage 5.

Stage 5: the awareness bridge now supplies the physical reference only after
normal attention/range/notice gates produce an observation. The memory owner
reuses its acquired record at the exact remembered place, independently of
session-local focus tracks. A changed ground place remains unidentified; hand
reidentification retains the active episode record and recovers earlier history.
Observed cursor/custody continuity still works. Tests cover close different/same
types, alternating focus, notice gating, unseen relocation and a different
physical portion replacing the old one. Earlier known-history fixtures now seed
the acquired reference explicitly; the replacement case asserts unknown notice
and both notice/approach receipts, rather than the former wrong borrowed name.

All 192 object tests and all 38 native World GUI cases passed on Python 3.11.9/
Pillow 11.3.0. Ruff 0.13.2, Mypy 1.18.2 and Pyright 1.1.414 passed. A preliminary
controlled replay of the original legacy snapshot identified each of its six
portions once and became idle (44 records, no repeated identification), while
conservatively retaining ambiguous old history. Durable restart integration and
the final complete suite follow in stage 6.

Stage 6, focused integration: new native tests learn two nearby portions through
actual pickup/inspection/put-down clips, then perform two cold restarts with no
new inspection, extra record or allocator growth. They cover 1x/2x and same-type
portions. An additional control exposed exactly coincident learned portions
resetting geometric tracks before notice dwell could complete. The tracker now
accepts acquired-place anchors only for already learned visible candidates;
unknown ties and actual gaps retain fresh tracks. Headless same/different-type
overlap controls and a native coincident same-type restart guard cover this.
The relocation unit case additionally checks a 0.001-pixel change, not proximity.

- All 193 object tests and all 42 native World GUI cases passed.
- Ruff 0.13.2, strict Mypy 1.18.2 (184 sources) and Pyright 1.1.414 passed.
- An initial complete run passed 1,103 tests in 234.546 seconds before the final
  coincident-track correction. The final complete Windows/Python 3.11.9 suite
  with Pillow 11.3.0 passed **1,105 tests in 235.608 seconds**, exit code 0.
  This includes the native regressions and existing real-timer runtime flows.
  Existing nonfatal ttk ThemeChanged teardown diagnostics preceded unittest OK.
- Both unchanged legacy diagnostic snapshots now identify each physical portion
  exactly once and reach idle. Original snapshot: 40 to 44 records; moved
  snapshot: 45 to 47. Ambiguous learned history is retained conservatively.
  Reloading the resulting moved-snapshot v3 save produces zero feedback events,
  zero further identifications, six current observations, the same 47 records
  and the same next-record counter (280) over another 54 controlled active seconds.
- Replays use isolated copies and real Tk/clip/cue owners with controlled elapsed
  time and unrelated automation disabled; the ordinary save is never written.
  Snapshot hashes still match the read-only diagnostic baseline. Current
  architecture/contracts and local documentation links are updated.
- Final source passed Ruff 0.13.2, strict Mypy 1.18.2 (184 sources), Pyright
  1.1.414 and git diff --check. The original pre-move snapshot was replayed
  again on final source: six one-time identifications, 44 records and idle.
- Manual visual/input acceptance remains open: on an isolated save at both
  scales, check readable notice versus identification cues, close placements,
  known exact-place recognition, unobserved moves, first identification by
  hand/face and the existing known-loss priority/search route. Automated native
  tests do not claim this human acceptance or fresh Linux/CI evidence.
- Restart the running application to load the changed source. A v1/v2 save may
  need one permitted identification per physical portion to learn its previously
  absent reference. New v3 saves retain that learning across restarts. No live
  save was edited and no commit, push or merge was made.

## Observed cursor transport and same-type search subjects

The next native report exposes two distinct continuity failures. A clean native
reproduction already confirms the first: take and release between perception
samples loses a known Dango, emits missing/search and creates a new unknown
record. A sampled held frame prevents the failure. The exact-place recall rule
must apply to unseen relocation, not override an explicitly witnessed cursor
take whose spatial track still survives. The second report concerns an absent
Dango being replaced as the search subject by a different already known Dango.
At the diagnostic baseline, search matched catalog type/kind and lost the
physical distinction.

| Stage | Change | Checks | Status |
|---|---|---|---|
| 7 | Commit witnessed take to the existing awareness/memory owners; preserve surviving transport through release/settling even without a held sample. No new phase or tracking timer. | Native fast take/drop at 1x/2x, sampled holding, repeated placement, attention loss and unseen-move negative controls. | Automatically verified |
| 8 | SearchPhase retains its immutable learned subject; match a learned physical reference rather than any other portion of the same catalog type. Guard direct found transitions too. | Two known same-type portions, unseen movement while busy, no false reunion/new identification; verified actual reunion after old-record reconciliation. Full suite and static gates. | Automatically verified; manual acceptance open |

First identification still requires hands or face presentation. Unknown items
gain no type from transport. Real tracking/attention loss still releases current
execution evidence. Keep the original save untouched and record each stage's
results before proceeding. No merge.

Stage 7: ObjectAwareness.follow_taken now records the actual witnessed custody
change through ObjectMemory.note_acquired immediately, using supplied active
time. The same surviving cursor track can therefore finish placement even when
there was no sampled held frame. No extra flag, phase, registry or timer was
added. Three consecutive native moves at each scale retain the same record,
identity and final pose with no missing/search/new-notice cue. All 44 World GUI
cases and 18 awareness tests passed, including prior sampled holding, loss and
unseen-relocation controls. Ruff 0.13.2, Mypy 1.18.2 and Pyright 1.1.414 passed.
The next same-type native regression still fails as expected before stage 8:
the wrong Dango is announced as found and ordinary approach resumes.

Stage 8: SearchPhase now captures the existing immutable knowledge value of the
searched subject, including its learned physical reference. Catalog type/kind
alone cannot substitute another already learned physical portion. Both ordinary
candidate selection and the coordinator's direct found transition use this same
predicate. Capturing the subject also keeps a real reunion possible when
hand/face verification reconciles away its original memory record. Historical
unbound legacy subjects retain their existing type uncertainty; no reference is
invented for them. This introduces no new phase or persistent state.

The native two-known-Dango regression failed before this correction and now
retains search on the missing reference, leaves the other Dango's record intact
and never emits false found/recognized/new-notice feedback. The unobserved find
at the new place remains unidentified. The take regression additionally checks
both identified and unknown portions before any held-frame sample: witnessed
custody never grants first identification. All 196 object tests and 45 native
World GUI cases passed on Python 3.11.9/Pillow 11.3.0. Ruff 0.13.2, strict Mypy
1.18.2 (184 sources), Pyright 1.1.414 and git diff --check passed.

Final Windows/Python 3.11.9/Pillow 11.3.0 complete suite: **1,111 tests passed in
236.312 seconds**, exit code 0. Existing nonfatal ttk ThemeChanged teardown
diagnostics preceded unittest OK. After the full run, the same-type native case
was strengthened to move the Dango while Aiko actually inspects an unrelated
apple, then finishes its decision/put-down before reacting to the missing Dango.
That stronger case passed in fresh processes on both Python 3.11.9/Pillow 11.3.0
and the user's Python 3.14.0 runtime. Both repeated fast-transport cases also
passed on Python 3.14.0. Production code was unchanged during that strengthening;
fresh Ruff/Pyright checks passed for the final fixture. Documentation links and
git diff --check passed.

This is controlled native automation with real Tk/clip/receipt owners, not a
claim of manual mouse/visual acceptance. The isolated manual checklist remains
open for both scales, including observed relocation versus genuine loss while
occupied. No original save was edited; no commit, push or merge was made. Restart
the running application to load these source changes.
