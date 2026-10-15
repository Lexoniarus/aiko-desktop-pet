# Packaged data and local saves

## Resource ownership

| Resource | Owns |
| --- | --- |
| `aiko_pet/data/balance.json` | Initial values, care effects, hunger/digestion, fun/mood, friendship, movement, attention and adaptive behaviour parameters |
| `aiko_pet/data/food_catalog.json` | Food IDs, display names, nutrition, categories and menu order |
| `aiko_pet/data/texts.de.json` | UI wording, status templates, care fallback text, game labels and farewell |
| `aiko_pet/data/dialogues.de.json` | Authored character dialogue, semantic events, filters, weights and cooldowns |
| `aiko_pet/data/routine.de.json` | Weekday/weekend schedules, activity labels and meal windows |
| `aiko_pet/assets/animation_timing.json` | Frame holds and playback sequences |
| `aiko_pet/assets/items/items.json` | Item images, icons and hand pivots |
| `aiko_pet/assets/animations.json` | Prepared character frames and provenance metadata |

Python owns rules, types, supported semantic IDs and technical constants such
as pixel dimensions, calendar structure and floating-point tolerances. It does
not contain a second editable nutrition, balance or translated wording table.
The parameter dataclasses remain available under their existing Python names;
their defaults come from the validated balance resource.

Resource files are loaded once and exposed as immutable catalogues. Restart
Aiko after editing them. There is no runtime network download, arbitrary code
execution or extra pip dependency for this data layer.

## Validation and editing

Resources reject duplicate JSON keys, non-finite numbers, unsupported versions,
missing required fields and unknown fields. Text keys must match their
consumer contract, and placeholders must have exactly the required names.
Dialogue events, emotions, day periods and animations must be supported IDs.
Nutrition IDs must match visual item IDs; asset paths must stay within their
asset directory. Frame order, count and timing are checked together.

Balance values use names that state their meaning and units. Integer counters
and milliseconds cannot be booleans or fractional numbers. Fractions and
probabilities stay within 0..1; mood weights add up to one; interval minimums
cannot exceed their maximums; simulation divisors and steps must be positive.
Simulation steps cannot exceed five minutes, and the catch-up limit cannot
exceed seven days. The shipped catch-up limit remains eight hours.

Adding a new parameter, text key or dialogue event requires updating the
corresponding typed consumer and its contract in `pet/balance_contract.py`,
`pet/text_contract.py` or `pet/mind/dialogue_events.py`. Changing an existing
value or sentence does not require another Python copy of that value.
Run the resource validation and functional tests before sharing changed data.

## Where progress is stored

On Windows, paste this into Explorer's address bar:

```text
%LOCALAPPDATA%\AikoDesktopPet
```

The file is `state.json`. Linux uses
`$XDG_DATA_HOME/AikoDesktopPet/state.json`, or
`~/.local/share/AikoDesktopPet/state.json` when that variable is unset.

An optional `AIKO_SAVE_PATH` overrides the complete **file path**. An existing
environment variable wins over the optional project `.env` file. Relative
overrides resolve from the project root. This is independent of the packaged
JSON resources; personal progress is not a source asset.

Close Aiko before manually backing up or restoring `state.json`. Copy the file
to a separate location; restoring it does not require reinstalling Aiko.
Backups inside the repository must remain ignored. Aiko does not upload saves.

## Version-one format and safe writes

The existing top-level sections are unchanged:

| Section | Stored information |
| --- | --- |
| `version` | Save schema number, currently 1 |
| `pet` | Needs, friendship/reward limits, meal-day markers, sleep state, fun, food/digestion state and `updated_at` |
| `settings` | Window positions, size and behaviour/observation preferences |
| `adaptive` | Aggregated learned weekday/hour patterns and bounded rhythm state; optional in older saves |

`pet.updated_at` is a Unix wall-clock timestamp in seconds. Need values are
saved to four decimal places. Older version-one saves missing newer optional
fields retain their existing defaults. Raw hardware samples, window titles,
keystrokes, pending dialogue and unfinished game rounds are not saved.

Normal saves occur about every 55 seconds and after the application's existing
care, preference and orderly shutdown paths. `StateStore` writes a temporary
UTF-8 JSON file beside the save, flushes and synchronizes it, then replaces
`state.json` atomically. A failed write leaves the existing file intact.

If an unreadable or unsupported-version file is about to be replaced by a new
session, its original bytes are first preserved beside it under a unique
`*.aiko-save-backup` name. Those backups are ignored by Git. Failure to create
the backup prevents replacement of the original file. Valid saves do not
produce these backup files on every autosave.

## Closed time and self-care

Loading JSON only decodes data. `PetSessionRestorer` subsequently calculates
closed time from `pet.updated_at` to the current clock, bounded by
`simulation.maximum_catchup_seconds` in `balance.json` (eight hours by default).
For longer absences it simulates the most recent bounded interval. Missing
or corrupt saves do not generate catch-up; a backwards clock produces none.

`StateStore.load_session()` reads state, settings and adaptive memory together
into one `LoadedPetData` snapshot. The old partial `load()` and `load_memory()`
wrappers have been retired; loading this snapshot never advances time itself.

During this calculation there is no observed workload, inferred user input,
human care reward, friendship gain or fabricated rhythm learning. Needs and
digestion still progress. With `auto_routine` enabled, scheduled sleep can
restore energy and due main meals can be eaten without a human care reward.
Meals use the existing nutrition catalogue, fullness limit and daily meal
markers. Sleep requested manually remains a manual sleep until woken.

After restoration, the timestamp is anchored at the current time. The shared
`ActiveSessionClock` then consumes running-session time exactly once across
ticks, care and saves; Windows suspend is excluded from that live clock.
`application.active_time.SessionInputs` carries the shared live-time context;
ticks, care and completed games use the same `advance_session_time()` function.
Closed-time wall-clock reconstruction cannot distinguish shutdown, suspend
or a forward clock correction, so all are subject to the same bounded rule.

Self-served meals are **only** enabled for closed-time reconstruction. During
the live application, the existing care actions and friendly requests remain
in effect. Turning off automatic routine disables automatic offline sleep
transitions and meals, while ordinary need progression still occurs.
