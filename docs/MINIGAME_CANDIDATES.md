# Minigame candidates and integration research

> **Exploratory reference only — not an approved roadmap.**
>
> Blackjack and Tic-Tac-Toe were explicitly selected on 2026-10-19; their
> agreed scope is recorded in the separate
> [implementation plan](MINIGAME_IMPLEMENTATION_PLAN.md), with implementation
> still awaiting authorization. All other entries remain research only.
> Inclusion of a game, algorithm, API or library below does not select it.
> Candidate effort and duration estimates are provisional comparison aids,
> not rankings or priorities.

This document records the game ideas, libraries, repositories, APIs, and
evaluation criteria discussed for the Aiko Desktop Pet project in October 2026.
It is a record of possibilities, **not a verified compatibility matrix or
procurement decision**. External API conditions, licenses, game coverage, and
platform compatibility must be checked again before any adoption.

The separately preserved [social and entertainment concept](SOCIAL_ENTERTAINMENT_CONCEPT.md)
records the broader API-content, jokes, local English-to-German translation and
cache design that can also serve quizzes. Its German-only/free social-content
constraints and original effort estimates are not captured by this catalogue's
general game preferences. The [adaptive cursor concept](ADAPTIVE_CURSOR_CONCEPT.md)
is a related interaction proposal with no dependency on that content pipeline.

## Existing baseline (not a decision about future games)

**Rock–Paper–Scissors** is already part of `main`. Its rules are local, and its
Tk player panel and Aiko's speech/emote/animation presentation are separate.
The player panel owns the player's selected hand and temporary round scores;
Aiko's character bubble owns only her hand and reactions. Closing the game
discards that window's game counters and restores normal pet behavior.

The baseline demonstrates a possible integration pattern. It does **not**
require future games to use the same panel shape or dialogue flow.

## Working preferences, not binding requirements

The following considerations were discussed for future evaluation:

- Prefer short, self-contained sessions for early experiments, while allowing
  longer or configurable variants where they suit the game. A round's estimated
  length is not an implementation date or selection criterion by itself.
- Reuse compatible Python libraries, maintained repositories, existing
  algorithms and rule implementations instead of rewriting proven components.
  Importing a library is generally a low hurdle; integrating it into Tk,
  selecting a playable opponent, and keeping it maintainable still require work.
- Prefer **local, offline and free** operation, with no required paid inference.
  API keys, registrations, continuous internet access, recurring fees and
  paid AI requests are disadvantages, not absolute prohibitions already decided
  for every possible game.
- Reuse available card assets, the Kenney UI/Emote assets and Aiko's authored
  animation clips where appropriate. The availability, completeness, license
  and fit of individual assets should be checked for each candidate.
- Treat Aiko as the playing partner/opponent. Classical game-search algorithms,
  scripted dealer logic and local agents are valid; generative language models
  are **not necessary** for the initial game implementations.
- Let game mechanics, local game state and game presentation have distinct
  owners. Reuse the existing bubble for Aiko's own dialogue or reactions, with
  a player-owned view for input and information where that is appropriate.
- Complete the game itself before designing new mood, energy, affection or
  friendship rewards. No reward formula, save migration or lifetime game
  statistics have been approved for future games.
- Keep source code, technical documentation, PR descriptions and commit
  messages in English. Only user-visible game UI and Aiko's in-game dialogue
  should be in German.

## Effort and playtime notation

All times are **very rough per-session estimates** based on a simple Aiko-sized
variant; they are not measured benchmarks. A library may reduce rule-engine
work without providing a ready-to-use GUI or a competent opponent.

| Effort label | Meaning for Aiko's current Python/Tkinter application |
| --- | --- |
| Very low | Small local rules, little new UI, no service required |
| Low | Small dedicated window or deterministic strategy, straightforward assets |
| Medium | Board/card-state UI, agent integration or external data validation |
| High | Imperfect information, complex rules, special assets or substantial dependencies |
| Very high | Multi-player or deep hidden-information strategy and substantial UI/agent work |

These labels **do not establish an implementation sequence**.

## Candidate games, grouped by mechanics (not priority)

Each item is a *possible* game. Its table position carries no meaning about
interest, approval or schedule.

### Short choice, number, word and dice games

| Candidate | Illustrative duration | Possible implementation basis | Rough effort |
| --- | --- | --- | --- |
| Hangman (German words) | 2–5 min | Local, licensed German vocabulary; drawn UI | Low |
| Higher or lower (cards) | 30–90 sec | Python card deck and existing card assets | Very low |
| Mastermind / code-breaking | 3–7 min | Local generation, scoring and optional opponent logic | Low–medium |
| Nim / take-away sticks | 1–3 min | Small deterministic optimal-play policy | Very low |
| Number guessing | 30–90 sec | Python standard library | Very low |
| Pig (risk-based dice game) | 1–3 min | Local turn and simple bot rules | Low |
| Simple dice duel | 30–90 sec | Python standard library; small dice icons | Very low |
| Tic-Tac-Toe | 1–3 min | Minimax or a small two-player game library | Low |
| Yacht / Kniffel-like scorecard | 5–12 min | Existing game rules where suitable; scorecard UI | Medium |

