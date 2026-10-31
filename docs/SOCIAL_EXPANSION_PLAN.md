# Sayings, daily horoscope and tarot expansion plan

> **Sprüche and shared bubble timing implemented. The AstroWay horoscope API
> prototype is replaced by the local held-book version with 96 authored entries.
> The approved book-reading reference governs Aiko's delivery.
> Earlier performance pilots rejected; hat extension and tarot deferred.**
> Initial documentation-only plan recorded on 2026-10-23 at checkout `f6ae2df`
> on `feature/social-optimization`. The owner later authorized the shared bubble
> times (including final second and punchline pause), followed by the Sprüche
> slice: German one-liners, quotations and their request/save/Credits boundaries.
> The owner subsequently authorized the daily horoscope API prototype, then
> corrected the local concept to Aiko reading a real held book. This replacement
> was subsequently authorized for implementation and verified local commits.
> No further asset generation, purchases, CI setup, push or merge is included.
> Existing parallel character work is preserved outside these commits.

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
| Rejected API prototype | AstroWay daily horoscope is discarded and must be fully replaced. Its delivered behavior below is retirement/migration evidence, not a retained online option or fallback. |
| Local horoscope replacement | Local calculation and 96 authored German book entries, with [confirmed reading reference](horoscope/book-reading-reference.de.md) and [module/migration plan](horoscope/LOCAL_HOROSCOPE_IMPLEMENTATION_PLAN.md). Aiko remains herself and may comment on the passage. The API mode is removed. |
| Book and later hat concept | One live book: place on the taskbar, pick up, open/read, close/put down. After the first complete reading and put-down it remains replayable for a fixed hour, then dissipates. Interruption does not exhaust it. Reuse the holding pose. Hat and its former gift-unlock requirement remain deferred; the floating-book design is superseded. |
| Tarot | Aiko explicitly plays the fortune-teller/card-reader role and presents the source's card meaning. |
| Address | Local book prose and Aiko's own speech use **du**. Source-preserving **Sie** was a property of the rejected horoscope API prototype and remains a separate consideration for any future sourced Tarot text. |
| Cost | Content acquisition and operation of these integrations must be free of provider charges. No API keys, accounts, paid fallback or subscriptions. |
| Reading time | Review actual bubble durations for Spruch, Witz, Kurioser Fakt and Plaudern together, including the new readings. |
| Later presentation | Card artwork, suitable gestures and subtle effects may extend the performance later. A crystal ball is explicitly outside the first step. |

