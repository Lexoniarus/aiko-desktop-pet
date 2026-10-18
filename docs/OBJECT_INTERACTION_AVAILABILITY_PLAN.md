# Hover, action availability and contact feedback

Recorded: 18 October 2026. Baseline: `1086385`, `feature/world-foundation`.
Status: stages 1 and 2 complete; stage 3 pending. Keep all changes local; no push or merge authorized.

## Required behavior and ownership

Opening, pinning or reading the toolbar does not interrupt a committed object
action, including the entire search and its candidate investigations. Hover
creates no extra pet response during that action. New care/game/feeding actions
are unavailable while another foreground activity owns Aiko. Action buttons show
that same permission and their callbacks recheck it. Passive UI controls remain
usable; existing explicit lifecycle termination and wake behavior remain intact.

A direct pet click may receive a contextual busy reply, without changing the
search subject, route, custody or current movement. Descriptive contact feedback
must remain distinct from required missing/found/identification receipts.

Keep SearchTask, the interaction coordinator, HoverUi and playback as their
existing owners. Derive availability from them; introduce no second busy flag,
search lifecycle, persisted field or movement writer. Preserve attention during
candidate inspection, learned-place orientation, every missing bubble before
candidate investigation, the corrected replacement rule, and observed relocation.
Follow [architecture](ARCHITECTURE.md) and [contribution rules](../CONTRIBUTING.md).

## Delivery stages

| Stage | Change | Required checks |
| --- | --- | --- |
| 1: hover | Stop treating UI hover as a new blocker for an existing object episode, including search. Retain idle UI/notification behavior. | Replace the missing search coverage in existing coordinator/native hover tests. Use a real stationary pointer over the sprite/toolbar, including cursor-follow disabled; verify movement and candidate selection continue without extra hover feedback. Run focused object/hover tests and pinned static gates. |
| 2: action buttons | Supply one read-only user-action permission from current owners. Render disabled care buttons and enforce the same permission in UI callbacks, including stale menus. Keep display/pin/details independent. | Exercise search, candidate action and ordinary foreground care/conversation; buttons and callback guards must agree and recover after completion. Preserve explicit lower-level safe interruption tests; adjust fixtures that previously started a second UI action during unfinished playback. Run native UI and focused architecture/projection tests plus static gates. |
| 3: busy replies | Keep contact asides descriptive while the existing action continues. Use search-specific authored replies. Required receipts still gate their phases and priority. | Verify actual click feedback while a search moves, including hover, route/subject continuity, no care effects and candidate/loss priority. Retain stale-receipt and cancellation protections. Run focused real-timer checks, full suite, pinned static gates and documentation validation. |

Use small English commits and record results after each stage. Verify exported
Git-index snapshots with Python 3.11.9, Pillow 11.3.0, Ruff 0.13.2, strict Mypy
1.18.2 and Pyright 1.1.414. Tk tests run sequentially with isolated temporary
saves and main-thread collection. Do not access or modify the normal save.

## Progress

| Stage | Status | Evidence |
| --- | --- | --- |
| Plan | Complete | Existing owners, UI callbacks and test gaps reviewed; worktree clean at baseline. |
| 1 | Complete | 59 targeted tests pass in 10.088 seconds on the exported snapshot; Ruff, strict Mypy (187 sources) and Pyright pass. |
| 2 | Complete | 79 targeted integration/UI/architecture tests pass in 57.890 seconds; all 6 care UI tests repeated on the final export after a typing-only correction. Ruff, strict Mypy (187 sources) and Pyright pass. |
| 3 | Pending | |

### Stage 1 evidence

Existing active object episodes now retain admission during UI hover, including
search and loss feedback. Idle UI blocking and unrelated game/playback/custody
rules remain. The revised coordinator regression fails on the baseline and passes
with the correction. A real-timer native regression holds an unmoving pointer
over the sprite with cursor-follow disabled: the toolbar opens, a visible unknown
candidate is approached, and movement continues without extra contact feedback,
care effects or a lost search subject. No new saved or mutable activity state.

### Stage 2 evidence

A read-only GUI admission query derives permission from existing World, game,
sleep and playback owners. Toolbar states and UI callbacks share that query,
including food selections from an already open menu. The existing toolbar tick
refreshes permission; pin/settings/details remain usable. Waking remains an
explicit end of sleep. Lower-level explicit interruption retains its safe custody
cleanup. No new mutable busy state was introduced.

Native care tests now complete the previous response before starting another
UI action. A focused regression verifies care/conversation ownership, passive
hover, callback guards and recovery. The stationary-hover search regression also
verifies disabled buttons and rejected callbacks during candidate approach.
