# Relaxed Aiko animation timing — desktop simulation

The desktop pet retains eight unique 192×208 PNGs for every regular clip.
Only playback changes: no source artwork, anchor, food overlay or game asset
is regenerated.

## Edit the profile

The single source of truth is `aiko_pet/assets/animation_timing.json` (version 3).

- `frame_duration_ms`: eight durations in milliseconds for source poses
  `0` through `7` per animation, even if a pose is replayed.
- `frame_sequences`: optional list of source pose indices. Missing entries
  mean the ordinary `0,1,2,3,4,5,6,7` order.
- The `waving` sequence revisits poses `3,4,5` for two hand waves while
  retaining the original eight PNGs.
- Longer last-pose holds in `waiting` and `review` provide quiet intervals
  between gestures. These are repeating ambient behaviors, not frame interpolation.

`idle` is intentionally **unchanged** at eight × 160 ms. Its separate head
sway, blink gap and spontaneous glances also remain unchanged.
`attack` remains **unchanged** at eight × 215 ms; the future gameplay core
will own responsive combat timings independently.

| Clip | Before | Relaxed test profile |
| --- | ---: | ---: |
| Idle | 1.28 s | **1.28 s** |
| Running right / left | 1.28 s | 1.52 s |
| Waving | 0.72 s | 1.895 s (14 playback steps) |
| Jumping (joy) | 0.84 s | 1.50 s |
| Failed | 1.20 s | 2.47 s |
| Waiting | 2.52 s | 4.57 s |
| Review | 2.52 s | 5.06 s |
| Sleep | 2.56 s | 4.00 s |
| Petting | 2.40 s | 2.90 s |
| Eat | 2.32 s | 3.59 s |
| Attack | 1.72 s | **1.72 s** |

The frame clock still presents every authored playback step even after late
GUI callbacks; walking distance is derived from the actual walk clip duration.

## Rebuild and validation

The checked-in runtime manifest (`aiko_pet/assets/animations.json`) mirrors
this policy: each unique image retains its per-pose `duration_ms`, and the
clip stores `sequence` and `playback_total_ms` separately. The loader rejects
missing/mismatched policies and invalid references before loading the GUI.

To regenerate after editing the profile, run:

```bash
python tools/prepare_character_assets.py
python -m unittest discover -s tests -q
```

The rebuild requires Pillow; normal desktop runtime does not. When reviewing
the visuals, adjust the **movement rhythm first**. Generate new in-between
artwork only if a pose transition is still visibly jumpy at good timing.
