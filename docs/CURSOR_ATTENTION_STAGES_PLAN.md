# Mausaufmerksamkeit: Stufen, Vorwarnung und Gefühlsreaktionen

Stand: 27.10.2026. Geprüfte Codebasis: `9a233d7` auf
`feature/social-optimization`. **Konzept und zukünftiger Umbauplan; noch nicht
implementiert.** In dieser Runde ändern sich ausschließlich Dokumente. Kein
Implementierungs-, Commit-, Push- oder Merge-Auftrag durch dieses Dokument.

Dieser Plan ersetzt widersprechende Zielregeln des
[bisherigen Cursor-/Idle-Umbaus](ADAPTIVE_CURSOR_REWORK_PLAN.md): Aufmerksamkeit
soll durch interessante Bewegung entstehen und bei langsamer Bewegung/Ruhe
abnehmen. Die bisherige Zuordnung „ruhig gehalten -> Neugier“ und die sofortige
Angsterfahrung bei schneller Annäherung reichen dafür nicht aus. Der bisherige
Umbau bleibt als geprüfte Ausgangsbasis und Verlauf erhalten, nicht als
praktische Abnahme dieses neuen Verhaltens.

## Verbindliche Trennung

1. **Reiz:** reale Zeigerbewegung, normierte Geschwindigkeit, Abstand und
   Annäherungsrichtung. Eigene Bewegung Aikos erzeugt keine Mausgeschwindigkeit.
2. **Aufmerksamkeit:** flüchtiger Wert 0–100 mit gehaltenen Stufen und Blickziel.
   Kein neues Bedürfnis, kein persistierter Wert, kein Moodlet und keine
   Freundschaftsachse. Hohe Aufmerksamkeit bedeutet noch keine Angst/Neugier.
3. **Bewertung:** Situation zusammen mit Vertrauen, Energie, Stimmung,
   Beschäftigungs- und Nähebedürfnis einordnen. Schnell kann interessant sein;
   langsam bedeutet nicht automatisch Neugier. Geringes Vertrauen allein ist
   kein Angstbeleg, hohe Freundschaft verhindert keinen echten Schreck.
4. **Erleben:** Vorwarnung und danach gegebenenfalls neue qualifizierte
   Neugier-/Angstbelege. Bestehende Moodlets sind Nachhall, keine neuen Reize.
5. **Handlung:** Kopf zuerst, später bewusste Körperdrehung und erst mit eigenem
   Anlass eine begrenzte Ortsbewegung. Der Renderer leitet daraus keine
   zusätzlichen Verhaltensentscheidungen ab.

Frontal bleiben alle 16 Kopfrichtungen verfügbar. Kopf und Körper teilen eine
gewählte Aufmerksamkeit; ihre Positionsänderung startet nicht bei jedem
Rohpunkt eine neue Begegnung, Drehung oder Schrittfolge.

## Vereinbarte Aufmerksamkeitsstufen

Die Bereiche sind die Eintrittsstufen. Für den Rückweg gelten bewusst andere
Schwellen, damit Grenzwerte kein Hin-und-her-Schalten erzeugen.

| Eintrittswert | Stufe | Mögliche Darstellung |
| --- | --- | --- |
| 0–19 | Unbeteiligt | Normale Idle-Aktivitäten haben Vorrang. |
| ab 20 | Bemerkt | Frontal beobachten, zunächst nur den Kopf bewegen. |
| ab 45 | Fokussiert | Weiter beobachten; bewusste Körperzuwendung wird möglich. |
| ab 70 | Stark aufmerksam | Interessante/bedrängende Situation weiter bewerten; ein Gefühl ist weiterhin keine automatische Folge. |

### Anstieg und Abnahme

`W` ist die aktuelle Spritebreite: 192 logische Pixel bei 1X beziehungsweise
384 Bildschirmpixel bei 2X. Geschwindigkeit wird in `W/s` verglichen. Abstand und
Reichweite stammen aus der vorhandenen normierten Körpergeometrie von
`CursorObservation`, nicht aus einer neuen Geometrie im Renderer.

| Situation innerhalb von drei W Körperabstand | Änderungsrate |
| --- | --- |
| Bewegung unter 0,5 W/s, außerhalb des Stillstandstoleranzbereichs | −8 Punkte/s |
| Normale Bewegung ab 0,5 und unter 1,5 W/s | +4 Punkte/s |
| Schnelle Bewegung ab 1,5 und unter 3 W/s | +18 Punkte/s |
| Sehr schnelle Bewegung ab 3 W/s | +24 Punkte/s |
| Stillstand innerhalb der vorhandenen Jittertoleranz | −15 Punkte/s |

Die Änderungen werden zeitgewichtet integriert und auf 0–100 begrenzt. Ein
Sample ist kein fixer Punktgewinn. Wiederholtes Lesen desselben Samples,
Render-Aufrufe, Framewechsel und Emoteanzeige integrieren keine zusätzliche Zeit.
Die vorhandene Geschwindigkeitsglättung erhält als Startwert eine Zeitkonstante
von **0,3 Sekunden**; keine zweite konkurrierende Geschwindigkeitsmessung.
Ein einzelner Sprung füllt den Wert nicht sofort.

