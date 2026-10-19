# Friendship balance proposal

> **Planning update, 2026-10-19:** The latest curve and combined care examples
> are the baseline for the [active care/time implementation plan](CARE_TIME_IMPLEMENTATION_PLAN.md).
> Earlier alternatives and discussion-status disclaimers below remain historical
> context. Implementation and the bounded remaining decisions are still pending.

> **Discussion proposal only — no implementation approval.** Recorded on
> 2026-10-19 on `feature/social-optimization`, from code baseline `b519da4`.
> Expanded on the same date with progressive upkeep and timed neglect rules.
> The latest revision adds shared reward ceilings, a gentler lower upkeep curve
> and repeated-day comparisons; earlier factors/examples are marked separately.
> The owner requested preservation of these candidate values. These values are
> not shipped settings, an accepted final
> specification or evidence of playtested balance. Runtime code, JSON balance,
> save formats and dialogue remain unchanged.

Related references: [social and entertainment concept](SOCIAL_ENTERTAINMENT_CONCEPT.md),
[dialogue review workbook](DIALOGUE_REVIEW.md),
[need balance and example day](NEEDS_BALANCE_PROPOSAL.md),
[adaptive sleep proposal](ADAPTIVE_SLEEP_PROPOSAL.md),
[current fun/mood rules](FUN_MOOD_SYSTEM.md),
[current data and time behavior](DATA_AND_SAVES.md) and
[current architecture](ARCHITECTURE.md).

## Product direction established in discussion

- Friendship represents the long-term relationship with the interacting person;
  the cursor is the person's observable means of contact.
- A high relationship level should require sustained, regular care. Absence
  should cause visible consequences and loss of relationship levels.
- Level 10 is the demanding peak, compatible with normal human sleep and
  everyday life. Average good care should support a good relationship around
  levels 7–8. Level 9 remains close; crossing below level 10 is not itself an
  offended-return trigger. There is no mandatory hourly interaction schedule.
- Regular morning/evening care should be able to maintain a smaller relationship
  instead of inevitably reaching zero. This is a balance target under adequate
  actual care, not a protected minimum despite neglect or negative actions.
- Real time continues while the application is open, closed or the computer is
  suspended. The proposed relationship loss must not inherit the current
  eight-hour closed-time reconstruction limit.
- Needs may reach zero. Aiko does not die. Available resources and later care
  can improve her condition, but reopening the application does not reset it.
- Autonomous care uses only actual available desktop resources. Consumption
  must be reflected in the remaining stock and saved state, without fabricated
  replacement supplies or duplicate use.
- Later consumable objects may partially satisfy fun, social or affection
  needs. Autonomous use does not manufacture human interaction or friendship
  gains, and does not stop contact-related friendship loss.
- Moodlets with stacking remain a later, separately specified mechanism.
  Hardware utilization is excluded from that proposed social-Moodlet reasoning.
  This does not approve changing all existing hardware/energy rules.

These directions establish the intended experience. The numeric tables below
are the candidate balance requested for documentation, not approved changes.

## Relationship scale and current implementation baseline

The current durable friendship scale is 0–100. Display level is
`min(10, 1 + floor(friendship / 10))`, so level 10 starts at 90 points. The
current starting value is 15 (level 2). This proposal retains those values
for its examples; it does not add another relationship scale.

Current production rules in [friendship.py](../aiko_pet/pet/friendship.py)
award food 0.9, play 1.0, petting 1.0 and talking 1.0, subject to a pre-care
need threshold of 80, a 720-second per-action interval, a five-point calendar-day
cap and a 0.35 variety bonus. Energy drinks and sleep do not award friendship.
Completed play is coordinated through the existing game-experience owner;
autonomous consumption does not receive human care credit.

Current [withholding](../aiko_pet/pet/mind/object_withholding.py) and
[relationship coordination](../aiko_pet/application/object_relationship.py)
allow bounded losses, with 0.15 as the configured loss amount, a 0.6 episode
allowance and additional episode/cross-episode timing rules. Current production
has no friendship decay caused by elapsed time without contact, and repeated
clicking changes temporary irritation rather than friendship.

## Proposed gains from personal care

These are friendship points, not changes to satiety, energy, fun, social or
affection. Need-replenishment candidates are recorded in the separate
[need balance proposal](NEEDS_BALANCE_PROPOSAL.md).

