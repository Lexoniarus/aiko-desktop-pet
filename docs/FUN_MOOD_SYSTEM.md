# Fun and mood — prototype tuning guide

> Current `feature/social-optimization` guide, checked against `5d20d9c` on
> 2026-10-23. The [mood](MOOD_BALANCE_PROPOSAL.md) and
> [need proposals](NEEDS_BALANCE_PROPOSAL.md) preserve design history.
> See [continuous friendship](FRIENDSHIP_SYSTEM.md), [adaptive sleep](SLEEP_SYSTEM.md)
> and the [active implementation plan](CARE_TIME_IMPLEMENTATION_PLAN.md).
> Delivery of foundations/UI is distinct from pending integrated acceptance and
> later dialogue about concrete emotional experiences.

Fun is one need; mood summarizes the five needs and active Moodlet contributions
over time. Several short play
sessions per active day support good care without fixed appointments.

## Editable JSON settings

Tune `fun`, `mood`, `needs`, `food` and the three `game_*` profiles in
`aiko_pet/data/balance.json`; the existing typed parameter objects read that
validated resource. Food nutrition remains in `food_catalog.json`.

Fun falls 3 points per awake hour and does not decay while sleeping. Each
completed RPS round gives 6 fun, costs 0.5 energy and gives 0.6 social,
regardless of win/draw/loss. Outcome evidence remains available for reactions.
The new profiles are 9 fun / 0.7 energy / 0.9 social per completed Tic-Tac-Toe
board, and 8 fun / 0.6 energy / 0.8 social per completed Blackjack hand. These
initial values give longer units more base credit without changing the shared
diminishing-return policy; they are not measured playtime equivalences.
Connect Four reuses the existing Tic-Tac-Toe completed-board profile; it adds
no balance values or game-specific wish targets. Its board and score remain
transient, and ordinary game-experience effects use the existing coordinator.
The first three rounds receive full fun credit, rounds four through six 60%,
and later rounds 25%, with a 20-point session cap. The existing high-fun
reduction starts above 85, declining linearly to 75% reward at 100.

Other need rates per real hour are:

| Need | Awake | Sleeping |
| --- | --- | --- |
| Satiety | -8 before bounded food/activity modifiers | -1.4 |
| Energy | -3, plus at most 0.5 for hardware | +7.5 |
| Social | -8 | -0.35 |
| Affection | -6 | -0.25 |

Talking gives +26 social and costs 1 energy. Petting gives +25 affection and
+2 social. Accepted personal food gives its nutrition and +1 social; an
energy drink gives +10 energy. All values clamp at 0–100; zero does not kill
Aiko. See [food](FOOD_SYSTEM.md) for reserve and hardware/input modifiers.

## Need-derived mood

`pet/mood.py` calculates the target as `0.16 * sum(five needs)` minus each
need's deficit deduction, capped by the strictest deficit limit. Friendship
and hardware add no separate numeric mood effect. Interpolate between anchors:

| Lowest/individual need | Individual deduction | Target limit | Decline ceiling, points/minute |
| --- | --- | --- | --- |
| 40 or higher | 0 | 100 | 1 |
| 25 | 5 | 60 | 3 |
| 10 | 12 | 45 | 6 |
| 0 | 20 | 30 | 10 |

Deductions sum across needs, and the lowest need determines the decline
ceiling. The need-only target is at most 80. Actual mood approaches the changing
target without overshoot; recovery is 2 points/minute with no extra delay.
Care, food, repeat food and completed games never change mood instantly.
Mood does not change needs; it does contribute to continuous friendship. Stage 5B.3 now composes existing
Moodlets through the same timed response; stage 5B.4 supplies direct negative
interaction triggers and targeted helpful-action matching.

