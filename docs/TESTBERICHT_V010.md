# Testbericht – Aiko Desktop Pet v0.10

**Ausgangsbasis:** Original-ZIP `Aiko_Desktop_Pet_Adaptiver_Rhythmus_v0_9.zip`
(vollständig und isoliert entpackt); bestehende Datei- und Speicherstruktur
beibehalten. Keine Änderungen am Repository eines anderen Projekts.

## Prüfungen

```text
xvfb-run -a python -m unittest discover -s tests -q
----------------------------------------------------------------------
Ran 167 tests in 10.281s

OK
```

Auch ohne grafisches Display lassen sich die reinen Domain-Tests unter
Python ausführen; Tk-GUI-Tests benötigen einen verfügbaren Display-Server.

Der Testumfang umfasst unter anderem:

- Alte v0.9-Funktionen und Speicherstandskompatibilität.
- 72-Stunden- und mehrwöchige Routine-Simulationen, Uhrzeit und Nachtarbeit.
- Mehrstufige Klickfolgen bei normaler, guter und niedriger Laune.
- Klicken während echter Lastphasen und Rückbezug nach Entlastung.
- Keine erfundenen Erinnerungen nach einer kurzen Lastspitze.
- Einmalige späte Reflexion nach längerer Arbeit, danach normale Ruhe.
- Unerwartete Arbeit nur nach hinreichend belastbarem Lernprofil.
- Zweiteilige Sprechblasen, Abbrechen des Nachsatzes bei neuer Reaktion
  oder bewusstem Schweigen.
- Vorhandene Animationsassets sowie UI-Verhalten der Fenster und Statusleiste.

**Sprite-Prüfung:** 73 PNG-Dateien sind gegenüber v0.9 per SHA-256
vollständig identisch geblieben.

**Dialoge:** 339 primäre Aussagen in 67 Ereigniskategorien,
109 davon mit optionalem zweiten Satz. 40 generischere Alttexte entfernt,
zentral genutzte Originaltexte redaktionell überarbeitet, neue Texte
für Klick-/Arbeits-/Ruhefolgen ergänzt. Texte werden nicht generiert.

## Visueller Probelauf

Die reale Tk-Anwendung wurde in einer virtuellen Linux-Anzeige geöffnet;
`vorschau/Aiko_v0_10_Klickreaktion.png` und
`vorschau/Aiko_v0_10_Nachsatz.png` sind tatsächliche Screenshots der
Originalsprites und der App, nicht künstlich erzeugte Illustrationen.
Sie zeigen das Nacheinander zweier Sprechblasen über Aikos Kopf.
Die Windows-Taskleiste wurde hier nicht nachgestellt.

## Noch nicht unter Windows verifiziert

- Win32-Z-Order bei Browser-Mikrofoneingabe.
- Tatsächliche NVIDIA-Telemetrie und GPU-intensiver Dauerbetrieb.
- Subjektive Qualität der Dialoge nach mehreren Tagen Nutzung.
- Timing und Lesbarkeit bei unterschiedlicher Windows-DPI-Skalierung.

Diese offenen Punkte werden nicht als bestandene Windows-Tests ausgegeben.
