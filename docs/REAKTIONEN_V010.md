# Aiko v0.10 – Situationen, Reaktionsfolgen und Sprachstil

## Charakter und Scope

Aiko ist die **Personifizierung dieses Rechners**, nicht eine Beobachterin
außerhalb davon. CPU- und GPU-Arbeit fühlt sich für sie wie eigene
Beanspruchung an; die bloße RAM-Belegung gilt nicht als gleich starke Arbeit.

Ihre feste Persönlichkeit: aufmerksam, eher still, kontrolliert, sensibel,
subtil spöttisch. Im Chibi-Desktop-Kontext hat sie auch eine leicht
**awkward-funny** Seite: Sie wird gelegentlich unsicher, korrigiert einen
Satz, witzelt trocken oder ist unfreiwillig komisch. Sie ist jedoch **nicht
ununterbrochen süß, frech oder witzig**. Bei Müdigkeit, Hunger, Gereiztheit
oder hoher Beanspruchung sind andere Ausdrucksweisen glaubwürdig.

Keine Academy, keine fiktiven Softwarevorgänge, kein Zugriff auf offene
Dokumente, Programme, Nachrichten oder Tastaturinhalte, keine Cloud und kein
LLM. Es bleiben die 73 freigegebenen Originalsprites.

## Datenfluss

```
OS-Uhr ────┐
Bedürfnisse ├──> AikoMind ──> Ereignis / Dialog ──> vorhandene Animation
Adaptive ──┤             │                      + erste Sprechblase
Rechnerlast ┤             │                      + optionaler Nachsatz
Mausklicks ┘             └──> kurzes soziales Gedächtnis (nur im Prozess)
```

`AdaptiveRoutine` aus v0.9 bleibt die Quelle für Beschäftigung, beobachtete
Belastungsdauer, Ruhe und erlernten Wochenrhythmus. `ComputerVoice` aus v0.8
bleibt die Quelle für belastbare Arbeitsphasen und Änderungen. `AikoMind`
interpretiert die Bedeutung dieser Ereignisse für Aiko.

Die v0.9-Fensterverwaltung, Geometrie, Statusanzeige, Speicherung und
Taskleistenbewegung werden **nicht umgebaut**. Zwei kurze Sätze werden nicht
zugleich angezeigt; ein Nachsatz folgt nach 0,6–2,6 Sekunden. Die zweite
Blase gehört weiterhin zu Aikos Kopf, nicht zur verschiebbaren Statusleiste.
Ein neuer Klick oder eine andere Äußerung bricht einen ausstehenden Nachsatz
ab. Bewusstes Schweigen entfernt auch die alte Blase.

## Verhalten statt bloßer Zufallsauswahl

### Klickfolge (Beispiel bei gelassener Stimmung)

| Klicks innerhalb 7,5 s | Interpretation | Ausdruck |
|---|---|---|
| 1–2 | Aufmerksamkeit | ruhige Antwort, Blick oder Winken |
| 3 | Muster bemerkt | neugieriger, trocken kommentiert |
| 4–5 | wiederholt gedrängt | etwas gereizt oder spöttisch |
| 6–7 | persönliche Grenze | knapper, bestimmter |
| 8 | letztes Wort | kurze Schlussbemerkung |
| 9+ | bewusstes Schweigen | keine neue Sprechblase |

Bei guter Laune wechselt die mittlere Stufe zu spielerischem Necken; bei
Müdigkeit reagiert Aiko zurückhaltender. Während echter Rechenarbeit
kommen eigene Unterbrechungsdialoge zum Einsatz. Nach mindestens zwei
solchen Unterbrechungen kann sie nach **nachgewiesener** längerer Arbeit
noch einmal darauf zurückkommen. Eine kurze Lastspitze wird nicht zur
großen erschöpfenden Geschichte erklärt.

