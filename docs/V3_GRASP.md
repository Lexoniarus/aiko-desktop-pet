# V3-Greiffamilie

Aufheben, Halten, Untersuchen und Hinlegen verwenden die freigegebene
Greifvorschau vom 10.11.2026. Vier gewinnt verwendet dieselben Zeichnungen
mit eigener Wurf-Wiedergabe. Das Paket enthält 77 unterschiedliche
384×416-PNGs: 15 Schlüsselbilder und 62 vorhandene Zwischenbilder. Für die
Laufzeitintegration wurde nichts neu generiert. Hochauflösende Originale,
Prompts und Vorbereitung bleiben im privaten Projektordner außerhalb von Git.

## Bildquelle und Darstellung

`infrastructure/grasp_assets.py` lädt und validiert `assets/actions/grasp.json`:
Dateipfade, SHA-256, Zeitgrenzen und eindeutige semantische Ereignisse.
`CharacterCatalog.clip_for` liefert für 1X und 2X denselben Clip. Der native
Cache verkleinert die HD-Quelle für 1X im Speicher; es gibt keinen zweiten
kleinen Bildsatz. Der Room-Paketexport übernimmt sämtliche neuen Clips,
Zeitphasen, Ereignisse und den Ankermodus `center`.

Die fertig montierten Bilder enthalten die vorhandenen Köpfe einschließlich
Kinn vor dem Körper. Die Laufzeit setzt diese Köpfe nicht neu zusammen.
Blickrichtungen, Gehen, Essen und Schlaf wurden nicht geändert.

Pro Pose gibt es einen gemeinsamen Palm-Haltepunkt. Gegenstände liegen mit
ihrer Bildmitte an diesem Punkt und werden an der Bodenlinie begrenzt. Hände
dürfen hinter dem Gegenstand verschwinden; zusätzliche Finger-Vordergrundmasken
und individuelle Greifkorrekturen pro Item entfallen für diese Familie.
Beim Übergang zur unveränderten Essensfolge gilt wieder deren bestehender
Kataloganker. Buchzustände bleiben beim bestehenden Buch-Renderer.

## Phasen und Zuständigkeiten

| Clip | Verwendung |
| --- | --- |
| `pick_up` | Herunterbeugen, am Ereignis `attach_object` aufnehmen, zum Halten aufrichten |
| `hold_item` | Stabile Haltepose mit Blick auf den Gegenstand; auch bei direkter Übergabe |
| `inspect_item` | Ankommen, nach links führen, links betrachten, über die Mitte nach rechts führen; 2.550 ms |
| `inspect_hold` | Rechts betrachten; mindestens 1.000 ms, bei längerem Kommentar dort warten |
| `inspect_return` | In 450 ms zur mittigen Haltepose zurückkehren |
| `put_down` | Rückweg zum Boden; nur `detach_object` gibt den Gegenstand frei |
| `throw_item` | 86 Abspielphasen für Vier gewinnt; eigener `release_object`-Marker |

Die Untersuchung dauert ohne verlängerten Kommentar vier Sekunden. Bei
400 ms beginnt der tatsächlich ausgewählte Untersuchungskommentar. Bei
850 ms erscheint einmal für 650 ms ein kleines 🔎, gleichzeitig mit dem Text.
Der Hinweis ersetzt weder Text noch dessen Abschluss. Längere Kommentare
verlängern nur die rechte Ruhepose, nicht die Armbewegung oder die Rückkehr.
Der Blick bleibt beim Gegenstand; die Rückkehr enthält keinen Blick zum Nutzer.

`ObjectInteractionCoordinator` besitzt den Ablauf und die World-Übergaben.
Die Erkennung erfolgt weiterhin durch die tatsächliche Wahrnehmung und das
Objektgedächtnis. Erst nach vollständiger Untersuchung und abgeschlossenem
Kommentar folgt gegebenenfalls der echte Erkennungskommentar. Es gibt keine
zeitgesteuerte Schein-Erkennung aus der Vorschau. Bekannte Gegenstände dürfen
den bestehenden direkten Verwendungspfad nehmen. Essen beginnt danach über
die vollständige Drei-Bissen-Folge; Bücher verwenden die bestehende Leselogik.
Nahrung und Beziehungseffekte werden durch diese Bildmarker nicht vervielfacht.

Desktop und Room verbinden den Koordinator über ihre bestehenden Abspiel- und
Feedback-Ports. Die neue Untersuchung ist nur mit vorhandenem Greifpaket aktiv;
ältere Installationen behalten ihren bisherigen Fallback. Abbruch entwertet
Aktionskennungen und ausstehende Kommentare/Marker; der vorhandene Koordinator
regelt das geordnete Hinlegen oder Freigeben des tatsächlichen Gegenstands.

## Vier gewinnt

`RoomGameEffects` und `ConnectFourThrow` spielen `throw_item` mit seinen
kanonischen Zeiten. Aufnehmen und Abwurf richten sich nach den Ereignissen,
nicht nach den alten festen Frame-Nummern 3 und 5. Der Flug startet am letzten
tatsächlichen Palm-Haltepunkt. Es gibt keine Untersuchung, keinen Verbrauch
und keinen zusätzlichen World-Gegenstand für den kosmetischen Spielstein.
Spielregeln, Landeposition, Zugabschluss und Belohnungen bleiben bei ihren
bestehenden Eigentümern. Schließen beendet Marker und Flugcallbacks.

## Reproduktion und Prüfung

```powershell
python -m tools.character_grasp_export <privater-Quelljob> aiko_pet/assets
```

Der Export kopiert die vorhandenen freigegebenen PNGs bytegleich, prüft
Auflösung und binäres Alpha und validiert das gestufte Paket vor dem Austausch.
Er schreibt nur `actions/grasp.json` und `actions/grasp/`. Die alten Atlas- und
Handmaskendaten bleiben gebundene Archiv-/Fallbackquellen; vollständige
Installationen wählen für diese Greifhandlungen das neue Paket.

Gezielte Tests prüfen Katalog und Paketexport, 1X/2X, native FrameClock und
Overlay-Anker, echte Room-Abspielzeiten, lange/kurze Kommentare, Erkennung und
einmaligen Verbrauch, Emoji/Text-Koexistenz, semantischen Abwurf und Abbruch.
Die Tests verwenden isolierte Zustände, keinen persönlichen Spielstand.
TypeScript, Ruff und die gezielte strikte Typprüfung ergänzen diese Tests.
Browserautomation und physische iPad-Abnahme sind keine Bestandteile dieser
Prüfung. Ein bereits laufender Runtime-Prozess lädt den Katalog erst nach
regulärem Neustart neu; ein iPad-Update benötigt ein neu bereitgestelltes Paket.
