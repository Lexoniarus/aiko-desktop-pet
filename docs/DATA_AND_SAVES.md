# Packaged data and local saves

Personal progress uses private SQLite schema version 2. Authored catalogs and
texts remain JSON resources in Git. JSON field paths below describe supported
legacy import records and their domain meanings; live saves write the mapped
SQLite tables, not new JSON checkpoints.

## Resource ownership

| Resource | Owns |
| --- | --- |
| `aiko_pet/data/balance.json` | Initial values, care effects, hunger/digestion, fun/mood, friendship, movement, attention and adaptive behaviour parameters |
| `aiko_pet/data/moodlets.json` | Twenty-six typed Moodlet family definitions and per-type parameters |
| `aiko_pet/data/wishes.json` | Seventeen typed wish forms, exact/flexible targets, original goals and fulfillment references |
| `aiko_pet/data/food_catalog.json` | Food IDs, display names, nutrition, categories and menu order |
| `aiko_pet/data/texts.de.json` | UI wording, status templates, care fallback text, game labels and emergency farewell fallback |
| `aiko_pet/data/object_grammar.de.json` | German grammatical gender and optional spoken-name override for every consumable; no duplicated nutrition/menu names |
| `aiko_pet/data/dialogues/de/index.json` | Version-3 character sequences, relationship/state filters, stories and rotation |
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

Optional [social API content](SOCIAL_CONTENT.md) is separate from packaged
catalogs. The settings owner stores `online_social` (default false) and the
optional zodiac sign. SQLite keeps the last 100 admitted provider IDs/text
fingerprints and actual introduction variants per API category, bounded provider
request reservations/pauses,
and the current-day horoscope's prepared reading, participation and paragraph
cursor. Joke/quote/fact payloads, warm buffers, pending playback and credentials
are not stored. Both Sprueche sources share category `single`; quote identities
are namespaced `zitat-service:<entry-id>`. Reservations are committed before HTTP;
a failed save prevents dispatch. Restart and opt-out retain quota metadata.
The social-history codecs support versions 1/2/3/4, with defaults only for
fields absent from the supported older version. Present invalid, excessive or
duplicate data stops import. Admission saves care and receipts in one transaction.

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

PL-1B stores the one authored catalogue under `data/dialogues/de/`. Its
`index.json` has `index_version: 1`, `catalogue_version: 3`, `language: "de"`,
an explicit ordered `files` list and a `line_order` list naming every source ID
exactly once. The latter preserves the old global sequence order, including
seeded weighted selection, even when an event has entries in different files.
Each source retains the existing version-three `{catalogue_version, language,
lines}` shape. Edit each complete sequence only in its listed topic file; add or
remove its ID in `line_order` when intentionally changing catalogue membership.

Populated sources cover `events/{objects,care,games,contact,work}.json`,
`spontaneous/{needs,state}.json` and PL-5's
`plaudern/{state,games,food,affection,social,negative_experiences,long_term}.json`.
Further planned story families get files when implemented; there are no empty
placeholder catalogues. PL-5 removed all sixty old requested-chat entries and
added a first set of grounded stories. PL-6C removes the fifty inventoried
ungrounded idle/calendar sequences and routes the eight preserved morning/night
fatigue variants through `tired`, with their other fields unchanged. All five
protected event sources remain unchanged. Spontaneous selection may yield silence
and never promotes a short comment into requested Plaudern.

