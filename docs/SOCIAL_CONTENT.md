# Conversations and API entertainment

The **Unterhalten** toolbar button opens four choices: **Plaudern**,
**Spruch erzählen**, **Witz erzählen** and **Kurioser Fakt**. Plaudern keeps the
existing authored, context-sensitive conversations. The three new categories
use API content exclusively.

Enable **Onlinequellen für Witze und Fakten verwenden** in settings to use the
API categories. It defaults to off, including when loading older saves without
the option. With online sources off, Plaudern remains available and the three
API choices show disabled controls with a settings hint.

## Providers and preparation

| Selection | Provider | Success fields used |
| --- | --- | --- |
| Spruch erzählen | [JokeAPI](https://jokeapi.dev/), German `type=single`, Safe Mode and excluded flags | `joke`, numeric `id`, `lang`, `safe`, `flags` |
| Witz erzählen | JokeAPI with `type=twopart` and the same language/filter settings | `setup`, `delivery` and the same metadata |
| Kurioser Fakt | [Random Useless Facts](https://uselessfacts.jsph.pl/), v2 random endpoint with `language=de` | `text`, string `id`, `source`, `source_url`, `language`, `permalink` |

Single means one provider text field; it can contain a longer joke or dialogue.
It is not rewritten into a separate authored sayings catalogue. Two Parts keeps
setup and delivery distinct, with a 700 ms pause before the delivery.
Each category has three short German introductions in the existing text resource.
A stable provider-text fingerprint varies the prepared introduction, sometimes
adding a restrained happy/idea emote after the full content. No final emote
precedes the punchline or takes a text slot. Framing and the holding line are
presentation copy, not substitute entertainment or a personal-memory record.

All items are prepared into the existing `Reaction`/`Cue` model, with at most
125 characters per text beat and five text beats including the introduction.
Preparation splits at sentence or word boundaries without discarding words.
Provider-truncated, wrong-language, unsafe-flagged, malformed and oversized
items are rejected. Plain text stays plain text, including literal HTML
entities that can be part of a joke. Provider facts are entertainment inputs;
a valid response is not independent verification of their claims.

The menu retains the most recently accepted item's source and API-entry links.
Links open only when clicked. Source metadata remains attached to the prepared
item; it is not added to Aiko's personal experiences or World knowledge.

The later owner-approved [settings/Credits design](UI_VN_DESIGN.md#approved-settings-and-separate-credits)
places provider information and these per-item source/API-entry links in a
dedicated Credits view rather than an interaction/game menu. This is a
preview/documentation decision only: current runtime placement above remains
unchanged until implementation is separately authorized. Retain the same
accepted-item metadata and ownership; do not add a parallel attribution history.

## Warm buffers and waiting

There are three independent in-memory buffers, each targeting two ready items:
Single, Two Parts and facts. A ready slot contains a validated complete playback
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

Requests have an eight-second network timeout and a 16 KiB response limit.
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
receipt, unless another category/buffer/offer still excludes it. Random-provider
duplicates allow at most three further individual attempts per refill.
Persistent duplicates pause that category instead of replaying a duplicate or
creating an endless request loop. Explicit selection can retry later.

Closing the menu, choosing another care action, disabling sources and shutdown
invalidate pending playback. Stale worker results never trigger a conversation.
Ordinary selection cancellation may leave background warming enabled. Opt-out
clears the online buffers; shutdown closes the worker without waiting on a
network call or allowing it to touch destroyed Tk widgets.

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
save. Requests, ready buffers, source payloads and pending playback are never
saved. The optional outer `social_history` version-one section stores only up to
ten receipts per category (thirty total): category, namespaced provider identity
and SHA-256 fingerprint of normalized provider words. No provider words, source
URLs, frame variants, buffers or pending tokens are stored. Opt-out clears
buffers and retains receipts.

The session restorer carries this value to the existing content coordinator
before online warming starts. Actual admission saves care and its receipt
together once through DesktopPersistence/StateStore; full-sequence wish
completion remains a separate later event. Missing legacy history starts empty.
Invalid history leaves valid pet/world values intact and uses the existing
original-file backup path before a replacement save. No new store, dependency,
translation model or elapsed-time simulator is added.

## Owners and verification

- `application/social_content.py` validates source data and prepares immutable
  source-aware reactions.
- `application/social_coordinator.py` owns the buffers, offers, selection and
  repetition history through the `SocialContentWorker` port.
- `application/social_history.py` supplies immutable bounded admission receipts;
  `infrastructure/social_history_codec.py` validates their version-one save
  representation, independently of provider stories and pet experiences.
- `infrastructure/social_api.py` owns bounded HTTP reads and the data-only worker.
- `desktop/social_runtime.py` coordinates holding and deferred admission through
  existing World, care and presentation callbacks.
- `desktop/care_runtime.py` owns deliberate care dispatch, care presentation and
  Social-to-World admission wiring. `gui.py` composes that owner and keeps its
  existing public care entry point.
- `ui/windows/social_menu.py` presents choices/status/source links; `HoverUi`
  owns its stacking, hover, topmost, dismissal and cleanup.

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
