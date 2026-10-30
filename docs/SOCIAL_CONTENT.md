# Conversations, API entertainment and local horoscope books

The [social expansion plan](SOCIAL_EXPANSION_PLAN.md) records the zero-cost
boundaries and shared reading-time policy. The rejected AstroWay prototype is
replaced by the [local horoscope book](horoscope/LOCAL_HOROSCOPE_IMPLEMENTATION_PLAN.md).
Its [old behavior](horoscope/rejected-api-prototype.md) is historical only.
Tarot remains planned. Aiko reads an actual placed/held book and stays herself.

The **Unterhalten** toolbar button opens five choices: **Plaudern**,
**Sprüche**, **Witz erzählen**, **Kurioser Fakt** and **Tageshoroskop**. Plaudern
keeps the existing authored, context-sensitive conversations. Sprüche, Witze
and Fakten use API content exclusively; Tageshoroskop places a local book.

Enable **Onlinequellen für Sprüche, Zitate, Witze und Fakten verwenden** in
settings to use the API categories. It defaults to off, including when loading
older saves without the option. With online sources off, Plaudern and the local
book remain available; the three API choices show a settings hint. The book
requires a directly selected zodiac sign and permits only one live instance.

## Providers and preparation

| Selection | Provider | Success fields used |
| --- | --- | --- |
| Sprüche: Einzeiler | [JokeAPI](https://jokeapi.dev/), German `type=single`, Safe Mode and excluded flags | `joke`, numeric `id`, `lang`, `safe`, `flags` |
| Sprüche: Zitate | [Zitat-Service](https://api.zitat-service.de/), public `/v1/quote?language=de` | `quote`, `language`, stable `link`, `authorName`, optional `authorLink`, `source`, `sourceLink` |
| Witz erzählen | JokeAPI with `type=twopart` and the same language/filter settings | `setup`, `delivery` and the same metadata |
| Kurioser Fakt | [Random Useless Facts](https://uselessfacts.jsph.pl/), v2 random endpoint with `language=de` | `text`, string `id`, `source`, `source_url`, `language`, `permalink` |

A Sprüche item is complete and at most **125 characters**, including spaces and
punctuation after whitespace normalization. Its introduction and quotation author
are separate bubbles. Long sayings are rejected, never split, shortened or
rewritten. Format checks inspect original structure before normalizing spaces:
reject multi-paragraph text, multi-turn dialogue, explicitly staged setup/delivery
and multi-line jokes. Multiple sentences or one colon alone are not rejections.
These deterministic checks are format checks, not a general semantic classifier;
provider `type=single` alone is insufficient. Dialect is not a new exclusion rule.

Quotations retain source words (including Sie), author/unknown status, entry link,
original source and any author link. A separate `Von {author}.` bubble ends the
text sequence and receives the final second. Credits identify Zitat-Service's
community collection, its [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
license and any normalized whitespace; author, original source and entry links
remain separate. These metadata do not enter subjective pet knowledge.

Two Parts keeps setup and delivery distinct, with an 800 ms pause before the
delivery, after the final setup bubble's complete reading time.
Each of these three buffered categories has three short German introductions
in the existing text resource.
The first introduction uses a stable provider-text fingerprint. Later offers
cycle through the three variants using the last admitted variant in the same
category, including after restart. Warming, selection and cancellation do not
advance the rotation. Old receipts without an explicit variant use the previous
fingerprint rule to recover their last introduction. The fingerprint still
sometimes adds a restrained happy/idea emote after the full content. No final emote
precedes the punchline or takes a text slot. Framing and the holding line are
presentation copy, not substitute entertainment or a personal-memory record.

Sayings, jokes and facts are prepared into the existing `Reaction`/`Cue` model, with at most
125 characters per text beat and five text beats including the introduction.
Two-part jokes and facts split at sentence or word boundaries without discarding
words; Sprüche content always occupies exactly one content bubble.
Provider-truncated, wrong-language, unsafe-flagged, malformed and oversized
items are rejected. Plain text stays plain text, including literal HTML
entities that can be part of a joke. Provider facts are entertainment inputs;
a valid response is not independent verification of their claims.

The Credits view retains the most recently accepted item's source and API-entry links.
Links open only when clicked. Source metadata remains attached to the prepared
item; it is not added to Aiko's personal experiences or World knowledge.

## Local daily horoscope book

The local book works without online opt-in, requests, keys or provider footers.
Direct sign selection stays in settings. Actual Sun/Moon/phase values come from
Astronomy Engine 2.1.19 (MIT); authored German entries come from the packaged
96-reading catalogue. Optional passage comments use the existing friendship and
emotional context. No translation/generation model is added.

Select a book under Unterhalten and place it by drag/drop. Aiko notices,
identifies, picks it up, opens and reads it using the existing holding pose.
The first reading freezes that local day's sign/text/cues and admits normal
conversation care once. Interruptions resume at the saved cursor.
After the first full reading's actual put-down, the book remains for a fixed
hour. Handing it back restarts the same frozen text without extra care or a
renewed deadline. At the hour it dissipates in any custody. Next day a new book
contains the new entry after old stock retires. Only one live book is allowed.
An incomplete previous-day book is retired at the day boundary. Restart
preserves progress and the absolute expiry.
Details: [owners, data and lifecycle](horoscope/MODULE_AND_CATALOGUE_CONTRACTS.md).

## Bubble reading time

Spruch, Witz, Kurioser Fakt and Plaudern share one reading policy for each
formatted, segmented text bubble: **1,500 ms + 65 ms per displayed character**,
including spaces and punctuation, clamped to **4,000–10,000 ms**. The last text
of the complete interaction receives **1,000 ms extra**, still capped at
10,000 ms, even when an emote follows. This is visible text time before hiding
or replacement, rather than a blank pause. A later credit/exit text would be
the last text instead.

The `Reaction` applies this policy to `talk` sequences before playback, using
the `conversation_*` values in `data/balance.json`. Other feedback retains its
existing timing. `ReactionPlayer` and `SpeechPresenter` receive the same
prepared duration; authored emotes/thinking pauses retain their own durations.
Two-part API jokes add one 800 ms pause between the complete setup and delivery.
Existing story reading clicks can advance sooner, skipping intervening pauses
and emotes, without extra care or wish effects.

Deterministic tests cover clamp boundaries, the final-text allowance with
trailing emotes/credits, segmented jokes, stale callbacks and completion.
Native Windows/Tk tests check mapped bubbles through the full deadlines with
a controlled clock, independently of any user save. These automated checks do
not establish the owner's subjective reading comfort.

The implemented [settings/Credits design](UI_VN_DESIGN.md#approved-settings-and-separate-credits)
places provider information and these per-item links in a dedicated Credits view.
It reads accepted-item metadata without a parallel attribution history or new
network requests.

## Warm buffers and waiting

There are three independent in-memory buffers, each targeting two ready items:
Sprüche, Two Parts and facts. Sprüche has two slots total across both providers;
it is not a two-slot buffer per source. When both are ready, prefer the source
other than the last admitted saying (initial preference: JokeAPI). If only one
is ready, use it immediately. Warming prefers the source with less ready stock
within the same bounded buffer; no fetch is made merely to force a ratio. A ready slot contains a validated complete playback
sequence. One daemon worker fetches and prepares one item at a time; no bulk
request, parallel per-category workers or owner-thread HTTP work is used.

Warming starts after opt-in, including startup with a saved opt-in. A ready item
can start immediately after normal foreground admission; consuming it triggers
individual refill. An empty selected category takes priority after the current
fetch and joins matching in-flight work. Aiko says **Ich muss kurz überlegen**
once and waits for the first prepared item, rather than waiting for both slots.
Waiting suppresses incidental speech and autonomous activity but allows another
deliberate care action to cancel the selection. Normal conversation playback
keeps its existing protection, including blank pauses and reading clicks.

Sayings/jokes/facts have an eight-second network timeout. All their responses
are bounded to 16 KiB. Local horoscope books do not use the worker or network.
There is no separate four-second display deadline. Errors end the waiting
attempt with a brief menu message; choosing the category retries. Failures never
select local authored entertainment or silently switch to Plaudern. Other ready
API items remain usable if the network subsequently becomes unavailable.

Ready and offered items cannot duplicate one another. The last 100 admitted
contents per category also participate in repetition checking, including after
restart. Namespaced provider IDs or normalized text fingerprints match across
all three categories, including text split differently into setup/delivery.
Only actual playback admission records a receipt; preparation, selection and
cancellation do not. One hundred newer admissions in its category release an older
receipt, unless another category/buffer/offer still excludes it. Both Sprüche
providers share the same 100-content history. Every rejected, duplicate or failed
attempt consumes the provider budget. A refill cycle stops after three rejected
or duplicate attempts per category/source, without imposing a provider pause.
Another deliberate selection can continue searching; repeated clicks while the
same selection is waiting do not reset that cycle. Transient HTTP/network failures
pause the provider for at least one minute; access changes stop it for a day.
No authored fallback is used.

Before JokeAPI content requests, one separately budgeted `/info` request supplies
the German ID bounds, cached for an hour in the session. The scheduler subtracts
all admitted IDs, buffered/offered IDs and active category-specific exclusions,
then chooses an allowed contiguous range for `idRange`. Counts are not hardcoded
and no bulk joke download is used. Preparation still checks fingerprints, safety,
language and presentation limits. A recognized unsuitable item's ID and reason,
or a range returning HTTP 400/code 106 (no matching joke), is saved as a bounded
exclusion for 24 hours with a filter revision. Malformed responses without a
trusted identity do not blacklist arbitrary IDs. Metadata and content share one
worker, pacing, quotas and reservation-before-dispatch persistence.

An exhausted candidate pool reports that no matching new jokes remain; the
100-content history is never automatically cleared or relaxed. Reaching the
three-attempt search bound reports a separate retry-selection message. Empty
ranges and unsuitable content never block another JokeAPI category. Facts and
quotations retain their existing random endpoints and final repetition checks.

Automatically hiding the menu or browsing another selection view preserves the
requested content. Explicitly leaving the social selection with Zurück, Escape
or an outside click cancels pending playback. Focus loss only hides the view
and preserves pending content, including an already queued answer start.
Accepted replacement actions, disabling sources and shutdown also invalidate
it. Stale worker results never
trigger a conversation, and cancelling a pending request does not stop an
already admitted story.
Ordinary selection cancellation may leave background warming enabled. Opt-out
clears the online buffers; shutdown closes the worker without waiting on a
network call or allowing it to touch destroyed Tk widgets.

## Free endpoints and request discipline

Only the reviewed public URLs are used, with no keys, account, billing path,
paid fallback or new dependency. HTTP redirects are refused; changed access
requirements remain unavailable. Provider documentation/terms were rechecked on
2026-10-23: JokeAPI documents 120 requests/minute per client; Zitat-Service and
Random Useless Facts have no numeric quota in the reviewed public documentation.
Unknown limits are not treated as unlimited. The local book makes no HTTP calls.

These are **Aiko client caps**, not claims about undocumented provider quotas:

| Provider | Minimum request spacing | Rolling hour | Rolling 24 hours |
| --- | --- | --- | --- |
| JokeAPI, shared by Einzeiler and Witz | 5 seconds | 60 | 300 |
| Zitat-Service | 10 seconds | 20 | 60 |
| Random Useless Facts | 10 seconds | 20 | 60 |

HTTP 429 respects Retry-After (seconds or HTTP date) and JokeAPI's HTTP-date
RateLimit-Reset; without usable metadata it pauses for fifteen minutes. A valid
last response with remaining budget zero remains playable while its reset blocks
further calls. Even a disabled/stale response can extend a provider-wide pause.
A long budget wait returns a retry-later status instead of holding a conversation
for hours. Normal short pacing is handled by the existing polling scheduler.

Each reservation is atomically saved **before HTTP dispatch**, through the
existing persistence owner without advancing pet time. A failed save prevents
network dispatch. Restart and opt-out do not reset caps or provider pauses.
Bounded bookkeeping expires after its rolling window; no permanent request log
is introduced. The local reading has independent bounded persistence. Shared-IP provider rejection remains
possible even when this client's own cap is not exhausted.

## Care and persistence

Every accepted variant uses the existing `talk` care transition: **+26 social,
-1 energy, no direct fun gain**, with normal need clamping. Accepted personal
contact feeds the continuous friendship policy; there is no instant care or
wish friendship bonus. Changing category does not create another reward. See
[friendship rules](FRIENDSHIP_SYSTEM.md) and [need effects](FUN_MOOD_SYSTEM.md).

Menu opening, warming, the holding line and failed/cancelled preparation grant
no care or qualified personal contact. When actual content playback is accepted,
care commits once. Reading clicks, the punchline and extra framing beats grant
no extra care; later interruption does not undo accepted care or its repeat
receipt. A matching social wish still requires the complete sequence and may
then create its existing fulfillment Moodlet.

PL-4 preserves original API words separately from the prepared reaction and
passes them through that same full-sequence completion. A qualifying wish or
ordinary social-gap cause retains one complete saying/one-line joke, quotation
with separate author, two distinct setup/punchline parts, or complete fact before
bubble segmentation. Provider identity, fingerprint and supplied source/author/
license metadata remain available across restarts without refetching. Intro
rotation, pauses, emotes and authored framing are not remembered source words.
Preparation, interrupted playback and unqualified completion retain no such
cause. Each cause keeps its own content within the existing one/two/three limit;
cause removal also removes its content. Plain chat and horoscope keep their
existing care/completion behavior. See [PL-4 delivery](CARE_TIME_IMPLEMENTATION_PLAN.md#pl-4-delivery-original-social-content-evidence).

PL-6B's requested Plaudern reflects those same causes through the single Mind/
catalogue path. A personal introduction precedes a literal retained reference
and Aiko's feeling about sharing it. Quotations add their supplied author;
two-part jokes keep setup and punchline separate. Long references use a visibly
ellipsized original prefix inside quotation marks, with each reference occupying
its own 125-character bubble. The complete original and metadata remain stored
unchanged. There is no semantic paraphraser, generated source title or provider
refetch. Aiko remains the teller and does not claim the user laughed or replied.
Older category-only causes reflect the telling without inventing lost words.
Wish-specific motives require their original wish; friendship and quiet/mixed
feelings color the full sequence. The body-free repetition history is unchanged.
See [PL-6B delivery](CARE_TIME_IMPLEMENTATION_PLAN.md#pl-6b-delivery-social-negative-and-long-term-story-families).

PL-6C keeps deliberately requested Plaudern separate from unsolicited short
comments. A calendar date or quiet desktop alone causes no speech; a genuine
need, emotional state or observed work/rest can supply a short comment. A cooled
social/affection reminder permits a different real topic or silence. The random
idle/calendar pool and automatic promotion into a multi-bubble `talk` story are
removed. Wishes keep their existing relationship-qualified disclosure and
display/completion path; item/search/handover reactions and deliberately started
social playback remain unchanged. This introduces no additional history or save
fields. See [PL-6C delivery](CARE_TIME_IMPLEMENTATION_PLAN.md#pl-6c-delivery-grounded-spontaneous-comments-and-generic-removal).

`settings.online_social` is an optional Boolean within the existing version-one
legacy JSON save. Ready sayings/joke/fact buffers and pending tokens are never
saved. The `social_history` transfer section now uses version six: up to 100
admission receipts per category (300 total), plus bounded expiring request timestamps
and provider pauses, and up to 512 expiring joke exclusions. SQLite schema version
four adds their table through the existing backed-up migration path. Existing
provider pauses retain their expiry because older records contain no cause.
Local horoscope days and frozen cues are stored separately
from online request history in the same atomic session checkpoint.
Receipt fields are category, namespaced provider identity, SHA-256 fingerprint
of normalized provider words and nullable `intro_variant` (0, 1 or 2). Quote identities use
`zitat-service:<entry-id>` in the existing `single` category. These three
receipt categories do not store source words, URLs, buffers or pending tokens.
Versions one through five remain readable with empty candidate exclusions.
Migration preserves old horoscope
admission/completion markers while discarding provider prose, counters and retired
provider request metadata. No history means empty defaults. Opt-out clears online
buffers and retains admission/request bookkeeping; the local book stays available.

The session restorer carries this value to the existing content coordinator
before online warming starts. Actual admission saves care and its receipt
together once through DesktopPersistence/StateStore; full-sequence wish
completion remains a separate later event. Missing legacy history starts empty.
Present invalid legacy history stops the complete strict import without
replacing the source or dropping adjacent pet/World data. Live care and receipts
commit together in the revision-guarded SQLite store. Missing older optional
fields receive neutral defaults. No translation model or second time simulator
is added. See [storage and import](DATA_AND_SAVES.md).

## Owners and verification

- `application/social_content.py` validates source data and prepares immutable
  source-aware reactions with separate original-content evidence.
- `pet/social_content_evidence.py` owns the frozen original parts/attribution and
  shared category/provider vocabulary; existing application imports re-export
  those same types. The existing completion path and Pet cause producers retain
  qualifying evidence; infrastructure serializes it in the existing cause rows.
- `application/social_coordinator.py` owns the buffers, offers, selection and
  repetition history through the `SocialContentWorker` port.
- `application/social_fetch.py` owns data-only requests/results and that worker
  port. `application/social_candidates.py` owns pure ID-range subtraction and
  bounded, category-specific exclusion records.
- `application/social_history.py` supplies immutable bounded admission receipts;
  `infrastructure/social_history_codec.py` validates the compatible version-six
  section, with strict exclusion validation in `social_candidate_codec.py`,
  independently of pet experiences.
- `application/horoscope_coordinator.py` independently freezes the local daily
  book entry, sign and Aiko cues, owns resumable progress and one-time admission,
  and preserves the original replay deadline. `application/horoscope.py` assembles
  the authored sequence; the models and codec bound the saved values.
  `desktop/horoscope_playback.py` uses the existing player while World owns the
  physical book. There is no provider footer.
- `application/social_requests.py` supplies finite provider budgets and immutable
  expiring metadata; `infrastructure/social_request_codec.py` validates it in the
  existing save boundary.
- `infrastructure/social_api.py` owns bounded HTTP reads and the data-only worker.
- `desktop/social_runtime.py` coordinates holding and deferred admission through
  existing World, care and presentation callbacks.
- `desktop/care_runtime.py` owns deliberate care dispatch, care presentation and
  Social-to-World admission wiring. `gui.py` composes that owner and keeps its
  existing public care entry point.
- `ui/windows/social_menu.py` presents choices and readiness/status; `HoverUi`
  owns stacking, hover, topmost, dismissal and cleanup. The existing Credits view
  projects accepted provider, author, source, entry and license metadata.

Deterministic provider-shaped fixtures are tests only. Focused tests cover
preparation, care, worker/coordinator lifecycle and real Tk selection/playback
with temporary saves. Separate live checks verified both providers, all three
playback variants and 2/2/2 buffer readiness. The
[delivery plan](SOCIAL_CONTENT_IMPLEMENTATION_PLAN.md#delivery-record) records
per-commit checks and final validation. Physical desktop visual acceptance is
distinct from automated native Tk assertions; no maintainer sign-off is implied.

See [architecture](ARCHITECTURE.md), [window behavior](UI_WINDOW_CONTRACT.md) and
[data and saves](DATA_AND_SAVES.md).


## VN menu and Credits (5C)

The four choices now occupy the existing main menu's right interaction column,
with Zurück, scrolling and current preparation/error/opt-out feedback. Closing
still cancels only pending content. The provider and last accepted item's
original-source/API-entry links moved to the settings window's separate Credits
page. Its immutable projection reads existing accepted metadata; it does not
fetch, reserve, replay, persist or maintain another source history. The original
source and API provider remain distinct, and missing URLs disable only their
corresponding links. Existing shared-care and playback completion rules remain.

## Slice 8 local verification, 2026-10-21

The playful framing and persisted ten-content window pass 103 selected local
headless tests in 0.711 seconds, with no individual case over 0.206 seconds.
Fixtures cover complete provider text, category framing, whole-sequence wishes,
reservation/cancellation, cross-category ID/text duplicates, bounded retries,
per-category eviction, actual atomic saves, legacy/default recovery and restart.
Native Tk/Toplevel construction was blocked, HTTP responses were faked, and
temporary save files were isolated from the normal save. Scoped Ruff, strict
Mypy and Pyright plus dependency/UI architecture checks pass. No native window,
mouse control, live API request, CI or full-suite run was used for slice 8.
The final integrated suite and OOP review remain slice 9.

## Sprüche integration verification, 2026-10-23

The complete Windows/Python 3.11.9 suite passes **1,756 tests** in 297.568 seconds.
After the last format/link edge refinements, the **97 focused social tests** pass
again, including native Tk selection, author delivery and Credits assertions.
Whole-repository Ruff, strict Mypy (260 source files) and Pyright pass. Temporary
saves cover restart, pre-dispatch quota persistence, failed writes and old-history
compatibility. Separate bounded live checks validated short German provider data;
normal tests do not depend on live endpoints. Horoscope and tarot remain planned.

## Historical rejected API delivery verification (2026-10-23)

The complete Windows/Python 3.11.9 suite passes **1,776 tests**, including twenty
new horoscope tests (four with native Tk and isolated saves). Ruff, strict Mypy
(264 source files), Pyright and the acyclic-import gate pass. One separate live
Widder request fits ten complete bubbles. Native visual checks cover the sign
selector and visible, unclipped footer. See the [expansion plan delivery
record](SOCIAL_EXPANSION_PLAN.md#horoscope-verification) for scope and evidence.
Tarot remains planned.
