# SQLite acceptance and OOP review

## Post-correction local acceptance (2026-10-25)

Reviewed `feature/social-optimization` at **`40cf4fe`**, including the fractional
time/save correction, wish-card rendering and subsequent game input/focus fixes.
The following acceptance covers the current workspace, including its **53
pre-existing modified/untracked character/export paths**. Those parallel paths
remain outside this delivery's commits. This is not a frozen clean-checkout run.

- Full local suite: **1,862 reported tests in 96.257 s**, zero failures/errors;
  **112 display-dependent skips**. Reviewed all recorded skip reasons: they
  require native Tk/display access, which was intentionally blocked before
  discovery. The report contains **1,862 individual timing records**.
- **No test over ten seconds.** Longest: isolated Windows install/repeat/launcher
  integration **8.847 s**; installer download/repair/failure-path fixture
  **7.724 s**; preserved broken-environment fixture **5.659 s**. These subprocess
  fixtures use temporary copies and substituted entrypoints/providers; they do
  not start the real pet or download/install system Python. Real venv/setup work
  verifies the installer boundary; no redundant simulation or delay was added.
- Next longest are existing explicit-time care schedules **3.983 s**, a full-week
  lifecycle **3.868 s**, and generated care/wish balance **3.242 s**. They advance
  supplied timestamps, not a real-time gameplay loop. No timing-based test
  rewrite or repeat run was justified.
- Local configured quality gates pass: `ruff check aiko_pet tests main.py tools`,
  fresh strict `mypy --no-incremental aiko_pet main.py tools` (**343 sources**),
  and complete repository Pyright (**zero errors/warnings**).
- An additional broader `ruff check .` found **191 existing style diagnostics**
  in `scripts/build_character_hd_2x.py` (last changed by `e6dd310`). That legacy
  exporter is outside the configured Ruff/Mypy source gate. It is unchanged here;
  this review does not claim every tracked auxiliary script is lint-clean.

The timing JSON remains outside Git at
`%TEMP%/aiko-final-local-20261025-4f2951d9-3860-44a7-8c77-766bee195d38.json`.
Default saves were redirected to a disposable directory before test discovery.
No personal save, native test/pet windows, mouse automation, HTTP probe, GitHub
CI or merge was used.

### Reviewed ownership and contracts

| Boundary | Source review and outcome |
| --- | --- |
| `TimePlan` / `SimulationStep` | Immutable interval definitions carry one elapsed axis and separate calendar anchors. Direct Pet progression and World coordination consume the same endpoints. `hours` is a rate conversion, not a second clock. |
| `PetState` / pure progression | One mutable aggregate commits immutable policy results. Relationship, Moodlet/poor-care/long-term cursors, sleep duration and wish expiry share the represented intervals. Step/final guards reject mismatches; no tolerance, lifetime overwrite or second progression owner was introduced. |
| Live clock / restorer / World coordination | The existing live clock consumes uptime once; the existing restorer reconstructs closed time once. The World coordinator handles finite resource effects and rollback with the existing aggregate, physical World and subjective memory owners. Storage does not simulate interactions or advance time. |
| Configured store / SQLite / desktop persistence | The configured store reuses one transactional writer. Mappers translate complete checkpoints without independent commits. Expected revisions remain transaction-checked; the desktop adopts the returned revision only after success. No fallback JSON writer, revision repair cache or automatic reset was added. |
| Wish projections / `WishPanel` | Authored target semantics and persisted identities remain domain-owned. UI uses the packaged icon catalog and only publishes a completed rendered identity set. Failed card construction can retry; UI does not invent or replace a wish. |
| Hover admission / game sequences / game rules | Existing menu/deferred-admission tokens prevent duplicate/stale starts. Sequences own readiness/timers; rule engines own boards and scores. Connect Four's nonblocking player-first welcome retains move/AI/result guards. No game score or rule state was moved into the toolbar. |
| `ScrollRegion` / Mastermind view / local drag | Pointer-focus suppression is local UI bookkeeping; keyboard reveal remains available. Selected color/draft are pending player input, not another completed-game state. The existing drag owner keeps a single gesture/preview and releases it before applying click/drop effects. The shared panel prepares its body before first mapping; no new polling/animation owner was added. |

The review included the twelve changed production files since `d03f104` and their
existing clock, restoration, storage, admission and rendering callers. Existing
dependency/architecture guards passed as part of the full suite. Tests cover
different boundaries: strict save/restart/time evidence, catalog-to-view assets,
view commands/focus tags and sequence/rule admission. The added widget doubles
do not recreate a gameplay simulation or establish native Windows input behavior.

**No further product refactor was justified in these reviewed boundaries.** This
is a bounded source/behavior review, not a guarantee about every possible runtime
scenario. Native Windows click delivery, preview visibility/layout, and the
previously reported AppHang remain practical acceptance items. The 112 display
skips must not be described as executed visual tests. No full-suite rerun is
needed for the documentation-only acceptance record below.

## Historical SQL-9 acceptance (2026-10-24)

> **Subsequent runtime finding, corrected 2026-10-24:** the original acceptance
> missed an inconsistent fractional time contract shared by Pet and World
> progression. Its statement that no product correction was needed was too broad.
> The [corrective delivery](CARE_TIME_IMPLEMENTATION_PLAN.md#time-contract-correction-after-sql-9-runtime-report)
> now records canonical elapsed endpoints, strict-save regression coverage and
> **226 passing targeted tests in 36.938 s**, no skips or tests over ten seconds.
> No new full-suite result is implied; the complete-run evidence below remains
> the historical SQL-9 workspace run.

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
