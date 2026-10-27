# Körperausrichtung beim Umgucken

> **Stand 27.10.2026:** Der
> [Cursor-/Idle-Umbau](ADAPTIVE_CURSOR_REWORK_PLAN.md) ist im Code umgesetzt.
> Die praktische Sichtung des Verhaltens mit dem Nutzer steht aus. Vorhandene
> Grafiken und die 1X-/2X-Exporte sind unverändert.

Frontal ist die normale Ausgangs- und Ruhehaltung. Alle 16 Kopfblickrichtungen
sind frontal frei verfügbar. `BodyOrientation` führt ausschließlich explizite
Front-/Dreiviertel-/Profilabsichten aus; die frühere Ableitung aus einem
Kopfsektor mit 1,2 Sekunden Verweilen ist entfernt.

## Verhalten

- Die Cursorpolicy wählt eine begrenzte Aufmerksamkeit mit stabilem Ziel.
  Ruhiges Interesse kann nach drei Sekunden eine Dreivierteldrehung erlauben.
  Ein kurzer oder hektisch wechselnder Blick bleibt frontal.
- Eine mögliche Annäherung braucht weitere ruhige Beobachtung, erreichbare
  Position und Bereitschaft. Der Körper dreht vor tatsächlichen Schritten bis
  ins Profil. Ein abgebrochener Auftrag wird nicht als alter Blick nachgespielt.
- Jede Drehphase bleibt mindestens 140 ms sichtbar. Späte Aufrufe überspringen
  keine Zeichnung. Beim Seitenwechsel führt die Folge über die Front.
- Ein gedrehter Körper erhält ausschließlich passende Kopfvarianten. Ein
  Gegenblick setzt keinen unmöglichen Kopf an den bisherigen Körper.
- `WalkController` und `WalkDriver` bleiben die einzigen Bewegungsbesitzer.
  Kleine Idle-Ausflüge erfolgen nach 45–90 Sekunden Ruhe, normalerweise mit
  einem, gelegentlich zwei Schritten. Ein kurzer Mausblick lenkt einen laufenden
  Idle-Ausflug nicht sofort um; reale Bedienung und World-/Aktionsvorrang gelten.
- Nach dem Idle-Schritt bleibt eine kurze Stand-/Blickpause, dann die geordnete
  Rückkehr zur Front. Ohne Schrittpaket bleibt die Figur stehen.
- Selbstständige Kopfblickgelegenheiten liegen bei 20–40 Sekunden und halten
  ein bis drei Sekunden. Der bestehende Blink-/Schwankrhythmus bleibt erhalten.
- Schlaf, Spiel, Aktionen, Übergabe und Halten behalten Vorrang. Absichtlicher
  Mauszugang und aktive Bedienung stoppen Ortsbewegung sofort. World-Ziele
  bleiben dabei gespeichert und können anschließend weiter ausgeführt werden.

Die Dreiviertelschritte sind ausschließlich Ausrichtungs-/Drehschritte. Sie
ändern weder Fensterposition noch `PetState` noch den Bewegungsauftrag. Die
seitliche Fortbewegung verwendet inzwischen den separat abgenommenen kleinen
Profilschritt; die zurückgewiesene experimentelle Gehschleife bleibt ausgeschlossen.
Vor Ortswechsel wird über alle acht Drehphasen bis zum Profil gedreht; danach
kehrt der Körper geordnet über Dreiviertel zur Front zurück. Kleine Idle-Schritte
und zugelassene Cursorannäherung nutzen denselben Bewegungsbesitzer.
Siehe [Umsetzung und Grenzen](ADAPTIVE_CURSOR_IMPLEMENTATION_PLAN.md).

## Daten und Zuständigkeiten

`assets/body_poses/manifest.json` beschreibt ein eigenständiges optionales
HD-Paket. Version 2 enthält 18 Clips mit insgesamt 102 PNGs: die bisherigen
acht Drehbilder und 18 Kopf-/Körperkombinationen plus 16 volle Drehphasen
und 60 Schritt-/Kopfmontagen. Die vollständigen Standkörper einschließlich
Kleidung und Beinen werden als Grundlage erhalten. Die Körperbewegung während
des Drehens kommt aus den vorhandenen ganzen Drehzeichnungen.

Die ursprünglichen `frames/`- und `frames_2x/`-Dateien samt Manifest bleiben
unverändert. Die neuen Bilder liegen mit 384 × 416 Pixeln separat vor; die
1X-Ansicht entsteht durch Tk-Subsampling. Alle neuen Laufzeitbilder verwenden
binäres Alpha wie der bisherige Atlas. Das verhindert halbtransparente
Farbsäume im Windows-Farbtransparenzfenster, ohne echte türkise Haarbereiche
anhand ihrer Farbe zu löschen.

- `BodyOrientation` besitzt die körperliche Ausrichtung und den Drehfortschritt
  für passive Blicke und die Profilbereitschaft vor einem Schritt.
- `DesktopAnimationRuntime` wendet ihn nach der bestehenden Prioritätsauswahl an.
- `CharacterCatalog.body_clips` ergänzt den unveränderten regulären Katalog.
- `BodyPoseCache` lädt die HD-Bilder erst bei Bedarf und hält skalierte Ansichten.
- `AnimatedPet` bleibt für Darstellung und Timer zuständig.

Fehlt das optionale Paket in einer alten Installation oder Testfixture,
bleiben die bisherigen frontalen Blickposen gültig.

## Reproduzierbarer Export

`python -m tools.character_body_pose_export PACKAGE ASSET_ROOT`

Das private Paket enthält `body-left.png`, `body-right.png`, die bestehenden
kalibrierten `heads/00.png` bis `15.png`, jeweils vier Bilder unter
`turn-left/` und `turn-right/` sowie `package.json` mit den geprüften
Kopfversätzen. Private HD-Originale bleiben außerhalb des Repositories.
Der Export validiert alle Quellen vor der Installation und schreibt nur das
separate Paket. Seine Quellenliste enthält Dateinamen und Hashes, keine
persönlichen absoluten Pfade.

## Prüfung

Tests prüfen die reguläre frontale Haltung, seitliche Drehfolge, Rückweg über
die Mitte, Prioritäten, Unterbrechungen und das Anzeigen in beiden Größen.
Ein verspäteter Tick darf keine Drehphase verschlucken. Die Bildprüfungen
kontrollieren Paketabmessungen und binäres Alpha; ein separater Hashabgleich
hält die bestehenden 241 Atlasdateien unverändert.


Das optionale Exportpaket mit `locomotion: true` in `package.json` ergänzt
`step-left/`, `step-right/`, `step-head-left/`, `step-head-right/` und
vollständige `orient-left/`, `orient-right/` für beide
Seiten. Es nutzt vorhandene abgenommene Zeichnungen und Halsmasken. Der
Laufzeitschritt enthält sechs Phasen in 620 ms und 16 logischen Pixeln Strecke;
identische Anfangs-/Endbilder werden als dieselbe PNG referenziert. Fünf
passende Kopfachsen und das vollständige Profil je Seite teilen eine
Bewegungsfamilie, sodass Kopfwechsel den Schritt nicht neu starten.
