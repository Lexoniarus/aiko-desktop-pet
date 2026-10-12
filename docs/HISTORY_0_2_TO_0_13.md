# Aiko Desktop Pet v0.13 – Kenney Sci-fi UI und echte Emote-Folgen

**Neu:** Beim Hover erscheint eine neu gestaltete, Kenney-Sci-fi-inspirierte
Statusleiste mit allen sechs Tamagotchi-Werten und den bisherigen Aktionen.
Der blaue Panelkopf und die hellen Schaltflächen greifen das echte `Sample.png`
aus deiner Dropbox auf; die Leiste bleibt frei verschiebbar und ausblendbar.

**Reaktionen:** Echte Kenney-Pixel-Emotes erscheinen **nacheinander** mit Aikos
Texten, z. B. `? → „...Oh. Du schon wieder.“ → ♥`. Bei Reaktionen mit Nachsatz
folgen die Texte ebenfalls nacheinander. Die Emotes hängen von der Bedeutung
der Situation ab, nicht von einem zufälligen Effekt. Schnell wiederholte Klicks
unterbrechen alte Sequenzen sauber und überspringen nötigenfalls das
Einleitungs-Emote, damit die Antwort sichtbar bleibt.

**Schrift:** Falls `Kenney Mini` bereits auf deinem Windows-System installiert
ist, verwendet Aiko sie. Sonst läuft sie mit Segoe UI. Fontdateien sind nicht
im ZIP enthalten; verwende zum Installieren deine eigene Kopie.

**Erhalten:** Der gesamte v0.12-Tamagotchi-Kern, das Lernen des Tagesrhythmus,
alle 73 Originalsprites, der Spielstand, die Rechnerbeobachtung und die
Fensterverwaltung. Keine neue Laufzeitabhängigkeit, keine Cloud, keine KI.

**Installation:** Vorige Version beenden, dieses ZIP in einen neuen Ordner
entpacken, `Aiko_starten.bat` starten (Windows 10/11, Python 3.11+ mit Tk).

**Vorschau:** `vorschau/Aiko_v0_13_Reaktionsablauf.gif` zeigt die echten
aufeinanderfolgenden Stadien. Einzelbilder und das Sample sind beigelegt.

Details zu Assetquellen, Emote-Semantik und Grenzen:
`docs/KENNEY_UI_UND_EMOTES_V013.md`.

---

# Aiko Desktop Pet v0.12 – Zuwendung und Freundschaft

**Neu:** Sechs Anzeigen in Hover-Leiste und Statusfenster:
**Sättigung · Laune · Energie · Sozial · Zuwendung · Freundschaft** (Level 1–10).
Zuwendung ist ein eigenes kurzfristiges Bedürfnis, das Streicheln mit
+25 Punkten erfüllt. Streicheln gibt zusätzlich +6 Laune und +2 Sozial,
**keine** Energie. Spielen und Reden erfüllen weiterhin getrennte Bedürfnisse.

- **Freundschaft** wächst nur durch sinnvolle Pflege, wenn das primäre Bedürfnis
  vor der Aktion ≤80 % beträgt; abwechslungsreiche Pflege gibt einen kleinen
  Bonus. Maximal +5 Punkte/Tag, eine Belohnung pro Aktion/12 Minuten.
  Energy Drinks und Schlafen sind nicht mehr zum Freundschaftsfarmen nutzbar.
- **Rechnerlast:** Sättigung, Laune und Energie bleiben von tatsächlicher Arbeit
  abhängig; Zuwendung sinkt sanft und unabhängig von CPU/GPU-Last.
- **Persönlichkeit:** Sozialmangel und Zuwendungsmangel werden unterschieden;
  es gibt eigene zurückhaltend-awkward Kommentare zu Nähe, Distanz und
  Streicheln. Bereits vorhandene Animationen und Fensterverwaltung bleiben.
- **Migration:** v0.11-Saves werden automatisch ergänzt (Zuwendung = 75),
  Freundschaft und alle bisherigen Bedürfnis-/Einstellungswerte bleiben erhalten.