Weiter entfernte Bewegung kann höchstens „Bemerkt“ erreichen. Als technische
Startregel für diesen bisher nicht numerisch festgelegten Fall: Bewegung ab
0,5 W/s baut mit +4 Punkten/s bis höchstens 25 auf. Bereits höhere Aufmerksamkeit
nimmt dort mit −8 Punkten/s bis 25 ab, ohne hart abgeschnitten zu werden.
Stillstand/geringe Bewegung bauen auch dort gemäß Tabelle ab. Große Entfernung
allein ist niemals ein Angstbeleg und erlaubt keine Körperdrehung/Fangbewegung.

Stillstand muss trotz nachlaufender Geschwindigkeitsglättung zeitnah als Ruhe
wirken. Dafür wird die bestehende jittertolerante Stillstandserkennung benutzt;
als technischer Startwert haben 0,3 Sekunden stabiler Position Vorrang vor dem
Nachlauf der Filtergeschwindigkeit. Eigenbewegung zählt nicht als Zeigerreiz.

### Rückwege und fehlende Beobachtungen

- Körperrückkehr beginnt bei **unter 30 Punkten für eine Sekunde**.
- Der Kopfblick endet bei **unter 12 Punkten** mit kurzem Nachblick; eine
  Sekunde ist der geplante Startwert für diesen Nachblick.
- Als ergänzende Stufenhysterese verlässt „Stark aufmerksam“ die Stufe bei
  unter 55 Punkten für eine Sekunde; „Fokussiert“ bei unter 30 für eine Sekunde.
  Diese ergänzenden Haltewerte sind technische Startwerte für die Sichtung.
  Der Ferndeckel liegt deshalb unter 30, damit eine frühere Fokus-/Körperstufe
  nicht am Deckel hängen bleibt. Eine seit einer Sekunde außerhalb der drei W
  liegende Beobachtung gibt als zusätzliche Startregel die Körperseite frei;
  der Aufmerksamkeitswert kann während des Rückwegs weiter glatt abklingen.
- Ruhe beendet vorhandene Moodlets nicht sofort. Ihre kanonischen Profile
  laufen unabhängig weiter. Ein hoher alter Moodlet-Level hält Aufmerksamkeit
  nicht künstlich oben und erzeugt keine neue Gefühlsursache.
- Ungültige/veraltete Samples und Samplinglücken werden nicht als Stillstand
  oder rasante Bewegung interpretiert. Kein nachträgliches Aufladen über eine
  unbeobachtete Zeitspanne. Der vorhandene Frischevertrag (0,5 s) und die
  Lückengrenze der Sensorhistorie (1,5 s) bleiben zunächst erhalten.
- Spiel-/Schlafwechsel, deaktivierte Cursoroption und Maßstabswechsel verwerfen
  flüchtige Absichten und setzen den Sensor sauber neu auf. Geschützte
  Aktivitäten pausieren Cursorverhalten ohne erfundene Ruhe-/Bedrohungsbelege.
  Vorhandene Moodlets altern ausschließlich auf der Pet-Zeitachse weiter.

## Kopf, Körper und Seitenwechsel

Eine Dreiviertelzuwendung darf gewählt werden, wenn Aufmerksamkeit mindestens
45 beträgt, der Zeiger seit mindestens zwei Sekunden überwiegend auf derselben
nahen Seite beobachtet wird und kein vorrangiger Anlass blockiert. Die
Seitenbeobachtung beginnt beim Bemerken, nicht erst nach Erreichen von 45.

Für „überwiegend“ ist als technischer Startwert eine zeitgewichtete 2-s-Spanne
mit mindestens 1,75 s auf derselben Seite vorgesehen; die aktuelle Seite muss
passen. Das wird begrenzt in der bestehenden Policy gehalten, nicht als
unbegrenzte Zeigeraufzeichnung. Hektische Wechsel können Aufmerksamkeit erhöhen,
liefern aber keine stabile Körperrichtung. Frontal kann der Kopf frei folgen.

Kurze Gegenblicke ändern keine laufende Körperabsicht. Hält die Gegenseite
1,5 Sekunden an, führt der Weg zunächst zur Front. Eine neue seitliche
Zuwendung braucht wieder die gültigen Aufmerksamkeits-/Seitenbedingungen; keine
Warteschlange alter Richtungen und kein direktes Links-nach-rechts-Umspringen.
Der tatsächliche Körperzustand erlaubt nur passende Kopfachsen. Das ist sowohl
bei der Darstellung als auch bei der gemeinsamen World-Aufmerksamkeit zu prüfen.

`BodyOrientation` führt die vorhandenen ganzen Drehposen aus. Die bisherigen
mindestens 140 ms pro Drehphase und geordnete Rückwege bleiben erhalten.
Gelegentliche eigene Idle-Schritte, Blinzeln und Schwanken bleiben erhalten;
kurzes Bemerken allein startet keinen neuen Ortswechsel.

## Vorwarnung vor Angst

Ein hoher Aufmerksamkeitswert allein reicht nicht. Vorwarnung braucht eine
wirklich **schnelle, körpernahe Annäherung auf Aiko zu**. Schnelle Bewegung von ihr
weg oder seitlich in sicherem Abstand ist kein Bedrängen.

Die vereinbarte Reihenfolge lautet:

1. Wahrnehmen/Beobachten. Eine eindeutige schnelle Nahannäherung darf diese
   Beobachtung beschleunigen, statt erst mehrere Sekunden auf einen Wert zu warten.
