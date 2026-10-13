# Development workflow

This describes **how to contribute now** to [Aiko Desktop Pet](https://github.com/Lexoniarus/aiko-desktop-pet), not how its original sources were first uploaded.

The default branch is `main`. The first public feature baseline was v0.13; the completed object-oriented architecture refactor was merged via [PR #2](https://github.com/Lexoniarus/aiko-desktop-pet/pull/2) on October 13, 2026.

## Work on a branch

1. Fetch the latest `main` and inspect the current HEAD before making edits.
2. Create a focused branch such as `feature/…`, `fix/…` or `chore/…`.
3. Make a cohesive change with tests for altered behavior and use descriptive, English commit messages.
4. Run the relevant tests and type/lint checks (see [CONTRIBUTING.md](../CONTRIBUTING.md)).
5. Open a pull request targeting `main`, review its diff, and wait for green CI.
6. Run a real Windows smoke test for changes affecting transparent windows, focus, taskbar geometry, dragging, timers or GPU telemetry.
7. Merge only after review. Never force-push or replace the history of `main`.

The one-off upload helper used for initial publication is **not part of the maintained repository**. Development should use normal Git and pull requests, not a script that copies a local folder and pushes directly to `main`.

## Scope and security

Do not commit local `.env` settings, tokens, activity traces, save files, logs, private data, font binaries or built installers. `.gitignore` provides baseline exclusions but cannot replace review of the staged diff.

Only `AIKO_SAVE_PATH` is currently recognized by `.env.example`; no API credentials or cloud configuration are needed. The default local save file lives at `%LOCALAPPDATA%\AikoDesktopPet\state.json`.

Do not modify the user's existing save as part of a test or cleanup. Tests should use temporary paths. Maintain the current version-one JSON format unless a migration has been explicitly designed.

## Contracts

- Canonical code is organized under `pet/`, `personality/`, `application/`, `presentation/`, `ui/`, `desktop/` and `infrastructure/`.
- Preserve the documented public compatibility import paths while clients still depend on them.
- Application code must not manipulate Tk widgets or depend on concrete hardware providers.
- Hardware sampling and domain mutations have separate owners. Domain state changes must be testable without opening a desktop window.
- Keep authored German runtime/dialogue copy in German; technical docs, code identifiers and development messages are in English.

See [current architecture](ARCHITECTURE.md), [historical refactor audit](ARCHITECTURE_AUDIT_20261013.md), [asset licensing](../ASSETS.md) and [test status](https://github.com/Lexoniarus/aiko-desktop-pet/actions/workflows/tests.yml).
