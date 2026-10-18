# World offers, placement and search — practical retest

## Shared search acceptance — 18 October 2026

Use an isolated save at 1x and 2x. The
[current focus plan](SHARED_INTERACTION_FOCUS_PLAN.md) defines the
visibility conditions below. Older independent per-object patrols and general
ambient sensing during committed approach or other interactions are superseded.
Controlled native tests pass; the following human visual/input checks remain open.

- [ ] In free idle, move the cursor so Aiko looks to either side. Nearby items
  may be noticed; farther items require the actual forward field. An unknown
  sighting must not identify without hand inspection or deliberate face hold.
- [ ] Learn two nearby same-type portions and a drink; restart the same isolated
  save. Unchanged places are recognized without repeated pickup/identification.
- [ ] Learn four portions, including two nearby of the same type. As soon as Aiko
  walks toward a new item, move all four through real cursor gestures; repeat
  during hand inspection. Include positions before and behind her, near and far.
  No unrelated loss/new-item/observed-transport claim may occur during item focus.
  The diagnostics must retain the previous subjective places/assignments. After the
  full action, look toward the old places: only currently visible places supply
  fresh evidence. Put a new item on the other side; its earlier notice must not
  turn the look away before the place check completes. She announces confirmed
  loss, searches once, takes and identifies unknown finds, puts them down, and
  retains the same task for the other losses, even when hungry or thirsty.
  An unrelated known portion is never substituted.
- [ ] Repeat unseen relocation and a new drop during petting, conversation and a
  game. Ambient discoveries, loss claims and transport updates must wait until
  the complete action, including all dialogue bubbles, ends. Then visible old
  places get fresh evidence; confirmed loss precedes ordinary new investigation.
  A shorter animation ending must not truncate the conversation's focus.
  Closing the game must also release its playback deadline and restore free
  perception; an invisible leftover animation must not keep attention locked.
- [ ] Every confirmed missing portion gets its own named, readable bubble,
  including another loss discovered during patrol. No bubble overwrites the
  preceding one; the same search continues without restarting its route.
  The user has confirmed eating plus three unseen relocations and successful
  reunion of all three; this per-portion feedback correction still needs a retest.
- [ ] Present a missing portion steadily at her actual eyes during search and
  also after taking its approach target. She acknowledges the reunion without
  forced pickup or a desire/consumption bubble. Other losses retain priority.
- [ ] Leave a genuinely new portion among the finds and remove another entirely.
  Investigating the new portion does not erase the remaining loss. Only after
  the full pass and candidate checks does failed search finish without a loop.
- [ ] Leave an unknown occupant on one remembered place. That place stays
  uncertain; another visibly empty remembered place must still trigger search,
  and examining the occupant must remain possible. A vanished unknown target
  is forgotten without a patrol.
- [ ] Repeat take/move/drop while Aiko is actually looking at and following the
  cursor: no phantom loss or reidentification. Repeat during another hand focus:
  the old learned place remains remembered until a later valid empty-place look.
  Check readable notice, approach, pickup, result and put-down wording; neither
  repeated identification nor invented player actions should be spoken.

The remaining sections preserve historical evidence and checklists; current
behavior is defined by the linked plan and World contracts.