2. Eine kurze, konkrete Vorwarnung, beispielsweise: „Hey, langsamer! Das ist mir
   zu nah.“ Noch kein negatives Moodlet und noch kein Fluchtlauf.
3. Wird es ruhig oder entfernt sich der Zeiger, kann es bei der Warnung bleiben.
4. Erst eine **weitere qualifizierte Annäherung innerhalb der folgenden drei
   Sekunden** kann Angst begründen. Ein mehrfach gelesenes altes Sample zählt
   nicht als zweiter Anlass. Stärke berücksichtigt Nähe, Geschwindigkeit,
   Wiederholung, Vertrauen und Zustand.

Als technische Startgrenzen für die spätere Umsetzung: Nahbereich bis 1 W,
Geschwindigkeit mindestens 1,5 W/s und gerichtete Annäherung mindestens 1 W/s.
Diese drei Bedingungen müssen gemeinsam erfüllt sein. Die allgemeine schnelle
Beobachtungsstufe und die Bedrohungsprüfung sind getrennte Verträge.

### Anzeigequittung und geschützte Sprechplätze

„Warnung geplant“ ist nicht „Warnung gesehen“. Eine unveränderliche Warnungs-ID
wird im vorhandenen Ereignisvertrag ergänzt. Die Desktop-/Speech-Strecke meldet
**tatsächlich angezeigt oder verworfen** mit dieser ID zurück. Das 3-s-Fenster
beginnt erst bei bestätigter Anzeige; eine verspätete Quittung für eine bereits
abgelöste Warnung ist wirkungslos. Erst ein danach neu beobachteter Anlass kann
Angst qualifizieren. Die Quittung selbst vergibt weder Moodlet noch Pflegepunkte.

Die Zeile wird über den vorhandenen deutschen Dialogkatalog und PetMind
gewählt. Dafür ist ein semantisches Ereignis `cursor_warning_near_fast`
vorgesehen. Keine fest eingebauten deutschen Sätze in Sensor, Policy oder Tk.
Der Warnhinweis ist eine kurze Anzeige ohne geschützte ReactionPlayer-Aktion;
Kontakt und Menü bleiben bedienbar. Er darf Geschichte, Objektfeedback,
Spielanzeige oder andere geschützte Sprache nicht ersetzen.
Die Vorwarnung ist eine situative Rückmeldung. Sie hängt weder an der
Zufallswahrscheinlichkeit noch an der 100-s-Sprechpause des alten Cursorpfads.
Die Cursoroption schaltet den gesamten Ablauf ab; die vorhandene Option für
spontanes Plaudern ist keine Zufallsschranke für diese konkrete Reaktion.

Ist kein Sprechplatz frei, wird die Warnung verworfen. Es gibt keine spätere
Wiedergabe eines veralteten Hinweises und keine Angstauslösung aus der
unsichtbaren Warnphase. Ein neuer tatsächlicher Anlass kann später einen neuen
Warnversuch begründen. Als Startwert gilt höchstens eine angezeigte Warnung je
zehn Sekunden; während dieser Begrenzung keine heimliche Ersatzwarnung und
keine neue Angst aus einem nicht angezeigten Warnversuch. Bereits vorhandene
Angst darf weiter nachwirken. Geschützte Aktivitäten nehmen ohnehin nicht an
neuen Cursorreaktionen teil. Diese Anzeige-/Wiederholungsdetails ergänzen die
Besprechung als ausdrücklich benannte technische Startregeln.

Die alten zufälligen `cursor_far`-/`cursor_follow`-Kommentare werden dafür nicht
wieder parallel an rohe Zeigerbewegung gehängt. `walk_pause` bleibt für normale
Idle-/Cursorwege ausgeschaltet. Bestehende Autorentexte bleiben erhalten, solange
ihre tatsächlichen übrigen Aufrufer nicht geprüft sind.

## Neugier, Angst und vorhandene Moodlets

**Neugier** kann bei mindestens 70 Aufmerksamkeit entstehen, wenn die Situation
mindestens zwei Sekunden interessant und ungefährlich bleibt. Schnelle Bewegung
kann dafür ausdrücklich positiv sein. Langsames oder ruhiges Halten allein
qualifiziert keine neue Neugier. Die positiven zwei Sekunden werden nur aus
wirklich beobachteter passender Bewegung gesammelt; ein alter Moodlet-Level
oder eine Körperdrehung ist kein Ersatz dafür.
Als präziser Startvertrag beginnt diese Qualifikationszeit ab 70 Punkten;
es braucht zwei Sekunden gültiger positiver Beobachtung mit mindestens 70.
Ruhe, Bedrängen oder eine Beobachtungslücke unterbrechen diese Qualifikation.
Sie ist eine Dauer innerhalb derselben Policy, kein separater Timer.

**Angst** entsteht erst nach dem oben bestätigten Warnablauf und einem neuen
bedrängenden Anlass. Vorwarnung allein verändert keine Stimmungspunkte.

Die vorhandenen Familien `CURSOR_CURIOSITY` und `CURSOR_FEAR`, ihre Stärken 1–3,
Punkte, Symbole und Speicherverträge werden wiederverwendet:

