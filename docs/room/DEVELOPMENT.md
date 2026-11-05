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

Build dependencies are locked in `web/package-lock.json`. From `web/`, use
`npm ci`, `npm run build`, then the repository Python interpreter to run
`../scripts/build_room_package.py`. Generated downloads and distributions stay
outside Git. The resulting delivery includes a starter folder and runtime ZIP.
