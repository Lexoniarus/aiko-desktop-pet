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


## Progress on the refactor branch

- Completed: pure gaze, sprite metadata, frame/ambient policies, idle-emote
  selection and JSON timing validation assigned to canonical owners.
- Completed: `pet/mind/` is the canonical owner for PetMind, dialogue and
  existing adaptive/workload policies (with transitional legacy forwards).
- Completed: `pet/movement/` separates random departure planning from the
  one movement controller; `ui/pet_view/walk_driver.py` handles host motion.
- Completed: utility windows, pet-view renderers and UI view models have
  distinct canonical packages; existing compatibility imports remain.
- Completed: cursor-attention history is a pure pet-owned object, while native
  pointer sampling is provided by DesktopInput.
- R5: the composition root now delegates movement, cursor attention, timed
  actions, care presentations, spontaneous reactions, hover and click selection
  to explicitly owned objects. Settings values are composed by `PetSettings`
  without changing its flat save schema.
- R6: canonical active imports are enforced by
  `tests/test_canonical_import_paths.py`; existing architecture tests now
  exercise actual canonical owners, rather than legacy import wrappers.
- Still pending: interactive Windows smoke tests and final draft-PR approval.
  Compatibility shims remain intentionally limited to existing clients/tests,
  with no second business implementation.
- Automated checks: draft PR #9 runs the Python 3.11/3.13 and Windows-headless
  matrix. CI success is evaluated per commit, not assumed for future commits.

## Original R1–R6 acceptance ledger

| Phase | Implementation | Verification |
| --- | --- | --- |
| R1 Mind | `pet/mind/` canonical PetMind, dialogue and adaptive modules | Existing dialogue/click tests + CI |
| R2 Animation | `pet/animation/` pure policies, `ui/pet_view/` renderer | Frame/gaze tests + Windows visual smoke pending |
| R3 Movement | `RandomWalkPlanner`, `WalkController`, `WalkDriver` | Walk timing/bounds tests + Windows smoke pending |
| R4 UI | `ui/windows/`, `ui/common/`, `ui/view_models/` | Existing window and pin tests + Windows smoke pending |
| R5 Orchestration | `ContactCoordinator`, presenters, action playback, composed preferences | Use-case/UI integration tests + CI |
| R6 Consolidation | Canonical import audit and refreshed architecture docs | CI; no merge before native acceptance |

## Verification gates

Run Ruff, strict Mypy, Pyright, the complete Python 3.11/3.13 unit and Tk/Xvfb matrix and the project's Windows-native smoke checks. Verify in particular the merged item catalog, item sprites and cache tests, 1x/2x asset behaviour, hover/pin and the game window.

Manual acceptance steps and a sign-off record are in
[the Windows smoke checklist](PET_REFACTOR_WINDOWS_SMOKE.md).
Until this record is filled by a Windows tester, PR #9 remains a draft.
