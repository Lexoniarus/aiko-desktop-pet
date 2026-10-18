# Object behavior ownership cleanup

Recorded: 18 October 2026. Baseline: `feature/world-foundation`, `c7958fa`.
Status: planning recorded; implementation authorized. No merge authorized.

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
| 1 | Pending | Coordinator-level interruption proof precedes reset removal. |
| 2 | Pending | Retain all reachable search contracts. |
| 3 | Pending | Behavior-preserving extraction and final validation. |

All implementation and verification results will be recorded here after each stage.
