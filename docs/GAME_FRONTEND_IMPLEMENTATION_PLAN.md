# Spieloberflächen und Aikos Auftritte — Umsetzungsplan

Stand: 30.10.2026. **Native implementation delivered; validation recorded below.**

Dieser Plan überträgt die sechs freigegebenen Entwürfe aus
[UI_VN_DESIGN.md](UI_VN_DESIGN.md) in die bestehende Python/Tk-Anwendung.
Nach der Planung hat der Nutzer den Einbau in kleinen Commits beauftragt.
Keine neue Bildgenerierung, kein Push oder Merge.

## Quiz moderation reading-time correction — 2026-10-30

Owner playtesting found that the shared brisk game timing was too short for
Aiko's central quiz-host narration. QuizSequence now uses the dedicated
GamePacing.quiz_text_ms policy for every spoken text: greeting, question,
individual options, release, acknowledgement, outcome, catalogue explanation,
meta-comment and waiting reminder/repeated question.

Quiz text gets 500 ms plus 35 ms per character, bounded to 1.4–5 seconds per
bubble segment (previously 180 ms plus 25 ms, bounded to 0.75–3.2 seconds).
Long content still splits into complete segments and the visible bubble and
its continuation use the same deadline. Emoji interludes remain 450 ms and
the other five games retain their brisk pacing. No catalogue, speech copy,
quiz rule, save, visual asset or layout was changed.

The established moderation gates are preserved: question → A/B/C/D one at a
time → complete release cue → player choice. Explanation and host aside still
finish before Next Question. Waiting remains untimed and selection interrupts
its pose/reminder immediately. Close invalidates queued reading parts.

All 26 focused Quiz/pacing/cancellation checks pass. Three native host scenarios
also pass with timestamped traces, including actual question and short-answer
bubble identity beyond the old deadlines, hidden future options, blocked early
selection and automatic waiting without hover. A sampled short catalogue question
reached choice after approximately 14.5 seconds including welcome and release.
Ruff, strict Mypy (385 files) and Pyright pass. Evidence is local-only under
`../lokale-daten/quiz-reading-time-2026-10-30/`.

The frozen native regression suite passes **2,516 tests** in 434.171 seconds,
with no Python/JSON source changes during the run. The pacing change and its
regressions are committed as `791bc3f`.

## Mastermind solution visibility correction — 2026-10-30

Owner playtesting found that Aiko's solution was not visibly retained after
the round. The Sequence already revealed the correct CodeView, but the safe
only drew four tiny color lights on its closed-door frame. Opening the door
removed those lights. The earlier native assertions checked CodeView slots
and the safe frame, not a readable solution surface; they missed this defect.

MastermindWindow now projects the same public CodeView into a persistent
MastermindCodeStrip, matching the approved preview's secret strip. It shows
four question marks during play, reveals each position on the existing
180 ms reveal boundaries, and keeps the illustrated gems plus ordered German
color names visible throughout opening/eating and afterwards. Only an explicit
new round conceals it again. No secret is queried by the widget; the rules
owner still refuses any live-code reveal. Existing game art is reused, with
32px gems normally and a 24px compact variant. The body budget preserves the
large-screen ten-row layout; small windows keep their scrolling and input.

The secret itself was already constant: MastermindSession creates it once,
uses it for every submitted guess and generates another only in next_round.
An added regression checks ten different guesses, including repeated colors,
against independently stated feedback and verifies exactly one factory call
until the explicit next round. Native tests also count factory calls over all
ten attempts, inspect actual visible gem/caption items, progressive reveal,
both outcomes, persistence after the safe opens, reset and narrow-window input.

All 39 focused Mastermind checks pass. An isolated native run with white,
purple, blue and yellow also verifies readable ordering and persistence after
the snack. Captures and validation evidence remain outside Git under
`../lokale-daten/mastermind-code-reveal-2026-10-30/`.

The frozen full native suite passes **2,513 tests** in 407.082 seconds with no
Python/JSON source changes during the run. Ruff, strict Mypy (385 files) and
Pyright pass. The constant-secret regression is committed as `d49914d`; the
readable reveal and its native regressions are committed as `ab9e1a1`.

## Cross-game transition audit — 2026-10-30

Owner feedback prompted a native timing audit of the five games other than
Blackjack. Text, emoji, actual sprite completion, input release, new decisions,
round changes and close were checked with isolated saves and ControlledTkTime.
The existing game rules, opponent policies, art and physical action durations
remain unchanged.

