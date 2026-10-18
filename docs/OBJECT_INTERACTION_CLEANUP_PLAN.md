# Interaction ownership review cleanup

Recorded: 18 October 2026. Baseline: `063837a`, `feature/world-foundation`.
Status: the four scoped cleanups are complete and locally verified. All work stays local; no push or merge authorized.

Follow [architecture](ARCHITECTURE.md), [contribution rules](../CONTRIBUTING.md)
and the completed [interaction availability plan](OBJECT_INTERACTION_AVAILABILITY_PLAN.md).
Keep historical validation results in that plan unchanged.

## Scope and invariants

Preserve the working behavior: passive hover opens the UI without interrupting a
committed episode; care buttons and callbacks share ContactCoordinator admission;
World routes object-busy clicks before ordinary contact. Optional contact speech
does not stop search. Required missing/find/identification and withholding cues
retain their receipts, priority and stale-receipt protection. SearchTask remains
active during candidate inspection. No new saved field, busy flag, phase, timer,
movement writer or parallel owner is needed.

Keep coverage of admission, actual custody, search continuity, singleton game
windows and playback cancellation. Change artificial scenarios and misleading
names, not the protection they intend to verify. Use isolated temporary saves;
do not access the normal save. Do not change dialogue or user-facing behavior.

## Stages

| Stage | Concrete change | Validation before commit |
| --- | --- | --- |
| 1: reachable feedback test | Replace the synthetic object_approach aside during notice in test_object_interaction.py. Produce a return-request aside through an actual observed take and user-held waiting state; prove receipt ordering and that stale aside receipts cannot acknowledge the returned-item phase. Keep required-aside blocking. | Object interaction, behavior, withholding and receipt tests. No production change. |
| 2: singleton game admission | Remove the obsolete existing-window focus branch from _open_game_now. Keep the singleton check at the public open_game entry using the existing game_open property; the private callback starts only an admitted new game. Confirm callers in code/tests/tools/docs before removal. | Native game-window tests verify disabled play, ignored repeat invocation, unchanged window and no focus/new-window side effects; care/persistent-window and real-timer hover/search regressions remain green. |
| 3: duplicate validation | Remove only the second identical button validation in ContactCoordinator.click. Retain its entry validation, story handling, foreground/playback guards and domain validation. | Existing contact, story, care and click-policy tests. No new implementation-mirroring test. |
| 4: accurate playback test name | Rename the emote test that calls _react directly so it describes sequence replacement rather than a physical click interrupting busy speech. Preserve its assertions and playback cancellation coverage. | Emote/reaction tests; then the complete suite, pinned static checks and documentation checks on the final export. |

Deliver each stage as a small English local commit and record its checks here.
Verify staged Git-index exports with Python 3.11.9 and Pillow 11.3.0; use Ruff
0.13.2, strict Mypy 1.18.2 and Pyright 1.1.414. Run Tk suites sequentially with
main-thread collection. Native widget/timer checks use controlled input and
isolated saves; they do not claim an exploratory human playtest.

## Progress

| Stage | Status | Evidence |
| --- | --- | --- |
| Plan | Complete | Clean baseline and reviewed owners/callers confirmed. |
| 1 | Complete | 85 object interaction/behavior/withholding/reaction tests pass in 0.129 seconds on the staged export; targeted Ruff passes. |
| 2 | Complete | 32 native game/care/persistent-window/hover/search tests pass in 32.651 seconds on the staged export; targeted Ruff passes. |
| 3 | Complete | 33 contact/story/care/click-policy/follow-up tests pass in 22.288 seconds on the staged export; targeted Ruff passes. |
| 4 | Complete | 28 targeted playback tests pass in 15.192 seconds; the final export passes all 1,149 tests in 344.913 seconds. Ruff, strict Mypy (187 sources), Pyright and documentation checks pass. |

### Stage 1 evidence

The replacement test performs a real World take before pickup attachment,
acknowledges the taken cue and advances the injected active-time clock to the
configured return-request interval. The coordinator produces object_request_return
from observed user-held custody. Cancelling the relocation physically returns
the portion to its original place; the required aside still blocks the returned
phase until its own receipt arrives. Both stale success and cancellation receipts
then fail to release the fresh object_returned phase. Actual arrival alone cannot
replace that phase's readable receipt. No production code changed.

### Stage 2 evidence

Code, tests, tools and documentation contain no other callers of the private
_open_game_now callback. The production deferral is World.interrupt after public
admission; repeat play is already disabled. open_game now checks its existing
game_open property at entry, preserving the UI-owned singleton invariant without
another state field. The private existing-window focus branch is removed.

The existing native game-window test now explicitly verifies disabled play,
repeat button invocation and direct public invocation, no extra window
construction or game focus call, and the same live window. Other game creation,
closing/reopening, care availability and real-timer object regressions remain.

### Stage 3 evidence

Only the repeated validation and its redundant comment were removed. The initial
ContactCoordinator validation still runs before story advancement or any contact
effects; the domain validates its own input as before. Sleeping/game/playback
guards, World admission, dialogue selection and relationship effects are unchanged.
Existing boundary and native tests verify behavior without a new mirrored test.

### Stage 4 evidence

Only the name changed to test_new_reaction_replaces_entire_older_sequence. The
actual emote/text assertions, timer checks and explicit replacement behavior are
unchanged. Actual direct-click continuity is still covered by its separate native
follow-up and search tests. The old name has no script/documentation consumers.

The complete four-stage source/test export passes Ruff 0.13.2, strict Mypy 1.18.2
(187 source files), Pyright 1.1.414 and 274 local documentation file targets plus
15 anchors in 37 root/docs Markdown files. The full-suite result is recorded below.

## Scoped completion and further audit

The Git-index export at cd0df28 passes all 1,149 tests in 344.913 seconds with
Python 3.11.9 and Pillow 11.3.0. There are no failures, errors or skips. Source/test
static checks passed before this unchanged export. UTF-8/no-BOM and Git whitespace
checks pass. Existing Tk ThemeChanged teardown diagnostics do not fail the suite.

Local commits: plan d6f2394; reachable feedback 5e8bde7; game entry 05a5c8c;
validation 762ee54; accurate name cd0df28. No push or merge performed.

This completes only the four review findings. It does not certify that all
redundant tests or physically impossible fixtures have been removed. During
validation the user reported apparent long-distance item-to-hand jumps and
requested a broader audit of unreachable fixtures and expensive UI scenarios.
That audit remains open. It must distinguish invalid physical setup from valid
accelerated animation/custody tests, identify the relevant test names and existing
headless protection, and retain the necessary native input/timer boundaries.
No additional test removal is authorized by this completion record.
