# Adaptive sleep and finite unattended care

This guide describes stage 4 on `feature/social-optimization`. The
[proposal](ADAPTIVE_SLEEP_PROPOSAL.md) remains design history; the active
[implementation plan](CARE_TIME_IMPLEMENTATION_PLAN.md) records delivery scope.

## Expected quiet window and observations

The tentative window is 23:00–07:00 local time. Sleep uses actual anonymous
last-input timestamp changes, independently of hardware observation. Repeated
mouse or keyboard use counts; no key identities, text or application titles are
read. A single input/jitter does not establish a return. A return requires at
least three input changes, no gap over 30 seconds and two minutes of activity.
An observation gap over 60 seconds is unknown. The desktop can explicitly
recognize suspension by comparing suspend-inclusive and active uptime; this is
unavailability, never evidence of continued human activity.

An observed quiet phase lasts at least four and at most sixteen hours and ends
with a sustained return. Only one phase per local day is retained, at most seven
in total. Both endpoints must be within 90 minutes of another phase to recur.
Three matching phases establish a tendency; seven establish the learned window.
Median endpoints resist one-off exceptions. Each endpoint moves by at most
30 minutes per local day. No weighting, weekday model or background input
monitor is involved. Unknown closed time, app timestamps, manual commands and
CPU/GPU utilization do not train sleep. Actual input observations during a
manual sleep remain input observations, not command-derived evidence.

`learn_rhythm` disables new learning while retaining the learned expectation;
forgetting the profile restores the tentative window. `observe_computer`
controls hardware sampling, independently of sleep input observations.

## Priorities and real time

- The latest manual Sleep/Wake command takes priority for 30 elapsed minutes,
  surviving save/restart and standby. Waking grants no energy. Accepted personal
  care wakes Aiko with the same protection; rejected care and bare game requests
  do not. Manual sleep chooses main sleep inside the expected window and a
  75-minute nap outside it.
- After protection, exhaustion at energy at most 10 starts recovery toward 40,
  once an already committed action/game has finished. Activity cannot prevent
  this recovery. If still quiet inside the expected window at 40, continue main
  sleep; otherwise wake.
- Ordinary main sleep starts after 15 minutes of observed quiet inside its
  window. Ordinary daytime naps need that quiet and energy at most 25.
- Main sleep normally ends at its saved expected endpoint with energy at least
  40. Full energy alone does not end it. Early waking requires sustained input,
  four actual sleeping hours and energy at least 60. Naps end after 75 minutes,
  or on sustained return, with energy at least 25. Extreme exhaustion after
  manual grace promotes a nap to recovery.

Closed time follows the saved expectation: assume onset 15 minutes after the
window starts, without claiming measured inactivity. Reopening inside that
window after the onset may start sleep immediately. Outside it, unknown time
cannot prove daytime quiet; exhaustion remains possible. Waking occurs at the
historical endpoint, so a noon reopening already includes the intervening awake
hours. Multiple days produce successive episodes. Local schedule time and the
suspend-inclusive elapsed axis remain distinct.

Turning `auto_routine` off prevents new automatic sleep, naps and recovery.
An existing manual/automatic episode still reaches its endpoint after protection;
needs, relationship time and finite resources continue to progress.

## Food breaks and finite portions

At satiety at most 20, remembered, accessible actual food can trigger a brief
awake break toward at least 40. A remembered identity alone is insufficient:
the portion must have been identified and appraised, and must still rest at its
acquired remembered place within the World. Missing, moved, held, consumed,
unappraised and unknown items cannot supply food.
Remembered food can trigger a check even if it has actually moved; World truth
does not silently tell sleeping Aiko that a remembered place is empty.
Manual sleep protection defers a break. Low energy does not cancel acute food
care; the sleep priorities reapply afterwards. An expired live break first
finishes safe put-down of an unconsumed held item. A suspended unfinished held
action is not completed by fake offline animation; it keeps its physical custody
and defers new sleep until the existing owner can finish safely on return. Drinks, fun, social and affection do not trigger sleep-time
searches.

At zero with no accessible known food, one live search uses the existing
`SearchTask`, perception, route, inspection and intake owners, bounded to five
elapsed minutes. Failure persists within the episode, including naps/recovery,
and cannot restart on ticks or reopening. A newly acquired valid food source
allows a retry; manual waking ends the episode. A resumed expired search cannot
restart from zero. Brief care does not reset the episode or its cumulative actual
sleep. Awake break time uses awake need rates and does not count as sleep.

Closed time cannot investigate unknown food. It uses only saved acquired stock,
with one minute of awake intake time per portion. Outside sleep, known food and
drinks use the existing autonomous appetite thresholds; exhaustion takes
priority over a drink. No food is generated from the catalogue. Autonomous
intake never grants human social/friendship credit or renews personal contact.
Reopening displays the resulting state and stock, without replaying animations.

## Owners and save compatibility

`PetState` owns immutable `SleepEpisode` in its complete `PetValues` checkpoint.
`pet/sleep.py` calculates priorities; `pet/lifecycle.py` supplies the shared
chronological grid; `pet/need_decay.py` remains the only numeric need integrator.
`AdaptiveRoutine` owns anonymous observations and `QuietWindow` in its existing
adaptive memory. The former hardware-dependent sleep policy and its coefficients
are removed. Existing workload classification/hourly expectations remain for
grounded work conversation only; neither can choose sleep or train QuietWindow.

`SessionTimeProgression` in `application/session_time.py` coordinates those
existing owners with World resources through explicit application injection.
The clock contains no World callback. It plans the elapsed interval once and
uses `PetState.advance_time_step()` rather than recursively calling `advance()`.
First-save relationship history is finalized once at the whole interval's end.
The common `sleep_care_complete()` policy decides when care ends; the live
interaction owner still performs safe put-down before finishing. Historical
awake intake uses the existing object-use policy, including a known drink
when hunger cannot be supplied by any available food.


`ObjectConsumption.apply_portion` supplies one atomic World/Pet/object-memory
transaction for historical and animated intake. It does not own another pet,
clock, resource catalogue, search or movement writer. Restoration constructs
World and acquired memory before reconstruction. Clock checkpoints and paired
owner snapshots roll back failed advancement together.

Outer saves remain version 1. Optional `pet.sleep_episode` v1 stores elapsed
protection/search/intake deadlines, episode type, actual slept duration, expected
wake time and failed-source evidence. Optional `adaptive.quiet_window` v1 stores
only coarse phase endpoints/dates and the expectation. Missing records preserve
progress without inventing old sleep hours, observed quiet or manual protection.
Invalid/future records preserve valid needs and require an original-byte backup
before replacement. Relationship migration remains neutral during a first
legacy catch-up even when finite resource steps split that interval.

Production time/stock equivalence uses the same known timeline and 15-second
boundaries. Numerical comparison tolerates a boundary-sized interval; real live
movement/reading can legitimately add awake break time. Unknown discoveries are
never assumed equivalent to previously known closed-time stock. Physical
suspend/resume acceptance remains explicitly separate from injected clock tests.
