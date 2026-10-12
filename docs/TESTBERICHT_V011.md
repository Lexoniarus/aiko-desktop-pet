# Testbericht – Aiko Desktop Pet v0.11

**Basis:** Unverändertes Archiv `Aiko_Desktop_Pet_Dialoge_und_Verhalten_v0_10.zip`
mit allen 73 Sprites und bisherigen 167 Tests. Keine Schreibzugriffe auf
frühere Versionen.

## Automatischer Teststand

```bash
xvfb-run -a python -m unittest discover -s tests -q
```

195 Tests erfolgreich (vor der finalen Verpackung). Beinhaltet die früheren
167 Tests und neue Prüfungen für:

- Alte Spielstände mit nur drei Werten, neue Felder, Freundschaftslevel,
  kaputte JSON-Werte und atomare Speicherung
- Sozialbedürfnis als eigene Achse, Reden, Spielen, Streicheln, Füttern
- Energy Drink: +10 je Klick, bis 100; Wiederholung; voller Wert;
  nachts manuelles Wecken ohne sofortiges automatisches Wiedereinschlafen
- Langfristige Freundschaft, Grenzen gegen Spam und Tageslimit
- Hohe im Vergleich zu niedriger Live-Auslastung, keine ungemessenen
  Hintergrundstunden, Abschalten/Veralten der Telemetrie
- Unterschiedliche Dialogereignisse bei Sozialmangel, hoher Freundschaft,
  neuer Versorgung; überprüfte Sprite-Animationen
- Tkinter: fünf Balken, exakte 100-%-Füllung, alle Pflege-Buttons,
  verschiebbares Hover-UI, Detailstatus, Drei-Punkte-Menü, Ausblenden

## Sichtprüfung

Die Vorschau `vorschau/Aiko_v0_11_Tamagotchi.png` zeigt das tatsächlich
laufende Tkinter-Fenster mit den Originalsprites auf einem virtuellen
1366×768-Linux-Desktop. Die Simulation setzt Beispielwerte, sie zeigt
keine realen Hardwaremesswerte. Alle fünf Balken benutzen ein einheitliches
Raster und füllen bei 100 % ihre tatsächlich sichtbare Breite.

## Nicht verifiziert

Win32-Taskleistenposition unter verschiedenen DPI-Skalierungen, Windows-
Browser/Mikrofon-Z-Order, echte Hardwaremessungen einschließlich NVIDIA
und subjektive Balance nach mehrtägigem Betrieb. Die bisherigen 167
Tests werden nicht als Nachweis dieser Windows-spezifischen Effekte gewertet.