| Game | Finding and resulting behavior |
| --- | --- |
| Fingerduell | Revealing Aiko's persistent hand rebuilt the bubble and immediately erased “Papier!”. The hand is now installed before the word. The third word stays visible from 2.25 to 2.70 seconds, followed by the 0.45-second emoji and result text at 3.15 seconds. Choosing again at reveal still interrupts the old recovery immediately. |
| Tic-Tac-Toe | The same assessment could restart when Aiko moved after 1.4 seconds. An assessment already being read now keeps its original deadline; its optional emoji follows once. Accepted input and a new round clear the old visible comment, including a new round started by the player. |
| Vier gewinnt | An effect-owned delayed gaze reset could run during the next turn. Landing focus and its cancellable return now belong to the Sequence/window path. Moving the window retargets the landed cell rather than an earlier search cell. Pickup, throw, flight and drop timing are preserved. |
| Mastermind | Code feedback, emoji, announcement, safe opening, eating and final comment already follow their actual completion boundaries. Win and loss both reach the cosmetic snack ending; no satiety is added. Progress comments share the corrected single-pass commentary lifecycle. |
| Quiz | Question and A/B/C/D reveals, release, selection, resolution and explanation retain their order. Superseded reading/wait callbacks now validate their generation and token before touching the active timer. Selection still cancels waiting gaze/pose immediately, without hover. |

Incidental GameCommentary is text once → optional emoji → idle. It no longer
replays the entire old sentence after the emoji or remains active after expiry.
These comments never lock input. Cancellation removes completed timer ownership
and rejects callbacks from an older move. Blackjack's explicitly authored
result/aside sequence remains owned by its own Sequence.

The audit's eleven native scenarios pass, including actual “Papier!” widget
content, preserved Tic-Tac-Toe reading time with free input, both start orders,
Connect Four window movement, both Mastermind snack outcomes, close during
opening/moderation and the autonomous Quiz wait interrupted by selection.
Timestamped speech/action traces and validation logs remain local-only under
`../lokale-daten/game-transition-audit-2026-10-30/`.

The frozen native regression suite passes **2,512 tests** in 412.029 seconds,
with no Python/JSON source changes during the run. Ruff and strict Mypy
(384 files) pass; Pyright reports zero errors/warnings. Code changes are split
into `ee4d896` (RPS reveal), `ac531eb` (commentary and landing gaze) and `5472ec6`
(Quiz reading/wait cancellation). The final run validates that combined state.

## Runtime presentation and repeat-round correction — 2026-10-30

Blackjack now plays its welcome only when the game window starts. Subsequent
hands keep their start/completion receipts and go directly to shuffle/deal.
A native timing check bounds that repeat-round shuffle/deal to 2.3 seconds.

The bank caption no longer paints text at a fixed coordinate on the transparent
card canvas. A separate opaque, wrapping native label reserves its measured
height, including large fonts, before placement and flight-target calculation.
The reserve uses the masked caption so flipping/revealing does not change the
footer height. Cards remain 128px; masked totals remain concealed during flip.

Kenney emote PNGs already contain a speech bubble and tail. During game emoji
interludes they now render on transparency without a second VN panel or drawn
tail. Text still uses the VN panel. The text/emoji viewport remains stable and
the persistent RPS hand stays visible in its own readout region.

Focused tests cover actual native caption bounds at Tk font scaling 1.0, 1.67
and 2.67, emoji-only and emoji-plus-hand transitions, repeat-round moderation,
masked totals and cancellation. Native captures and final validation evidence
remain local under `../lokale-daten/game-presentation-fixes-2026-10-30/`.
Complete frozen native suite: **2,504 tests pass** in 408.797 seconds, with no
Python/JSON source changes during the run. Ruff and strict Mypy (384 files) pass;
Pyright reports zero errors/warnings. An additional fresh-process large-font
capture measured a 32px font line height and a fully fitting 74px caption area.
The one-time Blackjack greeting is committed as `2c19967`; the shared emoji and
caption rendering fixes accompany this validation.

## Runtime pacing correction — 2026-10-30

Subsequent owner feedback supersedes the earlier preview reading-time and
Blackjack restart timings. All six games now share `ui/common/game_pacing.py`;
game cues no longer inherit the 4–10 second social-conversation estimates.
The displayed bubble and its phase deadline use the same duration.

| Cue | Current duration |
| --- | --- |
| Game text | 0.75–3.2 seconds, proportional to text length |
| Emoji interlude | 0.45 seconds |
| Blackjack single-card flight | 0.32 seconds (previously 0.62) |
| Blackjack shuffle / gather | 0.9 / 0.45 seconds |
| Blackjack revealed-hole-card flip / bank gap | 0.2 / 0.1 seconds |
| Blackjack restart countdown after the restored aside | 0.9 seconds |

Game text bubbles use the approved VN panel artwork through PanelSurface, including
a speech tail and the persistent RPS hand region. The Windows color-key export
preserves every source RGB value and only prepares binary alpha. The original
asset and ordinary social-conversation timing remain unchanged.

GameEffects configures and raises each native overlay only at creation, and
updates images/positions/captions only when changed. Deck input is bound once.
Flying-card flips retain the centre of their 128px card plane; hidden cards stay
backs throughout. Existing phase order, moderation, rules and completion receipts
are preserved. Controlled native measurements reached the first player decision
at 4.82 seconds for a sampled Blackjack hand and 8.9 seconds for a sampled quiz
question; quiz duration still depends on question/answer length.