Rock–Paper–Scissors is omitted from this *candidate* table because it is
already implemented, not because anything else has been approved.

### Card games

The existing card assets are a potential advantage; actual required card faces,
deck size, rule variants, game-board layout and reuse terms need validation
for the chosen candidate.

| Candidate | Illustrative duration | Possible implementation basis | Rough effort |
| --- | --- | --- | --- |
| Blackjack | 1–3 min per hand | Local dealer rules or assessment of RLCard | Low |
| Bridge | 15–30+ min | Specialist partnership/bidding engine | Very high |
| Crazy Eights / Mau-Mau-like game | 5–12 min | Local turn rules, optional game library | Medium |
| Gin Rummy | 5–15 min | RLCard as a candidate rule/agent foundation | Medium–high |
| Go Fish | 3–10 min | Local card rules; assess existing implementations | Medium |
| Poker / Texas Hold'em | 15–30+ min | RLCard environment and more demanding opponent logic | High–very high |
| UNO-like game | 5–15 min | Assess RLCard; special card artwork and rule variants | Medium–high |

These game names refer to potentially different rule variants. Brand-specific
names, art and licensing must be assessed independently if bundled.

### Board and spatial strategy games

| Candidate | Illustrative duration | Possible implementation basis | Rough effort |
| --- | --- | --- | --- |
| Backgammon | 10–20 min | OpenSpiel or another suitable rule engine | High |
| Battleship | 10–20 min | Local hidden-board game; evaluate OpenSpiel coverage | Medium–high |
| Checkers / draughts | 5–20 min | Game-search engine or suitable local library | Medium–high |
| Connect Four | 2–6 min | Minimax / easyAI / OpenSpiel | Low–medium |
| Dominoes | 5–12 min | Existing rule environment or local rules | Medium |
| Dots and Boxes | 3–8 min | OpenSpiel or small local search | Medium |
| Gomoku / Five in a Row | 5–15 min | Existing search algorithms and board UI | Medium–high |
| Kalaha / Mancala | 5–15 min | OpenSpiel or suitable local rules | Medium |
| Mahjong | 15–30+ min | RLCard/Ludii depending on exact Mahjong variant | Very high |
| Nine Men's Morris | 5–20 min | Existing rule/search engine to be assessed | Medium–high |
| Reversi / Othello | 5–15 min | easyAI-style search, OpenSpiel | Low–medium |

Chess was explicitly excluded from the earlier shortlist; it is **not** a
candidate proposed by this document.

### Quiz and content-driven game variations

