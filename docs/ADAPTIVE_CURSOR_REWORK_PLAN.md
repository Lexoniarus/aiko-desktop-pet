# Idle, Mausinteresse und erreichbare Bedienung: Konzept und Umbauplan

Stand: 27.10.2026. Ausgangsbasis: `2ecca2f` auf
`feature/social-optimization`. Der Nutzer hat anschließend die Umsetzung in den
elf unten aufgeführten Commits einschließlich gezielter Tests und abschließender
vollständiger CI beauftragt. **Der Codeumbau ist umgesetzt; praktische
Verhaltensabnahme durch den Nutzer steht aus.** Kein Merge ist freigegeben.
Assets und private Originale wurden nicht verändert.

Diese Fassung hat Vorrang vor widersprechenden historischen Cursor-/Drehregeln.
Der [erste Implementierungsplan](ADAPTIVE_CURSOR_IMPLEMENTATION_PLAN.md) bleibt
als Verlauf erhalten. Eine grüne CI belegt technische Prüfungen, keine praktische
Abnahme der sichtbaren Wirkung. Die früher beobachtete hektische Konkurrenz
zwischen Live-Blick und Körperdrehung war der Anlass dieses Umbaus.

## Verbindliche Richtung

- Frontal ist Aikos normale Ausgangs- und Ruhehaltung. Dabei stehen ihr alle
  16 Blickrichtungen zur Verfügung. Ein langer Seitenblick verpflichtet den
  Körper nicht zur Drehung.
- Körperdrehungen drücken eine gewählte Zuwendung/Abwendung aus oder bereiten
  einen kleinen Ortswechsel vor. Ein gemeinsamer Aufmerksamkeitsplan führt
  Kopf, Körper und Schritte. Die aktuelle Mausposition ist ein Reiz für diese
  Entscheidung, kein laufend neuer Animationsbefehl.
- Gelegentliches Beinevertreten im Idle umfasst einen, seltener zwei kleine
  Schritte. Kein gewöhnliches Idle-Rennen, kein automatischer Kommentar.
- Freundschaft liefert langfristiges Vertrauen. Aktuelle Neugier/Angst ergeben
  sich aus wahrgenommenem Zeigerverhalten und Aikos Zustand. Nähe,
  Geschwindigkeit und Annäherungsrichtung werden gemeinsam betrachtet.
- Zwei eigene Moodlet-Familien zeigen Neugier und Angst. Sie sind keine neue
  gespeicherte Bedürfnis- oder Freundschaftsskala.
- Vorhandene Stand-, Dreh-, Schritt- und Rennbilder sowie vorhandene Emotes
  werden wiederverwendet. Keine neuen Skins, Generierung, Exportänderungen oder
  Änderungen an 1X-/2X-Atlanten für diesen Umbau.
- Die Maus muss Aiko und ihre Bedienelemente zuverlässig erreichen können.
  Angst darf einen begrenzten Ausdruck/Rückzug verursachen, aber keine
  fortgesetzte Flucht vor einem Bedienversuch.

Zeitwerte und geometrische Toleranzen sind festgehaltene Startwerte für die
Sichtung. Sie bestimmen mögliche Entscheidungen; sie erzwingen nicht nach
jedem Zeitablauf die nächste Bewegungsstufe.

## Idle-Ablauf

1. Frontal stehen, blinzeln und leicht schwanken. Das Schwanken läuft beim
   Blinzeln weiter.
2. Etwa alle **20–40 Sekunden** einen eigenen Blick von **1–3 Sekunden** wählen.
   Der Kopf nutzt die verfügbaren Richtungen; der Körper bleibt gewöhnlich
   frontal. Kurze Blicke setzen die gesamte Ruheplanung nicht ständig zurück.
3. Nach ungefähr **45–90 Sekunden freiem Idle** kann Aiko einen kleinen
   Ortswechsel wählen: erst in die Richtung schauen, dann über Dreiviertel
   ins Profil drehen, dann einen Schritt machen.
4. Ein Schritt ist der Regelfall; gelegentlich ist eine Folge von zwei Schritten
   gewählt. Der zweite setzt weiterhin freien Weg und zulässige Bewegung
   voraus. Eine neue Richtung wird nicht mitten in diese Folge hineingeschoben.
5. Danach kurz stehen bleiben und umsehen, anschließend geordnet zur Front
   zurückkehren. Es beginnt eine neue Ruhephase. Diese Folge löst weder einen
   Sprachkommentar noch ein Cursor-Moodlet aus.

Ein beiläufiger Mausreiz darf einen passenden Kopfblick auslösen, ohne sofort
die eigene Schrittfolge umzulenken. Deliberate Bedienung, geschützte Aktionen
und tatsächliche nahe Bedrohung behalten ihre unten beschriebenen Grenzen.
Fehlt das optionale Schrittpaket, bleibt Aiko für diese Idle-Gelegenheit stehen;
es gibt keinen stillen Ersatz durch die alte Rennschleife.

## Ablauf des Mausinteresses

| Wahrgenommene Situation | Gewählte mögliche Folge |
| --- | --- |
| Zeiger weit weg | Eigenen Idle fortsetzen, höchstens gelegentlich kurz hinsehen. |
| Langsame Bewegung in der Nähe | Zunächst 1–3 Sekunden frontal nur mit dem Kopf beobachten. |
| Zeiger etwa drei Sekunden ruhig auf derselben nahen Seite; Interesse bleibt bestehen | Eine bewusste körperliche Zuwendung wählen. Aiko darf danach einfach stehen und schauen. |
| Nach der Zuwendung weitere 1–2 Sekunden ruhiger, bodennah erreichbarer Zeiger und ausreichende Bereitschaft | Einen Annäherungsschritt wählen; ein zweiter ist möglich, höchstens zwei pro Versuch. |
| Hektische Links-rechts-Wechsel | Kein neuer Körperauftrag pro Wechsel. Kurz beobachten, gegebenenfalls Interesse lösen und zur Ruhe kommen. |
| Schnelle körpernahe Annäherung | Schreck, Abstandsschritt oder begrenzte Flucht, abhängig von Vertrauen, Erleben und Energie. |
| Schnelle Bewegung von ihr weg / weit entfernte schnelle Bewegung | Geschwindigkeit allein begründet keine Angstreaktion. |