Complete native suite: **2,502 tests pass** in 429.061 seconds, with no Python/JSON
source changes during the frozen run. Ruff and strict Mypy (384 files) pass;
Pyright reports zero errors/warnings. Native captures and pacing checks pass.
Timing/flight changes are committed as `215c406`; the prepared bubble and cached
window rendering are the accompanying visual fix. Evidence is local-only under
`../lokale-daten/game-pacing-2026-10-30/` relative to the checkout.

## Delivery and validation — 2026-10-30

All six approved game frontends are integrated with the existing domain owners.
Player windows stay stationary and draggable; only Aiko's presentation follows
her. Existing Blackjack card files, game rules, opponent policies, catalogue
questions and completion/reward ownership are preserved. No new character art,
World inventory object, persistent game state, push or merge was introduced.

| Step | Delivered commit |
| --- | --- |
| G0: shared action/gaze/speech ports | `a23bba5` |
| G1: Fingerduell | `8d46c58` |
| G2: Denkbrett | `7008920` |
| G3: Vier gewinnt | `6de74a9` |
| G4: Mastermind | `264571d` |
| G5: Blackjack | `a475e10` |
| G6: Quizshow | `c0f21e0` |
| Native card test correction | `1a43e59` |
| Final cancellation, stand acknowledgement and composition cleanup | `89dc35f` |
| Quizshow cream/gold question-frame polish | `94338ed` |

Validation of the final runtime state:

- Complete local suite at `89dc35f`: **2,474 tests pass** in 543.464 seconds. A source-hash
  check confirms no Python/JSON inputs changed during this final run.
- Ruff passes; strict Mypy passes for 382 files; Pyright reports zero errors and
  warnings. The 640-line composition-root guard remains intact: game speech and
  presentation wiring now belong to the desktop game assembly.
- An independent clean Git export passes strict Mypy for 379 files and all 26
  architecture checks and all **43 native game-surface checks**. These checks
  are independent of the preserved uncommitted Social work.
- The subsequent cosmetic question-frame correction (`94338ed`) passes all
  23 quiz checks, Ruff, scoped strict Mypy and the complete Pyright gate. The
  final Quizshow panel was captured and inspected again.
- Actual Windows/Tk panels for all six games were captured and inspected using
  temporary saves. Controlled native checks cover action markers, moving flight
  targets, fixed player windows, 1x/2x card-size consistency, close/reopen cleanup,
  cosmetic snack completion and automatic quiz waiting without hover.
- Full logs, clean-export checks and native captures remain outside Git in
  `../lokale-daten/game-frontend-implementation-2026-10-30/`, relative to the
  checkout. The external approved preview bundles remain unchanged.

Broader manual acceptance across physical monitors and Windows DPI settings is
still separate from these controlled native checks. In particular, the owner
should judge animation rhythm and layout feel in the normal desktop session.
The approved older action/directional artwork remains visually distinct from
newer frontal V3 expressions; it was reused without regeneration.

## Implementation log

The remaining-work statements in these milestone notes describe their original
point in the delivery sequence; the final state is recorded above.

- G0 foundation: the existing sprite clock now admits cancellable finite game
  actions with actual frame markers and exact requested duration. Game gaze
  uses the existing body-orientation policy; a persistent RPS hand can share
  the existing bubble with text/emote. No second sprite or speech clock.
  Validation: 3 new playback checks, 7 speech checks, 20 animation-runtime
  checks and 29 existing native sprite checks pass. Remaining G0 integrations
  are exercised with each game below; G1–G6 are not yet delivered.
- G1 Fingerduell: approved mat and transparent hand exports installed. Selection
  immediately shows the player hand; three complete 900 ms Attack cycles emit
  words on their real frame-04 markers, reveal on cycle three and permit a new
  choice during recovery. Native clock/GUI, input, surface-layout and expression
  checks pass; the actual Windows panel was captured and inspected outside Git.
  Shared G0 commit: `a23bba5`. G2–G6 remain pending.
- G2 Denkbrett: accepted frame, warm cells, 1400 ms thinking, live board target
  gaze and interruption-safe comment/emote cues installed. Public-board analysis
  classifies threats, forks and genuine mistakes without changing the opponent.
  All reachable open boards from either starter were checked for truthful draw
  statements; 13 TTT tests and the existing input/layout/runtime checks pass.
  New game-role lines are isolated in `events/game_frontends.json`; original
  dialogue definitions are preserved. Native panel inspected. G3–G6 pending.
- G3 Vier gewinnt: full illustrated frame with registered alpha holes, custom
  chips and red desktop stack installed. Actual pickup markers drive hand masks,
  release, a single board-clearing parabola and velocity-continuous fall behind
  the board face. The player window can move during flight without moving Aiko.
  Player-phase comments no longer lock legal columns. Validation: 6 sequence,
  6 native GUI, 2 ballistic geometry and 3 sprite-clock checks pass; native panel
  inspected, including a moved-window throw and close/cleanup. G4–G6 pending.
