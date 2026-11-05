# Shared Aiko room and local iPad PWA — overall implementation plan

Status: phase 0 complete. Shared-room implementation is in progress on
`feature/shared-room-pwa`; final automatic and actual-device acceptance are pending.

Planning baseline: 2026-11-04, `feature/social-optimization` at `54c6e46`,
including the currently uncommitted desktop/UI work as work to finish in phase 0.
This is an inventory reference, not the future room branch's starting commit.
GitHub CI and merge status have not been established by this planning document.

Technical documents and identifiers are English; the product UI and Aiko's
authored dialogue remain German. This plan extends the existing
[architecture](../ARCHITECTURE.md), [contribution rules](../../CONTRIBUTING.md)
and [GitHub workflow](../GITHUB_WORKFLOW.md).

## 1. Agreed product and delivery boundaries

- Build one shared room frontend for iPad and a later desktop integration.
- Retain the existing Python Tamagotchi rules, dialogue, game rules and content.
  Adapt their platform dependencies instead of copying an iPad-specific core.
- On iPad, run Python locally through Pyodide in a Web Worker. Use a PWA with
  its own Home Screen icon and standalone window. Windows is the development
  machine; a Mac and a native iOS build/signing pipeline are outside this route.
- Use the supplied v16 prototype as the room reference. Aiko acts autonomously;
  the user can look around independently, call her, offer objects and play.
- Aiko has a defined daily routine on iPad. Do not learn or import the user's
  desktop rhythm. Final routine times are a product configuration decision;
  existing desktop rhythm learning remains intact.
- Keep the current needs, relationship, care boundaries, wishes and game effects.
  Do not add thirst, a separate health/age system, or other invented parity items.
- Keep state automatically and advance real elapsed time on return. There is no
  manual save/load flow. Closed-time simulation does not pretend the user cared,
  played or spoke to Aiko.
- Deliver versioned runtime ZIPs through Dropbox or GitHub. These contain built
  application files, required Python packages and runtime assets, not a raw
  branch source archive or the user's private save.
- A small technical check on the actual iPad is an early feasibility gate.
  Its diagnostic harness is not acceptance of a reduced functional product.
  The first functional test version, T1, must include the entire current
  Tamagotchi scope in section 3, including every existing game and conversation.
- Planned notification support uses forecasted events and Web Push. Its external
  sender and network delivery are separate from Aiko's local simulation. Do not
  promise native offline scheduled notifications from the PWA.
- Full desktop embedding and switching between taskbar and room remain later
  work. Shared contracts and room code must support that direction from the start.

## 2. Phase 0 is mandatory: finish and merge the current desktop work

The repository's default branch is `main`; this is the branch called "Master"
in the discussion. Do not start implementation on a branch taken directly from
the unfinished feature branch.

| Step | Work | Required evidence |
| --- | --- | --- |
| P0.1 | Inspect current status, diff, active PRs and actual branch ownership. Finish the intended desktop refactor/UI work without discarding parallel changes. | An explicit inventory of completed work, remaining failures and the intended PR head. |
| P0.2 | Commit the finished work in cohesive changes; review the exact diff and required resource/configuration changes. | Stable final head SHA; no personal saves, private originals or generated installers in the diff. |
| P0.3 | Run the local no-window suite, Ruff, strict Mypy and Pyright; obtain full GUI/Windows results in isolated CI. Fix demonstrated failures in their owning modules. | Distinct headless, full-CI and visual acceptance records; a skipped native case is not a passed GUI check. |
| P0.4 | Push the reviewed branch and wait for all required GitHub checks on that final head. | Exact PR head SHA equals the SHA of the successful checks; any subsequent change invalidates this evidence. |
| P0.5 | Merge the reviewed PR into `main` under the repository workflow. | Merge commit/result recorded. |
| P0.6 | Verify successful required CI on the resulting `main` commit and update the local base. | Green `main` SHA, not just a green pre-merge feature head. |
| P0.7 | Branch from that `main` commit into `feature/shared-room-pwa`, preferably in a separate worktree at `E:/aiko-desktop-pet/aiko-room-pwa`. | Recorded base SHA, correct branch and a clean new worktree. |

At inventory time, `main` contains only the RPS game module; the feature branch
contains the remaining game work. Phase 0 brings the intended complete desktop
baseline into `main` before branching.

Use the current workflow as the authority for exact checks. At this baseline,
it includes Linux Python 3.11/3.13 unit and GUI runs plus Windows boundary checks:

```text
python tools/local_test_suite.py
python -m ruff check aiko_pet tests main.py tools
python -m mypy --strict --no-incremental aiko_pet main.py tools
python -m pyright --project pyrightconfig.json
```

Local automated checks must not create visible windows on the user's primary
display. The headless helper explicitly blocks native Tk creation. Full GUI
checks run in isolated GitHub Linux/Xvfb and Windows jobs; their results remain
mandatory. If a local visual check is needed, use the designated secondary
display. Re-read the actual workflow at execution time; this snapshot must not
freeze CI rules.

Phase 0 is now an execution task. Record its completed checks separately;
branch creation and merge after green CI remain later steps in that task.

