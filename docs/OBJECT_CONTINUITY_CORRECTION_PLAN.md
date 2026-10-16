# Observed item continuity and knowledge-aware interaction

Approved follow-up to the completed object focus correction. Preserve care,
animation, subjective search and save compatibility. No merge is authorized.

## Contracts and ownership

Observation, learned identity and current desire are independent. Aiko can learn
an identity and develop a desire while the player holds a portion. An observed
pickup and continuously followed placement preserve the same subjective record;
two identical portions do not become one. Unobserved movement still uses bounded
subjective search and matching, never objective instance IDs as proof of knowledge.

World owns custody and motion. ObjectAwareness/ObjectTracker own sensory
continuity, ObjectMemory owns learned facts and completed assessment, and
ObjectIntentions owns the selected current wish. The interaction coordinator owns
action phases. CursorItemGesture owns input capture and current pointer pose.
Dialogue and tuning remain in the existing JSON catalogues.

An ordinary held portion is not a stolen target. Only taking the subject of an
already committed action invokes return requests, irritation and friendship
consequences. A newly expressed desire must not retroactively become theft.
Committed focus continues to exclude unrelated drops and offers.

A known identity needs no repeated identification. Recognition does not imply a
completed use assessment. Consumption always rechecks current capacity/activity.
A desire expressed for an observed offer survives its observed placement; seeking
thresholds and actual care origin are separate. Release in the handover area is
still required for human handover. Ground collection remains autonomous.

Known identity/assessment survive restart using existing memory serialization;
live tracking and current wishes remain session-only. No new save version or
parallel known-items store is needed.

## Small delivery steps

1. Record these contracts and the evidence ledger; update architectural links.
2. Establish current cursor pose before observation and generalize observed pickup
   tracking independently of committed focus. Failed capture must not create a
   pickup observation. Test continuity and loss of sight separately.
3. Keep existing recognition dwell/range for unknown held items; reuse known
   identity under continuous observation. Assess and select held wishes through
   the existing intentions owner. Separate use context from consumption origin.
4. Route known, unassessed and unknown items through the appropriate coordinator
   phases. Preserve unchecked-consumption protection and full consumption clips.
5. Preserve wishes across observed placement without theft mechanics; keep actual
   handover/ground origin and true target withholding rules. Test both paths.
6. Align authored cues with first identification, desire, known acceptance and
   actual return. Keep the existing identified feedback player and JSON variants.
7. Verify paired save/restart, native 1x/2x cursor flows, targeted regressions,
   complete suite and final CI. Update practical retest instructions and evidence.

Split steps further when an independently green boundary is useful. Run targeted
tests during development plus Ruff, strict Mypy and Pyright. Run the complete
local suite only at the end. Push each green commit, monitor preceding CI runs,
and stop implementation to repair a red run. Preserve unrelated local work and
real saves; use temporary test saves only.

## Evidence ledger

- Baseline: `8e9374d`, clean checkout on `feature/world-foundation`.
- Baseline diagnosis: ordinary pickup calls `follow_taken` only if
  `target_taken` succeeds; awareness stops following without committed focus;
  offer assessment requires a new recognized observation; known but unassessed
  coordinator routing repeats identification; handover text mixes known and
  unknown cases. Current wishes are limited to resting portions.
- Implementation and verification evidence will be recorded below.
- Step 1: `42789e3` records this approved plan and its architecture link.
- Step 2: ordinary observed pickup and held-item tracking survive without a
  committed action; settlement releases the cursor lock. Capture establishes
  current pointer pose before save/view/observation. Verified 10 awareness tests,
  23 native World GUI tests (including 1x/2x focus resumption), Ruff, strict Mypy
  (178 sources) and Pyright. Tk emits teardown ThemeChanged diagnostics in the
  existing GUI fixture; all assertions pass.
