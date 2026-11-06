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


## Floor-grid preview, fixed furniture and retained-save upgrade (2026-11-06)

Verified runtime source: `0aef82356f357e93f8f67bdddf938e6e5c50f961`, package
`0.1.0-0aef82356f35`. This is a preview of the more spatial presentation, not
owner acceptance of that visual direction. The owner explicitly requires
kitchen, fridge and other furniture to keep their own room orientation.

All furniture cutouts now occupy fixed room faces, including the kitchen and
fridge; they do not billboard toward the view. Cropped alpha masks block picking
through visible furniture while allowing transparent gaps. The one floor is
clipped against the camera near plane: partially visible planks are retained,
rather than leaving the lower-edge holes found during screenshot review.
Authored character art was reused without regenerating or changing PNGs.

Final local checks, all after the implementation commits:

- 348 selected, headless Python regressions: World state/falling/persistence,
  object attention/perception/tracking/knowledge/absence/interaction/consumption,
  all SQLite boundary/migration modules, and room-session/grid scenarios.
  This is a targeted selection, not a claim that the complete native GUI suite ran.
- Four Node checks: floor projection round-trip at rotated bearings and relative
  size; near-plane floor clipping; admitted route-corner interpolation; package
  path/protocol validation.
- 21 existing architecture/boundary checks: dependency graph, UI ownership,
  pet movement/mind and animation timing/policy boundaries.
- Ruff across application, tests, tooling and balance tests; strict Mypy across
  432 application/tool source files; repository Pyright: no errors or warnings.
- TypeScript, production starter/runtime/service-worker build and GitHub
  **Shared room web** run `42245562415`: successful for the runtime source above.

Browser plugin not available. Used the installed Playwright Chromium headless
shell with software WebGL and isolated profile/storage; no visible windows,
resident desktop process or personal save was used. Local test origin:
`http://127.0.0.1:8893/room/`; viewports 1024x768 and 768x1024, with touch input.

The actual previous production package `0.1.0-6515ed307321` first created a
synthetic live save. The current starter downloaded the preview and applied
**Jetzt neu starten** to the same IDBFS database. Schema 6 -> 7 retained live
portion IDs, zodiac and pet values, allowing only genuine elapsed progression.
A separate SQLite fixture also proves the automatic schema-6 backup, exact pet
checkpoint preservation, independent remembered-position migration, stable
reopening and rejection of an older schema reader.

Actual touch flows passed: camera following, swipe releases following, fixed
furniture at different bearings, conditional Find, need cards, wish cards,
removed room-size selector, supply drag with a raised release and real fall,
original RPS choice/artwork, native petting, and offline reopening with retained
live object IDs/settings. Visible images were awaited before capture. Page
identity/nonblank content, no framework overlay, image loading and interaction
results were checked; no JavaScript page errors. Expected console resource
messages were limited to the deliberately absent initial update descriptor
and the intentionally disconnected network during offline checks.

The isolated QA script, screenshots and browser profiles stay outside Git under
`%TEMP%/aiko-room-grid-qa/`. Generated runtime/installer/site ZIPs and checksums
are under ignored `dist-room/grid-final/`; no save/profile data enters them.
Physical iPad acceptance and complete forward/backward character step assets
remain open, as described in `IPAD_ACCEPTANCE.md`.

