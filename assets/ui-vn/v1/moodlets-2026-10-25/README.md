# Eight additional Moodlet symbols — 2026-10-25

The owner requested asset production after reviewing the 26 current Moodlets
against the 18 original symbols. These eight new symbols complete source-art
coverage. The owner subsequently requested using them immediately, and the shared
runtime Moodlet icon mapping now assigns all eight symbols to their own families.
No Moodlet rules, wishes, save format, book/hat or character artwork changes are
part of this delivery.

| Current Moodlet | Source | Motif |
| --- | --- | --- |
| Doch verloren (`disappointed`) | [PNG](../icons/moodlet_disappointed.png) | Drooping blue game star and downward accent |
| Essenswunsch missachtet (`food_wish_disregarded`) | [PNG](../icons/moodlet_food_wish_disregarded.png) | Food-wish speech bubble with dismissal slash |
| Vertrauensvoll (`trusting`) | [PNG](../icons/moodlet_trusting.png) | Two gently clasped hands |
| Wertgeschätzt (`appreciated`) | [PNG](../icons/moodlet_appreciated.png) | Heart with recognition star |
| Zuversichtlich (`optimistic`) | [PNG](../icons/moodlet_optimistic.png) | Cream sunrise over a blue arc |
| Verunsichert (`uncertain`) | [PNG](../icons/moodlet_uncertain.png) | Signpost pointing in two directions |
| Übersehen (`overlooked`) | [PNG](../icons/moodlet_overlooked.png) | Smaller subdued star beside a brighter companion |
| Auf der Hut (`guarded`) | [PNG](../icons/moodlet_guarded.png) | Heart partly protected by a blue shield |

All eight 1254 × 1254 RGBA originals were generated individually with the
OpenAI built-in Imagegen tool. [generation.json](generation.json) preserves
the exact prompt set, semantic roles and output names. The existing secure
and connection symbols were inspected for visual comparison; new generations
used descriptive prompts without image edit targets. Original generator output
bytes and transparency are preserved.

The existing exporter produces 24, 32, 40, 48, 64, 96 and 128 px derivatives
under `aiko_pet/assets/ui/`; the packaged catalogue includes all eight IDs.
Only optical cropping and size normalization are applied to these derivatives.
The originals remain untouched. The existing MoodletStrip consumes the shared
mapping directly; no additional image loader or state owner is introduced.

[validation.json](validation.json) records source hashes, alpha bounds,
dimensions and export coverage. All 54 earlier source/control hashes match
their previous catalogue. Visual review covered all originals and a contact
sheet showing 24/32/48 px derivatives on the approved pale rose/white UI colors.
The small silhouettes remain distinguishable; fine facial/finger details are
secondary at 24 px. This does not claim native application acceptance.

The subsequent integration check constructed the real native MoodletStrip with
all 26 families and verified every displayed 40 px image against its assigned
PNG, without changing pet state or opening a user save. Twenty-five targeted
asset/emotional-view/menu tests, scoped Ruff and strict Mypy checks passed.

The labeled review sheet is deliberately outside Git, alongside other local
design previews: `E:/aiko-desktop-pet/design-previews/moodlets-2026-10-25/overview.png`.
These files extend the existing UI artwork origin record; they do not amend
the project's existing licensing terms.
