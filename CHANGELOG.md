# Project change history

This repository distributes source and a Windows setup script. The entries below
record source changes and verified milestones; they do not announce a packaged
Windows release. The current documentation starts at [docs/README.md](docs/README.md).

## Unreleased — World interaction, perception and ownership

### Added and changed

- Add typed, immutable definitions and validated JSON catalogues for the 18
  planned Moodlet families and 11 wish forms, shared balance parameters and
  German descriptions. Validate activity and positive fulfillment references.
  This supplies definitions only; no active Moodlets/wishes or gameplay/save
  changes.

- Separate the five care needs from numeric mood and friendship. Give the
  existing pet progression and status-advice contracts explicit names while
  preserving balance, save fields, German wording and the seven status readouts.

- Preserve a newly noticed unknown item's investigation through both orientation
  looks. Look back and require fresh perception before approach on either side;
  keep new-item curiosity separate from missing-stock searches.

- Add Unterhalten with existing Plaudern and separate API-only Single, Two Parts
  and fact choices. Prepare two items per category through individual background
  fetches after saved opt-in; preserve sources, introductions, punchline pauses
  and shared talk care/friendship rules. Cancel stale waiting selections and
  report failures without substitute content. Provider payloads remain in memory;
  [social content](docs/SOCIAL_CONTENT.md) records behavior and owners.

- Add the Spielen submenu with Rock–Paper–Scissors, Blackjack and Tic-Tac-Toe.
  Keep RPS's round flow; add local rules and
  outcome-neutral need profiles for the two new games. All session scores and
  game state remain transient, with one completion summary through the existing
  care coordinator. No runtime dependency or save migration is added.
- Import 52 Kenney Playing Cards Pack faces and one back under CC0, with license
  and source hashes. Keep player Blackjack cards/controls in the window and
  Aiko's masked/revealed hand in a separate desktop presenter with hover, flip
  and cancellation. Add targeted rule/UI/lifecycle and ownership coverage; the
  [delivery plan](docs/MINIGAME_IMPLEMENTATION_PLAN.md) records actual checks.
- Enlarge Blackjack player cards with 2x integer scaling and use a clickable
  pile of the existing card backs for drawing. Start the next hand automatically
  after a 2.8-second result pause, preserving the session score and cancelling
  the pending restart on close. Aiko's desktop cards retain their own scale;
  Tic-Tac-Toe keeps its explicit next-round control.

- Correct stage-4 time ownership: keep the clock responsible for elapsed time,
  inject one session progression through application ports and apply each
  planned step once. Preserve neutral legacy migration and live World care.
- Share sleep-care completion and existing intake decisions; eligible known
  drinks are no longer blocked by hunger with no available food. Clarify sleep
  policy names and add the early-wake energy boundary regression.
- Consolidate resource equivalence cases, separate monthly planner coverage
  from shorter multi-day state coverage, and review all tests over ten seconds.
  Verify 1,273 local virtual-display cases (eight Windows-only skips), 130
  headless Windows cases and pinned static checks. Remove the temporary manual
  full-CI extension; physical Windows acceptance remains separate.

- Implement adaptive sleep with one aggregate-owned episode and the existing
  chronological need integrator: 23:00–07:00 tentative expectation, simple
  three/seven-phase quiet learning, bounded daily adjustment, manual protection,
  exhaustion recovery and actual sleeping-time/early-return gates. Remove the
  former hardware-dependent sleep policy and its unused coefficients.
- Restore World and acquired knowledge before closed-time resource use. Consume
  only finite identified/appraised stock at its remembered accessible place,
  through the shared atomic consumption owner; unknown food stays unknown.
  Sleep food breaks reuse normal native search/pickup/intake and safe put-down.
- Persist optional sleep episodes and quiet windows inside outer save v1,
  including search failure, actual sleeping duration and real-time deadlines.
  Preserve old progress and original-byte backups for malformed/future records;
  keep relationship migration neutral across split resource reconstruction.
- Pass 91 final focused tests and pinned static checks. Record isolated native
  stock/save/command and Tk food/search/put-down evidence separately from the
  incomplete final full-suite rerun. The input probe's frozen idle sprite was
  an invalid visual sleep fixture; further visible/input-injecting probes stopped
  after owner feedback. Maintain rules in `docs/SLEEP_SYSTEM.md`; visual sleep,
  physical standby and later expression/context acceptance remain separate.

- Implement progressive friendship on the existing elapsed axis: shared rolling
  +0.75/two-hour and +5/24-hour credit, qualified personal contact independent
  of reward exhaustion, same-type timing and high-need reductions. Replace
  calendar eligibility and the variety bonus; personally used drinks now count.
- Integrate piecewise absence and bounded rolling per-need neglect alongside
  existing numeric need steps, choosing the strongest passive rate per interval
  and continuously scaling by the relationship curve. Restorative sleep exempts
  recovering energy; contact/refills do not erase neglect history.
