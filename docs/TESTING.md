# Test groups and ownership

The normal application suite is in `tests/`. Exporter/media checks and long
balance references have separate roots, so ordinary application runs do not
rebuild the character package or repeat long equilibrium simulations.

## Groups

| Group | Root | Purpose |
| --- | --- | --- |
| Application | `tests/` | Domain rules, application adapters, persistence and focused Tk integration |
| Asset tooling and media | `tests_tooling/` | Exporters, source preservation, package preparation and preview integrity |
| Long balance scenarios | `tests_balance/` | Long-term friendship references and the eight-hour care scenario |

Runtime asset loading and the generated normal-care scenario remain in the
application group. Moving exporter checks does not remove those contracts.

## Local execution

Only run checks when execution is authorized. The no-window entry point defaults
to the application group and blocks native Tk creation:

```powershell
python tools/local_test_suite.py
python tools/local_test_suite.py --group tooling
python tools/local_test_suite.py --group balance
python tools/local_test_suite.py --group all
```

`--report <path>` writes timings and the chosen group to an explicitly selected
file. Native-only cases are reported as skipped; a no-window result does not
prove native pointer delivery, focus, stacking or layout. The runner also sets
`AIKO_TEST_NO_NATIVE_TK=1` so Windows installer probes that create Tk in child
processes are skipped; blocking only the parent interpreter would not cover them.

A native run uses an explicitly chosen display in CI/Xvfb, or the designated
secondary monitor when native local execution is authorized:

```powershell
python -m unittest discover -s tests -q
python -m unittest discover -s tests_tooling -q
python -m unittest discover -s tests_balance -q
```

Use `xvfb-run -a` before a native command on Linux without a display. Do not run
GUI checks on the user's primary display. Do not start background test runs as
part of a source-only analysis or cleanup request.

## CI

[Application CI](../.github/workflows/tests.yml) keeps the Python-version matrix
and Windows integration selection. Ruff and Pyright include all three roots.
[Asset tooling](../.github/workflows/asset-tooling.yml) and
[balance scenarios](../.github/workflows/balance-scenarios.yml) run separately
when their listed source paths change, or through explicit workflow dispatch.
A skipped path-filtered workflow is not a successful execution of that group.

## Cleanup record: 2026-11-04

The cleanup removed obsolete refactor spelling/path checks, merged repeated
assertions into their behavior owners and reduced repeated desktop fixtures.
It did not add tests that assert test counts, file layout or the cleanup itself.
No application behavior was changed by the cleanup commits.

Static counts of test-method definitions in the local worktree:

| Scope | Before | After |
| --- | ---: | ---: |
| Application methods | 2,612 | 2,458 |
| Separate tooling/media methods | 0 | 71 |
| Separate long-balance methods | 0 | 2 |
| Total methods | 2,612 | 2,531 |

This is 81 fewer methods overall. The application root also excludes the
separate groups. Counts do not expand loops or describe runtime performance.
The existing uncommitted UI work was preserved separately from cleanup commits;
these worktree counts include its methods.

Important reductions include the 6,561-pair Mastermind evaluation sweep,
full GUI rounds previously played only to inspect the last board row, repeated
social-request phases and duplicate save/reopen and window-lifecycle scenarios.
Mastermind board geometry now uses a prepared rules state and a standalone
window. Finale effects use their presentation ports; canonical eating frames
remain covered by food-rendering checks.

### Current owners of retired collections

| Retired collection | Remaining responsibilities |
| --- | --- |
| `test_domain.py` | Care actions, need/mood progression, pet checkpoints and legacy decoding |
| `test_needs_and_bond.py` | Care actions, food activity, friendship policy/neglect, storage and social dialogue |
| `test_dialogue_modules.py` | Character-mind injection and dialogue catalogue/parser |
| `test_final_architecture_audit.py` | UI projection parity; literal source-shape checks retired |
| `test_canonical_owner_identity.py` and the retired gaze/emote boundary files | Behavioral owner tests and actual application assembly |
| `test_daily_need_schedules.py` | Historical numeric snapshots retired; generated real-care balance remains |

Some older plans and source inventories retain their original filenames and
line numbers as historical evidence. They are not current invocation lists.

