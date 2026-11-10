# V3-Kommunikationsmimik im Raum

Stand: 10.11.2026. Die vorhandenen V3-Ausdrucksclips sind kurze
Kommunikationsanimationen. Neutraler Idle, Umsehen und Gehen behalten ihre
freigegebenen Kopf-/Körperbilder. Es werden keine neuen Bilder erzeugt oder
vorhandenen Konturen verändert.

## Behobener Rückfall auf V2

Einige historische Dialogeinträge starteten noch `waiting`, `waving`,
`waving-greeting` oder `jumping`. In der Raumfassung begann diese
Ganzkörperaktion vor dem V3-Ausdruck. Weil `RoomSession` Mimik nur außerhalb
einer Körperaktion zulässt, verwarf sie den eigentlich richtigen Ausdruck.
Insbesondere `waiting/00` und `waiting/07` enthalten noch vollständig den
alten V2-Idle mit Kopf und Körper. Eine alte Endpose konnte dadurch wie
eine zusätzliche Idle-Variante wirken.

Die direkte SSP-Begrüßung hatte denselben Fehler. Der Spieladapter hielt die
ausgewählte V2-Geste außerdem nach Ende ihrer Bilder weiter als aktuelle
Aktion fest. Ein isolierter Spielstart zeigte auch nach zehn Sekunden noch
`waving-greeting` statt der neutralen V3-Basis.

## Auswahl und Eigentümer

`frontend/room_communication.py` passt historische Kommunikationsreaktionen
an der Grenze zur Raumdarstellung an: `animation="idle"` plus vorhandene
V3-Mimik. Der bereits aus Ereignis, Zustand, Gesprächston und Autorenvorgabe
ermittelte `Reaction.expression` bleibt vorrangig. Fehlt er, bleiben
`waiting`/`waving` neutral; Begrüßung und reine Freude sind positiv,
`failed` bedrückt und `review` fragend. Keine globale Umdeutung der PNGs.
IDs, Text, Bedingungen, Dialogphasen, Ausdruckszeitpunkt und Rückmeldungen
bleiben erhalten. Der gemeinsame Katalog wird nicht umgeschrieben.

`RoomPlayback.speak` verwendet diese Anpassung vor der bestehenden
`ReactionPlayer`-Wiedergabe. Echte Körperaktionen behalten Vorrang. Während
einer solchen Aktion abgewiesene Mimik wird nicht später überraschend
nachgeholt. Der Ausdruck endet nach einer vollständigen vorhandenen Folge;
Abbruch und Spielschluss räumen ihn auf. Danach wird wieder die bestehende
V3-Ruhe-/Idle-Auswahl sichtbar, einschließlich Umsehen und Dreiviertelstand.

`RoomPlayback.presentation_id` unterscheidet wiederholte gleiche Ausdrücke
für die Webdarstellung. Die körperliche `action_id` und ihre Objektmarker
werden dafür nicht verändert. Alte Ausdrucks-Timer dürfen einen neueren
Ausdruck nicht löschen.

## Spiele

SSP-Begrüßung sowie die gesprochenen Ergebnisreaktionen von SSP,
Tic-Tac-Toe und Vier gewinnt starten keine V2-Wink-/Hüpfgeste mehr. Sie
geben den Ruhekanal frei und fordern über das bestehende `event_expression`
die passende V3-Mimik an: positive Freude, bedrückte Niederlage oder
fragendes Unentschieden aus Aikos Perspektive. Gleiches gilt für den
Mastermind-Ergebnisfallback ohne Snackfinale. Das reguläre Drei-Bissen-Finale
und seine Hand-/Itemmarker bleiben erhalten.

`GameSessionCoordinator` begrenzt übrige einfache Aktionsaufrufe zeitlich.
Die getrennte `game_action`-Steuerung für Greifen, Werfen, Mischen und Essen
bleibt Eigentümer ihrer Marker und Abschlüsse. Echtes Streicheln und Schlaf
werden ebenfalls nicht durch Gesichtsausdrücke ersetzt. Ein ausdrücklich
inszenierter Freudenhüpfer ist weiterhin eine eigene körperliche Bewegung,
keine notwendige Begleitaktion jeder positiven Äußerung.

## Gezielte Regressionen

`tests/test_room_communication.py` prüft mit einer echten Raum-Session und
isoliertem temporärem Spielstand:

- historische Sprechgesten mit allen vorhandenen Ausdrucksarten, inklusive
  neutralem Fallback und unverändertem Text;
