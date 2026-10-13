# Aiko application boundary and future integrations

Status: **application contracts only**. No HTTP listener, browser extension,
open firewall port, web endpoint, message broker or external permissions exist.

## Dependency direction

```text
future browser/IPC adapter -> validated NotificationCommand --+
                                                       +-------v-------+
Tkinter toolbar/buttons -> CareCommand ---------------->|ApplicationRouter|
                                                       +-------+-------+
                                                               |
                                      +------------------------+----------------+
                                      |                                         |
                                CareController                         NotificationInbox
                           PetState / AikoMind                     bounded, data-only FIFO
                                      |                                         |
                                  CareOutcome                             UI thread polls
                                      |                                         |
                                  Tk presenter <------------------------------+
```

- **Care commands:** UI supplies trusted clock and real workload conditions.
  The controller owns the existing sequence: advance needs, note interaction,
  choose pre-action dialogue, apply care, update dialogue memory, select reply.
  The GUI alone shows speech/emotes, refreshes panels and persists state.
- **Notification commands:** future authenticated adapters supply *data only*.
  Ingress is thread-safe, bounded to 32 pending events, duplicate-safe with a
  bounded 128-ID history, and never calls Tk. An owner-thread method drains
  events; display is non-interrupting when other speech or sleep is active.
- **No arbitrary commands:** an integration cannot trigger a care action on
  a worker thread or supply execution timestamps for it.
- **Transport is unspecified:** no API is started automatically. A future
  adapter may implement local HTTP, authenticated IPC or a browser bridge.

## Future payload shape (not a running endpoint)

```json
{
  "version": 1,
  "type": "notification.created",
  "id": "notif-123",
  "title": "Kalender",
  "message": "Dein Termin beginnt in 10 Minuten.",
  "priority": "normal"
}
```

The adapter MUST authenticate and authorize the sender, then call
`IncomingNotification.from_payload(payload, authenticated_source=identity)`.
It must not trust a user-supplied `source`. It should apply request body size,
rate and origin limits, loopback binding by default, and protect against
browser cross-origin / cross-site request abuse. The application inbox does
not provide network authentication.

Notification text is presentation data, never HTML, Python or a program
command. Priority is preserved for a future attention/interrupt policy.
The current UI only presents one message when no other conversation is active.

## Adapter boundary and security

A future HTTP or IPC adapter must run separately from Tk event handling:

1. Authenticate and authorize the external caller. Bind its identity as the
   trusted `source` argument; a supplied `source` field is rejected.
2. Validate event `version`, `type`, `id`, `title`, `message` and
   `priority`. Oversized strings, control characters, unsupported versions
   and unknown fields are rejected before entering the inbox.
3. Map the `NotificationReceipt.status` values (`accepted`, `duplicate`,
   `full`) to transport-specific acknowledgements.
4. Apply a separate adapter-side body limit, per-caller rate limit, origin
   allowlist and authentication. Bind local HTTP to loopback only unless the
   user deliberately configures an alternative.
5. No notification callback may call Tk, pet-care mutation or arbitrary
   computer processes. The desktop tick alone may consume and display data.

The current inbox uses arrival order and stores priority metadata. A later
attention policy may choose to defer or prioritize without changing the wire
contract, but must preserve the non-interrupting default and bounded queue.

## Semantic read contracts

The live desktop constructs an immutable, language-neutral
`PetReadSnapshot` in `application/read_snapshot.py`. This is distinct from
the existing German `HoverSnapshot` and `StatusSnapshot`, now owned by
`presentation/contracts.py` and composed by `DesktopPresentation`.
A future external adapter should expose only an authorized subset of the
semantic snapshot rather than returning German desktop strings, local
window geometry or unapproved computer-activity details.

Application activity/attention policies use structural provider contracts
in `application/ports.py`; `telemetry.ComputerSnapshot` is a shared
hardware-independent value type. No new observer or network service was
introduced.

## Possible read-side API (not implemented)

