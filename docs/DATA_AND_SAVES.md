# Packaged data and local saves

## Resource ownership

| Resource | Owns |
| --- | --- |
| `aiko_pet/data/balance.json` | Initial values, care effects, hunger/digestion, fun/mood, friendship, movement, attention and adaptive behaviour parameters |
| `aiko_pet/data/moodlets.json` | Eighteen typed Moodlet family definitions and per-type parameters |
| `aiko_pet/data/wishes.json` | Eleven wish objectives, supported targets, round scope and positive fulfillment references |
| `aiko_pet/data/food_catalog.json` | Food IDs, display names, nutrition, categories and menu order |
| `aiko_pet/data/texts.de.json` | UI wording, status templates, care fallback text, game labels and emergency farewell fallback |
| `aiko_pet/data/object_grammar.de.json` | German grammatical gender and optional spoken-name override for every consumable; no duplicated nutrition/menu names |
| `aiko_pet/data/dialogues.de.json` | Version-2 character sequences, relationship/state filters, stories and rotation |
| `aiko_pet/data/routine.de.json` | Weekday/weekend schedules, activity labels and meal windows |
| `aiko_pet/assets/animation_timing.json` | Frame holds and playback sequences |
| `aiko_pet/assets/items/items.json` | Item images, icons and hand pivots |
| `aiko_pet/assets/playing_cards/provenance.json` | Imported Kenney card filenames, source package and hashes; independent of World items |
| `aiko_pet/assets/animations.json` | Prepared character frames and provenance metadata |

Python owns rules, types, supported semantic IDs and technical constants such
as pixel dimensions, calendar structure and floating-point tolerances. It does
not contain a second editable nutrition, balance or translated wording table.
The parameter dataclasses remain available under their existing Python names;
their defaults come from the validated balance resource.

Resource files are loaded once and exposed as immutable catalogues. Restart
Aiko after editing them. There is no runtime network download, arbitrary code
execution or extra pip dependency for this data layer.

Optional [social API content](SOCIAL_CONTENT.md) is separate from the packaged
catalogues. The existing settings owner persists `online_social`, default false;
only a saved Boolean true enables it. Provider content, preparation buffers and
pending requests are session-local and never enter the version-one save.

RPS, Blackjack and Tic-Tac-Toe sessions are temporary. Their scores, decks,
boards and hidden/revealed cards are not serialized. Closing reports completed
units through the existing application game-experience path before final save;
ordinary session scores still do not persist. Optional inner wishes may now
store only a bounded objective block (round identities and win/loss counts),
not the game session itself. Game-to-wish reporting consumes actual round results;
the storage contract does not reconstruct or replay games.

## Validation and editing

Resources reject duplicate JSON keys, non-finite numbers, unsupported versions,
missing required fields and unknown fields. Text keys must match their
consumer contract, and placeholders must have exactly the required names.
Dialogue events, typed condition domains, day periods and animations must be supported IDs.
Nutrition IDs must match visual item IDs; asset paths must stay within their
asset directory. Frame order, count and timing are checked together.

Balance values use names that state their meaning and units. Integer counters
and milliseconds cannot be booleans or fractional numbers. Fractions and
probabilities stay within 0..1; mood anchors, response rates and hardware ranges are consistent; interval minimums
cannot exceed their maximums; simulation divisors and steps must be positive.
The shared sleep/resource grid uses the numeric need interval (15 seconds);
the unused former five-minute routine interval is removed. Elapsed-time advancement has no
catch-up age limit; the former eight-hour limit and its parameter are removed.

Adding a new parameter, text key or dialogue event requires updating the
corresponding typed consumer and its contract in `pet/balance_contract.py`,
`pet/text_contract.py` or `pet/mind/dialogue_events.py`. Changing an existing
value or sentence does not require another Python copy of that value.
Run the resource validation and functional tests before sharing changed data.

### Character copy

