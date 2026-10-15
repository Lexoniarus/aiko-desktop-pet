# Pet domain / UI boundary refactor

Baseline: `main` at `c5d48d1043b1bbe696b6e5d984f2be79ff9348a7` (including PR #8 food and item overlays).

## Purpose

Prepare a readable, character-independent architecture **without adding** cursor fear, dragging, object recognition, World, new emotions, or autonomous item consumption in this refactor.

Canonical ownership:
- `pet/`: PetState, its rules, and pure pet behaviour (mind, gaze, motion and animation policies).
- `application/`: use-case orchestration and command boundaries.
- `ui/`: concrete Tk visuals, both pet sprite and independent toolbar/food/game/settings windows.
- `desktop/`: platform-specific events, taskbar coordinates and scheduling.
- `infrastructure/`: persistence, hardware and asset loading.
- `games/`: game-neutral mechanics already present.

`World` is deliberately not created until its runtime/ownership contract is specified.

## Safety constraints

1. No changes to save-file shape, imported PNGs, authored dialogue, food/item selection, game rewards or animation frames.
2. Retain 16-direction gaze, frame timing, walking pace, taskbar clamping, hover bridging, pinning, click reactions and non-modal settings.
3. Do not import Tk, native desktop adapters or infrastructure into pure `pet/` policies.
4. Place implementation behind canonical imports. Compatibility shims, if temporarily needed for existing consumers, must remain tiny and contain no second implementation.
5. Do not treat an import-only migration as a completed behavioural refactor.
6. No merge to `main` before the full test matrix and Windows smoke checks.

## Small-step migration

- A. Establish the new architecture contract and record main baseline.
- B. Move independent pure animation policies into `pet/animation/`, redirect live consumers, preserve explicit compatibility during the transition.
- C. Separate random-walk planning from movement execution; replace its taskbar-specific input with a pure movement boundary.
- D. Extract `pet/mind/` and the current dialogue, click and adaptive policy owners. Preserve existing line-selection semantics.
- E. Regroup Tk controls under `ui/windows/`, concrete pet visuals under `ui/pet_view/`, and presentation-only status view models under `ui/view_models/`.
- F. Unmix `AnimatedPet` responsibilities and reduce `gui.py` to a bounded composition root; update import-graph checks and remove obsolete shims.

This is a work plan, not an implementation claim. Mark each step complete only after passing relevant automated checks.


## Progress on the refactor branch (15 October 2026)

- **R1 canonical owners:** `pet/mind/` owns `PetMind`, dialogue and adaptive
  policy; Aiko's authored catalogue is injected by the character factory.
- **R2 implementation separated:** `pet/animation/` owns pure timing,
  gaze, priority and ambient policies. `DesktopAnimationRuntime` chooses
  complete sprite intent and supplies an immutable `RenderDecision`;
  `DesktopVisualObservation` owns gaze history and workload observation.
  `AnimatedPet.render()` now applies the selected frame, retains only Tk
  frame playback and uses injected walking/frame callbacks. A single shared
  `AmbientDirector` avoids duplicate animation state. Automated checks and
  targeted Windows revalidation are the remaining R2 acceptance gates.
- **R3 done:** `pet/movement/` plans bounded movement;
  `desktop/walk_runtime.py` owns the host `WalkDriver` and placement
  connection independently of the Tk sprite.
- **R4 done:** `ui/pet_view/`, `ui/windows/`, `ui/common/` and
  `ui/view_models/` are the sole implementation owners.
- **R5 in progress:** movement, cursor, care and spontaneous event handling
  are delegated from the shell. Sleep/wake dialogue is selected by
  `AttentionCoordinator` and presented by `DesktopAttentionRuntime`.
  `gui.py` now reads `ActionPlayback` state and deadlines directly rather
  than mirroring them in shell properties; `DesktopPreferences` no longer
  requires an unused `PetState`. Constructor wiring and remaining private
  adapters still need the final ownership review.
- **R6 in progress:** the former `personality/`, `presentation/` and
  root-level UI forwarding modules are **gone**; canonical-import checks
  enforce their absence. `PetState.mood_hint()` now returns typed status keys,
  and `PetState.due_meal()` returns meal IDs. German status copy is owned by
  `ui/view_models/text_de.py`. Fourteen import-identity-only test files were
  consolidated into one stronger canonical-owner matrix. Remaining historical
  APIs and documentation must be audited before marking R6 complete.
- **Windows acceptance:** on 15 October the maintainer reported the prior
  branch's Windows behavior functional. Exact machine/DPI/tested SHA were not
  recorded, and subsequent cleanup commits need a targeted recheck.
- **CI:** Ruff, strict Mypy, Pyright, Python 3.11/3.13 and Windows-headless
  tests are required for each candidate commit. Historical success is not
  acceptance of newer commits; PR #9 stays a draft until final sign-off.

## Original R1–R6 acceptance ledger

| Phase | Implementation | Verification |
| --- | --- | --- |
| R1 Mind | `pet/mind/` canonical PetMind, dialogue and adaptive modules | Existing dialogue/click tests + CI |
| R2 Animation | `pet/animation/` pure policies, `ui/pet_view/` renderer | Priority/frame/gaze tests + targeted Windows recheck |
| R3 Movement | `RandomWalkPlanner`, `WalkController`, `WalkDriver` | Walk timing/bounds tests + reported Windows smoke |
| R4 UI | `ui/windows/`, `ui/common/`, `ui/view_models/` | Existing window and pin tests + reported Windows smoke |
| R5 Orchestration | `ContactCoordinator`, presenters, action playback, composed preferences | Use-case/UI integration tests + CI |
| R6 Consolidation | Canonical import audit and refreshed architecture docs | CI; no merge before native acceptance |

## Verification gates

Run Ruff, strict Mypy, Pyright, the complete Python 3.11/3.13 unit and Tk/Xvfb matrix and the project's Windows-native smoke checks. Verify in particular the merged item catalog, item sprites and cache tests, 1x/2x asset behaviour, hover/pin and the game window.

Manual acceptance steps and a sign-off record are in
[the Windows smoke checklist](PET_REFACTOR_WINDOWS_SMOKE.md).
Keep PR #9 in draft until the final exact commit is tested on Windows and
the acceptance record is completed. A prior reported successful test does not
automatically cover later changes.
