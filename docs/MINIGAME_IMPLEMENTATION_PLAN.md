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
| German text and character voice | Labels in `data/texts.de.json`; authored game reactions in `data/dialogues.de.json`, registered through `pet/mind/dialogue_events.py` when adding events. Embedded play uses the injected session `PetMind`, as RPS does; never add a second mind/catalogue history for it. |
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