The first practical test found missing investigation/feedback, truncated drink
playback and Magenta item fringes. Corrections are implemented on
`feature/world-foundation`. On 15 October 2026 the user reported that the revised
basic flow at `ea4361f` now looks correct; longer-term behavior remains to be
observed. Unreported boundary/restart cases below remain open.
[Draft PR #10](https://github.com/Lexoniarus/aiko-desktop-pet/pull/10) remains
unmerged. See [delivery/evidence](WORLD_OBJECT_IMPLEMENTATION_PLAN.md) and
[behavior contracts](WORLD_OBJECT_CONTRACTS.md).

On 16 October, the user confirmed successful edge pickup in the updated build.
They also reported slow approach/possible repeated loops. Keep that observation
open for separate behavior analysis; it is not claimed solved by the edge-grip
correction. The complete left/right 1x/2x native checklist remains to be checked.

## Combined multi-object regression — 17 October 2026

This checklist follows the later pickup/search priority decision. Start with a
fresh isolated save. Repeat with multiple apples, cookies and drinks at 1x/2x;
the user's normal save is not part of this experiment.

- [ ] Offer a completely unidentified item directly in Aiko's hand area and
  release it without the one-second face presentation. After normal noticing,
  she accepts it, identifies it only while inspecting it in her hands, decides,
  and either consumes it or animates the put-down. No pre-identification is
  required to hold it. Deliberately identified and refused offers still fall.
- [ ] Have Aiko learn an apple at place X, then remove it while she is distracted
  and leave X empty. When X enters the very same noticing range used for new
  objects, local empty evidence triggers one missing reaction and one bounded
  search. This happens even when satiety is full; the search does not loop.
- [ ] Put an unrelated unknown portion nearby during that absence detection.
  The disappearance must be announced and search started before investigating
  the new object. If the discovered type is the uniquely missing apple, recover
  the old knowledge without double-counting; if it is a cookie, no apple
  knowledge may be transferred to the cookie.
- [ ] Repeat the apple reunion with the new type identification *before* and
  *after* the local absence confirmation. Both event orders must reconcile one
  remembered portion. If two indistinguishable missing apples compete, do not
  pretend certainty about which one returned.
- [ ] Replace a known apple at X with a different apple or a cookie while
  distracted. A different portion at X is unknown, including another apple;
  only the exact unchanged learned portion can be recalled there. A replacement
  must be examined in hand or deliberately presented before its type is
  used; it must never be eaten under stale apple identity.
- [ ] Observe a pickup and relocation through cursor movement, release and
  landing; retain continuous tracked knowledge. Repeat out of sight: Aiko
  knows only the old place until genuine new evidence. Verify the focused
  approach, missing-place feedback, active search and normal idle recovery,
  including both display edges and repeated moves.

The historical checklists below document earlier rules. Their descriptions
of compulsory face-presentation before all acceptance and optional search for
unwanted missing reserves are superseded by this section.

## Three-level perception retest — 17 October 2026

The [perception correction plan](OBJECT_PERCEPTION_CORRECTION_PLAN.md) supersedes
earlier "hold near Aiko" expectations below: **deliberately hold the displayed
item before her face for one active second**. Mere presence, identity and current
willingness are separate facts. These checks still need practical acceptance.

Start a **fresh isolated save** with the existing launcher; old saves cannot tell
whether previously learned identity came from the old premature ground sensing.
Do not reset the normal save. Run the main checks at both 1x and 2x:

```powershell
.\Aiko_World_Test.bat --scenario curious
```

- [ ] Drop a fresh unknown food/drink several character widths away. Aiko notices
  an item and investigates it without naming its type on the ground or in flight.
  Only after pickup reaches the safe holding pose does she inspect, identify and
  assess it. Food at 76 satiety/drink at 60 energy may be deferred under ordinary
  supply rules. A hungry profile must instead show complete consumption.
- [ ] Hold a fresh portion far away, pass briefly before her face, then make
  several brief passes. No identification/offer decision from these passes.
  Hold steadily before her face for about one second, allowing small jitter:
  she can identify and state current willingness. Keep holding: no consumption.
  Test both a wanted portion and `--scenario full` refusal.
- [ ] Move a completed presentation down into her hand and release: accept only
  if still wanted, followed by full slow consumption. A dropped known offer is
  followed through fall/hops and collected without another first identification;
  autonomous consumption grants no human care reward.
- [ ] Pick up a known lying portion while she is free and watching, then carry it
  far away. Identity remains known, but a **new gesture** needs its own face
  presentation before another offer decision. Ordinary holding causes no theft
  protest, irritation or friendship loss.
- [ ] Take the exact unknown target during her approach. She requests its return
  without naming it. Present it before her face for a second: identification,
  then an explicit wanted/refused decision. Refusal ends return demands and
  withholding effects; agreement permits release or continued observed placement.
- [ ] Let her learn and defer a portion, then open a game so attention is occupied.
  Move that portion elsewhere while she is distracted. Close the game with its
  former place visible. After a short local look she notices the empty place
  before new ordinary discoveries/offers. Every confirmed missing place gets a short bounded search, including
  an unwanted known reserve. Repeating
  ticks must not repeat the loss message. Unknown previously noticed portions use
  "etwas", never an unlearned name.
- [ ] Repeat while she watched the actual take/placement, or while she owns the
  portion. No unexplained ground-loss message. Other drops/moves remain ignored
  during a committed investigation; verify ordinary clicks still ask for a moment.
- [ ] Reopen the exact printed temporary save. Learned identity/assessment remain;
  current presentation, visibility, gesture and action do not resume. An unknown
  new portion found at a previously confirmed empty place needs real identification.
  Check known-stock retrieval with `--needs hungry` as documented below.

Parameters live in the existing validated balance JSON: noticing 6 widths/0.2 s,
face hold 1 s, local empty-place evidence 0.5 s. Handover, walking and pickup reach
are unchanged. Automated checks do not establish visual calibration or user acceptance.

Automated handoff: 1,020 tests passed in 224.194 s on Windows/Python 3.11;
Ruff, strict Mypy (179 source files) and Pyright passed. Code commit `53434a5`
passed [CI 38978799149](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/38978799149)
on Linux Python 3.11/3.13 and Windows. The actual Python 3.14 isolated launcher
with two unknown portions and its same-save restart also exited normally.
Earlier Tk teardown fixtures still print ThemeChanged diagnostics in the full
suite, without failed tests. These results do not replace the unchecked visual
and input observations above. Commit evidence is in the perception plan.


## Observed continuity and known-item retest — 16 October 2026

Use the isolated launcher below, at both 1x and 2x. The
[continuity plan](OBJECT_CONTINUITY_CORRECTION_PLAN.md) records automated evidence.

- [ ] Pick up a known cookie while Aiko is free and watching. Move it far across
  the supported display. She retains its identity; ordinary holding causes no
  return protest, irritation or friendship loss.
- [ ] Hold a fresh unknown food/drink near Aiko. Recognition still takes time;
  once recognized, the offer/refusal names it. Move it away and back while she
  watches: no repeated identification. Change need during holding: she can begin
  wanting it without treating the previous holding time as theft.
- [ ] Release a desired portion high above the floor. She follows fall/hops,
  waits for ground contact and collects the same known portion without another
  identification. Test food around 76 satiety and drink around 65 energy after
  an expressed offer wish. Ground collection provides no human care reward.
- [ ] Release into her hand instead: known acceptance, then full slow eating or
  drinking. No text claims she must find out what the accepted item is.
- [ ] Take her already committed target: the existing protest/return rules still
  apply. Drop a different identical portion: it must not replace that subject.
- [ ] Take an unknown Energy Drink during approach, then hold it near her. After
  the return request she names the recognized drink and states whether she wants
  it. Agreement allows actual handover or known ground retrieval; refusal ends
  return requests and further withholding penalties while retaining knowledge.
  Change her need during a cue and release during recognition to check ordering.
- [ ] Close while holding a recognized desired portion, reopen the same temporary
  save, and check knowledge survives but cursor/wish/interaction do not resume.
  A previously known but unassessed portion needs a decision, not identification.
- [ ] Break actual visual contact while moving a portion: hidden motion cannot
  update its remembered location. Existing bounded subjective search still applies.

Practical acceptance of these changes remains open; automation is not visual
acceptance. Earlier results below describe their respective earlier builds.

Automated handoff (17 October): 997 tests passed in 220.374 s on Windows/Python
3.11; Ruff, strict Mypy (178 sources) and Pyright passed. Code-fix CI
[38973573575](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/38973573575)
passed Linux Python 3.11/3.13 and Windows. The native module includes 27 cases;
the actual Python 3.14 isolated launcher and same-save restart also exited
normally. The complete commit ledger is in the continuity plan.

## Committed attention and withholding retest — 16 October 2026

Use the same isolated launcher below, initially with `--scenario hungry --stock
two`. The [correction plan](OBJECT_FOCUS_CORRECTION_PLAN.md) records commits and
automated evidence. These new visual/input checks still require practical acceptance.

- [ ] At 1x and 2x, wait until Aiko starts investigating one portion. Drop another,
  relocate another, move the mouse and hold a different offer near her. The first
  episode continues; other objects are discovered only after it ends.
- [ ] Click/hover during approach and inspection. She asks for a moment at sensible
  intervals, keeps her target and continues walking despite cursor/toolbar presence.
- [ ] Pick up exactly her target before grasp. She stops safely and protests;
  follow it across the supported primary display. A second identical portion must
  not replace her target. A failed press/capture causes no protest or social loss.
- [ ] Drop it high/low, including outside reachable bounds. She watches its hops,
  waits for rest, acknowledges return and continues the same investigation. A known
  assessed portion goes to full consumption without another identification.
- [ ] Briefly reposition once: no friendship loss. Hold for over 18 seconds, or
  repeatedly take it back: spaced requests can turn irritated, with small bounded
  friendship loss. Return provides no bonus. Accepted handover/ground collection
  retain their different care origins.
- [ ] Lose genuine visual contact: she cannot know its new place through the World
  handle; existing short search applies. Explicit play/sleep still interrupts
  safely. Restart the same isolated save: friendship/knowledge persist, waiting
  and input capture do not resume.

Automated handoff: 986 tests passed on Windows/Python 3.11 in 217.982 s; Ruff,
strict Mypy (178 sources) and Pyright passed. Code CI
[38968361032](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/38968361032)
passed Linux Python 3.11/3.13 and Windows. The isolated Python 3.14 launcher and
same-save restart also exited normally. These results cover automation; the
unchecked practical observations above remain for the user.

## Earlier combined retest — 16 October 2026

The [delivery plan](OBJECT_PLACEMENT_AND_SEARCH_PLAN.md) records the implementation
commits and checks. This combined behavior still needs the user's practical
acceptance; earlier successful retests below describe their earlier builds.

Use `--stock one` or `--stock two` on a **fresh** test profile for one or two
unknown Onigiri near Aiko, for example:

```powershell
.\Aiko_World_Test.bat --scenario full --stock two
```

The existing save is never reseeded; omit `--stock` when reopening its printed
path. Arrangement uses actual sprite footprints and reachable bounds, and seeds
no knowledge. Keep the same isolated save to test memory across restart.

- [ ] Hold an offer until Aiko identifies and accepts/refuses it. A watched
  placement preserves assessment when spatial tracking remains continuous.
  Later known retrieval must not repeat inspection. An accepted handover has a
  readable acknowledgement and complete consumption, with human care origin.
- [ ] Drag a resting portion by a visible pixel. Release elsewhere or offer it.
  The same portion moves; there is no duplicate. Escape/capture loss/off-monitor
  release returns an existing portion, while a new chooser portion is discarded.
- [ ] Move it while Aiko can watch, then while she cannot. Disconnected finds do
  not inherit hidden identity or special own-deferral experience. Two identical
  portions remain distinct; one find cannot explain two missing portions.
- [ ] Trigger a need after moving known stock out of sight. At the empty old
  place, check left/right gaze and short ordinary walking, bounded search and a
  single outcome. Reveal useful stock during search; repeat with find-before-need.
  Neither order should produce repeated empty-place searches.
- [ ] Drop low and high at both edges and both scales. Height controls rebound
  strength and the number of hops; low-energy outside releases may finish with
  a short inward ground slide. Every portion finally rests within normal reach.
  Aiko cannot collect it during a hop. There is no special edge snap/grip.
- [ ] Change scale during motion and immediately quit. Reopen the same save:
  surviving portions recover on valid ground, knowledge remains subjective and
  no action/capture/search resumes. Recheck ordinary controls and mouse following.

The fast geometric matrix and native Windows visible/transparent-pixel test cover
both scales; retained real-timer flows cover readable consumption and interruption.
Automated checks do not substitute for this visual acceptance.

## Isolated launcher

Close other Aiko instances. Double-click [Aiko_World_Test.bat](../Aiko_World_Test.bat)
for the hungry profile (satiety/energy 55). To reproduce the reported levels:

```powershell
.\Aiko_World_Test.bat --scenario curious
```

This starts at satiety 76 and energy 60. `--scenario full` starts at 100/100.
Every fresh run creates a different `aiko-world-smoke-*` directory in system
temp. The console prints its exact path and restart command. Existing explicit
save paths are reused without reseeding. The normal user save, including an
`AIKO_SAVE_PATH` override, is not used; selecting that path is rejected.

The launcher prefers `.venv`, otherwise the Python launcher. Runtime requires
Python/Tk only. Pillow is a development/build dependency. All profiles disable
random walks, automatic routine, hardware observation, rhythm learning and
spontaneous speech. Required object bubbles remain enabled. Normal need decay
continues; no World consumption happens while closed.

## Persistent memory and shortened retrieval — 16 October 2026

Start a fresh `--scenario full` session and keep the printed temporary save path.
Drop Onigiri and Energy Drink, one at a time. Let Aiko investigate and put both
down. Quit normally, then reopen that exact save without overrides. She should
retain their identity/inspection, release object gaze and continue normal
interaction without lifting them again just because of the restart.

To test later hunger immediately, quit and reopen the same isolated save with:

```powershell
.\Aiko_World_Test.bat --save-path "C:\exact\printed\temp-folder\state.json" --needs hungry
```

`--needs` explicitly sets only satiety/energy to the selected test profile
(`hungry`: 55/55, `curious`: 76/60, `full`: 100/100) and reanchors its pet time.
World, learned knowledge, food history and friendship remain intact. Omit the
option for ordinary restart; `--scenario` alone never reseeds an existing path.
The normal save path remains rejected, including with this override.

- [ ] Aiko names her current need and recalls the known supply. “Aufgehoben”
  belongs only to a confirmed deliberate reserve, not an interrupted action.
- [ ] Known inspected stock uses approach, pickup, full consumption and outcome.
  No repeated inspect/recognize/desire bubbles. Grasp alone changes no needs.
- [ ] First discovery retains investigation; assessed cursor handover uses its own readable acknowledgement and full consumption.
- [ ] An unwanted known supply lets her follow the cursor normally, including
  after restart and at both sides/scales. A later need activates retrieval.
- [ ] Close during pickup/holding, after put-down or during consumption, then
  reopen the same path. Unconsumed items recover grounded; inspection knowledge
  remains, recovery invents no observed pose, and consumed items/effects do not
  return. Running actions are not resumed.
- [ ] A remembered missing portion gets a bounded local search and one missing
  bubble; it does not keep Aiko looking at or revisiting an absent target.

The existing 30-second pause after consumption still limits renewed seeking of
another already inspected supply. Allow that pause when testing both together;
first investigation of a different unknown item remains independent of it.
Approach pacing/possible repeated loops remains a separate observation.

## What the complete sequence should show

Use one object at a time initially. Bubbles normally remain readable for
1.8–3.5 seconds; this is a deliberate multi-step sequence, not an immediate
feeding click. Ground pickup/put-down lasts 1.41 s, held inspection at least
1 s, and the existing complete consumption clip lasts about 3.59 s.

Record commit, Windows version, primary-monitor/taskbar setup, display scaling
and sprite scale. Repeat visual/input checks at 1× and 2×.

- [ ] Press and hold a food/drink choice. One cursor portion appears; no needs
  change from selection or carrying. Cursor, ground and hand images have clean
  edges on both bright and dark desktop backgrounds, without a purple fringe.
- [ ] Hold near Aiko until recognition and a willingness/refusal bubble. Release
  in the handover area to offer; holding alone transfers nothing. You may release
  once willingness is signaled, without waiting for preview speech to disappear.
- [ ] Accepted assessed handover visibly holds and acknowledges the item, then
  announces use before complete consumption without repeated identification. Nutrition/energy changes once at the visible
  consumption start. Moving the pointer over Aiko after release must not cut
  the consumption clip short. Human handover retains normal care effects.
- [ ] Release elsewhere above the taskbar: the portion falls, rebounds according to impact energy
  and settles on reachable ground. Move away from Aiko/active controls to allow approach;
  keeping random walks off must not prevent object-directed walking.
- [ ] In `curious`, drop Onigiri within roughly 1–2 character widths. Aiko notices
  it, comments, approaches, picks up, holds/examines, identifies it and decides
  she does not need it now. She animates put-down and says she keeps it for later.
  Satiety does not gain meal effects, and the same item is not repeatedly lifted.
- [ ] In fresh `hungry`, drop Onigiri: the same investigation leads to a wanted
  decision and complete consumption. No human-care/friendship reward is granted
  for autonomous use. A known deferred portion can become wanted at later hunger
  without repeating the surprise/discovery story.
  Already inspected stock uses recall, pickup and consumption, followed by the
  outcome; it must not repeat inspect/recognize/desire bubbles. First-time
  investigation and assessed cursor handover retain their separate entries.
- [ ] In fresh `curious`, drop Energy Drink: energy around 60 motivates use after
  investigation. Energy rises by up to ten; satiety and digestion do not gain food
  effects. Renewed supply seeking of examined items pauses for 30 seconds after
  consumption; a different unexamined ground item can still be investigated.
- [ ] Leave Onigiri and Energy Drink together, with hunger and energy around
  66. After finishing the Onigiri, Aiko investigates the drink without the
  former 30-second wait. At energy above 60 she puts it down for later; first
  investigation is independent of the consumption threshold.
- [ ] In `full`, offered food is visibly refused and falls. Ground food is still
  investigated and put down for later. Existing capacity limits remain food ≥96
  and drink at 100; even a small natural energy deficit permits a human drink
  offer, while autonomous drink use requires energy ≤60.
- [ ] During held inspection, request sleep, talk or a game. The unconsumed item
  is put down before the requested action. During pickup after grasp, Aiko first
  reaches the safe held pose, then puts down. No meal effect occurs from grasp
  or interruption. A deliberate action after consumption cannot recreate food.
- [ ] Escape/input-capture loss cancels a carry without consumption or a duplicate.
  Release outside the supported primary monitor discards a new portion or returns
  an existing portion to safe source ground, with brief feedback. Sleeping/busy Aiko does not silently queue an accepted offer.
- [ ] Check taskbar/screen edges, scale changes, item layering, focus,
  click-through and stacking. Existing toolbar pin, settings and game controls
  stay usable. Ambient speech/notifications do not overwrite object-phase bubbles.
- [ ] Repeat drops at both extreme ground edges at 1x and 2x, with Aiko near
  enough to observe them. The damped drop finishes inward on reachable ground.
  Aiko uses normal approach and frame-4 grasp; no extra edge reach is granted.
  If unwanted, she puts it at her feet and releases gaze. Moving her out of
  ordinary reach before grasp must prevent acquisition.
- [ ] During Onigiri consumption, the portion overlaps the fingers in front of
  the character at both scales. Compare the [grip calibration](media/world-eating-grip-comparison.png)
  (source composition, not a native capture). Consumables stay in front of the
  character during pickup, holding and put-down too; no extra hand mask is drawn
  over them. The eating calibration changes neither item pivots nor ground/cursor
  placement.
- [ ] After inspecting and deferring the drink at energy 65–66, Aiko releases
  object gaze and resumes normal cursor/ambient interaction. The recognized
  portion stays remembered at its observed location and is not picked up again
  until wanted (autonomous energy threshold 60, normal retry rules still apply).

Start a fresh profile when comparing need-specific outcomes; a previous meal or
drink changes desire. Missing desire must still permit first investigation.

## Save/restart the same session

Keep at least one unconsumed portion and quit normally. Reuse the exact printed
path, rather than creating another profile:

```powershell
.\Aiko_World_Test.bat --save-path "C:\exact\printed\temp-folder\state.json"
```

- [ ] Ground portions retain identity and valid position. Unconsumed cursor-held,
  falling/bouncing or pet-held portions recover grounded, without resuming input/actions.
- [ ] Consumed portions do not return and effects do not repeat. Saving still
  writes Pet and World together atomically with outer schema version 1.
- [ ] Learned identity, inspection and confirmed own placement survive reopening.
  Known unwanted portions release gaze and do not trigger another investigation.
  Old saves without the optional memory section start without that knowledge;
  unidentified sightings stay unidentified. No World item is eaten while closed.
- [ ] A later need produces a truthful hunger/energy recall naming the known
  supply, then approach, pickup and the complete consumption clip. There is no
  repeated examination or "Das ist ..." recognition. If needs change before use,
  Aiko declines visibly and puts it down. A remembered missing target is searched
  locally for at most two seconds, then dismissed with one bubble.

## Current automated evidence

Final local regression: 966 tests passed in 189.963 seconds; Ruff 0.13.2,
strict Mypy 1.18.2 (176 source files) and Pyright 1.1.414 for Windows/Linux pass.
[Implementation CI at e78c707](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/38891597930)
passes Linux Python 3.11/3.13 and Windows. The final test-only change positions
its goal-handoff fixture on the smaller CI desktop; production matches c7bf92b.
Native input checks include visible/transparent pixels at 1x/2x without focus
activation, plus the retained actual-timer consumption/interruption flows.
The enhanced starter launched a fresh two-portion save and reopened that same
isolated file successfully. Combined user visual acceptance remains pending.
See the [full delivery evidence](OBJECT_PLACEMENT_AND_SEARCH_PLAN.md#final-automated-handoff--16-october-2026).

## Historical automated evidence

Current verification is recorded in the [delivery ledger](OBJECT_PLACEMENT_AND_SEARCH_PLAN.md#small-delivery-steps). Older counts below are historical.

16 October persistent-memory follow-up: 907 tests passed on Windows/Python 3.11
in 210.6 s, with pinned Ruff, strict Mypy (169 source files) and Pyright green.
Cold restoration covers both edges at 1x/2x, unwanted supplies releasing gaze,
later need-driven direct consumption, saved absence/local search and consumption
snapshots without ghost targets. The new actual-timer food restore test passed
in 12.4 s and preserves the complete eat clip. A weak-reference test verifies
immediate Tk image-owner shutdown without relying on later garbage collection.

Separate Python processes also exercised one temporary save: known deferred
Onigiri survived a full restart, `--needs hungry` consumed it once, and another
default-launcher Python 3.14 restart retained no portion/target or repeated care
effect. The typed memory codec, active ages, reset IDs, old saves, backups and
interrupted atomic writes have headless regression coverage. These are automated
checks; native visual/input acceptance for this follow-up remains pending.

Windows/Python 3.11, 15 October 2026:

- C1 `f902d20`: 830 tests; reproduce missing investigation and hover truncation.
- C2 `5730516`: 834 tests; curiosity, use decisions and subjective examined memory.
- C3 `ae12dd6`: 837 tests; identified phases/receipts and safe cancellation.
- C4 `1c0e95c`: 845 tests; full visible flow, handover holding and hover protection.
- C5 `bf2f562`: 848 tests; reproducible 22 binary-alpha copies, unchanged source
  hashes/RGB/geometry and shared cursor/ground/hand display paths.
- C6 `9dec641`: 850 tests passed in 157.4 s. Ruff 0.13.2, strict Mypy 1.18.2
  (167 source files) and Pyright 1.1.414 passed. The curious launcher and reopening
  its same temporary save both exited cleanly with `--auto-close-ms 1000`.
- C7 `416607c`: 851 tests passed in 178.0 s; a different first investigation
  bypasses the supply-seeking pause. CI run
  [38770173465](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/38770173465)
  passed all three jobs (Linux Python 3.11/3.13 and Windows).
- C8 `ea4361f`: 855 tests passed in 183.9 s with the same pinned static gates.
  Eating-grip coverage and pickup/hold/put-down top-layer assertions pass at both
  scales; complete asset preparation preserves decoded pixels/metadata, validates
  per-build file hashes and is repeatable with the same encoder. A follow-up
  corrects the cross-platform test's original assumption of identical PNG bytes.
  Deferred drink memory survives gaze release; cursor following and later
  need-driven return are verified.
- The test portability follow-up also passed 855 tests on Windows in 183.2 s
  plus the pinned static checks; the Linux matrix covers the different encoder.
- Current CI results are linked in the implementation ledger and
  [PR checks](https://github.com/Lexoniarus/aiko-desktop-pet/pull/10/checks)
  run Linux/Xvfb Python 3.11/3.13 and Windows, including real Tk flow tests.

16 October edge-grip follow-up: 867 tests passed locally in 205.5 s, with the
same static gates green. The four left/right 1x/2x component cases check actual
driver arrival, frame-4 custody/snap, refusal and placement at the feet, remembered
location and released gaze. Additional cases reject acquisition after Aiko moves
away and verify wanted edge consumption without early nutrition. Pure geometry
tests include an offset track, unchanged ordinary reach and unsupported poses.
Five real-timer tests passed in 100.7 s, including left 1x/right 2x edge flows.

`test_world_runtime_flow.py` runs actual timers and desktop gates: readable,
ordered bubbles, Onigiri at 76%, deferred reuse after hunger, staged drink with
full playback through Enter, interrupted inspection and restart. Component tests
and actual timers also check food consumption followed promptly by drink
investigation/defer at energy 66, preserved recognition and released gaze.
Component tests
separately exercise delayed/stale/duplicate completions and transaction recovery.
These checks do not replace native visual/input acceptance. The user's positive
retest covers the observed basic sequence; keep unreported checklist cases open.
The PR remains draft and unmerged for review; no merge was requested.
