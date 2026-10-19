# Packaged data and local saves

## Resource ownership

| Resource | Owns |
| --- | --- |
| `aiko_pet/data/balance.json` | Initial values, care effects, hunger/digestion, fun/mood, friendship, movement, attention and adaptive behaviour parameters |
| `aiko_pet/data/food_catalog.json` | Food IDs, display names, nutrition, categories and menu order |
| `aiko_pet/data/texts.de.json` | UI wording, status templates, care fallback text, game labels and emergency farewell fallback |
| `aiko_pet/data/dialogues.de.json` | Version-2 character sequences, relationship/state filters, stories and rotation |
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

### Character copy

Spoken character game reactions live in the dialogue catalogue; countdowns,
player-facing labels, status displays and emergency care fallback wording stay
in the text catalogue. Catalogue version 2 replaces the former first-text,
follow-up and before/after-emote fields with one `beats` list. Each text beat
has 1–125 characters and derived reading time; emote/pause beats may specify a
bounded duration. Short reactions have at most two text beats, stories at most
five. Named filters use supported `stages`, `moods`, simultaneous `needs`, day
periods and weekdays; `requires_present` requires observed or direct contact.
Item placeholders are allowed only on object events and only as `{item}`.
Object formatting applies to every text beat, never to an emote or a pause.
The resulting text determines its reading time through the dialogue balance
values. Spontaneous story frequency and quiet time use
`spontaneous_story_probability` and `spontaneous_story_quiet_seconds` in that
same section. Mutable selection history belongs to the session mind, or to
one standalone game instance; neither is a second source of authored copy.

The editorial voice is quiet, dry, curious and sometimes cheeky. Clear wishes,
charming competitiveness and sincere affection replace repeated denial of
positive feelings. Relationship stages describe growing familiarity, not new
care rules. Neither resource migration changes the version-one save schema;
unfinished stories and rotation history remain session-local.

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
| `world` | Optional separately versioned World snapshot (`version: 1`), surface, active portions, revisions and next instance ID |
| `object_memory` | Optional subjective records (`version: 2`, v1 readable): learned type/assessment, relative active age, place status, possible source links, allocation provenance and own-placement disposition |

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

> This section describes the current runtime. The separate
> [adaptive sleep proposal](ADAPTIVE_SLEEP_PROPOSAL.md) records unimplemented
> learned sleep/wake timings and full elapsed-time continuation, together with
> the [need balance proposal](NEEDS_BALANCE_PROPOSAL.md). These candidates do
> not replace the existing time, manual-sleep or self-care behavior below.

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

Scheduled self-served meals are enabled only for closed-time reconstruction.
Live autonomous consumption instead requires an observed/remembered World
portion and the normal interaction sequence. Turning off automatic routine
disables automatic offline sleep/meals; live object behavior remains available.

## Joint World recovery

Pet and World are written together through the existing flush/fsync/atomic
replacement path. Old version-one saves without `world` load an empty World.
The optional World section is validated independently: unknown definitions,
duplicate IDs, invalid geometry/revisions or unsupported versions require a
backup before replacement while valid pet progress is retained.

Only nonterminal portions are saved. Cursor-held, falling, bouncing and unconsumed pet-held
portions normalize to reachable resting ground positions; pet-held recovery uses
Aiko's position. IDs and the next-ID counter prevent accidental identity reuse.
Consumed/removed instances, live capture, animations, pending user actions and
interaction receipts are not resumed. No World consumption
is simulated while closed. A completed meal and removal of its portion share
the same durable snapshot, so restart cannot replay the meal from that snapshot.
See [isolated restart testing](WORLD_SMOKE_TEST.md).

## Subjective object knowledge

`ObjectMemory` owns learned facts separately from current perception and World
truth. Recognized identities, acquired references and assessment survive restart.
Confirmed learned-place absence marks unavailable remembered stock. Current
identified portions reunite through acquired evidence; legacy associations remain
supported without claiming hidden identity. Only unidentified sightings expire after
600 active seconds. Saved ages are relative active durations: closed time does
not age memories, accumulate sensory evidence or produce observations.

The optional `object_memory` section is captured with Pet/World and written by
the same atomic replacement. Consumption resolves its remembered target before
that save; an ambiguous consumed-find witness remains unavailable until further
evidence resolves its possible former places. It cannot be reused as supply.
Confirmed own
placement is recorded at detach; interrupted placement is distinct from keeping
a supply for later. Held/falling recovery never invents observed ground positions.

Restore does not look up a remembered identity or location in current objects.
Unseen relocation/removal can therefore leave outdated knowledge until fresh
observation or deliberate learned-place orientation and search. Actual observations and sensory progress
start empty; restored knowledge alone cannot claim current visibility.

Older saves without memory start with empty knowledge. A malformed or unsupported
memory section requires an original backup before replacement, retaining valid
Pet/World sections. Without a valid paired World, old instance-bound knowledge
is discarded rather than attaching to reused IDs in a fresh World.
Version-one records convert to subjective history; their old object labels are
never recognition evidence. Current bindings, observations and search budgets
are not serialized. Runtime checkpoints retain exact motion, while durable
World v1 writes only valid ground targets. Geometry is synchronized before saves,
including an immediate scale toggle. See the
[current custody and persistence contract](WORLD_OBJECT_CONTRACTS.md#custody-physics-consumption-and-persistence).
