# Aiko auf dem iPad testen

Das Paket besteht aus dem kleinen **HTTPS-Starter** und der größeren
**Aiko-Runtime-ZIP**. Beide werden auf Windows gebaut. Ein Mac ist nicht nötig.

1. Den Inhalt von `aiko-starter-<version>.zip` auf einer stabilen HTTPS-Adresse
   bereitstellen. Der vorbereitete GitHub-Workflow heißt
   **Deploy room starter (manual)**. Die Veröffentlichung ist ein eigener Schritt.
2. Diese Adresse auf dem iPad in Safari öffnen. Über **Teilen → Zum
   Home-Bildschirm** Aikos Symbol hinzufügen. Diesen Safari-Schritt bestätigt
   der Benutzer selbst.
3. Aiko über das neue Symbol starten.
4. `aiko-room-<version>.zip` über Dropbox oder GitHub laden und in **Dateien**
   ablegen. Eine ZIP des Branch-Quellcodes ist dafür ungeeignet.
5. In Aiko **Aiko-Paket auswählen** antippen und die Runtime-ZIP auswählen.
   Nach dem Import laufen Raum, Python und Spielstand lokal auf dem iPad.
6. Zum Prüfen der Offline-Nutzung Flugmodus aktivieren und Aiko neu öffnen.

Zum Aktualisieren **Einstellungen → Paket aktualisieren** öffnen und die neue
Runtime-ZIP importieren. Die Starter-Adresse beibehalten, damit Aikos vorhandener
Spielstand zur gleichen Installation gehört. Es gibt keinen manuellen
Speichern-Knopf; bestätigte Aktionen und regelmäßige Zwischenstände werden
automatisch lokal gesichert.

Die erste Geräteabnahme ist für **iPad, 9. Generation, iPadOS 26.6** vorgesehen.
Sie steht noch aus. Neuere iPadOS-Versionen bleiben ebenfalls Zielplattformen.
Die vollständige Abnahmeliste steht im Repository unter
`docs/room/IPAD_ACCEPTANCE.md`.

Diese T1-Version enthält noch keinen Push-Sendedienst. Benachrichtigungen bei
geschlossener App und die Einbettung desselben Raums in die Desktop-App folgen
in ihren getrennten Umsetzungsschritten.
