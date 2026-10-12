# Dialogue, events, emotions, and animation — original v0.7 design

This file documents the **v0.7 dialogue foundation**. Some quantities and behaviors have changed in later releases; for current Tamagotchi balancing and emote sequencing, also see the v0.10–v0.13 documentation.

## Character voice

Aiko's character sheet describes someone observant, precise, reserved about intimacy, sensitive without melodrama, and quietly sarcastic. In trusted moments she shows affection without becoming loud. Statements are generally short, dry, and deliberate.

Avoid forced cuteness, nonstop conversation, and any Academy or Character Chronicles roleplay. In later releases, the desktop version also developed an awkwardly funny streak.

## Component responsibilities

- `routine.py`: local clock, weekdays, meals, and sleep windows without external fictional obligations.
- `domain.py`: needs, care actions, and sleep state.
- `dialogue.py`: emotion derivation in `AikoMind` and weighted selection in `DialogueBook`; neither depends on the GUI or external services.
- `data/dialogues.de.json`: editable **German** dialogue with fields such as `id`, `event`, `text`, `moods`, `periods`, `weekdays`, `animation`, `weight`, and `cooldown_seconds`. The catalog has expanded since the original 236 entries.
- `system_activity.py`: local CPU/RAM/uptime and optional NVIDIA GPU observations, collected without reading files or applications.
- `gui.py`: event dispatch, sprite rendering, speech bubbles, and optional autonomous comments.

## Original emotion precedence (v0.7)

1. Sleeping: limited quiet responses; ordinary clicks do not force wake-up.
2. Temporarily irritated after a rapid click burst.
3. Energy at or below 25: tired.
4. Satiety at or below 25: hungry.
5. Mood at or below 28: withdrawn.
6. Shortly after a positive care action: receptive or affectionate.
7. Mood at or above 82 and energy at or above 45: playful.
8. Otherwise: calm.

Later releases added social needs, affection, friendship, and multi-stage click reactions. The values above record the earlier rule set rather than override current code.

Aiko's mood is sampled **before** a care action so her response to being fed, for example, can still reflect her hunger even though satiety rises immediately.

## Core dialogue events

| Trigger | Examples of `event` | Notes |
| --- | --- | --- |
| Startup | `greeting` | Weighted by time of day and weekday |
| Left/right mouse click | `click_left`, `click_right` | Does not provide care by itself |
| Repeated clicking | `rapid_click` (original) | Later releases add escalation and deliberate silence |
| Click while sleeping | `sleep_click` | Does not automatically wake her |
| Care | `pet`, `play`, `play_tired` | Pre-action state affects speech |
| Food | `feed_meal`, `feed_snack`, `feed_full` | Meals versus snacks versus already full |
| Sleep | `sleep`, `wake` | Manual or automatic |
| Return after an absence | `return` | Triggered only by an actual re-approach |
| Cursor | `cursor_follow`, `cursor_far` | Rare, with cooldown |
| Stopping a walk | `walk_pause` | Rare and optional |
| Timed context | `idle`, `hungry`, `tired`, `low_mood`, `morning`, `midday`, `evening`, `night`, `weekend`, `monday`, `friday` | Reserved, nonintrusive observations |

## The computer's workload as Aiko's own effort

`ComputerVoice` converts local hardware measurements to subjective exertion. CPU/GPU are primary signals; RAM/VRAM allocation only modestly indicates memory pressure. Reserved memory alone is not proof of actual work. Missing values remain unknown.

On Windows, samples are taken around every **six seconds**, with smoothing of two samples for CPU/GPU. Aiko **does not say technical component names in her speech**; those values may still be shown numerically in the status panel.

| Event | Interpretation |
| --- | --- |
| `computer_effort_rising` | Work is increasing |
| `computer_effort_heavy` | Sustained high workload |
| `computer_effort_peak` | A sustained demanding peak |
| `computer_effort_easing` | Work is becoming easier |
| `computer_effort_recovered` | Relief after confirmed work |
| `computer_effort_recovered_peak` | Relief after a prolonged intense interval |
| `computer_effort_rest` | A long quiet spell |
| `computer_effort_steady` | Consistently occupied |
| `computer_uptime` | Context from how long the PC has been running |

The design requires a real sustained workload before expressing major exhaustion; short spikes must not be treated as lengthy completed tasks. The original minimum was approximately **18 seconds** of sustained high load, combined with per-event spacing and longer cooldowns for spontaneous remarks.

Her status line may summarize her own experience; diagnostics may display CPU/GPU/RAM percentages. No measurement identifies the active program or user intent.

**Historical note:** v0.7 used workload to affect behavior and sprite choices, not the Tamagotchi need decay. Measured workload began affecting satiety, mood, and energy in v0.11.

## Speech bubbles and movable status panel

Speech belongs directly to Aiko's head, not to her movable status panel. The panel appears on hover, can be dragged by its header, remembers its position, and hides when dismissed or after moving away. The separate detailed status window remains independent.

A catalog entry with empty `moods`, `periods`, or `weekdays` matches any value on that axis. Specific matches receive higher weights. Selection avoids the last several lines where possible, honors cooldowns, and falls back gracefully when all candidates are temporarily restricted.

## Supported sprite groups

`idle`, `waiting`, `review`, `waving`, `jumping`, and `failed` can accompany dialogue. `running-left`, `running-right`, and `running` depict movement; `look` contains **16 directional frames** and is used for cursor tracking rather than random animation.

A meal may be represented by a thoughtful pause, **not** a fictional eating animation. Similarly, the current sprite set does not contain a dedicated sleep, anger, or petting animation.

## Quality expectations

All dialogue IDs must be unique, all referenced animation groups must exist, and no event should depend on an unavailable sprite. Automated domain/GUI tests validate selection, state priority, click history, session transitions, bubbles, placement, and save migration.

Additional specialized sprite animations remain optional future work, not a claim about the current 73 frames.
