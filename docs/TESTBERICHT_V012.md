# Aiko Desktop Pet v0.12 – Tests und Abnahmehinweise

## Technischer Stand

Basis: unverändertes v0.11-ZIP, vor den Änderungen ausgepackt.
Baseline: `xvfb-run -a python -m unittest discover -s tests -q`:
**195 Tests, alle bestanden.**

v0.12: derselbe Befehl:
**220 Tests, alle bestanden.**

Darin enthalten: bestehende GUI-/Fensterverwaltungs-, Dialog-, Sprite-,
Tages- und Systemlast-Tests sowie 25 neue Tests für Zuwendung,
Freundschaft, alte Spielstände, Dialogereignisse und GUI.

Separat geprüft: vollständiges Sprite-Inventar (73 unveränderte PNGs),
JSON-Katalog (404 gültige Dialogeinträge), Tkinter-GUI im virtuellen
Linux-X11-Display und tatsächlicher Screenshot mit den sechs Balken.

## Abgedeckte Fälle

- Streicheln ist eigenständig: +25 Zuwendung, +6 Laune, +2 Sozial,
  kein Energiebonus.
- Spielen, Reden, Füttern und Energy Drink erfüllen jeweils andere Bedürfnisse.
- Bekannte hohe CPU-/GPU-Last verstärkt die bestehenden Belastungsraten,
  aber **nicht** den Zuwendungsabbau oder den Abbau von Freundschaft.
- Zuwendung sinkt langsam bei Wachheit und im Schlaf; bei geringer
  Zuwendung wirkt ihre Stimmung etwas zurückhaltender.
- Freundschaft steigt bei wirksamer Versorgung und abwechslungsreicher
  Pflege, nicht beim Klicken auf bereits volle Bedürfnisse.
- Belohnungssperre, Tagesmaximum, neuer Tag, Energy-Drink-Spam.
- v0.11-Spielstand ohne Zuwendung: alte Werte und Einstellungen erhalten;
  neue Zuwendung = 75; Neustart und erneutes Speichern funktionieren.
- Defekte Speicherwerte werden geklemmt oder ignoriert.
- Zwei Reihen mit sechs Statuswerten im Hover, Balken füllen bei 100 %
  ihre tatsächliche Pixelbreite; Status-Details und Menüs bleiben bedienbar.
- Neue Sprechblasen nutzen nur vorhandene Sprite-Animationen.

## Grenzen

Der Test erfolgte unter Linux/Xvfb. Win32-spezifisches Topmost-Verhalten,
Browser-Mikrofon-Overlay und die echte NVIDIA-Telemetrie wurden hier nicht
auf echter Windows-Hardware reproduziert. Sie sind im Code unverändert,
müssen aber beim praktischen Einsatz weiter geprüft werden.
