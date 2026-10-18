# Object behavior ownership cleanup

Recorded: 18 October 2026. Baseline: `feature/world-foundation`, `c7958fa`.
Status: all three stages implemented; final full regression pending. No merge authorized.

## Purpose and protected behavior

This follows the [orientation and continuity delivery](OBJECT_ORIENTATION_AND_CONTINUITY_PLAN.md)
and its subsequent read-only OOP review. The user reports that practical behavior
now matches expectations. Preserve that flow; the occasional pre-approach pause
is not a timing change in this cleanup. The current notice sequence waits for its
readable receipt, after the required learned-place orientation.

Preserve separate learned identity, appraisal, current wish, observed continuity,
committed episode, confirmed absence, and enclosing search lifetime. A search
remains active during candidate inspection. Preserve hand/face identification,
physical custody/reach, exact-place recall, named loss receipts, same-type
ambiguity, persistence compatibility, and exactly-once consumption. No changes to
dialogue, durations, balance, saves, native input, or movement ownership.

Follow [CONTRIBUTING](../CONTRIBUTING.md), the [architecture](ARCHITECTURE.md),
and the [branch workflow](GITHUB_WORKFLOW.md). Keep English technical documents,
identifiers and commits; authored German dialogue stays unchanged.

## Three implementation stages

| Stage | Change | Proof and verification |
| --- | --- | --- |
| 1: interruption ownership | Keep bound-activity invalidation in `ObjectBehaviorCoordinator`. Remove the duplicated `object`/`unavailable` reset inside `OrientationProgress.advance`. | The coordinator is the sole production caller and admits progress only when not bound. First add a coordinator regression for interruption partway through the right look, both foreign activity and real witnessed transport. Verify fresh left/right dwell after release, preserved knowledge, and no loss invented during focus. Only then retire the isolated reset test. Run object and native focus/transport regressions plus pinned static gates. |
| 2: redundant search guard | Remove the later `checking_absence` condition around `complete_search`. | Earlier absence/notice checks already return; the intervening route calculation changes only `SearchTask` and cannot mutate Awareness. Retain the early evidence guard, route-completion guards, and all search tests. Run route, candidate, later-loss and object regressions plus pinned static gates. No test for an unreachable second branch. |
| 3: readable observation pipeline | Extract target-loss handling, accepted-loss feedback, and gaze selection into named private coordinator methods. Share the existing followed-knowledge read used by observation and orientation. | Preserve statement order, evidence snapshots, early returns, feedback acknowledgement, and synchronous offer boundary. Keep the orientation decision in its current owner. Add no coordinator, persisted flag, timer, or duplicate wish. Compare application traces before/after extraction, run object/architecture and native timer/restart checks, then the full suite and pinned static gates. |

The test cleanup is deliberately narrow: replace one isolated lifecycle-reset
test with its owner-level regression. Wrong gaze/time-gap, Memory evidence-order,
occupied-place, wanted/unwanted, restart, and feedback tests remain. Tests of the
new private method names would merely mirror the refactoring and are not needed.

## Small commits and checks

1. Commit this plan before source changes.
2. Implement and verify each stage separately. Include its tests in the same code
   commit, then update this ledger before proceeding to the next stage.
3. Verify exported Git-index snapshots, rather than relying on unrelated dirty
   files. Use Python 3.11.9 with Pillow 11.3.0, Ruff 0.13.2, strict Mypy 1.18.2,
   and Pyright 1.1.414. Run Tk tests sequentially with isolated temporary saves
   and the established main-thread collection harness.
4. At completion run the full suite, static gates, Markdown link/anchor validation,
   UTF-8 decoding and `git diff --check`. Record actual results, not estimates.
   Keep practical user feedback distinct from automated native verification.
5. Leave changes committed locally, with no push or merge. Do not touch the normal
   save or create a new runtime/GUI test runner in the repository.

## Delivery ledger

| Stage | Status | Commit and evidence |
| --- | --- | --- |
| Planning | Recorded | Baseline inspected; worktree clean. Three review findings scoped above. |
| 1 | Complete | `ea93518`; 213 object and four native focus/transport tests pass, plus all static gates. |
| 2 | Complete | `8c3e225`; 213 object tests and all static gates pass. |
| 3 | Targeted checks complete | `b2a51c0`; 250 targeted tests, 257 identical trace events and all static gates pass. Full regression pending. |

All implementation and verification results will be recorded here after each stage.

### Stage 1 evidence

The new coordinator regression passes on the unchanged baseline before reset
removal. It interrupts a partly completed right look using foreign activity or a
real successful take of learned stock, then returns actual cursor custody to the
floor. Neither interrupted time nor the earlier left look can complete the new
sequence. Identity persists; no false loss or feedback is emitted. This replaces
`test_bound_activity_resets_the_check_without_borrowing_its_elapsed_time` at its
actual lifecycle owner. Progress retains gaze/gap/dwell handling and validation.
The exported staged tree passes 217 tests in 4.250 seconds, including native
petting/conversation exclusion and witnessed relocation at 1x/2x. Ruff, strict
Mypy (187 sources), and Pyright pass. No dialogue, duration, or save changes.

### Stage 2 evidence

Only the later dominated `checking_absence` condition was removed. The early
absence/notice return remains. `search_destination` mutates only the existing
route and invokes no Awareness-changing callback; `complete_search` retains its
own readiness/actual-route-completion guards. No reachable search test is removed
or added for the dead condition. The exported staged tree passes 213 object tests
in 0.950 seconds, including endpoint evidence, later losses, candidate resumption,
wanted/unwanted recovery and actual arrival at both route ends. Ruff, strict Mypy
(187 sources), and Pyright pass.

### Stage 3 evidence

`observe` now has 84 lines instead of 136. Named private steps handle approach
association loss, accepted loss feedback and gaze selection; a shared read-only
query obtains the followed knowledge. The same coordinator owns orientation and
samples pre-observation evidence. Early exits, receipt handoff, search priority,
current wish and synchronous offer ordering remain unchanged. No state, mode,
timer, saved field, tuning parameter or dialogue line was added or changed.

A temporary external probe records 257 application-boundary events across the
213 object tests. Before/after extraction, return values, phases, focus/record,
search lifetime/progress, current wish, memory, observations and pending losses
are identical. The probe is not added as a repository test or runner. The exported
staged tree passes 250 targeted tests in 39.102 seconds: 213 object tests, 31
architecture checks, and six native close-portion restart, observed relocation
and actual conversation/missing-bubble timer cases. Both display scales are
covered. Ruff, strict Mypy (187 sources), and Pyright pass. The complete regression
and final documentation checks follow before this stage is marked complete.

### Final fixture refinement

The interruption regression now derives the host `carrying` fact from its actual
USER_HELD custody snapshot. The first version left that host fact at its default,
although tracking already made the same update bound. This corrects the fixture's
production context without changing application code or expected behavior. The
first validation caught a trailing-comma syntax error in this test refinement;
the initial success note was premature. The corrected exported snapshot passes
213 tests in 0.922 seconds, all three static gates, and the same 257 trace events.
Only these corrected results finalize the unpublished fixture commits. The
complete suite then runs on this final test/source combination; the earlier
in-flight full run is not substituted for validation of the edited fixture.
