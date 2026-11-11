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

## Single-window and four-wall picture calibration (2026-11-06)

Runtime source `a4e8069e75f44e9f955b01d71329ef85e9c1a1f3`, version
`0.1.0-a4e8069e75f4`. The owner explicitly selected **keep the current furniture
distribution across four walls**. The correction therefore changes presentation
and the west wall's background asset, not the placement of world furniture.
A comparison with the preceding layout confirmed every furniture record,
footprint, mounting height, grid dimension and revision is unchanged. Geometry
version 2, protocol 2 and SQLite schema 7 remain unchanged; no migration or
personal save access was needed. Character and room PNGs were not modified.

The duplicated window came from using `living` artwork on both east and west.
West now uses neutral art; exactly one wall (east) uses the window image.
The other mismatch came from applying angular/radial screen placement and
generic logical heights to a four-panel picture. Wall-linear chart coordinates
now agree at room corners and map floor positions, camera following/calling and
touch placement consistently. Original full-height backgrounds retain the 802px
floor seam. Ground-foot height controls painter order.

`RoomPresentation.ts` owns the v16 cutout widths independently of collision-box
dimensions, shelf picture mounting and corner overhang/orientation. Door, bed,
table and shelf anchor/size assertions use explicit reference values. Nonblocking
wall-mounted artwork stays on its exact attachment point. Bed and plant pictures
stay within their wall joints; the bed headboard faces the near corner. The
window-frame restoration is bounded to its own opening so cool wall pixels do
not create a false strip at the skirting. `RoomBackground.ts` assembles the
unchanged source images; no new drawing or perspective mesh was introduced.

Final local checks:

- 36 targeted existing Python checks (character/body asset catalogs, room grid
  and session) passed without native windows.
- Five focused Node checks passed: round-trips including lifted positions and
  both sides of a corner, one east window, explicit picture dimensions/mounts,
  corner containment, panorama wrap, route interpolation and package validation.
- TypeScript/production build, Prettier and diff whitespace checks passed.
  [Source web CI](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42266448363)
  passed for the exact source above.

The actual previous 7cafd package created an isolated local save, which upgraded
through the real starter/update/restart flow to this package. IDs, settings and
pet progress were retained. Touch food dragging used the visible floor and
produced a raised release/fall with the same portion; camera following and swipe
release, Find, needs/wishes, original RPS, petting and offline reopening passed.
The narrower restored 2D floor uses a 24-design-pixel release offset rather than
a fixed large world height. All screenshots were captured from the installed
runtime after image loading, not a mock layout.

Browser plugin unavailable; existing Playwright Chromium headless shell with
software WebGL was used at 1024x768 and 768x1024, touch enabled. Additional
cardinal-wall views at 1800x900 show each complete panel and its corner cutouts.
Page identity/content, absence of an error overlay, image loading and interaction
results were checked. No JavaScript page errors. Expected resource messages were
limited to the deliberately disabled initial update descriptor and the offline
network check. Evidence stays outside Git in `%TEMP%/aiko-room-wall-qa/`:
`result.json`, `wall-{north,east,south,west}.png`, corresponding `-full.png`
views, care/drag/game screenshots and isolated browser profiles. Generated ZIPs
and checksums are under ignored `dist-room/wall-calibrated-publish/`.

### Cached-starter update ordering and publication recovery

The final code adds runtime-owned update ordering in source `a4159a00e702985ba6a71dba6e0ec83fef004db2`,
package `0.1.0-a4159a00e702`. Six focused Node checks, the production build,
Ruff and strict Mypy for the package builder passed. The exact
[source web CI](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42270907054)
passed. Package manifests carry the source commit timestamp; the runtime takes
ownership through the cached starter's public update methods. Older hosted
packages cannot silently replace a newer imported runtime.

An isolated profile actually ran the unchanged 7cafd starter (`index-CjUiuH0a.js`),
imported the a415 runtime through its file input, and continued receiving the
older 7cafd online descriptor. The retained object IDs and zodiac survived the
import, online reload and offline reload. No rollback/pending package or
JavaScript page errors occurred. Evidence is
`%TEMP%/aiko-room-wall-qa/manual-safe/legacy-manual-result.json` and its offline
screenshot. No personal save was accessed.

The first a4e Pages publication and two operational retries failed after artifact
upload, while Pages reported deployment failure without its internal cause.
Explicit cancellation and a backed-up recreation at the same URL did not make
those attempts succeed. A rollback to the unchanged last-known-good 7cafd site
then passed, including the public checksum gate, in
[run 42270245318](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42270245318).
The source/configuration and prior site archive were backed up outside Git.
No browser storage was cleared. This does not establish a general GitHub outage
or prove which internal Pages condition failed.

The subsequent final a415 publication succeeded in
[run 42271808025](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42271808025),
deploy commit `149f854280a86f8d97f1b25fa864580d540f2be6`, including the public
descriptor/starter/runtime verification gate. The published runtime ZIP SHA-256
is `3608b3d2ee249439663bbba30a757d0513b1a510f1c709b8974bd6e5a77809e5`;
the starter ZIP is `e783052332155130a8e75945b3708b898e72e68b9fd8be9f5130b258355e5038`.
The direct runtime ZIP is also attached to the test release for file import
through the existing app, without changing the profile or storage origin.

After the gate passed, the existing isolated profile at the real production
HTTPS origin upgraded from 7cafd to a415 through Settings -> Check for updates
-> Restart. Its object IDs and zodiac remained intact, touch petting worked,
no stale pending package remained, and offline reopening preserved the same
version and saved data. JavaScript page errors: none. Evidence is
`%TEMP%/aiko-room-wall-qa/deploy-upgrade-result.json`, `deploy-after.png` and
`deploy-offline.png`. The owner's real iPad visual acceptance is still pending.

## Connect Four at the existing room table (2026-11-07)

Runtime `0.1.0-7a0517e5f24a`, source
`7a0517e5f24aae4327e5a1d2f90fc6f608416391`. Table furniture/layout, room geometry
2, protocol 2 and SQLite schema 7 remain unchanged. The source was built from an
isolated clean checkout; parallel unstaged character-asset edits were excluded.
No personal save was read or altered. Existing desktop game code/rules and PNGs
were not changed.

