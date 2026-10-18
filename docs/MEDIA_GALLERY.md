# Aiko Desktop Pet media gallery

The public gallery contains exactly the six media files used by the README.
The UI captures show the real Tk application under Linux/Xvfb; they are not
native Windows screenshots or performance measurements. Additional detail
stills have been removed. The captures are historical illustrations and may
predate the current mood-bar hierarchy and object-count details. Use the
[UI contract](UI_WINDOW_CONTRACT.md) for the current layout and the
[documentation index](README.md#validation-and-acceptance) for separately recorded
desktop acceptance; image filenames do not establish an exact-commit sign-off.

## Desktop overview

![Aiko and the draggable, pinnable care toolbar](../vorschau/Aiko_Current_Hover.png)

The toolbar owns care controls and optional inline status details. Settings
remain an independent persistent window. See the [window contract](UI_WINDOW_CONTRACT.md).

## Reactions and ambient behavior

![Sequential emote, dialogue, follow-up and closing emote](../vorschau/Aiko_Current_Reaction_Sequence.gif)

The reaction GIF uses the real reaction player and speech presenter with
controlled cue progression. Emotes and dialogue occupy the same speech surface.

![Resting motion, a complete blink and autonomous gaze](../vorschau/Aiko_Current_Ambient_Blink_And_Glance.gif)

The ambient recording demonstrates the real Tk sprite, anchored feet,
subtle pose-relative head motion and all eight blink poses. Encoded hold
intervals illustrate pacing; they do not measure native Windows timer behavior.

## Character asset catalog

![All 112 prepared character poses](../vorschau/Aiko_Current_Animations.gif)

This sprite-only preview uses the prepared PNGs and per-pose holds from the
runtime manifest. It catalogs twelve eight-frame clips and sixteen static gaze
poses. It does not reproduce idle gaps or every derived greeting replay.
Source artwork is unchanged. See the [timing guide](ANIMATION_TIMING_PROFILE.md).

## Rock–Paper–Scissors

![The player's hand and Aiko's independently revealed hand](../vorschau/Aiko_RPS_Aufgedeckt.png)

![Real countdown, reveals, reactions and local session score](../vorschau/Aiko_RPS_Spielablauf.gif)

The player panel shows the player's own choice and session counters; Aiko's
bubble shows her own hand and reactions. Counters are not persisted.

## Manual capture and provenance

The developer-only capture commands are:

```bash
xvfb-run -a -s "-screen 0 1366x900x24" python -m tools.capture_current_gallery
xvfb-run -a -s "-screen 0 1366x900x24" python -m tools.capture_rock_paper_scissors_media
```

They require Pillow, Tk and Xvfb and write only these six files. There is no
automatic screenshot commit/push workflow. The [framing utility](../tools/media_crop.py)
captures the complete desktop and crops to the union of mapped application
windows with 24 pixels of padding, without rescaling. UI GIFs retain one
shared crop across frames.

Historical captures remain in Git history. Unused design references are
archived outside the repository. Character [asset terms](../assets/aiko-anime-8-frames/LICENSE.md),
[Kenney CC0](../LICENSES/KENNEY_CC0.md) and [Twemoji attribution](../LICENSES/TWEMOJI_CC_BY_4.md)
continue to apply. See [asset provenance](../ASSETS.md).
