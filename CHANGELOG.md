# Project change history

This repository distributes source and a Windows setup script. The entries below
record source changes and verified milestones; they do not announce a packaged
Windows release. The current documentation starts at [docs/README.md](docs/README.md).

## Unreleased — World interaction, perception and ownership

### Added and changed

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
