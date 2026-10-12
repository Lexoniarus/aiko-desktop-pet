# v0.12 — affection, differentiated care, and friendship

## Design goal

Aiko is a Chibi personification of the computer. She has **five short-term care needs** and one lasting relationship with the user who looks after her. No Academy or Character Chronicles commitments are simulated.

Computer workload is experienced as her own work, but **does not automatically mean she is receiving less affection**.

## Six gauges: five needs and friendship

| Value | What it means | Primary care | Progression |
| --- | --- | --- | --- |
| **Satiety** | Hunger | Feeding | Depletes faster with intensive computer work |
| **Mood** | Immediate well-being | Playing | Responds to workload, day phase, and unmet needs |
| **Energy** | Wakefulness and fatigue | Sleep / energy drink | Depletes faster at work and regenerates during sleep |
| **Social** | Conversation and shared activity | Talking | Depletes slowly; a small amount during the night |
| **Affection** | Feeling noticed, supported, and safe | Petting | Depletes at about **1.35 points/h awake** and **0.25 points/h asleep** |
| **Friendship** | Long-term familiarity (levels 1–10) | Meaningful, varied care | **No passive decline** |

All values range from 0 to 100. A new game starts with **75 points per short-term need** and 15 friendship points (level 2). Existing saves preserve every previously stored value. New affection starts at 75 for migrated saves.

## Care balance

| Action | Primary effect | Side effects |
| --- | --- | --- |
| Feed | +27 satiety | +3 mood for a snack or +5 for the first eligible meal; +1 social |
| Play | +23 mood | +12 social, −9 energy, −4 satiety; unavailable when too tired |
| Talk | +26 social | +5 mood, −1 energy |
| Pet | **+25 affection** | +6 mood, +2 social, **no energy bonus** |
| Energy drink | **+10 energy** | Repeatable until 100; no direct friendship reward |
| Sleep | +22 energy/h | Sleep/wake toggle governed by normal day/night logic |

Measured high CPU/GPU activity continues the v0.11 rules: it can raise satiety drain to roughly **1.95×** and increase mood and energy loss. Affection does **not** directly decline faster because of utilization; social decline is affected only modestly. Unobserved time is never treated as confirmed high load.

## Friendship: gradual trust instead of button farming

Friendship differs from ordinary replenishable needs. A meaningful care action can grant friendship only when its **primary target need was at most 80 before the action**:

- Feed checks satiety.
- Play checks mood.
- Talk checks social.
- Pet checks affection.

Care still works when friendship points are not granted.

- Meaningful care typically gives **0.9–1.0 friendship points**.
- The first additional care type introduced in a day grants a one-time **+0.35** diversity bonus.
- The same action can award friendship at most once every **12 minutes**, and only if the need qualifies again.
- The maximum award is **5.0 points per local calendar day**, with an overall friendship cap of 100.
- Energy drinks and sleep/wake do **not** directly grant friendship.
- Inactivity and background work do **not** passively reduce friendship.

Existing friendship points and historical award timestamps are retained during migration. The new daily limit does not retroactively remove earned progress.

## Character reactions

- Low social contact: Aiko might appreciate company and use `social_low` reactions with long cooldowns.
- Low affection: she can become more reserved or miss a small caring gesture, with **different** dialogue than social deprivation.
- High affection plus friendship: she may respond more warmly, calmly, or awkwardly to a click or pet.
- Hunger, exhaustion, verified computer work, irritation, and the actual time of day still have priority. She does not have to speak constantly.

This release added **16 handwritten dialogue entries in four event categories**. The existing 73 sprites, the movable hover panel, window stacking, and adaptive rhythm remained intact.

## Privacy and compatibility

The fields `affection` and `care_types_today` were added to the existing JSON save at `%LOCALAPPDATA%\AikoDesktopPet\state.json` while maintaining schema `version: 1`.

There is no extra database, cloud account, AI API, or new runtime package. The saved data contains no raw application activity, typed text, or browser content. Balancing remains intentionally simple and testable pending extended Windows play sessions.
