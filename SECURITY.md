# Security policy

Aiko Desktop Pet is a small, local-first hobby project. Security reports
are welcome, especially where user data, local file paths, desktop
interaction or unexpectedly reachable services might be affected.

## Supported source

Security fixes are considered against the current `main` branch. Old
historical feature baselines and screenshots are documentation, not
separately supported installer releases.

## Reporting a vulnerability

**Please do not post a working exploit, private save contents, credentials,
or personal desktop/activity details in a public issue.**

1. If the repository's GitHub **Private Vulnerability Reporting** option is
   available, use its private `Report a vulnerability` workflow.
2. If that option is not enabled, use a private contact channel published by
   the repository maintainer's GitHub profile. If no private channel is
   available, open a *non-sensitive* issue requesting a secure contact
   method; do not attach vulnerability specifics publicly.
3. Include affected commit/Windows/Python version, steps to reproduce
   and the impact once a private communication channel is established.

No guaranteed response window or bug-bounty program is offered. Please
allow time for investigation and coordinate disclosure of reproducible
security issues with the maintainer.

## What Aiko currently accesses

- Local CPU/GPU load, RAM, uptime and user idle duration for adaptive work
  and rest behavior.
- Tkinter UI input and limited global button/focus observations for the
  on-screen companion.
- A local JSON save file; the optional `AIKO_SAVE_PATH` override changes
  only its location.

Aiko does not intentionally read typed content, browser pages, process titles
or microphone audio, and it does not start a network server or invoke cloud
AI APIs. This describes the present public implementation; future features
that add permissions or connectivity will need a separate security review.

For privacy details, see [README.md](README.md#privacy-and-local-data).
For public contributions, use [CONTRIBUTING.md](CONTRIBUTING.md).