- G4 Mastermind: canonical safe presenter replaces the desktop code strip;
  33 registered door phases play over 1560 ms. Symbol gems and the lavender/gold
  console are installed. Win and spare-key endings use the same cosmetic donut
  and original eating anchors/timings; no care action is invoked. Draft editing
  cancels incidental comments without hinting at secret positions. Validation:
  5 sequence, 13 input, 13 native GUI and 6 expression-event checks pass, including
  snack completion, preserved care values, pending-result boundaries and close
  during opening. Native floating props use binary alpha with unchanged RGB.
  G5–G6 and final full-suite/static/Windows acceptance remain pending.

- G5: Landing-based Blackjack choreography uses one interactive deck to Aiko's
  right and the bank to her left; all cards use 128px surfaces. Existing rules,
  deck and rewards are retained. Readable result, aside, emoji, restore and
  countdown precede gather/shuffle. Native tests cover moved endpoints, scale,
  cancellation and repeated rounds. G6 remained at this milestone.
- G6: Quizshow stage, centered answer podiums, question cues and ten progress
  lights are installed. The host reads the full local catalogue question and
  each answer before releasing input. Selection, suspense, visible correctness,
  catalogue explanation, personal aside and explicit next are separate phases.
  No-hover waiting/gaze and the finite existing hands-together gesture cancel
  on selection. Focused quiz checks: 23 pass, including actual desktop-host
  presentation and interruption. The final full-suite/static results are recorded above.

## Ziel und Referenzen

Die Spielerfenster erhalten ihre jeweilige Spielidentität innerhalb der
gemeinsamen weißen/roséfarbenen VN-Oberfläche. Aiko bleibt auf dem Desktop und
spielt ihre vereinbarte Rolle mit Bubble, Blickführung, Mimik und vorhandenen
Körperaktionen. Die HTML-Seiten sind visuelle und funktionale Referenzen;
ihre JavaScript-Regelkerne, Beispieldaten und Timer werden nicht importiert.

Alle folgenden Pfade liegen relativ zum Checkout im übergeordneten Ordner
`../design-previews/`. Der [Handoff](UI_PREVIEW_HANDOFF.md) und die jeweiligen
`approval-record.json` bestimmen zusammen die aktuelle Referenz.

| Spiel | Freigegebene aktuelle Vorschau | Kern der Übernahme |
| --- | --- | --- |
| Schere–Stein–Papier | `rps-animation-2026-10-28/preview.html` | Ruhiges Fingerduell, Handmatte, drei Armzyklen, anhaltende Hand in der Bubble |
| Tic-Tac-Toe | `ttt-v3-2026-10-28/preview.html` | Kleines Denkbrett, verständliche Gewinnwege, übertrieben ernste Chibi-Strategin |
| Vier gewinnt | `connect-four-v3-2026-10-28/preview.html` | Illustriertes blaues Brett, eigene Chips, Stapel und parabolischer Wurf |
| Mastermind | `mastermind-v3-2026-10-28/preview.html` | Anime-Tresor rechts, korrigierte Öffnung, beide Snackabschlüsse |
| Blackjack | `blackjack-v3-2026-10-29/preview.html` | Casino-Auftritt, Originalkarten, gemeinsamer Stapel, vollständige Ergebnisfolge |
| Quiz | `quiz-2026-10-27/preview.html` | Kleine Quizshow, geführte Moderation, Antworten einzeln sichtbar und später freigegeben |

Die jeweils früheren 2026-10-27-Referenzen bleiben zusätzlich maßgeblich für
unverändert übernommene Assets und Abläufe. Die Beispiele bleiben außerhalb
Git; nur benötigte Laufzeitassets werden später mit Herkunft/Lizenz übernommen.

## Ausgangslage nach Codeabgleich

Geprüft auf `feature/social-optimization`, HEAD `c0f3e21`, am 30.10.2026.
Parallele uncommittete Sozial-/Inhaltsarbeit bleibt unangetastet. Vor jedem
Einbauschritt Branch, Status und betroffene Schnittstellen erneut abgleichen.