| Interaction | Nominal candidate gain before shared ceilings | Qualification |
| --- | --- | --- |
| Personally handed-over food | +0.9 | Actually accepted and consumed; not merely placing a portion nearby |
| Personally handed-over energy drink | +0.25 | Actually accepted and used |
| Talking | +1.0 | Accepted conversation interaction |
| Petting | +1.0 | Accepted affection interaction |
| Playing together | +1.0 per session | At least two completed rounds; victory/defeat does not determine friendship gain |
| Sleep, wake, ordinary UI operation | 0 | No independent relationship reward |
| Autonomous resource use | 0 | Need fulfillment without fabricated personal care |

Proposed limits and qualification rules:

- At most **+0.75 friendship within any rolling two-hour interval**, shared
  across all care types. Bundling several actions into one visit still helps
  needs, but does not award a large relationship increase all at once.
- At most **+5 friendship within any rolling 24-hour interval**. This latest
  candidate resolves the earlier rolling-versus-calendar question in favor of
  rolling time; it differs from the current calendar-day runtime rule.
- The same care type receives its full gain at most **once per two hours**.
  The exact handling of intervening repetitions remains open.
- If the corresponding need is already **above 80**, award **25%** of the gain.
  Accepted relationship contact can matter without an urgent need.
- The shared ceilings limit actual credited gains after ordinary qualification
  and reductions. They are not guaranteed awards per visit or per time window.
- Rejected, unperformed or repeatedly clicked commands are not multiple care
  events. Consumed portions, completed rounds and genuine accepted interaction
  remain authoritative.
- A valid personal-care interaction still counts as care contact when its
  reward limit is exhausted. Reward eligibility and contact accounting are
  distinct questions.

The earlier baseline's variety bonus is recorded above for comparison. Its
retention or replacement has not been decided by this proposal; it must not
bypass the new shared ceilings. The old uncapped-per-visit +5/day comparison
is superseded by the shared two-hour ceiling.

The temporary suggestion of awarding friendship only after every need reaches
40 was withdrawn. A positive interaction can count while another need is low;
the neglect rules below address persistent poor care separately.

## Proposed loss during absence

Measure real elapsed time since the last **valid personal-care interaction**.
Merely starting the application, pointer hover, ordinary UI operation and
annoying Aiko do not renew that care-contact interval. Autonomous feeding,
sleep and later self-entertainment do not renew it either.

| Time without qualifying care | Reference loss rate before progressive scaling |
| --- | --- |
| First 4 hours | 0 points/hour |
| After 4 through 12 hours | 0.5 points/hour |
| After 12 through 24 hours | 1 point/hour |
| After 24 through 48 hours | 1.5 points/hour |
| After 48 hours | 2 points/hour |

These are the original **reference** rates. The later progressive factor below
scales their instantaneous effect. Rates apply **piecewise and continuously**,
not retroactively at the newest rate to the entire absence. For elapsed hours
`h >= 0`, the original unscaled total loss is:

```text
0.5 * max(0, min(h, 12) - 4)
+ 1.0 * max(0, min(h, 24) - 12)
+ 1.5 * max(0, min(h, 48) - 24)
+ 2.0 * max(0, h - 48)
```

Friendship remains bounded to 0–100. The complete absence is considered;
loss does not stop after eight hours. Sleep and computer suspension are
included in this candidate real-time contact interval; the four-hour grace
period is its proposed initial allowance, not an additional overnight pause.
The briefly discussed one-hour grace period was withdrawn; four hours remains
the candidate. Sleep does not stop the contact clock.

An accepted new care interaction ends the current contact gap and begins a
new one. Its ordinary gain does not refund all losses or restore old levels.
Exact persistence, clock-correction handling and first-session anchoring are
future implementation decisions.

### Original unscaled illustration from 95 friendship points

This preserves the first discussion's arithmetic **without the later
progressive factor** and without neglect or direct-action losses. It is not
the predicted trajectory of the expanded proposal, whose loss softens as the
relationship falls.

| Absence | Unclamped total loss | Remaining points | Display level |
| --- | --- | --- | --- |
| 4 hours | 0 | 95 | 10 |
| 8 hours | 2 | 93 | 10 |
| 12 hours | 4 | 91 | 10 |
| 18 hours | 10 | 85 | 9 |
| 24 hours | 16 | 79 | 8 |
| 36 hours | 34 | 61 | 7 |
| 48 hours | 52 | 43 | 5 |
| 72 hours | 100 | 0 | 1 |

The original unscaled tuning could erase even a maximal numeric relationship
within three days. That historical consequence is not a claim for the later
progressively scaled design or approval of either tuning.

### Original unscaled progression examples

Assume the full proposed +5 budget is earned every day, no other negative
events, daytime contact gaps of at most four hours, and one uninterrupted
overnight contact gap per day:

