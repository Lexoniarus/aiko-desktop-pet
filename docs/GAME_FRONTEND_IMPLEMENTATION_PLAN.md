# SpieloberflÃ¤chen und Aikos Auftritte â€” Umsetzungsplan

Stand: 30.10.2026. **Einbau beauftragt; schrittweise Umsetzung lÃ¤uft.**

Dieser Plan Ã¼bertrÃ¤gt die sechs freigegebenen EntwÃ¼rfe aus
[UI_VN_DESIGN.md](UI_VN_DESIGN.md) in die bestehende Python/Tk-Anwendung.
Nach der Planung hat der Nutzer den Einbau in kleinen Commits beauftragt.
Keine neue Bildgenerierung, kein Push oder Merge.

## Implementation log

- G5: Landing-based Blackjack choreography, one interactive desktop deck to Aiko's right, bank to her left, all card faces at 128px. Existing rules/deck/rewards retained; readable result, aside, emoji, restore and countdown precede gather/shuffle. Native controlled tests cover moving endpoints, scale, cancellation and repeated rounds. G6 remains.

- G0 foundation: the existing sprite clock now admits cancellable finite game
  actions with actual frame markers and exact requested duration. Game gaze
  uses the existing body-orientation policy; a persistent RPS hand can share
  the existing bubble with text/emote. No second sprite or speech clock.
  Validation: 3 new playback checks, 7 speech checks, 20 animation-runtime
  checks and 29 existing native sprite checks pass. Remaining G0 integrations
  are exercised with each game below; G1â€“G6 are not yet delivered.
- G1 Fingerduell: approved mat and transparent hand exports installed. Selection
  immediately shows the player hand; three complete 900 ms Attack cycles emit
  words on their real frame-04 markers, reveal on cycle three and permit a new
  choice during recovery. Native clock/GUI, input, surface-layout and expression
  checks pass; the actual Windows panel was captured and inspected outside Git.
  Shared G0 commit: `a23bba5`. G2â€“G6 remain pending.
- G2 Denkbrett: accepted frame, warm cells, 1400 ms thinking, live board target
  gaze and interruption-safe comment/emote cues installed. Public-board analysis
  classifies threats, forks and genuine mistakes without changing the opponent.
  All reachable open boards from either starter were checked for truthful draw
  statements; 13 TTT tests and the existing input/layout/runtime checks pass.
  New game-role lines are isolated in `events/game_frontends.json`; original
  dialogue definitions are preserved. Native panel inspected. G3â€“G6 pending.
- G3 Vier gewinnt: full illustrated frame with registered alpha holes, custom
  chips and red desktop stack installed. Actual pickup markers drive hand masks,
  release, a single board-clearing parabola and velocity-continuous fall behind
  the board face. The player window can move during flight without moving Aiko.
  Player-phase comments no longer lock legal columns. Validation: 6 sequence,
  6 native GUI, 2 ballistic geometry and 3 sprite-clock checks pass; native panel
  inspected, including a moved-window throw and close/cleanup. G4â€“G6 pending.
- G4 Mastermind: canonical safe presenter replaces the desktop code strip;
  33 registered door phases play over 1560 ms. Symbol gems and the lavender/gold
  console are installed. Win and spare-key endings use the same cosmetic donut
  and original eating anchors/timings; no care action is invoked. Draft editing
  cancels incidental comments without hinting at secret positions. Validation:
  5 sequence, 13 input, 13 native GUI and 6 expression-event checks pass, including
  snack completion, preserved care values, pending-result boundaries and close
  during opening. Native floating props use binary alpha with unchanged RGB.
  G5â€“G6 and final full-suite/static/Windows acceptance remain pending.

## Ziel und Referenzen

Die Spielerfenster erhalten ihre jeweilige SpielidentitÃ¤t innerhalb der
gemeinsamen weiÃŸen/rosÃ©farbenen VN-OberflÃ¤che. Aiko bleibt auf dem Desktop und
spielt ihre vereinbarte Rolle mit Bubble, BlickfÃ¼hrung, Mimik und vorhandenen
KÃ¶rperaktionen. Die HTML-Seiten sind visuelle und funktionale Referenzen;
ihre JavaScript-Regelkerne, Beispieldaten und Timer werden nicht importiert.

