# Mood balance proposal

> **Planning update, 2026-10-19:** The latest discussed model is the baseline
> for the [active care/time implementation plan](CARE_TIME_IMPLEMENTATION_PLAN.md).
> Original discussion-status disclaimers below remain historical context;
> this documentation update does not implement the model.

> **Discussion proposal only — no implementation approval.** Recorded on
> 2026-10-19 on `feature/social-optimization`, alongside code baseline `b190694`.
> The owner requested preservation of the discussed values and timings as a
> proposal. These are not shipped settings, a final accepted specification or
> playtested balance. This documentation change does not alter runtime code,
> balance JSON, save formats or dialogue.

Related references: [friendship balance proposal](FRIENDSHIP_BALANCE_PROPOSAL.md),
[need balance and example day](NEEDS_BALANCE_PROPOSAL.md),
[current fun/mood behavior](FUN_MOOD_SYSTEM.md),
[current time and saves](DATA_AND_SAVES.md) and
[social and entertainment concept](SOCIAL_ENTERTAINMENT_CONCEPT.md).

## Responsibilities and scope

Mood (the UI's **Laune**) expresses Aiko's overall condition, combining needs
with later emotional experience effects. It is not another need with its own
care action or independent passive drain. Changes in needs and experiences
change the target; actual mood approaches that target over time.

Friendship remains the separate relationship with the interacting person.
Improving Aiko's physical condition does not refund relationship losses or
automatically erase an offended response after absence.

Moodlets with stacking remain a later, separately specified system. They must
have precise contextual triggers rather than automatically duplicating every
need fulfillment or deficit. Hunger, fatigue and loneliness are not charged
again as generic negative Moodlets on top of the need penalties below.

## Proposed need contribution

The five needs are satiety, energy, fun, social and affection, each on 0–100.
Each has equal weight (20%). Their average is scaled to **0–80 mood points**:

```text
need_base = 0.16 * (satiety + energy + fun + social + affection)
```

All five needs at 100 therefore produce a base of 80. The remaining positive
range is reserved for later experience effects; full needs alone do not
automatically mean maximum mood. Friendship has no generic bonus in this
proposed need base.

The later [consumption-modifier proposal](NEEDS_BALANCE_PROPOSAL.md#proposed-consumption-modifiers)
now restricts hardware effects to additional hunger/energy consumption. Hardware
has no direct mood penalty or social-Moodlet trigger in that candidate; mood
responds to the resulting needs. This supersedes the earlier open modifier
scope in the discussion, not the currently implemented workload/energy rules.

## Proposed deficit penalties and target limits

Apply this curve separately to each need:

| Need value | Additional mood deduction for that need | Upper limit on target mood |
| --- | --- | --- |
| 40 or higher | 0 | No additional limit |
| 25 | 5 | 60 |
| 10 | 12 | 45 |
| 0 | 20 | 30 |

Deductions add across deficient needs. The strictest target limit applies.
Interpolate continuously between the anchors rather than introducing jumps.
For interpolation of the upper limit, "no additional limit" at 40 corresponds
to the normal maximum of 100. Values above 40 add no deduction or deficit limit.

The target calculation, without yet defining a Moodlet catalogue, is:

```text
target_mood = clamp(need_base - sum(need_deductions), 0, strictest_target_limit)
```

Later positive experience effects must respect the same deficit limits: they
cannot make an unmet need irrelevant. Their exact strengths and stacking rules
are not settled here. Mood remains bounded to 0–100.

### Examples without Moodlets

| Needs | Need base | Total deduction | Target mood after limits |
| --- | --- | --- | --- |
| All five at 100 | 80 | 0 | 80 |
| All five at 80 | 64 | 0 | 64 |
| One at 25, the other four at 100 | 68 | 5 | 60 |
| One at 10, the other four at 100 | 65.6 | 12 | 45 |
| One at 0, the other four at 100 | 64 | 20 | 30 |
| Two at 0, the other three at 100 | 48 | 40 | 8 |
| One at 0, the other four at 50 | 32 | 20 | 12 |
| All five at 0 | 0 | 100 | 0 |

These limits constrain the **target**, not the instantaneous visible value.
Actual mood reaches the target through the decline/recovery timing below.
Aiko does not die when a need reaches zero.

## Proposed decline speed

When target mood is below actual mood, the lowest current need determines
the maximum decline rate:

| Lowest need | Mood decline per real minute |
| --- | --- |
| 40 or higher | 1 point |
| 25 | 3 points |
| 10 | 6 points |
| 0 | 10 points |

Interpolate the rate continuously between these anchors. Multiple deficient
needs already lower the target more strongly; their decline rates do not add.
Stop at the current target, without overshoot or continued independent drain.

For an interval of `minutes` with unchanged needs and target:

```text
new_mood = max(target_mood, current_mood - decline_rate * minutes)
```

Illustration: actual mood starts at 80, one need becomes zero and the other
four remain at 100. Target mood is 30 and the decline rate is 10 per minute:

| Real elapsed time | Actual mood |
| --- | --- |
| Start | 80 |
| 1 minute | 70 |
| 3 minutes | 50 |
| 5 minutes | 30 |

This isolates the response to a severe deficit; it does not imply that needs
normally jump straight from full to empty. The values assume an unchanged
target throughout the example.

## Proposed recovery speed

When target mood exceeds actual mood, recovery is **2 points per real minute**.
It starts immediately when actual care or another valid change raises the
target above actual mood. There is no extra waiting period and no overshoot.

For an interval with an unchanged target:

```text
new_mood = min(target_mood, current_mood + 2 * minutes)
```

| Recovery with a stable sufficient target | Required real time |
| --- | --- |
| 30 to 50 | 10 minutes |
| 30 to 60 | 15 minutes |
| 30 to 80 | 25 minutes |
| 8 to 80 | 36 minutes |

Care first improves the real need and therefore its contribution, deduction
and limit. Partial care enables only the resulting partial recovery. An energy
need still at zero, for example, continues to limit target mood to at most 30.
Further changes to needs or experiences update the target during recovery.

There is no additional universal instant mood bonus per care action in this
proposal. Special experience effects belong to the later contextual Moodlet
design; they must not be silently copied from the current immediate-care rule.

## Real elapsed time and absence

The same elapsed-time reasoning applies with the application open, closed or
the computer in standby. Reopening does not reset mood, needs or recovery.
The proposed behavior must not inherit the current eight-hour reconstruction
limit or the live clock's exclusion of standby.

Absence must follow the chronological course of needs and actual available
resources. A desktop item that is genuinely available and consumed can improve
a need and permit subsequent recovery; it is then consumed and persisted.
There is no hidden supply or fabricated human interaction. Autonomous care
does not award friendship or stop contact-related relationship loss.

The constant-target examples are arithmetic illustrations, not a full absence
simulation. A future implementation cannot apply the final need state and its
rate retroactively to the entire absence. Changes in needs, resource use and
target direction must be accounted for in their actual order.

## Open questions before implementation

The [combined example day](NEEDS_BALANCE_PROPOSAL.md#combined-example-day-with-needs-mood-sleep-and-friendship)
records a normal-care calculation with actual mood approximately 57–78, no
critical deficits, and recovery toward each updated care target. It distinguishes
target from actual mood and leaves expression thresholds/refusal rules open;
it is not a runtime test or final approval of the scale's presentation.

- Confirm or revise these candidate values through integrated scenarios and
  practical desktop use; none of the timings are playtest results.
- Validate the separate [need-rate and care candidates](NEEDS_BALANCE_PROPOSAL.md),
  including sleep, finite autonomous resources and retained modifiers, before
  treating their simplified example as integrated balance.
- Define contextual Moodlet triggers, strengths, stacking, durations and their
  interaction with the target limits without duplicate penalties.
- Define offended-return behavior separately from numeric mood and friendship.
- Specify persistence, exactly-once elapsed-time accounting, clock corrections
  and numerical integration through existing state/time owners.

The current runtime remains described in [Fun and mood](FUN_MOOD_SYSTEM.md).
Recording this proposal does not approve implementing it.
