# Focused World OOP cleanup — delivery plan

Recorded: 17 October 2026.
Baseline: `d12c5a1e5eb9` on `feature/world-foundation`.
Status: stages P0–P6 automatically verified; final P7 documentation CI pending.
Manual native World acceptance remains open.
PR #10 stays **draft and unmerged**. Main must remain untouched.

This follows the reviewed OOP stages 1–7 in [OOP_REFACTOR_PLAN.md](OOP_REFACTOR_PLAN.md)
and the newer [World behavior contract](WORLD_OBJECT_CONTRACTS.md).
The goal is *clearer state ownership and reliable transitions*, not an arbitrary
class count or broad feature refactor. Preserve one owner for each state,
existing authored dialogue, timings, object IDs, save formats, assets, physical
reach/ownership validation and handover versus autonomous care origin.

## Non-negotiable behavior

- Perception of a missing remembered place uses the **same outer notice radius**
  as perception of a new object, with separate continuous dwell and pending
  occupant checks. Confirmed missing has priority over novel discovery.
- Confirmed missing starts **one bounded search**, even if no current appetite.
  A suitable new find can replace a search and one uniquely identified same-type
  finding can reconcile missing memory in either event order.
- An unidentified cursor object can be accepted in the valid handover area,
  examined in Aiko's hands, and then used or put down. Deliberate presentation
  before the face remains an independent identification and appraisal route;
  an explicit recognized refusal remains effective.
- A remembered local type may match a different technical instance. Type
  conflicts are checked safely when held, but World definition handles never
  silently identify food in Aiko's mind. A hidden move cannot disclose its new
  location. Save/restart and multiple identical portions must keep their
  previous subjective contracts.

## Small, independent commits

| Order | Purpose and owner | Specific boundary | Regression gate |
|---|---|---|---|
| P0 | Record plan, baseline and protected semantics | Documentation only | No behavior diff |
| P1 | Prevent premature Mind contact on rejected/failed handover | `PetMind` provides nonmutating context capture; `ObjectConsumption` records accepted contact only after canonical commit | Failed/accepted handover, duplicate receipt and rollback tests |
| P2 | Eliminate second implicit search trigger for an unconfirmed location | `ObjectAbsencePerception` is sole negative evidence; `ObjectBehaviorCoordinator` waits for confirmation; desktop only reports native reach | Timed missing, delayed candidate, boundary, no phantom search |
| P3 | Put held type-conflict validation behind the World/perception boundary | `ObjectAwareness` supplies a narrow recognition-safety decision; interaction coordinates inspection only | Same apple at same place, cookie substitution, actual hand investigation |
| P4 | Remove dead phase/results and obsolete preview state | Drop unreachable `SearchStopped`, unconditional `search_after`, unused cursor preview property | Search, feedback, offers and type checks |
| P5 | Divide long coordination steps by responsibility, preserving one transition owner | Extract small private operations for sensory/update/phase groups; no parallel state machine | Interaction/awareness suites, synchronous receipts |
| P6 | Reduce implicit `gui.py` setup ordering with meaningful assembly ownership | Reuse or extend desktop composition helpers; do not duplicate session or window state | Dependency graph, runtime startup/shutdown, native UI |
| P7 | Correct current architecture/older plan wording, close ledger | Document revised search priority and acquisition boundary without altering history | Full regression, documentation consistency, CI, native checklist |

**Every implementation commit must be reviewable and pass focused tests and
Ruff, strict Mypy and Pyright checks.** Use pinned repository versions and
existing CI on every pushed commit. Stop and fix a red run before extending
the implementation. Re-run the full suite on the final commit: Python 3.11
and 3.13 with Tk/Xvfb and the Windows boundary suite.

Keep test-only fake sessions isolated. No real user save, PNG art, balance JSON
or external application settings are changed. Any discovered semantic ambiguity
must be explicitly documented instead of silently reinterpreted.

## Review checkpoints

- No World/Tk dependency in Pet/Mind policies.
- No objective definition lookup in the interaction state machine.
- The application does not mutate a second live pet, clock, target, memory,
  search timer or care owner.
- Failed World/Pet/Memory operation does not leave a prematurely recorded
  social contact in Mind; successful human handover does exactly one.
- Deferred and restarted sessions preserve known history but never resume an
  action/gesture that was not persisted.
- Native visual/interaction acceptance by the user remains an independent
  gate after the final automated green CI.

## Delivery evidence and current ownership outcome

Each entry is a separate, narrow commit on `feature/world-foundation`, with a
complete, pinned GitHub Actions run before the next code stage.

| Stage | Commit | Evidence |
|---|---|---|
| P0 | `4ae29a3` | [CI 39069711093](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/39069711093) green |
| P1 | `d0e1215`, test correction `8206220` | [CI 39069880728](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/39069880728) green |
| P2 | `2619465` | [CI 39070216022](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/39070216022) green |
| P3 | `dd121f2` | [CI 39070524884](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/39070524884) green |
| P4 | `e539908` | [CI 39070938577](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/39070938577) green |
| P5a | `792ebb7` | [CI 39071246899](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/39071246899) green |
| P5b | `34c3110` | [CI 39071647505](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/39071647505) green |
| P6 | `0564f8b` | [CI 39071951843](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/39071951843) green |
| P7 | Final documentation and ledger cleanup | Final source-equivalent CI after documentation commit |

P1 preserves the existing canonical direct-care path: only the World handover
consumption path now uses side-effect-free pre-care capture. Mind still owns
its social-contact record and the application records accepted contact once.
P2 removes the competing no-binding search trigger rather than inventing a
second negative-evidence policy. P3 adds a pure, non-identifying guard at the
application awareness boundary, injected into the existing interaction owner.
P4 removes obsolete search and offer diagnostics. P5 splits existing methods
without moving the phase state or candidate memory elsewhere. P6 late-binds
callbacks to the same DesktopWorldRuntime object rather than copying its state.

No real save, image/animation asset, balance value, authored dialogue or schema
was altered. The original OOP stages and dated documents remain historical;
the latest [architecture](ARCHITECTURE.md) and
[World behavior contract](WORLD_OBJECT_CONTRACTS.md) define current execution.
A manual Windows visual/input acceptance at 1x and 2x is still required before
PR #10 can be taken out of Draft; neither automated Tk nor Linux Xvfb tests
substitute for the user's live interaction check.
