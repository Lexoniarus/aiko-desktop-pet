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

Zum Aktualisieren **Einstellungen → Paket aktualisieren** öffnen und die neue
Runtime-ZIP importieren. Die Starter-Adresse beibehalten, damit Aikos vorhandener
Spielstand zur gleichen Installation gehört. Es gibt keinen manuellen
Speichern-Knopf; bestätigte Aktionen und regelmäßige Zwischenstände werden
automatisch lokal gesichert.

Die veröffentlichte Startadresse bleibt für die Installation stabil und wird
in der Profildatei hinterlegt. Bereitgestellt werden nur Programm und Bilder;
der persönliche Spielstand bleibt lokal. Die Dateien für die Veröffentlichung
werden getrennt von der kleinen Installations-ZIP erzeugt.

Die erste Geräteabnahme ist für **iPad, 9. Generation, iPadOS 26.6** vorgesehen.
Sie steht noch aus. Neuere iPadOS-Versionen bleiben ebenfalls Zielplattformen.
Die vollständige Abnahmeliste steht im Repository unter
`docs/room/IPAD_ACCEPTANCE.md`.

Diese T1-Version enthält noch keinen Push-Sendedienst. Benachrichtigungen bei
geschlossener App und die Einbettung desselben Raums in die Desktop-App folgen
in ihren getrennten Umsetzungsschritten.
