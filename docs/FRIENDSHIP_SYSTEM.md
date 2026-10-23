# Continuous friendship, contact and neglect

This guide describes the current `feature/social-optimization` runtime, checked
against `5d20d9c` on 2026-10-23. The [active plan](CARE_TIME_IMPLEMENTATION_PLAN.md)
records delivery and open decisions. The [original proposal](FRIENDSHIP_BALANCE_PROPOSAL.md)
preserves historical care-reward alternatives; its capped reward model is superseded.
Friendship remains one 0–100 relationship value, initially 15. Display level is
`min(10, 1 + floor(points / 10))`. Needs can reach zero without death.

## Continuous balance

Numeric mood, every active Moodlet's current tier, and absence/qualified neglect
contribute over actual elapsed time. There is no instantaneous friendship gain
for ordinary care or fulfilled wishes, and no current two-hour/daily reward pot.
Care changes needs and renews accepted contact; fulfillment creates its defined
Moodlet. Those changed facts affect subsequent elapsed balance.

Raw emotional amounts per 30 seconds, before progressive factors:

| Source | Positive amount | Negative amount |
| --- | --- | --- |
| Numeric mood | 0 at 60 or below; linear to 0.002 at 80; capped there | 0 at 40 or above; linear to 0.004 at 20; capped there |
| Each active Moodlet | 0.003 per positive tier | 0.006 per negative tier |

Only the positive numeric-mood baseline requires accepted contact within the
last four hours. Negative mood and active Moodlets contribute independently.
The 40–60 mood band is neutral. Numeric-mood group/global caps do not suppress
Moodlets' relationship contributions. Two negative impressions can outweigh
otherwise good numeric mood; current tiers, not historical peak tiers, count.

Interpolate each progressive factor linearly between point anchors:

| Friendship points | 0 | 35 | 50 | 70 | 90–100 |
| --- | --- | --- | --- | --- | --- |
| Positive factor | 1 | 1 | 1 | 0.6 | 0.35 |
| Negative factor | 0.05 | 0.15 | 0.35 | 0.75 | 2 |

One solver integrates simultaneous positive and negative contributions across
these anchors. The only hard point bounds are 0 and 100; there is no protected
level floor. Direct event penalties remain separate and are not scaled by this
elapsed policy. Values live in `aiko_pet/data/balance.json`.

The existing shared session clock samples ordinary status every 30 seconds;
actions and saves flush pending elapsed time immediately. Numeric progression
uses intervals of at most 15 seconds and splits at relevant Moodlet/contact/need
boundaries. This is neither another timer nor a fixed-size point jump.

## Accepted contact

| Personal action | Qualifying evidence |
| --- | --- |
| Food / energy drink | Actual personal intake, not placement or an unused/refused offer |
| Talking / petting | Accepted, committed care transition |
| Shared play | At least one actual completed round in the once-only session summary |

Opening a menu/game, cancelling before completion, rejected food/drink, sleep,
wake, hover, ordinary input, app opening and autonomous intake do not renew
contact. Talking/petting count at admission, not a later bubble receipt;
interrupting presentation cannot undo or repeat accepted care. Session summaries
remain once-only. Wish resolution can occur at an earlier actual round result
without granting a second contact event or an instant friendship bonus.

The food-avoidance wish has a separate handover rule: a perceived personal
handover can fulfill it even if refused. This does not invent intake or accepted
contact. Autonomous food can fulfill an ordinary food wish and create its Moodlet,
but cannot fabricate personal contact.

## Absence and neglect reference

| Care-contact gap | Reference points lost per hour in that interval |
| --- | --- |
| First four hours | 0 |
| After four through twelve hours | 0.5 |
| After twelve through twenty-four hours | 1 |
| After twenty-four through forty-eight hours | 1.5 |
| After forty-eight hours | 2 |

Sleep, closure and standby do not pause this elapsed axis. Rates apply only
to their own intervals, without retroactive re-rating or an eight-hour cap.

