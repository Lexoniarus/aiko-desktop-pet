# Mausaufmerksamkeit: Stufen, Vorwarnung und Gefühlsreaktionen

> **Formularentkopplung, 30.10.2026:** Der
> [Hover-Fix](HOVER_ACTION_DECOUPLING_FIX_PLAN.md) ersetzt frühere Regeln,
> die Menübedienung als Kontakt, Cursorpause oder Bewegungssperre behandelten.
> Reine Formularbedienung besitzt keine Handlung; ausdrückliche akzeptierte
> Interaktionen behalten ihre bestehenden Schutz- und Abschlussregeln.

Stand: 27.10.2026. Ausgangsbasis: `9a233d7` auf
`feature/social-optimization`. **Der dokumentierte Umbau ist in den neun
geplanten Schritten umgesetzt.** Die praktische Verhaltensabnahme durch den
Nutzer steht aus. Assets und parallele UI-Arbeiten bleiben unverändert; kein
Merge ist freigegeben. Die folgende Spezifikation ist der aktuelle Vertrag.

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

Auch bei bestehender Neugier oder Angst darf die Policy nach ausreichender
Aufmerksamkeit und beständiger Seitenbeobachtung eine Dreiviertel-Standhaltung
anfordern. Das Gefühl selbst löst weder diese Drehung noch neue Bewegung oder
Erfahrungsbelege aus. Kurze wechselnde Seitenblicke bleiben frontal; das
Blickziel folgt unabhängig von der gehaltenen Körperabsicht weiter dem Zeiger.

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
| Normale Bewegung ab 0,5 und unter 1,5 W/s | +12 Punkte/s |
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

Beim normalen Beobachten ohne aktives Cursor-Gefühl darf eine
Dreiviertelzuwendung gewählt werden, wenn Aufmerksamkeit mindestens
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

Bei tatsächlich aktivem Neugier- oder Angst-Moodlet und bereits bemerktem,
frischem Zeiger hat der Blick Vorrang. Frontal ist die Grundhaltung; beständige
Seitenbeobachtung kann auch ohne Ortsbewegung die gewählte Dreiviertelpose
halten. Blockiert die tatsächliche Körperpose den neuen Kopfsektor,
zeigt bereits derselbe Renderaufruf frontal mit passendem Kopf. Für eine
Cursorbewegung folgt eine passende bestehende Dreiviertel-Kopfpose und nach
70 ms der Profil-Schrittsatz mit passendem Kopf. Ein Seitenwechsel kann dabei
über die sofortige Frontkorrektur führen; die frühere Pflicht, erst alle acht
Drehzwischenbilder abzuspielen, gilt hier nicht mehr. Gerade nach oben/unten
oder direkt vor die Nase bleibt frontal frei; passende vertikale Kopfsektoren
sind auch in Dreiviertel erlaubt. Körperbegrenzung und Kopfwahl nutzen dafür
dieselben Sektorgrenzen einschließlich Hysterese. Eine unpassende Profillage hält
nur die Ortsbewegung, nicht den Blick. Normale Idle-/World-Drehungen behalten
ihre vollständigen 140-ms-Phasen.

Der vorhandene Sprite-Animationstimer erhält den nächsten Darstellungszeitpunkt
über `RenderDecision`; der 140-ms-Sensor-/Verhaltenstakt bleibt unverändert.
Eine Darstellungsauffrischung liest nur die bereits gewählte Absicht und wertet
Sensor, Policy oder Moodlet-Zeit nicht erneut aus. `desired_cursor_gaze` ist eine
reine Projektion zur Posewahl: World erhält weiterhin die tatsächlich gezeigte,
körperkompatible Aufmerksamkeit, keinen vorweggenommenen Gegenblick. Ein
Moodlet allein startet weder Blick noch Bewegung.
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

