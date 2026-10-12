# Aiko Desktop Pet — historical release notes (v0.2–v0.13)

This document records how the desktop pet evolved. It is **historical documentation**, not a replacement for the current README or source code. Later versions supersede earlier care formulas and dialogue counts.

The game interface and Aiko's character dialogue remain **German**. Project documentation is maintained in **English**.

---

## v0.13 — Kenney sci-fi panel and sequential emotes

**Interface:** The hover panel was redesigned using visual elements and the layout language of Kenney's **UI Pack: Sci-fi**. A blue header, light controls, and six need/relationship indicators match the supplied `Sample.png` reference. The panel remains movable, remembers its position, and hides as before.

**Expressions:** Kenney pixel emotes play as part of one sequential reaction, for example `question → text → heart`. Optional follow-up speech also appears in order rather than in parallel. Emotes are selected by contextual meaning rather than random decoration. Rapid clicks cancel the previous sequence and may skip an introductory emote so the actual response is visible.

**Font:** The UI uses **Kenney Mini** only if installed on Windows; otherwise it falls back to Segoe UI. No font binary is distributed.

**Unchanged:** v0.12 Tamagotchi care, the adaptive rhythm, all 73 original sprite frames, local saves, hardware observation, and window management. No new runtime dependency, cloud service, or AI inference.

**Preview:** `vorschau/Aiko_v0_13_Reaktionsablauf.gif` shows the actual sequence. See [v0.13 emote/UI design](KENNEY_UI_UND_EMOTES_V013.md) for more.

## v0.12 — affection as a distinct need

The hover and detailed status panels now display **six values**: satiety, mood, energy, social, affection, and friendship (levels 1–10). Affection represents being cared for and is refilled mainly by **petting**.

Petting now grants **+25 affection, +6 mood, +2 social, and no energy**. Playing and talking retain distinct purposes.

Friendship grows from **meaningful care** only when the action's primary target need was at most 80 beforehand. Varied helpful care receives a modest bonus. The same care action can grant friendship at most every **12 minutes**, with a daily cap of **5 points**. Energy drinks and sleeping do not directly award friendship.

Workload still influences satiety, mood, and energy; affection is not drained faster simply because CPU/GPU are busy. Low affection and low social connection trigger different, reserved character responses.

Old saves are migrated without losing earlier stats or friendship: affection starts at **75** when newly introduced. All 73 sprites and window management remain unchanged.

**Tests:** 220 passed under Linux/Xvfb, not a full native Windows endurance test. See [v0.12 core](TAMAGOTCHI_KERN_V012.md) and [test report](TESTBERICHT_V012.md).

## v0.11 — social need, energy drinks, and friendship

Aiko gained a distinct **social** need, a friendship score and level, and more deliberate care actions.

- **Talk:** +26 social, +5 mood, −1 energy.
- **Energy drink:** +10 energy per click, repeatable up to 100.
- **Play:** +23 mood, consumes 9 energy and 4 satiety.
- **Feed:** +27 satiety with a small mood bonus.
- **Friendship:** increased gradually through care, originally limited to one reward per action every 12 minutes and **7 points per day**. That rule was revised in v0.12.
- **Computer utilization:** confirmed intense CPU/GPU work increased satiety consumption and energy/mood drain. High reserved RAM alone was not treated as work; unobserved hours were not charged retroactively.

Social deprivation and growing trust influence Aiko's dialogue without overriding tiredness, irritation, or real workload. The interface used five gauges at that point.

**Tests:** 195 passed on Linux/Xvfb. See [v0.11 core](TAMAGOTCHI_KERN_V011.md) and [test report](TESTBERICHT_V011.md).

## v0.10 — linked reactions and an awkward sense of humor

v0.10 used the adaptive foundation to make Aiko less like a random quote generator.

- Click bursts progress from acknowledgment to curiosity, dry teasing, growing irritation, a final reply, and sometimes **deliberate silence**.
- The sequence changes with mood, tiredness, time of day, and measured ongoing work.
- After repeated interruptions during **verified prolonged work**, Aiko can refer to the interruptions after the work ends. Short spikes do not create fictional long-work memories.
- Some reactions contain a delayed second sentence: she can pause, correct herself, or reveal an awkward thought.
- Canceled follow-ups do not reappear later. Silence clears the bubble.
- Forty generic earlier entries were removed. At this point the catalog contained **339 primary entries** across 67 categories, with 109 supporting a second line.

The taskbar, local save, gaze, and multi-window system were kept intact.

**Tests:** 167 passed under Linux/Xvfb. See [reactions](REAKTIONEN_V010.md) and [test report](TESTBERICHT_V010.md).

## v0.9 — adaptive routine and local usage learning

Aiko began slowly learning when the computer is usually busy and when it is quiet, without treating **Windows uptime as uninterrupted work or wakefulness**.