For the shared provider/translation design and the original 4/5 estimate for
riddles/Open Trivia DB (assuming an installed translator), see the
[social concept](SOCIAL_ENTERTAINMENT_CONCEPT.md#content-sources-and-original-relative-effort).
That estimate does not assign an effort rating to every metadata-based quiz
theme below or select one for implementation.

One reusable four-choice quiz mechanic could potentially support multiple
themes. Data APIs generally provide *content*, not complete, validated German
questions, wrong-answer choices or an AI opponent.

| Possible theme | Illustrative session | Research source candidate | Considerations |
| --- | --- | --- | --- |
| General four-answer German quiz | 3–5 questions, ~2–4 min | Open Trivia DE; local German question set | German wording, correctness, attribution |
| Anime/manga trivia | ~2–5 min | AniList | Generate and validate German questions |
| Countries, flags and capitals | ~1–4 min | countries.dev or comparable dataset | German names, source/service availability |
| Film and TV trivia | ~2–5 min | TMDB | Account/API key and image rights |
| Music artist/album/song quiz | ~2–5 min | MusicBrainz | Rate limits and answer validation |
| Pokémon identification | ~2–5 min | PokéAPI | German species names and art rights |
| Programming/IT trivia | ~2–5 min | QuizAPI or local question set | API key; many datasets are English |
| Broad structured knowledge | ~2–5 min | Wikidata SPARQL | Query design and reliable distractors |
| Word association / language games | Varies | Datamuse; German word datasets | Mostly English source material |

### Additional ideas discussed

Potential variants mentioned during research included extended dice games,
custom quiz themes and the possibility of smaller board sizes to shorten
games such as Battleship. They are not separately approved features.

## Candidate libraries, engines and repositories

These links are **research leads**, not approved dependencies. Their current
maintainer activity, supported games, compatible Python/Windows versions,
licenses, distribution terms and transitive dependencies must be validated.

| Project | Candidate use | Integration caution |
| --- | --- | --- |
| [easyAI](https://github.com/Zulko/easyAI) | Python adversarial search (e.g. minimax) for two-player games | Does not supply Aiko's Tk presentation automatically |
| [RLCard](https://github.com/datamllab/rlcard) | Card-game environments, agents and evaluation tooling | A game environment is not necessarily a ready-to-play bot or full UI |
| [OpenSpiel](https://github.com/google-deepmind/open_spiel) | Multiple game definitions and search/learning algorithms | Installation, platform fit and exact per-game support to verify |
| [PettingZoo](https://pettingzoo.farama.org/) | Standardized multi-agent game environments | The environment alone may not include an opponent strategy |
| [GamesCrafters Universal Web API](https://github.com/GamesCrafters/GamesCraftersUWAPI) | HTTP-based legal moves and game evaluations for supported positions | Coverage and dependable public hosting must be verified |
| [boardgame.io](https://boardgame.io/) | Turn-based multiplayer game framework | JavaScript stack introduces a separate integration boundary |
| [Ludii](https://github.com/Ludeme/Ludii) | General game-rule/strategy framework | Java integration rather than native Python/Tk |

Before adopting an engine, verify separately that it supplies (1) the specific
rule variant, (2) an opponent suitable for the desired difficulty, and
(3) a usable Python/runtime boundary. These are independent questions.

## External game/data APIs and datasets considered

API service claims below were **not freshly verified for this document**.
Avoid hard-coding assumed uptime, key requirements, costs, rate limits or
license permissions into any future implementation.

| Source | Potential use | Possible hurdle / evaluation |
| --- | --- | --- |
| [Deck of Cards API](https://deckofcardsapi.com/) | Shuffle/draw deck operations | Internet need; local `random.shuffle` may suffice |
| [Open Trivia DE](https://opentrivia.de/api) | German general-knowledge quiz | Question quality, dataset reuse/license |
| [German quiz question repository](https://github.com/nicoruti/quizfragen) | Potential four-answer offline questions | Audit provenance, license and wording |
| [Open Trivia Database](https://opentdb.com/api_config.php) | General trivia questions | Mainly English and usage limits |
| [The Trivia API](https://the-trivia-api.com/) | Broad trivia subjects | Access tiers and German-language availability |
| [QuizAPI](https://quizapi.io/docs) | Developer/programming questions | API credentials and language |
| [AniList GraphQL API](https://docs.anilist.co/) | Anime and manga knowledge | Construct questions from records |
| [MusicBrainz API](https://musicbrainz.org/doc/MusicBrainz_API) | Music metadata | Rate limits; user-facing German questions |
| [PokéAPI](https://pokeapi.co/docs/v2) | Pokémon metadata | Rights to images and translated data |
| [TMDB](https://developer.themoviedb.org/docs/getting-started) | Film and television data | API key and media-image terms |
| [countries.dev](https://countries.dev/docs) | Country/flag data | Service availability and German localization |
| [Wikidata Query Service](https://query.wikidata.org/) | Structured knowledge across topics | SPARQL complexity; answer quality |
| [Datamuse](https://www.datamuse.com/api/) | Word associations and vocabulary | Mostly English results |

Other services such as Jikan or REST Countries arose during exploration but
had reported service-access or key-related caveats. They are **not validated**
as currently available, free, or suitable for inclusion.

## How to evaluate any candidate later

When the project owner chooses to investigate a particular option, assess it
individually rather than inheriting assumptions from this catalogue:

1. **Rules and experience:** exact rules/variants, solo play against Aiko,
   realistic round length and a working exit/restart behavior.
2. **Available code:** existing rules, local bot, difficulty control, license,
   maintenance and compatibility with Python 3.11+ on Windows.
3. **Presentation:** player inputs, the information Aiko owns, the player's
   information, animation/emote usage, Tk window sizing and accessibility.
4. **Assets:** reuse existing cards/Kenney artwork, verify missing visuals and
   confirm distribution rights.
5. **Service needs:** offline functionality, accounts/keys, rate limits, costs,
   failure handling, cacheability and privacy.
6. **Boundaries and tests:** separate game logic and state from the desktop
   composition root; test all outcomes, lifecycle cancellation and UI behavior.
7. **Future pet effects:** decide whether completed games should affect needs
   or friendship only when explicitly scoped; avoid accidental persistent
   stat changes or new save fields.

The criteria above are **evaluation questions**, not gates that impose a
sequence, deadline or acceptance decision.

## Decision status and how to update this reference

- **Implemented today:** Rock–Paper–Scissors on `main`.
- **Selected additions:** Blackjack and Tic-Tac-Toe, with the Spielen submenu
  and desktop-card presentation described in the
  [planning-only implementation plan](MINIGAME_IMPLEMENTATION_PLAN.md).
- **All remaining entries:** optional research candidates only.
- **Implementation authorization:** pending; only documentation was requested.
- **Proposed delivery stages:** see the separate plan; no schedule is committed.
- **Approved additional APIs, engines or paid AI services:** none.
- **Approved schedule, budget expenditure or dependency change:** none.

When a decision is eventually made, record the explicit selection and its
scope in a separate issue, PR or decision note. Do not infer approval from
the order or content of this reference document.
