# Local horoscope: module, object and catalogue contracts

Implementation contract, 2026-10-25. The user authorized the local replacement.
The rejected API implementation is removed. Verified local commits are authorized;
push and merge remain outside this work.
The latest book lifecycle below supersedes the earlier single-use proposal.

## Ownership

| Owner | Responsibility |
| --- | --- |
| `pet/horoscope.py` | Immutable sky/profile/catalogue values; zodiac ordering, relative solar houses, lunar phase quarters, eligibility and deterministic selection. |
| `infrastructure/astronomy.py` | Astronomy Engine 2.1.19 adapter; actual geocentric tropical Sun/Moon longitudes and lunar phase. No text, HTTP, credentials or pet mutation. |
| `infrastructure/horoscope_catalogue.py` | Strict explicit-file catalogue loading and coverage report. |
| `application/horoscope_models.py` | Frozen prepared reading, per-day progress and bounded two-day history. Local date uses a fixed local-noon reference converted to UTC. |
| `application/horoscope.py` | Assemble opening, complete book passages, optional passage-specific comment and closing; apply shared conversation timing once. |
| `application/horoscope_coordinator.py` | Admit once, freeze sign/texts/cues, persist cursor, replay original contents and manage the first-put-down deadline. No Tk or World mutation; effects use ports. |
| `desktop/care_runtime.py` | Compose the local owners with actual sign, friendship/emotional context, normal care router, persistence and physical READ eligibility. |
| `desktop/horoscope_playback.py` | Cancellable half-open/read/close presentation through ReactionPlayer. Never changes nutrition or physically moves an object. |
| Existing `ObjectInteractionCoordinator` | Own pickup, held READ, interruption, legal put-down, stale episode guards and use eligibility. |
| Existing `WorldState` | Own physical instances/custody and immutable expiry deadlines; retire expired books in any custody. |
| Existing `ObjectAwareness` / `ObjectIntentions` | Own learned identity/places and normal investigation/retrieval. Eligibility is supplied by application, without a second intention loop. |
| Existing item overlay and WorldView | Render approved book states and existing holding pose. The last second fades the separate World item window. |

PetState remains the mutable pet aggregate. Object memory remains subjective.
Book expiry does not directly erase Aiko's memories; ordinary observation handles
absence. Local reading history is independent of online social request history.

## Public values and functions

Domain values are `SkySnapshot`, `HoroscopeProfile`, `BookPassage`,
`EntryEligibility`, `HoroscopeEntry`, `HoroscopeCatalogue`, `HoroscopeTheme`,
`DevelopmentDirection`. `normalized_angle`, `sign_at`, `relative_house`,
`phase_direction`, `build_profile`, `entry_matches` and `select_entry` are pure.
`select_entry` sorts eligible IDs and uses SHA-256 over the explicit date/sign key.
It never interpolates a new sign into an ineligible text or uses process hash().

Moon's relative solar house selects one of twelve themes, in order:
`self`, `resources`, `exchange`, `home`, `play`, `routine`, `encounter`, `change`,
`perspective`, `goals`, `friendship`, `rest`.
Phase quarters select `begin` [0,90), `develop` [90,180), `reflect` [180,270),
`conclude` [270,360). Sun context is calculated and saved; optional entry
eligibility can restrict Sun/Moon signs/houses. The current catalogue does not
claim narrower solar conditions: its eligibility objects are empty.
These are entertainment selection conventions, not scientific predictions.

Application values are `DailyReadingRequest`, `PreparedBookReading`,
`HoroscopeDay`, `HoroscopeHistory` and the `SkyCalculator` protocol.
`prepare_book_reading` assembles a complete immutable sequence; coordinator
methods are `availability`, `start`, `advance`, `pause`, `put_down`, `today`,
`for_book`, `obsolete_books`, plus read-only `history` and callback `generation`.

## JSON catalogue boundaries

| Resource | Contents |
| --- | --- |
| `data/horoscope/de/index.json` | index_version 1, catalogue_version 1, language de, catalogue_id, revision and explicit twelve-file list. |
| Twelve theme JSONs in that directory | catalogue_version/language/entries; 8 complete readings per theme = 4 directions x 2 variants. |
| Each entry | id, revision, theme, direction, variant a/b, reviewed allowed_signs, eligibility, ordered passages. |
| Each passage | id, complete text <=125 characters, optional semantic comment_key. At most one anchor per reading. |
| `data/dialogues/de/events/horoscope.json` | Normal v3 DialogueBook source: opening, closing, 24 passage comment keys x four friendship groups. Registered by the existing dialogue index and line_order. |
| `assets/items/items.json` | Item catalogue v2 readables declaration: ID, localized label_key, state_manifest. No copied pivots, reading state or rewards. |
| Existing book manifest | Four approved states, native 1x/2x images, pivots and icons. No physical custody, prose or daily progress. |
| Existing text catalogue | Menu, settings, zodiac labels and object grammar. No horoscope prose or callback logic. |

