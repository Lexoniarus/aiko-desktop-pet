# iPad delivery and acceptance

Target provided by the owner: **iPad (9th generation), iPadOS 26.6**.
Use standard browser/PWA APIs; do not pin acceptance to this one OS release.
Later iPadOS releases remain compatibility targets requiring their own checks.

## Build on Windows

Use Node 22.12+ and the project's Python environment with `requirements.txt`.
No Mac, Apple developer account or iOS signing step is part of this PWA route.

```powershell
$env:AIKO_PYTHON = '<absolute path to the project Python interpreter>'
npm --prefix web ci
npm --prefix web run build
& $env:AIKO_PYTHON scripts/build_room_package.py --prototype '<path to aiko-360-raumtest-v16.zip>' --starter-url '<stable HTTPS directory ending with />'
```

The user transfers only `Aiko-iPad-Installation-<version>.zip` to the iPad.
It contains the launch profile and concise instructions. `starter/` and
`aiko-starter-<version>.zip` are deployment artifacts: they include the starter,
first-run descriptor and runtime download. `aiko-room-<version>.zip` remains
the runtime/update artifact. `BUILD.json` records hashes, source and target.
A source archive downloaded from a branch is not the built runtime ZIP.
See [the German quick start](INSTALLATION_DE.md) and
[completed automated checks](VERIFICATION.md).
No private save, fonts, source-art authoring jobs or prototype review captures
are included. The selected runtime artwork retains its existing asset terms.

Deploy the generated site to the profile's stable HTTPS origin/path. GitHub
Pages can host it; `.github/workflows/room-starter.yml` downloads a reviewed,
hash-pinned release artifact. Neither source-art authoring originals nor saves
are needed in CI. Hosting publishes the bundled program/runtime images for
the initial download and remains a separate external publication step.

## Floor-grid update acceptance

For an already installed icon, publish the complete updated starter/runtime to
the existing origin first. A cold reopening then loads the compatible starter;
use **Einstellungen -> Nach Updates suchen -> Jetzt neu starten**. The older
starter running in an already open window cannot import protocol 2 until that
shell has refreshed. Reopen the installed app; do not remove its profile or
clear browser/app storage.

The schema-6 database is backed up before schema 7 is applied. Stock IDs and
pet progress survive; old object positions and remembered positions are mapped
independently. The backup is internal database recovery data, not a new UI
restore/export feature. Original user data must not be used for automated QA.

On the target iPad, verify:

- Swipe through all four flat wall panels and their joins; the floor/skirting
  stays level, and furniture translates without tilting, narrowing or turning.
- Confirm exactly one window on the east wall and neutral art behind the west
  desk/shelf. Keep the current four-wall furniture distribution; check original
  v16 picture proportions, shelf mounting and corner-contained bed/plant art.
- Update through the existing icon and retain the save. If a runtime ZIP is
  imported through Settings, an older online offer must not replace it, including
  after online and offline reopening. Do not reinstall the profile.
- Call Aiko closer; size changes with distance while her logical size stays fixed.
- Aiko walks around the table and occupied furniture footprints, including behind.
- Fixing follows her bearing; a swipe releases it. Find appears only off-camera.
- Lift food, move it in front of furniture, release and see it fall/bounce; pick
  up the same portion again. Present at the face before handing it over.
- Read the horoscope: closed/carry/open size and hand registration are coherent.
- Inspect moodlet details, need cards and wishes with progress/pin/dismiss.
- Confirm the old pet values, zodiac, live portions and progress after update,
  after closing/reopening, and with the network disabled.

Full forward/backward authored walking cycles and new furniture back views are
not part of this asset set. Assess the reused 2D directional poses accordingly.

All physical-device items above remain pending until the owner checks them.

## Touch selection and editing acceptance

In both Safari and the installed Home Screen app, in landscape and portrait:

- Hold and move a finger over toolbar labels, panel text, speech bubbles and
  game artwork. No browser text selection, selection handles, image preview or
  link callout should appear. Normal taps and source-link navigation still work.
- Swipe the room, drag food from the supply and move an existing portion; drag
  a game chip. Holding before moving must not interrupt the intended gesture.
- Scroll a long panel from its text area. Check checkboxes, native selects and
  the package file picker. If text editors are added, check caret placement,
  selection, copy/paste and the keyboard, including nested editable text.
- Page zoom outside the custom room/drag surfaces must remain available; this
  change must not add a global touch-event cancellation or zoom restriction.

Actual iPad acceptance of these checks remains pending. Desktop headless
WebKit/Chromium checks cannot prove iPadOS selection handles or system callouts.