`pet/mind/catalog.py:DialogueBook.from_file()` remains the single loader and
selection owner. The default is the index; an explicitly supplied standalone
version-three source is still supported by the same parser. There is no old
packaged monolith or fallback loader. Missing sources, invalid relative paths,
duplicate files/IDs, nested indexes and incomplete/duplicate ordering fail before
playback. Unlisted JSON is never recursively discovered. Ship the complete
indexed source directory with the application.

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
`situational_conditions` and boolean `sleeping`. PL-5 additionally supports
semantic `conversation_topics`, `conversation_attributions` and
`conversation_causes`. Their values are validated; every requested `talk` clause
must bind a topic. Topic-bound placeholders are limited to proved fields
(`target`, `count`, actual Blackjack totals or the existing `wish_text`).
PL-6A adds typed `conversation_objectives`, `conversation_targets`,
`conversation_outcomes`, `conversation_round_outcomes` and `conversation_wishes`.
The aggregate goal outcome is distinct from its final round. Revealed RPS-hand
topics may render `aiko_move`/`player_move` using existing German move labels;
older missing-detail topics may not. These filters project saved causes and
their original wish snapshots without new storage fields. PL-6B adds typed
`social.content.*` topic keys for retained original words and separate author/
setup/punchline references. Source placeholders occupy a complete bubble and
render literal, visibly shortened prefixes when needed; the original stored
parts remain complete. Category-only causes cannot invent those words.
The parser permits a named `{target}` in monotony/disregarded-food stories only
under a canonical-food target guard. Long-term topics cannot render individual
gift/game fields or internal counters from a period summary. These story families
use the existing cause envelopes and introduce no save format or schema change.
State/tone/topic/cause choices within one field are alternatives;
directions/needs/situations require every listed fact. Topic selection reads
existing wish/Moodlet facts; it adds no conversational storage or schema fields.
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
values. The obsolete spontaneous story probability/quiet controls are retired
from the strict balance contract; ordinary attention cadence, variant cooldowns
and reading-time settings remain. Mutable selection history belongs to the session mind, or to
one standalone game instance; neither is a second source of authored copy.

The editorial voice is quiet, dry, curious and sometimes cheeky. Clear wishes,
charming competitiveness and sincere affection replace repeated denial of
positive feelings. Relationship stages describe growing familiarity, not new
care rules. These authored resources remain independent of personal save schema changes;
unfinished stories and rotation history remain session-local. B2 search
reunion transfers assessment/placement intent to the actual identified finding
and retires the old subjective subject. Its acquired World reference remains
factual. Legacy object memory v3 / outer save v1 import without inventing knowledge;
the search's current findings remain task-local, with known stock excluded when
a task is rebuilt from saved missing subjects.

## Optional Moodlet state

SQLite stores Moodlet episodes, stage budgets and causes in their owned tables.
The legacy outer v1 format has optional `pet.moodlets` with a strict v1 codec. Frozen episode values belong to `PetValues`, and the
complete existing checkpoint/restore path includes them. Store stable instance
IDs, family IDs, intensity, elapsed timestamps, remaining stage time and consumed
per-level relief allowances together. The latter survive refresh/escalation and
recovery pauses; loading does not grant new allowances or advance the timers.

Missing legacy sections start empty at the saved elapsed baseline. Present
invalid or future sections stop the complete import; no part is silently
discarded and no fresh session replaces the source. No separate save, clock or emotional score is added.
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
fields invalidate import of the whole legacy save; the source is left intact.
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
entire legacy import; the original remains untouched.

Active episodes retain a bounded chronological `causes` tuple of language-neutral
facts: semantic receipt, elapsed timestamp, attribution, actual outcome and, for
wish results, the original target/objective/count snapshot and available game
result/counts. Retention is at most the current intensity: one/two/three actual
causes at level one/two/three. Renewal at level three retains the latest three;
decay trims to the newest fitting the lower level. A stronger single event or
incomplete old save may have fewer actual causes. Missing events are never
fabricated and ended episodes have no separate archive.

PL-2/PL-3 add optional `game_details` to a retained cause. For Rock Paper Scissors
it contains `game_id: "rock_paper_scissors"`, `player_move` and `aiko_move`, each
using the canonical rock/paper/scissors vocabulary from `games/contracts.py`.
For Blackjack it contains `game_id: "blackjack"`, `player_total`, `aiko_total`
and `reason` from the actual settled hand. Reasons are `aiko_bust`, `player_bust`,
`aiko_blackjack`, `player_blackjack`, `both_blackjack`, `higher_total` and
`equal_total`. Natural Blackjack means initial two-card 21; later 21 remains a
comparison/draw. An early player bust retains Aiko's real undrawn total, possibly
below 17. The game supplies these facts only after reveal and settlement.
The game event uses the player's result perspective; the cause validates the
details against Aiko's actual final-round result. For a cumulative wish that is
`game.round_outcome`, not the aggregate goal outcome. Old causes without these
facts remain valid and are not reconstructed.

