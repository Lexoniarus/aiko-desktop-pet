# T1 verification record — 2026-11-05

The implementation remains local on `feature/shared-room-pwa`, based on green
desktop `ce4797e`. This is automated integration evidence, not actual-iPad
acceptance or green GitHub CI on the room branch.

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