## First installation

1. Download the installation ZIP through Dropbox or GitHub into Files.
2. Unpack it and open **Aiko-installieren.mobileconfig**.
3. In Settings, confirm the downloaded profile. Enter the device code if asked.
4. Launch Aiko through the new Home Screen icon while online.
5. Wait for automatic download, verification and the actual Python room.
6. Reopen offline. No manual Safari address or runtime file picker is required.

The HTTPS origin identifies browser storage. Changing it is a different
installation; do not move it between updates. The profile adds a removable
full-screen Web Clip after system confirmation. It does not itself embed the
runtime. Direct opening from Files needs device acceptance; Apple Mail is the
documented fallback for handing a profile to the system installer.

## Actual-device record — first installation confirmed, parity open

On 2026-11-05 the owner confirmed profile installation and opening the room on
the target iPad. They reported incorrect room transitions, bubble placement and
some literal question marks, unreliable drag-and-drop, jerky motion, scale/depth
and furniture overlap, and missing desktop-equivalent game presentation/assets.
The correction build **0.1.0-ff6d7142a7cc** implements fixes for these findings;
its headless touch/game and offline checks are recorded in
[verification](VERIFICATION.md#room-and-game-correction-build-2026-11-05).
Device acceptance remains open until the owner rechecks the same findings on
the iPad. No Safari frame-rate or pixel-identical desktop parity pass is claimed.

In the next device pass the owner confirmed improvement and acceptable normal
character size, but requested native walking instead of running, smoother motion,
better floor joins and desktop-equivalent food dragging/recognition/hand use.
Follow-up build **0.1.0-3351f6ec864a** implements those corrections and retains
normal size. Recheck holding food near the face, lowering it to ready hands,
release acceptance versus falling, lifting existing portions, cancellation and
the three-bite meal. Automated evidence is recorded in verification; actual
Safari performance and visual acceptance remain open.

The following report clarified foreground staging and real profile heads.
Build **0.1.0-e0fbaec47ab4** moves Aiko/portable items onto the foreground strip,
keeps furniture behind them and accepts drops over furniture or other portions.
Existing object IDs survive depth normalization. Recheck these drops, close
ground pickup, lateral profile walking, quarter-body survey and the window base.
Forward quarter posing uses existing stance/turn artwork; a full forward step
cycle is not included in the current asset pack. Device acceptance stays open.

Build **0.1.0-6515ed307321** adds the shared petting visual, finite one-shot
completion independent of unread dialogue, and a simple room-only daily motion
sequence. Recheck petting -> rest -> walking, reached goals without direction
flicker, short autonomous outings followed by quarter-body/head holds, and
interruption by care/call/drag. The pixel-sway effect is not used. Actual iPad
smoothness and long-running animation stability remain device checks.

Record version/hash, model, OS and the observed result of each item. Windows or
headless-browser results do not mark these as passed.

- Icon starts a standalone window; touch targets work in portrait and landscape.
- Opening the profile from the unpacked ZIP reaches the system installer;
  confirmation creates exactly one Aiko icon. Record any required Mail fallback.
- First icon launch downloads the package automatically; interrupted/mismatched
  downloads leave no active partial package and can be retried.
- Swipe independently of Aiko, call her, and watch her own movement/routine.
- Drag a new portion onto the floor and onto Aiko. Move an existing portion;
  quantities and custody remain correct. Cancel a gesture without losing food.
- Offer all ten foods and Energy Drink; inspect recognition, refusals and intake.
- Pet, poke, sleep/wake, read status, inspect/pin/dismiss wishes, and Plaudern.
- Play every game, close during a round, reopen, and inspect actual rewards.
- Select a zodiac sign, offer/read/interrupt/resume/put down the horoscope book.
- Enable online content deliberately; verify provider attribution and failure
  states separately from offline Plaudern, local jokes and the horoscope.
- Wait for a care action's acknowledgement, close/reopen and confirm retained
  state. Background/kill during unfinished dialogue grants no false completion.
- Start in airplane mode, including after an iPad reboot. Check Python resources,
  SQLite publication/revision writes, Astronomy Engine and pyjokes metadata.
- Keep the existing icon/profile and take the first d073 update online using
  the close/reopen steps in [the quick start](INSTALLATION_DE.md). Confirm that
  existing settings and World objects survive, and version information appears.
- Use **Einstellungen → App-Version und Updates → Nach Updates suchen**.
  A verified update is staged in the background. It must not interrupt a game;
  **Jetzt neu starten** saves first. Check full close/reopen and offline start.
- A failed/corrupt or interrupted update keeps the installed package and progress.
  The manual **Paket aus Datei importieren** path remains an alternative.
- Shared mobile release: iPad and POCO use the same `/room/` origin/path and
  `install.json`. Verify one newer runtime is offered and activated on both,
  matching version/package hash while preserving their separate saves. Record
  delayed activation on an offline device separately; no second platform feed.
- Open a second window; it must refuse a second save writer.
- Record startup time, responsiveness, any memory reload, and search cancellation.
  `?diagnostics=1` enables a local device-report download without the pet save.

Interrupted actions are cancelled on suspension. Care already acknowledged as
saved remains durable. Abrupt OS termination can precede an in-flight flush;
the periodic checkpoint is a recovery point, not guaranteed background execution.

Notifications are the subsequent T2 phase: forecast data is local; closed-app
Web Push needs a separately operated Internet sender. No native offline scheduled
notifications or continuous background Python are claimed for this PWA.

## Table-based Connect Four acceptance (2026-11-07)

- Open Vier gewinnt: Aiko walks around furniture to the near side of the table.
  Closing during that walk must not start a game later.
- Check both orientations: board feet rest on the tabletop, Aiko stays beside
  the board, and speech/controls leave the seven columns unobstructed.
- Empty openings show the real window/room through the board. The board stands
  towards the front of the tabletop; both supplies rest on the foreground floor.
  Aiko's stack must not rise or sink when her pickup pose changes.
- Drag yellow from the supply over an entry. Check entry/landing previews,
  release/fall, full columns, returning invalid drops and cancelled gestures.
  Tap a column directly as an alternative; there is no numbered button row.
- Compare the supply, held, flying, falling and settled chip diameters. Check the
  handoff above the board and its face hiding the chip during its fall.
- Swipe outside the board to look around. Dragging a chip must hold the camera
  only until release/cancel. Check normal and 175% menu size independently.
- Close during Aiko's throw, reopen, then close/reopen offline. Retain the same
  pet progress, zodiac and existing objects. Unfinished games remain transient.

## Ground feeding and corrected gaze acceptance (2026-11-07)

- Keep the existing profile/icon. Install the update normally and confirm the
  same pet progress, zodiac and existing ground objects after offline reopening.
- Compare turn starts and frontal up/down looks to the corrected desktop art.
- Drag a portion onto the floor in front of Aiko. It must remain in place while
  she walks to its observer-facing side, then play the original bend/pickup with
  the portion appearing in her hands at the source contact marker. No floor-to-
  hands attraction should occur.
- Repeat facing each wall and near furniture. An obstructed front station must
  not be replaced by pickup from behind or at a distance.
- Move a portion away during approach/before hand contact. No acquisition at
  the old location, duplicate portion or nutrition credit should occur. Verify
  direct handover separately, including touch cancellation.
- Inspect portrait and landscape for natural hand contact and foreground masks;
  check identification/eating, then reopen offline without respawn.

## Fixed food line and same-cell drawing (2026-11-07)

- Update the existing profile. Older food stays at its previous position; begin
  moving an old portion and cancel to verify exact restoration without snapping.
- Drag a new portion left/right, then move only up/down. Its size and target
  ground line stay constant; only release height changes. Repeat at each wall
  and across a corner. Falling/bouncing should settle on the same line.
- Walk Aiko behind a portion, onto its cell, then onto a nearer cell. Food covers
  her on the same cell or behind; she covers it only from a nearer cell. Food
  does not block walking, and pickup remains at the authored contact marker.
- Repeat ordinary direct handover. A refused/timed-out offer and an offered item
  returned on app suspension land on the line; a successful offer stays in hand.
- Reopen offline and verify the same object identities and care progress. Check
  portrait/landscape on the actual iPad; no new profile is needed.

## Furniture and table-board depth acceptance (2026-11-10)

- Update the installed app without replacing its profile. Verify retained food,
  settings and pet progress after offline reopening.
- Walk beside the kitchen/fridge and other wall furniture. Aiko must remain in
  front of their artwork on allowed floor, with no path through their footprint.
- Open Vier gewinnt while Aiko approaches. She must cover table/board when nearer
  and be covered when farther away; holes show the real room behind them.
- Exercise direct tap, yellow-chip drag, invalid release, touch cancellation and
  Aiko's pickup/throw/fall. Compare chip size and masks; closing mid-action must
  remove all game artwork without leaving a held camera or later game action.
- Check tablet portrait/landscape and phone entry reachability. Pan away and back,
  rotate the device, and confirm hit targets remain aligned with the seven slots.
