# Need balance and daily care proposal

> **Discussion proposal only — no implementation approval.** Recorded on
> 2026-10-19 on `feature/social-optimization`, alongside code baseline `b190694`.
> The owner requested preservation of the discussed need values, example day,
> progressive friendship and neglect rules. These are candidate values, not
> shipped settings, a final specification or playtested balance. No runtime
> code, JSON balance, save schema or dialogue changes accompany this record.

Related proposals: [friendship, progressive upkeep and neglect](FRIENDSHIP_BALANCE_PROPOSAL.md)
and [overall mood](MOOD_BALANCE_PROPOSAL.md).
The later [adaptive sleep proposal](ADAPTIVE_SLEEP_PROPOSAL.md) records sleep,
wake, habit-learning and closed-time candidates for this balance.
It also records brief food breaks during sleep, the 20/40 satiety thresholds,
bounded zero-hunger search and stricter identified-stock use while closed.
Current implementation guides: [food](FOOD_SYSTEM.md),
[fun/mood](FUN_MOOD_SYSTEM.md) and [time/saves](DATA_AND_SAVES.md).

## Intended care rhythm

Maintaining level 10 should require attentive care distributed throughout the
waking day, while allowing normal human sleep and daily life. It is not an
hourly appointment or a demand to refill every need every hour. Several short
care periods roughly two to three hours apart are the high-care example.

Average good care should still support a good relationship, approximately
levels 7–8. Level 9 remains a very close relationship; occasionally falling
from 10 to 9 is not itself evidence that Aiko should act offended. Actual
absence, neglect and negative interactions supply that context.

All five needs use 0–100. They can reach zero; Aiko does not die. Friendship
and mood are separate consequences, not additional replenishable needs.

## Proposed rates per real hour

| Need | While Aiko is awake | While Aiko is asleep |
| --- | --- | --- |
| Satiety | -8 | -1.4 |
| Energy | -3 | +7.5 |
| Fun | -3 | 0 |
| Social | -8 | -0.35 |
| Affection | -6 | -0.25 |

These are elapsed-time base rates, including closed-app time and computer
suspension. Closing the app or suspending the computer does not automatically
put Aiko to sleep. The example assumes an actual 23:00–07:00 sleep interval;
the later sleep proposal preserves the adaptive timing and priority discussion.
Offline observation rules and some transition details still need specification.

The latest energy proposal **replaces** the earlier discussed -6 per awake
hour and +12.5 per sleeping hour. At the new rates, eight hours of sleep
restore up to 60 energy, while 16 awake hours consume 48 before action costs.
Recovery from complete exhaustion can take longer than one normal night.
Energy drinks should be optional for the example day.

Over a 16-hour waking day and eight hours asleep, the other base losses are
139.2 satiety before digestion effects, 48 fun, 130.8 social and 98 affection.
Hardware/activity modifiers are not included in these rates or examples.
Their future interaction with the balance remains to be settled; this record
does not approve removing all existing workload/energy behavior.

## Proposed effects of completed care

| Actual accepted action | Need effects |
| --- | --- |
| Conversation | +26 social, -1 energy |
| Petting | +25 affection, +2 social |
| Completed RPS round | +6 fun before diminishing returns, +0.6 social, -0.5 energy |
| Consumed energy drink | +10 energy; no satiety or digestion reserve |
| Personally handed-over and eaten food | Satiety/reserve according to the food; +1 social |
| One real hour asleep | +7.5 energy, with the other sleeping rates above |

Clamp needs to 0–100. A button press, rejected offer or unfinished game round
is not completed care. Improving a need changes the mood target; subsequent
mood recovery follows the separate proposal, without a universal instant bonus.

For RPS, retain the discussed diminishing returns: rounds 1–3 award full fun,
rounds 4–6 award 60%, and later rounds 25%, with at most 20 fun per session.
The base award is equal for victory and defeat; special emotional consequences
belong to later contextual Moodlets. Three completed rounds can award 18 fun,
1.8 social and cost 1.5 energy before clamping or other unresolved modifiers.
The existing high-fun reward reduction is not modeled in the example; its
retention/replacement must be explicitly settled rather than silently assumed.

### Food values retained as candidates

| Food | Immediate satiety | Digestion reserve, minutes |
| --- | --- | --- |
| Sandwich | +38 | 145 |
| Onigiri | +30 | 105 |
| Melonpan | +29 | 85 |
| Dorayaki | +21 | 60 |
| Taiyaki | +20 | 55 |
| Donut | +18 | 42 |
| Cupcake | +17 | 46 |
| Apple | +14 | 38 |
| Cookie | +12 | 30 |
| Dango | +10 | 20 |

These preserve the food distinctions discussed from the existing catalogue.
Digestion reserve temporarily slows satiety loss; it is not another immediate
satiety award or a promise that the entire listed time has zero hunger decay.
Its exact future curve, fasting/activity modifiers and food acceptance need
separate evaluation. Existing authored food mood bonuses are not automatically
approved as additional instant effects in the new mood proposal.