The proposed rule-based Sie-to-du converter is withdrawn. No NLP package,
local language model, translation service or paid inference is part of this
scope. Authored framing is allowed; replacement authored jokes, quotations,
horoscopes or card meanings are not selected for the delivered API baseline.
The later [local horoscope draft](#local-horoscope-alternative-and-complete-scene-draft)
separately explores authored interpretations; it does not activate them as API
fallbacks. Existing Plaudern remains authored.

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

The existing online-source opt-in remains the boundary for online providers,
off by default. Disabling it prevents new network work and invalidates pending
online playback. The local book reading is independent of that opt-in.

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

**Rejected and superseded.** Full replacement of the AstroWay API prototype
is decided. Its previous request rules, source text, role switches and fetch
attempts are [archived as implementation history](horoscope/rejected-api-prototype.md),
not current target behavior. Use the local book concept and replacement plan
below. Existing code is removed during implementation; this documentation task
changes no runtime.

<a id="local-horoscope-alternative-and-complete-scene-draft"></a>

## Local horoscope replacement: held book and authored entries

Current planning authority, corrected on **2026-10-25** after content and
character review: Aiko uses a placed and picked-up book, reads its horoscope
and may comment while remaining herself. The approved book example replaces
the rejected performance scripts. The technical plan below specifies the local
replacement. Implementation was subsequently authorized and completed; its
current contracts are maintained in the linked module plan. The AstroWay API
prototype is removed completely, without a retained provider mode.

### Local calculation and authored interpretation

- Selected calculation library: **[Astronomy Engine (Python)](https://github.com/cosinekitty/astronomy/blob/master/source/python/README.md)**,
  under the [MIT license](https://github.com/cosinekitty/astronomy/blob/master/LICENSE).
  Version 2.1.19 is pinned; its copyright/license notice is shipped. No provider
  key, account, paid service, online translation or additional language model
  is part of this replacement. The library calculates astronomy; it does not
  supply horoscope prose or validate our interpretations.
- Implemented basis: geocentric tropical Sun/Moon longitude and lunar phase at
  local noon converted to UTC, with explicit zodiac and phase boundaries.
- Keep direct zodiac selection. In the proposed simplified solar-house scheme,
  the selected sign is the first house and subsequent signs supply relative
  thematic positions. Birth time, birthplace and a full natal chart are outside
  this draft.
- Moon position relative to the selected sign chooses the daily theme; lunar
  phase chooses its development direction. Sun position is calculated and saved
  as context; the current entries do not restrict selection by Sun position.
  These are playful interpretations of astrological symbolism, not scientific
  predictions. Select a coherent theme before selecting complete authored
  German passages; do not combine unrelated sentence fragments at random.
- Date and selected sign should determine a stable daily reading. Keep one
  resumable reading per day, the twelve-text-bubble ceiling and shared display
  times. A wholly local replacement would not need HTTP fetch attempts; the
  three-attempt rule is only a historical property of the rejected API code
  and is removed with that code at cutover.
- Author the local book text directly in **du**, separating book prose from
  Aiko's own voice. The old API text and source-wording rules are history,
  not a second live mode. Complete replacement of the prototype is decided;
  the separately authorized implementation now delivers that replacement.

### Planned text collection: 96 complete scene templates

Owner decision recorded on **2026-10-25**: plan a starting collection of
**96 complete scene templates shared by all twelve zodiac signs**. This is a
scope decision only; recording that scope did not authorize new readings,
pilot texts, catalogue files or runtime implementation. The owner subsequently
authorized twelve editorial pilots, rejected their direction, and approved one
new book-reading reference. The subsequently authorized runtime now contains
all 96 entries, with explicit sign applicability and four-stage Aiko comments.

| Dimension | Planned count | Purpose |
| --- | --- | --- |
| Theme families | 12 | The solar-house-inspired families and their editorial boundaries are defined below. |
| Development directions per theme | 4 | Begin, develop, reflect and conclude, with the agreed lunar-cycle intervals below. |
| Complete variants per theme/direction pair | 2 | Distinct complete book entries, with separate optional Aiko comments and suitable holding/emote presentation. |
| Total starting target | **96** | **12 × 4 × 2**, shared across the signs rather than a separate 96-entry collection for each sign. |

#### Twelve theme families

Owner decision recorded on **2026-10-25**. These are Aiko's accessible editorial
adaptations of traditional [house symbolism](https://cafeastrology.com/articles/housesofthehoroscope.html),
not a complete natal-chart interpretation. The German names identify the planned
families; they are not new spoken readings or runtime catalogue entries.

| Solar house | Theme family | Editorial scope |
| --- | --- | --- |
| 1 | **Selbstbild und Auftreten** | Personal attitude, willingness to be seen and first impressions; focus on how someone presents themselves. |
| 2 | **Eigene Mittel und Werte** | Time, attention, possessions and what matters personally; choosing and appreciating resources. |
| 3 | **Austausch und kleine Entdeckungen** | Questions, listening, explaining and learning something through everyday exchange. |
| 4 | **Vertrautheit und Geborgenheit** | Familiar places and rituals, settling in and a sense of home. |
| 5 | **Spielfreude und Kreativität** | Experimentation, imagination, hobbies and enjoyment of an idea; room for Aiko's playfulness. |
| 6 | **Alltag und hilfreiche Gewohnheiten** | Small routines, order, practical help and manageable improvements. |
| 7 | **Begegnung und Zusammenspiel** | A concrete counterpart: invitations, listening, coordination and doing something as a pair. |
| 8 | **Veränderung und Vertrauen** | Handling novelty or uncertainty, sharing responsibility and allowing familiar things to change. |
| 9 | **Neugier und neue Perspektiven** | Broadening a familiar viewpoint, encountering unfamiliar ideas and discovering connections. |
| 10 | **Ziele und sichtbarer Fortschritt** | Working toward something, noticing a milestone, completing or showing an achievement. |
| 11 | **Freundschaft und gemeinsame Ideen** | Belonging, shared interests and plans that grow through other people. |
| 12 | **Ruhe und innere Gedankenwelt** | Retreat, daydreaming, processing impressions and giving thoughts room. |

Keep these boundaries visible during later editorial review:

- **3 versus 9:** immediate exchange and everyday learning versus a broader
  perspective or unfamiliar conceptual territory.
- **4 versus 12:** security in familiar surroundings versus inner quiet and
  retreat.
- **6 versus 10:** a functioning everyday routine versus a longer-term goal
  or visible milestone.
- **7 versus 11:** a concrete one-to-one encounter versus friendship,
  belonging and shared interests.

#### Four development directions and lunar phases

Use four consecutive quarters of the calculated lunar phase angle. Astronomy
Engine defines 0 degrees as new Moon, 90 as first quarter, 180 as full Moon
and 270 as third/last quarter; see its
[phase reference](https://github.com/cosinekitty/astronomy/blob/master/source/python/README.md#MoonPhase).
The interpretations below are our editorial choices, not meanings supplied by
the calculation library.

| Direction | Editorial meaning | Lunar-cycle interval | Phase-angle interval |
| --- | --- | --- | --- |
| **Beginnen** | Notice a possibility, choose a small starting point or allow something to emerge. | New Moon to first quarter | 0 degrees inclusive to 90 exclusive |
| **Weiterentwickeln** | Build on something, try it out, develop it and keep going. | First quarter to full Moon | 90 degrees inclusive to 180 exclusive |
| **Betrachten** | Notice what has emerged, put it in perspective, appreciate it or share observations. | Full Moon to last quarter | 180 degrees inclusive to 270 exclusive |
| **Abschließen** | Round something off, simplify, let it rest or make room. | Last quarter to the next new Moon | 270 degrees inclusive to 360 exclusive |

At a boundary, use the direction whose interval starts there; a new cycle
wraps to 0 degrees. These are phase-angle quarters, not fixed seven-day blocks
or equal illumination-percentage ranges. Membership in an interval does not
mean the exact named Moon event happens on that local calendar day.

Directions describe what happens **within** a theme. Beginnen can concern a
small playful occasion; Abschließen need not imply a farewell. Family 8 is the
subject of change/trust, not a synonym for Abschließen: it can take any of the
four directions.

#### Selection rules for the local replacement

1. Use the existing directly selected zodiac sign as the first solar house.
   Count subsequent signs in zodiac order; the Moon's sign relative to that
   starting point selects the corresponding **leading theme family**.
2. Use the calculated lunar phase at the fixed daily reference time to select
   **one development direction** from the intervals above.
3. Use the Sun's relative position as an optional compatible background.
   It must not introduce a second compulsory theme or multiply the catalogue
   into every Sun-house/Moon-house/phase combination.
4. The Moon's sign may color presentation. It does not add another mandatory
   collection dimension or justify an interpretation that contradicts the
   selected theme and direction.
5. Select one of the two complete variants for the resulting theme/direction
   pair, respecting the later repetition policy. Actual astronomical facts may
   appear in complete sentences with validated substitutions. Keep the scene
   coherent; do not assemble unrelated sentence fragments or change facts to
   fit a preferred script.
6. Keep the chosen reading stable for its local date and resumable after an
   interruption. Eligibility limits take precedence over merely avoiding a
   recent variant. Storage and the exact stable-selection mechanism remain
   future implementation work.

This preserves **12 themes × 4 directions × 2 variants = 96** complete templates
shared across the signs. The twelve pilot scenes should exercise different
development directions across all four, as well as different scene arcs, before
the expansion to 48 and 96 templates. These are our own simplified editorial
rules, not a researched industry standard or proof of content quality. Exact
eligibility for the approved Stier reference remains to be reviewed; the old
nine-bubble performance is rejected, not an exception to the selection rules.

#### Complete variants and staged editorial work

A second variant must offer a genuinely different complete book entry, not
merely replace an interjection, a sign name or an emote. Aiko's optional comment
must arise from the actual passage; she stays herself throughout. The book
text must carry the reading even when no personal comment is selected. Keep full-scene coherence rather than
random sentence-fragment assembly. Friendship-sensitive personal passages may
have targeted alternatives; four full copies of every scene are not assumed.

Plan the editorial work in cumulative stages:

| Stage | Total complete templates at that stage | Coverage |
| --- | --- | --- |
| Pilot | **12** | One complete book reading per theme family, starting from the confirmed style and optional passage-specific Aiko reactions. |
| Basic coverage | **48** | Expand the pilots to one complete scene for each of the twelve themes and four development directions. |
| Starting target | **96** | Add a second independent full variant for every theme/direction pair. |

These are cumulative totals, not 12 + 48 + 96 separate scenes. The previous
twelve drafts are rejected and do not satisfy the pilot milestone. One new
Stier reading is stylistically approved, but its eligibility still needs review;
the rest of the pilot collection remains to be written. No new readings are
created by this documentation correction.

At an average of seven to nine text bubbles, 96 templates imply roughly
**670–860 text bubbles**, plus staging/emote instructions and any targeted
friendship alternatives. Seven to nine is a working estimate, not a new fixed
length; retain the twelve-bubble maximum and shared timing rules.

Before later publication, assess repetition with simulated longer daily
sequences for all twelve signs. Prefer other eligible variants before repeating
a scene, while keeping each day's selected reading stable and resumable.
Ninety-six entries do not guarantee ninety-six different consecutive days:
sky/theme eligibility narrows the available pool. Do not promise a repetition
interval before that evaluation. No simulation is run as part of this update.

### Confirmed book-reading concept and content reference

The owner corrected the concept on **2026-10-25** and approved the
**[Stier book-reading reference](horoscope/book-reading-reference.de.md)**.
That reference supersedes the earlier role-entry/role-exit scenes.

- The player places a real book on the taskbar by drag-and-drop. Aiko picks
  it up, opens and reads it, then closes and puts it down. After the first completed
  reading and put-down it remains for a fixed hour, then dissipates. Manual
  handover replays the same frozen text from the start without another care
  credit or deadline extension. Next day uses a newly placed book.
  Interruption before completion does not exhaust the book. The existing
  holding pose is reused; the book is a World object, not a floating prop.
- Aiko remains Aiko throughout. The book supplies a complete, sign-specific
  horoscope; her own framing and optional response remain clearly separate.
  Do not say she becomes a fortune-teller and then becomes Aiko again.
- Write the book entry first: a personal daily situation, disposition,
  development or tension, followed where appropriate by an impulse. Do not
  announce internal theme labels, narrate selection rules or stretch one
  generic coaching recommendation across many bubbles.
- Add a personal comment only when that passage gives Aiko something to react
  to. Current reading is already a real occasion; do not invent shared creative
  projects, free conversation or a mandatory connection to a minigame.
- Friendship **1–2 / 3–5 / 6–8 / 9–10** affects her own openness and address,
  not the book text. Current emotional state remains a separate condition.
  There is no mandatory pair of replacement bubbles or compulsory role break.
- Reuse the existing text/emote surface and display times. Holding the book
  continues through text and emote beats. Do not replace that pose with a
  free-hand gesture that visually drops the book. The approved
  [four-state V1 asset pack](HOROSCOPE_BOOK_ASSETS.md) exists; fitting its grip
  to the character pose and runtime registration remain integration work.

### Technical replacement and migration plan

The **[local horoscope implementation plan](horoscope/LOCAL_HOROSCOPE_IMPLEMENTATION_PLAN.md)**
records the audited reuse/retirement matrix, implemented module boundaries,
frozen daily reading and cue progress, legacy-save cases, persistent World-book
lifecycle, online-provider separation and staged validation.
Its [concrete module and catalogue contracts](horoscope/MODULE_AND_CATALOGUE_CONTRACTS.md)
name the objects/functions and divide book prose, Aiko dialogue,
item assets, UI messages and private SQLite snapshots without duplicating owners.

The current prototype's day/sign settings, reading rules, once-only care path,
speech player, timing and atomic persistence are foundations to reuse. Its
mandatory AstroWay footer, nonzero-attempt storage constraints, live HTTP path
and role-reentry prefix require deliberate replacement. Local text must not
be stored as a fake provider response. Shared online joke/quotation/fact
components remain in service. The rejected API prototype is not kept as an
online option or fallback. Any legacy-save support performs one-way data conversion, without API retrieval
or playback. The local replacement implements this separation.

### Twelve editorial pilot drafts (rejected)

The previous **[twelve pilot drafts](horoscope/pilot-scenes.de.md)** are retained
for comparison and explicitly rejected as a starting catalogue. Their static
length checks did not constitute editorial approval. They overemphasized Aiko's
own performance and sometimes invented creative collaboration with the player.
The approved Stier entry remains the style reference. The replacement
`pilot-book-entries.de.json` contains the separately authored and reviewed 96
complete entries; the rejected drafts are not counted toward that coverage.

The older nine-bubble scene and full hat/gift/floating-book concept are
[preserved separately as superseded history](horoscope/superseded-scenes-and-hat.md).
They must not be used as current production instructions.

## Planned horoscope gift and VN presentation

**Deferred/superseded for the first book version.** The current concept uses
only a placed, picked-up and held book. A hat is not a prerequisite for this
version; its former gift-unlock rule is not carried into this delivery plan.
A future hat/gift feature needs a separate decision. Its historical perspectives
and production notes remain in the archive above. The book does not float,
and page-turn/particle effects are optional later work.

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

The local horoscope uses its independent book coordinator and the existing
atomic session save for frozen text/cues, current progress, admission and expiry.
Admission and care persist together before display; each cue transition persists
before the next cue is shown. A failed write prevents dispatch or stops playback.
No footer, HTTP worker, provider retry counter, additional completion reward or
horoscope wish family is introduced. The former API behavior below is historical.

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
