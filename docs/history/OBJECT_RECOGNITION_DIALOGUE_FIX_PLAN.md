# Object recognition and natural German dialogue fix plan

> **B2 — completed and verified on 2026-10-19.** Target: `feature/social-optimization`.
> Added on 2026-10-19 from the owner's supplied fix plan and Onigiri example.
> Track delivery in the [care/social implementation plan](../CARE_TIME_IMPLEMENTATION_PLAN.md).

## Intended behavior

1. Notice an unknown object: “Oh, da liegt ein Gegenstand!”
2. Identify it: “Ah, ein Onigiri!” If full, put it aside for later.
3. Lose it: “Hä? Wo ist denn mein Onigiri hin?”
4. Identify the first matching Onigiri during the active search:
   “Ah, da ist ja wohl mein Onigiri!” Resolve that missing subject even if
   the physical instance differs.
5. Identify another Onigiri later: “Oh, ein Onigiri!” Treat it as a new portion.

During an actual search, recognized identity/kind is sufficient for subjective
reunion; matching the internal physical instance ID is not required. An unknown
sighting cannot resolve a named search. A wrong kind (an apple during an Onigiri
search) cannot resolve it either. One identified portion resolves at most one
matching missing subject, with deterministic ordering when several match.

This is a correction within the existing search mechanism. Keep
`object_recognized` and `object_found` distinct; no second search service,
perception system or memory store is needed.

## Baseline evidence and ownership

The current `SearchTask._match()` requires equal instance IDs for subjects
with physical references; identity/kind-only matching is limited to an
unambiguous legacy subject. `_reunite()` already resolves the task and chooses
`object_found`; ordinary identification chooses `object_recognized` instead.
`format_object_reaction()` currently substitutes a bare label for `{item}`.
Catalogue validation currently permits only that object placeholder.

| Existing owner / planned file | Planned responsibility |
| --- | --- |
| `application/object_interaction_state.py` | Match one recognized candidate by identity/kind during the existing active search. |
| `application/object_interaction.py` | Coordinate reunion, the memory transition and exactly one found cue; remove that subject from pending search/feedback. |
| `pet/mind/object_memory.py` | Reconcile subjective history with the identified portion and retire the old unresolved memory consistently. |
| `pet/mind/object_stock.py` | Preserve ordinary new-instance recognition outside a search; do not globally equate equal food types. |
| `ui/view_models/object_reactions.py` | Render complete German noun phrases using known identity, without making recognition decisions. |
| `ui/view_models/german_object_phrases.py` (new) | Pure deterministic article, case and possessive inflection, reusing an existing owner if one appears before implementation. |
| `data/object_grammar.de.json` (new) | Validated grammatical gender and optional spoken-name override for the eleven consumable kinds. |
| `pet/mind/catalog.py` | Explicitly allow supported object-form placeholders; continue rejecting arbitrary expressions, conversions and format specifications. |
| `data/dialogues.de.json` | Review complete object sequences and use the correct indefinite, definite or possessive form in context. Preserve dialogue IDs. |
| `data/texts.de.json` | Use “Gegenstand” for unknown-object statements and align feeding fallbacks where applicable. |

The grammar files are proposed additions, not existing modules. Keep rendering
in presentation and resource loading/validation at the established boundary;
the domain must not import German UI grammar. Keep menu labels and canonical
nutrition/item IDs unchanged; a spoken-name override must not duplicate the
whole food catalogue.

## A. Subjective reunion and memory consistency

Part A now uses the existing search task's chronological same-kind matching and
an explicit `ObjectMemory.reunite_search()` transition. Found physical facts
remain intact; the old subjective subject is retired. Existing known stock and
already assigned findings are excluded until a newly confirmed loss reopens an
episode. Patrol reunion requires current observation, not memory alone.
The acquired-reference and association invariants round-trip through existing
memory v3 / outer save v1; no new persisted field or migration is needed.
Part A (`4757da7`, pushed) passed all 1,194 native Windows unit/Tk tests in 260.058 seconds,
Ruff, strict Mypy and Pyright. Part B and integrated C verification are recorded below.

Relaxing search matching alone is insufficient: it could announce “mein
Onigiri” while retaining the old missing entry as an unresolved memory.

- The found portion retains its actual World instance ID, custody and position.
- Transfer relevant subjective history, including the prior intention to save
  the missing portion for later, through an explicit memory-owned transition.
- Resolve and retire the previous missing subject so no orphaned search,
  pending loss feedback or duplicate subjective binding remains.
- If the original physical portion is identified later without continuous
  tracking, treat it as a new subjective exemplar. Preserve factual continuous
  observation when it actually exists; do not rewrite physical World truth.
- Keep ordinary stock recognition strict outside the active-search context.
  Define deterministic selection among several same-kind missing subjects;
  never consume one finding more than once.
- Check persisted memory/reference invariants and restart behavior. The supplied
  plan expects existing fields to suffice; verify that before deciding no save
  migration is required. Do not assert compatibility without a round-trip test.

## B. Complete German phrases and sequence review

Implemented: all 138 complete object sequences across 32 events reviewed;
82 dynamic sequences and eight other object sequences rewritten (90 changed,
48 retained). IDs, filters, emotes, pauses and non-object sequences are
unchanged. The review workbook retains baseline wording and records the
implemented replacements; its other rows are preserved. Three feeding
fallbacks are also reviewed and use complete food phrases.