`pet/progression.py` is the single pure numeric integration owner. It calls
food/fun/mood policies in chronological intervals of at most 15 seconds, then
returns frozen `PetProgress`. Only `PetState` applies that result to its
existing frozen `PetValues`. The time plan still owns observation and routine
boundaries; this calculation reads no clocks and introduces no second state.

## Moodlet composition and elapsed time

`calculate_moodlet_contributions()` reads each active family's current total
level contribution. Apply game-wish +15, social-wish +15 and poor-care -15 group
limits first. The six longer-term families have separate joint limits of +5
positive and -10 negative; opposing long-term contributions are not netted.
Then separately cap all positive effects at +20 and all negative
effects at -30. Combine those effects with the need-derived target, clamp to
0-100 and retain the strictest need ceiling. A zero need still limits the final
target to thirty. A numeric cap does not remove or weaken emotional evidence.

The pure rules in `pet/moodlets.py` and `pet/moodlet_timing.py` provide 3-2-1
expiry, bounded renewal/stacking and per-episode relief usage. New positive
multi-tier wish after-effects start with 60/45/45 minutes at levels 1/2/3.
An ascent restores each remaining tier to at least its base, retaining longer
residuals up to ninety minutes. An already level-three family gains ten minutes
per remaining tier, up to 270 minutes total. Two-tier outcomes choose ascent
or renewal, never both. Food starts at one sixty-minute tier, extends by ten
minutes and caps at ninety. The balance catalogue owns these shared times;
fixed family durations remain the legacy-save fallback for implicit lower tiers.
Passive snapshots sum actual remaining budgets. Negative poking/closeness relief
still requires
five minutes of quiet. Existing poor-care impressions require thirty stable
minutes at a need of at least forty before their two-hour recovery stages run;
a renewed drop pauses the remaining stage and requires stable qualification
again. One qualified helpful completion shortens only the current eligible tier,
discarding excess and retaining its used allowance through later escalation.
Friendship and petting-refusal deadlines are separate effects.

Long-term families use their own fixed thirty-/thirty-six-hour stages. A newly
qualified care period raises one level, up to three, and resets only the current
stage. They never receive wish-family extensions. Their per-intensity friendship
rates are +0.00005/-0.00010 per thirty seconds, replacing ordinary +0.003/-0.006
rates for those families. Ordinary short-term rates and progressive factors
remain unchanged. Pattern qualification itself is still a later feature slice;
elapsed time alone does not create long-term feelings or imaginary encounters.

The existing progression loop splits at tier/expiry, recovery qualification and
need-crossing boundaries. Before a boundary, actual mood still approaches the
previous target at its ordinary rate. Moodlet time continues through sleep,
closed time and unknown suspend intervals. Reconstructed time cannot extend an
observed withholding pause or generate negative user-interaction evidence.
Both application restoration paths use that same progression owner, including
short closed intervals; saves do not perform their own simulation.

Negative interactions now qualify poking, unwelcome petting, food monotony,
wanted-object withholding and familiar-arrangement disruption. Accepted care,
completed social sequences and shared play match targeted relief; existing
quiet/resolution/stable-recovery gates and per-level allowances still apply.
These functions accept qualified facts at an already-advanced endpoint; they do
not infer acceptance or user blame. Direct friendship consequences stay separate.
Stage 5B.5 also creates the five poor-care after-effects from actual modeled
need trajectories in live, closed and standby intervals. Wish lifecycle,
fulfillment, overall emotional interpretation and the VN status UI are delivered.

### Prolonged poor care

Satiety, energy, fun, social and affection each have one separate impression:
`hunger_worn`, `exhaustion_irritated`, `unstimulated`, `lonely` and
`missing_closeness`. The canonical relationship/care history supplies exposure;
small processing markers distinguish handled burden from new residual time.

| Intensity | Time below 25 in the last 24 hours | Alternative time at zero |
| --- | --- | --- |
| 1 | 2 hours | 1 hour |
| 2 | 4 hours | 2 hours |
| 3 | 6 hours | 3 hours |

