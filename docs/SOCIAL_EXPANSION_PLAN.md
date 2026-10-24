# Sayings, daily horoscope and tarot expansion plan

> **Sprüche, shared bubble timing and the daily horoscope baseline implemented;
> horoscope gift/VN presentation and tarot planned.**
> Initial documentation-only plan recorded on 2026-10-23 at checkout `f6ae2df`
> on `feature/social-optimization`. The owner later authorized the shared bubble
> times (including final second and punchline pause), followed by the Sprüche
> slice: German one-liners, quotations and their request/save/Credits boundaries.
> The owner subsequently authorized the daily horoscope slice below, then recorded
> the future hat-gift and VN presentation concept. That extension remains planning
> only. This documentation update authorizes no implementation, further asset
> generation, purchases, CI setup, push or merge. Existing parallel work is preserved.

This is the current planning authority for the selected social expansion.
The [original concept](SOCIAL_ENTERTAINMENT_CONCEPT.md) preserves earlier ideas;
the [jokes/facts delivery record](SOCIAL_CONTENT_IMPLEMENTATION_PLAN.md) and
[current social behavior](SOCIAL_CONTENT.md) describe the implemented baseline.
Decisions below supersede earlier proposals for the selected scope. The current
Sprüche and horoscope behavior are described in [social content](SOCIAL_CONTENT.md);
the delivery records below retain their individual scope. Tarot remains future work.

## Owner decisions

| Area | Selected direction |
| --- | --- |
| German UI label **Sprüche** | Mix genuine short one-line jokes from JokeAPI with short quotations from Zitat-Service behind one choice. A provider `single` field alone does not qualify as a one-liner. |
| Daily horoscope baseline | German AstroWay content with direct zodiac selection, a role performance of at most twelve text bubbles and one resumable reading per local calendar day; at most three fetch attempts per day. Birthday assistance is later work. |
| Planned horoscope gift and VN presentation | Receiving a permanent fortune-teller hat as a gift unlocks the horoscope. Aiko wears it only during the reading. Match its views to the scene's actual head poses and plan a separate floating book. See the [gift and presentation decision](#planned-horoscope-gift-and-vn-presentation). Implementation remains future work. |
| Tarot | Aiko explicitly plays the fortune-teller/card-reader role and presents the source's card meaning. |
| Address | Aiko's ordinary framing uses **du**; source text may retain **Sie** inside the announced role. Preserve source wording. |
| Cost | Content acquisition and operation of these integrations must be free of provider charges. No API keys, accounts, paid fallback or subscriptions. |
| Reading time | Review actual bubble durations for Spruch, Witz, Kurioser Fakt and Plaudern together, including the new readings. |
| Later presentation | Card artwork, suitable gestures and subtle effects may extend the performance later. A crystal ball is explicitly outside the first step. |

The proposed rule-based Sie-to-du converter is withdrawn. No NLP package,
local language model, translation service or paid inference is part of this
scope. Authored framing is allowed; replacement authored jokes, quotations,
horoscopes or card meanings are not selected. Existing Plaudern remains authored.

## Mandatory zero-cost and keyless boundary

- Use only free, unauthenticated endpoints that require no provider account,
  payment details, billing agreement, purchased credits or subscription.
- A free trial, introductory credit balance or free tier requiring a key does
  not satisfy this requirement. No shared embedded developer credential or
  user-supplied key is an alternative.
- Do not introduce paid hosting, translation/inference services, asset
  purchases or compulsory paid software for these features.
- Restrict each adapter to its reviewed free endpoint paths. HTTP errors,
  exhausted limits and changed access requirements must produce temporary
  unavailability, never a fallback to a metered endpoint or a purchase flow.
- Recheck free access, desktop use, attribution, caching and request limits
  before implementation and activation. If a source no longer meets these
  conditions, leave it disabled while discussing another free source.
- No promise of permanent third-party availability is made. The durable product
  rule is that Aiko must not incur provider charges to keep content available.

The existing online-source opt-in remains the admission boundary, off by
default. Its future German wording must cover the expanded sources. Disabling
it prevents new network work and invalidates pending online playback.

## Sprüche: short jokes and quotations

Use German JokeAPI `type=single` with the existing safety filters and German
Zitat-Service quotations. The two sources feed one public action, with internal
provider identity and attribution preserved. Witz retains its separate
two-part setup/punchline flow; Kurioser Fakt and Plaudern retain their meanings.

Approved Sprüche eligibility (implemented in this slice):

1. Keep the confirmed 125-character limit for one complete short content item
   in one content bubble, including spaces and punctuation. Introduction and
   quotation attribution are separate framing. Visual word wrapping does not
   turn a long story into a one-liner or require the text to occupy one physical
   screen line.