| Gefühl | Bestehende Beiträge | Bestehende frische Gesamtdauer Stufe 1/2/3 | Mögliche Folge |
| --- | --- | --- | --- |
| Neugier | +1 / +2 / +3 | 30 / 60 / 90 s | Beobachten, zuwenden, bei starker Neugier spielerischer Fangversuch. |
| Angst | −2 / −4 / −6 | 15 / 30 / 60 s | Schreck, Abstandsschritt, bei starker Angst kurzer Fluchtlauf. |

Aufmerksamkeit 70 oder 100 ist keine automatische Moodlet-Stärke 1 oder 3.
Stärke wird bei einem echten Anlass aus Situation, Vertrauen und Bereitschaft
qualifiziert; sie steigt nicht durch wiederholtes Auswerten derselben Lage.
Vorhandene absolute Stärken und Beleg-IDs bleiben maßgeblich. Neue reale Anlässe
können verstärken, ein schwächeres Signal stuft keine stärkere Episode abrupt ab.
Beide Gefühle können nachwirken; eine neue wirkliche Bedrohung hat bei der
aktuellen Handlungswahl Vorrang. Kein neuer Angst-/Neugier-Langzeitscore,
keine Freundschaftsgutschrift/-strafe und kein Care-/Wunschfortschritt.

### Fangversuch und Rückzug

Ein Fangversuch ist ein kurzer sichtbarer Versuch, einem erreichbaren,
bewegten Zeiger näherzukommen beziehungsweise ihn zu erreichen. Das ist mehr
als der bisherige feste Schritt zu einem stillstehenden Punkt. Er übernimmt
keine Kontrolle über den echten Mauszeiger und benötigt keine neuen Assets.

Der technische Startumfang übernimmt die vorhandenen Grenzen: bodennahes
reichbares Ziel, ein oder höchstens zwei kleine Profilschritte je Versuch,
mindestens zwölf Sekunden bis zum nächsten Versuch. Innerhalb des Versuchs darf
sich das gewählte Ziel begrenzt aktualisieren. Quellen-ID, verbrauchte Strecke,
Schrittgrenzen und Restbudget dürfen dabei nicht neu starten. Ein Zielwechsel
hinter den Körper beendet den Versuch am sicheren Stand statt eines laufenden
Links-rechts-Pendels. Neue Versuche brauchen neue passende äußere Bewegung;
ein aktives positives Moodlet allein startet keinen weiteren Versuch.

Starke Angst erlaubt den vorhandenen kurzen Fluchtlauf: höchstens eine Sekunde
wirkliche Laufbewegung, danach mindestens fünf Sekunden Standruhe. Höchstens
ein Rückzug/Fluchtlauf je zusammenhängender Begegnung; erneute Flucht erst nach
bestätigtem zwischenzeitlichem Verlassen des Nahbereichs. Das Moodlet allein
startet keine Fluchtkette. Neue Stärke darf einen Ausdruck ändern, ohne einen
verbrauchten Bewegungsversuch erneut freizugeben.

## Menü-Erreichbarkeit und Prioritäten

- Bewusster Zugang per Enter, Polling oder Klick hat sofort Vorrang vor
  Beobachten, Vorwarnung, Fangversuch und Flucht. Der Cursorauftrag wird
  freigegeben und tatsächliche Ortsbewegung gestoppt.
- Der vorhandene gemeinsame Bedienbereich mit sechs logischen Pixeln
  Zusatzrand und die Herkunftsprüfung bleiben erhalten. Eigenbewegung unter
  einen ruhenden Zeiger ist kein absichtlicher Benutzerkontakt.
- Die Vorwarnung ist ebenso wenig eine Kontaktsperre wie der kurze Gefühls-Emote.
  Belegte/geschützte Sprechplätze werden nicht überschrieben.
- Während echter Toolbar-/Menübedienung stehen auch erhaltene World-Aufträge
  physisch still. Auftrag, Suchfortschritt und Objektbesitz bleiben bestehen.
  Ein sichtbares unbenutztes Fenster hält Aiko nicht unbegrenzt fest.
- Native Objektgriffe behalten aktuelle Ereigniskoordinaten, ohne die Policy
  erneut auszuwerten oder aus dem Klick eine Blick-/Wissensänderung zu erfinden.
- Aufmerksamkeit, Warn-ID, bestätigtes Warnfenster und Fangziel sind flüchtig.
  Laden erzeugt weder Warnung noch Gefühlsbeleg. Vorhandene Moodlets bleiben
  gespeichert und altern auf `PetState.lived_seconds`.

Als technische Startregel verwirft eine Bedienübernahme die flüchtige
Aufmerksamkeit und ihre Seiten-/Warn-/Fangabsichten. Nach Bedienende beginnt
ein neuer beobachteter Aufbau; hohe alte Werte und verspätete Anzeigequittungen
starten keine Bewegung. Geschützte Aktivitäten geben Cursorabsichten ebenfalls
frei. Ihre Dauer wird danach nicht als beobachtete Aktivität nachintegriert.

## Geprüfter Iststand und konkrete Umbauten

Pfade in dieser Tabelle sind relativ zu `aiko_pet/`. Ein genannter neuer
Methoden-/Wertname ist ein geplanter Vertrag, keine Behauptung über vorhandenen Code.