- Apply bounded click losses only after an existing boundary warning and
  claimed-object withholding losses through the existing coordinators. Persist
  shared negative budgets across episodes/restarts, without rewarding return.
- Add optional version-one relationship history inside unchanged outer save v1,
  strict decoding/backups and checkpoint coverage. Legacy progress is preserved
  without inventing historical care or charging unrecorded past neglect.
- Verify 1,226 Windows tests, pinned static checks and an isolated native
  eight-hour return, injected clicks, visible labels and care/save/reopen.
  Record current behavior in `docs/FRIENDSHIP_SYSTEM.md`; later sleep and
  expression stages remain pending.

- Review all 138 object sequences and improve 90 with complete German noun
  phrases and pronouns. Keep names hidden before identification, distinguish
  new-portion speech from subjective reunion, and share article/case formatting
  with food fallbacks. Add strictly validated grammatical metadata without
  renaming menus or changing saves. Preserve saved-for-later intent through
  found-item placement. Verify 1,203 native Windows unit/Tk tests and static
  checks; record full replacement sequences in the dialogue review workbook.

- Reunite a missing subjective object with one newly identified same-kind
  portion during search, preserving actual World facts and transferring
  remembered assessment and saved-for-later intent. Retire the old missing
  record, exclude known stock and unseen findings, and keep ordinary stock
  recognition strict. Verify existing save compatibility and 1,194 tests.

- Restore rapid direct sprite clicks during an existing click reply, so the
  original teasing counter and irritation escalation remain reachable. Keep
  care/game/object actions exclusive and story-reading clicks exempt. The
  existing reaction player owns the active semantic event; add no click store.
- Verify stage-2 needs/mood with 1,177 Windows unit/Tk tests, pinned Ruff/Mypy/
  Pyright checks and two isolated native care/save/reopen launches. Physical
  standby/resume and later interaction fixes remain pending.
- Apply the agreed real-time awake/sleep need rates and bounded CPU/GPU/input
  consumption surcharges. Retain food nutrition, reduce digestion protection
  to 25% and remove fasting acceleration and activity-based reserve speedup.
- Derive mood only from needs, interpolated deficit deductions and the strictest
  target limit; decline at 1–10 points/minute by shortage and recover at two.
  Remove instant food/care/game mood bonuses and workload/friendship additions.
  Give all completed RPS outcomes the same base six fun per round.
- Consolidate numeric progression in the existing pure need policy, returning
  immutable `NeedProgress` to the sole mutable `PetState`. Keep coefficients
  in validated JSON and outer saves v1; add production-policy daily scenarios.
- Record separate fixes for blocked idle repeated clicks and subjective
  same-kind object reunion with natural German noun phrases. B1 is implemented;
  B2 subjective reunion and German phrases are implemented and verified,
  including 21 actual visible text bubbles with real timers in an isolated
  native Onigiri flow. Archive the completed B2 delivery record.

- Advance full real elapsed time across closed sessions and live standby;
  remove the eight-hour cap and stream long routine timelines. Keep active
  World observation/physics time separate, bound recent telemetry to its
  observed tail and restore pet/clock checkpoints together on failed progress.
- Add optional `pet.time` v1 with aggregate-owned elapsed seconds, preserving
  outer save v1, legacy progress and atomic paired saves. Back up malformed or
  future time records before replacement. Remove catalogue-generated offline
  meals; actual finite-stock closed-time care remains a later stage.
- Align the required placeholders for the existing meal fallback with its
  already-authored text, fixing startup catalogue validation without changing
  German wording. Friendship loss and learned sleep remain later stages.
- Add individual food/drink portions with cursor carrying, relocation, falling,
  damped rebounds, safe reachable placement, handover and autonomous pickup.
- Keep learned identity, current desire, visible tracking and missing-subject
  search distinct. Unknown items identify only in hand or through deliberate
  face presentation; continuously witnessed relocation preserves acquired knowledge.
- Focus every committed interaction on its own subject/activity. After focus
  releases, check learned places left and right across the taskbar before ordinary
  new-item investigation. Unknown replacements cannot hide a learned loss.
- Give each missing known portion its own readable bubble. One SearchTask retains
  its route while candidates are approached, inspected and put down; verified
  findings resolve their own missing subjects without restarting the whole pass.
- Keep passive hover available during search and inspection. Disable competing
  care/game/feed actions at buttons and callbacks; contextual busy replies allow
  the committed action to continue while required feedback keeps its receipts.
- Add desktop/known/assigned/missing object counts to expandable toolbar details.
  Show overall mood above the individual need bars, including a separate fun bar.
- Persist acquired object knowledge separately from World truth in optional memory
  v3 with v1/v2 readers. Commit consumption and custody through their explicit
  owners, preserving atomic outer save v1 and exactly-once nutrition/social effects.