Spoken character game reactions live in the dialogue catalogue; countdowns,
player-facing labels, status displays and emergency care fallback wording stay
in the text catalogue. Catalogue version 3 retains the ordered `beats` list
introduced in version 2, replacing the mixed condition vocabulary. Each text beat
has 1–125 characters and derived reading time; emote/pause beats may specify a
bounded duration. Short reactions have at most two text beats, stories at most
five. Named filters use supported `stages`, day periods and weekdays;
`requires_present` requires observed or direct contact. `conditions` contains
alternative clauses (OR), whose populated fields combine (AND):
`emotional_states`, `emotional_directions`, `need_conditions`, `reaction_tones`,
`situational_conditions` and boolean `sleeping`. State/tone choices within one
field are alternatives; directions/needs/situations require every listed fact.
For example, `low_satiety` never qualifies as an emotional state, while `proud`
never qualifies as a care condition. Old `moods`/`needs` keys are rejected.
All 1,082 catalogue IDs and their authored text/emote beats were preserved in
this schema migration; display labels live in `texts.de.json`.
Object placeholders are allowed only on object events. The finite contract in
`pet/object_text_contract.py` permits bare `{item}` for compatibility plus
`item_{indef|def|poss|pron}_{nom|acc|dat}` and sentence-initial `Item_...`
variants: indefinite/definite/possessive noun phrases and pronouns in nominative,
accusative and dative. Attribute/index access, conversions and format specs are
rejected. No expression evaluation or general-purpose German language engine
is involved. `pet/content.py` validates the grammar resource once against the
canonical food IDs plus `energy_drink`; only presentation inflects it.
Unknown identity uses “Gegenstand”; a possessive field becomes a definite
reference rather than inventing ownership. A learned new portion uses an
indefinite form; missing/found and saved-supply lines use possessives where
subjective history supports them. Care food fallbacks use the same full
indefinite nominative phrase. Menu names stay catalogue-owned and unchanged.
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
unfinished stories and rotation history remain session-local. B2 search
reunion transfers assessment/placement intent to the actual identified finding
and retires the old subjective subject. Its acquired World reference remains
factual. Existing object memory v3 / outer save v1 round-trip without migration;
the search's current findings remain task-local, with known stock excluded when
a task is rebuilt from saved missing subjects.

## Optional Moodlet state

The existing outer version-one save now includes optional `pet.moodlets` with
its own version-one codec. Frozen episode values belong to `PetValues`, and the
complete existing checkpoint/restore path includes them. Store stable instance
IDs, family IDs, intensity, elapsed timestamps, remaining stage time and consumed
per-level relief allowances together. The latter survive refresh/escalation and
recovery pauses; loading does not grant new allowances or advance the timers.

Missing legacy sections start empty at the saved elapsed baseline. Invalid or
future sections are not partially interpreted: other valid pet values survive,
and StateStore preserves the original file before replacing it through its
existing atomic-save path. No separate save, clock or emotional score is added.
Stage 5B.3 now advances existing episodes and their numeric mood effects through
the shared progression path. Stages 5B.4/5B.5 supply negative interaction and
prolonged-poor-care triggers. Decoding never advances stored episodes or invents
triggers.

The optional `moodlets.interactions` extension stores communicated poke/petting
boundaries, the independent petting-refusal deadline and bounded food repetition
evidence (current food, at most the configured repetition count of elapsed intake
timestamps, pending/communicated variety request and saturated ignored-portion
count). Earlier 5B saves lacking this extension start with neutral evidence.
Unknown food IDs, future evidence, invalid counters and inconsistent request
fields invalidate that optional Moodlet section, preserving unrelated pet values.
Relationship penalties remain in `relationship.penalties`: each kind retains
only its own rolling window, including petting, food-variety and relocation
caps. Request expiry/new episodes/restart do not refund those budgets. Transient
observed cursor-take attribution is never reconstructed from saved World truth.

