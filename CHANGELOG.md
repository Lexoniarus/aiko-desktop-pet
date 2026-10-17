## Unreleased — World pickup, missing-place search and reunion correction

- Separate handover acceptance from prior type identification and consumption:
  accept a currently eligible unidentified cursor item on valid release, then
  inspect in Aiko's hands. Keep preidentified explicit refusals effective.
- Give confirmed absent remembered places priority over discovering unknown
  portions, then initiate one bounded search independent of current appetite.
  Use exactly the ordinary item-noticing range for absent-place detection.
- Reconcile unique missing same-type finds as remembered supplies in either
  observation order, without copying type/assessment to ambiguous or conflicting
  portions. Recheck actual hand-held type before skipping known-stock inspection.
- Prevent premature search while normal notice or native final reach is still
  pending; recover from truly unavailable approach targets instead of looping.
- Add domain, ownership and native/Tk regression tests. Manual native World
  acceptance and merging draft PR #10 remain open.

## Unreleased — PetState encapsulation

- Complete OOP stage 7: keep one frozen PetValues inside the mutable pet
  aggregate, expose scalars as read-only properties and detach collection reads.
- Preserve named construction, save v1, deepcopy, equality and canonical
  nutrition/friendship transitions without adding public setters or new gameplay.
- Migrate GUI/walk/animation read protocols, isolated smoke setup, media
  captures and tests to existing domain commands/checkpoints. Add regression
  coverage for rejected outside writes and isolated history copies.
- Complete Linux 3.11/3.13 and Windows CI; manual practical World acceptance
  and merging PR #10 remain separate and open.

## Unreleased — Read-only pet policies and checkpoints

- Convert need, care, routine and friendship policy inputs to read-only
  properties and Sequence/Mapping histories without changing game decisions.
- Introduce complete immutable PetValues checkpoints, prepare consumption in the
  pet domain and restore the same live pet identity across joint World/memory
  rollback; retain the existing compatibility method until stage 7.
- Give session restoration an explicit time-anchor operation and test unchanged
  care origins, independent histories, save values and rejected preparations.
  Stage 7 and manual native World acceptance remain open.

## Unreleased — Notice, identification and assessment

- Separate noticed presence, learned type and current willingness. Unknown floor
  and moving items identify only during Aiko's actual post-pickup inspection.
- Require a deliberate one-second face presentation for cursor offers, including
  known items. Retain acquired identity and completed presentation through observed
  movement into the handover area; preserve actual release and care-origin rules.
- Notice covered empty remembered places before new discoveries/offers, with
  local dwell and pending-occupant protection. Use separate early-loss feedback
  and one bounded search only for current targets or needed reserves.
- Prevent unknown finds at confirmed missing places from inheriting old identity;
  preserve subjective stock reconciliation, observed continuity and save formats.

## Unreleased — Observed item continuity

- Preserve learned identity across ordinary observed floor/cursor/placement
  movement, independently of an existing investigation or current desire.
- Let recognition and desire develop during holding; retain the expressed wish
  after observed placement, with capacity checks and actual care origin.
- Skip repeated identification for known items, including known but unassessed
  restart cases. Keep unknown-item inspection and full consumption playback.
- Distinguish ordinary holding from withholding a committed target, and align
  known acceptance, offer and collection dialogue with the actual knowledge.
- Recognize and reappraise a withheld investigation target while presented at
  the cursor. Express current agreement/refusal; refusal ends return demands
  without acquiring the portion or continuing withholding penalties.

## Unreleased — Committed object attention

- Keep one investigation committed through ordinary hover, clicks and other item
  gestures; exclude distractions before perception and memory updates.
- Follow an observed target take through cursor motion and settling, then resume
  the same interaction with acquired knowledge. Preserve actual handover origin,
  safe explicit interruption and bounded search after genuine visual loss.
- Add spaced return requests, temporary irritation and limited persisted
  friendship loss for repeated/prolonged withholding, without return bonuses.
- Preserve configured dialogue reading times and make timing fixtures portable;
  extend targeted native 1x/2x and isolated restart coverage.

## Unreleased — Offers, placement and subjective search

- Remember recognized cursor assessments and acknowledge accepted handovers
  without repeating inspection, preserving complete consumption and care origin.
- Separate subjective records from technical World identities, reconcile stock
  ambiguity and persist memory v2 with v1 conversion. Search checked empty places
  visibly and briefly; useful finds can end the old search.
- Let players relocate the same resting portion through visible-pixel input.
  Cancel existing portions back to their source; keep moving items click-through.