| Nightly care gap | Absence loss per night | Maximum net daily gain | Approximate 15-to-90 progression |
| --- | --- | --- | --- |
| 8 hours | 2 | 3 | 25 days |
| 10 hours | 3 | 2 | 37.5 days, approximately 38 |
| 12 hours | 4 | 1 | 75 days |

These are arithmetic illustrations of the proposed rates, not results from
an integrated simulation, verified daily schedules or practical playtests.
Thresholds, reward budgets and contact qualification can change feasibility.
They also precede the progressive factor and shared two-hour reward ceiling;
25/38/75 days must not be presented as the expanded proposal's verified
leveling times or feasibility for those overnight care gaps.

## Proposed progressive relationship upkeep

Keep one 0–100 friendship scale and the existing display-level mapping.
Progression here means rising maintenance demands rather than a new XP bar
or a newly approved level-threshold table. Apply this factor to passive
absence/neglect loss, with continuous linear interpolation between anchors:

| Current friendship | Display level | Passive-loss factor |
| --- | --- | --- |
| 0 | 1 | 0.05 |
| 35 | 4 | 0.15 |
| 50 | 6 | 0.35 |
| 70 | 8 | 0.75 |
| 90 through 100 | 10 | 2.00 |

Interpolate between the anchors at 0, 35, 50, 70 and 90; keep 2.00 from 90
through 100. Reevaluate from current friendship as time progresses; crossing
a display level does not create a rate jump. At zero, 0.05 is a loss-rate
factor, not an award or a positive minimum friendship value.
The +0.75/two-hour and +5/24-hour gain ceilings are not multiplied by this upkeep
factor. This proposal does not additionally scale the separately bounded
clicking/withholding losses.

This replaces the earlier anchors (15: 0.25, 45: 0.50, 70: 0.75, 95: 1.00).
An intermediate stricter lower curve could push morning/evening care to zero;
that result is explicitly superseded by the gentler lower anchors above.
The more demanding upper factor of 2.00 from 90 remains part of the latest
comparison, not the old factor of 1.00 at high friendship.

The target experience is attentive distributed care for level 10, average good
care maintaining approximately levels 7–8, and gradual changes across weaker
days. This is an intended outcome, not a guarantee for every schedule.

For contacts at 07:00, 13:00, 19:00 and 23:00, the two six-hour gaps cost one
reference point each, the four-hour gap costs zero and the eight-hour night
costs two: four in total. Around 70 friendship, 0.75 gives approximately three
points of loss. If actual care earns +3, that is approximately maintenance;
the shared two-hour ceiling now makes +3 the maximum for those four visits.
At level 10 the reference four-point loss is multiplied by 2, giving up to
eight before factor changes, so +3 no longer maintains that level. The factor
changes during the day; these are explanations, not exact fixed-factor paths.

See the [eight-period high-care day](NEEDS_BALANCE_PROPOSAL.md) for the
corresponding need values and a feasible eight-hour night without energy drinks.

## Latest daily friendship comparisons

The following isolates friendship upkeep. All schedules use valid personal
care at the listed times, with an eight-hour 23:00–07:00 overnight contact gap.
Every care visit still renews valid contact if its reward budget is exhausted.
It is not merely opening the app or clicking Aiko.

### Calculation assumptions

- Use the latest piecewise-linear factor above and the existing proposed
  reference absence-rate intervals, continuously updating from current points.
- Assume enough qualified, accepted care to earn up to 0.75 at each visit,
  subject to the shared rolling two-hour and 24-hour ceilings. All listed
  visits are at least two hours apart. These are earned-gain upper scenarios,
  not guaranteed gains from one arbitrary action or automatic rewards for time.
- Exclude neglect, clicking/withholding losses and autonomous friendship gains.
  This is not a simulation of need satisfaction, item availability, sleep
  decisions, workload, dialogue or Moodlets. Those can alter real feasibility.
- Integrate passive loss in one-minute intervals. For the first-day column,
  start at 95 immediately before 07:00 care with no previous rewards using the
  budget, and finish before the next 07:00 care. Repeat the schedule for 540
  days to illustrate the settled within-day range, clamping friendship to 0–100.

