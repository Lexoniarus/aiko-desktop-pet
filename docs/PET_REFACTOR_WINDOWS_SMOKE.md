# Windows acceptance checklist — pet architecture refactor

Scope: draft PR #9, `refactor/pet-domain-ui-boundaries`. Record a result
against the **exact commit SHA** tested; a previous successful screenshot or
an unrelated CI run is not acceptance for the new branch.

This is a manual, interactive Windows 10/11 check. Linux/Xvfb and
Windows-headless CI **do not** verify transparent-window layering, real mouse
events, taskbar positioning or visual sprite alignment.

## Preparation

1. Check out the refactor branch on a Windows machine. Record `git rev-parse HEAD`.
2. Close other Aiko Desktop Pet instances before starting the smoke test.
3. Use a **new temporary** `AIKO_SAVE_PATH` rather than risking your real save.
   Never overwrite or delete the actual user data for this verification.
4. Start with `python -m aiko_pet` (or the usual Windows launcher).
5. Test at scale 1× and 2× where indicated.

## Manual verification

- [ ] **Startup:** Aiko appears once at the taskbar in her saved or default
  location, with no stray magenta background, lost image or stray Tk root.
- [ ] **Idle/animation:** All eight authored frames play in order for idle,
  walking, sleep, eating, petting and existing greeting/reaction sequences.
  The idle blink returns to neutral without frame skips.
- [ ] **Gaze:** Move the cursor around Aiko and to far desktop positions.
  She continues using the sixteen existing look directions, including on the
  left and above the primary monitor when a secondary display exists.
- [ ] **Walking:** Random walking is horizontal, feet remain on the taskbar,
  movement stays within the allowed track and remains smooth between the
  main scheduler ticks. Hover and sleep still suspend walking appropriately.
- [ ] **Toolbar:** Hovering Aiko opens exactly one care/status toolbar.
  Moving from Aiko to an unpinned toolbar across its bridge retains it.
  Leaving the area hides only an unpinned toolbar.
- [ ] **Pin/F2:** `Offen halten`, `Pin lösen` and F2 preserve the existing
  toolbar visibility and focus rules. A pinned but idle toolbar does not
  permanently suppress spontaneous behaviour.
- [ ] **Settings:** Opening settings via the existing controls shows one
  independently movable persistent window. Outside clicks, resizing and
  toolbar hiding do not close it. Invoking settings again focuses the same
  instance. Escape/Schließen closes it explicitly.
- [ ] **Snack/food:** The menu opens without duplicates. All eleven
  consumables (including the Energy Drink) display the current graphics and
  labels. Successful feeding uses the matching held-item overlay.
  Denied feeding
  or a full-energy drink never pretends an item was consumed.
- [ ] **Scaling and item sprites:** Change scale 1× ↔ 2× during a normal
  session and after selecting food. Sprites, hand overlays, anchors and
  window positions stay correct; changing scale does not duplicate frames.
- [ ] **Minigame:** Opening Rock-Paper-Scissors produces one independent
  game window, with the existing game pose and speech. Only finished rounds
  award the existing fun/energy/social results; closing an untouched game
  grants no game reward.
- [ ] **Speech/attention:** Greeting, click sequences, follow-up bubbles,
  emotes, occasional idle comments and notifications retain their timing.
  Non-interrupting messages do not cover currently active controls.
- [ ] **Window layering:** Check `Immer im Vordergrund` on and off.
  Verify Aiko, pinned toolbar, settings, minigame and speech windows stack
  correctly without focus stealing or accidental duplicate controls.
- [ ] **Saving/restarting:** Close normally, restart using the same temporary
  save, and confirm settings, position, mood/friendship and care values.
  The save must retain `version: 1` and the same flat `settings` keys.

## Targeted regression check for the later R2/R5 cleanup

After the earlier positive Windows report, the moving and observation
boundaries changed substantially. Before approving the **latest commit**,
repeat at least these interactive checks, in addition to any impacted items
above:

- [ ] Smooth horizontal walking between 140 ms desktop ticks; pause at
  taskbar limits, hover, sleep, game, disabled walking and busy workload
- [ ] All sixteen gaze directions, stale-pointer reset and switching
  between cursor gaze and computer-busy review pose
- [ ] Full eight-frame idle blink and head sway; game waiting, care animations
  and one-shot completion (including selected hand-held food assets)
- [ ] Settings changes to follow-cursor, auto-walk and scale 1x/2x, with
  independent settings window, toolbar, and non-activating window layering
- [ ] No duplicate animations, unexpected monitor polls or callback errors
  after switching between game, sleep, care and passive idle

These steps should be recorded against the exact new SHA. Automated green
CI alone is insufficient for interactive Win32 acceptance.

## Acceptance record

Maintainer report, 15 October 2026: the refactor branch was tested
interactively on Windows and its behavior was reported functional. The exact
tested commit, Windows/DPI setup and individual checklist entries were not
provided. This report is useful evidence, but is **not** a final per-commit
sign-off for later R2/R5/R6 changes.


- Exact branch commit:
- Windows version and DPI/scaling:
- Displays / taskbar configuration:
- Python version:
- Manual tester:
- Date:
- Failed steps / observed regressions:
- Attached screenshots or log paths:
- Decision: pending / accepted / rejected

Do not approve or merge the PR if any required visual or behavioural step
fails. Fix the regression on the refactor branch, rerun CI and repeat the
relevant interactive tests.