Nach einer Klickpause beginnt eine neue Folge. Gereiztheit klingt getrennt
davon nach kurzer Zeit ab. Bei niedriger Laune setzt Aiko früher Grenzen und beendet die Folge
schon nach sechs Klicks; nachts fallen die ersten Antworten eher leise aus.

Die Anzahl der Klicks ist ein **flüchtiger**
Zustand, keine über Tage gesammelte Schuld.

### Laufzeit und Tagesrhythmus

Die Tageszeit bestimmt, ob Arbeit spät oder Erholung passend wirkt. Der
individuell gelernte Wochenrhythmus aus v0.9 kann eine unerwartete
Beanspruchung kenntlich machen – nur wenn genug Beobachtungen vorliegen.
Die reine Windows-Laufzeit ist **kein** Beleg, dass Aiko so lange wach oder
beschäftigt war. In ruhigen, unbeaufsichtigten Phasen kann sie schlafen,
auch wenn der Rechner eingeschaltet bleibt.

### Situationsgedächtnis

Flüchtig gespeichert werden: kurze Klickfolge, Wiederholungen während einer
bestätigten Arbeitsphase, letzte Pflegeaktion und ein kleines Zeitfenster
nach Arbeitsende. Das Lernprofil aus v0.9 behält nur aggregierte Kennwerte
und keine einzelnen User-Aktionen. Aiko behauptet nichts über Arbeit, die
sie während einer Programmpause nicht beobachten konnte.

## Redaktionsregeln

- Kurze, natürliche deutsche Sätze; nur manche bekommen eine Pointe.
- Eine Pause oder ein „...Hm?“ ist manchmal die beste Reaktion.
- Humor entsteht aus Kontext und leichtem Kontrollverlust, nicht aus
  fortgesetztem Sarkasmus.
- Sie sagt „Ich habe gerade viel zu tun“, nicht „Die GPU ist ausgelastet“.
- Sie beansprucht keine Kenntnis geöffneter Apps oder der Arbeit der Person.
- Ereignisse dürfen sich auf unmittelbar vorher beobachtete Interaktionen
  beziehen; nach Neustart erfindet sie keine solche Erinnerung.
- Animationen dürfen nur `idle`, `waiting`, `review`, `failed`, `waving`,
  `jumping` zugewiesen bekommen. Kein neues „ärgerlich“, „verlegen“ oder
  „essen“ als vorgetäuschter Spritezustand.

## Abnahme unter Windows

1. Zehnmal schnell hintereinander auf Aiko klicken. Sie sollte zuerst
   antworten, dann ihr Verhalten ändern und schließlich kurz schweigen.
2. Mit hoher Laune wiederholen; sie sollte länger spielerisch reagieren.
3. Eine tatsächlich rechenintensive Aufgabe mindestens einige Dutzend
   Sekunden ausführen, Aiko mehrmals anklicken, nach der Entlastung auf
   den Rückbezug achten.
4. Die Aufgabe ohne Unterbrechungen wiederholen: keine erfundene Erinnerung
   an Klicks. Erst längere Belastungsphasen rechtfertigen längere Erholung.
5. Einen Zweizeiler abwarten oder mitten im Nachsatz erneut klicken; es
   darf kein verspäteter alter Satz aufploppen.
6. Bei Tages- und Nachtzeiten vergleichen. Windows-Uptime alleine darf
   Aiko nicht als übermüdet darstellen.
7. Bei Spracheingabe im Browser erneut Vordergrundverhalten prüfen:
   Die Fensterkorrektur ist unverändert aus v0.8, ein echter Win32-Test
   bleibt erforderlich.

**Nicht behaupten:** Eine ausgewogene Persönlichkeit lässt sich nicht allein
durch automatisierte Tests abnehmen. Die 167 bestehenden/neuen Tests prüfen
Zustandslogik und GUI-Kontrakte. Für Sprachstil und Timing ist der
Windows-Praxistest ausschlaggebend.