| Care pattern and times | Maximum credited gain per 24 hours | Reference absence loss before factor | First-day change from 95 | Approximate repeated-day range | Display level in that range |
| --- | --- | --- | --- | --- | --- |
| Eight: 07:00, 09:30, 12:00, 14:30, 17:00, 19:00, 21:00, 23:00 | +5.00 | 2 | +1.00 | 96–100 | 10 |
| Six: 07:00, 10:00, 13:00, 16:00, 19:00, 23:00 | +4.50 | 2 | +0.50 | 96–100 | 10 |
| Five: 07:00, 11:00, 15:00, 19:00, 23:00 | +3.75 | 2 | -0.25 | 86.2–89.9 | 9 |
| Four: 07:00, 13:00, 19:00, 23:00 | +3.00 | 4 | -5.00 | 69.2–70.8 | 7–8 |
| Three: 07:00, 15:00, 23:00 | +2.25 | 6 | -9.39 | 50.9–51.6 | 6 |
| Two: 07:00 and 23:00 | +1.50 | 10 | -15.84 | 34.2–35.4 | 4 |

These are numerical discussion illustrations, not production-policy tests,
playtested balance or exact analytic equilibria. The first-day drop remains
large for a previously close relationship with sparse care, but lower-level
upkeep becomes milder as the relationship settles. Less actual reward or
additional negative influences can lower these ranges.

### Why morning/evening care can sustain a smaller relationship

Two fully rewarded care visits can earn 2 * 0.75 = 1.5. Their 16-hour daytime
and eight-hour overnight gaps cost 8 + 2 = 10 reference points. Around 35
friendship, factor 0.15 makes that approximately 1.5, explaining the smaller
relationship's maintenance point. Starting from the existing 15 points, the
same simplified schedule also builds toward this range (about +0.56 on its
first day), rather than only preserving a previously acquired level.

Level 4 is not a guaranteed floor. Without continued adequate care, or with
neglect/annoyance, points can fall further. The factor at zero neither restores
points nor cancels losses. The intended outcome is a maintainable smaller
relationship, not immunity from consequences.

### Why distributed care matters at the upper end

Near level 10, an eight-hour contact gap now costs two reference points times
factor 2, approximately four actual points; it is not the old two-point night.
Six to eight adequately rewarded visits can cover that cost. Five visits can
earn only 3.75, making permanently holding level 10 harder; four are bounded
to +3 and settle near levels 7–8 under the isolated assumptions above.

The earlier lower-curve comparison placing three visits near 30 and two visits
near zero is superseded. Only the latest gentler table should be used when
discussing the current candidate daily outcomes.