SQLite reuses `moodlet_causes.details_snapshot`: version 1 remains unchanged
for causes without new facts; version 2 adds the non-null `game_details` member
beside existing `game` and `period` data. PL-4 adds version 3 with non-null
`social_content` instead of `game_details`. All three versions are read strictly;
mixed, missing, unknown or inconsistent detail fields are rejected. The database
schema version and shared transaction/revision ownership are unchanged.
Details disappear with their trimmed/removed cause, including on row replacement.
No hands, totals or decision reasons are added to the bounded care-event history
or wish progress; only the existing transient final event carries them until
session qualification. PL-3 adds a subtype within the existing version-two
envelope, without a new table, envelope version or database migration.

PL-4's optional `social_content` stores the actually played original `parts`
(one complete one-liner/quotation/fact or distinct setup and punchline), category,
provider, identity, fingerprint, source/source URL, permalink and applicable
author/author URL and license name/URL. These are immutable source facts from
preparation, not reconstructed from intro/author bubbles or a generated summary.
Only actual full-sequence completion may attach them to an existing qualifying
wish or ordinary social cause. Older causes omit this field without invented
text. Cause trimming/removal removes its content; no separate archive exists.
The 100 admission receipts per category remain body-free, and the care-event
window and active wish progress do not gain content bodies.