The room walks to a reachable near-side table spot before starting the existing
ConnectFourSequence. Preparation is transient and cancellable. One board-space
diameter controls its supply, held chip, arc, fall and settled pieces. One moving
image changes painter layer at entry rather than changing size or handing off to
another differently scaled image. Direct column taps, drag entry/landing previews,
invalid-drop return and pointer-cancel cleanup replace the numbered button row.
Speech sits above the playfield and the room camera remains swipeable outside
chip gestures. Game text/control zoom is capped at 125%; board geometry does not
change with the separate menu setting.

Final checks, run only after implementation, without visible windows:

- 26 Python checks in `tests.test_room_session` and `tests.test_room_grid` passed.
  New coverage exercises the real route around occupied furniture, deferred
  start, close/suspend cancellation and retained World objects on reopen.
- Seven Node checks passed, including chip geometry/continuous arc-to-entry,
  direct-column boundaries and full-column preview rejection.
- TypeScript/production build, Ruff, Mypy for changed Python sources, Prettier
  (Windows checkout line endings accepted) and diff whitespace checks passed.
- [Exact-source web CI](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42388732562)
  passed.

Browser plugin not available; existing Playwright headless Chromium with software
WebGL was used, with real CDP touch at 1024x768 and 768x1024. An isolated profile
installed the prior a415 runtime, stored zodiac/World objects, then upgraded by
the normal check/restart flow to this package. Drag/tap, invalid drop, touch
cancellation, camera swipe after release, close during Aiko's turn, portrait,
175% menu size and offline reopening passed. Object IDs/settings were retained.
Drawn drag/flight/fall/settled chips measured 24.584px in the landscape fixture,
within 0.001px of the shared diameter. Held-chip sizing is controlled by that same
frame diameter in the renderer; held and flight screenshots were inspected.

Initial rendered checks exposed an offscreen/occluded partner and speech over
the board. The final play spot/framing and speech placement correct both in the
reviewed cardinal/portrait shots. The initial large-menu test attempted a covered
toolbar button while Settings remained open; the final flow closes Settings
through its visible close control before opening the game.

Page title/content, image loading, absence of framework overlays and JavaScript
page errors were checked. Only expected missing initial update-descriptor and
deliberate offline-network messages were recorded. Evidence is outside Git in
`%TEMP%/aiko-room-c4-qa/`: `result.json`, `table-ready-landscape.png`,
`table-ready-portrait.png`, `table-drag-preview.png`, `table-aiko-held.png`,
`table-aiko-flight.png`, `table-aiko-fall.png` and `table-large-menu.png`.
Actual iPad visual/touch acceptance remains pending.

