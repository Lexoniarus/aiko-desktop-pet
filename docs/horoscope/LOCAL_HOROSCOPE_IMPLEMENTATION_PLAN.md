# Local horoscope book: implementation and acceptance plan

Updated 2026-10-26 during completion of the authorized local replacement.
The API prototype is rejected and replaced, without a fallback mode.
The owner authorized verified local commits; push and merge remain unauthorized.

The detailed [module and catalogue contract](MODULE_AND_CATALOGUE_CONTRACTS.md)
records concrete owners, objects, functions and JSON boundaries. The
[approved German reference](book-reading-reference.de.md) establishes the reading
style; the complete editorial sources are `pilot-book-entries.de.json` and
`aiko-book-dialogues.de.json`.

## Scene and content

Aiko stays Aiko. A physical book supplies an independently written horoscope;
she reads it and optionally reacts to a specific passage. No identity change,
forced role-break, shared creative activity or automatic game invitation.
Friendship changes only her own comments, independently of emotional state and
needs. The book text must remain understandable without her comment.

| Step | Physical and spoken sequence | Technical owner |
| --- | --- | --- |
| Place | Select the local book under Unterhalten; drag/drop it onto the taskbar or offer it. No need effects on selection/placement. | Shared cursor gesture and World |
| Notice | Aiko perceives an unknown item, approaches, picks up and identifies it. Known eligible books use normal retrieval. | Existing awareness, intentions and object interaction |
| Open | Keep existing holding pose; carry_closed, half_open, open_reading. | Object custody and item overlay; cancellable presentation |
| Frame | Aiko naturally introduces reading what the book says for the chosen sign. | Existing DialogueBook |
| Read | Complete authored passages express the daily situation, tension/development and useful impulse. At most one passage-specific optional comment. | Frozen local reading and ReactionPlayer |
| Close | Natural closing, half_open, carry_closed, legal put-down. | Playback releases to the same object episode |
| Remain | Closed book remains available for manual replay within its fixed hour. | Persistent World expiry |
| Dissipate | Fade its separate window during the last second; remove by the deadline, including while held. | World expiry and presentation projection |

Shared conversation timing is applied once across the assembled sequence;
<=125 characters per text bubble, <=12 text bubbles including Aiko's framing and
comment, final text has the agreed additional second. No obligatory punchline
pause is inserted into a horoscope.

## Local calculation and selection

Pinned MIT dependency: Astronomy Engine 2.1.19, pure Python, no provider/account,
key, translation model or runtime generation. Its license is shipped in
`LICENSES/ASTRONOMY_ENGINE_MIT.txt` and its project is linked in Credits.
The install already processes requirements.txt.

Use actual geocentric tropical Sun/Moon longitude and Moon phase at a fixed
local-noon reference converted to UTC. The selected sign defines the relative
solar-house ordering; Moon house chooses one of twelve themes and phase quarter
one of four development directions. These are authored entertainment rules,
not scientific predictions. Sun context is computed/saved; narrower catalogue
eligibility can use it, but the current entries claim no narrower solar rule.

96 complete entries = 12 themes x 4 directions x 2 variants, produced through
twelve pilots and 48 basic entries, then the second variants. Every entry has
explicit reviewed sign applicability. No phrase soup, runtime sign swapping,
borrowed API content or fallback reading for an ineligible combination.
Selection uses stable SHA-256 date/sign keys, then freezes the chosen complete
reading, source revisions, sky snapshot and selected Aiko cues.

## Daily book lifecycle (latest owner decision)

One book contains one daily entry. First reading may pause and resume at the
saved cue. It receives the normal agreed conversation care admission once;
completion/replay does not award extra care or fabricate a food gift/wish.

After Aiko puts down the book following its first full reading, start a fixed
3600-second wall-clock deadline. Both first-put-down time and matching instance
expiry are saved together. During that hour handing the same book back starts
its **same frozen story from the beginning**. Subsequent replays, put-downs and
restarts cannot extend the hour. It never disappears at pickup or admission.
At the deadline it dissipates in any custody; pending speech/visual/episode
callbacks are invalidated safely. A completed held book recovered onto the
taskbar gets its first put-down deadline at recovery; an existing deadline is
always retained. Partial first reading alone does not start this replay hour.

Only one live horoscope book may exist, including cursor and Aiko custody.
Next local day a new book gives the new day's entry after the previous book
retires. An old completed book retains its original entry and deadline across
midnight; it blocks new stock until expiry. An incomplete previous-day book is
retired at the day boundary so it cannot block today's reading. At most two day
records are retained. Aiko does not autonomously reread completed books.
The earlier immediate single-use/used_up proposal is superseded.

