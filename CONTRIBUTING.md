# Contributing to Aiko Desktop Pet

Thanks for helping improve Aiko. The aim is a reliable, **local-first** Windows desktop companion with expressive, authored German dialogue and no required cloud services.

## Before you begin

Read [README.md](README.md) for setup, [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for object ownership, and [docs/GITHUB_WORKFLOW.md](docs/GITHUB_WORKFLOW.md) for the branch/PR workflow.

The baseline is Python 3.11+ with standard-library Tkinter on Windows 10/11. Running Aiko requires **no third-party Python package**. Some CI quality tools are installed only for development and tests.

## Development workflow

1. Branch from current `main` using `feature/…`, `fix/…`, `docs/…` or `chore/…`.
2. Make focused changes with readable, descriptive English identifiers and commit messages. Prefer real object responsibilities over arbitrary line-count splits.
3. Add or update tests when behavior, persistence, UI timing or public imports change.
   Name test modules, classes and cases by their feature or behavior, rather than
   the release that introduced them. Keep necessary legacy-format context in fixtures.
4. Run the complete test suite (GUI tests need a display):

   ```bash
   python -m unittest discover -s tests -q
   ```

   Under Linux with Xvfb: `xvfb-run -a python -m unittest discover -s tests -q`.

5. Run the pinned quality checks used by CI:

   ```bash
   python -m ruff check aiko_pet tests main.py tools
   python -m mypy --strict --no-incremental aiko_pet main.py tools
   python -m pyright --project pyrightconfig.json
   ```

6. Open a pull request to `main`. Describe changed behavior, tests and any Windows-specific manual checks. Do not merge with failing CI.

CI enforces PEP 8 whitespace, blank lines and 88-character lines, unused imports,
import ordering and Python identifier conventions across application code,
tests and tools. Ruff preview rules are enabled with its pinned version; only
the exact foreign Win32 function names listed in `pyproject.toml` are exempt
from lowercase function naming. Consult [the workflow](.github/workflows/tests.yml)
for tool versions and additional quality gates.

For maintained guides, reported desktop acceptance and completed delivery history,
start at the [documentation index](docs/README.md). Keep one current Unreleased
changelog section and archive completed plans rather than extending the active
documentation with superseded task checklists.

## Design constraints

- **One mutable pet aggregate:** `pet/state.py`. Pure domain policies calculate transitions; `PetState` applies them.
- **Typed application ports:** do not import or manipulate Tk from `application/` or put OS sensors in the pet domain.
- **UI ownership:** `AnimatedPet` handles character animation; `HoverUi` handles accessory windows. Coordinate through named callbacks.
- **Save compatibility:** preserve the version-one save schema and `AIKO_SAVE_PATH` behavior unless migration is explicitly designed.
- **Canonical imports:** import classes and functions from their owning packages. Removed flat-module paths and desktop forwarding attributes are listed in [the migration guide](docs/ARCHITECTURE.md#import-migration). Keep regression coverage and document changes to callable interfaces.
- **Language:** technical docs and code identifiers in English; authored UI text and Aiko's dialogue remain in German.

A real Windows smoke test is required for window focus, transparency, taskbar placement, mouse handling, reaction timers or GPU sampling changes.

## Protect users and contributors

Never commit a personal `.env`, tokens, save files, raw activity logs, privately obtained assets, fonts or build artifacts. Check `git diff --cached` in addition to the exclusions in `.gitignore`. Tests must use isolated temporary save paths and must not overwrite `%LOCALAPPDATA%\AikoDesktopPet\state.json`.

Please avoid attaching unredacted system logs, window titles or personal file paths to public issues. For sensitive vulnerabilities, follow the
[security reporting policy](SECURITY.md) rather than posting exploit
details publicly.

## Artwork and documentation

The current 120-pose Aiko Anime set has restricted asset terms; project code remains MIT and Kenney graphics remain CC0. Distributed forks must obtain permission for the new character assets or replace them with appropriately licensed artwork. The older 73-frame MIT release is documented separately. See [ASSETS.md](ASSETS.md). Do not bundle separately installed font binaries. Avoid regenerating or replacing approved character art in ordinary code cleanups; document any intentional visual changes with before/after captures.

New documentation should link to [the current architecture](docs/ARCHITECTURE.md). Keep historical feature reports clearly identified as historical rather than silently rewriting their old numbers.
