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
& $env:AIKO_PYTHON scripts/build_room_package.py --prototype '<path to aiko-360-raumtest-v16.zip>'
```

`dist-room/starter/` is the small HTTPS-hosted starter.
The same starter is supplied as `aiko-starter-<version>.zip`.
`dist-room/aiko-room-<version>.zip` is the offline runtime to transfer through
Dropbox or a GitHub download. `BUILD.json` records the package hash and commit.
A source archive downloaded from a branch is not the built runtime ZIP.
See [the German quick start](INSTALLATION_DE.md) and
[completed automated checks](VERIFICATION.md).
No private save, fonts, source-art authoring jobs or prototype review captures
are included. The selected runtime artwork retains its existing asset terms.

Deploy only the starter directory to a stable HTTPS origin/path. GitHub Pages
can host it; `.github/workflows/room-starter.yml` provides a manual deployment.
The workflow does not upload the prototype or publish the private runtime ZIP.
Hosting/account configuration and actual deployment remain explicit actions.

## First installation

1. Open the starter's HTTPS address in Safari.
2. Use Share → Add to Home Screen. This Safari step is manual.
3. Launch Aiko from the new icon before importing anything.
4. Download the built ZIP using Dropbox or GitHub and save it in Files.
5. In Aiko, choose **Aiko-Paket auswählen** and select that ZIP.
6. Wait for Aiko's real Python state and room to appear.

The HTTPS origin identifies browser storage. Changing it is a different
installation; do not move it between updates. A ZIP cannot install a Home Screen
icon or replace Safari's shell automatically.

## Actual-device record — not yet performed

Record version/hash, model, OS and the observed result of each item. Windows or
headless-browser results do not mark these as passed.

- Icon starts a standalone window; touch targets work in portrait and landscape.
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