## 3. Complete functional scope of T1

"Reuse" means reuse the authoritative rules/content, not a promise that every
existing module imports unmodified under Pyodide. Every visible Tk surface needs
a corresponding web surface or an explicit room-equivalent interaction.

### 3.1 Pet state, care and physical objects

| ID | Function to retain | Reuse | Web surface / required adaptation |
| --- | --- | --- | --- |
| C01 | Satiety, energy, fun, social and affection | Needs and progression policies | Readouts; connect one admitted elapsed-time path. |
| C02 | Mood and emotional composition | Existing mood/Moodlet calculations | Befinden, expression and explanatory text. |
| C03 | Friendship stages, qualified rewards, limits and decay | Relationship/history policies | Relationship readout; preserve actual-action evidence and caps. |
| C04 | Short and long-term Moodlets, causes, recovery and poor-care consequences | Current definitions and lifecycle; exclude the two cursor-only definitions on iPad | Moodlet icons/details, duration and cause readouts. |
| C05 | Autonomous movement, pauses and interruption | Existing planners/controller as foundation | Room movement, depth, reachable targets and cancellation. |
| C06 | Idle expressions, gestures, blinks, emotes and state-dependent animation | Existing selection/playback policies and approved runtime resources | Pixi presentation with correct priorities and foot/hand anchors. |
| C07 | Own daily routine and current/next activity | Existing schedule/lifecycle models | Fixed room routine profile; no user-input rhythm learning. |
| C08 | Manual sleep/wake, automatic sleep, naps, exhaustion recovery and protected actions | Existing sleep policy and episode state | Sleep controls and playback; replace desktop observation inputs with explicit room policy. |
| C09 | Automatic persistence and full elapsed-time catch-up | PetSessionRestorer, SessionTimeProgression and checkpoints | Browser persistence, lifecycle and restart coordination. |
| F01 | All ten foods and Energy Drink | Food catalogue, nutrition and menu order | Full selector with existing names/icons/benefits. Foods: Onigiri, Sandwich, Taiyaki, Apfel, Dango, Donut, Cookie, Melonpan, Cupcake, Dorayaki. |
| F02 | Food effects, digestion, meal timing and repeated-food response | Existing food and care transitions | Feeding/eating feedback and retained meal history. |
| F03 | Acceptance/refusal, specific food wishes and excluded foods | Existing permission/decision rules | Show the actual committed result; no frontend acceptance rules. |
| F04 | Energy Drink and full-energy refusal | Existing care transition | Offer/drink playback and result. This is not a separate thirst system. |
| O01 | Create and carry a portion; offer and hand it over | World identity/custody and interaction coordination | Touch/mouse drag, offer feedback, valid transfer zones. |
| O02 | Drop, settle, relocate and cancel an object gesture | Existing object states/motion as applicable | Room-ground geometry, depth and safe cancellation on lost input. |
| O03 | Notice, approach, inspect, acquire, consume and put down | ObjectBehaviorCoordinator/ObjectInteractionCoordinator and existing owners | Room perception/reach/movement and identified animation events. |
| O04 | Subjective object identity, appraisal, remembered positions, absence and search | ObjectMemory/perception/stock policies | Adapt geometry without granting knowledge from unseen World truth. |
| O05 | Finite unattended food care and sleep food breaks | Current time/stock/consumption rules | Only actual acquired, appraised, accessible portions; no generated meals. |
| A01 | Petting, affection effects, saturation, refusal and ignored boundaries | Existing care/interaction rules | Accessible touch action and actual reaction. |
| A02 | Greeting, contact, repeated poking and disturbing sleep | Contact and click policies | Deliberate taps; reading advancement remains distinct from poking. |
| A03 | Interrupted actions, crowding and withholding effects | Existing interaction episodes and evidence | Report real interruptions once; camera swipes alone are not interruptions. |

Canonical sources: `pet/state.py`, `pet/care_actions.py`, `pet/progression.py`,
`pet/sleep.py`, `application/contact.py`, `application/object_interaction.py`,
`application/object_behavior.py`, `application/object_consumption.py`, `world/`.

### 3.2 Every existing game

| ID | Game | Rules to reuse | Web work and parity boundary |
| --- | --- | --- | --- |
| G01 | Schere–Stein–Papier | Choice, reveal, result and session score | Hand selection, countdown, separate hands, commentary and next round. |
| G02 | Tic-Tac-Toe | Board, local opponent, result, alternating starter | Shared board, turn control, result and next round. |
| G03 | Blackjack | Card/dealer rules, hidden card, hit/stand and result | Both hands, concealed/revealed cards, movement and existing session flow; no new betting system. |
| G04 | Vier gewinnt | 7x6 board, bounded search, result, alternating starter | Column input, drop/win presentation; replace ThreadPoolExecutor/Event assumptions and handle stale/cancelled searches. |
| G05 | Mastermind | Four positions, six colours, repeats, ten attempts and feedback | Touch/mouse pins, all attempt rows, feedback and hidden-code reveal. |
| G06 | Quiz | Existing 200-question catalogue, ten-question rounds, answers and explanations | Staged quizmaster presentation, answer release, resolution and next question/round. |
| G07 | Shared game lifecycle | Existing round/session events and GameExperienceCoordinator | One active game, entry/exit, readable commentary, cancellation and exactly-once qualified completion. |

