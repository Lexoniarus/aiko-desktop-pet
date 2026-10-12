# Aiko v0.7: Ereignisse, Emotionen, Animationen

## Charaktertreue

Grundlage ist Aikos eigenes Character Sheet: konzentriert, präzise,
beobachtend, vorsichtig mit Nähe, verletzlich ohne Theatralik, subtil
spöttisch, in vertrauten Momenten leise zugewandt. Ihre Aussagen sind
kurz, eher trocken und absichtsvoll. **Keine erzwungene Niedlichkeit, kein
ständiges Reden und kein Rollenspiel im Character-Chronicles-Setting.**

## Technische Zuständigkeiten

- `routine.py`: Uhrzeit/Wochentag, Mahlzeiten und Schlafphasen ohne
  Story-Rollen oder externe Tagesaktivitäten.
- `domain.py`: Bedürfnisse, Versorgung und Schlafzustand.
- `dialogue.py`: Emotionsableitung (`AikoMind`) und gewichtete Auswahl
  (`DialogueBook`). Keine UI-Abhängigkeit, keine externen Dienste.
- `data/dialogues.de.json`: 236 editierbare Zeilen, pro Satz `id`, `event`,
  `text`, `moods`, `periods`, `weekdays`, `animation`, `weight` und
  `cooldown_seconds`.
- `system_activity.py`: lokale CPU/RAM/Uptime-Erfassung, optionale NVIDIA-GPU-Abfrage auf eigenem Thread; keine Inhalte oder Apps.
- `gui.py`: Ereignisauslösung, 1×/2×-Originalsprite-Rendering,
  Sprechblasen und optionale autonome Kommentare.

## Priorität bei Emotionen

1. Schlafend (nur ruhige Reaktionen, Klicks wecken sie nicht automatisch).
2. Durch schnelles Klicken kurzfristig gereizt (13 Sekunden).
3. Energie ≤ 25 → müde.
4. Sättigung ≤ 25 → hungrig.
5. Laune ≤ 28 → zurückgezogen.
6. Kurz nach positiver Versorgung → zugewandt (45–70 Sekunden).
7. Hohe Laune (≥ 82) und genügend Energie (≥ 45) → verspielt.
8. Sonst → gelassen.

Vor einer Versorgung wird die Emotion eingefroren, **damit z. B. Hunger**
beim anschließenden Füttern noch Einfluss auf Aikos Antwort hat. Danach
werden die Werte normal aktualisiert.

## Dialogereignisse

| Quelle | JSON-`event` | Hinweise |
|---|---|---|
| Start | `greeting` | Gewichtung nach Tagesphase/Wochenende |
| Klicks | `click_left`, `click_right` | Eigenständige Reaktionen, ohne Pflege-Effekt |
| 4 schnelle Klicks in 5 s | `rapid_click` | Kurze Gereiztheit statt immer derselben Reaktion |
| Klick im Schlaf | `sleep_click` | Aiko bleibt schlafend |
| Pflege | `pet`, `play`, `play_tired` | Vorherige Stimmung wird berücksichtigt |
| Essen | `feed_meal`, `feed_snack`, `feed_full` | Mahlzeit, Snack, satt |
| Schlaf/Wecken | `sleep`, `wake` | Automatisch oder Button |
| Kontakt nach 25 min | `return` | Nur bei der nächsten echten Annäherung |
| Mausbewegung | `cursor_follow`, `cursor_far` | Selten, separater Cooldown |
| Bewegungsende | `walk_pause` | Selten; niemals erzwungen |
| Zeitgesteuert | `idle`, `hungry`, `tired`, `low_mood`, `morning`, `midday`, `evening`, `night`, `weekend`, `monday`, `friday` | Ruhig und zurückhaltend |

### Rechner als Aikos eigenes Arbeitsgefühl (v0.7)

`ComputerVoice` liest **nur lokale Auslastungs-Snapshots** und leitet daraus
Aikos Anstrengung ab. CPU-/GPU-Last tragen das Hauptsignal. RAM- und
Grafikspeicherbelegung sind lediglich zusätzliche Drucksignale; viel
reservierter Speicher bedeutet nicht automatisch viel aktive Arbeit.
Unbekannte Messwerte bleiben unbekannt. Auf Windows wird ungefähr alle
6 Sekunden im Hintergrund gemessen (CPU/GPU über zwei Samples geglättet).

