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

## Verification gates

Run Ruff, strict Mypy, Pyright, the complete Python 3.11/3.13 unit and Tk/Xvfb matrix and the project's Windows-native smoke checks. Verify in particular the merged item catalog, item sprites and cache tests, 1x/2x asset behaviour, hover/pin and the game window.
