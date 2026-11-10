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
