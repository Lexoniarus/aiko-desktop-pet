# Aiko application boundary and future integrations

Status: **application contracts only**. No HTTP listener, browser extension,
open firewall port, web endpoint, message broker or external permissions exist.

## Dependency direction

\`\`\`text
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
\`\`\`

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

\`\`\`json
{
  "version": 1,
  "type": "notification.created",
  "id": "notif-123",
  "title": "Kalender",
  "message": "Dein Termin beginnt in 10 Minuten.",
  "priority": "normal"
}
\`\`\`

The adapter MUST authenticate and authorize the sender, then call
\`IncomingNotification.from_payload(payload, authenticated_source=identity)\`.
It must not trust a user-supplied \`source\`. It should apply request body size,
rate and origin limits, loopback binding by default, and protect against
browser cross-origin / cross-site request abuse. The application inbox does
not provide network authentication.

Notification text is presentation data, never HTML, Python or a program
command. Priority is preserved for a future attention/interrupt policy.
The current UI only presents one message when no other conversation is active.

## Migration safety

Existing entrypoints, stored JSON schema, dialogue catalogue, and user-facing
care methods remain in place. The new application components live alongside
the old modules as an incremental dependency cutover. Future work can replace
direct \`DesktopPet\` references from Tk widgets with narrow UI ports and
separate sprite/speech/window coordination from \`gui.py\`. No migrations or
extra runtime libraries are necessary.