Retain the current difficulty/opponent behaviour. Do not add the separately
discussed difficulty redesign. Session scores remain transient as on desktop;
durable pet experience and wish progress remain durable. Cancelling an unfinished
round must not manufacture a result or reward. Reopening a killed app does not
implicitly require restoring an unfinished game that desktop does not persist.

### 3.3 Conversations, external content and horoscope book

| ID | Function | Reuse | Web work / adaptation |
| --- | --- | --- | --- |
| S01 | Authored Plaudern | German catalogue, friendship/need/context selection | Conversation selection, bubbles and emotes. |
| S02 | References to actual retained experiences | Food/game/social/affection/negative/long-term topic policies | Use existing evidence, including literal source attribution; do not fabricate memories. |
| S03 | Multi-beat speech, pauses, reading advancement and interruption | Reaction/Cue and existing Tk-independent ReactionPlayer | Timer/display ports, visible text acknowledgement and qualified completion. |
| S04 | Spontaneous comments and care requests | Existing topic selection and timing | Exclude workload/cursor topics on iPad; respect busy/play/sleep ownership. |
| S05 | Sprueche: sayings and quotations | Source-aware formatting, selection, identity and repetition rules | Existing category and presentation; browser fetch adapter. |
| S06 | Two-part jokes and reviewed local jokes | Setup/punchline timing, validation and pinned pyjokes review | Full text presentation and local package/review resources. |
| S07 | Curious facts | Existing preparation, validation and history | Browser fetch and actual failure/wait states. |
| S08 | Sources, attribution, credits and retry/limit/exhaustion states | Existing metadata and coordinator state | Web credits/links; replace local file URI links. |
| H01 | Zodiac selection | Existing twelve signs and preference | Settings control and durable setting. |
| H02 | Local daily horoscope | Astronomy Engine, catalogue, generation and daily history | Verify required package metadata and offline resource loading in Pyodide. |
| H03 | Place, offer, hold and put down the horoscope book | One-live-book binding and World custody | Room object, reading pose and interaction zones. |
| H04 | Read, pause, resume, finish, replay and expire | HoroscopeCoordinator and current history rules | Cancellable playback and restart/day-boundary handling. |

The existing sources are JokeAPI, Zitat-Service, WitzAPI.de, Random Useless Facts
and the reviewed local pyjokes subset. Retain the existing explicit source opt-in.
Plaudern, local reviewed jokes when enabled, games and the local horoscope form
offline content; fresh external content still needs the Internet.

Check direct browser access for each provider early. If a provider's CORS policy
prevents parity, record that finding and settle the smallest suitable fetch relay
or another explicit product decision before calling T1 complete. Do not silently
delete a category or replace it with invented fallback content. Provider text is
not a bulk dataset to add to the runtime ZIP.

### 3.4 Wishes, information, settings and storage

| ID | Function | Reuse | Web work / adaptation |
| --- | --- | --- | --- |
| W01 | All current 17 wish definitions and prerequisites | Existing selection/matching/fulfilment | Full wish cards and availability information. |
| W02 | Specific/excluded food; chosen/any/other game; round/overall goals; rematch/comeback; social categories/any social; petting | Current goals and experience requirements | Correct targets, progress and actual completion events. |
| W03 | Inner versus spoken wishes, remaining time, pin and dismiss | Existing actions and state | Disclosure feedback, pin/dismiss controls and timers. |
| U01 | Befinden, all needs, friendship and detailed causes | Existing immutable snapshots/projections as applicable | Status panel and accessible details instead of hover-only information. |
| U02 | Current/next activity, sleep/contact information and object status | Existing read models | Own-routine context and room-object summaries; no hardware readouts. |
| U03 | Auto-walk, auto-routine, spontaneous speech, source opt-in and zodiac | Existing behaviour preferences | Web settings; retain fixed schedule rather than adaptive learning. |
| U04 | Character size and UI size | Existing intent/preferences as applicable | Responsive touch layout; distinguish world scale, camera zoom and UI scale. |
| U05 | Open/keep-open/details/menu navigation and position reset | Existing user capabilities | In-window panels; map centring to camera rather than moving World truth. |
| P01 | Complete coherent saved session | Pet/World/knowledge, friendship, Moodlets, wishes, applicable settings, social receipts and horoscope bindings | Preserve save ownership and revisions; browser storage adapter and schema migration. |
| P02 | Validation, supported migration, failure handling and recovery | Current codecs and storage contracts | File publication/backup operations require browser verification; never reset silently. |
| P03 | Durable writes during use and lifecycle transitions | Current autosave intent | Flush meaningful actions and periodically; do not depend solely on an app-close event. |

Rhythm learning and forgetting the learned profile are intentionally absent on
iPad. Desktop-only window positions remain desktop preferences. Preserve existing
desktop save compatibility when adding room locations/settings.

