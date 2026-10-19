# Adaptive sleep proposal

> **Implementation update, 2026-10-19:** Stage 4 implements the simplified
> model on `feature/social-optimization`; current rules and bounded delivery
> choices are in [Sleep rules](SLEEP_SYSTEM.md) and the
> [active implementation plan](CARE_TIME_IMPLEMENTATION_PLAN.md). Original
> discussion disclaimers and superseded examples below remain historical evidence.

> **Discussion proposal only — no implementation approval.** Recorded on
> 2026-10-19 on `feature/social-optimization`, alongside code baseline `b190694`.
> The owner requested preservation of the proposed sleep, wake and habit-learning
> rules, expanded with manual-control priority and recovery/wake conflict rules.
> The later sleep-time care-break discussion is preserved below as well.
> Habit learning was subsequently simplified to actual input, inactivity and
> powered-off/standby computer state, without weighted or additional signals.
> These are candidate timings, not shipped settings, a final accepted
> specification or playtested behavior. No runtime code, balance JSON, save
> schema, dialogue or user save changes accompany this documentation.

Related proposals: [need balance and example day](NEEDS_BALANCE_PROPOSAL.md),
[friendship and neglect](FRIENDSHIP_BALANCE_PROPOSAL.md) and
[overall mood](MOOD_BALANCE_PROPOSAL.md).
Current implementation: [time and saves](DATA_AND_SAVES.md),
[adaptive memory](../aiko_pet/pet/mind/adaptive_models.py),
[adaptive routine](../aiko_pet/pet/mind/adaptive.py) and
[sleep policy](../aiko_pet/pet/mind/adaptive_policy.py).

## Intended experience and implementation distinction

Aiko should align her main sleep with the user's recurring quiet phase, her
energy and current observed activity. The phase will often be at night, but
an early-morning or daytime sleep pattern is equally possible. Normal sleep
must remain compatible with maintaining high friendship without human care
during the night.

The current code already persists coarse hour-of-week activity/presence
aggregates. Existing sleep decisions still depend strongly on the configured
night period and workload. Closed-time reconstruction is currently capped at
eight hours, live standby is excluded, and manual sleep currently persists
until waking. These existing rules are not the proposed model below.

The proposal changes neither the current implementation nor its documented
settings. It does not imply that the existing adaptive learner already provides
all of the learning, sleep-window or reconstruction behavior described here.

## Proposed learning of the main quiet phase

Keep the first model simple. Learn recurring beginnings and endings of longer
quiet phases from these signals only:

| Signal | Meaning for the proposed learner |
| --- | --- |
| Repeated mouse movement, clicks or keyboard input | Actual user activity; mouse and keyboard are alternatives, not a requirement to use both |
| At least 15 minutes without actual use | Inactivity and a possible quiet phase |
| Computer powered off or in standby | Clear unavailability; Aiko's elapsed time continues |

A single brief mouse jitter does not end the quiet phase. Recognize actual
repeated input rather than treating every tiny movement as renewed use. User
activity need not be directed at Aiko; personal friendship contact still uses
its separate care rules. Powered-off/standby state indicates unavailability,
not proof that the human is asleep or an automatic command for Aiko to sleep.

| Learning stage | Candidate rule |
| --- | --- |
| No usable pattern yet | Tentative quiet phase 23:00–07:00 |
| First personal tendency | After three similarly timed quiet phases |
| More established personal pattern | After seven similarly timed quiet phases, the learned window takes precedence over the initial orientation |
| Regular adjustment | Move sleep onset and wake time by at most 30 minutes per day |

The default window is an orientation, not a forced bedtime or a restriction to
nighttime users. A recurring 02:00–10:00 pattern can replace 23:00–07:00.
One unusually late night must not immediately replace the established rhythm.
The three/seven phases are recurring longer quiet periods, not repeated polling
samples within one evening. Repeated changes can gradually move the expected
sleep and wake times; one exception does not immediately replace the pattern.