Alle folgenden Pfade liegen relativ zum Checkout im Ã¼bergeordneten Ordner
`../design-previews/`. Der [Handoff](UI_PREVIEW_HANDOFF.md) und die jeweiligen
`approval-record.json` bestimmen zusammen die aktuelle Referenz.

| Spiel | Freigegebene aktuelle Vorschau | Kern der Ãœbernahme |
| --- | --- | --- |
| Schereâ€“Steinâ€“Papier | `rps-animation-2026-10-28/preview.html` | Ruhiges Fingerduell, Handmatte, drei Armzyklen, anhaltende Hand in der Bubble |
| Tic-Tac-Toe | `ttt-v3-2026-10-28/preview.html` | Kleines Denkbrett, verstÃ¤ndliche Gewinnwege, Ã¼bertrieben ernste Chibi-Strategin |
| Vier gewinnt | `connect-four-v3-2026-10-28/preview.html` | Illustriertes blaues Brett, eigene Chips, Stapel und parabolischer Wurf |
| Mastermind | `mastermind-v3-2026-10-28/preview.html` | Anime-Tresor rechts, korrigierte Ã–ffnung, beide SnackabschlÃ¼sse |
| Blackjack | `blackjack-v3-2026-10-29/preview.html` | Casino-Auftritt, Originalkarten, gemeinsamer Stapel, vollstÃ¤ndige Ergebnisfolge |
| Quiz | `quiz-2026-10-27/preview.html` | Kleine Quizshow, gefÃ¼hrte Moderation, Antworten einzeln sichtbar und spÃ¤ter freigegeben |

Die jeweils frÃ¼heren 2026-10-27-Referenzen bleiben zusÃ¤tzlich maÃŸgeblich fÃ¼r
unverÃ¤ndert Ã¼bernommene Assets und AblÃ¤ufe. Die Beispiele bleiben auÃŸerhalb
Git; nur benÃ¶tigte Laufzeitassets werden spÃ¤ter mit Herkunft/Lizenz Ã¼bernommen.

## Ausgangslage nach Codeabgleich

GeprÃ¼ft auf `feature/social-optimization`, HEAD `c0f3e21`, am 30.10.2026.
Parallele uncommittete Sozial-/Inhaltsarbeit bleibt unangetastet. Vor jedem
Einbauschritt Branch, Status und betroffene Schnittstellen erneut abgleichen.

| Bestehender EigentÃ¼mer | Vorhanden | Konkrete LÃ¼cke zum Entwurf |
| --- | --- | --- |
| `ui/windows/game_panel.py`, `ui/common/window_drag.py` | Gemeinsame VN-HÃ¼lle, initiale Platzierung, freies Ziehen | SpielidentitÃ¤t und FlÃ¤chennutzung angleichen; vorhandenes unabhÃ¤ngiges Fensterverhalten bewahren |
| `ui/windows/game_speech.py`, `ui/pet_view/speech_presenter.py` | Text, Emotes, RPS-Hand und Mimikereignisse | Text/Emote ersetzt aktuell die ganze Bubble; RPS braucht eine bestÃ¤ndige Handregion darunter |
| `ui/windows/*_sequence.py` | Eigene AblÃ¤ufe, Timer, Ergebnisereignisse | Mehrphasige Moderation, Lesedauer, Bewegung und abbrechbares Warten verbinden |
| `desktop/animation_runtime.py`, `pet/animation/`, `ui/pet_view/animated_pet.py` | Blick, KÃ¶rperorientierung, Aktionen und installierte Mimik | Schmaler Spielauftrag fÃ¼r reale Blickziele und Aktionsmarker statt direkter Spritezugriffe |
| `BlackjackSequence`, `BlackjackHandPresenter` | Maskierte Bankhand, Flip, Bankregeln, 2,8-s-Neustart | Gemeinsamer rechter Stapel, gleich groÃŸe Karten, Mischen/Austeilen/RÃ¼ckflug und spÃ¤terer Pausenbeginn |
| `ConnectFourSequence` | Bankzug-Suche und kurzer Fall im Brett | Aufheben, Handkontakt, Wurf Ã¼ber das Brett und anschlieÃŸender Fall |
| `MastermindSequence`, `MastermindCodePresenter` | Versuchsauswertung und schrittweiser Code-Reveal | Tresor statt alleiniger Codeleiste, echte Ã–ffnungsfolge und kosmetischer Snackabschluss |
| `QuizSequence`, `QuizWindow` | Lokaler Katalog, Antwortauswahl, ErklÃ¤rung, Weiteraktion | Bisher alle Antworten zusammen; Auswahl lÃ¶st sofortige Ergebnisdarstellung aus, statt erst Moderation/Spannung |
| `games/`, `application/game_experience.py` | Regelwahrheit, Ergebnisdaten, einmalige Auswertung | Bewahren; Darstellung darf keine zweite Partie oder Belohnungslogik erzeugen |

