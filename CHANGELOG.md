# Project change history

Aiko Desktop Pet is maintained as a source repository. The dates below describe
verified GitHub milestones, **not** packaged Windows releases. There is currently
no separate downloadable installer or published GitHub Release.

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

Historical module paths and public methods are retained where consumers may
still use them. A future change that breaks these interfaces or the JSON save
schema needs explicit migration instructions and new regression tests.