The codec accepts and validates obsolete optional per-cause `level` metadata,
but ignores it; new saves omit it. Available old receipts survive within the
current cap; already discarded receipts cannot be reconstructed. Wish results,
qualified everyday positives, negative interactions and poor-care producers now
supply concrete causes. Longer-term causes retain the actual qualifying-period
summary. Old `legacy` causes remain unknown and are never reconstructed.
See the [open audit](CARE_TIME_IMPLEMENTATION_PLAN.md#documentation-audit-and-open-work-2026-10-23).

Each active Moodlet may additionally store `attribution`: `user`, `autonomous`
or `unknown`. This describes the latest qualifying cause's known origin;
episodes saved before 5B.8 default to unknown. Loading never fabricates blame.
The supported legacy section and outer wire format remain version one. Overall emotional
composition, localized labels, current wish restrictions and read-side
countdowns are derived, never serialized as a second source of truth.

### Bounded actual care evidence

The optional monotonic `next_experience_id` belongs to that same checkpoint.
It supplies deterministic identities for personal intake/petting and immediate
interaction causes, so preparing and directly executing identical care agree.
Older saves default it to one; actual game/social/withholding receipts retain
their original semantic identities. Cause timestamp identities normalize numeric
integer/float representations across JSON save/reload.

The optional Pet-owned `care_evidence` record stores at most 128 encounters and
512 semantic experiences, plus one processing cursor for each of the six
longer-term families. Encounter identities link welcome activities in two-hour
visits. Evidence distinguishes actual fulfilled wish identities from admission
assignments, real wins from fair losses, upsetting incidents from escalation
messages and communicated boundary disregard from unexpressed preferences.
Autonomous intake and closed time do not invent personal care visits.

Each family cursor accounts real elapsed time and completed twenty-four-hour
periods once. Current and longest awake contact gaps survive checkpoints and
saves; `longest_awake_contact_gap_seconds` is an optional additive field. Older
records conservatively use their known current gap. Sleep pauses gap accumulation;
qualified periods consume handled burden. The existing relationship need-exposure
history supplies care quality, without a second need timeline. Period-duration
validation permits only tiny floating-point integration error (1e-7 seconds).

Evaluate before pruning raw facts. Keep the current period plus bounded latest
activity/round anchors for gap and comeback queries. If an unprocessed window
saturates, restart its reliable baseline rather than declaring missing evidence
positive care. Old saves start new qualification from the observed endpoint;
they receive no fictional prior periods. Active episodes keep their own bounded
causes independently of raw-evidence cleanup, using the same atomic Pet save.

## Continuous relationship and status precision

Continuous friendship uses the existing `relationship` record and elapsed axis.
Its optional `continuous_since` marks policy activation after an older save's
already elapsed catch-up. Points, accepted-contact/neglect history and historical
credit metadata are preserved, without refunds or replay. Current care and wishes
do not create instantaneous credits; old reward fields/limits remain solely for
v1 compatibility. Main status floats are saved at full precision. Normal status
advances on the shared 30-second clock; actions and saves flush pending time.

## Optional wish state

SQLite stores wish instances, targets, original goals and progress in related
tables. Its strict import reader retains the legacy `pet.wishes` v1 codec. `WishState`
is frozen and owned in `PetValues` alongside Moodlets. Persist up to three active
wishes, including multiple distinct goals per area, with stable instance IDs,
original goals and typed exact/any/exclusion targets, elapsed creation/expiry
and actual expression times.
Keep original deadlines on load, even when already expired; domain progression
will resolve expiry later. Do not infer speech from a queued/displayed status.

Game wish progress stores the original `WishGoal`/`WishObjective`, required
count, bounded round receipts and Aiko-perspective results. New shared-play
objectives count two rounds across sessions; cumulative wins count three wins
across sessions. Next-win/non-loss objectives resolve on their next qualifying
round; overall non-loss evaluates its three-round block. Saved older goals keep
their original session/retry/block semantics and progress; decoding does not
replace them with the current catalogue. Boards, decks, pending rounds and
ordinary session scores remain transient.

Creation evidence for at most four areas, the last actual expression anchor,
next stable identity and the shared `refresh_at` survive retirement/restart.
The legacy `refill_not_before` field remains readable. Runtime uses one shared
600-second rotation: retain pinned goals and replace expired unpinned goals,
then fill to three at the awake due endpoint. Fulfillment/dismissal does not
postpone it. Return/sleep closure never replays a backlog. Full needs influence
area weights but alone neither exclude nor retire a desire. Temporary inability
blocks disclosure/admission independently from original wish existence.

Pins preserve goals/progress across sleep and closure. Left pins; first right
unpins; another right dismisses. Unpinning keeps the goal until the next regular
refresh, including after an obsolete four-hour deadline. Existing saved game
goals retain their original objective/progress and expiry. Old four-hour and
twelve-minute parameters remain compatibility read bounds, not live timers.

Only actual text presentation records `expressed_at` and the shared thirty-minute
expression anchor. Status display, queued text and cancelled playback do not.
Low trust/mood restricts expression, not inner existence. All seventeen forms use
the existing German text catalogue and canonical food/game labels.

Actual fulfillment atomically retires the stable wish identity and creates its
Moodlet with a concrete original-goal cause snapshot. No current care/wish path
consumes legacy reward pots or grants an instant friendship bonus. Actual
matching intake can fulfill an ordinary food goal; recognized personal handover
now also qualifies desired/alternative food under the later approved rule.
Explicit unwanted-food handover produces food-wish-disregarded, not a positive
award, even when put down uneaten. Nutrition remains separate. Actual wished-for
petting is allowed at full needs but cannot bypass explicit refusal. Complete
matching social sequences and assigned game rounds use shared pre-outcome
priority; bounded completion receipts prevent duplicate outcomes after reload. Failed non-loss game goals create `disappointed`;
expiry/dismissal and other unsuccessful goals grant no fulfillment impression.
Pending game rounds/social playback are not replayed or completed by loading.

The optional `food_handovers` collection retains at most 32 actual-transfer
receipts, each with up to three original food-wish snapshots, recognition facts,
status and bounded accounted-wish markers. Recognition evaluates this original
context even after rotation; a goal already settled elsewhere cannot repeat.
It starts the Moodlet clock and preserves actual handover time in the cause.
World/Memory application ports confirm custody and genuine identity; decoding
itself supplies no recognition. Technical safe-on-ground recovery preserves
pending context. Actual withdrawal cancels it; consumption, completed put-down
and permanent removal release no-longer-needed processing records. Whole-Pet
checkpoints include receipts/permissions for joint consumption rollback.

Missing old sections stay empty. Present invalid sections stop import without
replacing the source or dropping valid adjacent data. A supported valid source
is backed up unchanged before SQLite initialization. Whole-Pet checkpoints
include both collections, so the existing joint consumption transaction can
restore them together with World custody and subjective object memory.

## Where progress is stored

Windows uses `%LOCALAPPDATA%/AikoDesktopPet/state.sqlite3`. Linux uses
`$XDG_DATA_HOME/AikoDesktopPet/state.sqlite3`, or
`~/.local/share/AikoDesktopPet/state.sqlite3` if that variable is unset.
No database or personal backup is distributed in Git: the first successful save
creates the database from the checked-in schema using Python's standard SQLite.

`AIKO_SAVE_PATH` selects one **file**, with OS environment precedence over the
optional project `.env`. Relative paths resolve from the project root; quotes,
home and environment expansion remain supported. No `.env` is required.

| Configured suffix | Active save | One-time legacy candidate |
| --- | --- | --- |
| `.sqlite3`, `.sqlite`, `.db` | Exact configured path | Same-stem `.json` |
| `.json` | Same-stem `.sqlite3` | Exact configured JSON path |
| Other/extensionless | Configured path plus `.sqlite3` | Exact old path |

With no override the legacy candidate is the previous `state.json`. A custom
selection never searches the default directory. `StateStore.path` and
`default_save_path()` now identify the SQLite destination; `StateStore.paths`
contains both resolved paths.

## Import, transactions and errors

A supported existing SQLite database is authoritative; neighboring JSON is
ignored, even if old or malformed. With no database, the designated source must
pass complete strict validation. Only absent optional older fields receive
neutral defaults. Unsupported formats, malformed present fields, duplicate keys
and nonfinite numbers stop startup rather than silently resetting progress.

Before import writing, an exclusive `*.aiko-save-backup` preserves exactly the
validated JSON bytes and is flushed/synced. Failure stops the import. The
original JSON is never overwritten or subsequently updated. The complete save
is built and validated in a temporary database, then published atomically
without overwriting a competing initialization. SQLite `import_provenance`
retains source format and import UTC time, without a private source-path log.
Neither import nor snapshot read advances pet time.

`infrastructure/persistence.py:StateStore` resolves paths and delegates to the
strict importer and single `sqlite/store.py:SqliteStateStore` writer. A snapshot
includes core/sleep/settings, relationship/exposure, World/subjective memory,
wishes/handovers, Moodlets/causes/care evidence, adaptive memory and social/
horoscope state. Related owners commit together; no second JSON writer remains.
The original cutover used schema version 1. Version 2 adds the nullable
`social_receipts.intro_variant` field for persistent introduction rotation.
Existing version-one databases upgrade transactionally after a consistent
pre-upgrade backup; old receipts retain their IDs, fingerprints and order. A
missing old variant uses the previous deterministic fingerprint rule when
choosing the next introduction. No raw API content is added to these receipts.
Future schema changes require a
consistent pre-update database backup and transactional migration.

Every write supplies the session's last successful `SaveRevision`. The writer
compares it inside the same transaction and returns a newer revision only after
commit/publication. A stale session cannot overwrite another writer and does
not reload its revision to retry. Failed writes leave the last complete
checkpoint and expected revision intact. Autosave remains about every 55 seconds,
with the same care/settings/World/social and orderly shutdown save points.
Failed attempts are paced independently from the last successful save time.

Locked, inaccessible, damaged, newer, foreign and incomplete databases stop
loading. No error falls back to JSON, a different path or a fresh pet. Startup
shows a storage error and exits before desktop windows; save failures are
reported through the existing warning/social-admission paths. Fix access/locks
or restore a known-good backup before restarting; no automatic repair/reset is
attempted. The original error is not converted into successful persistence.

Close every Aiko instance before manually copying/restoring a database. Copy the
SQLite save and any existing `-wal`/`-shm` sidecars together; do not replace only
one file while another instance is open. JSON files are import inputs, not
ongoing backups of current progress. Databases, sidecars and private backups
remain ignored by Git. Aiko does not upload saves.

## Time anchors and legacy compatibility

`save_state.updated_at` is UTC seconds; `lived_seconds` is the pet's elapsed
axis, including later reconstructed closed time. It is neither uptime nor proof
of observed human activity. SQLite keeps status values at full precision.
Legacy saves missing `pet.time` start at zero without inventing earlier care,
contact or neglect. Present invalid time/history stops import. Raw sensor
samples, window titles, typed keys, pending dialogue and unfinished rounds
remain outside the save.

## Relationship history

SQLite stores relationship history and exposure buckets; the import reader
accepts the legacy optional `pet.relationship` v1 record. Baseline, last qualifying contact, compatibility-only per-type eligibility
and historical reward entries, per-need critical/zero exposure and direct-action
budgets use
`pet.time.lived_seconds`, never inferred mouse activity or wall-clock age.
Exposure has minute resolution and coalesces homogeneous buckets into spans;
its default 24-hour history is bounded to 1,441 spans. Reward/event histories
are bounded by their finite action set, timing and caps. Legacy calendar
reward fields remain compatibility metadata, not a second active calculation.

New histories are part of the complete immutable checkpoint and joint rollback.
Absent legacy history preserves progress and starts tracking at first upgrade
reconstruction completion, without retroactive loss or invented contact. Once
saved, that baseline survives restart. Present unsupported or invalid records
stop import without replacing the original, just like invalid time records. Strict validation rejects future timestamps,
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
sleep duration, manual grace or observed quiet. Present corrupt/future records
stop import; sleep and learned expectation then live in their SQLite tables,
not a separate settings file. See [sleep rules](SLEEP_SYSTEM.md).

## Real time, closed sessions and standby

> Stages 1–4 of the [implementation plan](CARE_TIME_IMPLEMENTATION_PLAN.md)
> provide real time, need/mood balance, friendship and adaptive sleep with finite
> stock. See the maintained [sleep guide](SLEEP_SYSTEM.md) for current priorities.

Reading SQLite or importing supported JSON only decodes data. `PetSessionRestorer` subsequently calculates
closed time from `pet.updated_at` to the current clock, without truncating the
absence. `pet.lifecycle.TimePlan` streams chronological steps rather than
allocating a list proportional to the gap. Missing saves start fresh; corrupt
saves stop loading without generating catch-up; a backwards clock produces zero elapsed time and rebases
the next anchor. The obsolete `simulation.maximum_catchup_seconds` setting has
been removed. Stage 2 applies the [need/mood rates](FUN_MOOD_SYSTEM.md) through
the same pure domain path. Existing saved mood is preserved on load and
approaches its new target over elapsed time; no balance migration resets it.

`StateStore.load_session()` reads state, settings and adaptive memory together
into one `LoadedPetData` snapshot. The old partial `load()` and `load_memory()`
wrappers have been retired; loading this snapshot never advances time itself.

Runtime progression now carries one plan-owned elapsed endpoint through the
pet and World paths. Calendar timestamps do not redefine supplied uptime
durations. Sleep, relationship/exposure, Moodlet recovery/long-term evidence
and wish expiry use that same interval. Finalization checks consistency rather
than rebasing only `lived_seconds`. This fixes fractional-tick save rejection
without loosening strict codecs, changing schema or resetting old saves.


During this calculation there is no observed workload, inferred user input,
personal contact or fabricated rhythm learning. Needs, digestion, existing
Moodlets and continuous friendship still progress. Existing emotional evidence
can contribute positive or negative elapsed relationship flow; closure does
not invent a human interaction. Qualified finite-stock intake may still fulfill
a pre-existing food wish through its existing consumption owner. No contact
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

Pet and World commit together in one SQLite snapshot transaction. Supported
legacy saves without `world` start with an empty World. Present unknown
definitions, duplicate IDs, invalid geometry/revisions or unsupported versions
stop import without replacing the source or dropping its World section.

Only nonterminal portions are saved. Cursor-held, falling, bouncing and unconsumed pet-held
portions normalize to reachable resting ground positions; pet-held recovery uses
Aiko's position. IDs and the next-ID counter prevent accidental identity reuse.
Consumed/removed instances, live capture, animations, pending user actions and
interaction playback is not resumed. Existing application reconstruction uses
only identified accessible saved stock during closed time, without UI playback. A completed meal and removal of its portion share
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

Subjective memory is captured with Pet/World and committed in the same SQLite
transaction; the legacy `object_memory` section remains an import format. Consumption resolves its remembered target before
that save; an ambiguous consumed-find witness remains unavailable until further
evidence resolves its possible former places. It cannot be reused as supply.
Confirmed own
placement is recorded at detach; interrupted placement is distinct from keeping
a supply for later. Held/falling recovery never invents observed ground positions.

Restore does not look up a remembered identity or location in current objects.
Unseen relocation/removal can therefore leave outdated knowledge until fresh
observation or deliberate learned-place orientation and search. Actual observations and sensory progress
start empty; restored knowledge alone cannot claim current visibility.

Older saves without memory start with empty knowledge. A present malformed or
unsupported memory section stops import without replacing the source or
discarding adjacent Pet/World data. A missing or invalid paired World also
stops import when subjective records are present; they never attach to reused
IDs in a fresh World.
Version-one records convert to subjective history; their old object labels are
never recognition evidence. Current bindings, observations and search budgets
are not serialized. Runtime checkpoints retain exact motion, while durable
World v1 writes only valid ground targets. Geometry is synchronized before saves,
including an immediate scale toggle. See the
[current custody and persistence contract](WORLD_OBJECT_CONTRACTS.md#custody-physics-consumption-and-persistence).