**Installieren:** Vorige Aiko beenden, ZIP in einen neuen Ordner entpacken,
`Aiko_starten.bat` starten (Windows 10/11, Python 3.11+ mit Tkinter).
Keine externen Laufzeitpakete, keine Cloud, keine KI-API. Das Spiel speichert
weiter unter `%LOCALAPPDATA%\AikoDesktopPet\state.json`.

**Tests:** 220 automatisierte Tests unter Linux/Xvfb bestanden; realer
Windows-Langzeittest noch offen. Technische Erläuterung:
`docs/TAMAGOTCHI_KERN_V012.md`, Testbericht: `docs/TESTBERICHT_V012.md`.

**Vorschau:** `vorschau/Aiko_v0_12_Zuwendung.png` (Originalsprites,
beispielhafte Werte).

---

# Aiko Desktop Pet v0.11 – Tamagotchi-Kern und Freundschaft

**Aiko ist dein personifizierter Rechner in Chibi-Form.** v0.11 ergänzt
zur vorhandenen v0.10-Persönlichkeit die neuen Bedürfnisse und eine
langsam wachsende Beziehung, ohne Taskleisten-Fensterverwaltung,
Originalsprites oder den adaptiven Tagesrhythmus auszutauschen.

## Neu: fünf Anzeigen, sechs Aktionen

In der Maus-Hover-Leiste und im Statusfenster stehen jetzt:
**Sättigung · Laune · Energie · Sozial · Freundschaft (Level 1–10)**.
Freundschaft ist langfristig; die anderen vier Werte sind kurzlebige Bedürfnisse.

- **Reden** (+26 Sozial, +5 Laune, -1 Energie) ist eine eigenständige
  Interaktion. Auch Spielen und Streicheln fördern soziale Nähe.
- **Energy Drink +10** steigert die Energie pro Klick um **10 Prozentpunkte**,
  direkt beliebig oft wiederholbar bis maximal 100. Schlafen bleibt möglich.
- Freundschaft steigt durch Versorgung langsam an. Mehrfaches Auslösen der
  gleichen Aktion in Sekunden erhöht sie nicht immer weiter: maximal einmal
  je Aktion/12 Minuten und höchstens 7 Punkte am Tag.
- Aikos Äußerungen und ihr Verhalten berücksichtigen den sozialen Bedarf und
  die bereits erreichte Vertrautheit, ohne den Grundcharakter zu verändern.
- Bei nachgewiesener hoher CPU-/GPU-Arbeit sinken Sättigung und Laune schneller;
  auch Energie wird stärker beansprucht. RAM allein ist kein Maß für Arbeit.
  **Unbekannte Zeiten werden nicht als Hochlast angerechnet.**
- 49 neue Dialogzeilen in 14 zusätzlichen Kategorien; nur vorhandene
  Originalanimationen werden verwendet. Das HUD bleibt verschiebbar.

**Installieren:** Die alte Aiko vollständig beenden, ZIP in einen neuen
Ordner entpacken und `Aiko_starten.bat` ausführen. Benötigt Windows 10/11,
Python 3.11+ mit Tkinter, keine externen Laufzeitpakete.
Dein bisheriger Spielstand unter
`%LOCALAPPDATA%\AikoDesktopPet\state.json` wird weiterverwendet.

**Tests:** 195 Unit- und GUI-Tests mit einer virtuellen Linux-Anzeige bestanden.
Ein echter Windows-Langzeittest (insbesondere Taskleiste, NVIDIA-Messung,
Fokus und Balance über mehrere Tage) steht noch aus.

Details zu Formeln, Grenzen, Beziehungslogik und Datenspeicherung:
`docs/TAMAGOTCHI_KERN_V011.md`. Testbericht: `docs/TESTBERICHT_V011.md`.

---

# Aiko Desktop Pet v0.10 – ihre Persönlichkeit wird erlebbar

Ein kleines **lokales** Windows-Desktop-Pet mit 73 Originalsprites.
Aiko ist der personifizierte Rechner: ruhig, aufmerksam, gelegentlich
unfreiwillig komisch, manchmal trocken-frech – abhängig von ihrer Stimmung.
Sie hat eigene Bedürfnisse, einen adaptiven Tagesrhythmus und lebt an der
Taskleiste. **Kein Academy-Alltag, keine KI, keine Cloud.**

