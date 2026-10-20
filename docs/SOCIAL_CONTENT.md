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
setup and delivery distinct, with a 700 ms pause before the delivery. Facts
always start with a short German introduction. Framing and the holding line
are presentation copy, not substitute entertainment content.

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

Ready and offered items cannot duplicate one another. The last two delivered
items per category also participate in repetition checking; older deliveries
can become eligible again. Random-provider duplicates allow at most three
further individual attempts per refill. Persistent duplicates pause that
category instead of creating an endless request loop.

Closing the menu, choosing another care action, disabling sources and shutdown
invalidate pending playback. Stale worker results never trigger a conversation.
Ordinary selection cancellation may leave background warming enabled. Opt-out
clears the online buffers; shutdown closes the worker without waiting on a
network call or allowing it to touch destroyed Tk widgets.

## Care and persistence

Every accepted variant uses the existing `talk` care transition: **+26 social,
-1 energy, no direct fun gain**, with normal need clamping. All four choices
share the same friendship category, eligibility interval and rolling budgets.
Changing category never opens another friendship reward. See
[friendship rules](FRIENDSHIP_SYSTEM.md) and [need effects](FUN_MOOD_SYSTEM.md).

Menu opening, warming, the holding line and failed/cancelled preparation grant
no care or qualified personal contact. When actual content playback is accepted,
care commits once. Reading clicks, the punchline and completion grant nothing
extra; later interruption does not undo accepted care.

`settings.online_social` is an optional Boolean within the existing version-one
save. Requests, ready buffers, source payloads and pending playback are never
saved. Restart warms fresh items and preserves the existing pet and shared
friendship history. No runtime dependency or translation model is added.

## Owners and verification

- `application/social_content.py` validates source data and prepares immutable
  source-aware reactions.
- `application/social_coordinator.py` owns the buffers, offers, selection and
  repetition history through the `SocialContentWorker` port.
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