Nach einem Annäherungsversuch gelten **mindestens zwölf Sekunden ohne neuen
Annäherungsversuch**. Hinschauen bleibt möglich. Nach Interessenverlust endet
eine laufende Bewegung am nächsten passenden stabilen Stand; es wird keine
Warteschlange veralteter Zeigerziele abgearbeitet.

Kopf und Körper teilen den gewählten Gegenstand beziehungsweise Beobachtungsort.
Während der Körper frontal ist, darf der Kopf alle Blickrichtungen verwenden.
Während einer Drehung gelten zur tatsächlichen Körperphase passende Kopfachsen.
Ein bewusster Seitenwechsel führt über die Front. Das System darf ruhige
Zeigerbewegung innerhalb einer gehaltenen Beobachtung verfolgen; Richtungs- und
Körperabsichten werden dabei nicht für jeden neuen Rohpunkt neu begonnen.

### Freundschaft, Zustand und aktuelle Reaktion

| Ausgangslage | Tendenz, keine harte Freischaltung |
| --- | --- |
| Wenig Vertrauen, ruhiger Zeiger | Vorsichtig schauen, gegebenenfalls zögerlich zuwenden oder näherkommen. |
| Viel Vertrauen, ruhiger Zeiger | Eher stärkere Neugier und eine begrenzte Annäherung. |
| Wenig Vertrauen, schnelle nahe Annäherung | Eher Angst, Abstand und längere Vorsicht. |
| Viel Vertrauen, schnelle nahe Annäherung | Schreck bleibt möglich, meist geringere Stärke und schnellere Beruhigung. |

Energie, Stimmung, Nähebedürfnis und Interesse an Beschäftigung beeinflussen die
Bereitschaft. Hohe Freundschaft erzwingt keine Annäherung bei Müdigkeit oder
schlechter Stimmung; niedrige Freundschaft schließt Neugier nicht aus.
Schlechte Stimmung ist auch nicht automatisch Angst.

Neugier und Vorsicht dürfen sich überlagern. Die jeweils aktuelle Entscheidung
ist trotzdem eindeutig; bei einer frischen tatsächlichen Bedrohung erhält die
vorsichtige Reaktion Vorrang. Der bestehende Moodlet-Nachhall ist kein neuer
äußerer Reiz und darf keine Selbstauslösung erzeugen.

## Zwei kurze Cursor-Moodlets

Die Punkte gelten als Beitrag der **gerade aktiven Stufe**. Sie sind kein
fortlaufender Punktgewinn oder -verlust. Die Gesamtdauer gilt ohne neue
qualifizierte Erfahrung und umfasst alle verbleibenden Abklingstufen.

| Familie | Stufe | Beitrag | Gesamtdauer bei frischem Beginn in dieser Stufe | Begünstigt |
| --- | --- | --- | --- | --- |
| Neugierig auf den Mauszeiger | 1, leicht | +1 | 30 s | Interessierter Kopfblick bei frontalem Körper. |
| Neugierig auf den Mauszeiger | 2, deutlich | +2 | 60 s | Bewusste Zuwendung bei weiterhin ruhigem Interesse. |
| Neugierig auf den Mauszeiger | 3, stark | +3 | 90 s | Ein, gegebenenfalls zwei Annäherungsschritte, wenn erlaubt. |
| Angst vor dem Mauszeiger | 1, leicht | −2 | 15 s | Kurzer Schreck und aufmerksames Stehenbleiben. |
| Angst vor dem Mauszeiger | 2, deutlich | −4 | 30 s | Abwenden und ein kleiner Abstandsschritt. |
| Angst vor dem Mauszeiger | 3, stark | −6 | 60 s | Kurzer Fluchtlauf bei ausreichender Energie. |

Die daraus folgenden **Stufenbudgets von unten nach oben** sind für Neugier
`[30, 30, 30]` Sekunden und für Angst `[15, 15, 30]` Sekunden. Angst 3 bedeutet
also 30 s auf Stufe 3, danach 15 s auf Stufe 2 und 15 s auf Stufe 1; nicht
dreimal 60 Sekunden. Stärke ist ein absolutes qualifiziertes Niveau 1–3,
kein blind zu addierender Triggerwert.

- Die wahrgenommene Begegnung und der kanonische Zustand qualifizieren das
  Gefühl. Eine Körperdrehung, ein Animationsframe oder ein gesetztes Moodlet
  sind für sich keine Verstärkungsereignisse.
- Pro Familie gibt es eine aktive Episode. Derselbe qualifizierte Auslöser wird
  genau einmal verbucht; echte erneute Erfahrungen dürfen sie mit realer Ursache
  verstärken. Ein schwächeres neues Signal senkt keine stärkere Episode abrupt.
- Freundschaft und Zustand beeinflussen die erreichte Stufe. Die feste
  Zeitstaffel dieser Stufe bleibt nachvollziehbar. Niedrige Freundschaft darf
  nicht allein ein Angst-Moodlet erzeugen.
- Der Zustand wird im bestehenden Moodlet-System geführt und auf dessen
  `PetState.lived_seconds`-Achse abgebaut. Kein zweiter Emotionsspeicher und kein
  eigener Moodlet-Timer. Laden erzeugt keine neuen Mausbegegnungen.
- Cursorbegegnungen sind weder erfüllte Pflegewünsche noch Beweise absichtlicher
  schlechter Behandlung. Keine neuen automatischen Freundschaftsbelohnungen,
  -strafen, Care-History-Ereignisse oder Wunschfortschritte aus diesem Umbau.
- Beide Familien dürfen gleichzeitig nachwirken. Ihre Stimmungspolaritäten
  bleiben bei der Beitragsbegrenzung getrennt erhalten.

### Darstellung

Normale vorhandene Aiko-Bilder bleiben die Grundlage. Bei Entstehen oder
deutlicher Verstärkung kurz **1–2 Sekunden** einen vorhandenen Emote zeigen:
`question`/`idea` für Neugier und `exclamation`/`drops` für Angst.
Kein Emote pro Frame, keine automatische Sprachzeile und kein sperrender
Interaktions- oder Animationsauftrag.

