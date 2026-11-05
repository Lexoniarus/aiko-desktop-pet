# Aiko auf dem iPad testen

Du bekommst **eine ZIP namens `Aiko-iPad-Installation-<version>.zip`**.
Ein Mac ist nicht nötig. Die erste Einrichtung darf einmalig online laden;
diesen Ablauf hat der Besitzer ausdrücklich bestätigt.

1. Die Installations-ZIP über Dropbox oder GitHub auf das iPad laden und in
   **Dateien** antippen, um sie zu entpacken.
2. Die enthaltene Datei **Aiko-installieren.mobileconfig** öffnen.
3. In den **Einstellungen** das geladene Profil auswählen und **Installieren**
   bestätigen. Diesen Systemdialog muss der Benutzer bestätigen; gegebenenfalls
   wird der iPad-Code verlangt.
4. Das neue **Aiko-Symbol** auf dem Home-Bildschirm antippen.
5. Für die erste Einrichtung online bleiben. Aiko lädt und prüft ihr gesamtes
   Paket automatisch. Du musst keine Adresse öffnen und keine Runtime-ZIP
   auswählen. Danach laufen Raum, Python und Spielstand lokal auf dem iPad.
6. Zum Prüfen der Offline-Nutzung Flugmodus aktivieren und Aiko neu öffnen.

Das selbst erzeugte Profil ist nicht signiert und enthält genau einen
entfernbaren Web Clip. Es enthält keine Geräteverwaltung, Zertifikate oder
VPN-Konfiguration. Falls Dateien das Profil nur anzeigt, ist das Öffnen derselben
Datei als Anhang in Apple Mail der dokumentierte Ausweichweg. Der direkte Weg
aus Dateien muss auf dem echten iPad bestätigt werden.

Das Hinzufügen des Symbols allein installiert die Runtime noch nicht. Der
erste Start muss den Download abschließen. Erst danach ist der Offline-Start
abgesichert. Eine unterbrochene Einrichtung kann erneut gestartet werden.

Updates werden beim Öffnen und bei Rückkehr in die App im Hintergrund geprüft.
Nur vollständig heruntergeladene und geprüfte Pakete werden für den nächsten
Start vorgemerkt. Unter **Einstellungen → App-Version und Updates** stehen die
installierte Version, **Nach Updates suchen** und bei einem fertigen Update
**Jetzt neu starten**. Ein laufendes Spiel wird nicht automatisch unterbrochen;
vor einem bewussten Neustart wird der Spielstand gesichert. Ohne Internet läuft
die bereits installierte Version weiter. Neue Updates brauchen wieder Internet.
Ein Git-Push allein veröffentlicht noch kein App-Update: Das geprüfte Paket muss
zusätzlich auf der bestehenden Startadresse bereitgestellt werden.

**Erstes Update von der ursprünglichen Testversion:** Das vorhandene Aiko-Symbol
online öffnen. Danach Aiko im App-Umschalter vollständig schließen und erneut
öffnen, damit die neue Startoberfläche verwendet wird. Sobald „Update bereit“
erscheint, nochmals vollständig schließen und wieder öffnen. Danach sind die
Update-Einstellungen verfügbar. Je nach bereits erfolgtem Laden entfällt der
erste Neustart. **Profil, Symbol und Website-Daten nicht entfernen.** Eine neue
ZIP oder Profilinstallation ist für diesen Übergang nicht nötig.

Der Dateiimport bleibt als manueller Ausweichweg in den Einstellungen erhalten.
Die Starter-Adresse beibehalten, damit Aikos vorhandener Spielstand zur gleichen
Installation gehört. Es gibt keinen manuellen
Speichern-Knopf; bestätigte Aktionen und regelmäßige Zwischenstände werden
automatisch lokal gesichert.

Die veröffentlichte Startadresse bleibt für die Installation stabil und wird
in der Profildatei hinterlegt. Bereitgestellt werden nur Programm und Bilder;
der persönliche Spielstand bleibt lokal. Die Dateien für die Veröffentlichung
werden getrennt von der kleinen Installations-ZIP erzeugt.

Die erste Geräteabnahme ist für **iPad, 9. Generation, iPadOS 26.6** vorgesehen.
Profilinstallation und Start wurden vom Besitzer bestätigt. Die erste Nutzung
hat offene Abweichungen bei Raumübergängen, Blasen, Drag-and-drop, Bewegung,
Figurengröße/Tiefe, Möbelüberdeckung und Spieloberflächen gezeigt. Die
Desktop-Parität ist damit noch nicht abgenommen. Neuere iPadOS-Versionen bleiben
ebenfalls Zielplattformen.
Der Korrekturbuild **0.1.0-ff6d7142a7cc** behebt diese gemeldeten Punkte und
wurde ohne sichtbare Fenster mit Touch-Eingaben, allen sechs Spielen sowie
Offline-Neustart geprüft. Bitte denselben Ablauf auf dem iPad erneut ansehen;
die Geräteabnahme bleibt bis dahin offen. Das Update kommt über das vorhandene
Symbol und die oben beschriebenen Update-Einstellungen.
Der anschließende Build **0.1.0-3351f6ec864a** ergänzt die vorhandene Gehfolge,
einen durchgehenden Boden und die Desktop-Abläufe beim Vorhalten, Erkennen,
Übernehmen und Essen. Zum Anbieten eine Portion kurz vor Aikos Gesicht halten,
dann zu ihren Händen führen und loslassen. Nicht angenommene Portionen fallen
auf den Boden und lassen sich dort wieder aufheben. Erneut über dieselben
Update-Einstellungen laden; die normale Figurengröße bleibt erhalten.
Die vollständige Abnahmeliste steht im Repository unter
`docs/room/IPAD_ACCEPTANCE.md`.

Diese T1-Version enthält noch keinen Push-Sendedienst. Benachrichtigungen bei
geschlossener App und die Einbettung desselben Raums in die Desktop-App folgen
in ihren getrennten Umsetzungsschritten.