- Replace the edge-grip exception with shared reachable placement and analytic,
  impact-dependent damped rebounds. Preserve motion across scale changes and
  normalize interrupted motion to valid ground on restart, without new dependencies.
- Consolidate redundant native edge matrices, retain grasp/timing/recovery
  evidence and extend the isolated starter with one/two-portion arrangements.

## Unreleased — Dialogue and ownership review

- Preserve the completed dialogue-v2 catalogue, relationship/compound-need
  selection, authored stories and cancellable beat playback on the World branch.
- Keep story pacing in validated JSON and remove obsolete object event families,
  unused coordinator state and the test-only pickup entry point.
- Give confirmed World/memory custody changes one application service and cursor
  input its own desktop owner; name consumption commits separately from playback.
- Scope standalone game dialogue history per game while embedded games retain
  Aiko's session mind. Use responsibility-named modules without old forwarders.
- Close isolated Tk image owners before destroying fixtures, correct the v2
  placeholder regression and consolidate duplicate/long native World cases.
  Preserve the edge/scale, restart, interruption and readable animation checks.

## Unreleased — World practical-test corrections

- Separate learned object knowledge from current sensory observations. Preserve
  known identity and completed inspection across observed relocation; expire
  only unidentified sightings after ten active minutes. Add typed portable
  memory values and distinguish deliberate reserve placement from interruption.
- Commit consumed portions, needs and subjective memory together; roll back all
  three owners on failure. Record inspection and own placement at confirmed
  events, rather than waiting until the last bubble has completed.
- Persist subjective object knowledge alongside Pet/World in the existing atomic
  version-one save. Restore learned facts and active ages without offline sensing,
  current visibility or automatic reconciliation to hidden World changes.
- Retrieve known, inspected supplies with hunger/energy recall and full
  consumption, skipping redundant inquiry. Keep first investigation and handover
  separate, distinguish confirmed deferral in dialogue, and announce local absence
  once after bounded search rather than repeatedly pursuing a missing portion.
- Cover cold restoration at both edges/scales and full timed remembered-food
  consumption. The isolated test starter accepts `--needs hungry` on its existing
  temporary save to exercise later need without losing World or memory.
- Release character, zoomed/rest-pose and held-item image caches on the Tk thread
  before shutdown, preventing repeated restart tests from leaving image cleanup
  to later background garbage collection.

- Let Aiko approach and grasp ground portions at both screen edges at 1x/2x.
  A shared geometry rule requires actual arrival at the closest legal standing
  pose for the bounded edge grip. Acquire/snap at pickup frame 4; defer by
  putting the same portion down at her feet and remember the new position.
- Add need-independent investigation and subjective examined memory. Aiko
  approaches, picks up, examines and decides; unwanted items are put down for
  later without repeated investigation, and hunger can activate known items.
- Keep the post-consumption supply-seeking pause from delaying the first
  investigation of another ground item; a drink at energy 66 is examined and
  put down for later without waiting 30 seconds.
- Coordinate readable notice, approach, recognition, decision and outcome
  bubbles through existing Mind/dialogue/reaction owners and identified receipts.
- Stage accepted handover through safe holding/inspection before use; preserve
  the full consumption clip through passive cursor entry. Explicit actions still
  put down unconsumed items first, and automatic use records no human contact.
- Derive 22 reproducible binary-alpha display copies for cursor, ground and hand,
  preserving original item RGB/geometry and preventing Magenta alpha blending.
- Calibrate eating anchors for native item sizes so Onigiri overlaps the fingers
  in front of the character. Preserve source artwork, timing and pickup hand
  layers; verify all eight poses at 1x/2x and reproducible preparation.
- Stop drawing additional hand masks over consumables, including held inspection
  and put-down. Deferred recognized portions release object gaze, preserving
  memory and returning attention to normal cursor/ambient behavior until wanted.
- Add real-timer flow/restart regressions and a `curious` isolated profile at
  satiety 76/energy 60. Native practical retest and merge remain pending.

## Unreleased — World interaction test build

- Replace direct feeding UI with one cursor-carried food/drink portion per
  gesture, recognized release-to-accept, fall-on-refusal and taskbar ground items.
- Add timed perception, subjective object memory, stable hunger/energy goals
  and goal walking independent of random-walk settings through one executor.
- Import the approved eight-pose pickup and hand layers reproducibly. Acquire
  at source frame 4, consume after completion, and animate reverse put-down
  before an interrupting user action. Deduplicate identified playback events.
