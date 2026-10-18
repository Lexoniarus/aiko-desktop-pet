# Gemeinsamer Interaktionsfokus — 18. Oktober 2026

**Planning follow-up:** The [object orientation and observed continuity
plan](OBJECT_ORIENTATION_AND_CONTINUITY_PLAN.md) records the implemented follow-up
and its verification ledger. Live left/right integration and audited cleanup are
complete; the current ledger separates automated checks from human acceptance.
It replaces local-only post-action checks with deliberate
left/right checks of all learned places while preserving exclusive activity
focus and independent knowledge, wish, tracking, and search states. The follow-up
uses small verified English commits; historical blanket no-commit wording below
does not apply to that implementation. The delivery history remains unchanged.

## Auftrag und verbindliche Regel

Eine laufende Interaktion besitzt Aikos Aufmerksamkeit bis zu ihrem vollständigen
Abschluss. Das gilt ab der Bindung eines Item-Ziels, einschließlich Hinlaufen,
Aufheben, Untersuchen, Essen und Ablegen, sowie für Spielen, Streicheln und Reden.
Währenddessen werden andere Gegenstände weder entdeckt, verfolgt, identifiziert
noch als vermisst festgestellt. Nähe und Blickrichtung öffnen keine Ausnahme.
Der eigene Gegenstand bleibt überprüfbar; seine beobachtete Wegnahme, Rückgabe,
Hand-/Face-Identifikation und sichere Physik dürfen weiter funktionieren.

Nach Ende der Interaktion wird die normale Umgebungswahrnehmung freigegeben.
Nur tatsächlich sichtbare alte Plätze liefern frische Verlustbelege. Bestätigte
Verluste werden einzeln gemeldet und haben mit ihrer gemeinsamen Suche Vorrang
vor freien neuen Zielen. Freies Gehen und Suchpatrouille beobachten ihre Umgebung;
die Untersuchung eines Suchkandidaten bindet den Fokus wieder exklusiv.

Das präzisiert und ersetzt die bisherige Ausnahme für gerichtete
Umgebungswahrnehmung während eines fokussierten Hinlaufens im
[älteren Aufmerksamkeitsplan](ATTENTION_PERCEPTION_SIMPLIFICATION_PLAN.md).
Keine Änderung an Speicherformat, Konsum, Care-Wirkung oder Statuszählung.
Kein automatisches Bereinigen des normalen Spielstands, kein Commit/Push/Merge.

## Diagnose und Zuständigkeiten

- `choose_object_attention` gibt Bewegung Vorrang vor `approach` und öffnet damit
  Umgebung und beobachteten Cursortransport trotz festen Item-Ziels. Nativ bei
  1x/2x nachgestellt: unbekannter Cupcake bleibt Ziel, ein anderer Cookie wird
  verfolgt und am neuen Ort erinnert, Vermisst bleibt null.
- Die native Aufmerksamkeit kennt bisher Objektphase, Schlaf, Bewegung und
  Cursortracking. Streicheln und Gespräch sind dort nicht vollständig vertreten.
  `blocked` unterbindet die Zielwahl, nicht die Sensorverarbeitung. Nativ wurden
  während Streicheln und einer laufenden Gesprächssequenz neue Sichtungen angelegt.
- Ein räumliches Fenster am fokussierten Platz darf nicht alle Nachbarn zu
  eigenen Entdeckungen machen. Die Anwendung grenzt den gewählten Gegenstand
  anhand vorhandener Ausführungszuordnungen ein; Welt-IDs allein erkennen nichts.
- Bestehende Besitzer bleiben zuständig: Objektkoordinator für Item-Episode,
  ActionPlayback für Animationsdauer, ReactionPlayer/SpeechPresenter für
  Gesprächs-/Bubble-Abschluss, Spielbesitzer für Spielaktivität. Die gemeinsame
  Aufmerksamkeit liest diese Besitzer. Kein zweiter Aktionszustand oder Timer.

## Etappen und Prüfungen

