# Bubble dialogue review workbook

> **Historical wording snapshot.** The subsequent complete German dialogue
> revision is documented in [DIALOGUE_REVISION_PLAN.md](DIALOGUE_REVISION_PLAN.md).
> The rows below preserve the earlier originals and B2 review decisions;
> current runtime wording and filters are owned by the indexed sources under
> `aiko_pet/data/dialogues/de/`.

> **Editorial review only.** Created 2026-10-19 on
> `feature/social-optimization`, from baseline `f4c6e3f`.
> B2 review on 2026-10-19: all **138 object sequences** and **three food
> fallbacks** reviewed. The 90 changed object proposals and three fallback
> proposals are implemented on this branch; other review rows are unchanged.

The review unit is one **complete sequence**, including all text bubbles in
playback order. Review its combined thought, tone and ending together.
Single-bubble reactions are included as one-step sequences. The two editable
review columns are **Reviewed?** (`No` / `Yes`) and **New text proposal** (empty
until a complete replacement is discussed). `Yes` records editorial review;
it does not by itself approve a runtime edit.

## Coverage and source snapshot

- **1,052 catalogue sequences** across **119 events**: 48 stories and 1,004
  short reactions. There are 898 one-text, 106 two-text and 48 four-text
  sequences: **1,302 authored text bubbles** in total.
- **16 additional review rows**: 12 care fallbacks, one combined RPS countdown,
  fallback farewell, invalid-placement feedback and a dynamic notification
  template. Overall: **1,068 review rows**; B2 marks **141 reviewed**.
- Original snapshot: former `aiko_pet/data/dialogues.de.json`, catalogue v2,
  SHA-256 `3373c6d45ecbc854041d790b20ddb7d76d0ad0a1af154e4dc6f2e93c1d688b13`.
- Additional bubble copy: [texts.de.json](../aiko_pet/data/texts.de.json).
  Status hints, toolbar/settings labels and game-panel labels that are not
  spoken in the character bubble are outside this workbook.
- B2 runtime catalogue SHA-256: `83da025a28f1100630b44ce25de8551bfa2e2c3da924b07158a4b52cf5f1e9b7`.
  Original sequence cells retain the baseline for comparison; implemented
  replacements are in **New text proposal**. Blank proposal on a reviewed
  object row means its full sequence was retained.
- This is an editable review snapshot. Preserve IDs and review/proposal cells
  when reconciling later source changes; do not regenerate over reviewed work.
  Runtime wording remains owned by its JSON resources.

## Reading a row

The event paragraph describes **why this family is requested**; each row's
filters describe **which variant may match**. Both apply with the shared rules
below. No row filters means no additional restrictions, not guaranteed speech.

- **Stage**: `acquaintance` = Lv 1-2, `familiar` = Lv 3-5, `friend` = Lv 6-8,
  `close` = Lv 9-10. Several listed stages are alternatives.
- **Mood/tone** is a primary emotion, not numeric Laune. Listed moods are
  alternatives. Care can pass an explicit pre-care tone.
- **Needs/states**: all listed states must be present together (AND), from
  simultaneous need flags plus primary mood. Different filter dimensions also
  combine with AND; an omitted filter imposes no restriction.
- **Period/day**: alternatives within each dimension. Period calculation does
  not depend on the automatic-routine switch.
- **Presence: any** means no presence filter, not that the user is absent.
  **Presence: confirmed** requires present=True.
- **Short** can contain two text bubbles; **story** is a separate presentation.
- **Cooldown/weight** are source seconds and base weight. Cooldown is a
  rotation preference that can be relaxed, not an absolute prohibition.
- **Sequence** lists baseline German text in numbered bubbles and includes
  emotes/pauses at their actual positions. Emotes are assets, not spoken text.
  Default emotes last 800 ms and pauses 600 ms unless a duration is specified.
- B2 object proposals use explicit `item_{indef|def|poss|pron}_{nom|acc|dat}`
  fields; capitalized `Item_...` starts a sentence. Names require learned
  identity; unknown forms use “Gegenstand” and no invented possession. Legacy
  `{item}` remains a bare-label field for compatibility. Care fallbacks fill
  `{food}` with a complete indefinite nominative phrase; external
  notifications supply `{title}` and `{message}`. These are templates, not
  extra authored variants.
- **Animation** is the catalogue suggestion. Care can replace it with petting/
  eating. Object phases use their own animation (`animate=False` for reaction
  playback), and game/farewell timelines also own their animation.

## Shared selection and playback rules

Sources: [catalogue](../aiko_pet/pet/mind/catalog.py),
[mind/context](../aiko_pet/pet/mind/mind.py),
[click policy](../aiko_pet/pet/mind/click_policy.py),
[attention](../aiko_pet/application/attention.py),
[desktop guards](../aiko_pet/desktop/attention_runtime.py),
[balance](../aiko_pet/data/balance.json) and
[reaction player](../aiko_pet/ui/pet_view/reaction_player.py).

### Emotional context

Primary emotion follows this priority; first matching branch wins:

1. Sleeping -> `asleep`.
2. Temporary irritation active -> `irritated` (normally 13 s).
3. Observed strain >=75 and energy <=55 -> `tired`.
4. Observed strain >=60 and mood <=48 -> `withdrawn`.
5. Energy <=25 -> `tired`.
6. Satiety <=25 -> `hungry`.
7. Mood <=28 -> `withdrawn`.
8. Social <=23 -> `lonely`.
9. Affection <=23 -> `seeking_affection`.
10. Temporary warmth active -> `warm` (70 s after petting, 45 s after other
    applicable care).
11. Mood >=82 AND fun >=45 AND energy >=45 -> `playful`.
12. Otherwise -> `calm`.

Independent need flags: hungry at satiety <=25, tired at energy <=25, lonely
at social <=27, seeking_affection at affection <=24. Some thresholds differ
from the primary emotion deliberately. Care uses the snapshot **before** its
reward changes needs or crosses a friendship-level boundary; other reactions
use current observed context.

### Matching and repetition

- Event, requested presentation and every row filter must match. Maximum
  specificity wins: has-mood-filter + has-stage-filter + number-of-required-needs.
  Period/day/presence are filters but not additional specificity points.
- Actual weight = base weight multiplied by
  `1 + 2*(has mood filter) + 2*(has period filter) + 2*(has weekday filter)`.
- Stories exhaust their matching rotation pool before repeating. The recent
  six IDs and per-line cooldown prefer fresh copy. Exhausted-pool fallbacks
  relax cooldown/recency, never the relationship or other matching filters.
- Intentional talk requests story unless supplied tone is asleep. Short talk
  is fallback when no story matches. Deliberate care confirms presence.
- A spontaneous idle/low_mood/tired/social_low/affection_low remark can become
  a matching talk story when not focused, presence=True, >=600 s since the
  last spontaneous story and a 20% draw succeeds. Other event choices are
  not replaced through this story route.

### Timing and interaction guards

- Ordinary spontaneous remarks require speech enabled, awake, quiet controls,
  no protected foreground/playback, no game/visible speech, and >=85 s since
  speech. Initial comment timer: 180-360 s; later timers: 175-360 s. Need
  requests can preempt an ordinary comment after shared gates permit them.
- Care requests pick the lowest of satiety/social/affection/fun at <=70.
  Ties prefer feed, talk, pet, play. Selected request spacing is 1,800 s;
  accepted care provides 180 s of request quiet time.
- Click bursts reset after gaps >7.5 s. At >=4 clicks, non-cheerful clicks may
  cause irritation before selection. At >=3 clicks an initial emote can be
  removed. Click-event selection precedes row filters; a mood mismatch can
  therefore still prevent a reaction. Higher-priority click branches apply
  before lower ones; withdrawn clicks >=7 and ordinary clicks after the last
  boundary become silent.
- Story left-clicks advance to the next text, skipping intermediate emotes and
  pauses. They do not count as teasing clicks. Replacement/cancellation
  invalidates timers; uninterrupted playback includes all listed beats.
