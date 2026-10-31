# Rejected AstroWay horoscope prototype: implementation history

The owner explicitly rejected this API prototype and decided full replacement
by the [local book version](LOCAL_HOROSCOPE_IMPLEMENTATION_PLAN.md).
**Everything below is historical delivered behavior, not a retained alternative,
fallback or instruction to implement the API again.** Preserved for retirement
and save-migration review. No code or provider behavior is retained by archiving
this documentation.

## Daily horoscope and role performance

**Rejected API prototype: historical implementation/retirement evidence only.**
The owner explicitly discarded it and decided full replacement by the local
book version. The source-preserving role performance below is not retained as
an alternative or fallback. This documentation correction does not implement
that removal yet.

The owner confirmed this design on 2026-10-23 and subsequently explicitly
authorized its implementation. The runtime, direct sign option and compatible
daily save extension now implement these rules. Tarot remains separately planned.
The [later gift and VN presentation decision](../SOCIAL_EXPANSION_PLAN.md#planned-horoscope-gift-and-vn-presentation)
is a future extension; the following sections describe the delivered API baseline,
which does not yet require or display a hat.

Use `GET https://api.astroway.info/v1/public/horoscope/daily` with an explicitly
selected `sign`, `lang=de` and the intended local calendar `date`. The reviewed
endpoint needs a zodiac sign, not birth date, birth time or birthplace.

Options belong to the existing `PetSettings` owner:

- First version: a direct selection labelled "Sternzeichen fürs Tageshoroskop",
  containing all twelve signs and "Nicht ausgewählt" as the default. No sign
  means the horoscope choice is disabled with an explanatory settings hint;
  never guess a sign.
- Store one confirmed sign as the canonical choice. Choosing a sign or opening
  settings/the menu performs no request and starts no reading.
- Birthday assistance is later work, outside the first version. It could suggest
  a sign locally from day/month for confirmation, without a birth year. Do not
  transmit a birthday or introduce a second competing sign preference. Input
  retention and exact assistance UI remain future decisions.
- Tarot and Sprüche do not require a birthday or zodiac sign.

Aiko announces entering the fortune-teller role, presents the original German
provider text, then visibly returns to her ordinary voice. The formal address
is part of this performance. Framing and role exit use du. Do not change
pronouns, conjugate verbs, claim the reading is Aiko's own observation of the
user or insert provider statements into subjective Mind/World knowledge. An
interruption ends the role immediately; resuming briefly announces re-entry.

Selected presentation order (framing examples, not runtime catalogue changes):

1. Role entry, for example: "Ich schlüpfe mal in die Rolle der Wahrsagerin. Mal
   sehen, was heute für dein Sternzeichen geschrieben steht."
2. Present the complete provider AI/entertainment disclaimer.
3. Read the complete overview and daily advice, retaining original wording and
   Sie address within the announced role.
4. Return to Aiko's ordinary voice, for example: "So, die Sterne hatten ihren
   Auftritt. Jetzt bin ich wieder deine Aiko."

Keep the original provider footer and source attribution visible with the
reading; Credits supplement them rather than replacing mandatory visible hints.
Do not offer a key/payment flow or read an English fallback as horoscope content.

### Content and twelve-bubble budget

Use complete `data.sections.overview` and `data.sections.advice`, not all six
topics or the full concatenated `data.horoscope`. Validate the successful response
envelope, daily period, German language, requested sign/date, both complete
sections, disclaimer and provider footer before admission. An HTTP 200 alone is
insufficient: the provider can return older or non-German text with fallback
metadata while computed fields still match the requested date. Check the text's
actual date/language too; reject stale or non-German fallback content without
consuming reading eligibility. See the
[public daily endpoint contract](https://api.astroway.info/en/docs/api/operations/publichoroscopedaily/).

The approved bound is **at most twelve text bubbles for one prepared horoscope
sequence**, including role entry/exit, the complete AI/entertainment disclaimer
and any spoken attribution. Every text bubble keeps the **125-character limit**.
Use the existing common reading time, final-text second and reading clicks. The
actual final text receives the allowance, normally the role exit. The earlier
eight-bubble proposal is superseded; the five-text budget for other social
content is not enlarged by this decision.

The live Widder sample for 2026-10-23 has a 371-character overview and a
201-character advice section: five content bubbles with current segmentation.
Its 231-character disclaimer takes three more. With one role-entry and one exit
bubble, that is ten text bubbles, roughly eighty seconds using the selected
reading times. This is one sizing sample, not a guarantee for every sign/day.
Reject content that cannot fit completely within twelve bubbles. Never shorten
source text, omit a required section or bypass the budget with unrelated reactions.

### Once per day and interrupted delivery

The selected rule is **one resumable daily reading per local calendar day across
all signs**, not one reading per sign. Use the user's local date (Europe/Berlin in
this planning session), with no 24-hour cooldown, offline backlog or request merely
because midnight passes. Pass the selected date explicitly; the provider's
default is UTC.

| State | Planned selection behavior |
| --- | --- |
| Not begun | "Tageshoroskop anhören"; fetch only on deliberate selection if no eligible prepared item exists. |
| Fetch/preparation failed or content rejected | Leave reading eligibility open, subject to the separate three-attempt request cap and provider pauses. |
| Interrupted | "Tageshoroskop fortsetzen"; resume the same item's interrupted bubble, without another fetch or care booking. |
| Full sequence completed, including role exit | "Heute bereits vorgelesen"; another reading is available tomorrow. |
| Restart | Restore the same daily state and any eligible continuation, without automatic playback or completion. |

- First actual playback admission fixes that day's reading and books the existing
  talk care once. Full-sequence completion marks the day completed. Continuing
  the same item repeats neither the care booking nor already completed content
  bubbles. No new reward formula or wish family is selected.
- Before playback begins, the sign may change. Invalidate any mismatching
  prepared item or in-flight result; a discarded request still counts. Once
  playback has begun, changing the preference applies from tomorrow and neither
  replaces the active item nor unlocks another reading after completion.
- A reading already playing at midnight may finish as the previous day's item;
  it must not mark the new day completed. A paused previous-day reading expires
  instead of being resumed or completed offline. Today's reading is independently
  eligible. Late fetch results must never become the new day's reading.
- Disabling online sources prevents playback/continuation and further requests,
  while retaining the daily status and already booked care. Re-enabling on the
  same day can resume the same still-eligible item, without resetting anything.

Persist a bounded daily record containing date, selected sign, validated content,
reading progress, admission/care status and completion evidence through the
existing atomic save owner. Keep settings, provider content and lifecycle evidence
distinct within that boundary, not in a second mutable store or journal. Existing
social admission receipts contain hashes/identities, not content or continuation
state. The implemented version-three social history adds exactly this bounded
daily record, while continuing to read version-one and version-two histories.
Development verification uses isolated temporary saves.

### At most three horoscope fetch attempts per day

- Normally fetch one successful item per used day and reuse it for playback or
  continuation. Opening/reopening menus and repeated clicks coalesce matching
  in-flight work; never fetch merely to prepare a second ready horoscope.
- Allow **at most three dispatched horoscope HTTP attempts per local calendar
  day**, shared across all signs. Count timeouts, HTTP errors, rejected/oversized
  content and discarded stale/sign-mismatched responses as attempts too. Each
  attempt uses the existing bounded request-admission and persistence boundary.
- Persist the attempt count independently of successful reading/completion.
  Restart, sign changes, cancellation and opt-out must not reset it. Once all
  three attempts are spent, show a retry-later/tomorrow status; an already valid
  cached reading may still play or resume within its daily eligibility.
- Retries are deliberate and paced, subject to provider pauses/Retry-After and
  the shared AstroWay public IP budget of 30 requests per sliding hour. No
  automatic endless retries, new worker, credential, paid fallback or local
  replacement horoscope is allowed. Tarot's eventual attempt policy remains
  undecided and must share the provider budget without inheriting this rule.
