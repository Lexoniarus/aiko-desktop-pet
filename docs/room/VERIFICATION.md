# T1 verification record — 2026-11-05

The implementation is on `feature/shared-room-pwa`, based on green desktop
`ce4797e`. The initial checks below are historical; publication and subsequent
correction-build evidence are recorded separately. Automated checks do not
replace actual-iPad acceptance.

## Completed checks

| Check | Observed result |
| --- | --- |
| Ruff, standard repository roots plus the three new packaging/export scripts | Passed. |
| Strict whole-application Mypy | Passed; 420 source files. |
| Repository-wide Pyright | Passed; no errors or warnings. |
| TypeScript/Vite starter, runtime and Service Worker production builds | Passed. |
| Node projection/package-boundary checks | Both passed. |
| Eight portable room integration tests | Passed, using isolated SQLite state and controlled time. |
| Complete application suite on Linux CPython 3.11 with Tk under Xvfb | Passed: 2,460 tests, 17 platform-specific skips, 182.470 seconds. |
| Existing dependency-graph, UI architecture and public-document checks | Passed; canonical import restrictions retained. |

The full native suite used an isolated Git archive at `a98053e9` with all pinned
runtime requirements installed. Subsequent implementation commits through
`641f45a0` change only room CSS; the Python sources and tests are identical.
The earlier Windows no-window run found only three stale audit paths after the
namespace move; their focused eight-test audit passed after correction.
Local headless skips are not counted as GUI acceptance. No visible host test
windows were opened, and neither the resident desktop pet nor its save was used.

The first Docker attempt was discarded: its old image lacked Astronomy Engine
and pyjokes, and startup waited for an error dialog in the virtual display.
The recorded successful run installed `requirements.txt` before execution and
ran against a fresh source copy on the container filesystem.

## Built-browser evidence

Headless Playwright with Chromium, software WebGL and isolated browser storage
loaded the actual runtime ZIP, Pyodide/WASM, original Python owners and SQLite.
There was no mocked pet/backend. The Browser plugin was unavailable, and visible
test windows were prohibited; this is the reason for the headless fallback.

- ZIP import and actual Python/room startup succeeded.
- Camera swipes did not send a call or change canonical pet position directly.
- All six game surfaces accepted real game input: RPS reveal, Tic-Tac-Toe move,
  Blackjack stand, Connect Four drop, Mastermind guess and Quiz answer.
- Direct feeding, dragging a new portion onto the floor, contact/status menus
  and authored conversation worked.
- The local horoscope began reading with network access disabled. Suspending
  it released custody safely and retained the same book for subsequent use.
- Failed ZIP import retained the installed package and pet progress.
- A second window refused a second save writer.
- Offline reload reopened the real room and retained World objects.
- Portrait/landscape screenshots were inspected. Menu scales of 75% and 200%
  retained toolbar touch targets of at least 44 CSS pixels on an 810px viewport.
- The actual Pyodide browser fetch adapter delivered and presented a live fact
  after explicit source opt-in, with provider/source attribution.
- Separate browser CORS probes could read JokeAPI metadata and content,
  Zitat-Service, WitzAPI and Random Useless Facts; each returned HTTP 200.

The extended browser pass and live-fetch pass used
`aiko-room-0.1.0-641f45a0f2bf.zip`. The six-game interaction pass used the same
game implementation at `5eb89b66`; later functional changes concerned custody,
startup/update lifecycle and layout. Browser console/page-error capture was
empty for the successful extended and live-fetch passes.

## Still pending

- The initial d073 source and deployment checks passed on GitHub, and the
  HTTPS starter is published. The owner confirmed profile installation/start on
  iPad 9th generation/iPadOS 26.6. The remaining
  [device checklist](IPAD_ACCEPTANCE.md) is still open.
- The owner's first device pass found room-transition, bubble placement/emote,
  drag-and-drop, motion, size/depth/occlusion and game presentation differences
  from desktop. The earlier browser interaction checks do not establish parity.
- Safari-specific storage/memory limits, actual touch input, OS eviction,
  background termination, reboot/airplane-mode recovery and multi-day use.
- Later iPadOS compatibility checks, notification sender/Web Push (T2), and
  native desktop room embedding (D1).