Geschichten, Objektfeedback, Spiele und tatsächliche Bedienung werden dadurch
nicht unterbrochen. Ist der Sprechplatz belegt, entfällt der betreffende kurze
Emote, statt später eine veraltete Reaktion nachzuholen. Das Moodlet bleibt in
der bestehenden Anzeige mit eigener Beschriftung und tatsächlicher Ursache
sichtbar. Vorhandene Moodlet-Icons werden zunächst wiederverwendet:
`moodlet_enthusiastic` für Neugier und `moodlet_uncertain` für Angst.
Das sind benannte Darstellungszuordnungen, keine Umbenennung der bestehenden
Familien. Für kurze Restzeiten muss die Anzeige Sekunden darstellen können.

Dabei ist ein bestehender Testvertrag ausdrücklich mitzunehmen:
`tests/test_vn_assets.py` verlangt bisher einen unterschiedlichen Icon-Schlüssel
pro Moodlet. Die bisherigen Zuordnungen behalten diese Eigenschaft. Für die
zwei neuen Cursor-Familien werden ausschließlich die beiden oben benannten
Wiederverwendungen als ausdrückliche Alias-Zuordnungen geprüft; die allgemeine
Prüfung auf vorhandene Ressourcen bleibt bestehen. Weder identische PNG-Kopien
unter neuen Namen noch ein pauschales Entfernen der Eindeutigkeitsprüfung sind
Teil des Plans.

## Erreichbarkeit und Kontakt

1. **Langsame Annäherung allein verursacht keine Flucht.**
2. Pro zusammenhängender Begegnung höchstens ein Rückzug beziehungsweise
   Fluchtlauf. Flucht umfasst höchstens **eine Sekunde tatsächlicher
   Laufbewegung**; Drehen, gesperrtes Warten und Zeit im Menü zählen nicht als
   zurückgelegte Laufzeit. Räumliche Taskleistengrenzen gelten zusätzlich.
3. Anschließend mindestens **fünf Sekunden Standruhe ohne erneute Flucht**.
   Ein erneuter Fluchtversuch wird erst nach zwischenzeitlichem bestätigtem
   Verlassen des Nähebereichs zugelassen. Ein aktives Angst-Moodlet hebt diese
   Regeln nicht auf; fortgesetztes Nachsetzen startet keine Fluchtkette.
4. Ein aktiv bewegter Zeiger im Bedienbereich übernimmt sofort die Bedienung.
   Cursorbewegungsaufträge werden freigegeben, die Ortsbewegung stoppt, der
   vorhandene Kontaktpfad öffnet die Toolbar. Die Darstellung findet einen
   stabilen Stand, ohne vor dem Menü weiterlaufen zu müssen.
5. Während tatsächlicher Toolbar-/Menübedienung steht Aiko. World-Ziele und
   Objektbesitz bleiben erhalten: nötigenfalls Bewegung pausieren, nicht
   committed Ziele löschen oder physische Handlungen vortäuschen. Der aktuelle
   pauschale Menü-Bypass für committed Bewegung genügt dafür nicht.
6. Eigenbewegung unter einen ruhenden Zeiger öffnet nicht automatisch die
   Toolbar und verbucht keinen absichtlichen Benutzerkontakt. Ein anschließender
   Klick oder eine bewusste Zeigerbewegung übernimmt aber unmittelbar.
7. Ein lediglich sichtbares unbenutztes Fenster blockiert das Verhalten nicht
   unbegrenzt. Es gelten vorhandene Aktivitäts-/Bedienfakten. Schlaf, Spiele,
   geschützte Aktionen und World-Interaktionen behalten ihre fachlichen Regeln.

### Gemeinsame Geometrie und Eingabeherkunft

Als lesbare Kalibrierbasis besitzt das aktuelle Idle-Bild bei 1X eine
Alpha-Bounding-Box `(51, 38, 140, 194)`; bei 2X genau das Doppelte. Der geplante
tolerante Zugang verwendet als Startwert **sechs logische Pixel Zusatzrand**,
also zwölf Bildschirmpixel bei 2X. Das ist eine geometrische Ergänzung der
nativen Enter-/Klickwege, keine Verkleinerung ihrer bisherigen Trefferfläche.
Der Referenzbereich ist gemeinsam zu verwenden; es gibt keinen eigenen
abweichenden Hoverrand je Policy oder UI-Widget und keine Pillow-Abhängigkeit
zur Laufzeit. Quellen- und Exportmanifeste bleiben unverändert.

Native Enter-Ereignisse, Hover-Polling, tatsächliche Klicks und die Zulassung
vor jedem Bewegungsframe verwenden dieselbe Herkunfts-/Zugangsentscheidung.
Aktuelle native Ereigniskoordinaten dürfen zwischen Heartbeats gelesen werden;
das wertet die Verhaltenspolicy nicht erneut aus und dreht Aikos Wahrnehmung
nicht künstlich zum Klickort. Kontakt und wahrgenommenes Objektwissen bleiben
unterschiedliche Fakten.

## Ausgangsbefund vor dem Umbau (`2ecca2f`)

| Bestehender Vertrag | Konsequenz für den Umbau |
| --- | --- |
| `CursorBehaviourPolicy` setzt bei jedem interessanten bewegten Zeiger wieder `observe`; `CursorIntent.gaze` ist hauptsächlich eine Freigabe. | Eigenständige zeitlich gehaltene Begegnung und gewähltes Blickziel ergänzen; bloße Bewegung setzt keine Interessensdauer endlos zurück. |
| `DesktopVisualObservation.attention()` nutzt bei freigegebenem Interesse weiter `relative(pointer)`. | Für allgemeines Mausinteresse das gewählte Ziel beziehen. Die vorhandenen fachlichen World-/Objektziele bleiben maßgeblich. |
| `BodyOrientation.select()` leitet die Körperseite direkt aus dem Blicksektor und 1,2 s Verweilen ab. | Durch explizite Ausrichtungsabsicht ersetzen; frontal mit beliebigen Kopfblicken ist regulär. |
| `RandomWalkPlanner` plant aktuell einen Schritt mit 35–65 s Pause; ohne Schrittpaket fällt er auf Rennen zurück. | Eigene ruhige Idle-Folge mit 45–90 s und ein oder zwei Schritten; ohne Paket kein Idle-Rennersatz. |
| `WalkDriver.apply_cursor_intent()` kennt im Wesentlichen einen Wegbetrag und ein Ablaufdatum. | Zahl und Ende kleiner Schritte sowie tatsächliche Laufzeit getrennt von Dreh-/Wartezeit führen. |
| `reinforce_moodlet()` arbeitet teilweise additiv und verweigert für Interaction-/Periodenereignisse direkte Stufen über 1. | Cursorbelege erhalten einen gezielten absoluten Vertrag; bestehende Pflege-/Poke-Verträge nicht aufweichen. |
| `MoodletDefinition.uses_positive_stage_budgets` und Codecs reservieren explizite untere Stufen bislang für positive Wunschbudgets. | Kurze explizite Cursor-Profile samt validierter Speicherung ergänzen, ohne deren Stundenprofile zu übernehmen. |
| `calculate_moodlet_contributions()` summiert zuerst pro Gruppe. | Bei einer neuen gemischtpolaren Cursor-Gruppe positive und negative Beiträge getrennt begrenzen; bestehende Gruppen müssen identische Ergebnisse behalten. |
| `MoodletRead` liefert bereits aktuelle und gesamte Restzeit; `duration_text()` rundet kurze Werte auf Minuten. | Vorhandenes Read-Modell verwenden und Sekundendarstellung ergänzen. |
| `ContactCoordinator.enter()` und `WalkDriver` besitzen bereits Unterbrechungs-/Platzierungspfade. | Diese verbinden; keinen zweiten Kontakt- oder Positionsbesitzer schaffen. |
| `SpeechPresenter.show_emote()` ersetzt die aktuelle Sprechblase; `ReactionPlayer` kann Interaktionen sperren. | Vor der Darstellung fachlich zulassen; kurze Cursor-Emotes erzeugen keine geschützte ReactionPlayer-Aktion. |

