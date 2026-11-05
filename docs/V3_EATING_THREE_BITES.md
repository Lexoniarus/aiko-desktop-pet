# V3-Essen mit drei Bissen

Die gemeinsame Essensfolge verwendet die zwölf Ganzfigurzeichnungen der neutralen
V3-Essensbasis und den unveränderten neutralen Idle als Schlussbild. Zwischen
benachbarten Posen liegen zwei rechnerisch interpolierte Bilder. Die Mund- und
Kaubewegung wird für drei Bissen wiederverwendet; die Arme lösen sich erst
danach zur Idle-Haltung. Das Gericht bleibt bis zum dritten Bissen sichtbar.

Der vollständige Ablauf umfasst 85 Abspielphasen aus 37 unterschiedlichen
PNG-Dateien und dauert 7.420 ms. Die 24 interpolierten Bilder sind abgeleitete
384×416-Animationsbilder, keine neuen hochauflösenden Originalzeichnungen.
Es wurden dafür keine neuen ImageGen-Aufträge ausgeführt. Die Interpolation
richtet die Hände innerhalb der ganzen Figur aus; es gibt keine getrennte
Kopf-/Körpermontage oder pauschale Streckung. Kurze Zwischenframes bleiben
etwas weicher als ihre gezeichneten Endpunkte.

## Laufzeit und Zuständigkeiten

- `infrastructure/eating_assets.py` validiert das optionale HD-Paket
  `assets/actions/eat.json`, einschließlich Pfaden, Hashes, Zeitgrenzen, drei
  Bissereignissen und dauerhaft ausgeblendetem Gegenstand nach dem letzten Biss.
- `CharacterCatalog.clip_for` wählt dieselbe abgenommene Essensfolge und
  dieselben Zeiten für 1X und 2X. 1X entsteht im Speicher aus der 2X-Quelle;
  es wird keine zusätzliche kleine Bildserie erzeugt. Auch der reguläre
  Charaktercache leitet seine 1X-Darstellung aus den vorhandenen HD-Bildern ab.
  Die alten Atlanten und ihre Manifeste bleiben vorerst Referenz-/Fallbackdaten.
- `BodyPoseCache` lädt die vorbereiteten HD-Bilder bei Bedarf. Es gibt keine
  Interpolation, OpenCV- oder NumPy-Abhängigkeit in der laufenden Anwendung.
- `AnimatedPet` verwendet denselben Clip für Sprite, FrameClock und
  Gegenstandsanker. Auch der regelmäßige Overlay-Abgleich der Welt delegiert
  an diese Auflösung. Die tatsächliche Clipdauer verlängert die bestehende
  ActionPlayback-Frist über den vorhandenen Port.
- Ein Größenwechsel behält Quelle, Phasenindex und Zeitablauf der gemeinsamen
  Essensfolge. Er startet keine neue Anwendungshandlung und verbucht keine Nahrung.
- `ObjectInteractionCoordinator` bleibt Eigentümer des tatsächlichen
  Verbrauchs: einmal beim Beginn des Essens. Die drei Bissereignisse sind
  visuelle Marker und lösen keine weiteren Nahrungs-, Freundschafts- oder
  Moodlet-Effekte aus.

## Quellen und Export

Die hochauflösenden Originale, die Interpolationsvorbereitung und die
Prüfbelege bleiben im privaten Projektordner außerhalb des Repositories.
Die gemeinsame lokale Asset-Anleitung verzeichnet den aktuellen Quelljob.
Der Export ist reproduzierbar mit:

```powershell
python -m tools.character_eating_sequence_export <privater-Quelljob> aiko_pet/assets
```

Der Export prüft und staged das vollständige Paket vor dem Austausch.
Er schreibt ausschließlich die neue HD-Essensfolge unter `assets/actions/`.
Blickrichtungen, Gehbilder, Körper-/Kopfmodule, Mimik und 1X-Dateien bleiben
unverändert. Der Katalog wird beim Anwendungsstart eingelesen; eine bereits
laufende Instanz benötigt einen regulären Neustart.

## Prüfung

Gezielte Katalogtests decken ungültige Pfade/Hashes, fehlerhafte Bisszahlen,
frühes Verschwinden und Wiederauftauchen des Gerichts ab. Isolierte native
Tk-Tests spielen sämtliche Phasen und drei Bissereignisse ab, prüfen die
Aktionsfrist, Menü-unabhängigen Overlay-Abgleich, Größenwechsel und Abbruch.
Die Prüfung verwendet eigene PetState-Instanzen und keinen normalen Spielstand.
Die unabhängige Bildprüfung ist von der anschließenden Nutzersichtung getrennt.

## Mastermind-Snackfinale

Das Snackfinale verwendet dieselben 85 Phasen und 7.420 ms wie normales Essen,
in beiden Größen. `GamePresentation.action` erhält dafür `None` als Dauer:
Der Sprite-Eigentümer übernimmt dann die vollständigen Clipzeiten unverändert.
Explizite Spielzeiten bleiben für andere Gesten möglich, müssen aber zur
tatsächlichen Quelle passen. Eine alte Acht-Phasen-Essensvorgabe wird abgewiesen.

Die Handposition kommt pro tatsächlich gezeichnetem Frame über den schmalen
`food_anchor`-Port aus `AnimatedPet`. Die Fensteransicht hält weder einen
zweiten Animationskatalog noch eigene Essensanker oder Bisszähler vor. Ein
fehlender Handanker blendet den kosmetischen Donut ab dem dritten Bissen aus.
Der Abschluss erfolgt einmal nach dem vollständigen Ausklang. Schließen
entwertet Bildmarker und Abschluss und räumt die Snackanzeige ab.

Das Finale bleibt rein kosmetisch: kein World-Gegenstand, keine zusätzliche
Sättigung, Freundschaft oder Moodlet-Gutschrift. Native Integrationstests
prüfen die volle Folge, alle Snackpositionen, das Verschwinden beim dritten
Bissen, beide Größen, Größenwechsel und Abbruch während des Essens.

## Verbleibende Atlasreferenzen

Die vollständige Installation zeigt bei 1X die verkleinerte HD-Quelle statt
der alten Pixelzeichnungen. Es werden dafür keine zusätzlichen PNGs abgelegt.
Die 120 alten Dateien unter `frames/` und die acht früheren HD-Essensdateien
unter `frames_2x/eat/` sind noch durch den Atlasloader, das alte HD-Manifest,
Archivexporter und Herkunftsprüfungen gebunden. Sie sind deshalb in dieser
Steuerungskorrektur nicht gelöscht. Ihre spätere Entfernung erfordert zuerst
die Auflösung dieser Verweise; sie darf keine verbliebenen Aufrufe oder
Reproduktionswerkzeuge beschädigen. Vorschauen und große Originale bleiben
im privaten Projektordner außerhalb des Repositories.