Build outputs include versioned runtime/starter ZIPs, `BUILD.json`, and the
German `START_HIER.md`. They contain no personal save or authoring originals.

## Installed-package updates (2026-11-05)

The update flow was checked headlessly with the actual published d073 starter,
Service Worker, package, Python/SQLite and a persisted isolated pet. A same-origin
server switched to the new production starter while an old RPS game was open.
The new worker took over without navigation or game interruption. Reopening
started the new shell with the old runtime; it verified/staged the full new
package, left the active pointer unchanged and offered only a close/reopen notice.
The next start activated it with the original zodiac preference and World object
IDs intact. No profile recreation, storage clearing or ZIP import was used.

A test-only package with unchanged code and a different manifest version then
exercised a second update. Wrong manifest hashes and interrupted downloads kept
the active version and save intact. Retry completed, an open game blocked the
restart button, and explicit restart preserved a just-changed preference and
the same object identities. Full browser restart offline retained the package
and state. Cache cleanup retained current and previous packages only. No page
errors or unexpected console errors were seen; deliberate offline networking
produced the expected browser resource error. Landscape 1080x810 and portrait
810x1080 were inspected. The Browser plugin was unavailable; Playwright used
the installed headless shell with software WebGL, without visible test windows.

A deliberately injected failed `suspend` response additionally checked the save
boundary: activation was refused, active/pending IDs stayed unchanged, and the
original runtime resumed ticking. The subsequent real suspend/flush and restart
succeeded. The final portrait inspection confirmed the notice no longer overlays
open menus.

The starter/runtime/worker production build and both existing Node boundary
checks passed. No Python behavior or native UI was changed, so the full native
suite was not rerun for this update. Actual iPad update lifecycle and Safari
storage limits still require device confirmation.

### Published update and live upgrade