**Neugier** kann ab bemerkter Aufmerksamkeit (20) nach einer Sekunde
passender, ungefährlicher Bewegung entstehen. Normale Bewegung baut mit
12 Punkten/s auf; schnelle/sehr schnelle Bewegung behält 18/24 Punkte/s.
Kontrollierte kontinuierliche Proben bei 1/2/4 Körperbreiten pro Sekunde
qualifizieren damit nach 2,7/2,2/1,9 Sekunden statt 19,5/5,9/5 Sekunden.
Ein einzelner Vorbeiflug oder ruhiges Halten erzeugt kein sofortiges Moodlet.
Ruhe, bedrängende Bewertung und eine echte Beobachtungslücke unterbrechen die
Qualifikation. Menüpausen erhalten nur die zuvor wirklich beobachtete Zeit:
Die vorhandene Policy verschiebt ihren Qualifikationsbeginn um die gültigen
Menü-Sampleintervalle, statt Menüzeit als sichere Bewegung zu zählen.

Die Bewertung einer schnellen Nahannäherung erfolgt vor dem Text:
- Ein bestehendes Angst-Moodlet bleibt defensiv.
- Bei mindestens 25 Energie gilt bestehende Neugier ab Stimmung 45 als
  spielerisch; alternativ genügt `Stimmung + 3 * (Freundschaftsstufe - 1) >= 75`.
  Damit können sowohl gute Stimmung bei geringer Freundschaft als auch
  Vertrautheit bei mittlerer Stimmung positives Interesse ermöglichen.
- Schnelles Vorbeiflitzen überschreibt eine spielerische Bewertung nicht pauschal
  mit Angst. Ändern sich Zustand oder Bewertung defensiv, braucht neue Angst
  weiterhin eine eigene tatsächlich angezeigte defensive Vorwarnung.
- Spielerisches Vorbeiflitzen wählt `cursor_notice_playful`. Nur eine defensive
  tatsächliche Nahannäherung wählt `cursor_warning_near_fast`.

Der bestehende flüchtige `CursorWarning` transportiert dafür einen typisierten
Ton (`playful`/`cautious`, bisherige Konstruktoren bleiben vorsichtig).
Die Quittung einer spielerischen Anzeige darf niemals ein Angst-Warnfenster
öffnen oder dessen Wiederholungssperre verbrauchen. Texte bleiben kurze
Katalog-Cues ohne Aktionsbesitz; Annäherungshinweise stehen 2,8 Sekunden,
qualifizierte Gefühls-Kommentare 3 Sekunden. Belegte Sprechplätze bleiben geschützt.

**Angst** entsteht erst nach dem oben bestätigten Warnablauf und einem neuen
bedrängenden Anlass. Vorwarnung allein verändert keine Stimmungspunkte.

Die vorhandenen Familien `CURSOR_CURIOSITY` und `CURSOR_FEAR`, ihre Stärken 1–3,
Punkte, Symbole und Speicherverträge werden wiederverwendet:

| Gefühl | Bestehende Beiträge | Bestehende frische Gesamtdauer Stufe 1/2/3 | Mögliche Folge |
| --- | --- | --- | --- |
| Neugier | +1 / +2 / +3 | 30 / 60 / 90 s | Beobachten, zuwenden, bei starker Neugier spielerischer Fangversuch. |
| Angst | −2 / −4 / −6 | 15 / 30 / 60 s | Schreck, Abstandsschritt, bei starker Angst kurzer Fluchtlauf. |

Aufmerksamkeit 70 oder 100 ist keine automatische Moodlet-Stärke 1 oder 3.
Neugier beginnt nach der Qualifikation auf Stufe 1. Weitere frisch beobachtete,
sichere Bewegung sammelt Spielzeit: Stufe 2 nach 6, Stufe 3 nach 12 gewichteten
Sekunden ab Beginn dieser Spielphase. Vertrauen gewichtet die Rate mit
`0,75 + 0,5 * Vertrauen`; Energie und Stimmung gewichten jeweils zwischen 0,5
und 1. Diese Bereitschaft wird vor dem eigenen Moodlet pro Begegnung festgelegt.
Geringe Freundschaft sperrt höhere Stufen nicht. Langsame/ruhige Bewegung baut
den Fortschritt mit einer Sekunde pro Sekunde ab. Tatsächliches Moodlet-Abklingen
wird aus PetState gelesen und nicht durch einen veralteten Policy-Level umgangen.