- den ursprünglichen Ausdruckszeitpunkt und Abbruch;
- fortbestehende echte Pflegeaktionen;
- SSP-Begrüßung ohne hängende V2-Endpose und alle drei SSP-Ergebnisse;
- Tic-Tac-Toe- und Vier-gewinnt-Siegreaktionen, weiterhin mit echtem Wurf;
- Rückkehr zur neutralen V3-Basis, Spielschluss und ungültige alte Timer;
- erneutes Starten desselben Ausdrucks ohne veränderte Objekt-Aktionsnummer.

Ergänzend laufen die vorhandenen Raum-, Spiel-, Dialog- und Aktionsregressionen.
Lokal bestanden: 92 gezielte Python-Tests, neun Webtests, TypeScript-Prüfung,
repositoryweites Ruff und Pyright sowie striktes Mypy für alle 433 Quelldateien.
Die bereits vorbereiteten Assetkorrekturen wurden getrennt mit 22 Tests
für Körperposen, Cache, Charakter-, Ausdrucks- und Essensassets geprüft.
Ein vorhandener Abbruchtest initialisiert seine Snapshot-Variable jetzt vor
der Schleife, damit auch die repositoryweite statische Prüfung eindeutig ist.
Die Veröffentlichung eines neuen iPad-Pakets ist ein gesonderter Schritt;
ein lokaler Commit verändert die bereits installierte App nicht.

## Veröffentlichtes Testupdate (10.11.2026)

Diese Fassung ist als
[0.1.0-45d4cf160811](https://github.com/Lexoniarus/aiko-desktop-pet/releases/tag/room-test-0.1.0-45d4cf160811)
über den bestehenden iPad-Updatekanal veröffentlicht. Enthalten ist auch der
parallele Touch-Auswahlfix. Kein neuer Icon-/Profilimport und keine Änderung
des Spielstandschemas sind nötig; es wurde nichts gemergt.

Vor der Veröffentlichung bestanden auf dem exakten Paketquellstand
`45d4cf160811af1f6821a4b83be16ba550d4c750`:

- [Python 3.11/3.13, vollständige Anwendungssuiten und Windows-Grenztests](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42820946719)
- [Asset-Tooling](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42820951733)
- [Langzeitszenarien](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42820956831)
- [Web-Build und Webtests](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42820962470)

Dabei wurden veraltete Asset-Snapshot-/Herkunftsannahmen aktualisiert und die
fehlende `pathfinding`-Abhängigkeit im Offline-Wheel-Testbestand ergänzt.
Die Bilddateien wurden dafür nicht geändert. Alle 1113 PNGs des Pakets sind
bytegleich mit dem bisherigen veröffentlichten Paket. Ein isolierter Lauf
des tatsächlich gepackten Python-Codes unter Pyodide bestätigte V3-Reaktionen,
Rückkehr zu Idle und SQLite-Übernahme eines synthetischen alten Spielstands.
Eine Safari-/IDBFS- oder reale iPad-Abnahme wird dadurch nicht behauptet.

Die Pages-Vorprüfung erlaubte die frische Deployment-Kennung und wies die
bekannte fehlgeschlagene Kennung zurück. Ein bereits identischer öffentlicher
Stand wurde korrekt als nicht erneut zu veröffentlichen erkannt.
[Deployment 42822273365](https://github.com/Lexoniarus/aiko-desktop-pet/actions/runs/42822273365)
auf `b3f781fc5c1f3b4419cc80231edd242e71ca979a` bestand im ersten Versuch.
Die fünf Release-Dateien wurden gegen GitHubs SHA-256-Digests geprüft;
anschließend wurden öffentlicher Deskriptor, Starter und vollständiges
Runtime-ZIP durch den Workflow und nochmals lokal verifiziert.

Runtime-SHA-256:
`9adcce8fe935410fb5ce46b5af2ea99c3a9e3a11e2019cee6d37df916f77c072`.
Starter-SHA-256:
`c4d06c3d77865efb2b82ac315cdf71ef9ea7b3e13258522d25b6ae1cc2d8913b`.

Auf dem iPad: **Einstellungen → App-Version und Updates → Nach Updates
suchen**, den geprüften Download abwarten und **Jetzt neu starten** wählen.
Danach insbesondere spontane Sprechreaktionen, SSP-Begrüßung und Ergebnisse,
Vier-gewinnt-/Tic-Tac-Toe-Reaktionen sowie die Rückkehr zu neutralem Idle prüfen.
Die visuelle Abnahme auf dem Gerät bleibt beim Nutzer. Prüfbelege und Pakete
liegen privat außerhalb Git im Veröffentlichungsjob vom 10.11.2026.