RPS verwendet derzeit einen 1â€“2â€“3-Ablauf und schaltet Eingaben erst nach der
Ergebnisreaktion frei. TTT hat derzeit eine 650-ms-Denkpause; die freigegebene
Vorschau zeigt 1400 ms. Diese Abweichungen werden ausdrÃ¼cklich migriert.
Die vorhandenen Spiele werden nicht neu implementiert.

## Verbindliche Grenzen

- Spielerfenster bleiben nach dem Ã–ffnen stehen und frei verschiebbar. Nur
  Aikos Anzeigen und zugehÃ¶rige Desktop-Requisiten folgen ihrem Anker.
  Kein zweiter Positions-/Bewegungsschreiber fÃ¼r Aiko.
- `games/` besitzt Regeln, geheime Daten, legale ZÃ¼ge und Ergebniswahrheit.
  Die Sequence besitzt Ablaufphase und Eingabefreigaben; Views zeichnen
  freigegebene Projektionen. PrÃ¤sentation bekommt keine unnÃ¶tigen Geheimdaten.
- `HoverUi` bleibt EigentÃ¼mer der einen Spielinstanz. `GameSpeech` nutzt den
  bestehenden `SpeechPresenter`; keine zweite Sprechblase oder zweite PetMind.
- Gaze-/MimikauftrÃ¤ge gehen durch die bestehende AnimationsprioritÃ¤t. Aktionen
  wie Aufheben, Werfen oder Essen dÃ¼rfen nicht von verspÃ¤teter Mimik Ã¼berschrieben
  werden. Keine direkten PNG-Wechsel aus einer Spiel-Sequence.
- Regelabschluss, sichtbare VerÃ¶ffentlichung und kosmetischer Nachlauf sind
  getrennt. Bestehende `GameRoundEvent`-/Summary-/Experience-Wege genau einmal
  verwenden. Abbruch nach einem echten Abschluss darf ihn weder verlieren noch
  erneut zÃ¤hlen; eine unvollstÃ¤ndige Runde erzeugt keinen erfundenen Erfolg.
- Stapel, Karten, Chips, Tresor und Show-Snack sind SpielprÃ¤sentation. Keine
  World-Objekte, FÃ¼tterungsaktionen, Inventar-, Wunsch-, Moodlet- oder SaveeintrÃ¤ge.
  Der Mastermind-Snack verÃ¤ndert ausdrÃ¼cklich keine SÃ¤ttigung oder BedÃ¼rfnisse.
- Regeln, KI-Strategie, Balance, Quizkatalog und API-Verhalten bleiben erhalten.
  Kein neuer Browser-/Game-Engine-Unterbau und keine neue LaufzeitabhÃ¤ngigkeit.

## Reihenfolge und Arbeitspakete

Jedes Spiel wird als vollstÃ¤ndiger vertikaler Schritt umgesetzt: benÃ¶tigte
Assets, Fenster, Aikos Ablauf, Texte und PrÃ¼fungen zusammen. Keine sechs halben
OberflÃ¤chen. Erst nach fachlicher und visueller PrÃ¼fung folgt das nÃ¤chste Spiel.

### G0 â€” Referenzen und gemeinsame AnschlÃ¼sse

1. Freigabehashes und benÃ¶tigte Originaldateien prÃ¼fen. Pro Spiel eine kleine
   Assetliste mit Ziel, Zweck, Herkunft, Lizenz und GrÃ¶ÃŸe festlegen. SVG/CSS-Art
   aus den Referenzen fÃ¼r Tk reproduzierbar als Grafik/Canvas Ã¼bernehmen;
   Originaldatei und Exportparameter nachvollziehbar halten. Keine Screenshots
   ganzer MenÃ¼s als LaufzeitoberflÃ¤che und keine erneute KI-Generierung.
