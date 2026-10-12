# Aiko Desktop Pet v0.12 – Zuwendung und Freundschaft

## Zweck und Persönlichkeit

Aiko ist der personifizierte Rechner in Chibi-Form. Sie hat fünf kurzfristige
Bedürfnisse und eine dauerhafte Beziehung zu dem Menschen, der sie versorgt.
Es gibt keine Academy- oder Character-Chronicles-Alltagspflichten. Rechnerlast
ist ihre eigene Arbeit, aber **nicht automatisch fehlende Zuwendung**.

## Sechs Anzeigen, fünf Bedürfnisse

| Wert | Bedeutung | Hauptpflege | Verlauf |
| --- | --- | --- | --- |
| Sättigung | Hunger | Füttern | sinkt bei hoher Rechenarbeit schneller |
| Laune | momentanes Wohlbefinden | Spielen | reagiert auf Arbeit, Tageszeit und Unterversorgung |
| Energie | körperliche Wachheit | Schlafen / Energy Drink | sinkt bei Arbeit schneller; Schlaf regeneriert |
| Sozial | Gespräch und gemeinsame Aktivität | Reden | sinkt langsam, auch nachts geringfügig |
| **Zuwendung** | wahrgenommene Nähe, Geborgenheit und kleine Gesten | **Streicheln** | sinkt wach um 1,35 Punkte/h, im Schlaf um 0,25 Punkte/h |
| **Freundschaft** | langfristige Vertrautheit (Level 1–10) | hilfreiche, abwechslungsreiche Pflege | **kein** passiver Abbau |

Alle Werte liegen bei 0–100. Ein neues Spiel beginnt bei 75 Punkten pro
kurzfristigem Bedürfnis und 15 Freundschaft (Level 2). Alte Spielstände
behalten alle bisher gespeicherten Werte. Neu hinzugekommene Zuwendung
startet bei bestehenden Spielständen mit 75 Punkten.

## Pflege-Balance

| Aktion | Primärer Effekt | Weitere Effekte |
| --- | --- | --- |
| Füttern | +27 Sättigung | +3 Laune (Snack), +5 bei erster passender Mahlzeit; +1 Sozial |
| Spielen | +23 Laune | +12 Sozial, -9 Energie, -4 Sättigung (zu müde: keine Aktion) |
| Reden | +26 Sozial | +5 Laune, -1 Energie |
| Streicheln | **+25 Zuwendung** | +6 Laune, +2 Sozial, **kein Energiebonus** |
| Energy Drink | **+10 Energie** | beliebig wiederholbar bis 100; kein direkter Freundschaftsbonus |
| Schlafen | +22 Energie/h | toggle Schlafen/Wecken, normale Tages-/Nachtlogik |

Die normale Auslastungsregel aus v0.11 bleibt erhalten: Beobachtete
CPU-/GPU-Arbeit erhöht den Sättigungsverbrauch (bis etwa 1,95-fach),
verstärkt Launeverlust und Energieverbrauch. Zuwendung wird dadurch
**nicht** direkt schneller abgebaut; Sozial reagiert nur leicht.
Unbeobachtete Stunden werden niemals als Hochlast angenommen.

## Langsame Freundschaft statt Klick-Farming

Freundschaft ist keine weitere Versorgungsleiste. Sie wächst durch
angemessene Pflege nur dann, wenn der **primäre Bedürfniswert vor der
Aktion höchstens 80** betrug: Sättigung bei Füttern, Laune bei Spielen,
Sozial bei Reden, Zuwendung bei Streicheln. Pflege funktioniert immer
(sofern die Aktion ausführbar ist), auch wenn sie kein Vertrauen mehr gibt.

- Ein sinnvoller Pflegeschritt gibt typischerweise 0,9–1,0 Freundschaftspunkte.
- Eine erstmals an diesem Tag zusätzlich versorgte **andere** Bedürfnisart
  gibt einmalig +0,35 Punkte extra.
- Dieselbe Aktion bringt höchstens alle 12 Minuten erneut Freundschaft
  **und nur dann**, wenn das entsprechende Bedürfnis wieder unter der Schwelle ist.
- Höchstens **5,0 Punkte pro lokalem Tag**, niemals mehr als 100 insgesamt.
- Energy Drink und Schlafknopf steigern **nicht direkt** die Freundschaft.
- Ein Tag Pause und Hintergrundarbeit verringern die Freundschaft **nicht**.

Die bisherige Freundschaft und die alten historischen Belohnungszeitpunkte
bleiben beim Import erhalten. Die Tagesobergrenze wird für v0.12 angepasst;
damit wird kein bereits verdienter Freundschaftswert rückgängig gemacht.

## Auswirkungen auf Aikos Verhalten

- Bei wenig Sozialkontakt: Gesellschaft wird wichtig; eigene `social_low`-
  Dialoge bleiben mit längerer Wiederholungspause aktiv.
- Bei wenig Zuwendung: Sie wirkt zurückhaltender und kann eine kleine Geste
  vermissen; eigene Klick-/Streichelreaktionen, andere Texte als bei Sozialmangel.
- Bei hoher Zuwendung und gewachsener Freundschaft: Sie kann gelassener und
  leicht unbeholfen-freundlich auf Klicks reagieren.
- Hunger, Müdigkeit, Rechenarbeit, Gereiztheit und ihre tatsächliche Tageszeit
  behalten Vorrang. Sie muss nicht ständig etwas sagen.

v0.12 ergänzt 16 handgeschriebene Aussagen in vier Ereigniskategorien.
Die vorhandenen 73 Spriteframes, das Hover-Verhalten, die verschiebbare
Leiste und die zentrale Z-Order-Verwaltung bleiben erhalten.

## Datenschutz und technische Kompatibilität

Die neuen Werte `affection` und `care_types_today` stehen im bereits
vorhandenen JSON-Spielstand unter
`%LOCALAPPDATA%\AikoDesktopPet\state.json` (Schema `version: 1`).
Keine eigene Datenbank, keine KI-API, kein Kontozwang und keine zusätzliche
Laufzeitbibliothek. Es werden keine Rohdaten zu Apps, Tastatureingaben oder
Browserinhalten abgelegt. Die Balance ist eine erste, bewusst nachvollziehbare
Regelbasis und kann später nach Windows-Langzeittests feinjustiert werden.