- Reuse canonical food/drink effects with explicit human/autonomous origin;
  ground consumption grants no human social/adaptive/friendship rewards.
- Save Pet and optional versioned World together atomically; load older saves
  and recover transient portions grounded without replaying consumption.
- Add isolated hungry/full test profiles, real Tk integration regressions and
  a restart checklist. Native practical acceptance and merge remain pending.

## Unreleased — Refactor consolidation

- Add a headless in-memory World foundation with immutable snapshots, logical
  geometry, distinct portion IDs, revision-checked custody/lifecycle operations
  and canonical food/asset references. No desktop, perception, UI, nutrition or
  save integration is enabled by this foundation.
- Enforce PEP 8 whitespace/blank lines, 88-character lines, import ordering
  and identifier naming across code, tests and tools with pinned Ruff rules.
  Keep exact Win32 API name exceptions; remove obsolete partial lint steps.
- Name selected mind reactions, nap permission queries, workload detectors
  and their regression suites consistently; retire the unused `AikoMind` alias.
- Compare Windows setup/launcher paths by filesystem identity so 8.3 aliases
  and expanded paths both pass, retaining strict shortcut argument quoting.
- Name current regression suites, classes and cases by their tested feature
  instead of historical release tags; preserve all existing test bodies.
- Validate dialogue weights as integers from 1 to 10, independently of
  normalized mood/activity weights. Retain all shipped balancing values.
- Use `application.active_time.SessionInputs` and one interval-consumption
  function for live ticks, care and completed games. Cancelled games still
  leave elapsed time for the next tick; offline restoration remains separate.
- Retire unused asset aliases, the `bounded` alias and partial save-loading
  wrappers. Import models, geometry and view contracts from their owners.
  Load state, settings and adaptive memory together through `load_session()`.
- Consolidate duplicate layer and ownership tests, covering relative imports
  and package-submodule imports without removing functional regression cases.

## Unreleased — JSON resources, closed time and Windows regression

- Move remaining UI/farewell copy and named balancing parameters into validated
  JSON resources, retaining current values and Python parameter interfaces.
  Use the canonical food display name in the recent-food status line.
- Reject duplicate JSON keys, non-finite numbers, unknown/missing fields,
  misspelled events, invalid text placeholders and inconsistent balance ranges.
- Restore bounded closed-time progression on startup (eight hours by default).
  With automatic routine enabled, simulate sleep and due main meals only for
  that absence; do not invent observed work, human care or friendship rewards.
- Preserve the version-one save format. Back up unreadable/future saves before
  replacement; document location, atomic writes, autosave and time semantics.
- Synchronize the RPS geometry regression with native Tk visibility events;
  retain every pixel-size and image-bounds assertion on Windows and Linux.

## Unreleased — Care and persistence responsibility follow-up

- Return one immutable `CareResult` from pet care. Dialogue and consumption
  visuals use its effect instead of separately testing acceptance thresholds.
- Capture pre-care tone/context and format unchanged German fallback text in
  the UI. Preserve care values, friendship, meals and conversation ordering.
- Move pet/nutrition save decoding and encoding to infrastructure while keeping
  the version-one JSON keys, defaults, bounds and rounding unchanged.
- Name care input data `SessionInputs` and animation identity `clip_id`; update
  repository callers and document the Python contract migration.

## Unreleased — Repository cleanup

- Archive historical food exports, unused Kenney bitmaps/design references and
  superseded design/test reports outside the repository, with SHA-256 records.
- Keep six README media files; remove redundant detail stills and the automatic
  screenshot commit workflow. Manual capture tools produce only retained media.
- Remove the unused application-only Pyright configuration; retain the complete
  application/tools/tests configuration and all active architecture checks.
- Consolidate history here and current rhythm/dialogue guidance in the
  architecture guide. Preserve current refactor acceptance and specialist docs.

## Unreleased — Windows source setup

- Add `requirements.txt` documenting the standard-library-only runtime.
- Add a double-click Windows setup that detects Python/Tkinter, installs
  the official Python runtime including Tcl/Tk directly when missing or incomplete
  (without requiring WinGet), verifies its SHA-256, prepares an isolated `.venv`, checks
  imports and character PNG loading, and creates per-user start shortcuts.
- Prefer the setup environment in normal and diagnostic launchers; document
  setup options, troubleshooting and removal without changing saved progress.
- Test an actual Tk window before accepting a runtime. Automatically back up
  broken local environments and rebuild them; reject Windows older than 10.

## Unreleased — Remove duplicate German copy and food-asset metadata

