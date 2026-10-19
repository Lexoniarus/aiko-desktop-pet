# Food system — practical tuning guide

> This guide describes the current implementation. The separate
> [need balance and daily care proposal](NEEDS_BALANCE_PROPOSAL.md) preserves
> discussion candidates and an illustrative day; it does not replace the
> runtime food, time or care rules below.
> Its later [consumption modifiers](NEEDS_BALANCE_PROPOSAL.md#proposed-consumption-modifiers)
> propose bounded hardware/input surcharges and weaker reserve protection,
> omitting fasting acceleration and activity-based reserve speedup. Those
> candidate replacements have not been applied to the existing implementation.

This is the current, editable food design. It supersedes historical v0.11/v0.12
feeding constants. The goal is three normal meals and optional snacks over a
16-hour active day, with no mandatory meal alarm. Reopening now reconstructs bounded closed time with optional scheduled self-care; see [data and saves](DATA_AND_SAVES.md).

## One source per responsibility

The nutrition rules and food *definitions* are deliberately separate:

- **Gameplay policy:** `aiko_pet/pet/food.py` owns `FOOD_BALANCE` and the
  pure hunger/digestion calculations. Its named policy parameters control
  waking/sleeping hunger, activity modifiers, digestion decay, long fasting,
  and the repeat-food penalty. These algorithmic rules remain Python code.
  Parameter values come from `aiko_pet/data/balance.json`; the dataclass no
  longer owns an independent set of editable numeric defaults.
- **Food content:** `aiko_pet/data/food_catalog.json` is the authoritative
  record of the ten food IDs, localized display names, meal/snack category,
  instant satiety, digestion reserve, mood bonuses and menu order (including
  the Energy Drink). `pet/food_catalog.py` validates that data into immutable
  `FoodProfile` values consumed by `pet/food.py`.
- **Sprites/icons:** `aiko_pet/assets/items/items.json` owns the icon paths,
  native 1×/2× PNGs and their grip pivots. It does **not** store duplicate
  food display names. `infrastructure/item_assets.py` validates asset IDs
  against the nutrition menu and derives food names from the canonical
  nutrition records (the drink's name comes from `data/texts.de.json`).
  Weapon-specific labels remain in this asset manifest.
- **UI menu:** `ui/view_models/food_models.py` builds immutable `FoodChoice`
  values from the validated nutrition and item catalogs. It never fabricates
  icon paths. The desktop assembly loads a single `ItemCatalog` and shares
  it between the picker and the sprite hand overlay.

To alter the nutrition numbers or menu order, edit
`aiko_pet/data/food_catalog.json` rather than a second Python table. The
JSON files are packaged content; no cloud service or SQLite is required for
the current runtime. A later repository backend can keep the same typed
catalogue contracts.

Reserve is consumed faster under combined activity and its defensive hunger
effect progressively fades. Snacks do not reset
`awake_hours_since_main_meal`. The third or later consecutive serving of
one food reduces its normal mood bonus by six points but does not reduce
nutritional value or damage friendship. Aiko's scripted German
`feed_repeat` reactions are in `aiko_pet/data/dialogues.de.json`.

Meals are *suggestions*, not a requirement at fixed wall-clock times. A
proper meal in an existing breakfast/lunch/dinner time slot still marks that
slot as eaten. The canonical `PetState.interact("feed")` chooses Onigiri by
default as a domain convenience; the desktop chooser creates World portions
and does not call direct feeding. It displays eleven food-and-drink choices.

Press and hold a choice to carry one portion. Offer it near Aiko long enough
to be recognized, then release in her handover area, or release above the taskbar
to let it fall. Aiko investigates new noticed resting objects independently of
appetite. After held inspection she decides whether to use or put down for later.
Autonomous food use starts at satiety ≤70, drink use at energy ≤60; known deferred
items can become goals at later need without repeated discovery. Required phase
bubbles are independent of spontaneous talk. Random walking can stay disabled.
Ground pickup grants custody at source frame 4, nutrition only at subsequent
consumption after investigation and readable decision. Interruptions after
grasp animate put-down before the user action; passive hover does not cut use short.
Human handover retains existing care rewards; autonomous ground consumption
does not grant human social/adaptive/friendship credit. See
[World contracts](WORLD_OBJECT_CONTRACTS.md) and [practical test](WORLD_SMOKE_TEST.md).

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
masters *outside the repository*. Runtime `ui/pet_view/food_overlay.py` uses the
shared `items/items.json` manifest's scale-specific pivots to attach the
chosen sprite to all eight source-frame `food_anchor` positions. It never
zooms tiny food images to make 2× objects, and it doesn't re-load them when
Aiko's character size changes.

The Energy Drink is a *drink choice, not a nutrition entry*: consuming its World
instance reuses the existing `energy_drink` care rules, restoring up to ten energy
points without adding satiety, digest reserve or fun. The old standalone
toolbar button is removed. Menu selection at full energy still starts cursor
carrying. Refusal is assessed later through valid hand/face evidence; a refused
drink does not play the consumption animation. Its future mood-side-effect has deliberately **not yet been
balanced or enabled**; Fun/Mood  rules remain unchanged.

The original full-resolution artwork stays outside GitHub. Offline
preparation produces the two runtime scales and picker icons; item pivots
live in the checked-in JSON manifest. Historical standalone 64px food images
and their old exporter are archived outside the repository; only the current
item catalog is shipped. Pillow is never needed at runtime.

## Quality and further balancing

Use `tests/test_food.py`, `tests/test_food_activity.py`, the existing care
and persistence tests, `tests/test_food_gui.py` for menu/cursor wiring, and
[standalone food rendering tests](../tests/test_food_rendering.py) for native
assets, hand anchors, stacking and scale changes. Run the complete
Ruff, Mypy, Pyright, Python 3.11/3.13 Tk/Xvfb and Windows-headless suites;
native Windows visual verification is required for hand overlay placement.

The initial values deliberately emphasize a *playable* day rather than
realistic human nutrition. Tune after several real-life days observing hunger,
not by adding hidden penalties to other needs.
