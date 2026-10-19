# Fun and mood — prototype tuning guide

> This guide describes stage 2 on `feature/social-optimization`. The
> [mood](MOOD_BALANCE_PROPOSAL.md) and [need proposals](NEEDS_BALANCE_PROPOSAL.md)
> retain the agreed design evidence. Friendship, adaptive sleep and expression
> tuning remain later stages of the [implementation plan](CARE_TIME_IMPLEMENTATION_PLAN.md).

Fun is one need; mood summarizes the five needs over time. Several short play
sessions per active day support good care without fixed appointments.

## Editable JSON settings

Tune `fun`, `mood`, `needs`, `food` and `game_rock_paper_scissors` in
`aiko_pet/data/balance.json`; the existing typed parameter objects read that
validated resource. Food nutrition remains in `food_catalog.json`.

Fun falls 3 points per awake hour and does not decay while sleeping. Each
completed RPS round gives 6 fun, costs 0.5 energy and gives 0.6 social,
regardless of win/draw/loss. Outcome evidence remains available for reactions.
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
Mood has no feedback effect on needs or rewards; Moodlets remain deferred.

`pet/need_decay.py` is the single pure numeric integration owner. It calls
food/fun/mood policies in chronological intervals of at most 15 seconds, then
returns frozen `NeedProgress`. Only `PetState` applies that result to its
existing frozen `PetValues`. The time plan still owns observation and routine
boundaries; this calculation reads no clocks and introduces no second state.

## Game-neutral pipeline

Every game adapter returns a frozen `GameExperience` with a game ID,
number of *completed units* and outcome counts from Aiko's perspective.
What a unit means and how strongly it is rewarded is a per-game profile.
Rock–Paper–Scissors currently maps each *revealed round* to one unit;
the user's score `wins` maps to Aiko's setbacks and `losses` to Aiko wins.

The `RockPaperScissorsWindow` reports its immutable `Score` exactly
once upon closing; `HoverUi` passes it to the application; its RPS
adapter creates the generic experience; `GameExperienceCoordinator`
updates `PetState`. The minigame and its UI never adjust needs directly.

Only actual completed play awards fun. Leaving the game window open,
starting a round without reaching reveal, or closing an empty game
awards **nothing**. The round score remains transient, including on
application shutdown; only Aiko's adjusted fun, energy, social
and existing friendship bookkeeping are saved.

The game is closed before the final save both during Aiko's goodbye
animation and on direct shutdown. It cannot credit a session twice.

## Presentation and compatibility

The toolbar displays **Laune** as the wide overall bar above six individual
indicators. **Spaß** has its own bar between satiety and energy; the second row
contains social, affection and friendship. Fun is no longer repeated as a
percentage line in the expandable details. Requests to play use *fun*, not mood.
The legacy direct
`interact("play")` is deliberately non-rewarding, since a real
minigame must be completed.

Old saves without `fun` load at 75. Previously saved mood values
are preserved initially and gradually follow the new formula.
Full closed time and standby now advance needs and mood, using the existing
stage-2 balance. Automatic routine can apply existing scheduled sleep; time alone no
longer creates self-served catalogue meals. Adaptive sleep remains a later stage. Expression filters above 80 are
explicitly pending stage 5; this numeric change does not retune dialogue labels. See [data and saves](DATA_AND_SAVES.md).

## Verification

`tests/test_fun_mood.py` and `tests/test_game_experience.py` validate
domain math, multiple sessions/day, game-neutral adapters and persistence.
Existing UI, lifecycle, farewell and application tests validate the
one-shot close callback and before-save processing. Values should be
tuned after several normal desktop usage days.