## Umgesetzte Modul- und OOP-Zuständigkeiten

Pfade sind relativ zu `aiko_pet/`, soweit nicht anders benannt. Neue Werte und
kleine Methoden gehören zu diesen Besitzern; keine neue Managerhierarchie.

| Modul / Besitzer | Umgesetzter Vertrag |
| --- | --- |
| `pet/mind/cursor_attention.py` / `CursorAttention` | Einziger Besitzer roher Zeigerhistorie und geglätteter Geschwindigkeit. Messungen von subjektivem Interesse getrennt halten. |
| `application/cursor_observation.py` / `CursorObservation` | Gemeinsame Geometrie, Reichweite, Nähe und Eingabeherkunft liefern; keine Moodlet- oder Bewegungsentscheidung. |
| `pet/mind/cursor_behaviour.py` / `CursorBehaviourPolicy` | Eine Begegnung mit stabiler Identität, gewähltem Aufmerksamkeitsziel, beabsichtigter Körperrichtung, begrenzter Bewegungsfolge, Erholung und Freigabebedingung besitzen. Unveränderliche Entscheidung plus höchstens neu qualifizierte Gefühlsbelege zurückgeben. |
| `application/cursor_behaviour.py` / `CursorBehaviourCoordinator` | Den kanonischen Pet-Zustand lesen, einmal pro Eingabephase entscheiden, neue Belege genau einmal über PetState verbuchen, Absicht an alle Leser teilen und Bewegung nach World sowie vor Frames erneut zulassen. Kein eigener Moodlet-Zustand. |
| `pet/interaction_events.py` | Kleinen unveränderlichen `CursorExperience`-Wert mit Begegnungs-/Belegidentität, Art und absoluter Stärke ergänzen. Nicht als vorhandene Pflege-/HelpfulInteraction behandeln. |
| `pet/state.py` / `PetState` | Dünne öffentliche Methode `experience_cursor(event)` als einziger veränderlicher Zugang. Die reine Cursor-Erfahrungsfunktion liefert den neuen MoodletState; keine Fenster-/UI-Zugriffe. |
| `pet/moodlet_types.py`, `pet/moodlet_models.py` | Eigene IDs `CURSOR_CURIOSITY` und `CURSOR_FEAR`, eine kurze Gruppe `CURSOR` und kleine Profilparameter für die expliziten drei Stufen vorsehen. Bestehende Richtungen `CHEERFUL` beziehungsweise `UNCERTAIN` wiederverwenden; die konkreten Familien behalten ihre eigenen Namen und Ursachen. |
| `pet/moodlet_catalog.py`, `data/moodlets.json`, `pet/moodlet_timing.py`, `pet/moodlets.py` | Geschlossene Gruppen-/Polaritätsprüfung für die neuen Familien erweitern, kurze Stufenbudgets und absoluten Cursor-Vertrag unterstützen. Kein Umdeuten bestehender Wish-, Poking- oder Long-term-Verstärkung. |
| `infrastructure/moodlet_codec.py`, `infrastructure/moodlet_cause_codec.py`, `infrastructure/sqlite/moodlet_rows.py`, `infrastructure/sqlite/moodlet_cause_rows.py` | IDs, echte Ursachen und explizite Sekundenbudgets rundlaufend validieren. Bestehende SQLite-Tabellen erlauben die Text-IDs und Stufen bereits; kein vorsorglicher Datenbankumbau. Alte Saves bleiben lesbar. |
| `application/read_snapshot.py`, `ui/view_models/emotional_text.py`, `ui/view_models/moodlet_causes.py`, `data/texts.de.json` | Eigene Labels, Quellenbezeichnung Mauszeiger, vorhandene Icon-Zuordnung und genaue kurze Restzeiten. Read-Modell nur bei tatsächlicher Datenlücke ändern. Kein eigener UI-Moodlet-Speicher. |
| `desktop/pointer_runtime.py` / `PointerRuntime` | Native Eingabe mit Beobachtung verbinden, absichtliche Zugangsübernahme als begrenzten Laufzeitzustand halten, Cursorauftrag freigeben und diesen Zugang an Einlassprüfung und Kontaktpfad teilen. Lesen einer Zulassungsbedingung allein darf keine neue Begegnung oder wiederholte Kontaktreaktion auslösen. |
| `desktop/geometry.py`, `desktop/input.py`, `ui/windows/hover_ui.py`, `application/contact.py` | Gemeinsamer toleranter Bereich, Enter-/Polling-/Klickpfade und vorhandene Toolbaröffnung. Kontakt gilt vor weiterem Ortsversatz; Eigenbewegung bleibt als solche erkennbar. |
| `desktop/visual_observation.py`, `application/object_behavior.py`, `desktop/world_runtime.py` | Gewählte Aufmerksamkeit einmal in Blick und Wahrnehmung projizieren. Keine konkurrierende lebende Cursorposition hinter der Policy. Echte angebotene Objektziele und geschützte World-Phasen erhalten. |
| `pet/animation/body_orientation.py` / `BodyOrientation` | Ausschließlich tatsächliche Ausrichtung/Drehphase ausführen. Explizite Front-/Dreiviertel-/Profilabsicht statt automatischer Körperableitung aus Kopfsektoren; Gegenrichtung über Front und stabiler Stand bei Abbruch. |
| `desktop/animation_runtime.py`, `ui/pet_view/animated_pet.py`, `pet/animation/gaze.py` | Dieselbe ausgewählte Absicht auf erlaubte Kopf-/Körperbilder abbilden; Kopfwechsel setzt Schrittzeit nicht zurück. `pet/animation/gaze.py` bleibt Winkel-/Hystereserechnung, kein Interessensbesitzer. Renderer rendert und meldet Fortschritt zurück. |
| `pet/movement/contracts.py`, `pet/movement/controller.py`, `desktop/walk_runtime.py` | Ein Auftrag mit Quelle/Identität, ein oder zwei Schritten und begrenztem tatsächlichem Laufbudget; Abschluss mit Grund/Fortschritt zurückmelden. Einziger Ausführungs- und Positionspfad bleibt erhalten. Bedienung pausiert auch World-Ortsbewegung, ohne dessen Auftrag zu löschen. |
| `pet/movement/random_walk.py`, `pet/animation/ambient.py` | Bestehende Besitzer für seltene Idle-Ortswechsel und eigene Kopfblick-/Blinkgelegenheiten anpassen. Kein zweiter Bewegungs- oder Idle-Timer. |
| `desktop/attention_runtime.py`, `application/attention.py`, `ui/pet_view/attention_presenter.py`, `ui/pet_view/speech_presenter.py` | Neue qualifizierte Cursor-Emotes fachlich zulassen und vorhandene Anzeige benutzen. Alte automatische `cursor_far`-/`cursor_follow`-Kommentare und `walk_pause` für diese Idle-/Cursorfolgen nicht parallel auslösen. Autorentexte/Katalogereignisse nicht pauschal löschen; andere tatsächliche Aufrufer vorher prüfen. |
| `desktop/runtime.py`, `application/assembly.py`, `desktop/animation_assembly.py`, `desktop/preferences.py`, `gui.py` | Bestehende Instanzen einmal verdrahten, Reset-/Kontakt-/Abschlusswege erweitern. GUI bleibt Composition Root innerhalb ihrer bestehenden Größen-/Abhängigkeitsgrenzen. |
| `data/balance.json`, `pet/balance_contract.py` | Zeitwerte, Geometrie und Reaktionsgrenzen an einem validierten Ort führen. Moodlet-Punkte und Stufenprofile gehören dagegen in den Moodlet-Katalog; keine doppelten Zahlenquellen. |