Do not use CPU/GPU workload, app closing/opening times or manual Sleep/Wake
choices as additional habit-learning signals. Manual commands retain their
control priority below but do not serve as training evidence. The simplified
proposal uses no signal weights, percentage quotas, confidence scoring or
separate weekday/weekend models.

A closed app supplies no input observations. Unless the computer's off/standby
state is actually known, absence of app observations remains unknown rather
than measured inactivity. While closed, Aiko follows her already known rhythm;
app start/stop timestamps do not become substitute training evidence. No
background input monitoring while closed is implied.

Use coarse activity and quiet-period timing without typed content, application
names or a raw user-action log. Learned rest is an expectation of availability,
not a claim to know when the human actually sleeps.

## Proposed autonomous sleep onset

During the expected main quiet phase, Aiko may fall asleep after **15 minutes
without recognizable user activity**, provided no direct interaction is still
in progress. Do not end a game or conversation merely because bedtime arrives.

Continued actual user activity postpones normal sleep onset. The clock alone
does not force sleep. CPU/GPU load from a download or computation does not by
itself keep Aiko awake: machine workload and human presence are distinct.
Under the later [consumption-modifier proposal](NEEDS_BALANCE_PROPOSAL.md#proposed-consumption-modifiers),
hardware can increase awake hunger/energy consumption but supplies no direct
sleep signal. Sleep can still follow the resulting energy level; while Aiko
sleeps, hardware surcharges do not apply.

Outside the expected main quiet phase:

| Current energy | Candidate behavior |
| --- | --- |
| Above 25 | An ordinary user break does not automatically cause a long sleep |
| At most 25 | After 15 minutes of quiet, a 60–90-minute nap is allowed |
| At most 10 | A longer recovery sleep is needed instead of only a short nap; the initial recovery target is at least 40 energy |

At the proposed +7.5 energy per sleeping hour, a 60–90-minute nap restores
7.5–11.25 energy before clamping and therefore does not replace the main sleep.
The priority rules below distinguish ordinary bedtime from acute exhaustion.
At energy at most 10, exhaustion can require recovery even during the main
quiet phase or continued user activity. Subject to the manual-control grace
period, finish a direct interaction in an orderly way and then rest; activity
must not keep an exhausted Aiko awake indefinitely. Exact orderly completion
and nap-length selection within the agreed range still need specification.

## Proposed waking

The learned wake time is the normal endpoint of the main sleep, provided
energy is at least **40**. If energy is below 40, continue recovery until that
threshold rather than automatically waking in severe fatigue. Reaching 100
energy earlier does not itself wake Aiko while her quiet phase continues.

If the user returns before the expected wake time, allow automatic early waking
after **two minutes of recognizable activity**, provided both conditions hold:

- Aiko has actually slept for at least **four hours**.
- Her current energy is at least **60**.

An isolated brief mouse movement at night therefore does not immediately end
sleep. The four-hour/60-energy conditions are the proposed early-waking gate,
not a claim that four hours is the normal sleep duration. Exact interpretation
of sustained recognizable activity remains to be specified.

Manual waking remains possible at any time. Manually starting sleep should
also allow a later automatic end rather than leaving Aiko asleep indefinitely
until another explicit click. This differs from the current manual-sleep rule.

## Proposed priority and manual-control grace period

This later discussion resolves the previously open conflict priority as a
candidate design. It does not implement or authorize these rules.

| Priority | Candidate rule |
| --- | --- |
| 1. Explicit manual choice | Execute Sleep or Wake; if commands conflict, the latest takes precedence |
| 2. Acute exhaustion | At energy at most 10, start or continue recovery toward at least 40, after honoring manual protection |
| 3. Normal sleep endpoint | Main sleep ends at the expected wake time if energy is at least 40 |
| 4. Observed user return | May end sleep early under the sleep-type conditions below |
| 5. Expected quiet phase | Supplies the ordinary sleep frame; actual activity may postpone normal sleep onset |

An explicit Sleep or Wake receives **30 minutes of protection against an
automatic opposite decision**. A manual wake is not immediately undone by
automatic sleep; a manual sleep is not immediately undone by activity or a
scheduled wake. A later manual command still takes precedence and establishes
its own protection period. After protection expires, reevaluate the normal
rules; it is not an instruction to reverse the state automatically.

Manual commands do not restore energy. Energy and other needs continue using
the actual sleep/wake rates during the protected interval. An exhausted Aiko
can therefore be manually woken but remains exhausted. Her subsequent automatic
recovery may resume once protection ends. The protection uses real elapsed time,
including closed-app and standby time, rather than restarting on reopening.

## Proposed endpoints by sleep type

| Sleep type | Normal endpoint | Early endpoint from observed activity |
| --- | --- | --- |
| Main sleep | Expected wake time and at least 40 energy | Two minutes of recognizable activity, at least four hours actually asleep and at least 60 energy |
| Nap | Normally no earlier than 60 minutes and no later than 90 minutes | Two minutes of recognizable activity and at least 25 energy; this exception can occur before 60 minutes |
| Exhaustion recovery | Reach at least 40 energy; then continue main sleep if still within its quiet phase, otherwise recovery may end | Activity alone does not end necessary recovery; explicit manual waking remains possible |

All automatic endpoints remain subject to an active manual protection period.
The four-hour/60-energy gate applies to **early main-sleep waking**, not every
nap and not waking at the normal scheduled time. It does not override the
40-energy minimum for normal main-sleep completion. The user need not be present
for a scheduled normal wake or the end of recovery outside the quiet phase.

If recovery reaches 40 during the main quiet phase, this ends the acute recovery
requirement rather than forcing Aiko awake. Normal main-sleep rules then apply.
An ordinary quiet phase can be postponed by activity; the at-most-10-energy
exhaustion rule has higher priority, except during explicit manual protection.

### Recorded conflict examples

Unless explicitly stated otherwise, these examples assume no active manual
protection and the learned main-sleep endpoint at 07:00:

| Situation | Proposed result |
| --- | --- |
| 07:00, energy 72 | Wake, even if the user is not present |
| 07:00, energy 22 | Continue to 40; at +7.5/hour this takes another 2 hours 24 minutes, reaching 40 at 09:24 |
| 03:00, one brief mouse impulse | Continue sleeping |
| 06:00, user returns for sustained activity, six hours slept, energy 80 | Early wake is allowed after two minutes of recognizable activity |
| 23:00, energy 45, game still in progress | Postpone ordinary bedtime; do not end play solely because of the clock |
| 23:00, energy 8, user remains active | Exhaustion takes priority; end the interaction in an orderly way and begin recovery |
| Explicit Wake while exhausted | Wake and retain low energy; no automatic return to sleep during the next 30 minutes |
| Explicit Sleep followed by an activity signal or scheduled wake inside 30 minutes | Continue sleeping until protection ends, unless explicitly woken |

These examples preserve decision logic, not observed runtime or playtest results.
Manual commands do not train the schedule. Repeated changes in actual input,
inactivity or known off/standby timing may still move it gradually under the
simplified learning rules.

## Proposed care breaks during sleep

A brief care break is distinct from ending the main sleep and starting the
waking day. Aiko can wake to eat and then continue the same main-sleep phase.
The trigger should have a concrete prospect of remedying a need; simply waking
does not satisfy hunger, social contact, affection or fun.

| Need while asleep | Candidate response |
| --- | --- |
| Satiety at most 20 | Brief food break if Aiko remembers a suitable available, accessibly placed portion |
| Satiety exactly zero | Additionally allow one short supply search even without a remembered suitable food portion |
| Energy low or critical | Continue restorative sleep; do not wake to consume an energy drink |
| Social low or critical | No automatic wake solely for this need |
| Affection low or critical | No automatic wake solely for this need |
| Fun low or critical | No automatic wake solely for this need |

Low social, affection and fun remain low and affect mood and eligible neglect
loss under their separate proposals. Do not invent self-conversation or human
care to refill them. Later objects for these needs require their own usage rules.

### Food-break sequence and search limit

1. At satiety at most 20, use remembered identity and the expected place of a
   suitable accessible food portion as the reason to attempt a break.
2. Briefly wake and check the actual subject at the expected place. Memory is
   not a guarantee of present availability; a missing or unreachable portion
   cannot be consumed.
3. If a real usable portion is available, eat it through valid consumption.
4. Aim for **at least 40 satiety**. If one portion is insufficient, another
   actually available usable portion may be consumed. A larger portion can take
   satiety above 40, subject to the normal 0–100 bound.
5. Continue sleeping afterward if the applicable sleep phase still continues.

The 20-point entry threshold and 40-point care target avoid a tiny snack
causing immediate repeated wake-ups. Reaching the target depends on actual
stock; it is not a fabricated refill when portions are insufficient.

At exactly zero satiety without remembered suitable food, allow a supply search
of at most **five minutes**. With the app running, reachable objects may be
investigated under the normal perception/identification rules. This does not
grant advance knowledge of unknown contents or hidden movements. If no suitable
food is found, return to sleep with hunger still present; Aiko does not die.

After a failed attempt, do not repeatedly wake/search during the **same main
sleep phase**. A new valid food offer or manual waking can change the situation.
Brief care breaks do not start a fresh main-sleep phase and thereby reset the
failed-attempt restriction. Exact nap/recovery episode treatment and persistence
of that restriction still require specification.

### Interaction with sleep priority and elapsed time

- The **30-minute manual-Sleep protection** applies to automatic care breaks
  too. Wait for its expiry; an explicit manual Wake remains possible at any time.
- A short care break does not restart the night. For the four-hour condition
  on early main-sleep waking, add actual sleeping time within that same main
  phase; the awake break itself contributes no sleep time.
- Use awake need rates during the break and sleeping rates after returning to
  sleep. Energy recovery and its neglect exemption follow actual restorative
  sleep, not the entire labeled night including awake care time.
- If the expected wake time has arrived by the end of the break, apply the
  normal wake/recovery decision, including the 40-energy threshold, rather than
  unconditionally starting another sleep period. Manual protection still applies.

Consuming food may end the relevant hunger-neglect deduction once the need is
restored, but autonomous consumption does not create personal care contact,
social/affection credit or friendship points. It does not reset the absence clock.

## Closed app and computer standby

Use the same elapsed-time sleep model whether the app is open, closed or the
computer is suspended. Closing/standby is not automatic proof that Aiko has
entered her main sleep. There is no eight-hour cutoff in the proposed elapsed
time accounting.

| Situation | Proposed behavior |
| --- | --- |
| App closes while Aiko sleeps | Sleep continues until its applicable wake condition |
| App closes shortly before her expected quiet phase | Aiko can fall asleep later according to her own routine |
| Computer enters daytime standby | Sleep is not automatic; rhythm and energy determine it |
| App stays closed for several days | Reconstruct recurring sleep and wake phases rather than one uninterrupted multi-day sleep |

With no live activity observations while closed, reconstruction uses the
available prior state, learned expectation and explicit sleep/wake rules.
Do not invent intermediate user actions, fresh activity evidence or personal
care. How absence of observations satisfies the quiet-onset policy still needs
an explicit reconstruction rule; it is not fabricated input-idle measurement.
Manual-protection expiry, energy recovery and normal sleep endpoints are applied
in chronological order. Do not invent a user-return event to trigger early
waking while closed, and do not postpone an otherwise due wake until reopening.

Apply care-break thresholds chronologically while closed or suspended too, but
initially limit autonomous consumption during that reconstruction to portions
that were **already identified and saved as accessibly placed**. They must
actually remain available. An unknown stored portion cannot become a known
food through an invented offline discovery; the zero-hunger search allowance
does not override this restriction. Do not infer observed scenes or human offers
while the app was closed. Used portions remain consumed in saved stock.

On reopening or resuming, advance events in chronological order. For example,
if Aiko actually slept from 23:00 to 07:00 and the app opens at 12:00, she has
already accumulated five awake hours since 07:00. Do not treat all 13 elapsed
hours as sleep or defer waking until the application opens.

The existing example day assumes sleep actually starts at 23:00, for example
after the user's sleep action. An automatic onset after 15 quiet minutes may
instead start at 23:15; an unchanged 07:00 wake time would then give 7 hours
45 minutes. The quiet-window start is not an unconditional promise of exactly
eight hours asleep.

## Needs, resources and friendship during sleep

Use the separately proposed sleeping rates: energy +7.5/hour, satiety
-1.4/hour, social -0.35/hour, affection -0.25/hour and fun unchanged. Clamp
needs to 0–100. Aiko can remain hungry or socially underprovided while sleeping;
sleep does not refill those needs.

Only actual available desktop portions may be consumed and must remain consumed
in saved stock. The care-break section now records candidate hunger thresholds,
search and sleep resumption, with stricter identified-stock rules during
closed-time reconstruction. There is no hidden offline food supply or fabricated
human feeding.

Contact-related friendship loss continues over real time. Sleeping, automatic
waking and autonomous care do not award personal friendship or renew care
contact. An eight-hour contact gap has two points of reference absence loss.
Under the latest friendship revision, level 10 has factor 2, making this
approximately **four actual friendship points**, not the earlier two-point
night. Adequately rewarded distributed daytime care can cover this within the
rolling +5/24-hour ceiling; there is no additional night exemption.

While energy is actually increasing during restorative sleep, the proposed
energy-neglect clock and energy-neglect deduction pause. Earlier history is
not erased, and this does not pause absence-related loss. Other neglected needs
continue to be assessed under their own rules. Mood follows the evolving needs
and its separate decline/recovery proposal.

## Remaining decisions and future verification

The [combined example day](NEEDS_BALANCE_PROPOSAL.md#combined-example-day-with-needs-mood-sleep-and-friendship)
now records the normal branch with manual Sleep at 23:00, full energy around
06:40 and scheduled Wake at 07:00. No nap, exhaustion recovery or food break
is triggered; it is an arithmetic consistency check, not a runtime playtest.

- Verify recurring quiet-phase recognition and the three/seven-phase milestones
  using only actual repeated input, inactivity and known off/standby state.
  Preserve the simple model without adding weighted or substitute signals;
  do not treat unknown app-closed time as measured inactivity.
- Resolve onset when observations are unavailable, sleep-type selection at
  boundaries, orderly completion under exhaustion, exact nap length within
  60–90 minutes and interruption boundaries. Actual sleep time is summed across
  short care breaks within one main phase; phase reset criteria remain open.
  Priority, 30-minute manual protection and energy thresholds are recorded above.
- Specify durable care-break/failed-search accounting, valid new-offer detection
  and nap/recovery episode handling without reopening-triggered search loops.
  Validate finite stock, remembered availability versus actual availability,
  and the stricter no-new-discovery rule for closed-time consumption.
- Evaluate the combined sleep, need and friendship trajectory for normal days,
  late nights, shifted work patterns, early returns and multi-day absences.
- Specify persisted sleep expectations/transitions and exactly-once time
  reconstruction across saves, restarts and standby; account for clock changes
  without creating fictitious activity or replaying consumption.
- Verify live/offline consistency and actual desktop behavior with isolated
  saves when implementation is separately authorized.

These timings preserve the discussion. They are not implementation approval.
