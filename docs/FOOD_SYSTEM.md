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
| Donut | Snack | +18 | 42 min | +4 |
| Cookie | Snack | +12 | 30 min | +3 |
| Melonpan | Snack | +29 | 85 min | +4 |
| Cupcake | Snack | +17 | 46 min | +4 |
| Dorayaki | Snack | +21 | 60 min | +4 |

Reserve is consumed faster under combined activity and its defensive hunger
effect progressively fades. Snacks do not reset
`awake_hours_since_main_meal`. The third or later consecutive serving of
one food reduces its normal mood bonus by six points but does not reduce
nutritional value or damage friendship. Aiko's scripted German
`feed_repeat` reactions are in `aiko_pet/data/dialogues.de.json`.

Meals are *suggestions*, not a requirement at fixed wall-clock times. A
proper meal in an existing breakfast/lunch/dinner time slot still marks that
slot as eaten. The direct legacy `interact("feed")` chooses Onigiri by
default; the current desktop toolbar displays eleven food-and-drink choices.

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

Ten food types and an Energy Drink appear in the selection window, laid out
in two rows (up to six columns each). The menu icons are native transparent
64 × 64 images in `aiko_pet/assets/items/icons/64/`. There are independent
prepared **1× and native 2× PNGs** under
`aiko_pet/assets/items/food/{1x,2x}/`, built from the high-resolution
masters *outside the repository*. Runtime `ui/food_overlay.py` uses the
single `items/items.json` manifest's scale-specific pivots to attach the
chosen sprite to all eight source-frame `food_anchor` positions. It never
zooms tiny food images to make 2× objects, and it doesn't re-load them when
Aiko's character size changes.

The Energy Drink is a *drink choice, not a nutrition entry*: selecting it
invokes the existing `energy_drink` care action, restoring up to ten energy
points without adding satiety, digest reserve or fun. The old standalone
toolbar button is removed. A full-energy refusal does not play the consumption
animation. Its future mood-side-effect has deliberately **not yet been
balanced or enabled**; Fun/Mood  rules remain unchanged.

The existing five food images in `aiko_pet/assets/food/` remain available as
legacy prepared references, but are not used by the current selector.

The original full-resolution artwork stays outside GitHub. Offline
preparation produces the two runtime scales and picker icons; item pivots
live in the checked-in JSON manifest. The original
`tools/prepare_food_assets.py` continues to cover the five historical
64px images; it is not the generator for the new native 1×/2× collection.
Pillow is never needed at runtime.

## Quality and further balancing

Use `tests/test_food.py`, `tests/test_food_activity.py`, the existing care
and persistence tests, and `tests/test_food_gui.py`. Run the complete
Ruff, Mypy, Pyright, Python 3.11/3.13 Tk/Xvfb and Windows-headless suites;
native Windows visual verification is required for hand overlay placement.

The initial values deliberately emphasize a *playable* day rather than
realistic human nutrition. Tune after several real-life days observing hunger,
not by adding hidden penalties to other needs.