Some integrations may eventually request read-only status (e.g. needs,
availability or current activity). Build this through a dedicated typed
`PetStatusSnapshot` query handler instead of exposing `PetState` or Tk
objects directly. Snapshot reads must cross the owner-thread boundary or use
an immutable, thread-safe cache. Do not expose application names, window
titles or unapproved personal activity details.

## Pending architecture cleanup

- Desktop scheduling, state serialization and ordered shutdown now have
  dedicated services under `desktop/`. The runtime consumes named
  `DesktopTickPorts` callbacks instead of inheriting private GUI stages;
  `DesktopPreferences` coordinates setting effects without duplicate state.
  The typed forwards in `desktop/compatibility.py` remain only for
  historical callers and must not be used by new integrations.
- `ActivityCoordinator` owns pet time progression during desktop ticks and
  before persistence; `DesktopPersistence` writes the supplied state without
  advancing the pet or choosing sleep policy.
- `PetSessionRestorer` performs startup catch-up for valid existing saves
  using the `SavedPetReader` port. `PetSettings` is owned by the application
  settings module, and `StateStore` only decodes/encodes JSON data. Neither
  application component imports the storage implementation.
- The hover/status/settings widgets **already** use immutable view models
  and narrow callbacks, with a separate `HoverUi` owner; guard this direction
  against new direct `DesktopPet` references in future changes.
- Migrate flat domain/monitoring modules into package directories gradually,
  retaining compatibility imports throughout.
- Consider an outbound application event stream only when a consumer exists.
  A general-purpose event bus is intentionally not introduced prematurely.

## Personality and reaction ownership

Adaptive observations, conversation decisions, workload event detection
and work-session context now have explicit canonical modules in
`aiko_pet/personality/`. The detector's descriptive English name is
`WorkloadEventDetector`; old `ComputerVoice` imports are aliases.
Presentation-owned cue scheduling lives in
`presentation/reaction_playback.py`. Neither the API contract nor any
German authored responses have changed.

## Platform and visual-policy ownership

Windows taskbar discovery, native window ordering and read-only global
input sampling now live in `desktop/` and are no longer primary imports
from the root package. Sprite frame timing, gaze and horizontal motion
planning are pure code in `presentation/`, consuming only immutable or
explicitly typed desktop geometry. No hooks, key inspection, browser
integration or network access were added.

## Persistence infrastructure contract

`infrastructure/persistence.py` owns the only state JSON repository;
`storage.py` is a legacy import façade. Application session restoration
consumes its typed load port and keeps bounded time catch-up outside
the repository. Old save path precedence and version-one schema are
preserved, including relative environment-variable overrides.

## Migration safety

Existing entrypoints, stored JSON schema, dialogue catalogue, and user-facing
care methods remain in place. The new application components live alongside
the old modules as an incremental dependency cutover. The animated character
is now `AnimatedPet`, the accessory-window owner is `HoverUi`, and the
desktop shell `DesktopPet` connects them through narrowly scoped callback
ports. View snapshots are produced by `DesktopPresentation`, not the Tk
windows themselves. `DesktopViewSource` is a legacy presentation subclass.
No migrations or extra runtime libraries are necessary.


# Application-boundary cutover

- Package `aiko_pet/application/` contains typed care and notification
  commands, future integration events, an owner-thread command router, and a
  bounded, thread-safe notification inbox.
- `DesktopPet.interact()` now submits `CareCommand` and receives a
  `CareOutcome`. The controller owns domain/dialogue sequencing; the GUI
  still presents text, refreshes widgets and saves locally.
- External notification data uses `IncomingNotification.from_payload(...,
  authenticated_source=...)`. The adapter is responsible for authenticating
  and authorizing the source (not provided in this change).
- `DesktopPet._tick()` drains at most one message when not sleeping,
  speaking, running an action or actively using controls. No separate
  application thread ever manipulates Tk windows.
- No HTTP endpoint, browser extension, WebSocket or daemon is started here.