The update is live at the existing
`https://lexoniarus.github.io/aiko-desktop-pet/room/` origin and path. Runtime
version **0.1.0-a8a6a75a11c9** was built from `a8a6a75a11c9` and published as
[`room-test-0.1.0-a8a6a75a11c9`](https://github.com/Lexoniarus/aiko-desktop-pet/releases/tag/room-test-0.1.0-a8a6a75a11c9).
The source [web check](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42022876595)
and [deployment](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42023103814)
both completed successfully. Deployment commit `8dc2747b` pins site asset
SHA-256 `9c043d18f11f2a20ede4976caefe7bc5cb8972cbab4ca9041eb7cd7979b55549`.

Before deployment, a separate headless browser profile installed the actual
HTTPS d073 release and persisted a zodiac preference plus a World object. After
deployment that same profile upgraded through the existing icon URL without
storage recreation or manual ZIP import. The new version, preference and exact
object ID were confirmed, then the real HTTPS app reopened offline. The version
and controls were inspected in landscape and portrait, with no page errors.
The existing Dropbox installer/profile does not need replacement for this
transition. Device-specific confirmation remains pending; the room branch has
not been merged into main.

## Room and game correction build (2026-11-05)

Runtime **0.1.0-ff6d7142a7cc**, from `ff6d7142a7cc`, addresses the owner's
first-device findings. The v16 reference seams and actual visible character
height are used; render interpolation follows Python-owned movement, with shared
floor footprints and routes around furniture. Speech and original emote artwork
are anchored over Aiko independently of menus and game-hand props. Pointer
capture, cancellation and World reservations preserve the same dragged object;
new portions are created only after a valid drop.

All six games use the existing rules/sequences with their original boards,
icons and presentation assets. The room adapter connects arm countdown, public
card flight, chip pickup/throw and the cosmetic safe/snack finale. These visual
effects do not create food, settle rules or award care. The portrait game sheet
reserves the upper room area; boards fit inside the available play area.

Final verification used the actual packaged Python/SQLite in an isolated,
headless Chromium profile with software WebGL. No visible windows, resident
desktop process or personal save were used. Tests ran after implementation.

- Thirteen portable room tests passed, including five focused regressions for
  furniture routing, drag custody/cancellation, hidden-card privacy and cosmetic
  game boundaries. Forty-three existing pure game/reaction/architecture tests
  passed. The full native GUI suite was not repeated.
- All three Node checks passed, including motion interpolation; the production
  TypeScript/Vite starter, runtime and Service Worker built successfully.
- Ruff passed; strict Mypy passed for 421 application files; repository Pyright
  reported zero errors and warnings.
- Actual touch input exercised independent swipes, floor placement, same-ID
  movement, cancelled reservation, secondary contacts, rejected wall drops and
  direct torso offers. A completed touch tap is dispatched once even when the
  browser omits its compatibility click after a captured drag.
- All six games were played in landscape and opened/inspected in portrait.
  Touch Mastermind ran through all attempts to the safe/snack finale without
  reading its hidden code; swapping and invalid-drop recovery were checked.
  Blackjack hole cards stayed private; chip flight and RPS hand/speech artwork
  remained separate. The snack finale granted no food or satiety.
- Menu scaling and portrait/landscape screenshots were inspected. A complete
  browser close/relaunch offline retained the installed package and preference.
  No page errors or unexpected console errors occurred; the offline fetch
  produced the expected browser resource error.

The source [web check](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42036861043)
passed. The browser evidence establishes the exercised interactions, not Safari
frame rate or final visual acceptance on the iPad. The owner must recheck the
reported findings on the correction build; the device checklist remains open.

### Published correction and retained-save upgrade

The correction is live at the existing HTTPS origin/path. The
[`room-test-0.1.0-ff6d7142a7cc` release](https://github.com/Lexoniarus/aiko-desktop-pet/releases/tag/room-test-0.1.0-ff6d7142a7cc)
contains the reviewed site artifact; deployment commit `fcf579ca` pins its
SHA-256 `a1718030866466bad02e90cd76855f4ffa10509b1889be3b5363a6c87dd9e3eb`.
The [deployment run](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42037507463)
completed successfully.

A separate existing browser profile with the actual published a8 package and
durable state upgraded through the real HTTPS app's **Jetzt neu starten** flow.
The old runtime remained active while the complete correction package staged.
Restart retained the same World object identity and the zodiac preference
changed immediately before activation. The installed version was confirmed as
`0.1.0-ff6d7142a7cc`. A touch RPS choice produced exactly one game command,
revealed the original hand artwork and kept hand/commentary separate. Offline
reload reopened the published app with that preference and version, without
page errors. The existing Dropbox ZIP/profile needs no replacement. These are
browser results, not completion of the owner's actual-iPad acceptance.

## Walking, floor and feeding follow-up (2026-11-05)

The owner confirmed a clear improvement and acceptable normal character size,
but reported remaining floor joins, intermittent motion and feeding differences.
Runtime **0.1.0-3351f6ec864a**, source `3351f6ec864a`, addresses these findings:

- `RoomLocomotion` selects the existing body/step and compatible head banks,
  including quarter poses before travel. Step speed follows the native
  16-logical-pixel/620-ms cycle at room scale. Running clips are no longer used.
  Compatible walking variants retain their cycle phase; a short display buffer
  interpolates consecutive snapshots instead of restarting a movement ramp.
- All wall panels share one continuous floor and aligned skirting lines, with
  the balcony/curtain base preserved. Original PNG files are unchanged.
- A real World-owned user-held portion now exists during a drag. Finite move
  commands feed actual face-relative presentation into the existing perception,
  offer assessment and release-handover owners. Holding near the face can
  identify food before release; ready hands do not grant custody or intake.
- Unaccepted releases use the existing World fall/bounce/settle lifecycle,
  rather than immediate scripted landing. Cancel returns the same existing
  portion to its original location; a cancelled new portion supplies no food.
- Hand contact blends to the authored anchor over the same 130 ms used on
  desktop. Ordinary food stays in front of the character as in FoodOverlay;
  only the Connect Four pickup uses its deliberate hand mask. The original
  85-phase, three-bite meal and nutrition owner remain unchanged.

Checks ran only after implementation and without visible windows. Fifteen
portable room tests passed, including two new regressions for airborne release
and pre-release identification/handover. Forty-three existing pure
game/reaction/architecture tests and three Node checks passed. Production
starter/runtime/Service Worker build, Ruff and strict application Mypy passed;
repository Pyright reported zero errors/warnings. The native GUI suite was not
rerun. The source [web CI](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42045839035)
passed.

The target browser flow is: installed room -> touch-drag food into the air ->
release and fall -> pick up/cancel the same item -> hold another portion near
Aiko's face -> lower to her hands -> release -> original meal. Headless
Playwright exercised this with the actual production ZIP, Python/SQLite and
isolated storage; no synthetic offer command or pet-state mutation was used.
The Browser plugin was unavailable. Independent camera pans and native walking
were checked, including the absence of running clips and the observed step
speed. Screenshots cover airborne food, face presentation, ready hands, meal,
walking and the panorama joins. RPS hand/speech and portrait Connect Four
pickup/flight still worked. Full browser close/relaunch offline retained the
package, preference and item identity. No page errors or unexpected console
errors occurred; offline fetch failure was the expected browser resource error.

These checks do not establish Safari frame rate or close the actual-device
findings. Recheck floor transitions, movement, positioning and feeding on the
owner's iPad using this version. Normal character size was retained.

The follow-up is published as
[`room-test-0.1.0-3351f6ec864a`](https://github.com/Lexoniarus/aiko-desktop-pet/releases/tag/room-test-0.1.0-3351f6ec864a).
Deployment commit `643c0e44` pins site SHA-256
`972faab85d0d636809e84b2d7c9c0bfd8032bb10baf0d86daf60d9dd292d42d2`;
the [deployment run](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42046215574)
passed. The retained HTTPS browser profile upgraded from ff6d to 3351 using
the existing update/restart controls. The same World object IDs and a setting
changed immediately before restart survived. Published RPS accepted exactly one
touch choice and rendered its hand prop; the app reopened offline with the new
version and preference, without page errors. No new ZIP/profile or origin change
was used. Main and the resident desktop process/save were untouched.

## Foreground play area and pose correction (2026-11-05)

The next device report clarified the intended staging: Aiko and portable
objects should stay in front of the furniture, drops must remain possible at
the same horizontal position as furniture/other portions, and side walking
must use the real profile head. Build **0.1.0-e0fbaec47ab4** implements this:

- One shared foreground strip (`1.05`–`1.13` in canonical room depth) replaces
  the earlier furniture-footprint route graph. The backdrop no longer blocks
  placement or travel; all furniture is drawn behind Aiko/portable objects.
  The table sits further back. Old room depths are normalized on load, retaining
  object IDs, quantities and horizontal positions; subjective identity is not
  manufactured by this relocation.
- Ground pickup requires a distance of at most 18 room units. In an isolated
  real-session probe Aiko walked to a portion and acquired it at 13.83 units;
  this uses actual World custody and the normal interaction coordinator.
- Lateral travel selects `body-step-*-profil`, after the existing turn sequence.
  Survey/following uses the quarter-body look bank. Predominantly forward
  facing uses the existing quarter stance. The package contains no complete
  quarter-body forward step cycle, so this is directional posing, not a newly
  authored forward walking animation. Existing PNG assets are unchanged.
- Rectangular window brightening is removed. Continuous skirting now preserves
  original balcony/curtain contours instead of leaving a guessed rectangular
  opening beside the window.

Final checks ran without visible windows and after implementation: 17 portable
room tests, 43 existing pure game/reaction/architecture tests, three Node checks,
production build, Ruff, strict application Mypy and repository Pyright passed.
The source [web CI](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42049343599)
passed. No full native GUI suite was rerun.

The browser flow is: room -> drag over visible furniture -> release -> portion
falls to the foreground -> place another portion on an occupied position ->
normal pickup/feeding and game use. Headless Chromium/Playwright with actual
Pyodide/SQLite and isolated storage confirmed drops in front of the kitchen
unit, fridge, table, desk and bed at their actual horizontal coordinates.
Overlapping portions were accepted; cancellation retained the same identity.
Face presentation, ready hands, release handover, the native three-bite meal,
true profile walking, original RPS hands and portrait Connect Four props passed.
The final window/room screenshots were inspected. Full browser restart offline
retained the package, preference and objects. No page errors or unexpected
console errors occurred; deliberate offline fetching produced the expected
browser resource error. Browser plugin unavailable; headless fallback retained.

Actual iPad visual/motion acceptance remains open, particularly foreground
spacing, profile versus quarter posing, and the revised window transition.

Published as
[`room-test-0.1.0-e0fbaec47ab4`](https://github.com/Lexoniarus/aiko-desktop-pet/releases/tag/room-test-0.1.0-e0fbaec47ab4).
Deployment commit `7108f7a9` pins site SHA-256
`8591ad4b85f56ee17dc5e85b4fa1697dbd5cff6992a72d63c2407820a3246056`;
the [deployment run](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42049822073)
passed. The retained real HTTPS profile upgraded from 3351 to e0fb using the
existing update/restart controls, preserving object IDs and a setting changed
immediately before restart. Published RPS still accepted exactly one touch
choice; offline reload retained the new version and preference without page
errors. No profile/storage recreation was used. Main and the resident desktop
app/save remain untouched.

## Petting, finite animations and a simple room day (2026-11-05)

The owner clarified that the requested daily movement belongs to the room/iPad,
and also reported a held pose sliding/changing direction without a visible walk.
Build **0.1.0-6515ed307321** fixes the room presentation boundaries:

- Accepted petting uses the same care-result-to-animation mapping as the native
  presenter. The room had omitted the native presenter's explicit `petting`
  override. Refusal keeps the existing care decision and does not start petting.
- Normal one-shot reactions now clear their animation at the authored clip end.
  Previously their completion was sent only to the object coordinator, which
  cannot finish an unrelated care pose. Physical animation/effect timers now
  run independently of the unread-text clock. Hidden text still cannot earn
  presentation/completion, while a pose cannot remain frozen waiting for it.
- An active one-shot yields no walking display. Once it ends, actual movement
  selects the walking bank again. Already reached destinations settle before
  another turn is selected, avoiding turn attempts at a zero-length goal.
- `RoomLeisure` reuses the existing `AmbientDirector` for quiet look/quarter
  poses and head changes. Occasional outings are bounded to 650 room units,
  with 25–50 seconds of quiet between completed outings. Longer gaps between
  furnishings use intermediate stops. Quarter holds begin after the body has
  reached the pose; care/call/drag interrupt cosmetic routing. Actual object
  interactions retain their existing owners and take priority.
- No procedural pixel/head sway is applied. Leisure does not feed, read, play,
  change quantities, identify objects directly or grant care/friendship credit.
  The desktop pet's movement policy is unchanged; the native presenter only
  shares its previously inline visual mapping with the room.

Tests ran after implementation without visible windows: 20 portable room tests
passed, including three focused regressions for unseen petting completion,
visible post-care walking/arrival, and quarter holds yielding to care. Sixty-nine
existing pure care-presentation, ambient, game/reaction/architecture tests passed.
Three Node checks, production build, Ruff, strict application Mypy (390 files)
and repository Pyright passed. No full native GUI suite was run.

The browser flow is: touch petting -> native frames -> passive return -> call
and visible profile walk -> stop -> autonomous outing -> held quarter pose and
head change -> care interruption. Actual Pyodide/SQLite and isolated storage in
headless Chromium exercised it with real touch input. The off-camera petting
case ended its pose while its unseen text remained pending. Recorded moving
snapshots did not retain a prior one-shot animation; a finished route retained
its position. Screenshots show the petting hand, changed walk phases, quarter
hold and second head direction. RPS arm/reveal, Blackjack dealing/result and
portrait Connect Four pickup/flight remained functional. Drag/fall yielded
correctly; complete offline browser restart retained preference and portion.
No page errors or unexpected console errors occurred. Offline fetching produced
the expected browser resource error. Browser plugin unavailable; headless
Playwright fallback retained. Actual iPad animation/motion acceptance stays open.

The source [web CI](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42055055538)
passed for the final runtime source.

Published as
[`room-test-0.1.0-6515ed307321`](https://github.com/Lexoniarus/aiko-desktop-pet/releases/tag/room-test-0.1.0-6515ed307321).
Deployment commit `ecf61395` pins site SHA-256
`45bea898ac26408cc62feccb95f6005773706ace711c7a3b80b6bfcb8dbc6e64`;
the [deployment run](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42055681589)
passed. A retained real HTTPS installation upgraded from e0fb to 6515 using the
existing update controls. Object IDs and an immediately changed setting survived
restart. The published app showed petting and completed its pose, then accepted
one RPS touch choice. Offline reload retained the version and preference without
page errors. No profile/storage recreation was used. Main and the resident
desktop app/save were untouched.
