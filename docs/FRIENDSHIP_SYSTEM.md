# Progressive friendship, contact and neglect

This guide describes stage 3 on `feature/social-optimization`. The
[active plan](CARE_TIME_IMPLEMENTATION_PLAN.md) records delivery; the
[proposal](FRIENDSHIP_BALANCE_PROPOSAL.md) preserves earlier alternatives.
Friendship remains one 0–100 relationship value, initially 15. Display level
is `min(10, 1 + floor(points / 10))`. Needs can reach zero without death.

## Personal care and rolling rewards

| Accepted personal action | Nominal gain | Evidence |
| --- | --- | --- |
| Food | 0.9 | Actual personal intake, not placement or an unused offer |
| Energy drink | 0.25 | Actual personal intake |
| Talking / petting | 1.0 each | Accepted, committed care transition |
| Shared play | 1.0 per session | At least two completed rounds, irrespective of outcome |

Above 80 in the corresponding pre-care need, multiply the nominal award by
0.25. Then enforce same-type eligibility once per two real hours, a shared
0.75 per rolling two hours and a shared five points per rolling 24 hours.
There is no variety bonus or midnight reset. Values and curves live only in
`data/balance.json`; Python owns their validation and transition rules.

An eligible same-type attempt sets its two-hour anchor even if a shared
budget or the 100-point limit leaves no award. Earlier repetitions do not
move that anchor. Limits constrain actual credited gain, never need care or
qualified contact. Loss does not reopen a reward budget.

Accepted personal care renews contact even with no remaining reward. A
completed one-round game is contact, but earns no friendship award. Opening
a game, cancelling before any completed round, rejected food/drink, sleep,
wake, hover, ordinary input, app opening and autonomous intake do not renew
it. Autonomous consumption still supplies its actual need normally.

Talking/petting count at their existing committed care transition, rather
than on a later bubble receipt. Interrupting presentation does not undo an
already accepted interaction or credit it again. A blocked/pre-commit
cancelled command never counts. Games keep their existing once-only close
summary; handovers count only at committed consumption. Callers advance the
shared session clock before committing care or completed play.

## Passive loss

| Care-contact gap | Reference points lost per hour in that interval |
| --- | --- |
| First four hours | 0 |
| After four through twelve hours | 0.5 |
| After twelve through twenty-four hours | 1 |
| After twenty-four through forty-eight hours | 1.5 |
| After forty-eight hours | 2 |

Sleep and standby do not pause this clock. Rates apply to their own
intervals, without retroactive re-rating or an eight-hour cap.

Passive scaling interpolates linearly between these anchors:

| Friendship | 0 | 35 | 50 | 70 | 90–100 |
| --- | --- | --- | --- | --- | --- |
| Loss factor | 0.05 | 0.15 | 0.35 | 0.75 | 2.00 |

The policy integrates the changing factor continuously, including crossings
between anchors. Direct negative actions and positive gains are not scaled.
Zero is a possible endpoint, not a protected floor or automatic refund.

Each need keeps critical/zero exposure over the preceding 24 elapsed hours.
Below 25, neglect becomes eligible after two accumulated critical hours;
at zero it can qualify after one zero hour. Zero also counts as critical.
Disjoint periods add up; contact and refilling do not erase prior exposure.
At 25 or above, that need stops charging immediately.

| Current eligible need | Reference rate | After six accumulated critical hours |
| --- | --- | --- |
| Above zero, below 25 | 0.25/hour | 0.5/hour |
| Zero | 0.5/hour | 1/hour |

While actual sleep increases energy, energy adds no new neglect and causes
no energy-neglect charge; its old history still expires normally. Other
needs remain eligible. Closed-app time is not itself proof of sleep.

For each chronological interval, use the greater of the absence rate and
the strongest eligible need rate, then apply the factor once. Neither sum
all needs nor compare only whole-day totals. The need policy passes each
existing numeric step to the friendship policy, without another simulator.
Exposure is stored in bounded minute buckets; full identical buckets are
coalesced into spans. Partial-bucket distribution/expiry has at most one-minute
resolution. At most 1,441 bucket spans are needed for the default 24-hour
window; sustained depletion normally coalesces to a handful of spans.

## Negative interactions

A selected `click_boundary`, `click_work_boundary` or
`click_withdrawn_boundary` warns within the existing click burst. Only later
admitted clicks in that burst deduct 0.25 each, at most one point per rolling
minute. Reading clicks and blocked input never count. Remaining reply
animations retain their ordinary input protection. Ending the burst resets
the warning, not the durable rolling loss allowance.

Withholding uses existing observed claimed-object custody: the third take
or eighteen seconds held qualifies for escalation, evaluated on the existing
ten-second request cadence. Then a further 0.5 can be requested every thirty
seconds, bounded globally to two points per rolling two minutes. Returning
stops further holding charges and gives no refund. No delayed callback
replays every missed charge. Unrelated object pickup is not withholding.

The existing application coordinators admit evidence and deduplicate receipts;
PetState applies durable caps. Restarting or beginning another episode cannot
reset those caps. Offline time does not invent clicking/withholding events.

## Ownership and save compatibility

`PetState` remains the sole mutable pet aggregate. Immutable
`FriendshipHistory` lives in its complete `PetValues` checkpoint. Pure
`friendship.py` calculates rewards/direct penalties; `friendship_decay.py`
integrates passive loss alongside `progression.py`. There is no second clock,
relationship service or mutable history store.

The optional `pet.relationship` v1 record uses `pet.time.lived_seconds` for
baseline, contact, eligibility, actual credits, exposure and penalty windows.
Outer save v1 is unchanged. Legacy calendar/reward fields remain compatibility
metadata and do not participate in new eligibility or loss calculations.

Missing/invalid history starts at first upgrade reconstruction completion:
preserve existing points and needs, infer no old contact, and charge no
unrecorded past neglect/absence. Subsequent saves retain that baseline.
Corrupt/future relationship data is backed up before replacing the save.
Wall-clock corrections and session rebasing do not reset elapsed-axis limits.
Existing checkpoints and paired consumption rollback include every new field.

Production-policy tests cover all six discussed contact schedules. The
combined eight-phase day maintains level 10 around 96–100; the sufficiently
supplied four-phase day stays around 69–71. Under the isolated adequate-care
assumption, morning/evening visits settle around 34–36, rather than zero.
Sparse contact is not a protected minimum against unmet needs or harassment.
Adaptive sleep, closed-time stock consumption and richer offended-return
expression/Moodlets remain separate stages.