Each need keeps critical/zero exposure over the preceding 24 elapsed hours.
Below 25, neglect qualifies after two accumulated critical hours; at zero,
after one zero hour. Zero also counts as critical. Disjoint periods add up;
contact/refilling does not erase prior exposure. At 25 or above, charging for
that need stops immediately.

| Current eligible need | Reference rate | After six accumulated critical hours |
| --- | --- | --- |
| Above zero, below 25 | 0.25/hour | 0.5/hour |
| Zero | 0.5/hour | 1/hour |

Actual restorative sleep excludes new energy-neglect exposure and charges;
other needs follow their actual sleep trajectories. Closure alone does not
prove sleep. Use the greater of absence and the strongest eligible need rate,
not their sum. Add that reference to negative emotional flow, then apply the
progressive balance once. Exposure uses bounded minute buckets, coalescing
identical spans; the default 24-hour window needs at most 1,441 spans.

## Negative interactions

An actually delivered boundary reply, including `click_last_word`, warns
within the existing click burst. Selecting or queuing text alone is not
communicated evidence. Only later
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
A committed investigation of an
unidentified object can establish claimed interest before a later assessment
or food-consumption decision; these are distinct facts.

The existing application coordinators admit evidence and deduplicate receipts;
PetState applies durable caps. Restarting or beginning another episode cannot
reset those caps. Offline time does not invent clicking/withholding events.

Negative interactions have distinct event penalties, using that same persisted ledger:

| Perceived event | Separate loss | Rolling cap |
| --- | --- | --- |
| Unwelcome petting after a communicated boundary/active refusal | 0.25 | 1 per 10 minutes |
| Same personal food after a communicated variety request; first ignored portion is free | 0.25 | 1 per 24 hours |
| Independent witnessed relocation of a known object outside its familiar area | 0.25 | 1 per hour |

A refused stroke grants no care reward/contact. Unknown causes of an empty
familiar place can create an impression without blame. The same take is not
charged both as withholding and relocation. Moodlet creation/stacking/expiry
and helpful relief add no second instant
penalty or refund. Active tiers independently affect the continuous balance.
Each penalty kind is pruned by its own window; longer food budgets do not retain
unbounded minute-by-minute click history.

Poor-care qualification reads this same bounded history to qualify prolonged-poor-care
Moodlets. Processing watermarks are owned by MoodletState; the original care
history is neither reset nor copied. Creating, escalating, recovering or keeping
these after-effects adds no instantaneous relationship penalty or new contact.
Active poor-care Moodlets nevertheless contribute to the continuous emotional
balance, alongside numeric mood and the absence/neglect reference.

## Ownership, saves and evidence

`PetState` is the sole mutable pet aggregate. Frozen `FriendshipHistory` belongs
to `PetValues` and complete checkpoints. `friendship.py` owns accepted contact
and bounded direct consequences; `friendship_decay.py` integrates elapsed
balance alongside `progression.py`. No second clock, simulator or history store
is introduced.

Optional `pet.relationship` v1 uses `pet.time.lived_seconds`. The optional
`continuous_since` marks the accounted transition from older policy; old points,
contact, exposure and historical credits survive without refunds or replay.
Old reward fields/limits remain compatibility metadata only. Missing/invalid
history cannot invent earlier contact or unrecorded neglect; original corrupt
bytes are preserved by the existing save recovery policy. Full-precision status
and joint Pet/World rollback retain the existing save owner.

Historical stage-3 schedule tests and their 96–100 / 69–71 plateau examples
apply to the old capped-reward model. They are not evidence that current generated
wishes and continuous flow achieve the intended level-7–8 average / level-10
intensive care balance. That integrated acceptance, current full suite, slow-test
audit and OOP review remain slice 9. Concrete cause recording for negative and
poor-care Moodlets is also an open gap in the [documentation audit](CARE_TIME_IMPLEMENTATION_PLAN.md#documentation-audit-and-open-work-2026-10-23).
