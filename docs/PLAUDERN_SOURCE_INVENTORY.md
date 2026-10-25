# PL-1A: Plaudern source and reference inventory

Documentation-only audit, 2026-10-25, on `feature/social-optimization`.
[Delivery plan](CARE_TIME_IMPLEMENTATION_PLAN.md#plaudern-delivery-plan-owners-source-files-and-small-slices-2026-10-25).
This task changes no runtime, catalogue, tests or saves. No app imports, GUI,
mouse control, live API calls, runtime tests or CI were used.

> **Later PL-1B cutover:** the definitions now live in indexed topic sources;
> see the [source format](DATA_AND_SAVES.md#character-copy). This inventory keeps
> the original monolith's snapshot hash/line coordinates for comparison, not as
> an active source-path requirement. PL-1B verified all definitions and order.
> **Later PL-5 replacement:** all sixty old requested-chat IDs listed here are
> now removed, with 24 first grounded stories in their topic sources. All 1,093
> non-talk definitions remain unchanged. This frozen manifest still documents
> the original audit; see the [PL-5 delivery](CARE_TIME_IMPLEMENTATION_PLAN.md#pl-5-delivery-evidence-based-requested-plaudern)
> for current membership and validation. Spontaneous filler replacement remains
> PL-6C.

## Snapshot and decisions

The runtime baseline at capture was `c2c31493cfa7f1255bffff78854a34f9795968c7`:
**1,118 sequences / 142 events**, catalogue schema 3. The approved planning
documentation was subsequently secured separately as `7a58367`.

The frozen working-copy snapshot contains **1,153 sequences / 148 events**:
**48 stories and 1,105 short reactions**. All baseline IDs and full definitions
are unchanged; the only catalogue delta is **35 parallel Quiz additions** across
six events. At capture these were separate, uncommitted runtime work, not a
PL-1A delivery. During the audit the parallel owner committed Quiz as `e473338`,
between the documentation commits `7a58367` and `dd70f41`. That existing shared-
branch commit was included in the push; PL-1A's own commits contain docs only.
The final live catalogue still matches the frozen hash exactly.
Earlier exploratory reads saw 1,168 sequences while Quiz copy was being revised.
All tables and per-ID decisions here consistently use the frozen 1,153 snapshot.
Reconcile later parallel changes before PL-1B; never reset the live catalogue
to match this audit.

- Frozen source SHA-256: `510c7784a31705e9cebee03fe23fc8b9678dd91ed433ec09ad3060f08e421641`.
- Baseline source SHA-256: `62e57a80f1ce95409666967d6a8d224c1d99234a11fcd4136dae2be7f38668b2`.

[PL1A_DIALOGUE_IDS.tsv](inventories/PL1A_DIALOGUE_IDS.tsv) identifies every sequence
by stable ID, event, presentation, disposition, planned file, reason, origin,
frozen-source line and full-definition SHA-256. It is a derived audit manifest,
not a second editable dialogue source. Hashes use each complete JSON entry with
sorted object keys, UTF-8, `ensure_ascii=False` and compact comma/colon separators;
array order, conditions and ordered text/emote beats are preserved.

| Disposition | Count | Required later action |
| --- | ---: | --- |
| `PROTECT_EVENT` | 992 | Preserve functional event dialogue and actual callers. |
| `KEEP_GROUNDED` | 43 | Preserve the real need/state/observation guard; no unconditional filler. |
| `KEEP_REHOME_GROUNDED` | 8 | Preserve fatigue-conditioned morning/night entries while replacing their random calendar route. |
| `REMOVE_GENERIC` | 50 | Remove idle/calendar filler in PL-6C. |
| `REPLACE_LEGACY_TALK` | 60 | Replace/review the old requested-chat route in PL-5/PL-6; not all sixty are ungrounded. |

There are **1,043 protected/grounded entries**, including **214 sequences across
all 32 object events**. These are dated audit counts, not final size targets.
PL-1B first moves the catalogue without intentional behavior/text changes;
removal/replacement belongs to the later explicitly planned slices.

## Protected flows and evidence

| Flow | Actual basis and preservation boundary |
| --- | --- |
| Object discovery, approach, pickup, inspection, recognition, known/unknown decisions | `pet/mind/object_events.py` defines the shared ObjectEvent contract. Application interaction phases and feedback drive the real events. Preserve full sequences, knowledge limits and object grammar. |
| Search, missing familiar place, found/missing results and remembered stock | Existing Mind perception/knowledge/memory/absence and actual search phases provide the basis. Preserve successful and unsuccessful searches; a complaint or generic pronoun is not grounds for deletion. |
| Offer/handover/refusal, withholding/escalation/return, intake and busy/search interruption | Preserve all `object_*`, especially `object_taken`, `object_request_return`, `object_withheld`, `object_returned`, `object_busy` and `object_busy_search`. Keep existing custody rules; cursor pickup alone is not a completed relocation. |
| Direct clicks, repeated-click boundaries and sleep clicks | `PetMind.click()` and `click_policy.py` use real contact. Preserve work, sleep, low-affection, withdrawal and escalation variants. Simple wording still has a basis when an actual click triggers it. |
| Feeding, petting, energy drink, sleep/wake and care requests/refusals | Existing care/contact selection uses actions and pre-care state. Preserve staged petting boundaries, food-variety requests and functional care feedback. |
| Games including parallel Quiz | Preserve actual greetings, progress, result and moderation events. Quiz completion is not a competitive Aiko win; preserve its current shared contract. |
| Return, greeting/farewell, availability and cursor remarks | Actual return/contact, measured cursor displacement or current work availability. `talk_busy` is functional availability feedback, not ordinary generic `talk`. |
| Work/load/uptime | `workload_events.py`, `work_episode.py` and `PetMind.select_computer_reaction()` represent observed transitions. Keep them and their current guards. |
| Completed walk | `application/attention.py:walk_reaction()` selects `walk_pause` after a real completed-walk opportunity. Preserve its six entries; probability schedules an observed-event comment. |
| Quiet alone/together | `_select_spontaneous_event()` checks resting mode and presence. Preserve all six and their observed-situation guard. |
| Need/emotional comments | Hunger, fatigue, low social/affection and emotional state are actual guards. Preserve the 31 entries; replace reminder-throttle fallback to `idle`, not the need comments themselves. |

`select_computer_reaction()` maps `computer_uptime` to
`computer_uptime_grounded`. The six older uptime entries are not evidence of a
reachable random-idle fallback. Protect them from this removal scope; separate
dead-copy cleanup requires checking their direct tests/catalogue consumers.

## Old requested-chat pool: sixty explicit replacements/reviews

There are 12 short and 48 four-text `talk` sequences. The TSV gives every exact ID.
Their conditions and full text sequences were reviewed, rather than treating the
event name as proof that all text is ungrounded. Valid current-state motifs may
survive with truthful topic conditions; no count requires rewriting a good line.

| Manifest reason | Count | Review result |
| --- | ---: | --- |
| `TALK_SHORT` | 12 | Relationship-only general statements, hypothetical future games or unspecified activity. Replace the old short fallback; it proves no active wish or actual success. |
| `TALK_CALM` | 8 | General desktop/taskbar/life stories. Mood filters do not prove particular food care, cursor behavior or shared events. Retire this generic topic pool. |
| `TALK_PLAYFUL` | 8 | Imagined spectators/buttons, traffic-police/spacecraft play and future-game rules. Playfulness does not prove an active game wish or past match. Replace with concrete occasions. |
| `TALK_TIRED` | 8 | Fatigue is real, but several stories invent counted steps, an abandoned thought or a planned game. Preserve useful present-fatigue wording only in a truthful state topic. |
| `TALK_WITHDRAWN` | 8 | Subdued/irritated feeling is real; it does not identify poking as its cause. Separate truthful state expression from a retrospective complaint requiring cause evidence. |
| `TALK_HUNGRY` | 4 | Low satiety is real; interrupted thinking or future-game plans are not recorded by that condition. Rework against actual state/wish/experience. |
| `TALK_LONELY` | 4 | Loneliness/low social is real; a specific find or game preference is not proved. Preserve the truthful meaning without invented history. |
| `TALK_SEEKING_AFFECTION` | 4 | Low affection is real, but is not a new wish or permission to bypass actual acceptance. Preserve boundaries and disclosure. |
| `TALK_WARM` | 4 | Affectionate feeling or a short warm tone does not establish what happened "just now". Retained causes must support "Das eben" claims. |

## Selection, public contracts and later cleanup

| Reference | Later action / protected meaning |
| --- | --- |
| `PetMind._choose_idle_topic()` | Remove the generic idle/calendar pool after preserving the eight fatigue exceptions. |
| `_select_spontaneous_event()` | Keep genuine need/work/rest/emotion selection. Its two reminder-throttle `return "idle"` paths and final idle picker must stop forcing filler. |
| `select_spontaneous_reaction()` / `_last_spontaneous_story` | Remove unsolicited promotion into a `talk` story and its unused throttle state. Preserve sleeping checks and real disclosure/event paths; add no conversation archive. |
| `data/balance.json` / `pet/balance_contract.py` | Later remove only `spontaneous_story_quiet_seconds` and `spontaneous_story_probability` with strict validation/tests/docs. Keep ordinary attention scheduling and text-variant cooldowns. |
| `pet/mind/dialogue_events.py` | Retire only unconsumed dialogue keys. **Keep `talk`**, which is an action/reaction event used by API content, horoscope and future legitimate Plaudern. |
| `catalog.py:Reaction`, `reaction_sequence.py`, reaction player | `talk` also controls timing of prepared API/horoscope sequences. Preserve timing, completion, cancellation and actual care/wish/relief outcomes. |
| `application/attention.py` | Keep spontaneous-talk settings, cursor/walk/sleep observations and silent idle animation/emotes. Animation `idle` is not generic spoken `idle`. |
| `routine.py`, `routine_catalog.py`, `status_hints.py` | Night/evening/weekend are also real sleep/routine/status facts. No global matching-string deletion. |

## Loader, tests, tools, deployment and external limits

- `pet/mind/catalog.py:CATALOGUE` owns the current path and strict schema.
  `infrastructure/character_mind.py` assembles one book/RNG.
- `ui/windows/rock_paper_scissors_dialogue.py:GameDialogue` is a supported
  standalone loader caller. Keep `DialogueBook.from_file()` usable after the move.
- Tests read `CATALOGUE`, `data/dialogues.de.json` and sometimes
  `CATALOGUE.parent / "balance.json"`. Moving only the constant breaks fixtures;
  resolve balance independently of the nested source index.
- Boundary tests assert the old exact path; catalogue checks assert minimum
  size. Replace those stale expectations with actual indexed resources and
  protected-flow coverage, not filler retained to satisfy a count.
- Keep strict invalid schema/conditions/placeholders, ordered beats, object
  grammar/knowledge/search/handover, click/petting escalation, actual need/state,
  game sequence and real completion/cancellation coverage. Replace assertions
  requiring unsolicited `talk` promotion with the new separation/silence rule.
- Historical `DIALOGUE_REVIEW.md` is a snapshot with editorial decisions; do not
  regenerate over reviewed cells or use its counts as a live deletion list.
- `tools/install_windows.ps1` operates on the complete source folder and checks
  `requirements.txt`, `Aiko_Pet.pyw`, `aiko_pet/__main__.py`; setup also imports
  app/assets. No frozen-resource build specification was found in the repository
  file inventory. PL-1B must verify all indexed JSON ships with the source and
  assembly can load it. This audit did not run installer/application imports.
- Searches covered production, tests, tools, scripts, docs, workflows and root
  text/config/launcher files. External installed/copied consumers were not
  enumerated. Preserve the public loader facade; no claim of zero external users.

The reference index below gives every hit of the narrow catalogue-loader and
spontaneous-story search, separated from the reviewed real routes above. A
literal match alone does not establish reachability. Line numbers describe the
audit checkout; parallel edits may move them. Historical docs are evidence, not
automatic edit targets.

## Generic removal: every exact sequence

| Stable ID | Event | Complete current text |
| --- | --- | --- |
| `idle-01` | `idle` | Mein Weg hier ist überschaubar. Trotzdem schaue ich gern, ob sich etwas verändert hat. |
| `idle-02` | `idle` | An dieser Stelle kann ich stehen, ohne dir mitten im Fenster herumzuhüpfen. |
| `idle-03` | `idle` | Ich drehe noch eine kleine Runde auf meinem Stück Taskleiste. |
| `v011-close_thought-01` | `idle` | Hier unten habe ich meinen Platz. Wenn du etwas hinlegst, sehe ich es mir an. |
| `v011-close_thought-03` | `idle` | Mein Weg ist klein, aber beim Herumlaufen fällt mir immer wieder etwas auf. |
| `v011-close_thought-04` | `idle` | Ich strecke die Beine aus. Dafür muss ich zum Glück nicht erst ein Fenster öffnen. |
| `situation-morning-037` | `morning` | Guten Morgen. Ich komme langsam in den Tag. |
| `situation-morning-038` | `morning` | Morgen! Ich mache mich hier erst mal richtig wach. |
| `situation-morning-039` | `morning` | Ein neuer Morgen. Mal sehen, was heute auf mich wartet. |
| `situation-morning-040` | `morning` | Guten Morgen, du! Was machen wir heute zusammen? |
| `situation-morning-041` | `morning` | Hach, ein neuer Tag bei dir. Ich freue mich auf uns. |
| `situation-morning-042` | `morning` | Morgen! Ich bin da und möchte mit dir loslegen. |
| `situation-midday-043` | `midday` | Es ist Mittag. Zeit für eine Unterbrechung wäre das schon. |
| `situation-midday-044` | `midday` | Der Mittag ist da. Ich strecke mich erst mal. |
| `situation-midday-045` | `midday` | Mittags schaue ich gern, ob Zeit für eine kleine Pause ist. |
| `situation-midday-046` | `midday` | Mittag! Wie wäre es mit einer kleinen Pause bei mir? |
| `situation-midday-047` | `midday` | Du, der halbe Tag ist schon um. Ein bisschen gemeinsame Zeit wäre schön. |
| `situation-midday-048` | `midday` | Hach, Mittagszeit. Ich hätte jetzt Lust auf eine Pause mit dir. |
| `situation-evening-049` | `evening` | Es wird Abend. Mein Tag hier hat noch etwas Platz für einen Spaziergang. |
| `situation-evening-050` | `evening` | Der Abend ist da. Ich lasse es langsam angehen. |
| `situation-evening-051` | `evening` | Ich bleibe noch etwas hier und schaue mich um. |
| `situation-evening-052` | `evening` | Hach, Abend. Hast du noch ein bisschen Zeit für uns? |
| `situation-evening-053` | `evening` | Zum Abend hätte ich gern noch etwas Gesellschaft von dir. |
| `situation-evening-054` | `evening` | Es ist Abend geworden. Eine kleine gemeinsame Runde würde mir gefallen. |
| `situation-night-055` | `night` | Es ist Nacht. Ich mache es mir hier etwas bequemer. |
| `situation-night-056` | `night` | So spät noch hier. Ich lasse mir mit allem etwas mehr Zeit. |
| `situation-night-057` | `night` | Schon Nacht. Hier unten habe ich auch um diese Uhrzeit meinen Platz. |
| `situation-night-058` | `night` | Du bist noch wach? Dann leisten wir uns ein bisschen Gesellschaft. |
| `situation-night-059` | `night` | Hach, schon Nacht. Ich mache es mir hier bei dir gemütlich. |
| `situation-night-060` | `night` | Unser Tag reicht bis in die Nacht. Zeit für mich hast du vielleicht auch noch? |
| `situation-monday-061` | `monday` | Montag. Eine neue Woche an meinem kleinen Platz. |
| `situation-monday-062` | `monday` | Die Woche fängt wieder an. Ich bin hier mit dabei. |
| `situation-monday-063` | `monday` | Ein neuer Montag. Ich schaue mal, was der Tag bringt. |
| `situation-monday-064` | `monday` | Neue Woche, du und ich wieder hier. Auf geht's! |
| `situation-monday-065` | `monday` | Montag! Mal sehen, was wir diese Woche zusammen schaffen. |
| `situation-monday-066` | `monday` | Na, bereit für die Woche? Ich bin schon auf meinem Platz. |
| `situation-friday-067` | `friday` | Es ist Freitag. Die Woche ist bald geschafft. |
| `situation-friday-068` | `friday` | Freitag. Mal sehen, was wir heute noch vorhaben. |
| `situation-friday-069` | `friday` | Die Arbeitswoche geht ihrem Ende entgegen. Ich bleibe noch etwas hier. |
| `situation-friday-070` | `friday` | Freitag! Vielleicht bleibt heute Zeit für eine kleine Runde mit mir. |
| `situation-friday-071` | `friday` | Hach, die Woche ist fast geschafft. Ich freue mich auf etwas gemeinsame Zeit. |
| `situation-friday-072` | `friday` | Freitag, du! Für ein schönes Ende der Woche wäre ich zu haben. |
| `situation-weekend-073` | `weekend` | Wochenende. Ich schaue mal, was wir heute zusammen machen. |
| `situation-weekend-074` | `weekend` | Samstag oder Sonntag, mein Platz hier wartet trotzdem auf mich. |
| `situation-weekend-075` | `weekend` | Das Wochenende ist da. Ich nehme mir Zeit für eine kleine Runde. |
| `situation-weekend-076` | `weekend` | Wochenende! Hast du heute ein bisschen mehr Zeit für mich? |
| `situation-weekend-077` | `weekend` | Hach, Wochenende mit dir. Vielleicht bekommen wir eine Spielrunde unter. |
| `situation-weekend-078` | `weekend` | Ich wäre am Wochenende gern mit dir beschäftigt. Suchst du uns etwas aus? |
| `morning-02` | `morning` | Guten Morgen. Ein neuer Tag an meinem Platz beginnt. |
| `night-01` | `night` | Inzwischen ist Nacht. Ich lasse meinen Tag langsam ausklingen. |

## Fatigue exceptions: every exact sequence

These have explicit `fatigued` predicates as well as period filters. Retain
IDs/text/guards in PL-1B; later preserve/rehome them when retiring the picker.

| Stable ID | Current event |
| --- | --- |
| `situation-morning-079` | `morning` |
| `situation-morning-080` | `morning` |
| `situation-morning-082` | `morning` |
| `situation-morning-083` | `morning` |
| `situation-night-085` | `night` |
| `situation-night-086` | `night` |
| `situation-night-088` | `night` |
| `situation-night-089` | `night` |

## Event coverage and protected IDs

Every ID is listed in the TSV; counts below group that exact manifest.

| Event | Count | Disposition | Planned source |
| --- | ---: | --- | --- |
| `affection_low` | 6 | `KEEP_GROUNDED` | `spontaneous/needs.json` |
| `after_work_thought` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `care_request_feed` | 12 | `PROTECT_EVENT` | `events/care.json` |
| `care_request_pet` | 12 | `PROTECT_EVENT` | `events/care.json` |
| `care_request_play` | 12 | `PROTECT_EVENT` | `events/care.json` |
| `care_request_talk` | 12 | `PROTECT_EVENT` | `events/care.json` |
| `click_affection_low` | 12 | `PROTECT_EVENT` | `events/contact.json` |
| `click_after_work` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `click_at_ease` | 12 | `PROTECT_EVENT` | `events/contact.json` |
| `click_boundary` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `click_during_work` | 10 | `PROTECT_EVENT` | `events/contact.json` |
| `click_flustered` | 12 | `PROTECT_EVENT` | `events/contact.json` |
| `click_last_word` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `click_left` | 18 | `PROTECT_EVENT` | `events/contact.json` |
| `click_lonely` | 12 | `PROTECT_EVENT` | `events/contact.json` |
| `click_night` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `click_notice` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `click_notice_playful` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `click_notice_withdrawn` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `click_right` | 13 | `PROTECT_EVENT` | `events/contact.json` |
| `click_sleepy` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `click_tease` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `click_tease_more` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `click_wake` | 12 | `PROTECT_EVENT` | `events/contact.json` |
| `click_weary` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `click_withdrawn` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `click_withdrawn_boundary` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `click_work_boundary` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `click_work_repeat` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `computer_effort_easing` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `computer_effort_heavy` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `computer_effort_peak` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `computer_effort_recovered` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `computer_effort_recovered_peak` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `computer_effort_rest` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `computer_effort_rising` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `computer_effort_steady` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `computer_uptime` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `computer_uptime_grounded` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `cursor_far` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `cursor_follow` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `energy_drink` | 10 | `PROTECT_EVENT` | `events/care.json` |
| `energy_drink_full` | 6 | `PROTECT_EVENT` | `events/care.json` |
| `evening` | 6 | `REMOVE_GENERIC` | `none` |
| `farewell` | 12 | `PROTECT_EVENT` | `events/contact.json` |
| `feed_full` | 12 | `PROTECT_EVENT` | `events/care.json` |
| `feed_meal` | 24 | `PROTECT_EVENT` | `events/care.json` |
| `feed_repeat` | 12 | `PROTECT_EVENT` | `events/care.json` |
| `feed_snack` | 16 | `PROTECT_EVENT` | `events/care.json` |
| `feed_variety_reminder` | 1 | `PROTECT_EVENT` | `events/care.json` |
| `feed_variety_request` | 1 | `PROTECT_EVENT` | `events/care.json` |
| `friday` | 6 | `REMOVE_GENERIC` | `none` |
| `game_aiko_win` | 12 | `PROTECT_EVENT` | `events/games.json` |
| `game_blackjack_greeting` | 3 | `PROTECT_EVENT` | `events/games.json` |
| `game_c4_aiko_win` | 3 | `PROTECT_EVENT` | `events/games.json` |
| `game_c4_block` | 3 | `PROTECT_EVENT` | `events/games.json` |
| `game_c4_blocked` | 3 | `PROTECT_EVENT` | `events/games.json` |
| `game_c4_draw` | 3 | `PROTECT_EVENT` | `events/games.json` |
| `game_c4_greeting` | 3 | `PROTECT_EVENT` | `events/games.json` |
| `game_c4_player_win` | 3 | `PROTECT_EVENT` | `events/games.json` |
| `game_draw` | 12 | `PROTECT_EVENT` | `events/games.json` |
| `game_greeting` | 12 | `PROTECT_EVENT` | `events/games.json` |
| `game_mm_aiko_win` | 3 | `PROTECT_EVENT` | `events/games.json` |
| `game_mm_greeting` | 3 | `PROTECT_EVENT` | `events/games.json` |
| `game_mm_last` | 3 | `PROTECT_EVENT` | `events/games.json` |
| `game_mm_player_win` | 3 | `PROTECT_EVENT` | `events/games.json` |
| `game_mm_progress` | 3 | `PROTECT_EVENT` | `events/games.json` |
| `game_player_win` | 16 | `PROTECT_EVENT` | `events/games.json` |
| `game_quiz_correct` | 7 | `PROTECT_EVENT` | `events/games.json` |
| `game_quiz_encourage` | 6 | `PROTECT_EVENT` | `events/games.json` |
| `game_quiz_finish` | 5 | `PROTECT_EVENT` | `events/games.json` |
| `game_quiz_greeting` | 5 | `PROTECT_EVENT` | `events/games.json` |
| `game_quiz_incorrect` | 7 | `PROTECT_EVENT` | `events/games.json` |
| `game_quiz_rolebreak` | 5 | `PROTECT_EVENT` | `events/games.json` |
| `game_round_aiko_win` | 3 | `PROTECT_EVENT` | `events/games.json` |
| `game_round_draw` | 3 | `PROTECT_EVENT` | `events/games.json` |
| `game_round_player_win` | 3 | `PROTECT_EVENT` | `events/games.json` |
| `game_ttt_greeting` | 3 | `PROTECT_EVENT` | `events/games.json` |
| `greeting` | 16 | `PROTECT_EVENT` | `events/contact.json` |
| `hungry` | 7 | `KEEP_GROUNDED` | `spontaneous/needs.json` |
| `idle` | 6 | `REMOVE_GENERIC` | `none` |
| `low_mood` | 6 | `KEEP_GROUNDED` | `spontaneous/state.json` |
| `midday` | 6 | `REMOVE_GENERIC` | `none` |
| `monday` | 6 | `REMOVE_GENERIC` | `none` |
| `morning` | 4 | `KEEP_REHOME_GROUNDED` | `spontaneous/needs.json` |
| `morning` | 7 | `REMOVE_GENERIC` | `none` |
| `night` | 4 | `KEEP_REHOME_GROUNDED` | `spontaneous/needs.json` |
| `night` | 7 | `REMOVE_GENERIC` | `none` |
| `object_approach` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_busy` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_busy_search` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_collect_wanted` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_consider_known` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_consuming_drink` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_consuming_food` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_finished_drink` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_finished_food` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_found` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_handover` | 12 | `PROTECT_EVENT` | `events/objects.json` |
| `object_inspect` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_later` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_missing` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_notice` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_offer` | 16 | `PROTECT_EVENT` | `events/objects.json` |
| `object_pick_up` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_place_missing` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_put_down` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_recall_drink` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_recall_food` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_recall_saved_drink` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_recall_saved_food` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_recognized` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_refuse` | 12 | `PROTECT_EVENT` | `events/objects.json` |
| `object_request_return` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_returned` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_search` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_taken` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_unknown` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_want` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `object_withheld` | 6 | `PROTECT_EVENT` | `events/objects.json` |
| `pet` | 28 | `PROTECT_EVENT` | `events/care.json` |
| `pet_boundary_ignored` | 1 | `PROTECT_EVENT` | `events/care.json` |
| `pet_during_work` | 20 | `PROTECT_EVENT` | `events/care.json` |
| `pet_enough` | 1 | `PROTECT_EVENT` | `events/care.json` |
| `pet_enough_firm` | 1 | `PROTECT_EVENT` | `events/care.json` |
| `pet_needs_affection` | 12 | `PROTECT_EVENT` | `events/care.json` |
| `pet_refused` | 1 | `PROTECT_EVENT` | `events/care.json` |
| `play` | 16 | `PROTECT_EVENT` | `events/care.json` |
| `play_tired` | 12 | `PROTECT_EVENT` | `events/care.json` |
| `quiet_alone` | 3 | `KEEP_GROUNDED` | `spontaneous/state.json` |
| `quiet_together` | 3 | `KEEP_GROUNDED` | `spontaneous/state.json` |
| `rapid_click` | 6 | `PROTECT_EVENT` | `events/contact.json` |
| `return` | 18 | `PROTECT_EVENT` | `events/contact.json` |
| `return_after_work` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `return_working` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `sleep` | 12 | `PROTECT_EVENT` | `events/care.json` |
| `sleep_click` | 12 | `PROTECT_EVENT` | `events/contact.json` |
| `social_low` | 6 | `KEEP_GROUNDED` | `spontaneous/needs.json` |
| `talk` | 60 | `REPLACE_LEGACY_TALK` | `plaudern/<actual-topic>.json` |
| `talk_busy` | 12 | `PROTECT_EVENT` | `events/contact.json` |
| `tired` | 6 | `KEEP_GROUNDED` | `spontaneous/needs.json` |
| `wake` | 16 | `PROTECT_EVENT` | `events/care.json` |
| `walk_pause` | 6 | `KEEP_GROUNDED` | `spontaneous/state.json` |
| `weekend` | 6 | `REMOVE_GENERIC` | `none` |
| `work_concentrating` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `work_finished_interrupted` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `work_finished_long` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `work_late` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `work_long_thought` | 6 | `PROTECT_EVENT` | `events/work.json` |
| `work_unexpected` | 6 | `PROTECT_EVENT` | `events/work.json` |

## Complete narrow reference index

| File | Matching lines |
| --- | --- |
| `aiko_pet/application/attention.py` | 283 |
| `aiko_pet/infrastructure/character_mind.py` | 17 |
| `aiko_pet/pet/balance_contract.py` | 422, 423 |
| `aiko_pet/pet/mind/catalog.py` | 34 |
| `aiko_pet/pet/mind/mind.py` | 88, 417, 436, 498, 500, 509, 515, 518, 523, 533 |
| `aiko_pet/ui/windows/rock_paper_scissors_dialogue.py` | 19 |
| `docs/ARCHITECTURE.md` | 122, 140, 635, 726, 768, 769 |
| `docs/CARE_TIME_IMPLEMENTATION_PLAN.md` | 1173, 10602, 10603, 10687 |
| `docs/DATA_AND_SAVES.md` | 18, 114 |
| `docs/DIALOGUE_REVIEW.md` | 6, 29 |
| `docs/DIALOGUE_REVISION_PLAN.md` | 101 |
| `docs/MINIGAME_IMPLEMENTATION_PLAN.md` | 158 |
| `docs/history/OBJECT_FOCUS_CORRECTION_PLAN.md` | 46 |
| `docs/history/OBJECT_PLACEMENT_AND_SEARCH_PLAN.md` | 218 |
| `docs/history/OBJECT_RECOGNITION_DIALOGUE_FIX_PLAN.md` | 46 |
| `tests/test_affection.py` | 343, 349, 355, 363 |
| `tests/test_attention_policy.py` | 59 |
| `tests/test_canonical_import_paths.py` | 69 |
| `tests/test_content_catalog.py` | 101 |
| `tests/test_conversation_timing_tk.py` | 55 |
| `tests/test_dialogue.py` | 44, 162, 367, 371, 377, 385, 393 |
| `tests/test_dialogue_context.py` | 203, 204, 208, 211, 212, 213, 219, 223, 224, 228 |
| `tests/test_dialogue_modules.py` | 30 |
| `tests/test_emote_sequences.py` | 28 |
| `tests/test_german_object_phrases.py` | 111, 128 |
| `tests/test_gui.py` | 513, 523, 524 |
| `tests/test_needs_and_bond.py` | 247, 253, 259, 335 |
| `tests/test_object_feedback_flow.py` | 129 |
| `tests/test_object_reactions.py` | 22, 36, 75 |
| `tests/test_object_withholding.py` | 20, 83 |
| `tests/test_pet_mind_boundary.py` | 20 |
| `tests/test_pet_mind_catalogue.py` | 17, 20 |
| `tests/test_resource_validation.py` | 35, 56, 129, 145, 149 |
| `tests/test_rock_paper_scissors_gui.py` | 193 |
| `tests/test_rock_paper_scissors_sequence.py` | 99 |
| `tests/test_social_scenarios.py` | 258, 264, 270, 308, 328, 334, 373, 403, 424 |
| `tests/test_spontaneous_events.py` | 38, 46, 54, 57, 66, 72, 81, 90, 96, 104 |
| `tests/test_system_activity.py` | 402 |

## PL-1B handoff and verification scope

Reconcile current source against the frozen per-ID manifest before moving it;
later Quiz IDs/revisions must not disappear. PL-1B changes only source organization
and consumers. Preserve complete retained definitions; defer removal/replacement
to PL-5/PL-6C. Keep object/public-loader/talk-action/animation contracts and
actual state guards. Recheck references before later cleanup.

PL-1A validation is static JSON/AST and documentation consistency only: unique
IDs, exhaustive classifications/hashes, baseline/parallel comparison, links and
diff checks. No runtime suite is necessary or claimed. Stage documentation and
the derived manifest only; preserve parallel runtime, Quiz and asset changes.