### Genau ein neues Produktionsmodul

`pet/cursor_experiences.py` enthält die kleine reine Funktion
`apply_cursor_experience(...) -> MoodletState`. Sie wendet bereits qualifizierte
absolute Stärken und echte Belege auf die zwei Familien an. Sie besitzt weder
PetState noch Uhr, Input, Policy oder UI. Diese Trennung verhindert, dass die
neue positive Erfahrung durch die bestehende Funktion für schlechte
Pflegeerfahrungen läuft oder eine Angstreaktion fälschlich Pflegevergehen zählt.

Die vorhandenen beiden Cursor-Produktionsmodule werden umgebaut, nicht durch
weitere Koordinatoren ersetzt. Unveränderliche Werte bleiben in den bestehenden
Vertrags-/Ereignismodulen. Neue Testmodule sind keine neuen Produktionsbesitzer.

## Zustände, Identitäten und Update-Reihenfolge

- Die Cursorpolicy hält nur die aktuelle Begegnung: bemerken/beobachten,
  bewusst zuwenden, annähern oder zurückweichen, beruhigen und lösen. Sie
  speichert gewähltes Ziel und Absicht, keine zweite reale Körperphase.
- `BodyOrientation` besitzt reale Ausrichtung und Drehfortschritt;
  `WalkController` besitzt reale Strecke, Restweg und tatsächlich verbrauchtes
  Bewegungsbudget. Die Policy liest Rückmeldungen dieser Besitzer.
- Eine Aufmerksamkeit darf durch ruhige Folgepunkte aktualisiert werden, ohne
  ihre Identität, Körperdrehung und Schrittzeit jedes Mal neu zu starten.
  Seitenwechsel und Interessenverlust sind explizite Übergänge.
- Belege besitzen eine stabile Identität pro qualifiziertem Ereignis. Eine
  injizierte neue Sitzungskennung verhindert Kollisionen mit gespeicherten
  Ursachen nach Neustart; Tests verwenden eine feste Kennung. Die aktuelle
  Begegnung und ausgelieferte Revisionen bleiben begrenzt und sitzungslokal.
- PetState verbucht Belege auf dem im bestehenden Lifecycle bereits
  fortgeschrittenen Endpunkt. Keine doppelte Zeitkonsumierung im selben Tick,
  keine Moodlet-Mutation aus Render-, Frame- oder Tooltip-Callbacks.
- Reihenfolge bleibt: Lifecycle/Bedienung, Zeigerbeobachtung, eine
  Cursorentscheidung und deren neue Pet-Erfahrungen, World-Beobachtung mit der
  geteilten Aufmerksamkeit, Bewegungszulassung gegen den neuen World-Zustand,
  Darstellung. Native Kontaktübernahme und jede Framebewegung prüfen aktuelle
  harte Sperren zusätzlich; sie berechnen die Policy nicht erneut.
- Nach Deaktivierung der Option, Spiel-/Schlafwechsel, Maßstabswechsel oder
  ungültiger Eingabe werden flüchtige Absichten und Cursoraufträge gezielt
  freigegeben. Moodlets altern im kanonischen System weiter; bestehende World-
  Aufträge und Objektbesitz werden nicht als Cursorzustand zurückgesetzt.
- Zwei gemeinsame Moodlets dürfen keine sich selbst verstärkende Schleife
  bilden. Das Vorliegen eines Moodlets oder sein Beitrag zu `state.mood`
  qualifiziert keinen neuen Beleg ohne erneute passende äußere Situation.

## Geplante lokale Commitfolge

