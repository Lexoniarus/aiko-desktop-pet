# Object perception: noticing, identifying and assessing

Status: implementation authorized; delivery evidence is recorded below.
Recorded: 17 October 2026.
Code baseline: `86c3bce` on `feature/world-foundation`.

This is the next delivery plan after the implemented
[continuity correction](OBJECT_CONTINUITY_CORRECTION_PLAN.md). It tightens the
perception contracts below without discarding observed continuity, subjective
search, care origin, safe interruption or persistent knowledge. It supersedes
earlier assumptions that attentive proximity alone permits identification.
Current implementation ownership is described in [ARCHITECTURE.md](ARCHITECTURE.md).

## Three distinct knowledge levels

Use **bemerken / notice**, **identifizieren / identify**, and **beurteilen / assess**
consistently in contracts, interfaces, tests, events and authored dialogue.
Avoid the ambiguous German word "erkennen" where it could mean either noticing
presence or identifying a type.

| Level | Subjective knowledge | Permitted consequence |
|---|---|---|
| Noticed / bemerkt | "There is an item at this place." Identity and food/drink kind can still be unknown. | Follow its observed movement, become curious, investigate, or notice its absence. |
| Identified / identifiziert | "This portion is an Energy Drink." | Retain its learned identity and consider its actual use. Identification alone is no consumption wish. |
| Assessed / beurteilt | "I want this now" or "I do not need this now." | Select or decline use under current need/activity/capacity rules. A previous assessment is not a permanent wish. |

World existence is not subjective notice. Notice is not identification. Wanting
to investigate an unknown item is not wanting to consume it. Custody is another
independent dimension: a noticed, identified or assessed portion can be on the
ground, held by the player, moving, or held by Aiko.

Reuse the existing representation where it expresses these facts:
`ObjectObservation`/`ObjectKnowledge` can have no identity or kind;
`ObjectKnowledge.recognized` currently means **identified**, and `assessed` records
a completed assessment. `ObjectIntentions.goal` owns the current selected wish.
Do not introduce a parallel knowledge enum, inventory or persisted wanted flag.
Existing `recognize`/`recognize_offer` phases and `object_recognized` events must
be explicitly understood as identification, not presence detection. Rename only
where needed to remove real ambiguity; preserve save compatibility.

## Identification and presentation rules

| Situation | Notice and tracking | First identification |
|---|---|---|
| Unknown resting item | Allowed with attention, range and notice time. | Forbidden while it lies on the ground. |
| Unknown falling/bouncing item | Allowed when actually observable. | Forbidden merely from observing its motion. |
| Unknown player-held item outside a deliberate presentation | Allowed when observable. | Forbidden, including prolonged carrying or a quick pass near Aiko. |
| Unknown item deliberately presented before her face | Allowed. | Allowed after continuous attentive presentation time. |
| Unknown item acquired by Aiko | Own acquisition remains confirmed at source frame 4. | Allowed during the subsequent actual hand inspection, after pickup reaches its safe pose. |
| Previously identified portion | Existing knowledge survives valid observed continuity. | Do not repeat first identification. A new offer still requires deliberate presentation before offer assessment/feedback. |

Deliberate presentation uses the displayed item's position, including its pivot,
relative to Aiko's existing eye/face reference. The supported display, current
attention and committed subject still constrain eligibility. No second character
position, independent cursor cognition, or World-derived identity shortcut is added.

Presentation requires a moment of holding in the face area. Small hand jitter is
allowed; moving past the face is not equivalent to holding an offer. Leaving the
area before completion or losing eligible attention interrupts progress. Do not
accumulate several brief passes or time spent outside the area.

Completed presentation is session-local evidence for the same continuously
observed gesture/portion. It remains valid when moving from the face to the
handover area, so the player does not have to present it again before release.
A new gesture or genuine loss of continuity invalidates presentation evidence,
not previously learned identity. The offer can be reappraised if need changes.

