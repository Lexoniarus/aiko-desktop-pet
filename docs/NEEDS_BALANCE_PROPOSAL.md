# Need balance and daily care proposal

> **Implementation update:** Stage 2 now applies the latest numeric need/care,
> consumption and mood rules on `feature/social-optimization`; see the maintained
> [food](FOOD_SYSTEM.md) and [fun/mood](FUN_MOOD_SYSTEM.md) guides. Production
> tests reproduce both repeated-day need/mood schedules within 0.1 point.
> Their explicit manual sleep is a scenario assumption; new friendship and
> learned sleep rules are still pending. Earlier disclaimers preserve history.

> **Planning update, 2026-10-19:** The owner accepted the latest combined
> care examples as a suitable starting point for implementation planning.
> See the [active care/time implementation plan](CARE_TIME_IMPLEMENTATION_PLAN.md).
> Earlier recording disclaimers below describe the original discussion status;
> none of these values is implemented by this documentation update.

> **Discussion proposal only — no implementation approval.** Recorded on
> 2026-10-19 on `feature/social-optimization`, alongside code baseline `b190694`.
> The owner requested preservation of the discussed need values, example day,
> progressive friendship and neglect rules. These are candidate values, not
> shipped settings, a final specification or playtested balance. No runtime
> code, JSON balance, save schema or dialogue changes accompany this record.
> The later hardware, input-activity and digestion discussion is preserved below
> as a proposed replacement for the corresponding current runtime modifiers.
> A later combined example calculates needs, mood, sleep and actually credited
> friendship together under explicit assumptions; it is not a runtime test.

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
The original base-only example is retained as such. The later modifier section
below now specifies candidate additional effects and separate food calculations;
it does not implement or approve changes to existing workload/energy behavior.

## Proposed consumption modifiers

Normal elapsed time must require food, including during idle or light office
use. Hardware is an **additional consumption driver**, never a prerequisite
for hunger or a way to remove the base need for feeding. Input activity is a
separate small contribution, not a count of how often the user clicks Aiko.

| Influence | Candidate effect |
| --- | --- |
| Awake satiety base | 8 points lost per real hour, independently of hardware/input activity |
| Hardware | No surcharge up to approximately 30% smoothed CPU/GPU load; above that, increasing toward at most +20% hunger at high load |
| Actual input activity | At most +10% hunger, based on sustained actual use |
| Combined hardware/input | At most +25% hunger in total |
| Digestion | Temporarily reduce awake hunger by at most 25%, replacing the existing 55% maximum |
| Energy hardware surcharge | Same load threshold; at most an additional 0.5 points lost per awake hour, replacing the existing 2.8 maximum |
| Social, affection and fun | No direct hardware-related consumption surcharge |

The earlier -8 satiety and -3 energy base rates remain unchanged. Smooth load
over time rather than making a short spike require extra care. Actual input
is not an independent energy surcharge in this candidate. Its precise scaling
to the 0–10% hunger range and the sensor aggregation for the hardware threshold
still need validation against representative measured use.

Hardware has no direct mood penalty, social emotion/Moodlet trigger or sleep
signal in this proposed model. It can indirectly lower mood or create a need
for rest by increasing hunger/energy consumption. Sleep learning continues to
use the separately agreed actual-input, inactivity and off/standby signals.
This is a future design boundary, not a claim about all current code paths.

### Digestion and removal of overlapping accelerators

Keep the existing food-specific immediate satiety and reserve distinctions.
A meal first restores satiety; its remaining reserve then temporarily slows
awake hunger, gradually losing that protective effect as reserve runs out.
Reserve is not an additional automatic satiety refill.

- Use up one reserve minute per real awake minute.
- Use up 0.3 reserve minutes per real sleeping minute.
- Retain the maximum stored reserve of 175 minutes.
- Remove the extra hardware/activity-based acceleration of reserve use from
  this candidate. Extra hunger consumption already accounts for that activity.
- Omit the existing additional hunger acceleration after a long food break
  for the first version of this proposal. Base hunger continues regardless;
  mood and timed neglect still express the consequences of missing care.

The current runtime's fasting bonus and activity-based digestion acceleration
therefore remain implemented today but are **not** part of this new candidate.
Existing authored food mood bonuses are likewise not silently added to the
separate mood proposal.

For the combined percentage ceiling, add hardware and input surcharges before
capping at 25%; digestion then reduces the resulting awake hunger by at most
25%. Illustrative bounds:

