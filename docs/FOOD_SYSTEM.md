# Food system — practical tuning guide

This is the current, editable food design. It supersedes historical v0.11/v0.12
feeding constants. The goal is three normal meals and optional snacks over a
16-hour active day, with no mandatory meal alarm and no offline hunger penalty.

## Change values in Python

The *single* food policy is `aiko_pet/pet/food.py`:

- `FOOD_BALANCE.awake_hunger_points_per_hour = 8.0`: waking baseline, even
  if no user input or hardware load is currently observed
- `FOOD_BALANCE.sleeping_hunger_points_per_hour = 1.4`: night baseline
- `FOOD_BALANCE.maximum_hardware_hunger_bonus = 0.20`: CPU/GPU/RAM work
- `FOOD_BALANCE.maximum_user_input_hunger_bonus = 0.18`: actual user input
- `FOOD_BALANCE.maximum_combined_activity_bonus = 0.35`: combined cap
- `awake_hours_before_hunger_accelerates = 3.0`: hungry again without food
- `maximum_long_fast_hunger_bonus = 0.25`: cap on prolonged hunger
- `maximum_digest_hunger_reduction = 0.55`: fullest digestion protection
- `maximum_digest_reserve_minutes = 175`: limit repeated eating
- `consecutive_repeats_before_dislike = 2`: third identical food in a row

All quantities use hours, minutes, fractions or points, not opaque magic
integers. The named functions `hunger_activity_multiplier`,
`hunger_after_long_food_break`, `digestion_hunger_multiplier`,
`eat_food`, `is_repeated_food` and `advance_food` are individually
testable. The food definition table `FOOD_CATALOG` is adjacent:

| Food | Category | Instant satiety | Digestion reserve | Mood on first serving |
| --- | --- | ---: | ---: | ---: |
| Onigiri | Meal | +30 | 105 min | +4 |
| Sandwich | Meal | +38 | 145 min | +5 |
| Taiyaki | Snack | +20 | 55 min | +4 |
| Apple | Snack | +14 | 38 min | +3 |
| Dango | Snack | +10 | 20 min | +2 |

Reserve is consumed faster under combined activity and its defensive hunger
effect progressively fades. Snacks do not reset
`awake_hours_since_main_meal`. The third or later consecutive serving of
one food reduces its normal mood bonus by six points but does not reduce
nutritional value or damage friendship. Aiko's scripted German
`feed_repeat` reactions are in `aiko_pet/data/dialogues.de.json`.

Meals are *suggestions*, not a requirement at fixed wall-clock times. A
proper meal in an existing breakfast/lunch/dinner time slot still marks that
slot as eaten. The direct legacy `interact("feed")` chooses Onigiri by
default; the current desktop toolbar displays the five-item food selector.

## Hardware workload versus user input

`aiko_pet/application/food_activity.py` owns `ACTIVITY_BALANCE`,
`FoodActivityHistory.observe` and `current_food_activity`. CPU, GPU and
RAM contribute through the existing `telemetry.workload_intensity` when a
fresh measurement is available. Actual input evidence is obtained from the
Windows *last-input age*, sampled cursor displacement and current mouse-button
edges. No key names, keycodes, typed text, application titles, click
coordinates, or full event histories are stored. Only short anonymous
time-weighted buckets for the last hour remain in memory.

The rolling activity summary blends the last 15 minutes and 60 minutes,
using `ACTIVITY_BALANCE.short_window_weight`. The two axes are independent:
the GPU can be busy with nobody using the computer; typing can be intense
while CPU load is low. Unknown and stale signals do not fabricate work.
Inactivity affects only the user input bonus, not the base hunger. Aiko's
social reaction to being alone belongs to a separate feature.

The activity observer lives in the application layer. Windows input adapter
functions live in `desktop/global_input.py`, and UI widgets cannot modify
hunger. `PetState` owns nutrition and delegates calculations to
`pet/food.py`; `pet/need_decay.py` assembles the other needs.

## Session time and compatibility

The pet's active-session clock is authoritative. Saving and loading the
existing version-one JSON adds an optional nested `pet.food` value;
old saves load with neutral food state. Closing Aiko, suspending Windows or
restarting a computer does not consume food or digest the reserve while the
simulation is stopped. Only a bounded, simulated active interval progresses
hunger.

## Food graphics, scale and animation

Five transparent 64 × 64 runtime food images live in
`aiko_pet/assets/food/`. They were prepared from the separately kept
original high-resolution character-compatible food assets with a **0.98
object-scale factor** (two percent smaller), not by editing the original
artwork. The selection window shows the prepared image at its native menu
size. `ui/food_overlay.py` displays a smaller version on Aiko, using all
eight frame-specific `food_anchor` coordinates already in
`assets/animations.json`. The food graphic follows her hand for the full
`eat` sequence; no food is permanently embedded in her animation frames.

To regenerate from original assets when adjusting the two-percent size,
use the developer-only `tools/prepare_food_assets.py --source DIR` script.
Pillow is needed only for image preparation, not to run Aiko.

## Quality and further balancing

Use `tests/test_food.py`, `tests/test_food_activity.py`, the existing care
and persistence tests, and `tests/test_food_gui.py`. Run the complete
Ruff, Mypy, Pyright, Python 3.11/3.13 Tk/Xvfb and Windows-headless suites;
native Windows visual verification is required for hand overlay placement.

The initial values deliberately emphasize a *playable* day rather than
realistic human nutrition. Tune after several real-life days observing hunger,
not by adding hidden penalties to other needs.