The two routes are alternatives, not added durations or deductions. Existing
strengths are -5/-10/-15 per family, with a -15 combined poor-care group cap.
Needs continue to affect numeric mood directly; the emotional after-effect
changes its target through the same timed response. Creation adds no instant
friendship penalty; active tiers do contribute to continuous friendship.
Actual restorative sleep does not add exhaustion exposure; other needs retain
their actual sleep trajectories. Finite acquired food can prevent hunger burden.

At 40+, require 30 continuous healthy minutes before recovering one tier every
two hours. A new drop below 40 pauses earned progress and restarts qualification.
Brief improvement or the 25–40 range is not emotional recovery. Disjoint deficits
continue accumulating; genuinely new higher burden can escalate, but old handled
history cannot restore an expired impression. Qualified recovery consumes only
handled thresholds, preserving fresh subthreshold remainder. At the maximum,
existing burden is represented without refresh or a queued later stack.
Needed care remains available; helpful relief keeps its existing qualification
and once-per-tier rules. No death or new general interaction lock is introduced.

## Game-neutral pipeline

Every game adapter returns a frozen `GameExperience` with a game ID,
number of *completed units* and outcome counts from Aiko's perspective.
What a unit means and how strongly it is rewarded is a per-game profile.
Rock–Paper–Scissors currently maps each *revealed round* to one unit;
the user's score `wins` maps to Aiko's setbacks and `losses` to Aiko wins.

Each window reports one immutable `games.contracts.SessionSummary` exactly
once upon closing. Its counts use the player's perspective and are derived
from the game's own score. `HoverUi` passes the summary to the application;
`experience_from_session` creates the generic experience; `GameExperienceCoordinator`
updates `PetState`. The minigame and its UI never adjust needs directly.

Blackjack, Tic-Tac-Toe and Connect Four settle the required completed reveal/turn before
crediting their game-owned score. Closing during a pending reveal or bot turn
does not count it; closing during the subsequent reaction retains that unit.

Mastermind settles after its four feedback marks are placed. Closing before
that finishes credits nothing; closing during the subsequent secret reveal or
result reaction retains the completed round. Its explicit profile alias reuses
Tic-Tac-Toe values, without changing balance, friendship or wish targets.

Only actual completed play awards fun. Leaving the game window open,
starting a round without reaching reveal, or closing an empty game
awards **nothing**. The round score remains transient, including on
application shutdown; only Aiko's adjusted fun, energy, social
and existing friendship bookkeeping are saved, alongside bounded wish progress
and any fulfilled wish's Moodlet.

Actual round start/result facts also reach the existing application coordinator
through each game's sequence. Only the wish captured at round start can qualify.
Result translation from player to Aiko occurs once. New shared-play wishes need
two cumulative rounds across sessions; next-win and next-non-loss wishes resolve
on the next qualifying round. Overall wins need three cumulative wins, with no
consecutive requirement; overall non-loss uses a three-round block. Saved older
wishes retain their original objective/count and progress until retirement.
Wish resolution is immediate at the actual result, independent of later window
close. It does not duplicate ordinary session care. Failed non-loss goals create
`disappointed`; other unsuccessful goals grant no fulfillment impression.

The game is closed before the final save both during Aiko's goodbye
animation and on direct shutdown. It cannot credit a session twice.

## Presentation and compatibility

The combined VN status window presents numeric **Laune**, the five needs and
friendship alongside active Moodlets and inner wishes. The separate emotional
label interprets impressions rather than replacing any physical need.
Requests to play use fun, not numeric mood. Legacy `interact("play")` grants no
care: actual minigame completion remains necessary.

Old saves without fun load at 75; existing mood is preserved and approaches the
current target over time. Full closure/standby advances through the shared
progression. Adaptive sleep and finite identified World-stock care are delivered;
time alone cannot create food. See [data and saves](DATA_AND_SAVES.md).