Solange sichere interessante Bewegung und bemerkte Aufmerksamkeit bestehen,
erneuert höchstens alle 8 Sekunden ein frischer Beleg die bestehende endliche
Moodlet-Dauer. Doppelte Samples, Renderaufrufe, Menünutzung, Ruhe, Ferne oder
das Moodlet selbst liefern keinen neuen Beleg. Eskalation liefert sofort einen
neuen Beleg. Identität und absolute Stärke bleiben beim vorhandenen PetState-
Endpunkt; nach ausbleibendem Reiz laufen die bekannten unteren Stufen ab.
Neugier und Angst schließen sich aus. Ein neu qualifiziertes Gefühl ersetzt das
vorherige vollständig. Innerhalb desselben Gefühls bleiben absolute Stärken und
die bestehenden Budgets maßgeblich. Nach dem begrenzten Rückzug und seiner
Standruhe kann erst neue, eine Sekunde lang qualifizierte sichere Bewegung
wieder Neugier auslösen. Ein Seitenwechsel allein ist kein neuer Gefühlsbeleg.
Jede neue Qualifikation erhält eine eigene Beleg-ID, auch beim Wechsel zurück
zur vorherigen Gefühlsart innerhalb derselben Begegnung.
Kein neuer Angst-/Neugier-Langzeitscore,
keine Freundschaftsgutschrift/-strafe und kein Care-/Wunschfortschritt.

### Fangversuch und Rückzug

Ein Fangversuch folgt dem bewegten Zeiger sichtbar auf der horizontalen
Taskleistenebene. Ein Zeiger über Kopfhöhe kann verfolgt werden; die frühere
Handhöhen-/Reichbarkeitsbedingung ist entfernt. Ein horizontaler Abstand von
0,15 Körperbreiten bleibt erhalten. Direkt über/bei Aiko kann der bestehende
Auftrag innerhalb seiner Frist warten, statt als blockiert ständig neu zu starten.

Ein Versuch hat höchstens 5 Sekunden Wandzeit und 3/5/7 kleine Schrittbreiten
Gesamtweg für Neugier 1/2/3; jede Schrittbreite beträgt 1/12 Spritebreite.
Ein längerer Laufauftrag erhält mindestens eine vorhandene Laufzyklus-Strecke
(68 logische Pixel), damit alle acht Rennframes gezeigt werden können.
Nach Ende folgt eine kurze Pause von 0,35 Sekunden. Ein neuer Versuch braucht
weiterhin passende frische Bewegung; ein Moodlet allein genügt nicht. Kurze
Unterbrechungen dürfen bis zu zwei Sekunden überbrückt werden.

Das Tempo richtet sich nach tatsächlicher horizontaler Reststrecke statt nach
dem Moodlet-Level: ab 0,65 Spritebreiten darf Aiko rennen, unter 0,35 wechselt
sie wieder zum Gehen. Die Hysterese verhindert ständigen Tempowechsel. Die
vorhandenen `running-left`/`running-right` enthalten fest gezeichnete Seitenköpfe.
Deshalb werden sie bei passendem horizontalem Blick (04/12) unverändert und im
Originaltakt verwendet. Für diagonale Kopfachsen bleiben die vorhandenen
Profil-Gehbanken bei echter Gehgeschwindigkeit zuständig. Blickführung hat Vorrang;
keine beschleunigten Gehframes als Ersatz fürs Rennen und keine neue Kopfmontage.

Seitenwechsel korrigieren denselben Fangauftrag. Token, Wandfrist, verbrauchte
Zeit, Gesamtweg und Schrittgrenzen bleiben erhalten. Beim Richtungswechsel wird
nur ein gegenläufiger Subpixelrest gelöscht. Keine neue Position wird außerhalb
des bestehenden WalkControllers/WalkDrivers geschrieben. Profile verwenden die
vorhandenen Kopf-Schritt-Banken; die Wiedergabe folgt dem bestehenden Bewegungstempo
und der deklarierten Schrittweite. Beim Rückzug schaut Aiko weiter zum Zeiger;
die passende vorhandene Geh-/Rennfolge wird für den Rückzug rückwärts abgespielt.
Das ersetzt keine Assets und erzeugt keine neue Zeichnung.

