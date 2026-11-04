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
prove native pointer delivery, focus, stacking or layout.

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

The cleanup was reviewed statically. No tests or test discovery were executed
for this cleanup. Runtime acceptance and a green CI run remain outstanding.