2. `GamePanel` nur fÃ¼r tatsÃ¤chlich gemeinsame HÃ¼lle/Status/Controls weiterfÃ¼hren.
   Spieltypische BrettflÃ¤chen und Embleme Ã¼ber kleine View-AnschlÃ¼sse liefern;
   keinen wachsenden zentralen Renderer fÃ¼r sechs Regelwerke bauen.
3. `GameSpeech`/`SpeechPresenter` um eine spielgebundene Bubble-Komposition
   erweitern: gewÃ¶hnlich Text **oder** Emote; bei RPS zusÃ¤tzlich eine dauerhaft
   reservierte Handregion. Bestehende soziale Texte, Attribution und Abbruch
   mÃ¼ssen unverÃ¤ndert funktionieren.
4. Kleine typisierte PrÃ¤sentationsports an `game_contracts.py` anbinden:
   reales Blickziel, Aktionsauftrag/Marker, Effektabschluss und Abbruch.
   Die Ports und konkrete ZustÃ¤ndigkeit zunÃ¤chst am RPS-Schritt beweisen.
   `desktop/game_assembly.py` verdrahtet nur; Animationsruntime und vorhandene
   Presenter bleiben die Effektbesitzer. Kein allgemeiner Eventbus oder neuer
   globaler Scheduler.
5. Darstellung und Ablauf haben eindeutige Lebensdauer: Session/Rundengeneration,
   abbrechbare Pflichtfolge und unabhÃ¤ngig unterbrechbare Wartekommentare.
   Eingabe beendet Warte-Cues sofort, ohne Spielzug/Regelwahrheit zu verwerfen.
   Der Abbruch beendet auch laufende FlÃ¼ge und entfernt temporÃ¤re Overlays.
6. Sprechende Phasen verwenden die bestehende Cue-/Lesedauerberechnung und
   deren verbindliches Ende. Keine Kopie der HTML-Zeichenformel, keine zweite
   konkurrierende Deadline und kein neu vorausgesetztes TTS-System. Ein spÃ¤terer
   Audiopfad muss denselben Abschlussport bedienen kÃ¶nnen.

Abnahme: ein gemeinsamer Kanal, klare PrioritÃ¤t Aktion â†’ Blick/KÃ¶rper â†’ kompatible
Mimik; keine alten Timer nach Wechsel/SchlieÃŸen und keine Regression von
HauptmenÃ¼, Einstellungen oder normaler Sprache. Neue Hilfsklassen nur bei einem
konkreten gemeinsamen Bedarf; keine erzwungene Spiel-Basisklassenhierarchie.

### G1 â€” Schereâ€“Steinâ€“Papier als erster vollstÃ¤ndiger Einbau

- Fingerduell-Matte, Titelzeichen und Handkacheln im bestehenden Fenster;
  das freigegebene Faustsymbol statt eines gegenstÃ¤ndlichen Steins verwenden.
- Wahl startet sofort. Drei vollstÃ¤ndige Attack-Zyklen, je 900 ms;
  Schere/Stein/Papier jeweils an Frame 04. Reveal und ZÃ¤hlung am dritten Marker
  (2250 ms), Ende der Bewegung bei 2700 ms. Marker Ã¼ber den vorhandenen
  Animationsbesitzer, nicht durch eine zweite Sprite-Uhr synchronisieren.
- Ab Reveal neue Wahl zulassen. Sie verwirft die verbleibende Bewegung/Reaktion,
  ohne die bereits abgeschlossene Runde doppelt auszuwerten. Hand bleibt bis
  zur nÃ¤chsten Wahl sichtbar, wÃ¤hrend nur der Kommentarbereich wechselt.
- Kein Start-/NÃ¤chste-Runde-Button und kein Desktop-Gegenstand.

Abnahme: alle neun Handkombinationen, Eingabe vor/nach Reveal, sofortige neue
Wahl, Abbruch an jedem Marker, FuÃŸanker und reduzierte Darstellung.

### G2 â€” Tic-Tac-Toe

- Blau-violettes Denkbrett mit warmen Feldern, bestehenden X/O und Gewinnlinie.
- Reale Gewinnwege, Drohungen und eigene Fehler aus dem Ã¶ffentlichen Brett
  ableiten. Kleine reine Analysefunktion beim Regel-/Projektionsbesitzer, falls
  noch nÃ¶tig; kein zweiter Gegner und keine erfundenen Gewinnprozente.