| Bestehender Besitzer | Heute auf `9a233d7` | Geplanter Umbau |
| --- | --- | --- |
| `pet/mind/cursor_attention.py` / `CursorAttention`, `CursorPerception` | Rohe Historie, normierte Geschwindigkeit, EMA mit 0,12 s; alter Snapshot enthält noch Aufmerksamkeitstimestamps. | Einziger Besitzer der Messhistorie bleiben, Filterzeit aus validierten Parametern lesen; Messfakten liefern. Kein zweiter subjektiver Punktestand hier. Vor Entfernung alter Snapshotfelder alle realen Leser prüfen. |
| `application/cursor_observation.py` / `CursorObservation` | Abstand, Reichweite, Annäherung und Eingabeherkunft; Reset invalidiert auch das abgeleitete Sample. | Bestehende gemeinsame Geometrie behalten; Stillstand, Sample-Frische und normierte Bewegungsbänder für die Policy lesbar liefern. Keine Gefühle auswählen. |
| `pet/mind/cursor_behaviour.py` / `CursorBehaviourPolicy`, `CursorIntent` | Kurzer Beobachtungszeitraum, ruhiges Verweilen als Neugierauslöser; direkte Angst bei schneller Nahannäherung. | Einziger Besitzer des flüchtigen 0–100-Werts, Integrationszeitpunkts, Stufenhysterese, Seitenfensters, Warnphase und der gewählten Fangabsicht. `CursorIntent` um unveränderliche Score-/Stufen-/Warnfakten erweitern. Alte Ruhe-/Sofortangst-Zweige ersetzen. |
| `pet/interaction_events.py`, `pet/cursor_experiences.py`, `pet/state.py` | Unveränderlicher `CursorExperience`, reine Anwendung absoluter Stärken, dünner `PetState.experience_cursor`. | Warnwert/Anzeigequittung in bestehendem Vertragsmodul ergänzen; Warnung bleibt außerhalb von `InteractionEvent`/Care. Nur qualifizierte `CursorExperience` an PetState liefern. Bestehende Moodlet-Funktion weiterverwenden. |
| `application/cursor_behaviour.py` / `CursorBehaviourCoordinator` | Ein Policy-Aufruf am fortgeschrittenen Pet-Endpunkt; Erfahrungsübergabe und Bewegungszulassung. | Warn-/Gefühlsfeedback unterscheiden, einmal liefern, Warnquittung an die aktuelle Policy zurückmelden. Anzeigenachricht verarbeitet keinen zweiten Wahrnehmungstick und keine Pet-Zeit. Zulassung erneut gegen aktuelle Sperren prüfen. |
| `application/attention.py`, `pet/mind/mind.py`, `pet/mind/catalog.py`, `pet/mind/dialogue_events.py`, `data/dialogues/de/` | Alter zufälliger Cursor-Kommentarweg vorhanden, aber vom Laufzeitpfad getrennt. | Situativ ausgelöste, katalogisierte Vorwarnung auswählen. Neuer Ereignisschlüssel und vollständige Dialogdefinition im gleichen Commit; bestehende Auswahl/Variation nutzen. Keine Reaktivierung des alten Zufallswegs. |
| `desktop/attention_runtime.py`, `ui/pet_view/attention_presenter.py`, `ui/pet_view/speech_presenter.py` | Kurzer nicht blockierender Cursor-Emote, `blocks_contact` unterscheidet geschützte Sprache. | Kurzen katalogisierten Warntext ohne ReactionPlayer-Sperre anzeigen und tatsächliche Anzeige quittieren. Warnformat enthält genau einen Text, keine geschützte Aktions-/Wartesequenz. Der vorhandene Dialogvertrag muss dieses Format validieren; kein stilles Abschneiden mehrteiliger Autorensequenzen. |
| `desktop/pointer_runtime.py`, `desktop/animation_assembly.py`, `gui.py` | Eine Eingabestrecke, Feedback als `CursorExperience`, direkte Zugangsübernahme. | Vorhandene Ports typisiert um Warnfeedback/Quittung erweitern. Dieselbe Instanz teilen, keine zweite Auswertung in Render-/Klick-/Framecallbacks. GUI bleibt Composition Root unter 640 Zeilen. |
| `desktop/visual_observation.py`, `pet/animation/body_orientation.py`, `desktop/animation_runtime.py`, `application/object_behavior.py`, `desktop/world_runtime.py` | Gewähltes Cursorziel, explizite Körperabsicht und gemeinsame World-Aufmerksamkeit vorhanden. | Neue gehaltene Stufe und Seitenabsicht benutzen; Blicke bei aktiver Bewegung aktualisieren, ohne Drehung neu zu starten. Tatsächliche Körperphase und kompatible Kopfachsen auch für World prüfen; gegenläufige Sicht erst über Front freigeben. |
| `pet/movement/contracts.py`, `pet/movement/controller.py`, `desktop/walk_runtime.py` | Quellenpriorität World/Cursor/Idle, begrenzte Schritte/Laufzeit; Cursorziel bleibt pro Token fest. | Eigenen Fangauftrag als Cursorabsicht ausdrücken; begrenztes Retargeting aktiver Aufträge mit gleicher Identität. Tatsächlichen Fortschritt/Budget bei Retargeting behalten; abgeschlossene Tokens nicht wieder aktivieren. Kein zweiter Positionsschreiber. |
| `desktop/input.py`, `desktop/geometry.py`, `ui/windows/hover_ui.py`, `application/contact.py` | Gemeinsamer toleranter Zugang, Herkunft und harte Bedienpause bereits vorhanden. | Zugang zusätzlich gegen neue Warn-/Fangzustände absichern. Neue Scorewerte oder Quittungen dürfen nach Kontaktübernahme keinen Cursorauftrag und kein verbrauchtes Fluchtbudget reaktivieren. |
| `pet/movement/random_walk.py`, `pet/animation/ambient.py`, `desktop/preferences.py`, `application/assembly.py`, `desktop/runtime.py` | Bestehende Idle-/Reset-/Aufrufreihenfolge und alleinige Besitzer. | Neue Aufmerksamkeit in bestehende Prioritäten/Resets einpassen; keine neuen Timer. Ruhiger Zeiger gibt eigene Blicke/Idle wieder frei. Kein Idle-Rennen als Ersatz und keine Routinekommentare. |
| `data/balance.json`, `pet/balance_contract.py` | Validierter Katalog bisheriger Cursorgrenzen. | Score-Raten, Speedbänder, Filterzeit, Stufenschwellen, Dwell-/Warnfenster an einer Stelle führen; Beziehungen zwischen Grenzwerten validieren. Moodlet-Stufenzeiten bleiben im bestehenden Moodlet-Katalog. |