| Bestehender Eigentümer | Vorhanden | Konkrete Lücke zum Entwurf |
| --- | --- | --- |
| `ui/windows/game_panel.py`, `ui/common/window_drag.py` | Gemeinsame VN-Hülle, initiale Platzierung, freies Ziehen | Spielidentität und Flächennutzung angleichen; vorhandenes unabhängiges Fensterverhalten bewahren |
| `ui/windows/game_speech.py`, `ui/pet_view/speech_presenter.py` | Text, Emotes, RPS-Hand und Mimikereignisse | Text/Emote ersetzt aktuell die ganze Bubble; RPS braucht eine beständige Handregion darunter |
| `ui/windows/*_sequence.py` | Eigene Abläufe, Timer, Ergebnisereignisse | Mehrphasige Moderation, Lesedauer, Bewegung und abbrechbares Warten verbinden |
| `desktop/animation_runtime.py`, `pet/animation/`, `ui/pet_view/animated_pet.py` | Blick, Körperorientierung, Aktionen und installierte Mimik | Schmaler Spielauftrag für reale Blickziele und Aktionsmarker statt direkter Spritezugriffe |
| `BlackjackSequence`, `BlackjackHandPresenter` | Maskierte Bankhand, Flip, Bankregeln, 2,8-s-Neustart | Gemeinsamer rechter Stapel, gleich große Karten, Mischen/Austeilen/Rückflug und späterer Pausenbeginn |
| `ConnectFourSequence` | Bankzug-Suche und kurzer Fall im Brett | Aufheben, Handkontakt, Wurf über das Brett und anschließender Fall |
| `MastermindSequence`, `MastermindCodePresenter` | Versuchsauswertung und schrittweiser Code-Reveal | Tresor statt alleiniger Codeleiste, echte Öffnungsfolge und kosmetischer Snackabschluss |
| `QuizSequence`, `QuizWindow` | Lokaler Katalog, Antwortauswahl, Erklärung, Weiteraktion | Bisher alle Antworten zusammen; Auswahl löst sofortige Ergebnisdarstellung aus, statt erst Moderation/Spannung |
| `games/`, `application/game_experience.py` | Regelwahrheit, Ergebnisdaten, einmalige Auswertung | Bewahren; Darstellung darf keine zweite Partie oder Belohnungslogik erzeugen |

RPS verwendet derzeit einen 1–2–3-Ablauf und schaltet Eingaben erst nach der
Ergebnisreaktion frei. TTT hat derzeit eine 650-ms-Denkpause; die freigegebene
Vorschau zeigt 1400 ms. Diese Abweichungen werden ausdrücklich migriert.
Die vorhandenen Spiele werden nicht neu implementiert.

## Verbindliche Grenzen

- Spielerfenster bleiben nach dem Öffnen stehen und frei verschiebbar. Nur
  Aikos Anzeigen und zugehörige Desktop-Requisiten folgen ihrem Anker.
  Kein zweiter Positions-/Bewegungsschreiber für Aiko.
- `games/` besitzt Regeln, geheime Daten, legale Züge und Ergebniswahrheit.
  Die Sequence besitzt Ablaufphase und Eingabefreigaben; Views zeichnen
  freigegebene Projektionen. Präsentation bekommt keine unnötigen Geheimdaten.
- `HoverUi` bleibt Eigentümer der einen Spielinstanz. `GameSpeech` nutzt den
  bestehenden `SpeechPresenter`; keine zweite Sprechblase oder zweite PetMind.
- Gaze-/Mimikaufträge gehen durch die bestehende Animationspriorität. Aktionen
  wie Aufheben, Werfen oder Essen dürfen nicht von verspäteter Mimik überschrieben
  werden. Keine direkten PNG-Wechsel aus einer Spiel-Sequence.
- Regelabschluss, sichtbare Veröffentlichung und kosmetischer Nachlauf sind
  getrennt. Bestehende `GameRoundEvent`-/Summary-/Experience-Wege genau einmal
  verwenden. Abbruch nach einem echten Abschluss darf ihn weder verlieren noch
  erneut zählen; eine unvollständige Runde erzeugt keinen erfundenen Erfolg.
- Stapel, Karten, Chips, Tresor und Show-Snack sind Spielpräsentation. Keine
  World-Objekte, Fütterungsaktionen, Inventar-, Wunsch-, Moodlet- oder Saveeinträge.
  Der Mastermind-Snack verändert ausdrücklich keine Sättigung oder Bedürfnisse.
- Regeln, KI-Strategie, Balance, Quizkatalog und API-Verhalten bleiben erhalten.
  Kein neuer Browser-/Game-Engine-Unterbau und keine neue Laufzeitabhängigkeit.

## Reihenfolge und Arbeitspakete

Jedes Spiel wird als vollständiger vertikaler Schritt umgesetzt: benötigte
Assets, Fenster, Aikos Ablauf, Texte und Prüfungen zusammen. Keine sechs halben
Oberflächen. Erst nach fachlicher und visueller Prüfung folgt das nächste Spiel.

### G0 — Referenzen und gemeinsame Anschlüsse

1. Freigabehashes und benötigte Originaldateien prüfen. Pro Spiel eine kleine
   Assetliste mit Ziel, Zweck, Herkunft, Lizenz und Größe festlegen. SVG/CSS-Art
   aus den Referenzen für Tk reproduzierbar als Grafik/Canvas übernehmen;
   Originaldatei und Exportparameter nachvollziehbar halten. Keine Screenshots
   ganzer Menüs als Laufzeitoberfläche und keine erneute KI-Generierung.
2. `GamePanel` nur für tatsächlich gemeinsame Hülle/Status/Controls weiterführen.
   Spieltypische Brettflächen und Embleme über kleine View-Anschlüsse liefern;
   keinen wachsenden zentralen Renderer für sechs Regelwerke bauen.
