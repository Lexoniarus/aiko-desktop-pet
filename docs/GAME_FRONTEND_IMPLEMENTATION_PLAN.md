# Spieloberflächen und Aikos Auftritte — Umsetzungsplan

Stand: 30.10.2026. **Einbau beauftragt; schrittweise Umsetzung läuft.**

Dieser Plan überträgt die sechs freigegebenen Entwürfe aus
[UI_VN_DESIGN.md](UI_VN_DESIGN.md) in die bestehende Python/Tk-Anwendung.
Nach der Planung hat der Nutzer den Einbau in kleinen Commits beauftragt.
Keine neue Bildgenerierung, kein Push oder Merge.

## Implementation log

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