1. **Gemeinsame Aufmerksamkeitsentscheidung.** Item-Fokus vor Bewegung und freiem
   Cursorblick; laufende andere Aktion aus den vorhandenen Besitzern einbeziehen.
   Objektphase bleibt während eigener Feedback-Bubbles maßgeblich. Gesprächsfokus
   endet erst mit vollständiger Sequenz/Bubble und Animation, nicht nach einem
   kürzeren Clip. Unit-/Adapterprüfungen und statische Gates ausführen.
2. **Exakte Grenze am Wahrnehmungsbesitzer.** Während Item-Fokus nur den eigenen
   Gegenstand verarbeiten, einschließlich eigenen Cursortransports und Handpose.
   Nachbarobjekte dürfen keine neuen Erinnerungen oder Verlustbelege erzeugen.
   Verlust einer Ausführungszuordnung darf unbekannte Ziele freigeben, aber keine
   bekannte Identität erfinden. Objekt-, Besitz- und Physikprüfungen ausführen.
3. **Praxisablauf und falsche Tests korrigieren.** Den nativen Fall ab laufendem
   Anmarsch bei 1x/2x absichern: andere bekannte Portionen umstellen, Erinnerung
   während Fokus unverändert, erst danach sichtbare Verluste, eigene Bubbles und
   gemeinsame Suche. Streicheln/Gespräch und Freigabe nach tatsächlichem Ende
   absichern. Bestehende native World-/Timerprüfungen durchlaufen.
4. **Vollständige Regression und Übergabe.** Gesamtsuite, Ruff, Mypy, Pyright,
   Architektur- und Dokumentationsprüfung; Verträge und manuelle Prüfliste auf
   die gemeinsame Regel bringen. Ergebnisse und verbleibende Praxisabnahme hier
   festhalten. Normalen Spielstand für die Prüfungen nicht verwenden.

## Korrektur und Erhalt der Tests

| Bestehender Nachweis | Behandlung |
| --- | --- |
| `test_object_attention`: `approach` plus Bewegung ergibt `moving` | Falsche Erwartung ersetzen: eigener Gegenstand bleibt exklusiv |
| `await_return`/`await_settle` öffnet allgemeines `cursor`-Umfeld | Auf eigenen wartenden Gegenstand begrenzen; Rückgabe und Face-Nachweis erhalten |
| Native Vier-Portionen-Suche startet Umplatzierung erst in `inspect` | Um den tatsächlich gemeldeten früheren Einstieg ergänzen; 1x/2x, getrennte Portionen, Route und echte Cursor-/Physikwege erhalten |
| Blockierte Zielwahl allein erlaubt Beobachtung | Bei tatsächlicher Interaktion korrigieren; bloß geöffnete/gepinnte Toolbar bleibt kein Aktionsfokus |
| Freie Sichtfelder, Suchpatrouille, unbekannte Belegung | Erhalten; eingeschränkt werden nur laufende Interaktionen |
| Hand-/Face-Identifikation, eigener Target-Take/Return, fehlendes unbekanntes Ziel, sichere Übergabe, Clip-/Receipt-Ende | Erhalten; keine Teleport- oder willkürlichen Bindungsinjektionen hinzufügen |
| Ein Verlust je Bubble, getrennte physische Portionen, Nahpaar-Neustart, unveränderte Statuszahlen beim Lesen | Erhalten |

## Lieferstand

Etappen **1–4 abgeschlossen und automatisch geprüft**.
Die menschliche Praxisabnahme nach Neustart bleibt offen.
Vorhandene lokale Änderungen bleiben erhalten.

### Etappe 1 abgeschlossen — gemeinsame Priorität

Item-Episoden, einschließlich Hinlaufen und Warten auf den eigenen Gegenstand,
haben nun Vorrang vor Bewegung und allgemeinem Cursorblick. Die zentrale Policy
erhält zusätzlich einen gelesenen Aktivitätswert aus Animationsdeadline,
laufender Reaktionssequenz und sichtbarer Sprach-/Emote-Bubble. Ein Spiel und
Schlaf behalten ihre vorhandene Sperre. Es wurde kein Aktionsflag gespeichert:
Die bestehenden Besitzer liefern den aktuellen Abschlusszustand.