- Move emotion labels into the existing versioned German text JSON. Hover
  and status now share the same sleep and observation-disabled labels.
- Keep food titles and ordered nutrition records only in the food JSON;
  remove repeated food titles from the PNG manifest.
- The food picker uses the exact validated icon paths from the shared
  `ItemCatalog`, not a second hardcoded path convention.
- Keep all visible German text, hand sprites, care amounts, and save keys
  unchanged, with expanded regression tests.

## Unreleased — Pet domain/UI architecture consolidation (draft PR #9)

- Canonical `pet/mind/`, `pet/animation/`, `pet/movement/`,
  `ui/pet_view/`, `ui/windows/`, `ui/common/` and
  `ui/view_models/` ownership; historical import-forwarding modules removed.
- Headless pet animation priorities and desktop-only gaze, movement and
  animation decisions feed the Tk sprite through typed ports. All original
  image clips, 16 gaze directions, timings and interaction precedence stay.
- Bounded application and animation assemblies reduce the desktop
  composition constructor; session lifecycle, UI refresh and save ordering
  have an independent `DesktopSessionRuntime`.
- Removed unused module-level care, need-decay, friendship and routine
  mutation adapters, with regression tests on pure transitions and
  `PetState` state changes instead.
- Typed mood-hint keys, due-meal IDs and UI-owned German status/weekday
  formatting replace duplicated and obsolete localized domain helpers.
- Final interactive Windows revalidation remains required before PR #9 merge.

## Unreleased — Food, digestion and observed workload

- Five selectable foods (Onigiri, Sandwich, Taiyaki, Apple, Dango) with
  independent satiety gains, digestible reserves and repetition reactions.
- New testable `pet/food.py` tuning constants and `FoodState` stored in the
  optional `pet.food` field of the existing version-one save format.
- Hunger progression uses actual active session time plus separate hardware
  and user-input observations, not inferred tasks or offline uptime.
- Food selector and smaller transparent sprite overlays follow per-frame
  hand anchors of the eight-frame eat animation.
- 24-hour nutrition, workload/privacy, persistence and GUI regression tests.

# Project change history

Aiko Desktop Pet is maintained as a source repository. The dates below describe
verified GitHub milestones, **not** packaged Windows releases. There is currently
no separate downloadable executable installer or published GitHub Release;
the source includes a Windows setup script.

## Unreleased — Pinnable toolbar and persistent settings

- Keep one care/status toolbar; replace the redundant status window with an
  optional session-local visibility pin and expandable inline status details.
- Make settings a persistent, independently movable Kenney-styled window.
  Outside clicks and preference changes no longer close it; explicit reopen
  focuses the existing instance. Remember its position within the session.
- Share root-local AikoSkin images/styles and title-only WindowDrag behavior
  between toolbar, settings and the existing minigame. Preserve game mechanics.
- Separate active control use from visibility so idle open windows do not
  permanently suppress autonomous behavior or queued notifications.
- Migrate affected tests, lifecycle wiring and the gallery capture script.
  Preserve version-one saves, approved artwork and authored dialogue.
- Full CI and native Windows acceptance remain pending for the prepared patch;
  see [the window contract](docs/UI_WINDOW_CONTRACT.md).

## Unreleased — Aiko Anime assets and playback

- Restore calm 2.52-second ambient cycles and slower 1.413-second walking.
  Preserve all eight poses and source timings. Walk two to four cycles, then
  rest for 60–180 seconds; fractional motion no longer ends walks prematurely.
- Use one suspend-excluding session clock across ticks, care, settings and
  saving. Preserve save values on reopen without offline decay or recovery.
- Set waking hourly decay to 30 satiety, 4 mood, 6 energy, 8 social and 6
  affection points, with bounded measured-load additions. Retain sleep recovery,
  care effects and friendship limits. Add non-interrupting friendly care requests.
- Fix the Pillow 11.3 strict-type boundary and explicit Win32 scalar conversions.
  Make GUI mapping and repeated-local-hour test fixtures portable on Windows/DST.

- Track only the 134 original inputs needed to rebuild the selected character
  export, with SHA-256 inventory and separate restricted asset terms. Ignore
  the other 813 archive members. Preparation code remains MIT; Kenney stays CC0.
- Replace the previous 73 runtime sprites with 112 full-width 192 × 208 poses.
  Prepared Windows images preserve the source artwork and use binary alpha.
- Decode typed animation metadata, play authored frame timings independently
  of the desktop tick, show every pose under delayed callbacks, extend one-shot
  deadlines and cancel timers on shutdown. Walking positions update every
  33 ms independently of the unchanged 140 ms simulation tick.