The finite contract includes nominative, accusative and dative indefinite,
definite, possessive and pronoun forms, plus sentence-start capitalization.
All eleven consumables have validated gender metadata; only Energy-Drink
needs a spoken-name override. Unknown identity becomes “Gegenstand”, with
definite rather than invented possessive reference. Ordinary new identification
uses an indefinite phrase. Existing content loading owns metadata validation;
the pure UI formatter owns inflection. No change to menus or save versions.

The native Onigiri integration additionally exposed a found-item put-down
overwriting the transferred saved-for-later disposition. The existing
coordinator now passes that remembered intent to its normal safe placement;
an actual queued interruption still suppresses deferred placement.


The supplied audit describes 138 object-dialogue sequences across 32 events,
82 using `{item}` and 56 without it. Recount at implementation start and review
all object sequences, including their conditions and multi-bubble context.
These counts are a scope estimate, not a permanent catalogue constraint.

Do not mechanically replace every `{item}` with “ein {item}”. Supply explicit
forms such as `{item_indef_nom}`, `{item_indef_acc}`, `{item_poss_nom}` and
`{item_poss_acc}`. Include definite forms and other cases where the actual
sentences require them; define the supported finite set before the data edit.

| Item | Indefinite nominative | Indefinite accusative | Possessive nominative | Possessive accusative |
| --- | --- | --- | --- | --- |
| Onigiri | ein Onigiri | ein Onigiri | mein Onigiri | mein Onigiri |
| Apfel | ein Apfel | einen Apfel | mein Apfel | meinen Apfel |
| Sandwich | ein Sandwich | ein Sandwich | mein Sandwich | mein Sandwich |
| Energy-Drink | ein Energy-Drink | einen Energy-Drink | mein Energy-Drink | meinen Energy-Drink |
| Cupcake | ein Cupcake | einen Cupcake | mein Cupcake | meinen Cupcake |

Cover all eleven kinds, not just these examples. Unknown-object phrases use
“ein Gegenstand”, “einen Gegenstand” or “der Gegenstand” according to the
sentence. Ordinary expressions such as “etwas müde” and “etwas übersehen”
remain valid. Never reveal an item's name before identification. Keep the
spoken language natural and local, with no model/API dependency.

## C. Verification and documentation

Parts B and integrated regression passed **1,203 native Windows unit/Tk tests
in 271.518 seconds**, with no unittest failures, errors or skips. Ruff 0.13.2,
strict Mypy 1.18.2 (190 source files) and Pyright 1.1.414 passed. The complete
Onigiri test exercises real perception, pickup, inspection and placement,
including a different finding and later identification of the original portion.
Part A is `4757da7`; Part B and integrated regression are `b984078`, both
pushed. Part C completes the acceptance documentation without changing runtime.

A separate isolated Windows/Tk probe passed in **70.520 seconds** with **21
rendered text bubbles**. It reused the complete Onigiri integration scenario,
retained real `after` callbacks/dwell, and checked each visible native Label
against the selected, formatted text. Perception time, movement and animation
frames were driven through the existing test fixture; this was not a manual
drag/drop run. It exercised ordinary identification twice, one subjective
reunion with a different World ID, remembered deferred placement, and no
consumption while full. The normal save was never used. See the maintained
[B2 smoke record](../WORLD_SMOKE_TEST.md#b2-subjective-reunion-and-german-dialogue-2026-10-19).


| Test owner | Required checks |
| --- | --- |
| `tests/test_object_reactions.py` | Correct articles/cases for all eleven kinds, safe unknown forms and no premature name disclosure. |
| `tests/test_object_memory.py` | Different same-kind instance inherits relevant subjective history, preserves physical reference and leaves no orphaned missing record; save/restart remains valid. |
| `tests/test_object_interaction.py` | Discover → identify → put aside → miss → search → identify first matching portion → found; wrong/unknown candidates do not resolve it. |
| `tests/test_object_stock.py` | A later same-kind portion outside a search remains a new exemplar. |
| `tests/test_object_feedback_flow.py` | Found cue starts only after identification, once; animation and completion acknowledgements remain correct. |
| `tests/test_content_catalog.py` and catalogue validation tests | Valid German fallbacks, complete grammar coverage, explicit allowed placeholders and rejection of malformed/unsupported templates. |

Add regression cases for multiple missing portions, distinct kinds and a later
rediscovery of the original portion. Verify the complete Onigiri sequence in
native Windows/Tk with an isolated save. Run the repository's full suite, Ruff,
strict Mypy, Pyright and architecture/import checks before delivery.

Update `docs/WORLD_OBJECT_CONTRACTS.md`, the maintained smoke guide and
`docs/DIALOGUE_REVIEW.md` with the delivered behavior and actual reviewed
sequences. Retain the real perception, pickup/put-down, animation, nutrition
and World ownership paths. This fix changes subjective association and spoken
forms; it adds no parallel mechanism or physical identity rewrite.

Deliver A, then B, then integrated C in reviewable commits, pushing completed
increments. Schedule separately from unfinished need/mood work. The general
dialogue-rewrite exclusion in the foundation plan does not exclude the specific
object-sequence corrections authorized and recorded here.