Eigene Objektphasen haben auch bei ihrer eigenen Bubble Vorrang vor der
allgemeinen Aktivitätssperre; Untersuchung, Ergebnis und sichere Ablage bleiben
damit ausführbar. Freies Gehen und Suchpatrouille bleiben nach Ende einer
laufenden Rückmeldung umgebungsoffen.

**64 Policy-, Adapter-, Architektur-, Reaktions- und Care-Presenter-Tests grün**.
Die falsche `approach`-Bewegungserwartung ist korrigiert; Warten öffnet kein
allgemeines Cursorumfeld mehr. Ruff grün, striktes Mypy über **186 Quellen** grün,
Pyright **0 Fehler / 0 Warnungen**. Die räumliche Eingrenzung des eigenen
Gegenstands folgt in Etappe 2; native Gesamtszenarien sind noch nicht behauptet.
Kein Commit, Push oder Merge; normaler Spielstand nicht verwendet.

### Etappe 2 abgeschlossen — eigener Gegenstand statt Umfeld

Awareness begrenzt positive Sichtungen während Objektfokus jetzt auf den bereits
zugeordneten eigenen Gegenstand, exakten gelernten Platz oder tatsächliche eigene
Hand. Das kleine geometrische Zielfenster ist keine Freigabe benachbarter Items.
Auch negative Ortsbelege betreffen währenddessen nur das eigene Ziel. Ein Take
eines anderen Items kann trotz alter Bindung keinen Cursortrack eröffnen.
Der beobachtete Take des eigenen Ziels darf weiterhin verfolgt werden, auch wenn
der Cursor seine ursprüngliche Position verlässt.

Geht die ausführbare Zielzuordnung am tatsächlich betrachteten eigenen Platz
verloren, wird die Aktion freigegeben. Unbekannte Ziele werden vergessen;
gelernte Erinnerungen bleiben bis zum späteren echten Verlustbeleg erhalten.
Ein neuer Nachbar wird erst nach Freigabe in der normalen Wahrnehmung entdeckt.
Es gibt keine neue Zustandsvariable für diese Entscheidung.

**196 Objekttests grün**, einschließlich einer kompakten Prüfung für nahe
Nachbarn, deren Take und ausbleibende fremde Verlustbelege. Zusätzlich **7 native
World-Prüfungen grün**: Vier-Portionen-Neustart/Suche bei 1x/2x, beide
Face-Reunion-Einstiege, unbekanntes entzogenes Getränk mit Identifikation am
Cursor sowie unbekannte umplatzierte Nahpaare nach Handuntersuchung bei 1x/2x.
Ruff, striktes Mypy (**186 Quellen**) und Pyright (**0 Fehler / 0 Warnungen**)
sind grün. Der vollständige frühere Anmarschfall und Care-Abschlüsse folgen in
Etappe 3. Kein Commit, Push oder Merge; normaler Spielstand nicht verwendet.

### Etappe 3 abgeschlossen — tatsächlicher Anmarsch und Care-Abschluss

Der bestehende native Vier-Portionen-Fall wurde bei 1x/2x auf den früheren
Einstieg umgestellt: Aiko läuft bereits auf einen unbekannten Apfel zu, während
vier gelernte Portionen mit echten Cursor-Takes, Releases und Fallphysik
umgestellt werden. Vorhandene Bindungen dürfen keine beobachteten Transporte
erzeugen. Die Erinnerungen bleiben während des gesamten Hinlaufens unverändert;
die Handphase wird anschließend vollständig abgeschlossen. Ein zusätzlicher
synthetischer Blick nach der Aktion entfällt. Die alten Plätze liegen für den
ersten Abgleich im tatsächlichen Nahbereich; weitere Verlustbelege folgen der
Patrouille. Alle vier Portionen bekommen je eine passende Verlustmeldung.
Suchroute, Untersuchungen, unbekannter Zwischenfund und die wirklich fehlende
Portion bei 2x bleiben abgesichert. Der Zwischenfund liegt nun tatsächlich auf
dem begangenen Suchweg; nach Ende der Suchaufgabe endet auch deren Test, bevor
legitime neue Hungerhandlungen beginnen.