### 3.5 Explicit exclusions and new work

Desktop-only: pointer curiosity/fear/following, global input observation,
CPU/GPU/RAM/workload observation and dialogue, learned user rhythm, taskbar/monitor
placement and topmost/native-window management. These remain in the desktop app.
External-application incoming notifications are not a prerequisite for the
Tamagotchi test build; the existing incoming inbox is not outgoing Web Push.

New shared room work: independent camera, call action, room-depth geometry,
room movement/reach/perception, touch interactions and the common browser UI.
New browser work: runtime packaging, starter PWA, ZIP install/update, durable
storage and lifecycle adaptation. New simulation work: wishes during absence
and forecast consistency. New notification work: subscription, external timed
sender, revision/replacement and open-from-notification handling.

Tarot, additional games, a room economy and the prototype's shop/upgrades are
not existing desktop parity. Keep them as explicit reference/product decisions,
not unnoticed additions to T1.

## 4. Prototype reference and technical stack

Reference: `aiko-360-raumtest-v16.zip`, supplied by the user. The archive contains
`aiko-360-prototype/`; its package identifies version `0.21.0` and describes an
offline 2.5D depth/camera/interaction prototype. Archive SHA-256:

```text
2ef2e1ad245abb967c565100e429d19f25e0fecadad9d8d93fb2965b7979a1af
```

Do not commit the private archive, review captures or full-resolution originals
as part of this plan. Reference geometry is evidence, not authorization to
regenerate art. Follow the local asset guide before future asset-specific work.

| Prototype component | Intended destination |
| --- | --- |
| `core.js`: world extent, wrap, depth, fixed places and reach | Canonical room definition plus Python geometry/interaction rules. |
| `renderer.js`: depth projection, layered furniture and character rendering | Shared TypeScript RoomProjection/RoomView. |
| `app.js`: DOM, input, camera-follow, localStorage and demo loop | New independent camera/input, platform lifecycle and package storage. Automatic camera-follow must not defeat independent browsing. |
| Demo pet/economy/upgrade state | Do not create a second production pet model; record any later feature decision separately. |

| Layer | Choice | Remaining integration work |
| --- | --- | --- |
| Web language/build | TypeScript and Vite | Pin compatible tool versions and lockfile; build under Windows/CI. |
| Drawing/input primitives | PixiJS 8 | Scene, projections, display layers, hit areas and semantic input. |
| Camera | Compatible pixi-viewport release | Independent controls and correct wrap/depth behaviour from the prototype; a flat viewport does not implement all room projection. |
| Frame animation | PixiJS AnimatedSprite | Reuse canonical timing/animation data and existing policy/events; no duplicate authored timing table. |
| Python execution | Pinned Pyodide release in a module Web Worker | Verify Python version/packages/imports and serial owner-loop execution. |
| Menus/game controls | HTML/CSS and TypeScript, with Pixi where suitable | All current care/status/settings/game views. No extra UI framework is required initially. |
| Offline shell | Manifest, Service Worker and Workbox with custom routing | Bootstrap caching and imported package routing. |
| ZIP reader | fflate | Package validation, staged installation, activation and recovery remain Aiko work. |
| Program storage | Cache Storage plus small IndexedDB package metadata | One active-version pointer; installed content and save data have separate lifetimes. |
| Pet storage | Verify current SQLite adapter on Pyodide/IDBFS first | Confirm durable synchronisation, revisions, file publication and recovery; select an alternative adapter only from measured incompatibilities. |
| Distribution | Stable HTTPS starter; ZIP download through Dropbox/GitHub | No Mac, Apple signing or native installer; source archives are not runtime packages. |

Bundle the pinned runtime and required packages for offline use. Normal CPython
native wheels, Tk, socket servers and ThreadPoolExecutor are not assumed to work
in Pyodide. Pillow's existing Tk UI scaling is not a dependency to impose on the
new frontend. Preserve the desktop requirements separately.

## 5. Ownership, modules and dependencies

### 5.1 Shared ownership rules

1. PetState owns pet values; WorldState owns objective objects/custody and the
   authoritative room spatial state; PetMind/ObjectMemory own subjective facts.
2. RoomSession composes/delegates to those owners. It stores no parallel pet,
   inventory, relationship or independent simulation clock.
3. GameSessionCoordinator owns the currently active game object, not copies of
   game rules. It reports to the existing GameExperienceCoordinator.
4. Presentation receives immutable snapshots/events. JS may interpolate drawing
   positions, but cannot independently decide authoritative motion or rewards.
5. Camera state is presentation state. Its visibility is not Aiko's perception.
6. Existing WorldPosition.height is height above ground. Add room depth as a
   distinct dimension and a stable environment identity; do not reinterpret
   existing saved height as depth. Version/validate codecs accordingly.
7. Extend existing movement contracts/execution for room routes; do not run two
   competing movement controllers. World/taskbar differences belong in geometry
   and environment adapters.
8. A per-device Aiko remains local. Sharing code does not imply cross-device save
   synchronisation. Later desktop room/taskbar views use the same desktop pet.