`cursor_play_start`, `cursor_play_more`, `cursor_play_peak` und
`cursor_fear_response` wählen kurze deutsche Katalogtexte mit Emoji. Nur Beginn,
Gefühlswechsel und tatsächliche Verstärkung liefern Kommentarfeedback;
gleichstarke Auffrischungen bleiben stumm. Alle vier Ereignisse erlauben genau
einen Text-Cue und nutzen den vorhandenen freien, nicht blockierenden Sprechplatz,
ohne Action/ReactionPlayer oder Warteschlange. Belegte Sprechplätze bleiben geschützt.
Eine Spielpause verhindert keine echte Nahannäherungswarnung; vor neuer Angst
bleibt die bestätigte Vorwarnung erforderlich.

Starke Angst erlaubt den vorhandenen kurzen Fluchtlauf: höchstens eine Sekunde
wirkliche Laufbewegung, danach mindestens fünf Sekunden Standruhe. Höchstens
ein Rückzug/Fluchtlauf je zusammenhängender Begegnung; erneute Flucht erst nach
bestätigtem zwischenzeitlichem Verlassen des Nahbereichs. Das Moodlet allein
startet keine Fluchtkette. Neue Stärke darf einen Ausdruck ändern, ohne einen
verbrauchten Bewegungsversuch erneut freizugeben.

## Menü-Erreichbarkeit und Prioritäten

- Native `<Enter>`-Ereignisse und Hover-Polling öffnen das Menü sofort. Bei
  laufender Mausverfolgung ist das Überfahren Aikos keine Bedienübernahme:
  Aufmerksamkeit, ausgewählter Blick, Moodlet und ein weiterhin gültiger
  Fangversuch bleiben erhalten. Eine neue Begrüßungsreaktion unterbricht sie nicht.
- Explizite Klicks haben weiterhin Vorrang und dürfen Cursorabsichten abbrechen.
  Der Zugang zur sichtbaren Toolbar einschließlich ihrer Brücke, Draggen,
  Tastaturbedienung und geöffnete Auswahlmenüs halten die Ortsbewegung an.
  Die bloße Sichtbarkeit der Toolbar beendet keine laufende Mausverfolgung.
- Der vorhandene gemeinsame Bedienbereich mit sechs logischen Pixeln
  Zusatzrand und die Herkunftsprüfung bleiben erhalten. Eigenbewegung unter
  einen ruhenden Zeiger ist kein absichtlicher Benutzerkontakt.
- Die Vorwarnung und die kurzen Gefühls-Kommentare sperren keinen Kontakt.
  Belegte/geschützte Sprechplätze werden nicht überschrieben.
- Während echter Toolbar-/Menübedienung stehen auch erhaltene World-Aufträge
  physisch still. Auftrag, Suchfortschritt und Objektbesitz bleiben bestehen.
  Ein sichtbares unbenutztes Fenster hält Aiko nicht unbegrenzt fest.
- Native Objektgriffe behalten aktuelle Ereigniskoordinaten, ohne die Policy
  erneut auszuwerten oder aus dem Klick eine Blick-/Wissensänderung zu erfinden.
- Aufmerksamkeit, Warn-ID, bestätigtes Warnfenster und Fangziel sind flüchtig.
  Laden erzeugt weder Warnung noch Gefühlsbeleg. Vorhandene Moodlets bleiben
  gespeichert und altern auf `PetState.lived_seconds`.

