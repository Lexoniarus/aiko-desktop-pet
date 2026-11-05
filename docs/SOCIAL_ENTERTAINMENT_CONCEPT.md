# Social and entertainment concept

> **Preserved product concept, not an implementation report.** Recorded on
> 2026-10-19 from the owner's supplied German concept, originally based on
> `1753266` (PR #9, 2026-10-15). The implementation comparison below was checked
> against `fd8414a` (main after PR #10). Recording this concept does not select
> the next feature, install dependencies or approve the entire delivery order.

This preserves the substance of **“Aiko – Social & Entertainment: Gesamtkonzept
auf Basis des aktuellen Main”** in the repository's English technical-document
format. Provider names, translation direction, content ideas, settings and the
original staged proposal are retained. Historical implementation assumptions
are distinguished from the current application.

Related references: [current architecture](ARCHITECTURE.md),
[dialogue resources and saves](DATA_AND_SAVES.md),
[minigame candidates](MINIGAME_CANDIDATES.md),
[adaptive cursor concept](ADAPTIVE_CURSOR_CONCEPT.md) and
[integration boundaries](INTEGRATION_ARCHITECTURE.md).

The owner selected jokes and facts for the next social-content delivery. The
[jokes and facts implementation plan](SOCIAL_CONTENT_IMPLEMENTATION_PLAN.md)
records the **Unterhalten** menu, shared conversation effects,
separate Single and Two Parts choices, fact introductions and two individually
prepared API items per category. The selected delivery uses API entertainment
content exclusively, without an authored local catalogue or local fallback;
existing **Plaudern** remains available. These later decisions supersede earlier
fallback assumptions for the new choices; the broader concept below remains
preserved. Implementation was subsequently authorized and delivered on the
feature branch; [current social behavior](SOCIAL_CONTENT.md) describes the
runtime, and the plan records actual verification. Broader translation,
horoscope and spontaneous-content ideas below remain future work.

The later [selected social expansion plan](SOCIAL_EXPANSION_PLAN.md) supersedes
this exploratory source list for selected features. Sprüche with genuine
one-liners/quotations and shared bubble timing are implemented. The horoscope
API prototype is **rejected and fully replaced**, without an online
alternative or fallback. Its [local book replacement plan](horoscope/LOCAL_HOROSCOPE_IMPLEMENTATION_PLAN.md)
and [approved content reference](horoscope/book-reading-reference.de.md) now
govern that work: a placed and picked-up book supplies the text, Aiko remains
herself and may comment. Hat gating and a floating-book performance are not
part of its first version. The local replacement contains 96 complete readings
with a persistent physical book and a fixed one-hour replay deadline.
Tarot remains separate future work; older source/role/translation suggestions
below are historical possibilities, not current implementation instructions.

The [bubble dialogue review workbook](DIALOGUE_REVIEW.md) records complete
existing sequences and their conditions for individual editorial review before
any wording changes. Its review status and proposals do not change runtime copy.

The later [friendship balance proposal](FRIENDSHIP_BALANCE_PROPOSAL.md) records
candidate relationship gains/losses and real-time absence consequences. It is
separate from this preserved content-provider concept and is not implemented.

The [mood balance proposal](MOOD_BALANCE_PROPOSAL.md) separately records need
contributions, critical-deficit penalties and real-time decline/recovery timings.
It also preserves discussion values only, without implementing Moodlets or
changing runtime balance.

The [need balance and daily care proposal](NEEDS_BALANCE_PROPOSAL.md) connects
care effects and real-time need rates to an example day with normal sleep.
The friendship proposal also records progressive upkeep and sustained neglect;
these remain unimplemented balance candidates, separate from content providers.

## Product direction

Aiko should offer small, varied moments of entertainment on her own initiative,
without losing her quiet, dry, curious personality or repeatedly interrupting
the user. Authored German lines and externally sourced content should enter a
common preparation and selection path.

The supplied concept establishes these product constraints:

- Social content is free to use, with no required paid AI APIs.
- All spoken output is German. English content is translated locally before
  it becomes available for selection; there is no English display fallback.
- The application remains useful offline with authored German content and
  previously prepared content whose reuse and caching terms permit it.
- Aiko uses her existing speech surface, reaction presentation and attention
  coordination. Content providers do not introduce another bubble or player.
- Online sources and local model installation are explicit user choices.
  Ordinary runtime must not silently download a model.
- Failed retrieval, translation or validation skips that content and allows a
  suitable German fallback. Missing translation support does not break the base
  application.

These constraints are more specific than the broad preferences in the minigame
catalogue. They apply to this proposed social-content pipeline; the catalogue
does not replace them.

## Current main comparison

| Area | Checked state at `fd8414a` | Consequence for this concept |
| --- | --- | --- |
| Authored dialogue | Catalogue v2, context and relationship filters, session rotation and 48 authored talk stories exist | Reuse existing selection and voice rules |
| Sequential presentation | `Reaction` contains text, emote and pause beats; `ReactionPlayer` plays them sequentially | The original proposal to add a separate `play_steps()` API is superseded |
| Playback lifecycle | Completion/cancellation, stale-timer invalidation, reading clicks and protection during blank pauses exist | Extend these contracts for prepared content rather than building another player |
| Content size | Text beats have 1–125 characters; a story has at most five text beats | Longer external content needs a deliberate preparation/segmentation policy |
| Attention | Spontaneous stories, quiet periods and protected interactions exist | Reuse the existing attention and focus owners |
| External social providers | No implemented joke/fact/trivia content pipeline | Provider adapters and preparation remain future work |
| Local translation | No CTranslate2/OPUS-MT integration | Model installation, tokenization and workers remain future work |
| Prepared-content storage | No persistent social-content/translation cache | Cache ownership, format and retention remain to be designed |
| Settings | Existing behavior/display settings include spontaneous speech | Category, online-source and translator controls remain future work |
| Minigames | Rock–Paper–Scissors and a game-neutral experience adapter exist | Interactive quiz logic is separate from content supply |

The original paper described 417 dialogue entries, 120 follow-up entries and
767 collected tests with seven skips under Python 3.11/3.13 at its older
baseline. It also reported green CI and Windows checks. Those are historical
claims from the supplied paper, not freshly verified counts or evidence for a
new commit. Current ownership and delivery evidence belong in the maintained
guides.

## Shared content pipeline

The conceptual flow is:

1. Read authored/local content or fetch an explicitly enabled provider.
2. Preserve source ID, original language, category and attribution/reuse data.
3. Validate German content directly; translate English content locally first.
4. Validate the prepared German result, including suitability for its content
   type, and cache it only where the source terms allow.
5. Select eligible content using situation, mood, category settings, quiet
   periods and repetition history.
6. Present through the existing reaction player and speech presenter, or pass
   quiz content to its separately owned interactive game session.

The original conceptual names were `SocialStory` and `StoryStep`. They express
a source-aware item with an ordered sequence, timing, pauses, optional emotes
and an appropriate animation. They do not require duplicate representations of
the current immutable `Reaction`/`Cue` playback model. Source metadata and
preparation still need an explicit owner outside the renderer.

### German-only availability

An English provider item is unavailable until translation and validation have
succeeded. A missing model, failed translation or unacceptable result must not
cause raw English text to reach Aiko's bubble.

For quizzes, translate the question and all answer choices consistently while
preserving correct-answer identity. Already written trivia questions and
metadata used to construct questions are distinct inputs: neither translation
nor an API adapter alone establishes factual correctness or good distractors.
Translation quality, especially for wordplay, requires separate evaluation.

### Proposed local translator

The supplied paper explicitly selects **CTranslate2 with
`Helsinki-NLP/opus-mt-en-de`**, running locally on the CPU. This preserves that
design choice; recording it does not install or freshly validate the runtime.

- Convert the model once during development/setup, then use the prepared model
  with its matching tokenizer. Do not reconvert or reload it per text.
- Run retrieval and inference outside the Tk owner thread. Prepare content
  before presentation rather than translating while a bubble is displayed.
- Keep the inference runtime behind a separate integration boundary.
- Associate cached translations with the model/version that produced them.
- The base installation works without the model. English social providers
  become eligible only after local translation is configured.
- Download the model during installation or explicit activation.
- Check distribution and attribution requirements for the runtime, tokenizer
  and model before bundling them.

The original paper cited CTranslate2 4.8.3, OPUS-MT/Marian conversion support,
Windows wheels for Python 3.11 and 3.13, and a CC-BY-4.0 model attribution
requirement. These are preserved historical research claims, not a current
compatibility or licensing certification. Verify them against official sources
before adopting or pinning dependencies.

## Content sources and original relative effort

The supplied scale is **1/5 to 5/5**, a rough comparison rather than measured
development time. English-source estimates assume the translator is already
installed. The shared infrastructure is additional work, so a small adapter
does not describe the total cost of the first complete feature.

| Original effort | Content/source candidates | Main work identified in the concept |
| --- | --- | --- |
| 1/5 | Authored German sayings, compliments, teasing and playful fortunes | Local JSON, existing selection and situation filters |
| 1/5 | German `pyjokes` | Local library adapter; no HTTP retrieval |
| 2/5 | German JokeAPI | Structured setup and punchline, retrieval and filtering |
| 2/5 | Random Useless Facts | German facts and simple structured responses |
| 2/5 | Redewörter and a quotation service | German text, attribution and content filtering; exact quotation service unspecified |
| 2/5 | `holidays` and calendar remarks | Local date rules and existing time context |
| 3/5 | CTranslate2 foundation | Model, tokenizer, installation, worker and cache |
| 3/5 | Advice Slip, Affirmations, Bored API and Cat Facts | Local translation, source adapters and content filters |
| 3/5 | ZenQuotes and English compliments | Local translation and attribution; exact compliment source unspecified |
| 3/5 | AstroWay horoscopes and daily tarot | Sections, date, zodiac sign and source terms |
| 4/5 | English joke APIs | Wordplay may fail even with a successful literal translation |
| 4/5 | Free Horoscope API | Translate and segment longer text |
| 4/5 | Riddles and Open Trivia DB | User input, answer evaluation and translation validation |
| 4/5 | Wikimedia “On this day” | Reliable selection, source preservation and short German narration |
| 5/5 | Kerykeion astrology | Calculations are not finished dialogue; licensing and text preparation |

The original paper keeps AstroWay conditional on checking desktop-use terms
and excludes Sigastra under the terms known at that time. This does not claim
that those terms, provider availability, language support or free tiers are
unchanged. Free retrieval does not automatically permit caching, modification
or redistribution. The supplied paper does not contain complete endpoint and
license records for every named source.

## Story presentation and interruption

The intended experience is a staged delivery rather than concatenated strings.
For example, a joke can have a short introduction, a setup, a deliberate pause,
a punchline and an optional dry remark/emote. Illustrative German copy from the
original concept is:

1. “Ich hab da einen Witz für dich!”
2. “Warum können Geister so schlecht lügen?”
3. A deliberate pause before “Weil man durch sie hindurchsehen kann!”
4. Optional emote and “...Okay, der war ziemlich flach.”

This is an example, not newly approved runtime dialogue.

The entire story owns its playback interval, including invisible pauses.
Deliberate user interactions may interrupt; incidental idle commentary must not
insert itself between setup and punchline. Current main already supplies these
basic sequence/lifecycle rules. Prepared content must honor them and the current
length limits. The original description of overlapping first/follow-up strings
and the need to create a general sequential player is historical.

## Settings and social initiative

The proposed Social & Entertainment section in the existing settings window
contains:

- Content categories: jokes, funny sayings, curious facts, compliments,
  horoscopes/tarot and riddles/quiz.
- Frequency choices: rare, occasional and frequent.
- An explicit opt-in for free online content sources.
- Local translation activation and visible installation/readiness state.
- Global quiet time, category cooldowns and a limit on spontaneous stories.

The original mockup checked jokes, sayings, facts and compliments, left
horoscopes/tarot and riddles/quiz unchecked, selected occasional frequency and
left online sources off. These are illustrative defaults, not implemented
settings or a final UI decision.

Selection should use observed context. Application-specific or media-specific
remarks require a real, privacy-conscious source; do not infer application
names, window content or media from coarse hardware observations.

The original proposal uses separate versioned social-settings and content-cache
files under `%LOCALAPPDATA%\AikoDesktopPet` while leaving outer `state.json` v1
unchanged. Exact persistence integration remains to be designed against today's
single `PetSettings` owner and state-store boundaries. A separate file must not
silently become a competing mutable settings model.

## Relationship to minigames and cursor behavior

Quiz/riddle sessions can reuse providers, translation, validation and prepared
content. They additionally need rules, user input, answer evaluation, an exit/
restart lifecycle and an explicit game-experience profile if need rewards are
later included. The content pipeline must not directly mutate pet needs.

Blackjack, Connect Four and other local rule games do not require translation or
social providers. A quiz can be selected without first implementing astrology,
every joke source or the full settings mockup.

The [cursor concept](ADAPTIVE_CURSOR_CONCEPT.md) shares Aiko's context,
attention, interaction protection and reaction presentation, but does not
depend on online content or translation. These are related product directions
with separately selectable implementation scopes.

## Original staged proposal

The supplied paper suggests this order; it is retained as planning history, not
a newly approved roadmap:

1. General story model, pauses, sequential playback and cancellation tests.
   **Current adjustment:** the core sequential playback already exists.
2. German sources: authored content, `pyjokes`, JokeAPI, Random Useless Facts,
   then sayings and quotations.
3. Local translation, prepared OPUS-MT model, cache and German-only checks;
   then English facts, advice and activity suggestions.
4. Longer content, horoscopes/tarot, category/frequency settings and contexts.
5. Interactive riddles, quiz and additional games.

The next delivery should be selected explicitly using current effort and user
value. No implementation has been authorized by the documentation step alone.

## Future validation

- Unit-test normalization, language eligibility, source metadata and failure
  handling. A failed translation must never enable an English display fallback.
- Test ordered presentation, cancellation, quiet pauses, concurrent events,
  protected games and repeated-content behavior through the existing owners.
- Use fixed provider JSON fixtures in ordinary CI; free API outages must not
  determine normal test outcomes. Keep live provider/model checks separate.
- Validate actual CPU translation and Tk behavior on Windows using isolated
  saves when those integrations are implemented.
- Recheck each source's API contract, terms, attribution and caching permission
  before activation. Evaluate question/answer correctness and translated
  wordplay as content-quality concerns, not just schema checks.