## Reuse and replacement

Reuse direct sign selection, atomic session persistence, shared conversation
care owner/timing, ReactionPlayer, object awareness/custody/intention phases,
D&D cursor gesture, item overlay, four approved book sprites and existing hold
pose. Keep physical truth, subjective memory and frozen reading separate.

Replace the entire HTTP horoscope request/preparation/footer/counter path with
local calculation, authored catalogue and independent daily coordinator. Remove
the rejected provider from live online budgets and Credits. Retain old DDL only
for valid legacy migration, not a parallel feature.

Schema 3 migrates API admission/completion markers without the prose or attempts,
so an already credited day cannot grant care again. It adds typed local days and
cue rows, book memory kind and World expiry. Failed snapshot admission rolls
back the care change. A saved cursor never reselects a new sign, comment or text.

## Acceptance

- Full sign/theme/direction coverage, restrictions, stable selection and actual
  astronomical boundary checks; <=125 chars and <=12 text bubbles.
- Friendship/emotion/low-energy eligibility for optional passage comments.
- Pickup/held READ/put-down through the existing object phases; no nutrition or
  fabricated food-handover reward, no food-only recall wording for books.
- Pause, repeated handover, click-to-advance, stale callbacks, closing/opening
  cancellation, hard expiry in resting/user-held/pet-held custody.
- Same-day fixed credit/deadline, next-day new book after old stock retires,
  SQL/JSON migration, save failure and restart behavior.
- Offline menu placement and native 1x/2x book rendering with isolated saves;
  preserve food/drink, other social providers and parallel character changes.
- Repository lint/types and relevant/full regression checks, with unrelated
  existing failures clearly separated in delivery.

Tarot, hat gifts, extra character animation and page-turn effects remain future
work. No new character artwork is generated by this implementation.

## Completion verification, 2026-10-26

The local runtime replacement is committed as `556565a`, after separate commits
for startup/dependency checks (`facecaa`), the reviewed catalogue (`13875dc`) and
generic readable World objects (`39a990a`). The working tree's parallel
character work is excluded from these commits. A byte/hash comparison confirmed
91 parallel files unchanged; the shared animation file retains its separate
unstaged body-orientation changes.

Verification uses immutable Git-tree exports and temporary SQLite saves, without
opening the personal save. The 206 targeted integration checks pass: 22 horoscope
checks, 96 SQLite checks, 10 actual Windows/Tk book-flow checks, 19 shared drag/
readable checks and 59 provider-retirement/compatibility checks. The SQLite
coverage includes retired book history with an earlier pet clock. Native checks
include same-instance drag/drop/relocation, stable held
reading, failures without care credit, restart, manual replay and expiry during
reading or cursor custody. These are automated checks, not a new visual approval
of the character artwork.

The isolated staged tree passes repository Ruff and strict Mypy (349 source
files). Pyright reports the same two pre-existing union-narrowing errors at
`tests/test_rock_paper_scissors_sequence.py:92` as base commit `ed2c809`.

The repository regression is not fully green. Separate runs of base `ed2c809`
reproduce existing failures in `test_generated_care_balance` (competitive quiz
fixture), the chatter-switch case in `test_gui`, two `test_story_gui` cases, the
story-click case in `test_click_gui`, the ghost/drop case in `test_mastermind_gui`
and two `test_world_gui` drink-handover cases. Two further World fixtures
(`test_missing_unwanted_reserve_starts_one_bounded_search` and
`test_unknown_absence_finishes_without_search_before_new_discovery`) use invalid
subjective memory IDs and trigger existing save warnings. The same nonblocking
warning guard was applied only inside the temporary base export for comparison:
both the 54-case base World module and the current 64-case module have exactly
the same four failures. The ten added book cases pass.

The module-isolated regression covers 2,197 tests after the final replacements,
with eleven reproduced baseline failures/errors and the same two Pyright
findings. The new horoscope paths are green; this is not a claim that the whole
repository is green. Existing balance/fixture problems remain outside this
completion. Test warnings are asserted after Tk cleanup so failures cannot leak
roots into subsequent tests.

The initial dirty tree and diagnostics are preserved in a private snapshot
outside Git. Neither this completion nor validation pushes, merges, changes CI,
generates artwork or edits the normal save. Start with `Aiko_starten.bat`, which
requires the project `.venv`; startup verifies a real offline Sun/Moon/phase
calculation before opening a save. An incomplete Python environment gives an
installation instruction instead of a late error while Aiko holds the book.
