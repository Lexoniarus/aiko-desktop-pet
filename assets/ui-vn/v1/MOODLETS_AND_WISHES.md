# Moodlet and wish artwork coverage

Prepared 2026-10-20 after the owner approved completing the documented artwork.
This is asset preparation only: the application, Moodlet rules, wishes and saves
remain unchanged. Source rules remain in the
[care/time plan](../../../docs/CARE_TIME_IMPLEMENTATION_PLAN.md), with the
[approved UI direction](../../../docs/UI_VN_DESIGN.md) governing appearance.

The initial pack had four illustrative Moodlets. This extension adds **14
Moodlet sources and five reusable wish components**, bringing the full source
pack to **46 PNGs**. The visual catalogue now covers the documented **18 Moodlet
families (eight positive, ten negative)** and all **11 wish objective forms**.
The labels below are descriptive working labels, not newly settled emotional
vocabulary or runtime identifiers.

## Moodlets

| Documented impression | Direction | Source artwork |
| --- | --- | --- |
| Genau das Gewünschte | positive | [moodlet_food_fulfilled.png](icons/moodlet_food_fulfilled.png) |
| Gemeinsame Spielfreude | positive | [moodlet_shared_play.png](icons/moodlet_shared_play.png) |
| Verbundenheit | positive | [moodlet_connection.png](icons/moodlet_connection.png) |
| Heiterkeit | positive | [moodlet_cheerful.png](icons/moodlet_cheerful.png) |
| Begeisterung | positive | [moodlet_enthusiastic.png](icons/moodlet_enthusiastic.png) |
| Zu viel Nähe | negative | [moodlet_crowded.png](icons/moodlet_crowded.png) |
| Immer dasselbe Essen | negative | [moodlet_food_monotony.png](icons/moodlet_food_monotony.png) |
| Vorenthalten | negative | [moodlet_withheld.png](icons/moodlet_withheld.png) |
| Vertrauter Platz verändert | negative | [moodlet_disrupted.png](icons/moodlet_disrupted.png) |
| Vom Hunger zermürbt | negative | [moodlet_hunger_worn.png](icons/moodlet_hunger_worn.png) |
| Von Erschöpfung gereizt | negative | [moodlet_exhaustion_irritated.png](icons/moodlet_exhaustion_irritated.png) |
| Lange unterfordert | negative | [moodlet_unstimulated.png](icons/moodlet_unstimulated.png) |
| Einsam | negative | [moodlet_lonely.png](icons/moodlet_lonely.png) |
| Nähe fehlt | negative | [moodlet_missing_closeness.png](icons/moodlet_missing_closeness.png) |
| Stolz | positive | [moodlet_pride.png](icons/moodlet_pride.png) |
| Erleichtert | positive | [moodlet_relief.png](icons/moodlet_relief.png) |
| Geborgen | positive | [moodlet_secure.png](icons/moodlet_secure.png) |
| Genervt vom Pieksen | negative | [moodlet_annoyed.png](icons/moodlet_annoyed.png) |

The existing generic Genervt face is assigned to repeated-poking annoyance.
Unwelcome closeness, withholding and disrupted arrangements have their own
cause-specific icons. The five prolonged-poor-care pictures represent emotional
after-effects, not extra copies of the ordinary need meters. These distinctions
do not create or alter domain rules.

Do not bake tags, descriptions, strength or time into PNGs. One icon per family
is sufficient; intensity levels do not require three separate images. Positive
and negative Moodlets can coexist.

## Wish components and reuse

All wishes can use the hollow [thought-bubble marker](icons/wish_thought_bubble.png).
Its empty transparent interior is reserved for a concrete target image. The
[shield](icons/wish_protection_shield.png) marks a non-loss objective.
[Spruch](icons/wish_single.png), [Witz](icons/wish_twopart.png) and
[Fakt](icons/wish_fact.png) distinguish the three corresponding content wishes.

| Documented wish form | Target / objective artwork |
| --- | --- |
| A specific food | Existing picker image of the eligible concrete food ID |
| Play a named game together | Existing game-selection emblem |
| Win a round | Game emblem plus existing trophy |
| Do not lose the next round | Game emblem plus new shield |
| Win overall | Game emblem plus trophy and UI-rendered round-block label/progress |
| Do not lose overall | Game emblem plus shield and UI-rendered round-block label/progress |
| Chat | Existing social speech bubbles |
| Tell an API Single | New Spruch symbol |
| Tell an API Two Parts | New Witz symbol |
| Share a fact | New Fakt symbol |
| Be petted | Existing petting-hand symbol |

Keep food/game target, objective badge and scope separate. Do not generate a
distinct full icon for each food or for every objective/game combination.
Blackjack's existing playing cards remain unchanged. A thought-bubble display
shows an inner wish; it does not prove that Aiko has spoken it, that an object
exists, or that the wish has been fulfilled.

The artwork does not invent punishment, new wish types or an extra generic
fulfillment Moodlet. All timing, eligibility, fulfillment and stacking remain
owned by the separate domain proposal.

## Files and verification

- [Gallery](preview.html#moodlets-wishes) includes the full Moodlet/wish groups
  with 24/32/48/64 px previews and source-image links.
- [Machine-readable mapping](catalog_mapping.json) inventories the 18 families
  and 11 forms using design-only keys.
- [Exact generation prompts](generation_prompts_moodlets_wishes.json) records
  the built-in Imagegen request for every added icon.
- [Extension generation record](generation_record_moodlets_wishes.json) records
  source-output basenames and reference paths.
- [Combined provenance](provenance.json) stores hashes, source dimensions,
  alpha checks and retained-source verification.

Generated masters remain unmodified. Later export work can normalize optical
scale and review low-alpha fringe while preserving these originals. Source-image
checks and browser previews do not establish native Windows/Tk acceptance.