Die folgende Reihenfolge wurde für diesen Umbau umgesetzt. Jeder Funktionscommit migriert seine unmittelbar
betroffenen Signaturen/Aufrufer gemeinsam; keine bewusst kaputten Imports und
keine zweite dauerhafte Legacy-Verfolgung neben dem neuen Besitzer.

**Pro Commit ausschließlich die gezielten Tests des jeweiligen Vertrags.**
Gezielter Lint-/Typcheck geänderter Module bei Bedarf. Kein pauschaler globaler
Prüflauf oder Zwischenpush nach jedem Commit. Weitere Tests nur bei neuem
konkretem Befund. Vorhandene Baselines nicht durch pauschale Skips oder
abgeschwächte fachliche Erwartungen grün machen.

| Nr. / Commit | Abgeschlossener Umfang | Ausschließlich gezielte Tests |
| --- | --- | --- |
| 1 — `docs(cursor): record revised behavior and rework ownership` | Diese Konzeptfassung, Statusverweise in den älteren Dokumenten, Modulgrenzen und Commitfolge. | Dokumentlinks, vorhandene Modul-/Testpfade und Widerspruchsfreiheit. Keine Laufzeitsuite. |
| 2 — `feat(moodlets): support short cursor impression profiles` | Neue IDs/Gruppe/Profilwerte, Katalog und Texte, getrennte Polaritätsbeiträge, Stufenzeiten, passende Codec-/SQLite-Rundläufe sowie vollständige bestehende Icon-/Read-Zuordnung atomar einführen. Noch keine laufenden Cursorereignisse erzeugen. | `test_moodlet_catalog.py`, `test_moodlet_timing.py`, `test_moodlet_progression.py`, `test_moodlet_mood.py`, `test_emotional_reads.py`, Klasse `MoodletPersistenceTests` aus `test_emotional_persistence.py`, `test_sqlite_moodlet_rows.py`; gezielte Katalog-/Iconfälle aus `test_vn_assets.py`, `test_vn_status.py` und `test_resource_validation.py`. Fälle für exakte 30/60/90 und 15/30/60 s, Sekundendarstellung, alte Wunschbudgets, beide Polaritäten, genau zwei freigegebene Icon-Aliasse und ältere Saves. |
| 3 — `refactor(cursor): select stable attention encounters` | Vorhandene Cursorpolicy und immutable Entscheidungen um stabile Ziele, Körperabsicht, Stärke, neue Belege und Freigabe nach Verlassen erweitern; den unveränderlichen CursorExperience-Wert in `pet/interaction_events.py` einführen und kanonische Parameter sowie direkt betroffene Coordinator-Adapter mitführen. | `test_cursor_behaviour_policy.py`, `test_cursor_behaviour_coordinator.py`; relevante Fälle aus `test_cursor_observation.py` und `test_cursor_attention.py`. Kontrollierte Zeitreihen für ruhiges Interesse, hektischen Seitenwechsel, Freundschaft/Zustand, Vorbeifahrt, Eigenbewegung und Samplinglücken. |
| 4 — `feat(cursor): commit qualified moodlet experiences once` | Neues reines `pet/cursor_experiences.py`, dünne PetState-Methode für den bereits eingeführten Ereigniswert und genau eine Coordinator-Übergabe am fortgeschrittenen Endpunkt. Echte Belege statt Pflege-/Belohnungsereignissen. | Neu: `tests/test_cursor_experiences.py`; `test_cursor_behaviour_coordinator.py`, gezielt `MoodletPersistenceTests` und `test_care_evidence_storage.py`. Doppellieferung, Revisionen, Sitzungswechsel, absolute Stärke, beide Gefühle, kein Selbsttrigger, keine Freundschafts-/Care-/Wish-Gutschriften und atomarer Zustand bei Fehler. |
| 5 — `refactor(gaze): share selected attention with world perception` | VisualObservation und World verwenden dieselbe ausgewählte Aufmerksamkeit; allgemeines Live-Nachführen ersetzen, Objektfokus sowie aktuelle native Greifkoordinaten erhalten. | `test_desktop_visual_observation.py`, `test_cursor_front_pose.py`, `test_cursor_behaviour_integration.py`, gezielte WorldGui-Fälle unten. Prüfen, dass ein Rohpunkt keine unbeabsichtigte Kopf-/Wissensänderung erzwingt und ein angebotenes Objekt weiter korrekt verfolgt wird. |
| 6 — `refactor(animation): execute explicit body orientation plans` | Automatische Körperableitung aus Kopfsektor/1,2-s-Verweilen ersetzen. BodyOrientation, Animationsauswahl und notwendige Rendererports gemeinsam auf explizite Front-/Dreiviertel-/Profilabsichten führen. | `test_body_orientation.py`, `test_desktop_animation_runtime.py`, `test_animated_pointer_ports.py`; gezielte Schritt-/Kopfwechsel-/Reloadfälle aus `test_animated_pet_isolation.py`. Alle 16 Richtungen frontal, gehaltene Absicht, Gegenblick, geordneter Rückweg und erhaltener Framefortschritt. |
| 7 — `feat(movement): bound cursor steps and actual escape time` | Ein oder zwei kleine Schritte, erneute Zulassung an der zweiten Schrittgrenze, tatsächliches Ein-Sekunden-Laufbudget, genau eine Rückmeldung mit Quelle/Grund und stabile Beendigung. Idle-/Cursorfolgen nicht durch alte Laufabschlusskommentare begleiten. | `test_movement_requests.py`, `test_desktop_walk_runtime.py`, `test_goal_walk.py`, Klasse `WalkControllerTests` aus `test_motion_animation.py`, relevante `test_desktop_animation_runtime.py`-/`test_desktop_attention_runtime.py`-Fälle. 1X/2X, Rand, blockierter zweiter Schritt, nur reale Laufzeit, Stoppgrund und World-Zielerhalt. |
| 8 — `fix(input): guarantee pointer access during cursor reactions` | Gemeinsamer toleranter Bedienbereich und Herkunftsentscheidung, Enter-/Polling-/Klickübernahme, sofortige Cursorfreigabe, harte Bewegungspause bei tatsächlicher Bedienung auch für erhaltene World-Ziele. Keine Fluchtkette nach Rückzug. | Neu: `tests/test_cursor_menu_access.py`; `test_cursor_contact_origin.py`, `test_desktop_input_controller.py`, gezielte `test_hover_geometry.py`-/`test_hover_isolation.py`-/`test_contact_coordinator.py`-Fälle sowie `test_desktop_walk_runtime.py`. Schneller Erstkontakt, Zugang zwischen Frames, Eigenkontakt, aktives Angst-Moodlet, Klick ohne vorheriges Hover, Menü offen, sichtbares unbenutztes Fenster und committed World-Ziel prüfen. |
| 9 — `feat(cursor): present brief nonblocking feeling emotes` | Qualifizierte Gefühlswechsel über vorhandenen Attention-/Speech-Pfad präsentieren. Kein Sperren durch ReactionPlayer, kein Überschreiben geschützter Texte, keine parallelen alten Cursor-Kommentare und keine Emote-Warteschlange. | `test_attention_presenter.py`, `test_speech_presenter.py`, `test_desktop_attention_runtime.py`, `test_reaction_playback.py`, `test_contact_coordinator.py`; neue Integrationsfälle für ein Emote pro Auslöser/Stufenwechsel, Ablenkung während Geschichte/Objektfeedback und sofort bedienbares Menü. |
| 10 — `refactor(idle): choose quiet one or two step outings` | Vorhandenen RandomWalkPlanner und AmbientDirector auf 45–90 s freie Idle-Gelegenheiten, 20–40 s Kopfblickgelegenheiten, bewusste Dreh-/Schrittfolge und Rückkehr zur Front abstimmen. Ohne Schrittpaket stehen bleiben; kein Idle-Rennen und kein Kommentar. | `test_idle_steps.py`, `test_ambient_director.py`, `test_pet_idle_emote_boundary.py`, passende `test_desktop_animation_runtime.py`-/`test_cursor_behaviour_integration.py`-Fälle. Blinkschwanken, volle frontale Blickfreiheit, ein/zwei Schritte, Unterbrechung, fehlendes Paket und keine alte Textreaktion. |
| 11 — `test(cursor): verify complete behavior trajectories and final CI` | Bestehende Assemblies/Resets vollständig verbinden, Zeitreihen und praktische Abnahmeliste vervollständigen, Architektur-/Verhaltensdocs auf den tatsächlich erreichten Stand bringen, neue Testmuster im vorhandenen Windows-Job ergänzen. | Zuerst gezielte Integrations-/Assembly-/Präferenz-/World-Grenzfälle; danach einmal alle lokalen Tests und globalen statischen Gates sowie die echte vollständige GitHub-CI am finalen Head. Vorgehen unten. |