## Neu in v0.10: Zusammenhängende Reaktionen

- **Klickfolgen statt Wiederholungsroulette:** Aiko merkt innerhalb kurzer
  Zeit, wenn du sie mehrfach anklickst. Aus Aufmerksamkeit wird je nach
  Verfassung Necken, genervtes Abgrenzen oder bei Übertreibung bewusstes
  Schweigen. Nach einer Pause normalisiert sich das Verhalten.
- **Ein und dasselbe Ereignis, verschiedene Bedeutungen:** Gute Laune,
  Müdigkeit, Pflege, Uhrzeit, Arbeitsbelastung und die vorigen Interaktionen
  beeinflussen, was sie sagt. Besonders beim konzentrierten Arbeiten
  reagiert sie anders als bei Freizeit.
- **Kleine soziale Erinnerung:** Wird sie während einer nachgewiesenen
  intensiven Berechnung mehrfach unterbrochen, kann sie das nach dem
  Arbeitsende aufgreifen. Ein langer Arbeitstag erhält nur dann einen
  passenden Abschluss, wenn die Dauer tatsächlich beobachtet wurde.
- **Subtiler „awkward-funny“-Humor:** Einige Dialoge kommen in zwei kurzen
  aufeinanderfolgenden Sprechblasen. Sie redet sich gelegentlich um Kopf
  und Kragen, korrigiert sich oder lässt einfach eine Pause stehen.
- **Redaktionelle Überarbeitung:** 40 schwächere alte Einträge entfernt,
  zentrale Standardformulierungen neu geschrieben und situative Varianten
  ergänzt. Aktuell 339 Sprechblasen-Auslöser, teilweise mit Nachsatz.
  Es gibt bewusst auch ganz schlichte, ruhige Aussagen.
- **Keine erfundenen Rechnererlebnisse:** Laufzeit ist nicht Wachzeit.
  Aussagen über Belastung, ungewöhnliche Arbeitszeiten oder Unterbrechungen
  benötigen reale Beobachtungen. Rohdaten über Apps oder Eingaben werden
  nicht gesammelt.

**Bestand erhalten:** v0.9-Tagesrhythmus und lokales Wochenprofil,
Pflegewerte, Taskleistenlauf, Mausverfolgung, verschiebbare Hover-/Statusleiste,
Fenster-Z-Order und Spielstand bleiben kompatibel. Beim Windows-Test
muss sich besonders die Interaktion während einer Browser-Spracheingabe
bewähren; sie wurde hier nur in einer virtuellen Linux-Oberfläche getestet.

Dokumentation mit konkreten Szenarien: `docs/REAKTIONEN_V010.md`.
Der Prüfumfang steht unter `docs/TESTBERICHT_V010.md`.

**Automatischer Prüfstand:** Alle 167 vorhandenen und neuen Tests unter
Linux/Xvfb bestanden, inklusive Reaktionseskalation, Langzeitarbeit, Rückbezug,
Nachsatz-Timing, Stummschaltung und früherem Speicherschema. Die persönliche
Wirkung der Dialoge muss im Alltag geprüft werden.

## Installation unter Windows

1. Die bisherige Aiko komplett beenden.
2. Dieses ZIP in einen **neuen Ordner** entpacken.
3. `Aiko_starten.bat` starten (Python 3.11+ notwendig, keine weiteren
   Pakete für die Laufzeit).
4. Der bisherige Spielstand in `%LOCALAPPDATA%\AikoDesktopPet\state.json`
   wird weiterverwendet.

Für eine Konsolenansicht bei Problemen gibt es `Aiko_starten_debug.bat`.

---

## Historischer Stand: v0.9 (übernommen)

Ein kleines **lokales** Desktop-Tamagotchi für Windows 10/11 mit Aikos
73 originalen Chibi-Sprites. Aiko lebt am Taskleistenrand, schaut dem
Mauszeiger hinterher, hat Bedürfnisse und spricht in kurzen deutschen
Sprechblasen. Die Geschichtenwelt und der Academy-Alltag spielen hier
**keine Rolle**. Kein Konto, keine Cloud, keine KI-API.