**Keine neuen Produktionsmodule vorgesehen.** Neue unveränderliche Werte gehören
in die bestehenden Vertragsmodule. `CursorAttention` bleibt Sensorhistorie,
`CursorBehaviourPolicy` subjektive Aufmerksamkeit, `BodyOrientation` tatsächliche
Pose, `WalkController` tatsächlicher Bewegungsfortschritt, `PetState` persistentes
Erleben. Kein zusätzlicher AttentionManager, Moodlet-Timer oder Bewegungspfad.

## Datenfluss und Zeitbesitz

Die vorhandene Reihenfolge bleibt erhalten: Lifecycle und Bedienung, Sensor,
eine Policy-Auswertung samt neuen qualifizierten Gefühlsbelegen, World mit
geteilter Aufmerksamkeit, aktuelle Bewegungszulassung, Darstellung. Warnanzeige
und Quittung laufen als einmaliges Feedback über die vorhandene Desktopstrecke.
Die Quittung aktualisiert nur den passenden Warnstatus; eine neue Gefühlsentscheidung
benötigt den nächsten gültigen äußeren Wahrnehmungsanlass.

Aufmerksamkeit und Warnfenster benutzen die vorhandene monotone Laufzeitachse;
Moodlets ausschließlich die bereits fortgeschrittene Pet-Zeit. Bei gleichem
Sampledatum kein zweiter Anstieg. Nach Lücken keine vollständige Differenz als
beobachtete Aktivität nachholen. Derselbe Begegnungs-/Warnbeleg wird nicht pro
Frame neu identifiziert; Sitzungskennungen und begrenzte Receipts bleiben erhalten.

## Geplante Commitfolge mit gezielten Prüfungen

Dies ist die nächste Folge nach `9a233d7`, keine Umbenennung der bereits
abgeschlossenen elf Commits. Jeder Funktionscommit führt unmittelbar betroffene
Signaturen, Ports, Katalogverträge und Aufrufer gemeinsam mit. Keine bewusst
kaputten Zwischenstände und keine dauerhafte alte/neue Parallelpolicy.