### 5.2 Implemented Python boundaries

| Path | Owner | Responsibility |
| --- | --- | --- |
| `world/room.py`, `world/state.py` | RoomGeometry, RoomSpatialState, WorldState | One authoritative spatial state; camera-independent wrap/depth and places. |
| `application/room_contracts.py` | Finite protocol vocabulary and serialization | Named commands and immutable output, no browser types. |
| `application/room_routine.py` | RoomRoutine | Initial fixed 23:00–08:00 profile; no learned computer rhythm. |
| `application/wish_context.py`, `wish_forecast.py` | Shared capability context, RoomTimeProgression, WishForecastService | One admitted time path; isolated preview without live mutation. |
| `frontend/room_session.py`, `room_runtime.py` | RoomSession, RoomRuntime | Portable composition, existing object owners, call/offer/reach and lifecycle. |
| `frontend/room_content.py`, `room_content_ports.py` | RoomContent, RoomContentHost | Existing social and horoscope owners behind an acyclic host interface. |
| `frontend/games/session.py`, `frontend/games/` | GameSessionCoordinator, extracted original sequences | All six original games, rewards and cancellable presentation; bounded deferred search. |
| `frontend/playback.py`, `room_playback.py` | ReactionPlayer, RoomPlayback | Original cues plus explicit timer, display and animation acknowledgement adapters. |
| `frontend/view_models/`, `geometry.py` | Existing immutable projections and pure geometry | Shared German presentation, readouts and game views; no Tk imports. |
| `browser/bootstrap.py`, `endpoint.py` | Factory, BrowserEndpoint | Browser adapter composition and finite JSON dispatch. |
| `infrastructure/browser/` | Filesystem publication and browser fetch adapters | Existing SQLite and content contracts under Pyodide. |
| `infrastructure/sqlite/room_rows.py` | Optional room mapping | Schema 6 inside the existing complete save transaction. |

Native Tk callers use the extracted frontend owners too. Domain/application
modules cannot import this frontend. The previously retired `presentation`
namespace remains retired; its canonical-import guard has not been relaxed.
`ObjectInteractionCoordinator.suspend` settles custody on host suspension
without manufacturing animation receipts, care completion or game rewards.
Notification subscription/sender and the native desktop host remain later phases.

### 5.3 Target directory layout

```text
aiko_pet/
  pet/                         existing domain and movement rules
  world/                       existing owner; room.py added
  games/                       existing game rules
  application/                 existing use cases plus room/session contracts
  frontend/
    room_session.py
    room_runtime.py
    room_content.py
    room_content_ports.py
    room_playback.py
    view_models/               shared immutable projections
    playback.py
    games/                     extracted reusable sequence controllers
  browser/
    bootstrap.py
    endpoint.py
  infrastructure/
    browser/
      persistence.py
      social_fetch.py
  desktop/                     existing native runtime; later room host
  ui/                          existing native Tk views
  data/
    ...                        existing authored catalogues
web/
  package.json
  tsconfig.json
  vite.starter.config.ts
  vite.runtime.config.ts
  index.html
  public/manifest.webmanifest
  src/
    main.ts                    composition only
    bridge/
      RoomClient.ts
      commands.ts              generated finite command vocabulary
    room/
      RoomView.ts
      RoomProjection.ts
      RoomCamera.ts
      AikoView.ts
    input/
      ObjectDragController.ts
    ui/
      FoodPanel.ts
      SocialPanel.ts
      StatusPanel.ts
      WishPanel.ts
      SettingsPanel.ts
      CreditsPanel.ts
    games/
      RockPaperScissorsView.ts
      TicTacToeView.ts
      BlackjackView.ts
      ConnectFourView.ts
      MastermindView.ts
      QuizView.ts
    platforms/
      browser/
        BrowserRoomClient.ts
        python.worker.ts
        BrowserLifecycle.ts
        PackageImporter.ts
        PackageStore.ts
        service-worker.ts
      desktop/
        DesktopRoomClient.ts   later; same RoomClient contract
  tests/
scripts/
  export_room_contracts.py
  build_room_package.py
services/push/                 later notification sender, separately deployed
tests/                         Python, persistence and architecture coverage
docs/room/
  IMPLEMENTATION_PLAN.md        this combined plan and parity register
```

Create modules when their real responsibility is implemented, not as empty
scaffolding. Keep current resources canonical: the build copies approved runtime
resources by ID, rather than adding independently editable food/dialogue/animation
catalogues under web/. Split this document only when a maintained contract or
device checklist warrants its own owner.

### 5.4 Runtime contract and ordering

- RoomClient is the shared TypeScript interface. BrowserRoomClient uses the
  Python Worker; DesktopRoomClient later uses native Python transport.
- Keep a versioned, finite set of named commands. Generate TypeScript types;
  also validate incoming messages at runtime. No arbitrary Python execution API.
- Commands carry request identity; object operations carry expected instance
  revision where relevant. Outcomes/events have identities for acknowledgements.