## Neu in Version 0.9: Aiko entwickelt einen eigenen Alltag

**Auf v0.8 aufgebaut, ohne Fenster- oder Sprite-Umbau.** Aiko lernt langsam,
zu welchen Tages- und Wochenzeiten **ihr Rechner** gewöhnlich gefordert wird
und wann Ruhe herrscht. Die eigene Tageszeit bleibt wichtig; eine lange
Windows-Laufzeit ist kein Beleg für ununterbrochene Arbeit.

- **Aktuelle Beschäftigung:** Arbeiten, nach einer Arbeitsphase erholen,
  ruhen, aufmerksam sein oder herumstreifen. Anhaltende Last erzeugt eine
  langsam veränderliche Beanspruchung; vorübergehende Spitzen wirken schwächer.
- **Anpassbarer Schlaf:** Aiko bleibt bei realer hoher Rechnerarbeit auch
  nachts wach und schläft bei Entlastung. Ein seltener kurzer Mittagsschlaf
  bei niedriger Energie ist möglich. Manuelle Schlafentscheidungen bleiben
  gültig. Die Pflegewerte werden nicht direkt aus CPU-Prozenten berechnet.
- **Lernendes Wochenprofil:** verdichtete Statistik nach Stunde und Wochentag,
  allmähliche Anpassung über mehrere Wochen. Keine schnellen Umstellungen
  nach einer ungewöhnlichen Nacht.
- **Kontrolle:** Lernen in den Einstellungen abschaltbar; neues **„Gelerntes
  Tagesmuster löschen“**. Die Live-Reaktion funktioniert ohne Lernen weiter.
- **Statusfenster:** zeigt Aikos aktuelle Beschäftigung, Beanspruchung und
  separat die gemeldete Windows-Laufzeit. Das Hover-Fenster und seine
  drei Bedürfnisbalken bleiben unverändert.

**Noch nicht geändert:** Der Dialogkatalog mit seinen 236 Aussagen,
Click-Eskalation und Sprite-Animationen. Die neue Gedächtnisschicht ist das
Fundament für einen gesonderten, anspruchsvolleren Dialog- und
Reaktions-Slice. Sie behauptet noch nicht, dass Aiko komplett neue Gespräche
führen kann.

### Verhalten bei dauerhaft eingeschaltetem PC

Der Rechner kann viele Tage laufen, ohne dass Aiko automatisch tagelang wach
ist. Nachts im Leerlauf kann sie schlafen, aber sie unterbricht keine aktuelle
starke Berechnung nur wegen einer Uhrzeit. Die lokale Nutzungsstatistik merkt
sich langsam wiederkehrende Aktivitätsfenster. Sie zählt keinen Windows-
Ruhemodus und keine mehrstündige App-Pause als beobachtete Arbeitsstunden.

**Teststand v0.9:** 147 Unit- und Tk-GUI-Tests unter Linux/Xvfb erfolgreich,
inklusive 72-Stunden-Simulation, mehrwöchigem Lernprofil, alter Speicherstände,
Ruhephasen, Tagesaktivität und Live-Oberflächeneinstellungen. Die konkrete
Windows-Langzeitnutzung und `GetLastInputInfo` sind auf diesem Rechner nicht
real ausführbar und müssen unter Windows geprüft werden.

Vertiefung und fachliche Grenzen: `docs/ADAPTIVER_RHYTHMUS.md`.

---

## Bestehende Version 0.8: gemeinsame Fenstersteuerung

Die Fensterreihenfolge hält Aiko mit ihrer Sprechblase sichtbar.

**Fehlerbehebung der Fensterreihenfolge (Z-Order) unter Windows:**

- Aiko, Status-/Aktionsleiste, Sprechblase und Einstellungen besitzen nun
  eine gemeinsame, zentral verwaltete Vordergrund-Reihenfolge.
- Eine neue Sprechblase wird nicht mehr **allein** per `lift()` nach vorne
  gezogen, besonders nicht bei jeder Bewegung von Aiko.
