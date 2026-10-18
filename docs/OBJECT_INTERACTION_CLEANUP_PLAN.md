# Interaction ownership review cleanup

Recorded: 18 October 2026. Baseline: `063837a`, `feature/world-foundation`.
Status: planned. All work stays local; no push or merge authorized.

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
| 1 | Pending | |
| 2 | Pending | |
| 3 | Pending | |
| 4 | Pending | |
