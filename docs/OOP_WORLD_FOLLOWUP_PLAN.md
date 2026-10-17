# Focused World OOP cleanup — delivery plan

Recorded: 17 October 2026.
Baseline: `d12c5a1e5eb9` on `feature/world-foundation`.
Status: implementation in progress; manual native World acceptance open.
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