| Nr. / Commit | Abgeschlossener Umfang | Nur gezielte Tests dieses Commits |
| --- | --- | --- |
| 1 — `docs(cursor): record staged attention and warning plan` | Dieser Plan und eindeutige Statusverweise in den bisherigen Dokumenten. | Relative Links, reale Modul-/Testpfade, Zeit-/Schwellenkonsistenz und reiner Dokumentdiff. Keine Laufzeitsuite. |
| 2 — `refactor(cursor): normalize motion evidence for staged attention` | Sensorfilter/Stillstand und kanonische, validierte Parameter. Kein subjektiver Score im Sensor. Direkt betroffene Messadapter gemeinsam migrieren. | `test_cursor_attention.py`, `test_cursor_observation.py`, `test_resource_validation.py`, relevante bestehende Policy-Grenzfälle. 1X/2X, Bandgrenzen 0,5/1,5/3, Jitter, Eigenbewegung, Filter-Nachlauf, ungültiges dt und Samplinglücken. |
| 3 — `feat(cursor): integrate held attention stages and selected gaze` | Policy-Wert, Stufen, Auf-/Abbau, Hysterese, Frische und gewähltes Ziel; Coordinator/Visual-Adapter gemeinsam führen. Keine neue Persistenz und kein autonomer Moodlet-Trigger aus dem Wert. | `test_cursor_behaviour_policy.py`, `test_cursor_behaviour_coordinator.py`, `test_desktop_visual_observation.py`, `test_cursor_front_pose.py`, relevante `test_cursor_behaviour_integration.py`-Fälle. Gleiche Zeitreihe bei verschiedenen Tickraten; Einzelimpuls, Ferndeckel, Ruhe, doppelte Samples und Stufenschwanken. |
| 4 — `feat(cursor): warn before qualifying a new fear experience` | Warnanlass, ID, katalogisierte Ein-Text-Vorwarnung, nicht blockierende Anzeige und Quittung atomar verbinden. Alte Sofortangst entfernen; erst weitere echte Nahannäherung nach bestätigter Warnung darf Angst qualifizieren. Verworfen/veraltet/belegt haben keinen versteckten Angstpfad. | Neu geplant: `test_cursor_warning.py`; außerdem `test_dialogue_events.py`, `test_dialogue_modules.py`, `test_dialogue_index.py`, `test_content_catalog.py`, `test_attention_presenter.py`, `test_speech_presenter.py`, `test_desktop_attention_runtime.py`, relevante Policy-/Coordinator-/Kontaktfälle. Warnung allein ohne Pet-Mutation, angezeigt/verworfen, frischer zweiter Anlass, 3-s-Grenze, 10-s-Begrenzung, falsche/späte/duplizierte Quittung, Geschichte/Spiel/Objektfeedback, Text ohne Aktionssperre. |
| 5 — `refactor(animation): turn from held attention and return through front` | Zwei-Sekunden-Seitenbeobachtung, 45/30-Körperschwellen, Rückwege und kompatible Darstellung/World-Sicht gemeinsam auf neue Aufmerksamkeit führen. | `test_body_orientation.py`, `test_desktop_animation_runtime.py`, `test_desktop_visual_observation.py`, `test_animated_pointer_ports.py`, gezielte Kopf-/Schritt-/Reloadfälle in `test_animated_pet_isolation.py`. Hohe Aufmerksamkeit bei wechselnden Seiten, kurze Gegenseite, gehaltene Gegenseite, Unterbrechung, verspätete Frames und World-Gegenblick vor/nach Front. |
| 6 — `feat(cursor): qualify feelings from observed interest and pressure` | Alte Ruhe-als-Neugier-Regel ersetzen; Aufmerksamkeit plus zwei Sekunden sichere interessante Bewegung und Zustand qualifizieren Neugier. Angststärken auf neue reale Belege nach Warnung führen. Vorhandene Profile, absolute Stärken, Speicherung und Emotes weiterverwenden. | `test_cursor_experiences.py`, relevante Policy-/Coordinator-/Integrationsfälle, `test_moodlet_timing.py`, `test_moodlet_mood.py`, `test_emotional_reads.py`, Klasse `MoodletPersistenceTests` aus `test_emotional_persistence.py`, `test_sqlite_moodlet_rows.py`, `test_care_evidence_storage.py`. Beide Gefühle, kein Ruhe-/Moodlet-Selbsttrigger, kein Care/Wunsch/Freundschaftskredit, einmalige Belege, alte Saves und nachwirkendes Gefühl bei fallender Aufmerksamkeit. |
| 7 — `feat(movement): execute bounded cursor catching attempts` | Aktiver kurzer Fangversuch statt festem Ziel zu ruhendem Zeiger. Gleiches-Token-Retargeting, unveränderte Fortschritts-/Schritt-/Laufbudgets, sicherer Richtungsabbruch und einmaliger Abschluss gemeinsam mit direkten Aufrufern. | `test_movement_requests.py`, `test_desktop_walk_runtime.py`, `test_goal_walk.py`, Klasse `WalkControllerTests` aus `test_motion_animation.py`, relevante `test_cursor_behaviour_integration.py`-/`test_desktop_animation_runtime.py`-Fälle. Bewegtes erreichbares Ziel, Zielverlust, Fremdziel-Priorität, zwei Schritte, Rand, 12-s-Pause, kein Budgetreset, kein Wiederstart abgeschlossener Tokens, Flucht nur eine Sekunde tatsächliche Bewegung. |
| 8 — `fix(input): preserve menu access across attention and warning phases` | Native Zugangsübernahme, Reset, geschützte Aktivität und bestehende Idle-/World-Prioritäten durch alle neuen Phasen absichern; keine neue Timer-/Kontaktinstanz. | `test_cursor_menu_access.py`, `test_cursor_contact_origin.py`, `test_desktop_input_controller.py`, `test_contact_coordinator.py`, `test_hover_geometry.py`, `test_hover_isolation.py`, `test_desktop_preferences.py`, `test_application_assembly.py`, `test_idle_steps.py`, `test_ambient_director.py`; gezielte World-Fälle unten. Hoher Score, Warntext offen, Quittung zwischen Frames, aktives Gefühl, Fang-/Fluchtbewegung, Eigenkontakt, erhaltenes World-Ziel und sichtbares unbenutztes Fenster. |
| 9 — `test(cursor): verify staged trajectories and complete final CI` | Lange Zeitreihen und Assemblies vervollständigen, erreichten Stand dokumentieren, ausschließlich tatsächlich neue Testmodule im bestehenden Windows-Job ergänzen. | Erst verbleibende gezielte Integrations-/Assembly-/World-Fälle; danach vollständiges lokales Ruff/Mypy/Pyright und Gesamtsuite samt Tk, anschließend echte vollständige CI am exakten finalen Head. Kein Merge. |

Neue Tests dürfen starke alte Aussagen nicht pauschal entfernen. Direkt
widersprechende Erwartungen der alten Verhaltensfassung werden mit vollständigen
neuen Zeitreihen ersetzt: beispielsweise schnelle Aktivität beobachten und erst
später warnen, statt jede schnelle Nähe sofort als Angst zu verbuchen.

### Konkrete Integration und Regression

Lange kontrollierte Zeitreihen müssen echte Besitzer verbinden, nicht nur
Clipnamen vergleichen:

- Ruhiger Ausgang -> schnelle sichere Bewegung -> Bemerken/Fokus -> gleiche
  Seite -> Körperzuwendung -> mögliche Neugier -> kurzer Fangversuch -> Ruhe
  -> Aufmerksamkeitsabbau und Front bei noch nachwirkendem Moodlet.