Native Care-Fälle prüfen Streicheln und Gespräch: fremde Moves/Drops liefern
weder Sichtungen noch neue Orte oder Verlustmeldungen. Auch nach Ende des
kürzeren Animationsanteils hält die Gesprächssequenz den Fokus. Nach vollständiger
Freigabe kommt bestätigter Verlust vor der neuen Untersuchung. Ein zusätzlicher
Fall mit echten Tk-Timern wartet auf das tatsächliche Ende der Gesprächssequenz,
ohne die Bubble per Testhelper abzukürzen. Die gemeinsame Aufmerksamkeit sperrt
auch erinnerungsbasierte neue Ziele und noch nicht ausgespielte Verlustreaktionen
während einer fremden Aktivität; reine Sensorunterdrückung genügt dafür nicht.

Der erste breite native Lauf meldete fünf alte Erwartungsfehler: Die gemeinsame
Rand-Anmarschhilfe verlangte in drei Fällen noch `moving`, ein Test verlangte
die Entdeckung eines fremden Items während Fokus, und ein verschwundenes
unbekanntes Ziel sollte trotz zulässigem sofortigem Vergessen erst eine
Verlust-Bubble abwarten. Diese Erwartungen sind korrigiert. Reichweitenprüfung
am Greifframe, Wiederherstellung, Konsumzeitpunkt und Freigabe bleiben erhalten.
Der ältere Awareness-Nachweis wird als **freies** Gehen ohne `committed` geführt;
damit bleibt Umgebungswahrnehmung ohne Item-Fokus ausdrücklich geprüft.

Der neue vollständige native Wiederholungslauf besteht **56 Tests in 157.331
Sekunden**, Exitcode 0, keine Skips. Enthalten sind alle World-GUI- und
World-Runtime-Fälle, Hand-/Face-Rückgaben, Randreichweite, Nahpaar-Neustarts,
beide Skalen, echte Gesprächs-/Bubble-Zeiten und vollständige Konsumclips.
Zusätzlich **196 Objekttests grün**, Ruff grün, Mypy **186 Quellen grün**, Pyright
**0 Fehler / 0 Warnungen**. Architektur, Verträge und manuelle Prüfliste verweisen
auf die gemeinsame Regel. Kein Commit, Push oder Merge; normaler Spielstand
nicht verwendet.

### Etappe 4 abgeschlossen — Abschlussprüfung und gefundener Spielabschluss

Der erste vollständige Lauf führte **1.119 Tests in 277.614 Sekunden** aus.
Er hatte genau einen Fehlschlag: Nach Spielschließung blieb Cursorwahrnehmung
gesperrt. Der Test war fachlich richtig und wurde nicht abgeschwächt. Ursache:
Der visuelle Spielmodus beendete zwar den Sprite-Clip, dessen Deadline beim
kanonischen ActionPlayback-Besitzer blieb aber aktiv. `_set_game_mode` beendet
diese Deadline jetzt ebenfalls über `cancel_at`; der vorhandene Spieltest prüft
zusätzlich den tatsächlichen Playback-Abschluss. Es gibt keinen weiteren Timer.

Der gezielte Gegenlauf mit Spiel-GUI, Architektur, visueller Aufmerksamkeit,
Policy sowie beiden Care-Fokusfällen besteht **48 Tests in 6.561 Sekunden**.
Ruff, Mypy (**186 Quellen**) und Pyright (**0 Fehler / 0 Warnungen**) sind grün.
Die vollständige Regression wird nach diesem tatsächlichen Fix wiederholt.

#### Reproduzierbare Abschlussprüfung

Windows, Python **3.11.9**, Pillow **11.3.0**, Tk **8.6**; Ruff **0.13.2**,
Mypy **1.18.2**, Pyright **1.1.414**. Tk-Suiten laufen nacheinander mit temporären
Spielständen. Wie im vorherigen Plan beschrieben sammelt der externe Harness
zyklische Tk-Ressourcen zwischen Tests auf dem Hauptthread; keine Anwendungsausnahme
und kein Test werden unterdrückt.

