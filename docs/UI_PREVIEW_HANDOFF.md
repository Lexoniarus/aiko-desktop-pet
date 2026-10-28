# VN UI preparation — shared local handoff

**Implementation update (5C, 2026-10-20):** main status/menu, embedded selectors,
shared VN assets and settings/Credits are implemented on `feature/social-optimization`.
The preparation-only authorization statements below describe the historical
approval pass. The external reference bundle and original masters are unchanged.
The three gameplay layouts/artwork remain with their existing owners; native
Windows/DPI/input acceptance has not been executed in this headless delivery.

Design/asset preparations completed and all three reference groups approved by
the owner on 2026-10-20. This is the entry point for other local chats continuing
the UI work. Read [the canonical design](UI_VN_DESIGN.md) first.

## Durable local reference bundle

### Approved RPS identity and animation follow-up

On 2026-10-28 the owner approved the Fingerduell revision at
`../design-previews/rps-animation-2026-10-28/preview.html`, relative to the checkout
root. Read the [latest RPS direction](UI_VN_DESIGN.md#approved-rockpaperscissors-identity-and-animation--2026-10-28)
and its README/`approval-record.json`. The original RPS bundle below is preserved.

An illustrated stitched rose mat, cream/blue hand area and blue/peach/lavender
hand tiles give RPS its own quiet identity. Three unchanged Attack cycles now
accompany Schere–Stein–Papier, 900 ms each by default; the third forward moment
reveals Aiko's sign and the result. V3 gaze/body reactions and existing emotes
follow. Her sign remains visible while the comment slot switches text/emoji.
Direct selection, input gating and interruption retain the accepted game flow.
Native integration is not authorized. The prior animation-only draft, source
provenance, SVGs, validation and screenshots remain local companion files.

### Approved game-specific follow-up: Quiz

On 2026-10-28 the owner accepted the revised Quiz design at
`../design-previews/quiz-2026-10-27/preview.html`, relative to the checkout root.
Read the [canonical design](UI_VN_DESIGN.md#approved-quiz-follow-up--2026-10-28)
and the external README before continuing. `approval-record.json` freezes the
reference, owner statement and the reported preview limitation.

The blue-violet small quiz studio, centered answer podiums and question-star
emblem give the game its own identity within the VN shell. Aiko moderates the
question and individual options, each becoming visible with its announcement;
input unlocks only after her release cue. Installed V3 gaze/body poses, existing
emotes and personal asides carry the host role. While waiting she occasionally
clasps her hands, looks around and comments; choices stay enabled and interrupt
her immediately. Source questions and factual explanations remain unchanged.

The owner reported that the automatic waiting sequence appeared to depend on
hovering the answer buttons. They accepted the design and deferred that preview
issue; its cause is unconfirmed. **Native waiting must start without hover** and
be checked with real Windows input. Passing local automation is not acceptance
of this observed execution behavior. Final timing and the complete dialogue pool
remain later work. No application changes or production-asset installation are
authorized; previews, source copies and validation remain outside Git.

### Approved game-specific follow-up: Rock–Paper–Scissors

On 2026-10-27 the owner approved the revised Rock–Paper–Scissors concept at
`../design-previews/rps-2026-10-27/preview.html`, relative to the checkout root.
Its `README.md` records the decisions; `approval-record.json` freezes the reviewed
files by hash. Its `asset-provenance.json` retains the built-in Imagegen prompt
and references for the new closed-fist sign. No production asset is replaced.

For this game the follow-up supersedes the 2026-10-20 layout/countdown concept:
large own-hand display, immediate selection/start, own hand visible immediately,
Aiko's sign revealed in her bubble, persistent result and compact session tally.
See the [canonical approved follow-up](UI_VN_DESIGN.md#approved-rockpaperscissors-follow-up--2026-10-27).
The owner explicitly retained the no-application-code boundary. Other game
references remain unchanged except for separately approved follow-ups below.

### Approved game-specific follow-up: Tic-Tac-Toe

On 2026-10-27 the owner approved the final Tic-Tac-Toe revision at
`../design-previews/ttt-2026-10-27/preview.html`, relative to the checkout root.
Its `README.md` and `approval-record.json` retain the decisions, explicit approval
and file hashes. This is the approved final Chibi-voice/reaction revision;
the earlier generic and dry analyst drafts are only historical comparisons.

Use the [canonical design](UI_VN_DESIGN.md) for the full approved behavior:
large shared board, explicit Nächste Runde, alternating starters, actual-board
qualitative comments in Aiko's warm, playfully competitive Chibi voice and existing
one-shot character reactions. Her bubble stays with her; no extra taskbar item.
`asset-provenance.json` records unchanged UI copies; `reaction-provenance.json`
records the 31 existing character-frame copies. No production asset is replaced.
Local tests and screenshots are retained in the same preview folder.

### Approved game-specific follow-up: Connect Four

On 2026-10-27 the owner approved the final Connect Four revision at
`../design-previews/connect-four-2026-10-27/preview.html`, relative to the checkout
root. Its `README.md` and `approval-record.json` retain the approval and file
hashes. Use the [canonical design](UI_VN_DESIGN.md#approved-connect-four-follow-up--2026-10-27)
for the full accepted direction: illustrated saturated blue board, matching
custom yellow/red chips, Aiko as a mischievous Chibi trap-setter, a red chip stack,
existing pickup poses and a single parabolic toss over the board into its column.

The bundle retains exact built-in Imagegen prompts, native artwork, exports,
registration/provenance, browser screenshots and validation. Earlier geometric
boards and the rejected two-part flight remain under its `history/` directory.
Timing and native integration remain later work. No application implementation
or production-asset replacement is authorized. Mastermind has a separately
approved follow-up below.

### Approved game-specific follow-up: Mastermind

On 2026-10-27 the owner approved the corrected Mastermind revision at
`../design-previews/mastermind-2026-10-27/preview.html`, relative to the checkout
root. Its `README.md` and `approval-record.json` record the approval and reviewed
file hashes. See the [canonical design](UI_VN_DESIGN.md#approved-mastermind-follow-up--2026-10-27)
for the full accepted flow and scope.

The lavender/silver code console shares the VN window family. Aiko guards her
own donut in the little anime safe **to her right**, on the same floor baseline.
The corrected opening uses the actual closed and open drawings through a
continuous hinge transition, ending with the original open-door perspective.
The distorted closed-texture flip is rejected history. On a cracked code she
thanks the player and eats; after ten failed attempts she opens with her spare
key and eats anyway. The snack is a visual gag without satiety or other pet,
reward or World effects. Existing eating frames and food artwork are reused.

The external folder retains exact Imagegen prompts, unchanged sources,
`safe-animation/` with nine registered frame samples and its provenance/checks,
browser screenshots and both playable endings. No application implementation,
production-asset replacement or import of the HTML examples is authorized.

### Approved game-specific concept: Blackjack

On 2026-10-27 the owner accepted the Blackjack visual direction and basic flow
at `../design-previews/blackjack-2026-10-27/preview.html`, relative to the checkout
root, while explicitly leaving further animation-flow optimization open.
`approval-record.json` freezes this reference as an **approved concept**, not a
fully polished animation. See the [canonical concept](UI_VN_DESIGN.md#approved-blackjack-concept--2026-10-27).

Aiko plays an over-the-top Las Vegas dealer. Her bank hand is on her left, the
shared deck on her right. Existing Attack frames provide a remote show gesture;
cards gather, shuffle above the deck and travel individually to both hands.
All cards use the same 128×128 size and all original faces/backs/frames stay intact.
The player window uses the VN rose/white shell and an emerald/cream/gold table.

The external README records the remaining timing/sequence refinement. Sources,
license, comparisons, screenshots and checks remain local companions. No
application changes or native integration are authorized. Quiz has a separately
approved follow-up above.

### Original shared bundle

The self-contained reference bundle is outside the Git checkout:

`../design-previews/vn-ui-2026-10-20/` relative to the checkout root.

Resolve the checkout's parent directory on the current machine; no user profile
path, chat ID or cloud service is required. The bundle is local companion material,
not part of a public source checkout.

Open `index.html` there for main menu, settings/Credits, game concepts and the
asset gallery. Relative links and required local images/licenses/documentation
are included so the bundle does not depend on a particular Codex chat or a
running server. Other chats on this same machine can read these ordinary files.
This is local availability, not cloud synchronization or a published website.

The example directories `assets/ui-vn/v1/{main-menu,settings,games}/`, control
composition HTML and rejected PNG attempts were compared against the archive by
hash and moved out of the checkout during the owner-requested cleanup. Ignore
rules prevent accidentally reintroducing them. A recovery copy of those removed
checkout companions is retained under `checkout-cleanup-backup-2026-10-20/` inside
the bundle; the active entry points below are unchanged.

Version only selected source artwork, exact prompts, source/usage provenance and
the canonical approved specification. The pre-existing icon source gallery stays
with its asset catalogue; it is separate from the interactive menu prototypes.
The canonical design records the accepted layout without requiring HTML fixtures
in Git. No application integration is authorized by this cleanup/commit.

## Reference entry points

These paths are relative to the external bundle root, not to a source checkout:

| Reference | Bundle path |
| --- | --- |
| Overview and approval status | `index.html` |
| Main menu, wishes and embedded selectors | `assets/ui-vn/v1/main-menu/preview.html` |
| Settings and separate Credits | `assets/ui-vn/v1/settings/preview.html` |
| Credits directly | `assets/ui-vn/v1/settings/preview.html#credits` |
| All three game surfaces | `assets/ui-vn/v1/games/preview.html` |
| Button/bar/panel composition | `assets/ui-vn/v1/controls/preview.html` |
| Rejected generation references | `assets/ui-vn/v1/controls/drafts/` |

Each interactive reference directory retains its detailed README and approval
record. Archived draft paths in the versioned control metadata identify these
local generation references; only the eight selected control PNGs need to exist
in a fresh source checkout.

## Accepted scope and final review

- Main-menu design approved by the owner on 2026-10-20: need/action columns,
  dedicated wish row, Moodlets, embedded selectors and expanded details.
- Settings and separate Credits design approved on the same date. API provider,
  individual-content attribution and asset/license information belong in Credits,
  not game windows. Existing application data ownership remains unchanged.
- The three game surfaces were also visually approved by the owner on 2026-10-20.
  They are the final preview examples; Blackjack retains every card source/frame.
- Preparation is complete for the agreed scope. No further preview or concrete
  missing image asset remains; technical implementation/export work is separate.
- Application implementation remains unauthorized. The prototypes do not touch
  the application, saves, actual game sessions or background services.

## Asset readiness

The preparation set contains 46 icon masters and eight selected control/panel
masters, plus provenance and excluded attempts. It covers the documented Moodlet
families/wish components, menu actions, detail groups, RPS signs and X/O tokens.
Existing concrete food images and Blackjack cards are reused. Checkboxes, board
geometry, separators, navigation marks, focus rings, scrollbars and dynamic bar
fills are UI-rendered elements, so they do not require additional generated PNGs.

No concrete missing image asset or further preview screen was identified for
the agreed scope. The remaining technical work belongs to later implementation:
normalize/export sizes and slice insets, verify font delivery, DPI, input/focus,
timers and native Windows/Tk behavior. Example values/times do not settle domain
rules. Continue any independent Moodlet/wish/domain discussions in their existing
plan; do not turn prototype fixtures into another runtime state owner.

The external bundle's `BUNDLE_MANIFEST.json` records file hashes and review scope.
If references are revised later, update the bundle deliberately and retain the
owner's approval evidence. Main menu, settings/Credits and games each have their
own explicit owner approval; none authorizes application implementation.