| Activity condition | Awake hunger without reserve protection | With maximum digestion protection |
| --- | --- | --- |
| No hardware/input surcharge | 8/hour | 6/hour |
| Maximum combined surcharge | 10/hour | 7.5/hour |

Sleeping satiety loss remains 1.4/hour. Do not apply hardware hunger/energy
surcharges while Aiko sleeps, even if the computer continues a background task.
Energy recovery and the other sleeping rates remain as proposed above.

### Food-only repeated-day illustration with modifiers

Repeat the five food portions in the example day: Onigiri at 07:00, sandwich
at 12:00, apple at 17:00, sandwich at 19:00 and Dorayaki at 23:00, followed by
sleep until 07:00. Retain the 0–100 satiety bound and reject food at satiety
96 or above in this calculation, rather than assuming unlimited acceptance.

The calculation uses one-minute intervals for 60 repeated days, initially
75 satiety and zero reserve, with constant illustrative input/load values while
awake. It retains gradual linear reserve protection up to the existing
80-reserve-minute full-effect anchor for this illustration, now capped at 25%
reduction, and uses the reserve timing above. There is no fasting multiplier or
activity speedup of reserve use. The final fade curve still requires agreement.

| Illustrative activity profile | Result with three meals and two snacks |
| --- | --- |
| Idle: no surcharges | Repeating minimum satiety approximately 61.8; food remains necessary |
| Light office example: no hardware surcharge, input halfway to its maximum (+5% hunger) | Repeating minimum approximately 57.5; the food schedule remains stable |
| Maximum hardware hunger surcharge alone (+20%) | Original portions become insufficient over repeated days; extra food is needed |
| Maximum combined hardware/input surcharge (+25%) | More extra food is needed than for hardware alone |

The two stable profiles consume approximately 129.7 and 135.6 satiety points
per 24 hours respectively, including the eight-hour sleeping interval. Being
idle does not remove the need to eat. The office profile is an assumed numerical
case, not a measurement or certification of every office computer.