Schritt 1 enthält die vor der Umsetzung vorbereiteten Konzeptdokumente.

### Gezielte World- und Kontaktregressionen

Bei Commit 5 sind aus `WorldGuiTests` insbesondere vorgesehen:

- `test_native_relocation_reads_event_pointer_between_sensor_samples`
- `test_new_unknown_left_item_resumes_after_native_orientation_at_scale_two`
- `test_new_unknown_right_item_resumes_after_native_orientation_at_scale_two`
- `test_unknown_orientation_subject_stays_visible_on_a_narrow_track`
- `test_missing_unknown_approach_target_releases_without_patrol`
- `test_actual_driver_reaches_food_with_random_walk_disabled`

Die bestehenden Testfixtures für manuelle World-Ticks müssen den neuen
gemeinsamen Aufmerksamkeitspfad verwenden. Ein direkter Rohzeiger- oder
Rendering-Aufruf darf die Policy in einem Test nicht versehentlich umgehen.
Unbekannte Gegenstände werden nicht allein durch einen Klick als gesehen oder
erkannt angenommen. Kleine native Desktops dürfen zusätzliche Testgegenstände
nicht auf dasselbe Randziel legen und damit den eigentlichen Gegenstand verdecken.

Commit 8 prüft zusätzlich vorhandene Kontaktfälle
`ContactCoordinatorTests.test_hover_opens_toolbar_and_interrupts_walk` und
`test_hover_greeting_and_ui_contact_do_not_renew_durable_care`.
Der neue Zugangsvertrag muss den vorhandenen Pflege-/Story-/World-Schutz erhalten.

## Abnahme und vollständige CI am Schluss

1. Vor jedem späteren Commit den konkreten Diff prüfen und nur dessen Dateien
   aufnehmen. Parallele UI-Arbeiten, private HD-Quellen und reguläre Atlanten
   bleiben außerhalb dieser Änderungen. Existierende gültige Arbeit nicht
   zurücksetzen oder die bereits gepushten Commits umschreiben.
2. Funktionale Zwischencommits ausschließlich mit den aufgeführten Fachtests
   prüfen. Kein Zwischenpush allein zum erneuten Auslösen der gesamten CI.
   Bei Fehlern die betroffenen Fälle korrigieren und erneut prüfen.
3. Vor dem Abschluss lange kontrollierte Zeitreihen durch die echten Besitzer
   führen: schneller Links-rechts-Wechsel, ruhiger Zeiger, erst neugierig dann
   erschrocken, hohe/niedrige Freundschaft, Müdigkeit, Blockierung/Erholung,
   Menüübernahme zwischen Frames, Körperrückweg und beide Größen. Assertions
   prüfen Ziel-/Absichtswechsel, Position, Schritte, echte Laufzeit, belegte
   Moodlet-Ursachen und erreichbare Bedienung; nicht bloß vorhandene Clipnamen.
4. Am abschließenden Stand vollständig lokal prüfen:
   `python -m ruff check aiko_pet tests main.py tools`,
   `python -m mypy --strict --no-incremental aiko_pet main.py tools`,
   `python -m pyright --project pyrightconfig.json` und
   `python -m unittest discover -s tests -q` einschließlich Tk-Grenzen.
   Vorhandene Linux-/Xvfb-Testumgebung für konkrete plattformabhängige Befunde
   nutzen. Xvfb ohne Window Manager bestätigt einen Topmost-Auftrag nicht wie
   eine echte native Oberfläche; dafür den realen Settervertrag und kanonische
   Einstellung prüfen, nicht fachliche Tests pauschal überspringen.
5. Praktische Sichtung durch den Nutzer: nach Neustart mit dem neuen Code
   frontal frei umsehen, bewusst drehen, ein/zwei ruhige Schritte und Standruhe
   nach Schreck prüfen. Mindestens einmal bei aktiver Angst die Toolbar mit
   der Maus erreichen und bedienen. Keine Computer-Use-/UI-Fernsteuerung;
   für einen isolierten App-Smoke-Test vorhandene Test-Save-Wege verwenden.
