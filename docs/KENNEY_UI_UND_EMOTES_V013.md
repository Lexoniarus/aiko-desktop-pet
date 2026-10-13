# v0.13 — Kenney sci-fi interface and sequential emotes

## Interaction contract

An emote is **not** an extra bubble shown next to Aiko's dialogue. It is a timed expressive step in **the same reaction sequence**.

Examples:

- `question emote → text → heart emote` for a surprised, slightly awkward friendly click;
- `exclamation emote → text` for a sudden interruption or workload increase;
- `heart → text → optional follow-up text → heart` for an affectionate moment;
- `text only` for an understated reply;
- `emote only` for occasional wordless idle observations.

**One presentation slot:** Each step fully replaces the previous emote or text before the next begins. The existing speech-bubble-like Tk Toplevel is reused rather than opening multiple simultaneous bubbles. A generation counter prevents delayed callbacks from canceled sequences from reappearing.

A new user interaction interrupts the current sequence. During rapid click bursts, the introductory emote may be skipped so Aiko does not endlessly restart the first visual cue without reaching her actual response.

The dialogue catalog assigns `emote_before` and `emote_after` for semantically appropriate sequences; emotes are **not attached at random**. Existing two-part, self-correcting speech remains supported.

## Source material

The user supplied the following paths from a purchased Kenney Game Assets All-in-1 3.4.0 bundle:

- `2D assets/Emote Pack/PNG/Pixel/Style 1`
- `UI assets/UI Pack - Sci-fi/PNG`
- Reference layout: `UI Pack - Sci-fi/Sample.png` (the third-party sample is stored separately at [`docs/references/Kenney_SciFi_Sample_Referenz.png`](references/Kenney_SciFi_Sample_Referenz.png), not mixed with current application screenshots).

The shipped assets include **15 unchanged pixel emotes** and a small selection of Kenney-based sci-fi panels and buttons; the rest of the complete bundle is intentionally not included. Aiko's **73 original character sprites** are unchanged.

The included Kenney license files identify both asset packs as **CC0 1.0**, regardless of their purchase as part of the All-in-1 bundle. Voluntary attribution is included in [ASSETS.md](../ASSETS.md) and [LICENSES/KENNEY_CC0.md](../LICENSES/KENNEY_CC0.md).

## Typography

The user-supplied **Kenney Mini** font is selected automatically **only if already installed on Windows**. Otherwise Aiko uses Segoe UI. Font binaries are not included in the repository; the user can install a separately obtained copy according to its applicable terms.

## UI compatibility

All six Tamagotchi indicators, care actions, `Status` and `⋯`, the draggable hover panel, its saved position and auto-hide, an independently attached bubble above Aiko, Windows window stacking, daily habits, and the `%LOCALAPPDATA%` save file remain available.

## Known limitations

- The automated GUI tests run under Linux/Xvfb; real Windows 11 window stacking during browser microphone input still warrants testing.
- Without a locally installed Kenney Mini font, the UI uses Segoe UI.
- Emotes are short expression cues rather than replacements for actual animation sprites.