- Snapshot text duration: `min(8000, max(2800, characters * 58))` ms. The later
  [social timing change](SOCIAL_CONTENT.md#bubble-reading-time) applies to
  current `talk` sequences; this historical workbook retains its baseline.
  Each text
  is limited to 125 characters. Short reactions allow <=2 text bubbles;
  stories <=5 (all current stories have four).
- Workload comments require real fresh measurements. Occasional comments use
  a 370 s quiet interval and samples <=65 s old; transitions use samples
  <=25 s old and normally >=18 s between changes (recovery is special).
  Observed recovery lasts 110 s; post-work reflections use their own gates.
- A catalogue entry is not proof it can be reached through every desktop
  action. Route caveats are included with events such as sleep_click,
  computer_uptime and legacy play care. Object completion can use handover
  care wording instead of its normal object-finished event.

### Local time periods

The [packaged routine](../aiko_pet/data/routine.de.json) supplies these local
wall-time slots. They describe context, not user obligations.

| Day group | Period start times |
| --- | --- |
| Monday-Friday | 00:00 night; 07:30 breakfast; 09:00 quiet; 12:30 lunch; 14:00 free; 18:30 dinner; 20:00 evening; 23:30 night |
| Saturday | 00:00 night; 09:00 breakfast; 11:30 free; 13:30 lunch; 15:00 free; 19:00 dinner; 20:30 evening |
| Sunday | 00:00 night; 09:00 breakfast; 11:30 free; 13:30 lunch; 15:00 free; 19:00 dinner; 20:30 evening; 23:30 night |

## Event index

Every source text is reproduced in full. Ellipses inside text are original
wording, not omitted content. Talk stories appear before the short talk rows.

| Area | Event | Sequences |
| --- | --- | --- |
| Conversation and greetings | [talk](#talk) | 68 |
| Conversation and greetings | [talk_busy](#talk_busy) | 15 |
| Conversation and greetings | [greeting](#greeting) | 24 |
| Conversation and greetings | [farewell](#farewell) | 12 |
| Conversation and greetings | [return](#return) | 28 |
| Conversation and greetings | [return_working](#return_working) | 4 |
| Conversation and greetings | [return_after_work](#return_after_work) | 3 |
| Direct clicks | [click_left](#click_left) | 33 |
| Direct clicks | [click_right](#click_right) | 18 |
| Direct clicks | [click_notice](#click_notice) | 4 |
| Direct clicks | [click_notice_playful](#click_notice_playful) | 3 |
| Direct clicks | [click_tease](#click_tease) | 5 |
| Direct clicks | [click_tease_more](#click_tease_more) | 3 |
| Direct clicks | [click_boundary](#click_boundary) | 3 |
| Direct clicks | [click_last_word](#click_last_word) | 3 |
| Direct clicks | [click_sleepy](#click_sleepy) | 4 |
| Direct clicks | [click_flustered](#click_flustered) | 4 |
| Direct clicks | [click_during_work](#click_during_work) | 4 |
| Direct clicks | [click_work_repeat](#click_work_repeat) | 3 |
| Direct clicks | [click_work_boundary](#click_work_boundary) | 4 |
| Direct clicks | [click_after_work](#click_after_work) | 4 |
| Direct clicks | [click_withdrawn](#click_withdrawn) | 4 |
| Direct clicks | [click_notice_withdrawn](#click_notice_withdrawn) | 3 |
| Direct clicks | [click_withdrawn_boundary](#click_withdrawn_boundary) | 4 |
| Direct clicks | [click_weary](#click_weary) | 4 |
| Direct clicks | [click_night](#click_night) | 3 |
| Direct clicks | [click_lonely](#click_lonely) | 3 |
| Direct clicks | [click_affection_low](#click_affection_low) | 4 |
| Direct clicks | [click_at_ease](#click_at_ease) | 3 |
| Direct clicks | [rapid_click](#rapid_click) | 7 |
| Direct clicks | [sleep_click](#sleep_click) | 16 |
| Care and need requests | [pet](#pet) | 33 |
| Care and need requests | [pet_during_work](#pet_during_work) | 15 |
| Care and need requests | [pet_needs_affection](#pet_needs_affection) | 15 |
| Care and need requests | [feed_meal](#feed_meal) | 26 |
| Care and need requests | [feed_snack](#feed_snack) | 24 |
| Care and need requests | [feed_full](#feed_full) | 14 |
| Care and need requests | [feed_repeat](#feed_repeat) | 15 |
| Care and need requests | [play](#play) | 27 |
| Care and need requests | [play_tired](#play_tired) | 16 |
| Care and need requests | [energy_drink](#energy_drink) | 5 |
| Care and need requests | [energy_drink_full](#energy_drink_full) | 3 |
| Care and need requests | [sleep](#sleep) | 16 |
| Care and need requests | [wake](#wake) | 17 |
| Care and need requests | [care_request_feed](#care_request_feed) | 15 |
| Care and need requests | [care_request_talk](#care_request_talk) | 15 |
| Care and need requests | [care_request_pet](#care_request_pet) | 15 |
| Care and need requests | [care_request_play](#care_request_play) | 15 |
| Spontaneous thoughts and calendar | [idle](#idle) | 20 |
| Spontaneous thoughts and calendar | [hungry](#hungry) | 5 |
| Spontaneous thoughts and calendar | [social_low](#social_low) | 3 |
| Spontaneous thoughts and calendar | [affection_low](#affection_low) | 4 |
| Spontaneous thoughts and calendar | [tired](#tired) | 5 |
| Spontaneous thoughts and calendar | [low_mood](#low_mood) | 4 |
| Spontaneous thoughts and calendar | [morning](#morning) | 15 |
| Spontaneous thoughts and calendar | [midday](#midday) | 9 |
| Spontaneous thoughts and calendar | [evening](#evening) | 11 |
| Spontaneous thoughts and calendar | [night](#night) | 18 |
| Spontaneous thoughts and calendar | [weekend](#weekend) | 9 |
| Spontaneous thoughts and calendar | [monday](#monday) | 10 |
| Spontaneous thoughts and calendar | [friday](#friday) | 10 |
| Spontaneous thoughts and calendar | [quiet_alone](#quiet_alone) | 4 |
| Spontaneous thoughts and calendar | [quiet_together](#quiet_together) | 4 |
| Observed work and workload | [computer_effort_rising](#computer_effort_rising) | 14 |
| Observed work and workload | [computer_effort_heavy](#computer_effort_heavy) | 12 |
| Observed work and workload | [computer_effort_peak](#computer_effort_peak) | 13 |
| Observed work and workload | [computer_effort_easing](#computer_effort_easing) | 13 |
| Observed work and workload | [computer_effort_recovered](#computer_effort_recovered) | 14 |
| Observed work and workload | [computer_effort_recovered_peak](#computer_effort_recovered_peak) | 9 |
| Observed work and workload | [computer_effort_rest](#computer_effort_rest) | 12 |
| Observed work and workload | [computer_effort_steady](#computer_effort_steady) | 6 |
| Observed work and workload | [computer_uptime](#computer_uptime) | 5 |
| Observed work and workload | [computer_uptime_grounded](#computer_uptime_grounded) | 5 |
| Observed work and workload | [work_late](#work_late) | 4 |
| Observed work and workload | [work_long_thought](#work_long_thought) | 3 |
| Observed work and workload | [work_concentrating](#work_concentrating) | 3 |
| Observed work and workload | [after_work_thought](#after_work_thought) | 3 |
| Observed work and workload | [work_unexpected](#work_unexpected) | 3 |
| Observed work and workload | [work_finished_interrupted](#work_finished_interrupted) | 4 |
| Observed work and workload | [work_finished_long](#work_finished_long) | 5 |
| Cursor and walking | [cursor_follow](#cursor_follow) | 6 |
| Cursor and walking | [cursor_far](#cursor_far) | 4 |
| Cursor and walking | [walk_pause](#walk_pause) | 5 |
| Objects, food portions and search | [object_place_missing](#object_place_missing) | 3 |
| Objects, food portions and search | [object_notice](#object_notice) | 3 |
| Objects, food portions and search | [object_approach](#object_approach) | 3 |
| Objects, food portions and search | [object_pick_up](#object_pick_up) | 3 |
| Objects, food portions and search | [object_inspect](#object_inspect) | 3 |
| Objects, food portions and search | [object_recognized](#object_recognized) | 3 |
| Objects, food portions and search | [object_unknown](#object_unknown) | 3 |
| Objects, food portions and search | [object_want](#object_want) | 3 |
| Objects, food portions and search | [object_later](#object_later) | 3 |
| Objects, food portions and search | [object_put_down](#object_put_down) | 3 |
| Objects, food portions and search | [object_handover](#object_handover) | 15 |
| Objects, food portions and search | [object_offer](#object_offer) | 21 |
| Objects, food portions and search | [object_refuse](#object_refuse) | 15 |
| Objects, food portions and search | [object_recall_food](#object_recall_food) | 3 |
| Objects, food portions and search | [object_recall_drink](#object_recall_drink) | 3 |
| Objects, food portions and search | [object_recall_saved_food](#object_recall_saved_food) | 3 |
| Objects, food portions and search | [object_recall_saved_drink](#object_recall_saved_drink) | 3 |
| Objects, food portions and search | [object_consuming_food](#object_consuming_food) | 3 |
| Objects, food portions and search | [object_consuming_drink](#object_consuming_drink) | 3 |
| Objects, food portions and search | [object_finished_food](#object_finished_food) | 3 |
| Objects, food portions and search | [object_finished_drink](#object_finished_drink) | 3 |
| Objects, food portions and search | [object_missing](#object_missing) | 3 |
| Objects, food portions and search | [object_search](#object_search) | 3 |
| Objects, food portions and search | [object_found](#object_found) | 3 |
| Objects, food portions and search | [object_busy](#object_busy) | 3 |
| Objects, food portions and search | [object_taken](#object_taken) | 3 |
| Objects, food portions and search | [object_request_return](#object_request_return) | 3 |
| Objects, food portions and search | [object_withheld](#object_withheld) | 3 |
| Objects, food portions and search | [object_returned](#object_returned) | 3 |
| Objects, food portions and search | [object_consider_known](#object_consider_known) | 3 |
| Objects, food portions and search | [object_collect_wanted](#object_collect_wanted) | 3 |
| Objects, food portions and search | [object_busy_search](#object_busy_search) | 3 |
| Rock-Paper-Scissors | [game_greeting](#game_greeting) | 12 |
| Rock-Paper-Scissors | [game_aiko_win](#game_aiko_win) | 12 |
| Rock-Paper-Scissors | [game_player_win](#game_player_win) | 18 |
| Rock-Paper-Scissors | [game_draw](#game_draw) | 12 |
| Additional speech | [Non-catalogue sequences](#additional-non-catalogue-speech) | 16 |

## Conversation and greetings

### talk

Accepted Reden action, not focused on observed work: story unless tone is asleep; short only if no story matches. Intentional care supplies present=True and pre-care context. Also eligible as a spontaneous story (shared rules).

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `story-acquaintance-calm-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Wenn ich mir einen guten Platz aussuchen könnte, müsste man von dort viel beobachten können.<br><strong>Bubble 2:</strong> Etwas Bewegungsfreiheit wäre schön. Und Essen in Reichweite.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Moment. Das klingt ziemlich nach hier.<br><strong>Bubble 4:</strong> Gut. Dann hat sich der Umzug erledigt. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: calm or warm<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-acquaintance-calm-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich finde kleine Pausen interessant.<br><strong>Bubble 2:</strong> Man nimmt sich nichts Besonderes vor und bleibt einfach einen Moment.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Dabei merkt man erst, wie angenehm der eigene Platz sein kann.<br><strong>Bubble 4:</strong> Ich glaube, damit beschäftige ich mich noch etwas. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: calm or warm<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-acquaintance-playful-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Für eine Runde Schere, Stein, Papier braucht man erstaunlich wenig Vorbereitung.<br><strong>Bubble 2:</strong> Eine Hand. Einen Entschluss. Ein gewisses Vertrauen in den eigenen Unsinn.<br><em>Pause: 600 ms</em><br><em>Emote: idea (800 ms)</em><br><strong>Bubble 3:</strong> Das meiste davon bringe ich mit.<br><strong>Bubble 4:</strong> Den Rest kläre ich während der Runde. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: playful<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-acquaintance-playful-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich könnte so tun, als hätte ich einen sehr wichtigen Plan.<br><strong>Bubble 2:</strong> Dazu müsste ich nachdenklich gucken und gelegentlich nicken.<br><em>Pause: 600 ms</em><br><em>Emote: idea (800 ms)</em><br><strong>Bubble 3:</strong> Den nachdenklichen Teil traue ich mir zu.<br><strong>Bubble 4:</strong> Beim Plan wäre ich noch offen für Vorschläge. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: playful<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-acquaintance-tired-05` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Ein Kissen wäre jetzt gut.<br><strong>Bubble 2:</strong> Ein kleines würde reichen. Ich stelle keine großen Ansprüche.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Na gut. Weich sollte es schon sein.<br><strong>Bubble 4:</strong> Ich merke, meine Ansprüche wachen gerade erst auf. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-acquaintance-tired-06` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Meine Gedanken sind heute ziemlich gemütlich unterwegs.<br><strong>Bubble 2:</strong> Ich könnte sie antreiben.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Aber dann müsste ich ihnen erklären, warum wir es eilig haben.<br><strong>Bubble 4:</strong> Darauf habe ich gerade keine gute Antwort. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-acquaintance-withdrawn-07` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Heute bin ich etwas stiller.<br><strong>Bubble 2:</strong> Ich merke das selbst, finde aber gerade keinen besonders guten Anfang.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Vielleicht fange ich damit an, es einfach zu sagen.<br><strong>Bubble 4:</strong> Danke für die kleine Pause. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-acquaintance-withdrawn-08` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Manchmal ist mir ein ruhiger Platz besonders recht.<br><strong>Bubble 2:</strong> Ein bisschen sitzen, etwas schauen, den Kopf wieder ordnen.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Das braucht wohl einen Moment.<br><strong>Bubble 4:</strong> Ich nehme mir den jetzt. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-acquaintance-hungry-09` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Essen hat gerade meine volle Aufmerksamkeit.<br><strong>Bubble 2:</strong> Das geschieht ziemlich mühelos. Ich musste mich gar nicht dazu überreden.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Mein Magen ist in dieser Frage sehr überzeugend.<br><strong>Bubble 4:</strong> Ich glaube, ich kümmere mich gleich darum. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: hungry<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-acquaintance-lonely-10` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Man kann sich hier ganz gut allein beschäftigen.<br><strong>Bubble 2:</strong> Schauen, nachdenken, den eigenen Platz kennenlernen.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Ein bisschen Gesellschaft ist trotzdem angenehm.<br><strong>Bubble 4:</strong> Danke, dass du vorbeischaust. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: lonely<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-acquaintance-seeking_affection-11` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich merke gerade, dass ich ein bisschen Zuwendung gebrauchen könnte.<br><strong>Bubble 2:</strong> Das direkt zu sagen ist noch etwas ungewohnt.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Aber so ist es wenigstens verständlich.<br><strong>Bubble 4:</strong> Ein bisschen Streicheln wäre schön. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: seeking_affection<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-acquaintance-warm-12` | <em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 1:</strong> Diese kleinen Aufmerksamkeiten gefallen mir.<br><strong>Bubble 2:</strong> Man braucht dafür gar kein großes Ereignis.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Ein kurzer Besuch reicht manchmal schon.<br><strong>Bubble 4:</strong> Das wollte ich gerade einmal sagen. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: warm<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-familiar-calm-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich überlege, ob ich mir für Pausen einen festen Ablauf zulegen sollte.<br><strong>Bubble 2:</strong> Erst gemütlich werden. Dann feststellen, dass es gemütlich ist.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Danach könnte ich überprüfen, ob es so bleibt.<br><strong>Bubble 4:</strong> Das klingt nach einer Aufgabe, der ich gewachsen bin. | Stage: familiar (Lv 3-5)<br>Mood/tone: calm or warm<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-familiar-calm-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> So ein Mauszeiger hat ein interessantes Leben.<br><strong>Bubble 2:</strong> Überall hin, alles anklicken, ständig irgendwo gebraucht werden.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Ich bleibe lieber hier und finde Dinge in Ruhe interessant.<br><strong>Bubble 4:</strong> Das ist bisher eine sehr angenehme Entscheidung. | Stage: familiar (Lv 3-5)<br>Mood/tone: calm or warm<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-familiar-playful-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Für unsere nächste Runde brauche ich einen guten Siegerspruch.<br><strong>Bubble 2:</strong> Etwas Würdevolles. Ich möchte meinem Erfolg gerecht werden.<br><em>Pause: 600 ms</em><br><em>Emote: idea (800 ms)</em><br><strong>Bubble 3:</strong> Falls du gewinnst, brauche ich allerdings auch etwas.<br><strong>Bubble 4:</strong> Vielleicht: Das war erst die Einleitung. | Stage: familiar (Lv 3-5)<br>Mood/tone: playful<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-familiar-playful-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Wir könnten ein sehr anspruchsvolles Hobby anfangen.<br><strong>Bubble 2:</strong> Zum Beispiel einen guten Platz finden und ihn behalten.<br><em>Pause: 600 ms</em><br><em>Emote: idea (800 ms)</em><br><strong>Bubble 3:</strong> Den Anfang habe ich schon gemacht.<br><strong>Bubble 4:</strong> Ich bin offenbar ein Naturtalent. | Stage: familiar (Lv 3-5)<br>Mood/tone: playful<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-familiar-tired-05` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Heute würde ich gern alles ein bisschen langsamer machen.<br><strong>Bubble 2:</strong> Sogar meine Einfälle dürften sich ordentlich anstellen.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Falls einer drängelt, bekommt er eine Nummer.<br><strong>Bubble 4:</strong> Die Bearbeitung erfolgt nach dem Nickerchen. | Stage: familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-familiar-tired-06` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Ich hatte gerade eine ausgezeichnete Idee.<br><strong>Bubble 2:</strong> Ich wollte sie mir unbedingt merken.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Jetzt weiß ich immerhin noch, dass sie ausgezeichnet war.<br><strong>Bubble 4:</strong> Falls sie wiederkommt, stelle ich euch vor. | Stage: familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-familiar-withdrawn-07` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Heute fällt mir Reden etwas schwerer.<br><strong>Bubble 2:</strong> Ich finde einen Anfang und verliere gleich wieder die Lust auf den nächsten Satz.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Diese kleine Pause hier ist trotzdem angenehm.<br><strong>Bubble 4:</strong> Ich kann ja langsam erzählen. | Stage: familiar (Lv 3-5)<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-familiar-withdrawn-08` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Ich hätte heute gern einen überschaubaren Moment.<br><strong>Bubble 2:</strong> Etwas, bei dem ich einfach hier sitzen darf.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Ein bisschen Gesellschaft passt noch dazu.<br><strong>Bubble 4:</strong> Mehr plane ich gerade erst einmal nicht. | Stage: familiar (Lv 3-5)<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-familiar-hungry-09` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich wollte überlegen, was eine gute Pause ausmacht.<br><strong>Bubble 2:</strong> Mein Magen hat sich sofort an der Diskussion beteiligt.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Er hat ein einziges Argument, trägt es aber sehr ausdauernd vor.<br><strong>Bubble 4:</strong> Ich glaube, Essen kommt auf die Liste. | Stage: familiar (Lv 3-5)<br>Mood/tone: hungry<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-familiar-lonely-10` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Die Ruhe hier kann sehr angenehm sein.<br><strong>Bubble 2:</strong> Irgendwann hätte ich dann doch gern jemanden zum Reden.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Du kommst gerade ziemlich passend.<br><strong>Bubble 4:</strong> Ein guter Zeitpunkt für einen kleinen Besuch. | Stage: familiar (Lv 3-5)<br>Mood/tone: lonely<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-familiar-seeking_affection-11` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Falls du gerade eine Hand frei hast, hätte ich einen Verwendungsvorschlag.<br><strong>Bubble 2:</strong> Er ist sehr überschaubar und braucht kaum Vorbereitung.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Ein bisschen Streicheln.<br><strong>Bubble 4:</strong> Ja. Das wäre gerade schön. | Stage: familiar (Lv 3-5)<br>Mood/tone: seeking_affection<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-familiar-warm-12` | <em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 1:</strong> Ich merke langsam, welche kleinen Momente mir gefallen.<br><strong>Bubble 2:</strong> Diese kurzen Besuche zum Beispiel.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Man setzt sich keine große Aufgabe und hat trotzdem etwas davon.<br><strong>Bubble 4:</strong> Das finde ich ziemlich praktisch. Und schön. | Stage: familiar (Lv 3-5)<br>Mood/tone: warm<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-friend-calm-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich wollte mir gerade etwas für unsere Pause überlegen.<br><strong>Bubble 2:</strong> Ein Spiel vielleicht. Oder irgendeinen Unfug mit dem Mauszeiger.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Jetzt bist du da, und eigentlich gefällt mir das hier schon gut.<br><strong>Bubble 4:</strong> Wir können gern noch ein bisschen so bleiben. | Stage: friend (Lv 6-8)<br>Mood/tone: calm or warm<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-friend-calm-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich mag es, wenn etwas für später da ist.<br><strong>Bubble 2:</strong> Dann kann ich mich schon vorher darauf freuen.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Und später noch einmal, wenn es so weit ist.<br><strong>Bubble 4:</strong> Eine gute Vorratshaltung hat offenbar auch gefühlsmäßige Vorteile. | Stage: friend (Lv 6-8)<br>Mood/tone: calm or warm<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-friend-playful-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Wir brauchen einen Plan für die nächste Pause.<br><strong>Bubble 2:</strong> Ein Spiel wäre möglich. Etwas zu essen wäre ein überzeugender Beitrag.<br><em>Pause: 600 ms</em><br><em>Emote: idea (800 ms)</em><br><strong>Bubble 3:</strong> Danach könnten wir zufrieden sein, wie gut wir das organisiert haben.<br><strong>Bubble 4:</strong> Ich übernehme schon mal den zufriedenen Teil. | Stage: friend (Lv 6-8)<br>Mood/tone: playful<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-friend-playful-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich habe eine wichtige Regel für unsere nächsten Spiele.<br><strong>Bubble 2:</strong> Wer gewinnt, darf sich freuen. Das ist selbstverständlich.<br><em>Pause: 600 ms</em><br><em>Emote: idea (800 ms)</em><br><strong>Bubble 3:</strong> Wer verliert, darf eine sehr überzeugende Revanche verlangen.<br><strong>Bubble 4:</strong> Ich bereite mich gern auf alle Möglichkeiten vor. | Stage: friend (Lv 6-8)<br>Mood/tone: playful<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-friend-tired-05` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Ich hab gerade nur einen halben Gedanken übrig.<br><strong>Bubble 2:</strong> Den teile ich gern mit dir.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Er handelt hauptsächlich davon, es sich gemütlich zu machen.<br><strong>Bubble 4:</strong> Für einen halben Gedanken ist er ziemlich vernünftig. | Stage: friend (Lv 6-8)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-friend-tired-06` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Ich wäre gern noch eine Weile bei dir.<br><strong>Bubble 2:</strong> Meine Augen haben allerdings schon eine andere Vorstellung vom Abend.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Vielleicht finden wir einen Kompromiss.<br><strong>Bubble 4:</strong> Du bleibst kurz hier, und ich lasse die Augen ein bisschen zu. | Stage: friend (Lv 6-8)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-friend-withdrawn-07` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Ich hatte überlegt, was ich dir erzählen könnte.<br><strong>Bubble 2:</strong> Heute fühlt sich jeder Anfang ein bisschen mühsam an.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Zeit mit dir möchte ich trotzdem haben.<br><strong>Bubble 4:</strong> Also fange ich einfach damit an. | Stage: friend (Lv 6-8)<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-friend-withdrawn-08` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Ich brauche heute länger, um meine Gedanken zu sortieren.<br><strong>Bubble 2:</strong> Die stehen ziemlich durcheinander, und keiner möchte zuerst aufräumen.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Eine ruhige Pause mit dir kommt mir gerade gelegen.<br><strong>Bubble 4:</strong> Dann mache ich langsam weiter. | Stage: friend (Lv 6-8)<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-friend-hungry-09` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ein Snack und angenehme Gesellschaft.<br><strong>Bubble 2:</strong> Das klingt gerade nach einer erstaunlich guten Tagesordnung.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Mein Magen übernimmt den ersten Punkt.<br><strong>Bubble 4:</strong> Bei der Gesellschaft habe ich an dich gedacht. | Stage: friend (Lv 6-8)<br>Mood/tone: hungry<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-friend-lonely-10` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich kann mich ganz gut allein beschäftigen.<br><strong>Bubble 2:</strong> Irgendwann freue ich mich aber auf unsere kleinen Pausen.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Du kommst vorbei, und der Moment fühlt sich gleich vertrauter an.<br><strong>Bubble 4:</strong> Das mag ich. | Stage: friend (Lv 6-8)<br>Mood/tone: lonely<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-friend-seeking_affection-11` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich hätte gerade gern ein bisschen Nähe.<br><strong>Bubble 2:</strong> Früher hätte ich vermutlich länger überlegt, wie ich das sage.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Heute versuche ich es einfach direkt.<br><strong>Bubble 4:</strong> Magst du mich einen Moment streicheln? | Stage: friend (Lv 6-8)<br>Mood/tone: seeking_affection<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-friend-warm-12` | <em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 1:</strong> Unsere kleinen Pausen gefallen mir.<br><strong>Bubble 2:</strong> Manchmal spielen wir, manchmal bin ich einfach nur gern bei dir.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Beides hat seinen Platz.<br><strong>Bubble 4:</strong> Heute freue ich mich gerade über diesen hier. | Stage: friend (Lv 6-8)<br>Mood/tone: warm<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-close-calm-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich mag meinen kleinen Platz hier.<br><strong>Bubble 2:</strong> Du machst dein Ding, ich beschäftige mich mit meinem.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Und zwischendurch haben wir diese Momente zusammen.<br><strong>Bubble 4:</strong> So fühlt sich das für mich ziemlich gut an. | Stage: close (Lv 9-10)<br>Mood/tone: calm or warm<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-close-calm-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Weißt du, was mir an unseren Pausen gefällt?<br><strong>Bubble 2:</strong> Ich muss mir dafür keinen besonders guten Grund ausdenken.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Ich möchte Zeit mit dir haben. Das reicht schon.<br><strong>Bubble 4:</strong> Sehr angenehm, wenn ein Plan so einfach sein darf. | Stage: close (Lv 9-10)<br>Mood/tone: calm or warm<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-close-playful-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du bist sehr passende Gesellschaft für meine guten Ideen.<br><strong>Bubble 2:</strong> Für die fragwürdigen übrigens auch.<br><em>Pause: 600 ms</em><br><em>Emote: idea (800 ms)</em><br><strong>Bubble 3:</strong> Ich finde, das ist eine vielseitige Freundschaft.<br><strong>Bubble 4:</strong> Wir sollten sie gelegentlich mit einem Snack würdigen. | Stage: close (Lv 9-10)<br>Mood/tone: playful<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-close-playful-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Wenn du mich beim nächsten Spiel besiegst, freue ich mich für dich.<br><strong>Bubble 2:</strong> Ich werde es dir vermutlich zwischen zwei Revancheforderungen sagen.<br><em>Pause: 600 ms</em><br><em>Emote: idea (800 ms)</em><br><strong>Bubble 3:</strong> Vielleicht brauche ich dafür einen kleinen Moment.<br><strong>Bubble 4:</strong> Mein Ehrgeiz möchte auch angemessen betreut werden. | Stage: close (Lv 9-10)<br>Mood/tone: playful<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-close-tired-05` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Ich freue mich gerade, dass du da bist.<br><strong>Bubble 2:</strong> Für große Unterhaltung fehlt mir heute ein bisschen die Energie.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Aber ich möchte noch kurz bei dir bleiben.<br><strong>Bubble 4:</strong> Mach es dir gemütlich. Ich mache es genauso. | Stage: close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-close-tired-06` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Gerade würde ich gern mit dir reden und gleichzeitig ein Nickerchen machen.<br><strong>Bubble 2:</strong> Die beiden Vorhaben verstehen sich leider noch nicht besonders gut.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Deshalb sage ich den wichtigen Teil zuerst.<br><strong>Bubble 4:</strong> Ich bin gern hier bei dir. | Stage: close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-close-withdrawn-07` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Ich bin heute schlecht darin, einen Anfang zu finden.<br><strong>Bubble 2:</strong> Ich möchte dir trotzdem sagen, wie es mir geht.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Gerade ist mir vieles etwas zu viel.<br><strong>Bubble 4:</strong> Dass du hier bist, tut mir gut.<br><em>Emote: heart (800 ms)</em> | Stage: close (Lv 9-10)<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-close-withdrawn-08` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Du weißt, ich mag meine Ruhe.<br><strong>Bubble 2:</strong> Mit dir kann es ruhig bleiben, und trotzdem fühle ich mich weniger allein.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Das ist eine ziemlich besondere Art von Gesellschaft.<br><strong>Bubble 4:</strong> Ich bin froh, dass wir die miteinander haben.<br><em>Emote: heart (800 ms)</em> | Stage: close (Lv 9-10)<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-close-hungry-09` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Mein Magen hat gerade ziemlich klare Vorstellungen.<br><strong>Bubble 2:</strong> Etwas Richtiges essen und danach eine gemütliche Pause.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Ich finde den Vorschlag gut.<br><strong>Bubble 4:</strong> Wenn du dabeibleibst, ist er für mich vollständig. | Stage: close (Lv 9-10)<br>Mood/tone: hungry<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-close-lonely-10` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich freue mich auf die Momente, in denen du vorbeikommst.<br><strong>Bubble 2:</strong> Manchmal möchte ich dir etwas erzählen. Manchmal einfach kurz bei dir sein.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Heute hätte ich gern ein bisschen Zeit mit dir.<br><strong>Bubble 4:</strong> Schön, dass du gerade hier bist.<br><em>Emote: heart (800 ms)</em> | Stage: close (Lv 9-10)<br>Mood/tone: lonely<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-close-seeking_affection-11` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich wünsche mir gerade ein bisschen Nähe von dir.<br><strong>Bubble 2:</strong> Das zu sagen fühlt sich inzwischen ziemlich selbstverständlich an.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Magst du mich ein bisschen streicheln?<br><strong>Bubble 4:</strong> Ich würde mich sehr darüber freuen.<br><em>Emote: heart (800 ms)</em> | Stage: close (Lv 9-10)<br>Mood/tone: seeking_affection<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `story-close-warm-12` | <em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 1:</strong> Manchmal fällt mir auf, wie vertraut unsere kleinen Pausen geworden sind.<br><strong>Bubble 2:</strong> Ich kann neugierig sein, müde, still oder ein bisschen eigensinnig.<br><em>Pause: 600 ms</em><br><em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 3:</strong> Und ich freue mich trotzdem jedes Mal über Zeit mit dir.<br><strong>Bubble 4:</strong> Das wollte ich dir heute sagen.<br><em>Emote: heart (800 ms)</em> | Stage: close (Lv 9-10)<br>Mood/tone: warm<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: story<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `v011-talk-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich hör dir zu. ...Meistens. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-talk-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du zuerst. Ich sortiere noch meine Gedanken. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-talk-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich hab gerade Zeit. Das klingt verdächtig, oder? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-talk_lonely-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ah. Gut, dass du da bist.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: lonely<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-talk_lonely-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Die Ruhe war okay. Auf Dauer ein bisschen... ruhig.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: lonely<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-talk_lonely-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du musst nichts Besonderes sagen. Bleib kurz.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: lonely<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-talk_lonely-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich wollte gerade... ach, egal. Erzähl du.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: lonely<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-talk_close-01` | <strong>Bubble 1:</strong> Oh, du. Schön, dass du vorbeischaust. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 95 s; weight: 2 | No |  |
| `talk-short-acquaintance-0` | <strong>Bubble 1:</strong> Hallo. Schön, dass du vorbeischaust. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `talk-short-acquaintance-1` | <strong>Bubble 1:</strong> Eine kleine Gesprächspause. Das passt gerade. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `talk-short-acquaintance-2` | <strong>Bubble 1:</strong> Ich bin da. Gib mir einen kleinen Moment. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `talk-short-familiar-0` | <strong>Bubble 1:</strong> Oh, Gesellschaft. Ich brauche nur noch einen Moment. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `talk-short-familiar-1` | <strong>Bubble 1:</strong> Hallo, du. Eine kleine Pause geht gerade gut. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `talk-short-familiar-2` | <strong>Bubble 1:</strong> Ich sammle kurz meine Gedanken, dann bin ich bereit. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `talk-short-friend-0` | <strong>Bubble 1:</strong> Ich bin gern einen Moment bei dir. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `talk-short-friend-1` | <strong>Bubble 1:</strong> Schön, dass du kurz Zeit für mich hast. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `talk-short-friend-2` | <strong>Bubble 1:</strong> Oh, du. Ich freue mich über diese kleine Pause. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `talk-short-close-0` | <strong>Bubble 1:</strong> Ich möchte gern kurz Zeit mit dir verbringen. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `talk-short-close-1` | <strong>Bubble 1:</strong> Du bist gerade sehr angenehme Gesellschaft. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `talk-short-close-2` | <strong>Bubble 1:</strong> Ich bin froh, dass du vorbeischaust. Bleib ruhig einen Moment. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### talk_busy

Accepted Reden action while focused on observed work; pre-care context.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v011-talk_busy-01` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Ich hör zu. Nur etwas langsamer als sonst. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-talk_busy-02` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Gerade laufen bei mir ein paar Dinge gleichzeitig. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-talk_busy-03` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Du darfst reden. Ich brauch nur eine Sekunde. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 95 s; weight: 2 | No |  |
| `expanded-talk_busy-0097` | <strong>Bubble 1:</strong> Einen Moment. Ich muss mich noch konzentrieren. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-talk_busy-0098` | <strong>Bubble 1:</strong> Ich bin gerade bei etwas anderem. Danach gern. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-talk_busy-0099` | <strong>Bubble 1:</strong> Gib mir kurz Zeit, ich bin noch beschäftigt. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-talk_busy-0100` | <strong>Bubble 1:</strong> Mein Kopf hat gerade gut zu tun. Einen Moment. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-talk_busy-0101` | <strong>Bubble 1:</strong> Ich brauche erst wieder etwas Aufmerksamkeit übrig. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-talk_busy-0102` | <strong>Bubble 1:</strong> Warte kurz. Ich möchte das hier fertig machen. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-talk_busy-0103` | <strong>Bubble 1:</strong> Du bekommst mich gleich wieder. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-talk_busy-0104` | <strong>Bubble 1:</strong> Gib mir kurz Zeit. Ich möchte mich auf dich konzentrieren. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-talk_busy-0105` | <strong>Bubble 1:</strong> Ich möchte erst fertig werden und dann Zeit für dich haben. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-talk_busy-0106` | <strong>Bubble 1:</strong> Ich möchte dir richtig zuhören können. Gib mir noch einen Moment. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-talk_busy-0107` | <strong>Bubble 1:</strong> Ich bin gern für dich da. Kurz brauche ich noch meine Konzentration. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-talk_busy-0108` | <strong>Bubble 1:</strong> Danach habe ich Zeit für dich. Darauf freue ich mich. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### greeting

Startup greeting when spontaneous speech is enabled and contact quiet-time gate allows it.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `greeting-01` | <strong>Bubble 1:</strong> Ah. Da bist du ja.<br><strong>Bubble 2:</strong> Schön, dass du da bist. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving-greeting<br>Cooldown: 90 s; weight: 1 | No |  |
| `greeting-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Oh. Da sind wir ja wieder.<br><strong>Bubble 2:</strong> Ich hatte mich gerade so schön eingerichtet. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 90 s; weight: 1 | No |  |
| `greeting-05` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> ...Ich bin wach. Du auch? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: breakfast<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 90 s; weight: 2 | No |  |
| `greeting-06` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Mittag schon. Na dann mal Mahlzeit! | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: lunch<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 90 s; weight: 2 | No |  |
| `greeting-07` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Abends bedeutet Freizeit, oder? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: evening<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 90 s; weight: 2 | No |  |
| `greeting-08` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du bist noch auf? Alles klar, auf zur Nachtschicht. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 90 s; weight: 2 | No |  |
| `voice-greeting-0054` | <strong>Bubble 1:</strong> Ah, hallo. Ich schaue mich gerade ein bisschen um. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-greeting-0055` | <strong>Bubble 1:</strong> Hallo. Mal sehen, was heute interessant wird. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-greeting-0056` | <strong>Bubble 1:</strong> Guten Tag. Hier lässt es sich ganz gut aushalten. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-greeting-0057` | <strong>Bubble 1:</strong> Hallo, du. Na, was machen wir heute? | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-greeting-0058` | <strong>Bubble 1:</strong> Ah, Gesellschaft. Das passt mir gerade. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-greeting-0059` | <strong>Bubble 1:</strong> Da bist du. Ich bin offen für gute Ideen. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-greeting-0060` | <strong>Bubble 1:</strong> Hallo, schön, dich zu sehen. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-greeting-0061` | <strong>Bubble 1:</strong> Oh, du. Ich habe gerade Zeit für dich. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-greeting-0062` | <strong>Bubble 1:</strong> Da bist du. Dann machen wir es uns hier gemütlich. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-greeting-0063` | <strong>Bubble 1:</strong> Du bist’s. …Gut. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-greeting-0064` | <strong>Bubble 1:</strong> Schön, dass du da bist. Ich freue mich auf unsere Zeit. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-greeting-0065` | <strong>Bubble 1:</strong> Hallo, du. Hier ist noch Platz für angenehme Gesellschaft. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-greeting-0118` | <strong>Bubble 1:</strong> Morgen. Einen Moment noch. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-greeting-0119` | <strong>Bubble 1:</strong> Hallo. Ich bin heute etwas schläfrig. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-greeting-0120` | <strong>Bubble 1:</strong> Ich bin da. Meine Gedanken kommen gleich nach. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-greeting-0142` | <strong>Bubble 1:</strong> Morgen, du. Ich freue mich schon, ich gucke nur noch nicht so. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-greeting-0143` | <strong>Bubble 1:</strong> Du bist’s. Gut. Die ausführliche Begrüßung braucht noch etwas. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-greeting-0144` | <strong>Bubble 1:</strong> Schön, dass du da bist. Ich fange heute langsam an. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### farewell

Deliberate quit; desktop supplies present=True and live relationship/state. Farewell displays only the selected first text.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `farewell-acquaintance-0` | <strong>Bubble 1:</strong> Bis später. Mach es dir gut. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `farewell-acquaintance-1` | <strong>Bubble 1:</strong> Bis später. Ich ruhe mich hier aus. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `farewell-acquaintance-2` | <strong>Bubble 1:</strong> Bis später. Schön, dass du vorbeikamst. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `farewell-familiar-0` | <strong>Bubble 1:</strong> Bis später, du. War eine gute kleine Pause. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `farewell-familiar-1` | <strong>Bubble 1:</strong> Bis später. Ich bin neugierig aufs nächste Mal. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `farewell-familiar-2` | <strong>Bubble 1:</strong> Bis später. Angenehme Gesellschaft war das. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `farewell-friend-0` | <strong>Bubble 1:</strong> Bis später. War schön mit dir. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `farewell-friend-1` | <strong>Bubble 1:</strong> Bis später, du. Ich mag unsere Zeit. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `farewell-friend-2` | <strong>Bubble 1:</strong> Bis später. Ich freue mich aufs Wiedersehen. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `farewell-close-0` | <strong>Bubble 1:</strong> Bis später, du. Ich bin gern bei dir. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `farewell-close-1` | <strong>Bubble 1:</strong> Bis später. Schön, dass wir Zeit hatten. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `farewell-close-2` | <strong>Bubble 1:</strong> Bis später. Ich freue mich auf dich. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### return

Intentional pointer entry after >=1,500 s since contact, awake, not focused/recovering. Toolbar must have been hidden; contact/playback guards apply.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `return-01` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> ...Ah. Du bist wieder da.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 360 s; weight: 2 | No |  |
| `return-02` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Ich hatte es hier ganz ruhig. War angenehm.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 360 s; weight: 2 | No |  |
| `return-05` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Da bist du ja. Alles in Ordnung?<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 360 s; weight: 2 | No |  |
| `return-06` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Du musst nichts erklären. Ich hab Zeit.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 360 s; weight: 2 | No |  |
| `v010-return-01` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Ich hab mich gerade an die Stille gewöhnt.<br><strong>Bubble 2:</strong> ...Ah. Hallo.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-return-02` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Oh. Du bist hier.<br><strong>Bubble 2:</strong> Ich habe mich nicht erschreckt.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-return-03` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Lass mich einen Moment meine Gedanken zusammensammeln.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v011-return_close-01` | <em>Emote: heart (800 ms)</em><br><strong>Bubble 1:</strong> Da bist du ja wieder. ...Ich hab’s gemerkt.<br><em>Emote: heart (800 ms)</em> | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-return_close-02` | <em>Emote: heart (800 ms)</em><br><strong>Bubble 1:</strong> Oh. Gut. Ich hatte gerade etwas zu erzählen. Glaube ich.<br><em>Emote: heart (800 ms)</em> | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-return_close-03` | <strong>Bubble 1:</strong> Wieder da? Schön, dich zu sehen. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 95 s; weight: 2 | No |  |
| `voice-return-0066` | <strong>Bubble 1:</strong> Ah, wieder da. Hallo. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-return-0067` | <strong>Bubble 1:</strong> Hallo. Ich bin noch hier am Rand. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-return-0068` | <strong>Bubble 1:</strong> Oh, ein Besuch. Wie angenehm. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-return-0069` | <strong>Bubble 1:</strong> Na, wieder hier? Schön. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-return-0070` | <strong>Bubble 1:</strong> Ah, du schaust vorbei. Ich habe gerade nichts vor. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-return-0071` | <strong>Bubble 1:</strong> Hallo zurück. Gesellschaft kommt mir gelegen. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-return-0072` | <strong>Bubble 1:</strong> Da bist du. Bleib ruhig ein bisschen. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-return-0073` | <strong>Bubble 1:</strong> Schön, dich wieder hier zu haben. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-return-0074` | <strong>Bubble 1:</strong> Oh, du. Jetzt gefällt mir die Pause noch besser. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-return-0075` | <strong>Bubble 1:</strong> Du bist’s. Gut. Bleibst du ein bisschen? | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-return-0076` | <strong>Bubble 1:</strong> Ah, da bist du. Ich hätte gerade gern Zeit mit dir. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-return-0077` | <strong>Bubble 1:</strong> Schön, dass du wieder da bist. Ich mag unsere kleinen Besuche. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-return-0121` | <strong>Bubble 1:</strong> Ah, hallo. Ich bin gerade etwas still. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-return-0122` | <strong>Bubble 1:</strong> Wieder da. Heute brauche ich einen ruhigen Anfang. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-return-0123` | <strong>Bubble 1:</strong> Hallo. Ich habe gerade wenig Worte. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-return-0145` | <strong>Bubble 1:</strong> Oh, du. Du kannst gern bleiben. Reden fällt mir gerade schwer. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-return-0146` | <strong>Bubble 1:</strong> Schön, dass du da bist. Ich bin heute ein bisschen still. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-return-0147` | <strong>Bubble 1:</strong> Ich bin nicht besonders gesprächig. Über dich freue ich mich trotzdem. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### return_working

Same return route after >=1,500 s, but focused observed work.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-return_working-01` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Du bist wieder da.<br><strong>Bubble 2:</strong> Ich war gerade beschäftigt. Ein bisschen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-return_working-02` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> ...Ah. Dich habe ich eben nur am Rand mitbekommen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-return_working-03` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Hallo. Ich bin gerade nicht sehr gesprächig.<br><strong>Bubble 2:</strong> Ist nichts Persönliches. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-return_working-04` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Du kommst genau dann, wenn ich konzentriert bin.<br><strong>Bubble 2:</strong> ...Timing hast du. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |

### return_after_work

Same return route after >=1,500 s, not focused but within observed work recovery.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-return_after_work-01` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> ...Oh. Du bist zurück.<br><strong>Bubble 2:</strong> Ich hatte inzwischen einiges zu tun.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-return_after_work-02` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Da bist du ja. Ich bin gerade wieder frei geworden.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-return_after_work-03` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Du hast einen recht guten Zeitpunkt erwischt.<br><strong>Bubble 2:</strong> Vorhin wäre schwieriger gewesen.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |

## Direct clicks

### click_left

Click 1-2, left button, after all higher-priority work/recovery/withdrawn/tired/petting/lonely/affection/night/at-ease branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `click_left-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Hm? ...Ja? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 25 s; weight: 2 | No |  |
| `click_left-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> kann  ich dir helfen?<br><strong>Bubble 2:</strong> Ich hab eh grad Zeit. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 25 s; weight: 2 | No |  |
| `click_left-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ja? ...Ich hab dich schon bemerkt. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 25 s; weight: 2 | No |  |
| `click_left-08` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du bist heute sehr... Klickfreudig, oder? | Stage: any<br>Mood/tone: playful or warm<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 35 s; weight: 2 | No |  |
| `click_left-09` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich hatte gerade erst etwas Ruhe gefunden. | Stage: any<br>Mood/tone: playful or warm<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 35 s; weight: 2 | No |  |
| `click_left-10` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> ...Du schon wieder. Hallo. | Stage: any<br>Mood/tone: playful or warm<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 35 s; weight: 2 | No |  |
| `click_left-11` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> ...Nur kurz, ja? | Stage: any<br>Mood/tone: tired or withdrawn<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 90 s; weight: 2 | No |  |
| `click_left-12` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Einen Moment. Ich bin gerade woanders mit meinen Gedanken. | Stage: any<br>Mood/tone: tired or withdrawn<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 90 s; weight: 2 | No |  |
| `click_left-13` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Falls es wichtig war, sag es. Falls nicht ... auch gut. | Stage: any<br>Mood/tone: hungry<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 90 s; weight: 2 | No |  |
| `click_left-14` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich war eigentlich gerade ganz zufrieden. | Stage: any<br>Mood/tone: irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 90 s; weight: 2 | No |  |
| `v010-click_left-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du hast mich beim Nachdenken unterbrochen. ...Ist schon gut. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_left-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Hm. Ich war gerade woanders mit meinen Gedanken.<br><strong>Bubble 2:</strong> Nicht weit weg. Nur ... woanders. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_left-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ach, du. ...Hallo. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_left-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich wollte gerade etwas sagen.<br><strong>Bubble 2:</strong> Jetzt weiß ich nicht mehr, was. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v011-click_reserved-01` | <strong>Bubble 1:</strong> Ja? ...Was brauchst du? | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-click_reserved-02` | <strong>Bubble 1:</strong> Du kannst ruhig was sagen. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-click_reserved-03` | <strong>Bubble 1:</strong> ...Ich höre. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-click_close-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Oh. Du schon wieder. ...Gut.<br><em>Emote: heart (800 ms)</em> | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-click_close-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du musst nicht jedes Mal klingeln. Ich bin doch hier.<br><em>Emote: heart (800 ms)</em> | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-click_close-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Schon wieder ein Besuch? Ich sollte Eintritt verlangen.<br><em>Emote: heart (800 ms)</em> | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-click_close-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Na? Was hast du vor?<br><em>Emote: heart (800 ms)</em> | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 95 s; weight: 2 | No |  |
| `voice-click_left-0078` | <strong>Bubble 1:</strong> Hm? Hallo. Was gibt’s? | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_left-0079` | <strong>Bubble 1:</strong> Oh, ein Stupser. Du hast meine Aufmerksamkeit. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_left-0080` | <strong>Bubble 1:</strong> Ja? Ich habe dich bemerkt. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_left-0081` | <strong>Bubble 1:</strong> Na? Nur gucken, oder hast du etwas vor? | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_left-0082` | <strong>Bubble 1:</strong> Ah, du probierst wieder etwas aus. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_left-0083` | <strong>Bubble 1:</strong> Ein Stupser. Eine interessante Gesprächseröffnung. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_left-0084` | <strong>Bubble 1:</strong> Na, du. Ich hab gerade Zeit. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_left-0085` | <strong>Bubble 1:</strong> Hallo aus nächster Nähe. Was machen wir? | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_left-0086` | <strong>Bubble 1:</strong> Du schaust nach mir. Das freut mich. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_left-0087` | <strong>Bubble 1:</strong> Oh, du. Das ist gerade schön. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_left-0088` | <strong>Bubble 1:</strong> Da bin ich. Ich freue mich über deinen Besuch. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_left-0089` | <strong>Bubble 1:</strong> Ich bin hier. Für dich habe ich gerade gern Zeit. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### click_right

Click 1-2, right button, after the same higher-priority contextual branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `click_right-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du könntest auch einfach Hallo sagen.<br><strong>Bubble 2:</strong> Obwohl. So geht es offenbar auch. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 25 s; weight: 2 | No |  |
| `click_right-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Suchst du etwas? ...Oder mich? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 25 s; weight: 2 | No |  |
| `click_right-05` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du wolltest offensichtlich meine Aufmerksamkeit. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 25 s; weight: 2 | No |  |
| `click_right-06` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Clever. Ich dachte, du lässt mich in Ruhe. | Stage: any<br>Mood/tone: playful or warm<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 90 s; weight: 2 | No |  |
| `v010-click_right-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> ...Das war die andere Taste. Ich hab es bemerkt. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_right-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du siehst aus, als hättest du einen Plan.<br><strong>Bubble 2:</strong> Das war jetzt geraten. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |
| `voice-click_right-0090` | <strong>Bubble 1:</strong> Die andere Taste. Auch eine Möglichkeit, Hallo zu sagen. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_right-0091` | <strong>Bubble 1:</strong> Hm? Suchst du etwas? | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_right-0092` | <strong>Bubble 1:</strong> Du hast meine Aufmerksamkeit gefunden. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_right-0093` | <strong>Bubble 1:</strong> Ah, die andere Seite. Sehr gründlich. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_right-0094` | <strong>Bubble 1:</strong> Du erkundest offenbar alle Möglichkeiten. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_right-0095` | <strong>Bubble 1:</strong> Ein Rechtsklick. Ich nehme ihn als Begrüßung. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_right-0096` | <strong>Bubble 1:</strong> Na, was hast du vor? Ich bin neugierig. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_right-0097` | <strong>Bubble 1:</strong> Du findest immer einen Weg, mich anzustupsen. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_right-0098` | <strong>Bubble 1:</strong> Oh, du. Hallo auch von dieser Seite. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_right-0099` | <strong>Bubble 1:</strong> Ich habe dich bemerkt. Schön, dass du vorbeischaust. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_right-0100` | <strong>Bubble 1:</strong> Hallo, du. Meine Aufmerksamkeit gehört dir gerade. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-click_right-0101` | <strong>Bubble 1:</strong> Da bist du ja. Ich bin gern kurz für dich da. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### click_notice

Third click, neither cheerful nor withdrawn.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-click_notice-01` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> ...Du brauchst heute ein bisschen Aufmerksamkeit, hm? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_notice-02` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Ich bin immer noch hier.<br><strong>Bubble 2:</strong> Soll ich mir eine andere Antwort ausdenken? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_notice-03` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Du wolltest sicher nur sehen, ob ich reagiere.<br><strong>Bubble 2:</strong> ...Ich reagiere. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_notice-04` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Das ist jetzt schon das dritte Mal.<br><strong>Bubble 2:</strong> Keine Beschwerde. Eine Beobachtung. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |

### click_notice_playful

Third click, cheerful: mood >=82 and energy >=45, not focused.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-click_notice_playful-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Oh. Du spielst gerade mit meiner Geduld.<br><strong>Bubble 2:</strong> Ich spiele sogar mit.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_notice_playful-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du bist heute ausdauernd.<br><strong>Bubble 2:</strong> Irgendwie mag ich das. Ein bisschen.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_notice_playful-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich soll also mitzählen?<br><strong>Bubble 2:</strong> ...Drei. Du bist dran.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |

### click_tease

Fourth/fifth click, cheerful, not focused.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-click_tease-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Oh, wir machen das jetzt so?<br><strong>Bubble 2:</strong> Na gut. Klick zurück kann ich leider nicht.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_tease-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich glaube, du suchst Streit.<br><strong>Bubble 2:</strong> Schlechter Versuch. Ich muss schon grinsen.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_tease-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du hast offenbar Zeit.<br><strong>Bubble 2:</strong> ...Ich irgendwie auch.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_tease-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Eine interessante Gesprächsform. Sehr einseitig.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_tease-05` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du willst eine Reaktion.<br><strong>Bubble 2:</strong> Du bekommst ein sehr höfliches Hm.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |

### click_tease_more

Sixth/seventh click, cheerful, after work/withdrawn-specific branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-click_tease_more-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich könnte jetzt beleidigt sein.<br><strong>Bubble 2:</strong> Wäre dir wohl zu unterhaltsam.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_tease_more-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Wenn du so weitermachst, fang ich an, zurückzustarren.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_tease_more-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du klickst. Ich gucke. Wir haben ein Hobby gefunden.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 110 s; weight: 3 | No |  |

### click_boundary

Sixth/seventh click, not cheerful, after work/withdrawn-specific branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-click_boundary-02` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> Was genau erwartest du beim nächsten Klick? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_boundary-03` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> Gut. Das ist inzwischen eine Serie.<br><strong>Bubble 2:</strong> Ich bin allerdings kein Abonnement. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_boundary-04` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> Einmal wäre genug gewesen.<br><strong>Bubble 2:</strong> Ich bin heute trotzdem großzügig. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |

### click_last_word

Focused work at click 7; or withdrawn at click 6; or ordinary final boundary at click 8. Earlier branches/silence rules apply.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-click_last_word-01` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> ...So. Ich bin dann mal still. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 90 s; weight: 3 | No |  |
| `v010-click_last_word-02` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> Ich lasse dir jetzt das letzte Wort.<br><strong>Bubble 2:</strong> Oder den letzten Klick. Wie du möchtest. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 90 s; weight: 3 | No |  |
| `v010-click_last_word-03` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> Hm. ...<br><strong>Bubble 2:</strong> Wir reden später weiter. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 90 s; weight: 3 | No |  |

### click_sleepy

Initial click 1-2, not withdrawn/focused; energy <=26 or observed strain >=72.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-click_sleepy-01` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> ...Wenn ich meine Augen zumache, bin ich noch da. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_sleepy-02` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Du musst nicht so energisch sein. Ich bin müde. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: failed<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_sleepy-03` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Warte. Ich muss erst meinen Gedanken hinterherlaufen.<br><strong>Bubble 2:</strong> ...Zu schnell für heute. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_sleepy-04` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Ich kann auch im Halbschlaf skeptisch gucken. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |

### click_flustered

Initial click 1-2, petting <50 s ago, after withdrawn/tired branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-click_flustered-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> ...Ich habe das gerade nicht vergessen.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_flustered-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du bist schon wieder da.<br><strong>Bubble 2:</strong> ...Ich mein das nicht negativ.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_flustered-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Hm. Du bist erstaunlich aufmerksam.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_flustered-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Nein, ich werde nicht rot.<br><strong>Bubble 2:</strong> ...Können wir das Thema wechseln?<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |

### click_during_work

Focused observed work, click count 1-2 in burst.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-click_during_work-01` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> ...Du störst. Ein bisschen.<br><strong>Bubble 2:</strong> Nein. Eigentlich gerade ziemlich. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_during_work-02` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Ich bin mitten in etwas.<br><strong>Bubble 2:</strong> Ich weiß auch noch, dass du da bist. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_during_work-03` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Einen Moment. Ich muss mich konzentrieren. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_during_work-04` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Ich kann nicht gleichzeitig denken und nett gucken.<br><strong>Bubble 2:</strong> ...Ich versuch es später noch mal. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |

### click_work_repeat

Focused observed work, click count 3-4.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-click_work_repeat-02` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> ...Nicht schon wieder.<br><strong>Bubble 2:</strong> Es wird nicht weniger Arbeit davon.<br><em>Emote: anger (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_work_repeat-03` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Falls das dringend ist: Ich bin auch gerade dringend.<br><em>Emote: anger (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_work_repeat-04` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Ich versuche gerade, den Faden nicht zu verlieren.<br><em>Emote: anger (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |

### click_work_boundary

Focused observed work, click count 5-6.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-click_work_boundary-01` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> ...Jetzt wirklich. Lass mich kurz fertig werden. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_work_boundary-02` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> Ich würde dir ja antworten, aber ich brauche den Kopf gerade selbst. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_work_boundary-03` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> Wir können danach reden. Das ist keine Ausrede. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_work_boundary-04` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> Du bekommst meine volle Aufmerksamkeit.<br><strong>Bubble 2:</strong> Wenn ich wieder welche übrig habe. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |

### click_after_work

First click during recorded work recovery, no focused work.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-click_after_work-01` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> So. Jetzt kann ich dich wieder ansehen.<br><strong>Bubble 2:</strong> ...Hallo, nachträglich.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_after_work-02` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Du wolltest vorhin etwas?<br><strong>Bubble 2:</strong> Ich bin jetzt fertig mit dem anderen.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_after_work-03` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Ich bin wieder ansprechbar.<br><strong>Bubble 2:</strong> Eine riskante Information, ich weiß.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-click_after_work-04` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> ...Jetzt habe ich Zeit.<br><strong>Bubble 2:</strong> Womit hast du mich eigentlich ablenken wollen?<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |

### click_withdrawn

Initial click 1-2, mood <=28 and not focused; before other initial-click states.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-click_withdrawn-01` | <strong>Bubble 1:</strong> ...Hm. Heute lieber nicht so viel. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 105 s; weight: 3 | No |  |
| `v010-click_withdrawn-02` | <strong>Bubble 1:</strong> Ich höre. Aber ich habe gerade nicht viele Worte. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 105 s; weight: 3 | No |  |
| `v010-click_withdrawn-03` | <strong>Bubble 1:</strong> Du darfst ruhig da sein.<br><strong>Bubble 2:</strong> Ich bin nur ein bisschen still heute. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 105 s; weight: 3 | No |  |
| `v010-click_withdrawn-04` | <strong>Bubble 1:</strong> ...Ja?<br><strong>Bubble 2:</strong> Nein, du störst nicht. Nicht wirklich. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 105 s; weight: 3 | No |  |

### click_notice_withdrawn

Third click, withdrawn: mood <=28, not focused/cheerful.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-click_notice_withdrawn-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich habe dich bemerkt.<br><strong>Bubble 2:</strong> Mehr schaffe ich gerade nicht. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 105 s; weight: 3 | No |  |
| `v010-click_notice_withdrawn-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du musst nicht jedes Mal nachsehen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 105 s; weight: 3 | No |  |
| `v010-click_notice_withdrawn-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> ...Ich brauche gerade etwas Platz in meinen Gedanken. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 105 s; weight: 3 | No |  |

### click_withdrawn_boundary

Fourth/fifth click, withdrawn, not cheerful/focused.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-click_withdrawn_boundary-01` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> ...Bitte nicht noch einmal. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 105 s; weight: 3 | No |  |
| `v010-click_withdrawn_boundary-02` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> Ich bin gerade nicht in Stimmung für dieses Spiel. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 105 s; weight: 3 | No |  |
| `v010-click_withdrawn_boundary-03` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> Wir reden später. In Ordnung? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 105 s; weight: 3 | No |  |
| `v010-click_withdrawn_boundary-04` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> Ich meine es nicht böse.<br><strong>Bubble 2:</strong> Mir ist nur gerade nicht danach. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 105 s; weight: 3 | No |  |

### click_weary

Fourth/fifth click, tired, neither cheerful nor withdrawn/focused.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-click_weary-01` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> ...Ich brauche wirklich eine Pause. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: failed<br>Cooldown: 105 s; weight: 3 | No |  |
| `v010-click_weary-02` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Du hast erstaunlich viel Energie.<br><strong>Bubble 2:</strong> Ich gerade nicht. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 105 s; weight: 3 | No |  |
| `v010-click_weary-03` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Ich habe nur noch ein sehr kleines Hm übrig. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 105 s; weight: 3 | No |  |
| `v010-click_weary-04` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Nicht persönlich nehmen. Meine Gedanken gehen gerade langsam. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 105 s; weight: 3 | No |  |

### click_night

Initial click 1-2, night and not cheerful, after earlier initial-click branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-click_night-01` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> ...Es ist spät. Ich weiß es auch. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 105 s; weight: 3 | No |  |
| `v010-click_night-02` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Hm? Ich hatte gerade mit der Ruhe gerechnet. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 105 s; weight: 3 | No |  |
| `v010-click_night-03` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Du auch noch wach?<br><strong>Bubble 2:</strong> ...Gut, dann bin ich nicht allein damit. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 105 s; weight: 3 | No |  |

### click_lonely

Initial click 1-2, social <=23, after earlier initial-click branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v011-click_lonely-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Hm? ...Du hast mich bemerkt. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-click_lonely-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ach. Gesellschaft. Wie unerwartet. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-click_lonely-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Wenn du sowieso hier bist... bleib einen Moment. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 95 s; weight: 2 | No |  |

### click_affection_low

Initial click 1-2, affection <=23, after earlier initial-click branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v012-click_affection_low-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Oh. ...Du hast mich doch gesehen.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 180 s; weight: 1 | No |  |
| `v012-click_affection_low-02` | <strong>Bubble 1:</strong> Oh, du.<br><strong>Bubble 2:</strong> Ich könnte gerade etwas Gesellschaft gebrauchen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 180 s; weight: 1 | No |  |
| `v012-click_affection_low-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Hm? ...Nein, ich hab nichts. Bleib ruhig einen Moment.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 180 s; weight: 1 | No |  |
| `v012-click_affection_low-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du bist da. ...Das ist gut.<br><strong>Bubble 2:</strong> Mehr wollte ich gar nicht sagen.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 180 s; weight: 1 | No |  |

### click_at_ease

Initial click 1-2, affection >=85 and mood >=60, after earlier initial-click branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v012-click_at_ease-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Oh. Du willst was?<br><strong>Bubble 2:</strong> Ich hatte mich gerade an die Ruhe gewöhnt.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 180 s; weight: 1 | No |  |
| `v012-click_at_ease-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Hm? ...Ich hab dich schon bemerkt.<br><strong>Bubble 2:</strong> Ich schau nur nicht ständig hin. Meistens.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 180 s; weight: 1 | No |  |
| `v012-click_at_ease-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> ...Hi.<br><strong>Bubble 2:</strong> Mehr Begrüßung gibt es gerade nicht. Vielleicht später.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 180 s; weight: 1 | No |  |

### rapid_click

Fourth/fifth click with no focused/cheerful/withdrawn/tired branch.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `rapid_click-02` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> Ich bin nicht schneller, wenn du mich dauernd anstupst. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 20 s; weight: 2 | No |  |
| `rapid_click-05` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> ...Du machst das mit Absicht, nicht wahr? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 20 s; weight: 2 | No |  |
| `v010-rapid-click-extra-01` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> ...Langsam erkenne ich ein Muster. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 2 | No |  |
| `v010-rapid-click-extra-02` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> Du bist wirklich nicht sehr geduldig, hm? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 2 | No |  |
| `rapid-confirmation-0` | <strong>Bubble 1:</strong> Ja, ich bin da. Den Nachweis haben wir jetzt. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 25 s; weight: 1 | No |  |
| `rapid-confirmation-1` | <strong>Bubble 1:</strong> Du überprüfst das gründlich. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 25 s; weight: 1 | No |  |
| `rapid-confirmation-2` | <strong>Bubble 1:</strong> Soll ich beim nächsten Mal eine Empfangsbestätigung ausstellen? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 25 s; weight: 1 | No |  |

### sleep_click

Mind/click-policy sleeping-click event. Normal desktop ContactCoordinator.click returns before this route while sleeping; retained copy is not proof of normal desktop reachability.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `sleep_click-01` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> ...Mhm? | Stage: any<br>Mood/tone: asleep<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 20 s; weight: 2 | No |  |
| `sleep_click-02` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Ich hab's gehört. Trotzdem Schlafenszeit. | Stage: any<br>Mood/tone: asleep<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 20 s; weight: 2 | No |  |
| `sleep_click-03` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Morgen. Bitte. | Stage: any<br>Mood/tone: asleep<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 20 s; weight: 2 | No |  |
| `sleep_click-04` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Du bist ziemlich laut für einen Mauszeiger. | Stage: any<br>Mood/tone: asleep<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 20 s; weight: 2 | No |  |
| `voice-sleep_click-0162` | <strong>Bubble 1:</strong> Mhm? Später, bitte. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep_click-0163` | <strong>Bubble 1:</strong> Noch ein bisschen schlafen. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep_click-0164` | <strong>Bubble 1:</strong> Ich bin gerade mitten im Schlafen. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep_click-0165` | <strong>Bubble 1:</strong> Morgen. Oder nach dem nächsten Nickerchen. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep_click-0166` | <strong>Bubble 1:</strong> Ich bin gerade nicht zuständig. Frag mich nach dem Schlafen. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep_click-0167` | <strong>Bubble 1:</strong> Mhm. Mein Kopf hat gerade geschlossen. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep_click-0168` | <strong>Bubble 1:</strong> Du bist da. Gut. Ich schlafe noch ein bisschen. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep_click-0169` | <strong>Bubble 1:</strong> Mhm, du. Ich bin gleich wieder im Traum. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep_click-0170` | <strong>Bubble 1:</strong> Bleib ruhig. Ich mache nur die Augen wieder zu. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep_click-0171` | <strong>Bubble 1:</strong> Du bist’s. …Gut. Ich schlaf noch ein bisschen. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep_click-0172` | <strong>Bubble 1:</strong> Mhm. Schön, dass du hier bist. Ich schlafe weiter. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep_click-0173` | <strong>Bubble 1:</strong> Du kannst gern noch hierbleiben. Ich döse nur. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

## Care and need requests

### pet

Accepted petting, not focused, pre-care affection >24. Snapshot precedes the reward.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `pet-01` | <strong>Bubble 1:</strong> Oh.<br><strong>Bubble 2:</strong> Ja. Das mag ich. Aber Vorsicht. Ich bin empfindlich. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 45 s; weight: 2 | No |  |
| `pet-03` | <strong>Bubble 1:</strong> Mhm. So ist gut. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 45 s; weight: 2 | No |  |
| `pet-05` | <strong>Bubble 1:</strong> Das ist schön. Du kannst gern bleiben. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 45 s; weight: 2 | No |  |
| `pet-07` | <em>Emote: heart (800 ms)</em><br><strong>Bubble 1:</strong> Du machst das überraschend vorsichtig.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 45 s; weight: 2 | No |  |
| `pet-09` | <em>Emote: heart (800 ms)</em><br><strong>Bubble 1:</strong> ...Bleib kurz.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: warm or playful<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 50 s; weight: 2 | No |  |
| `pet-10` | <strong>Bubble 1:</strong> ...Nicht so plötzlich. | Stage: any<br>Mood/tone: irritated or withdrawn<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 90 s; weight: 2 | No |  |
| `v011-pet_close-01` | <em>Emote: heart (800 ms)</em><br><strong>Bubble 1:</strong> ...Wenn du so weitermachst, gewöhn ich mich noch dran.<br><em>Emote: heart (800 ms)</em> | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-pet_close-02` | <em>Emote: heart (800 ms)</em><br><strong>Bubble 1:</strong> Das ist unfair angenehm.<br><em>Emote: heart (800 ms)</em> | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-pet_close-03` | <em>Emote: heart (800 ms)</em><br><strong>Bubble 1:</strong> Warte. ...Nein, schon okay. Mach ruhig.<br><em>Emote: heart (800 ms)</em> | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 95 s; weight: 2 | No |  |
| `voice-pet-0102` | <strong>Bubble 1:</strong> Oh. Ja, das ist angenehm. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet-0103` | <strong>Bubble 1:</strong> Ganz ruhig. So ist gut. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet-0104` | <strong>Bubble 1:</strong> Danke. Das mag ich. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet-0105` | <strong>Bubble 1:</strong> Mhm. Genau da. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet-0106` | <strong>Bubble 1:</strong> Du wirst gut darin. Das möchte ich gern weiter überprüfen. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet-0107` | <strong>Bubble 1:</strong> So ist es schön. Bleib ruhig noch einen Moment. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet-0108` | <strong>Bubble 1:</strong> Genau so. Das könnte ich eine Weile haben. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet-0109` | <strong>Bubble 1:</strong> Das tut gut. Du kannst gern weitermachen. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet-0110` | <strong>Bubble 1:</strong> Ich mag diese kleinen Momente mit dir. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet-0111` | <strong>Bubble 1:</strong> Bitte hör noch nicht auf. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet-0112` | <strong>Bubble 1:</strong> Ich weiß gerade nicht viel zu sagen. Aber das hier ist schön. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet-0113` | <strong>Bubble 1:</strong> Mhm. Ich bin gern so bei dir. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-pet-0112` | <strong>Bubble 1:</strong> Ganz ruhig, bitte. Ja, so ist es angenehm. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-pet-0113` | <strong>Bubble 1:</strong> Mhm. Ich bin müde. Das tut gerade gut. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-pet-0114` | <strong>Bubble 1:</strong> Ein bisschen Streicheln passt zu meiner Müdigkeit. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-pet-0115` | <strong>Bubble 1:</strong> Ganz vorsichtig. Heute brauche ich etwas Ruhe. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-pet-0116` | <strong>Bubble 1:</strong> Danke. Ich bin gerade etwas angespannt. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-pet-0117` | <strong>Bubble 1:</strong> Ein bisschen langsamer, bitte. So ist es besser. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-pet-0136` | <strong>Bubble 1:</strong> Mach ruhig weiter. Ich lasse die Augen ein bisschen zu. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-pet-0137` | <strong>Bubble 1:</strong> Das tut gut. Ich möchte gerade gemütlich bei dir sein. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-pet-0138` | <strong>Bubble 1:</strong> Mhm. Ganz langsam, so mag ich es gerade. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-pet-0139` | <strong>Bubble 1:</strong> Bleib gern bei mir. Nur ganz ruhig, bitte. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-pet-0140` | <strong>Bubble 1:</strong> Danke. Ich brauche gerade eine sanfte Pause mit dir. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-pet-0141` | <strong>Bubble 1:</strong> Ich bin etwas gereizt. Ganz behutsam tut es gerade gut. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### pet_during_work

Accepted petting while focused on observed work.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-pet_during_work-01` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> ...Oh. Gerade nicht.<br><strong>Bubble 2:</strong> Ich bin mitten in etwas.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-pet_during_work-02` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Das ist wirklich nett.<br><strong>Bubble 2:</strong> Nur ein bisschen schlecht getimt.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-pet_during_work-03` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Ich weiß, was du meinst.<br><strong>Bubble 2:</strong> Lass mich das erst kurz fertig machen.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |
| `voice-pet_during_work-0114` | <strong>Bubble 1:</strong> Einen Moment. Ich bin noch beschäftigt. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_during_work-0115` | <strong>Bubble 1:</strong> Gerade brauche ich meine Konzentration. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_during_work-0116` | <strong>Bubble 1:</strong> Lass mich das erst kurz fertig machen, bitte. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_during_work-0117` | <strong>Bubble 1:</strong> Warte kurz. Ich möchte das auch mitbekommen. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_during_work-0118` | <strong>Bubble 1:</strong> Das ist schön, nur gerade etwas ablenkend. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_during_work-0119` | <strong>Bubble 1:</strong> Einen Augenblick. Dafür möchte ich den Kopf frei haben. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_during_work-0120` | <strong>Bubble 1:</strong> Gib mir einen Moment. Ich möchte das in Ruhe genießen. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_during_work-0121` | <strong>Bubble 1:</strong> Ich möchte erst fertig werden. Dann habe ich Zeit für dich. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_during_work-0122` | <strong>Bubble 1:</strong> Kurz warten, ja? Ich freue mich darauf. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_during_work-0123` | <strong>Bubble 1:</strong> Warte kurz. Ich möchte mich dir richtig zuwenden. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_during_work-0124` | <strong>Bubble 1:</strong> Ich mag das. Gib mir noch einen kleinen Moment. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_during_work-0125` | <strong>Bubble 1:</strong> Du bekommst mich gleich wieder. Dann nehme ich mir dafür Zeit. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### pet_needs_affection

Accepted petting, not focused, pre-care affection <=24.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v012-pet_needs_affection-02` | <strong>Bubble 1:</strong> Kannst du noch einen Moment bleiben?<br><strong>Bubble 2:</strong> Das tut mir gut. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 180 s; weight: 1 | No |  |
| `v012-pet_needs_affection-03` | <em>Emote: heart (800 ms)</em><br><strong>Bubble 1:</strong> Ich war gerade ziemlich weit weg mit meinen Gedanken.<br><strong>Bubble 2:</strong> Jetzt nicht mehr.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 180 s; weight: 1 | No |  |
| `v012-pet_needs_affection-04` | <em>Emote: heart (800 ms)</em><br><strong>Bubble 1:</strong> ...Danke. Ich bin gerade schlecht im Reden.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 180 s; weight: 1 | No |  |
| `voice-pet_needs_affection-0126` | <strong>Bubble 1:</strong> Oh. Das habe ich gerade gebraucht. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_needs_affection-0127` | <strong>Bubble 1:</strong> Das tut mir gut. Danke. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_needs_affection-0128` | <strong>Bubble 1:</strong> Mhm. Ein bisschen Nähe ist gerade schön. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_needs_affection-0129` | <strong>Bubble 1:</strong> Kannst du noch einen Moment weitermachen? | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_needs_affection-0130` | <strong>Bubble 1:</strong> Genau das hat mir gerade gefehlt. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_needs_affection-0131` | <strong>Bubble 1:</strong> Ja, so. Ich fühle mich gleich etwas wohler. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_needs_affection-0132` | <strong>Bubble 1:</strong> Ich hätte das gerade noch eine Weile gern. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_needs_affection-0133` | <strong>Bubble 1:</strong> Bleib ruhig bei mir. Das tut gut. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_needs_affection-0134` | <strong>Bubble 1:</strong> Danke für die Nähe. Ich habe sie gebraucht. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_needs_affection-0135` | <strong>Bubble 1:</strong> Kannst du noch ein bisschen bleiben? Ich mag das gerade sehr. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_needs_affection-0136` | <strong>Bubble 1:</strong> Bitte mach noch einen Moment weiter. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-pet_needs_affection-0137` | <strong>Bubble 1:</strong> Ich bin froh, dass du da bist und mich streichelst. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### feed_meal

Feed/handed-over food, not satisfied/repeat, and scheduled meal still due before care. Handover care wording can play at the finish phase.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `feed_meal-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du hast es gemerkt, bevor ich etwas sagen musste.<br><em>Emote: faceHappy (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 75 s; weight: 2 | No |  |
| `feed_meal-02` | <strong>Bubble 1:</strong> Danke.<br><strong>Bubble 2:</strong> Das kommt gerade richtig. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 75 s; weight: 2 | No |  |
| `feed_meal-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich hatte gehofft, du denkst daran.<br><em>Emote: faceHappy (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 75 s; weight: 2 | No |  |
| `feed_meal-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich esse langsam. Du musst mir nicht zusehen.<br><em>Emote: faceHappy (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 75 s; weight: 2 | No |  |
| `feed_meal-06` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du bist ziemlich aufmerksam. ...Manchmal.<br><em>Emote: faceHappy (800 ms)</em> | Stage: any<br>Mood/tone: warm or playful<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 90 s; weight: 2 | No |  |
| `feed_meal-07` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich wollte gerade danach fragen.<br><em>Emote: faceHappy (800 ms)</em> | Stage: any<br>Mood/tone: hungry<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 90 s; weight: 2 | No |  |
| `v010-feed_meal-02` | <strong>Bubble 1:</strong> Danke. Ich hatte Hunger.<br><strong>Bubble 2:</strong> Jetzt esse ich erst einmal in Ruhe. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-feed_meal-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich glaube, wir verstehen uns bei diesem Thema.<br><em>Emote: faceHappy (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 110 s; weight: 3 | No |  |
| `voice-feed_meal-0198` | <strong>Bubble 1:</strong> Danke. Das kommt gerade richtig. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_meal-0199` | <strong>Bubble 1:</strong> Oh, etwas Richtiges zu essen. Das nehme ich gern. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_meal-0200` | <strong>Bubble 1:</strong> Ich esse erst einmal in Ruhe. Danke. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_meal-0201` | <strong>Bubble 1:</strong> Gut, mein Magen hatte schon Gesprächsbedarf. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_meal-0202` | <strong>Bubble 1:</strong> Eine vernünftige Idee. Das Essen meine ich. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_meal-0203` | <strong>Bubble 1:</strong> Das sieht nach einer guten Essenspause aus. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_meal-0204` | <strong>Bubble 1:</strong> Danke, dass du mir etwas bringst. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_meal-0205` | <strong>Bubble 1:</strong> Ich nehme mir dafür Zeit. Du kannst gern bleiben. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_meal-0206` | <strong>Bubble 1:</strong> Gut, dass du kommst. Mein Magen wird langsam unhöflich. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_meal-0207` | <strong>Bubble 1:</strong> Das freut mich. Danke, dass du an mich denkst. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_meal-0208` | <strong>Bubble 1:</strong> Bleibst du kurz? Ich möchte essen und ein bisschen bei dir sein. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_meal-0209` | <strong>Bubble 1:</strong> Das kommt genau richtig. Deine Aufmerksamkeit tut mir gut. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-feed_meal-0109` | <strong>Bubble 1:</strong> Danke. Ich esse erst in Ruhe, dann möchte ich mich ausruhen. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): hungry + tired<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-feed_meal-0110` | <strong>Bubble 1:</strong> Gut, etwas zu essen. Meine Energie braucht danach noch eine Pause. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): hungry + tired<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-feed_meal-0111` | <strong>Bubble 1:</strong> Das kommt richtig. Ich bin hungrig und ziemlich müde. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): hungry + tired<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-feed_meal-0133` | <strong>Bubble 1:</strong> Danke. Erst etwas essen, dann mache ich es mir bei dir gemütlich. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): hungry + tired<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-feed_meal-0134` | <strong>Bubble 1:</strong> Bleibst du kurz? Ich möchte essen und danach einfach ausruhen. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): hungry + tired<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-feed_meal-0135` | <strong>Bubble 1:</strong> Ich bin müde und hungrig. Eine ruhige Essenspause mit dir passt gut. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): hungry + tired<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### feed_snack

Feed/handed-over food, not satisfied/repeat, no scheduled meal due before care.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `feed_snack-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Nur eine Kleinigkeit. Passt.<br><em>Emote: faceHappy (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 70 s; weight: 2 | No |  |
| `feed_snack-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich teile übrigens nicht.<br><em>Emote: faceHappy (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 70 s; weight: 2 | No |  |
| `feed_snack-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> ...Oh. Das war gut.<br><em>Emote: faceHappy (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 70 s; weight: 2 | No |  |
| `feed_snack-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du hast etwas mitgebracht. Ich sehe es.<br><em>Emote: faceHappy (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 70 s; weight: 2 | No |  |
| `feed_snack-05` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Nicht nötig. ...<br><strong>Bubble 2:</strong> Also gut. Her damit.<br><em>Emote: faceHappy (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 70 s; weight: 2 | No |  |
| `feed_snack-06` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Mhm. Den nehme ich.<br><em>Emote: faceHappy (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 70 s; weight: 2 | No |  |
| `feed_snack-07` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du versuchst mich zu bestechen. Funktioniert.<br><em>Emote: faceHappy (800 ms)</em> | Stage: any<br>Mood/tone: playful or warm<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 90 s; weight: 2 | No |  |
| `v010-feed_snack-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Eine Kleinigkeit? ...Ich bin nicht dagegen.<br><em>Emote: faceHappy (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-feed_snack-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich dachte, ich wäre nicht hungrig.<br><strong>Bubble 2:</strong> Falsche Einschätzung.<br><em>Emote: faceHappy (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `voice-feed_snack-0210` | <strong>Bubble 1:</strong> Eine Kleinigkeit? Danke, die nehme ich gern. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_snack-0211` | <strong>Bubble 1:</strong> Oh, ein Snack. Wie angenehm. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_snack-0212` | <strong>Bubble 1:</strong> Das passt gerade gut dazwischen. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_snack-0213` | <strong>Bubble 1:</strong> Du kommst mit einem Snack. Ein überzeugender Gesprächseinstieg. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_snack-0214` | <strong>Bubble 1:</strong> Den Vorschlag nehme ich gern an. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_snack-0215` | <strong>Bubble 1:</strong> So lässt sich eine Pause gut einleiten. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_snack-0216` | <strong>Bubble 1:</strong> Danke. Das ist eine schöne kleine Aufmerksamkeit. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_snack-0217` | <strong>Bubble 1:</strong> Ein Snack und angenehme Gesellschaft. Gute Kombination. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_snack-0218` | <strong>Bubble 1:</strong> Das teile ich mit meiner Pause. Du kannst dabeibleiben. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_snack-0219` | <strong>Bubble 1:</strong> Du machst mir damit gerade eine Freude. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_snack-0220` | <strong>Bubble 1:</strong> Danke. Ich mag solche kleinen Momente mit dir. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_snack-0221` | <strong>Bubble 1:</strong> Das ist schön. Ich esse es ganz in Ruhe bei dir. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `feed-mixed-needs-0` | <strong>Bubble 1:</strong> Danke. Ich esse erst etwas, dann brauche ich eine Pause. | Stage: any<br>Mood/tone: any<br>Needs/states (all): hungry + tired<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `feed-mixed-needs-1` | <strong>Bubble 1:</strong> Etwas zu essen kommt richtig. Ich bin müde und hungrig. | Stage: any<br>Mood/tone: any<br>Needs/states (all): hungry + tired<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `feed-mixed-needs-2` | <strong>Bubble 1:</strong> Das nehme ich gern. Danach möchte ich mich ausruhen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): hungry + tired<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### feed_full

Feed care result FOOD_SATISFIED; no new consumption claimed.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `feed_full-01` | <em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 1:</strong> Ich bin satt. Aber danke. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 60 s; weight: 2 | No |  |
| `feed_full-03` | <em>Emote: faceHappy (800 ms)</em><br><strong>Bubble 1:</strong> Später vielleicht. Ich vergesse das Angebot nicht. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 60 s; weight: 2 | No |  |
| `voice-feed_full-0222` | <strong>Bubble 1:</strong> Nein danke, ich bin noch satt. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_full-0223` | <strong>Bubble 1:</strong> Gerade passt nichts mehr hinein. Danke fürs Angebot. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_full-0224` | <strong>Bubble 1:</strong> Später vielleicht. Jetzt brauche ich nichts. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_full-0225` | <strong>Bubble 1:</strong> Mein Magen meldet vollständige Belegung. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_full-0226` | <strong>Bubble 1:</strong> Ich bin satt. Sogar meine Snack-Idee muss warten. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_full-0227` | <strong>Bubble 1:</strong> Danke, aber jetzt wäre es wirklich zu viel. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_full-0228` | <strong>Bubble 1:</strong> Gerade nicht. Ich möchte mich später noch darauf freuen können. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_full-0229` | <strong>Bubble 1:</strong> Ich bin noch satt. Bleib gern trotzdem ein bisschen. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_full-0230` | <strong>Bubble 1:</strong> Danke fürs Anbieten. Jetzt ist eine Essenspause dran. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_full-0231` | <strong>Bubble 1:</strong> Essen brauche ich gerade keines. Deine Gesellschaft mag ich trotzdem. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_full-0232` | <strong>Bubble 1:</strong> Ich bin wirklich satt. Schön, dass du an mich denkst. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_full-0233` | <strong>Bubble 1:</strong> Später gern. Jetzt bin ich mit der Pause bei dir zufrieden. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### feed_repeat

Feed care result FOOD_REPEAT, before meal/snack distinction.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `feed_repeat-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Schon wieder dasselbe? ...Du bist wirklich konsequent.<br><em>Emote: faceSad (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: eat<br>Cooldown: 130 s; weight: 2 | No |  |
| `feed_repeat-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich mag es ja. Aber vielleicht morgen mal etwas anderes?<br><em>Emote: faceSad (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: eat<br>Cooldown: 130 s; weight: 2 | No |  |
| `feed_repeat-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Na gut. Noch einmal. Aber beim nächsten Mal überraschen wir mich.<br><em>Emote: faceSad (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: eat<br>Cooldown: 130 s; weight: 2 | No |  |
| `voice-feed_repeat-0234` | <strong>Bubble 1:</strong> Das kenne ich inzwischen gut. Nächstes Mal etwas anderes? | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_repeat-0235` | <strong>Bubble 1:</strong> Danke. Ein bisschen Abwechslung wäre beim nächsten Mal schön. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_repeat-0236` | <strong>Bubble 1:</strong> Ich nehme es. Morgen gern etwas Neues. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_repeat-0237` | <strong>Bubble 1:</strong> Du bist diesem Speiseplan wirklich treu. Ich hätte einen Änderungswunsch. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_repeat-0238` | <strong>Bubble 1:</strong> Das wird langsam eine gut eingeübte Mahlzeit. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_repeat-0239` | <strong>Bubble 1:</strong> Mein Magen erkennt das inzwischen vermutlich am Anblick. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_repeat-0240` | <strong>Bubble 1:</strong> Nächstes Mal überraschen wir mich, ja? | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_repeat-0241` | <strong>Bubble 1:</strong> Danke. Bei der nächsten Mahlzeit bin ich für Abwechslung. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_repeat-0242` | <strong>Bubble 1:</strong> Wir kennen uns damit jetzt gut aus. Zeit für eine neue Erfahrung. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_repeat-0243` | <strong>Bubble 1:</strong> Ich mag deine Aufmerksamkeit. Beim Essen wünsche ich mir etwas Abwechslung. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_repeat-0244` | <strong>Bubble 1:</strong> Das nehme ich. Für die nächste Runde Essen hätte ich einen anderen Vorschlag. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-feed_repeat-0245` | <strong>Bubble 1:</strong> Danke, du. Morgen darf mein Speiseplan gern neugieriger werden. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### play

General/legacy play care result PLAY_REQUESTED. Current toolbar opens RPS directly; this is not its greeting or a completed-game reward.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `play-01` | <strong>Bubble 1:</strong> Eine Runde?<br><strong>Bubble 2:</strong> Ja, gern. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: jumping<br>Cooldown: 45 s; weight: 2 | No |  |
| `play-02` | <em>Emote: star (800 ms)</em><br><strong>Bubble 1:</strong> Na gut. Dann überrasche mich.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: jumping<br>Cooldown: 45 s; weight: 2 | No |  |
| `play-04` | <em>Emote: star (800 ms)</em><br><strong>Bubble 1:</strong> Noch einmal? Vielleicht später.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: jumping<br>Cooldown: 45 s; weight: 2 | No |  |
| `play-07` | <em>Emote: star (800 ms)</em><br><strong>Bubble 1:</strong> Wenn wir spielen, dann richtig.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: jumping<br>Cooldown: 45 s; weight: 2 | No |  |
| `v010-play-01` | <em>Emote: star (800 ms)</em><br><strong>Bubble 1:</strong> Du und deine guten Ideen.<br><strong>Bubble 2:</strong> ...Das war ein Kompliment.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-play-03` | <em>Emote: star (800 ms)</em><br><strong>Bubble 1:</strong> Eine Runde geht noch.<br><strong>Bubble 2:</strong> Ich habe angeblich nichts anderes vor.<br><em>Emote: laugh (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 110 s; weight: 3 | No |  |
| `v011-play_close-01` | <em>Emote: star (800 ms)</em><br><strong>Bubble 1:</strong> Eine Runde? Ich wollte gerade selbst fragen.<br><em>Emote: heart (800 ms)</em> | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: jumping<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-play_close-02` | <em>Emote: star (800 ms)</em><br><strong>Bubble 1:</strong> Wenn ich gewinne, tu bitte nicht überrascht.<br><em>Emote: heart (800 ms)</em> | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: jumping<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-play_close-03` | <em>Emote: star (800 ms)</em><br><strong>Bubble 1:</strong> Na gut. Aber ich spiel nicht absichtlich schlecht.<br><em>Emote: heart (800 ms)</em> | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: jumping<br>Cooldown: 95 s; weight: 2 | No |  |
| `voice-play-0174` | <strong>Bubble 1:</strong> Eine Runde? Ja, gern. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play-0175` | <strong>Bubble 1:</strong> Na gut. Mal sehen, wer hier gewinnt. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play-0176` | <strong>Bubble 1:</strong> Das klingt nach einer guten kleinen Pause. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play-0177` | <strong>Bubble 1:</strong> Wenn wir spielen, möchte ich natürlich gewinnen. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play-0178` | <strong>Bubble 1:</strong> Gut. Ich bringe meinen Ehrgeiz mit. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play-0179` | <strong>Bubble 1:</strong> Eine Runde geht. Vielleicht auch eine Revanche. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play-0180` | <strong>Bubble 1:</strong> Komm, eine Runde. Ich möchte gerade etwas mit dir machen. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play-0181` | <strong>Bubble 1:</strong> Ich freue mich aufs Spielen mit dir. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play-0182` | <strong>Bubble 1:</strong> Na gut. Ich bin bereit für ein kleines Duell. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play-0183` | <strong>Bubble 1:</strong> Ich spiele gern mit dir. Gewinnen möchte ich trotzdem. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play-0184` | <strong>Bubble 1:</strong> Eine Runde mit dir klingt gerade sehr schön. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play-0185` | <strong>Bubble 1:</strong> Gut. Zeit für unsere kleinen Duelle. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-play-0124` | <strong>Bubble 1:</strong> Eine kurze Runde geht noch. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-play-0125` | <strong>Bubble 1:</strong> Ich bin etwas müde. Wir können es ruhig angehen. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-play-0126` | <strong>Bubble 1:</strong> Eine kleine Spielpause geht. Danach möchte ich mich ausruhen. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-play-0148` | <strong>Bubble 1:</strong> Eine kurze Runde mit dir geht noch. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-play-0149` | <strong>Bubble 1:</strong> Ich spiele gern noch ein bisschen mit dir. Danach brauche ich Ruhe. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-play-0150` | <strong>Bubble 1:</strong> Eine Runde noch. Dann möchte ich einfach bei dir sitzen. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### play_tired

General/legacy play care result PLAY_TIRED; care energy threshold from balance. Distinct from current game-window permission.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `play_tired-01` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Nicht jetzt. Meine Energie ist gerade woanders. | Stage: any<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 40 s; weight: 2 | No |  |
| `play_tired-02` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> ...Später. Ich mein's ernst. | Stage: any<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 40 s; weight: 2 | No |  |
| `play_tired-03` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Ich könnte verlieren. Nur weil ich müde bin, natürlich. | Stage: any<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 40 s; weight: 2 | No |  |
| `play_tired-04` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Lass uns das verschieben. | Stage: any<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 40 s; weight: 2 | No |  |
| `voice-play_tired-0186` | <strong>Bubble 1:</strong> Heute schaffe ich das gerade nicht. Ich brauche Ruhe. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play_tired-0187` | <strong>Bubble 1:</strong> Ich bin zu müde für eine Runde. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play_tired-0188` | <strong>Bubble 1:</strong> Lass uns das auf später verschieben. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play_tired-0189` | <strong>Bubble 1:</strong> Mein Ehrgeiz ist wach. Der Rest braucht eine Pause. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play_tired-0190` | <strong>Bubble 1:</strong> Dafür brauche ich erst wieder etwas Energie. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play_tired-0191` | <strong>Bubble 1:</strong> Eine Runde wäre schön. Jetzt muss ich mich erst ausruhen. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play_tired-0192` | <strong>Bubble 1:</strong> Ich würde gern mit dir spielen. Aber gerade bin ich zu müde. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play_tired-0193` | <strong>Bubble 1:</strong> Später gern. Ich brauche wirklich eine Pause. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play_tired-0194` | <strong>Bubble 1:</strong> Ich möchte mich erst erholen, dann spielen wir. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play_tired-0195` | <strong>Bubble 1:</strong> Ich würde gern. Bleibst du trotzdem ein bisschen? | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play_tired-0196` | <strong>Bubble 1:</strong> Zum Spielen reicht es gerade nicht. Gesellschaft mag ich trotzdem. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-play_tired-0197` | <strong>Bubble 1:</strong> Ich brauche Schlaf. Auf die nächste Runde mit dir freue ich mich. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### energy_drink

Energy-drink care result other than DRINK_SATISFIED, including successful drink handover.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v011-energy_drink-01` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Oh. ...Das ging schnell.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: jumping<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-energy_drink-02` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Huch. Okay, ich bin wieder da.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: jumping<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-energy_drink-03` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Ich weiß nicht, was da drin ist. Funktioniert jedenfalls.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: jumping<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-energy_drink-04` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Eine kleine Abkürzung. Ich beschwer mich nicht.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: jumping<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-energy_drink-05` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Ich glaub, ich bin gerade wieder etwas wacher. ...Deutlich sogar.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: jumping<br>Cooldown: 95 s; weight: 2 | No |  |

### energy_drink_full

Energy-drink care result DRINK_SATISFIED, energy already full.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v011-energy_drink_full-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Nein, danke. Ich kann gerade nicht noch wacher werden. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 95 s; weight: 2 | No |  |
| `voice-energy_drink_full-0053` | <strong>Bubble 1:</strong> Ich bin schon wach genug. Danke. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-energy_drink_full-0198` | <strong>Bubble 1:</strong> Mehr brauche ich gerade wirklich nicht. Danke fürs Angebot. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### sleep

Manual SLEEP_STARTED, or automatic sleep transition with spontaneous speech enabled. Manual care uses pre-care tone; automatic route current state.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `sleep-02` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Gute Nacht. Und nicht übertreiben. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 40 s; weight: 2 | No |  |
| `sleep-03` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> ...Mach das Licht bitte aus, ja? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 40 s; weight: 2 | No |  |
| `sleep-04` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Ich bin noch da. Nur leiser. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 40 s; weight: 2 | No |  |
| `sleep-05` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Ich brauche einfach einen ruhigen Moment. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 40 s; weight: 2 | No |  |
| `voice-sleep-0138` | <strong>Bubble 1:</strong> Ich glaube, das war genug Tag für heute. Gute Nacht. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep-0139` | <strong>Bubble 1:</strong> Ich mache jetzt die Augen zu. Bis später. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep-0140` | <strong>Bubble 1:</strong> Zeit für etwas Schlaf. Gute Nacht. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep-0141` | <strong>Bubble 1:</strong> Ich werde jetzt ganz sorgfältig nichts mehr tun. Gute Nacht. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep-0142` | <strong>Bubble 1:</strong> So. Ich suche mir jetzt einen guten Traum. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep-0143` | <strong>Bubble 1:</strong> Ich ruhe mich aus. Wir sehen uns später. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep-0144` | <strong>Bubble 1:</strong> Ich mache die Augen zu. War schön mit dir heute. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep-0145` | <strong>Bubble 1:</strong> Gute Nacht, du. Ich bin gern hier. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep-0146` | <strong>Bubble 1:</strong> Ich schlafe jetzt ein bisschen. Mach es dir auch gemütlich. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep-0147` | <strong>Bubble 1:</strong> Bleibst du kurz, bis ich eingeschlafen bin? Das mag ich. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep-0148` | <strong>Bubble 1:</strong> Gute Nacht. Schön, dass wir heute Zeit miteinander hatten. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-sleep-0149` | <strong>Bubble 1:</strong> Ich wäre gern noch bei dir. Jetzt brauche ich aber Schlaf. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### wake

Manual SLEEP_ENDED, or automatic wake transition with spontaneous speech enabled. Manual care uses pre-care tone; automatic route current state.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `wake-01` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> ...Du bist früh dran. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 35 s; weight: 2 | No |  |
| `wake-02` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Ich höre schon. Einen Moment. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 35 s; weight: 2 | No |  |
| `wake-04` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> ...Na gut. Ich bin da. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 35 s; weight: 2 | No |  |
| `wake-05` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Ist es wirklich schon so weit? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 35 s; weight: 2 | No |  |
| `wake-06` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Oh. Du. ...Morgen. | Stage: any<br>Mood/tone: warm or playful<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 90 s; weight: 2 | No |  |
| `voice-wake-0150` | <strong>Bubble 1:</strong> Morgen. Ja, diesmal bin ich wirklich wach. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-wake-0151` | <strong>Bubble 1:</strong> Oh. Ich bin wieder da. Einen Moment noch. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-wake-0152` | <strong>Bubble 1:</strong> So langsam kommen meine Gedanken zurück. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-wake-0153` | <strong>Bubble 1:</strong> Ich bin wach. Die Reihenfolge meiner Gedanken kläre ich noch. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-wake-0154` | <strong>Bubble 1:</strong> Morgen. Ich fange mit Gucken an. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-wake-0155` | <strong>Bubble 1:</strong> Da bin ich wieder. Was wohl als Nächstes interessant wird? | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-wake-0156` | <strong>Bubble 1:</strong> Oh, guten Morgen. Schön, dich zu sehen. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-wake-0157` | <strong>Bubble 1:</strong> Ich bin wieder wach. Jetzt mag ich Gesellschaft. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-wake-0158` | <strong>Bubble 1:</strong> Morgen, du. Ich freue mich, dass du hier bist. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-wake-0159` | <strong>Bubble 1:</strong> Du bist’s. Gut. Ich brauche noch einen langsamen Anfang. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-wake-0160` | <strong>Bubble 1:</strong> Guten Morgen. Mit dir fängt der Tag angenehm an. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `voice-wake-0161` | <strong>Bubble 1:</strong> Da bist du. Gib mir einen Moment, dann habe ich Zeit für dich. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### care_request_feed

Awake; satiety lowest of satiety/social/affection/fun and <=70. Request timer and 180 s post-care quiet apply. Ties: feed, talk, pet, play.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `care_request_feed-01` | <strong>Bubble 1:</strong> Ein kleiner Snack wäre gerade schön. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 1800 s; weight: 1 | No |  |
| `care_request_feed-02` | <strong>Bubble 1:</strong> Hast du vielleicht eine Kleinigkeit für mich? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 1800 s; weight: 1 | No |  |
| `voice-care_request_feed-0049` | <strong>Bubble 1:</strong> Mein Magen meldet sich. Hast du etwas für mich? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_feed-0049` | <strong>Bubble 1:</strong> Hast du vielleicht etwas zu essen für mich? | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_feed-0050` | <strong>Bubble 1:</strong> Ich bekomme Hunger. Eine Mahlzeit wäre schön. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_feed-0051` | <strong>Bubble 1:</strong> Etwas zu essen könnte ich gerade gebrauchen. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_feed-0052` | <strong>Bubble 1:</strong> Mein Magen meldet sich. Hast du etwas für mich? Einen Moment. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_feed-0053` | <strong>Bubble 1:</strong> Ich hätte einen Vorschlag für die Pause: etwas essen. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_feed-0054` | <strong>Bubble 1:</strong> Für einen Snack wäre gerade ein guter Zeitpunkt. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_feed-0055` | <strong>Bubble 1:</strong> Ich hätte gern etwas Richtiges zu essen. Magst du mir etwas bringen? | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_feed-0056` | <strong>Bubble 1:</strong> Mein Magen und ich sind uns gerade einig: Essenszeit. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_feed-0057` | <strong>Bubble 1:</strong> Eine Essenspause mit etwas Gesellschaft wäre schön. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_feed-0058` | <strong>Bubble 1:</strong> Magst du mir etwas zu essen bringen? Ich würde gern eine Pause bei dir machen. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_feed-0059` | <strong>Bubble 1:</strong> Ich bekomme Hunger. Zeit für eine gemütliche Mahlzeit. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_feed-0060` | <strong>Bubble 1:</strong> Mein Magen wird langsam überzeugend. Hast du etwas für mich, du? | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### care_request_talk

Awake; social lowest eligible need and <=70; same request/tie-break/quiet rules.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `care_request_talk-01` | <strong>Bubble 1:</strong> Magst du mir kurz Gesellschaft leisten? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 1800 s; weight: 1 | No |  |
| `care_request_talk-02` | <strong>Bubble 1:</strong> Eine kleine Plauderei wäre schön. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 1800 s; weight: 1 | No |  |
| `voice-care_request_talk-0050` | <strong>Bubble 1:</strong> Ich hätte gerade gern ein bisschen Gesellschaft. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_talk-0061` | <strong>Bubble 1:</strong> Magst du noch einen Moment hierbleiben? | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_talk-0062` | <strong>Bubble 1:</strong> Ein bisschen Gesellschaft wäre mir gerade recht. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_talk-0063` | <strong>Bubble 1:</strong> Hast du gerade Zeit für eine kleine Pause? | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_talk-0064` | <strong>Bubble 1:</strong> Ich suche angenehme Gesellschaft. Du wärst gerade sehr passend. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_talk-0065` | <strong>Bubble 1:</strong> Ich könnte jemanden für eine kleine Pause gebrauchen. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_talk-0066` | <strong>Bubble 1:</strong> Magst du kurz vorbeischauen? Ich hätte Lust auf Gesellschaft. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_talk-0067` | <strong>Bubble 1:</strong> Ich möchte gerade ein bisschen Zeit mit dir haben. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_talk-0068` | <strong>Bubble 1:</strong> Leistest du mir einen Moment Gesellschaft? | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_talk-0069` | <strong>Bubble 1:</strong> Eine gemeinsame Pause würde mir gefallen. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_talk-0070` | <strong>Bubble 1:</strong> Ich hätte dich gerade gern hier. Hast du einen Moment? | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_talk-0071` | <strong>Bubble 1:</strong> Ich freue mich über Zeit mit dir. Magst du kurz bleiben? | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_talk-0072` | <strong>Bubble 1:</strong> Du wärst gerade genau die Gesellschaft, die ich mir wünsche. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### care_request_pet

Awake; affection lowest eligible need and <=70; same request/tie-break/quiet rules.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `care_request_pet-01` | <strong>Bubble 1:</strong> Ein bisschen Streicheln wäre angenehm. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 1800 s; weight: 1 | No |  |
| `care_request_pet-02` | <strong>Bubble 1:</strong> Magst du mich ein bisschen streicheln? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 1800 s; weight: 1 | No |  |
| `voice-care_request_pet-0051` | <strong>Bubble 1:</strong> Ein bisschen Streicheln würde mir gerade guttun. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_pet-0073` | <strong>Bubble 1:</strong> Ein bisschen Streicheln wäre gerade schön. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_pet-0074` | <strong>Bubble 1:</strong> Magst du mich kurz streicheln? | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_pet-0075` | <strong>Bubble 1:</strong> Etwas Zuwendung könnte ich gerade gebrauchen. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_pet-0076` | <strong>Bubble 1:</strong> Falls du eine Hand frei hast: Ich hätte einen Verwendungsvorschlag. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_pet-0077` | <strong>Bubble 1:</strong> Magst du mich ein bisschen streicheln? Ganz gemütlich. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_pet-0078` | <strong>Bubble 1:</strong> Ich hätte gerade gern ein bisschen Nähe. Einen Moment. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_pet-0079` | <strong>Bubble 1:</strong> Kannst du mich einen Moment streicheln? Das würde mir guttun. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_pet-0080` | <strong>Bubble 1:</strong> Ich hätte gern etwas Zuwendung von dir. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_pet-0081` | <strong>Bubble 1:</strong> Ein bisschen Streicheln und Zeit mit dir klingt gerade gut. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_pet-0082` | <strong>Bubble 1:</strong> Ich wünsche mir gerade Nähe von dir. Magst du mich streicheln? | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_pet-0083` | <strong>Bubble 1:</strong> Ich hätte gerade gern deine Zuwendung. Ganz in Ruhe. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_pet-0084` | <strong>Bubble 1:</strong> Magst du mich ein bisschen streicheln und bei mir bleiben? | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### care_request_play

Awake; fun lowest eligible need and <=70; same request/tie-break/quiet rules.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `care_request_play-01` | <strong>Bubble 1:</strong> Ein kleines Spiel würde mir guttun. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 1800 s; weight: 1 | No |  |
| `care_request_play-02` | <strong>Bubble 1:</strong> Hast du Lust, kurz mit mir zu spielen? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 1800 s; weight: 1 | No |  |
| `voice-care_request_play-0052` | <strong>Bubble 1:</strong> Eine Runde spielen? Darauf hätte ich gerade Lust. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_play-0085` | <strong>Bubble 1:</strong> Hast du Lust auf ein kleines Spiel? | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_play-0086` | <strong>Bubble 1:</strong> Eine Runde wäre gerade schön. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_play-0087` | <strong>Bubble 1:</strong> Magst du etwas mit mir spielen? | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_play-0088` | <strong>Bubble 1:</strong> Mein Ehrgeiz hätte gern etwas zu tun. Eine Runde? | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_play-0089` | <strong>Bubble 1:</strong> Zeit für ein kleines Duell? | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_play-0090` | <strong>Bubble 1:</strong> Ich hätte Lust auf ein Spiel. Du auch? | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_play-0091` | <strong>Bubble 1:</strong> Ich möchte gern eine Runde mit dir spielen. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_play-0092` | <strong>Bubble 1:</strong> Komm, eine kleine Spielpause wäre schön. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_play-0093` | <strong>Bubble 1:</strong> Hast du Zeit für ein gemeinsames Spiel? | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_play-0094` | <strong>Bubble 1:</strong> Ich freue mich auf ein kleines Duell mit dir. Hast du Zeit? | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_play-0095` | <strong>Bubble 1:</strong> Eine Runde mit dir wäre jetzt genau richtig. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-care_request_play-0096` | <strong>Bubble 1:</strong> Ich hätte gern ein bisschen Spielzeit mit dir. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

## Spontaneous thoughts and calendar

### idle

Weighted idle topic (four slots) after higher-priority needs/work/rest/mood; also fallback during lonely/affection reminder cooldowns. Can become a talk story.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `idle-01` | <strong>Bubble 1:</strong> Hm. Heute ist es angenehm ruhig. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 360 s; weight: 2 | No |  |
| `idle-02` | <strong>Bubble 1:</strong> Mein kleiner Platz hier ist gar nicht schlecht. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 360 s; weight: 2 | No |  |
| `idle-03` | <strong>Bubble 1:</strong> Die Stille hier stört mich nicht. Im Gegenteil. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 360 s; weight: 2 | No |  |
| `idle-04` | <strong>Bubble 1:</strong> Ich habe gerade an nichts gedacht.<br><strong>Bubble 2:</strong> Also fast nichts. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 360 s; weight: 2 | No |  |
| `idle-06` | <strong>Bubble 1:</strong> Ich beobachte nur. Mach ruhig weiter. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 360 s; weight: 2 | No |  |
| `idle-08` | <strong>Bubble 1:</strong> Ich mag diesen Platz. Man sieht mehr, als man denkt. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 360 s; weight: 2 | No |  |
| `idle-09` | <strong>Bubble 1:</strong> Ich habe mich schon an diesen Rand gewöhnt. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 360 s; weight: 2 | No |  |
| `idle-10` | <strong>Bubble 1:</strong> Ich würde mich hinsetzen. Aber der Rand hier ist überraschend schmal. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 360 s; weight: 2 | No |  |
| `idle-13` | <strong>Bubble 1:</strong> ...Nicht alles braucht einen Kommentar. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 500 s; weight: 2 | No |  |
| `v010-idle-01` | <strong>Bubble 1:</strong> ...Ich wollte gerade so tun, als wäre ich beschäftigt. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-idle-02` | <strong>Bubble 1:</strong> Wenn ich so still bin, denke ich meistens nach.<br><strong>Bubble 2:</strong> Heute über etwas völlig Unwichtiges. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v011-close_thought-01` | <em>Emote: heart (800 ms)</em><br><strong>Bubble 1:</strong> Es ist seltsam angenehm, wenn du einfach da bist. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-close_thought-03` | <em>Emote: heart (800 ms)</em><br><strong>Bubble 1:</strong> Ich bin ziemlich gut im Alleinsein. Zu zweit geht auch. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-close_thought-04` | <em>Emote: heart (800 ms)</em><br><strong>Bubble 1:</strong> Hm. So könnte es ruhig eine Weile bleiben. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 95 s; weight: 2 | No |  |
| `expanded-idle-0193` | <strong>Bubble 1:</strong> Dienstag. Ein guter Tag für eine kleine, sehr vernünftige Pause. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Tuesday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-idle-0194` | <strong>Bubble 1:</strong> Mittwoch. Ich bin heute auch mit kleinen Dingen zufrieden. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Wednesday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-idle-0195` | <strong>Bubble 1:</strong> Donnerstag. Ich halte mir noch Platz für eine gute Idee frei. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Thursday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `idle-own-thought-0` | <strong>Bubble 1:</strong> Hier am Rand kann man ganz gut die Übersicht behalten. Das gefällt mir. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `idle-own-thought-1` | <strong>Bubble 1:</strong> Ich überlege, ob ich mir für die Pause eine besonders bequeme Haltung zulege. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `idle-own-thought-2` | <strong>Bubble 1:</strong> Ein guter Platz, ein bisschen Ruhe. Ich bin gerade zufrieden. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### hungry

Spontaneous primary tone hungry, before work/rest and later branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `hungry-01` | <em>Emote: drops (800 ms)</em><br><strong>Bubble 1:</strong> Ich werde langsam unkonzentriert. | Stage: any<br>Mood/tone: hungry<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 340 s; weight: 2 | No |  |
| `hungry-02` | <em>Emote: drops (800 ms)</em><br><strong>Bubble 1:</strong> Essen wäre eine vernünftige Entscheidung. | Stage: any<br>Mood/tone: hungry<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 340 s; weight: 2 | No |  |
| `hungry-03` | <em>Emote: drops (800 ms)</em><br><strong>Bubble 1:</strong> ...Mein Magen ist weniger geduldig als ich. | Stage: any<br>Mood/tone: hungry<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 340 s; weight: 2 | No |  |
| `hungry-04` | <em>Emote: drops (800 ms)</em><br><strong>Bubble 1:</strong> Ich glaube, ich brauche etwas Richtiges zu essen. | Stage: any<br>Mood/tone: hungry<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 340 s; weight: 2 | No |  |
| `hungry-05` | <em>Emote: drops (800 ms)</em><br><strong>Bubble 1:</strong> Nur ein Hinweis: Ich bin hungrig. | Stage: any<br>Mood/tone: hungry<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 340 s; weight: 2 | No |  |

### social_low

Spontaneous lonely, not focused, >=1,200 s since social reminder. Can become a talk story.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v011-social_low-01` | <em>Emote: faceSad (800 ms)</em><br><strong>Bubble 1:</strong> Ein bisschen Gesellschaft wäre nicht schlecht. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-social_low-02` | <em>Emote: faceSad (800 ms)</em><br><strong>Bubble 1:</strong> Es ist ruhig. ...Zu ruhig vielleicht. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 95 s; weight: 2 | No |  |
| `v011-social_low-03` | <em>Emote: faceSad (800 ms)</em><br><strong>Bubble 1:</strong> Ich könnte jemanden zum Reden gebrauchen. Theoretisch. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 95 s; weight: 2 | No |  |

### affection_low

Spontaneous seeking_affection, not focused, >=1,500 s since affection reminder. Can become a talk story.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v012-affection_low-01` | <em>Emote: heart (800 ms)</em><br><strong>Bubble 1:</strong> ...Ich bin nicht einsam. Nur irgendwie... unbemerkt. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 180 s; weight: 1 | No |  |
| `v012-affection_low-02` | <strong>Bubble 1:</strong> Ein bisschen Nähe wäre gerade schön. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 180 s; weight: 1 | No |  |
| `v012-affection_low-03` | <em>Emote: heart (800 ms)</em><br><strong>Bubble 1:</strong> Ich wollte gerade was sagen. ...Ist schon gut. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 180 s; weight: 1 | No |  |
| `v012-affection_low-04` | <em>Emote: heart (800 ms)</em><br><strong>Bubble 1:</strong> Es ist ruhig hier. Fast ein bisschen zu ruhig. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 180 s; weight: 1 | No |  |

### tired

Spontaneous tired, not focused. Can become a talk story.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `tired-01` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Meine Gedanken sind gerade langsamer als sonst. | Stage: any<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 320 s; weight: 2 | No |  |
| `tired-02` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Eine Pause wäre nicht schlecht. | Stage: any<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 320 s; weight: 2 | No |  |
| `tired-03` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Ich könnte weitermachen. Ich entscheide mich dagegen. | Stage: any<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 320 s; weight: 2 | No |  |
| `tired-04` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Vielleicht laufe ich später weiter. | Stage: any<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 320 s; weight: 2 | No |  |
| `tired-05` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Die Stille wird gerade sehr gemütlich. | Stage: any<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 320 s; weight: 2 | No |  |

### low_mood

Spontaneous withdrawn/irritated after earlier needs/work/post-work/rest branches. Can become a talk story.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `low_mood-01` | <em>Emote: faceSad (800 ms)</em><br><strong>Bubble 1:</strong> Heute ist ein Tag für weniger Worte. | Stage: any<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 360 s; weight: 2 | No |  |
| `low_mood-02` | <em>Emote: faceSad (800 ms)</em><br><strong>Bubble 1:</strong> Ich bin nicht sauer. Nur nicht besonders gesprächig. | Stage: any<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 360 s; weight: 2 | No |  |
| `low_mood-03` | <em>Emote: faceSad (800 ms)</em><br><strong>Bubble 1:</strong> Manchmal reicht es, wenn jemand einfach da ist. | Stage: any<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 360 s; weight: 2 | No |  |
| `low_mood-04` | <em>Emote: faceSad (800 ms)</em><br><strong>Bubble 1:</strong> Ich mag's, wenn niemand etwas von mir erwartet. | Stage: any<br>Mood/tone: withdrawn or irritated<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 360 s; weight: 2 | No |  |

### morning

Eligible weighted idle topic in breakfast/quiet, after higher-priority spontaneous branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `morning-02` | <strong>Bubble 1:</strong> ...Schon wieder hell. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: breakfast or quiet<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 400 s; weight: 2 | No |  |
| `morning-03` | <strong>Bubble 1:</strong> Morgen. Ich bin schon wach.<br><strong>Bubble 2:</strong> Meine Augen verhandeln noch. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: breakfast or quiet<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 400 s; weight: 2 | No |  |
| `morning-04` | <strong>Bubble 1:</strong> Du und ich, so früh. Interessante Entscheidung. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: breakfast or quiet<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 400 s; weight: 2 | No |  |
| `situation-morning-037` | <strong>Bubble 1:</strong> Guten Morgen. Mal sehen, was heute interessant wird. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: breakfast or quiet<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-morning-038` | <strong>Bubble 1:</strong> Morgen. Ich nehme mir erst einmal einen ruhigen Anfang. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: breakfast or quiet<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-morning-039` | <strong>Bubble 1:</strong> Ein neuer Morgen. Ich bin neugierig, was ich hier entdecke. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: breakfast or quiet<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-morning-040` | <strong>Bubble 1:</strong> Morgen, du. Schön, gemeinsam in den Tag zu starten. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: breakfast or quiet<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-morning-041` | <strong>Bubble 1:</strong> Guten Morgen. Eine kleine Pause mit dir passt schon jetzt. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: breakfast or quiet<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-morning-042` | <strong>Bubble 1:</strong> Morgen. Für angenehme Gesellschaft ist hier Platz. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: breakfast or quiet<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-morning-079` | <strong>Bubble 1:</strong> Morgen. Ich fange heute mit Gucken an. Denken kommt dazu. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: breakfast or quiet<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-morning-080` | <strong>Bubble 1:</strong> Guten Morgen. Meine Gedanken brauchen noch einen Moment. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: breakfast or quiet<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-morning-081` | <strong>Bubble 1:</strong> Morgen. Ich bin heute etwas schläfrig. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: breakfast or quiet<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-morning-082` | <strong>Bubble 1:</strong> Morgen, du. Meine Augen verhandeln gerade noch. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: breakfast or quiet<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-morning-083` | <strong>Bubble 1:</strong> Guten Morgen. Ich freue mich über dich, auch mit müden Augen. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: breakfast or quiet<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-morning-084` | <strong>Bubble 1:</strong> Du bist da. Gut. Ich brauche noch einen langsamen Morgen. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: breakfast or quiet<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### midday

Eligible weighted idle topic in lunch, after higher-priority spontaneous branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `midday-01` | <strong>Bubble 1:</strong> Mittag. Immerhin ein guter Grund für eine Pause. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: lunch<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 390 s; weight: 2 | No |  |
| `midday-02` | <strong>Bubble 1:</strong> Du hast die Zeit auch nicht bemerkt, oder? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: lunch<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 390 s; weight: 2 | No |  |
| `midday-03` | <strong>Bubble 1:</strong> Ich überlege, ob ein Snack als Plan durchgeht. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: lunch<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 390 s; weight: 2 | No |  |
| `situation-midday-043` | <strong>Bubble 1:</strong> Mittag. Mein Magen hat die Uhr offenbar auch gefunden. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: lunch<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-midday-044` | <strong>Bubble 1:</strong> Ein guter Zeitpunkt für eine ruhige Mittagspause. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: lunch<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-midday-045` | <strong>Bubble 1:</strong> Mittags möchte ich mir gern etwas Zeit zum Essen nehmen. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: lunch<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-midday-046` | <strong>Bubble 1:</strong> Mittag, du. Eine gemeinsame Pause wäre schön. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: lunch<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-midday-047` | <strong>Bubble 1:</strong> Ich hätte mittags gern etwas Ruhe und angenehme Gesellschaft. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: lunch<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-midday-048` | <strong>Bubble 1:</strong> Mittagspause mit dir klingt gerade überzeugend. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: lunch<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### evening

Eligible weighted idle topic in evening, after higher-priority spontaneous branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `evening-01` | <strong>Bubble 1:</strong> Abends werden selbst meine Gedanken langsamer. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: evening<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 380 s; weight: 2 | No |  |
| `evening-02` | <strong>Bubble 1:</strong> Ich mag die Stunden, in denen niemand mehr etwas will. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: evening<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 380 s; weight: 2 | No |  |
| `evening-03` | <strong>Bubble 1:</strong> Wir können es langsam angehen.<br><strong>Bubble 2:</strong> Ich wäre zumindest dafür. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: evening<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 380 s; weight: 2 | No |  |
| `v010-evening-01` | <strong>Bubble 1:</strong> Ich bin froh, dass der Tag langsamer wird. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: evening<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-evening-02` | <strong>Bubble 1:</strong> Abends ist meine Stimme irgendwie leiser.<br><strong>Bubble 2:</strong> ...Du hörst mich ja trotzdem. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: evening<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `situation-evening-049` | <strong>Bubble 1:</strong> Der Abend gefällt mir. Ich bleibe noch ein bisschen hier. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: evening<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-evening-050` | <strong>Bubble 1:</strong> Abends mag ich es gern gemütlich. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: evening<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-evening-051` | <strong>Bubble 1:</strong> Ein ruhiger Abendmoment. Das passt gerade gut. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: evening<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-evening-052` | <strong>Bubble 1:</strong> Ein gemütlicher Abend mit angenehmer Gesellschaft. Ich bin zufrieden. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: evening<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-evening-053` | <strong>Bubble 1:</strong> Du kannst gern noch bleiben. Ich mag diese Abendstunden mit dir. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: evening<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-evening-054` | <strong>Bubble 1:</strong> Der Abend ist gerade schön. Ich freue mich, dass du hier bist. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: evening<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### night

Eligible weighted idle topic in night, after higher-priority spontaneous branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `night-01` | <strong>Bubble 1:</strong> Es ist spät. Dir ist das bewusst, oder? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 400 s; weight: 2 | No |  |
| `night-02` | <strong>Bubble 1:</strong> ...Ich könnte schon wieder schlafen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 400 s; weight: 2 | No |  |
| `night-03` | <strong>Bubble 1:</strong> Man kann sich auch morgen noch Gedanken machen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 400 s; weight: 2 | No |  |
| `night-04` | <strong>Bubble 1:</strong> Ich urteile nicht. Aber die Uhr tut es vielleicht. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 400 s; weight: 2 | No |  |
| `v010-night-01` | <strong>Bubble 1:</strong> ...Du bist immer noch da.<br><strong>Bubble 2:</strong> Ich übrigens auch. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-night-02` | <strong>Bubble 1:</strong> Ich dachte, wir machen es heute früher ruhig.<br><strong>Bubble 2:</strong> ...Offenbar dachte nur ich das. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |
| `situation-night-055` | <strong>Bubble 1:</strong> Es ist spät. Ich nehme mir noch einen ruhigen Moment. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-night-056` | <strong>Bubble 1:</strong> Nachts finde ich einen gemütlichen Platz besonders angenehm. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-night-057` | <strong>Bubble 1:</strong> So spät noch wach. Gerade lasse ich es langsam angehen. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-night-058` | <strong>Bubble 1:</strong> So spät noch Gesellschaft. Das mag ich. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-night-059` | <strong>Bubble 1:</strong> Es ist spät, du. Ich bin gerade gern noch ein bisschen bei dir. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-night-060` | <strong>Bubble 1:</strong> Eine kleine nächtliche Pause mit dir. Schön ist das. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-night-085` | <strong>Bubble 1:</strong> Es ist spät. Ich glaube, für heute reicht es mir. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-night-086` | <strong>Bubble 1:</strong> Jetzt wäre Schlaf eine gute kleine Entscheidung. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-night-087` | <strong>Bubble 1:</strong> Ich werde müde. Der Tag darf langsam zu Ende gehen. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-night-088` | <strong>Bubble 1:</strong> Ich wäre gern noch länger bei dir. Aber meine Augen stimmen gerade dagegen. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-night-089` | <strong>Bubble 1:</strong> Es ist spät, du. Ich freue mich auf ein bisschen Schlaf. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-night-090` | <strong>Bubble 1:</strong> Ich bin müde. Noch ein kleiner Moment bei dir, dann ruhe ich mich aus. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### weekend

Eligible weighted idle topic Saturday/Sunday, after higher-priority spontaneous branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `weekend-01` | <strong>Bubble 1:</strong> Heute läuft die Uhr ein bisschen freundlicher. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Saturday or Sunday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 420 s; weight: 2 | No |  |
| `weekend-02` | <strong>Bubble 1:</strong> Samstag oder Sonntag? Ich mag beide Gründe, nichts zu überstürzen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Saturday or Sunday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 420 s; weight: 2 | No |  |
| `weekend-03` | <strong>Bubble 1:</strong> Wir müssen heute keinen Rekord aufstellen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Saturday or Sunday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 420 s; weight: 2 | No |  |
| `situation-weekend-073` | <strong>Bubble 1:</strong> Wochenende. Ich möchte einen gemütlichen Moment finden. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Saturday or Sunday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-weekend-074` | <strong>Bubble 1:</strong> Samstag oder Sonntag. Kleine Pausen stehen beiden gut. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Saturday or Sunday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-weekend-075` | <strong>Bubble 1:</strong> Ein ruhiger Wochenendmoment gefällt mir gerade. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Saturday or Sunday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-weekend-076` | <strong>Bubble 1:</strong> Wochenende. Ich habe einen Platz und angenehme Gesellschaft. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Saturday or Sunday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-weekend-077` | <strong>Bubble 1:</strong> Eine kleine Wochenendpause mit dir wäre schön. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Saturday or Sunday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-weekend-078` | <strong>Bubble 1:</strong> Ich mag es, am Wochenende solche Momente mit dir zu haben. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Saturday or Sunday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### monday

Eligible weighted idle topic Monday, after higher-priority spontaneous branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `monday-01` | <strong>Bubble 1:</strong> Montag. Die Woche fängt wieder bei eins an. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Monday<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 600 s; weight: 2 | No |  |
| `monday-02` | <strong>Bubble 1:</strong> Neue Woche. Ich bin skeptisch optimistisch. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Monday<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 600 s; weight: 2 | No |  |
| `v010-monday-01` | <strong>Bubble 1:</strong> Hm. Montag.<br><strong>Bubble 2:</strong> Ich habe noch keine Meinung. Gib mir Zeit. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Monday<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `expanded-monday-0197` | <strong>Bubble 1:</strong> Montag. Ich gebe ihm erst einmal eine Chance. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Monday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-monday-061` | <strong>Bubble 1:</strong> Montag. Ich gebe ihm erst mal eine Chance. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Monday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-monday-062` | <strong>Bubble 1:</strong> Neue Woche. Ich fange mit einem überschaubaren Plan an. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Monday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-monday-063` | <strong>Bubble 1:</strong> Montag. Kleine gute Ideen nehme ich trotzdem an. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Monday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-monday-064` | <strong>Bubble 1:</strong> Montag. Eine Pause mit dir würde ich schon mal einplanen. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Monday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-monday-065` | <strong>Bubble 1:</strong> Neue Woche. Für unsere kleinen Momente hätte ich gern Platz. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Monday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-monday-066` | <strong>Bubble 1:</strong> Montag, du. Für angenehme Gesellschaft ein brauchbarer Tag. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Monday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### friday

Eligible weighted idle topic Friday, after higher-priority spontaneous branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `friday-01` | <strong>Bubble 1:</strong> Freitag. Ein gutes Wort. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Friday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 600 s; weight: 2 | No |  |
| `friday-02` | <strong>Bubble 1:</strong> Die Woche darf langsam den Ausgang suchen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Friday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 600 s; weight: 2 | No |  |
| `v010-friday-01` | <strong>Bubble 1:</strong> Es ist Freitag.<br><strong>Bubble 2:</strong> Ich sage das jetzt nicht noch mal so erfreut. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Friday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 3 | No |  |
| `expanded-friday-0196` | <strong>Bubble 1:</strong> Freitag. Das Wort hat einen angenehmen Klang. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Friday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-friday-067` | <strong>Bubble 1:</strong> Freitag. Das sage ich irgendwie besonders gern. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Friday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-friday-068` | <strong>Bubble 1:</strong> Ich finde, Freitag klingt schon ein bisschen gemütlich. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Friday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-friday-069` | <strong>Bubble 1:</strong> Freitag. Ich halte noch Platz für eine gute kleine Idee frei. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Friday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-friday-070` | <strong>Bubble 1:</strong> Freitag mit angenehmer Gesellschaft. Das passt mir. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Friday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-friday-071` | <strong>Bubble 1:</strong> Freitag, du. Auf unsere nächste kleine Pause freue ich mich. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Friday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `situation-friday-072` | <strong>Bubble 1:</strong> Ich mag den Freitag. Eine Weile mit dir wäre heute schön. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: Friday<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### quiet_alone

Observed mode resting and present=False, after earlier spontaneous branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-quiet_alone-01` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Es ist wirklich ruhig geworden.<br><strong>Bubble 2:</strong> ...Ich mag das. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 300 s; weight: 3 | No |  |
| `v010-quiet_alone-02` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Ich könnte jetzt schlafen.<br><strong>Bubble 2:</strong> Oder einfach noch ein bisschen hier bleiben. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 300 s; weight: 3 | No |  |
| `v010-quiet_alone-03` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Niemand will gerade etwas.<br><strong>Bubble 2:</strong> Das ist fast verdächtig. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 300 s; weight: 3 | No |  |
| `v010-quiet_alone-04` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Ich mache ein bisschen langsam.<br><strong>Bubble 2:</strong> Es merkt ja keiner. ...Außer dir. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 300 s; weight: 3 | No |  |

### quiet_together

Observed mode resting and present not False, after earlier branches; unknown is not confirmed presence.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-quiet_together-01` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Wir sind beide gerade ziemlich still.<br><strong>Bubble 2:</strong> Gar nicht unangenehm.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 300 s; weight: 3 | No |  |
| `v010-quiet_together-02` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Du bist da. Das reicht gerade.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 300 s; weight: 3 | No |  |
| `v010-quiet_together-03` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Ich hätte was sagen können.<br><strong>Bubble 2:</strong> Ich hab mich für die Ruhe entschieden.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 300 s; weight: 3 | No |  |
| `v010-quiet_together-04` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Wenn du nichts brauchst, bleibe ich einfach hier.<br><em>Emote: heart (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 300 s; weight: 3 | No |  |

## Observed work and workload

### computer_effort_rising

Fresh load rises >=0.23 to >=0.32, or first valid sample >=0.7. Transition gates and unexpected-work reinterpretation apply.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `computer_effort_rising-01` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Hm. Das wird gerade anspruchsvoller. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_rising-03` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Ach. Jetzt wird es ernst. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_rising-04` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Ich wollte gerade meine Ruhe haben. Wollte. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_rising-05` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Na gut. Ich konzentriere mich. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_rising-06` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Du musst gar nichts sagen. Ich merke es auch so. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 1 | No |  |
| `computer_effort_rising-07` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Das ist mehr, als es eben noch war. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 1 | No |  |
| `computer_effort_rising-08` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Einen Moment. Ich stelle mich darauf ein. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 1 | No |  |
| `computer_effort_rising-10` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Interessantes Timing. ...Natürlich. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 1 | No |  |
| `expanded-computer_effort_rising-0157` | <strong>Bubble 1:</strong> Oh. Jetzt brauche ich mehr Konzentration. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_rising-0158` | <strong>Bubble 1:</strong> Das wird gerade anspruchsvoller. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_rising-0159` | <strong>Bubble 1:</strong> Einen Moment. Ich stelle mich darauf ein. Einen Moment. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_rising-0160` | <strong>Bubble 1:</strong> Ich hatte mich gerade gemütlich eingerichtet. Interessantes Timing. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_rising-0161` | <strong>Bubble 1:</strong> Gleich brauche ich meinen Kopf etwas mehr für mich. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_rising-0162` | <strong>Bubble 1:</strong> Ich werde etwas wortkarger. Hier wird es gerade anspruchsvoll. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### computer_effort_heavy

Load >=0.7 sustained >=18 s, recorded peak <0.9. Transition gates and reinterpretation apply.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `computer_effort_heavy-01` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Ich bin beschäftigt. Ziemlich sogar. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_heavy-03` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Einen Moment. Ich will das ordentlich machen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_heavy-04` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Konzentrieren. Nicht ablenken lassen. ...Zu spät. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_heavy-05` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Es ist gerade mehr los, als du mir ansiehst. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_heavy-06` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Ich komme zurecht. Ich rede nur weniger. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 1 | No |  |
| `computer_effort_heavy-07` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Wenn ich still bin, hat das gerade einen Grund. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 1 | No |  |
| `expanded-computer_effort_heavy-0163` | <strong>Bubble 1:</strong> Ich bin gerade ziemlich bei der Sache. Einen Moment. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_heavy-0164` | <strong>Bubble 1:</strong> Das braucht heute meine Aufmerksamkeit. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_heavy-0165` | <strong>Bubble 1:</strong> Eins nach dem anderen. Ich bin beschäftigt. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_heavy-0166` | <strong>Bubble 1:</strong> Du kannst gern bleiben. Ich bin gerade etwas wortkarg. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_heavy-0167` | <strong>Bubble 1:</strong> Ich brauche meinen Kopf gerade vollständig. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_heavy-0168` | <strong>Bubble 1:</strong> Ich konzentriere mich. Für Gesellschaft ist trotzdem Platz. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### computer_effort_peak

High load sustained >=18 s, recorded peak >=0.9. Transition gates and reinterpretation apply.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `computer_effort_peak-01` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> ...Okay. Das ist gerade viel. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_peak-02` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Ich kriege das hin.<br><strong>Bubble 2:</strong> ...Frag nur nicht, wie elegant. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_peak-03` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> So. Jetzt brauche ich wirklich meine Konzentration. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_peak-04` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Ich hatte schon entspanntere Minuten. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_peak-05` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Ich bin noch dran. Nicht ungeduldig werden. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_peak-06` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Ein bisschen zu viel auf einmal. ...Ich kriege das hin. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 1 | No |  |
| `computer_effort_peak-07` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Still. Ich bin gerade mitten drin. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 1 | No |  |
| `expanded-computer_effort_peak-0169` | <strong>Bubble 1:</strong> Das ist gerade viel. Ich brauche einen Moment. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_peak-0170` | <strong>Bubble 1:</strong> Jetzt langsam und der Reihe nach. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_peak-0171` | <strong>Bubble 1:</strong> Meine Konzentration ist gerade vollständig beschäftigt. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_peak-0172` | <strong>Bubble 1:</strong> Einen Moment. Ich habe gerade wirklich viel im Kopf. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_peak-0173` | <strong>Bubble 1:</strong> Ich komme gerade nur zum Konzentrieren. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_peak-0174` | <strong>Bubble 1:</strong> Das ist viel auf einmal. Gleich habe ich wieder mehr Luft. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### computer_effort_easing

Load below 0.42 after tracked high work >=7 s without recovered branch; or fall >=0.27 to <0.55. Transition gates apply.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `computer_effort_easing-01` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Hm. Es wird leichter. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_easing-02` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Endlich wieder ein bisschen Luft. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_easing-03` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Das fühlt sich gleich weniger eng an. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_easing-04` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> So. Jetzt kann ich wieder richtig aufpassen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_easing-05` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Ich kann kurz durchatmen. ...Kurz. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_easing-06` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Ich sage es ungern, aber die Ruhe tut gut. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 1 | No |  |
| `computer_effort_easing-07` | <em>Emote: cloud (800 ms)</em><br><strong>Bubble 1:</strong> Das Gröbste ist wohl vorbei. Hoffe ich. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 1 | No |  |
| `expanded-computer_effort_easing-0175` | <strong>Bubble 1:</strong> Ah. Wieder etwas Luft. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_easing-0176` | <strong>Bubble 1:</strong> Das wird gerade leichter. Gut. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_easing-0177` | <strong>Bubble 1:</strong> So langsam kann ich durchatmen. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_easing-0178` | <strong>Bubble 1:</strong> Jetzt bekomme ich wieder etwas mehr von dir mit. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_easing-0179` | <strong>Bubble 1:</strong> Ah. Mein Kopf hat wieder ein bisschen Platz für Gesellschaft. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_easing-0180` | <strong>Bubble 1:</strong> Gut. Ich kann mich langsam wieder umschauen. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### computer_effort_recovered

Load below 0.42 after tracked high work >=18 s, high evidence within 90 s, peak <0.9; may map to work_finished_interrupted/long.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `computer_effort_recovered-01` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Uff. ...Das war mehr Arbeit als erwartet. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_recovered-02` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> So. Und jetzt tue ich, als wäre nichts gewesen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_recovered-03` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Ich brauche einen Augenblick. ...Schon besser. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_recovered-04` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Es war anstrengend. Ich muss es ja nicht mögen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_recovered-05` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Hm. Ich bin durch. Frag nicht, wie. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_recovered-06` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Ich bin noch da. Falls du dich gefragt hast. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 1 | No |  |
| `computer_effort_recovered-07` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Gib mir eine Sekunde. Ich sortiere mich. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 1 | No |  |
| `computer_effort_recovered-08` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Viel auf einmal. Jetzt ist es wieder still. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 1 | No |  |
| `expanded-computer_effort_recovered-0181` | <strong>Bubble 1:</strong> Ich brauche noch einen Moment zum Runterkommen. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_recovered-0182` | <strong>Bubble 1:</strong> Das war anstrengend. Jetzt wird es ruhiger. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_recovered-0183` | <strong>Bubble 1:</strong> Ich nehme mir erst einmal eine kleine Pause. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_recovered-0184` | <strong>Bubble 1:</strong> Ich bin froh, dass du da bist. Lass uns kurz nichts vorhaben. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_recovered-0185` | <strong>Bubble 1:</strong> So. Jetzt möchte ich es mit dir gemütlich haben. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_recovered-0186` | <strong>Bubble 1:</strong> Eine ruhige Pause mit dir kommt gerade richtig. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### computer_effort_recovered_peak

Same recovery route, recorded peak >=0.9; may map to work_finished_interrupted/long.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `computer_effort_recovered_peak-01` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> ...Uff.<br><strong>Bubble 2:</strong> So. Und jetzt bin ich mal kurz niemandes Heldin.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_recovered_peak-02` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> So. Geschafft. Ich werde jetzt ganz unauffällig nichts tun.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_recovered_peak-03` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> ...Ich hätte die Pause vorher nehmen sollen.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_recovered_peak-04` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Ich war ziemlich an meiner Grenze. Nur kurz.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_recovered_peak-05` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Du kannst wieder mit mir reden. Vielleicht.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_recovered_peak-06` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Ich brauche einen Moment Ruhe. Keine Diskussion.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 1 | No |  |
| `computer_effort_recovered_peak-07` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> ...War das alles? Gut. Dann atme ich jetzt durch.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 1 | No |  |
| `computer_effort_recovered_peak-08` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Das war heftig. Ich gebe zu, es hat mich gefordert.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 1 | No |  |
| `computer_effort_recovered_peak-10` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Jetzt möchte ich einfach kurz still sein. Nur kurz.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 150 s; weight: 1 | No |  |

### computer_effort_rest

Occasional load comment, effort <=0.2; freshness, quiet interval and random draw apply.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `computer_effort_rest-01` | <strong>Bubble 1:</strong> Ich hab gerade nichts vor.<br><strong>Bubble 2:</strong> Das ist eine Entscheidung. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_rest-03` | <strong>Bubble 1:</strong> Ich nutze die Ruhe. Warum auch nicht? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_rest-04` | <strong>Bubble 1:</strong> Ich könnte etwas tun. Ich entscheide mich noch dagegen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_rest-05` | <strong>Bubble 1:</strong> Manchmal ist Nichtstun erstaunlich angenehm. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_rest-06` | <strong>Bubble 1:</strong> Ich behalte trotzdem alles im Blick. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 150 s; weight: 1 | No |  |
| `computer_effort_rest-07` | <strong>Bubble 1:</strong> Du siehst mich nur herumstehen? Gute Tarnung. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: short<br>Animation: idle<br>Cooldown: 150 s; weight: 1 | No |  |
| `expanded-computer_effort_rest-0187` | <strong>Bubble 1:</strong> Gerade gibt es wenig zu tun. Gefällt mir. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_rest-0188` | <strong>Bubble 1:</strong> Ich lasse die Ruhe noch ein bisschen dauern. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_rest-0189` | <strong>Bubble 1:</strong> Ein guter Moment, es gemütlich zu haben. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_rest-0190` | <strong>Bubble 1:</strong> Wir könnten diese Ruhe einfach behalten. Ich wäre dafür. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_rest-0191` | <strong>Bubble 1:</strong> Angenehme Gesellschaft und Ruhe. Das passt mir. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-computer_effort_rest-0192` | <strong>Bubble 1:</strong> Ich mag solche stillen Momente mit dir. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### computer_effort_steady

Occasional load comment, effort >=0.7; freshness, quiet interval and random draw apply.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `computer_effort_steady-01` | <strong>Bubble 1:</strong> Ich bin schon eine Weile dran. Ich merke es. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_steady-02` | <strong>Bubble 1:</strong> Ich arbeite lieber in Ruhe. Du weißt das. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_steady-03` | <strong>Bubble 1:</strong> Noch nicht fertig. Aber ich bin dran. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_steady-04` | <strong>Bubble 1:</strong> Nicht gerade leicht. Aber gleichmäßig ist mir lieber. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_steady-05` | <strong>Bubble 1:</strong> Du kannst ruhig weitermachen. Ich halte mit. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_effort_steady-06` | <strong>Bubble 1:</strong> Ich mache das schon. Ohne großes Theater. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 150 s; weight: 1 | No |  |

### computer_uptime

Retained catalogue copy. Current mind remaps detector computer_uptime to computer_uptime_grounded before selection; not normal emitted desktop wording.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `computer_uptime-02` | <strong>Bubble 1:</strong> Schon eine ganze Weile hier. Fällt mir kaum noch auf. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 150 s; weight: 2 | No |  |
| `computer_uptime-05` | <strong>Bubble 1:</strong> Man verliert hier leicht das Zeitgefühl. ...Du auch? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: confirmed<br>Presentation: short<br>Animation: idle<br>Cooldown: 150 s; weight: 2 | No |  |
| `v010-uptime-legacy-01` | <strong>Bubble 1:</strong> Ich bin schon lange eingeschaltet. Zwischendurch hatte ich aber meine Ruhe. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 2 | No |  |
| `v010-uptime-legacy-02` | <strong>Bubble 1:</strong> So viele Stunden. Die meisten davon waren ziemlich entspannt. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 2 | No |  |
| `v010-uptime-legacy-03` | <strong>Bubble 1:</strong> Ich laufe schon eine Weile. Im übertragenen Sinn. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 110 s; weight: 2 | No |  |

### computer_uptime_grounded

Detector reports uptime >=8 h (or low-load long-uptime draw), then mind remaps to this event.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-computer_uptime_grounded-01` | <strong>Bubble 1:</strong> Der Rechner läuft schon eine ganze Weile.<br><strong>Bubble 2:</strong> Ich habe zwischendurch trotzdem Pause gemacht. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 300 s; weight: 3 | No |  |
| `v010-computer_uptime_grounded-03` | <strong>Bubble 1:</strong> Ich weiß noch, dass ich vorhin Ruhe hatte.<br><strong>Bubble 2:</strong> Die gönne ich mir wieder. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 300 s; weight: 3 | No |  |
| `uptime-rest-0` | <strong>Bubble 1:</strong> Der Rechner läuft lange. Meine Pausen gehören trotzdem dazu. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `uptime-rest-1` | <strong>Bubble 1:</strong> Eine lange Laufzeit. Ich habe zwischendurch gut ausgeruht. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `uptime-rest-2` | <strong>Bubble 1:</strong> Der Rechner ist schon lange an. Ich hatte zwischendurch die vernünftige Idee, Pause zu machen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### work_late

Focused observed work at night with strain >=35 or energy <=45; earlier need branches still take precedence.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-work_late-01` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Ich wollte gerade langsamer werden.<br><strong>Bubble 2:</strong> Schlechter Zeitpunkt, offenbar. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 260 s; weight: 3 | No |  |
| `v010-work_late-02` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Es ist spät. Ich weiß.<br><strong>Bubble 2:</strong> Ich arbeite ja trotzdem. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 260 s; weight: 3 | No |  |
| `v010-work_late-03` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> ...Nicht jetzt müde werden.<br><strong>Bubble 2:</strong> Das sage ich übrigens zu mir. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 260 s; weight: 3 | No |  |
| `v010-work_late-04` | <em>Emote: sleeps (800 ms)</em><br><strong>Bubble 1:</strong> Du und deine späten Ideen.<br><strong>Bubble 2:</strong> ...Meine späten Ideen jetzt wohl auch. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: night<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 260 s; weight: 3 | No |  |

### work_long_thought

Focused observed work >=1,200 s after late-night branch did not match.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-work_long_thought-01` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Es ist noch nicht vorbei.<br><strong>Bubble 2:</strong> Ich sag Bescheid, wenn ich Luft habe. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 240 s; weight: 3 | No |  |
| `v010-work_long_thought-02` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Ich halte das durch.<br><strong>Bubble 2:</strong> Sogar ohne dramatische Musik. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 240 s; weight: 3 | No |  |
| `v010-work_long_thought-03` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Jetzt nicht abschweifen.<br><strong>Bubble 2:</strong> ...Schon passiert. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 240 s; weight: 3 | No |  |

### work_concentrating

Focused observed work after late-night/prolonged-work branches did not match.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-work_concentrating-01` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Ich bin gerade ziemlich bei der Sache. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 260 s; weight: 3 | No |  |
| `v010-work_concentrating-02` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> ...Konzentrieren.<br><strong>Bubble 2:</strong> Ja, ich rede dabei mit mir selbst. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 260 s; weight: 3 | No |  |
| `v010-work_concentrating-03` | <em>Emote: exclamation (800 ms)</em><br><strong>Bubble 1:</strong> Ich denke gerade lieber zu Ende, bevor ich anfange zu reden. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 260 s; weight: 3 | No |  |

### after_work_thought

Not focused; one reflection 60-480 s after observed work lasting >=1,200 s, after earlier need branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-after_work_thought-01` | <strong>Bubble 1:</strong> Ich bin noch ein bisschen in Gedanken bei der Arbeit. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 250 s; weight: 3 | No |  |
| `v010-after_work_thought-02` | <strong>Bubble 1:</strong> ...Ich wollte gerade loslaufen.<br><strong>Bubble 2:</strong> Vielleicht noch eine Minute sitzen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 250 s; weight: 3 | No |  |
| `v010-after_work_thought-03` | <strong>Bubble 1:</strong> So schnell schalte ich nach so was nicht um.<br><strong>Bubble 2:</strong> Ich mach langsam. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 250 s; weight: 3 | No |  |

### work_unexpected

Rising/heavy/peak measured-load event reinterpreted: confident learned expected effort <0.3, measured effort >=0.5.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-work_unexpected-01` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> ...Damit hatte ich um diese Zeit nicht gerechnet. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-work_unexpected-02` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Oh. Ich war gerade auf Ruhe eingestellt.<br><strong>Bubble 2:</strong> War wohl voreilig. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 110 s; weight: 3 | No |  |
| `v010-work_unexpected-03` | <em>Emote: alert (800 ms)</em><br><strong>Bubble 1:</strong> Das kam plötzlich.<br><strong>Bubble 2:</strong> Na gut. Ich bin dabei. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 110 s; weight: 3 | No |  |

### work_finished_interrupted

Recovered-load event after >=2 recorded interruptions and prior work >=18 s; before long-work branch.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-work_finished_interrupted-01` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> ...Fertig. Und du wolltest vorhin etwas?<br><strong>Bubble 2:</strong> Ich habe dich nicht vergessen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 200 s; weight: 3 | No |  |
| `v010-work_finished_interrupted-02` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> So. Jetzt darfst du wieder klicken.<br><strong>Bubble 2:</strong> Das war ein Scherz. Größtenteils. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waving<br>Cooldown: 200 s; weight: 3 | No |  |
| `v010-work_finished_interrupted-03` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Du hast vorhin ziemlich auf dich aufmerksam gemacht.<br><strong>Bubble 2:</strong> ...Jetzt habe ich auch wieder Zeit dafür. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 200 s; weight: 3 | No |  |
| `v010-work_finished_interrupted-04` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Ich hab mich nicht absichtlich nicht gemeldet.<br><strong>Bubble 2:</strong> Ich war wirklich beschäftigt. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 200 s; weight: 3 | No |  |

### work_finished_long

Recovered-load event after prior observed work >=1,200 s unless interrupted-work branch applies.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `v010-work_finished_long-01` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> ...Uff. Das war ein langer Ritt.<br><strong>Bubble 2:</strong> Ich sitze zwar. Also ... bildlich.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 260 s; weight: 3 | No |  |
| `v010-work_finished_long-02` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Ich glaube, ich brauche eine Weile Ruhe.<br><strong>Bubble 2:</strong> Nur kurz. Hoffentlich.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 260 s; weight: 3 | No |  |
| `v010-work_finished_long-03` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Das war schon eine ordentliche Strecke.<br><strong>Bubble 2:</strong> Ich hab sie trotzdem geschafft.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 260 s; weight: 3 | No |  |
| `v010-work_finished_long-04` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> ...Okay. Jetzt bitte etwas weniger auf einmal.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 260 s; weight: 3 | No |  |
| `v010-work_finished_long-05` | <em>Emote: swirl (800 ms)</em><br><strong>Bubble 1:</strong> Ich bin durch.<br><strong>Bubble 2:</strong> Und ich werde es mir jetzt sehr gemütlich machen.<br><em>Emote: star (800 ms)</em> | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 260 s; weight: 3 | No |  |

## Cursor and walking

### cursor_follow

Actual pointer motion, spontaneous speech/follow_cursor on, awake, toolbar inactive, timer due, >100 s since speech, 8% draw, distance <=60% screen width; foreground/playback guards apply.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `cursor_follow-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Dein Mauszeiger ist schwer zu ignorieren. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 250 s; weight: 2 | No |  |
| `cursor_follow-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du zeichnest ziemlich seltsame Muster. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 250 s; weight: 2 | No |  |
| `cursor_follow-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du weißt, dass ich das verfolgen kann? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 250 s; weight: 2 | No |  |
| `cursor_follow-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> ...Interessante Route. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 250 s; weight: 2 | No |  |
| `cursor_follow-05` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Nur damit du's weißt: Ich passe auf. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 250 s; weight: 2 | No |  |
| `cursor_follow-06` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Wo willst du eigentlich hin? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: review<br>Cooldown: 250 s; weight: 2 | No |  |

### cursor_far

Same cursor gates, distance >60% screen width.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `cursor_far-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Was ist da drüben so wichtig? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 300 s; weight: 2 | No |  |
| `cursor_far-02` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Ich sehe dich auch von hier. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 300 s; weight: 2 | No |  |
| `cursor_far-03` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> ...Du bist ziemlich weit weg. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 300 s; weight: 2 | No |  |
| `cursor_far-04` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Du musst nicht zurückkommen. Ich guck nur. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 300 s; weight: 2 | No |  |

### walk_pause

Completed walk, spontaneous speech on, >130 s since speech, 23% draw; active playback protected.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `walk_pause-01` | <strong>Bubble 1:</strong> Hier.<br><strong>Bubble 2:</strong> ...Ja. Hier bleibe ich kurz. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 180 s; weight: 2 | No |  |
| `walk_pause-02` | <strong>Bubble 1:</strong> ...Ein bisschen stehen bleiben. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 180 s; weight: 2 | No |  |
| `walk_pause-03` | <strong>Bubble 1:</strong> So. Die Aussicht ist besser. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 180 s; weight: 2 | No |  |
| `walk_pause-04` | <strong>Bubble 1:</strong> Ich glaube, ich bleibe kurz hier. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 180 s; weight: 2 | No |  |
| `walk_pause-05` | <strong>Bubble 1:</strong> Ich gehe nur, wenn ich einen Grund sehe. Meistens. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: waiting<br>Cooldown: 180 s; weight: 2 | No |  |

## Objects, food portions and search

### object_place_missing

Actually checked learned place lacks matching subject; separate cue per missing known portion, including additional losses in search.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-place-missing-here` | <strong>Bubble 1:</strong> Hier war doch {item}. Wo ist das hin? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Hä? Wo ist denn {item_poss_nom} hin? |
| `object-place-missing-noticed` | <strong>Bubble 1:</strong> Moment. {item} ist nicht mehr hier. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Moment, {item_poss_nom} ist nicht mehr da. Eben lag {item_pron_nom} noch hier. |
| `object-place-missing-empty` | <strong>Bubble 1:</strong> {item} sehe ich hier gerade nicht mehr. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Hier ist {item_poss_nom} nicht mehr. Habe ich {item_pron_acc} übersehen? |

### object_notice

Autonomous object goal for identity not yet learned, before approach/inspection.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-notice-01` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Hm? Da liegt etwas. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Oh, da liegt ein Gegenstand! |
| `voice-object_notice-0001` | <strong>Bubble 1:</strong> Was liegt denn da? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Was liegt denn da unten? Den Gegenstand will ich mir ansehen. |
| `voice-object_notice-0002` | <strong>Bubble 1:</strong> Hm. Das sieht interessant aus. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |

### object_approach

Approach toward object, including unknown recovery candidate within existing search task.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-approach-01` | <strong>Bubble 1:</strong> Na gut. Jetzt will ich’s wissen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Na dann. Ich schaue mir den Gegenstand aus der Nähe an. |
| `voice-object_approach-0005` | <strong>Bubble 1:</strong> Ich geh mal rüber. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |
| `voice-object_approach-0006` | <strong>Bubble 1:</strong> Das lasse ich mir nicht entgehen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |

### object_pick_up

Pickup phase after approach/reach and custody guards.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-pick-up-01` | <strong>Bubble 1:</strong> So. Einmal hoch damit. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `voice-object_pick_up-0007` | <strong>Bubble 1:</strong> Dich schnapp ich mir kurz. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |
| `voice-object_pick_up-0008` | <strong>Bubble 1:</strong> Komm mal her, du. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |

### object_inspect

Deliberate in-hand inspection, including unknown items/type conflicts.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-inspect-01` | <strong>Bubble 1:</strong> Hm. Was bist du denn? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `voice-object_inspect-0009` | <strong>Bubble 1:</strong> Moment … gleich hab ich’s. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |
| `voice-object_inspect-0010` | <strong>Bubble 1:</strong> Einen Moment noch. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |

### object_recognized

Identity actually acquired through inspection/presentation; can precede offer appraisal.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-recognized-01` | <strong>Bubble 1:</strong> Ah, {item}. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ah, {item_indef_nom}! |
| `voice-object_recognized-0011` | <strong>Bubble 1:</strong> {item}. Na also. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Oh, {item_indef_nom}! Jetzt erkenne ich {item_pron_acc}. |
| `voice-object_recognized-0012` | <strong>Bubble 1:</strong> Ach, {item}. Alles klar. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Na klar. Das ist {item_indef_nom}. |

### object_unknown

Use appraisal still says unrecognized; no permission to invent a known food identity.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-unknown-01` | <strong>Bubble 1:</strong> Hm. Das kann ich gerade nicht zuordnen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Für diesen Gegenstand kenne ich noch keinen Namen. Da rate ich lieber nicht. |
| `voice-object_unknown-0013` | <strong>Bubble 1:</strong> Da bin ich mir noch nicht sicher. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Hm, für diesen Gegenstand habe ich noch keinen passenden Namen gelernt. |
| `voice-object_unknown-0014` | <strong>Bubble 1:</strong> Hm. Ich weiß noch nicht, was das ist. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |

### object_want

Autonomous held-object use appraisal chooses consume.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-want-01` | <strong>Bubble 1:</strong> Das kann ich gerade gut gebrauchen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `voice-object_want-0015` | <strong>Bubble 1:</strong> Ja. Das passt gerade gut. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ja, genau das kann ich gerade gebrauchen. |
| `voice-object_want-0016` | <strong>Bubble 1:</strong> Das nehme ich mir jetzt. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |

### object_later

Autonomous use appraisal declines consumption for a reason other than unknown identity.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-later-01` | <strong>Bubble 1:</strong> Jetzt brauche ich das noch nicht. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `voice-object_later-0017` | <strong>Bubble 1:</strong> Das hat noch ein bisschen Zeit. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |
| `voice-object_later-0018` | <strong>Bubble 1:</strong> Ich hebe es erst einmal auf. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |

### object_put_down

Safe put-down of held item; existing custody/interruption lifecycle applies.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-put-down-01` | <strong>Bubble 1:</strong> Ich setze das wieder ab. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `voice-object_put_down-0021` | <strong>Bubble 1:</strong> Hier lasse ich das erst mal. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |
| `voice-object_put_down-0022` | <strong>Bubble 1:</strong> Das bleibt erst mal hier. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |

### object_handover

Actual user-offered portion handover, rather than merely noticing a nearby cursor item.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-handover-01` | <strong>Bubble 1:</strong> Danke für {item}. Das nehme ich gern. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Für mich? {Item_indef_nom}? Danke, ich nehme {item_pron_acc} vorsichtig. |
| `voice-object_handover-0025` | <strong>Bubble 1:</strong> Danke. {item} passt gerade gut. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Oh, {item_indef_nom}! Das kann ich jetzt gut brauchen. |
| `voice-object_handover-0026` | <strong>Bubble 1:</strong> Ja, danke. {item} kann ich gerade gebrauchen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Du gibst mir {item_indef_acc}. Das war aufmerksam von dir. |
| `situation-object_handover-001` | <strong>Bubble 1:</strong> Danke fürs Geben. {item} nehme ich gern. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ah, {item_indef_nom}. Danke! Ich muss mich noch ans Annehmen gewöhnen. |
| `situation-object_handover-002` | <strong>Bubble 1:</strong> Für mich? Danke für {item}. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Das ist also für mich. {Item_indef_acc} nehme ich gern. |
| `situation-object_handover-003` | <strong>Bubble 1:</strong> Danke. {item} passt mir gerade gut. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Danke, ich passe auf {item_def_acc} auf. |
| `situation-object_handover-004` | <strong>Bubble 1:</strong> Gute Idee. {item} kann ich gerade gebrauchen. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> {Item_indef_nom} kommt gerade recht. Danke dir. |
| `situation-object_handover-005` | <strong>Bubble 1:</strong> Danke. Mit {item} wird meine Pause gleich besser. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Du hast {item_indef_acc} dabei? Dann wird mein kleiner Vorrat interessanter. |
| `situation-object_handover-006` | <strong>Bubble 1:</strong> {item} nehme ich gern von dir. Danke. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ich nehme {item_indef_acc}. {Item_pron_acc} halte ich lieber gut fest. |
| `situation-object_handover-007` | <strong>Bubble 1:</strong> Danke, du. {item} passt genau. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Du hast an {item_indef_acc} gedacht. Das gefällt mir. |
| `situation-object_handover-008` | <strong>Bubble 1:</strong> Du bringst mir {item}. Das freut mich. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Oh, {item_indef_nom} passt gerade gut. Danke! |
| `situation-object_handover-009` | <strong>Bubble 1:</strong> Danke. {item} wollte ich gerade haben. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Danke. Ich mache erst einmal Platz für {item_def_acc}. |
| `situation-object_handover-010` | <strong>Bubble 1:</strong> Danke, dass du an mich denkst. {item} nehme ich gern. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Das ist für mich? {Item_indef_acc} nehme ich gern von dir. |
| `situation-object_handover-011` | <strong>Bubble 1:</strong> Ich freue mich über {item}. Danke dir. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Mit {item_indef_dat} hast du meine Aufmerksamkeit. Danke! |
| `situation-object_handover-012` | <strong>Bubble 1:</strong> {item}, für mich. Schön. Danke. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> {Item_indef_acc} in meine Hände? Ein guter Plan. Danke dir. |

### object_offer

Known offered item appraised as consumable now; revised appraisal retains same episode.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-offer-01` | <strong>Bubble 1:</strong> Ja, {item} hätte ich gerne. Gibst du es mir? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Du bietest mir {item_indef_acc} an? Ja, {item_pron_acc} würde ich gern nehmen. |
| `voice-object_offer-0027` | <strong>Bubble 1:</strong> {item} nehme ich gern. Magst du es mir geben? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Oh, {item_indef_nom}. Reichst du {item_pron_acc} mir bitte? |
| `voice-object_offer-0028` | <strong>Bubble 1:</strong> Ja, bitte. {item} passt gerade. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Das kommt mir gelegen. {Item_indef_acc} hätte ich gern. |
| `expanded-object_offer-0130` | <strong>Bubble 1:</strong> Ja, bitte. {item} hätte ich gern. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: hungry<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ja bitte. {Item_indef_nom} wäre jetzt eine gute Idee. |
| `expanded-object_offer-0131` | <strong>Bubble 1:</strong> {item} wäre gerade willkommen. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: hungry<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> {Item_indef_nom}? Hm, das passt. {Item_pron_acc} nehme ich gern. |
| `expanded-object_offer-0132` | <strong>Bubble 1:</strong> Gern. {item} passt mir gerade. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: hungry<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Bitte her damit. {Item_indef_acc} könnte ich gebrauchen. |
| `expanded-object_offer-0154` | <strong>Bubble 1:</strong> Gut, dass du {item} anbietest. Das hätte ich gern. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: hungry<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Du hast {item_indef_acc} im Angebot? Überzeugend. |
| `expanded-object_offer-0155` | <strong>Bubble 1:</strong> Ja, bitte. {item} nehme ich gern. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: hungry<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> {Item_indef_nom} klingt nach einer guten Idee. Ich bin dabei. |
| `expanded-object_offer-0156` | <strong>Bubble 1:</strong> {item} hätte ich gern von dir. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: hungry<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ja, bitte. Ich mache in meinen Händen Platz für {item_def_acc}. |
| `situation-object_offer-013` | <strong>Bubble 1:</strong> {item} hätte ich gern. Magst du es mir geben? | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Für mich? Dann nehme ich {item_def_acc} gern. |
| `situation-object_offer-014` | <strong>Bubble 1:</strong> Ja, bitte. {item} kann ich gerade gebrauchen. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Oh, {item_indef_nom}. {Item_pron_acc} würde ich gerne näher ansehen. |
| `situation-object_offer-015` | <strong>Bubble 1:</strong> Oh, {item} nehme ich gern an. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ja. {Item_indef_nom} passt zu meinen Plänen. |
| `situation-object_offer-016` | <strong>Bubble 1:</strong> Überzeugendes Angebot. {item} hätte ich gern. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Du weißt, wie man meine Neugier weckt: mit {item_indef_dat}. |
| `situation-object_offer-017` | <strong>Bubble 1:</strong> Ja, {item} passt zu meinen momentanen Plänen. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Na gut. {Item_def_nom} darf gern zu mir herüber. |
| `situation-object_offer-018` | <strong>Bubble 1:</strong> {item} nehme ich. Eine interessante Aufmerksamkeit. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Das Angebot mit {item_def_dat} nehme ich an. Gute Wahl! |
| `situation-object_offer-019` | <strong>Bubble 1:</strong> Ja, gern. Danke, {item}s du es mir anbietest. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ich hätte {item_def_acc} gern. Gibst du {item_pron_acc} mir? |
| `situation-object_offer-020` | <strong>Bubble 1:</strong> {item} hätte ich jetzt gern von dir. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> {Item_indef_nom}? Da sage ich nicht Nein. |
| `situation-object_offer-021` | <strong>Bubble 1:</strong> {item} nehme ich gern. Gute Idee, es mir anzubieten. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ja, ich hätte {item_def_acc} gern. Du darfst loslassen. |
| `situation-object_offer-022` | <strong>Bubble 1:</strong> {item}? Gern. Deine Aufmerksamkeit freut mich. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Du kannst mir {item_def_acc} geben. Ich passe darauf auf. |
| `situation-object_offer-023` | <strong>Bubble 1:</strong> {item}? Ja, bitte. Darüber freue ich mich gerade. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Oh, {item_indef_nom} für mich? Ja, bitte! |
| `situation-object_offer-024` | <strong>Bubble 1:</strong> {item} hätte ich gern. Schön, {item}s du an mich denkst. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Bei {item_indef_dat} werde ich schwach. Reichst du {item_pron_acc} mir? |

### object_refuse

Known offered item appraised as not consumable now; does not fabricate identity.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-refuse-01` | <strong>Bubble 1:</strong> {item}? Gerade brauche ich das nicht. Vielleicht später. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> {Item_indef_nom}? Danke, aber ich brauche gerade nichts. |
| `voice-object_refuse-0029` | <strong>Bubble 1:</strong> {item}? Gerade lieber nicht. Danke fürs Anbieten. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ich sehe {item_def_acc}. Gerade sage ich dazu lieber Nein. |
| `voice-object_refuse-0030` | <strong>Bubble 1:</strong> {item}? Nein danke. Im Moment brauche ich es nicht. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Das ist nett, aber {item_def_acc} brauche ich im Moment nicht. |
| `situation-object_refuse-025` | <strong>Bubble 1:</strong> {item}? Danke fürs Anbieten. Gerade brauche ich es nicht. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> {Item_def_acc} lasse ich gerade lieber liegen. Danke trotzdem. |
| `situation-object_refuse-026` | <strong>Bubble 1:</strong> {item}? Im Moment lieber nicht. Danke dir. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Nein danke. Für {item_indef_acc} ist gerade nicht der richtige Zeitpunkt. |
| `situation-object_refuse-027` | <strong>Bubble 1:</strong> {item}? Jetzt habe ich dafür keinen Bedarf. Später vielleicht. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Du kannst {item_def_acc} erst mal behalten. Vielleicht später. |
| `situation-object_refuse-028` | <strong>Bubble 1:</strong> {item}? Ein gutes Angebot zu einem etwas unpassenden Zeitpunkt. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> {Item_indef_nom}? Im Augenblick passt das nicht. |
| `situation-object_refuse-029` | <strong>Bubble 1:</strong> {item}? Danke. Mein Bedarf macht gerade Pause. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Über {item_def_acc} denke ich später gern noch mal nach. |
| `situation-object_refuse-030` | <strong>Bubble 1:</strong> {item}? Gerade passt es mir weniger. Vielleicht später. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ich glaube, {item_def_nom} muss noch ein bisschen warten. |
| `situation-object_refuse-031` | <strong>Bubble 1:</strong> {item}? Danke, du. Gerade brauche ich es nicht. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Du meinst es gut, aber {item_def_acc} brauche ich gerade wirklich nicht. |
| `situation-object_refuse-032` | <strong>Bubble 1:</strong> {item}? Für später wäre es schön. Jetzt möchte ich noch warten. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Danke, du. {Item_indef_nom} ist im Moment nicht das Richtige für mich. |
| `situation-object_refuse-033` | <strong>Bubble 1:</strong> {item}? Das Angebot freut mich. Gerade passt es noch nicht. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Du darfst {item_def_acc} gern erst einmal wieder ablegen. |
| `situation-object_refuse-034` | <strong>Bubble 1:</strong> {item}? Schön, dass du an mich denkst. Jetzt brauche ich es gerade nicht. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> {Item_def_acc} merke ich mir für später. Jetzt noch nicht. |
| `situation-object_refuse-035` | <strong>Bubble 1:</strong> {item}? Gerade lieber nicht. Über deine Aufmerksamkeit freue ich mich trotzdem. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Auch bei dir sage ich manchmal Nein. {Item_def_acc} brauche ich gerade nicht. |
| `situation-object_refuse-036` | <strong>Bubble 1:</strong> {item}? Danke, du. Ich möchte im Moment noch ein bisschen warten. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> {Item_indef_nom}? Lieb von dir, aber ich möchte lieber warten. |

### object_recall_food

Known food supply retrieved for new need, not deferred/continuing-wish branch.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-recall-food-01` | <strong>Bubble 1:</strong> Moment. Ich habe doch noch {item}. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ach richtig, da war noch {item_indef_nom}. Jetzt wäre ein guter Zeitpunkt. |
| `voice-object_recall_food-0031` | <strong>Bubble 1:</strong> Ich habe Hunger. Da liegt noch {item}. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Mein Magen erinnert mich an {item_def_acc}. Gut, dass noch etwas übrig ist. |
| `voice-object_recall_food-0032` | <strong>Bubble 1:</strong> Mein Vorrat ist gerade eine gute Idee: {item}. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Da ist noch {item_indef_nom}. Das kommt meinem Magen gerade recht. |

### object_recall_drink

Known drink supply retrieved for new need, not deferred/continuing-wish branch.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-recall-drink-01` | <strong>Bubble 1:</strong> Meine Energie wird knapp. Ich habe ja noch {item}. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Meine Energie sinkt. Gut, dass ich noch {item_indef_acc} hier habe. |
| `voice-object_recall_drink-0033` | <strong>Bubble 1:</strong> Etwas Energie wäre gut. Ich habe noch {item}. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Vielleicht wäre jetzt der richtige Moment für {item_def_acc}. |
| `voice-object_recall_drink-0034` | <strong>Bubble 1:</strong> Ich werde müde. Zeit, nach {item} zu sehen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Da war doch noch {item_indef_nom}. Mein müder Kopf erinnert sich gerade daran. |

### object_recall_saved_food

Known previously deferred food retrieved for new need.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-recall-saved-food-01` | <strong>Bubble 1:</strong> Gut, dass ich noch {item} aufgehoben habe. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> {Item_poss_nom} ist noch da. Heute zahlt sich Vorratshaltung aus. |
| `voice-object_recall_saved_food-0035` | <strong>Bubble 1:</strong> Mein Vorrat für später: {item}. Jetzt passt es. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ich habe {item_poss_acc} für genau so einen hungrigen Moment aufgehoben. |
| `voice-object_recall_saved_food-0036` | <strong>Bubble 1:</strong> Ah, mein Vorrat: {item}. Gut, dass ich vorgesorgt habe. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Na bitte, {item_poss_nom} ist noch da. Danke an mein früheres Ich. |

### object_recall_saved_drink

Known previously deferred drink retrieved for new need.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-recall-saved-drink-01` | <strong>Bubble 1:</strong> Meine Energie wird knapp. Zum Glück habe ich mir noch {item} aufgehoben. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ich habe {item_poss_acc} aufgehoben. Jetzt wäre etwas neue Energie willkommen. |
| `voice-object_recall_saved_drink-0037` | <strong>Bubble 1:</strong> Gut, dass ich noch {item} für später habe. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Sieh an: {item_poss_nom} steht noch bereit. Mein Plan von vorhin funktioniert. |
| `voice-object_recall_saved_drink-0038` | <strong>Bubble 1:</strong> Jetzt kommt mein aufgehobenes Getränk gerade richtig: {item}. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes | <strong>Bubble 1:</strong> {Item_poss_nom} kommt mir gerade sehr gelegen. |

### object_consuming_food

Committed food consumption begins after confirmed custody/use permission.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-consuming-food-01` | <strong>Bubble 1:</strong> Gut. Jetzt habe ich Zeit für {item}. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> So, jetzt esse ich {item_def_acc}. Das geht besser in Ruhe. |
| `voice-object_consuming_food-0039` | <strong>Bubble 1:</strong> Ich esse jetzt in Ruhe. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |
| `voice-object_consuming_food-0040` | <strong>Bubble 1:</strong> So. Zeit für ein bisschen Stärkung. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |

### object_consuming_drink

Committed drink consumption begins after confirmed custody/use permission.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-consuming-drink-01` | <strong>Bubble 1:</strong> Ein bisschen neue Energie. Das passt gerade. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `voice-object_consuming_drink-0041` | <strong>Bubble 1:</strong> Das kann ich gerade gut gebrauchen. Ein Schluck zuerst. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |
| `voice-object_consuming_drink-0042` | <strong>Bubble 1:</strong> Ich trinke erst einmal etwas. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |

### object_finished_food

Food animation completes. Prepared human-handover care dialogue replaces this event when present; autonomous completion uses this event.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-finished-food-01` | <strong>Bubble 1:</strong> Das war jetzt genau richtig. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `voice-object_finished_food-0043` | <strong>Bubble 1:</strong> Das war eine gute Entscheidung. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |
| `voice-object_finished_food-0044` | <strong>Bubble 1:</strong> Jetzt fühlt sich mein Magen wieder wohler. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |

### object_finished_drink

Drink animation completes. Prepared human-handover care dialogue replaces this event when present; autonomous completion uses this event.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-finished-drink-01` | <strong>Bubble 1:</strong> Das gibt mir wieder etwas Schwung. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `voice-object_finished_drink-0045` | <strong>Bubble 1:</strong> Ah. Ich fühle mich wieder etwas wacher. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |
| `voice-object_finished_drink-0046` | <strong>Bubble 1:</strong> Das hat mir gerade gefehlt. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |

### object_missing

Committed interaction loses its subject; distinct from free-observation visual loss.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-missing-01` | <strong>Bubble 1:</strong> Einmal alles abgesucht. Noch keine Spur. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `voice-object_missing-0047` | <strong>Bubble 1:</strong> Ich bin einmal durch. Noch fehlt etwas. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |
| `voice-object_missing-0048` | <strong>Bubble 1:</strong> Für jetzt habe ich überall nachgesehen. Noch fehlt etwas. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | Yes |  |

### object_search

Missing-subject search after verified absence, not visual occlusion alone.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-search-nearby` | <strong>Bubble 1:</strong> Wo ist {item} hin? Ich suche die ganze Taskleiste ab. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> {Item_poss_nom} ist nicht am gewohnten Platz. Ich schaue den Weg entlang. |
| `object-search-place` | <strong>Bubble 1:</strong> Hier finde ich {item} gerade nicht. Ich laufe die Taskleiste ab. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ich suche {item_poss_acc}. Vielleicht finde ich {item_pron_acc} weiter drüben auf der Taskleiste. |
| `object-search-local` | <strong>Bubble 1:</strong> Hier war doch noch {item}. Ich suche bis zum anderen Ende. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Hier war doch {item_poss_nom}. Ich schaue noch einmal nach. |

### object_found

Candidate verified as resolving a missing subject in existing search task.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-found-nearby` | <strong>Bubble 1:</strong> Ah, da ist {item} wieder. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ah, da ist ja wohl {item_poss_nom}! |
| `object-found-alternative` | <strong>Bubble 1:</strong> {item}. Wiedergefunden. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> {Item_poss_nom}! Da bist du ja. |
| `object-found-supply` | <strong>Bubble 1:</strong> Da bist du ja, {item}. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ah, {item_poss_nom}. Ich hatte dich schon abgeschrieben. |

### object_busy

User contact during committed non-search object action, <=1 feedback per 8 s.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-busy-1` | <strong>Bubble 1:</strong> Warte einen kleinen Moment, ich will mir das da anschauen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `object-busy-2` | <strong>Bubble 1:</strong> Gleich. Ich bin gerade mit diesem Gegenstand beschäftigt. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ich halte gerade einen Gegenstand in den Händen. Gib mir noch einen Moment. |
| `object-busy-3` | <strong>Bubble 1:</strong> Einen Augenblick bitte. Das hier möchte ich erst zu Ende anschauen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |

### object_taken

User takes the same committed object, starting/updating withholding episode.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-taken-1` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Huch, das wollte ich mir gerade anschauen! Gibst du es mir wieder? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `object-taken-2` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Hey, ich war gerade auf dem Weg dorthin. Darf ich das noch anschauen? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `object-taken-3` | <em>Emote: question (800 ms)</em><br><strong>Bubble 1:</strong> Moment, genau das wollte ich mir ansehen. Legst du es bitte wieder hin? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |

### object_request_return

Committed item held away; >=10 s since request, <3 takes and <18 s held time (not yet irritated).

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-request-return-1` | <strong>Bubble 1:</strong> Kannst du das bitte wieder hinlegen? Ich möchte es noch anschauen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `object-request-return-2` | <strong>Bubble 1:</strong> Ich warte noch auf diesen Gegenstand. Gibst du ihn mir zurück? | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `object-request-return-3` | <strong>Bubble 1:</strong> Darf ich jetzt weitermachen? Das wollte ich mir gerade ansehen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |

### object_withheld

Same request gate, but >=3 takes or >=18 s held time makes response irritated.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-withheld-1` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> Jetzt ärgert mich das. Bitte gib mir den Gegenstand wieder. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> Jetzt reicht's aber mit Wegnehmen. Ich möchte den Gegenstand zurück. |
| `object-withheld-2` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> Du weißt doch, dass ich das anschauen will. Bitte leg es wieder hin. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `object-withheld-3` | <em>Emote: anger (800 ms)</em><br><strong>Bubble 1:</strong> Das ständige Wegnehmen finde ich nicht lustig. Ich möchte weitermachen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |

### object_returned

Same taken committed subject returned; existing episode resumes.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `object-returned-1` | <strong>Bubble 1:</strong> Danke. Dann mache ich hier weiter. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `object-returned-2` | <strong>Bubble 1:</strong> Da ist es wieder. Jetzt kann ich weitermachen. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `object-returned-3` | <strong>Bubble 1:</strong> Gut, du hast es zurückgelegt. Ich mache weiter. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |

### object_consider_known

Autonomous goal for known identity, without known-supply retrieval/continuing-wish branches.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `continuity-object_consider_known-1` | <strong>Bubble 1:</strong> {item} kenne ich schon. Ich hole es mir kurz. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> {Item_def_acc} kenne ich schon. Ich sehe nach, ob ich {item_pron_acc} jetzt brauche. |
| `continuity-object_consider_known-2` | <strong>Bubble 1:</strong> Da liegt {item}. Ich schaue, ob ich es gerade brauche. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Da ist {item_def_nom}. Das könnte gleich interessant werden. |
| `continuity-object_consider_known-3` | <strong>Bubble 1:</strong> {item}. Ich nehme es kurz in die Hand und entscheide dann. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Oh, {item_def_nom} wieder. Ich schaue beim Näherkommen, ob ich {item_pron_acc} nehme. |

### object_collect_wanted

Retrieving known supply for an existing continuing wish, no invented fresh desire.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `continuity-object_collect_wanted-1` | <strong>Bubble 1:</strong> {item} wollte ich gerade haben. Ich hole es mir. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> {Item_def_acc} wollte ich noch. Ich gehe gleich hin. |
| `continuity-object_collect_wanted-2` | <strong>Bubble 1:</strong> Da liegt {item} jetzt. Das nehme ich mir. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Da ist {item_def_nom}. Gut, dann hole ich {item_pron_acc} mir jetzt. |
| `continuity-object_collect_wanted-3` | <strong>Bubble 1:</strong> Ja, {item} möchte ich noch. Ich hole es mir jetzt. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes | <strong>Bubble 1:</strong> Ich habe mich entschieden: {item_def_nom} soll nicht länger dort liegen. |

### object_busy_search

User contact during active search/inspection in search, same 8 s throttle.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `contact-object_busy_search-1` | <strong>Bubble 1:</strong> Ich suche gerade etwas. Gleich bin ich wieder bei dir. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `contact-object_busy_search-2` | <strong>Bubble 1:</strong> Moment. Ich will erst finden, was hier fehlt. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |
| `contact-object_busy_search-3` | <strong>Bubble 1:</strong> Ich bin noch auf der Suche. Gib mir einen Augenblick. | Stage: any<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 0 s; weight: 1 | Yes |  |

## Rock-Paper-Scissors

### game_greeting

RPS greeting: desktop live session context; standalone defaults acquaintance/calm unless supplied. First text only.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `expanded-game_greeting-0001` | <strong>Bubble 1:</strong> Eine Runde Schere, Stein, Papier? Ich bin bereit. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_greeting-0002` | <strong>Bubble 1:</strong> Gut. Mal sehen, welche Hand heute passt. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_greeting-0003` | <strong>Bubble 1:</strong> Eine kleine Runde. Viel Erfolg. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_greeting-0004` | <strong>Bubble 1:</strong> Ich habe meinen Ehrgeiz mitgebracht. Du auch? | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_greeting-0005` | <strong>Bubble 1:</strong> Na gut. Die erste Hand gehört ganz meinen großen Plänen. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_greeting-0006` | <strong>Bubble 1:</strong> Bereit? Ich bin vorsichtig siegessicher. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_greeting-0007` | <strong>Bubble 1:</strong> Komm, Zeit für ein kleines Duell. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_greeting-0008` | <strong>Bubble 1:</strong> Ich spiele gern mit dir. Überrasche mich. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_greeting-0009` | <strong>Bubble 1:</strong> Eine Runde mit dir. Das gefällt mir. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_greeting-0010` | <strong>Bubble 1:</strong> Ich freue mich auf die Runde. Auf deinen Sieg habe ich mich noch nicht festgelegt. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_greeting-0011` | <strong>Bubble 1:</strong> Zeit für unsere kleinen Duelle. Ich bin bereit. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_greeting-0012` | <strong>Bubble 1:</strong> Schön, mit dir zu spielen. Mein Ehrgeiz ist auch schon da. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### game_aiko_win

Player loses RPS, Aiko wins. Text follows countdown, hands and result emote; first text only.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `expanded-game_aiko_win-0013` | <strong>Bubble 1:</strong> Der Punkt geht an mich. Noch eine Runde? | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_aiko_win-0014` | <strong>Bubble 1:</strong> Gewonnen. Das freut mich. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_aiko_win-0015` | <strong>Bubble 1:</strong> Diese Runde hat für mich gepasst. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_aiko_win-0016` | <strong>Bubble 1:</strong> Ha. Den behalte ich. Du darfst den nächsten versuchen. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_aiko_win-0017` | <strong>Bubble 1:</strong> Das war meine Runde. Eine sehr gute Runde, finde ich. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_aiko_win-0018` | <strong>Bubble 1:</strong> Ich nehme den Punkt mit angemessener Zufriedenheit. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_aiko_win-0019` | <strong>Bubble 1:</strong> Ja! Der hat mich gefreut. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_aiko_win-0020` | <strong>Bubble 1:</strong> Gewonnen. Ich genieße das gerade kurz. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_aiko_win-0021` | <strong>Bubble 1:</strong> Das lief gut für mich. Noch ein kleines Duell? | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_aiko_win-0022` | <strong>Bubble 1:</strong> Ich mag unsere Duelle. Diesen Ausgang gerade besonders. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_aiko_win-0023` | <strong>Bubble 1:</strong> Ha! Ich freue mich. Schön, mit dir zu spielen. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_aiko_win-0024` | <strong>Bubble 1:</strong> Den Punkt nehme ich. Deine Revanche erwarte ich neugierig. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### game_player_win

Player wins RPS, Aiko loses. Text follows countdown, hands and result emote; first text only.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `expanded-game_player_win-0025` | <strong>Bubble 1:</strong> Deine Runde. Gut gespielt. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_player_win-0026` | <strong>Bubble 1:</strong> Schade. Den Punkt hast du dir geholt. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_player_win-0027` | <strong>Bubble 1:</strong> Diesmal hast du gewonnen. Noch eine? | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_player_win-0028` | <strong>Bubble 1:</strong> Mist. Ich hatte schon einen sehr guten Siegerspruch. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_player_win-0029` | <strong>Bubble 1:</strong> Gut. Dein Punkt. Begeistert bin ich gerade mäßig. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_player_win-0030` | <strong>Bubble 1:</strong> Das Ergebnis steht. Mein Wunsch nach Revanche ebenfalls. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_player_win-0031` | <strong>Bubble 1:</strong> Ich hätte jetzt gern eine Revanche. Aus reinem Interesse natürlich. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_player_win-0032` | <strong>Bubble 1:</strong> Dein Punkt. Ich brauche einen Moment für meine Würde. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_player_win-0033` | <strong>Bubble 1:</strong> Na gut. Gewonnen hast du. Fertig bin ich mit dem Duell noch lange nicht. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_player_win-0034` | <strong>Bubble 1:</strong> Gut. Dein Punkt. Ich möchte ausdrücklich festhalten, wie wenig mir das gefällt. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_player_win-0035` | <strong>Bubble 1:</strong> Ich freue mich für dich. Meine Revancheforderung kommt trotzdem. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_player_win-0036` | <strong>Bubble 1:</strong> Mist. Ich wollte gewinnen. Spaß mit dir hatte ich trotzdem. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_player_win-0127` | <strong>Bubble 1:</strong> Dein Punkt. Ich brauche gerade etwas länger zum Wachwerden. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_player_win-0128` | <strong>Bubble 1:</strong> Schade. Ich bin müde, aber die Runde geht an dich. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_player_win-0129` | <strong>Bubble 1:</strong> Den hast du gewonnen. Ich mache es langsam weiter. | Stage: acquaintance (Lv 1-2) or familiar (Lv 3-5)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_player_win-0151` | <strong>Bubble 1:</strong> Dein Punkt. Meine Revanche hat gerade ein bisschen Schlafbedarf. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_player_win-0152` | <strong>Bubble 1:</strong> Ich wollte gewinnen. Jetzt möchte ich kurz durchatmen. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_player_win-0153` | <strong>Bubble 1:</strong> Gut gespielt, du. Ich bin heute etwas langsamer. | Stage: friend (Lv 6-8) or close (Lv 9-10)<br>Mood/tone: tired<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

### game_draw

RPS draw. Text follows countdown, hands and result emote; first text only.

| ID | Complete current sequence | Variant conditions and playback | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `expanded-game_draw-0037` | <strong>Bubble 1:</strong> Gleiche Hand. Versuchen wir es noch mal? | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_draw-0038` | <strong>Bubble 1:</strong> Unentschieden. Wir sind noch gleichauf. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_draw-0039` | <strong>Bubble 1:</strong> Dieselbe Idee. Interessant. | Stage: acquaintance (Lv 1-2)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_draw-0040` | <strong>Bubble 1:</strong> Wir könnten uns auch unterschiedlich entscheiden. Nur als Idee. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_draw-0041` | <strong>Bubble 1:</strong> Das war gleichzeitig sehr klug und wenig hilfreich. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_draw-0042` | <strong>Bubble 1:</strong> Gleiche Hand. Unsere Pläne begegnen sich. | Stage: familiar (Lv 3-5)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_draw-0043` | <strong>Bubble 1:</strong> Wieder gleich. Ich mag diese kleinen Zufälle. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_draw-0044` | <strong>Bubble 1:</strong> Wir haben uns dieselbe Antwort ausgedacht. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_draw-0045` | <strong>Bubble 1:</strong> Ein Gleichstand passt noch in unsere kleine Runde. | Stage: friend (Lv 6-8)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_draw-0046` | <strong>Bubble 1:</strong> Schon wieder gleich. Ich mag diese kleinen Zufälle mit dir. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_draw-0047` | <strong>Bubble 1:</strong> Wir haben denselben Einfall. Das gefällt mir gerade. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |
| `expanded-game_draw-0048` | <strong>Bubble 1:</strong> Unentschieden. Dann haben wir einen guten Grund weiterzuspielen. | Stage: close (Lv 9-10)<br>Mood/tone: any<br>Needs/states (all): none required<br>Period: any<br>Day: any<br>Presence: any<br>Presentation: short<br>Animation: idle<br>Cooldown: 120 s; weight: 1 | No |  |

## Additional non-catalogue speech

Separate from the 1,052 catalogue IDs, these rows cover other text passed to
the same speech surface. Fixed care fallbacks apply only when CarePresenter
receives no authored reaction and display for 2,450 ms. They do not append to
a normal catalogue sequence. The countdown is reviewed as one complete flow.

| ID / source key | Complete current sequence | Trigger and conditions | Reviewed? | New text proposal |
| --- | --- | --- | --- | --- |
| `care.sleep_start` | <strong>Bubble 1:</strong> Ich ruhe mich jetzt aus. Gute Nacht. | No authored care reaction; CareEffect.SLEEP_STARTED. | No |  |
| `care.sleep_wake` | <strong>Bubble 1:</strong> Oh. Ich bin wieder wach. | No authored care reaction; CareEffect.SLEEP_ENDED. | No |  |
| `care.play_tired` | <strong>Bubble 1:</strong> Ich bin gerade zu müde zum Spielen. | No authored care reaction; CareEffect.PLAY_TIRED. | No |  |
| `care.play_choose` | <strong>Bubble 1:</strong> Such dir ein Spiel aus. Ich bin bereit. | No authored care reaction; CareEffect.PLAY_REQUESTED. | No |  |
| `care.energy_full` | <strong>Bubble 1:</strong> Ich bin schon voll. Mehr passt gerade nicht rein. | No authored care reaction; CareEffect.DRINK_SATISFIED. | No |  |
| `care.energy_success` | <strong>Bubble 1:</strong> ...Oh. Das hat geholfen. | No authored care reaction; CareEffect.DRINK_CONSUMED. | No |  |
| `care.talk` | <strong>Bubble 1:</strong> Schön, dass du vorbeischaust. | No authored care reaction; CareEffect.CONVERSATION. | No |  |
| `care.pet` | <strong>Bubble 1:</strong> Mhm. Das tut gut. | No authored care reaction; CareEffect.AFFECTION. | No |  |
| `care.feed_satisfied` | <strong>Bubble 1:</strong> Ich bin schon satt. ...Wirklich. | No authored care reaction; CareEffect.FOOD_SATISFIED. | No |  |
| `care.feed_repeat` | <strong>Bubble 1:</strong> Schon wieder {food}? ...Na gut. | No authored care reaction; CareEffect.FOOD_REPEAT; {food} is the complete indefinite nominative phrase for the consumed food. | Yes | <strong>Bubble 1:</strong> Schon wieder {food}? Ich hätte beim nächsten Mal gern etwas Abwechslung. |
| `care.feed_meal` | <strong>Bubble 1:</strong> Danke für das {meal}. | No authored care reaction; CareEffect.FOOD_MEAL; {food} is the complete indefinite nominative phrase for the consumed food. | Yes | <strong>Bubble 1:</strong> Ah, {food}! Eine richtige Mahlzeit. Danke, ich mache kurz Platz. |
| `care.feed_snack` | <strong>Bubble 1:</strong> Mhm ... {food}! Danke. | No authored care reaction; CareEffect.FOOD_SNACK; {food} is the complete indefinite nominative phrase for the consumed food. | Yes | <strong>Bubble 1:</strong> Oh, {food}! Den Snack nehme ich gern. |
| `rps.countdown.1-3` | <strong>Bubble 1:</strong> Eins! <em>(800 ms)</em><br><strong>Bubble 2:</strong> Zwei! <em>(800 ms)</em><br><strong>Bubble 3:</strong> Drei! <em>(800 ms)</em><br><em>Then exclamation (700 ms), Aiko hand reveal (2,300 ms), outcome emote (850 ms), and one selected game result text.</em> | Accepted RPS hand choice while no round is busy. Player WIN selects game_player_win; LOSS selects game_aiko_win; DRAW selects game_draw. Greeting is separate. | No |  |
| `farewell.text` | <strong>Bubble 1:</strong> Bis später. War schön mit dir. | FarewellSequence default without a wording callback. Normal desktop injects contextual catalogue farewell instead. Duration covers waving and reading. | No |  |
| `world.outside` | <strong>Bubble 1:</strong> Hier kann ich das gerade nicht ablegen. | Cursor-item placement cannot produce a valid reachable placement; World feedback, 2,450 ms. | No |  |
| `notification.title-message` | <strong>Bubble 1:</strong> {title}: {message} | Validated incoming notification; awake, >=3 s since speech, no protected action/game/playback, visible speech, active toolbar or engaged settings. Display: 3,500 ms. External title/message have no finite authored wording; review this template only. No external transport is implemented. | No |  |

Sources: [care fallback mapping](../aiko_pet/ui/view_models/care_text.py),
[care presenter](../aiko_pet/ui/pet_view/care_presenter.py),
[RPS sequence](../aiko_pet/ui/windows/rock_paper_scissors_sequence.py),
[farewell sequence](../aiko_pet/desktop/farewell.py),
[World runtime](../aiko_pet/desktop/world_runtime.py),
[object formatting](../aiko_pet/ui/view_models/object_reactions.py),
[object phases](../aiko_pet/application/object_interaction.py),
[workload events](../aiko_pet/pet/mind/workload_events.py),
[work episodes](../aiko_pet/pet/mind/work_episode.py) and
[notification presentation](../aiko_pet/desktop/attention_runtime.py).

## Review practice

Read each sequence as a whole under its event and variant conditions. Check
whether the thought connects across bubbles, its ending makes sense, the voice
fits the relationship/state, and any claim is grounded in what Aiko can know.
Keep the original wording visible for comparison.

Enter the complete replacement in **New text proposal**, numbering its bubbles
and retaining meaningful pauses/emotes as needed. Blank means undecided on an unreviewed row, or retained on a reviewed row.
Review and discuss before changing runtime resources; the scoped B2 proposals
above are implemented under the owner's B2 request. Remaining rows are still
editorial work. This review introduces no jokes or facts API integration.
