# Friendship balance proposal

> **Discussion proposal only — no implementation approval.** Recorded on
> 2026-10-19 on `feature/social-optimization`, from code baseline `b519da4`.
> The owner requested preservation of these candidate values before continuing
> the mood discussion. These values are not shipped settings, an accepted final
> specification or evidence of playtested balance. Runtime code, JSON balance,
> save formats and dialogue remain unchanged.

Related references: [social and entertainment concept](SOCIAL_ENTERTAINMENT_CONCEPT.md),
[dialogue review workbook](DIALOGUE_REVIEW.md),
[current fun/mood rules](FUN_MOOD_SYSTEM.md),
[current data and time behavior](DATA_AND_SAVES.md) and
[current architecture](ARCHITECTURE.md).

## Product direction established in discussion

- Friendship represents the long-term relationship with the interacting person;
  the cursor is the person's observable means of contact.
- A high relationship level should require sustained, regular care. Absence
  should cause visible consequences and loss of relationship levels.
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
affection. The separate need-replenishment amounts are not settled here.

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

## Proposed loss during absence

Measure real elapsed time since the last **valid personal-care interaction**.
Merely starting the application, pointer hover, ordinary UI operation and
annoying Aiko do not renew that care-contact interval. Autonomous feeding,
sleep and later self-entertainment do not renew it either.

| Time without qualifying care | Candidate loss rate within that interval |
| --- | --- |
| First 4 hours | 0 points/hour |
| After 4 through 12 hours | 0.5 points/hour |
| After 12 through 24 hours | 1 point/hour |
| After 24 through 48 hours | 1.5 points/hour |
| After 48 hours | 2 points/hour |

Rates apply **piecewise and continuously**, not retroactively at the newest
rate to the entire absence. For elapsed hours `h >= 0`, the proposed total
unclamped loss is:

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

An accepted new care interaction ends the current contact gap and begins a
new one. Its ordinary gain does not refund all losses or restore old levels.
Exact persistence, clock-correction handling and first-session anchoring are
future implementation decisions.

### Consequences from 95 friendship points

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

This is deliberately severe candidate tuning: three days without qualifying
care can erase even a previously maximal numeric relationship. The table makes
that consequence explicit; preserving it is not approval of that severity.

### Idealized progression examples

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
Need deficits influence overall condition/mood; the table above separately
specifies the proposed direct relationship loss from contact absence. Additional
penalties for chronic poor care must not be introduced without deciding their
triggers and overlap with absence first.

## Open questions before implementation

- Confirm or revise the numeric gains, grace period, progressive loss curve
  and its three-day consequence.
- Define accepted relationship contact precisely, including abbreviated play,
  interrupted conversations, personal handovers and reward-limited care.
- Resolve reward-budget windows, repeat handling, reduced-gain ordering and
  the former variety bonus.
- Define clicking/withholding episodes and their exact loss-rate limits.
- Specify durable time accounting, idempotence, restart/suspend reconstruction
  and normal clock corrections without creating a second friendship owner.
- Define offended return behavior and its recovery separately from numeric
  friendship; the Moodlet catalogue and mood balance are not settled here.

Overall mood balance remains unspecified by this proposal. No code, runtime
resource, schema or editorial review status changes as part of this record.