2. Reject multi-paragraph stories, multi-turn dialogue, separately staged
   setup/delivery and oversized content. Length alone does not establish genre;
   the live sample on 2026-10-23 qualified six of nine delivered JokeAPI entries
   and ten of ten quotations. Implemented format checks do not claim general
   semantic classification. Dialect remains unchanged; no standard-German-only
   rule was approved.
3. Preserve every word of an accepted item. Do not shorten a long joke, take
   only the opening sentence of a quotation or rewrite content to make it fit.
   Preserve intentional literal HTML character sequences as part of the original
   content; do not blanket-decode entities or interpret them as markup. For
   example, JokeAPI's programming joke containing `gro&szlig;en` keeps that
   sequence unchanged, and all of its literal characters count toward the limit.
4. Keep quotation author, original entry/source link and provider/license
   attribution. An unknown author stays unknown. Credit the author in the
   performance and retain source/license details in the existing Credits view.
5. Vary sources and avoid repetition through the existing coordinator. A roughly
   balanced mix is a working proposal; exact weights are not yet selected.
   Provider outage may leave the other eligible free source usable within this
   same action; never substitute authored entertainment.
6. Count rejected, duplicate and failed fetches against request budgets. Stop
   bounded refill attempts when too few items qualify; do not fetch endlessly
   to fill a buffer or force a source ratio.

Illustrative framing, not approved catalogue copy:
"Hey, ich hab im Netz etwas für dich gefunden." Then the original content and,
for a quotation, a short author attribution. Keep current action/wish semantics
explicit when adding a provider subtype; quotations must not create a second
care reward or a separate competing history for the same Sprüche action.

## Sprüche delivery scope and initial client limits (2026-10-23)

The owner authorized this slice after the sample and 125-character/HTML decisions.
One public **Sprüche** choice now mixes JokeAPI and Zitat-Service, with two ready
items total, one shared ten-admission window and the existing once-only `talk`
care/wish semantics. Prefer alternating sources when both are ready; initial
preference is JokeAPI. Available content is not delayed or fetched again solely
to enforce a ratio. Authored introduction, original short content and separate
quotation author use the approved bubble timing; the author receives the final
second. Provider, original source, author/entry links and collection CC BY 4.0
attribution remain available in the existing Credits view.

Public access and provider terms were rechecked before this delivery. All selected
URLs remain free and anonymous. No key, account, paid service or dependency was
added. Refuse redirects and stop on access changes instead of following a new URL.
Conservative **client caps** are now explicit; these are not undocumented provider
quotas:

| Provider | Spacing | Rolling hour | Rolling 24 hours |
| --- | --- | --- | --- |
| JokeAPI, shared by Sprüche and Witz | 5 s | 60 | 300 |
| Zitat-Service | 10 s | 20 | 60 |
| Random Useless Facts | 10 s | 20 | 60 |

All attempts count. Stop each rejected/duplicate refill cycle after three attempts,
with a ten-minute provider pause; failures require a deliberate retry. Transient
HTTP/network errors pause at least one minute, access changes one day. HTTP 429
uses Retry-After/reset metadata, defaulting to fifteen minutes if absent. Provider
pauses and rolling counters survive restart and opt-out via the compatible
version-two `social_history` section in the existing atomic save. No source words,
source URLs, warm stock or pending playback are persisted. Reservation persistence
runs before dispatch, without pet-time progression; a failed save prevents HTTP.

Daily horoscope and direct zodiac options are now delivered in the separate slice
below. Tarot, birthday assistance, role effects and card assets remain planned.
The historical timing/test delivery records retain their original scope and results.

## Daily horoscope and role performance

