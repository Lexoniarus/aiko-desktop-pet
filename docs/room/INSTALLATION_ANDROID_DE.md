# Aiko auf dem POCO testen

Erstes Testgerät: **POCO X3 NFC, MIUI Global 14.0.5 Stabil, Android 12**.
Wir verwenden dieselbe Web-App wie auf dem iPad. Auf Android installierst du
kein Apple-Profil und keine APK. Aiko und ihr Spielstand bleiben auf dem Gerät.

## Einfacher Einstieg aus Dropbox

Im gelieferten Dropbox-Ordner liegt **Aiko-auf-dem-POCO-starten.pdf**. Öffne sie
direkt in Dropbox und tippe auf den großen Button **Aiko öffnen**. Öffne den
Link in Chrome; falls Dropbox eine eingebaute Vorschau verwendet, wähle dort
**Im Browser öffnen**. Danach folgst du den Chrome-Schritten unten. Du musst
keine Adresse abtippen.

Alternativ kannst du **Aiko-Android-Einstieg.zip** herunterladen, entpacken und
dieselbe PDF daraus öffnen. Diese kleine ZIP enthält nur die verlinkte Anleitung
und eine Textanleitung. Sie führt zur gleichen veröffentlichten PWA und zum
gleichen Updatekanal wie das iPad. Das Anlegen des Symbols bestätigst du in
Chrome. Die PDF/ZIP ist keine eigene App-Version und kein Runtime-Paket.
Der tatsächliche Datei-/Link-Übergang auf dem POCO bleibt Teil der Geräteprüfung.

## Einrichtung über Chrome

1. Chrome im Play Store auf den für dein Gerät verfügbaren Stand aktualisieren.
   Die genaue Chrome-Version für den Test notieren.
2. [Aikos Startseite](https://lexoniarus.github.io/aiko-desktop-pet/room/) in
   Chrome öffnen. Für die erste Einrichtung online bleiben und warten, bis das
   Zimmer mit den Bedienelementen erscheint.
3. Im Chrome-Menü **App installieren** beziehungsweise **Zum Startbildschirm
   hinzufügen** wählen und den Systemdialog bestätigen. Die genaue Bezeichnung
   hängt von Chrome und Gerät ab.
4. Aiko über ihr Symbol öffnen. Unter **Einstellungen → App-Version und Updates**
   die angezeigte Version prüfen. Sie muss zur vereinbarten Testversion passen.
5. Aiko schließen, Flugmodus einschalten und über dasselbe Symbol erneut öffnen.

Die öffentliche Startseite liefert jeweils die veröffentlichte Version.
Ein lokal vorbereitetes Testpaket erscheint dort erst nach Veröffentlichung.
Ein neu erzeugtes Symbol allein bestätigt noch keinen abgeschlossenen Download
oder zuverlässigen Offlinebetrieb.

## Gemeinsame Updates mit dem iPad

iPad und Android nutzen dauerhaft dieselbe PWA unter derselben Startadresse.
Ein veröffentlichtes mobiles Update liefert beiden dasselbe Programmpaket.
Updates werden beim Öffnen, bei Rückkehr in die App und nach erneuter
Internetverbindung geprüft. Unter **Einstellungen → App-Version und Updates →
Nach Updates suchen** kannst du die Prüfung selbst starten.

Nach vollständigem Download und erfolgreicher Prüfung wird das Update für den
nächsten Start vorgemerkt. **Jetzt neu starten** sichert vorher den Spielstand;
ein laufendes Spiel wird nicht automatisch unterbrochen. Beide Geräte können
das Update zu unterschiedlichen Zeiten übernehmen, etwa wenn eines offline ist.
Ihre Spielstände bleiben unabhängig voneinander auf dem jeweiligen Gerät.
Es gibt keinen separaten dauerhaften Android-Updatekanal.

## Ein lokales Testpaket vor der Veröffentlichung verwenden

Falls du eine neuere Datei **aiko-room-<version>.zip** erhältst:

1. Diese Datei unverändert auf das POCO übertragen, beispielsweise per USB in
   **Downloads**. Die Runtime-ZIP **nicht entpacken**.
2. Die oben eingerichtete Aiko öffnen und **Einstellungen → Paket aus Datei
   importieren** wählen. Danach **Aiko-Paket auswählen** antippen und die ZIP
   aus Downloads wählen. Warten, bis die Prüfung und der Zimmerstart fertig sind.
3. Unter **Einstellungen → App-Version und Updates** die Version mit der
   gelieferten Testversion vergleichen. Danach den Offline-Neustart wiederholen.

Das vorhandene Symbol, die Startadresse und die Website-Daten beibehalten.
Zum Aktualisieren nicht deinstallieren und keine App-/Browserdaten löschen.
Der Spielstand dieses Smartphones ist unabhängig von deinem iPad-Spielstand.
Eine ältere veröffentlichte Version darf das neuere importierte Paket nicht
automatisch ersetzen; das gehört zu den Prüfungen.
Sobald diese Version gemeinsam veröffentlicht ist, bist du bereits auf diesem
Stand. Ein späteres neueres gemeinsames Update kommt wieder über den normalen
Updateweg; der Dateiimport erfordert keinen Wechsel zu einer anderen App.

## Erster Prüfdurchgang

- Im Hoch- und Querformat: Menüs öffnen und schließen, Texte lesen und längere
  Listen scrollen. Aiko rufen, streicheln und das Zimmer wischen.
- Eine Portion auf den Boden ziehen, eine Geste abbrechen und Füttern prüfen.
- Ein Sternzeichen wählen, kurz warten, Aiko schließen und offline neu öffnen.
  Die Auswahl muss erhalten bleiben.
- Alle sechs Spiele öffnen und bedienen. Die Android-Zurück-Geste getrennt mit
  offenem Menü, im Spiel und im Zimmer prüfen; ihr beobachtetes Verhalten notieren.
- Zu einer anderen App wechseln, das Display sperren und Aiko wieder öffnen.
  Anschließend vollständiges Schließen und einen Geräteneustart prüfen.

Bei einem Problem festhalten: Version, Hoch-/Querformat, die letzten Schritte,
erwartetes und tatsächliches Verhalten. Bildschirmfoto oder kurzes Video hilft
bei sichtbaren Fehlern. Akkusparmodus und Chrome-Einstellungen zunächst auf
ihrem normalen Stand lassen und diesen Stand beim Test notieren.

## Gerätebericht

Unter **Einstellungen → Gerätebericht herunterladen** wird eine lokale JSON-Datei
gespeichert. Möglichst je einen Bericht im Hoch- und Querformat erzeugen.
Der Bericht enthält Browserangaben, Bildschirm-/Fenstermaße, Paket-/Runtimeversion,
die Zeit bis zum fertigen Zimmer und den beobachtbaren Browserspeicherstatus.
Er enthält keinen Spielstand und lädt nichts automatisch hoch.

Gerätemodell, MIUI-/Android-Build und Chrome-Version zusätzlich notieren:
Browserangaben können vom Betriebssystem verkürzt sein. Ein Speicherstatus
`false` bedeutet, dass kein dauerhafter Schutz gegen automatische Bereinigung
bestätigt ist; `null` bedeutet, dass die Abfrage kein Ergebnis liefern konnte.
Beides ist getrennt vom beobachteten Speichern und Wiederöffnen zu beurteilen.

Die vollständige technische Liste steht in [ANDROID_ACCEPTANCE.md](ANDROID_ACCEPTANCE.md).
Automatische Browserprüfungen ersetzen deine Prüfung auf dem POCO nicht.