6. Zum technischen Abschluss gehört **echte GitHub-CI** am exakten letzten
   Head: `Tests` auf dem vorhandenen PR #11 beziehungsweise seinem dann gültigen
   Nachfolger. Ein bloßer Branch-Push ohne zugehörigen PR löst diesen Workflow
   derzeit nicht aus; Push nach `main` ist kein Weg zur Abnahme. Umsetzung und
   späterer Push bedürfen ihres jeweiligen Auftrags. Kein automatischer Merge.
7. Die vorhandenen drei Jobs umfassen Linux Python 3.11/3.13 mit globalen
   statischen Prüfungen und vollständiger Unit-/GUI-Suite sowie Windows setup
   and desktop boundaries. Neue Testmodule kommen in dessen bestehende
   Testmuster. Pillow bleibt dort als bereits vorhandene Testabhängigkeit
   installiert; kein zweiter CI-Workflow und kein zusätzlicher manueller
   statischer Audit als Ersatz für die vollständige CI.
8. CI-Fehler gezielt untersuchen, betroffene Tests nachprüfen und die echte CI
   am korrigierten Head abwarten. Nur bestätigte Ergebnisse als grün ausweisen.
   Lauf-/Head-Zuordnung im Abschlussbericht festhalten, ohne für eine reine
   Statusnotiz nachträglich wieder einen vollständigen CI-Lauf zu erzeugen.
9. **Technisch grün und praktisch abgenommen sind getrennte Befunde.** Ohne
   entsprechende Nutzersichtung ist die Verhaltenswirkung weiterhin offen;
   aus grüner CI allein folgt diesmal kein Urteil „verhaltensseitig fertig“.

## Ursprüngliche Prüfung der Dokumentationsrunde

Vorgesehen sind ausschließlich relative Dokumentlinks, Modul-/Testpfade,
eindeutige Zuständigkeiten, widerspruchsfreie Zeiten und ein kontrollierter
Git-Diff. Die hier geplanten Funktionen und neuen Testmodule werden dafür
nicht angelegt. Keine Laufzeittests oder vollständige CI durch bloßes Planen.


## Umsetzungsprüfung vom 27.10.2026

Die elf Schritte wurden in der festgelegten Reihenfolge ausgeführt. Die ersten
zehn Commits enthalten jeweils den abgeschlossenen Fachvertrag mit gezielter
Prüfung; Schritt 11 verbindet die tatsächlichen Assemblies/Resets, ergänzt
kontrollierte längere Abläufe und führt die abschließenden globalen Gates aus.
Neue Produktionsdatei ist ausschließlich `pet/cursor_experiences.py`.

Zusätzliche Befunde aus der Gesamtsuite:

- Renderer-Tests geben die ausgewählte Aufmerksamkeit und explizite Körperabsicht
  jetzt über den echten Port vor. Ein Raw-Pointer-Argument allein ist keine
  fachliche Auswahl und löst keine automatische Körperdrehung mehr aus.
- Beobachteter Objekttransport setzt eine tatsächlich ausgewählte Sicht auf den
  Gegenstand vor dem nativen Grab voraus. Die Ereigniskoordinate bleibt frisch;
  sie erzeugt keine erfundene Blick-/Wissensänderung.
- World-Tests prüfen während Hover/Bedienung ausdrücklich Stillstand und danach
  die Fortsetzung desselben Ziels. Frühere Erwartungen, während geöffnetem
  Zugriff weiterzulaufen, widersprachen der neuen Erreichbarkeitsregel.
- `SpeechPresenter.blocks_contact` unterscheidet eine kurze Cursor-Emoji-Anzeige
  von geschützter Sprache. Ein freier Cursorhinweis blockiert weder Kontakt noch
  gemeinsame visuelle Wahrnehmung und kann vorhandene Sprache nicht ersetzen.
- Ein Reset verwirft sowohl Rohhistorie als auch abgeleitete Zeigerbeobachtung;
  gespeicherte Moodlets und fremde World-Aufträge bleiben bestehen.

Die vollständigen lokalen Ergebnisse und der exakte GitHub-CI-Head werden im
Abschlussbericht belegt. Die Nutzer-Sichtung nach Neustart bleibt ausdrücklich
getrennt: frontales Umsehen, bewusste Drehung, ein/zwei Schritte, Ruhe nach
Schreck und Toolbarzugang bei aktivem Angst-Moodlet. Keine automatische
Computer-Use-Sichtung und kein Merge.


### Abschließende lokale technische Befunde

- Globales Ruff: bestanden.
- Striktes Mypy über Anwendung, Einstieg und Tools: 361 Dateien, bestanden.
- Repository-weites Pyright einschließlich Tests: 0 Fehler/Warnungen.
- Windows-Gesamtsuite mit echten Tk-Grenzen: 2.308 Tests, bestanden.
- Linux/Xvfb (lokaler Debian-Container, Python 3.11.2): 2.308 Tests,
  acht bestehende Plattform-Skips, genau ein Mastermind-Layoutfehler.
  `test_first_mapping_shows_all_ten_rows_when_body_has_room_without_input`
  misst dort 496 statt benötigter 504 Pixel. Der gezielte Vergleich auf dem
  unveränderten Ausgangscommit `2ecca2f` ergibt exakt denselben Fehler.
  An diesem UI-Code und dieser Test-Erwartung wurde nichts geändert.
  Alle neuen Cursor-/Moodlet-/Bewegungs- und World-Grenzfälle bestehen.
- Das ältere Containerimage benötigte die bereits in `requirements.txt`
  vorgeschriebene `astronomy-engine==2.1.19`. Sie wurde ausschließlich in der
  isolierten Testumgebung ergänzt. Keine gelockerten Abhängigkeits-/Starttests.
- Der Asset-Diff gegenüber `2ecca2f` ist leer. Die GUI-Composition-Root bleibt
  mit 637 Zeilen innerhalb der bestehenden Grenze von 640.

Die echte Ubuntu-3.11-/3.13- und Windows-CI wird am abschließenden Commit auf
PR #11 geprüft; ihr exakter Head und Befund gehören in den Abschlussbericht.