- Bestehende ZugprioritÃ¤ten erhalten. Denkpause zur Referenz angleichen,
  kompatibler Blick zum relevanten Feld und RÃ¼ckkehr zum Spieler.
- Kommentare/Emotes unterbrechen legale Spielereingaben nicht. Manueller
  Rundenwechsel und wechselnder Starter bleiben erhalten; kein Extraobjekt.

Abnahme: konkreter Gewinnweg, Blockade, eigener Fehler, Remis, Startwechsel,
legale Felder wÃ¤hrend einer Reaktion und keine Regel-/KI-Ã„nderung.

### G3 â€” Vier gewinnt

- Abgenommenes illustriertes blaues Brett und eigene rote/gelbe Chips Ã¼bernehmen;
  die exakte 7Ã—6-Registrierung mit Lochmaske bewahren.
- Kleiner roter Stapel bei Aiko. Ein begrenzter Desktop-Chip-Presenter besitzt
  Stapel, Haltechip, Flug und Cleanup; Sequence besitzt die Zugfolge.
- Vorhandene Aufhebefolge mit den geprÃ¼ften Handpunkten und Freistellmasken
  koordinieren. Ein Chip verlÃ¤sst die Hand, fliegt in einer Parabel **Ã¼ber**
  das Brett zur gewÃ¤hlten Spalte und fÃ¤llt anschlieÃŸend senkrecht ins Zielfeld.
  Kein Doppelsprite an ÃœbergÃ¤ngen; Geschwindigkeit am FallÃ¼bergang passend halten.
- Flugziele bei Fensterbewegung aus aktueller Geometrie beziehen. Der Wurf
  verÃ¤ndert Aikos Desktopposition nicht. Danach Feldblick, Fallenstellerin-
  Kommentar und RÃ¼ckkehr zum Spieler. Drohungen mÃ¼ssen tatsÃ¤chlich bestehen.

Abnahme: linke/rechte Spalte, hohe/niedrige Landung, verschobenes Fenster auch
wÃ¤hrend des Flugs, keine Eingabe im laufenden Zug, legale Eingabe wÃ¤hrend
anschlieÃŸender Kommentare, Abbruch ohne verwaiste Chips/Worker-Callbacks.

### G4 â€” Mastermind

- Eigene Lavendel/Silber/Gold-Konsole und freigegebener Anime-Tresor rechts von
  Aiko auf gemeinsamer Bodenlinie. Bestehende Eingabe Ã¼ber `mastermind_drag.py`
  erhalten: aktive Zeile, Tauschen, ungÃ¼ltiger Drop ohne Verlust, Tastatur.
- `MastermindCodePresenter`-Verantwortung bewusst zur Tresor-/Revealansicht
  migrieren oder durch einen klar benannten Safe-Presenter ersetzen. Kein
  dauerhaft paralleler Code- und Tresorbesitzer.
- Blick/Kommentar nur aus sichtbarer aggregierter RÃ¼ckmeldung; EntwurfsÃ¤nderung
  eines Slots lÃ¶st keine richtig/falsch-Mimik aus. Kein per-Slot-Geheimhinweis.
- VollstÃ¤ndige freigegebene Ã–ffnung (1560 ms als Referenz) mit fixer Bodenlinie
  und korrekter TÃ¼rkante Ã¼bernehmen; kein Spiegeltrick oder bloÃŸer Bildsprung.
- Erfolg: Spieler Ã¶ffnet fÃ¼r Aiko. Fehlschlag: ErsatzschlÃ¼ssel. Beide Enden
  fÃ¼hren zum Donut, danach manueller Rundenwechsel. Die vorhandene Essensfolge
  besitzt wÃ¤hrenddessen exklusiv Sprite und Snackkontakt.

Abnahme: zehn Versuche, wiederholte Farben, Auswertung, beide Enden, richtige
TÃ¼rgeometrie, Essen, Abbruch wÃ¤hrend Ã–ffnung/Essen und unverÃ¤nderte Carewerte.
Ein bereits vollstÃ¤ndig ausgewertetes Spiel zÃ¤hlt auch bei abgebrochenem Gag
genau einmal Ã¼ber den bestehenden Abschlussweg.

### G5 â€” Blackjack

- CasinoflÃ¤che und alle Originalkarten erhalten. Spielerhand, Bankhand,
  gemeinsamer rechter Stapel, Mischpakete und Flugkarten haben denselben
  KartenmaÃŸstab (128Ã—128 in der Referenz); nicht an Aikos FigurengrÃ¶ÃŸe koppeln.
