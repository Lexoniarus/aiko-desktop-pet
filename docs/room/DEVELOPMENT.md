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
iPad Settings and the file handoff still need real-device acceptance.

The deployment workflow reads `.room-release.json` only on the dedicated
`deploy/room-pwa` branch (or manual dispatch). The descriptor pins a reviewed
GitHub release asset by SHA-256. The release artifact contains the prebuilt site,
including the runtime; private prototype originals are never required in CI or
added to source Git. Actual publication is a separate external action.
