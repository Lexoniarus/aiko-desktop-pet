# Documentation

Use the maintained guides below for the current implementation. Completed plans
and earlier acceptance checklists are [history](history/README.md), not an active
backlog. There is no remaining implementation stage in the completed World/OOP
and test-cleanup plans.

## Maintained guides

| Topic | Document |
| --- | --- |
| Getting started, privacy and licensing | [Project README](../README.md) |
| Module owners, dependency rules and canonical imports | [Architecture](ARCHITECTURE.md) |
| Attention, identification, learned-place checks, search and custody | [World behavior](WORLD_OBJECT_CONTRACTS.md) |
| Desktop acceptance and repeatable isolated-save checks | [World smoke guide](WORLD_SMOKE_TEST.md) |
| Toolbar, action availability, details and native windows | [UI window contract](UI_WINDOW_CONTRACT.md) |
| Packaged JSON, save versions, recovery and time | [Data and saves](DATA_AND_SAVES.md) |
| Food, digestion, workload and item graphics | [Food system](FOOD_SYSTEM.md) |
| Need rewards and overall mood | [Fun and mood](FUN_MOOD_SYSTEM.md) |
| Animation profile and playback timing | [Animation timing](ANIMATION_TIMING_PROFILE.md) |
| Source installation on Windows | [Windows setup](WINDOWS_SETUP.md) |
| Branches, reviews and CI | [Development workflow](GITHUB_WORKFLOW.md) |
| Existing media and its capture limitations | [Media gallery](MEDIA_GALLERY.md) |

[Contributing](../CONTRIBUTING.md) gives local test and quality commands;
[CHANGELOG](../CHANGELOG.md) summarizes current unreleased changes and milestones.

## Validation and acceptance

- Maintainer-reported desktop acceptance for the current World interaction flow
  is **passed**, recorded 2026-10-18. This does not invent individual sign-offs for
  every old matrix cell. The latest work after that report changed tests/docs only.
- Local full verification at `5f1bdea`: **1,146 tests in 258.742 seconds**, no
  failures, errors or skips, using Python 3.11.9, Pillow 11.3.0 and native Tk.
  Ruff 0.13.2, strict Mypy 1.18.2 (188 source files) and Pyright 1.1.414 passed.
- The final scoped OOP review at `65175f2` reran **126 targeted tests**. Menu
  selection, actual custody-guard reachability and the separate feedback
  integration were verified; no new scoped findings remained.
- CI portability follow-up: all 48 WorldGui cases pass on both 1,024- and
  1,280-pixel simulated taskbars with a neutral pointer inside the simulated
  desktop (31.900 and 31.536 seconds). The eight affected cases also pass on
  the normal wider desktop (6.183 seconds). Only four scene-helper starting
  positions changed; test methods, assertions and production code are unchanged.
- Remote CI must pass for the newly pushed commit. The
  [Tests workflow](https://github.com/Lexoniarus/aiko-desktop-pet/actions/workflows/tests.yml)
  runs Linux Python 3.11/3.13 and Windows jobs. Prior run links and local test
  results are not a green status for a different SHA.
- The maintainer authorized merging
  [PR #10](https://github.com/Lexoniarus/aiko-desktop-pet/pull/10) on 2026-10-18,
  subject to final review and green checks for its current head. Verify the
  resulting `main` push workflow separately after merging.

Detailed commit-specific evidence is in the
[completed test ownership record](history/TEST_OWNERSHIP_FOLLOWUP_PLAN.md).

## Optional design references

[Integration boundaries](INTEGRATION_ARCHITECTURE.md) document the existing
application contracts and explicitly unimplemented external transports.
[Minigame candidates](MINIGAME_CANDIDATES.md) are exploratory research, not an
approved roadmap or a dependency list for the running application.

## Preserved product concepts

The following owner-supplied concepts were recorded on 2026-10-19. They preserve
future product direction, with explicit comparisons against main after PR #10.
They describe proposed extensions rather than currently implemented behavior;
recording them does not select the next feature or approve a delivery schedule.

| Concept | Scope |
| --- | --- |
| [Social and entertainment](SOCIAL_ENTERTAINMENT_CONCEPT.md) | German jokes/facts, content APIs, local EN-to-DE translation, cache, initiative/settings and shared quiz preparation |
| [Adaptive cursor perception and interaction](ADAPTIVE_CURSOR_CONCEPT.md) | State-sensitive startle/trust, flight, curious approach/touch and reliable direct interaction through existing owners |

The social concept connects the [minigame catalogue](MINIGAME_CANDIDATES.md)
to the proposed content/translation pipeline. Cursor behavior shares attention
and presentation owners but does not depend on online sources or translation.

## Dialogue editorial review

The [bubble dialogue review workbook](DIALOGUE_REVIEW.md) inventories every
complete catalogue sequence and additional non-catalogue speech, with current
event triggers, variant filters and ordered text/emote/pause beats. Each row
has one review-status field and an initially empty whole-sequence proposal.
It is an editorial snapshot for `feature/social-optimization`; the runtime
catalogues remain the source of shipped wording. All entries start unreviewed.

## Keeping documentation current

Maintain behavior in the World contract, ownership in the architecture guide and
practical instructions in the smoke guide. Add concise changes to the single
Unreleased changelog section. Archive completed delivery ledgers with their
original counts, proposals and baseline dates; do not promote their superseded
rules or pending wording back into current guidance.
