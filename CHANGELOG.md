# Project change history

Aiko Desktop Pet is maintained as a source repository. The dates below describe
verified GitHub milestones, **not** packaged Windows releases. There is currently
no separate downloadable installer or published GitHub Release.

## Unreleased — Aiko Anime assets and playback

- Restore calm 2.52-second ambient cycles and slower 1.413-second walking.
  Preserve all eight poses and source timings. Walk two to four cycles, then
  rest for 60–180 seconds; fractional motion no longer ends walks prematurely.
- Use one suspend-excluding session clock across ticks, care, settings and
  saving. Preserve save values on reopen without offline decay or recovery.
- Set waking hourly decay to 30 satiety, 4 mood, 6 energy, 8 social and 6
  affection points, with bounded measured-load additions. Retain sleep recovery,
  care effects and friendship limits. Add non-interrupting friendly care requests.
- Fix the Pillow 11.3 strict-type boundary and explicit Win32 scalar conversions.
  Make GUI mapping and repeated-local-hour test fixtures portable on Windows/DST.

- Track only the 134 original inputs needed to rebuild the selected character
  export, with SHA-256 inventory and separate restricted asset terms. Ignore
  the other 813 archive members. Preparation code remains MIT; Kenney stays CC0.
- Replace the previous 73 runtime sprites with 112 full-width 192 × 208 poses.
  Prepared Windows images preserve the source artwork and use binary alpha.
- Decode typed animation metadata, play authored frame timings independently
  of the desktop tick, show every pose under delayed callbacks, extend one-shot
  deadlines and cancel timers on shutdown. Walking positions update every
  33 ms independently of the unchanged 140 ms simulation tick.
- Bind feeding to eating, petting to its own action and sleep to the breathing
  loop; preserve dialogue, care rules and version-one saves.
- Retain attack artwork, hand layers and overlay anchors without an attack
  trigger or new game mechanic.

## Unreleased — Remove obsolete import and desktop adapters

- Review repository consumers and remove 25 flat-module forwarding files,
  five old application view modules, the legacy presentation adapter and
  the desktop compatibility facade (32 files in total).
- Migrate behavior tests to canonical packages and component owners; remove
  tests whose sole purpose was keeping old imports or attributes alive.
- Remove the `ComputerVoice` alias, the `DesktopPet.computer_voice` attribute
  and unused compatibility re-exports from the desktop bootstrap.
- Update CI import/type-check commands and enforce application boundaries
  without exceptions for the removed view modules.
- Document [import migration](docs/ARCHITECTURE.md#import-migration).
  Existing launchers, version-one saves, artwork and dialogue are preserved.
  External Python code using retired paths or desktop attributes must migrate.

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

For earlier v0.2–v0.13 design changes, see
[the historical feature timeline](docs/HISTORY_0_2_TO_0_13.md). The numeric
feature baseline is not a GitHub Release tag or a claim of an installer build.

## Compatibility approach

The current source uses canonical package imports. Retired module paths and
desktop forwarding attributes are documented in the import migration table.
Version-one save compatibility is retained; changes to callable interfaces or
the JSON schema require explicit migration instructions and regression tests.
