# Shared room development

Worktree: `feature/shared-room-pwa`, based on the green desktop commit
`ce4797ed65a477ca0d8015262584ff895e0a554d`. The workload hotfix is included.

The accepted v16 room is the visual reference. Reuse its approved room artwork
and the canonical character catalogues; this task does not regenerate art.
The native desktop retains its own entry point and dependency environment.

The starter is a small HTTPS-installed PWA. Its Service Worker caches the shell
and serves validated, versioned ZIP content. Program updates and pet data have
separate stores. The browser Worker owns one local Python session. The same
RoomClient contract supports a later native desktop host.

Implementation commits precede test execution. Automated local verification
must be headless; device acceptance stays explicitly pending until observed on
the user's iPad. A Windows browser pass cannot supply that evidence.

The actual shared host composition lives under `frontend/room_session.py`,
`frontend/room_runtime.py`, `frontend/room_content.py` and
`frontend/games/session.py`. This preserves the existing rule that the
application layer cannot import frontend modules. The former retired
`presentation` namespace remains prohibited by the canonical import audit.
Existing rules stay in
`application/`, `pet/`, `world/` and `games/`. The browser root only supplies
fetch, filesystem publication and transport adapters. Native callers use the
same extracted playback, game timelines and immutable projections.

The browser SQLite migration is schema 6. Optional room location/depth belongs
to World; observed depth belongs to ObjectMemory. Native snapshots use compatible
defaults. First browser publication uses exclusive file creation under the
browser's lifetime writer lock; successful UI acknowledgement follows IDBFS
flush. Desktop hard-link publication remains the default adapter.

The supplied device is an iPad of the ninth generation on iPadOS 26.6. Follow
[the device acceptance sheet](IPAD_ACCEPTANCE.md); later OS releases remain
compatibility targets rather than an assumed proven result. Automated browser
QA uses headless Playwright: the Browser plugin/skill is unavailable in this
session, and the owner explicitly prohibits visible test windows.

Build dependencies are locked in `web/package-lock.json`. From `web/`, use
`npm ci`, `npm run build`, then the repository Python interpreter to run
`../scripts/build_room_package.py`. Generated downloads and distributions stay
outside Git. The resulting delivery includes a starter folder and runtime ZIP.

The user-facing installer is now a single ZIP with a removable Web Clip profile
and a brief instruction file. Build with `--starter-url <stable HTTPS directory>`
to also generate `install.json` and the self-contained deployment site. Opening
the installed icon downloads the verified runtime automatically on first launch;
later starts use the active local package before any network request.
The owner explicitly permits this first online setup. Profile confirmation in
iPad Settings and the file handoff have since been confirmed by the owner.

The deployment workflow reads `.room-release.json` only on the dedicated
`deploy/room-pwa` branch (or manual dispatch). The descriptor pins a reviewed
GitHub release asset by SHA-256. The release artifact contains the prebuilt site,
including the runtime; private prototype originals are never required in CI or
added to source Git. Actual publication is a separate external action.

The owner approved publication on 2026-11-05. The first test installation is
live at `https://lexoniarus.github.io/aiko-desktop-pet/room/`, backed by the
prerelease `room-test-0.1.0-d073fc2958cf`. The source build is `d073fc29`;
deployment branch `deploy/room-pwa` pins its release artifact at `ab4863d7`.
Both the shared-web check and deployment completed successfully. The actual
HTTPS installation and subsequent offline reopening were checked with the
real Python runtime in a headless browser. The Web Clip's system confirmation
and first-run behavior on the owner's iPad were subsequently confirmed. The
owner's feedback leaves room geometry/motion, bubbles, drag-and-drop and game
presentation parity open; successful installation is not visual acceptance.

## Updates on the installed icon

The starter checks the current same-origin `install.json` after the local room
has started, on foreground return and on reconnect (automatic checks are
throttled to once per minute). Settings also provide a manual check and version.
The descriptor is fetched without caching with a 10-second timeout. A full
package download has a 10-minute bound and uses the existing streamed manifest,
file-hash, size, path, protocol and schema checks. Delta downloads are not used.

Updates commit only a `pending` entry in the existing package settings database.
The active/previous/pending package caches are distinct from the pet IDBFS
database. A cold start acquires both the pet-writer and installation locks before
switching pending to active; only then are unreferenced package caches removed.
The previous package is retained, but automatic save-schema rollback is not
promised. This starter accepts schema 6 only. Another live pet writer prevents
activation. Failed or interrupted downloads leave the active package unchanged.

The new runtime registers an awaited shutdown hook: stop ticks/input, suspend
and flush IDBFS, then release the writer. Only after success can the starter
activate and reload. Restart is disabled while a game is open. A failed save
leaves the old runtime running and the verified update pending. No automatic
in-session reload is performed.

For the original d073 installation, the new Service Worker takes over only shell
routing without reloading the existing page. Runtime requests remain bound to
their package UUID. On the next navigation the new shell can run the unchanged
old runtime and stage its replacement. An external notice asks the user to close
and reopen: old runtimes have no shutdown hook and never receive an unsafe
restart button. Preserve the same URL, profile, icon and website data throughout.
See [installation instructions](INSTALLATION_DE.md) for this first transition.