- Preserve authored contextual dialogue, full consumption animations, ordinary
  reach at attachment, safe interruption and same-save recovery.

### Tests and documentation

- Add real-time regression coverage for suspend-inclusive clocks, source
  fallback/recovery, shared rollback, full long-gap advancement, initialization
  time, legacy/new time records and backup/replay safety. Include the new
  elapsed-time and persistence suites in Windows CI. Refresh obsolete copy
  expectations for the branch's existing authored text without rewriting it.
  Local full verification: 1,166 tests, Ruff, strict Mypy and Pyright passed;
  isolated native restart checks passed. Physical Windows resume is pending.
- Add the active care/time implementation plan for the latest discussed needs,
  mood, progressive friendship and simple adaptive sleep baseline. Record code
  ownership, staged delivery, save/time migration, finite closed-time resource
  use, remaining details and production/Windows acceptance criteria. Preserve
  the accepted combined four-phase care example supporting levels 7–8.
  Planning documentation only; no runtime, balance JSON or save changes.
- Record the combined proposed example day across needs, digestion/input
  modifiers, target/actual mood, normal sleep and individually credited
  friendship. Preserve assumptions, repeated-day values and numerical sensitivity;
  distinguish this arithmetic consistency check from implementation or playtests.
- Preserve proposed consumption modifiers: independent base hunger, bounded
  hardware/input surcharges, at most 25% digestion protection and a smaller
  energy surcharge. Record omitted fasting/reserve accelerators, closed-time
  behavior and food-only repeated-day examples; link the mood/sleep boundaries.
  No runtime, balance JSON or save changes.
- Record the latest proposed friendship curve and daily comparisons: shared
  rolling +0.75/two-hour and +5/24-hour reward ceilings, gentler lower upkeep,
  factor 2 from 90 points and a maintainable smaller morning/evening relationship.
  Update cross-references and overnight examples; distinguish isolated arithmetic
  from integrated need/neglect balance. No runtime, balance JSON or save changes.
- Simplify the proposed habit learner to actual repeated input, 15-minute
  inactivity and known off/standby state. Retain three/seven quiet-phase
  milestones and gradual adjustment; exclude weighted scoring and extra signals
  from app timestamps, manual controls or workload. Runtime learning is unchanged.
- Record proposed food breaks during sleep: satiety at most 20 triggers known-food
  use toward at least 40, zero satiety permits a bounded five-minute search, and
  failed searches do not loop within one main sleep phase. Preserve manual-sleep
  protection, actual sleep-time accounting and identified-stock limits while
  closed. No application, balance or save changes.
- Extend the adaptive sleep proposal with conflict priority, 30-minute protection
  for manual Sleep/Wake, exhaustion recovery, sleep-type endpoint conditions and
  worked conflict examples. Record resolved design candidates without changing
  application behavior or saves.
- Preserve the unimplemented adaptive sleep proposal: habit-learning milestones,
  sleep-onset and wake timings, naps/recovery, manual controls and chronological
  continuation while closed or suspended. Separate expected rhythm from observed
  activity and retain unresolved transition details as design questions.
- Preserve the unimplemented need/care balance and repeated-day example with
  eight hours of sleep. Extend the friendship proposal with progressive upkeep,
  rolling neglect thresholds and non-additive overlap with absence. Label
  superseded suggestions and original unscaled arithmetic explicitly.
- Record the unimplemented mood balance proposal: equal need contributions,
  critical-deficit deductions and target limits, real-time decline rates,
  slower recovery and worked examples. Keep current runtime guidance separate.
- Record the unapproved friendship balance proposal, including personal-care
  gains, progressive real-time absence losses, negative interaction values,
  level/progression examples and open decisions. Runtime balance is unchanged.
- Add a complete bubble-dialogue review workbook with ordered sequences,
  event/context conditions, an unreviewed status per sequence and empty text
  proposal fields. Include fixed speech fallbacks and the RPS countdown without
  changing the runtime catalogues or selection/playback behavior.
- Preserve the owner-supplied social/entertainment and adaptive cursor concepts,
  including content APIs, local translation and contextual mouse interaction.
  Link them from the documentation index and minigame catalogue, and distinguish
  older assumptions from the current main implementation. No runtime behavior,
  dependencies, settings or save formats change.
- Replace redundant long UI replays with focused native boundaries and headless
  feedback integration. Standalone rendering fixtures retain anchors, layering,
  scaling and image checks without constructing a full game instance.
- Merge the obsolete full-energy menu-refusal test into actual cursor-selection
  coverage, correct the pickup custody-guard fixture and inject feedback ports
  through a dedicated integration fixture.
- Anchor four native scene fixtures at the available taskbar edge so 2x layouts
  fit smaller CI desktops and unseen-relocation cases actually leave the old
  place. Preserve all existing behavioral assertions and production geometry.