- Admit time once before a semantic action. Preserve exactly-once consumption
  and rewards. Nutrition is committed at the existing confirmed consumption
  boundary, not re-awarded when a drawing animation happens to finish.
- Run mutations on one owner loop. Serialise asynchronous requests; an await
  must not permit a second command to mutate the same session concurrently.
- Playback acknowledgement means the specific text/action was actually shown.
  Sleep/cancellation/backgrounding must not manufacture social completion.
- The rendering loop can interpolate between snapshots locally. It does not
  require a Python round trip for every displayed frame.
- The Pyodide Worker executes Aiko; the Service Worker serves offline files and
  handles push events. Neither provides guaranteed continuous background life.
- Protect against a second window/tab creating two live writers for one save.
  Use existing revision checks plus a tested single-session admission mechanism.

## 6. Implementation phases, commits and exit gates

Commit labels below are a proposed order, not commits already made. Each commit
must be cohesive, reviewed and validated. Split further when needed; do not
combine unrelated fixes just to match a label. A diagnostic slice must not be
presented as the complete functional test delivery.

### Phase 1 — early technical feasibility, before broad UI transfer

Commits:

- C01 `build(room): add reproducible web and runtime packaging`
- C02 `feat(pwa): add offline starter and diagnostic zip import`
- C03 `feat(browser): run an isolated Aiko session in Pyodide`

Use small real core actions and a basic Pixi scene. Include the pinned Pyodide
runtime, needed packages/metadata and a realistic asset sample. Preserve simple
diagnostics for runtime errors and storage status without exposing private data.

Actual-iPad check with the user's device:

1. Open the stable HTTPS starter, manually add it to Home Screen and launch it
   from the icon before importing app data.
2. Download the runtime ZIP via Dropbox or GitHub; select it from Files within
   the installed app. No Dropbox/GitHub account integration is required in Aiko.
3. Start Python and Pixi, perform a real core action, persist and reopen it.
4. Test SQLite import/write/revision and required file publication; explicitly
   check os.link/backup/replace assumptions and IDBFS synchronisation.
5. Confirm package resources, Astronomy Engine and reviewed pyjokes metadata can
   load locally. Exercise a representative Connect Four search/cancellation.
6. Cold-start in airplane mode, including after an iPad reboot.
7. Import a second package and retain the same pet data/icon.
8. Record iPad model, iPadOS, package/runtime versions, start time, memory-related
   failures and the observed results. Windows browser success alone is not this gate.

Exit: documented end-to-end evidence, or a concrete adapter change/retest before
large-scale transfer. If no actual iPad evidence is available, leave this gate
pending rather than calling the route proven. Continue only independent design
work, not broad implementation predicated on an unproved deployment route.

### Phase 2 — canonical room model, fixed routine and contracts

- C04 `feat(world): define room locations and reference layout`
- C05 `feat(room): add spatial movement and fixed daily routine`
- C06 `feat(application): expose typed room commands and snapshots`

Translate prototype geometry into canonical room data; extend World contracts,
movement and persistence with compatible defaults/migration. Add RoomCoordinator
and RoomSession around existing services. Parameterise schedule/sleep inputs so
the iPad never trains the user's rhythm. Set the initial routine times explicitly
in the profile before acceptance; do not silently inherit learned desktop data.

Exit: headless examples cover call/approach, depth/reach, fixed routine, manual
sleep/wake and unchanged desktop coordinates/saves. Architecture tests prove
single ownership and domain/platform separation.

### Phase 3 — complete browser session and portable presentation

- C07 `refactor(presentation): share cancellable reaction and game playback`
- C08 `feat(browser): compose care social and game session services`
- C09 `feat(storage): persist complete browser sessions safely`

Reuse portable ReactionPlayer/sequences and existing pure projections. Add real
browser timer/network/storage adapters. Integrate horoscope and local resources.
Move Connect Four search onto a tested execution strategy: bounded cooperative
work or isolated pure-search Worker with immutable inputs and cancellation;
never introduce a second mutable pet owner. Test each social provider's CORS.

Exit: every command family reaches its real owner; complete snapshots survive
reopening; stale events/search replies cannot mutate a new session; storage
errors remain visible and leave the last valid checkpoint recoverable.

### Phase 4 — shared room drawing, independent camera and input

- C10 `feat(room-ui): render the referenced room and character states`
- C11 `feat(room-ui): add independent camera and semantic object input`

Implement RoomProjection/RoomView, layers, depth, wrap and animation anchors.
Use pixi-viewport for applicable camera primitives. Route drawing from actual
snapshots and presentation events. Add call action and drag-versus-camera gesture
ownership, pointer cancellation and screen-to-room coordinates.

Exit: compare representative views to v16; camera movement does not alter Aiko's
location, perception or routine. Touch and mouse work against the same actions.
Verify portrait/landscape, edge/wrap crossings, object layering and interruption
on the iPad as well as Windows browsers.

### Phase 5 — all care, status, conversation and book surfaces

- C12 `feat(room-ui): expose complete care status and wish controls`
- C13 `feat(room-ui): present authored and sourced conversations`
- C14 `feat(room-ui): support the complete local horoscope book lifecycle`
- C15 `feat(room-ui): add applicable settings credits and accessible details`