### Retained boundaries

- Atomic saves, schema upgrades, backups, stale revisions and rollback.
- Actual completed interactions, exactly-once rewards and cancelled callbacks.
- Real elapsed time, clock rollback, standby and no replay on reopening.
- Separate World custody and subjective object memory.
- Native drag capture/release, physical reach and attachment at pickup.
- Different wish goal meanings and assignment at actual interaction start.
- Provider-specific decoding and strict resource validation.

The first cleanup was reviewed statically without running tests or discovery.
The follow-up below records the subsequently authorized final verification.

## Follow-up audit and cleanup: 2026-11-04

The second pass included the pending UI work and inspected all three test roots,
their helpers and workflow entry points. Test execution stayed disabled during
the main cleanup; findings from final verification received focused reruns.

| Scope in the combined local worktree | Before this pass | After this pass |
| --- | ---: | ---: |
| Application methods | 2,468 | 2,449 |
| Tooling/media methods | 71 | 76 |
| Long-balance methods | 2 | 2 |
| Total methods | 2,541 | 2,527 |

This is 14 fewer methods overall. Focused setup-failure and UI-command cases
replace mixed scenarios, so the main reduction is also inside methods:

- Explicit tactical boards replace the Tic-Tac-Toe traversal of over 8,000 boards
  and its partly self-referential comparisons.
- Hardware-observation wiring uses six samples per case instead of 3,601.
  Hourly consumption rates remain with their domain tests.
- Fractional-time evidence keeps its full in-memory matrix, with two SQLite
  save/restart cases instead of 32 repeated save/restart cycles.
- Sleep-recovery partition checks sample the actual qualification boundaries
  instead of performing 1,824 one-second advances.
- Cursor escalation remains with its coordinator; renderer integration checks
  real movement and alignment without repeating the full escalation/expiry run.
- Duplicate horoscope, save-path, settings-window and historical source-shape
  checks were removed.

`tests/support/` contains ordinary factories and owned fixtures. Application
tests no longer import other test modules or invoke `setUp()` manually.
Finite reaction playback uses the existing scheduler with a bounded drain.
No tests of the cleanup, test counts or test-helper implementations were added.

Source hashes and reproducible exports are in the tooling group. Runtime
loading, transparency, card/icon completeness and image-cache ownership remain
in the application group. Workflow filters include root asset sources and
balancing data; the manual Ruff audit includes all test roots.

UI-specific corrections cover deterministic popup positioning, actual movement
of Aiko's anchor, canvas clicks after scaling, preference validation and the
save callback. Assertions about a requested topmost command do not assume a
window manager acknowledges that flag under Xvfb.

The existing production UI work was preserved. Final verification exposed a
popup-positioning defect after live scaling: the pending selector now follows
Configure events from its anchor and unbinds that callback on close. Cleanup
commits contain the independent test changes; corrections that require the
pending UI APIs remain alongside that UI work. Final worktree results therefore
include the pending UI feature and do not establish standalone acceptance of
the committed branch or native Windows behavior.

### Final verification

The combined worktree, including the pending UI feature, was checked only after
the main cleanup. Native Tk ran under Xvfb at 3840x2160 in an isolated Linux
container with the exact runtime dependencies from `requirements.txt`. No tests
opened windows on the Windows host.

| Check | Result |
| --- | --- |
| Ruff, all application/test/tool roots | Passed |
| Strict Mypy, application/entrypoint/tools | Passed, 399 files |
| Repository Pyright | Passed, zero errors and warnings |
| Application suite, Python 3.11 / Xvfb | 2,449 tests, zero failures/errors, 17 platform skips |
| Tooling/media group | 76 tests passed |
| Long-balance group | 2 tests passed |

The 17 skips are 16 Windows installer cases and one Windows layered-window
hit-testing case. Native Windows acceptance and GitHub CI were not run by this
cleanup. The final application run produced no destroyed-interpreter Tk
background messages.

The safe Tk helpers drain pending idle work before destroying standalone test
roots. Repeated display probes use that cleanup too. No-window local execution
also excludes native installer child processes, whose Tk interpreters cannot
be blocked by patching only the parent.
