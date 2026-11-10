# Android / POCO acceptance — A1

Status: **physical-device checks pending**. Initial device information is supplied
by the owner, not obtained from an automated device session. Follow the
[German setup and first-test instructions](INSTALLATION_ANDROID_DE.md).

## Record for each pass

- Device: POCO X3 NFC; MIUI Global 14.0.5 Stable; Android 12.
- Full OS build: capture from the device (spoken/transcribed identifier unverified).
- Chrome version, date, free storage and ordinary battery-saver settings: pending.
- Runtime version, source commit, ZIP SHA-256 and hosted/manual-import route: pending.
- CSS/visual viewport and display mode: download Settings -> Device report in
  both portrait and landscape. Hardware pixels are not CSS viewport dimensions.
- Result per row: pending / passed / failed; attach observed steps and evidence.

## Technical and interaction checks

All rows below are pending on the actual POCO. First separate Python/installation
failures from viewport/input findings. Use the same built package as the iPad;
do not create an Android-specific rule implementation or save.

| Area | Required observation |
| --- | --- |
| First install | Chrome opens stable HTTPS origin, verifies/downloads runtime, starts actual Python and room; browser installation creates a usable icon. Record standalone versus browser shortcut. |
| Candidate identity | Settings and downloaded report match the intended version/hash. A local candidate is not assumed to be the currently hosted release. |
| Diagnostics | Report download works from Settings without a query parameter; actual browser/viewport, fixed startup duration, runtime/package identity and persistence/quota observations are present, with no pet state. |
| Persistence | Change zodiac/settings and perform acknowledged care; retain the same settings, progress and object identities after reopen. Record persistence grant independently of successful writes. |
| Offline / restart | After complete setup, close/reopen in airplane mode; repeat after device reboot. Required Python packages, room assets and saved state load locally. |
| Lifecycle | App switch, display lock, return, full close and restart preserve acknowledged progress. Interrupted drags/actions/games grant no false completion. Time catch-up occurs once. No continuous background Python is assumed. |
| Updates | Import the candidate through the existing icon, retain save/settings/objects, reopen online/offline and reject a stale online offer. Test a subsequent newer package, interrupted/corrupt download and safe activation without data clearing. |
| Writer admission | A second browser window refuses a second live save writer. Record installed/browser storage behaviour rather than assuming two separate Aikos. |
| Portrait / landscape | Toolbar/care controls, menus, wishes/status and speech remain reachable/readable. Long panels scroll; UI size settings, system bars and camera cutout do not hide the close/control targets. |
| Room / touch | Swipe, call/follow/find, care, supply drag, existing-portion drag, drop, handover and touch cancellation preserve the existing rules and object identities. |
| System Back | Record browser/installed behaviour with an open panel, active game and plain room. No stranded game, save loss or duplicate action after return. Native Back acceptance requires the phone. |
| Functional parity | All section-3 care, wishes, conversations, offline content, horoscope book and opt-in online behaviour from the overall plan. Preserve acknowledgement, interruption and reward boundaries. |
| Every game | Schere–Stein–Papier, Tic-Tac-Toe, Blackjack, Vier gewinnt, Mastermind and Quiz: start, actual input, visible feedback, round completion/reward where earned, close/cancel and reopen in both orientations. |
| Sustained use | Record startup/responsiveness, memory reloads, thermal/battery observations and repeated meals/sleep/closures/updates. Establish device measurements before performance promises or optimisation. |

Relevant iPad flows need separate regression checks after shared changes. An
Android phone pass does not prove Android tablet, every browser or iPad support.
Record headless Chromium/WebKit evidence separately in [VERIFICATION.md](VERIFICATION.md).