3. `GameSpeech`/`SpeechPresenter` um eine spielgebundene Bubble-Komposition
   erweitern: gewöhnlich Text **oder** Emote; bei RPS zusätzlich eine dauerhaft
   reservierte Handregion. Bestehende soziale Texte, Attribution und Abbruch
   müssen unverändert funktionieren.
4. Kleine typisierte Präsentationsports an `game_contracts.py` anbinden:
   reales Blickziel, Aktionsauftrag/Marker, Effektabschluss und Abbruch.
   Die Ports und konkrete Zuständigkeit zunächst am RPS-Schritt beweisen.
   `desktop/game_assembly.py` verdrahtet nur; Animationsruntime und vorhandene
   Presenter bleiben die Effektbesitzer. Kein allgemeiner Eventbus oder neuer
   globaler Scheduler.
5. Darstellung und Ablauf haben eindeutige Lebensdauer: Session/Rundengeneration,
   abbrechbare Pflichtfolge und unabhängig unterbrechbare Wartekommentare.
   Eingabe beendet Warte-Cues sofort, ohne Spielzug/Regelwahrheit zu verwerfen.
   Der Abbruch beendet auch laufende Flüge und entfernt temporäre Overlays.
6. Sprechende Phasen verwenden die bestehende Cue-/Lesedauerberechnung und
   deren verbindliches Ende. Keine Kopie der HTML-Zeichenformel, keine zweite
   konkurrierende Deadline und kein neu vorausgesetztes TTS-System. Ein späterer
   Audiopfad muss denselben Abschlussport bedienen können.

Abnahme: ein gemeinsamer Kanal, klare Priorität Aktion → Blick/Körper → kompatible
Mimik; keine alten Timer nach Wechsel/Schließen und keine Regression von
Hauptmenü, Einstellungen oder normaler Sprache. Neue Hilfsklassen nur bei einem
konkreten gemeinsamen Bedarf; keine erzwungene Spiel-Basisklassenhierarchie.

### G1 — Schere–Stein–Papier als erster vollständiger Einbau

- Fingerduell-Matte, Titelzeichen und Handkacheln im bestehenden Fenster;
  das freigegebene Faustsymbol statt eines gegenständlichen Steins verwenden.
- Wahl startet sofort. Drei vollständige Attack-Zyklen, je 900 ms;
  Schere/Stein/Papier jeweils an Frame 04. Reveal und Zählung am dritten Marker
  (2250 ms), Ende der Bewegung bei 2700 ms. Marker über den vorhandenen
  Animationsbesitzer, nicht durch eine zweite Sprite-Uhr synchronisieren.
- Ab Reveal neue Wahl zulassen. Sie verwirft die verbleibende Bewegung/Reaktion,
  ohne die bereits abgeschlossene Runde doppelt auszuwerten. Hand bleibt bis
  zur nächsten Wahl sichtbar, während nur der Kommentarbereich wechselt.
- Kein Start-/Nächste-Runde-Button und kein Desktop-Gegenstand.

Abnahme: alle neun Handkombinationen, Eingabe vor/nach Reveal, sofortige neue
Wahl, Abbruch an jedem Marker, Fußanker und reduzierte Darstellung.

### G2 — Tic-Tac-Toe

- Blau-violettes Denkbrett mit warmen Feldern, bestehenden X/O und Gewinnlinie.
- Reale Gewinnwege, Drohungen und eigene Fehler aus dem öffentlichen Brett
  ableiten. Kleine reine Analysefunktion beim Regel-/Projektionsbesitzer, falls
  noch nötig; kein zweiter Gegner und keine erfundenen Gewinnprozente.
- Bestehende Zugprioritäten erhalten. Denkpause zur Referenz angleichen,
  kompatibler Blick zum relevanten Feld und Rückkehr zum Spieler.
- Kommentare/Emotes unterbrechen legale Spielereingaben nicht. Manueller
  Rundenwechsel und wechselnder Starter bleiben erhalten; kein Extraobjekt.

Abnahme: konkreter Gewinnweg, Blockade, eigener Fehler, Remis, Startwechsel,
legale Felder während einer Reaktion und keine Regel-/KI-Änderung.

### G3 — Vier gewinnt

- Abgenommenes illustriertes blaues Brett und eigene rote/gelbe Chips übernehmen;
  die exakte 7×6-Registrierung mit Lochmaske bewahren.
- Kleiner roter Stapel bei Aiko. Ein begrenzter Desktop-Chip-Presenter besitzt
  Stapel, Haltechip, Flug und Cleanup; Sequence besitzt die Zugfolge.
- Vorhandene Aufhebefolge mit den geprüften Handpunkten und Freistellmasken
  koordinieren. Ein Chip verlässt die Hand, fliegt in einer Parabel **über**
  das Brett zur gewählten Spalte und fällt anschließend senkrecht ins Zielfeld.
  Kein Doppelsprite an Übergängen; Geschwindigkeit am Fallübergang passend halten.
