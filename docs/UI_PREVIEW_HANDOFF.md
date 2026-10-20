# VN UI preparation — shared local handoff

Design/asset preparations completed and all three reference groups approved by
the owner on 2026-10-20. This is the entry point for other local chats continuing
the UI work. Read [the canonical design](UI_VN_DESIGN.md) first.

## Durable local reference bundle

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