Ein expliziter Klick verwirft die flüchtigen Cursorabsichten. Reine
Toolbar-/Menübedienung hält dagegen Aufmerksamkeit und Blick aufrecht, beendet
eine Ortsbewegung sicher und setzt keine dauerhafte Zugangssperre. Dabei werden
keine neuen Warn-/Gefühlsbelege qualifiziert; ein altes Warnfenster wird verworfen.
Beim Verlassen der Bedienflächen bleiben Aufmerksamkeit und bereits gesammelte
positive Beobachtungszeit bestehen. Menüzeit lädt weder Gefühle noch Spielzeit
auf; vorhandene Moodlets altern normal weiter. Ein gehaltenes Interesse kann
bei neuer passender Bewegung sofort einen neuen begrenzten Versuch erlauben.
Der während der Bedienung sicher beendete alte Bewegungsauftrag wird nicht mit
zurückgesetztem Budget wiederbelebt. Eine Menüpause erzwingt keine zusätzliche
Fangversuchs-Abkühlung; explizite Klicks behalten ihre harte Übernahme. Geschützte Aktivitäten geben Cursorabsichten weiterhin frei. Ihre
Dauer wird danach nicht als beobachtete Aktivität nachintegriert.

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
historischer Befund und bestätigt den neuen Umbau nicht. Der bereits
belegte lokale Debian-Mastermind-Sonderfehler ist im
[bisherigen Prüfprotokoll](ADAPTIVE_CURSOR_REWORK_PLAN.md) dokumentiert und auf
`2ecca2f` identisch. Nicht pauschal Tests überspringen oder UI-Erwartungen lockern.
Eine Linux-Testumgebung braucht die tatsächlichen `requirements.txt`, insbesondere
Astronomy Engine; ein modaler Fehlerdialog ist kein regulär weiterlaufender Test.
Bei langsamen Windows-Bind-Mounts kann eine lokale isolierte Kopie statt einer
Änderung des Repositorys verwendet werden.

Assets, private Originale, parallele UI-Arbeiten und vorhandene Exporte bleiben
außerhalb des Umbaus. Es wird nichts neu generiert. Die Umsetzung wurde
ausdrücklich in neun Commits
mit gezielten Tests je Schritt und abschließender Gesamtsuite sowie vollständiger
CI beauftragt. Der endgültige CI-Lauf und sein exakter Head werden im
Umsetzungsbericht verknüpft; ein früherer grüner Lauf ersetzt diese Prüfung nicht.

## Umgesetzte Modulgrenzen

- `CursorAttention` filtert ausschließlich Messwerte. `CursorBehaviourPolicy`
  integriert neue gültige Samplezeit in 0–100 und hält Stufen/Seitenbeobachtung.
  Gleiche oder rückwärts eintreffende Samples verändern die Aufmerksamkeit nicht.
- Geschützte Aktivität gibt Blick-/Bewegungs-/Warnabsichten und Seitenverlauf
  frei, pausiert aber die bisherige Aufmerksamkeit. Beim Freigeben beginnt eine
  neue Samplebasis; die unterbrochene Zeit wird nicht integriert. Nur explizite
  Klickübernahme setzt Aufmerksamkeit und Absichten zurück. Hover öffnet sofort;
  echte Menübedienung hält Blick/Aufmerksamkeit ohne neue Gefühle aufrecht und
  stoppt die Ortsbewegung. Cursor aus, Schlaf,
  Spiel und Größenwechsel invalidieren zusätzlich beim Übergang die Sensorhistorie.
  Anschließend bleibt die native Herkunftsprüfung für Kontakt aktiv, auch bei
  ausgeschaltetem Cursorverhalten.
- Der Warnkatalog erlaubt genau einen Textcue. `SpeechPresenter` quittiert einen
  tatsächlich freien, nicht blockierenden Sprechplatz; `PointerRuntime` gibt
  diese Quittung zurück, ohne die Policy erneut auszuwerten. Die bestätigte
  Anzeigezeit eröffnet das Drei-Sekunden-Fenster. Erst ein neuer Nah-Anflug nach
  einer zwischenzeitlichen Entschärfung qualifiziert Angst. Doppelte Samples
  oder fortdauernd derselbe Anflug reichen nicht.
- Die World-Wahrnehmung liest dieselbe tatsächliche Kopf-/Körperkompatibilität
  wie die Darstellung. Es gibt keinen zweiten Posebesitzer. Bei Gegenseite
  erreicht Aiko erst wieder frontal die volle Kopffreiheit.