- Occupation state: working, recovering, resting, present, or wandering.
- Short work spikes influence Aiko less than sustained computation.
- At night she can stay awake to work, then sleep during actual quiet periods, even if Windows has been running for days.
- A short daytime nap can occur when needed, within a bounded duration.
- An aggregated, local **168-bucket** weekday/hour profile gradually learns recurring patterns over multiple weeks; unusual single days do not immediately rewrite her habits.
- Settings allow monitoring and habit learning to be disabled independently; the learned profile can be cleared without deleting her care state.

This release intentionally deferred the complete dialogue overhaul, retaining the earlier response set. It preserved window management and save compatibility.

**Tests:** 147 passed, including simulations of 72-hour uptime, overnight work, naps, and learning over several weeks. See [adaptive routine](ADAPTIVER_RHYTHMUS.md).

## v0.8 — central window stacking and focus behavior

The Windows Z-order system was unified so Aiko, her bubble, the status/action panel, and settings are managed together.

- Showing or moving a bubble no longer calls `lift()` on that window alone.
- When “always on top” is enabled, a Windows check runs approximately every **1.5 seconds** and repairs a genuine occlusion, with rate limits.
- The repair uses Win32 `SetWindowPos` with `SWP_NOACTIVATE` to avoid stealing keyboard focus from a browser or microphone session.
- Disabling “always on top” disables these automatic topmost repairs.
- The panel remains draggable and hideable, and saved progress and dialogue logic are unchanged.

A native Windows test involving browser speech recognition is still important; the original Linux tests simulated key Win32 paths.

**Tests:** 120 passed on Linux/Xvfb.

## v0.7 — subjective workload and a movable status panel

Aiko is **the voice of the computer**, not a component monitor reading CPU/GPU/RAM numbers aloud. She describes her subjective effort.

- Measured CPU/GPU work is the main workload signal; memory pressure contributes cautiously.
- Longer work phases and actual recovery can trigger context-appropriate remarks. A quick spike must not trigger an exaggerated exhaustion story.
- Hardware values can still appear as diagnostics in the status panel, while dialogue remains personal and character-specific.
- The speech bubble is attached to Aiko's head, **not** to the movable status panel.
- The status/action panel can be dragged by its header, keeps its position locally, appears on hover, and hides when dismissed. The user can reset it to Aiko's side through settings.
- The existing sprite collection provides reactions; unavailable animations are not invented.

The original v0.7 catalog had 236 lines across 37 events after edits. These figures are historical; later releases expanded and reshaped the catalog.

## Earlier versions — v0.2 through v0.6

| Version | Main milestone |
| --- | --- |
| **v0.2** | Taskbar-bound movement, hover care controls, and automatic wandering replaced free dragging. |
| **v0.3** | Time-of-day and weekday awareness; full-desktop cursor tracking without the earlier distance cutoff. Some early Academy-themed rules were removed later. |
| **v0.4** | Expanded handwritten dialogue, mood-aware reactions, spontaneous comments, and startup positioning improvements; fictional Academy obligations removed. |
| **v0.5** | Local CPU/GPU/RAM observation and five-digit status access; first attempts at reactions to system work. |
| **v0.6** | Fixed bar-fill geometry, hover/popup dismissal, settings accessibility, and response timing for large workload changes. |

The concept gradually shifted from a simple animated companion to a Tamagotchi-like **personification of the user's own machine** with a private daily rhythm, long-term care, and restrained character humor.

## Windows installation and persistence

Requirements: Windows 10/11, Python 3.11 or later, and Tkinter.

1. Close the currently running Aiko.
2. Extract the downloaded ZIP rather than launching from inside it.
3. Start `Aiko_starten.bat`. Use `Aiko_starten_debug.bat` to view error output.
4. Saved progress under `%LOCALAPPDATA%\AikoDesktopPet\state.json` is carried forward.

No extra runtime Python package, account, cloud service, or paid model API is required. An optional Windows EXE can be built with PyInstaller:

```bat
py -m pip install pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name AikoDesktopPet --add-data "aiko_pet\assets;aiko_pet\assets" --add-data "aiko_pet\data;aiko_pet\data" Aiko_Pet.pyw
```

## Privacy and platform limitations

System observations use Windows APIs and optional local NVIDIA `nvidia-smi`. They do **not** collect raw keystrokes, open documents, browser contents, process lists, or window titles. No data is transmitted to a remote server. Unsupported sensors are shown as unavailable, not silently filled with fictional zeroes.

The majority of automated GUI acceptance was performed under Linux/Xvfb. That does not fully validate Windows transparency, taskbar alignment, browser microphone focus/overlays, NVIDIA telemetry, or high-DPI behavior. Actual Windows practice is still required.

For current behavior and setup, refer to the [README](../README.md), not historical mechanics from an older release.
