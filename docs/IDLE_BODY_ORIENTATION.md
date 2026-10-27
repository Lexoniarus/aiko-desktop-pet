# Körperausrichtung beim Umgucken

> **Status 27.10.2026:** Die folgenden Regeln beschreiben den bisherigen
> Einbau. Der Nutzer hat sein Zusammenspiel mit dem Mausinteresse noch nicht
> abgenommen. Der [neue Konzept- und Umbauplan](ADAPTIVE_CURSOR_REWORK_PLAN.md)
> ersetzt als Ziel insbesondere die automatische Körperdrehung nach 1,2 s
> Seitenblick durch eine bewusste gemeinsame Absicht. Frontal bleiben alle
> 16 Kopfblickrichtungen nutzbar. In dieser Dokumentationsrunde wurde der
> beschriebene Laufzeitcode nicht geändert.

Die vorhandene Halbprofil-/Dreiviertel-Standbasis und die kleinen Drehschritte
sind in die passive Darstellung eingebunden. Die frontale Haltung ist die
Ausgangs- und Ruhehaltung. Der Körper folgt erst nach länger anhaltendem Blick
nach links oder rechts; Kopfvarianten können innerhalb der passenden Richtung
wechseln. Für diese Umsetzung wurde kein Bild neu generiert.

## Verhalten

- Die ersten 1,2 Sekunden auf derselben Blickseite reagiert nur der Kopf.
  Kurzes Mauswechseln löst keine dauernden Körperdrehungen aus.
- Alle rechten Blicksektoren 1–7 und linken Sektoren 9–15 zählen jeweils als
  dieselbe Seite. Kleine Kopfbewegungen innerhalb dieser Seite starten die
  Wartezeit nicht neu. Es gibt keine Bedingung für einen besonders seitlichen
  Blickwinkel; auch ein längerer diagonaler Blick kann den Körper mitnehmen.
- Ein kurzer Blick auf die Gegenseite lässt einen schon gedrehten Körper
  ebenfalls stehen. Erst nach 1,2 Sekunden anhaltender neuer Blickseite dreht
  er über die Mitte um. Bis dahin bleibt der Kopf innerhalb der zur aktuellen
  Körperausrichtung passenden Posen.
- Rein vertikale Blicke starten frontal. Nach längerem vertikalem Blick
  kehrt auch ein zuvor gedrehter Körper zur Front zurück. Endet die
  Aufmerksamkeit ganz, beginnt der Rückweg ohne zusätzliche Wartezeit.
- Die vorhandenen Fußhebe-/Umsetzphasen 1–3 führen zum Dreiviertel-Stand.
  Jede Drehphase bleibt mindestens 140 ms sichtbar; verspätete Aufrufe
  überspringen keine Zeichnung.
- Bei einem Seitenwechsel dreht Aiko zuerst über die Mitte zurück. Ein nach
  links ausgerichteter Körper bekommt keinen nach rechts blickenden Kopf.
- Wenn die Aufmerksamkeit endet, führen die Drehschritte zurück zur Front.
  Die bestehende Idle-Steuerung für Blinzeln und Schwanken bleibt aktiv.
- Schlafen, Aktionen, Übergabe und vorhandene Ortsbewegung behalten Vorrang.
  Sie setzen die passive Körperausrichtung zurück.

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