- `WalkController` besitzt weiterhin alle tatsächlichen Bewegungsfortschritte.
  Fangziele werden innerhalb desselben aktiven Tokens aktualisiert; Gesamtweg,
  Schrittgrenzen, Restbudget, Restpixel und Ablaufzeit bleiben erhalten.
  Freigegebene oder abgeschlossene Tokens werden nicht wiederbelebt.
- Moodlet-Familien, absolute Stärken, Speicherung, Care-/Wunsch- und
  Freundschaftsgrenzen bleiben erhalten. Ein stiller Zeiger oder ein bereits
  aktives Moodlet startet keine neue Neugier und keinen neuen Fangversuch.

Die bisherigen harten Verhaltenserwartungen wurden mit realen Zeitreihen
migriert: sichere kreisende Mausbewegung baut Interesse auf, danach kann ein
bewegtes bodennahes Ziel einen begrenzten Fangversuch auslösen. World-Fixtures
bauen das Bemerken durch echte Sensor-/Policy-Samples auf; native Klicks
ersetzen weiterhin keine ausgewählte Aufmerksamkeit oder Objektkenntnis.


## Prüfstand des Abschlusscommits

Die acht vorausgehenden fachlichen Commits enthalten jeweils ihre gezielten
Prüfungen. Die Abschlussschritte prüfen zusätzlich die durchgehende Übergabe
Sensor -> Policy -> Coordinator -> Anzeigequittung -> Gefühl -> Bewegung und
aktualisieren das vorhandene Windows-CI-Testmuster um `test_cursor_warning.py`.

- Ruff über `aiko_pet tests main.py tools`: grün.
- Mypy strict ohne inkrementellen Cache: 361 Quelldateien grün.
- Pyright einschließlich Tests: keine Fehler oder Warnungen.
- Vollständiger lokaler Windows-/Tk-Lauf: 2336 Tests grün. Der danach ergänzte
  Übergangsfall „Cursor aus, Herkunftsprüfung bleibt aktiv“ ist zusammen mit den
  zugehörigen Kontakt-/Preferences-/Coordinator-Tests grün (27 gezielte Tests).
  Ein weiterer kompletter Lauf prüft diesen abschließenden Stand ebenfalls.
- Bestehende Kontakttexte sind inhaltlich unverändert; ergänzt ist ausschließlich
  die neue Warnzeile. Keine Bild-/Exportdateien geändert. Die parallelen
  UI-Dokumente wurden gegen ihren eigenständigen Commit unverändert geprüft.
- Die vollständige bestehende CI auf PR #11 wird am finalen Head geprüft:
  Linux Python 3.11 und 3.13 einschließlich aller statischen Gates/Gesamtsuite,
  außerdem Windows setup and desktop boundaries. Exakter Head, Lauf und
  Abschlussstatus gehören in den Umsetzungsbericht, nicht zu einem älteren Lauf.

Ein zwischenzeitlicher fremder UI-Konzeptcommit bleibt unverändert zwischen den
gezielten Commits erhalten. Die neun Cursor-Commits verändern ihn nicht.
Kein Merge und keine praktische Verhaltensabnahme durch technische Tests.

## Nachkorrektur der Hover-Kopplung, 27.10.2026

Der vorherige Abschlussstand setzte beim nativen Enter und beim Hover-Polling
`claim_access` und wertete eine ungepinnte sichtbare Toolbar pauschal als
Bedienübernahme. Dadurch fiel Aufmerksamkeit von 100 auf 0; die Policy-Sperre
gegen Körperzuwendung und Fangversuche blieb bis zum Begegnungsende bestehen,
obwohl das Neugier-Moodlet noch aktiv war. Die bisherigen Zugangstests sicherten
diese zu grobe Unterbrechung ab.

Die Korrektur bleibt in den vorhandenen Besitzern: `DesktopInput` meldet Hover
ohne Klickübernahme, `HoverUi` öffnet sofort und unterscheidet während laufender
Verfolgung sichtbare Oberfläche von tatsächlichem Zugang zu den Bedienelementen.
`ContactCoordinator` löst beim Überfahren keine Wegunterbrechung/Begrüßung aus.
`PointerRuntime` hält den nativen Klickpfad getrennt; Menüpausen gehören der
bestehenden `CursorBehaviourPolicy`. `WalkController` bleibt der einzige Besitzer
der tatsächlichen Bewegung. Ruhender Zeiger unter Aikos Eigenbewegung bleibt
von absichtlichem Hover unterschieden; Idle-/World-Bedienpausen bleiben erhalten.