## Overall emotional interpretation and reads

Numeric mood remains the timed need/Moodlet wellbeing value. The separate
`EmotionalComposition` is a pure interpretation of every active impression's
current intensity (1/2/3), independent of numeric contribution caps. Sum each
polarity and direction; the stronger polarity's greatest combined direction
sets the primary state. Equal nonzero totals yield Zwiegespalten. Direction
ties prefer the latest trigger, then strongest individual impression, then
stable enum order. No-Moodlet fallback: Gedrückt below 40, Gelassen at 40–<70,
Zufrieden from 70. All causes and secondary directions remain readable.

Physical needs, sleep, short irritation/warmth and friendship are separate facts.
They coexist in dialogue context rather than replacing one another with a
mixed label. Existing need priority and interaction-specific boundaries remain;
an overall label creates no reward or blanket refusal. Passive snapshots expose
all supported Moodlet families and wish forms, including unspoken wishes, paused
recovery, original deadlines, round progress and temporary restrictions. Reading
never advances or fulfills them. Stage 5C now presents these records in the combined status UI. The pure
numeric target, real sleep reason, relationship stage and known contact age
are detached alongside actual mood. Moodlets/wishes remain passive views.
Ordinary positive stories/idle emotes are reachable at mood 70, while the
longer playful click sequence retains 82 and its existing boundaries. The
same overall composition gates positive expression; hardware strain alone
does not imply emotional offense or sleepy clicks.

## Wishes and fulfillment

Storage supports three inner wishes, including several distinct goals in one
area. The current live picker still chooses at most one per area. Awake live
evaluation fills available slots initially or after the saved twelve-minute
vacancy pause; further vacancies do not postpone it. Closed time never generates
new wishes. Original lifetime is four real hours, except while pinned.

Food/affection creation requires the respective need at most 70, and affection
also requires actual petting willingness. Unpinned supplied food/affection wishes
retire at 90; games and social are exempt from this need gating. Low mood/trust
does not suppress inner wishes. Disclosure requires friendship level three,
mood fifty, current capability and a free speech opportunity; urgent care takes
priority. Actual text presentation counts once per wish, thirty minutes apart.
Temporary unavailability keeps the wish and its original deadline.

Left-click pins a card. Right-click unpins a pinned wish; right-click on an
unpinned wish dismisses it. Current late unpinning can retire the wish immediately
if its original deadline passed. The already agreed correction keeps an unpinned
wish until the next shared refresh; that lifecycle change is the next planned
slice, together with the ten-minute rotation and new wish mix.

Actual desired intake, welcome petting, qualifying game results and complete
matching social sequences can fulfill wishes, including unspoken ones. The
food-avoidance form instead uses a perceived personal handover, even of the
excluded food and even if subsequently refused. It does not fabricate nutrition.
Fulfillment retires the stable identity and creates its defined positive Moodlet;
there is no direct friendship bonus or reward pot. Numeric mood follows its
timed response; friendship integrates active impressions over elapsed time.

Food fulfillment remains at one tier; overall game success adds two tiers of
pride/relief; other successes add one within family limits. Episodes retain the
latest actual causes up to current intensity (maximum three), trimming on decay
and rolling on renewal. A single two-tier success still has only one actual
cause; no event is invented to fill a row. Negative interaction and poor-care triggers
currently lack structured concrete causes and fall back to generic evidence.

## Verification scope

Existing focused domain, persistence, game, social, UI-contract and hover checks
are recorded by delivery in the master plan. These are historical results, not
a fresh full-suite claim for current HEAD. Generated-wish/balance integration
remains in the later feature acceptance; full-suite/static gates, tests over ten
seconds and the final OOP review remain in the closing phase of the current
master plan. Native Windows/DPI/input acceptance remains separate; the original
reported AppHang is not conclusively diagnosed. Later concrete-experience speech
is deliberately outside this delivery.