Dialoge greifen **niemals** auf konkrete Hardwarebegriffe zurück, sondern
beschreiben ihre eigene Erfahrung. Neu sind die Ereignisse:

| Ereignis | Bedeutung |
|---|---|
| `computer_effort_rising` | Die Arbeit nimmt merklich zu |
| `computer_effort_heavy` | Hohe Last ist länger vorhanden |
| `computer_effort_peak` | Besonders hohe Last hält an |
| `computer_effort_easing` | Die Arbeit wird leichter |
| `computer_effort_recovered` | Erholung nach andauernder Belastung |
| `computer_effort_recovered_peak` | Erleichterung nach intensiver langer Phase |
| `computer_effort_rest` | Längere ruhige Phase |
| `computer_effort_steady` | Gleichmäßig mit Arbeit beschäftigt |
| `computer_uptime` | Schon eine Weile wach |

Erst nach mindestens **18 Sekunden** hoher Last kommt ein Kommentar wie
„Uff. ...Das hatte es wirklich in sich.“ infrage. Bei kurzen Spitzen ist
solch ein Satz **nicht** zulässig. Die Reihenfolge berücksichtigt frische
Messungen, Mindestabstände von rund 18 Sekunden für normale Veränderungen,
bevorzugte Erholungskommentare und den Vorrang direkter Nutzeraktionen.
Spontane Hardwaredialoge sind zusätzlich selten und haben mehrminütige
Pausen. Die verbesserte Reaktionsqualität hängt von realen Lastverläufen ab;
keine Messung wird als bestimmtes Programm oder erledigte Aufgabe erfunden.

Die Hover-Leiste zeigt weiterhin rohe CPU/GPU/RAM-Werte zur Kontrolle,
aber die subjektive Zeile ist etwa „Ich habe ordentlich zu tun.“.
Sensorwerte werden nur lokal genutzt und nicht gespeichert. Hohe Last
verschlechtert nicht ihre Tamagotchi-Bedürfnisse, beeinflusst aber ihre
Bewegung und die bereits vorhandenen `review`-Frames.

Die **Sprechblase** ist ausschließlich relativ zu Aiko positioniert.
Die Status-/Aktionsleiste ist als separates Fenster am Kopfbereich ziehbar,
merkt sich ihre Position lokal und erscheint durch Hover; beim Wegklicken
verschwindet sie. Sie wird standardmäßig neben Aiko gezeigt. Über `⋯` kann
sie wieder neben Aiko zurückgesetzt werden.

Eine JSON-Zeile mit leeren `moods`, `periods` oder `weekdays` ist für diese
Dimension allgemein gültig. Spezifisch passende Zeilen werden höher
gewichtet. Der Selector meidet die letzten sechs Äußerungen, respektiert
Zeilen-Cooldowns, und fällt erst bei Erschöpfung auf weniger strenge
Wiederholungsvermeidung zurück.

## Zugeordnete Sprite-Gruppen

`idle`, `waiting`, `review`, `waving`, `jumping`, `failed` werden für
Sprechreaktionen verwendet. `running-left`, `running-right`, `running` sind
Bewegungsframes; `look` sind **16 feste Blickrichtungsframes**. Letztere
werden als Cursor-Orientierung verwendet, nicht als zufällige Animation.

`feed_meal` verwendet beispielsweise `review`: eine sinnvolle Pause,
**keine echte Essbewegung**. Bei Schlafen fehlt bislang ein Schlafsprite;
die UI verwendet einen vorhandenen ruhigen Idle-Frame.

## Qualitätsgrundlagen

Alle Dialogzeilen müssen einen eindeutigen Schlüssel und eine auflösbare
Spritegruppe besitzen. Kein Triggertyp darf auf Bilder referenzieren, die
nicht im ausgelieferten Spritesatz existieren. Einfache Einheiten-/GUI-Tests
prüfen u. a. den Katalog, Auswahl, Emotionspriorität, wiederholte Klicks,
Verlaufswechsel, UI-Bubble, Startposition und Speicherkompatibilität.

Eine spätere weitere Ausbaustufe könnte zunächst **neue Originalsprites**
für Essen, Schlafen, Ärger und Streicheln ergänzen. Sie sind für v0.7
absichtlich nicht vorausgesetzt.
