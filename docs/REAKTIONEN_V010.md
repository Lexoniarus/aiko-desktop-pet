# v0.10 — situations, reaction sequences, and Aiko's voice

## Character and scope

Aiko **is the personification of the computer**, not an independent observer of it. CPU/GPU activity is experienced as her own exertion. Allocated RAM by itself is not equivalent to active work.

She remains observant, usually quiet, controlled, emotionally sensitive, and subtly sarcastic. The Chibi desktop version is also **awkwardly funny**: she may become momentarily uncertain, correct herself mid-thought, make a dry joke, or accidentally say something revealing. She is not relentlessly cute or cheeky.

Tiredness, hunger, irritation, and genuine work must influence how she speaks. There is no Academy schedule, fictional software activity, access to documents or messages, cloud service, or LLM. The release uses 73 approved original sprites.

## Information flow

```text
Local clock ─────┐
Needs ───────────┼──> AikoMind ──> event / response ──> existing animation
Adaptive state ──┤              │                         + first speech bubble
System workload ─┤              │                         + optional follow-up
Mouse clicks ────┘              └──> short social memory (in process)
```

`AdaptiveRoutine` (v0.9) supplies current occupation, observed work duration, rest, and slowly learned habits. `ComputerVoice` (v0.8) supplies confirmed workload changes and periods. `AikoMind` interprets what those events mean to Aiko.

This work did not replace the existing window stack, taskbar geometry, save format, or movable status panel. Two lines are never displayed at once: the optional follow-up appears after a pause of approximately **0.6–2.6 seconds**. A new event cancels any pending follow-up; deliberate silence clears the bubble.

## Behavior instead of random response roulette

### Example click sequence in a calm mood

| Clicks within 7.5 seconds | Interpretation | Behavior |
| --- | --- | --- |
| 1–2 | She notices you | Calm reply, gaze, or wave |
| 3 | Recognizes a pattern | Curious or dry observation |
| 4–5 | Repeatedly interrupted | Irritation or playful sarcasm depending on mood |
| 6–7 | Personal boundary | Brief, firm answer |
| 8 | Final response | A short closing line |
| 9+ | Deliberate silence | No further speech bubble |

At high mood, the middle stages remain playful longer. At low mood she sets boundaries earlier and may stop responding after six clicks. At night the first reactions are quieter. During measured intense work, interruption-specific lines take precedence.

After a gap, the click sequence resets; irritation fades independently. Click count is an ephemeral session state, not a persistent accusation.

### Contextual follow-through

If Aiko is interrupted **at least twice during verified sustained work**, she may refer to those interruptions after the work ends. A brief GPU/CPU spike is not a valid long-work story.

The same principle applies to her uptime and time of day: nighttime work should feel different from daytime work, but Windows uptime alone does not prove she was continuously awake.

A learned weekly pattern is only used to identify unusual activity when enough observations exist. Aiko cannot claim awareness of a task, document, application, or prior offline activity she never observed.

### Short-lived situation memory

The running application retains the current click sequence, interruptions during confirmed work, the latest care action, and a limited period after work completion. The longer-term adaptive profile stores aggregate time buckets instead of individual user actions or raw inputs. On restart, missing personal history is not invented.

## Editorial rules

- Keep natural German text short and credible; only some lines need a punchline.
- Silence, a pause, or a minimal acknowledgment can be the strongest response.
- Awkward humor comes from context and occasional loss of composure, not relentless sarcasm.
- Aiko describes **her own work**, not named CPU/GPU/RAM percentages.
- Never invent knowledge of applications, windows, documents, user intentions, or messages.
- Prior experiences may be mentioned only when actually observed.
- Only the existing `idle`, `waiting`, `review`, `failed`, `waving`, and `jumping` animation groups can be assigned to dialogue.
- Do not invent nonexistent sprite states such as dedicated eating, blushing, or angry poses.

## Windows acceptance checklist

1. Click Aiko quickly ten times: initial acknowledgment, escalated reaction, then temporary silence.
2. Repeat in a positive mood: she should remain playful longer.
3. Run a verifiably intense task, interrupt Aiko repeatedly, and check the after-work callback.
4. Repeat intense work without interruptions: there must be no invented interruption memory.
5. Trigger a two-part line, then interrupt it: stale follow-ups must never appear.
6. Compare daytime with late-night behavior. Uptime alone must not create fake tiredness.
7. Use browser voice input and observe window stacking without stealing browser focus.

The historic v0.10 automated suite contained **167 tests**, but the subtlety of Aiko's personality and the full Windows UI behavior require hands-on validation.
