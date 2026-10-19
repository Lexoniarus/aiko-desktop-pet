# Three-game selection and presentation plan

Status: implementation authorized on 2026-10-19; delivery in progress.
The owner selected Blackjack and Tic-Tac-Toe alongside the existing
Rock–Paper–Scissors (RPS). The owner authorized stepwise implementation, small
commits and targeted tests, with full-suite validation only at the end.
No merge is authorized.

## Agreed experience

- **Spielen** opens a small submenu: **Schere–Stein–Papier**, **Blackjack**,
  **Tic-Tac-Toe**. Only selecting a game requests the existing game admission
  flow. Dismissal, Escape and outside clicks close the submenu without starting
  play or granting rewards. Existing interaction restrictions still apply.
- One game window/session at a time. While a game is open, further selection
  is disabled. Preserve existing RPS behavior.
- The new games allow any number of rounds. Show temporary player/Aiko/draw
  counts, a result and **Nächste Runde** after each round; no automatic restart.
  RPS retains its existing hand-selection controls and round flow.
- Aiko remains on the desktop and uses existing speech, emotes and animations.
  Her speech bubble carries comments, not the Blackjack card layout.
- Closing releases the game presentation and restores ordinary behavior.
  Completed rounds count once; an unfinished round never counts. Session
  scores, decks and boards are discarded rather than saved.

## Blackjack

**Player window:** the player's cards and total, **Karte ziehen**, **Bleiben**,
result, session score and next-round control. No duplicate of Aiko's cards or
separate Aiko-hand display in this window.

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
Paths marked **new** below are proposed homes, not existing implementations.

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

This documentation update itself creates no implementation commits and runs no
game, GUI or full-suite tests.

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
Implementation authorization remains separate from this documented assessment.

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
  the delivered behavior. This plan records no completed implementation/tests.

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