- Unter Windows prüft die App circa alle 1,5 Sekunden, ob ein fremdes,
  sichtbares Fenster über Aiko liegt, während „Immer im Vordergrund“ aktiv
  ist. Nur bei tatsächlich erkannter Überdeckung korrigiert sie die
  Fensterreihenfolge; zusätzliche Reparaturen sind auf mindestens drei
  Sekunden Abstand begrenzt.
- Für die Korrektur wird die Windows-Funktion `SetWindowPos` mit
  `SWP_NOACTIVATE` verwendet. Dadurch wird der Browser nicht absichtlich
  deaktiviert, und Aiko fordert keinen Tastaturfokus an. Der echte
  Mikrofon-Fokuswechsel ist bislang nicht auf Windows verifiziert.
- Ist „Immer im Vordergrund“ deaktiviert, findet **keine** automatische
  Wiederherstellung der Vordergrundreihenfolge statt.
- Die Leiste bleibt verschiebbar und ausblendbar; Statusanzeigen,
  Tagesrhythmus, Dialoge, Bedürfnisse und Originalsprites sind unverändert.

**Windows-Praxistest:**

1. Aiko starten; `⋯` → **Immer im Vordergrund** aktivieren.
2. Bei eingeblendeter Sprechblase im Browser die Mikrofon-/Diktierfunktion
   verwenden; dabei beobachten, ob Aiko hinter den Browser rutscht.
3. Den Browser währenddessen weiter bedienen: Die Korrektur soll ihm weder
   Tastatur- noch Mikrofonfokus wegnehmen.
4. Die Leiste verschieben, ein-/ausblenden, Status und Einstellungen öffnen.
   Alle UI-Teile sollten sichtbar und bedienbar bleiben.

**Prüfstand:** 120 Unit- und Tk-GUI-Tests auf Linux/Xvfb bestanden;
Win32-Z-Order und nichtaktivierendes Anheben mit API-Simulationen getestet.
Noch **nicht** auf einem echten Windows-System getestet. Insbesondere
browser- oder systemeigene Always-on-top-Overlays können besondere Regeln
haben, die ein echter Praxistest aufdecken muss.

## Änderungen aus Version 0.7

**Arbeit statt Messwert-Kommentar:** Aiko verkörpert den Rechner. Sie
bekommt mit, wenn sie zunehmend gefordert wird, sich längere Zeit stark
konzentrieren muss und danach wieder Luft hat. Sie nennt in ihren
Sprechblasen **keine CPU, GPU, RAM oder technischen Kennzahlen**. Sie
formuliert kurze eigene Eindrücke im Ton ihres Character Sheets.

- 236 handgeschriebene Dialogzeilen in 37 Ereigniskategorien. Darunter
  69 neu verfasste Sätze über ihr Arbeitsgefühl und 28 sprachlich
  überarbeitete ältere Kommentare.
- Ein kurzes Belastungshoch erzeugt **keinen** Erschöpfungskommentar.
  Erst nach ungefähr 18 Sekunden anhaltender hoher Last kann sie
  reagieren wie „Uff. ...Das hatte es wirklich in sich.“.
- Technisch werden CPU und GPU als Hauptsignal berücksichtigt.
  Hohe RAM-/VRAM-Belegung trägt vorsichtig als Zusatzbelastung bei;
  belegter Arbeitsspeicher allein ist **nicht** gleich aktive Arbeit.
- Die Rechnerwerte können in der Status-/Aktionsleiste weiterhin direkt
  als Prozentzahlen abgelesen werden. Ihre eigene Statuszeile lautet
  dagegen z. B. „Ich habe ordentlich zu tun.“.

**Sprechblasen folgen Aiko:** Der Text erscheint über ihrem Kopf,
**nicht** über der Aktionsleiste. Aiko kann weiter auf der Taskleiste
herumlaufen; die Blase bewegt sich mit. Beim kurzen Spruch steht Aiko
ruhig. Ist oberhalb kein Platz, wird die Blase seitlich an ihren Kopf
gelegt.

**Status-/Aktionsleiste ist verschiebbar:**

