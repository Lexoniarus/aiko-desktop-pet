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

## Actual-device record — not yet performed

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
- Import an updated valid ZIP through **Einstellungen → Paket aktualisieren**;
  keep the icon and Aiko's progress. A failed/corrupt import keeps the old package.
- Open a second window; it must refuse a second save writer.
- Record startup time, responsiveness, any memory reload, and search cancellation.
  `?diagnostics=1` enables a local device-report download without the pet save.

Interrupted actions are cancelled on suspension. Care already acknowledged as
saved remains durable. Abrupt OS termination can precede an in-flight flush;
the periodic checkpoint is a recovery point, not guaranteed background execution.

Notifications are the subsequent T2 phase: forecast data is local; closed-app
Web Push needs a separately operated Internet sender. No native offline scheduled
notifications or continuous background Python are claimed for this PWA.
