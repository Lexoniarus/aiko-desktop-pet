# Adaptive cursor perception and interaction concept

> **Latest agreed direction, 2026-10-27:**
> [staged attention and warning plan](CURSOR_ATTENTION_STAGES_PLAN.md).
> Movement builds transient attention; calm reduces it. Feeling qualification
> follows situational assessment, and a displayed warning precedes new fear.
> This revision is implemented in the nine planned steps; practical user
> acceptance is pending. Historical implemented status below applies to the
> preceding revision only.

> **Current product decision, 2026-10-27:** the
> [revised behavior and module plan](ADAPTIVE_CURSOR_REWORK_PLAN.md) supersedes
> conflicting historical assumptions below. Frontal full-direction gaze is the
> normal posture; body turns express selected intent. Curiosity/fear receive
> short Moodlets, and reliable pointer access to controls takes precedence over
> the earlier idea of intentionally making Aiko harder to click. This is a
> implemented revision with practical visual acceptance still pending.

> **Preserved product concept; implementation covers a subset.** Recorded on
> 2026-10-19 from the owner's German conceptual draft v1.0 dated 2026-10-15.
> Current-owner notes were checked against `fd8414a` (main after PR #10).
> Recording the concept does not enable cursor flight, approach or touch,
> select the next feature or approve final tuning values. The implemented
> observation, bounded approach/retreat and small Idle steps are recorded in the
> [implementation ledger](ADAPTIVE_CURSOR_IMPLEMENTATION_PLAN.md); continuous
> following and autonomous touch remain future work.

This preserves the substance of **“Gesamtkonzept – Aikos adaptive
Mauswahrnehmung und -interaktion”** in English technical-document form.
The product intent is retained while older paths, illustrative scales and
integration assumptions are identified explicitly.

Related references: [current architecture](ARCHITECTURE.md),
[module ownership and commit plan, 2026-10-27](ADAPTIVE_CURSOR_IMPLEMENTATION_PLAN.md),
[UI window contract](UI_WINDOW_CONTRACT.md),
[World behavior](WORLD_OBJECT_CONTRACTS.md),
[fun and mood](FUN_MOOD_SYSTEM.md) and
[social and entertainment concept](SOCIAL_ENTERTAINMENT_CONCEPT.md).

## Product direction

Extend the existing “Maus beobachten” option from eye tracking into contextual
cursor interpretation. The cursor represents a possible sign of the player's
presence. Aiko should combine curiosity, caution, startle and growing trust
rather than react identically to every movement.

The intended results are visible autonomy, playful interaction without clicks,
friendship expressed through behavior and reuse of the existing input,
movement, animation, click and dialogue systems. All evaluation is local and
deterministic for the same inputs and policy state; no AI API is needed.

The supplied paper establishes the overall product idea, state-sensitive
behavior, extension of the existing mouse-observation option and priority for
successful user interactions. It leaves thresholds, weights, recovery curves,
movement speeds and the touch animation open for technical design and playtest.

## Current main comparison

| Area | Checked state at `fd8414a` | Consequence for this concept |
| --- | --- | --- |
| Pointer observation | Global pointer sampling and short-lived `CursorAttention` history exist | Reuse observations rather than adding a second global input system |
| Gaze | Existing gaze policy and rendering support cursor attention | Do not replace gaze ownership |
| Direct contact | `ContactCoordinator` handles entry/click behavior and `HoverUi` owns accessory windows | Preserve successful user contact and current action guards |
| Movement | Domain movement policies, desktop walking execution and World goal/focus owners exist | Cursor intentions need arbitration through these owners |
| Dialogue | Existing relationship/state context and sequential reaction playback exist | Select authored reactions through the current mind |
| Proposed cursor interpretation | No combined speed/direction threat model, curiosity approach, flight or autonomous touch policy | These remain future behavior |

The earlier paper speaks of “six status values”: friendship, affection, mood,
energy, satiety and social need. Current main has **six individual indicators
plus overall mood**, including the separate **fun** need. Preserve the original
state-sensitive intent, but decide fun's relevance explicitly during design.
Do not introduce a second mood or omit the current need model accidentally.

The paper's 0–100 friendship examples are illustrative. Current dialogue uses
friendship levels 1–10 with four familiarity stages. Cursor trust should derive
from the canonical friendship state; a new persistent friendship scale is not
part of this concept.

## Observable situations and possible behavior

| Situation | Intended possible response |
| --- | --- |
| Cursor far away | Ignore it or observe occasionally |
| Slow cursor movement | Track with the eyes and remain attentive |
| Slow approach toward Aiko | Watch cautiously, usually remain calm |
| Fast approach toward Aiko | Startle, step away or flee if allowed |
| Fast movement away from Aiko | Observe without treating speed alone as a threat |
| Cursor stationary for a while | Curiosity can grow and lead to approach |
| Cursor within actual reach | Attempt a cautious touch |
| Sudden movement during touch | Startle, retreat or respond playfully |
| Repeated hectic movements | Become more cautious, distrustful or irritated |
| High friendship and favorable mood | More confident, playful contact |

These are contextual possibilities, not independent event-to-animation rules.
The same movement can produce a different decision according to current needs,
trust, protected activities and recent cursor history.

## Friendship and state interpretation

Friendship primarily supplies long-term trust. At low familiarity, rapid
approach can cause Aiko to move away before the player reaches her. With growing
trust, proximity becomes easier and Aiko can initiate contact herself.
Friendship does not make her immune to a sudden startle.

The original illustrative bands are retained for product discussion only:

| Illustrative scale | Intended progression |
| --- | --- |
| 0–20: distrustful | High flight tendency; careful approach matters |
| 21–40: cautious | More tolerance of proximity; early curious exploration |
| 41–60: familiar | Easier direct contact; a startle more often causes a short retreat |
| 61–80: trusting | Low flight tendency and more self-initiated contact |
| 81–100: closely bonded | Mostly confident/playful; occasional startle remains |

These are neither final probabilities nor hard thresholds. The proposed
behavior should vary gradually. The player learns to approach calmly while
Aiko expresses increasing familiarity through easier, more confident contact.
This does not unlock abilities or add a separate reward system.

The original paper assigns these roles:

| State | Intended influence |
| --- | --- |
| Friendship | Long-term trust, perceived threat and willingness to flee |
| Affection | Desire for closeness and contact attempts |
| Overall mood | Playfulness, caution, indifference or irritation |
| Energy | Ability and endurance for approach or retreat |
| Satiety | Physical comfort; hunger may reduce cursor interest or increase irritability |
| Social need | Interest in contact despite some underlying caution |

Combine these into one decision. They must not independently start competing
animations. A close friend in a bad mood may want space without being afraid;
an exhausted Aiko may startle without being able to sustain a flight; a lonely
Aiko may approach cautiously. The mapping from canonical need values to these
influences remains to be tuned, including the current fun need.

## Perception, interpretation and temporal behavior

The proposed perception input includes pointer position, smoothed speed,
direction relative to Aiko, distance and stationary duration. Interpretation
combines perceived threat, curiosity, familiarity and actual reachability with
current state, sleep and ongoing activities.

The abstract result can be ignore, observe, freeze, avoid, flee, approach or
touch. An independent UI-free policy, provisionally `CursorBehaviourPolicy`,
may choose that intent; it must not move windows or render animations itself.

Distinguish a brief **startle** from longer-lived **fear/distrust**. Startle can
occur at any friendship level; trust influences recovery and the likelihood of
continued retreat. The original examples contrast a low-trust Aiko who flees
and stays cautious with a high-trust Aiko who briefly recoils and may return.

Threat may rise quickly and decay more slowly; curiosity grows during calm
behavior and can drop after a startle. Use transient policy state initially,
not new saved Tamagotchi needs. Minimum response times, hysteresis, reaction
cooldowns and recovery periods prevent jitter and repeated reactions.

Measurements must scale meaningfully with resolution and Aiko's sprite size.
Smooth out isolated speed spikes. Verify whether the existing sample cadence
can detect the relevant fast movements before choosing thresholds. Reuse
existing global pointer readings; Windows input details stay in adapters.

## Hover, clicks and intentional contact

### Before the player reaches Aiko

A threatening approach may cause movement before hover/contact begins. At low
friendship, the resulting difficulty in clicking her is an intentional part
of the proposed play experience.

### After successful contact

Once the player reaches Aiko and begins hover or a click interaction, direct
operation wins. Autonomous flight must stop or be suppressed. The toolbar and
existing click policy continue to work reliably; a startled expression may
remain, but movement must not take the controls away.

The existing repeated-click, friendship, mood, fatigue and busy-state policy is
retained. Cursor behavior covers the approach to contact; it does not replace
the interpretation of deliberate clicks. Existing World committed-action
guards remain authoritative for which actions are available after contact.

### Aiko reaches a stationary cursor

Autonomous approach must not automatically open the toolbar merely because
the moving sprite enters the stationary pointer. Distinguish contact caused
by the player's pointer movement from contact caused by Aiko's movement.
A subsequent deliberate pointer action or click enables normal operation.
Exact event attribution is an implementation design question, not an assumed
property of Tk's enter event.

### Accessory windows

While the user actively operates the toolbar, settings or another control,
cursor flight/approach must not compete. A visible but unused settings window
must not suppress normal behavior indefinitely. Preserve the existing
distinction between visible and actively engaged interfaces.

## Motion coordination and spatial limits

The original proposed cursor-related priority order is:

1. Active user interaction: successful hover, clicks and control operation.
2. Protected activities: sleep, minigames and non-interruptible animations.
3. Flight, which may interrupt ordinary autonomous walking.
4. Curious approach when no higher-priority activity owns behavior.
5. Ordinary autonomous wandering.

This is not a replacement for the current World focus/ownership contract.
Consumption, custody, committed object actions, search/inspection and required
feedback must be reconciled explicitly before any cursor movement is enabled.
Do not infer that flight may preempt a committed object goal. Cursor perception
can continue during a protected action without gaining permission to move.

Keep the existing horizontal taskbar movement boundary. Retreat should move
away from the cursor where feasible; approach should move toward a reachable
stationary cursor. At an edge, use a bounded reaction or startle without
repeated impossible flight attempts. A cursor high in the middle of the screen
does not become reachable just because its horizontal coordinate is close.

There must remain one movement execution path and position authority. Cursor
intentions must not introduce another writer of Aiko's position or a parallel
walking loop.

## Curious approach and touch

The intended sequence is:

1. Notice a stationary cursor and look toward it.
2. Wait and assess whether it remains calm.
3. Approach cautiously if curiosity, state and activity protection permit it.
4. Attempt contact only after actual reach is established.
5. Respond with curiosity/satisfaction if it stays still, or a startle/playful
   retreat if it moves suddenly.

Successful touch does not automatically award friendship or change other
needs. Leaving the mouse stationary must not farm progression. Contact is a
visible consequence of existing trust, not a new reward source.

The supplied paper suggests existing look and left/right walking/running
animations for observation and travel. A dedicated touch animation may be
added later, but its artwork, timing and actual asset suitability are not yet
selected. Do not invent a finished touch animation from a symbolic state name.

## Settings and user control

| Existing option | Proposed extended meaning |
| --- | --- |
| “Maus beobachten” on | Gaze and contextual autonomous cursor responses are allowed |
| “Maus beobachten” off | No autonomous cursor gaze, flight, approach or touch; direct mouse operation remains available |
| “An der Taskleiste laufen” off | No cursor-driven relocation initially; gaze and expression can still respond |
| Automatic daily routine | Existing sleep/activity protections still apply |

No separate fear toggle is required by the initial concept. Preserve F2 as the
direct way to open/pin the toolbar. Mouse operation remains available regardless
of autonomous cursor settings. These are proposed semantics for the extension,
not a claim that all such behavior exists today.

## Current ownership map

The original paths such as `ui/animated_pet.py`, `presentation/gaze.py`,
`presentation/movement.py`, `ui/hover_ui.py` and `personality/click_policy.py`
refer to an older layout. Use current canonical owners instead:

| Responsibility | Existing owner/reference |
| --- | --- |
| Pointer sampling and Tk bindings | `desktop/input.py` |
| Application cursor observations | `application/cursor_observation.py` |
| Short-lived cursor history | `pet/mind/cursor_attention.py` |
| Gaze policy | `pet/animation/gaze.py` |
| Domain movement and walking execution | `pet/movement/` and `desktop/walk_runtime.py` |
| Character rendering and reaction playback | `ui/pet_view/` |
| Entry/click coordination and character click interpretation | `application/contact.py` and `pet/mind/click_policy.py` |
| Toolbar/settings/game windows and engagement | `ui/windows/hover_ui.py` |
| Attention, tick order and visual observations | `application/attention.py`, `desktop/runtime.py` and `desktop/visual_observation.py` |
| World commitments, custody and focused actions | [Current World and architecture contracts](WORLD_OBJECT_CONTRACTS.md) |

This map identifies reuse points, not final class placement for the proposed
perception and decision components. Keep policy tests independent of Tk and
OS sensors. Avoid hidden secondary state owners, shadow input fields or
reintroducing retired imports.

## Balance principles

- Flight ends and has a recovery period; it does not form an endless chase.
- Small speed changes do not alternate movement directions uncontrollably.
- Hectic pointer motion cannot produce an animation or dialogue flood.
- Successful direct contact provides reliable controls.
- Friendship changes behavior gradually, without arbitrary progression jumps.
- Even a trusting Aiko need not pursue the cursor continuously.
- Cursor observation and touch do not automatically mutate needs/friendship.
- Variance must remain understandable; deterministic input/history tests and
  practical playtests should explain why a response happened.

## Future acceptance scenarios

These describe intended checks for a future implementation, not passed tests.

| Scenario | Expected result |
| --- | --- |
| Low friendship, rapid approach | Flight before contact is possible when activity guards permit it |
| High friendship, equivalent approach | Considerably lower sustained flight tendency |
| Slow approach | Aiko more often observes without moving away |
| Stationary reachable pointer | Curiosity may eventually lead to approach |
| Aiko reaches the stationary pointer | No accidental toolbar activation |
| Player reaches Aiko and clicks | Existing click interpretation runs reliably |
| Player moves into toolbar controls | No competing flight |
| Aiko is exhausted | Shorter or absent flight movement |
| Aiko sleeps or plays a minigame | Protected activity continues |
| Cursor observation disabled | No autonomous cursor response; normal controls still work |
| Taskbar walking disabled | No cursor-driven position change |
| Aiko is at the screen edge | No invalid or endless movement attempts |
| Pointer is outside reachable taskbar space | No impossible touch/approach loop |
| Repeated abrupt movements | Bounded reactions without dialogue/animation flooding |
| Settings visible but unused | Existing engagement rules permit normal behavior |
| Committed World action or protected story | Existing focus and interruption rules remain authoritative |
| Cursor stays still indefinitely | No automatic friendship/need farming |

Exercise temporal policy behavior with controlled inputs, then validate actual
hover origin, click reliability, scaling, F2 and taskbar limits on Windows with
an isolated save. Exact speeds, distances, weights, recovery curves and touch
art should be chosen against real sprite size and animation/movement timing.

## Delivery discussion

The complete concept is broader than a small gaze or emote change. Its core
value is friendship becoming visible through everyday contact: initial caution
can develop into confidence and self-initiated play. Any smaller first scope
should state which part of that experience it delivers and which remains open.

It shares attention and presentation with the social concept but does not
require its providers, translation model or cache. Neither concept determines
the next implementation by being recorded here.