```powershell
@'
import sys, unittest, gc
gc.disable()
class MainThreadCollectionResult(unittest.TextTestResult):
    def stopTest(self, test):
        super().stopTest(test)
        gc.collect()
r = unittest.TextTestRunner(verbosity=1, resultclass=MainThreadCollectionResult).run(
    unittest.defaultTestLoader.discover('tests'))
sys.exit(not r.wasSuccessful())
'@ | uv run --no-project --python 'C:\Users\Alexa\AppData\Local\Programs\Python\Python311\python.exe' --with Pillow==11.3.0 python -B -
uvx --from ruff==0.13.2 ruff check aiko_pet tests main.py tools
uv run --no-project --python 'C:\Users\Alexa\AppData\Local\Programs\Python\Python311\python.exe' --with Pillow==11.3.0 --with mypy==1.18.2 python -m mypy --strict --no-incremental aiko_pet main.py tools
uv run --no-project --python 'C:\Users\Alexa\AppData\Local\Programs\Python\Python311\python.exe' --with Pillow==11.3.0 --with pyright==1.1.414 python -m pyright --project pyrightconfig.json
git -c core.safecrlf=false diff --check
```

#### Abschlussergebnis und praktische Übergabe

- Vollständiger frischer Wiederholungslauf nach dem Spielabschluss-Fix:
  **1.119 Tests grün in 276.916 Sekunden**, Exitcode 0, keine Skips.
  Alle Objekt-, Besitz-, Physik-, Persistenz-, Care-/Spiel-, Dialog-, UI-,
  Architektur-, Asset- und nativen Timerprüfungen sind enthalten. Die bekannten
  Tk-`ThemeChanged`-Diagnosen beim Fensterabbau sind nicht fehlschlagend.
- Zusätzlich unter dem installierten **Python 3.14.0 / Pillow 12.3.0**:
  **5 native Praxisfälle grün in 4.345 Sekunden** — gemeinsame Suche ab Anmarsch
  bei 1x/2x, Streicheln, Gespräch und unmittelbare Freigabe nach Spielschließung.
- Ruff grün; striktes Mypy über **186 Quellen** grün; Pyright **0 Fehler und
  0 Warnungen**. **211 lokale Dateiverweise und 15 Abschnittsverweise** in
  **33 Markdown-Dateien** lösen auf; `git diff --check` ist unauffällig.
- Der Vergleich mit dem Quellsnapshot nach Plananlage zeigt gezielte Änderungen
  an sechs Produktions-, sieben Test- und fünf Dokumentationsdateien einschließlich
  dieses neu angelegten Plans. **776 weitere Repository-Dateien sind bytegleich**;
  außer dem Plan wurde keine weitere Datei neu angelegt oder gelöscht.
  Branch `feature/world-foundation` und HEAD `fb4f3578d14aafc230b1e26e9192ed3ad9a0c99a`
  werden nicht verändert; maßgeblich bleibt die vorhandene lokale Arbeit.

Für die menschliche Abnahme die neue Version neu starten und die aktuelle
[praktische Prüfliste](WORLD_SMOKE_TEST.md) verwenden: vier Umplatzierungen schon
ab Anmarsch, fremde Drops/Moves während Streicheln, Gespräch und Spiel, unveränderte
Erinnerungen bis zum vollständigen Ende, danach frische sichtbare Verlustbelege,
je eine Bubble und gemeinsame Suche. Während tatsächlichen Item-Fokus darf der
eigene Gegenstand weiterhin weggenommen, zurückgegeben oder vorgeführt werden.
Die ursprünglichen Hand-/Face- und sicheren Greifregeln bleiben erforderlich.

Der normale Spielstand wurde für Umsetzung oder Prüfungen weder bereinigt noch
verändert. Kein Commit, Push oder Merge. Der automatische Teil dieses Plans ist
abgeschlossen; die praktische menschliche Rückmeldung wird nicht vorweggenommen.