The optional `moodlets.poor_care` extension records a baseline and exactly five
processing cursors, indexed by the canonical need names. Each cursor contains
an accounted watermark, the latest handled threshold watermark, handled level
and an open-exposure-cycle flag. Watermarks contain elapsed time and consumed
critical/zero duration in the anchor minute, so partial minutes and coalesced
full spans can share the original history without rounding replay or duplication.
This is bounded processing metadata, not another exposure record collection.

Missing older sections remain uninitialized until the next valid progression
endpoint; existing old care history is not replayed into new emotions. Need
improvement alone does not discard the unaccounted remainder. Actual qualified
recovery closes already handled burden; the remaining amount stays in the same
rolling 24-hour history. Markers, current stage progress and relief usage survive
checkpoint, save/reopen and paired Pet/World consumption rollback. Future markers,
invalid levels/flags, missing/unknown needs and malformed offsets invalidate the
optional Moodlet section under the existing backup/preservation rules.

Each active Moodlet may additionally store `attribution`: `user`, `autonomous`
or `unknown`. This describes the latest qualifying cause's known origin;
episodes saved before 5B.8 default to unknown. Loading never fabricates blame.
The optional section and outer save remain version one. Overall emotional
composition, localized labels, current wish restrictions and read-side
countdowns are derived, never serialized as a second source of truth.

## Optional wish state

`pet.wishes` has a focused version-one codec in that same outer save. `WishState`
is frozen and owned in `PetValues` alongside Moodlets. Persist up to three active
wishes, at most one per area, with stable instance IDs, catalogue objective and
concrete target IDs, elapsed creation/expiry times and actual expression times.
Keep original deadlines on load, even when already expired; domain progression
will resolve expiry later. Do not infer speech from a queued/displayed status.

Game wish progress stores only the objective's bounded round identities and
Aiko's win/loss counts. Shared play includes a session token to distinguish its
single-session requirement. Normal decks/boards/session scores remain transient.
Creation evidence for at most four areas and the last actual wish expression
survive ended wishes. The optional elapsed `refill_not_before` deadline also
survives retirement and restart; legacy v1 records without it remain valid.
The next instance ID is retained when the active collection becomes empty.
These values support later duplicate-safe fulfillment; no reward is generated
by decoding, and no parallel relationship accounting is stored in wishes.

Awake live evaluation fills the normal three-wish stock, at most one per area.
Retirement starts a twelve-minute refill pause; later vacancies do not postpone
it. Expiry schedules from its original deadline, including closed time. No new
save version, independent timer or retrospective wish sequence is introduced.
All time paths remove a wish at its original four-hour deadline without a penalty,
retaining its retired identity and creation evidence. A restart fills only current
free slots after live evaluation resumes and any saved refill deadline is due.

Only an actually presented wish text records `expressed_at` and the shared
thirty-minute expression anchor. Merely selecting text, showing status or
canceling before text does not count. Temporary activity restrictions and low
trust/mood preserve the original stored wish; they do not pause or extend it.
Wording for all eleven forms is validated in `texts.de.json`, with canonical
food/game labels and objective round counts interpolated at presentation.

Stage 5B.7 retires the matching stable identity on actual fulfillment, leaving
creation/disclosure pacing intact. Its positive Moodlet and eligible personal
bonus commit with that retirement in the existing aggregate/action transaction.
Autonomous food intake has no personal bonus. `relationship.rewards` accepts
`wish` alongside ordinary care kinds; both share the unchanged two-hour/day
ceilings. The bounded reward-list capacity additionally allows the maximum
creation cadence plus three wishes carried into the history window. No separate
wish budget, completion archive, save file or top-up queue is introduced.

Fixed game-block progress survives window closes and reloads. Shared play resets
partial progress for a different session; an eventual round-win objective keeps
only the last unsuccessful round identity while retrying. Actual pending rounds
and social playback stay transient, so restart does not replay or complete them.
Only qualifying started/settled rounds can extend persisted objective progress.