The 96-entry editorial source is `docs/horoscope/pilot-book-entries.de.json`;
Aiko's separately reviewed source is `aiko-book-dialogues.de.json`. Runtime data
is packaged under `aiko_pet/data/`, never read from docs. Both content passes
completed sequentially. The second pass corrected two book sentences and raised
those entry revisions. Editorial review by agents is not user approval of every
individual text.

Each entry currently allows all twelve signs because its relative-house reading
is independently applicable to each. There are no named-sign substitutions.
Validate IDs, exact schemas, all passages, each sign/theme/direction combination,
selection restrictions, comment keys and four friendship groups. A missing
optional comment is omitted; no unrelated generic comment replaces it.

Aiko always stays Aiko. Friendship groups are acquaintance (1-2), familiar
(3-5), friend (6-8), close (9-10). Only her own comments change. Comment conditions
also require a suitable emotional state; low energy independently omits comments.
A frozen resumed/replayed reading keeps its originally selected full sequence.

## Physical lifetime and replay

One physical book contains one day's entry. The player places it by drag/drop;
Aiko notices, identifies, picks up and holds it through the existing owners.
No hat gate or floating prop is introduced.

Visual order: `closed_world -> carry_closed -> half_open -> open_reading ->
half_open -> carry_closed -> closed_world`. Existing pickup/holding/put-down
character poses are reused; no new character frames or page-turn animation.

After the **first completed reading's actual put-down**, persist
`first_put_down_at` with the matching World instance's `expires_at = timestamp
+ 3600 seconds` in the same session transaction. There is no `used_up` field:
that earlier proposal is superseded. A replay or later put-down cannot renew
the deadline. A partially read first reading can resume at its saved cursor and
has not started the completed-book replay hour.

During the hour the user can hand that same book to Aiko again. It restarts the
same frozen reading from cue zero, without another daily care credit. Aiko does
not autonomously loop completed readings. At the absolute deadline World removes
the book even if the user/Aiko currently holds it; invalidate reading/episode
callbacks and release cursor capture safely. Restart never renews a saved expiry.
A completed held book recovered onto the taskbar starts its first put-down hour
when recovery performs that placement. World allows only one live horoscope
book across all custody states, including a newly selected cursor object.
Across midnight an old completed book keeps its old entry until expiry and
blocks new stock. An incomplete previous-day book is retired on the next World
frame. A newly placed next-day book then receives the new day's entry.

## Persistence and retirement

SQLite schema 3 adds typed `local_horoscope_days` and ordered
`local_horoscope_cues`, extends World objects with expiry and memory kind with
book. Care admission and the frozen local reading share the existing atomic
session save. Failed admission saves undo that day's pet care change.
Session read/write validates physical book bindings and matching expiry against
the paired World snapshot; already retired historical references remain valid.
`HoroscopeHistory` keeps at most the current day and an unexpired previous book.

JSON/SQL migration discards rejected API prose and request counters; it preserves
an admitted/completed day marker to prevent another same-day care credit.
Legacy request metadata for the retired provider is discarded. The old SQL DDL
remains only as migration history so valid v1/v2 saves can be read and upgraded.
No AstroWay client, provider mode, footer, API key or HTTP fallback remains.
Online opt-out controls only online Sprueche/Witze/Fakten, not local books.

## Verification

Meaningful coverage includes astronomy/phase boundaries, deterministic complete
coverage, text budgets/timing, cancellation/stale callbacks, partial resume,
same-entry replay, non-renewing expiry, midnight/new-day behavior, SQL migration
and restart, physical pickup/read/put-down without consumption, offline menu
placement and native 1x/2x held-book rendering. Preserve food/drink and unrelated
social behavior. Native rendering and the whole-suite result are reported in the
implementation delivery; they are not inferred from pure model tests.

## Drag-and-drop correction and visual registration (2026-10-25)

The book choice now starts on ButtonPress-1 and closes the selector before
shared cursor capture, exactly like FoodMenu. Selecting stock is independent
of Aiko's talk/care admission. Release, falling/bouncing, resting pixel pickup,
relocation, offer recognition and handover all use the existing World owners.
No book-specific drag loop or separate inventory is introduced.

`world_registration.zoom = 2` makes the closed book clearly visible at both
character scales. WorldView prefers the existing native 2x source before any
integer zoom. Cursor and ground use the same image, pivot and physical instance.
The closed book's authored bottom support pivot grounds its actual cover on the
taskbar; transparent padding is not treated as the support point. Food geometry
retains its existing convention. `holding_readable` projects the live READ phase
through the existing animation composition, keeping a stable final pickup pose
instead of restarting pickup or clearing the held graphic. The middle held
position keeps the owner's latest +12px 1x vertical attachment adjustment;
character frames and source book PNGs are unchanged.

Real Tk regressions cover press/drag ownership, release/drop/settling, opaque
resting-item pickup, same-instance relocation/cancel, unknown direct handover,
ground pickup/reading/put-down, runtime pose selection and same-story replay
without renewed care or expiry. The recovery callback is cancelled at teardown.
