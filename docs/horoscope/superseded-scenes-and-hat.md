# Superseded horoscope scene and hat concepts

Historical planning text preserved on 2026-10-25; **not the current design**.
The nine-bubble performance and twelve original pilots were rejected/superseded.
The hat remains a possible later extension; its former mandatory-unlock rule
and floating-book scene do not govern the first local book version.
See the [current plan](LOCAL_HOROSCOPE_IMPLEMENTATION_PLAN.md) and
[approved book-reading reference](book-reading-reference.de.md).

All sections below are historical quotations of the earlier plan, including
old statements of scope/authorization. They do not authorize implementation.

### Twelve editorial pilot drafts

On **2026-10-25**, the owner authorized drafting the twelve pilots, one for each
theme family, including Aiko's explicitly played fortune-teller role and the
existing friendship tiers. The resulting
**[twelve German pilot scenes](pilot-scenes.de.md)** are editorial
Markdown only; they are not a runtime catalogue or an approved replacement
for the API prototype.

- Each pilot contains seven complete text bubbles, with role entry, thematic
  interpretation, Aiko's own response and an explicit return to ordinary Aiko.
  The main sequence shows friendship **6–8**; full replacements for bubbles
  **1 and 5** assemble the **1–2**, **3–5** and **9–10** versions without mixing
  sentence fragments. Closeness changes openness, warmth and teasing, not the
  astronomical inputs or interpretation. These remain twelve content pilots,
  not 48 distinct entries toward the 96-template target.
- Three pilots cover each direction: Beginnen **P01/P05/P08**,
  Weiterentwickeln **P03/P06/P09**, Betrachten **P02/P07/P11**, Abschließen
  **P04/P10/P12**. Their relative Moon house and phase-angle interval are
  documented as eligibility conditions, not fabricated live calculations.
- Staging uses existing `idle` and occasional one-shot `waiting`, plus existing
  emotes between text bubbles. Larger poses, simultaneous effects, fixed gaze
  changes, hat and floating book are not delivered. Later orchestration is still
  needed for the described per-beat changes. P04/P12 intentionally remain quiet
  without compulsory comedy; other asides arise from their specific scenes.
- The pilots target a calm, suitable emotional context. Complete tired,
  irritated or subdued coverage is not claimed; friendship must not force
  cheerfulness. Review actual voice and stage differences before any expansion.
- No dialogue offers a real text-input mechanism, automatically starts a game,
  creates a persisted wish or adds a care reward. No extra character assets,
  dependencies, runtime data, save changes or balance changes are part of this
  editorial work. The example scene below remains a separate reference.

### Complete nine-bubble scene

This is one full authored scene for an already friendly relationship, not a
finished catalogue for every friendship/emotional state or sky configuration.
**Example input:** selected sign Taurus/Stier, Sun in Scorpio, waxing Moon in
Pisces. These are illustrative inputs, not a calculation for today's date.
The simplified scheme places the Sun in the seventh and Moon in the eleventh
solar house: encounter/relationship and friendship/shared ideas. Our resulting
theme is **encounter, imagination and a small shared beginning**.

Aiko stays at a quiet fixed desktop position. She enjoys her solemn performance,
notices a contradiction in her own advice, comments on it, regains composure
and ends with her own invitation. Her aside follows this particular reading;
an apology or the same role-break gag is not mandatory in every future scene.

| Beat | Complete German text bubble | Proposed staging with existing assets |
| --- | --- | --- |
| 1: enter the role | Also gut. Für diese Lesung bin ich die Hüterin der zwölf Sternzeichen. Ein bisschen Ehrfurcht, bitte. | Play the existing `waiting` question/request gesture once: raise the hands and bring them together before her chest. Show `star` briefly after the text. |
| 2: begin the reading | Stier … die Sonne steht im Skorpion. In meiner Deutung rückt heute dein Gegenüber in den Mittelpunkt. | Quiet `idle`; the deliberate language carries the role without another effect. |
| 3: interpret the Moon | Der zunehmende Mond in den Fischen bringt Fantasie dazu. Etwas Gemeinsames darf erst noch Gestalt annehmen. | Continue `idle` with its existing blink. A glance into the floating book is a later addition only. |
| 4: concrete advice | Mein Rat: Lade jemanden zu etwas Kleinem ein. Eine unfertige Idee reicht. Du brauchst keinen großen Auftritt. | Face the player and maintain the solemn role. A deliberately controlled gaze is later orchestration work. |
| 5: notice her own performance | … Keinen großen Auftritt. Hm. | After the text, show `question` for about 800 ms as the silent thinking beat before the joke; do not add another 800 ms blank pause on top. |
| 6: Aiko's own comment | Ich verlange Ehrfurcht und rate dir, keinen Auftritt zu machen. Mein Orakel ist heute ziemlich frech. | `idle`, followed by a short `laugh` emote. She is amused at her own theatricality. |
| 7: regain composure | Ähem. Für dich bleibt es dabei: Mach eine kleine Einladung. Was daraus wird, findet ihr gemeinsam heraus. | Return to quiet composure without repeating the opening gesture. |
| 8: personal invitation | Ich wäre übrigens für Vier gewinnt zu haben. Das ist jetzt aber mein Vorschlag. Die Sterne haben da keine Stimme. | Show a short `faceHappy` after the text. This line does not start a game, create a persisted wish or award an additional care effect. |
| 9: leave the role | So. Die Hüterin hat Feierabend. Ich bleibe noch hier. | Normal `idle`; apply the agreed extra final second to this text. |

The emotional arc is **anticipation → concentration → self-irony → regained
composure → desire for shared time**. The aside does not claim to know the
player's thoughts, relationships, previous actions or response to the reading.

### Presentation, timing and later props

- All nine texts are complete bubbles below 125 characters (lengths in order:
  101, 101, 107, 109, 29, 101, 105, 113, 53). Nine leaves room below the existing
  maximum of twelve; it is not a new mandatory length for every reading.
- Apply the shared reading formula and final-second allowance. Text alone is
  approximately 68.35 seconds; with short emotes the example is roughly
  75 seconds without reading clicks. This is a design estimate, not a runtime
  measurement. Existing reading-click advancement remains available.
- Text and emotes occupy the **same** speech surface sequentially. Do not plan
  simultaneous text/emote overlays or treat the `star` emote as surrounding
  particles. Keep the brief expression beats between readable text bubbles.
- `idle`, `waiting`, `star`, `question`, `laugh` and `faceHappy` already exist.
  The current reaction player does not orchestrate a new animation/gaze at
  every text beat automatically. Coordinating those changes is later work;
  recording the storyboard does not claim an existing scene engine.
- **Hat remains later:** show it on role entry, remove it on completion or
  interruption, and retain the permanent gift/unlock concept below. Fit each
  used head view before integration. This draft does not bring that asset or
  unlock requirement into the current prototype.
- **Floating book remains later:** slightly in front on screen-right near chest
  level, with a suitable down-right gaze during interpretation and attention
  returning to the player for Aiko's own comment. Floating/page-turn motion,
  gaze coordination and final placement remain separate asset/scene work.
- The nine spoken texts do not claim that a hat is being worn or a book is
  present. The basic performance therefore needs neither prop. No new images,
  runtime text, dependencies, saves or balance rules are delivered by this draft.

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
- Future implementation must respect the existing [World ownership boundaries](../WORLD_OBJECT_CONTRACTS.md):
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
