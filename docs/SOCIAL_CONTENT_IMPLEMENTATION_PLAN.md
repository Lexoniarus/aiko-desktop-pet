# Jokes and facts implementation plan

> **Implementation authorized; delivery in progress.** Recorded on 2026-10-19 on
> `feature/social-optimization`, against checkout `7049869`. The owner selected
> jokes and facts as the next social-content features and requested this plan
> in the repository documentation. This records the discussed menu, effects and
> delivery boundaries. The owner subsequently authorized incremental
> implementation on the existing branch, with small commits, targeted tests
> during delivery and the complete suite only at the end. Do not merge.

Implementation starts from `e6aad99`. Delivery and actual validation are recorded
below; the initial planning baseline remains historical.

The first delivery adds three API-content choices alongside existing authored
conversation in a shared **Unterhalten** menu. JokeAPI single-part content,
JokeAPI two-part jokes and German facts have separate selections and separate
two-item preparation buffers. All new entertainment content comes exclusively
from the APIs. There is no authored local catalogue or local content fallback.
Existing **Plaudern** remains the existing authored conversation.

Related references: [social and entertainment concept](SOCIAL_ENTERTAINMENT_CONCEPT.md),
[friendship rules](FRIENDSHIP_SYSTEM.md), [need and mood effects](FUN_MOOD_SYSTEM.md),
[application boundaries](INTEGRATION_ARCHITECTURE.md) and
[dialogue resources and saves](DATA_AND_SAVES.md).

## Unterhalten menu

Replace the toolbar label **Reden** with **Unterhalten**. Clicking it opens one
small selection window in the existing Aiko skin, following the food-selection
window's placement and lifecycle conventions.

| German choice | Behavior |
| --- | --- |
| **Plaudern** | Existing authored, situation-dependent conversation |
| **Spruch erzählen** | German JokeAPI `type=single` content |
| **Witz erzählen** | German JokeAPI `type=twopart` joke with separate setup and punchline |
| **Kurioser Fakt** | One German API fact with a short introduction |

Single and two-part content stay separate from request through buffer, selection
and playback. `single` describes the provider's one-field format, which can also
contain narrative jokes or dialogue. The **Spruch erzählen** label does not
establish a different API genre; do not manually rewrite or reclassify the
provider's content into a self-authored sayings catalogue.

- Place the menu near the toolbar and keep it within screen bounds.
- Reopening focuses the existing window rather than creating another one.
- Closing the menu or pressing Escape cancels selection without care effects.
- Include the menu in existing window stacking, focus, hover and shutdown handling.
- Preserve current interaction restrictions during sleep, games and conversation
  playback. Reading clicks still advance the current story; they do not start
  another conversation. A silent pause remains part of protected playback.

## German content and presentation

Use these APIs as the sole sources for the three new content choices:

| Category | Planned provider | Request and preparation |
| --- | --- | --- |
| Single | [JokeAPI](https://jokeapi.dev/) | German, Safe Mode, excluded content flags and `type=single`; read `joke` |
| Two Parts | [JokeAPI](https://jokeapi.dev/) | German, Safe Mode, excluded content flags and `type=twopart`; read `setup` and `delivery` separately |
| Facts | [Random Useless Facts](https://uselessfacts.jsph.pl/) | Current v2 random-fact endpoint with `language=de`; preserve source metadata |

Provider documentation describes these language and response options. Provider
use, attribution requirements and content reuse terms must be checked before
adapter activation. API availability does not establish factual correctness.

Before implementation, inspect both APIs' actual response formats. Five separate
successful live responses per provider were checked on 2026-10-19 in the planning
chat: two single-part and three two-part JokeAPI items, plus five facts. JokeAPI
used `lang`, numeric `id`, flags and either `joke` or `setup`/`delivery`; facts used
string `id`, `text`, `source`, `source_url`, `language` and `permalink`. One fact
was already truncated by its provider. Valid JSON alone is not sufficient for
ready content. Response examples stay in the chat, not in a runtime catalogue.

Add one persisted setting, **Onlinequellen für Witze und Fakten verwenden**,
defaulting to off. It belongs to the existing `PetSettings` owner and normal
settings persistence. Existing saves without the setting load with online
sources disabled. With the setting off, the three API choices are unavailable
with a brief settings hint; **Plaudern** remains available. Enabling sources
starts warming. Do not provide substitute authored content when sources are off.

## Prepared content buffers

Keep **two Single items, two Two Parts items and two facts** ready in memory
while online sources are enabled: three independent buffers, six ready slots
in total. Ready means that retrieval,
validation and conversion to the complete playback sequence have finished;
raw downloaded JSON does not occupy a ready slot.

- Fetch and prepare each item individually. Do not use a multi-item API request
  or wait for a whole category batch before making its first item available.
- Use at most one online fetch at a time across all three categories. Fill the six
  slots through successive individual requests, accounting for queued and
  in-flight work so a category cannot exceed its target of two ready items.
- Start warming only after online sources have been explicitly enabled, including
  startup with an already saved opt-in. Background warming itself grants no
  care effect, qualified personal contact or reward.
- When the user selects a category, take a ready item for immediate playback
  acceptance and refill the consumed slot individually in the background.
- If the selected category is empty, prioritize that user's request and reuse
  matching in-flight work instead of launching a duplicate fetch. Deliver the
  first valid prepared item without waiting for the buffer to reach two.
- Keep pending work and ready content under the same application coordinator.
  Disabling online sources clears its online buffers and invalidates pending
  work. External content remains session-local, without a persistent cache.

## Reaction presentation

Use the existing `Reaction`/`Cue` representation and `ReactionPlayer`:

- Single content uses the provider's `joke` text, segmented where necessary,
  with a short introduction where appropriate. Do not invent a setup/punchline
  split that the response does not contain.
- Two Parts content uses a short introduction where appropriate, then `setup`,
  a deliberate pause and `delivery` as the punchline.
- Every fact has a short introduction before its API `text`. Prepare the
  introduction and fact together before marking the item ready.
- Presentation framing stays quiet, dry and curious. Its scope is short
  introductions and the agreed holding line, not self-authored entertainment
  content, additional punchlines, invented facts or substitute stories. It must
  not change the provider's meaning or invent a personal research history.
- Keep the existing maximum of **125 characters per text beat** and **five text
  beats per story**, including framing. Split at sentence or word boundaries.
- Reject content that cannot fit completely. Never truncate a punchline or fact
  merely to satisfy the display limit. Reject provider-truncated items as well.
  Rejection never activates a local replacement or another content category.
- Prepare the entire sequence before playback. No retrieval or translation
  happens between its bubbles.

## Shared social and relationship effects

The planned initial balance treats all four choices as conversation variants.
Content choice does not create another care or friendship reward category.

| Effect per accepted conversation | Plaudern | Single | Two Parts | Fact |
| --- | --- | --- | --- | --- |
| Social | +26 | +26 | +26 | +26 |
| Energy | -1 | -1 | -1 | -1 |
| Direct fun gain | 0 | 0 | 0 | 0 |
| Qualified personal contact | Yes | Yes | Yes | Yes |
| Friendship category | Shared `talk` | Shared `talk` | Shared `talk` | Shared `talk` |

Use the current care balance values through their existing owner rather than
copying constants into providers or UI code. Need values retain their normal
0–100 clamping. A joke-specific fun bonus would be a separate balance change.

All variants share the existing conversation friendship rules:

- Nominal `talk` friendship gain is 1.0, subject to the existing limits.
- Same-type eligibility is once per two real hours, shared across all four
  choices. Switching category does not open another reward interval.
- If pre-care social is above 80, apply the existing 0.25 reward multiplier.
- Retain the common cap of 0.75 friendship per rolling two hours and five per
  rolling 24 hours, including rewards from other eligible care actions.
- Exhausted friendship credit does not prevent need care or qualified contact.
- Preserve the existing saved reward history and restart behavior.

## Acceptance and once-only effects

Use this lifecycle for each selection:

1. Open the menu: no care effect or qualified care contact.
2. Select a category and take a prepared item, or wait for its individual
   preparation: still no care effect or qualified care contact.
3. If no item is ready, Aiko says **Ich muss kurz überlegen** once and waits
   until a valid item is ready. This holding line grants no conversation credit.
   The complete item must be validated and prepared before its content begins.
4. On the UI owner thread, recheck the request's validity and current interaction
   permission, using the existing foreground and World coordination.
5. When playback is accepted to start, commit the shared conversation transition
   once and start the prepared sequence through the existing presenter/player.

This preserves the current conversation principle: acceptance at playback start
counts, rather than receipt of the last bubble. The introduction is not played
as a separate rewarded interaction. Reading clicks, the punchline and completion
callbacks never award additional effects. A later playback interruption does not
undo or repeat an already committed conversation.

The holding line, loading indicators and error messages never count as
conversation. If no valid item can be prepared or interaction is blocked before
acceptance, there is no care effect. Failure never falls back to **Plaudern**
or other authored entertainment.

## Loading failures and repetition

- Allow at most one active online fetch. Run HTTP work outside the Tk owner
  thread; workers never call Tk or mutate pet state. User selection joins or
  prioritizes the shared warming work rather than adding another request.
- While a selected category has no ready item, display the holding line through
  the existing speech surface and keep a cancellation control available in the
  menu. Coordinate waiting and its transition to content through the existing
  attention and playback owners; do not add another bubble or player.
- Wait for content readiness without a fixed four-second presentation deadline.
  The holding line is not repeated. HTTP operations still need finite network
  timeouts. A failed fetch ends the waiting attempt, clears the holding
  presentation and displays an honest brief failure with a retry option.
  Do not retry indefinitely or deliver authored replacement content.
- Reject invalid, wrong-language, unsuitable, incomplete or oversized responses.
  They do not fill a ready slot. If no valid ready item in the selected category
  can satisfy the waiting selection, report the failed attempt without care
  effects. Provider error text is never spoken as entertainment content.
- A background fetch failure leaves its target slot unfilled and preserves
  other valid ready items. Do not continuously refetch failed preparation.
  A user retry starts or joins a new individual preparation attempt.
- Cancellation, another care action, shutdown or disabling online sources
  invalidates the pending user's selection and clears its holding presentation.
  Late results must not start playback or award care. Background warming may
  continue after a selection is cancelled while online sources remain enabled;
  shutdown and disabling online sources also invalidate the warming work.
  Ending a selection with an error also invalidates its playback entitlement,
  so a later result cannot unexpectedly start a conversation.
- Track provider IDs or text fingerprints during the session to avoid repeated
  delivered content and duplicate items in ready or in-flight slots. Keep the
  Single and Two Parts buffers distinct. Record an item as delivered only when
  its playback is accepted.
- Do not persist external content in this first delivery. Keep source and
  attribution metadata attached to prepared content rather than losing it when
  converting to playback beats.

## Application ownership

One application coordinator owns the pending selection, warming work and the
three prepared-content buffers. Small infrastructure adapters fetch provider
data; a shared preparation path
validates it and constructs the existing immutable reaction sequence.

Introduce a typed conversation variant at the application boundary. The domain
care action and friendship category remain `talk`. The care controller accepts
the selected prepared conversation through its application contract and does
not additionally select or present an ordinary talk response for the same
action. Capture current pre-care context when committing, not when a background
request began.

`PetState` remains the only owner applying need and relationship changes.
Settings remain under `PetSettings`; the UI supplies selections and displays
results. Reuse the existing attention, safe interruption, presentation and
persistence paths. There is no second bubble player, need model or mutable
settings store. The initial implementation is intended to use Python's standard
library without adding a translation runtime or provider wrapper dependency.

## Delivery and acceptance

| Stage | Scope | Acceptance |
| --- | --- | --- |
| A: menu and content contracts | Unterhalten with four choices, separate Single/Two Parts/fact contracts and existing playback preparation | Single and Two Parts stay distinct; every fact includes its introduction; deterministic provider fixtures exercise preparation without creating a runtime content catalogue |
| B: shared care effects | Typed conversation variant, shared `talk` transition and friendship eligibility | Exactly one transition; opening/cancelling the menu grants nothing; switching variants does not bypass limits |
| C: online content | Shared application coordinator, two provider adapters, opt-in, three two-item buffers, individual warming, waiting line and invalidation | Ready content starts immediately; an empty category waits for its first ready item; failures are reported without replacement content; cancelled or stale replies never start playback |
| D: integration and verification | Settings saves, window behavior, attention, shutdown and maintained documentation | Relevant automated checks and isolated-save Windows smoke acceptance pass |

## Commit and test discipline

Deliver the subsequently authorized implementation in small, cohesive, readable
commits. Each commit has one clear purpose and a descriptive English message;
include its directly related tests and documentation. Review the staged diff
and keep unrelated local changes out of it. Split stages into smaller commits
where that improves reviewability, while keeping each committed change coherent.

During implementation, run only the targeted tests for the behavior and
contracts affected by the current change. Include relevant adjacent owners when
their contracts change, and complete required static checks for that scope.
Validate each increment before committing. Do not run the complete suite after
each increment or commit.

Run the full test suite only at the end, in stage D after the feature is
integrated, alongside the final required static checks. Record the focused
checks separately from the final complete run and Windows acceptance. If final
verification exposes a failure, fix and verify it with targeted tests, then
repeat the final complete check when justified by that correction. The owner
has authorized implementation and local commits; merging remains unauthorized.

Ordinary tests use fixed provider JSON fixtures and controlled worker/clock
results. Cover normalization, language and length rejection, once-only effects,
provider truncation, cancellation, late responses, opt-in persistence, shared
reward limits and restart behavior. Check each category's two-item target,
individual sequential fetches, refill after consumption, selection priority,
reuse of in-flight work, Single/Two Parts separation and mandatory fact framing.
Verify that warming, the holding line and failures never award care and that
errors never select authored replacement content. Verify protected pauses and
reading clicks through the existing playback owners. Test fixtures are not a
runtime fallback. Live provider checks are separate from deterministic CI; run
the repository's required checks for the eventual code change.

Windows acceptance uses an isolated save and checks menu placement near screen
edges, focus/hover/stacking, immediate playback from a ready buffer, the holding
line and its replacement when content becomes ready, loading responsiveness,
failure behavior with no connection and an empty buffer, cancellation, separate
Single/Two Parts playback, fact introductions, sequential setup/punchline
delivery and shutdown with a request pending. Already prepared API items may
still be used while a connection is unavailable; there is no authored offline
entertainment fallback.

Horoscopes, translation/model installation, spontaneous online stories, extensive
category/frequency settings and persistent external-content caching are outside
this first delivery.

## Delivery record

- Planning baseline preserved before implementation; stages A–D pending.