Notice range, presentation area and release/handover area are distinct. First
identification, assessment and their bubbles transfer no custody and apply no
nutrition. Human handover remains conditional on actual release, willingness,
capacity and the valid handover area. Ground collection remains autonomous.

Known wishes, true withholding and the recently corrected player-held
identification/decision path remain intact. `recognize_offer`/`decide_offer` may
announce knowledge and willingness only after the required presentation evidence;
`await_return` must not bypass that evidence. Refusal ends that episode's return
demands and further withholding effects, while retaining learned knowledge.

## Absence and attention priority

Absence can be noticed even if the item was never identified:
"Da lag doch etwas" requires only previous notice. A named absence such as
"Hier lag mein Energy Drink" requires learned identity.

- Check remembered places that are currently within eligible attention and
  observation coverage; do not infer absence from invisible World mutations,
  missing instance handles, or a single absent tracking sample.
- Require local observation time and account for raw candidates not yet noticed.
  A pending notice, gap, screen boundary or distraction is not confirmed emptiness.
- Resolve observed pickup, continued cursor tracking, own acquisition/placement,
  and consumption before claiming unexplained loss. If Aiko watched the take,
  she knows the player took it. Own expected custody changes are not lost stock.
- Confirmed absence takes priority over new discoveries and ordinary offers at
  the next eligible behavior decision. Preserve the existing committed focus:
  while investigating one subject, unrelated places do not enter perception;
  check them when attention becomes available. Explicit commands and safe
  custody/animation completion retain their established ordering.
- Use the existing `remembered`/`missing` memory states and one identified
  reaction per new absence. Do not repeatedly rediscover the same missing item.
  Separate early absence feedback from the final outcome of unsuccessful search.
- A missing active target can enter existing bounded search without first
  walking to a place already confirmed empty. Merely noticing a missing reserve
  does not require an endless or unconditional search. Reuse the coordinator's
  sole search budget and the existing stock/count reconciliation.

The same place is not proof of the same portion after confirmed absence. Review
`match_find`/`observe_find` as well as the recognizer: a new unclassified find must
not inherit a missing portion's identity just because their locations coincide.
Preserve confirmed continuity and supported remembered-stock recovery across
restart. Keep uncertain associations subjective; technical World IDs must not
resolve them. Two identical portions remain distinct.

## Responsibility boundaries

- **World:** concrete portions, objective custody, revisions and motion. It does
  not decide what Aiko notices, identifies or wants.
- **Desktop geometry/input:** existing eye reference, displayed item geometry,
  supported area, capture and actual release. It supplies observation inputs.
- **ObjectAwareness / ObjectPerception / ObjectTracker:** eligible observations,
  continuous presence/identity evidence, presentation progress/confirmation,
  observed continuity and confirmed empty-place evidence. Pure policies receive
  typed context, without importing Tk, desktop APIs or World state enums.
- **ObjectMemory / object_stock:** learned facts, checked place status and
  subjective association/count uncertainty. Memory does not poll World truth.
- **ObjectIntentions and existing use policy:** investigation versus consumption
  goals, current need decisions and preserved wishes. No duplicate goal store.
- **Interaction coordinator:** ordered action phases, absence priority and
  feedback receipts, existing search, withholding, custody and consumption flows.
  Use the existing feedback presenter/player rather than another bubble queue.
- **Existing JSON catalogues:** validated tuning and authored wording appropriate
  to noticing, identification, assessment, observed taking and unexplained absence.

## Small implementation stages

Every implementation commit must remain independently green. Keep a contract
change with its producer/consumer updates when separating them would break the
running application. Split a stage further only at a usable green boundary.

