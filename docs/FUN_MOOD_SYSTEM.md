# Fun and mood — prototype tuning guide

Fun and mood now have **different responsibilities**. The target experience
is to play **three or four times per active day, with two or three completed
rounds per session**. These are optional, not fixed appointments.

## Editable JSON settings

Tune the `fun`, `mood` and `game_rock_paper_scissors` sections of
`aiko_pet/data/balance.json`. The existing `FUN_BALANCE` and `MOOD_BALANCE`
parameter objects read their defaults from this validated resource.

The fun-need policy is in `aiko_pet/pet/fun.py`. Its `FUN_BALANCE` contains
a 2.6-point-per-awake-hour fun decline (41.6 points over 16 waking hours),
zero boredom decay while sleeping, diminishing returns for long continuous
sessions and a 20-point cap per completed session.

Each game's relative reward lives in `GAME_FUN_PROFILES`. RPS awards
5.4 fun per completed round, plus 0.6 for an Aiko win, 0.25 for a draw,
and zero extra for an Aiko loss. A loss still grants base enjoyment.
The first three completed rounds receive full credit, rounds four through
six get 60%, and later rounds 25%. These are tentative tuning values.

`aiko_pet/pet/mood.py` defines `MOOD_BALANCE` and pure functions for
the emotional whole. Its target is influenced by the five underlying
needs (fun, food, energy, social, affection), critical deficits, actual
workload strain and a small positive long-term friendship effect.
Mood smoothly approaches its target. **Mood never influences fun or any
other need**, avoiding feedback loops. Direct care responds immediately
but gently as it improves a real need; food retains a brief enjoyment/
repetition reaction. The old unconditional minus-four-per-hour mood
rule is replaced.

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
application shutdown; only Aiko's adjusted fun, mood, energy, social
and existing friendship bookkeeping are saved.

The game is closed before the final save both during Aiko's goodbye
animation and on direct shutdown. It cannot credit a session twice.

## Presentation and compatibility

The existing six main bars stay in place. The expandable toolbar
details now display **Spaß** separately; the Laune bar represents
the whole. Requests to play use *fun*, not mood. The legacy direct
`interact("play")` is deliberately non-rewarding, since a real
minigame must be completed.

Old saves without `fun` load at 75. Previously saved mood values
are preserved initially and gradually follow the new formula.
On reopening, bounded closed time now advances needs and mood. Routine sleep and self-served main meals apply only during this reconstruction when automatic routine is enabled. Windows suspend remains excluded from the running-session clock. See [data and saves](DATA_AND_SAVES.md).

## Verification

`tests/test_fun_mood.py` and `tests/test_game_experience.py` validate
domain math, multiple sessions/day, game-neutral adapters and persistence.
Existing UI, lifecycle, farewell and application tests validate the
one-shot close callback and before-save processing. Values should be
tuned after several normal desktop usage days.
