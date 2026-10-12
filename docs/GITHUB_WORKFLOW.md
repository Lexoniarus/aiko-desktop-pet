# GitHub development workflow

Repository: https://github.com/Lexoniarus/aiko-desktop-pet

Default branch: `main`. Initial published project baseline: **v0.13**.

## Initial publication

The initial release was imported with `Auf_GitHub_veroeffentlichen.bat`. Its PowerShell implementation clones the existing `main` branch into a temporary directory, stages the prepared project, checks the staged diff, and creates a normal commit. It does **not** rewrite history or use force-push.

The upload helper is retained only for historical reproducibility; normal future development should use a Git checkout and feature branches instead.

## Development guidelines

1. Confirm the current remote branch and commit before making changes.
2. Create a focused `feature/*` or `fix/*` branch.
3. Keep each change scoped, with tests for altered behavior.
4. Run `python -m unittest discover -s tests -q`; GUI tests need a display (for example Xvfb on Linux).
5. Open a pull request to `main` and review CI results and the diff.
6. Validate Windows-specific behavior manually before calling those cases verified.

Never commit local saves, private information, font binaries, system logs, authentication tokens, caches, or generated build output. The project's `.gitignore` excludes common local artifacts.

## Source and asset licenses

The project's code and creator-controlled rights in Aiko artwork are offered under [MIT](../LICENSE). Kenney graphics remain CC0, with voluntary creator credit. Fonts are not redistributed.

For details see [ASSETS.md](../ASSETS.md) and [LICENSES/KENNEY_CC0.md](../LICENSES/KENNEY_CC0.md).

## Language policy

All project documentation, including README, license explanations, development notes, and test reports, is written in **English**. Runtime UI text and Aiko's dialogue remain **German**.
