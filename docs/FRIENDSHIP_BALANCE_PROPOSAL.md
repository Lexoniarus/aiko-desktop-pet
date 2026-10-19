# Friendship balance proposal

> **Discussion proposal only — no implementation approval.** Recorded on
> 2026-10-19 on `feature/social-optimization`, from code baseline `b519da4`.
> Expanded on the same date with progressive upkeep and timed neglect rules.
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

| Interaction | Candidate gain | Qualification |
| --- | --- | --- |
| Personally handed-over food | +0.9 | Actually accepted and consumed; not merely placing a portion nearby |
| Personally handed-over energy drink | +0.25 | Actually accepted and used |
| Talking | +1.0 | Accepted conversation interaction |
| Petting | +1.0 | Accepted affection interaction |
| Playing together | +1.0 per session | At least two completed rounds; victory/defeat does not determine friendship gain |
| Sleep, wake, ordinary UI operation | 0 | No independent relationship reward |
| Autonomous resource use | 0 | Need fulfillment without fabricated personal care |

Proposed limits and qualification rules:

- At most **+5 friendship within 24 hours**. Whether the budget is a rolling
  interval or another real-time accounting scheme remains to be settled; it
  must not be silently confused with the current calendar-day rule.
- The same care type receives its full gain at most **once per two hours**.
  The exact handling of intervening repetitions remains open.
- If the corresponding need is already **above 80**, award **25%** of the gain.
  Accepted relationship contact can matter without an urgent need.
- Rejected, unperformed or repeatedly clicked commands are not multiple care
  events. Consumed portions, completed rounds and genuine accepted interaction
  remain authoritative.
- A valid personal-care interaction still counts as care contact when its
  reward limit is exhausted. Reward eligibility and contact accounting are
  distinct questions.

The earlier baseline's variety bonus is recorded above for comparison. Its
retention or replacement has not been decided by this proposal.

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
They also precede the progressive factor; 25/38/75 days must not be presented
as the expanded proposal's verified leveling times.

## Proposed progressive relationship upkeep

Keep one 0–100 friendship scale and the existing display-level mapping.
Progression here means rising maintenance demands rather than a new XP bar
or a newly approved level-threshold table. Apply this factor to passive
absence/neglect loss, with continuous linear interpolation between anchors:

| Current friendship | Display level | Passive-loss factor |
| --- | --- | --- |
| 15 | 2 | 0.25 |
| 45 | 5 | 0.50 |
| 70 | 8 | 0.75 |
| 95 | 10 | 1.00 |

Use 0.25 below 15 and 1.00 above 95. Reevaluate from current friendship as
time progresses; crossing a display level does not create a rate jump.
The +5 care-gain budget is not multiplied by this upkeep factor. This proposal
does not additionally scale the separately bounded clicking/withholding losses.

The target experience is attentive distributed care for level 10, average good
care maintaining approximately levels 7–8, and gradual changes across weaker
days. This is an intended outcome, not a guarantee for every schedule.

For contacts at 07:00, 13:00, 19:00 and 23:00, the two six-hour gaps cost one
reference point each, the four-hour gap costs zero and the eight-hour night
costs two: four in total. Around 70 friendship, 0.75 gives approximately three
points of loss. If actual care earns +3, that is approximately maintenance;
near level 10 the same care slowly loses ground. The factor changes during
the day, so these are explanatory estimates rather than exact equilibria.

See the [eight-period high-care day](NEEDS_BALANCE_PROPOSAL.md) for the
corresponding need values and a feasible eight-hour night without energy drinks.

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

These isolate neglect, assume no stronger absence rate, no prior critical
history in the window and an unscaled reference factor of 1. They are not
exact changing-friendship trajectories.

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
- Resolve reward-budget windows, repeat handling, reduced-gain ordering and
  the former variety bonus.
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