- Flugziele bei Fensterbewegung aus aktueller Geometrie beziehen. Der Wurf
  verändert Aikos Desktopposition nicht. Danach Feldblick, Fallenstellerin-
  Kommentar und Rückkehr zum Spieler. Drohungen müssen tatsächlich bestehen.

Abnahme: linke/rechte Spalte, hohe/niedrige Landung, verschobenes Fenster auch
während des Flugs, keine Eingabe im laufenden Zug, legale Eingabe während
anschließender Kommentare, Abbruch ohne verwaiste Chips/Worker-Callbacks.

### G4 — Mastermind

- Eigene Lavendel/Silber/Gold-Konsole und freigegebener Anime-Tresor rechts von
  Aiko auf gemeinsamer Bodenlinie. Bestehende Eingabe über `mastermind_drag.py`
  erhalten: aktive Zeile, Tauschen, ungültiger Drop ohne Verlust, Tastatur.
- `MastermindCodePresenter`-Verantwortung bewusst zur Tresor-/Revealansicht
  migrieren oder durch einen klar benannten Safe-Presenter ersetzen. Kein
  dauerhaft paralleler Code- und Tresorbesitzer.
- Blick/Kommentar nur aus sichtbarer aggregierter Rückmeldung; Entwurfsänderung
  eines Slots löst keine richtig/falsch-Mimik aus. Kein per-Slot-Geheimhinweis.
- Vollständige freigegebene Öffnung (1560 ms als Referenz) mit fixer Bodenlinie
  und korrekter Türkante übernehmen; kein Spiegeltrick oder bloßer Bildsprung.
- Erfolg: Spieler öffnet für Aiko. Fehlschlag: Ersatzschlüssel. Beide Enden
  führen zum Donut, danach manueller Rundenwechsel. Die vorhandene Essensfolge
  besitzt währenddessen exklusiv Sprite und Snackkontakt.

Abnahme: zehn Versuche, wiederholte Farben, Auswertung, beide Enden, richtige
Türgeometrie, Essen, Abbruch während Öffnung/Essen und unveränderte Carewerte.
Ein bereits vollständig ausgewertetes Spiel zählt auch bei abgebrochenem Gag
genau einmal über den bestehenden Abschlussweg.

### G5 — Blackjack

- Casinofläche und alle Originalkarten erhalten. Spielerhand, Bankhand,
  gemeinsamer rechter Stapel, Mischpakete und Flugkarten haben denselben
  Kartenmaßstab (128×128 in der Referenz); nicht an Aikos Figurengröße koppeln.
- `BlackjackHandPresenter` und sein typisierter Port bleiben für die Bankhand
  verantwortlich. Stapel/Kartenbewegung erhalten einen begrenzten Presenter
  und nutzen denselben Bildcache; kein zweites Deck oder eigener Zufall.
- Einsammeln → Mischgeste/Pakete → vier einzelne wechselnde Austeilungen →
  freie Wahl → Hit/Stand → angekündigter Flip → regelgebundener Bankzug.
  Karten und Summen erst bei Landung veröffentlichen. Verdeckte Karten bleiben
  in Flug, Text, Fokus-/Hilfsbeschreibungen und Zwischenansichten verborgen.
- Blick und sparsame, unterbrechbare Wartekommentare wie freigegeben.
  Ergebnisverkündung → persönlicher Nachsatz → Emoji → zurück zum Nachsatz →
  **erst dann** 2,8 s Pause → Vorbereitung der nächsten Hand.
- Keine Einsätze, Chips, neuen Blackjack-Regeln oder Nächste-Runde-Schaltfläche.
  Bestehende Flugkurven übernehmen; native Geste/Flug/Lesedauer praktisch abstimmen.

Abnahme: Naturals, Soft 17, mehrere Asse, beide Bust-Fälle, Gleichstand, lange
Hände, Verdeckung bis zum Flip, Ziehen vom echten Stapel, verschobene Ziele,
automatische nächste Hand und Abbruch in jeder Reise-/Ergebnisphase.

### G6 — Quiz

- Eigenes blau-violettes Mini-Studio mit Fragekarte, Showemblem, Fortschritts-
  lichtern und zentrierten Antwortpodesten innerhalb der VN-Hülle.
- Explizite Präsentationsphasen: Frage → A → B → C → D → Freigabe → Wahl →
  Bestätigung/Spannung → Auflösung → Katalogerklärung → Weiterfreigabe.
  Jede vollständige Antwort erscheint mit ihrer eigenen Ansage. Vorher keine
  sichtbare/fokussierbare Antwort; Platz bleibt reserviert. Bis zur Freigabe
  sind Maus und Tastatur gesperrt. Vor Auflösung keine Lösung oder Punktänderung.
- Sequence besitzt die Sichtbarkeits-/Freigabeprojektion; `QuizWindow` darf
  nicht mehr allein aus `game.selected` die Lösung vorzeitig rendern.