1. Mit der Maus über Aiko fahren: Die Leiste erscheint automatisch.
2. Die obere Zeile mit Wochentag/Uhrzeit bei gedrückter **linker Maustaste**
   ziehen und an der gewünschten Stelle loslassen.
3. Die Position wird gespeichert. Ein Klick außerhalb schließt die Leiste;
   beim nächsten Hover über Aiko erscheint sie wieder am gewählten Ort.
4. Über **`⋯` → „Leiste wieder neben Aiko“** wird die Position zurückgesetzt.

Die Leiste erscheint standardmäßig **rechts oder links neben Aiko**, statt
ihre Sprechblase zu verdecken. Beim Verlassen verschwindet sie nach einer
kurzen Verzögerung (an einer frei gewählten Position nach ca. zwei
Sekunden, damit du sie mit der Maus erreichen kannst). Ein Klick außerhalb
schließt sie sofort. Sättigung, Laune und Energie bleiben im Hover sichtbar.

Das separat über **Status** geöffnete Detailfenster funktioniert weiterhin
wie ein normales Windows-Fenster und bleibt bis zum Schließen offen.

## Installation und Start

1. Vorherige Aiko-Version schließen.
2. ZIP in einen **neuen Ordner** entpacken (nicht direkt im ZIP starten).
3. Windows 10 oder 11 und Python **3.11 oder neuer mit Tkinter** verwenden.
4. **`Aiko_starten.bat`** doppelklicken. Bei Problemen
   `Aiko_starten_debug.bat` starten.

Für den normalen Start sind keine externen Python-Pakete nötig; eine
fertige `.exe` liegt nicht bei. Spielstände aus v0.1–v0.8 bleiben erhalten:

`%LOCALAPPDATA%\AikoDesktopPet\state.json`

Die optionale Panelposition und der neue aggregierte `adaptive`-Abschnitt
liegen im bisherigen Format (`version: 1`). CPU/GPU/RAM-Rohwerte werden
nicht gespeichert.

## Computerbeobachtung und Privatsphäre

- CPU und RAM: Windows-System-APIs; GPU: optional NVIDIA `nvidia-smi`.
- GPU ohne verfügbare NVIDIA-Abfrage wird als **„–“** angezeigt, nicht
  als ausgedachte Null. Andere GPUs sind noch nicht angebunden.
- Hintergrundmessung ungefähr alle **sechs Sekunden**, CPU/GPU über zwei
  Samples geglättet. Es werden keine Prozessnamen, Fenstertitel, Dateien
  oder Tastatureingaben ausgelesen, keine Daten versendet.
- In den Einstellungen lässt sich die Rechnerbeobachtung deaktivieren.
  Die Bedürfniswerte werden von der Auslastung nicht beeinflusst.
- Aiko wird bei hoher Belastung ruhiger und nutzt vorhandene `review`-
  Frames; es wurden keine neuen oder erfundenen Animationsassets ergänzt.

## Tests und Einschränkungen

```bat
py -m unittest discover -s tests -v
```

Die Entwicklungsumgebung hat für Version 0.8 **120 Unit- und Tk-GUI-Tests** unter
Linux/Xvfb bestanden. Geprüft wurden u. a. anhaltende und kurze
Belastung, die Dialoge ohne technische Kennzahlen, die Positionierung
der Blase über Aiko, Verschieben und Speichern der Leiste, Auto-Hide,
Einstellungen und bestehende Pflegeaktionen.

**Noch nicht auf einem echten Windows-PC getestet:** Windows-Overlay-
Transparenz, globales Wegklicken, NVIDIA-Lastwerte und Maushandhabung beim
Ziehen der Leiste. Auch die tatsächlichen Reaktionsintervalle hängen
von den Messwerten und der Hardware ab. Die unter `vorschau/` gezeigten
CPU-/GPU-/RAM-Werte sind für den GUI-Test simuliert.

## Optionaler Windows-EXE-Build

```bat
py -m pip install pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name AikoDesktopPet --add-data "aiko_pet\assets;aiko_pet\assets" --add-data "aiko_pet\data;aiko_pet\data" Aiko_Pet.pyw
```