| Stage | Work and owner | Required evidence |
|---|---|---|
| 1. Contracts and regression expectations | Record the three knowledge levels and custody/presentation matrix. Identify existing tests that incorrectly require ground identification. | Tests and wording distinguish unknown presence, learned identity, prior assessment and current desire. |
| 2. Separate geometry and tuning | Reuse the eye reference through the desktop adapter. Define broader noticing, face presentation and handover areas separately; validate timing, bounds and movement tolerance in the existing balance catalogue. | Geometry at 1x/2x, pivots, supported screen edges and all configuration validation. |
| 3. Gate first identification | Carry explicit observation/inspection context through awareness into perception. Enable unknown-item identification only for valid presentation or actual pet-hand inspection. Update affected fixtures with the correct context. | Unknown ground/moving items stay unidentified; pickup frame 4 alone does not identify; actual inspection can identify. |
| 4. Gate offers and preserve continuity | Require presentation evidence for new offer assessment/readiness, including already known items. Preserve completed presentation through the observed face-to-hand movement and keep known identity independently. | Passing, carrying far away, leaving early and repeated brief passes fail; deliberate presentation succeeds; known targets skip repeated identification; release remains mandatory. |
| 5. Harden memory association | Check existing matching and stock reconciliation against the stricter identification gate and confirmed absence. Preserve genuine observed identity through take/drop/restart. | A new find at a confirmed empty place stays unknown; hidden moves, identical portions and prior known reserves remain correctly distinguished. |
| 6. Observe empty known places | Add typed local negative evidence with attention, coverage and dwell. Apply existing missing-place semantics without omniscient World polling. | Previously noticed unknown items can go missing; unnoticed occupants, gaps, boundaries, own actions and closed time cannot create false absence. |
| 7. Integrate priority and dialogue | Feed confirmed absence into the coordinator before new discovery/offer decisions. Reuse bounded search, identified feedback and JSON dialogue; distinguish first loss from failed search. | One correctly worded loss reaction; early search for a missing target; no repeated loss, duplicate search budgets or disruption by unrelated changes during committed focus. |
| 8. Combined verification and practical handoff | Consolidate affected expectations and extend focused regression cases. Run final full verification and prepare an isolated practical checklist. | Food/drink; unknown/known; ordinary/withheld offers; deliberate presentation; take/drop/hops; real visual loss; 1x/2x; stale receipts; restart and existing care/animation rules. |

Proposed calibration starting points, not measured final values: increase notice
range from three to six character widths and use about one active second for
deliberate presentation. Calibrate face bounds and allowed jitter separately at
both scales; do not enlarge walking/grasp/handover reach as a side effect.
Retain the existing hand-inspection timing unless practical evidence requires a
separate agreed adjustment. No new values belong in ad hoc UI conditions.

## Verification, saves and delivery limits

During implementation, run targeted behavior tests plus Ruff, strict Mypy and
Pyright. Adapt existing perception/awareness/memory/stock/retrieval/reaction tests
and the native World tests; avoid a duplicate heavy end-to-end matrix. Retain
necessary real-timer reading/animation coverage. Run the complete local suite at
the end. Commit/push green steps and monitor CI; repair a red run before continuing.

Preserve durable identity and completed assessment. Presentation clocks,
visibility, current wishes and action phases remain session-local. No new save
version is planned; validate that against the final implementation contract.
Existing saves do not record how identity was originally learned, so they cannot
reliably distinguish old premature ground identification from valid knowledge.
Do not silently erase that knowledge or reset real saves. Practical acceptance
must include a fresh isolated profile plus a separate known-stock restart case.

## Delivery evidence

- Stage 1: recorded the approved three-level contracts, ownership, state matrix
  and eight delivery stages. Baseline `86c3bce`; only the three expected planning
  documents were uncommitted. Implementation was subsequently authorized.
- Each following entry records the actual checks and commit evidence. Earlier
  delivery evidence remains in the continuity plan; PR #10 remains unmerged.
- Stage 1 commit: `f035b1d`.
- Stage 2: wider noticing and validated presentation timing/face bounds/jitter
  are in the existing JSON catalogue. Displayed item-center geometry reuses the
  eye reference and normalizes scale/pivots without changing grasp or walking
  reach. Verified 31 targeted geometry, configuration, perception, awareness and
  reach tests; Ruff, strict Mypy and Pyright pass. Presentation enforcement follows
  with the producer/consumer update in stages 3-4.