The later [combined example day](NEEDS_BALANCE_PROPOSAL.md#combined-example-day-with-needs-mood-sleep-and-friendship)
checks the eight-period schedule against individual pre-care need values and
actual rolling reward allowances. In that normal-care model, the listed actions
do earn +5, with no neglect and four overnight points lost: 95 before morning
care, 100 by evening and 96 the next morning. Other rows above still represent
isolated maximum-gain comparisons, not full need/acceptance simulations.

## Proposed sustained-neglect rules

Evaluate each need separately using its actual history over the **preceding
24 real hours**. Time at zero also counts as time below 25. Disjoint critical
periods accumulate; partial refills and new personal contact do not erase
earlier periods while they remain inside the window.

| Need history/state | When neglect loss becomes eligible |
| --- | --- |
| Current value at least 25 | No ongoing neglect deduction |
| Current value below 25 | After two accumulated hours below 25 in the preceding 24 hours |
| Current value exactly zero | After one accumulated hour at zero in the preceding 24 hours |
| At least six accumulated hours below 25 in the preceding 24 hours | Stronger rate while currently critical |

The zero-state allowance can end before the two-hour critical allowance. No
loss is retroactively charged for either initial allowance. For eligible needs:

| Current state | Reference friendship loss per real hour |
| --- | --- |
| Above zero and below 25 | 0.25 |
| Zero | 0.50 |
| Above zero and below 25, with at least six critical hours in the window | 0.50 |
| Zero, with at least six critical hours in the window | 1.00 |

Use the strongest eligible need rate, **not their sum**. At 25 or higher,
that need stops charging immediately, although its prior critical time remains
in the rolling window. Restored needs do not refund lost relationship points.
As old periods leave the window, eligibility and escalation can subside.

Actual restorative sleep is care for energy: while energy is increasing during
sleep, do not accumulate further energy-neglect time or charge energy-neglect
loss. That does not erase earlier history, generate friendship or stop the
absence clock. Other unmet needs still advance over real time while asleep.
Computer standby or closing the app alone is not evidence of restorative sleep.

Talking does not repair hunger; unrelated contact cannot end another need's
neglect. A genuinely available and consumed resource can improve its need and
stop its deduction, without manufacturing personal contact or relationship gains.

### Overlap with absence

For each chronological time interval, select the **higher** of the reference
absence rate and the strongest eligible reference neglect rate, then apply the
progressive factor **once**:

```text
passive_loss_rate = friendship_factor(current_friendship)
                    * max(absence_rate, strongest_neglect_rate)
```

This avoids adding two full passive penalties for the same extended absence.
It is not the maximum of cumulative totals computed afterward: whichever
rate is stronger can change during the interval. Direct negative actions keep
their own bounded episode rules; they do not replace passive loss.

### Neglect arithmetic examples

These isolate neglect, assume no stronger absence rate and no prior critical
history in the window, and show **unscaled reference** losses. They are not
high-level actual losses: the latest factor is 2 at level 10 and lower below
that. Apply it once after choosing the stronger passive rate; a changing factor
also changes the actual trajectory.

| Need history | Reference neglect loss |
| --- | --- |
| One 45-minute period below 25, then care | 0 |
| Three accumulated hours below 25, never zero | 0.25 |
| Two hours continuously at zero | 0.50 |
| Eight hours continuously at zero | 4.50 |

For the last example: hour 0–1 is free, hours 1–6 cost 5 * 0.5 = 2.5, and
hours 6–8 cost 2 * 1 = 2, totaling 4.5. Two separate 90-minute nonzero critical
periods also total three critical hours, with one chargeable hour at 0.25.
Short deficits can therefore remain manageable, while repeated or prolonged
neglect can outweigh the maximum daily care gain.

Long-term emotional memories, stacking Moodlets and their text/expression
effects remain separate design work. This section defines numeric candidates.

## Proposed losses from direct actions

| Action | Candidate relationship consequence |
| --- | --- |
| Escalated direct clicking after a clear boundary response | -0.25 per qualifying escalation; continued annoyance can reach -1 per minute |
| Repeatedly taking a claimed object, or holding it away longer | Initial -0.5, then another -0.5 per 30 seconds while withholding continues; at most -2 within two minutes |
| Returning the object | Ends further withholding losses; no automatic gain/refund |
| Winning a game against Aiko | No friendship loss |

Reading clicks that advance a story and ordinary control operation are excluded
from annoying clicks. The exact escalation thresholds, initial withholding
duration, episode boundaries and rate-limit windows remain to be defined.
Do not mistake the current production thresholds for approved new thresholds.

Losses must follow actual interaction evidence. Picking up an unrelated
desktop object is not automatically the same as taking a subject Aiko claims.
Different handlers must not charge the same event twice.

## Visible consequences and unmet needs

On return after an absence, dialogue and expression should reflect both the
elapsed absence and the remaining relationship. Selecting a less-familiar
generic line solely because the numeric level dropped is not enough to express
the requested visibly offended response.

One care action stops the increasing contact gap, but does not instantly
restore the previous relationship or erase the return reaction. Exact wording,
reaction duration, relation to later Moodlets and recovery behavior remain open.

Available resources can sustain needs during absence. Once they are used up,
needs may reach zero. There is no death, automatic reset or hidden free supply.
Need deficits influence overall condition/mood. The sustained-neglect section
now records candidate timing, losses and overlap with absence; it does not add
generic hunger/fatigue Moodlets or authorize runtime changes.

## Open questions before implementation

- Confirm or revise gains, grace periods, progressive factors and neglect
  thresholds. Recalculate long absences with the expanded model; the original
  unscaled three-day consequence is not its current predicted trajectory.
- Define accepted relationship contact precisely, including abbreviated play,
  interrupted conversations, personal handovers and reward-limited care.
- Resolve same-type repetition inside two hours, reduced-gain ordering and the
  former variety bonus within the shared ceilings. Rolling two-hour and 24-hour
  budget windows are the latest candidate, not an open calendar-day alternative.
- Validate the latest daily comparisons against actual accepted care, need
  trajectories, sleep and combined neglect; they currently bound credited
  gains rather than proving all schedules supply every need adequately.
- Define clicking/withholding episodes and their exact loss-rate limits.
- Specify durable time accounting, idempotence, restart/suspend reconstruction
  and normal clock corrections without creating a second friendship owner.
- Specify bounded history for rolling critical/zero durations, first-load
  behavior when history is unavailable, and chronological combination of
  factor changes, history expiry, care and restorative sleep. Do not invent
  past neglect without evidence.
- Define offended return behavior and its recovery separately from numeric
  friendship; the Moodlet catalogue and mood balance are not settled here.

Overall mood balance is recorded separately in the later
[mood balance proposal](MOOD_BALANCE_PROPOSAL.md), also without implementation
approval. No code, runtime resource, schema or editorial review status changes
as part of this record.
