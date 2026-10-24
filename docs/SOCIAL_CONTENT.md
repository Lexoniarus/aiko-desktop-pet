# Conversations and API entertainment

The [selected social expansion plan](SOCIAL_EXPANSION_PLAN.md) records the
implemented Sprüche/quotation slice, zero-cost/keyless boundaries and the shared
reading-time policy. Daily horoscope now implements the selected role performance,
direct sign choice and resumable daily reading. Tarot remains planned.
The later [hat-gift and VN presentation direction](SOCIAL_EXPANSION_PLAN.md#planned-horoscope-gift-and-vn-presentation)
is documented as future work: a permanent gifted hat unlocks the horoscope and
is worn only during its reading, with matching hat perspectives and a separate
floating book. The current runtime described here has no hat ownership gate or
hat/book presentation; the concept does not yet replace its content provider.

The **Unterhalten** toolbar button opens five choices: **Plaudern**,
**Sprüche**, **Witz erzählen**, **Kurioser Fakt** and **Tageshoroskop**. Plaudern
keeps the existing authored, context-sensitive conversations. The four online categories
use API content exclusively.

Enable **Onlinequellen für Sprüche, Zitate, Witze, Fakten und Tageshoroskop
verwenden** in settings to use the API categories. It defaults to off, including when loading older saves without
the option. With online sources off, Plaudern remains available and the four
API choices show disabled controls with a settings hint.

## Providers and preparation

| Selection | Provider | Success fields used |
| --- | --- | --- |
| Sprüche: Einzeiler | [JokeAPI](https://jokeapi.dev/), German `type=single`, Safe Mode and excluded flags | `joke`, numeric `id`, `lang`, `safe`, `flags` |
| Sprüche: Zitate | [Zitat-Service](https://api.zitat-service.de/), public `/v1/quote?language=de` | `quote`, `language`, stable `link`, `authorName`, optional `authorLink`, `source`, `sourceLink` |
| Witz erzählen | JokeAPI with `type=twopart` and the same language/filter settings | `setup`, `delivery` and the same metadata |
| Tageshoroskop | [AstroWay public daily endpoint](https://api.astroway.info/en/docs/api/operations/publichoroscopedaily/), explicit `sign`, `lang=de`, local `date` | `ok`, `sign`, `date`, `period`, `language`, complete `sections.overview`/`advice`, `disclaimer`, `_footer`; reject fallback metadata/STALE cache |
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
A stable provider-text fingerprint varies the prepared introduction, sometimes
adding a restrained happy/idea emote after the full content. No final emote
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

## Daily horoscope

Choose **Sternzeichen fürs Tageshoroskop** in behaviour settings: twelve direct
signs plus **Nicht ausgewählt** (default). No birth date is collected or sent.
The horoscope button stays disabled without a sign and shows a settings hint.
Sign selection/menu opening never requests a horoscope.

Selecting the horoscope loads it on demand through the same single worker. Aiko
announces the fortune-teller role in du, reads the complete provider disclaimer,
overview and advice in the original Sie wording, then returns to her normal
voice. The entire prepared reading has at most twelve 125-character text bubbles
with the common timing and final second; oversized content is rejected whole.
The complete original AstroWay footer is visible beneath each bubble, without
using a spoken slot. Credits additionally link to the provider. No translation,
local prediction/fallback or personal-memory claim is introduced.

One reading is admitted per local calendar day across all signs. Admission books
the existing talk care once and persists it with the daily episode before display.
Interruption ends the role; **Tageshoroskop fortsetzen** briefly reintroduces the
role and repeats the interrupted bubble, without repeating completed content,
fetching or booking care. Full delivery including role exit completes the day.
Restart restores progress without automatic playback. Sign changes after admission
apply tomorrow. Opt-out stops playback/network but preserves progress and quotas.
A running old-day reading may finish; paused old-day content expires.

Each day allows at most three dispatched attempts across signs, counting failed,
rejected and discarded replies. Retries require another deliberate selection and
respect 60-second spacing and provider pauses. Matching repeated selections join
an in-flight request; there is no warming or automatic retry. A cached eligible
reading is still available after attempt three. HTTP 200 alone is insufficient:
wrong dates/languages/signs/periods, fallback metadata and STALE cache responses
are rejected. The public endpoint needs no key/account/payment.

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

Sayings/jokes/facts have an eight-second network timeout; horoscope allows 25
seconds for provider generation. All responses are bounded to 16 KiB.
There is no separate four-second display deadline. Errors end the waiting
attempt with a brief menu message; choosing the category retries. Failures never
select local authored entertainment or silently switch to Plaudern. Other ready
API items remain usable if the network subsequently becomes unavailable.

Ready and offered items cannot duplicate one another. The last ten admitted
contents per category also participate in repetition checking, including after
restart. Namespaced provider IDs or normalized text fingerprints match across
all three categories, including text split differently into setup/delivery.
Only actual playback admission records a receipt; preparation, selection and
cancellation do not. Ten newer admissions in its category release an older
receipt, unless another category/buffer/offer still excludes it. Both Sprüche
providers share the same ten-content history. Every rejected, duplicate or failed
attempt consumes the provider budget. A refill cycle stops after three rejected
or duplicate attempts per source and pauses that provider for at least ten
minutes. Transient HTTP/network failures pause it for at least one minute;
access changes stop it for a day. Failed cycles require a new deliberate selection
to retry, within the retained provider pause. No authored fallback is used.

Closing the menu, choosing another care action, disabling sources and shutdown
invalidate pending playback. Stale worker results never trigger a conversation.
Ordinary selection cancellation may leave background warming enabled. Opt-out
clears the online buffers; shutdown closes the worker without waiting on a
network call or allowing it to touch destroyed Tk widgets.

## Free endpoints and request discipline

Only the reviewed public URLs are used, with no keys, account, billing path,
paid fallback or new dependency. HTTP redirects are refused; changed access
requirements remain unavailable. Provider documentation/terms were rechecked on
2026-10-23: JokeAPI documents 120 requests/minute per client; Zitat-Service and
Random Useless Facts have no numeric quota in the reviewed public documentation.
AstroWay publishes 30 public calls per sliding hour per IP, shared with any
other clients on that IP. Unknown limits are not treated as unlimited.

These are **Aiko client caps**, not claims about undocumented provider quotas:

| Provider | Minimum request spacing | Rolling hour | Rolling 24 hours |
| --- | --- | --- | --- |
| JokeAPI, shared by Einzeiler and Witz | 5 seconds | 60 | 300 |
| Zitat-Service | 10 seconds | 20 | 60 |
| Random Useless Facts | 10 seconds | 20 | 60 |
| AstroWay | 60 seconds | 30 | 60 (plus at most **3 per local day**) |

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
is introduced. Only the bounded daily horoscope text is persisted for continuation. Shared-IP provider rejection remains
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

`settings.online_social` is an optional Boolean within the existing version-one
save. Ready sayings/joke/fact buffers and pending tokens are never saved. The
optional outer `social_history` section now uses version three: up to ten admission
receipts per category (thirty total), plus bounded expiring request timestamps
and provider pauses, plus one bounded daily horoscope record (date, attempts,
validated sign/text/footer, interrupted bubble, care admission and completion).
Receipt fields remain category, namespaced provider identity and SHA-256 fingerprint of normalized provider words. Quote identities use
`zitat-service:<entry-id>` in the existing `single` category. These three
receipt categories do not store source words, URLs, frame variants, buffers or
pending tokens. Version-one receipt-only and version-two request histories remain
readable; no history means empty defaults. Opt-out clears buffers and retains admission/request bookkeeping.

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
  source-aware reactions.
- `application/social_coordinator.py` owns the buffers, offers, selection and
  repetition history through the `SocialContentWorker` port.
- `application/social_history.py` supplies immutable bounded admission receipts;
  `infrastructure/social_history_codec.py` validates the compatible version-three
  section, independently of pet experiences. `application/horoscope.py` validates
  the daily text; `application/horoscope_models.py` defines immutable values without
  depending on preparation. `infrastructure/horoscope_codec.py` bounds the saved record.
  `desktop/horoscope_playback.py` joins that record to the existing player,
  visible footer and one-time care admission.
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

## Daily horoscope delivery verification (2026-10-23)

The complete Windows/Python 3.11.9 suite passes **1,776 tests**, including twenty
new horoscope tests (four with native Tk and isolated saves). Ruff, strict Mypy
(264 source files), Pyright and the acyclic-import gate pass. One separate live
Widder request fits ten complete bubbles. Native visual checks cover the sign
selector and visible, unclipped footer. See the [expansion plan delivery
record](SOCIAL_EXPANSION_PLAN.md#horoscope-verification) for scope and evidence.
Tarot remains planned.