Missing old sections stay empty. Invalid sections preserve valid Moodlet/care
values, and the existing atomic repository backs up the original bytes before
replacement, including when saving without first loading. Whole-Pet checkpoints
include both collections, so the existing joint consumption transaction can
restore them together with World custody and subjective object memory.

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
| `object_memory` | Optional subjective records (`version: 3`, v1/v2 readable): learned type/assessment, relative active age, place status, possible source links, allocation provenance and own-placement disposition |

`pet.updated_at` is a Unix wall-clock timestamp in seconds. Need values are
saved to four decimal places. Older version-one saves missing newer optional
fields retain their existing defaults. Raw hardware samples, window titles,
keystrokes, pending dialogue and unfinished game rounds are not saved.

The optional `pet.time` section has its own `version: 1` and nonnegative finite
`lived_seconds`. This is the aggregate-owned elapsed axis since introducing
this record, including subsequently reconstructed closed time. It is not an
uptime, wall timestamp or claim about observed user activity. It survives
wall-clock rebasing and checkpoints. Legacy saves start at zero without
inventing earlier contact, rewards or neglect history; existing progress is
retained. Malformed/future time sections start neutral, preserving pet progress,
and the original file is backed up before replacement. Outer save version is 1.

Stage 3 now uses this elapsed axis for rolling relationship and critical-need
histories inside `PetValues`. Sleep episodes share that owner; learned
expectations remain in adaptive memory. Missing qualifying contact remains
unknown, not inferred from an app timestamp or from the time record alone.

Normal saves occur about every 55 seconds and after the application's existing
care, preference and orderly shutdown paths. `StateStore` writes a temporary
UTF-8 JSON file beside the save, flushes and synchronizes it, then replaces
`state.json` atomically. A failed write leaves the existing file intact.

If an unreadable or unsupported-version file is about to be replaced by a new
session, its original bytes are first preserved beside it under a unique
`*.aiko-save-backup` name. Those backups are ignored by Git. Failure to create
the backup prevents replacement of the original file. Valid saves do not
produce these backup files on every autosave.

## Relationship history

Stage 3 adds optional `pet.relationship` v1 alongside the unchanged outer save
v1. Baseline, last qualifying contact, per-type eligibility, actual rolling
reward entries, per-need critical/zero exposure and direct-action budgets use
`pet.time.lived_seconds`, never inferred mouse activity or wall-clock age.
Exposure has minute resolution and coalesces homogeneous buckets into spans;
its default 24-hour history is bounded to 1,441 spans. Reward/event histories
are bounded by their finite action set, timing and caps. Legacy calendar
reward fields remain compatibility metadata, not a second active calculation.

New histories are part of the complete immutable checkpoint and joint rollback.
Absent or malformed history preserves pet progress and starts tracking at
first upgrade reconstruction completion, without retroactive loss or invented
personal contact. Once saved, that baseline survives restart. Unsupported or
invalid records cause the original bytes to be backed up before replacement,
just like invalid time records. Strict validation rejects future timestamps,
unknown fields/actions, invalid durations, overlapping spans and exceeded budgets.
See [friendship rules](FRIENDSHIP_SYSTEM.md) for care/contact qualification.

## Sleep history and learned expectation

Optional `pet.sleep_episode` v1 belongs to `PetValues`: type, elapsed start,
actual sleeping seconds, expected wall-time endpoint, manual/search/intake
elapsed deadlines and failed food-source evidence. Short awake food breaks
retain the episode. Failed source IDs describe current attempted stock, not an
input-event log; the saved list is bounded to 4,096 entries. Optional
`adaptive.quiet_window` v1 stores the expected local endpoints, at most seven
coarse completed phases and the last adjustment day. Actual input sampling and
current return detection remain session-local.

Legacy records preserve needs/World/relationship without inferring historical
sleep duration, manual grace or observed quiet. Corrupt/future optional records
require preservation of original bytes before replacement. No new top-level
schema or settings file is introduced. See [sleep rules](SLEEP_SYSTEM.md).

