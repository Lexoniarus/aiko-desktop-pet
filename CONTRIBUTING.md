# Contributing to Aiko Desktop Pet

Thanks for helping improve Aiko. The aim is a reliable, **local-first** Windows desktop companion with expressive, authored German dialogue and no required cloud services.

## Before you begin

Read [README.md](README.md) for setup, [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for object ownership, and [docs/GITHUB_WORKFLOW.md](docs/GITHUB_WORKFLOW.md) for the branch/PR workflow.

The baseline is Python 3.11+ with standard-library Tkinter on Windows 10/11. Running Aiko requires **no third-party Python package**. Some CI quality tools are installed only for development and tests.

## Development workflow

1. Branch from current `main` using `feature/…`, `fix/…`, `docs/…` or `chore/…`.
2. Make focused changes with readable, descriptive English identifiers and commit messages. Prefer real object responsibilities over arbitrary line-count splits.
3. Add or update tests when behavior, persistence, UI timing or public imports change.
4. Run the complete test suite (GUI tests need a display):

   ```bash
   python -m unittest discover -s tests -q
   ```

   Under Linux with Xvfb: `xvfb-run -a python -m unittest discover -s tests -q`.

5. If the tools are installed, run:

   ```bash
   python -m ruff check aiko_pet tests main.py
   python -m ruff check --select E501 aiko_pet main.py tools
   python -m mypy --strict --no-incremental aiko_pet main.py tools
   python -m pyright --project pyrightconfig.json
   ```

6. Open a pull request to `main`. Describe changed behavior, tests and any Windows-specific manual checks. Do not merge with failing CI.

CI pins Ruff and Mypy and verifies source and tests with Pyright. Consult [the workflow](.github/workflows/tests.yml) for its exact versions and additional quality gates.

## Design constraints

- **One mutable pet aggregate:** `pet/state.py`. Pure domain policies calculate transitions; `PetState` applies them.
- **Typed application ports:** do not import or manipulate Tk from `application/` or put OS sensors in the pet domain.
- **UI ownership:** `AnimatedPet` handles character animation; `HoverUi` handles accessory windows. Coordinate through named callbacks.
- **Save compatibility:** preserve the version-one save schema and `AIKO_SAVE_PATH` behavior unless migration is explicitly designed.
- **Legacy public imports:** do not delete compatibility shims or rename public entrypoints without a migration and regression coverage.
- **Language:** technical docs and code identifiers in English; authored UI text and Aiko's dialogue remain in German.

A real Windows smoke test is required for window focus, transparency, taskbar placement, mouse handling, reaction timers or GPU sampling changes.

## Protect users and contributors

Never commit a personal `.env`, tokens, save files, raw activity logs, privately obtained assets, fonts or build artifacts. Check `git diff --cached` in addition to the exclusions in `.gitignore`. Tests must use isolated temporary save paths and must not overwrite `%LOCALAPPDATA%\AikoDesktopPet\state.json`.

Please avoid attaching unredacted system logs, window titles or personal file paths to public issues. For sensitive vulnerabilities, contact the maintainer privately through the available GitHub security/contact channels rather than posting exploit details publicly.

## Artwork and documentation

The 73 shipped Aiko frames and sourced Kenney graphics have distinct provenance/licensing conditions. See [ASSETS.md](ASSETS.md). Do not bundle separately installed font binaries. Avoid regenerating or replacing approved character art in ordinary code cleanups; document any intentional visual changes with before/after captures.

New documentation should link to [the current architecture](docs/ARCHITECTURE.md). Keep historical feature reports clearly identified as historical rather than silently rewriting their old numbers.