Published test release:
[`room-test-0.1.0-0aef82356f35`](https://github.com/Lexoniarus/aiko-desktop-pet/releases/tag/room-test-0.1.0-0aef82356f35).
Deployment commit `b76f47bafbb57f07eb28977566835f0170829e1e` pins starter
SHA-256 `b47dd0b33a03230bda14a494de4662a5c31415f979f4568b31b4a9362079045f`.
The [deployment run](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42247193246)
completed successfully. The live HTTPS `install.json` exactly matched the local
descriptor for version `0.1.0-0aef82356f35`; live `index.html` and `sw.js` also
matched the built files byte for byte.

A separate fresh, isolated headless HTTPS installation then downloaded the
published version, reported geometry 2, accepted touch petting and retained a
changed zodiac setting through an offline reload. No JavaScript page errors.
Evidence is `live-result.json`, `live-grid.png` and `live-offline.png` in the
same external QA directory. This verifies delivery and offline reopening in
Chromium; physical iPad/Safari visual and interaction acceptance remains open.
Main, the resident desktop app and the owner's actual save were untouched.

## Flat 2D panorama over the retained grid (2026-11-06)

Runtime source `7cafd21e2a35b4bef5364229c78cacf5b211025d`, package
`0.1.0-7cafd21e2a35`, replaces the rejected perspective preview with flat wall
panels and proportion-preserving furniture sprites. Swiping translates art;
camera yaw never changes its width, height or vertical position. Physical floor
coordinates, footprints, A* routing, transport protocol 2 and SQLite schema 7
are retained without another migration. The inverse panorama projection handles
floor drops and raised drags using those same coordinates. The now-unused
gl-matrix dependency was removed.

Ten prepared profile walking images from `2026-11-06-profil-geh-hals-vorschau`
were copied only after checking their manifest's source and output SHA-256.
Private originals were preserved. Their neck corrections and per-step head
registration are recorded in the committed `profile-walk-2026-11-06.json`;
other character art and the existing 620ms playback cycle are unchanged.

Final checks, after implementation:

- 36 existing Python checks: body-pose and character catalogs, room grid and
  room session. No Tk/native windows were opened.
- Four existing Node checks, adapted in place for the new projection: ground
  and elevated round-trips across four directions, size/depth behavior, stable
  art dimensions and height across panorama wrap, held-height recovery, route
  corner interpolation and installer validation.
- TypeScript production build, Prettier and diff whitespace checks passed.
  [Shared room web CI](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42251675611)
  passed for the exact runtime source.

Browser plugin not available; used installed Playwright Chromium headless shell
with software WebGL, touch enabled, and isolated storage. Target flow:
`http://127.0.0.1:8893/room/` -> import the real 0aef preview -> use the actual
online updater/restart -> retained grid save in the flat renderer. Settings,
live object IDs and pet values survived; no schema change was needed. Actual
touch supply dragging, lifted release/fall, follow/swipe release, conditional
Find, needs/wishes, original RPS, petting and offline reopening passed at
1024x768 and 768x1024. An additional retained-profile touch sweep captured all
four panels and joins, including bed, desk/plant, kitchen/fridge and table.

Page identity and meaningful content, image completion, no framework error
overlay, screenshots and interaction results were checked. No JavaScript page
errors. The update harness's expected resource messages were limited to its
deliberately disabled initial update descriptor and the deliberate offline
check. Screenshots and scripts stay outside Git in
`%TEMP%/aiko-room-flat-qa/`; `result.json` records the retained-save flow.

The more spatial renderer is superseded, not an optional visual default.
Artwork seams between the two original wall backgrounds remain visible; the
shared skirting and floor edge remain level. Actual iPad/Safari visual acceptance
is still open. Main and the owner's running desktop pet/save were untouched.

The immutable test release
[`room-test-0.1.0-7cafd21e2a35`](https://github.com/Lexoniarus/aiko-desktop-pet/releases/tag/room-test-0.1.0-7cafd21e2a35)
contains the installer, starter site and direct runtime ZIP. GitHub confirmed
the runtime upload (86,888,454 bytes) and SHA-256
`84bb2cee3bc4b8ef93428c6244fc88ad5097164d1d4acf7275ae42d7acdfd489`.
A ZIP-to-ZIP comparison proves exactly the ten intended profile PNGs changed;
all other packaged PNGs match 0aef. The starter site SHA-256 is
`7b2cd8832f297a856ea35e9609612ec1fa6726f685a9a09432818ace908bfb51`.

**Publication is blocked, not live-verified.** Pages run
[`42253263202`](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42253263202)
timed out in `updating_pages`; its retry encountered duplicate artifact names.
Fresh run `42255542889` reused the cancelled deployment revision and was
cancelled. A separate CI fix gives upload and deployment the same
attempt-specific artifact name. It was applied to source (`bad0977d`) and
deployment (`a629c647`). The resulting fresh
[`42256011899`](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42256011899)
passed artifact selection/upload but again timed out in Pages `updating_pages`.
The public descriptor still returned `0.1.0-0aef82356f35` at the final check.
Do not describe the new room as available through the installed app's updater.

An additional isolated **Einstellungen -> Paket aus Datei importieren** flow
retained settings and object IDs (`manual-result.json`). However, a second real
flow serving the *old* online descriptor confirmed that the existing starter
stages that old package again after the manual import. Version inequality alone
does not establish release order. This is a pre-existing updater limitation,
not a reason to change room coordinates or pet behavior. An online manual-import
workaround is therefore not recommended while the feed is stale. No production
profile was used or changed in either check. The direct ZIP is a prepared
artifact, not proof of a safe online production upgrade during this blockage.

## Pages delivery recovered and retained HTTPS save verified (2026-11-06)

The publication blockage above is resolved. The pinned runtime remains
`0.1.0-7cafd21e2a35`; no pet, geometry, save-schema or character changes were
made during this recovery.

Diagnosis localized the failure to Pages' server-side publication step:

- Successful and failed runs used identical SHAs of all six GitHub Actions.
  The failing artifact was accepted, selected unambiguously and passed download
  hash validation before a deployment ID was created.
- The new starter site has nine files totaling 87,022,821 bytes, compared with
  173,920,832 bytes in the last successful site. Both pinned ZIPs passed CRC and
  SHA-256 checks; neither has an individual file above 100 MB or unusual entries.
- The failed Pages records reported `deployment_cancelled`; the public site
  continued serving 0aef. No domain or source misconfiguration was found.

The two failed Pages deployment IDs (`cbe2a071...` and `a629c647...`) were
explicitly cancelled through the supported Pages REST endpoint. A fresh run
then deployed the **same pinned site ZIP** successfully in 106 seconds. This
supports a stuck Pages publication-state diagnosis; GitHub's internal cause is
not exposed by its status endpoint. The result does not establish a general
GitHub outage. No Pages site deletion/recreation, publishing-source switch,
environment reset, URL change or browser-storage clearing was performed.

A separate deployment fix (`af317e0b` in source, `b4c8fa22` in deployment) adds
`scripts/verify_room_deployment.py` as a required final workflow step. It waits
for the expected public descriptor, compares the live starter HTML/service
worker byte for byte, and downloads the runtime to check its size and SHA-256
against the reviewed ZIP. A stale or mismatched publication now fails CI.
Ruff, formatting and strict Mypy passed for the new script; the actual public
verification succeeded both on GitHub and locally.

The [deployment run](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42260645693)
is green, including the public-files gate. The
[source web CI](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42261653186)
is also green for the deployment-verifier change. The live descriptor advertises
`0.1.0-7cafd21e2a35`; the complete downloaded runtime matches SHA-256
`84bb2cee3bc4b8ef93428c6244fc88ad5097164d1d4acf7275ae42d7acdfd489`.

Before the fresh publication finished, an isolated headless Chromium profile
installed the actual previous production version at the real HTTPS origin
`https://lexoniarus.github.io/aiko-desktop-pet/room/`, set zodiac `virgo`, placed
an apple outside the actor's sight, and durably suspended its synthetic save.
After publication the same profile used **Einstellungen -> Nach Updates suchen
-> Jetzt neu starten**. It upgraded from 0aef to 7cafd while retaining the zodiac
and live object IDs. Touch petting completed, no old pending package remained,
and an offline reload retained the new version and the same saved IDs/settings.
Page identity, meaningful content, screenshot/image loading and absence of
JavaScript page errors were checked. Browser plugin unavailable; existing
Playwright headless shell/software WebGL was used at 1024x768 with touch.

Evidence remains outside Git in `%TEMP%/aiko-room-flat-qa/`:
`deploy-baseline.json`, `deploy-upgrade-result.json`, `deploy-before.png`,
`deploy-after.png` and `deploy-offline.png`. No personal iPad save was read,
changed or uploaded. Actual iPad visual/device acceptance remains the owner's
next check. Main and parallel desktop asset work were not modified by recovery.