Gezielte Regressionen prüfen Aufmerksamkeit 100 mit aktivem Moodlet, gültigen
Fangauftrag, native und gepollte Eintritte, tatsächliche Toolbar-Nutzung mit
erhaltenem World-Auftrag, Freigabe bei weiterhin sichtbarer Toolbar sowie alte
Warnfenster. Zwei Tk-Tests verbinden die echten Assemblies; der Überflug wird
bei 1X und 2X geprüft. Assets und parallele UI-Arbeiten bleiben unverändert.

## Vorherige Nachkorrektur: ausschließliche Gefühle und reaktive Drehung, 27.10.2026

Die vorherige Fassung konnte beide Cursor-Moodlets speichern und verzögerte
auch emotionales Folgen mit der normalen Seitenbeobachtung. Eine kontrollierte
Folge brauchte nach dem Seitenwechsel 3,8 Sekunden bis zur anderen
Dreiviertelpose. Diese historische Nachkorrektur wurde durch die oben
beschriebene Blickpriorität und fortlaufende Spielphase weiterentwickelt.
Ihr damaliger Stand unterschied:

- Normales Beobachten: unveränderte Aufmerksamkeits-/Seitenhysterese und 140 ms
  je Drehphase. Ein Moodlet allein erzeugt keine neue Ortsbewegung.
- Aktive Neugier/Angst: aktuelle Seite sofort als Körperabsicht; alle vorhandenen
  Drehphasen mit 70 ms. Die Tk-Prüfung zeigt bei 1X und 2X die vollständige Folge
  Dreiviertel rechts -> frontal -> Dreiviertel links in 560 ms, einschließlich
  der sichtbaren Frontphase. Eine fertige Front-/Seitenpose plant keine weitere
  Drehauffrischung. Der Haupttakt und die einzige Verhaltensauswertung bleiben
  unverändert.
- Laufender Fang-/Rückzugsversuch: Ein Seitenwechsel hinter den Körper beendet
  den Versuch sicher. Danach folgt die Körperausrichtung der neuen Seite.
  Kein neues Token, kein zurückgesetztes Schritt-/Fluchtbudget; die vorhandene
  Stand-/Versuchspause bleibt erhalten. Eine spätere echte Gefühlsqualifikation
  kann das andere Moodlet ablösen, ohne eine verbrauchte Flucht freizugeben.
- Speicherung: `cursor_experiences.py` löst den exklusiven Wechsel auf. Die
  vorhandenen Codecs normalisieren gültige alte Doppelzustände nach dem letzten
  Auslösezeitpunkt, bei Gleichstand zugunsten von Angst. Identität, Stärke,
  Restzeit, untere Stufen, Ursachen und nächste Instanz-ID werden nicht erneuert.
  Auch SQLite-Snapshots durchlaufen denselben Vertrag; andere Moodlets und
  Pflege-/Wunsch-/Freundschaftsdaten bleiben erhalten. Kein neues Speicherformat.

Gezielte Tests prüfen beide Wechselrichtungen, erneute sichere Qualifikation
nach Angst, einmalige frische Belege innerhalb derselben Begegnung, JSON- und
SQLite-Altdaten, Moodlet-Ablauf, normale Seitenhysterese, schnellen Seitenwechsel
ohne Bewegung und den tatsächlichen Tk-Animationstimer bei beiden Größen.
Die zuvor implementierte Hover-Korrektur wird weiterhin mitgeprüft. Es wurden
keine Assets generiert oder verändert und keine parallelen UI-Arbeiten übernommen.