- `BlackjackHandPresenter` und sein typisierter Port bleiben fÃ¼r die Bankhand
  verantwortlich. Stapel/Kartenbewegung erhalten einen begrenzten Presenter
  und nutzen denselben Bildcache; kein zweites Deck oder eigener Zufall.
- Einsammeln â†’ Mischgeste/Pakete â†’ vier einzelne wechselnde Austeilungen â†’
  freie Wahl â†’ Hit/Stand â†’ angekÃ¼ndigter Flip â†’ regelgebundener Bankzug.
  Karten und Summen erst bei Landung verÃ¶ffentlichen. Verdeckte Karten bleiben
  in Flug, Text, Fokus-/Hilfsbeschreibungen und Zwischenansichten verborgen.
- Blick und sparsame, unterbrechbare Wartekommentare wie freigegeben.
  ErgebnisverkÃ¼ndung â†’ persÃ¶nlicher Nachsatz â†’ Emoji â†’ zurÃ¼ck zum Nachsatz â†’
  **erst dann** 2,8 s Pause â†’ Vorbereitung der nÃ¤chsten Hand.
- Keine EinsÃ¤tze, Chips, neuen Blackjack-Regeln oder NÃ¤chste-Runde-SchaltflÃ¤che.
  Bestehende Flugkurven Ã¼bernehmen; native Geste/Flug/Lesedauer praktisch abstimmen.

Abnahme: Naturals, Soft 17, mehrere Asse, beide Bust-FÃ¤lle, Gleichstand, lange
HÃ¤nde, Verdeckung bis zum Flip, Ziehen vom echten Stapel, verschobene Ziele,
automatische nÃ¤chste Hand und Abbruch in jeder Reise-/Ergebnisphase.

### G6 â€” Quiz

- Eigenes blau-violettes Mini-Studio mit Fragekarte, Showemblem, Fortschritts-
  lichtern und zentrierten Antwortpodesten innerhalb der VN-HÃ¼lle.
- Explizite PrÃ¤sentationsphasen: Frage â†’ A â†’ B â†’ C â†’ D â†’ Freigabe â†’ Wahl â†’
  BestÃ¤tigung/Spannung â†’ AuflÃ¶sung â†’ KatalogerklÃ¤rung â†’ Weiterfreigabe.
  Jede vollstÃ¤ndige Antwort erscheint mit ihrer eigenen Ansage. Vorher keine
  sichtbare/fokussierbare Antwort; Platz bleibt reserviert. Bis zur Freigabe
  sind Maus und Tastatur gesperrt. Vor AuflÃ¶sung keine LÃ¶sung oder PunktÃ¤nderung.
- Sequence besitzt die Sichtbarkeits-/Freigabeprojektion; `QuizWindow` darf
  nicht mehr allein aus `game.selected` die LÃ¶sung vorzeitig rendern.
- Quizmasterin und Meta-Kommentare, echte Katalogfrage/-antwort/-erklÃ¤rung,
  passende Blicke, Fragekarten und Emotes. Wartende Bittepose und gelegentliche
  Kommentare starten automatisch ohne Hover; Wahl unterbricht sie sofort.
- Zehn Fragen, kein Gegnerscore und kein Zeitdruck. ErklÃ¤rung und Fortsetzungs-
  cue geben NÃ¤chste Frage frei; Schlussmoderation gibt Neue Quizrunde frei.

Abnahme: versteckte Optionen einschlieÃŸlich Tastatur, Fragewechsel setzt alles
zurÃ¼ck, lange Texte, richtige/falsche Wahl, keine vorzeitige LÃ¶sung, zehnte
Frage, neuer Durchlauf und zuverlÃ¤ssiges Warten ohne Mausbewegung. Die bekannte
Quiz-VorschauauffÃ¤lligkeit beim Hover ausdrÃ¼cklich nativ nachprÃ¼fen.

## Texte und Assets je Spielschritt

UI-Beschriftungen in `data/texts.de.json`, gesprochene Rollen-/Ergebnisvarianten
im vorhandenen Dialogkatalog mit registrierten Ereignissen und derselben
PetMind-Auswahl halten. Keine groÃŸen neuen Textlisten in Fenstern oder Effekten.
Qualitative Kommentare erhalten echte Ã¶ffentliche Brett-/RÃ¼ckmeldungsdaten.
Beziehung fÃ¤rbt Aikos Stimme, verÃ¤ndert aber weder Regeln noch Hinweise auf
Geheimdaten. Kein bloÃŸer ZufallsfÃ¼ller beim Warten.