- Record 1,146 passing native Windows/Python 3.11.9 tests at `5f1bdea`, with Ruff,
  strict Mypy and Pyright passing. The final scoped review at `65175f2` reran 126
  targeted tests. These local results do not predeclare new-commit CI success.
- Record maintainer-reported desktop acceptance and explicit authorization on
  2026-10-18 to merge PR #10 after final review and green current-head CI, then
  verify the resulting `main` workflow.
- Consolidate maintained World rules and smoke guidance; archive completed plans,
  superseded checklists and the prior patchwork changelog as explicitly historical
  [delivery records](docs/history/README.md).

## 2026-10-15 — Pet domain/UI consolidation merged (PR #9)

[PR #9](https://github.com/Lexoniarus/aiko-desktop-pet/pull/9) merged as
[`1753266`](https://github.com/Lexoniarus/aiko-desktop-pet/commit/1753266db0dafc94024913cb281b80e7abe289a0).
It established canonical package owners, typed desktop assemblies, immutable read
contracts and PetState transitions; retained authored assets/dialogue; consolidated
JSON resource ownership, food/workload rules, bounded closed-time restoration,
Windows setup and the pinnable care/settings UI. Earlier incremental entries and
commit-specific validation remain in the
[pre-consolidation history](docs/history/CHANGELOG_PRE_CONSOLIDATION.md).

## 2026-10-13 — Public repository polish (PR #3)

[PR #3](https://github.com/Lexoniarus/aiko-desktop-pet/pull/3)
updates public documentation and repository hygiene without changing Aiko's
runtime behavior, sprite assets, or save format.

- Reorganize the README around the running application, getting started,
  privacy, contribution and asset attribution.
- Curate the existing real screenshots, animation GIFs and historical UI
  references without regenerating or relicensing the underlying art.
- Explain the optional `.env.example` and expand ignored local test, editor
  and diagnostic artifacts.
- Remove the obsolete script that copied local files and pushed directly to
  `main`; use focused branches and pull requests instead.
- Add the maintained architecture guide, contribution guidance and GitHub
  issue/PR templates.
- Clarify historical documents and pin developer-only static analysis tooling.
- Document security disclosure and validate the public repository with tests.

## 2026-10-13 — Modular OOP architecture merged (PR #2)

[PR #2](https://github.com/Lexoniarus/aiko-desktop-pet/pull/2) was merged
into `main` as
[`073e7a4`](https://github.com/Lexoniarus/aiko-desktop-pet/commit/073e7a43551f0b29abe5d04b760c6324230e4be8).

- Canonical `pet/`, `personality/`, `application/`, `presentation/`,
  `ui/`, `desktop/` and `infrastructure/` responsibilities.
- Pure pet transitions and an application-owned valid-save catch-up policy.
- Immutable semantic read snapshots and separate German display projections.
- Typed desktop tick ports, lifecycle, preferences and provider contracts.
- Preservation of version-one local save data, historical public imports,
  approved character sprites and authored German dialogue.
- Maintainer-reported native Windows acceptance.

Post-merge GitHub Actions
[38382796398](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/38382796398)
passed 486 tests each under Linux Python 3.11/3.13 and 257 Windows-headless
tests, with successful Ruff/Mypy/Pyright checks.

## v0.13 — Original public feature baseline

The historical **v0.13** project included a Kenney sci-fi hover interface,
15 pixel emotes, 73 Aiko character animation frames, six displayed gauges
(five care needs plus friendship) and sequenced German character reactions.

Earlier milestones introduced desktop placement and gaze (v0.2–v0.8),
adaptive local rhythm learning (v0.9), context-sensitive reactions (v0.10),
care/friendship (v0.11) and differentiated affection (v0.12). The numeric
feature baseline is not a GitHub Release tag or a claim of an installer build.
Detailed historical records are available at the fixed
[pre-cleanup documentation snapshot](https://github.com/Lexoniarus/aiko-desktop-pet/tree/502c95d88062481d457b4901d1cc797bff8756e2/docs),
including the [original feature timeline](https://github.com/Lexoniarus/aiko-desktop-pet/blob/502c95d88062481d457b4901d1cc797bff8756e2/docs/HISTORY_0_2_TO_0_13.md)
and [completed OOP refactor record](https://github.com/Lexoniarus/aiko-desktop-pet/blob/502c95d88062481d457b4901d1cc797bff8756e2/docs/REFACTOR_ARCHITECTURE.md).
Historical test totals and balancing figures describe their own revisions,
not the current implementation or latest CI status.

## Compatibility approach

The current source uses canonical package imports. Retired module paths and
desktop forwarding attributes are documented in the import migration table.
Version-one save compatibility is retained; changes to callable interfaces or
the JSON schema require explicit migration instructions and regression tests.