This calculation models satiety, reserve and food acceptance only. It does not
exercise production policies or jointly simulate sleep decisions, food seeking,
friendship gains, mood, neglect, hardware sampling or the other needs. The
original base-only five-need table below has not become an integrated test.
The later [combined example day](#combined-example-day-with-needs-mood-sleep-and-friendship)
extends the arithmetic to the other needs and consequences for one normal case.

For energy, the original day has 48 base points lost plus 5 for conversations
and 4.5 for nine RPS rounds: 57.5, leaving 42.5 from a starting 100. With the
maximum hardware surcharge for all 16 awake hours, another 8 points are lost,
leaving 34.5 instead. Eight hours asleep restore at most 60, so such sustained
maximum load cannot be assumed to repeat indefinitely without extra recovery
or an energy drink. Normal light office use should not require either.

### Closed app, standby and missing observations

Base consumption and reserve timing continue over real elapsed time according
to Aiko's actual modeled sleep/wake state. Do not invent hardware or input
surcharges for unobserved closed-app intervals. Computer standby/off is not a
reason to remove awake base hunger; Aiko follows her own sleep rules, with
sleeping rates only when she actually sleeps. Resources remain finite and
autonomous consumption does not fabricate personal care or friendship gains.

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
The existing high-fun reward reduction is not modeled in the original base-only
example. The later combined example checks it both retained and omitted, with
the same repeating-day result for this schedule. Its general retention or
replacement still needs a decision.

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
The later consumption-modifier section specifies weaker reserve protection and
omits fasting/activity-based reserve acceleration. Its final fade curve and
interaction with food acceptance still need evaluation. Existing authored food
mood bonuses are not automatically approved as additional instant effects in
the new mood proposal.

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

This is the earlier **base-only** illustration. Use the later combined example
for the latest normal-day results with digestion, input activity and mood.

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

## Combined example day with needs, mood, sleep and friendship

> **Discussion calculation only.** This preserves the owner's requested joint
> calculation of the proposed rules. It does not implement them, run production
> policies or establish Windows/UI acceptance. The base-only and food-only
> examples above remain separately labeled illustrations.

### Assumptions and method

- Use the eight care periods and five personally handed-over food portions
  listed above. Conversations, petting and completed play are accepted; food
  is rejected at satiety 96 or above rather than assumed always consumable.
- Model light office use: hardware below the proposed surcharge threshold,
  input activity halfway to its maximum, giving +5% awake hunger. This is an
  assumed profile, not a measured workload. Sleep has no activity surcharges.
- Use the previously described linear reserve fade with maximum 25% protection,
  one reserve minute used per awake minute and 0.3 per sleeping minute; omit
  fasting acceleration and activity-based reserve speedup.
- Calculate the five needs, need-derived mood target and actual mood together.
  Exclude Moodlets, instant food mood bonuses and direct hardware mood penalties.
  Actual mood does not jump when a care action changes its target.
- Use the learned 23:00–07:00 main-sleep frame, with explicit manual Sleep at
  23:00 after the snack/petting and normal scheduled Wake at 07:00. No earlier
  sustained user-return event is assumed. This case evaluates the applicable
  normal sleep branch, not every unresolved sleep transition.
- Calculate nominal friendship gains from each action's actual pre-care need,
  reduce to 25% when that need is above 80, apply the per-type timing rule and
  both shared rolling ceilings, and renew valid contact even when no reward
  remains. The old variety bonus is omitted. Use the latest progressive loss
  factor. All same-type actions in this schedule are at least two hours apart.
- Repeat 60 days to settle the needs/reserve/mood and rolling reward history,
  then report the next day. Set friendship to 95 before the reported 07:00 care;
  that chosen relationship value does not feed back into needs or mood. Use
  one-minute intervals, with a 15-second comparison to check numerical sensitivity.
  Actions are represented at their listed times, without measured animation or
  conversation durations. This is arithmetic, not application execution.

### Daytime and next-morning values

Need values are **immediately after** the listed care block. The final row is
the next morning **before** care. The last column is the new **target mood**;
actual mood approaches it at the separately proposed rates. Rounded values do
not represent instant mood jumps.

| Time and completed care | Satiety | Energy | Fun | Social | Affection | Target mood |
| --- | --- | --- | --- | --- | --- | --- |
| 07:00: Onigiri, talk | 100 | 99 | 92.5 | 100 | 97 | 78.2 |
| 09:30: talk, three RPS rounds | 81.3 | 89 | 100 | 100 | 82 | 72.4 |
| 12:00: sandwich, pet | 98.3 | 81.5 | 92.5 | 83 | 92 | 71.6 |
| 14:30: talk, three rounds, pet | 81.0 | 71.5 | 100 | 92.8 | 100 | 71.2 |
| 17:00: apple, talk | 74.0 | 63 | 92.5 | 99.8 | 85 | 66.3 |
| 19:00: sandwich, pet | 95.5 | 57 | 86.5 | 86.8 | 98 | 67.8 |
| 21:00: talk, three rounds | 82.3 | 48.5 | 98.5 | 98.6 | 86 | 66.2 |
| 23:00: Dorayaki, pet, then sleep | 86.6 | 42.5 | 92.5 | 85.6 | 99 | 65.0 |
| Next 07:00, before care | 75.4 | 100 | 92.5 | 82.8 | 97 | 71.6 |

Before the first reported care, the already settled morning values are likewise
approximately 75.4 satiety, 100 energy, 92.5 fun, 82.8 social and 97 affection,
with actual mood about 71.6. The matching next-morning needs demonstrate that
this repeating schedule does not silently lose supply from one day to the next.

| Need | Lowest value between care periods in the reported day |
| --- | --- |
| Satiety | Approximately 57.5 |
| Energy | 42.5 |
| Fun | 80.5 |
| Social | 63 |
| Affection | 67 |

All five food portions are accepted. No need reaches the 40-point deficit
boundary, so no additional critical-need mood deductions/limits apply and no
neglect allowance is used. There is no need for a nap, exhaustion recovery or
sleep-time food break in this case. Retaining or omitting the current high-fun
reward reduction gives the same settled result for this schedule; this does
not settle its effects in other situations.

### Actual mood and sleep

Actual mood ranges approximately **57–78**. With one-minute steps the range
is 57.15–77.88; with 15-second steps it is 57.14–77.93. The finer calculation
also gives minimum satiety 57.48 instead of 57.51; the other need minima and
friendship totals are unchanged at the displayed precision.

Actual mood rises toward each new care target at two points per minute, usually
taking roughly three to five minutes to catch the changing target here. The
earlier 25-minute recovery example concerns a much larger 30-to-80 deficit,
not a mandatory delay after every care action. Between actions, actual mood
follows the gradually falling target. With no need below 40, its decline speed
ceiling is one point per minute; there is no independent extra mood drain.

The moderate evening value follows the lower energy and other partly depleted
needs, despite high friendship. Around 60 mood must not automatically be read
as relationship offense. With full needs producing at most 80 before Moodlets,
existing cheerful thresholds above 80 still require a separate design decision
for expressions/text selection. This calculation does not change them.

At 23:00 manual Sleep begins and its 30-minute protection expires at 23:30
without a competing wake event. Energy rises from 42.5 to 100 after seven
hours 40 minutes, approximately **06:40**. Reaching full energy does not end
the main sleep, so Aiko continues until **07:00** and meets the normal wake
minimum of 40. The next morning's actual mood is again approximately 71.6.

### Actually credited friendship in the combined day

This uses the individual nominal/reduced awards rather than assigning the
maximum 0.75 to each visit without checking its care actions.

| Care time | Credited gain for that care block | Friendship after care |
| --- | --- | --- |
| 07:00 | +0.75 | 95.75 |
| 09:30 | +0.75 | 96.50 |
| 12:00 | +0.75 | 97.25 |
| 14:30 | +0.75 | 98.00 |
| 17:00 | +0.75 | 98.75 |
| 19:00 | +0.75 | 99.50 |
| 21:00 | +0.50 | 100.00 |
| 23:00 | 0; 24-hour budget exhausted | 100.00 |

The care at 23:00 still renews contact, so the overnight gap remains eight
hours. The four-hour grace followed by four hours at the 0.5 reference rate,
multiplied by factor 2 at this friendship, costs **4 actual points**. No neglect
rate is eligible. Friendship reaches **96 before the next 07:00 care**, remains
at level 10 throughout and has a net +1 across this selected 95-start day.
The older abstract visit-only comparison's +5 is therefore achievable by the
specific actions in this normal case, rather than merely an assumed allowance.

### Interpretation and limits

For this maintained light-office day, the proposed need, mood, sleep and
friendship arithmetic is mutually compatible. It does not prove the balance
for sustained heavy load, missed care, initial exhaustion, other schedules,
or current production refusal/playback behavior. The reserve fade curve,
actual input/load scaling, expression thresholds and possible care refusal
rules remain design questions. No files or saves were changed by the arithmetic
and no implementation was authorized by recording it.

## Combined four-phase average-care day

The owner accepted this later comparison as the average-care baseline for
implementation planning. It uses the same light-office modifiers, reserve
curve, accepted-action assumptions, mood calculation and 23:00–07:00 sleep
as the combined eight-phase day above. The care is bundled into four longer
visits; fewer visits do not mean that less total nutrition or conversation
will automatically suffice.

| Time | Accepted care in order |
| --- | --- |
| 07:00 | Onigiri, talk, pet, three RPS rounds |
| 13:00 | Sandwich, apple, two talks, pet, three RPS rounds |
| 19:00 | Sandwich, talk, pet, three RPS rounds |
| 23:00 | Dorayaki, talk, pet, then manual Sleep |

That is five food portions, five accepted conversations, four petting actions
and three three-round game sessions, matching the eight-phase day's total
care. The second midday talk improves social need but receives no extra
same-type friendship reward inside two hours. Visits must allow these actions
to finish; the calculation does not measure conversation/animation duration
or bypass an actual runtime rejection or busy state.

Repeat the independent arithmetic for 241 days, starting friendship at 70,
retaining rolling histories and reporting the final settled day rather than
resetting friendship for the report. One-minute steps produce the following
post-care need values and new target mood. Actual mood still approaches the
target over time; it does not jump with the care action.

| Time | Satiety | Energy | Fun | Social | Affection | Target mood |
| --- | --- | --- | --- | --- | --- | --- |
| 07:00 | 100 | 97.5 | 100 | 100 | 100 | 79.6 |
| 13:00 | 100 | 76 | 100 | 100 | 89 | 74.4 |
| 19:00 | 92.3 | 55.5 | 100 | 82.8 | 78 | 65.4 |
| 23:00 | 83.4 | 42.5 | 88 | 79.8 | 79 | 59.6 |
| Next 07:00, before care | 72.2 | 100 | 88 | 77 | 77 | 66.3 |

Across the settled day, minimum satiety is approximately 51.9, energy 42.5,
fun 82, social 50.8 and affection 53. All food is accepted, all needs stay
above 40 and no neglect, nap, recovery or sleep-time food break is triggered.
Actual mood ranges approximately **47.8–79.1**; it starts and finishes the
repeating day around 66.3. Energy again reaches 100 around 06:40 and normal
sleep continues until 07:00. These are arithmetic results, not a runtime test.

Each visit actually earns the shared ceiling of +0.75, totaling **+3**. The
progressive absence loss also settles at approximately **-3 per day**, without
an additional neglect charge. Friendship varies approximately **69.2–70.8**,
crossing levels **7–8**, rather than maintaining level 10. This is the intended
average-care relationship; its moderate mood is not itself evidence of offense.

The shorter comparison with no extra midday apple and only one midday talk
does not maintain equivalent needs. Under repeated-day arithmetic, satiety and
social need reach zero, actual mood can reach zero, and friendship settles
around 50–51 (levels 5–6) with sustained neglect. Four visits alone therefore
cannot certify good care. The accepted baseline is the sufficiently supplied
four-phase schedule, without retuning away its required care quantities.

The one-minute arithmetic reproduces the preceding discussion. A finer
15-second comparison gave minimum satiety about 51.88 and actual mood about
47.79–79.14, preserving the same relationship outcome. Production-policy,
save/resume and Windows verification remain tasks in the implementation plan.

## Relationship consequences of the example

The [friendship proposal](FRIENDSHIP_BALANCE_PROPOSAL.md) specifies the gains,
reward limits, four-hour contact grace period, progressive upkeep factor and
neglect rules. The temporary suggestion of a one-hour contact grace period was
withdrawn. An eight-hour night is compatible with maintaining level 10.

The later friendship revision adds shared rolling ceilings of +0.75 per two
hours and +5 per 24 hours, and replaces the earlier upkeep anchors. The
example has no daytime absence loss. Its eight-hour night costs two reference
points, now multiplied by 2 at level 10: approximately four actual points.
Actual qualified care can earn up to +5 across the distributed day, including
ordinary reduced gains when the corresponding need was already above 80.
A relationship starting at 95 before sleep therefore reaches approximately 91
on waking and can reach 96 after a fully rewarded day. The earlier 95-to-93-to-98
illustration is superseded. The isolated repeated-day friendship comparison
settles at 96–100 under its maximum-earned-reward assumptions.

For comparison, contacts only at 07:00 and 23:00 create 16- and eight-hour gaps.
The reference rates produce 10 unscaled loss points across those gaps. With
the latest shared ceiling, two visits can earn at most +1.5; the latest lower
curve makes that approximately maintenance around 35 friendship (level 4),
where factor 0.15 turns 10 reference loss into approximately 1.5. High friendship
falls more quickly, but this is not a fixed loss or an inevitable fall to zero.
Neglect, negative actions or lower actual gains can still reduce friendship.

Average-good-care example: contacts at 07:00, 13:00, 19:00 and 23:00 produce
four points of reference absence loss. Around 70 friendship (level 8), the
factor of 0.75 gives roughly three points of loss. The shared two-hour ceiling
now limits those four visits to +3. If that gain is actually earned, the isolated
calculation settles around 69–71 points (levels 7–8). At level 10 the factor is
2, so the same reference loss is about eight rather than the earlier four;
it no longer supports level 10. Three adequately rewarded visits settle near
51–52 (level 6), five near 86–90 (level 9), and six to eight at 96–100 (level 10)
in the separate maximum-gain friendship calculation. Contact times alone do
not establish adequate need care or guarantee gains. See the
[daily comparison assumptions](FRIENDSHIP_BALANCE_PROPOSAL.md#latest-daily-friendship-comparisons).

The suggestion to block all friendship gains until every need reaches 40 was
withdrawn. Positive care can count while another need is temporarily low;
the timed neglect rules distinguish short deficits from sustained poor care.

## Remaining decisions

- The combined normal-day arithmetic above now includes digestion, food
  acceptance, actual reward windows and mood. Still verify production behavior,
  retained modifiers, actual care refusal and desktop timing before treating
  this discussion calculation as balanced gameplay or a passed runtime test.
- Resolve the [adaptive sleep candidates](ADAPTIVE_SLEEP_PROPOSAL.md), including
  remaining transition details and reconstruction while closed/suspended without
  inventing observed activity, resources or personal care. Manual priority,
  protection times and sleep-type wake thresholds are recorded there as proposals.
- Resolve high-fun saturation, the final reserve fade curve and repeated-drink
  rules. Validate the recorded hardware/input thresholds against measured use;
  fasting acceleration and activity-based reserve speedup are omitted from the
  latest candidate, rather than still being assumed parts of its balance.
- Validate other daily schedules, missed contacts and recovery from already
  poor needs; this example is maintenance, not an emergency recovery plan.
- Keep Moodlet triggers, durable emotional memories and offended-return
  dialogue separate from these numeric candidates.

Recording these values does not approve implementation or change existing saves.