Close C/F/O/A/S/H/W/U parity rows, including all food choices, refusals, boundaries,
real object handling, dialogue advancement, source opt-in, credits, retries and
horoscope interruption/restart. Keep German product text in canonical resources.

Exit: a feature-by-feature checklist has actual results. Test offline Plaudern,
local jokes and horoscope; separately test fresh online categories and failure
states. Hidden or hover-only desktop information must remain touch-accessible.

### Phase 6 — all six game views, one at a time

- C16 `feat(room-games): add rock paper scissors parity`
- C17 `feat(room-games): add tic tac toe parity`
- C18 `feat(room-games): add blackjack parity`
- C19 `feat(room-games): add connect four parity`
- C20 `feat(room-games): add mastermind parity`
- C21 `feat(room-games): add quiz parity`

Each commit includes its existing rule/session integration, view, timing,
commentary and outcome tests. Finish with G07 cross-game lifecycle verification.
Preserve hidden information and staged reveal boundaries, not just final scores.

Exit: actual iPad play of every game; correct qualified rewards and wish progress;
no duplicate credit, leaked timers or stale search results after close/switch.
Do not mark this phase complete with only one example game implemented.

### Phase 7 — absence wishes, robust updates and T1 delivery

- C22 `feat(wishes): share simple absence progression and forecasts`
- C23 `feat(pwa): activate validated package updates without losing pet data`
- C24 `test(room): verify full core parity and device delivery`

Reuse current wish selection/expiry rules at explicit shared evaluation deadlines.
Persist isolated wish randomness so preview and catch-up agree without dialogue
randomness changing forecast outcomes. Preview copies Pet/World/Memory and the
same durable starting representation; it never mutates live state. Do not add
movement replay, a general event-sourcing engine or permanently locked wishes.

Complete the package format: version, protocol/save compatibility, entry files,
required resources and integrity inventory. Validate/stage all files before
switching one active-version pointer. Keep the bootstrap/Service Worker separately
hosted and compatible with package versions; a ZIP does not silently replace
Safari's install step or the Service Worker update mechanism.

Test failed imports, insufficient storage, interrupted activation, incompatible
packages and migrations. Do not promise rollback across a save schema change
without retaining and verifying a compatible checkpoint. Updates preserve data
and the installed app identity. Prepare a built runtime ZIP for both Dropbox
and GitHub download; no publishing is performed merely by completing a local build.

T1 exit: all mandatory section-3 rows pass, the referenced autonomous room works,
fixed routine/catch-up/absence wishes are correct, and offline cold-start/update
checks pass on the actual iPad. The test packet contains version/hash, brief
German setup steps, expected checks and known limitations. Internal slices are
not substitutes for this complete first functional version.

### Phase 8 — notification integration and T2

- C25 `feat(notifications): produce revisioned forecast schedules`
- C26 `feat(push): deliver and replace scheduled web notifications`

Select a small number of meaningful future messages from the local forecast.
Store and replace the plan after relevant interactions/reopening; persist the
subscription and durable timed jobs at a separately operated minimal sender.
The sender receives only the delivery payload/deadline/version needed for push,
not the whole pet save. Messages do not imply the wish still exists when opened.

Settle hosting of this small service before implementing/deploying it. Plan
identity and cancellation must prevent superseded jobs from being sent; messages
already handed to a push service cannot be guaranteed retractable from a device.
On open, catch up local Aiko first. The notification itself grants no care credit.

T2 exit: actual iPad permission/subscription, closed-app delivery, stale-plan
replacement, offline/delayed delivery and tap-to-open tests. Record server
deployment and Internet dependence explicitly. This is new functionality after
T1 core parity, not a missing pre-existing Tamagotchi function.

### Phase 9 — later desktop host and D1

- C27 `feat(desktop-room): host the shared frontend through RoomClient`
- C28 `feat(desktop-room): coordinate taskbar and room environment handoff`

Choose the native host after a focused Tk/event-loop/transport check. pywebview
with WebView2 is a candidate, not a settled integration. A separate host process
may transport commands; it must not construct another authoritative pet session.
Calls from host threads are marshalled to the existing state owner.

Connect the same built room frontend to native Python. Define later the exact
room/taskbar handoff UX, object access and suspended interactions. Preserve one
desktop Aiko, clock and save; no second Pyodide pet runs beside native Python.

D1 exit: real Windows input/focus/close/handoff tests, no duplicate progression,
and no loss or duplication of objects/experiences. This phase is not a reason to
delay the initial iPad core test once T1 is accepted.

### Phase 10 — sustained use and review

- C29 `test(room): record sustained device and desktop acceptance`
- C30 `docs(room): record deployment updates and accepted limitations`

Run multi-day device use across sleep, meals, absent wishes, scarce food, long
closures, repeated package updates, orientation changes and game sessions. Check
startup/responsiveness, thermal/battery observations and memory-related reloads.
Repeat the relevant Windows regression/native checks after shared-core changes.