- Quizmasterin und Meta-Kommentare, echte Katalogfrage/-antwort/-erklärung,
  passende Blicke, Fragekarten und Emotes. Wartende Bittepose und gelegentliche
  Kommentare starten automatisch ohne Hover; Wahl unterbricht sie sofort.
- Zehn Fragen, kein Gegnerscore und kein Zeitdruck. Erklärung und Fortsetzungs-
  cue geben Nächste Frage frei; Schlussmoderation gibt Neue Quizrunde frei.

Abnahme: versteckte Optionen einschließlich Tastatur, Fragewechsel setzt alles
zurück, lange Texte, richtige/falsche Wahl, keine vorzeitige Lösung, zehnte
Frage, neuer Durchlauf und zuverlässiges Warten ohne Mausbewegung. Die bekannte
Quiz-Vorschauauffälligkeit beim Hover ausdrücklich nativ nachprüfen.

## Texte und Assets je Spielschritt

UI-Beschriftungen in `data/texts.de.json`, gesprochene Rollen-/Ergebnisvarianten
im vorhandenen Dialogkatalog mit registrierten Ereignissen und derselben
PetMind-Auswahl halten. Keine großen neuen Textlisten in Fenstern oder Effekten.
Qualitative Kommentare erhalten echte öffentliche Brett-/Rückmeldungsdaten.
Beziehung färbt Aikos Stimme, verändert aber weder Regeln noch Hinweise auf
Geheimdaten. Kein bloßer Zufallsfüller beim Warten.

Die vollständigen Beispielsets sind kein endgültiger Dialogkatalog. Pro Spiel
eine kleine vollständige Ereignismatrix mit passenden vorhandenen Reaktionen
liefern; vorhandene geschützte Katalogdefinitionen nicht pauschal ersetzen.
Die parallele Sozial-/Plaudern-Arbeit bei gemeinsamen Katalogdateien abstimmen.

Neue Laufzeitassets im jeweiligen Schritt registrieren und mit vorhandenen
Bildcaches laden. Nur konkret verwendete Varianten übernehmen. Vorhandene
Blackjack-Karten bleiben bytegleich; private große Charakteroriginale und
komplette HTML-Vorschaupakete gehören nicht ins Repository.

## Prüfung und Abschlusskriterien

Pro Schritt fokussierte Sequence-/Projektions-/GUI-Tests erweitern; bestehende
Regeltests als Regression nutzen. Besonders prüfen: falsche Phase, Doppelklick,
erneute Eingabe während Nachlauf, Abbruch und bereits eingereihte alte Callbacks,
verdeckte Daten, genau einmalige Zählung und unvollständige Runde.

Vorhandene Testgruppen sind unter anderem `test_rock_paper_scissors_*`,
`test_tic_tac_toe_*`, `test_connect_four_*`, `test_mastermind_*`, `test_blackjack_*`,
`test_quiz*`, `test_game_*`, `test_other_game_input`, `test_emote_sequences`,
`test_expression_*`, `test_desktop_animation_runtime` und Architekturprüfungen.
Für neue Phasen sinnvolle Grenztests ergänzen; keine reinen Layoutkopie-Tests.

Nach allen Spielschritten einmal die vollständigen Repository-Gates:

```powershell
python -m ruff check aiko_pet tests main.py tools
python -m mypy --strict --no-incremental aiko_pet main.py tools
python -m pyright --project pyrightconfig.json
python -m unittest discover -s tests -q
```

Gezielte Gates je Schritt früher ausführen. Reproduzierbare bestehende Fehler
von neuen Regressionen trennen; kein grünes Gesamtergebnis behaupten, solange
eine vorgeschriebene Prüfung fehlt.

Praktische Windows/Tk-Abnahme mit isoliertem Save: 1×/2× Aiko, 100/125/150/200 %
DPI soweit verfügbar, kleine Arbeitsfläche und mehrere Monitore, Randplatzierung,
Verschieben während Effekten, Taskleiste, Fokus/Tastatur, Topmost, Close/Escape,
erneutes Öffnen und Shutdown. Kein normaler Spielstand für Tests. Vollständige
Vergleichsbilder mit der jeweiligen Referenz machen; Headless-Tests ersetzen
die tatsächliche Eingabe- und Sichtprüfung nicht.

Abgeschlossen ist ein Spiel erst, wenn Referenznähe, Rolle, Eingaberegeln,
Lebensdauer und native Anker zusammen passen. Dokumentation und Assetherkunft
je Schritt aktualisieren, kleine klar abgegrenzte Commits erstellen, parallele
Arbeit niemals mitstagen. Kein Push oder Merge ohne eigenen Auftrag.

## Nächster Auftrag

Nach Freigabe des Einbaus mit **G0 und G1 (RPS)** beginnen. Danach in der obigen
Reihenfolge weiterarbeiten. Dieser Plan legt die Umsetzung fest; er führt sie
noch nicht aus. Es wird kein neuer Mechanik-/Assetentwurf benötigt, um G0/G1
konkret zu beginnen. Native Details werden am jeweiligen geprüften Spiel gelöst.
