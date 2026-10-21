# Architecture — canonical pet and desktop UI packages

Aiko Desktop Pet is a local-first Windows companion built with Python 3.11+, Tkinter and prepared PNG artwork. The program requires no remote services or inference model at runtime. This document describes the **current code structure**, not the original v0.7–v0.13 implementation history.

The key design principle: **one owner per mutable state or external side effect**, with small, named interfaces between components. Imports point directly to the packages that own each responsibility.

Optional [social API content](SOCIAL_CONTENT.md) uses an explicit opt-in. The
application owns source-aware preparation and three two-item buffers through a
worker port; `infrastructure/social_api.py` owns the single HTTP worker. Desktop
coordination admits prepared content through the existing `talk` transition and
reaction player. It creates no additional pet aggregate, settings owner or
persistent content cache.

Current behavior is defined in the [World contract](WORLD_OBJECT_CONTRACTS.md).
The [documentation index](README.md) separates maintained guides, validation and
accepted desktop behavior from [completed delivery history](history/README.md).
Historical plan rules and pending checklists are not an active roadmap.

Object attention, learned identity, appraisal, current wish, tracking and search
remain distinct. `ObjectBehaviorCoordinator` owns one immutable
`OrientationProgress`: after focus releases, both learned-place looks complete
before ordinary new goals. `SearchTask` owns recovery subjects and route progress
across candidate action episodes; the current patrol phase is a separate fact.
Required loss bubbles precede investigation. Observed transport preserves acquired
knowledge without granting identity to unknown sightings. All movement executes
through the existing WalkDriver and mutable pet aggregate.

## Dependency overview

```mermaid
flowchart TB
    Shell["gui.py — DesktopPet (composition root)"]
    App["application/ — care, attention, activity and commands"]
    Pet["pet/ — PetState, PetMind, animation and movement policies"]
    View["ui/view_models/ — immutable UI projections"]
    Sprite["ui/pet_view/ — sprite, overlays and reaction playback"]
    Windows["ui/windows/ and ui/common/ — controls and reusable Tk helpers"]
    Desktop["desktop/ — timer, pointer/input and native Windows adapters"]
    Infra["infrastructure/ — hardware, item/animation loaders and JSON save"]
    Ports["application/ports.py and telemetry.py — read contracts"]

    Shell --> App
    Shell --> Pet
    Shell --> Sprite
    Shell --> Windows
    Shell --> Desktop
    Shell --> Infra
    App --> Pet
    App --> Ports
    View --> App
    View --> Pet
    Sprite --> Pet
    Windows --> View
    Windows --> Pet
    Desktop --> Sprite
    Desktop --> Windows
    Infra --> Pet
    Infra -. "satisfies reader contracts" .-> Ports
```

The solid arrows highlight major code dependencies; the dotted provider-to-port
relationship represents structural compatibility, **not** an import from
infrastructure into the application. The checked-in tests enforce
additional import rules. Platform-level coordination intentionally happens
in the desktop shell; the architecture does not pretend to eliminate
all runtime coupling between composed services.

## State and business rules

**`pet/state.py — PetState`** is the only mutable, persisted pet aggregate. Its public `interact(action, now=...)` and `advance(now, ...)` operations commit care and elapsed-time state changes. Pure policy modules in `pet/` calculate immutable decisions:

Stages 6-7 complete PetState encapsulation. ProgressionValues, CareValues,
RoutineValues and FriendshipRecord expose read-only properties and
Sequence/Mapping policy inputs. PetState retains one frozen
`pet/state_values.py::PetValues` value, replacing it only within owned
transitions; the existing named constructor, equality and deepcopy contracts
remain usable. Public scalars are read-only properties, and public
meal/reward histories are detached list/dict copies, never writable handles
into the aggregate. The complete PetValues checkpoint is distinct from the
smaller application-facing PetReadSnapshot. PetState owns
`capture_checkpoint()`, `prepare_item_consumption()`,
`restore_checkpoint()` and `anchor_live_session()`; recovery preserves
the same live aggregate identity. Legacy `restore_values()` remains as a
compatibility wrapper around explicit checkpoints, not a public field setter.
Only test-only smoke/scenario helpers manipulate prepared checkpoints for
isolated test data. Current maintainer-reported desktop acceptance is recorded
in the [smoke guide](WORLD_SMOKE_TEST.md#acceptance-status).

`interact()` returns a language-neutral `CareResult` from `pet/care_result.py`.
The one care decision owns acceptance, consumption, the chosen food and meal
credit. Application outcomes expose that same result; they never recalculate
satiety or energy thresholds. `application/active_time.py` owns the immutable
`SessionInputs` record used by ticks, care and completed games. Its
`advance_session_time()` function consumes the shared clock interval exactly
once and forwards the same schedule, workload and nutrition context. The mind
captures pre-care conversation context before mutation, then
interprets the committed effect.
German fallback wording is selected only by `ui/view_models/care_text.py`.

- `care_actions.py`: `CareTransition` for care actions and their rewards.
- `needs.py`: frozen `NeedLevels` contains exactly satiety, energy, fun, social
  and affection. Mood and friendship are separate values, not care needs.
- `progression.py`: frozen `PetProgress` for all numeric time progression,
  with separate need, mood, food and relationship results. Integrates targets with the
  existing pure food/fun/mood policies; `PetState` applies one result. It reads
  no clocks, owns no mutable store and offers no alternate precomputed path.
- `friendship.py`: rolling relationship credits, contact and direct penalty caps.
- `friendship_decay.py`: progressive passive loss during the existing need steps;
  `friendship_history.py`: immutable elapsed-axis evidence inside PetValues.
- `lifecycle.py` and `routine.py`: streaming full-time advancement and local schedule.
- `sleep.py`: immutable sleep episode/context and pure priority policy;
  `PetState` owns episode/protection/break transitions in its full checkpoint.
- `mind/quiet_rhythm.py`: bounded coarse quiet phases and window recurrence,
  inside the existing adaptive memory, independent of workload classification.

Food and localized UI content now have distinct, validated JSON owners:
`data/balance.json` holds the initial values and named gameplay parameters;
`data/food_catalog.json` holds nutrition/menu records;
`data/texts.de.json` holds care, mood, emotion, workload, status and
game-message copy; `data/routine.de.json` holds day schedules;
`data/dialogues.de.json` holds authored situational lines.
`data/object_grammar.de.json` holds grammatical metadata only, validated and
loaded by the existing `pet/content.py` owner. Immutable contracts and the
finite placeholder set live in `pet/object_text_contract.py`; the pure
`ui/view_models/german_object_phrases.py` inflects articles and pronouns for
object reactions and care fallbacks. It makes no recognition, custody or
search decisions and does not duplicate canonical food/menu names.
`assets/items/items.json` holds only item paths, dimensions, pivots and
weapon labels, not duplicate food names or menu icon conventions.
`desktop/animation_assembly.py` loads one immutable `ItemCatalog` and
shares it with the hand overlay and food picker via typed UI values. Python
food/status catalog models validate resource data; they do not define a
second, independently editable list of food profiles or emotions.
`pet/catalog_validation.py` rejects malformed JSON, duplicate keys and
non-finite numbers. Typed catalogues reject missing/unknown fields, invalid
references, text placeholders and inconsistent balance ranges before use.
See [resource ownership and local saves](DATA_AND_SAVES.md).

**`pet/mind/mind.py — PetMind`** selects reactions and maintains short-term conversational context. It does not own Tk windows or play sounds. `WorkloadEventDetector` in `pet/mind/workload_events.py` converts observed load changes into event keys. Authored Aiko dialogue remains in `aiko_pet/data/dialogues.de.json`; it is not regenerated by this refactor.

**`application/session_time.py`** coordinates existing Pet/World/object-memory
owners between the shared planner's intervals. `ObjectConsumption.apply_portion`
commits historical or animated intake with the same rollback contract. The
session restorer reconstructs the paired owners before progressing closed time;
the existing World access port supplies that same coordination explicitly to
application use cases. The clock only measures elapsed time. One plan is
applied through PetState's shared step operation, without nested replanning;
first-save history is initialized once for the complete interval. Live movement,
perception and intake remain with their existing World interaction owners.
No extra need integrator, clock, search, movement writer or pet store is added.

**`pet/mind/adaptive.py`** learns coarse local daily patterns from observations. Unknown hardware readings do not become fabricated activity. No application names, process titles or content are collected for this version.

`PetState.status_hint()` returns a typed `StatusHint` key from
`pet/status_hints.py`. The exact same pure policy works on the immutable
`PetReadSnapshot`; only `ui/view_models/text_de.py` selects German status
wording. `PetState.due_meal()` returns a due meal ID, and the UI decides
whether to display a meal name or "Snack". Historical localized helpers
`TimeContext.label`, `TimeContext.schedule_line` and
`TimeContext.greeting()` have been removed; localized weekday/status display
belongs to `ui/view_models/text_de.py`.

`pet/moodlets.py` defines immutable Moodlet catalogue values and distinct
emotional directions. `pet/moodlet_catalog.py` strictly loads nineteen
families from `data/moodlets.json`, with shared caps/recovery settings in the
existing balance catalogue and descriptions in the existing German text owner.
`pet/wishes.py` and `pet/wish_catalog.py` provide twelve wish objective
forms in `data/wishes.json`, referencing actual food/game targets and positive
Moodlet definitions. Shared creation/disclosure settings and the nominal wish
friendship bonus live in the existing balance catalogue. The pet package does
not import application social preparation; social objective IDs are checked
against supported categories in focused tests. Labels/descriptions stay in
`texts.de.json`. Both catalogues detach nested values into frozen dataclasses,
tuples and read-only mappings.

Food avoidance is eligible only with an actual repetitive-food reason and the
food need gate. Failed non-loss game wishes create the downcast `disappointed`
family without an instantaneous friendship penalty. Game selection applies
catalogue weights within an eligible area; non-game forms retain equal selection.
`WishGoal`/`WishObjective`
preserve each active wish's original meaning and count independently of newer
catalogue meanings. Older saves migrate to their actual delivered objectives,
and new creation snapshots the current catalogue goal: cumulative rounds/wins
across sessions, strict next-round results or the fixed overall-result block.
`GameWishRead.required_count` is interpreted in the original objective's unit.
The persisted pin flag protects lifecycle now; pin/dismiss UI controls follow separately.

`PetState` commits wish retirement and bounded concrete Moodlet causes together.
Causes retain the original wish/target, semantic receipt, actor and actual outcome;
game causes distinguish objective outcome from final-round result/counts. At most
three actual causes live with each active Moodlet, without a completed-wish archive.
Duplicate receipts cannot reinforce or refresh the same impression.

`ObjectConsumption` admits a personally perceived food release through the
existing cursor/interaction handover owners, including a recognized refusal or
identification after taking the food. This fulfills food avoidance once even if
the offered food was unwanted, without fabricating nutrition or accepted contact.
Preview, ground placement and autonomous intake cannot substitute for handover.
Ordinary food wishes require actual matching intake; the existing prepared
World/Pet/Memory consumption transaction includes the portion ID in its cause
and preserves rollback and offline attribution. Physical care and food-monotony
consequences remain independent. No extra event store or progression clock exists.

Pet rules share only `games/contracts.py`'s immutable game IDs and outcome type;
they never import game implementations, sessions or scores. The package boundary
gate checks resolved import targets, including this narrow shared-contract rule,
rather than treating relative-import depth as a domain boundary.

`MoodletState`/`MoodletEpisode` and `WishState`/`ActiveWish`/`GameWishProgress`
are frozen values owned by `PetValues` and exposed read-only by `PetState`.
Focused `infrastructure/moodlet_codec.py` and `wish_codec.py` extend the existing
`pet_codec.py` entry point and outer version-one atomic save. Checkpoint/restore
includes both collections in the existing Pet/World/memory transaction.
Elapsed timestamps refer to `lived_seconds`; loading never advances them or
creates emotional evidence. Wish IDs, creation evidence and refill deadlines survive
removed wishes;
round receipts are bounded independently of cumulative attempt counts and never
become a second game session/score owner. `MoodletCause`/`MoodletWishCause` preserve
at most three real, language-neutral trigger snapshots within the active episode.
Their wish keys are validated by codecs, avoiding a domain import cycle. Old
episodes have explicit unknown evidence; expiry removes causes with their episode.
Immutable application reads expose original goals, pins and causes, without
owning history or changing the UI. Friendship rewards retain their existing
history owner.

`pet/wishes.py` also owns pure creation, original-deadline expiry, temporary
restrictions and disclosure eligibility. The existing `PetState` progression
expires wishes during live, closed and standby time. Creation is a separate
live-endpoint operation: `DesktopAttentionRuntime.handle_time_progress()` asks
the existing `AttentionCoordinator` to replenish the normal three inner wishes,
even while presentation is occupied. `replenish_wishes()` fills available areas
at the current endpoint using the existing Mind RNG and aggregate-owned current
`NeedLevels`. Food/affection creation requires their need at most 70 and existing
petting willingness. At 90, live evaluation neutrally retires an unpinned supplied
wish; actual matching care resolves first in its existing transaction. Games/social
have no fun/social gate. Retirement starts one saved
twelve-minute refill pause; further vacancies do not postpone it. Four-hour
expiry uses its original deadline unless pinned, including offline; generation remains
awake/live only. Legacy saves without a refill deadline can fill available slots
at the next live evaluation. The old global/hour and same-area/ninety-minute
creation locks are removed; one wish per area and independent disclosure remain.

`ActiveWish.is_active_at()` consistently applies protected lifetime to fulfillment,
speech selection and actual expression receipts. `PetState.set_wish_pinned()` and
`dismiss_wish()` expose neutral aggregate-owned operations without new care or
reward events. Unpinning cannot renew the original deadline or revive an expired
unprotected instance. A late unpin starts its vacancy now; dismissal neither clears
Moodlets nor resets another pending refill. No extra store or clock is introduced.

`WishContext` is a frozen current capability/acceptance input, not another
state/history owner. Attention reads pure existing petting admission, game
energy rules, Moodlet context and online opt-in. The existing social runtime
exposes prepared categories without fetching or reserving a buffer item.
Temporary restrictions retain each wish's identity, slot and original deadline;
their typed reason can feed the later status projection.

At a free speech opportunity, care urgency precedes wishes and ordinary
commentary. PetMind renders the concrete wish from `texts.de.json` and attaches
its instance ID to the existing immutable `Reaction`. The existing
`ReactionPlayer` acknowledges that ID only after the text display succeeds;
the aggregate ignores duplicate, absent and expired IDs. There is no second
player or wish queue, and disclosure grants no contact, care or emotional
reward. Fulfillment is delivered below; the combined status presentation remains 5C.

Stage 5B.7 uses pure `fulfill_activity_wish()` and `progress_game_wish()` results
in the existing `wishes.py`. `PetState._apply_wish_resolution()` commits retirement,
the catalogue's one positive Moodlet family/strength and any shared-pot personal
reward together. Creation anchors and allocation survive retirement. The existing
Moodlet reinforcement/progression owners retain stacking, refresh, decay and
numeric caps; fulfillment does not jump numeric mood or erase negative episodes.

Accepted food intake and welcome petting resolve through the existing care
transition after ordinary credit. Autonomous intake uses the same food match
inside the existing World/Pet/Memory transaction, including finite known stock
reconstructed before the deadline, without personal reward/contact.

The three existing game sequences emit immutable player-perspective
`games.contracts.GameRoundEvent` start/settled-result facts through typed window
ports, the router and `GameExperienceCoordinator.observe_round()`. That existing
coordinator holds one transient pending attempt (identity, elapsed start and
pre-existing wish ID), translates the result once, and retires the attempt after
a successful commit. No score, board, deck or unplayed round is reconstructed.
Only bounded objective progress persists. Normal session care still occurs once
at window close; immediate wish resolution occurs at the qualifying round, not
at a convenient later close. The common reward budget constrains both boundaries.

`SocialCompletion` now carries the admitted category and optional existing wish
identity through the same `Reaction`/`ReactionPlayer` lifecycle. The existing
controller applies helpful relief and category-specific fulfillment only after
the whole sequence completes. Cancellation, an unrelated/expired/replaced wish,
preparation and a wish first created during playback cannot grant the outcome.
Desktop coordination saves completed social/round outcomes using existing storage.

`pet/moodlets.py` now owns pure tier ageing, bounded reinforcement, resolution
and per-level relief. Definitions are supplied by the canonical catalogue;
shared coefficients remain in balance JSON. `pet/mood.py` composes the capped
contributions with need-based mood, and `pet/progression.py` splits its existing
numeric steps at emotional/recovery boundaries. Its frozen result includes
Moodlet state, committed once by PetState with the existing elapsed progress.
Reconstructed time is explicitly unobserved on both restoration paths, so it
ages after-effects without inventing continued user provocation. No additional
clock, replay loop, mutable manager or numeric mood writer is introduced.

`pet/interaction_events.py` defines immutable perceived facts and bounded
interaction evidence. Pure `interaction_rules.py` qualifies negative experiences
and helpful-action matching; it delegates stacking/ageing/relief to `moodlets.py`.
`plan_care_action()` owns petting admission and returns the same immutable
consequences that PetState commits. Two tolerated extra strokes receive distinct
accepted-care effects and feedback; the third refuses, and only subsequent
disregard of displayed refusal produces crowded and direct loss. A bounded count
and last-additional-attempt timestamp live in `InteractionMemory` and save v1,
alongside the communicated boundary and independent refusal deadline. Warning
reset, refusal renewal and Moodlet decay share the existing elapsed axis.
`CareResult.affection_accepted`/`affection_refused` keep controller, Mind, wish
resolution and animation consistent. `petting_is_welcome()` separately exposes
real willingness for wish eligibility without executing/spending an extra stroke.
Level-ten trust permits full-affection contact while active refusal still binds.
Direct friendship losses use the existing
relationship ledger, independently of the continuing impression. No event bus
or additional mutable owner is introduced. The application translates visible
text receipts into boundary facts. Explicit metadata on accepted social
reactions yields completion only after the entire existing playback sequence.
Object owners qualify wanted-object withholding separately from confirmed
learned-place loss. Only absence admitted to the existing missing-object search
creates the disrupted-arrangement Moodlet. Continuously observed transport and
placement update subjective knowledge without that Moodlet or relocation loss;
there is no second relocation-origin tracker or competing trigger. Missing-place
evidence alone never proves user blame. Closed-time intake
can create food monotony but never human culpability. Short-lived custody and
observed-time trigger anchors stay in the existing object episode/perception;
refusal/request/intake evidence belongs to the aggregate and its existing save.

`pet/need_exposure.py` reads the existing bounded relationship/care history.
`pet/poor_care.py` qualifies the five lasting poor-care impressions, using frozen
processing markers in MoodletState rather than another history or simulation.
The same progression loop advances original exposure, emotional recovery and
numeric mood; it splits at actual zero/25/40 and new burden thresholds. A
qualified emotional recovery closes handled thresholds while preserving fresh
residual exposure. Inadequate care or a brief improvement does not reset that
cycle. Old history before the processing baseline is not retroactively emotional.
The existing Moodlet lifetime owner retains pause/resume and relief allowances;
PetState remains the single mutation owner. Pure numeric calls without supplied
relationship evidence do not invent an absent history or qualify poor-care events.

Wish lifecycle/fulfillment and overall emotional interpretation are delivered.
`pet/emotions.py` derives a frozen `EmotionalComposition` from every active
Moodlet's intensity, retaining all directions, causes and known attribution.
It owns no state, timer, reward or refusal. Positive/negative totals select the
winning polarity; its strongest combined direction selects the label. Equal
nonzero totals produce ambivalence. Without Moodlets, numeric mood supplies
subdued below 40, calm below 70 and satisfied from 70. Numeric caps never
truncate emotional evidence.

`PetMind.emotional_state()` and the application snapshot call that same pure
policy. `reaction_tone()` exposes the independent short irritation/warmth
reaction; `record_accepted_care()` records accepted timing and starts the
existing brief care response. Sleep never clears lasting Moodlets.
`DialogueContext` separates numeric mood, emotional composition, typed need
conditions, situational fatigue/playfulness, sleep, presence and relationship.

`application/read_snapshot.py` exposes frozen `MoodletRead`, `WishRead` and
bounded `GameWishRead` values on the aggregate's existing elapsed axis. Hover
and status projections share one `EmotionalSnapshot`, with German labels,
concrete targets, remaining stage/deadline work, paused recovery, expression
flags, objective counters and current temporary restrictions. The status label
is derived from that snapshot, rather than stored independently.
`DesktopPresentation` receives the existing attention owner's `wish_context`
read port; it needs neither a Mind object nor a clock. Reading cannot consume
API buffers, advance time, acknowledge speech or apply rewards. Stage 5C renders these values in the existing status window through
`MoodletStrip`, `WishPanel` and shared VN controls. Embedded selector frames
replace only the interaction column; HoverUi remains the sole transient-menu
and visibility owner. Settings keeps its independent window, with four page
views and central `CreditsPanel`; the latter receives detached metadata via
`project_credits()` from the existing social snapshot. No new native submenu,
window manager, state store, API queue or preference store is introduced.

## Application layer

- `CareController.execute()` advances pet time, coordinates the character's care event, applies the command and returns a presentation-independent `CareOutcome`.
- `ContactCoordinator` coordinates intentional cursor entry, user clicks and startup greetings through UI effect ports. `PetMind` still chooses all authored dialogue.
- `ApplicationRouter` accepts owner-thread care commands and validated, bounded incoming notifications. An external HTTP or IPC server is **not implemented**.
- `ActivityCoordinator` consumes hardware samples and coordinates adaptive observations and elapsed-time pet state.
- `AttentionCoordinator` controls spontaneous lines, non-interrupting notifications and idle gestures.
- `PetSessionRestorer` restores pet, World and acquired knowledge through a narrow reader port before coordinating full closed time, expected sleep and finite known-stock intake. It never generates meals or user observations.
- `PetReadSnapshot` is an immutable, language-neutral copy for presentation and potential future read-only adapters.
- `application/ports.py` describes capabilities such as `ComputerReadings`, not concrete OS drivers.
- `application/assembly.py` builds the single care/game/activity/cursor
  use-case graph using existing state, mind and active-session clock. The
  assembly imports no desktop, Tk, or infrastructure implementations.

The application never imports Tkinter or native system monitor implementations.

## Pet animation, UI views and Tk widgets

Pet-owned pure behaviour lives in `pet/animation/` and `pet/movement/`:
`gaze.py` computes sixteen directional sectors, `ambient.py` schedules
subtle idle motion, `animation.py` owns frame-selection and timing policies,
`timing.py` validates already-decoded animation profiles, and the
`RandomWalkPlanner` selects departures separately from the `WalkController`'s
movement execution. `pet/mind/cursor_attention.py` retains only short-lived
pointer-attention timestamps, not operating-system access.

`ui/pet_view/` owns the concrete renderer and overlays:

- `AnimatedPet` owns Tk frame playback, sprite caches, overlays and
  per-frame animation callbacks. Its `render()` applies a typed
  `RenderDecision`; it no longer chooses behavioural priority, reads
  hardware, owns gaze history or constructs a walking controller.
- `DesktopAnimationRuntime` (`desktop/animation_runtime.py`) composes pure
  pet animation policies, attention timing and already observed host facts.
  Its single `AmbientDirector` is passed into `AnimatedPet` for head sway
  and complete blink-frame playback without duplicating ambient state.
- `DesktopVisualObservation` (`desktop/visual_observation.py`) owns
  16-direction gaze hysteresis and reads cached workload only when needed.
- `WalkDriver` (`desktop/walk_runtime.py`) translates host placement and
  the current attention/work situation into steps from the single pet-owned
  `WalkController`. Tk frame callbacks still advance movement smoothly.
- `CharacterSpriteCache` handles runtime sprite frames, including lazy 2x
  variants. `RestPoseRenderer` handles pose-relative head motion, and
  `FoodOverlay` renders the selected hand item without affecting nutrition.

At shutdown, the lifecycle closes `AnimatedPet` before destroying Tk. The sprite
owner releases original/zoomed/rest-pose images and its food overlay on Tk's
thread; delayed background garbage collection does not own those image effects.
- `SpeechPresenter` and `ReactionPlayer` display timed text and emote cues.
  The pure need-based idle emote choice lives under `pet/animation/`.
- `ActionPlayback` owns the current visual action state and deadline, not the
  desktop shell. `CarePresenter` renders accepted care outcomes, including
  held items, reactions and status refreshes. `AttentionPresenter` translates
  approved spontaneous speech, idle gestures and notifications into visuals.

`ActionPlayback.clip_id` identifies the running animation clip; it is distinct
from the pet aggregate and its needs. `CarePresenter` uses the result's action
and consumed item directly instead of accepting a second copy of that action.

`ui/windows/` owns `HoverUi`, the pinnable `ActionToolbar`, `FoodMenu`,
`SettingsWindow`, the game selector and three game windows. Controls are
independently movable where applicable. `ui/common/` owns reusable skin and
window-dragging helpers; `ui/view_models/` owns `DesktopPresentation`,
immutable status/hover/settings contracts, projections and localized UI copy.

No user-facing window owns PetState transitions. Actions are sent to the
application boundary through named callbacks. The pet sprite and the utility
windows are distinct UI owners even though both use Tkinter.

Menu engagement (`HoverUi.menu_engaged`) only suppresses incidental chatter
and uncommitted wandering. It is not character-action ownership and does not
block World discovery or committed object movement. `BehaviorFacts` receives
`character_action_busy` from actual non-offer reaction playback/online waiting,
with sleep, games and animation playback retaining their separate rules.

Snacks use the `place_item` command and `can_place_item` capability, independently
of direct-care `can_interact`. `DesktopWorldRuntime.begin_carry` prepares finite
World stock without interrupting Aiko. `CursorItemGesture` admits one capture,
preserves an existing held portion and refuses a foreign Tk grab. Normal release
still attempts authorized handover before dropping the item. Offer previews
retain their existing handover eligibility; `ObjectFeedbackPresenter` only
cancels its own offer/refusal speech when a cursor gesture is cancelled.

### Minigame owners

`games/` owns each transient session's rules and score, with frozen card/board
reads and a common `SessionSummary`. `HoverUi` owns the sole active `GameWindow`
and a cancellable pending selection while World finishes interruption. Its
submenu has no game/care effect. Per-game sequences under `ui/windows/` own
turn/reveal pacing through injected timers; the game owns result settlement.
The application summary adapter uses the existing game-experience coordinator.

`ui/pet_view/BlackjackHandPresenter` (in `blackjack_hand_presenter.py`) owns the
separate floating-card window and visual hover/flip timers. It receives a
masked `HandView`, not a hidden hand or World state. `GamePanel` supplies small
window chrome for the two new player panels; it owns no rules. The root-local
`PlayingCardImages` cache is shared by both Blackjack views.
`desktop/game_assembly.py` composes these existing boundaries and native effects;
`WindowStack` remains the z-order owner. Placement and preference changes update
the same card presenter. Speech, pet movement, World custody and saved pet state
retain their owners. See the [delivery record](MINIGAME_IMPLEMENTATION_PLAN.md).

`presentation/`, `personality/` and the former root-level `ui/*.py` widget
forwarders have been **removed**. Runtime and tests import directly from the
owning `pet/`, `ui/`, or `infrastructure/` module. See the
[UI window contract](UI_WINDOW_CONTRACT.md).

## Desktop runtime and operating-system adapters

`gui.DesktopPet` is the composition root. It wires typed callbacks and starts
`DesktopLifecycle` without owning a duplicate application or animation state.
`desktop/animation_assembly.py` constructs the interdependent WalkDriver,
visual observer, animation runtime and sprite as one bounded assembly.
`desktop/session_runtime.py` coordinates lifecycle advancement, window
refresh and the advance-before-persist sequence through narrow effect ports.

- `DesktopRuntime` takes explicit `DesktopTickPorts` and owns the ordered 140 ms update cycle and timer IDs.
- `DesktopAnimationRuntime` chooses sprite intent without importing Tk.
  `WalkDriver` executes bounded host displacement, while
  `DesktopVisualObservation` resolves cursor and measured workload inputs.
- `DesktopPreferences` coordinates the consequences of option changes without a second settings model.
- `application/settings.py` defines `PetSettings` as the single settings
  aggregate, composing `PetBehaviorSettings` and `DesktopDisplaySettings`.
  The historical flat properties and version-one JSON keys are preserved; no
  preference value is duplicated between the two child objects.
- `DesktopInput` owns Tk bindings, global click checks, pointer-coordinate sampling and cancellable delayed focus callbacks.
- `DesktopLifecycle` controls startup/shutdown ordering.
- `desktop/taskbar.py` and `window_stack.py` own Windows-specific taskbar discovery and z-order operations; `desktop/geometry.py` contains pure taskbar value calculations.

`infrastructure/character_assets.py` reads the prepared character catalog into immutable `pet/animation/character.py` contracts before Tk widgets are constructed. `infrastructure/animation_timing.py` owns JSON decoding while pure validation is in `pet/animation/timing.py`. Full-width frames and visible ground anchors preserve the wider sleeping pose. `tools/prepare_character_assets.py` retains the selected rebuild inputs and produces binary-alpha runtime PNGs. Runtime metadata retains historical source durations while each regular clip uses one constant frame hold, independently configurable in `assets/animation_timing.json` and validated when loaded. Walking currently uses 190 ms per frame (1.52 seconds per cycle); the idle blink is event-like with a 3–8-second rest interval and a one-source-pixel pose-relative head sway. Attack is cataloged but has no trigger. See [asset licensing](../ASSETS.md).

Hardware implementation details live in `infrastructure/hardware/`. `telemetry.ComputerSnapshot` is immutable and shared by the provider and application layers. The sampler uses local OS APIs and optional bounded NVIDIA tooling.

## Persistence, configuration and privacy

`infrastructure/persistence.py — StateStore` is the only implementation of the version-one atomic local JSON repository. The default Windows file is `%LOCALAPPDATA%\AikoDesktopPet\state.json`. The sole optional environment override, `AIKO_SAVE_PATH`, selects another **file path**. No `.env` is required.

`infrastructure/pet_codec.py` owns pet/nutrition JSON translation: field names,
legacy defaults, malformed-value handling and four-decimal save rounding.
`PetState` and `FoodState` contain gameplay values and transitions, with no
`from_dict`/`to_dict` methods. Existing saves retain their version-one shape.

- Storage decodes/writes data but does not simulate elapsed pet time.
  - The application reconstructs full closed time after decoding. A shared
    `ActiveSessionClock` consumes each interval once across ticks, care, settings
    and saving. Life time uses suspend-inclusive `GetTickCount64` on Windows
    and `CLOCK_BOOTTIME` on Linux, with wall-time fallback on missing reads.
    Existing active uptime remains separate for observation/physics. A streaming
    domain plan handles long gaps without truncating them or generating meals.
    Optional `pet.time` persists the aggregate's elapsed axis; checkpoints and
    joint atomic saves include it. See [time and migration](DATA_AND_SAVES.md).
- Tests use temporary save files, never the user's production save.
- No cloud, login, browser integration, microphone listener or network service is started.

See [privacy and installation](../README.md#privacy-and-local-data) and [integration design](INTEGRATION_ARCHITECTURE.md) for future, explicitly unimplemented extension points.

## Import migration

The care/storage follow-up also changes these Python call contracts:

| Previous call | Current owner/contract |
| --- | --- |
| `PetMind.emotion()`, dialogue `mood`/merged `states` | `PetMind.emotional_state()` and typed `DialogueContext.emotions`, `mood_value`, `need_conditions`, `reaction_tone`, `situational_conditions` |
| `PetMind.after_care()`, `irritated_until`, `warm_until` | `record_accepted_care()`, `irritation_reaction_until`, `warm_reaction_until`; lasting impressions remain separate |
| `DialogueBook.choose(event, emotion, time, now, dialogue=...)` | `choose(event, context, now, presentation=...)` with a single immutable `DialogueContext` |
| `MoodHint`, `MoodHintState`, `choose_mood_hint()`, `PetState.mood_hint()` | `StatusHint`, `StatusHintValues`, `choose_status_hint()`, `PetState.status_hint()` |
| `format_mood_hint()`, `mood_hint_text()`, text keys `mood.*` | `format_status_hint()`, `status_hint_text()`, `status_hint.*`; German wording unchanged |
| Seven-entry `PetReadSnapshot.needs` | Five-field immutable `NeedLevels`; numeric mood and friendship remain separate snapshot fields |
| UI `needs`/`need_value()`, toolbar `NEEDS`/`needs` | Presentation `status_values`/`status_value()`, toolbar `READOUTS`/`readouts`; seven displayed bars remain unchanged |
| `pet.need_decay`, `NeedProgress`, `calculate_need_decay()` | `pet.progression`, `PetProgress`, `calculate_pet_progression()`; five `NeedLevels` fields live in `pet.needs` |
| `MoodFactors`, need-only `calculate_mood_target()` | `NeedMoodFactors`, `calculate_need_mood_target()`; composed Moodlet targets use the shared progression owner |
| Hover `feed` callback / Snack button `feed` action | `place_item` callback/action with independent `can_place_item`; direct domain feeding remains `feed` |
| `HoverUi.interaction_active`, walk/assembly `toolbar_visible`, attention-runtime `toolbar_active` | `menu_engaged`; actual visibility remains distinct in session UI refresh |
| World `controls_active` | `character_action_busy`, sampled from actual character playback/waiting without menu hover |
| `PetState.interact()` returning German text | Returns `pet.care_result.CareResult`; UI uses `format_care_response` |
| `PetState.from_dict` / `to_dict` | `infrastructure.pet_codec.decode_pet_state` / `encode_pet_state` |
| `FoodState.from_dict` / `to_dict` | `infrastructure.pet_codec.decode_food_state` / `encode_food_state` |
| `CareRuntime`, router `runtime=` | `SessionInputs`, router `inputs=` |
| `application.controller.CareInputs`, `ActivityCoordinator.care_inputs()` | `application.active_time.SessionInputs`, `ActivityCoordinator.session_inputs()` |
| `StateStore.load()` / `load_memory()` | One `load_session()` snapshot: `.state`, `.settings`, `.adaptive_memory` |
| `asset_paths.ASSETS`, `EMOTE_ASSETS`, `SCI_FI_UI` | `SPRITE_FRAME_DIR`, `EMOTE_IMAGE_DIR`, `KENNEY_UI_DIR` |
| `pet.value_rules.bounded` | `pet.value_rules.clamp_need_value` |
| `ActionPlayback.state`, animation port `action_state` | `clip_id`, `action_clip_id` |
| `PetMind.computer_event()` / `spontaneous_event()` | `select_computer_reaction()` / `select_spontaneous_reaction()`; both return a selected reaction |
| `ActivityCoordinator.interrupt_nap()` | `should_interrupt_nap()`; a condition query without mutation |
| `pet.mind.mind.AikoMind` | `pet.mind.PetMind` |

The desktop entrypoints and on-disk save format remain compatible. Repository
callers use these canonical owners directly; no reverse domain-to-storage import
or compatibility registry is needed.

The 2026-10-13 repository usage review found no runtime consumers of the 25
flat-module forwarding files or the five old application view modules.
Their imports were confined to tests and forwarding modules. `DesktopPet`
inherited `DesktopCompatibility`, but its live code already accessed the
owning components directly. `presentation/legacy.py` only supported the old
view modules and their tests. These 32 files have been removed, and the
behavior tests now exercise their canonical owners directly.

The source launchers (`main.py`, `Aiko_Pet.pyw`, `python -m aiko_pet` and both
Windows batch files) use `aiko_pet.gui.main` and require no import migration.
Version-one JSON saves, save-path configuration, sprites and authored dialogue
are unchanged. The repository review cannot establish whether unknown external
Python code imports the removed paths; such callers need the mappings below.

| Removed path under `aiko_pet` | Canonical owner |
| --- | --- |
| `domain` | `pet.state.PetState`; care/friendship/time constants and functions in their respective `pet` policy modules |
| `care_actions`, `friendship`, `routine`, `value_rules` | Modules of the same name under `pet` |
| `pet_lifecycle` | `pet.lifecycle` |
| `adaptive`, `adaptive_models`, `adaptive_policy`, `work_episode`, `reaction_sequence` | Modules of the same name under `pet.mind` |
| `dialogue` | `pet.mind.mind.PetMind` and `pet.mind.catalog` types |
| `dialogue_catalog`, `dialogue_events` | `pet.mind.catalog`, `pet.mind.click_policy` |
| `computer_voice`; `ComputerVoice` alias | `pet.mind.workload_events.WorkloadEventDetector` |
| `animation`, `gaze`, `movement`, `reaction_playback` | `pet.animation`, `pet.movement`, `ui.pet_view.reaction_player` |
| `desktop_input` | `desktop.global_input` |
| `taskbar` | `desktop.taskbar` and `desktop.geometry.TaskbarTrack` |
| `window_stack` | `desktop.window_stack` |
| `storage` | `infrastructure.persistence.StateStore`; settings in `application.settings` |
| `system_activity` | Providers in `infrastructure.hardware`; shared snapshots/effort in `telemetry` |
| `application.view_models` | `ui.view_models.contracts` |
| `application.hover_projection`, `status_projection`, `settings_projection` | `ui.view_models.projections` |
| `application.read_models`; `presentation.legacy.DesktopViewSource` | `ui.view_models.read_models.DesktopPresentation` |
| `desktop.compatibility.DesktopCompatibility` | Owning `DesktopPet` components; no replacement facade |

Hover/status projectors accept `application.read_snapshot.snapshot_pet(state)`
instead of a mutable `PetState`. The status projector reads the composition
from that snapshot, without a second emotion argument. `DesktopPresentation`
provides desktop views without exposing the old public component handles.

Legacy desktop accesses such as `pet.toolbar`, `pet._bubble`, `pet.say()` and
`pet._walk_remaining` have been retired. Desktop composition and integration
tests use `pet._hover`, `pet._speech` and `pet._animated` respectively. These
are implementation components, not a new public integration API. Future
external adapters should use the typed application boundary.

Unused widget, asset and policy re-exports from `gui.py` have also been
removed; import them from their canonical `pet`, `ui`, `infrastructure`,
`asset_paths` or `desktop` modules.
The application uses `workload_events`, not the old `computer_voice` attribute.
Existing domain convenience methods and version-one data decoding remain
outside this module-import cleanup.

The `tests/test_canonical_import_paths.py` audit forbids references to
removed `personality/`, `presentation/` and root-level UI module paths in
production code, tools and tests. `tests/test_canonical_owner_identity.py`
checks implementation ownership without reviving obsolete compatibility tests.
`tests/test_dependency_graph.py` centrally checks layer boundaries and cycles,
including absolute, relative and from-package submodule imports. Former
duplicate layer/identity checks have been folded into these shared audits;
functional GUI, asset and domain tests remain in their owning suites.
Adaptive models/policies, telemetry, geometry and UI snapshots are imported
directly from their defining modules instead of historical re-exports.
There are no surviving import-forwarding packages for these historical paths.
The redundant module-level mutating adapters `apply_care_action`,
`apply_need_decay`, `award_friendship_for_care`, `advance_pet_time` and
`apply_daily_routine` have been retired. `PetState` alone applies their
associated pure transition decisions. Legacy-only migration tests were
updated to exercise immutable policies and the actual aggregate owner.


## Rhythm and dialogue

`pet/mind/adaptive.py` and its pure policies combine needs, local time,
new hardware observations and user-idle evidence into measured work/rest
behavior. Missing sensors stay unknown; uptime never acts as an exhaustion
multiplier. Learned summaries use a local weekday/hour profile, not process
names, typed text or browser content. Observation and learning can be disabled
independently, and learned rhythm can be cleared without resetting pet progress.
Life time includes standby and reconstructed closed wall time; observed activity
does not extend across those unknown gaps. See [data and saves](DATA_AND_SAVES.md).

`pet/mind/catalog.py` validates and selects authored German lines from
`data/dialogues.de.json`. `infrastructure/character_mind.py` supplies Aiko's
catalog at composition time. Event, mood and context filters, weighted choice
and cooldowns belong to the mind policies; the UI only presents their decisions.
Aiko is reserved, observant, curious and quietly sarcastic. She can express
warmth directly without retracting it. Friendship changes the familiarity of
her wording; current needs, irritation and measured work still matter. Avoid
invented knowledge about the user's applications, speech or work. No runtime
LLM is involved.

`DialogueContext` freezes the display-level relationship stage, primary mood,
simultaneous need flags, time and observed situation. The four stages cover
levels 1–2, 3–5, 6–8 and 9–10. Care captures the whole context before applying
its effects, including before a friendship level boundary is crossed.
Relationship filters never relax during rotation or fallback. Specific need
and mood variants take priority over suitable general wording.

Catalogue version 3 retains ordered text, emote and pause beats. Its explicit
`conditions` are alternative AND clauses: typed emotional states/directions,
need conditions, short reaction tones, situation and sleep remain separate.
The old `moods`/`needs` filters and mixed `EMOTIONS` vocabulary are retired. `Reaction` carries
that immutable sequence and a short/story presentation mode. The UI only plays
it: one speech surface, length-based reading time (58 ms/character, 1.8–8 s),
800 ms default emotes and 600 ms deliberate pauses. There are 48 authored talk
stories, twelve per relationship stage, with independent emotional, need,
short-reaction and situational variants.
Stories exhaust their matching rotation pool before repeating. Warm moments
also admit suitable calm stories, keeping repeated contact varied after care.

An intentional talk normally runs three to five text bubbles. Left-clicking
Aiko during a story advances to the next text, skipping intermediate emotes
and pauses. Clicking the last text ends it. These reading clicks do not enter
the teasing counter or apply care rewards; normal clicks start a fresh burst.
Other deliberate interactions can interrupt. Automatic speech, gaze remarks,
idle effects and object-goal acquisition respect active playback, including
blank pauses. Spontaneous stories require observed presence, a 20% draw among
eligible quiet moments and at least ten minutes since the previous one. Those
values come from `dialogue.spontaneous_story_probability` and
`dialogue.spontaneous_story_quiet_seconds` in the validated balance catalogue.

Playback completion and cancellation are reported once; stale timers cannot
advance or complete a newer sequence. Object-phase feedback retains its
receipt-driven interaction ownership. The RPS countdown/reveal timeline also
retains its owner; greeting/outcome wording is selected through the same mind
and relationship context, with outcome perspective explicitly mapped. Standalone
games use an instance-owned `GameDialogue` from
`ui/windows/rock_paper_scissors_dialogue.py`; no mutable game catalogue is created
at import time. Embedded games keep the existing session mind and its history.
Need tuning belongs to the current
[food](FOOD_SYSTEM.md) and [fun/mood](FUN_MOOD_SYSTEM.md) guides.

## Historical architecture refactor (October 15, 2026)

PR #9 established canonical package ownership and is merged. Its
[delivery record](history/PET_ARCHITECTURE_REFACTOR.md) and
[old Windows checklist](history/PET_REFACTOR_WINDOWS_SMOKE.md) are history;
the maintained World sections below describe the current runtime.

## World, subjective knowledge and object interaction

`world/contracts.py` defines immutable object definitions, logical surface and
position values, footprints and objective snapshots. `world/state.py` owns one
in-memory World with stable instance IDs, revisions and explicit
custody/lifecycle operations. It imports neither pet rules nor desktop/UI code.
`infrastructure/world_catalog.py` builds definitions by referencing the existing
food and item-asset IDs; it does not copy nutrition, labels or sprite data.

`pet/mind/object_perception.py`, `object_knowledge.py`, `object_memory.py` and
`object_intentions.py` separate timed identification, learned facts and stable
need-based goals. Knowledge distinguishes identity, assessment and
confirmed own deferral; observed relocation preserves learning. Recognized facts
persist across restart; checked absence marks a place missing rather than erasing
all its learned history. Only unknown sightings expire.
An unknown ground or moving portion can be noticed but cannot be identified.
First identification requires explicit actual hand-inspection context after
safe pickup, or a continuous player presentation before the face. `recognized`
means identified; the independent historical `assessed` fact is not a lasting wish.
Presentation clocks/evidence are transient sensory state, never saved knowledge.
`application/object_awareness.py` is the objective-to-subjective boundary.
`choose_object_attention` in the existing application coordinator derives one
immutable `ObjectAttention` from action phase, actual movement, cursor attention,
current subject and ongoing activity read from existing playback/speech owners.
Item commitment takes precedence over walking; the other activity owners retain
attention through animation and full speech completion, without another timer.
`DesktopVisualObservation` supplies eye coordinates and
body width, projects that decision into the gaze atlas, and the World adapter
translates the same value into World coordinates before sensing. Normal visibility
is the one-body-width near field plus the forward half-plane up to six body widths.
Every committed item phase excludes ambient evidence, including approach. Its
ground-place window checks only the selected execution subject, not neighbours.
Other active interactions and sleep/game states also exclude ambient evidence;
own held/placed custody stays continuous. A lost execution association releases
the action without inventing learned absence. See the
[attention contract](WORLD_OBJECT_CONTRACTS.md#attention-noticing-and-identification).
Ordinary positive candidates use this local field. Deliberate left/right
orientation additionally covers learned places across the taskbar without remote
unknown discovery;
`ObjectPerception` only accumulates notice, inspection and presentation dwell for
qualified inputs. A cursor take also requires the current attention, sampled before
resetting the old gaze. A witnessed cursor lock can follow that one portion beyond
the ambient range; attention loss ends the lock without erasing learned knowledge.
Unseen moves do not update memory. The existing tick observes objects after
need progression and before presentation. Faster physics/render callbacks do
not run a second mind loop. Object gaze reuses sixteen directions and does not
set the user-attention flag that would block walking toward the goal.
`application/object_tracking.py` associates only current spatial sightings and
maps them to execution handles. Subjective memory IDs are independent of World
IDs. `object_stock.py` supplies one-to-one matching/count uncertainty; the memory
owner retires explained checked places and keeps ambiguous consumption witnesses
unavailable until evidence resolves them. No parallel inventory is maintained.

For an actually identified portion, `ObjectMemory` additionally owns an acquired
physical reference (`instance_id`) alongside identity and the last observed
place. Only completed hand/face identification acquires this reference; unknown
ground sightings never borrow a learned type by proximity. The awareness bridge
passes references only after normal attention/range/notice gates. At the exact
remembered place, learned identity/assessment can then restore the same record
after restart or a focused tracking gap, even for close same-type portions.
An unseen relocation requires a new permitted identification; it cannot silently
refresh the remembered place. Observed custody/motion retain their existing
continuity. A verified reunion preserves the current episode record while the
memory owner reconciles earlier learning. This supersedes position-only reunion
as proof of a known portion; unknown tracking remains geometric. Acquired
references at exactly remembered places may anchor known tracks through a
geometric tie, so coincident known portions can complete normal notice dwell.
Actual sensory gaps still reset tracks, and unknown ties gain no identity.

The interaction's `focus_record` commits the current action to one subject.
Unrelated tracking, recognition and absence sensing are excluded during that
commitment; a witnessed track of the selected subject may continue.
A successful observed take can lock the existing visible track to the
cursor-rendered portion through hand motion and settling. Absence or a sensory
gap discards that lock; a World handle cannot recover it. Recognition during
focus cannot merge its record into an
unobserved neighbouring portion. Other goals wait for the committed action or
the shared search task to release them.
Ordinary observed pickup also retains this track without an action focus. Its
witnessed take immediately records non-resting custody in ObjectMemory, so a
complete take/drop between perception ticks does not become a phantom loss. A
newly noticed cursor portion can be tracked while its identity is learned. Rest
releases the cursor lock. Current visibility, learned identity and completed
presentation jointly permit offer assessment. A new gesture requires presentation
even for known items; it never requires repeating learned identification.
`CursorItemGesture.presentation()` derives the displayed item's center, including
its sprite pivot, from the existing eye reference. The pure perception policy
validates face bounds, holding time and jitter in character-relative units.
Completed presentation survives an observed face-to-handover move in that gesture.
The sole `ObjectIntentions.goal` can hold a session-local wish while the player
holds a portion. `ObjectUseContext` separates seeking, offered use and continued
wishes from actual care origin. An observed drop preserves the wish but starts
no acquisition until ground contact; it is not a withholding episode.

`pet/movement/controller.py` shares the existing walking executor between random
and deliberate goals; `auto_walk` gates only random departures. `WalkDriver`
still reports actual clamped desktop displacement, with no second pet position.
Its read-only committed-goal port suppresses incidental cursor/toolbar blockers
only for the active object episode. Sleep, energy and work blockers retain their
existing rules; random walking retains ordinary hover/cursor behavior.

`application/object_interaction.py` owns explicit notice, approach, pickup,
held inspection, recognition, decision, consumption and put-down phases. The
mind distinguishes investigate from consume, so a new noticed item can prompt
investigation without current appetite. Subjective assessed knowledge prevents
repeated handling; later needs can activate known deferred portions.

`application/object_interaction_state.py` holds the coordinator's private
`InteractionEpisode`: subject/custody references, care origin/use context,
learned identity, queued interruption, withholding and effect history. Takes and
observed returns retain the episode; a fresh attempt creates a new record, and
completion releases it before cancelling feedback. Record/instance identifiers
remain readable properties. Typed phase variants now own arrival, playback,
inspection time, use decisions and cue/aside prerequisites. Waiting and
offer phases share their current appraisal while each transition gets fresh
feedback; a new approach requires fresh arrival. The coordinator owns phase
transitions and session counters/contact cooldown. The same coordinator owns one
session-local SearchTask, which encapsulates missing subjects, route coverage and
unreachable candidates. Its `add`, `resolve`, `exclude_candidate` and `destination`
operations preserve the task's invariants; callers receive immutable subjects
and read-only progress/completion queries rather than mutable task collections.
The task has no World reads, UI callbacks or movement execution. It survives
candidate action episodes and gathers further confirmed losses. SearchPhase is
only the current patrol action; generic CuePhase carries absence and reunion
speech. `search_progress` describes endpoint coverage, including during inspection,
and is zero outside a task. See
the [search contract](WORLD_OBJECT_CONTRACTS.md#one-search-task-explicit-action-phases).

The coordinator preserves that consume purpose: known assessed stock uses recall,
pickup and full consumption without repeating inspection/recognition/desire cues.
The pure postpickup type-consistency guard in `object_awareness.py` can request
actual hand inspection when a local type hypothesis contradicts the acquired
portion. Supported saved knowledge can contradict the paired World definition:
the memory codec validates history without rewriting it from objective truth.
The guard therefore remains a required boundary, backed by a restored-conflict
test. It never writes World definition identity to subjective memory; the
interaction coordinator receives only the guard's boolean result.
Changed needs safely lead to refusal/put-down; conflicting evidence restores
inquiry. Identified loss starts a complete taskbar search with existing gaze/walk
assets. SearchTask owns route advancement; the coordinator owns task lifetime,
phase transitions and search/find/missing feedback. Desktop adapters still
execute movement and report actual position.
Unknown reachable resting candidates use ordinary pickup/inspection/put-down
before resuming this route. Hand/face verification, or permitted exact-place
recall, updates memory; verified remembered findings resolve their own missing
subjects even if response was delayed by another action. A different learned
portion of the same type cannot substitute a bound subject. Captured subjects
survive old-record reconciliation. The coordinator's `found(record)` patrol
entry reads canonical memory; hand inspection and face presentation share
`_announce_identification`. All use `_reunite` for one task resolution and result
cue, without creating an ObjectGoal just to announce a finding. Completing a
readable recognition cue separately invokes `_complete_recognition`, which
rechecks current facts and previously confirmed losses whose reaction was deferred
until that cue. This is not ambient perception during hand inspection.
A nonmatching find is safely placed, or released from the episode with player custody intact,
before the task continues; ordinary use retains its decision/consumption path.
`object_absence.py` owns local negative sensory evidence: covered remembered
places, continuous attention/dwell and raw occupants, including unnoticed ones.
The awareness bridge resolves current custody first, then marks confirmed absent
portions missing and retains unacknowledged sensory facts until the coordinator
can handle them. A different occupant, including an unidentified replacement,
does not conceal a learned loss. The same learned portion must still occupy its
exact remembered place; that check never identifies a replacement or reveals a
hidden new location. Unknown places retain their local presence evidence.
All confirmed losses receive their own completed bubble before the next search
candidate is approached. Free walking and search patrol observe
their forward field; item commitment and other interactions exclude unrelated
sightings, empty-place evidence and transport, including during focused approach.
After focus release, learned-place orientation and its sensory evidence start
fresh. Its left/right coverage spans the taskbar. While it is pending,
the existing look stays fixed and free goals/offers wait, including a continuing
consumption wish. All confirmed learned losses join the same task before a new
free investigation; evidence still requires the admitted look and continuous dwell. During search,
`advance_search` selects investigations and free appetite does not steer the look.
`notice_absence` announces `object_place_missing` before ordinary new discovery.
An unknown confirmed loss is acknowledged and forgotten without patrol. An
identified loss starts a complete route regardless of appetite, from the nearer
reachable end to the opposite end. Actual position observations advance coverage;
elapsed time does not. Only an exhausted route, no pending local evidence and no
eligible unexamined candidates allow `object_missing`. More losses join the same
task; resolving one does not restart the pass for the others. Cursor gestures and
soft motion blocking retain the task; explicit interruption cancels safely.
Losing a spatial association alone does not mark a ground place missing or start
a patrol. A new unknown find at an already
confirmed missing place cannot inherit the old identity from location alone.
Known but unassessed acquisitions decide without repeating identification;
unknown or conflicting evidence retains inspection. Known handover uses authored
acceptance, while expressed-wish collection has its own cue. Shared offer copy
names the item and does not claim a food need when offering a drink.
Observed player acquisition before the grasp commits enters `await_return`;
visible falling/bouncing enters `await_settle`. Settling resumes the same
interaction with acquired assessments. Actual visual loss retires an unknown
target or searches for a learned one. An accepted return into Aiko's hand retains
the interaction but
uses actual human-handover origin; ground retrieval stays autonomous.
An observed held target can be identified and reappraised during that wait,
after deliberate face presentation. Own-hand inspection similarly waits for
confirmed identification before announcing its result.
`recognize_offer` and `decide_offer` retain player custody and identified reading
receipts; they are distinct from pet-held inspection/use. Agreement resumes the
waiting/settling path, while refusal completes the episode without acquisition
or further withholding escalation. Current assessments can update pending cues.
Identified animation events acquire at source frame 4, finish pickup at pose 8
and release during reverse frame 4→3. The animator changes no needs.
`application/object_feedback.py` correlates phase cues and completion receipts.
Mind/catalogue supplies authored reactions; `ObjectFeedbackPresenter` formats
known names and uses `ReactionPlayer`'s completion/cancellation acknowledgements.
Transitions wait for readable cues and required animation/dwell. Auxiliary cue
IDs cannot acknowledge phases. One pending aside waits for the phase bubble,
using the existing speech surface and timers. Ordinary clicks request a bounded
wait acknowledgement, without normal click/care effects. Contact asides describe
the ongoing action and do not block movement or phase progression. A required
loss/find/identification cue supersedes a contact aside and retains its reading
receipt; stale aside receipts cannot release it. Search has its own contextual
busy reply. The attention adapter reads this exception from the same live phase
feedback, rather than treating that optional reply as a new foreground activity.

Passive hover opens accessory UI without pausing a committed object episode or
producing an extra pet reaction. ContactCoordinator derives one read-only user
action permission from the current World, game, sleep and playback owners. That
permission controls care button states and their UI callbacks, including stale
food menus. Pin/settings/details remain
independent. Explicit lower-level care/game commands retain safe interruption;
UI actions cannot start a competing activity. See the
[hover and availability contract](WORLD_OBJECT_CONTRACTS.md#hover-controls-and-busy-replies).
Ambient feedback cannot replace action speech.

`pet/mind/object_withholding.py` calculates immutable active-time episode decisions.
The interaction owns the episode and only evaluates currently observed user-held
custody. `application/object_relationship.py` deduplicates social effects;
`PetState` applies shared durable rolling penalty caps through the pure
friendship policy. `PetMind` owns temporary irritation and the warning within
its existing click burst; the contact coordinator admits later annoyance
without counting story-reading or blocked input. Loss preserves reward history
and creates no return bonus. Episode/request/cursor state stays session-local;
`pet.relationship` v1 saves contact, credit, neglect and penalty histories on
`lived_seconds`, inside the existing outer save v1. See the
[current friendship rules](FRIENDSHIP_SYSTEM.md).
`application/object_custody.py` commits confirmed acquisition and placement in
World and memory together, restoring both owners on failure. The interaction
coordinator retains animation deduplication, cue receipts and phase ordering.
`application/object_consumption.py` uses `ObjectConsumption.commit()` to apply
canonical food/drink effects at consumption start with explicit handover/autonomous
origin. It captures pre-care Mind context without modifying social contact,
then prepares the canonical pet effect through PetState-owned immutable checkpoints.
It commits World, PetState and ObjectMemory together on the owner thread,
restoring the same pet object on failure and recording human contact only
after a successful commit. Completed requests remain deduplicated. World `consume()`
alone still cannot feed Aiko. Human-only care rewards are excluded for ground
consumption, while canonical nutrition, repetition and food mood effects remain.

`application/object_behavior.py` coordinates object attention, checked-absence
priority, shared missing-subject search, waiting for return and approach
start/change using the existing state, awareness, interaction and World owners.
It owns behavioral eligibility, continuing-wish decisions and returning-offer
appraisal. Immutable host facts enter the application; relative gaze and bounded
`Hold`, `Approach` or `SearchMotion` instructions leave it. Normal completion
ports retain cancellation effects without an obsolete search-stop result. Attention is applied before cursor offer observation, then motion is
decided against the resulting episode. Completed local target evidence separates
an ambiguous association from pending notice or an empty place; unknown actions
cannot retain orphaned memories. Search candidates use ordinary investigation;
unrelated consumption waits. Soft motion blocking pauses the task; explicit
interruption ends it safely. Matching reunion waits through its receipt before
ordinary approach, while return waiting holds for its original tick. It stores no
duplicate wish, memory, episode or clock. See the
[shared search contract](WORLD_OBJECT_CONTRACTS.md#one-search-task-explicit-action-phases).

`desktop/world_runtime.py` composes the owners, samples host/sensory facts and
translates application instructions into native movement/gaze. It retains actual
arrival, taskbar reach, scale bounds and source-frame reach revalidation; contact
capture precedes arrival acknowledgement. It contains no phase-name behavior
branching. The mind tick and separate motion/render timer remain unchanged.
The typed `desktop/world_access.py` binds to this one World runtime after
composition, replacing implicit `hasattr` guards without duplicating state.
`desktop/cursor_item_gesture.py` owns one input gesture: cursor
instance handle, native capture, pointer geometry, offer-preview IDs and release
or cancellation. Named ports keep appetite/feedback and custody decisions with
the existing application owners. There are no shadow cursor fields or retired
forwarding properties in the runtime. `ui/world_view.py` renders snapshots in small
native windows; resting items accept visible-pixel presses, while moving/carried
items remain click-through and all item windows remain nonactivating.
`FoodOverlay` draws consumables above the character
without additional hand masks. Calibrated eating anchors come from reproducible
asset preparation. Assessed deferred portions preserve memory but release
incidental object gaze; only unassessed observations or active goals attract it.
`TaskbarTrack` derives a reachable ground inset from ordinary standing bounds
and reach. `WorldSurface.ground_interval()` intersects it with each footprint;
every placement/recovery route uses this rule. There is no special edge grip.
`ground_approach()` and `can_grasp_ground()` retain actual arrival/reach checks,
including frame-4 revalidation and ordinary ground-to-hand blending.
`world/motion.py` calculates analytic flights, exact contacts, damped rebounds
and continuous low-energy inward completion. Immutable motion belongs to World
snapshots; `WorldState.advance_motion()` alone commits it. Parameters come from
validated balance JSON through `infrastructure/world_motion.py`. Geometry is
synchronized before frames, gestures and save snapshots; scaling does not reset
velocity or multiply World coordinates. Only final settlement grants rest.
Chooser press creates one portion. Deliberate face presentation may identify
and assess it before handover; a current refusal prevents accepted transfer.
Alternatively, Aiko may accept a still-unknown portion on release in the
valid handover area and actually identify it in her hands before deciding.
A known approved handover takes the shorter confirmation route. Unknown ground
finds retain inspection/decision. Resting-item press acquires the same portion
through the same gesture. Escape/capture loss or off-monitor release removes new
chooser portions and returns existing portions to their safe source place.
Delayed gesture requests recheck the button after animated interruption.
Existing native toolbar/game rules remain in their owners.
All three item presentations use manifest-referenced binary-alpha display copies
prepared reproducibly from unchanged native 1x/2x originals for Windows color-key
transparency; no runtime Pillow or replacement artwork is introduced.

`infrastructure/world_codec.py` adds an optional separately versioned World
section inside outer save v1. Pet, World, settings and adaptive data use one
atomic StateStore write. `object_memory_codec.py` writes optional version-three
subjective records, acquired physical references, assessment, place status/
associations and relative active ages. It validates reference uniqueness and
allocation provenance. Its v1/v2 readers retain legacy history without inventing
acquired references or live bindings.
`WorldSessionSnapshot` captures World
and memory together for that write. Old saves without memory grant no knowledge;
transient nonconsumed items recover on valid ground positions without restoring
actions or fabricating observations of recovery positions. Learned facts remain
separate from current observations/evidence, which start empty on restore.
World objects are never consumed during existing pet-only closed-time catch-up.

The [maintained World contract](WORLD_OBJECT_CONTRACTS.md) defines behavior;
the [isolated smoke guide](WORLD_SMOKE_TEST.md) records reported desktop
acceptance and repeatable checks. Implementation iterations and superseded
contracts are kept in [delivery history](history/README.md).

## Testing and contribution

GitHub Actions checks:

- Full Python 3.11 and 3.13 unit/Tk suites under Linux/Xvfb.
- Windows-hosted headless checks for native boundary logic.
- Ruff E/F/I/N/W checks across code, tests and tools: PEP 8 whitespace,
  88-character lines, import order and identifier naming; strict Mypy and Pyright.
- Domain invariants, immutable read data, import boundaries without legacy exceptions, and absence of module import cycles.

Native Windows layering, transparent-window and taskbar behavior must also be tested interactively for relevant changes. The October 2026 OOP refactor passed its full automated checks and received maintainer-reported Windows acceptance before [PR #2](https://github.com/Lexoniarus/aiko-desktop-pet/pull/2) merged.

For local commands, source changes and review expectations see
[CONTRIBUTING.md](../CONTRIBUTING.md). The [documentation index](README.md)
records current local evidence and acceptance; [CHANGELOG](../CHANGELOG.md)
summarizes unreleased changes and verified milestones. Prior refactor plans and
review ledgers are [historical records](history/README.md), not active blockers.


## VN presentation delivery (5C)

`ui/common/icon_images.py` is the one root-local image owner. The development-only
`tools/export_vn_ui.py` normalizes the 46 approved masters and exports shared
nine-slice button/control sizes from eight source surfaces into `assets/ui`.
Their runtime catalogue records source hashes. Tk alone loads/composes the
exports; runtime remains standard-library-only. `image_button.py` preserves
native invocation and adds disabled/hover/press/active artwork, independent
keyboard focus and explicit destruction cleanup. `scroll_region.py` owns local
scroll bindings and focus reveal; `description_tip.py` renders in-window passive
details. These are UI behaviors, not new domain or input-capture authorities.

Numeric target mood, current value, relationship stage, actual sleep reason and
known contact age flow through `PetReadSnapshot` and existing pure projections.
No clock or elapsed progression runs on a read. The same emotional composition
now colors click/dialogue/idle expression. Normal positive stories/idle stars
are reachable from good care at mood 70; the longer playful click sequence
retains 82 and its previous escalation policy. Negative/ambivalent compositions
do not produce contradictory positive expression. Observed work may still
select work dialogue; hardware strain alone no longer claims sleepy clicks.
All authored German dialogue sequences remain unchanged.