Review the complete PR against green CI on its exact final SHA. Record accepted
device evidence and limitations separately from automatic checks. Merge/publish
only as the applicable execution task calls for; this plan performs neither.

## 7. Test, CI and acceptance strategy

Retain all existing Python/Tk/Windows gates. Extend CI incrementally with the
web build, TypeScript checks, focused interaction tests and offline/package
integration checks. Test real built files and locally bundled Pyodide, not a
network-CDN path that hides missing runtime files.

| Layer | Evidence required |
| --- | --- |
| Pure Python | Room geometry/routine, existing care/game policies, wish boundaries and preview/catch-up consistency. |
| Ownership/contracts | Import direction, single session/World owners, serial dispatch, protocol mismatch, stale revisions and duplicate events. |
| Persistence | Full-owner round trip, durable flush, restart, migration and interrupted update recovery with isolated saves. |
| Presentation | Actual text/action acknowledgement, readable staging, cancellation, hidden-information boundaries and no false completion. |
| Browser | Mouse/touch gesture conflicts, panels, every game, offline resource requests, installed-package routing and reload. |
| Actual iPad | Home Screen install, Files import via both transports, reboot/airplane cold start, state retention, orientation, background/kill, update and later Web Push. |
| Actual Windows | Existing desktop smoke checks plus later native room host and environment handoff. |

Use deterministic clocks, seeded random sources and isolated fixture saves for
automated contracts. Use realistic device actions for native/PWA acceptance.
For every parity row, record not started/implemented/automatically verified/device
verified, the relevant commit/package and evidence. "Implemented" is not the same
as device-accepted. Do not fill acceptance with a historical desktop screenshot.

## 8. Decisions to close at their earliest useful phase

| Decision | Deadline / evidence |
| --- | --- |
| Exact pinned Pyodide/Python and compatible web versions | Phase 1, after real package/runtime checks. |
| Actual iPad model/iPadOS and initial stable starter origin | Before phase-1 device check; use the real device rather than assumed Safari support. |
| Browser SQLite publication and durable storage route | Phase-1 gate, before broad state/persistence integration. |
| CORS access or minimal relay for each online source | Phase 3, before claiming social parity. |
| Explicit fixed daily schedule and supported manual controls | Phase 2, recorded as room data and consistent sleep policy. |
| Search execution/cancellation and acceptable responsiveness | Phases 1/3, using the existing bounded Connect Four search on the device. |
| Prototype shop/economy/upgrades | Separate product decision; no effect on existing-core parity. |
| Notification sender host, operation and deployment | Before phase 8; offline native scheduling is not the PWA fallback. |
| Desktop host, transport and room/taskbar switch UX | Phase 9; maintain the shared RoomClient contract before then. |

Do not add mandatory architecture work merely because it might be useful later.
Close measured blockers at their gate; leave later UX decisions explicit without
forking the core or prematurely implementing a native shell.

## 9. Execution record

| Milestone | Status |
| --- | --- |
| Phase 0: green desktop branch, merge, green main, fresh room branch | Complete. PR #11 merged; subsequent workload fix and CI correction included at green `ce4797e`. |
| Actual-iPad technical feasibility | Pending. |
| T1: complete Tamagotchi core in the shared room PWA | Implementation and local automated checks complete; GitHub and actual-device parity acceptance pending. See [verification](VERIFICATION.md). |
| T2: notification-enabled iPad candidate | Pending. |
| D1: shared room hosted by the desktop application | Later work; pending. |
| Multi-day acceptance and final review | Pending. |

The room branch is pushed. The owner-approved first-download site and test
prerelease `room-test-0.1.0-d073fc2958cf` are published; the single installation
ZIP has been copied to the owner's Dropbox and confirmed downloadable there.
No merge into main has been performed. Generated program/installation ZIPs stay
outside source Git; the deployment branch pins only their release metadata.

## References

- [Current architecture](../ARCHITECTURE.md), [World contracts](../WORLD_OBJECT_CONTRACTS.md), [UI contract](../UI_WINDOW_CONTRACT.md).
- [Sleep rules](../SLEEP_SYSTEM.md), [social content](../SOCIAL_CONTENT.md), [data and saves](../DATA_AND_SAVES.md).
- [Pyodide browser constraints](https://pyodide.org/en/stable/usage/wasm-constraints.html), [Web Worker](https://pyodide.org/en/stable/usage/webworker.html), [file systems](https://pyodide.org/en/stable/usage/file-system.html).
- [Pixi input](https://pixijs.com/8.x/guides/components/events), [AnimatedSprite](https://pixijs.download/release/docs/scene.AnimatedSprite.html), [pixi-viewport](https://github.com/pixijs-userland/pixi-viewport).
- [Vite](https://vite.dev/guide/), [Workbox custom Service Worker](https://developer.chrome.com/docs/workbox/modules/workbox-build), [fflate](https://github.com/101arrowz/fflate).
- [Home Screen web apps and Web Push](https://webkit.org/blog/13878/), [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).

Library capabilities are documented; this combined Aiko deployment is not yet
device-proven. Record actual integration evidence at the phase-1 gate.
