# Aiko Desktop Pet v0.13 – Sci-fi-Oberfläche und Emote-Sequenzen

## Verbindliches Interaktionsprinzip

Ein Emote ist **kein zweites paralleles Fenster zum Text**, sondern ein
aufeinanderfolgender Ausdrucksschritt derselben Reaktion.

Mögliche Abläufe:

- `Fragezeichen → Text → Herz` (verlegene, freundliche Klickreaktion)
- `Ausrufezeichen → Text` (Überraschung, Belastungsanstieg)
- `Herz → Text → Textnachsatz → Herz` (Zuwendung, awkward Kommentar)
- `Text` (normale, zurückhaltende Reaktion ohne Emote)
- `Emote` allein in seltenen wortlosen Idle-Momenten, niemals zeitgleich
  mit einer Textsequenz.

**Ein Anzeigeplatz:** Bei jedem Abschnitt wird das vorige Emote oder der vorige
Text entfernt, bevor der nächste Abschnitt angezeigt wird. Nur Aikos vorhandene
sprechblasenartige Toplevel-Oberfläche wird dafür genutzt. Der interne
Generation-Zähler verhindert, dass verspätete Timer aus unterbrochenen
Reaktionen wieder erscheinen. Nutzerklicks unterbrechen den laufenden Ablauf;
bei schnellen Klickserien wird das eröffnende Emote übersprungen, damit
Aikos eigentliche Antwort nicht dauerhaft verdrängt wird.

Die Stufen werden ausdrücklich über `emote_before` und `emote_after` im
bestehenden Dialogkatalog pro Eintrag festgelegt. Es werden **keine zufälligen
Emotes unabhängig von der Bedeutung** über einem Satz angezeigt.
Die bisherigen nachfolgenden, selbstkorrigierenden Kommentare bleiben erhalten.

## Herkunft der Assets

Die Dateien stammen aus der vom Nutzer benannten Dropbox:

- `/Kenney Game Assets All-in-1 3.4.0/2D assets/Emote Pack/PNG/Pixel/Style 1`
- `/Kenney Game Assets All-in-1 3.4.0/UI assets/UI Pack - Sci-fi/PNG`
- Referenzlayout: `UI Pack - Sci-fi/Sample.png` (im Ordner `vorschau/`)

Die verwendeten Kenney-Packs stehen laut den beiden mitgelieferten
`License.txt` unter **CC0 1.0**. Angewandt werden 15 unveränderte
Emote-Pixelgrafiken und ein kleines Set bestehender bzw. aus ihnen abgeleiteter
Sci-fi-Panel- und Button-Bilder. Der Rest des umfangreichen Asset-Packs ist
nicht nötig und wird nicht mitgeliefert. Aikos 73 eigene Sprites bleiben
unverändert.

## Typografie

Die vom Nutzer bereitgestellte Schrift `Kenney Mini` wird automatisch gewählt,
**falls sie lokal unter Windows installiert ist**. Andernfalls verwendet
Aiko `Segoe UI`. Die Schriftdatei ist aus Lizenz-/Bereitstellungsgründen **nicht
im Projekt-ZIP enthalten**; vor dem Start kann der Nutzer seine eigene Kopie
unter Windows installieren. Keine Schriftdatei wird aus dem System extrahiert
oder weitergegeben.

## UI-Rückwärtskompatibilität

Erhalten bleiben: sechs Tamagotchi-Werte, die Pflegeaktionen, `Status`, `⋯`,
verschiebbares Hover-Panel, dessen Position und Auto-Ausblenden, getrennte
Sprechblase über Aiko, zentrale Windows-Z-Order-Steuerung, vorhandene
Stimmung und Tageslogik, Rechnerauslastung und `%LOCALAPPDATA%`-Speicherstand.

## Bekannte Grenzen

- Visuelle GUI-Tests laufen unter Xvfb/Linux; die tatsächliche Windows-11-
  Fensterreihenfolge bei Browser-Spracherkennung benötigt Praxistests.
- Ohne lokal installierte Kenney-Mini-Schrift wird Segoe UI angezeigt.
- Emotes sind nur kurzfristige Äußerungscues; sie ersetzen weder Text noch
  neue Charakteranimationssprites.