Prüfstand dieser Nachkorrektur: 250 gezielte Tests einschließlich Hover-,
World-, Pflege-/Moodlet-, Speicher- und Architekturgrenzen sind grün. Weitere
25 gezielte Bewegungs-/Animationstests prüfen insbesondere das unveränderte
Fluchtbudget mit dem schnelleren tatsächlichen Tk-Frameablauf. Ruff, Mypy strict
und Pyright sind grün. Praktische Sichtabnahme erfolgt nach Neustart der Anwendung;
die Daten des laufenden Nutzerprozesses wurden durch die Tests nicht verändert.


## Prüfstand: Blickführung und fortlaufendes Spiel, 27.10.2026

336 gezielte Tests decken Sensor/Policy/Koordinator, Moodlet-Anwendung und
Speicherung, Bewegung, tatsächlichen Tk-Animationstimer, native/gepollte Hover-
Zugänge, freie Kommentare, Dialog- und Balancekataloge sowie Architekturgrenzen ab.
Längere Trajektorien bei 1X und 2X prüfen Folgen auf beide Seiten, Steigerung bis
Stufe 3 auch bei geringer Freundschaft, Auffrischung ohne Kommentarspam und Ablauf
nach ruhendem Zeiger. Der Tk-Test prüft Kopfkorrektur im selben Renderaufruf,
Fortsetzung desselben Fang-Tokens und unverbrauchtes Restbudget. Flucht behält
höchstens eine Sekunde tatsächlicher Bewegung und blickt dabei zum Zeiger.
Ruff, Mypy strict und Pyright sind grün. Dies ist keine vollständige CI-Ausführung.
Die praktische Sichtabnahme nach Neustart der Anwendung bleibt offen; Tests
verändern weder den laufenden Nutzerprozess noch seinen Spielstand. Keine Assets,
Exporte oder parallelen UI-Entwürfe wurden verändert. Push und Merge sind für diese Nachkorrektur nicht freigegeben.


## Nachkorrektur: situative Reaktionen, Menüfortsetzung und echte Rennfolge

Der Auftrag vom 27.10.2026 ersetzt die vorige pauschal negative Vorwarnung,
70-plus-zwei-Sekunden-Qualifikation und Moodlet-Level-Tempowahl durch die oben
beschriebenen aktuellen Regeln. Zuständigkeiten bleiben in Policy, Koordinator,
WalkDriver/WalkController und bestehendem Animationstimer. Kein neues Bild,
keine Exportänderung und keine neue Bewegungs- oder Gefühlsinstanz.

Gezielte Ablaufprüfungen decken positive/negative Bewertungen einschließlich
Zustandswechsel, nicht als Angstbeleg nutzbare positive Anzeigequittungen,
früheren Einstieg ohne Sofort-Moodlet, Menüzeit ohne Aufladung, erhaltene
Moodlet-Identität mit normalem Zeitablauf, unmittelbare Wiederaufnahme und
unveränderte Bedien-/World-/Klickprioritäten ab. Tempo-/Zielkorrekturen erhalten
Token, Frist sowie verbrauchte Zeit-/Wegbudgets. Der echte Tk-Timer zeigt bei 1X
und 2X sämtliche acht Original-Rennframes mit tatsächlichem Ortswechsel;
diagonales Kopffolgen bleibt Gehen. Die praktische Sichtabnahme steht aus.


Prüfstand dieser Nachkorrektur: Die vollständige lokale Suite besteht mit
2.374 Tests. Zusätzliche Tk-Prüfungen zeigen sämtliche Original-Rennframes
links und rechts bei beiden Größen. Ruff, Mypy strict (361 Quelldateien) und
Pyright sind grün. Der Quittungstest verwendet jetzt ausdrücklich eine defensive
Stimmung; seine Prüfung unveränderter Policy-/Pet-Zeit bleibt bestehen. Ein
Menüeintritt unmittelbar nach dem ersten Moodlet und dessen späterer Ablauf
sind separat gegen eine Wiederbelebung aus alten Beobachtungsmarken geprüft.
Assets und parallele UI-Arbeiten bleiben unverändert. Kein Push, keine neue
Remote-CI und keine Mergefreigabe für diese Nachkorrektur.
Die laufende Nutzerinstanz und ihr Spielstand wurden nicht verändert.