The owner confirmed this design on 2026-10-23 and subsequently explicitly
authorized its implementation. The runtime, direct sign option and compatible
daily save extension now implement these rules. Tarot remains separately planned.
The [later gift and VN presentation decision](#planned-horoscope-gift-and-vn-presentation)
is a future extension; the following sections describe the delivered API baseline,
which does not yet require or display a hat.

Use `GET https://api.astroway.info/v1/public/horoscope/daily` with an explicitly
selected `sign`, `lang=de` and the intended local calendar `date`. The reviewed
endpoint needs a zodiac sign, not birth date, birth time or birthplace.

Options belong to the existing `PetSettings` owner:

- First version: a direct selection labelled "Sternzeichen fürs Tageshoroskop",
  containing all twelve signs and "Nicht ausgewählt" as the default. No sign
  means the horoscope choice is disabled with an explanatory settings hint;
  never guess a sign.
- Store one confirmed sign as the canonical choice. Choosing a sign or opening
  settings/the menu performs no request and starts no reading.
- Birthday assistance is later work, outside the first version. It could suggest
  a sign locally from day/month for confirmation, without a birth year. Do not
  transmit a birthday or introduce a second competing sign preference. Input
  retention and exact assistance UI remain future decisions.
- Tarot and Sprüche do not require a birthday or zodiac sign.

Aiko announces entering the fortune-teller role, presents the original German
provider text, then visibly returns to her ordinary voice. The formal address
is part of this performance. Framing and role exit use du. Do not change
pronouns, conjugate verbs, claim the reading is Aiko's own observation of the
user or insert provider statements into subjective Mind/World knowledge. An
interruption ends the role immediately; resuming briefly announces re-entry.

Selected presentation order (framing examples, not runtime catalogue changes):

1. Role entry, for example: "Ich schlüpfe mal in die Rolle der Wahrsagerin. Mal
   sehen, was heute für dein Sternzeichen geschrieben steht."
2. Present the complete provider AI/entertainment disclaimer.
3. Read the complete overview and daily advice, retaining original wording and
   Sie address within the announced role.
4. Return to Aiko's ordinary voice, for example: "So, die Sterne hatten ihren
   Auftritt. Jetzt bin ich wieder deine Aiko."

Keep the original provider footer and source attribution visible with the
reading; Credits supplement them rather than replacing mandatory visible hints.
Do not offer a key/payment flow or read an English fallback as horoscope content.

### Content and twelve-bubble budget

Use complete `data.sections.overview` and `data.sections.advice`, not all six
topics or the full concatenated `data.horoscope`. Validate the successful response
envelope, daily period, German language, requested sign/date, both complete
sections, disclaimer and provider footer before admission. An HTTP 200 alone is
insufficient: the provider can return older or non-German text with fallback
metadata while computed fields still match the requested date. Check the text's
actual date/language too; reject stale or non-German fallback content without
consuming reading eligibility. See the
[public daily endpoint contract](https://api.astroway.info/en/docs/api/operations/publichoroscopedaily/).

The approved bound is **at most twelve text bubbles for one prepared horoscope
sequence**, including role entry/exit, the complete AI/entertainment disclaimer
and any spoken attribution. Every text bubble keeps the **125-character limit**.
Use the existing common reading time, final-text second and reading clicks. The
actual final text receives the allowance, normally the role exit. The earlier
eight-bubble proposal is superseded; the five-text budget for other social
content is not enlarged by this decision.

The live Widder sample for 2026-10-23 has a 371-character overview and a
201-character advice section: five content bubbles with current segmentation.
Its 231-character disclaimer takes three more. With one role-entry and one exit
bubble, that is ten text bubbles, roughly eighty seconds using the selected
reading times. This is one sizing sample, not a guarantee for every sign/day.
Reject content that cannot fit completely within twelve bubbles. Never shorten
source text, omit a required section or bypass the budget with unrelated reactions.

### Once per day and interrupted delivery

The selected rule is **one resumable daily reading per local calendar day across
all signs**, not one reading per sign. Use the user's local date (Europe/Berlin in
this planning session), with no 24-hour cooldown, offline backlog or request merely
because midnight passes. Pass the selected date explicitly; the provider's
default is UTC.

| State | Planned selection behavior |
| --- | --- |
| Not begun | "Tageshoroskop anhören"; fetch only on deliberate selection if no eligible prepared item exists. |
| Fetch/preparation failed or content rejected | Leave reading eligibility open, subject to the separate three-attempt request cap and provider pauses. |
| Interrupted | "Tageshoroskop fortsetzen"; resume the same item's interrupted bubble, without another fetch or care booking. |
| Full sequence completed, including role exit | "Heute bereits vorgelesen"; another reading is available tomorrow. |
| Restart | Restore the same daily state and any eligible continuation, without automatic playback or completion. |

- First actual playback admission fixes that day's reading and books the existing
  talk care once. Full-sequence completion marks the day completed. Continuing
  the same item repeats neither the care booking nor already completed content
  bubbles. No new reward formula or wish family is selected.
- Before playback begins, the sign may change. Invalidate any mismatching
  prepared item or in-flight result; a discarded request still counts. Once
  playback has begun, changing the preference applies from tomorrow and neither
  replaces the active item nor unlocks another reading after completion.
- A reading already playing at midnight may finish as the previous day's item;
  it must not mark the new day completed. A paused previous-day reading expires
  instead of being resumed or completed offline. Today's reading is independently
  eligible. Late fetch results must never become the new day's reading.
- Disabling online sources prevents playback/continuation and further requests,
  while retaining the daily status and already booked care. Re-enabling on the
  same day can resume the same still-eligible item, without resetting anything.

Persist a bounded daily record containing date, selected sign, validated content,
reading progress, admission/care status and completion evidence through the
existing atomic save owner. Keep settings, provider content and lifecycle evidence
distinct within that boundary, not in a second mutable store or journal. Existing
social admission receipts contain hashes/identities, not content or continuation
state. The implemented version-three social history adds exactly this bounded
daily record, while continuing to read version-one and version-two histories.
Development verification uses isolated temporary saves.

### At most three horoscope fetch attempts per day

- Normally fetch one successful item per used day and reuse it for playback or
  continuation. Opening/reopening menus and repeated clicks coalesce matching
  in-flight work; never fetch merely to prepare a second ready horoscope.
- Allow **at most three dispatched horoscope HTTP attempts per local calendar
  day**, shared across all signs. Count timeouts, HTTP errors, rejected/oversized
  content and discarded stale/sign-mismatched responses as attempts too. Each
  attempt uses the existing bounded request-admission and persistence boundary.
- Persist the attempt count independently of successful reading/completion.
  Restart, sign changes, cancellation and opt-out must not reset it. Once all
  three attempts are spent, show a retry-later/tomorrow status; an already valid
  cached reading may still play or resume within its daily eligibility.
- Retries are deliberate and paced, subject to provider pauses/Retry-After and
  the shared AstroWay public IP budget of 30 requests per sliding hour. No
  automatic endless retries, new worker, credential, paid fallback or local
  replacement horoscope is allowed. Tarot's eventual attempt policy remains
  undecided and must share the provider budget without inheriting this rule.

## Planned horoscope gift and VN presentation

Owner decision recorded on **2026-10-23**. This is an approved product direction
for later implementation, not a description of current runtime behavior or a
production-asset approval.

### Permanent gift and horoscope unlock

- The fortune-teller hat is a **permanent gift/item** that the player gives Aiko.
  Actual receipt unlocks the horoscope; choosing a zodiac sign or merely selecting
  an item in a menu is not receipt. Before the gift, the future horoscope action
  remains locked. The direct zodiac selection remains a separate prerequisite.
- Keep the gift and resulting access across sessions. The hat is retained for
  later readings and is not consumed by a reading. Its acquisition route and
  concrete save representation remain future design work.
- Aiko wears the hat **only while performing the horoscope reading**. At completion
  or interruption she leaves the role and removes it from the scene while retaining
  the item. Resuming the daily reading restores the role and hat without another
  gift or a second reading admission.
- The once-per-day/resumable-reading rule, twelve-text-bubble ceiling and common
  reading times, including the final second, remain in place. This decision adds
  no friendship, care or reward-balance changes.
- Future implementation must respect the existing [World ownership boundaries](WORLD_OBJECT_CONTRACTS.md):
  durable item receipt/possession and temporary scene appearance are distinct.
  Do not make a visible hat overlay the authority for gift ownership or unlock.

### Anime/VN scene and hat perspectives

- Treat the reading as an activity in Aiko's Desktop-Tamagotchi life: the gift gives
  her an occasion to try the fortune-teller role with the player. Coordinate her
  existing poses, emotes, pauses and text bubbles as a small VN scene.
- Aiko's own curiosity, pride, hesitation or spontaneous comments may emerge from
  the particular reading. An apology or explicit return-to-role joke is not a
  mandatory repeated step. Example dialogue and the exact choreography remain
  drafts, not an approved text catalogue.
- Limit the initial hat artwork to the head views actually selected for this
  scene, such as facing the player, looking at the book and a chosen head tilt.
  Standing at a fixed desktop position does not keep the head angle fixed.
- Match hat perspective, position, scale and hair overlap to those poses and their
  transitions; keep Aiko's face readable and her identity/proportions consistent.
  One front-facing overlay must not be assumed to fit every gaze or animation
  frame. Exact views, anchor data and production counts require a later review.
- Emotes currently replace text on the same speech surface. Place them between
  text bubbles; simultaneous surrounding particles would be additional presentation
  work. Coordinated pose changes within the reading also need later orchestration.

### Separate floating book

- Plan the book as its **own scene asset**, with a perspective that lets Aiko
  visibly look into the pages. The first placement candidate is slightly in front
  of her on screen-right near chest level, matching the existing down-right gaze.
  Keep her face, hands and speech area readable; final size and position are open.
- Gentle floating motion and occasional page-turn animation are later asset and
  choreography work. Opening/closing states are candidates to review with that
  sequence, not a fixed frame-production order. Aiko need not hold the book.
- The first concept image supports the hat/book direction only. Its malformed book
  is a composition placeholder, not approved book artwork; it must not become a
  runtime asset. The hat's fit and perspectives also still need a proper asset pass.
- Follow the local character-asset workflow for any later authorized production:
  inspect the selected existing poses, preserve originals outside Git and review
  the complete composition and transitions before a separate integration decision.

### Scope of this decision

This records the hat gift/unlock, scene-only wearing, suitable hat perspectives
and floating-book direction. It does not select a replacement horoscope provider,
a local astronomical library or a generated-text system. Those options remain
under discussion; the earlier AstroWay implementation and its delivery evidence
are retained as the current baseline. Sprüche and tarot retain their separate
existing scope. No code, saves, runtime assets or dependencies are changed here.

## Tarot

Start with the free `GET https://api.astroway.info/v1/public/tarot/daily`, an
explicit local date and `lang=de`. Use the original card identity, orientation
and the matching German localized meaning. A missing/false localization flag,
missing German meaning or inconsistent orientation makes the item unavailable.
Do not speak the parallel English base fields as a fallback.

Planned first performance: enter the card-reader role, announce the card and
orientation, read its complete short meaning, then leave the role. Authored
framing may be playful and theatrical; the interpretation remains provider
content. Aiko does not claim personal knowledge about the user's past or future.

The reviewed daily draw is date-seeded, not a new personal shuffle on every
click. Reuse that day's card and describe it honestly as a Tageskarte. The
horoscope's once-per-day completion rule does not automatically impose a
tarot reward/cooldown rule; replay availability and care treatment must be
settled before delivery. Repeated selection must not create new network draws.

Full generated three-card interpretations, a personalized new-draw mode, new
gestures/effects, card-asset imports and the crystal ball remain later work.
Any future artwork must be free to obtain with suitable reuse terms. Confirm
the exact image source and license separately from the text API; a returned
image URL is not a completed asset review. Follow local character-asset guidance
before any later Aiko artwork/frame selection or generation.

## Provider access and request limits

Checked against primary documentation on 2026-10-23; these are current research
findings, not permanent service guarantees. Unauthenticated German responses
from Zitat-Service and the selected AstroWay horoscope/daily-card endpoints
were also read successfully in the planning conversation. No activation or
distribution acceptance is implied by those samples.

| Provider and use | Free/keyless access evidence | Documented request budget |
| --- | --- | --- |
| [Zitat-Service API](https://api.zitat-service.de/), quotations | Public API specification has no authentication requirement; a German quote was retrieved without credentials. Collection terms declare CC BY 4.0. | No numeric limit found in the reviewed API documentation/terms. This is unknown, not unlimited. |
| [AstroWay public endpoints](https://api.astroway.info/en/free/), daily horoscope and card | The selected public paths are described as free without signup or key. They are distinct from key-based monthly-credit plans. | 30 requests per sliding hour per IP, shared across public calls. The higher site-header/server tier is not the desktop client's budget. |
| [JokeAPI](https://jokeapi.dev/#ratelimit), single and two-part jokes | Documentation states no token, registration or payment is required. | 120 requests per minute per client; headers expose remaining budget/reset and Retry-After. Both joke types share this provider budget. |
| [Random Useless Facts](https://uselessfacts.jsph.pl/), existing facts | The documented v2 German endpoint works without credentials. | No numeric limit found in the reviewed documentation. This is unknown, not unlimited. |

Reuse conditions: [Zitat-Service terms](https://www.zitat-service.de/en/start/contact)
declare the collection CC BY 4.0; preserve attribution and source links.
[AstroWay terms](https://api.astroway.info/en/terms/) permit application use and
caching and require retained AI/entertainment disclaimers. Public responses
also carry a source footer. Provider pricing, path access and conditions must
be rechecked before delivery. All of these conditions are subordinate to the
owner's zero-provider-cost requirement for source selection.

Planned request discipline:

- Extend the existing one-worker coordinator with per-provider scheduling and
  shared budgets, not independent counters per menu choice or new workers.
- Fetch horoscope/card on demand and reuse the bounded daily item. Normally
  this needs one successful horoscope call and one card call on a used day.
- Keep small bounded buffers for jokes, quotations and facts. Include every
  attempt, rejection, duplicate retry and refill in the provider's budget.
- Coalesce matching in-flight requests. Menu reopen, settings repaint and
  repeated clicks must not enqueue duplicate work.
- Respect HTTP 429, Retry-After and reset metadata. Use bounded backoff for
  transient errors, stop on access changes, and expose a useful unavailable/
  retry-later status. Do not spin, evade a quota or introduce credentials.
- Unknown limits require conservative finite client pacing/caps before
  activation. Exact initial values must be recorded after provider review;
  lack of a published number is not permission for unrestricted retries.
- A local client cannot know all traffic from another client sharing its public
  IP. Handle provider rejections even when Aiko's own budget is not exhausted.
- Restart must not be a quota-reset mechanism. Define bounded persisted request
  bookkeeping with expiry through the existing persistence boundary; no second
  pet elapsed-time simulator or permanent request log is needed.

## Bubble-duration review

The owner reports that some bubbles feel too brief and approved the following
timing policy on 2026-10-23. It covers Spruch, Witz, Kurioser Fakt and Plaudern,
with the same reading policy planned for the new reading performance. The
owner subsequently authorized and received the timing slice for the four
existing actions. This does not claim a reproduced native timer fault or
delivery of the new social actions.

### Runtime baseline before the timing change

- `pet/mind/reaction_sequence.py::Cue.text` derives duration from text length.
- `data/balance.json` sets minimum 2,800 ms, 58 ms per character and maximum
  8,000 ms. At the 125-character limit the length term reaches 7,250 ms.
- Examples: 40 characters = 2.8 s; 80 = 4.64 s; 125 = 7.25 s. There is no
  additional fixed orientation-time term above that clamped calculation.
- `ui/pet_view/reaction_player.py` passes cue duration to display and schedules
  the next beat; `speech_presenter.py` owns the visible bubble/hide timer.
  Reading clicks may deliberately advance a story.

### Approved text-bubble timing

Use one common automatic reading speed across the four actions:

1. Calculate **1,500 ms orientation time + 65 ms per displayed character**,
   including spaces and punctuation, after text formatting and segmentation.
2. Clamp that result to **at least 4,000 ms and at most 10,000 ms** per bubble.
3. Give the **last text bubble of the complete interaction another 1,000 ms**,
   still capped at **10,000 ms**. It qualifies even if an emote follows. A
   following author-attribution or role-exit text is itself the last text and
   receives the allowance instead; do not add it to every section or fragment.

The final-bubble allowance is visible reading time before the bubble disappears
or a following emote replaces it, rather than an extra blank pause.

| Displayed text length | Existing duration | Approved ordinary bubble | Approved final text bubble |
| --- | --- | --- | --- |
| 40 characters | 2,800 ms | 4,100 ms | 5,100 ms |
| 80 characters | 4,640 ms | 6,700 ms | 7,700 ms |
| 125 characters | 7,250 ms | 9,625 ms | 10,000 ms |

### Approved sequence-specific behavior

| Action | Selected timing behavior (new content remains planned) |
| --- | --- |
| Sprüche and quotations | Apply the common formula to the introduction, one content bubble and any separate author credit. The actual last text receives the final-bubble allowance. |
| Witz | Give every setup and delivery bubble its full reading time. After the final setup bubble, add **800 ms of deliberate pause before the first punchline/delivery bubble**. This is additional to setup reading time, not a deduction from it, and replaces the existing 700 ms pause. The final punchline text receives the final-bubble allowance when no later text follows, even if an emote follows. |
| Kurioser Fakt | Apply the common formula to the introduction and every complete content segment. Add no artificial gaps between contiguous content bubbles. The last text receives the final-bubble allowance. |
| Plaudern | Apply the common formula to every text bubble. Preserve authored thinking/expression pauses; the last text receives the final-bubble allowance. |

Deliberate reading clicks remain available to advance the sequence sooner,
including the existing ability to skip intervening emotes/pauses. They retain
their reading-only semantics. The 800 ms punchline pause describes automatic
playback; it is not a new unskippable input lock. No extra category-specific
reading speeds or user speed settings are selected in this step.

### Timing implementation and verification

`Reaction.__post_init__` prepares the common text durations for `talk` sequences
through `reaction_sequence.conversation_timing`, using the `conversation_*`
balance keys. Final-text detection spans the full sequence, including trailing
emotes. Replacing immutable reaction metadata recomputes the same duration;
it never accumulates another final second. Generic feedback keeps its existing
timing. API preparation inserts the 800 ms punchline pause once, after all setup
segments. The existing player and speech presenter consume the prepared
durations without an additional timer or care writer.

Cue validation now permits text up to 10,000 ms; emotes/pauses keep their
8,000 ms ceiling. Balance validation checks the conversation profile too.
Deterministic tests check character/clamp boundaries, trailing emotes/credits,
multi-bubble setup/delivery, the full pause, early reading clicks, stale
callbacks and once-only completion. Native Windows/Tk tests map real speech
widgets using a controlled clock and verify visibility until the full reading
deadline, the final allowance before an emote, pause hiding and cancellation.
They exercise all four existing actions and short/medium/125-character text
without reading or writing a user save. Subjective desktop reading comfort
still requires owner feedback; automated widget assertions do not claim it.

## Existing owners and eventual verification

| Owner | Planned responsibility |
| --- | --- |
| `application/settings.py` | One online opt-in and canonical zodiac preference; passive UI edits through existing settings flow. |
| `infrastructure/social_api.py` and worker port | Reviewed free endpoints, bounded HTTP, typed failure/rate metadata; no Tk or pet mutations. |
| `application/social_content.py` | Source-aware validation, one-liner eligibility, original text segmentation and reading preparation. |
| `application/social_coordinator.py` / `social_history.py` | Provider mixing, bounded buffers, identity/repetition checks, request admission and daily lifecycle evidence. |
| `desktop/social_runtime.py` / `care_runtime.py` | Existing interaction admission, role sequence lifecycle and once-only shared care/contact effects. |
| `Reaction` / `Cue` / `ReactionPlayer` / `SpeechPresenter` | One ordered speech surface, durations, pauses, reading clicks and cancellation. |
| Existing persistence and social codecs | Explicit compatible daily/cache extension and atomic saves; no live-save manipulation during development. |
| Existing social/settings/Credits views | Choices, readiness, daily status and source/license details. Preserve required disclaimers visibly with the reading; generic hidden Credits alone must not silently replace them. |

Later verification must cover one-liner accept/reject fixtures, attribution,
original Sie/du text preservation, role exit on cancellation, zero-cost endpoint
allowlists, mixed-source duplicates, all provider budgets/429s, bounded retries,
local day/DST/restart/sign-change cases and exactly-once care/wish completion.
Ordinary tests use provider-shaped fixtures and temporary saves. Keep live
provider checks separate and limited. No new reward formula or wish family is
selected; adding two menu choices must not leave duplicate contact/need writers.

The daily horoscope now uses the existing worker on demand, a visible original
footer beneath every spoken bubble, and the existing atomic save for daily
attempts, validated text, current bubble, care admission and full completion.
Admission and care are persisted together before display; each bubble transition
is persisted before the next bubble is shown. A failed write prevents dispatch
or stops playback. A resumed role introduction does not advance provider-text
progress. No additional completion reward or wish family is introduced.

Remaining work after separate authorization: tarot lifecycle/presentation,
birthday assistance, optional role effects and assets. Subjective practical
reading-comfort acceptance remains pending.

## Verification of this documentation pass

The initial documentation-only pass changed this plan and its links. Its
Markdown diff was reviewed, all 77 relative documentation link targets across
the four files exist, and scoped whitespace checks pass. No runtime tests were
run for that documentation-only change. No runtime implementation,
model/dependency installation, asset work, live-save access or new provider
content catalogue was part of that pass. The subsequent timing-only runtime
delivery is described above; its final checks are recorded below.

## Bubble-timing delivery checks (2026-10-23)

- Windows, Python 3.11.9: the ten new timing tests pass, including two native
  Tk cases with mapped speech windows and controlled time. The existing native
  World conversation-focus test also passes after replacing its artificial
  250 ms text assumption with the prepared sequence duration. It now checks
  that focus remains protected until the last millisecond before completion.
- Whole-repository Ruff passes. Strict Mypy passes for all 258 application/tool
  source files; repository-wide Pyright, including tests, reports zero errors
  and warnings. Scoped whitespace checks and all 129 relative link targets in
  the six checked guides pass.
- Final full suite: **1,725 tests in 242.636 s; 13 assertion failures**. This is
  not a green suite. Every remaining failed assertion is also reproducible in
  a separate archive of the unchanged pre-timing checkout `48a59b3`, using the
  corresponding fourteen selected test methods (including passing controls).
  Subsequent parallel commits changed only separate care-planning documentation.

The remaining failures concern existing friendship/nutrition and daily schedule
expectations (`test_consumption_origin`, `test_daily_need_schedules`,
`test_interaction_relief`), the expected Moodlet family count (`test_emotions`,
`test_moodlet_mood`), menu/toolbar layout and enabled-state expectations
(`test_main_menu_layout`, `test_rock_paper_scissors_gui`, two unrelated cases in
`test_world_runtime_flow`), old fixed API-introduction/no-history expectations
(`test_social_gui`), and a real-clock friendship precision assertion
(`test_world_gui`). No fix for those separate findings is claimed.

The final timing change adds no provider, dependency, API credential, new
request path, asset or save format. Native automated visibility checks do not
constitute subjective reading-comfort approval. Quotations, genuine one-liner
filtering, horoscope and tarot remain planned.

## Test and wish-card layout follow-up (2026-10-23)

The owner subsequently authorized updating stale expectations, stabilizing the
clock-sensitive withholding test and fixing the wish-card layout. The thirteen
earlier failed assertions are a historical pre-repair result. Friendship
parameters/production policies and new social actions remain unchanged.

- Food tests check actual personal contact instead of instant friendship gains.
  Conversation completion is compared with an elapsed-only control, checking
  that neither completion nor a repeated callback grants another care effect.
- Eight-/four-phase schedule fixtures retain their need/mood baselines and
  contact/neglect invariants. They do not generate wishes and no longer assert
  retired friendship reward plateaus; no replacement balance target is chosen.
- Emotion/catalogue tests cover every defined family, including disappointed,
  while preserving group/global contribution checks and all active entries.
- Native social tests allow the selected introduction variants, check the full
  provider body and 800 ms pause, and verify receipt-only persistence with
  empty buffers after restart. Selector tests distinguish opening navigation
  from starting an action and exercise denied choices without state changes.
- Withholding's discrete half-point receipt and save/restart checks use zero
  consumed session time and an immediate restore endpoint. Continuous live and
  offline progression keep their separate coverage. Ordinary World holding
  checks assert unchanged contact/penalty evidence, allowing natural elapsed
  emotional flow instead of demanding bit-identical friendship points.
- The passive pin now occupies reserved title space within each wish card,
  removing the extra width column. Native checks exercise three visible cards,
  pin/unpin without width changes, title/pin/objective separation, overflow and
  removal. Existing card controls and saved pin state remain intact.

Final follow-up validation on Windows / Python 3.11.9: **all 1,725 tests pass
in 236.859 seconds**. Whole-repository Ruff, strict Mypy (258 source files) and
Pyright pass. All 140 checked relative documentation targets exist and scoped
whitespace checks pass. Native geometry probes measure **621 px of card content
inside a 644 px viewport**, both pinned and unpinned, at the same 690 px menu
width; no horizontal scrollbar is shown. The previous content width was 705 px.
These automated native checks do not claim every DPI/monitor configuration or
subjective reading comfort. Integrated friendship-balance acceptance remains
separate; no balance parameter or new social feature was changed in this follow-up.

## Sprüche delivery verification (2026-10-23)

- Windows / Python 3.11.9: full suite **1,756 tests passes in 297.568 seconds**.
  After the final unquoted-dialogue and missing-source-link edge refinements,
  all **97 focused social tests** pass again in 7.660 seconds. The quote-specific
  wish check also covers full author delivery, cancellation and duplicate completion.
- Whole-repository Ruff passes; strict Mypy passes all **260 source files**;
  repository-wide Pyright reports zero errors/warnings. Relative documentation
  links and scoped whitespace checks pass.
- Native temporary-save Tk tests exercise the existing Sprüche choice, unchanged
  care booking, author bubble/final second and separate provider/source/author/entry
  Credits links. Ordinary tests use fixtures; the full suite emits non-failing
  ttk ThemeChanged shutdown messages while destroying test windows.
- Limited live checks retrieved an eligible 82-character JokeAPI one-liner and
  a 52-character Zitat-Service quotation with author metadata; an ineligible
  provider item was rejected rather than shortened. JokeAPI sends Retry-After
  even with remaining budget: a regression test distinguishes ordinary reset
  information from an exhausted quota. The adapter retains 429/reset pauses and
  refuses HTTP redirects, separately tested against a local HTTP server.
- No normal user save, dependency installation, horoscope/tarot implementation,
  card/character asset work, CI setup, push or merge is part of this slice.

## Daily horoscope implementation (2026-10-23)

- Direct sign selection has twelve signs and an unselected default. The existing
  online opt-in explicitly includes horoscope content. Selecting a sign or opening
  a menu does not fetch a horoscope. Missing signs disable its menu choice and
  show a settings hint.
- The reviewed public daily path needs no key, registration or paid fallback.
  Only explicit selections dispatch requests; matching in-flight selections join
  the same request. There are at most three dispatched attempts per local day
  across signs, plus a 60-second client spacing, provider pauses/Retry-After and
  the provider-wide rolling-hour budget. An existing valid item remains usable
  after the last attempt. No automatic horoscope refill/retry is introduced.
- Successful replies must match sign/date/period/language, contain both complete
  sections, disclaimer and attribution, and fit twelve 125-character bubbles.
  Fallback metadata or a STALE cache header is rejected conservatively. Provider
  wording/Sie is preserved; the role entry and exit use du. The original footer
  is rendered as visible plain-text attribution, outside the spoken bubble budget,
  and AstroWay is also listed in Credits.
- A bounded version-three daily record extends the existing social history;
  version-one and version-two saves remain readable. Care admission, continuation,
  opt-out, sign changes and day boundaries follow the rules above. A running
  old-day reading can complete without completing the new day. A paused old-day
  reading is not offered again.
- One separate live Widder request for 2026-10-23 passed validation in ten bubbles
  with lengths 108/88/71/70/123/125/121/124/76/70. This is a sizing/contract
  observation, not a guarantee for all future signs/days.
- Fixture and native temporary-save tests cover full text/budget rejection,
  quota persistence, stale replies, sign changes, same-request coalescing,
  save failures, restart continuation, one-time care and opt-out. Tarot has no
  runtime, endpoint call, menu choice or asset integration in this slice.

### Horoscope verification

- Windows / Python 3.11.9: **1,776 tests pass in 245.153 seconds**, including
  sixteen new horoscope contract/lifecycle/playback tests and four native Tk
  acceptance tests with temporary saves. The existing buffered formats and wish
  catalogue remain covered; horoscope is explicitly outside social wish targets.
- Whole-repository Ruff passes. Strict Mypy passes all **264 source files**;
  repository-wide Pyright reports zero errors/warnings. The import-graph gate
  confirms an acyclic graph after separating immutable horoscope models from
  preparation. Relative documentation links and whitespace checks pass.
- Native visual inspection confirms the direct sign selector, expanded opt-in
  copy and the complete original footer below the speech text, without clipping.
  This verifies layout; personal reading-comfort feedback remains open.
- The single live sizing check is recorded above. Development did not use the
  normal user save, install dependencies, implement tarot, change assets/CI,
  commit, push or merge.
