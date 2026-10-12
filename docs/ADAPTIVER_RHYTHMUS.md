# Aiko's adaptive daily rhythm — v0.9 design

## Product scope

Aiko **personifies the computer she lives on**, while retaining her own personality, short-term needs, time-of-day preferences, and weekly rhythm. CPU, GPU, and RAM signals describe her **workload**, not her whole life. Windows uptime alone is neither continuous wakefulness nor effort.

There is no Academy schedule, Character Chronicles story simulation, LLM, or cloud service.

## Observed inputs

- The local clock and weekday, including existing meal and sleep windows.
- Hardware samples from `system_activity.py`: primarily CPU/GPU workload, with cautious consideration of memory pressure; missing sensors remain unknown.
- System uptime as contextual information, **never as an exhaustion multiplier**.
- Windows idle duration through `GetLastInputInfo`, without reading typed text, window titles, process names, or browser/microphone content.
- Short-term needs from `PetState` and explicit care interactions.

## AdaptiveRoutine: a separately testable domain model

`aiko_pet/adaptive.py` provides `Observation`, `Behaviour`, `AdaptiveMemory`, and `AdaptiveRoutine`. The GUI updates the model only on **new** hardware measurements, approximately every six seconds, on the Tk thread rather than inside the sampling worker. No extra runtime dependency is needed.

The model describes Aiko's current occupation:

| Occupation | Meaning |
| --- | --- |
| `working` | Measured or smoothed workload is high |
| `recovering` | A genuine recent work period has ended |
| `resting` | A quiet period without recent user input |
| `present` | User activity is detected without high computation |
| `wandering` | No other activity dominates, including unknown input |

A separate strain value from 0 to 100 rises during sustained computation and falls during recovery. In **v0.9**, strain did not directly change satiety, mood, or energy, but could influence emotion when energy was limited. **Later releases (from v0.11) added measured workload effects on the care needs.** This document records the original v0.9 behavior.

### Nights and rest

- Aiko may stay awake during **observed high computational work** even at night.
- During quiet evenings she can sleep despite the machine having been on for days. With extremely low energy she may still need to rest while the user is active.
- Explicit manual sleep decisions take precedence.
- A single daytime nap per local calendar day may occur after a long quiet interval, with low energy, or during a reliably quiet learned time. It ends within **45 minutes**, or sooner when meaningful work or input resumes.
- The automatic routine can be disabled from the GUI.
- Missing telemetry falls back to the earlier time-based routine rather than inventing zero-load readings.

### Learning recurring habits

The local profile maintains **168 aggregate buckets** (weekday × hour) containing sampled time, average strain, and presence. The profile decays by a factor of **0.965 per day** (roughly a 19-day half-life).

Each observation contributes at most **30 seconds** so a suspended system, paused application, or system-clock jump cannot become imaginary hours of activity.

After a long unobserved shutdown or pause, stale strain is reduced without treating the gap as observed work or rest. A single unusually intense night is not enough to establish a habit. Repeated observations on separate occurrences of the same weekday are required before a learned expectation becomes reliable.

The learned pattern can influence nap opportunities and whether a period counts as unusual; context-rich dialogue development was initially deferred to a later release.

**Missing data does not mean low utilization.** Snapshots without usable workload information do not update workload buckets. NVIDIA GPU utilization is currently collected with local `nvidia-smi`; no other vendor-specific provider is included. The model never assumes which application or task generated the load.

## Persistence, privacy, and control

Aggregate data is stored in an optional `adaptive` section of the existing atomic save file:

```text
%LOCALAPPDATA%\AikoDesktopPet\state.json
```

The storage schema remains `version: 1`; older saves retain existing values, settings, and panel positions. Invalid or unknown learning fields are ignored.

The settings menu includes:

- **Monitor computer utilization:** disables sampling, including learning observations.
- **Learn my routine:** stops new weekly aggregates and use of learned habits without disabling immediate workload reactions.
- **Clear learned daily pattern:** removes all 168 buckets without deleting care stats or current work state.

No network transfer occurs. NVIDIA measurements use only local `nvidia-smi`. The save file contains no raw CPU/GPU/RAM timeline, websites, text, application names, or keystrokes.

## Covered scenarios

- 72 hours of uninterrupted PC uptime, with idle nights and periods of intensive daytime work, without phantom exhaustion from uptime alone.
- Sustained nighttime computation beyond an ordinary sleep window, followed by sleep after genuine relief.
- Manual sleep and a single short nap, including early wake-up on renewed activity.
- Brief spikes versus long-running work.
- A single unusual workday versus slowly learned repeated weekday patterns.
- Missing sensors, interrupted sampling, disabled learning, reset settings, corrupted saves, and old save versions.

## Known limitations at this release

- v0.9 retained its predecessor's dialogue catalog. Later releases developed linked reaction sequences, click escalation, and richer characterization.
- Tests used a virtual Linux display, not a real long-running Windows 24/7 session.
- Windows sleep/resume, NVIDIA polling, and Tk window stacking still require real Windows testing.
- Learning requires extended real-world observation; short demos only reveal immediate work, rest, and movement changes.