Autonomous use provides the corresponding physical need effects from an
actually available desktop portion. It does not fabricate human social,
affection or friendship credit. A used portion is consumed and persisted;
there is no hidden replenishment. Future fun/social/affection objects remain
separate concepts. Repeated energy-drink restrictions remain undecided.

## Example high-care day

Times are movable. Their distribution, actual completed actions and adequate
resources matter; these are not mandatory wall-clock appointments.

| Time | Actual care / activity |
| --- | --- |
| 07:00 | Wake; personally give Onigiri and talk |
| 09:30 | Talk and play three completed RPS rounds |
| 12:00 | Personally give a sandwich and pet |
| 14:30 | Talk, play three completed rounds and pet |
| 17:00 | Personally give an apple and talk |
| 19:00 | Personally give a sandwich and pet |
| 21:00 | Talk and play three completed rounds |
| 23:00 | Personally give a small snack (Dorayaki in the calculation), pet; then sleep |
| 23:00–07:00 | Eight hours asleep; no human care required |

There are eight care periods: three meals, two snacks, five conversations,
four petting interactions and three play sessions. All daytime contact gaps
are at most 2.5 hours. The overnight contact gap is eight hours, from the
last actual petting to the next morning's care, not merely from clicking Sleep.

### Simplified repeated-day arithmetic

This illustration starts well supplied and repeats the same schedule, clamping
each need after each action. It assumes all listed actions are accepted and
completed, uses only the base rates and immediate food values above, and
excludes digestion reserve, activity/workload modifiers, high-fun reward
reduction, mood calculations and Moodlets. It does not import or exercise
production policies and is not an integrated runtime or desktop playtest.

| Need | Approximate lowest awake value in the repeating example |
| --- | --- |
| Satiety | 56 |
| Energy | 42.5, immediately before sleep |
| Fun | 80.5 |
| Social | 63 |
| Affection | 67 |

At 23:00, the repeating values are approximately satiety 83, energy 42.5,
fun 92.5, social 85.6 and affection 99. After eight hours asleep they are
71.8, 100, 92.5, 82.8 and 97 respectively, before morning care.
The needs do not progressively drain from day to day under these assumptions.
Food reserve, acceptance and other modifiers can change the actual trajectory.

## Relationship consequences of the example

The [friendship proposal](FRIENDSHIP_BALANCE_PROPOSAL.md) specifies the gains,
reward limits, four-hour contact grace period, progressive upkeep factor and
neglect rules. The temporary suggestion of a one-hour contact grace period was
withdrawn. An eight-hour night is compatible with maintaining level 10.

At high friendship, the example has no daytime absence loss and approximately
2 points of overnight loss before small changes in the progressive factor.
Actual qualified care can earn up to the proposed +5 budget per 24 hours,
including the reduced gains when the corresponding need is already above 80.
A relationship starting at 95 before sleep therefore goes to roughly 93 on
waking and can reach roughly 98 after a fully rewarded day. These are rounded
illustrations; reward-window accounting and continuous factor changes matter.

For comparison, contacts only at 07:00 and 23:00 create 16- and eight-hour gaps.
The original high-friendship reference rates produce 10 points of loss across
those gaps, exceeding even +5 gained. The progressive factor later softens the
decline at lower friendship; this is not a permanent ten-point daily deduction.

Average-good-care example: contacts at 07:00, 13:00, 19:00 and 23:00 produce
four points of reference absence loss. Around 70 friendship (level 8), the
factor of 0.75 gives roughly three points of loss. **If** the real care earns
three points, that is an approximate maintenance point. At high friendship,
the same pattern loses roughly four and therefore slowly drops with +3 gained.
The contact times alone do not establish adequate need care or guarantee gains.

The suggestion to block all friendship gains until every need reaches 40 was
withdrawn. Positive care can count while another need is temporarily low;
the timed neglect rules distinguish short deficits from sustained poor care.

## Remaining decisions

- Verify the entire day with digestion, acceptance, reward windows and other
  retained modifiers before treating the arithmetic as balanced gameplay.
- Resolve the [adaptive sleep candidates](ADAPTIVE_SLEEP_PROPOSAL.md), including
  remaining transition details and reconstruction while closed/suspended without
  inventing observed activity, resources or personal care. Manual priority,
  protection times and sleep-type wake thresholds are recorded there as proposals.
- Resolve high-fun saturation, food reserve/fasting/activity effects and any
  repeated-drink rules, preserving the intended overnight feasibility.
- Validate other daily schedules, missed contacts and recovery from already
  poor needs; this example is maintenance, not an emergency recovery plan.
- Keep Moodlet triggers, durable emotional memories and offended-return
  dialogue separate from these numeric candidates.

Recording these values does not approve implementation or change existing saves.