- Gleiche Aktivität mit hektischen Seitenwechseln: Aufmerksamkeit kann hoch
  sein, der Körper bleibt frontal; keine Richtungswarteschlange.
- Schnelle körpernahe Annäherung -> sichtbare Warnung -> Ruhe ohne Angst;
  alternativ neuer bedrängender Anlass -> Angst und begrenzter Rückzug.
- Warnung verworfen, veraltet, verspätet quittiert, doppelt quittiert oder unter
  Story/Objektfeedback: keine erfundene Anzeige, kein neuer Angstbeleg.
- Freundschaft hoch/niedrig, Müdigkeit, schlechte Stimmung und beide Größen;
  kein harter Freundschafts-Unlock und keine Angst allein aus schlechter Stimmung.
- Enter/Klick/Polling zwischen Samples bei hoher Aufmerksamkeit, Warnung,
  Fangversuch und Angst; danach reale Bedienung und geordnete Freigabe.
- Ruhender Zeiger, unter den Aiko selbst läuft: keine falsche Geschwindigkeit,
  automatische Toolbar, Pflegegutschrift oder erfundene Bedrohung.

Für die World-Grenze bleiben insbesondere die bestehenden Fälle aus
`test_world_gui.py` maßgeblich: `test_native_relocation_reads_event_pointer_between_sensor_samples`,
`test_new_unknown_left_item_resumes_after_native_orientation_at_scale_two`,
`test_new_unknown_right_item_resumes_after_native_orientation_at_scale_two`,
`test_unknown_orientation_subject_stays_visible_on_a_narrow_track` und
`test_taken_target_is_followed_through_hops_and_resumes_at_both_scales`.
Aus `test_world_runtime_flow.py` bleiben
`test_stationary_hover_pauses_travel_and_preserves_search_and_candidate` und
`test_search_click_reply_keeps_native_patrol_and_hover_active` erhalten.
Die Policy wird in Fixtures tatsächlich beliefert; ein nativer Klick ersetzt
keine ausgewählte Aufmerksamkeit und kein erworbenes Objektwissen.

## Gesamtsuite, CI und praktische Abnahme

Pro Funktionscommit ausschließlich seine gezielten Fachtests und bei konkretem
Bedarf begrenzte Lint-/Typprüfungen. Keine globale Suite oder Zwischenpush nach
jedem kleinen Commit. Erst nach der fachlichen Umsetzung:

1. `python -m ruff check aiko_pet tests main.py tools`.
2. `python -m mypy --strict --no-incremental aiko_pet main.py tools`.
3. `python -m pyright --project pyrightconfig.json`.
4. `python -m unittest discover -s tests -q` einschließlich isolierter Tk-/Save-
   Grenzen. Regulären Spielstand und laufende Nutzerinstanz unangetastet lassen.
5. Echte `Tests`-CI des vorhandenen PR #11 am abschließenden Head: Linux Python
   3.11/3.13 mit allen statischen Gates und voller Unit-/GUI-Suite sowie Windows
   setup and desktop boundaries. Neue `test_cursor_warning.py` nur dann in den
   vorhandenen Windows-Mustern ergänzen, wenn sie tatsächlich angelegt wurde.
   Bestehende Pillow-Testabhängigkeit erhalten, kein zusätzlicher Auditworkflow.
6. Befunde mit exaktem Head/Lauf belegen. Bei Fehlern gezielt diagnostizieren,
   betroffene Fälle erneut prüfen und echte CI am korrigierten Head abwarten.
   Ein grüner lokaler Teiltest ist keine vollständige CI.
7. Praktische Sichtung durch den Nutzer nach späterer Freigabe/Neustart:
   Aufmerksamkeit baut sich sichtbar auf und ab; Körper bleibt bei hektischen
   Seitenwechseln ruhig; Vorwarnung erklärt Angst vor deren Auslösung;
   neugieriger Fangversuch und Menüzugang sind nachvollziehbar. Technische
   Prüfung und sichtbare Verhaltensabnahme bleiben getrennt.

Der bisherige Head `9a233d7` hatte eine grüne vollständige CI; das ist ein
historischer Befund und bestätigt diesen zukünftigen Umbau nicht. Der bereits
belegte lokale Debian-Mastermind-Sonderfehler ist im
[bisherigen Prüfprotokoll](ADAPTIVE_CURSOR_REWORK_PLAN.md) dokumentiert und auf
`2ecca2f` identisch. Nicht pauschal Tests überspringen oder UI-Erwartungen lockern.
Eine Linux-Testumgebung braucht die tatsächlichen `requirements.txt`, insbesondere
Astronomy Engine; ein modaler Fehlerdialog ist kein regulär weiterlaufender Test.
Bei langsamen Windows-Bind-Mounts kann eine lokale isolierte Kopie statt einer
Änderung des Repositorys verwendet werden.

Assets, private Originale, parallele UI-Arbeiten und vorhandene Exporte bleiben
außerhalb des Umbaus. Es wird nichts neu generiert. Für diese Dokumentationsrunde
werden ausschließlich Links, Pfade, Werte-/Zustandskonsistenz und der Git-Diff
geprüft; keine Implementierung, Testsuite, CI, Commits, Pushes oder Merges.
