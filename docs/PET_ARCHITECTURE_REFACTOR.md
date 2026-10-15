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


## Completion review — 15 October 2026

- **R1 implemented:** `pet/mind/` owns `PetMind`, dialogues and adaptive
  policy; the Aiko catalogue is provided at the character composition boundary.
- **R2 implemented in code:** pure `pet/animation/` timing, gaze, idle and
  priority rules feed `DesktopAnimationRuntime`. Desktop visual observation
  and host movement have distinct runtime owners; `AnimatedPet.render()`
  applies a typed `RenderDecision` and keeps only Tk frame/timer concerns.
  One `AmbientDirector` is shared by the runtime and sprite playback.
  Native Windows visual/timing confirmation is still required for the final SHA.
- **R3 implemented:** `pet/movement/` owns movement policies;
  `desktop/walk_runtime.py` owns host displacement through `WalkDriver`.
- **R4 implemented:** `ui/pet_view/`, `ui/windows/`, `ui/common/`,
  `ui/view_models/` are the only current UI implementation owners.
- **R5 implemented in code:** `application/assembly.py` builds application
  use-case services, `desktop/animation_assembly.py` wires visual/motion
  components, and `DesktopSessionRuntime` owns lifecycle, overlays and
  advance-before-save ordering. `gui.py` holds composition and thin desktop
  callback adapters rather than business rules or mirrored action state.
- **R6 implemented in code:** removed historical `personality/`,
  `presentation/` and direct UI forwarding paths. Canonical imports and
  implementation ownership are checked by architecture tests. `PetState`
  owns all care, need-decay, friendship and routine mutations; the old
  policy-level mutation adapters have been retired. Localized
  `TimeContext` display helpers were removed in favor of
  `ui/view_models/text_de.py`; mood hints and meals use typed semantic
  decisions. Historical identity-only tests were consolidated and the
  remaining behavior tests now call canonical owners.
- **Verification:** the last reported Windows interactive acceptance covered
  an earlier refactor version. The exact tested SHA and DPI/display details
  were not recorded. Later R2/R5/R6 commits require a targeted Windows check.
  Full Ruff, strict Mypy, Pyright, Python 3.11/3.13, Linux/Xvfb Tk, and
  Windows-headless CI must be green for the final SHA.
- **Merge:** PR #9 stays in draft until the user explicitly approves merging
  after final green CI and the current-commit Windows smoke record.

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