Die vollstÃ¤ndigen Beispielsets sind kein endgÃ¼ltiger Dialogkatalog. Pro Spiel
eine kleine vollstÃ¤ndige Ereignismatrix mit passenden vorhandenen Reaktionen
liefern; vorhandene geschÃ¼tzte Katalogdefinitionen nicht pauschal ersetzen.
Die parallele Sozial-/Plaudern-Arbeit bei gemeinsamen Katalogdateien abstimmen.

Neue Laufzeitassets im jeweiligen Schritt registrieren und mit vorhandenen
Bildcaches laden. Nur konkret verwendete Varianten Ã¼bernehmen. Vorhandene
Blackjack-Karten bleiben bytegleich; private groÃŸe Charakteroriginale und
komplette HTML-Vorschaupakete gehÃ¶ren nicht ins Repository.

## PrÃ¼fung und Abschlusskriterien

Pro Schritt fokussierte Sequence-/Projektions-/GUI-Tests erweitern; bestehende
Regeltests als Regression nutzen. Besonders prÃ¼fen: falsche Phase, Doppelklick,
erneute Eingabe wÃ¤hrend Nachlauf, Abbruch und bereits eingereihte alte Callbacks,
verdeckte Daten, genau einmalige ZÃ¤hlung und unvollstÃ¤ndige Runde.

Vorhandene Testgruppen sind unter anderem `test_rock_paper_scissors_*`,
`test_tic_tac_toe_*`, `test_connect_four_*`, `test_mastermind_*`, `test_blackjack_*`,
`test_quiz*`, `test_game_*`, `test_other_game_input`, `test_emote_sequences`,
`test_expression_*`, `test_desktop_animation_runtime` und ArchitekturprÃ¼fungen.
FÃ¼r neue Phasen sinnvolle Grenztests ergÃ¤nzen; keine reinen Layoutkopie-Tests.

Nach allen Spielschritten einmal die vollstÃ¤ndigen Repository-Gates:

```powershell
python -m ruff check aiko_pet tests main.py tools
python -m mypy --strict --no-incremental aiko_pet main.py tools
python -m pyright --project pyrightconfig.json
python -m unittest discover -s tests -q
```

Gezielte Gates je Schritt frÃ¼her ausfÃ¼hren. Reproduzierbare bestehende Fehler
von neuen Regressionen trennen; kein grÃ¼nes Gesamtergebnis behaupten, solange
eine vorgeschriebene PrÃ¼fung fehlt.

Praktische Windows/Tk-Abnahme mit isoliertem Save: 1Ã—/2Ã— Aiko, 100/125/150/200 %
DPI soweit verfÃ¼gbar, kleine ArbeitsflÃ¤che und mehrere Monitore, Randplatzierung,
Verschieben wÃ¤hrend Effekten, Taskleiste, Fokus/Tastatur, Topmost, Close/Escape,
erneutes Ã–ffnen und Shutdown. Kein normaler Spielstand fÃ¼r Tests. VollstÃ¤ndige
Vergleichsbilder mit der jeweiligen Referenz machen; Headless-Tests ersetzen
die tatsÃ¤chliche Eingabe- und SichtprÃ¼fung nicht.

Abgeschlossen ist ein Spiel erst, wenn ReferenznÃ¤he, Rolle, Eingaberegeln,
Lebensdauer und native Anker zusammen passen. Dokumentation und Assetherkunft
je Schritt aktualisieren, kleine klar abgegrenzte Commits erstellen, parallele
Arbeit niemals mitstagen. Kein Push oder Merge ohne eigenen Auftrag.

## NÃ¤chster Auftrag

Nach Freigabe des Einbaus mit **G0 und G1 (RPS)** beginnen. Danach in der obigen
Reihenfolge weiterarbeiten. Dieser Plan legt die Umsetzung fest; er fÃ¼hrt sie
noch nicht aus. Es wird kein neuer Mechanik-/Assetentwurf benÃ¶tigt, um G0/G1
konkret zu beginnen. Native Details werden am jeweiligen geprÃ¼ften Spiel gelÃ¶st.
