# v0.11 — Tamagotchi care, social need, and friendship

This is the original v0.11 feature specification. **v0.12 subsequently added affection as a separate need and revised care balance and friendship rewards**; refer to the v0.12 document for current mechanics.

## Role and separation of concerns

Aiko personifies her computer. She has no Academy timetable or Character Chronicles story obligations. Her time of day and real workload, plus the adaptive routine introduced in v0.9, still matter.

Aiko experiences computer work as her own exertion without narrating technical CPU/GPU/RAM names in her character voice.

## Four short-term needs and a relationship (v0.11)

| Value | Meaning | Natural progression | Main care |
| --- | --- | --- | --- |
| Satiety | Hunger and food | Decreases while awake, slightly during sleep | Feed (+27) |
| Mood | Current well-being | Influenced by day phase, deprivation, and work | Play (+23), pet (+9 in v0.11), talk (+5), food (+3/+5) |
| Energy | Awake versus exhausted | Decreases during activity, regenerates in sleep | Sleep (+22 points/h), energy drink (+10 points/use) |
| Social | Desire for contact with the user | Gradual decline during long solitude; minor decline in sleep | Talk (+26), play (+18 in v0.11), pet (+12 in v0.11); food only +1 |
| Friendship | Long-term trust | No passive decline or workload multiplier | Meaningful care across multiple days; v0.11 cap +7/day |

Every value is between 0 and 100. Friendship also has a visible **level from 1 to 10**. It is not a need that must be refilled periodically. A new game starts with 15 friendship points (level 2); old save files keep their previously existing values and get compatible defaults for added fields.

All care buttons are available in the hover panel and the detail window. Talk is a distinct interaction. An energy drink restores **exactly 10 energy points** each time and may be repeated up to 100. Sleeping remains available. Playing consumes 9 energy and 4 satiety; talking consumes 1 energy.

## Workload and need decay

`workload_intensity()` estimates active computer work primarily from CPU and GPU utilization, with relatively little influence from memory pressure. High allocated RAM is **not** proof of high computation.

During active **measured** workload, the ordinary awake need rates change. At near-maximal intensity (1.0), the v0.11 implementation approximated:

- Satiety decline: **1.95×** its base rate.
- Mood: an additional **−2.1 points per hour**.
- Energy: an additional **−2.8 points per hour**.
- Social: only a slight additional effect, because heavy computer work is not the same as loneliness.

Baseline rates still depend on local time and weekday. Missing telemetry uses the baseline; a measurement is applied for at most **30 seconds** of eligible recent time. Startup, sleep/resume, and prolonged observation gaps must not create fictional hours at maximum load. Sleeping does not consume awake energy simply because telemetry is available.

## Friendship and character

- Friendship rises through care, not the clock, pure uptime, or rapid ordinary clicks.
- In v0.11, the same care action could grant friendship at most once every **12 minutes** and the total daily award was at most **7 points**. Repeated care still replenished needs.
- Low social well-being changes Aiko's tone: she may be more reserved or quietly grateful for company, without begging for attention. Spontaneous social-need remarks have at least a **20-minute** interval.
- Greater friendship makes some click, talk, pet, and return responses warmer or more teasing.
- Real tiredness, irritation, workload, and time of day still outrank indiscriminate cheerful responses.

## Persistence and privacy

New needs and friendship reward timestamps are stored in the existing atomic JSON save:

```text
%LOCALAPPDATA%\AikoDesktopPet\state.json
```

Storage remains `version: 1` with no second database or external service. The adaptive weekly profile and window management continue unchanged. The save does not record raw CPU/GPU/RAM time-series, process names, window titles, or keystrokes.

## Known limitations

This release added dialogue for talking, energy drinks, lack of social contact, and growing trust, but there were still no dedicated sprites for every activity. The 73 existing sprites remained the source of visual gestures.

Care balance was provisional pending real-world Windows long-term observation. Actual Windows telemetry could not be validated directly in the Linux test environment. See [v0.12](TAMAGOTCHI_KERN_V012.md) for subsequent balancing changes.
