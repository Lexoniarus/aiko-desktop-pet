# Minigame delivery and expansion plan

Delivered baseline: three games, implemented and locally verified on the feature
branch, 2026-10-19. The [Connect Four extension](#connect-four-extension-vier-gewinnt)
was authorized and implemented locally on 2026-10-23.
Native Windows visual/input acceptance remains separate; no merge performed.
The owner selected Blackjack and Tic-Tac-Toe alongside the existing
Rock–Paper–Scissors (RPS). The owner authorized stepwise implementation, small
commits and targeted tests, with full-suite validation only at the end.
No merge is authorized.

The original delivery sections and evidence below retain their three-game scope.
The appended Connect Four section records its separate implementation and
validation. A scoped Connect Four commit is authorized. No new dependency,
balance values, push or merge is included.

The [Mastermind extension](#mastermind-extension) records its separately
authorized local implementation: Aiko provides the code, with a concealed
desktop strip, ten prepared drag-and-drop rows, Kenney pieces and local
Python-standard-library rules. No Mastermind commit or merge is included.

The [quiz concept](#quiz-concept-planning-only) records the owner's subsequent
topic, difficulty, round flow, Aiko-role and separate question-feedback decisions.
The owner subsequently authorized the 200-question catalogue, including film
and television. Its [editorial draft](#authored-starting-catalogue-editorial-draft)
is separate from game implementation. The owner subsequently authorized the
[local Quiz delivery](#quiz-delivery-2026-10-25) under Spielen, including its
reviewed catalogue, quizmaster role and shared-play rules. Feedback settings
remain separate future work. A scoped local Quiz commit was subsequently
authorized; push and merge remain excluded.

## Agreed experience

- **Spielen** opens a small submenu: **Schere–Stein–Papier**, **Blackjack**,
  **Tic-Tac-Toe**. Only selecting a game requests the existing game admission
  flow. Dismissal, Escape and outside clicks close the submenu without starting
  play or granting rewards. Existing interaction restrictions still apply.
- One game window/session at a time. While a game is open, further selection
  is disabled. Preserve existing RPS behavior.
- The new games allow any number of rounds. Show temporary player/Aiko/draw
  counts and a result. Following the owner's playtest feedback, Blackjack
  automatically starts the next hand after 2.8 seconds; Tic-Tac-Toe offers
  **Nächste Runde**. RPS retains its hand-selection controls and round flow.
- Aiko remains on the desktop and uses existing speech, emotes and animations.
  Her speech bubble carries comments, not the Blackjack card layout.
- Closing releases the game presentation and restores ordinary behavior.
  Completed rounds count once; an unfinished round never counts. Session
  scores, decks and boards are discarded rather than saved.

## Blackjack

**Player window:** the player's cards at 2x integer scale and total, a clickable
back pile for **Karte ziehen**, **Bleiben**, result and session score. Results
remain visible for 2.8 seconds before an automatic fresh hand; close cancels
that pending restart. No duplicate of Aiko's cards or separate Aiko-hand
display in this window.

**Aiko on the desktop:** her entire hand floats as a compact group in front of
or beside her. Initially one card is face up and one face down. Additional
dealer cards appear in this group. Keep it anchored to her position and scale,
inside the usable desktop, clear of the taskbar and readable alongside speech.
Use compact overlap for longer hands while keeping exposed ranks legible.

Hover subtly raises/highlights a card. It never reveals a hidden card; clicking
cannot reveal it early either. When Aiko's turn starts, show a short flip
(narrow, swap face, widen), followed by readable individual draw steps.
Hidden card identity/value must stay out of visible text, tooltips and totals
until reveal. The renderer receives a masked card view until then.

Cards are temporary game graphics. They are not World objects: no pickup,
custody, inventory, perception, memory, ground placement or save entries.
Their hover must not trigger ordinary direct-pet contact or annoyance actions.

Rules:

- One 52-card deck, freshly shuffled before every hand; two cards each.
- Number cards use their rank; J/Q/K count ten; aces count one or eleven to
  produce the highest non-bust total.
- The player chooses hit or stand. A non-natural 21 automatically stands;
  exceeding 21 ends the hand immediately as a player loss.
- Aiko is the dealer, drawing below 17 and standing on all 17s, including soft
  17. She follows fixed rules, without training or mood-based difficulty.
- Resolve initial naturals before ordinary input: two-card Blackjack beats
  any non-natural hand; two naturals draw. Otherwise compare valid totals;
  equal totals draw, and a dealer bust is a player win.
- Reveal the remaining hidden card on settlement, including a player bust;
  do not play unnecessary dealer draws after the player has already busted.
- No stakes, money, chips, splitting, doubling, insurance or extra variants.

Assets were inspected locally in
`D:\Dropbox\Kenney Game Assets All-in-1 3.4.0\2D assets\Playing Cards Pack`.
The pack is version 1.0, with all 52 faces in each PNG size and a matching back
in the large set. Plan to import only the 52 faces plus `card_back.png` from
`PNG\Cards (large)` (64×64 canvases with transparent margins), retaining the
pixel style and using integer scaling where appropriate. Its `License.txt`
states CC0 and voluntary attribution. Record provenance and preserve the
license with the eventual import; no new artwork is needed.
The playtest follow-up rechecked the source sizes (16, 32 and 64 pixels): the
existing large originals are retained, with 128×128 player-card canvases and a
runtime composite of the same back for the draw control. Aiko's scale is
independent of this player-only enlargement.

## Tic-Tac-Toe

- One shared 3×3 board in the player window. Player X, Aiko O; player starts the
  first round, then the starter alternates after each completed round.
- Accept only legal clicks on the player's turn. Aiko moves after a short
  thinking pause; input stays disabled during her turn and after settlement.
- Aiko takes an immediate win, otherwise blocks an immediate player win,
  otherwise prefers the center, then corners, then remaining squares. Vary
  choices within the same priority. This deliberately simple opponent has no
  difficulty menu, perfect-search requirement or emotional difficulty coupling.
- Three in a row wins; a full board without a winner draws. Highlight the
  winning line and offer the same result/next-round/session controls.
- Draw the board and marks with Tk. No new image assets. Aiko's comments and
  reactions remain with her desktop figure.

## OOP ownership and current-code alignment

Checked against `feature/social-optimization` at `7049869`,
[Architecture](ARCHITECTURE.md), [UI window ownership](UI_WINDOW_CONTRACT.md)
and the actual game/window/desktop code. The governing rule is one owner per
mutable state or external side effect, connected through small typed ports.
The target-owner table below is now implemented; **new** identifies the files
introduced by this delivery. The code baseline above records the pre-change audit.

### Existing seams that need a bounded change

- `ui/windows/action_toolbar.py` already sends the `play` action to `HoverUi`.
  Keep that dispatch; change its destination from immediate RPS entry to the
  submenu. `FoodMenu` is a local style/lifecycle reference, not a game superclass.
- `ui/windows/hover_ui.py` currently owns a concrete
  `RockPaperScissorsWindow`, and `HoverUiPorts.game_completed` accepts RPS
  `Score`. Those two seams need generalization; the toolbar does not need to
  learn individual game rules.
- `gui.py` currently converts that score with
  `experience_from_rock_paper_scissors`. In contrast,
  `ApplicationRouter.complete_game(GameExperience, inputs=...)` and
  `GameExperienceCoordinator` are already game-neutral. Extend the adapters,
  not the reward coordinator or its ownership.
- `GameSpeech.hand()` uses `SpeechPresenter.show_game_hand()`. Speech/emotes
  replace that same bubble, so Blackjack cards cannot use this RPS hand path.
  Keep RPS intact and provide a separate card presenter that survives speech.

### Target owners

| Responsibility | Canonical location and boundary |
| --- | --- |
| Deck, board, legal actions, dealer/bot decisions, outcomes and session score | **New** `games/blackjack.py` and `games/tic_tac_toe.py`, following `games/rock_paper_scissors.py`. One session object per active game owns all mutable game truth; expose frozen results/snapshots. Inject randomness. No Tk, pet state, World, persistence, desktop APIs or dialogue. |
| Shared identity and completion payload | **New** `games/contracts.py`: a bounded game ID and immutable session summary, with documented player-perspective outcome counts. Construct the summary from the game's existing score at close; do not maintain a second shared score. No generic engine or game base-class hierarchy. |
| Submenu and active window lifetime | **New** `ui/windows/game_menu.py`; existing `HoverUi` remains the sole menu/window instance owner. **New** `ui/windows/game_contracts.py` defines only the small window interface needed by its consumers (`window`, `greet`, `close`, topmost handling). Select among the three concrete windows with explicit typed construction. |
| Player controls and board/card rendering | **New** `ui/windows/blackjack_window.py` and `ui/windows/tic_tac_toe_window.py`. Render snapshots, forward permitted actions and host their sequence; do not recalculate results, mutate needs or hold another deck/board/score. Reuse `AikoSkin` and `WindowDrag`. |
| Turn/reveal timing | **New** per-game sequence objects alongside the existing `rock_paper_scissors_sequence.py` pattern. They own turn pacing and cancellable scheduled cues through injected schedule/cancel/effect callbacks, without importing Tk. They command the game session; they do not duplicate its rules or counters. |
| Detached visible data | **New** `ui/view_models/game_models.py` for the small menu/card projections. A hidden card exposes only its back/slot, with no rank, suit or hidden total. The desktop presenter receives this projection, never the deck or full hidden hand. |
| Aiko's floating Blackjack hand | **New** `ui/pet_view/blackjack_hand_presenter.py`: owns its Tk overlay, image references, hover/flip frames and their cancellation. Accepts projected hand/anchor/bounds/scale and injected native-window effects. No rules, speech selection, movement writes or World membership. |
| Card image loading | **New** small Tk cache under `ui/common/playing_card_images.py`, shared by player/card views. Put packaged card paths in existing `asset_paths.py`; selected PNGs/provenance belong under `aiko_pet/assets/`, with notices in `ASSETS.md`/`LICENSES/`. No runtime Dropbox lookup or second item catalog. |
| Game completion and care effects | Extend `application/game_experience.py` with the new summary adapters; keep `ApplicationRouter.complete_game`, `GameExperienceCoordinator` and `PetState.record_game_experience` as the existing write path. Profiles remain in `pet/fun.py`, values in `data/balance.json` with the existing balance-contract validation. |
| German text and character voice | Labels in `data/texts.de.json`; authored game reactions in `data/dialogues/de/index.json`, registered through `pet/mind/dialogue_events.py` when adding events. Embedded play uses the injected session `PetMind`, as RPS does; never add a second mind/catalogue history for it. |
| Composition and native integration | `gui.py` wires callbacks only; a bounded **new** `desktop/game_assembly.py` may construct the card presenter and image cache to keep wiring small. Existing `desktop/window_stack.py`, `preferences.py`, `lifecycle.py` and placement callbacks retain their respective effects. Native no-activate/hit-test setup stays in `desktop/`, using the existing adapter where suitable. |

### Integration invariants

- `HoverUi` remains the single source of active-window presence; no parallel
  application game registry or extra busy flag in `DesktopPet`. Reserve one
  pending selection while `defer_game` completes World interruption, so a
  second selection cannot queue another session. Recheck admission before
  construction and release the reservation on failure/cancellation. The
  resumed callback uses `game_ready` for a fresh sleep check: the original
  `can_interact` check includes World's own still-active interruption
  reservation and must not reject that already-admitted callback.
- Include the game submenu in `interaction_active`, outside-dismissal,
  topmost handling, overlay enumeration and toolbar/shutdown cleanup alongside
  the existing transient food menu. Opening a selector never starts
  `GameSpeech` or records a completed game.
- The window owns its sequence; the sequence owns the one game session and
  pacing timers. The card presenter owns only visual animation timers. Close
  first invalidates/cancels outstanding work and clears cards, then reports
  the immutable completed summary exactly once, with cleanup in `finally`.
  Constructor failure must also release game mode and partial overlays.
- Keep one explicit game-owned completion transition after the required
  reveal/turn steps. A computed pending outcome alone is not completed play.
  Once the result is presented, closing during its reaction must retain that
  completed unit; no need to wait for the final spoken line. Preserve RPS's
  existing reveal-based completion point.
- The shell replaces its RPS-only conversion with the application adapter for
  the common summary, retaining current `SessionInputs`. No UI-to-`PetState`
  shortcut and no need/reward imports in `games/`.
- Wire the card overlay into `DesktopPet._overlay_windows` and the existing
  `WindowStack`; use no independent z-order/focus loop. Route position/scale
  changes through existing `_place_x`/`DesktopPreferences` effects. Compute
  card placement from supplied geometry, without moving Aiko or adding a
  second position writer. Speech and cards must remain readable together.
- Use card-local hover/hit testing that does not forward to pet click/drag,
  care or World pickup. Keep native behavior behind the desktop port rather
  than importing `DesktopPet` or Win32 code into a utility view.
- Existing `DesktopLifecycle` closes the active game before the final save
  and router shutdown. Extend that cleanup chain for cards/menu; do not create
  another shutdown owner or save transient game state.

## Small commits and their targeted checks

Implementation was authorized on 2026-10-19. Use the
following ordered, independently reviewable commits. Each commit includes its
behavioral tests and passes its targeted checks before moving to the next.
The table names existing test owners and proposed new owners; it does not claim
that new modules or passing results already exist. Split a row further if its
actual diff crosses unrelated responsibilities; do not combine rows merely to
reduce the commit count.

| Commit | Bounded change | Targeted validation before that commit |
| --- | --- | --- |
| 1 — `refactor: generalize minigame completion contracts` | Add the shared game ID/session summary and small window interface; migrate RPS window, `HoverUiPorts` and the shell's application adapter together. Preserve RPS mechanics, reveal timing and the existing reward path. | RPS rules/sequence and affected GUI completion cases; `test_game_experience`; exactly-once/empty/pending close and shutdown-before-save cases; affected canonical/UI architecture guards. |
| 2 — `feat: add the Spielen selection menu` | Add the selector under `HoverUi`, with pending-selection admission, dismissal, topmost/stack registration and cleanup. Migrate direct-entry fixtures and the RPS capture helper. Initially expose only the playable RPS entry; add each new selectable game in its own integration commit. | New `test_game_menu`; affected hover-isolation and RPS entry cases; repeat/deferred selection, Escape/outside dismissal, constructor failure and menu shutdown cases; affected desktop input/lifecycle tests. No media capture run on the working desktop. |
| 3 — `feat: add tic-tac-toe rules and opponent` | Add the pure session, immutable reads, legal moves, win/draw detection, alternating starts and injected-randomness priority opponent. No widgets or reward effects. | New `test_tic_tac_toe`: all winning lines, full-board draws, illegal/late moves, each bot priority, equal-priority variation with controlled randomness, round reset and starting-player alternation. |
| 4 — `feat: integrate tic-tac-toe play and completion` | Add the board window/sequence, German copy, result/next-round controls, completion adapter and explicit balance profile; enable its menu entry. Keep the rules owner from commit 3. | New sequence/GUI tests for turn blocking, cancellation and restart; Tic-Tac-Toe adapter/reward cases in `test_game_experience`/`test_fun_mood`; changed content/event/balance validation and new-module architecture coverage. |
| 5 — `assets: add licensed Kenney playing cards` | Import only the 52 faces/back, license and provenance; add canonical asset paths and the shared small Tk image cache. No game entry or native presenter yet. | New `test_playing_card_assets`: complete unique rank/suit mapping, back availability, readable PNGs/dimensions/transparency and provenance consistency; focused cache load/reuse/scale/release checks and affected resource validation. |
| 6 — `feat: add blackjack rules and session state` | Add the pure shuffled-deck session, ace/natural handling, player actions, fixed dealer policy, explicit completion and immutable visible reads. | New `test_blackjack`: unique finite draws, multiple aces, naturals versus later 21, ties, player/dealer bust, soft 17, legal phases, reset and no completed credit for pending/cancelled rounds. |
| 7 — `feat: present Aiko's blackjack hand on the desktop` | Add the masked card projection and dedicated presenter, hover/flip cancellation and small assembly/native-effect ports. No card membership in World and no selectable incomplete Blackjack window. | New projection/presenter tests for hidden identity/total exclusion, hover without reveal/contact, flip ordering/cancellation, bounds/scale and image cleanup; affected stacking/preferences/placement and UI/desktop architecture cases. Use fake scheduling or the existing isolated GUI environment as appropriate. |
| 8 — `feat: integrate blackjack play and completion` | Add the player window and turn sequence; wire reveal/draw effects, German dialogue, result/next-round controls, adapter/profile and menu entry. Complete constructor-failure, close and shutdown wiring for the hand presenter. | New Blackjack sequence/GUI cases including natural/bust reveal and cancellation during dealer turns; adapter/reward and balance/content cases; targeted desktop lifecycle/input cleanup and all-three-game admission/selection cases. |
| 9 — `docs: finalize minigame integration contracts` | Reconcile the implementation with this plan and update architecture, UI/fun, asset and smoke guides. Close any remaining cross-game lifecycle gaps with their regression tests, in a separate fix commit if needed. | Focused combined menu/completion/cleanup regression for all three games and architecture guards covering the touched boundaries. Verify documentation against the delivered files and actual targeted results. |

Every game adapter emits the existing immutable `GameExperience`, with outcomes
from Aiko's perspective. One settled hand/board is one completed unit. Review
the new profile values against round duration instead of silently assigning
RPS's per-reveal reward. Continue through `GameExperienceCoordinator`/`PetState`;
no UI-owned need writes, new reward system, persistent statistics or save migration.

### Validation cadence: targeted per commit, full suite at the end

- **During commits 1–9:** run only the changed behavior's tests and the affected
  neighboring integration/architecture checks listed above. Apply Ruff to the
  changed Python files and focused Mypy checks where typed contracts change.
  Fix relevant failures before committing or continuing; record commands and
  results for that commit. Do not run complete test discovery after each commit,
  after each game, or automatically after an individual fix.
- A focused module can be run with
  `python -m unittest discover -s tests -p test_blackjack.py -q`, substituting
  the actual module name. For large existing GUI modules, select the relevant
  cases rather than repeatedly running unrelated long scenarios.
- **After all implementation and integration steps are complete:** run the
  complete local suite once as the final integration gate, followed by the
  full pinned Ruff, strict Mypy and Pyright checks from
  [Contributing](../CONTRIBUTING.md#development-workflow). This is where the
  repository-wide checks belong; targeted results alone are not a green final
  implementation. This task-specific cadence refines the general workflow.
- If the final gate fails, fix each cause with targeted regression coverage,
  then rerun the failed full gate on the corrected final tree. Do not repeat
  already-green full gates without a relevant change or unresolved concern.
- Record the final commands/results and tested commit/tree after that gate,
  using a small documentation-only evidence commit if needed. Do not claim
  final validation in advance or rerun all tests just for that evidence edit.
- No remote CI execution or working-desktop windows/mouse control is authorized
  by this plan. Preserve the isolated-save/GUI restrictions below. Native
  Windows visual acceptance remains separately recorded and subject to the
  owner's existing authorization limits.

The initial planning edits ran no tests; subsequent authorized delivery and its
targeted results are recorded below. Final full-suite validation follows all
implementation/integration steps.

Keep technical documentation/code in English and visible copy in German.
Reuse the existing presentation skin and authored animation clips. The concrete
library/API assessment and recommended dependency choice follow below.

## Libraries and APIs: assessed choice for these two games

Reviewed official documentation/package metadata and RLCard's Blackjack source
on 2026-10-19. This is a source-level fit assessment, not an installation,
benchmark or verified Windows compatibility test. The
[candidate catalogue](MINIGAME_CANDIDATES.md#candidate-libraries-engines-and-repositories)
listed research options, not dependencies already selected for these games.

**Recommended implementation baseline:** existing Tk/Tkinter plus the Python
standard library for both games; Kenney PNGs for Blackjack. No Pygame, easyAI,
RLCard or remote deck service is selected for this scope. This recommendation
is based on the agreed rules and presentation, not a general ban on libraries.
Adding a useful dependency remains an option: the current installer processes
`requirements.txt`, and OOP boundaries allow a rule engine behind a game owner.

| Candidate | Useful work it supplies | Fit and recommendation for the agreed scope |
| --- | --- | --- |
| [Pygame](https://www.pygame.org/docs/) | Image/sprite rendering, transformations, audio, input and display/event facilities. | It supplies no ready-made Blackjack rules, dealer or Tic-Tac-Toe opponent. Our Tk windows, native floating cards, speech, hover and cancellation still need integration. An SDL display/event boundary adds coordination alongside Tk without removing that work. Retain Tk Canvas/PhotoImage/after for these small views and flips; do not add a Pygame loop. This is an integration judgment, not a claim that Tk/Pygame integration is impossible. |
| [easyAI](https://github.com/Zulko/easyAI) | Negamax/alpha-beta search and example two-player games, including Tic-Tac-Toe; MIT. | Relevant if we later want search-based difficulty or larger board games. The agreed immediate-win/block/center/corner policy needs no search engine. Game adaptation, Tk UI, dialogue and lifecycle remain ours. Current [2.1.0 metadata](https://pypi.org/project/easyAI/) requires Python >=3.12, above Aiko's supported 3.11 floor; an [older release](https://pypi.org/project/easyAI/2.0.12/) is a possible future compatibility investigation, not assumed unusable or already tested. Do not adopt for the current simple opponent. |
| [RLCard](https://github.com/datamllab/rlcard) | A local Blackjack environment, card/deck state, ace scoring and fixed dealer behavior; MIT. Its [base dependencies](https://github.com/datamllab/rlcard/blob/master/setup.py) include NumPy and termcolor; PyTorch is optional, not needed for dealer rules. | The checked [judger](https://github.com/datamllab/rlcard/blob/master/rlcard/games/blackjack/judger.py) compares totals without a special natural-Blackjack priority. Its [step implementation](https://github.com/datamllab/rlcard/blob/master/rlcard/games/blackjack/game.py) resolves the dealer's draws together and also draws after a player bust, unlike our agreed flow. Masked presentation and Tk integration remain ours. Correcting/adapting those behaviors would offset the saved small rule implementation; do not add RLCard or fork its engine for this scope. |
| [Deck of Cards API](https://deckofcardsapi.com/) | Remote deck creation, shuffling, drawing and card images. | It does not resolve Blackjack rules or supply our opponent/presentation. We already have licensed local images; a shuffled local 52-card list supplies the required deck without requests, remote state or failure handling. Do not use the service for these games. |

### Work to reuse and the small remainder to implement

- Reuse the existing game admission, session-completion/time/need pipeline,
  RPS sequence's injected scheduling pattern, `GameSpeech`, session mind,
  skin/drag helpers and native stacking/placement owners. This is existing
  project code to extend, not infrastructure to rebuild per game.
- Use standard-library enums/frozen dataclasses and injected randomness for
  game data, a shuffled 52-card deck and equal-priority bot choices. Do not
  write a generic deck framework, minimax engine, renderer or event loop.
- The remaining game rules are explicit and small: Blackjack hand totals,
  naturals, hit/stand, fixed dealer draws and comparison; Tic-Tac-Toe legal
  cells, eight winning lines, draws and the agreed move priorities.
- Tk owns buttons, drawn marks, PNG display and scheduled visual steps.
  Neither importing a rule engine nor using Pygame would eliminate the
  agreed player-window/desktop-hand split and its lifecycle work.
- Do not copy an external example wholesale to avoid a dependency. Any later
  source reuse needs the exact upstream revision, retained notices and review
  of its rules; otherwise implement only the bounded rules above.
- If the agreed scope later grows into search difficulty, complex card rules
  or real-time rendering, revisit the relevant library before expanding our
  code. An adopted engine must remain the single game-state owner behind the
  existing typed boundary, with no parallel custom rule implementation.

No new game content API, generative opponent or translation pipeline is needed.
The owner subsequently authorized implementation on the assessed baseline.

## Focused acceptance

- Rules: Blackjack ace combinations, naturals, ties, busts, soft 17 and unique
  draws; Tic-Tac-Toe rows/columns/diagonals, draws, illegal moves, bot priorities
  and alternating starts.
- Menu/lifecycle: dismiss without play, existing admission restrictions, no
  second session, restart, close/shutdown during a turn or flip, timer cleanup,
  no duplicate completion and unchanged RPS behavior.
- Rewards: completed units only; Aiko/player outcome mapping; abandoned rounds
  and merely opening the submenu/window grant nothing. No game-state saves.
- Desktop cards: no hidden face/value leak, hover without reveal/contact,
  readable long hands, scale/edge/taskbar placement, stacking and full cleanup.
- Extend the existing architecture guards (`test_ui_architecture`,
  `test_desktop_boundary`, canonical import/owner tests) to cover the new
  modules; retain the composition-root size limit and dependency rules.
  Exercise the existing `test_game_experience`, RPS sequence/GUI tests,
  desktop lifecycle/preferences/input tests and resource/catalog validation
  at their owning boundaries. Add focused owners for the new rules, menu,
  projections/sequences and card presenter rather than one broad GUI suite.
- RPS GUI tests currently call `HoverUi.open_game()` directly, while
  `tools/capture_rock_paper_scissors_media.py` invokes the play button and
  expects the RPS window immediately. Audit/migrate both consumers to the
  selected-game/submenu path; add separate submenu tests. Do not preserve
  an obsolete direct-RPS entry merely to satisfy old fixtures or weaken
  singleton, reward or architecture assertions.
- Follow the explicit cadence above: targeted rules/application/Tk/architecture
  tests per commit, full local suite and full static gates only after the
  implementation is complete. Record native Windows visual/input acceptance
  separately; automated checks alone do not establish desktop usability.
  Preserve the existing restrictions on visible test windows, mouse control
  and remote CI. Any desktop check outside that scope needs later authorization.
- Update asset notices and maintained UI/fun/architecture documentation with
  the delivered behavior. The delivery evidence below records actual checks.

## Delivery evidence

Targeted GUI checks use the existing local `aiko-local-tests:py311` image,
with a frozen source snapshot, Xvfb, disabled networking and no working-desktop
windows or mouse injection. Each row names the modules passed to
`PYTHONPATH=tests xvfb-run -a python -m unittest <modules> -q`.

| Step | Targeted result |
| --- | --- |
| 1: shared completion contracts | 57 tests passed (1.726s): `test_rock_paper_scissors`, `test_rock_paper_scissors_sequence`, `test_rock_paper_scissors_gui`, `test_game_experience`, `test_ui_architecture`, `test_desktop_boundary`, `test_desktop_lifecycle`. Changed-file Ruff and focused strict Mypy (`hover_ui.py`, `gui.py`) passed. |
| 2: selection menu | 76 tests passed (9.438s): `test_game_menu`, `test_rock_paper_scissors_gui`, `test_hover_isolation`, `test_click_gui`, `test_story_gui`, `test_persistent_windows`, `test_desktop_input`, `test_desktop_lifecycle`, `test_ui_architecture`, `test_content_catalog`. Changed-file Ruff and focused strict Mypy passed. Existing Tcl theme teardown diagnostics were not Python failures. |
| 3: Tic-Tac-Toe rules | `python -m unittest discover -s tests -p test_tic_tac_toe.py -q`: 5 headless Windows tests passed, covering all eight winning lines, draw/invalid actions, score settlement, cancellation, starting alternation and bot priorities. Changed-file Ruff and strict Mypy passed. |
| 4: Tic-Tac-Toe integration | 72 targeted Xvfb tests passed (1.300s): `test_tic_tac_toe`, `test_tic_tac_toe_sequence`, `test_tic_tac_toe_gui`, `test_game_menu`, `test_game_experience`, `test_fun_mood`, `test_content_catalog`, `test_pet_mind_catalogue`, `test_ui_architecture`, `test_resource_validation`. Changed-file Ruff and focused strict Mypy passed. The initial per-board profile is 9 fun / 0.7 energy / 0.9 social, versus RPS's 6 / 0.5 / 0.6, reflecting a longer completed unit without a new reward policy. |
| 5: Kenney cards | 13 targeted Xvfb tests passed (0.085s): `test_playing_card_assets`, `test_resource_validation`. All 53 PNGs match their source hashes; cache reuse, integer scaling, flip frames and Tk-thread release passed. Changed-file Ruff and focused strict Mypy passed. |
| 6: Blackjack rules | 7 headless Windows tests passed: `python -m unittest discover -s tests -p test_blackjack.py -q`, covering ace combinations, naturals, hidden/revealed settlement, soft 17, busts, one-card dealer steps, finite draws/reset and cancellation. Changed-file Ruff and strict Mypy passed. |
| 7: desktop hand | 42 targeted Xvfb tests passed (0.137s): `test_game_models`, `test_blackjack_hand_presenter`, `test_playing_card_assets`, `test_ui_architecture`, `test_desktop_boundary`, `test_desktop_preferences`. Hidden projection, hover, flip midpoint/cancellation, long-hand bounds and same-window scale changes passed. Topmost port invocation is tested; native visual acceptance is separate. Changed-file Ruff and focused strict Mypy passed. |
| 8: Blackjack integration | 89 targeted Xvfb tests passed (1.958s): Blackjack rules/sequence/GUI, Tic-Tac-Toe GUI, menu, game experience/fun, text/dialogue/resource validation, desktop lifecycle/input and architecture boundaries. Changed-file Ruff and focused strict Mypy passed. The initial per-hand profile is 8 fun / 0.6 energy / 0.8 social. Player-only cards, persistent desktop hand across speech, flip cancellation, failed native setup, resize/placement/topmost effects and shutdown cleanup are covered. |
| Visual/integration follow-up | Inspected actual Tk/Xvfb captures of menu, Blackjack and Tic-Tac-Toe in a temporary directory. Widened menu buttons to fit RPS's name, bounded the new headers, centered board content, moved the hand below Aiko's face and reserved taskbar space. Linux uses the same opaque fallback as the sprite; Windows keeps the color key. 19 focused menu/hand/model/new-game GUI tests passed (1.989s), plus changed-file Ruff and focused Mypy. No native Windows visual acceptance is claimed. |
| Capture consumer typing | The RPS media helper explicitly narrows the selected common window to `RockPaperScissorsWindow` before using RPS-only controls. Focused strict Mypy and Ruff passed; 49 RPS sequence/media and architecture/canonical-boundary tests passed (0.692s). The capture helper itself was not launched on the working desktop. |
| 9: integrated contracts | 76 targeted Xvfb tests passed (3.832s): menu, game experience, all three game GUIs, desktop lifecycle and UI/desktop/canonical architecture guards. Maintained architecture/UI/fun/save/asset/smoke guides and the feature/main distinction were reconciled with the delivered code. Full-suite validation is the following final gate. |
| Final static-gate correction | Full Ruff and strict Mypy passed (212 application/tool files). Pyright's first full pass identified test-side common-window/optional-widget narrowing and Pillow pixel types. Added concrete assertions in those tests without widening production interfaces. Full Pyright then passed with zero errors/warnings; 41 affected Xvfb tests passed (5.314s), with targeted Ruff green. No production behavior changed. |
| Headless Windows | 94 focused rules/sequence/application/model/resource/architecture tests passed (1.013s), using the local Python environment without creating any Tk window. Full GUI verification remains in the isolated Linux display. |
| First final full-suite gate | Snapshot `9a30b68`: 1,317 tests in 177.661s, eight Windows-only skips, two failures. The new events needed the catalogue's existing minimum of three variants per relationship; the media-output mock needed the concrete selected RPS window specification. Added the missing variants and updated that fixture without weakening assertions. Also made the new import guard compare module segments. 52 targeted capture/dialogue/architecture/new-game GUI checks passed (2.110s), plus affected Ruff/Pyright. The full suite is rerun on this correction. |
| Right-edge panel placement | A final geometry review found that the new player panels should prefer Aiko's left side when no space remains on her right. Interrupted the second full run before any result, corrected shared `GamePanel` placement and added the actual-host edge regression. Ten focused new-game GUI/model checks passed (1.075s), plus affected Ruff/Mypy/Pyright. A fresh final full run follows this production correction. |
| Final full-suite gate — passed | Frozen source at `8dc61e7b9583a8288245084a74247243fe3585d1`: **1,318 tests in 177.825s, eight platform skips, zero failures/errors**. Command: `PYTHONPATH=tests xvfb-run -a python -m unittest discover -s tests -q`, Python 3.11 in the local network-disabled container. The existing Tcl theme teardown messages did not produce Python errors. Prepared-asset checks ran inside the disposable snapshot, preserving the working tree. |
| Final static gates — passed | On the same implementation tree: `python -m ruff check aiko_pet tests main.py tools`; `python -m mypy --strict --no-incremental aiko_pet main.py tools` (212 source files); `python -m pyright --project pyrightconfig.json` (zero errors/warnings). Versions: Ruff 0.13.2, Mypy 1.18.2, Pyright 1.1.414. This final evidence edit changes documentation only and does not require another full-suite run. |

All nine planned delivery stages are complete, with separate bounded corrective
commits documented above. No runtime dependency, save migration, normal-save
write, working-desktop window/mouse probe, remote CI, push or merge was performed.
Native Windows acceptance remains the explicit checklist in
[World smoke checks](WORLD_SMOKE_TEST.md#three-game-native-acceptance--pending-separately),
not a claim inferred from Xvfb. Pre-existing social-content documentation edits
remain outside these game commits.

## Review corrections — 2026-10-19

The subsequent review reproduced three lifecycle defects. Each correction was
implemented in its existing owner and committed separately after focused checks.
The new regression checks failed before their respective corrections; they
exercise real Tk button/focus events, the registered `WM_DELETE_WINDOW`
callbacks, and injected construction failures, rather than only invoking game
selection or normal close methods directly.

| Commit | Correction and ownership | Focused validation |
| --- | --- | --- |
| `a52f610` | `HoverUi` keeps the toolbar in the selector's interaction area, so delayed focus checks and global polling of the opening click cannot dismiss it. True outside dismissal is preserved, without an extra grace timer. | 64 Xvfb tests passed (4.218s): `test_game_menu`, `test_hover_isolation`, `test_click_gui`, `test_persistent_windows`, `test_desktop_input_controller`, `test_desktop_input`, `test_ui_architecture`. Changed-file Ruff, strict Mypy and Pyright passed. |
| `ddddd1a` | `GameMenu` and shared `GamePanel` route system close through their existing owners. The same missing connection was corrected in RPS's own window, retaining its separate presentation. No second teardown owner was added. | 74 Xvfb tests passed (4.832s): `test_game_menu`, `test_blackjack_gui`, `test_blackjack_sequence`, `test_blackjack_hand_presenter`, `test_tic_tac_toe_gui`, `test_tic_tac_toe_sequence`, `test_rock_paper_scissors_gui`, `test_rock_paper_scissors_sequence`, `test_desktop_lifecycle`, `test_ui_architecture`. Checks cover pending turns/flips, empty card cache, stale callbacks, reopening and once-only completed-hand rewards. Changed-file Ruff, strict Mypy and Pyright passed. |
| `d569b40` | `TicTacToeWindow` destroys its own partial panel if setup fails. It does not emit completion for a session the host never accepted; `HoverUi` retains reservation and mode cleanup. | 60 Xvfb tests passed (3.238s): `test_tic_tac_toe_gui`, `test_tic_tac_toe_sequence`, `test_game_menu`, `test_blackjack_gui`, `test_game_experience`, `test_ui_architecture`, `test_desktop_lifecycle`. Both initial rendering and panel-show failure leave no extra root children, no reward or game mode, and allow a fresh session. Changed-file Ruff, strict Mypy and Pyright passed. |

The complete suite and full static gates were started only after all three
production corrections were committed. They use the same isolated local setup
as delivery above. Native Windows acceptance remains separate; the smoke
checklist now explicitly includes opening-click persistence and system close.

Final validation of the corrected code at
`d569b40711b5efc43d07fb5557a49f921cb36a14`:

- `PYTHONPATH=tests xvfb-run -a python -m unittest discover -s tests -q`:
  **1,325 tests in 178.653s, eight platform skips, zero failures/errors**.
  The network-disabled local container used a frozen source snapshot;
  prepared-asset checks did not alter the checkout. Existing Tcl theme
  teardown diagnostics did not produce unittest failures.
- Full `python -m ruff check aiko_pet tests main.py tools` passed.
- Full `python -m mypy --strict --no-incremental aiko_pet main.py tools`
  passed for 212 source files.
- Full `python -m pyright --project pyrightconfig.json` passed with zero
  errors/warnings.

This evidence and the UI/smoke contract updates are documentation only. No
subsequent production or test changes, working-desktop probes, normal-save
writes, pushes or merges were performed. The pre-existing social-content
documentation changes remain outside these correction commits.

## Blackjack playtest follow-up — 2026-10-19

The owner reported the three-game playtest acceptable and requested a larger
player hand, drawing through a pile and automatic next hands for Blackjack.
These decisions supersede the initial Blackjack manual-next-round controls
recorded in the original delivery sequence. Tic-Tac-Toe's controls and Aiko's
desktop hand retain their existing behavior.

| Commit | Bounded implementation | Focused validation |
| --- | --- | --- |
| `fd66cdf` | Render player cards on 128×128 canvases in a 480×144 hand area. Reuse the existing integer-scaled image cache. Compose three copies of the same back into a cached native draw-button image, without introducing deck state or new assets. Release that image with the shared cache on close. | 58 Xvfb tests passed (3.523s): `test_blackjack_gui`, `test_blackjack_hand_presenter`, `test_playing_card_assets`, `test_game_menu`, `test_tic_tac_toe_gui`, `test_game_models`, `test_ui_architecture`. Checks cover larger player cards, unchanged Aiko size, long-hand bounds, clickable/disabled drawing, transparent layered backs and image release. Affected Ruff, strict Mypy and Pyright passed. |
| `4af6de3` | Use `BlackjackSequence`'s single cancellable timer for the 2.8-second result pause and next hand. Derive the transition from the game's settled result; add no second phase/score owner. Remove Blackjack's manual-next methods and omit `GamePanel`'s now-optional button there. | 87 Xvfb tests passed (3.848s): `test_blackjack`, `test_blackjack_sequence`, `test_blackjack_gui`, `test_blackjack_hand_presenter`, `test_tic_tac_toe_gui`, `test_game_menu`, `test_game_experience`, `test_fun_mood`, `test_desktop_lifecycle`, `test_ui_architecture`. Injected-clock checks cover timing, blocked input, accumulated score, re-masking, consecutive naturals and cancelled/stale restart callbacks. An actual Tk timer also restarts a hand in the host-wiring test. Affected Ruff, strict Mypy and Pyright passed. |

Rechecked the local Playing Cards Pack PNG variants: 16×16, 32×32 and 64×64.
The existing imported 64×64 originals are the largest variant. No replacement
asset or extra runtime dependency is needed. Actual Tk/Xvfb captures of two
and four enlarged player cards, the result pause and the following hand were
inspected. A separate real 2.8-second Tk-timer probe confirmed automatic
restart, preserved score and a newly concealed dealer card. These checks used
temporary saves and the existing local network-disabled container; no
working-desktop window or mouse probe was run. The current player-panel/native
acceptance checklist includes this follow-up.

Full-suite and full static validation follow completion of both implementation
commits; the final results below identify their frozen source.

Final gate at `4af6de3d345822e100913fab9d99420c8f29cb33`:

- Full isolated suite: **1,332 tests in 177.510s, eight platform skips,
  zero failures/errors**, using
  `PYTHONPATH=tests xvfb-run -a python -m unittest discover -s tests -q`.
  The existing Tcl theme teardown diagnostics did not produce test failures.
- Full Ruff passed: `python -m ruff check aiko_pet tests main.py tools`.
- Full strict Mypy passed for 212 files:
  `python -m mypy --strict --no-incremental aiko_pet main.py tools`.
- Full Pyright passed with zero errors/warnings:
  `python -m pyright --project pyrightconfig.json`.

The following documentation reconciliation changes no production or test code.
Pre-existing social-content documentation remains outside these commits. No
normal-save writes, working-desktop probes, remote CI, pushes or merges were
performed for this follow-up.

## Connect Four extension (Vier gewinnt)

**Owner decision, 2026-10-23: implementation authorized and delivered locally.** Use yellow and red Kenney
pieces, project-owned local game rules with a bounded opponent search, and
contextual Aiko reactions. The experience below records the first implementation;
opponent strength remains a tuning choice rather than a difficulty guarantee.
The horoscope stays at its current prototype stage; its future hat/book scene
is not a prerequisite or part of this game extension.

### Round flow and player presentation

- Add **Vier gewinnt** to Spielen through the existing single-game admission
  and window lifecycle. Selecting it opens one shared seven-column, six-row
  board in the player window; Aiko remains on the desktop as the opponent.
- Give the player and Aiko fixed, clearly labelled yellow/red piece identities
  throughout a session: yellow for the player, red for Aiko. Show the active turn
  and temporary player/Aiko/draw counts. Keyboard keys 1–7 also select columns.
- Hovering a legal column previews the next piece/landing position. Clicking
  drops one piece into its lowest empty cell, with a short fall animation.
  A full column cannot accept a move or consume a turn.
- The player starts the first round; alternate the starter after each completed
  round. Aiko makes one legal move after a short thinking pause and uses the
  same fall presentation. Block extra drops during turn/fall resolution, while
  keeping close available and the Tk event loop responsive.
- Four or more connected pieces horizontally, vertically or diagonally win.
  Highlight the winning cells, keeping a win on the final move distinct from
  a full-board draw. Keep the settled result visible until **Nächste Runde**.
- Count each completed round once. Closing cancels pending presentation/search
  results and discards the unfinished round and transient session board/score.
  Do not add persistent lifetime statistics or an automatic next-round timer.

### Local rules and bounded opponent

- Use a small project-owned rule implementation and a limited local
  Minimax/Negamax search with Alpha-Beta pruning. No API, language model,
  training service or new game-engine dependency is selected.
- Aiko takes an immediate win, otherwise blocks an immediate playable player
  win where possible. Evaluate further candidates using a bounded lookahead,
  center access, expandable lines and opponent replies; avoid handing over an
  immediate win when a safe move exists.
- Search four individual moves ahead (two per participant), with Alpha-Beta
  pruning and a 5,000-node ceiling. Search an immutable snapshot in one worker
  thread; poll results on Tk after a minimum 650 ms thinking pause. Closing
  signals cancellation and invalidates pending callbacks/results.
- Vary equally rated legal choices without overriding immediate tactical wins
  or defenses. Keep one normal strength initially; mood/friendship may affect
  expression, but do not silently change playing strength or manufacture losses.
- Reuse the current game's presentation/lifecycle helpers and suitable clearly
  licensed components when they simplify integration. No easyAI, OpenSpiel or
  PettingZoo package is approved for installation; a later library adoption
  would require a concrete technical and license review.

### Selected Kenney assets

The local Dropbox **Kenney Game Assets All-in-1 3.4.0 / 2D assets / Boardgame
Pack (1.0)** was inspected. Selected frontal pieces, relative to that pack:

| Use | Existing source | Inspected format |
| --- | --- | --- |
| Yellow piece | `PNG/Pieces (Yellow)/pieceYellow_single10.png` | Transparent 64×64 PNG |
| Red piece | `PNG/Pieces (Red)/pieceRed_single11.png` | Transparent 64×64 PNG |

The supplied `License.txt` identifies CC0 and permits personal, educational and
commercial use; [Kenney's pack page](https://kenney.nl/assets/boardgame-pack)
also identifies CC0. Both originals are packaged under `assets/connect_four/`,
with the supplied license and source paths/SHA-256 hashes in `provenance.json`.
Runtime uses packaged assets rather than Dropbox.

The source named Red looks orange in the current preview. Yellow/red is the
selected color pair; the original palette is preserved and the legend labels
both participants. The previously shown blue piece is not part of this pair.
Draw the grid, hover preview and winning highlight with Tk and reuse the current
window styling. No newly generated board/piece or character artwork is required
for this first version.

### Aiko's contextual reactions

Keep Aiko's comments and emotes on the existing desktop speech surface, with
occasional matching existing character clips. The shared board owns the player's
input and piece layout. Emotes and text alternate on their existing surface.

| Trigger | Proposed existing presentation | Draft German tone example |
| --- | --- | --- |
| Start | Calm/attentive standing pose | „Mhm. Vier in einer Reihe. Ich behalte deine Diagonalen im Auge.“ |
| Aiko blocks a playable immediate win | Brief idea emote | „Ah-ah. Den vierten Platz lasse ich dir nicht einfach frei.“ |
| Player blocks Aiko's playable immediate win | Brief head tilt | „Du hast die Lücke gesehen. Hmpf. Dann eben anders.“ |
| Aiko wins | Short existing happy jump | „Vier! Hihi. Die Reihe gehört mir.“ |
| Player wins | Restrained head tilt or sad emote, then normal posture | „Oh … vier. Gut gespielt. Ich möchte eine Revanche.“ |
| Draw | Short pause | „Alles voll. Wir haben uns ziemlich gründlich gegenseitig aufgehalten.“ |

The dialogue catalogue contains three variants per trigger (18 lines total).
Existing `idle`, `review` and `jumping` clips accompany these cues; no new
character frames are imported. Reactions follow actual board evidence; a floating
three-piece pattern without a legal winning drop is not an immediate threat.
Use sparse intermediate comments rather than speech every turn, readable
length-based text durations and short emote beats. Preserve each line's reading
opportunity; avoid a stale comment/result appearing over a new round.
Final text remains capped at 125 characters. Text uses the shared conversation
reading time, including the final second; emotes precede speech for 800 ms.
Intermediate comments are separated by at least six moves. The short fall uses
six 30 ms frames; player input and the next-round button wait until the current
drop/reaction finishes, so another turn cannot replace a readable line.

### Ownership and verification

| Owner | Responsibility |
| --- | --- |
| `ConnectFourSession` under `games/` | Sole mutable board/turn/outcome/session-score owner; rules, legal moves and bounded opponent policy; immutable projections and injected randomness. No Tk, pet-state or World writes. |
| `ConnectFourSequence` beside existing game sequences | Cancellable turn, thinking, drop and reaction pacing; drive the session without duplicating rules or score. Reject stale search results. |
| `ConnectFourWindow` and the existing game host/presentation | Render snapshots and forward legal input; reuse `GamePanel`, `GameSpeech` and the single active-window owner. Pieces remain temporary game graphics, not World items or gifts. |
| Existing game-experience application path | Typed identity/summary/round adapters use once-only completion in `GameExperienceCoordinator`. Reuse Tic-Tac-Toe's completed-round fun profile; no new friendship formula, wish targets, save fields or balance values. |

Tests cover gravity/full columns, all winning directions (including longer and
crossing lines), draw versus last-move win, alternating starters, immediate
win/block decisions and search bounds. Controlled sequence tests cover reading
time, emotes, duplicate input, cancellation and stale callbacks. Native Tk tests
exercise the actual host with isolated saves, hover/click/drop presentation,
result/revanche, once-only completion, failed construction and reopening.

Development-worktree validation on 2026-10-23 (including the separate horoscope
prototype and parallel character-asset work):

- 23 new rule/search, controlled sequence, asset-provenance and native Tk tests
  passed. An 88-test combined run also passed, including menu layout/admission,
  game experience, existing wishes and the unchanged horoscope prototype.
- Repository Ruff, strict whole-application Mypy (269 source files), Pyright
  (including tests) and whitespace checks passed.
- A native Windows preview with a temporary isolated save confirmed yellow/red
  contrast, the legal-column preview, fall, winning highlight, readable desktop
  speech and manual next-round controls. A separate real-worker turn through the
  actual host completed correctly; a narrow 320×700 bounds test keeps the board
  scrollable and the footer accessible. The red source retains Kenney's original
  orange tone. Screenshots remain local outside Git.
- A development probe over 19 legal opening/midgame snapshots measured roughly
  4–38 ms per search on this machine. This is a sample, not a latency/difficulty
  guarantee. Runtime still uses a cancellable worker and the 650 ms minimum pause.
- Final complete native Windows suite: **1,810 tests passed in 247.846 seconds**
  (`python -m unittest discover -s tests -q`). Existing character-export work was
  preserved separately; game-specific expectation updates keep the wish catalogue
  unchanged and verify that the fourth menu choice remains reachable by scrolling.

The scoped Connect Four commit was also checked in a separate export of its
staged contents, without the uncommitted horoscope or character-asset changes:
**1,779 unit/GUI tests passed in 251.695 seconds**, together with Ruff, strict
Mypy (263 source files), Pyright and the staged whitespace check. Shared files
contain only the Connect Four additions; the existing wish targets stay intact.

Horoscope application/codec/playback/settings logic remains at the existing
prototype and is excluded from the Connect Four commit, together with parallel
character-asset changes. This change adds no API, key, external service or runtime
dependency. No push or merge is authorized.

## Mastermind extension

**Owner decision, 2026-10-23: implemented locally after explicit authorization.**
Aiko is the code setter. The player solves her fixed code with packaged Kenney
pieces and project-owned Python-standard-library rules. The corrected UI has
**ten prepared attempt rows**, each with four empty pin slots and an adjacent
feedback group. Drag pins from the palette into the active row; earlier submitted
rows remain as the visible history. This is ten attempts within one round.
The horoscope prototype and parallel character-asset work remain unchanged.
No commit, push or merge is included in this implementation request.

### Roles and round presentation

- Aiko selects one code at the start and keeps it unchanged for the entire
  round. The first version has no role reversal or solver playing as Aiko.
- Keep a small code strip beside Aiko on the desktop throughout the round,
  separate from both her speech bubble and the player's game window. It has
  four concealed positions, matching the agreed code length.
- Show identical neutral covers during play. Hovering or clicking the strip
  must not reveal colors, positions or other hidden information.
- The player window owns color selection, submitted guesses, their feedback
  and round controls. Aiko comments on submitted guesses through her existing
  text/emote surface, with readable shared conversation timing.
- At a solved or exhausted round end, uncover the actual code sequentially
  on the desktop, then present Aiko's result reaction. The code remains visible
  for the result; a new round starts concealed again.
- Use the Blackjack desktop-hand presentation as a reference for anchoring,
  scaling, topmost preferences, stacking and cleanup. Give the code strip its
  own side-placement calculation: choose the available side, switch sides near
  a screen edge, and keep Aiko's face, speech and player controls readable.
- Follow Aiko's position while the game is open. Closing or failed setup must
  clear the strip and cancel pending reveal/reaction callbacks. The code and
  round history remain transient game state, outside pet saves and World items.

### Agreed Mastermind rules

**Owner decision, 2026-10-23: implemented first-version rules.**

| Rule | Selected behavior |
| --- | --- |
| Code length | Four positions, with order significant. |
| Palette | Six colors: red, yellow, blue, green, purple and white. |
| Attempts | Ten submitted guesses per round, without a time limit. |
| Repeated colors | Allowed in both the secret and guesses, including the same color in all four positions. |
| Secret | Selected once at the start and unchanged throughout the round. |

Only a complete, explicitly confirmed four-color guess consumes an attempt.
The player may edit the current guess freely before submission. Palette drops
copy colors (allowing duplicates); dragging an existing draft pin swaps slots.
Drops outside the active row, onto earlier/later rows or clipped board areas
are rejected without changing the draft. Only **Prüfen** submits all four pins.
Optional keys 1–6 select colors, Left/Right select a slot, Delete clears it and
Enter confirms while the palette has focus. Four exact
matches win, including on the tenth attempt; check this before declaring an
exhausted-round loss. After ten unsuccessful guesses the round ends, and Aiko's
desktop strip reveals the secret using the staged end-of-round presentation.

Display feedback beside each submitted guess as a compact group of four marks:

- A **black filled mark** means the correct color in the correct position.
- A **white mark with a dark outline** means a correct color in another position.
- Unused places remain neutral gray placeholders and do not count as matches.
- Add explicit numeric counts, for example **"1 genau · 2 nur Farbe"**, and a
  permanently visible legend. Color alone must not carry the explanation.
- Group marks by feedback type; they must not map to individual guess positions
  or reveal which positions are correct.

Count each secret/guess piece at most once. Assign exact matches first, then
count matching remaining colors by multiplicity, so repeated colors cannot
inflate the result. Example: secret **red–red–blue–green**, guess
**red–blue–red–yellow** yields **one exact and two misplaced** matches.

### Existing Kenney assets

The previously inspected local **Kenney Game Assets All-in-1 3.4.0 / 2D assets /
Boardgame Pack (1.0)** contains matching frontal transparent 64×64 PNG pieces.
Packaged source paths below are relative to that pack; filenames differ by
color, so a shared numeric suffix must not be assumed.

| Packaged use | Inspected source |
| --- | --- |
| Yellow code piece | `PNG/Pieces (Yellow)/pieceYellow_single10.png` |
| Red code piece | `PNG/Pieces (Red)/pieceRed_single11.png` |
| Blue code piece | `PNG/Pieces (Blue)/pieceBlue_single09.png` |
| Green code piece | `PNG/Pieces (Green)/pieceGreen_single10.png` |
| Purple code piece | `PNG/Pieces (Purple)/piecePurple_single11.png` |
| White code piece | `PNG/Pieces (White)/pieceWhite_single10.png` |
| Neutral cover | `PNG/Pieces (Black)/pieceBlack_single10.png` |

The supplied license and [official pack page](https://kenney.nl/assets/boardgame-pack)
identify CC0; the supplied text permits personal, educational and commercial
use. Provenance and the license accompany the packaged import. Yellow and red
are already packaged for Connect Four; reuse suitable existing assets rather
than introducing duplicate copies. The red source retains its orange tone.
Runtime uses packaged files, without depending on Dropbox.

Draw the strip, cover framing and feedback fields with the existing Tk/VN
styling. No new generated character or game artwork is needed for this initial
version. White pieces have a contrasting backing. Palette labels and numbered
pins supplement color; the neutral cover carries a question mark. The ten-row
board scrolls when necessary, retaining the palette above it.

### Local rules and library choice

- Use the existing Python runtime and Tk interface. Select the secret locally
  with standard-library random selection; use `collections.Counter` or equivalent
  multiset counting for color feedback, including correct treatment of repeated
  colors under the agreed rules.
- Keep code generation and feedback in a small pure game-rule module. Aiko is
  the code setter, so this version needs no opponent search, language model,
  API, API key or paid service. It must be usable offline at no additional cost.
- No new external package is selected. The researched PyMasterMind and
  python-constraint2 alternatives remain unadopted; a future need for an Aiko
  solver would require a separate decision and dependency/license review.

### Implemented ownership and pacing

| Owner | Responsibility |
| --- | --- |
| `MastermindSession` under `games/` | Sole owner of the secret, submitted guesses, feedback and result; expose immutable views and keep hidden colors out of unrevealed UI projections. No Tk, PetState or World writes. |
| `MastermindSequence` beside the existing game sequences | Coordinate submission, feedback, staged reveal and Aiko's reactions with cancellable callbacks. |
| `MastermindCodePresenter` under `ui/pet_view/` | Render only masked positions during play and revealed pieces at round end; own the anchored desktop strip and its cleanup, following the Blackjack pattern. |
| `MastermindWindow` and existing game host | Own player input and round presentation; preserve single-game admission and forward actions to the session/sequence. |

`MastermindDrag` owns only its local Tk grab and temporary drag image; it never
attaches global input hooks or writes World state. Invalid drops preserve the
draft. Closing releases the grab, destroys the image and cancels the sequence.
`MastermindWindow` renders all ten rows immediately, with only the current row
editable. `GameCodePorts` connects the passive code strip; the existing game host
retains admission, topmost and once-only completion ownership.

Initial viewport correction (2026-10-26): all ten rows are drawn before input.
The prepared board height is retained while Tk still reports an unmapped
one-pixel body. MastermindWindow listens to the actual body viewport allocation
and board-frame placement before mapping, rather than waiting for another
top-level configure/input event. The frame's top padding is already included in
its y position, so only the bottom padding is deducted from the usable height.
Layout remains coalesced through one idle callback; preparation replaces older
pending work and closing cancels it. Large work areas show all ten rows without
a click; genuinely constrained areas keep a scrollable board.

Verification: 59 targeted tests pass in an isolated Git-tree export, including
the first-map/no-input case, constrained geometry, pending-layout cancellation,
all Mastermind GUI/rule/sequence tests and shared menu/scroll/game layouts.
The existing drag-cleanup fixture now generates motion before expecting a drag
preview, matching the click-versus-drag contract; production drag logic is
unchanged. Ruff and strict Mypy pass; only the two previously recorded unrelated
Pyright findings remain. No Computer Use workflow or normal save was used.

After confirmation Aiko places the four feedback marks at **90 ms intervals**.
Their grouping remains unordered: exact marks first, then misplaced, then unused.
Numeric counts appear after the fourth mark. Input stays blocked during this
sequence. At a terminal guess, settlement occurs after that feedback finishes;
closing earlier awards nothing. Closing during the subsequent code reveal keeps
the completed unit. The four secret pieces reveal at **180 ms intervals**, then
Aiko uses jumping/star for the player's win or review/idea for her own win.
Emotes precede dialogue by **800 ms**. Authored lines use shared conversation
reading time, including its final second; there is no automatic round restart.
Sparse comments follow guesses 3 and 6 (question emote) and guess 9 (last attempt).

`games/mastermind.py` uses `secrets.choice` and `collections.Counter`, without a
solver, dependency or external service. `MastermindImages` reuses the red/yellow
Connect Four files and loads only five additional unmodified CC0 PNGs (blue,
green, purple, white and the black cover). `place_code` chooses a bounded side
position while considering Aiko, speech and the player panel; the presenter
receives only masked or explicitly revealed `CodeView` snapshots.

No new balance values, friendship rules, wish targets or save fields are added.
Mastermind reuses the existing Tic-Tac-Toe fun profile through an explicit alias.
The existing game-experience adapter credits completed units on close exactly
once. An unfinished round has no reward. Code, drafts and scores are transient.

### Implementation verification

Tests cover multiplicity with an independent exhaustive 6,561-pair oracle,
invalid/incomplete guesses, the tenth-attempt win versus exhaustion, fixed secret
ownership, serial feedback/reveal, cancellation and once-only settlement.
Native Tk tests send actual drag press/motion/release events into prepared rows,
check draft swaps, repeated colors, rejected drops, immutable submitted rows,
local-grab cleanup, concealed-strip input, reopening, failure cleanup, narrow
bounds and 1x/2x positioning. Native Windows previews use temporary isolated saves;
preview images remain outside Git. Final check results are recorded below.

Development-worktree verification on 2026-10-23:

- **22 new Mastermind rule, sequence, native Tk and provenance tests passed**;
  together with the existing UI architecture guards, **48 tests passed**.
- Final complete native Windows suite after the drag-and-drop/layout corrections:
  **1,837 tests passed in 250.775 seconds**
  (`python -m unittest discover -s tests -q`).
- Repository CI-scope Ruff (`aiko_pet tests main.py tools`), strict Mypy across
  277 application/tool source files, Pyright including tests, and whitespace
  checks passed. Existing unrelated local asset-build scripts remain untouched.
- Native previews with temporary isolated saves checked the ten-row board,
  partial/full code reveal, retained feedback and the 1x/2x strip. A native
  320×700 bounds test also drags into the tenth row with the palette/confirmation
  controls visible and verifies scroll/grab cleanup.
- All five imported PNGs match their original pack files byte for byte; the
  included CC0 license retains its original wording. Red/yellow files are reused.
- Hash comparison against the starting worktree confirmed 73 other pre-existing
  dirty/untracked files unchanged, including the horoscope implementation and
  parallel character exports. Shared files contain the required game wiring,
  text contracts, catalogue assertions and documentation additions.

The preceding results were recorded during the original development pass before
the Mastermind source was committed. Its native previews/full-suite checks are
historical results and were not repeated for the following delivery.

### Headless baseline delivery before wish slice 1A

At the owner's request, secure the completed Mastermind implementation as a
separate baseline commit before enabling its game wishes. Stage only Mastermind
portions of shared files; preserve parallel horoscope and character-asset work.

An isolated copy of the exact staged baseline passed **68 targeted tests in
0.271 seconds**: Mastermind rules/sequence, pure placement/provenance, existing
game experience and wishes, and UI architecture. `_tkinter.create` was blocked
throughout this run, so it could not create native test windows. The slowest
individual test took 0.057 seconds. Changed-file Ruff, strict Mypy for eighteen
affected source files and focused Pyright passed. No full suite, mouse control
or GitHub CI was run for this delivery. No merge is authorized or performed.

## Quiz concept (planning only)

Owner decisions recorded on 2026-10-25. This section is the planning authority
for the quiz direction and supersedes the exploratory source/theme suggestions
in [minigame candidates](MINIGAME_CANDIDATES.md#quiz-and-content-driven-game-variations).
The owner subsequently authorized authoring the 200-question catalogue after
adding film and television. A subsequent explicit implementation request
authorized the local quiz runtime described in the delivery section below.
Separate feedback storage/settings and a feedback service remain future work.
The selected starting scope is **200 reviewed German questions**, with the
topic/difficulty counts and question information described below. The agreed
session flow and Aiko's role are also recorded here. Catalogue authoring is a
separate editorial deliverable; this section retains the planning history while
the delivery section records its implemented scope.

The owner explicitly classifies the quiz as a **game**. Its future entry is
**Spielen > Quiz**, using the existing game admission/lifecycle flow. Aiko's
quizmaster performance does not turn it into a social/entertainment action.
The social menu and horoscope prototype are outside this implementation scope.

### Audience and topic distribution

Use accessible general knowledge with an emphasis on gaming, anime/manga,
science fiction and fantasy. The quiz must work beyond the owner's personal
interests. Recognizable characters, worlds, concepts and cultural knowledge
are appropriate; detailed programming-language knowledge, obscure minor
characters, episode numbers, damage values and edition-specific trivia are
outside the intended scope.

| Group | Topic | Target share of catalogue | Starting question count | Content orientation |
| --- | --- | --- | --- | --- |
| Nerd topics | Gaming | 20% | 40 | Familiar characters, game concepts, classics and consoles |
| Nerd topics | Anime and manga | 15% | 30 | Well-known works, main characters and basic concepts |
| Nerd topics | Science fiction | 15% | 30 | Familiar worlds, characters and genre concepts |
| Nerd topics | Fantasy | 10% | 20 | Familiar works, mythical creatures and mythology |
| General knowledge | Nature and science | 10% | 20 | Space, animals and everyday phenomena |
| General knowledge | World, history and culture | 10% | 20 | Places, inventions, language, books and music |
| General knowledge | Film and television | 10% | 20 | Familiar films, series, animation, creators and screen culture |
| General knowledge | Computers and digital culture | 10% | 20 | Everyday technology, the internet and computing history |
| **Total** | **All topics** | **100%** | **200** | **120 nerd-topic / 80 general-knowledge questions (60% / 40%)** |

Each question has one primary topic for distribution accounting. Cross-topic
connections are welcome but must not count the same question twice. Computers
and digital culture belong to the general-knowledge allocation above.
Film and television is also general knowledge in this allocation. Classify
genre-specific questions about science fiction, fantasy or anime under their
respective topics; use film/television for other screen stories and general
screen culture, including general family-animation knowledge. Count each
question only once.

### Difficulty distribution

| Difficulty | Target share of catalogue | Starting question count | Intended knowledge level |
| --- | --- | --- | --- |
| Easy ("Leicht") | 50% | 100 | Solvable through incidental familiarity with the topic |
| Medium ("Mittel") | 35% | 70 | Basic familiarity and recall help |
| Tricky ("Knifflig") | 15% | 30 | More deliberate recall or reasoning, still without specialist knowledge |
| **Total** | **100%** | **200** | |

Apply this mix across the catalogue and approximately within each topic, with
small per-topic rounding while preserving the overall 100/70/30 counts in the
starting set. Anime/manga must not become the difficult category by
default. Difficulty comes from the knowledge or reasoning required, not from
ambiguous wording, trick answers or obscure detail. Questions should have a
clear solution and plausible, clearly incorrect alternatives.

These are editorial target shares, not exact quotas for every short game.
Initial difficulty labels are estimates to revisit using player feedback;
a wrong answer alone does not establish that a question is too difficult.

### Starting catalogue scope and question information

The 200-question starting set must span multiple subtopics and works within
each main topic. Avoid letting one franchise dominate its category or a session.
Rewordings of the same fact do not constitute additional variety. The first
set should primarily use durable knowledge to limit ongoing editorial work.

Use the following information for each question. This is an editorial content
contract. The authored draft below uses JSON for review and exchange; that
does not select a runtime serialization format, database schema or loader.

| Information | Purpose and requirement |
| --- | --- |
| Stable question identifier | Identify the question across sessions, repetition tracking and feedback. |
| Content revision | Associate feedback with the wording and answers actually presented; do not silently transfer old ratings to a changed version. |
| Question text | Short, self-contained German wording; no missing context from another question. |
| Four answer choices | Exactly one correct answer and three plausible, clearly incorrect alternatives. |
| Correct-answer reference | Unambiguously identify the correct choice even when display positions are shuffled. |
| Primary topic | Exactly one of the eight agreed topics for distribution accounting. |
| Subtopic and, where applicable, work/franchise | Support variety and avoid grouping similar facts or the same franchise too heavily in a session. |
| Difficulty | Easy, medium or tricky according to the agreed knowledge and reasoning criteria. |
| Short explanation | One or two sentences when they add useful context to the resolution; avoid merely repeating the answer. |
| Verification source(s) and review date | Make the evidence for the solution and the date of editorial checking traceable. |
| Content origin and reuse rights | Distinguish authored wording from reused material; for reused content, retain the source, author, applicable licence and required credit/modification information. |
| Editorial status | Draft, approved or temporarily disabled; only approved questions are eligible for play. |

For time-dependent claims, additionally record a clear reference date or period
and make that scope understandable in the question. A review date alone does
not make an otherwise undated changing fact unambiguous.

Keep factual question content separate from Aiko's quizmaster comments. Do not
require bespoke reactions for every question and friendship tier; her response
is driven by the answer outcome, existing friendship/current state and the
observed session situation. The factual explanation belongs to the question.

Keep player history and ratings separate from the distributed question content.
They refer to a question by its stable identifier and relevant content revision.
This preserves the meaning of earlier feedback after editorial corrections.
It does not settle storage, retention or transmission design, which remain
open in the feedback section below.

### Agreed quiz session flow

- One session contains **ten questions**, each with **four answer choices**
  and exactly one correct solution. There is **no time limit**, speed bonus
  or elimination after an incorrect answer.
- Aiko opens the session with a brief introduction. Mix topics and difficulty
  without repeating a question within that session; prefer questions not
  recently presented where the available pool permits. The catalogue shares
  above are long-term editorial targets, not rigid quotas for every session.
  Mix the order rather than making the final questions invariably harder.
- The player window keeps the complete question and all four answer choices
  readable, with progress such as **"Frage 3 von 10"**. Clicking an answer
  commits the choice once and prevents further answers to that question.
  Keyboard shortcuts **1-4** remain an optional input convenience to assess.
- After commitment, clearly distinguish the selected answer and the correct
  solution. Add a short explanation when it contributes useful context.
  Keep the question and resolution readable in the player window; Aiko's
  speech bubbles carry her framing and reactions.
- The player selects **"Weiter"** to proceed. Do not automatically advance
  or hide the resolution after a timer. Aiko gives the player thinking time
  without impatient nudges or answer-revealing expressions.
- Each correct answer counts as one point, independent of difficulty.
  After question ten, show the score out of ten, Aiko's closing reaction,
  **"Noch eine Runde"** and **"Beenden"**. A fresh session starts only on
  request. The ordinary close/exit path remains available during play.
- Keep question ratings in the separate settings area described below;
  neither answering nor finishing a session introduces a feedback prompt.

### Aiko's playful quizmaster role

Aiko stages a small quiz show on the player's desktop. Like the planned
fortune-teller performance, this is a consciously played role with a beginning,
an ongoing performance and a closing moment. It is a presentation analogy,
not a dependency on the horoscope, tarot, fortune-teller hat or floating book.

Her light anime/chibi personality remains visible beneath the performance:
enthusiastic, curious and occasionally ceremonious about her tiny desktop
stage. She knows the solutions and acts as quizmaster and companion; do not
invent a competing Aiko score or pretend she is independently guessing.

- Occasionally let her composure slip through sincere excitement, nerdy
  enthusiasm, a dry desktop-life aside or genuine encouragement. Role breaks
  vary by situation and do not happen after every question. Returning to the
  role must not rely on one repeated apology/catchphrase.
- Reuse suitable existing attentive, pleased, playful or thoughtful expressions
  and emotes. Larger gestures belong at selected moments, such as the opening
  or finale; each answer does not require an animation or long comment.
  This plan does not select or authorize new character artwork or props.
- Comments and light teasing must sound like Aiko speaking to this player,
  shaped by their actual friendship and her current state. Do not substitute
  a generic competitive TV-host persona or compulsory jokes for that relationship.

Use the established [friendship and voice contract](DIALOGUE_REVISION_PLAN.md#freundschaft-und-stimme)
and its unchanged friendship tiers as the editorial reference:

| Existing relationship | Intended quiz-comment tone |
| --- | --- |
| Acquaintance (1-2) | Reserved, polite, tentatively playful; do not assume an established teasing relationship. |
| Familiar (3-5) | More personal and relaxed, with occasional mild situational teasing. |
| Friend (6-8) | Open, lively and cheekier; shared playfulness can carry more direct banter. |
| Close (9-10) | Warm, familiar and candid; affectionate teasing alongside equally direct encouragement. |

Closeness permits a more familiar voice, not progressively harsher or more
frequent put-downs. Tease the particular choice or playful situation, never
the player's intelligence, worth or supposed personal failings. Do not claim
to know whether they guessed or what they were thinking. Repeated mistakes
are not a reason to escalate teasing; allow supportive or brief neutral
reactions instead. Her own exaggerated performance can also be the joke.

Friendship and current state shape expression without changing correct answers,
question difficulty or scoring. No new relationship thresholds, balance rules,
dialogue catalogue entries or mandatory four-variant script per question are
approved here. The tone examples below are approved planning references;
production dialogue authoring and catalogue integration remain later work.

#### Approved tone examples by friendship stage

The following German lines preserve the agreed voice direction. They are
standalone editorial examples, not a compulsory sequence, a complete dialogue
set or runtime catalogue entries. The differences come from familiarity,
cheekiness and openly expressed joy; higher friendship does not require more
elaborate jokes after every answer.

| Friendship stage | Correct answer | Incorrect answer |
| --- | --- | --- |
| 1-2, acquaintance | „Richtig! Ein Punkt für dich. … Mhm, das Verkünden gefällt mir.“ | „Oh, leider nicht. Ich zeig dir die Lösung. Wir haben ja Zeit.“ |
| 3-5, familiar | „Richtig! Hihi. Ich glaube, ich behalte den Job als Quizmasterin.“ | „Leider daneben. Ich hatte mich schon aufs Punkteverteilen eingestellt. Mein großer Auftritt muss wohl noch warten.“ |
| 6-8, friend | „Richtig! Du könntest wenigstens kurz so tun, als wäre meine große Auflösung noch spannend. Hihi.“ | „Die war’s nicht. Ich könnte jetzt sehr wissend nicken … aber ich hatte die Lösung vorher schon. Das wäre Angeberei.“ |
| 9-10, close | „Ja! Richtig! Ich soll hier eigentlich würdevoll moderieren. Ich freu mich aber gerade lieber mit dir.“ | „Die war’s nicht. Ich bin auf deiner Seite, aber die Lösung lässt sich von mir auch nicht bestechen.“ |

More direct teasing needs a fitting observed situation. For example, at
friendship 6-8 or an appropriately close relationship, after several correct
answers followed by the first incorrect answer:

> „Ha, doch noch ein Einsatz für meine Auflösung! Ich dachte schon, du brauchst
> mich hier nur zum Punkteaufschreiben.“

The joke is her playful wish to have a part and shine in their shared activity.
Do not use this line for repeated mistakes or as a generic incorrect-answer
response. Her exaggerated quizmaster performance can be the target of the joke
instead of making the player the target of every punchline.

After several incorrect answers, reduce teasing and performance, regardless
of friendship tier. Prefer calmer, supportive or briefly neutral responses.
For a familiar, warm relationship, the agreed example is:

> „Hach. Die Punkte lassen heute auf sich warten. Ich bleib trotzdem gern mit
> dir hier.“

At lower friendship, keep encouragement more reserved, following the existing
stage examples rather than assuming close affection. Mistakes do not lead to
disappointment in the player, harsher jokes or withdrawal of warmth. Direct
affection at high friendship may stand on its own without immediately being
undercut by another quip. The exact repeated-error threshold remains undecided;
this is an editorial reaction rule, not a new implemented streak mechanism.

Role breaks are deliberately prominent in these examples. Mix them with simple
responses such as „Genau, richtig!“ and „Leider nicht, die hier war’s“, so the
special comments retain their effect. Current state still governs delivery;
friendship does not force constant cheerfulness. No new dialogue IDs, question
content, animations, persistent counters or balance effects are created here.

### Separate feedback in settings

Plan a dedicated settings area, provisionally labelled **"Quizfragen bewerten"**,
outside the active game. Players can review and rate individual questions that
Aiko has already actually presented to them. Merely drawing, preloading or
reserving a question must not make it eligible for this list.

- Keep the review voluntary and separate from gameplay: no rating prompt,
  extra step or interruption inside a quiz round.
- Show the previously presented question, its answer choices and correct
  solution so the player can assess its wording and content. Do not reveal
  unasked questions through this settings area.
- Collect difficulty and quality separately. Proposed difficulty responses:
  **"Zu leicht"**, **"Passend"**, **"Zu schwer"**. Proposed quality responses:
  **"Gut"**, **"Unklar formuliert"**, **"Inhaltlicher Fehler"**; allow an
  optional explanatory comment. Exact controls and labels remain UI planning.
- Feedback refers to an identifiable question and its content revision, so a
  later correction does not silently attach old ratings to different wording.
  Revisiting a question should allow updating feedback rather than creating
  accidental duplicate votes.
- Treat feedback as editorial input for wording, correctness and difficulty
  review. It must not automatically rewrite questions, change a current round,
  affect rewards/friendship or equate player success rates with factual quality.

Retention, storage ownership and any way to share feedback with maintainers
remain to be designed. Local review must not silently imply a centrally
collected feedback service. Any future export or transmission needs a separate,
explicit user action or consent and must satisfy the zero-cost boundary below.
No external feedback provider or automatic upload is selected.

### Cost and content boundary

The intended basis is a bundled local German catalogue, with suitable freely
reusable material and/or authored questions. The starting draft below uses
newly authored wording and factual reference links, without importing an
external question bank, images or source prose. Preserve provenance and
applicable licence/credit requirements for any later reused material.

Content acquisition and operation must cause no provider charges: no monthly
subscription, paid fallback, compulsory account/API key, metered translation
or additional language model is part of the planned quiz. A library or service
is not a prerequisite for the catalogue. Catalogue authoring is authorized;
the quiz runtime is subsequently authorized and delivered below. Its separate
feedback settings/storage remain future work.

### Authored starting catalogue (editorial draft)

On 2026-10-25, after adding film and television, the owner explicitly authorized
authoring the catalogue. The resulting **200 German questions** are available as:

- [Canonical editorial content with metadata and source registry](quiz/catalogue.de.json).
- [Readable review of all 200 questions, answers, solutions and explanations](quiz/catalogue-review.de.html).

The review HTML is a static presentation of the JSON, with no scripts, external
assets or automatic network requests. It is not a playable quiz or a runtime UI.
Treat the JSON as the content authority and keep the review in sync when editing.
Question IDs remain stable; do not renumber existing records when adding entries.
The initial records have revision 1; the nineteen revised records described
below have revision 2. All have four uniquely identified answers. Later display
shuffling must retain the correct-answer reference rather than infer correctness
from position. The review has fifty solutions at each of the four positions;
this does not implement runtime shuffling or session selection.

| Topic | Easy | Medium | Tricky | Total |
| --- | --- | --- | --- | --- |
| Gaming | 20 | 14 | 6 | 40 |
| Anime and manga | 15 | 11 | 4 | 30 |
| Science fiction | 15 | 10 | 5 | 30 |
| Fantasy | 10 | 7 | 3 | 20 |
| Film and television | 10 | 7 | 3 | 20 |
| Nature and science | 10 | 7 | 3 | 20 |
| World, history and culture | 10 | 7 | 3 | 20 |
| Computers and digital culture | 10 | 7 | 3 | 20 |
| **Total** | **100** | **70** | **30** | **200** |

Every question includes a subtopic, work/franchise where applicable, explanation,
stable answer reference, source IDs, checking date, origin/reuse information and
editorial status. Claims tied to a particular film, event, edition or definition
also record their scope where needed. Each record counts in exactly one topic;
multiple questions about a work still need sensible separation in later sessions.

The reviewed records were approved for the starting runtime catalogue by the
owner's subsequent explicit implementation request including that catalogue.
This does not claim independent expert fact-checking. Source references
were researched on 2026-10-25, preferably through official publishers, creators,
institutions or technical documentation. The registry distinguishes accessed
pages from available search excerpts; it does not assert a full-page check or an
independent second review for every source. Difficulty labels are initial editorial
estimates. Feedback should later assess factual quality and difficulty separately.

The newly formulated questions, alternatives and explanations use the repository's
[MIT licence](../LICENSE). External pages, works and marks retain their own rights;
reference links do not license third-party text, images or character artwork.
This catalogue requires no provider, API key, subscription, translation service
or additional runtime language model. Reference links are editorial evidence,
not dependencies to call during play.

Data checks confirmed 200 unique question IDs/texts, 800 unique answer IDs,
four distinct answer texts and exactly one valid solution reference per question,
complete source references, the 120/80 topic-group split and the 100/70/30
difficulty split. These checks validate structure, not human approval or empirical
difficulty. No quiz code, settings controls, persistence, player ratings, Aiko
dialogue records, horoscope behavior or character assets were changed for this
catalogue delivery. No commit, push or merge was performed.

#### Catalogue revision 2: nineteen editorial corrections

The owner authorized these corrections on 2026-10-25, retaining every question's
ID, answer IDs, topic, difficulty and correct-answer reference. The catalogue
revision is now **2**. Exactly nineteen question records have revision 2; the
other 181 question records are unchanged. All 200 were subsequently approved for
the starting runtime catalogue by the explicit implementation request.

- Clarified profession versus gameplay income (`gam-033`), removed the W20
  answer from its own question (`gam-036`) and removed the type clue from Ash's
  companion question (`ani-006`).
- Asked explicitly for the in-series name of the Titans (`ani-013`), scoped
  Skynet to the 1984 film (`sci-021`), replaced the SSD alternatives with real
  storage technologies (`dig-005`) and included redistribution in the open-source
  rights question (`dig-012`).
- Replaced weak alternatives or reframed the same knowledge in `gam-006`,
  `gam-009`, `gam-020`, `ani-029`, `sci-010`, `sci-025`, `fan-020`, `fil-016`,
  `nat-020`, `dig-006`, `dig-008` and `dig-016`.

The review HTML reflects the canonical JSON, including the per-question revisions,
updated explanations, source access information and film/edition scope. Topic
counts, the 120/80 split, and all difficulty labels/counts remain unchanged.

### Implementation preparation (proposal only)

This is preparation for a future game implementation, not authorization to add
runtime code. Keep the agreed ten questions, four answers, no time limit,
explicit **Weiter**, one point per correct answer, and Aiko as quizmaster.
The existing code was inspected to identify these proposed owners and seams:

| Proposed owner / existing seam | Responsibility |
| --- | --- |
| `QuizCatalogue` in a future `games/quiz_catalogue.py` | Load and validate immutable, approved local question content. Check IDs, revisions, four distinct choices and solution references. No Tk, networking, player state or editorial auto-approval. |
| `QuizSession` in a future `games/quiz.py` | Own the ten-question selection, current question, committed answers, explicit advancement and score. Use the Python standard library with injectable randomness. Reject repeated answers and unknown answer IDs. No Tk, dialogue delivery or pet-state writes. |
| Future `QuizWindow` / `QuizSequence` in `ui/windows/` | Render the question, four answers, progress and resolution; coordinate Aiko's opening/reactions/closing through the existing game speech ports. Do not reveal answers before commitment. Closing cancels pending presentation without fabricating a completed question. |
| Existing `HoverGameUI` in `ui/windows/hover_ui.py` and `GameId` | Later add Quiz to the game menu and reuse `can_interact("play")`, deferred admission, one-game-window exclusion and cleanup. No social-menu route or separate game launcher. |
| Existing application game-experience and pet owners | Preserve single ownership of care effects and actual-play evidence. A UI/session must not write friendship, fun or wishes directly. Apply the agreed noncompetitive completion semantics below when designing the later contract integration. |

Reuse the VN skin, geometry/scrolling helpers, existing animation/emote ports and
game-window lifecycle. Plan a quiz-specific progress/score presentation. The
current `GamePanel` shows player/Aiko wins, losses and draws; it must not invent
an opposing Aiko score for this game. Reuse its suitable presentation helpers or
make a bounded score-display extension without changing other games' behavior.
Question/answer wrapping must accommodate the actual catalogue lengths rather
than a fixed line count; all answers and the explanation remain readable until
the player advances.

#### Selection and content preparation

- Bundle only explicitly approved questions in a later runtime catalogue. Keep
  editorial HTML and source research outside runtime loading. Invalid content
  or fewer than ten eligible questions must yield an unavailable-game message;
  do not call an API, invent replacement questions or duplicate questions.
- Sample without replacement and shuffle answer display independently of question
  order. Evaluate by stable answer ID; the review's repeating solution positions
  are not a runtime ordering rule. Difficulty labels and topic shares remain the
  long-term catalogue targets, with varied short rounds rather than rigid quotas.
- Treat related works as one variety group where appropriate, such as Tolkien's
  language questions and The Lord of the Rings. Do not rely only on exact equality
  of the current free-text work/franchise labels. Keep question sets with obvious
  answer hints to each other apart where the pool permits.
- Future presentation history records a question only when its question and
  choices are actually shown, using ID and content revision. Sampling/preloading
  is not presentation. Settings feedback stays separate from play, voluntary and
  local by default; storage and any explicit export remain separate design work.

#### Agreed quiz completion, fun and wishes (planning only)

Owner decision recorded on 2026-10-25. These rules supersede the earlier proposal
to settle completion semantics before coding. They initially authorized
documentation only; the subsequent implementation request covers these rules
and is recorded in the delivery section below.

**One completed ten-question quiz counts as one shared-play round.** The number
of correct answers remains a separate quiz score, with no player-versus-Aiko
win, loss or draw. Aiko is the quizmaster, not a competing player.

- Completion occurs when the tenth answer has been committed and its resolution
  displayed in the player window. Finishing Aiko's closing speech or clicking
  another button is not required. Closing during the subsequent reaction retains
  this completed round.
- Settle the completion exactly once through the application/pet owners. Repeated
  callbacks, reopening the result, later window closure and save/reload must not
  credit the same round again. A new requested ten-question round is a new unit.
- Opening, preloading, elapsed window time and individual answers award no partial
  round or partial fun. Abandoning a quiz before its completion boundary counts
  no completed round and creates no quiz defeat or extra disappointment penalty.
  Ordinary existing wish deadlines continue to run.

**Fun:** award **9 base fun points per completed quiz round**, using the same
starting base value as Connect Four and Mastermind. Existing high-fun reduction,
long-session diminishing returns and the session fun cap still apply. Treat
successive rounds requested in the same game session cumulatively for those
limits; awarding at completion must not reset the session allowance each round.
There is no per-question, speed or accuracy multiplier. Scores of 0/10, 5/10 and
10/10 have identical completion/fun value under otherwise equal conditions.
No additional performance-based friendship reward or penalty is introduced.

| Wish type | Agreed quiz contribution |
| --- | --- |
| General shared-play wish | One completed quiz gives one progress step. Preserve the existing requirement of two completed game rounds, which may be accumulated across eligible games/sessions. |
| Concrete quiz wish ("Mach ein Quiz mit mir") | One completed ten-question quiz fulfills the wish, regardless of score. This is a quiz-specific completion requirement, not a reduction of other games' existing wish goals. |
| Game-change wish | One progress step if Quiz meets the wish's original target/exclusion. Preserve the wish's existing required count. |
| Win, avoid losing, win streak/overall competitive result, or rematch/comeback wish | Quiz contributes no competitive result or result progress. Do not generate these wishes with Quiz as their target or use a quiz score as competitive history. |

Capture at most one eligible shared-play wish at quiz-round start, using the
existing assignment priority and the noncompetitive activity's eligibility.
Only that original wish can receive the completion, provided it still meets its
ordinary validity/deadline rules. Later-created wishes receive no retroactive
progress, and an ineligible/expired original wish does not redirect the same
completion to another wish. One quiz must not fulfill both a concrete quiz wish
and a general play wish simultaneously.

Fulfillment uses the existing shared-play wish effect and ordinary once-per-wish
handling. It creates no quiz-specific performance bonus. Normal shared-play and
wish effects remain distinct, so the same completion may give ordinary fun and
resolve its assigned wish without duplicating either effect.

**Later contract integration:** represent the activity as completed shared play,
without manufacturing a competitive outcome. The existing `GameExperience` can
already count unclassified completed units. Its result-free use is distinct from
`neutral_units`, which competitive adapters currently use for draws.

The current `SessionSummary` and `GameRoundEvent` describe player wins/losses/draws.
`application/game_experience.py` reverses them into Aiko's competitive experience.
Directly translating a correct quiz answer into a player win would therefore
give the wrong meaning to Aiko's experience. An incorrect answer must not become
an Aiko victory or trigger generic opponent-win banter. Do not substitute a draw:
that could accidentally satisfy an avoid-losing wish. Extend the completion/wish
path explicitly for noncompetitive shared play before wiring Quiz into it.
The concrete API/storage design remains implementation preparation; no runtime
contracts, balance data, wish definitions or other games are changed here.

#### Later delivery order and validation

1. Obtain implementation authorization and approve the intended runtime content;
   design the contract integration for the agreed shared-play semantics above.
2. Implement the pure catalogue/session layer and check selection, stable answer
   IDs after shuffling, exactly-once commitment, ten-question completion and
   cancellation boundaries.
3. Connect the player window and the **Spielen** route with quiz-appropriate score
   presentation, existing game gating and reliable close/restart cleanup.
4. Add Aiko's separate quizmaster reactions using the agreed friendship tone;
   reduce teasing after repeated errors without changing factual solutions.
5. Plan and deliver previously-presented-question feedback separately once its
   storage ownership is agreed. It must not become an in-round prompt.

For that later implementation, verify long-text wrapping at narrow window sizes,
single-click/keyboard commitment, **Weiter** control, absence of time limits,
menu exclusion, closing during a reaction, a fresh round, and appropriate care
accounting. This catalogue revision implements none of these runtime features.

## Quiz delivery (2026-10-25)

The owner authorized implementation under **Spielen > Quiz**, including the
reviewed 200-question catalogue, Aiko's quizmaster role and the agreed shared-play
fun/wish rules. The horoscope prototype and parallel character-asset work are
outside this delivery and were not edited.

- `games/quiz_catalogue.py` loads immutable approved local content from
  `data/quiz.de.json`, validating four distinct choices, stable IDs/revisions and
  solution references. The editorial JSON/HTML retain factual sources, rights and
  review history outside runtime loading. The implementation request approves
  the revised initial catalogue for use; no automatic editorial approval exists
  in the loader. No provider, key, account, translation model or network call is
  used. Topic/difficulty counts and all question/answer IDs are preserved.
- `games/quiz.py` selects ten different questions, preferring fresh questions,
  different works and a topic mix informed by catalogue size. Answers shuffle
  independently and resolve by ID. Tolkien language/LOTR entries share a variety
  group. Scoring, one-time commitment and explicit advancement are pure rules.
- `QuizWindow` and `QuizSequence` provide the VN game window, keyboard choices
  1–4, wrapped answers, visible selected/correct answers and explanations,
  **Weiter**, score out of ten and **Noch eine Runde**. There is no answer timer,
  automatic advancement, Aiko opponent score or score-based pass threshold.
  Invalid/insufficient local content produces a readable unavailable message.
- Aiko uses the existing speech/animation/emote ports and authored dialogue
  catalogue. Friendship stages have their agreed tone, mixed with short ordinary
  responses. A mid-round role break can occur, repeated errors select supportive
  dialogue, and quieter/irritated emotional contexts have restrained alternatives.
  No new character artwork or props are needed. The game uses the existing fun
  icon and VN UI resources.
- A result-free `completed` receipt extends the shared game-round contract for
  Quiz. Competitive quiz receipts/summaries are rejected. The application credits
  the round after the tenth answer's visible resolution, before the closing
  reaction. Existing Pet-owned bounded receipts prevent replay after reload.
  Closing an unfinished quiz gives no completion; closing after its result gives
  no second reward.
- Quiz reuses the nine-point board-game fun profile, including its ordinary
  energy/social amounts. Incremental completion preserves the existing per-window
  cumulative diminishing returns, twenty-point fun cap, high-fun reduction and
  existing friendship threshold. Correctness never enters care accounting.
- Named Quiz wishes use the existing exact-play form with a captured one-round
  goal. General/eligible game-change wishes keep their original required counts;
  one assigned completion advances one wish. Competitive/rematch forms exclude
  Quiz. Saved shared-play causes retain `completed`, with no fabricated draw,
  and the UI displays shared-play progress rather than an Aiko win/loss score.

The separate settings feedback feature remains at the explicitly deferred fifth
delivery step: its storage/retention/export design is not chosen here. No ratings
are requested during play and no feedback service or new save schema is added.
Question-repetition avoidance in this delivery is transient within the open game
window; no persistent quiz/answer history is claimed.

Validation: the final focused run passed **244 tests**, covering Quiz, wish
creation/completion/storage, game menu/window/session behavior, dialogue and
architecture/dependency checks. Whole-repository Ruff passed, strict Mypy passed
for 347 source files, Pyright reported zero errors/warnings, and diff whitespace
checks passed. The isolated native Windows quiz tests cover correct/incorrect
marking, long-answer wrapping in a narrow work area, explicit advancement,
new-round reset, cancellation and unavailable content. A separate native render
was visually inspected; no normal pet save or character-asset regeneration was
used. This is not a claim of a full manual mouse/keyboard session with the live pet.

The broader Windows run executed **2,092 tests** and had four failures:
`test_click_gui.test_story_reading_including_right_clicks_does_not_tease`,
`test_mastermind_gui.test_cancelled_drop_and_close_release_local_grab_and_ghost`,
and the two `test_world_gui` cases
`test_recognized_drink_handover_then_unknown_full_drink_is_examined` and
`test_refused_identified_offer_still_falls_instead_of_entering_hands`.
All four also failed identically in a temporary comparison copy with the
pre-Quiz tracked sources restored from HEAD and the existing parallel artwork
preserved. They were left unchanged. After the final Quiz/text changes, the
244-test focused run above passed; a second complete suite is not claimed.

Character-artwork and horoscope file hashes match their pre-implementation
snapshots. The independent parallel care-planning document was not edited by
this delivery. Existing non-Quiz dialogue/copy content is unchanged; new Quiz
dialogue was appended without reformatting the rest of the catalogue.
The owner subsequently authorized a local commit of Quiz, its catalogue, tests
and these related documents. Horoscope and parallel character-asset work are
excluded from that commit. No push or merge is authorized.