## Real time, closed sessions and standby

> Stages 1–4 of the [implementation plan](CARE_TIME_IMPLEMENTATION_PLAN.md)
> provide real time, need/mood balance, friendship and adaptive sleep with finite
> stock. See the maintained [sleep guide](SLEEP_SYSTEM.md) for current priorities.

Loading JSON only decodes data. `PetSessionRestorer` subsequently calculates
closed time from `pet.updated_at` to the current clock, without truncating the
absence. `pet.lifecycle.TimePlan` streams chronological steps rather than
allocating a list proportional to the gap. Missing or corrupt saves do not
generate catch-up; a backwards clock produces zero elapsed time and rebases
the next anchor. The obsolete `simulation.maximum_catchup_seconds` setting has
been removed. Stage 2 applies the [need/mood rates](FUN_MOOD_SYSTEM.md) through
the same pure domain path. Existing saved mood is preserved on load and
approaches its new target over elapsed time; no balance migration resets it.

`StateStore.load_session()` reads state, settings and adaptive memory together
into one `LoadedPetData` snapshot. The old partial `load()` and `load_memory()`
wrappers have been retired; loading this snapshot never advances time itself.

During this calculation there is no observed workload, inferred user input,
human care reward, friendship gain or fabricated rhythm learning. Needs and
digestion and the recorded relationship timeline still progress. No contact
clock is renewed merely by opening the app. Expected sleep can restore energy;
manual commands retain 30 minutes of elapsed protection. Turning automatic
routine off disables new automatic sleep, not elapsed time or an existing
protected episode's endpoint. Elapsed time cannot generate catalogue portions
or personal care credit.

After restoration, the timestamp is anchored at the current time. The shared
`ActiveSessionClock` then consumes running-session time exactly once across
ticks, care, completed games and saves. Windows uses `GetTickCount64`, Linux
uses `CLOCK_BOOTTIME`; both include suspend while ignoring wall-clock changes.
These semantics are documented by
[Microsoft](https://learn.microsoft.com/windows/win32/sysinfo/windows-time) and
[Python](https://docs.python.org/3.11/library/time.html#time.CLOCK_BOOTTIME).
If uptime is unavailable or resets, a nonnegative wall-time difference bridges
that interval. Both anchors advance together so recovery does not replay it.
Failed live advancement restores the pet checkpoint and clock anchors together.
The live clock is aligned with the closed-time endpoint before loading and
catch-up work, so time spent initializing the application remains part of the
next live interval instead of being lost or counted twice.
`application.active_time.SessionInputs` carries the shared live-time context;
ticks, care and completed games use the same `advance_session_time()` function.
Closed-time reconstruction and wall-time fallback cannot distinguish a real
absence from an unobserved forward clock correction. Positive wall differences
are treated as elapsed; no eight-hour cap hides the uncertainty. During a
running session, a valid suspend-inclusive uptime takes precedence over wall
corrections. DST/timezone changes affect local schedule labels, not elapsed
duration. Known uptime is not serialized across a computer reboot.

The latest hardware/input snapshot covers only the existing 30-second recent
observation window, not hours of unseen time. Current bedtime/nap activity flags
likewise do not rewrite historical routine decisions. Older intervals carry
unknown activity. Active observation time remains separate: existing
`active_uptime_seconds()` still excludes suspend for World physics/perception,
and closed time creates no sensory evidence or learned human activity.

Live autonomous consumption requires an observed/remembered World portion and
the normal interaction sequence. Restoration constructs World and acquired
knowledge before `SessionTimeProgression` coordinates closed-time consumption.
Only previously identified, actually accessible stock can be used. The same
`ObjectConsumption` transaction owns removal, nutrition and memory; a failed
joint progression restores pet/World/memory and the live clock together.
Reopening presents the result without historical Tk playback.

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
