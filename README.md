# Aiko Desktop Pet

**A small, expressive desktop companion that lives by your Windows taskbar.** Aiko is a chibi personification of your computer: she walks, notices your attention, reacts to measured work, and gradually develops a familiar routine and friendship with you.

[![Tests](https://github.com/Lexoniarus/aiko-desktop-pet/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/Lexoniarus/aiko-desktop-pet/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-3873b3.svg)](#getting-started)

**Windows 10/11 · Python 3.11+ · local-first · no cloud account or AI API.**

![The current Aiko Anime character and the current Kenney sci-fi hover panel](vorschau/Aiko_Current_Hover.png)

*Actual Tk application capture on Linux/Xvfb (not a native Windows desktop
screenshot). The current 112-pose Anime character, Kenney panel, and German
dialogue are shown together. Documentation is in English.*

## Play with Aiko (Rock–Paper–Scissors)

Aiko's character bubble shows **only her own choice** and her reactions.
The independent, always-open Kenney-styled player panel shows **your selected
hand**, the round counter, your wins, Aiko's wins and draws. The counters belong
only to the currently opened minigame window and are never saved.

Other games, libraries and external data sources have been discussed only as
**unapproved possibilities**, with **no selected next game or implementation
order**. See the [minigame candidate catalogue and integration research](docs/MINIGAME_CANDIDATES.md).

![Rock–Paper–Scissors with the separate player panel and Aiko's actual speech bubble](vorschau/Aiko_RPS_Aufgedeckt.png)

![Captured minigame countdown, separate hand reveal, animated reaction and local score](vorschau/Aiko_RPS_Spielablauf.gif)

*These are captures of the actual Tk application on Linux/Xvfb;
they are not native Windows screenshots.*

## See Aiko in action

![The current Anime character reacting with question emote, two dialogue lines and heart emote](vorschau/Aiko_Current_Reaction_Sequence.gif)

This reaction sequence uses the **current character sprites, speech presenter and
Kenney emotes**. The latest sprite animation preview includes all 112 runtime
poses: [Watch Aiko's current animations](vorschau/Aiko_Current_Animations.gif).

[Browse the refreshed current screenshots, UI states and GIFs →](docs/MEDIA_GALLERY.md)

Historical v0.7–v0.13 artwork remains in Git history, not in the current
preview gallery.

## What she does

- **Lives on your desktop.** Short, slower taskbar walks with 1–3 minute pauses, calm blinking, jumping, waving, resting and 16-direction cursor gaze.
- **Needs a little care.** Feed, play Rock–Paper–Scissors, talk, pet, sleep/wake or offer an energy drink. From full satiety, about an hour awake brings her to 67–70%, making a snack useful. Other needs develop more slowly across the day, with occasional friendly requests.
- **Has her own voice.** Handwritten German reactions vary with mood, time, repeated clicks, interruptions and recent interactions. Emotes, text and optional follow-ups play in sequence.
- **Notices actual workload.** Local CPU/GPU and memory observations inform her working/resting behavior, without inventing the application or task you are using. Missing sensors remain unknown.
- **Learns a gentle rhythm.** Locally aggregated activity evidence helps her adapt to regular working and resting periods.
- **Stays out of the way.** A draggable sci-fi hover toolbar, independent status/settings windows and a separate speech bubble.

This source builds on the **v0.13 feature baseline and modular OOP refactor**, with a new 112-pose Aiko Anime character set, per-frame timing, and dedicated eating, petting and sleeping animations. Attack artwork is stored for later use. It is a source project; there is currently no separate packaged Windows installer or published GitHub Release.

## Getting started

1. Install **Python 3.11 or newer** on Windows 10 or 11, including Tkinter (normally part of the standard Windows Python installer).
2. [Download the current `main` source ZIP](https://github.com/Lexoniarus/aiko-desktop-pet/archive/refs/heads/main.zip) and extract the folder. Rock–Paper–Scissors is already included in `main`.
3. Double-click `Aiko_starten.bat`, or open a terminal in that folder and run:

   ```powershell
   py -m aiko_pet
   ```

4. Hover over Aiko to open the care panel. If the window fails to start, use `Aiko_starten_debug.bat` to keep the error output visible.

You can also run `python main.py` or `python -m aiko_pet`. **No `pip install` is required for normal use.** If the optional Kenney Mini font is already installed, Aiko can use it; otherwise she falls back to Segoe UI. Font files are not redistributed.

### Saves and optional configuration

By default, Aiko stores progress outside the repository at:

```text
%LOCALAPPDATA%\AikoDesktopPet\state.json
```

**No `.env` file is needed.** The only optional setting is `AIKO_SAVE_PATH`, which changes the save *file* location. To use it, copy [.env.example](.env.example) to a local `.env` and edit the value. An existing OS environment variable takes precedence. The template contains no secrets and should remain unmodified when no override is wanted.

## Privacy and local data

Aiko runs locally. The current application does **not** send telemetry to a server, start an HTTP service, require a subscription or call an external AI inference API.

Her workload observations are drawn from local CPU/GPU utilization, memory pressure, uptime and user-idle timing. They do not inspect files, process/application names, browser content, typed text or microphone input. Optional NVIDIA sampling uses local OS tooling. Learned rhythm summaries and pet progress are stored locally in the save file.

Needs use time within the running session. Closing Aiko or suspending the PC
freezes needs and recovery; reopening does not catch up the missing interval.
Sleep inside a running session retains gentle need decay and energy recovery.
The real clock still determines meals and daily routine. Friendship remains a
separate, slowly earned bond with the existing daily limits.

Disable **Observe computer** or **Learn rhythm** individually from the settings panel if you do not want those behaviors. See [adaptive behavior notes](docs/ADAPTIVER_RHYTHMUS.md) for details and historical design context.

## For developers

The source is organized by responsibility rather than by window or feature version:

| Package | Owns |
| --- | --- |
| `aiko_pet/pet/` | The PetState aggregate, care rules, needs, friendship and daily routine |
| `aiko_pet/personality/` | Dialogue selection, personality, adaptive habits and workload events |
| `aiko_pet/application/` | Typed use cases, attention/activity coordination and read contracts |
| `aiko_pet/presentation/` | German UI text, visual policies and reaction playback |
| `aiko_pet/ui/` | Tkinter character, hover, status, settings and speech widgets |
| `aiko_pet/desktop/` | Tk runtime, native Windows window/input handling and preferences |
| `aiko_pet/infrastructure/` | Hardware providers and versioned local JSON persistence |

The bootstrap is `aiko_pet/gui.py`. Imports use the owning packages directly; obsolete flat-module paths have been removed. See the architecture guide for the import migration table. [Architecture and dependency rules →](docs/ARCHITECTURE.md)

### Tests

```bash
python -m unittest discover -s tests -q
```

GUI tests require a display; on Linux use `xvfb-run -a python -m unittest discover -s tests -q`. [GitHub Actions](https://github.com/Lexoniarus/aiko-desktop-pet/actions/workflows/tests.yml) runs Python 3.11/3.13 under Linux/Xvfb, Windows headless regressions, Ruff, strict Mypy and Pyright. Real Windows window behavior was also checked by the project maintainer during the October 2026 refactor.

See [Contributing](CONTRIBUTING.md), the [current change history](CHANGELOG.md),
[development workflow](docs/GITHUB_WORKFLOW.md), and
[historical feature notes](docs/HISTORY_0_2_TO_0_13.md).

## Artwork, fonts and licensing

- **Project code** is under the [MIT License](LICENSE).
- **Current Aiko Anime character assets** have [restricted reuse terms](assets/aiko-anime-8-frames/LICENSE.md), separate from MIT. Use in Aiko Desktop Pet is allowed; other reuse and redistributed forks containing these assets require Alex's explicit consent. The previous sprite release retains its earlier MIT designation. See [asset provenance](ASSETS.md).
- **Kenney Emote Pack and UI Pack: Sci-fi** artwork is [CC0 1.0](LICENSES/KENNEY_CC0.md), with voluntary credit to [Kenney](https://kenney.nl/).
- **Font binaries are not shipped** and are not relicensed by this project.

Please consult [ASSETS.md](ASSETS.md) for provenance, attribution and limitations.
Security and private vulnerability reporting are explained in
[SECURITY.md](SECURITY.md).

Aiko Desktop Pet is an independent project, separate from ComfyReview and
Character Chronicles.
