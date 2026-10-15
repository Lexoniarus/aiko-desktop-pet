# World objects, perception and autonomous interaction — implementation plan

Status: Stages 1–8 implemented; final automated regression passed through
`bac23e0` (828 tests). Native practical acceptance remains open.
Recorded: 15 October 2026.
Baseline: `main` at `1753266db0dafc94024913cb281b80e7abe289a0` (merged PR #9).

Stage 1 contracts were specified on 15 October 2026 in
[World object contracts and behavior rules](WORLD_OBJECT_CONTRACTS.md), including
the user's release-to-accept, goal-movement and care-attribution decisions.

This document records the accepted feature, delivery commits and verification.
Native acceptance is separate from automated implementation checks. Keep the
[current architecture](ARCHITECTURE.md) as the reference for the existing code.
The [refactor ledger](PET_ARCHITECTURE_REFACTOR.md) describes the preceding work;
its exclusions do not prohibit the explicitly planned feature here.

## First complete user scenario

### Accepted implementation update

Direct feeding is removed when cursor pickup is connected. All ten foods and
the energy drink use World instances. Accepted handover happens on release.
Pickup uses the supplied eight-frame animation (source frame 4 acquires), and
reverse playback puts a held item down before an interrupting user action.
Consumption starts only after pickup completes, with no effect on mere grasp.

Start parameters: seek food at satiety <=70, drink at energy <=60; notice within
3 character widths after 0.2 s, recognize within 1.5 widths after 0.6 s. Memory
expires after 600 active seconds. Reevaluate at most once per second plus
meaningful changes; search a remembered position for 2 s, retry after 10 s,
and pause 30 s after consumption. Stable eligible targets are retained.

The first practical handoff includes all eight stages and restart support, a
temporary-save launcher with hungry/full scenarios, full regression and a draft
PR. No merge to main occurs before practical acceptance.

Delivery sequence (each item is a tested commit; further splits are allowed):

1. Preserve existing World foundation and tests.
2. Record contracts and the accepted end-to-end plan.
3. Extend World for drinks, put-down and surface changes.
4. Add time-based object perception.
5. Add subjective object memory.
6. Add interests and stable intentions.
7. Add shared goal movement.
8. Integrate object attention with desktop phases.
9. Import approved pickup resources reproducibly.
10. Add forward/reverse playback and identified action events.
11. Share consumable effects with explicit origin.
12. Coordinate pickup, consumption and interrupted put-down.
13. Render World/hand items and foreground layers.
14. Connect cursor gestures/falling and retire direct feeding.
15. Persist joint pet/World state and recover interrupted objects.
16. Complete regression, smoke launcher and practical test checklist.

1. The user presses and holds an existing food choice, initially an Onigiri.
2. A concrete portion appears at the cursor and follows it while held.
3. The user can offer the portion directly to Aiko. She must notice it and
   decide whether to accept it before ownership changes.
4. Alternatively, the user releases it over the desktop. It falls to the
   taskbar-aligned ground and remains there.
5. Depending on distance and attention, Aiko notices and recognizes the object.
6. She can initially leave it alone and reconsider it when hungry.
7. She selects that portion, approaches its interaction position, checks it
   again, takes it and eats it using the existing nutrition rules.

The taskbar is the first horizontal walking surface. The desktop above it is
available for carrying and falling objects. Cursor pickup/release replaces
the old direct-feeding UI for all foods and the energy drink.

## Scope and limits

- Build a small real in-memory World before attaching mouse input to it.
- Separate objective objects, perception, remembered information, interest,
  intention and interaction execution.
- Reuse existing nutrition, food identity, assets, movement and animation.
- Include offering, falling, approach, acceptance, refusal and consumption in
  the complete feature; implement their UI after the headless behavior.
- Start with deterministic, time-based perception rules. Randomness, learned
  preferences and richer experience models can be added later if useful.
- Defer inventories, spoilage, complex physics, free desktop navigation and
  long-term learned food preferences.
- Do not consume World objects during closed-time reconstruction. Preserve the
  existing offline meal behavior as a separate mechanism.

## Canonical ownership

| Owner | Owns | Boundary |
| --- | --- | --- |
| New `world/` domain package | Object instances, spatial state, custody, fall progression and allowed object transitions | No Tk, Win32, pet needs or persistence I/O |
| Existing food catalog and pet food policies | Food identity, nutrition, digestion and acceptance rules | No duplicated food table in World |
| Existing item/character asset catalogs | Graphics, scale variants, grip points and animation resources | Visual data does not decide care or consumption |
| `pet/state.py` | Pet needs and committed nutrition effects | World and widgets never mutate needs directly |
| `pet/mind/` | Perception, subjective object memory, interest and intentions | Decisions receive observations, not unrestricted World access |
| `pet/movement/` | Pure movement policies and one shared movement executor | Random and goal movement cannot move Aiko independently |
| `application/` | Interaction execution, arbitration and coordinated World/Pet changes | No concrete Tk widgets or native APIs |
| `desktop/` | Input observations, coordinate mapping, actual placement and runtime wiring | Supplies host facts; does not invent pet decisions |
| `ui/` | Cursor item, World visuals, animations and feedback | Renders projections; owns no second object store |
| `infrastructure/` | Validated definitions, assets and durable session data | Decoding does not simulate behavior |

Suggested module names may be refined during each stage. Do not create empty
packages or a generic framework solely to mirror this table.

### Object definition, instance and presentation

- A definition describes an object type and its supported interactions. Food
  definitions reference the canonical food and visual catalogs by ID.
- An instance represents one portion with a stable instance ID, definition ID,
  position and lifecycle/custody state. Identical foods have distinct instances.
- Presentation resolves graphics and anchors from existing asset owners. World
  positions, ground anchors, hand grips and interaction positions are distinct.
- Read snapshots are immutable values. Only the World owner changes instances.
- Use explicit lifecycle/custody states for user-held, falling, resting,
  pet-held and consumed objects. Avoid contradictory independent flags.
- Offering is an interaction context around an existing instance; it creates
  neither a second portion nor a second custody owner.

### Objective information and subjective knowledge

The World knows the real identity and position. Perception decides what Aiko
can learn now. Object memory contains only information already acquired,
including last-known position and observation time.

An instance ID may support continuity without granting recognized food identity.
An unseen move must not update remembered position or a pursuit target. Losing
sight of an object is not proof of destruction. Revisiting an observed empty
location can invalidate its remembered presence.

### Intention and execution

Keep knowledge, evaluation and execution separate. Recognized, uninteresting
and currently resting can all be true simultaneously.

An intention holds a selected goal. An application interaction holds its actual
progress, interruptions and completion. The animation presenter owns playback
only. Define explicit reasons for completion, refusal, deferral and cancellation;
do not encode all these concerns in one large state machine.

## Invariants and integration rules

1. Every mutable value has one owner. Aiko's current position must not be copied
   into an independently writable World value alongside the existing settings.
   Define the position adapter before changing that ownership.
2. All domain mutations occur on the existing application owner thread. Add
   neither a second behavior thread nor an independent behavior heartbeat.
3. Advance pet needs before evaluating object interest. Reuse the shared
   active-session clock without consuming the same interval twice.
4. Update observations and intentions before character presentation. Existing
   faster movement/frame playback uses the most recently confirmed targets.
5. Perception uses elapsed time. Equivalent observations must behave consistently
   across update cadences. Inject clocks and any future random source.
6. Retain a target across minor interest changes. Reconsider for meaningful
   events, invalidation or an explicit reevaluation interval. Apply cooldowns
   after refusal, failed search, interruption and consumption as appropriate.
7. Validate existence, custody, distance and pet acceptance again immediately
   before acquisition or consumption. Repeated requests cannot duplicate effects.
8. Acquiring an item and consuming it are separate operations. The first eating
   interaction may perform them consecutively.
9. Nutrition is committed at the confirmed start of eating. Consumption and the
   pet effect form one coordinated application operation; no UI callback or save
   occurs between the related commits. Define failure handling before coding it.
10. The eating animation follows the confirmed result. Its completion cannot
    grant nutrition again. Interrupting playback after consumption does not
    recreate the portion or reverse the already committed meal.
11. Autonomous food uses canonical nutrition rules without simulating a user
    click or granting fictitious human care/friendship. Preserve the origin of
    direct human handover separately; specify its reward policy explicitly.
12. Direct user actions, sleep, games and existing animations participate in
    explicit arbitration. Define whether each event cancels, defers or allows
    completion. Do not reset ongoing animations on every behavior update.
13. `follow_cursor` and `spontaneous_talk` do not enable or disable object
    perception. As confirmed during Stage 1, `auto_walk` controls random walks;
    perceived wanted food can cause goal movement even when it is disabled.
14. Holding food near Aiko can attract her attention. Handover requires release
    in her handover area and acceptance at that moment. Failed handover falls.
15. Successful direct handover uses existing direct-feed care/friendship rules;
    autonomous ground collection does not grant those human-care effects.

## Staged implementation checklist

All eight implementation stages are complete. Native Windows input, layering,
taskbar edges and 1x/2x grip alignment await the first practical acceptance.
Use the [isolated test checklist](WORLD_SMOKE_TEST.md); the real save stays untouched.
The [draft PR](https://github.com/Lexoniarus/aiko-desktop-pet/pull/10) remains
unmerged. Local results below are not a remote CI claim.

| Stage | Deliverable | Status | Commit/PR and evidence |
| --- | --- | --- | --- |
| 1 | Contracts and behavior decisions | Specified (documentation only) | [Stage 1 contracts](WORLD_OBJECT_CONTRACTS.md), user decisions and scenario review, 15 October 2026; no runtime checks claimed |
| 2 | Minimal in-memory World | Implemented | `069923c`, `c08be50`; World state/catalog/extension tests |
| 3 | Perception and object memory | Implemented | `56617ad`, `a69e772`; perception/memory/awareness tests |
| 4 | Interest and stable intentions | Implemented | `34b9b74`; intention/cooldown/tie tests |
| 5 | Gaze, goal movement and runtime integration | Implemented; native acceptance open | `4b61579`, `5807c6c`, `293e56e`; goal walking and real Tk arrival tests |
| 6 | Acquisition and autonomous consumption | Implemented | `7047799`, `7f7ad39`, `50ad3b2`, `1b9dfc8`; playback, origin, transaction and interruption tests |
| 7 | Cursor pickup, offering and falling | Implemented; native acceptance open | `975bcb8`, `2b6b7e0`, `5d25d04`, `f4f18fd`; World GUI/falling/input tests |
| 8 | Persistence and complete regression | Implemented; practical acceptance open | `220043b`, `d4f356d`, `1b0e767`, `9581d61`; persistence, isolated launcher and real Tk put-down-before-sleep tests |

### Delivery commit ledger

Each requested step has a green implementation boundary; corrective splits
preserve the same branch and keep prior work intact.

| Step | Commit(s) |
| --- | --- |
| 1 — preserve foundation | `069923c` |
| 2 — accepted plan/contracts | `697322c` |
| 3 — drinks, put-down, surface | `c08be50` |
| 4 — perception | `56617ad` |
| 5 — subjective memory | `a69e772` |
| 6 — stable intentions | `34b9b74` |
| 7 — shared movement | `4b61579` |
| 8 — awareness/gaze phase | `5807c6c` |
| 9 — approved source import/provenance | `7047799`, `f4ed371` |
| 10 — identified pickup/reverse playback | `7f7ad39` |
| 11 — consumption origin | `50ad3b2` |
| 12 — interaction coordination | `1b9dfc8`, `26cc71c`, `852fb8b`, `bac23e0` |
| 13 — World and hand rendering | `975bcb8` |
| 14 — cursor/falls/input/arrival | `2b6b7e0`, `5d25d04`, `9e60fd3`, `293e56e`, `f4f18fd` |
| 15 — joint persistence/recovery | `220043b` |
| 16 — regression and test handoff | `d4f356d`, `1b0e767`, `9581d61`, final documentation |

Final local full suite through `bac23e0`: 828 tests passed in 108.0 s on Windows,
Python 3.11. Ruff 0.13.2, strict Mypy 1.18.2 (161 source files) and Pyright
1.1.414 passed. Capture-loss follow-up: six real Tk World tests passed. Asset
preparation reproduces 120 poses, with original runtime PNGs unchanged.
CI run `38759905855` passed Python 3.11/3.13 and Windows at `ffbffc2`.
Final regression, CI and isolated start/restart evidence is recorded in
[the test handoff](WORLD_SMOKE_TEST.md).

### Stage 1 — Contracts and behavior decisions

- [x] Specify instance identity, lifecycle/custody transitions and read contracts.
- [x] Define World coordinates, ground, interaction distance and scale mapping.
- [x] Define observation, recognition, acceptance and consumption prerequisites.
- [x] Write interruption and priority rules for contact, care, sleep, games and
      ongoing animations, including removed, moved and unreachable targets.
- [x] Specify the consumption commit boundary, failure handling and repeated
      request behavior.

Acceptance: the happy path and interruption paths have unambiguous owners and
effects. List remaining product choices with the stage that must resolve them.

Evidence: [Stage 1 contracts](WORLD_OBJECT_CONTRACTS.md) specifies owners, spatial
and lifecycle rules, perception/interest boundaries, arbitration, commit/recovery
behavior and review scenarios. Three product decisions were confirmed by the
user on 15 October 2026. Numeric tuning and later input/persistence details are
explicitly assigned to their implementation stages. No implementation is claimed.

### Stage 2 — Minimal in-memory World

- [x] Implement concrete portion creation and named lifecycle/custody operations.
- [x] Expose immutable snapshots and reject invalid transitions.
- [x] Model positions and the horizontal ground without desktop dependencies.
- [x] Connect definitions to existing food/asset IDs without copying their data.
- [x] Use scripted inputs and temporary test worlds; no mouse UI is required.

Acceptance: identical portions remain independent. Invalid custody transitions
are rejected and a consumed instance cannot be acquired again.

Implementation: [World contracts](../aiko_pet/world/contracts.py),
[World state owner](../aiko_pet/world/state.py) and
[catalog adapter](../aiko_pet/infrastructure/world_catalog.py).
The [Stage 2 API boundary](WORLD_OBJECT_CONTRACTS.md#stage-2-implementation-boundary)
separates recorded custody changes from future application-level eating.

Local evidence, Windows/Python 3.11, 15 October 2026:

- [21 focused World tests](../tests/test_world_state.py) and
  [catalog tests](../tests/test_world_catalog.py) passed together. Coverage includes
  independent portions, invalid transitions, single-carrier slots, stale
  revisions, bounds/footprints, immutable historical snapshots, thread ownership
  and canonical catalog identity.
- Full suite: `uv run --no-project --python 3.11 --with Pillow==11.3.0 python -m
  unittest discover -s tests -q` — 788 tests passed. Existing Tk tests emitted
  `ttk::ThemeChanged` teardown diagnostics; the runner finished with `OK`.
- Repository Ruff 0.13.2, strict Mypy 1.18.2 (149 source files) and Pyright
  1.1.414 passed. Dependency audits enforce the new World/pet boundaries.
- No UI, mouse, movement, pet mutation or persistence wiring was added. Timed
  falling, changing surface geometry, joined consumption and receipts remain
  later-stage work. No native interaction sign-off or remote CI run is claimed.

### Stage 3 — Perception and object memory

- [x] Add perception contracts/policies and one subjective object memory owner
      under `pet/mind/`, coordinated through application read ports.
- [x] Implement noticed, recognized and remembered information using distance,
      attention, motion and observation duration.
- [x] Store last-known position/time without leaking unseen World changes.
- [x] Extend validated balance data with explicit perception/memory parameters.
- [x] Cover loss of sight, observed absence and equivalent update cadences.

Acceptance: an unseen move leaves remembered position unchanged. The same
observation history produces consistent results at different update rates.

### Stage 4 — Interest and stable intentions

- [x] Evaluate known objects from needs and current activity using canonical
      food information.
- [x] Support looking, approaching, deferring and abandoning a goal initially.
- [x] Retain targets with explicit switching thresholds and deterministic ties.
- [x] Reevaluate on meaningful events/intervals and apply retry cooldowns.
- [x] Exercise decisions without any movement or rendering dependency.

Acceptance: a satiated Aiko can leave an Onigiri alone and later select the same
one when hungry. Competing portions do not produce rapid target switching.

### Stage 5 — Gaze, goal movement and runtime integration

- [x] Implement the confirmed random-versus-goal `auto_walk` semantics and
      Stage 1 arbitration rules in movement integration.
- [x] Extend the existing movement path for goals; share actual displacement
      feedback with random walking and preserve one position writer.
- [x] Resolve a reachable interaction position beside each target.
- [x] Add object gaze using the existing sixteen directions and explicit
      cursor/object attention selection.
- [x] Wire one named behavior coordination phase into the existing desktop tick.
- [x] Handle invalidation, bounds and interruption without conflicting timers.

Acceptance: Aiko smoothly reaches a scripted visible object without waiting for
a random departure. Sleep, contact, games, removed targets and unreachable goals
produce the specified result. Perform a native Windows movement/gaze check.

### Stage 6 — Acquisition and autonomous consumption

- [x] Add an application use case for a specific World instance and typed results.
- [x] Recheck custody, availability, reach and food acceptance at execution time.
- [x] Reuse pet nutrition policies, with `PetState` committing pet changes.
- [x] Coordinate acquisition/consumption with World and preserve action origin.
- [x] Begin existing eating/held-item presentation from the confirmed result.
- [x] Test refusal, interruption, failed/repeated requests and exactly-once effects.

Acceptance: autonomous eating changes the correct portion and pet once, with no
fabricated human-care reward. Refusal changes neither nutrition nor custody.
Keep the offline meal mechanism separate.

### Stage 7 — Cursor pickup, offering and falling

- [x] Implement release-to-accept and fall-on-refusal; finalize short-click/hold
      discrimination and input cancellation details.
- [x] Adapt food-choice press/hold/release input into World operations.
- [x] Render the user-held instance at the cursor; end user custody on handover.
- [x] Add elapsed-time-based fall progression and one ground-contact transition.
- [x] Present resting/falling instances through World read projections.
- [x] Feed carried and falling observations into the same perception pipeline.
- [x] Define cancellation, capture loss, shutdown and out-of-area release behavior.

Acceptance: the full Onigiri scenario works visibly, including successful
handover, refusal, falling, ignoring and later autonomous eating. A gesture
cannot accidentally create or consume multiple portions. Check native Windows
input, layering and scale changes with an isolated save.

### Stage 8 — Persistence and complete regression

- [x] Design the save-format extension/migration before changing serialization.
- [x] Preserve existing saves, `AIKO_SAVE_PATH` and safe backup/write behavior.
- [x] Save related durable pet/World state in one consistent session snapshot.
- [x] Define recovery for carried, falling and pet-held instances; do not restore
      stale cursor capture, active timers or an in-progress interaction verbatim.
- [x] Start perception and decision-making afresh after restoration; do not
      replay consumption or consume World food offline.
- [x] Complete automated checks.
- [ ] Complete native Windows end-to-end acceptance using the isolated launcher.
- [x] Update current architecture, user guidance and change history to describe
      only the behavior actually shipped.

Acceptance: reopening produces no extra portions or nutrition effects. Test old,
new, malformed and interrupted-save cases, plus scales, displays/taskbar setup,
games, sleep, direct care and existing animations.

## Resolved implementation decisions

| Decision | Resolve by | Current boundary |
| --- | --- | --- |
| Hunger threshold and reevaluation/cooldown values | Stage 4, implemented | Food ≤70, drink energy ≤60; reevaluate 1 s, search 2 s, retry 10 s, post-consumption 30 s; validated balance data |
| Movement setting semantics | Settled in Stage 1; implement in Stage 5 | `auto_walk` gates random walks; wanted perceived/remembered food goals can move independently under other activity gates |
| Action interruption/priority details | Specified in Stage 1; verify in Stage 5 | Follow the Stage 1 arbitration table; preserve existing render priorities |
| Offer gesture and refusal outcome | Stage 7, implemented | Press starts one portion; release after recognition/willingness offers it, otherwise it falls. Escape/capture loss cancels |
| Human-handover reward policy | Settled in Stage 1; implement in Stage 6 | Accepted direct handover uses canonical feed care/friendship rules; autonomous collection does not |
| Ground/display mapping and out-of-area drops | Stage 7, implemented | Primary taskbar surface; scale does not multiply positions. Unsupported release removes the cursor portion with brief feedback |
| Recognition and memory tuning | Stages 3 and 4, implemented | Notice 3 widths/0.2 s, recognize 1.5 widths/0.6 s, memory 600 active s; no unseen truth updates |
| Durable object recovery and schema migration | Stage 8, implemented | Optional World v1 inside outer v1; nonterminal objects recover grounded; no offline World consumption |

## Verification and delivery discipline

- Work from the checked current `main` on focused branches, following the
  [repository workflow](GITHUB_WORKFLOW.md). Preserve unrelated local work.
- Use small cohesive commits. Group stages into reviewable PRs according to the
  actual changes; the stage list does not mandate one PR per stage.
- Add behavioral tests for the invariants and failures above. Simulated sources
  exercise the real World/decision contracts rather than a parallel fake model.
- Run required checks from [Contributing](../CONTRIBUTING.md): Ruff, strict Mypy,
  Pyright and the relevant/full unit and GUI suites. Preserve Python 3.11/3.13
  and Windows coverage.
- Validate native mouse handling, movement, transparency/layering, taskbar
  placement, timers and scale 1x/2x on Windows for affected stages. Record exact
  commit, environment and observed result; headless tests do not prove these.
- Use isolated temporary save paths. Never test migration or consumption against
  the user's actual save.
- Treat exactly-once guarantees in early in-memory stages separately from
  restart consistency, which is verified in Stage 8.
- Record evidence in the stage table when complete. Do not infer completion or
  green CI from the baseline or from this planning document.
