# Aiko Desktop Pet v0.11 – Tamagotchi-Kern

## Rolle und Abgrenzung

Aiko ist die Personifizierung des Computers, **keine** Figur mit Academy- oder
Character-Chronicles-Tagesplan. Die Uhrzeit, die echte Nutzung und ihr
adaptiver Rhythmus aus v0.9 bleiben erhalten. Computerarbeit ist für Aiko
eigene Anstrengung. Die Hardwarebezeichnungen werden **nicht** automatisch
Teil ihres gesprochenen Dialogs.

## Vier Bedürfnisse und eine Beziehung

| Wert | Zweck | Verlauf | Pflege |
| --- | --- | --- | --- |
| Sättigung | Nahrung, kurzlebiges Bedürfnis | sinkt im Wachzustand und etwas im Schlaf | Füttern (+27) |
| Laune | momentanes Wohlbefinden | Tagesphase, soziale Unterversorgung und Arbeit | Spielen (+23), Streicheln (+9), Reden (+5), Füttern (+3/+5) |
| Energie | momentane Wachheit | sinkt im Wachzustand, steigt beim Schlafen | Schlaf (+22 Punkte/Stunde), Energy Drink (+10 Punkte pro Klick) |
| Sozial | Wunsch nach Kontakt mit der Person am PC | sinkt bei längerem Alleinsein langsam; wenig im Schlaf | Reden (+26), Spielen (+18), Streicheln (+12); Füttern nur +1 |
| Freundschaft | Langfristige Beziehung zum User | **kein** regelmäßiger Abbau, kein Rechenlastfaktor | sinnvolle Versorgung über mehrere Tage, max. +7 Punkte/Tag |

Alle Werte liegen zwischen 0 und 100. **Freundschaft** erhält zusätzlich
einen sichtbaren Level 1–10, berechnet aus dem Wert; sie ist kein Bedarf,
der regelmäßig wieder aufgefüllt werden muss. Ein neuer Spielstand startet
mit 15 Punkten (Level 2); ältere Saves behalten ihre bisherigen drei Werte
und erhalten für die neuen Felder kompatible Defaults.

Die Aktionen sind in der Hover-Leiste und im Statusfenster verfügbar.
**Reden** ist eine explizite soziale Interaktion. Ein Energy Drink gibt
**genau zehn Prozentpunkte Energie**, auch mehrfach direkt hintereinander,
bis maximal 100. Schlafen bleibt erhalten. „Spielen“ verbraucht weiterhin
Energie (-9) und Sättigung (-4). Reden benötigt minimal Energie (-1).

## Was die Rechnerlast macht

Die vorhandene Schätzung `workload_intensity()` bewertet vor allem aktive
CPU-/GPU-Nutzung; belegter RAM trägt nur wenig als zusätzlicher Druck bei.
Wir interpretieren RAM-Belegung **nicht** als Beleg für tatsächliche Arbeit.

Während einer aktiven, bekannten Arbeitsphase verändert sich die normale
Versorgungsrate. Bei nahezu maximaler Last (Intensität 1,0) gilt im Wachzustand
ungefähr:

- Sättigungsabnahme: **1,95×** der jeweiligen Grundrate
- Laune: zusätzlich **-2,1 Punkte/Stunde**
- Energie: zusätzlich **-2,8 Punkte/Stunde**
- Sozial: nur leicht schneller, nicht mit Computerarbeit verwechseln

Die normalen, von Uhrzeit und Wochentag abhängigen Werte bleiben bestehen.
Für unbekannte Hardwarewerte (oder bei deaktivierter Rechnerbeobachtung)
gelten ausschließlich die Grundraten. Ein aktuelles Sample darf maximal
**30 Sekunden** rückwirkend beeinflussen. Nach dem Programmstart, nach einem
Ruhezustand oder über einen mehrstündigen Abstand werden keine ungemessenen
Laststunden erfunden. Im Schlaf wird trotz möglicher Telemetrie keine
Wachenergie verbraucht.

## Freundschaft und Verhalten

- Freundschaft wächst durch gepflegte Interaktionen, **nicht** durch eine
  starre Uhr, pure Uptime oder fortgesetzte Klickserien.
- Dieselbe Pflegeaktion vergibt höchstens einmal alle **12 Minuten** einen
  Freundschaftszuwachs. Insgesamt maximal **7 Punkte pro lokalem Kalendertag**.
  Wiederholte Pflege kann weiterhin Sättigung/Laune/Energie/Sozial verbessern.
- Bei geringer sozialer Versorgung ändert Aiko ihren Blick auf Kontakte:
  ihre Dialoge werden eher zurückhaltend, gelegentlich dankbar für Gesellschaft.
  Sie wird dadurch nicht alle paar Minuten aufdringlich: Spontane Hinweise
  auf fehlenden Kontakt kommen frühestens alle 20 Minuten.
- Bei wachsender Freundschaft kann sie vertrauter und trocken-frecher sein,
  zum Beispiel bei Klicks, einem Gespräch, beim Streicheln und der Rückkehr.
- Diese Effekte sind **situationsabhängig**: Müdigkeit, Gereiztheit und echte
  Rechenarbeit behalten Vorrang vor einer fröhlichen Freundschaftsreaktion.

## Speichern, Datenschutz, Kompatibilität

Alle neuen Werte und die kleinen Freigabe-Zeitstempel für Freundschaft
werden in der bestehenden `%LOCALAPPDATA%\AikoDesktopPet\state.json`
(`version: 1`) abgelegt. Es gibt keine zusätzliche Datenbank, Cloud oder
KI-API. Das adaptive Wochenprofil und die bestehende Fensterkapselung bleiben
unverändert. Rohe CPU-/GPU-/RAM-Zeitreihen, Programmnamen, Fenstertitel und
Tastatureingaben werden nicht in diesen Spielstand geschrieben.

## Grenzen dieser Ausbaustufe

Der Dialogkatalog wurde für **Reden**, **Energy Drink**, Sozialmangel und
hohe Vertrautheit erweitert. Für sämtliche Situationen gibt es weiterhin
nicht unbegrenzt neue Animationen: Wir verwenden die vorhandenen 73 Sprites.
Die fachliche Balance ist ein erster Entwurf. Insbesondere Langzeitpflege
auf echten Windows-Rechnern muss im Alltag beobachtet und ggf. nachjustiert
werden. Das automatische Windows-Auslesen der Auslastung ist in der
Linux-Testumgebung nicht direkt messbar.
