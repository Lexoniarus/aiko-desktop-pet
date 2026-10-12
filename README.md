# Aiko Desktop Pet

**Aiko ist die Chibi-Personifizierung deines Rechners.** Sie lebt auf der Windows-Taskleiste, läuft gelegentlich umher, beobachtet die Maus und reagiert auf Interaktionen und Rechneraktivität. Sie ist eher ruhig, ein bisschen awkward und manchmal trocken-frech – abhängig von Stimmung, Energie und Erlebnissen.

**Aktuelle Version: v0.13** · lokal, kostenlos nutzbar, ohne KI-API, Konto oder Cloud.

![Aiko mit Kenney-Sci-fi-Statusleiste und Emote](vorschau/Aiko_v0_13_SciFi_und_Sprechblase.png)

[Reaktionsfolge als GIF ansehen](vorschau/Aiko_v0_13_Reaktionsablauf.gif)

## Was Aiko kann

- **Desktop-Pet:** Positioniert sich an der Taskleiste, läuft, springt, winkt und verfolgt den Mauszeiger auf dem Bildschirm.
- **Tamagotchi:** Fünf Bedürfnisse: Sättigung, Laune, Energie, Sozial und Zuwendung; dazu ein langfristiges Freundschaftslevel.
- **Pflege:** Füttern, Spielen, Reden, Streicheln, Schlafen und Energy Drink (+10 Energiepunkte pro Anwendung).
- **Persönlichkeit:** Situative deutsche Dialoge mit Stimmung, Tageszeit, Erinnerung, Wiederholungssperre und eskalierenden Klickreaktionen.
- **Emote-Sequenzen:** Emote → Text → eventuell Nachsatz → Emote; immer nacheinander im selben Anzeigeplatz.
- **Adaptive Aktivität:** Reagiert auf beobachtete CPU-/GPU-Arbeit und berücksichtigt RAM, Tages- und Wochenrhythmus sowie erlernte Gewohnheiten. Rechnerlaufzeit ist nicht dasselbe wie aktive Arbeitszeit.
- **UI:** Verschiebbare Kenney-Sci-fi-Statusleiste mit sechs Anzeigen, Hover-Aktionen und unabhängiger Sprechblase.

## Unter Windows starten

**Voraussetzungen:** Windows 10/11 und Python 3.11 oder neuer mit Tkinter.

1. [Code als ZIP herunterladen](https://github.com/Lexoniarus/aiko-desktop-pet/archive/refs/heads/main.zip) und in einen lokalen Ordner entpacken.
2. `Aiko_starten.bat` doppelklicken.
3. Mit der Maus über Aiko fahren, um die Pflegeaktionen und Werte zu sehen.
4. Bei Problemen `Aiko_starten_debug.bat` verwenden, um Fehlermeldungen anzuzeigen.

Zusätzliche Python-Laufzeitpakete sind nicht erforderlich. Eine lokale Schrift **Kenney Mini** wird automatisch verwendet, falls sie installiert ist; ansonsten Segoe UI. Schriftdateien werden nicht im Repository mitgeliefert.

Der Spielstand liegt unter `%LOCALAPPDATA%\AikoDesktopPet\state.json` und ist **nicht** Teil des Repositorys. Ein Versionswechsel übernimmt den bisherigen Spielstand.

## Tests

```bash
python -m unittest discover -s tests -q
```

GUI-Tests brauchen eine grafische Anzeige; unter Linux können sie über Xvfb laufen:

```bash
xvfb-run -a python -m unittest discover -s tests -q
```

Die automatisierten Tests wurden mit v0.13 unter Xvfb/Linux geprüft (231 Tests). Ein vollständiger manueller Langzeittest aller Windows-Fenster- und GPU-Sonderfälle steht aus.

## Projektstruktur

| Pfad | Inhalt |
|---|---|
| `aiko_pet/` | Domain, Desktop-Fenster, Rechneraktivität, Routinen, Interaktionen und Dialoge |
| `aiko_pet/assets/frames/` | 73 Chibi-Originalsprites |
| `aiko_pet/assets/emotes/` | Kenney-Emotes für aufeinanderfolgende Reaktionen |
| `aiko_pet/assets/kenney_ui/` | Kenney-basierte Panel- und Button-Grafiken |
| `aiko_pet/data/` | Deutscher Dialogkatalog |
| `tests/` | Unit- und GUI-Tests |
| `docs/` | Verhaltensmodelle, Pflegebalance und Entwicklungsnotizen |
| `vorschau/` | Screenshots und GIFs der echten Anwendung |

## Lizenz und Assets

Der **Programmcode** steht unter [MIT](LICENSE). Die verwendeten UI- und Emote-Grafiken von [Kenney](https://kenney.nl/) stehen unter [CC0 1.0](LICENSES/KENNEY_CC0.md). Aikos eigene Charaktergrafiken haben einen **separaten Rechtevorbehalt**; siehe [ASSETS.md](ASSETS.md). Öffentliches Repository bedeutet nicht, dass die Charaktergrafiken automatisch frei weiterlizenziert sind.

Aiko Desktop Pet ist ein eigenständiges Hobbyprojekt und benötigt weder ComfyReview noch Character Chronicles.
