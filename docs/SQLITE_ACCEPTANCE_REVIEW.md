# SQLite acceptance and OOP review

Local SQL-9 review on 2026-10-24, on `feature/social-optimization` after SQL-8.
This is storage acceptance under the requested no-window boundary, not native
visual/input acceptance or a merge approval.

## Verification and corrections

- Complete local suite: **1,844 reported tests in 95.936 seconds**, zero failures
  or errors, **112 explicitly recorded display-dependent skips**.
- Native Tk creation was blocked before discovery; the default save path pointed
  into a disposable temporary directory. The existing local runner recorded a
  duration for every reported case and wrote its JSON report outside Git.
- **No test exceeded ten seconds.** The slowest cases were isolated Windows setup
  integration at **8.657 s** and installer/repair/failure handling at **8.178 s**.
  Their subprocesses exercise PowerShell, temporary virtual environments and
  replaced launcher entrypoints; they do not run the real pet, install system
  Python, download runtime packages or wait for mouse/input. The integration
  cost verifies actual installer boundaries; no test split/mock substitution
  was needed to meet the agreed limit.
- The next slow cases were bounded fake-time scenarios: eight-/four-phase care
  schedules (**3.918 s**), a full-week lifecycle (**3.840 s**), unknown uptime
  (**3.227 s**) and generated wish/care balance (**3.217 s**). These use production
  policies and explicit timestamps, not real-time gameplay waits.
- Whole-repository Ruff and fresh strict Mypy passed (**343 application/tool
  source files** in this workspace). Complete Pyright initially found three
  stale horoscope test usages. They now return `StorageError` and obtain the
  public combined storage port instead of the private writer. Complete Pyright
  then passed with zero errors/warnings.
- Targeted tests after those fixture-only corrections: **16 in 0.006 s**, no
  failures/errors, plus one explicit native-only class skip. Scoped Ruff and
  Pyright passed too. Production logic did not change after the complete run;
  the full suite was not repeated merely for test annotations or documentation.

The complete run includes the current workspace's parallel character/export
files and their tests. Those pre-existing uncommitted changes were not included
in SQL-9 commits. The reported workspace count is not presented as an isolated
checkout of the pushed commit. Native case/class skip entries are unittest's
reported units, not a claim that every underlying widget method executed.
All 112 skip reasons were reviewed: each requires a native Tk/display surface;
none is a skipped SQLite, import, rollback or care-balance failure.

## Owner and dependency review

| Owner | Reviewed responsibility and outcome |
| --- | --- |
| `PetState` / immutable `PetValues` | Sole mutable pet aggregate; all 25 checkpoint fields are represented by existing owned mappings. No SQL rules or storage dependency enters the domain. |
| `PetSessionRestorer`, `ActiveSessionClock`, `SessionTimeProgression` | Existing closed/live time progression only. Snapshot reads, imports and writes do not consume time, create interactions or grant knowledge. |
| `WorldState` / subjective object memory | Physical stock and acquired knowledge remain separate. Safe ground recovery preserves identities/counters without turning saved World truth into observed identity or location. |
| `SavedPetReader`, `SavedPetWriter`, `SavedPetStore` | Application contracts carry complete owners and revision metadata. Backend errors are typed `StorageError`; no backend exception API leaks into care rules. |
| Configured `StateStore` | Resolves one source/destination pair, performs strict first import and inherits the single SQLite writer. No second revision cache, serializer or JSON writer. |
| `SqliteStateStore` / `session_rows` | One complete transaction, conditional expected-revision update, validation before commit and no-overwrite first publication. Mapper functions do not commit independently. |
| Schema/connection/backup/publication modules | Distinct infrastructure effects. Foreign keys, supported identity/version, schema consistency, rollback, schema-update backups and first-publication conflicts remain enforced. Initial schema stays version 1. |
| `DesktopPersistence` | Owns last successful revision/save time and independent attempt cadence. Failed or stale writes neither advance that checkpoint nor adopt another session's revision for a retry. |
| Desktop startup and existing save feedback | Loading fails before pet windows; failure is reported without a fresh replacement or alternate path. Autosave, immediate writes, social reservations and shutdown share the existing persistence owner. |
| Authored catalogs / UI read models | Catalog JSON remains canonical in Git. Wishes, Moodlet causes and domain facts are saved; labels, overall emotional projections and countdown views remain derived. |

`LoadedPetData` and immutable checkpoints are data transfers, not additional live
pet owners. Strict codecs reused inside SQLite are validation/translation, not
another repository. Bounded immutable handover/cause snapshots and list-valued
SQL cells are deliberate retained facts; they do not duplicate active mutable
wish tables or implement a second event archive.

## Preserved fields and feature evidence

Existing focused tests plus the full suite cover:

- Exact core/nutrition/sleep/time/settings values, optional legacy distinctions,
  full status precision and separate rolling relationship/exposure history.
- Frozen wish goals, exact/any/exclusion targets, progress, ordered round receipts,
  pins/rotation/expression anchors and food handovers surviving wish retirement.
- All active Moodlet fields, lower-stage budgets, relief usage, bounded actual
  causes and their wish/game/object/period/original-handover context.
- Interaction/poor-care processing, allocation counters, bounded encounters and
  evidence, all six longer-term cursors and retained period cause summaries.
- Anonymous adaptive profiles/quiet phases, source-aware last-ten social receipts,
  request caps/pauses and current-day horoscope sign/paragraph/participation.
- Full-owner round trips and rollback; coherent concurrent reads; stale, locked,
  unsupported/foreign/incomplete databases; competing first writes; preserved
  backups/source bytes; no fallback to stale JSON; exactly-once closed-time care.
- Generated ordinary/intensive care scenarios retain their distinct friendship
  outcomes without reintroducing retired instant wish bonuses or reward caps.

See `tests/test_sqlite*.py`, `tests/test_legacy_json_codec.py`,
`tests/test_desktop_persistence.py`, session/resource tests and
`tests/test_generated_care_balance.py` for the existing evidence. Mapper tests
check individual owner semantics; store/import tests check transaction and
migration boundaries. They serve different invariants. SQL-8 already consolidated
fourteen obsolete JSON-discard/replacement tests; no new redundant simulation
suite or compatibility repository was introduced for SQL-9.

## Outcome and limits

**SQL-1 through SQL-9 are delivered.** The review found no additional product
storage/domain correction necessary. SQL-9 fixes the three stale test usages
without widening production ports or weakening architecture checks.

No personal save was read, migrated or written. No native test/pet window,
mouse automation, live API probe or GitHub CI was used. Normal default-path
import happens only when the updated application is subsequently started.
The existing native visual/input acceptance and reported AppHang investigation
are separate; a no-window suite cannot certify them. No merge was performed.