- Bind feeding to eating, petting to its own action and sleep to the breathing
  loop; preserve dialogue, care rules and version-one saves.
- Retain attack artwork, hand layers and overlay anchors without an attack
  trigger or new game mechanic.

## Unreleased — Remove obsolete import and desktop adapters

- Review repository consumers and remove 25 flat-module forwarding files,
  five old application view modules, the legacy presentation adapter and
  the desktop compatibility facade (32 files in total).
- Migrate behavior tests to canonical packages and component owners; remove
  tests whose sole purpose was keeping old imports or attributes alive.
- Remove the `ComputerVoice` alias, the `DesktopPet.computer_voice` attribute
  and unused compatibility re-exports from the desktop bootstrap.
- Update CI import/type-check commands and enforce application boundaries
  without exceptions for the removed view modules.
- Document [import migration](docs/ARCHITECTURE.md#import-migration).
  Existing launchers, version-one saves, artwork and dialogue are preserved.
  External Python code using retired paths or desktop attributes must migrate.

## 2026-10-13 — Public repository polish (PR #3)

[PR #3](https://github.com/Lexoniarus/aiko-desktop-pet/pull/3)
updates public documentation and repository hygiene without changing Aiko's
runtime behavior, sprite assets, or save format.

- Reorganize the README around the running application, getting started,
  privacy, contribution and asset attribution.
- Curate the existing real screenshots, animation GIFs and historical UI
  references without regenerating or relicensing the underlying art.
- Explain the optional `.env.example` and expand ignored local test, editor
  and diagnostic artifacts.
- Remove the obsolete script that copied local files and pushed directly to
  `main`; use focused branches and pull requests instead.
- Add the maintained architecture guide, contribution guidance and GitHub
  issue/PR templates.
- Clarify historical documents and pin developer-only static analysis tooling.
- Document security disclosure and validate the public repository with tests.

## 2026-10-13 — Modular OOP architecture merged (PR #2)

[PR #2](https://github.com/Lexoniarus/aiko-desktop-pet/pull/2) was merged
into `main` as
[`073e7a4`](https://github.com/Lexoniarus/aiko-desktop-pet/commit/073e7a43551f0b29abe5d04b760c6324230e4be8).

- Canonical `pet/`, `personality/`, `application/`, `presentation/`,
  `ui/`, `desktop/` and `infrastructure/` responsibilities.
- Pure pet transitions and an application-owned valid-save catch-up policy.
- Immutable semantic read snapshots and separate German display projections.
- Typed desktop tick ports, lifecycle, preferences and provider contracts.
- Preservation of version-one local save data, historical public imports,
  approved character sprites and authored German dialogue.
- Maintainer-reported native Windows acceptance.

Post-merge GitHub Actions
[38382796398](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/38382796398)
passed 486 tests each under Linux Python 3.11/3.13 and 257 Windows-headless
tests, with successful Ruff/Mypy/Pyright checks.

## v0.13 — Original public feature baseline

The historical **v0.13** project included a Kenney sci-fi hover interface,
15 pixel emotes, 73 Aiko character animation frames, six displayed gauges
(five care needs plus friendship) and sequenced German character reactions.

Earlier milestones introduced desktop placement and gaze (v0.2–v0.8),
adaptive local rhythm learning (v0.9), context-sensitive reactions (v0.10),
care/friendship (v0.11) and differentiated affection (v0.12). The numeric
feature baseline is not a GitHub Release tag or a claim of an installer build.
Detailed historical records are available at the fixed
[pre-cleanup documentation snapshot](https://github.com/Lexoniarus/aiko-desktop-pet/tree/502c95d88062481d457b4901d1cc797bff8756e2/docs),
including the [original feature timeline](https://github.com/Lexoniarus/aiko-desktop-pet/blob/502c95d88062481d457b4901d1cc797bff8756e2/docs/HISTORY_0_2_TO_0_13.md)
and [completed OOP refactor record](https://github.com/Lexoniarus/aiko-desktop-pet/blob/502c95d88062481d457b4901d1cc797bff8756e2/docs/REFACTOR_ARCHITECTURE.md).
Historical test totals and balancing figures describe their own revisions,
not the current implementation or latest CI status.

## Compatibility approach

The current source uses canonical package imports. Retired module paths and
desktop forwarding attributes are documented in the import migration table.
Version-one save compatibility is retained; changes to callable interfaces or
the JSON schema require explicit migration instructions and regression tests.
