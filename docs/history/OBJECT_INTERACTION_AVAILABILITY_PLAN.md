# Hover, action availability and contact feedback

> **Historical record, archived 2026-10-18.** This delivery/review snapshot is
> completed or superseded and is not an active plan. Its old pending checks,
> future proposals and push/merge restrictions describe that revision only.
> Use the [current documentation](../README.md) and
> [current World rules](../WORLD_OBJECT_CONTRACTS.md) for maintained guidance.

Recorded: 18 October 2026. Baseline: `1086385`, `feature/world-foundation`.
Status: complete and locally verified. No push or merge performed.

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
Follow [architecture](../ARCHITECTURE.md) and [contribution rules](../../CONTRIBUTING.md).

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
| 3 | Complete | 98 initial focused tests pass in 22.926 seconds. After the contact-owner/fixture follow-up, 103 targeted tests pass in 70.580 seconds and all 1,149 tests pass in 346.515 seconds on Python 3.11.9. Ruff, strict Mypy (187 sources), Pyright and documentation links pass. |

### Stage 1 evidence

Existing active object episodes now retain admission during UI hover, including
search and loss feedback. Idle UI blocking and unrelated game/playback/custody
rules remain. The revised coordinator regression fails on the baseline and passes
with the correction. A real-timer native regression injects stationary pointer readings
over real sprite geometry with cursor-follow disabled: the toolbar opens, a visible unknown
candidate is approached, and movement continues without extra contact feedback,
care effects or a lost search subject. No new saved or mutable activity state.

### Stage 2 evidence

A read-only contact admission query derives permission from existing World, game,
sleep and playback owners. Toolbar states and UI callbacks share that query,
including food selections from an already open menu. The existing toolbar tick
refreshes permission; pin/settings/details remain usable. Waking remains an
explicit end of sleep. Lower-level explicit interruption retains its safe custody
cleanup. No new mutable busy state was introduced.

Native care tests now complete the previous response before starting another
UI action. A focused regression verifies care/conversation ownership, passive
hover, callback guards and recovery. The stationary-hover search regression also
verifies disabled buttons and rejected callbacks during candidate approach.

### Stage 3 evidence

PhaseFeedback now retains the current auxiliary cue itself instead of a separate
key without its meaning. Contact replies are derived as nonblocking from that
cue; required loss/recognition/find cues retain their receipt gates. The native
attention adapter reads the same distinction through WorldRuntimeAccess. No
additional busy flag, timer or search state was added. Search clicks use three
new authored `object_busy_search` replies on the existing speech surface.

The coordinator regression verifies movement during contact feedback, unchanged
subject/route, required loss priority and rejected stale contact receipts. Existing
mandatory-aside, phase and cancellation tests remain. The real-timer test verifies
both pet click routes, continuing patrol during the visible reply, disabled care
buttons, no care effect, and candidate approach superseding optional speech.

The first whole-suite run exposed older UI tests that start new actions during
unfinished hover/care/click speech, or expect a click to cancel that speech. These
fixtures/expectations now follow the agreed foreground rule. Lower-level explicit
replacement/cancellation contracts remain. Pure window component fixtures open
HoverUi directly instead of starting a pet response.

### Final validation follow-up

The full architecture guard also caught admission behavior growing the GUI
composition root. The read-only permission and ordinary contact guards now live in
the existing ContactCoordinator, with typed current-owner callbacks; World routes
object-busy clicks before ordinary contact. No new coordinator, busy
state or relaxed architecture limit was needed. Passive hover remains separate
from action admission. The unused GUI contact-recording forwarder was replaced
with direct late binding to its owner.

Window component fixtures open HoverUi without starting hover dialogue. Actual
sequential click/care/game tests finish the preceding response before the next
UI action; the pending-food case ends cursor custody before sleep. The old
click-cancels-ongoing-speech assertion now verifies continuation instead.
Low-level explicit command replacement and stale timer/receipt tests remain.
The first full run completed 1,148 tests in 338.431 seconds with nine failures:
eight incompatible UI scenarios/expectations and the unchanged GUI size guard.
All were addressed above. On the reviewed exported snapshot, 103 targeted native
UI, contact and architecture tests pass in 70.580 seconds, including both native
search regressions. Ruff, strict Mypy (187 sources), Pyright, 270 documentation
file targets and 15 anchors pass. A separate 93-test headless owner/architecture
check also passes.

### Completion

The final Git-index export at `99dc5c1` passes all **1,149 tests in 346.515
seconds** with Python 3.11.9 and Pillow 11.3.0. Static checks pass on identical
production/test sources: Ruff 0.13.2, strict Mypy 1.18.2 (187 source files) and
Pyright 1.1.414. Final documentation links, UTF-8 text and Git whitespace checks
also pass. Tk teardown can emit the existing ThemeChanged diagnostic; the
complete result is OK with no failures, errors or skips.

Native Windows/Tk tests use actual widgets and real timers, with controlled
pointer readings and click-handler input on temporary saves. They cover UI
opening, disabled controls/callback guards, continuing movement during busy
speech, candidate/loss priority and safe receipts. No normal save was accessed;
a separate exploratory user playtest is not claimed.

Local commits: plan `af35de4`; hover `4de11cb`; action buttons `1996e25`;
busy replies `b936f69`; contact ownership and corrected UI scenarios `99dc5c1`.
No push or merge performed.

## Subsequent ownership review

The [interaction cleanup plan](OBJECT_INTERACTION_CLEANUP_PLAN.md) records four
small review follow-ups. The completed implementation and validation above
remain the baseline; the follow-up preserves their behavioral contracts.