The final package is published in
[the test release](https://github.com/Lexoniarus/aiko-desktop-pet/releases/tag/room-test-0.1.0-7a0517e5f24a).
[Deployment 42388946229](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42388946229)
passed including the public descriptor/starter/runtime checksum gate. The runtime
ZIP SHA-256 is `cf070b73ae38c05439f71de309e4767324cef0e49fe7735d748b18bae7217923`;
the starter SHA-256 is `14294dc49b0ebc379fd2feeb4d96df6fd292a0cdf03ef1e70c8fb09ba166e11d`.
The existing icon/profile/update address is unchanged. A direct runtime ZIP is
also available in the release for the existing app's file-import path.

The existing synthetic profile at the real production HTTPS origin then upgraded
from a415 to 7a0517 through Check for updates -> Restart. Retained object IDs and
zodiac `virgo` survived. The table scene and seven direct targets loaded; closing
during preparation removed the scene without a late game. Touch petting and an
offline reload passed with no stale pending package or JavaScript page errors.
Evidence: `%TEMP%/aiko-room-c4-qa/deploy-upgrade-result.json`, `deploy-after.png`
and `deploy-offline.png`. This profile contains no personal iPad save.

## Transparent openings and foreground placement correction (2026-11-07)

The owner rejected the white empty-hole backing and rearward board/supplies.
Runtime `0.1.0-b2533d858c96` removes the backing, moves the board towards the front
of the existing tabletop, and puts both supplies on the floor. `PetScreenBounds`
now exposes the stable actor ground anchor; the red stack no longer follows its
pose-image origin. Geometry, save schema, game rules and PNGs are unchanged.

Production build/typecheck, seven existing Node checks and Prettier passed after
the changes. Python was not rerun because no Python code changed. The existing
headless touch flow upgraded a synthetic saved 7a0517 installation to this
package, verified dragging/tapping/cancellation/invalid drops, constant chip size,
camera swipe, both orientations, 175% menus and retained offline objects/settings.
No JavaScript page errors. Expected initial descriptor 404 and deliberate
offline-network messages only. Source web CI
[42389431909](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42389431909)
passed for the exact source.

The rendered empty board was compared to an immediately captured room-only view:
five centre pixels in each of all 42 openings matched the background exactly.
Final landscape/portrait screenshots were visually inspected; board feet rest
on the forward tabletop and both supplies on the floor. Evidence stays outside
Git in `%TEMP%/aiko-room-c4-placement-qa/`: `result.json`,
`transparency-result.json`, `table-background-landscape.png` and the corresponding
table, pickup, flight/fall and portrait screenshots. Real iPad/owner visual
acceptance remains pending.

The correction package is available in
[the b2533d test release](https://github.com/Lexoniarus/aiko-desktop-pet/releases/tag/room-test-0.1.0-b2533d858c96).
Its direct runtime ZIP can be imported through the existing app/profile. Runtime
SHA-256: `665bf09c28ba2bd055a5d99690909f4aee17c475cfabb559c085827c18f8d884`;
starter SHA-256: `7dc73613ec1342869e89ae55f7d4709f65ccb65c017134aed5e3d30903fe198b`.

## Repeated Pages timeout investigation and prevention (2026-11-07)

The owner requested a concrete comparison rather than another blind rerun.
Actions job logs and actual uploaded `artifact.tar` contents were inspected:

| Attempt | Artifact / Pages identity | Observed publication result |
| --- | --- | --- |
| 42388946229 | 7a0517 site, 86,904,921-byte Actions ZIP | Created 15:58:58 UTC; success 15:59:03. |
| 42389629791 attempt 1 | b253 site, 86,904,911-byte Actions ZIP; 722e1f97 identity | `syncing_files` until ten-minute timeout; action cancelled Pages. |
| 42389629791 attempt 2 | Same reviewed b253 site and same 722e1f97 identity | Empty status from first poll for over five minutes; explicitly cancelled for diagnosis. |
| 42391066779 | Same pinned b253 starter/runtime, fresh 0425bd46 identity | Created 16:23:56 UTC; success 16:24:01; public runtime verified 16:24:03. |

Both downloaded Actions archives passed ZIP CRC and TAR inspection: nine regular
site files, no symlinks/hardlinks/path traversal, normal 0644/0755 permissions and
the same owner. All starter/icon/HTML/SW bytes were identical; only install.json
and the runtime ZIP differed. The failed runtime was 27 bytes smaller. Upload
and Pages-create authorization succeeded. The exact resolved action SHAs were
identical on success/failure. Neither a malformed artifact, retry selecting the
wrong artifact, an action-version change nor a size-limit breach explains this
comparison. Large packages remain an operational cost, not a proven root cause.

The first stall is inside Pages synchronization; its internal cause is not
exposed. Same-SHA retry reused its identity and returned empty status, while a
fresh identity published the unchanged reviewed site in about five seconds.
This supports avoiding that retry path, not a claim that new commits cure every
Pages backend failure. Earlier queued/deployment_failed incidents are a distinct
recorded failure mode. GitHub's public status was operational during this check;
no general outage is asserted. The pinned action itself clamps timeout at
600,000ms and does not treat an empty status as an immediate terminal failure.

Prevention is implemented in source `80c90cfd` / deploy `282e81e7`:
`check_room_deployment.py` checks existing public files and deployment history
before configure/upload/deploy. Already-live sites skip publication but retain
the full live ZIP checksum gate; previously attempted unhealthy identities fail
before upload. Empty API status alone is insufficient: even never-deployed SHAs
return it, so the guard inspects actual workflow steps across attempts. A
15-minute whole-job bound is separate from the unchanged ten-minute Pages limit.

Validation ran after implementation, without visible windows. Ruff and strict
Mypy passed for preflight/verifier. Read-only real-API cases passed: already-live
site skips (0.92s), stale identity rejects (0.99s), fresh identity permits (1.47s),
and actual old workflow history identifies a prior Pages attempt. No tests for
tests or broad pet/game suite were added/run for this deployment-only change.
[Web CI 42391696100](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42391696100)
passed. The actual
[deployment workflow 42391700248](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42391700248)
passed twice on the same commit: preflight succeeded, configure/upload/deploy
were skipped, and the public runtime digest was fully verified both times.

The real HTTPS synthetic profile retained b253, zodiac and object IDs through
offline reopening with no stale pending package or JavaScript errors. Its energy
had fallen to 7.35 after absence, so the attempted live game start was correctly
refused; that fixture is not used to claim a live game-admission pass. Full touch
gameplay was already verified in the isolated local fixture above. No personal
iPad save was accessed. Evidence remains outside Git in
`%TEMP%/aiko-room-c4-placement-qa/`: artifact comparison, fetched job logs,
`preflight-result.json` and `live-save-result.json`.

A separate browser feasibility probe from the real Pages origin could read
public Release metadata but could not fetch either the asset API download or
browser-download URL. Therefore simply pointing the existing fetch importer at
GitHub Releases has not been established as an automatic fallback. No alternate
hosting, new origin, profile reset or runtime transport migration was introduced.

## Corrected gaze and foreground ground pickup (2026-11-07)

The owner reported old turn/up-down art, pickup behind ground food and portions
being pulled to the hands. Source commits `2d85535f`, `935fa49f`, `f78a9110` and
`e1c10527` adopt the existing 20 corrected images, require a free observer-side
contact station, remove the web floor-to-hand interpolation and cover the new
contact contract. Native pickup rendering and shared custody/nutrition ownership
are unchanged. Save format and origin remain unchanged.

All 40 targeted room/session/grid/character/body-pose test methods passed across
the batch and focused rerun. The new hungry-ground-food regression checks the
initial behind-item position, stationary portion before the pickup marker,
foreground arrival, single acquisition/consumption and durable nutrition with
no consumed-item respawn. The second new method checks four wall bearings and
an obstructed foreground station. Two test-fixture assertions were corrected
during final verification; no additional behavioral edits were needed. Ruff and
strict Mypy passed for the changed Python paths; TypeScript/Vite and seven
existing Node tests passed. No full desktop suite or visible native test window
was run. Exact-source
[web CI 42395468509](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42395468509)
passed.

Headless Chromium with touch input installed the previously published b253 ZIP,
saved a stock item and Pisces setting, then installed the final
`0.1.0-e1c105270b98` update through the normal settings controls. Both survived.
A real supply drag released one apple at `(450.0054, 134.9822)`. It stayed at that
position throughout approach and initial pickup; acquisition occurred only at
the foreground station `(444.4611, 151.8308)`, at the original animation marker.
Inspection used the source food anchor/mask without the removed attraction.
Landscape/portrait screenshots were inspected. Offline reload retained both
object IDs and settings, with no page errors. Diagnostics contained two 404s
during isolated manual bootstrap and an offline network request; the descriptor
was deliberately withheld until the update step. All 20 corrected source PNGs matched the final runtime archive
byte for byte. Evidence stays outside Git in
`%TEMP%/aiko-room-feeding-contact-qa/`: `result.json`, `observations.json`, and
supply/approach/contact/inspection/portrait screenshots. Real iPad visual
acceptance remains pending; no personal save was accessed.

Package runtime SHA-256:
`88df2e94ee5f8ac2b05fd2d840885661ccd8b683cee4a0c671516e02f3594fe5`;
starter SHA-256:
`7eed2c714834295bdc855b19e8e4741d01495d60acc0c84696c61dfc6f50e1d9`.

[The test release](https://github.com/Lexoniarus/aiko-desktop-pet/releases/tag/room-test-0.1.0-e1c105270b98)
includes the installer, direct runtime ZIP and pinned starter.
Deploy commit `cbedfba5` and
[publication run 42395824952](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42395824952)
passed: the fresh publication identity was allowed, Pages deployed in about six
seconds, and the public descriptor, starter and full runtime checksum matched.
The existing `/room/` origin and profile remain in use.

## Fixed food line and same-cell occlusion (2026-11-07)

The owner's follow-up separated drawing order from approach position: Aiko must
be behind a ground object on its cell or a farther cell, while player food drops
must use one line/scale instead of choosing depth from pointer height. Commits
`efba6f34`, `4cec135b`, `9b74d0ce`, `45fa68e7` and `42da08c1` implement the explicit
same-cell drawing priority, layout-owned food line, regressions and shared release
path including declined/timed-out offers. No existing ground object is migrated;
cancel restores the old place. Books retain free placement, Aiko retains free
depth/scaling, and native desktop rendering/custody/nutrition remain unchanged.

Thirty targeted Python session/grid test methods passed in the applicable
batches/focused rerun; the final session batch passed all 26 methods. The only
new geometric assertion correction was floating-point tolerance for repeated
projection. Coverage includes old off-line food through suspension/reopen/cancel,
new drop persistence, four wall bearings, source-marker pickup/consumption,
successful direct handover and refused/unfinished offer release. Ruff and strict
Mypy passed for the changed Python paths. TypeScript/Vite and all nine Node tests
passed, including behind/same/front cell order, invariant food-line scale and
height-only vertical dragging. Exact-source
[web CI 42398038938](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42398038938)
passed. No full desktop suite or visible test window was run.

Browser plugin not available: the final package was exercised with the existing
headless Playwright/Chromium setup at `http://127.0.0.1:8897/room/`, with real touch
events, landscape 1024x768 and portrait 768x1024. The flow was old e1c105 runtime
installation, saved stock/settings, normal in-app update to
`0.1.0-42da08c1d5ba`, vertical supply drag/drop, same-cell crossing, pickup and
offline reopening. Both old object coordinates/depth and Pisces were unchanged
after update. The portion's touch-ghost width was 59.859375px at both heights;
its floor point stayed constant and only height changed.

Pixi's existing application-init hook exposed the actual scene without modifying
served runtime bytes. On the same cell, Aiko's ground order was 733.94845 and the
apple's 733.95845 (child indices 22/23), even though the actor was slightly nearer
within the cell. The screenshot shows the apple covering her feet. It stayed at
`(452.5537,126.5728)` until pickup at `(447.3681,143.7052)`. Offline reopening kept
both original/new object IDs. Evidence stays outside Git under
`%TEMP%/aiko-room-food-line-qa/`: `result.json`, `observations.json`,
`same-cell-item-front.png`, supply/contact/inspection/portrait screenshots.

| Rendered check | Result |
| --- | --- |
| Intended route / meaningful app | Local room route, installer/update controls and room toolbar loaded. |
| Blank page / framework error overlay | None in the inspected landscape/portrait screenshots. |
| Console health | No page errors; two bootstrap 404s while descriptor withheld, plus expected offline network failure. |
| Interaction | Real touch y-only drag, fixed scale/point, floor fall, same-cell draw priority and original pickup marker passed. |
| Save / offline | Existing coordinates, IDs/settings survived update; offline reload retained both portions. |

Final runtime SHA-256:
`7c39bd39d736d747003461b46aa11708a85dff1abade5aee1a707f2adb672f64`;
starter SHA-256:
`cf10f3f8d82c7563e3560820576c7b68420295b2d848e10db6b721065b813328`.
Actual iPad/Safari visual acceptance remains pending. No personal save was read.

[The final test release](https://github.com/Lexoniarus/aiko-desktop-pet/releases/tag/room-test-0.1.0-42da08c1d5ba)
is pinned by deploy commit `2649bf7f`.
[Publication run 42398259255](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42398259255)
passed, including fresh-identity preflight and the full public runtime checksum.
Pages deployed in about eight seconds. The public `/room/` origin/profile remain
unchanged; use the installed app's normal update controls.

## Touch selection containment (2026-11-10, local only)

Frontend commit `0ba4f1c6` contains browser selection and long-touch callouts at
`.aiko-room`, restores native selection/callouts for inputs, textareas, selects
and contenteditable elements, and disables native image/link dragging. Existing
`touch-action` rules, pointer handlers, panel scrolling and viewport zoom policy
are unchanged. The Safari-specific properties follow Apple's
[Safari CSS reference](https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariCSSRef/Articles/StandardCSSProperties.html).

TypeScript, both Vite builds, service-worker build, all nine existing Node tests,
CSS formatting and the focused diff whitespace check passed. No redundant CSS
source-string tests or Python runtime changes were added for this fix.

Browser plugin not available: headless Playwright/Chromium ran at
`http://127.0.0.1:8901/room/`, at 1024x768 and 768x1024 with actual touch events.
An isolated QA-only package combined the newly built frontend with the unchanged
Python/assets from `0.1.0-42da08c1d5ba`; parallel Python communication work and
personal saves were excluded. This package is not a release or deployment.

| Rendered check | Result |
| --- | --- |
| Page identity / meaningful content | `Aikos Zimmer`, room toolbar and real settings/food panels loaded. |
| Blank page / framework error overlay | None; landscape drag and portrait settings screenshots inspected. |
| Console health | No page errors, warnings or console errors. |
| Selection boundary | Old behavior reproduced with selection restored; current CSS prevented double-click and mouse-drag text selection. Text outside the room remained selectable. |
| Native controls / editors | Input and textarea selection/replacement, contenteditable and nested editable spans, plaintext-only editing, checkboxes, selects and source-link navigation passed in a separate fixture using the actual room CSS. Native image drag did not start. |
| Touch interaction | 850ms hold then room swipe changed the rendered scene without selection; hold then food supply drag/drop completed. Panel scrolling from its explanation text and native settings changes passed. |

Evidence and temporary scripts are outside Git under
`%TEMP%/aiko-touch-qa/`: `result.json`, `chromium-editing.png`,
`landscape-food-drag.png` and `portrait-settings.png`. The installed WebKit
revision 2311 differs from the current Playwright driver's expected 2370; no
WebKit pass is claimed. Chromium cannot prove iPadOS callout suppression,
selection handles or native keyboard/copy-paste behavior. Actual Safari and
Home Screen acceptance remains pending as listed in
[the device checklist](IPAD_ACCEPTANCE.md#touch-selection-and-editing-acceptance).
Nothing was pushed, released or deployed for this change.

## Android/POCO preparation (2026-11-10, local candidate)

The next major branch work block is A1 in the overall plan. Commits `edd6efaf`
and `ca6302dc` prepare the same mobile PWA for iPad and Android: device-neutral
starter text, explicit Chrome/Safari build targets, a Settings device-report
download, Android install/manual-import instructions and a separate POCO
acceptance sheet. No separate Python simulation, save format or Android renderer
was introduced. Diagnostics record actual browser/viewport, package/runtime
identity and read-only persistence/quota observations. Room-ready startup time
is captured once, rather than growing until the report button is pressed.

Phone verification reproduced enlarged Settings panels outside the portrait
viewport at 175%/200% (393x873 CSS pixels; top positions -465.75/-657).
Commit `fcc45434` corrects zoom-adjusted phone panel limits/insets, permits header
wrapping, keeps the body scrollable and gives short-landscape panels usable
height. Quick-care controls can wrap. It retains the configured UI size and
leaves room positions, assets, saves and game rules unchanged.

Final local candidate: **`0.1.0-fcc4543432ed`**, source
`fcc4543432ed54471164dc417ed492fcb45499bb`, under
`dist-room/android-poco-ready/` (ignored generated files). Runtime size is
86,816,450 bytes with 1,169 manifest-listed files. Runtime SHA-256:
`adb6d89335644903285d589c9f513ef5c0b5bc3f6e6cdff220d15bcd2a85e94a`.
Starter SHA-256:
`5558e432a42a7a34b5480271d3b45b8067da4aa81e822f0eaa76f1739db613db`.
CRC, every runtime file size/hash, descriptor/manifest, bundled pathfinding wheel,
identical runtime embedded in the starter and delivered Android documents passed.
No private save, source-art job or original reference archive enters the runtime.

Rebuilding used a private deterministic ZIP of the ten preserved, extracted v16
room images. All ten were byte-compared to the previously shipped `42da08c1`
runtime. Its `prototypeSHA256` identifies this reconstructed build input, not the
original delivery archive. Provenance/hashes stay in the external QA folder;
the preserved images and character artwork were not modified.

Validation commands: `npm --prefix web run build`, `npm --prefix web test`,
Prettier check on changed web files, Ruff on `scripts/build_room_package.py`,
`python -m unittest tests.test_room_session tests.test_room_grid
tests.test_room_communication`, and focused diff whitespace checks. TypeScript,
both Vite builds, Service Worker build, all 11 Node tests and all 41 focused
Python tests passed. No dependency upgrade or personal-save access was needed.

Browser plugin not available: used the existing headless Playwright/Chromium
with actual bundled Pyodide/Python/SQLite and isolated synthetic saves at
`http://127.0.0.1:8903/room/`. Phone viewports were 393x873 and 873x393 CSS pixels;
tablet regressions used 768x1024 and 1024x768. These are representative browser
viewports, not measurements from the POCO. No visible windows were opened.

| Rendered / integrated check | Result |
| --- | --- |
| Page identity, meaningful screen, error overlay | Correct title/route, real room/canvas and controls; no blank app or framework overlay. |
| Diagnostics / controls | Settings report downloaded without a query parameter; viewport/package/storage fields were correct; repeated downloads retained the same startup duration. Checkboxes and zodiac select updated real Python state. |
| Phone and tablet layout | Status/game-menu screenshots inspected at all four viewports. Phone Settings stayed inside the viewport at 175%/200%, with a reachable wrapped close header and scrollable body. |
| Games / touch | Real touch input and close passed for all six games: RPS choice, Tic-Tac-Toe move, Blackjack stand, Mastermind placement, Quiz answer and Connect Four column. Futter supply touch cancellation left no user-held portion. This is interaction smoke evidence, not full round/reward parity acceptance. |
| Care / offline | Petting started its real animation. Zodiac remained after offline reload and full browser close/relaunch with the network disabled. |
| Manual candidate handoff | Imported candidate over `42da08c1` through Settings/file input; zodiac and object identities survived. Subsequent opening against the older feed retained the newer imported version. The package importer/store/Service Worker sources are unchanged from that published baseline. |
| Console health | No JavaScript page errors. Game/layout pass had no console warnings/errors; lifecycle run had only two deliberate offline-network errors. |

Scripts, JSON results, reports and screenshots stay outside Git under
`%TEMP%/aiko-android-poco-qa/`: `check-final.mjs`, `phone-flows-final.mjs`,
`result.json`, `phone-flows-result.json`, `package-result.json`, device reports
and phone/tablet screenshots. The earlier candidate is not the handoff version.

This candidate was not pushed, released or deployed by this task. The Android
guide explains importing the local ZIP through the existing HTTPS PWA. Actual
Chrome/MIUI installation, system Back, storage pressure, reboot/OS termination,
performance, sustained use and affected physical iPad/Safari acceptance remain
pending in their device sheets. A1 is not marked complete by browser emulation.

## Permanent shared mobile release channel audit (2026-11-10)

The owner confirmed that iPad and Android must permanently use the same PWA
with shared updates. Source inspection found this already implemented; this
audit changes documentation only. Section 1.2 of the overall plan now makes the
single origin/path, manifest identity, build/runtime and release feed mandatory.
The earlier conditional deployment wording was removed. Both setup guides and
device sheets describe one common channel, per-device activation/save ownership
and temporary manual candidate import followed by ordinary newer shared updates.

| Owning source | Audited implementation |
| --- | --- |
| `web/vite.*.ts`, `web/scripts/build-service-worker.mjs`, `scripts/build_room_package.py` | One starter/manifest and one runtime bundle/ZIP per version, targeting Chrome and Safari together. The Apple profile points to the configured common starter; Android instructions do not select another runtime. |
| `PublishedPackage.ts` | Fetches `install.json` relative to the same PWA directory. The descriptor selects one package/version/integrity inventory. No user-agent/OS-specific feed selection. |
| `BrowserRuntimeUpdates.ts`, `BrowserUpdates.ts`, `PackageStore.ts` | Shared discovery, complete validation/staging and safe save-before-restart/cold-start activation; local writer locks and per-installation pet storage. |
| `.github/workflows/room-starter.yml`, `prepare_room_deployment.py`, `verify_room_deployment.py` | One reviewed starter release pin and Pages publication/verification route for the common `/room/` site. No separate mobile-platform deployment matrix. |

Additional end-to-end check at `http://127.0.0.1:8903/room/`: installed baseline
`0.1.0-42da08c1d5ba` into two independent persistent Chromium profiles, with
different Android/iPad-like user agents, viewports and synthetic zodiac settings
(Aries/Pisces). Changed the single server descriptor to candidate
`0.1.0-fcc4543432ed`. Both profiles discovered it, staged it and applied it via
the ordinary Settings restart control, without manual ZIP import. Both requested
the same `/room/packages/aiko-room-0.1.0-fcc4543432ed.zip`, whose SHA-256 was
rechecked as `adb6d89335644903285d589c9f513ef5c0b5bc3f6e6cdff220d15bcd2a85e94a`.
Downloaded reports confirmed the same activated version; distinct zodiac values
and object identities survived activation and offline reload in each profile.
No JavaScript page errors; only the two deliberately induced offline network
errors. No source/runtime changes since that candidate affect these paths.

Evidence is external at `%TEMP%/aiko-android-poco-qa/shared-update.mjs`,
`shared-update-result.json` and the two `shared-*-report.json` files. Browser
plugin not available; used existing headless Playwright/Chromium. Different user
agents exercise request handling, not the Safari engine or actual POCO/iPad
installation. Physical-device acceptance remains pending. No package rebuild,
push, release or public deployment was performed for this documentation audit.

## Shared iPad/Android update published (2026-11-10)

The owner authorised publication of the shared mobile stand and requested a
local Dropbox download/protocol folder. Release
[0.1.0-9649458666e2](https://github.com/Lexoniarus/aiko-desktop-pet/releases/tag/room-test-0.1.0-9649458666e2)
is now offered through the existing common
[`/room/` update channel](https://lexoniarus.github.io/aiko-desktop-pet/room/).
No new installed identity, origin, save schema, native app or separate Android
feed was introduced. The source is
`9649458666e2b1b633337e3192acf4b9fded4a2c`; no merge into main was performed.

All required checks passed on that exact source:

- [Python 3.11/3.13, full application/GUI and Windows boundary checks](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42835809976).
- [Web build and all 11 Node tests](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42835698103).
- [Asset tooling](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42835816420).
- [Long balance scenarios](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42835822574).

The release package contains 1,169 manifest-listed files. CRC, each size/hash,
bundled Python/wheels and the identical runtime in the starter passed local
verification. All 1,123 PNG files (including room images) are byte-identical to
the previous `45d4cf16` package. The existing reconstructed v16 build reference
and its provenance are preserved externally; no private source-art archive or
personal save is published.

Headless Chromium used the actual new package and two separate persistent
profiles, with Android/iPad-like user agents and separate synthetic settings.
Both upgraded through ordinary Settings restart from the currently published
`0.1.0-45d4cf160811` baseline to `0.1.0-9649458666e2`, requesting the identical
runtime path/hash. Their different zodiac settings and object identities
survived activation and offline reload. No JavaScript page errors; only the
intentional offline-network failures. This is browser/profile evidence, not
physical Android or Safari acceptance.

The first [Pages attempt](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42837330375)
on `72f3c116c53229eb38f727b8aa30ad18a2c42ad5` timed out after ten minutes in
`syncing_files`. Its log confirms cancellation of that specific Pages ID; the
public site still offered the old release. The failed identity was not rerun.
A fresh deployment commit retained exactly the same release pin and bytes.
[Recovery deployment](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42839393079)
on `74dbe5f9bd2738d2a1b39a64bf4fe8ba4d59bd55` succeeded. Its live checksum gate,
then an independent local check, verified the public descriptor, starter HTML,
Service Worker and complete runtime ZIP against the reviewed build.

Runtime: 86,816,455 bytes, SHA-256
`79e47c094be2696d17978e98f8005d37101d8772deb75fc1a0251c4e52f2cf78`.
Starter: 86,820,146 bytes, SHA-256
`a235f44cbf710e07e62a321617d193a5629ea2bf95856beeaac394bdf85d178f`.

All eight release assets were downloaded **from GitHub** into the requested
local folder, then checked against GitHub's asset sizes and SHA-256 digests:
`D:/Dropbox/Download/Aiko-Gemeinsame-PWA-2026-11-10-0.1.0-9649458666e2/`.
It includes runtime/starter/iPad-initial-install ZIPs, build metadata, both setup
guides, Android acceptance, checksums, CI/update/live/download/publication
records, `LIES_MICH.txt` and `DIENSTE-UND-KOSTEN.txt`. Local placement is verified;
Dropbox cloud sync is performed separately by the existing desktop client.
Private scripts/logs and synthetic browser profiles remain outside Git under
`E:/aiko-desktop-pet/lokale-daten/release-pruefung/2026-11-10-shared-mobile-release/`.

Both already installed devices use Settings -> App-Version und Updates -> Nach
Updates suchen, then safe restart (or complete close/reopen). A first-time POCO
installation opens the same HTTPS address in Chrome and uses its install menu.
No manual runtime import is needed for this release. Physical POCO/iPad checks,
system Back, device performance and sustained use remain open in their sheets.

## Dropbox entry helper for the POCO (2026-11-10)

The owner requested an Android entry through Dropbox without a separate app
version. Added a local supplement beside the downloaded release files:
`Aiko-auf-dem-POCO-starten.pdf` and `Aiko-Android-Einstieg.zip`. The PDF has one
large HTTPS link to the unchanged shared `/room/` address and three German setup
steps. The ZIP contains exactly that same PDF and `LIES_MICH.txt`. It does not
contain an APK, runtime, Apple profile, script or personal save. The PDF can be
opened directly from Dropbox; extracting the ZIP is optional. Chrome still
performs the PWA installation after user confirmation.

Created with the bundled local ReportLab tools, rendered through Poppler and
visually inspected. One page, one URI annotation pointing to the canonical
shared address, matching PDF bytes inside the ZIP, ZIP CRC and local Dropbox
copy hashes passed. Actual POCO Dropbox preview/browser handoff remains pending.
The helper opens whichever common version is currently published; it is not a
version-pinned Android application. Source/runtime, hosted PWA and the eight
previously downloaded release files remain unchanged. This supplement was
generated locally, not represented as another GitHub release download.

PDF SHA-256:
`b82172265f696fb83c93dd77322472e0e467b2c5feb0632e130588791154eea7`.
Entry ZIP SHA-256:
`aa61a85857524f0cf3b237f6403e7a919fe8e0a417782e5961004fb95245e989`.
Generator, preview and verification data stay outside Git under the existing
publication job's `android-entry/` folder. Setup guidance is recorded in the
Android install guide and section 1.2 of the overall plan. No new service,
dependency installation or paid option was introduced for this helper.

## Wall-furniture and Connect Four room depth (2026-11-10)

The owner reported Aiko disappearing beside the kitchen and behind the game
board while walking in front of the table. Both causes were confirmed in code:
the kitchen's wide image could cover an allowed side position `(425,60)`, and
the board was a DOM overlay above the entire room canvas. Commits `b020193f`,
`e3fab823`, `ab321844`, `aa406d86` and `c5aa29a3` implement wall-art ordering,
Pixi game artwork, focused regressions and width-aware table framing. The final
implementation retains the tablet's actor/table composition and shifts only
enough to keep all input columns on narrow screens. Geometry/footprints, stock,
Python game rules, save schema and hosting origin are unchanged.

Validation started after implementation, without visible windows. TypeScript,
Vite/starter/runtime/service-worker build and all 13 Node tests passed. Two
focused regressions were added: wall overhang on an allowed route, and the shared
table/board support order with mobile entry bounds. Exact-source
[web CI 42851223916](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42851223916)
passed. No desktop GUI/full Python suite was run for these rendering changes.

Browser plugin not available: existing headless Playwright/Chromium exercised
`http://127.0.0.1:8905/room/` at 1024x768, 768x1024 and 393x873 with touch input.
The flow installed the actual previous `9649458666e2` package, saved Pisces and
one stock portion, walked beside the kitchen, then updated normally through
Settings to `0.1.0-c5aa29a3019e`. Entire room/object snapshots matched across the
update. Aiko was then drawn above the kitchen at exactly the same saved point.

During the real approach to the table, Aiko crossed both sides of the board's
floor order (actor/board 736.1618/727.7562 in front, 727.3654/727.7562 behind).
Pixi child order followed both cases. No game image remained in the DOM overlay.
Real touch supply drag/preview/drop, Aiko's held chip/flight/fall, two settled
pieces, invalid release, pointer cancellation, camera swipe, keyboard Enter and
direct taps passed. The shared screen chip size was 24.58397px in landscape.
Closing during active play and reopening in tablet/phone layouts left exactly
five live game nodes while open and zero after close, with no delayed game.
All seven touch targets remained inside each viewport. Tablet portrait was
visually inspected with both board and Aiko visible; narrow phones retain the
free panorama for viewing Aiko beside the playfield.

The renderer was briefly frozen to compare board holes to the same room without
the board. All 42 openings matched five centre pixels each (210 exact matches).
Runtime CRC and every manifest-listed file hash/size passed. All 1,123 PNGs are
byte-identical to the previous shared release. Bundled Python/resource paths and
contents match after CRLF normalization; archive bytes differ because text line
endings differ, not because of a backend change. Offline reload retained stock
identity/coordinates/depth and settings. No personal save was read.

| Rendered check | Result |
| --- | --- |
| Page identity / meaningful app | Expected local `/room/` URL, Aiko title, room toolbar and game controls loaded. |
| Blank page / error overlay | None in inspected kitchen/table/portrait screenshots. |
| Console | No page errors; two bootstrap 404s with the update descriptor intentionally withheld, plus expected offline network failure. |
| Interactions / cleanup | Touch, keyboard, front/back walk, cancelled/invalid drop, chip sequence and node cleanup passed. |
| Update / save / offline | Existing room/object snapshots matched at activation; stock/settings survived offline reload. |

Evidence remains outside Git at `%TEMP%/aiko-room-furniture-depth-qa/`:
`result.json`, `package-verification.json`, before/after kitchen, table-front/back,
held/flight/drop, transparency and three-viewport screenshots. Actual Safari/iPad
and Android device acceptance remains pending.

Runtime SHA-256:
`4deb2469717ad5e16b9e9e9162d9099a10261f7a284e5ba38dd584a212e7a2a5`;
starter SHA-256:
`f07cffb77e80ce43e385d03408d6c67001a6788679bc0fe27ed7bddf8dc8dcb9`.

[The shared test release](https://github.com/Lexoniarus/aiko-desktop-pet/releases/tag/room-test-0.1.0-c5aa29a3019e)
includes the direct runtime ZIP, starter and iPad initial-install helper.
Deployment commit `67535817` and
[publication run 42851722713](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42851722713)
passed: preflight accepted the new identity, the deployment step took about seven
seconds, and the public descriptor, starter and complete runtime checksum matched.
Both platforms continue using the existing `/room/` update feed and local save.

## First POCO startup reported by the owner (2026-11-10)

The owner confirms that Aiko started successfully on the POCO and works in
principle. They found first installation more manual than on the iPad and not
yet optimal. The Android acceptance sheet records this as startup evidence and
an open onboarding UX item, not full device acceptance. Running package/browser
versions, standalone mode, exact manual steps and remaining device checks are
unrecorded; do not assign this report to a particular release by inference.
The plan now makes ongoing delivery-cost review explicit. This documentation
record changes no runtime, hosting, service subscription or billing setting.

## Native Android long-press containment (2026-11-10, local only)

The owner reports selection/highlighting while holding and dragging on Android.
The shared runtime still contained the earlier CSS selection protection, but
Safari's `-webkit-touch-callout` does not contain Chromium's native context-menu
and drag path. A mobile Chromium fixture using the existing CSS reproduced a
native, uncancelled `contextmenu` event after a real long touch on a source link.
The installed POCO package/browser version is unrecorded; this identifies a
code-level gap, not the exact device-side rendering of every reported mark.
See Chromium's [Android touch-drag/context-menu notice](https://groups.google.com/a/chromium.org/g/blink-dev/c/KnfFsL2dM8w).

Commit `3b99630c` adds one room-scoped capture boundary for `selectstart`,
`contextmenu` and `dragstart`, leaving native inputs, textareas, selects and
editable descendants alone. Its listeners are released on startup failure and
successful shutdown. It never cancels pointer/touch events or changes
`touch-action`, scrolling, click handling or viewport zoom. CSS also removes the
browser tap highlight from the room, restoring its native default in editors;
existing keyboard focus and application pressed-state styles remain intact.

TypeScript, starter/runtime/service-worker builds, all 18 current Node checks,
Prettier for the three changed source files and focused whitespace checks passed.
Browser plugin not available: headless Playwright/Chromium ran an isolated
QA-only package at `http://127.0.0.1:8911/room/`, with the newly built frontend and
the last published `c5aa29a3019e` Python/assets. No personal save was used.

| Check | Observed result |
| --- | --- |
| Room identity / rendering / console | Correct title and toolbar; meaningful room/panels, no framework overlay, page errors, console errors or warnings. Screenshots inspected. |
| Native event boundary | Selection/context-menu/drag events cancelled on room text, assets, links and canvas, including text-node targets; allowed in inputs, textarea, select, nested editors and plaintext-only editors, and outside the room. A noneditable child inside an editor remains protected. Disposing the boundary restores native behavior. |
| Editing / ordinary controls | Real text selection/replacement, checkbox/select changes, ordinary source-link navigation and one activation per touch passed. Native pointer/touch sequences remained uncancelled by the boundary. |
| Phone portrait, 393x873 | One-second hold then room swipe and food supply drag/drop passed without selection. Text-origin menu scrolling and cancelled-drag cleanup passed. |
| Phone landscape, 873x393 | Native settings changes passed; panel remained scrollable. |
| Tablet regression, 1024x768 | Room swipe and settings passed. One-second hold then Vier-gewinnt chip drag showed the Pixi drag preview and committed a player chip on release. |
| Browser touch highlight | Toolbar computes to transparent; no focus-style or touch-action changes. |

Evidence and temporary regression scripts remain outside Git under
`%TEMP%/aiko-android-touch-qa-20261110/`: `result.json`, `check.mjs`,
`android-portrait-drag.png`, `android-landscape-settings.png`, `ipad-settings.png`
and `game-chip-drag.png`. An older failed fixture screenshot is not final
acceptance evidence. The phone screenshot also shows an existing moodlet/care
overlap at 393px; layout changes were outside this input fix.

Actual POCO/Android and Safari/iPad acceptance remains pending, particularly
system selection handles, native long-touch UI, keyboard/copy-paste and both
browser/installed modes. The Android checklist contains the required device
steps. No release, push or deployment was performed for this fix.

## Automatic update-check interval with cached starters (2026-11-10)

The owner's request to enforce the shared iPad/Android automatic-check limit
exposed an adapter bug: a cached starter's event handlers read its own timestamp,
but delegated `check()` updated only the runtime owner's timestamp. Frequent
foreground/reconnect events could therefore bypass the starter's 60-second guard.

`BrowserUpdates.checkAutomatically()` now enforces the interval in the runtime
owner, and the cached starter adapter delegates to that method. Current startup
and event wiring use the same guard. Settings still call the owner's immediate
manual `check()`, which also updates the timestamp. Failed attempts count and
concurrent calls share the in-flight promise. No polling timer was introduced.
The interval is per running app, in memory; a fresh launch may check immediately.
The shared delivery contract and development guide now state these boundaries.

All 18 Node tests passed, including five new behavioral tests covering event
bursts and the exact 60-second boundary, historical cached-starter event wiring,
the runtime without a starter, network failure, hidden-app events, manual checks
and in-flight deduplication. Network and package storage are stubbed; no personal
save or live endpoint is accessed. TypeScript and the complete Vite starter,
runtime and service-worker production build passed. No full Python suite or
physical iPad/POCO acceptance was run for this TypeScript update-routing fix.
This is a local source correction; it has not been published to the devices.

## Shared automatic-check correction published (2026-11-10)

The owner subsequently authorised publication and local Dropbox downloads.
The immutable source is `6a57c86375f0b42c258f55898a0a7d07bee1964b`, version
`0.1.0-6a57c86375f0`. It includes the preceding committed Android native-interaction
boundary. Later parallel documentation was preserved outside this build identity.
[Exact-source web CI 42857176835](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42857176835)
passed its 18 Node tests, TypeScript and production build. No full Python suite
was repeated: packaged Python contents (normalising text line endings), Pyodide
and all 1,123 PNGs match the previous shared release. ZIP CRC, all 1,169 manifest
entries, descriptor identity/size/hash and the shared runtime in the starter passed.

Browser plugin not available: existing headless Playwright/Chromium tested
`http://127.0.0.1:8913/room/` at 393x873 and 768x1024 in separate touch profiles.
Both installed `0.1.0-c5aa29a3019e`, then used that previous cached starter to
discover and activate the same new runtime through Settings. Their distinct
zodiac settings and object IDs survived activation and offline reopening.
Forty foreground/online events at 59,999 ms produced no request; an event at
60,000 ms produced one. Manual search was immediate and reset the automatic
interval. The clock was controlled in the test page; there were no minute-long
waits. Both settings screenshots show the target version and current status.
No page errors or framework overlays occurred; the two console network failures
are from the intentional offline checks. This does not constitute physical
Safari/iPad or POCO acceptance.

[Release room-test-0.1.0-6a57c86375f0](https://github.com/Lexoniarus/aiko-desktop-pet/releases/tag/room-test-0.1.0-6a57c86375f0)
contains eight files, including runtime, starter, iPad first-install helper,
Android/iPad instructions, build identity, Android checklist and SHA-256 sums.
All eight were downloaded from GitHub into
`D:/Dropbox/Download/Aiko-PWA-Updatepruefung-2026-11-10-0.1.0-6a57c86375f0`
and matched against GitHub's asset digests and sizes. Protocols and the inspected
screenshots are beside them. Existing Dropbox desktop sync handles the local
folder; remote cloud-sync completion was not independently checked.

Deployment commit `1d57ce6aea79df3ed1f7059c6c3092ec5dcf9e6b` pins the verified
starter on `deploy/room-pwa`.
[Publication run 42858207762](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42858207762)
passed, including public descriptor, starter and complete runtime verification.
An independent local live-download check also matched the reviewed site.
Both devices continue using `https://lexoniarus.github.io/aiko-desktop-pet/room/`;
existing icons and local saves are retained. No merge into `main` was performed.

Runtime: 86,817,364 bytes, SHA-256
`1d631937d580260e247d80476331074f539ae4c7c6600ad29f0ff20b002e2e90`.
Starter SHA-256:
`5d2cd5e51854ebd728e802427c01b17447780af96a463e4f31cb971709dad129`.
The site totals 86,952,320 bytes. Cost review reconfirmed the public repository,
standard runners and existing Pages route. No billing configuration, paid option,
subscription or quota was changed; full account billing/monthly bandwidth was
not audited. Details and source links are in the local Dropbox cost protocol.

## Manual package checks during the four-device test (2026-11-11)

The owner reported that the published update worked on two phones and two iPads
across two testers. The owner chose to notify testers when a release is ready.
Testers now initiate package checks from **Einstellungen → App-Version und
Updates → Nach Updates suchen**. Commit `ed990765` removes the startup,
foreground and reconnect triggers and ignores forwarded checks from older
starters. First setup still retrieves the initial package.

All 20 web tests and the production build passed. Headless Chromium updated
from `0.1.0-6a57c86375f0` to local candidate `0.1.0-ed990765093b` in a phone-sized
profile with the previous cached starter and a tablet-sized profile with the new
starter. Each manual update fetched one descriptor and the same runtime ZIP.
After activation, startup and simulated foreground/reconnect events produced
zero descriptor requests. Pressing the Settings button fetched one descriptor.
Both profiles retained their distinct settings and object IDs and reopened
offline. Page and console errors were absent. The local browser report is in
`%TEMP%/aiko-manual-update-qa-20261111/result.json`.

The candidate remains local. Physical acceptance of the manual-only version
follows publication and installation on the test devices.
