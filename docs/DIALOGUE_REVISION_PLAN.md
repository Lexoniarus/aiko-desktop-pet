# Deutsche Dialogüberarbeitung: Desktop-Aiko

Stand: 19. Oktober 2026. Grundlage ist die im Gespräch abgestimmte Stimme von
Desktop-Aiko. Dieser Plan betrifft die vorhandenen gesprochenen Texte, nicht
VN-Aiko oder eine Änderung des Verhaltenssystems.

## Umfang und Vorgehen

1. Alle 1.052 bisherigen Katalogfolgen als vollständige Aussagen prüfen.
2. Schwache Texte ersetzen und überlappende Varianten zusammenführen. Neue
   Abstufungen ersetzen bisherige allgemeine Varianten. Der Gesamtbestand
   wächst nicht. Gute Motive, etwa das Verkehrspolizistinnen-Bild, bleiben.
3. Die 119 vorhandenen Anlässe und 48 bestehenden Reden-Folgen beibehalten.
   Keine neuen Ereignisse, Auslöser, Messungen oder Verhaltensregeln einführen.
4. Den bestehenden JSON-Katalog und die gesprochenen Pflege-Fallbacks bearbeiten.
   UI-Beschriftungen und technische Statushinweise gehören nicht zu Aikos Stimme.
5. Vorhandene Auswahl-, Grammatik-, Ablauf- und Wiedergabetests ausführen.
   Zusätzlich die tatsächlich erreichbaren Zustandskombinationen und die
   eingesetzten Objektformen prüfen.

## Freundschaft und Stimme

| Stufe | Ausdruck | Beispiele für die Abstufung |
| --- | --- | --- |
| 1–2, `acquaintance` | Zurückhaltend, höflich, gelegentlich überrascht. Wünsche und Enttäuschung sind verhalten erkennbar. | Essen: überrascht bedanken. Niederlage: enttäuscht, aber gefasst; vorsichtig um eine weitere Runde bitten. |
| 3–5, `familiar` | Persönlicher, sichtbar erfreut, erste direkte Wünsche und kleine Beschwerden. | Aufmerksamkeit ausdrücklich genießen; eine Niederlage ärgerlich finden und Revanche wünschen. |
| 6–8, `friend` | Offen, ehrgeizig, neckisch. Sie möchte beeindrucken und kann ihre Enttäuschung schlechter verbergen. | Erfolge stolz teilen; beim Verlieren schmollen; Gesellschaft ausdrücklich wünschen. |
| 9–10, `close` | Vertraut, herzlich und unverstellt. Eigene Meinung, Trotz und Wünsche werden deutlich. | Zuneigung ohne anschließenden Rückzieher; offen Revanche verlangen; gemeinsame Zeit genießen. |

Leichter Kawaii-Chibi-Stil in allen Stufen: kurze gesprochene Sätze, sparsame
Ausrufe, gelegentlich „Hach“, „Hihi“ oder „Hmpf“. Keine Babysprache und kein
ständiges Selbstbeschreiben. Neugier zeigt sich durch Hinsehen und Nachfragen;
Stolz und Trotz durch konkrete Reaktionen. „Vorsichtig“ ist kein Grundmotiv.

Nicht jeder Anlass braucht vier sprachlich getrennte Fassungen. Wo die
Handlung dieselbe klare Aussage verlangt, bleiben Varianten gemeinsam nutzbar.
Bei vielen Objekt- und Arbeitsanlässen unterscheiden wir zunächst 1–5 und
6–10. Persönliche Pflege, gemeinsame Spiele, Begrüßung und Beziehungsgespräche
bekommen feinere Abstufungen. Die bestehenden Stufengrenzen bleiben unverändert.

## Zustand vor Ausdruck der Nähe

- Bedürfnisse kommen aus dem vorhandenen Kontext, bei Pflege vor der Wirkung
  der Aktion. Ein gefüllter Zuwendungswert ist keine Einladung zum Streicheln.
- Niedrige Freundschaft und gedeckte Zuwendung: Streicheln wird abgelehnt.
  Fehlende Zuwendung: zunächst dulden, mit wachsender Nähe zunehmend genießen.
- Bei Arbeit gilt dieselbe Unterscheidung. Zuwendungsmangel erhält ausdrücklich
  gefilterte Varianten für `pet_during_work` und `click_during_work`.
- Müdigkeit und Gereiztheit werden nicht durch ein freundschaftliches
  Standardkompliment übergangen. Hohe Nähe macht Wünsche offener, nicht jede
  Situation fröhlich. Hunger und Müdigkeit dürfen gleichzeitig vorkommen.
- Wiederholte Klicks bedeuten Ärgern. Verspieltheit verlängert die Geduld,
  die Folge endet trotzdem mit einer klaren Grenze.
- Spielen bei Müdigkeit und abgelehntes Spielen bleiben getrennte Anlässe.
  Ein angenommener kurzer Versuch ist keine Zusage für endlos weitere Runden.
- Aiko erlebt Rechnerarbeit als eigene Arbeit mit dem User: Anstrengung,
  Konzentration, Stolz und Erleichterung. Sie kommentiert nicht bloß Messkurven.
  Keine erfundenen Anwendungen, Tastatureingaben oder Mikrofonereignisse behaupten.
- Witze, Fakten und Nachrichten werden nicht als Ersatzinhalte in diese
  Dialoge geschrieben. Deren Beschaffung und zukünftige APIs bleiben separat.

## Objektablauf als zusammenhängende Folge

| Anlass | Eigene Information im Text |
| --- | --- |
| Entdecken | Da liegt etwas; noch kein unbekannter Objektname. |
| Hingehen | Abstand verringern, um besser hinsehen zu können. |
| Aufheben | Der Gegenstand kommt in ihre Hände. |
| Untersuchen | Was ist das? Anschauen oder Drehen statt die Neugier zu erklären. |
| Erkennen | Erst jetzt benennen; neuer Fund mit unbestimmtem Artikel. |
| Verwenden / aufheben / unbekannt | Absicht klar sagen. Allgemeine Anlässe nicht auf Essen festlegen. |
| Ablegen | Tatsächlich ablegen; die vorherige Entscheidung nicht erneut ausführen. |
| Bekanntes holen | Gegenstand und Grund fürs Holen verbinden. Essen und Getränk haben getrennte Anlässe. |
| Fehlen / Suchen | Fehlenden Gegenstand und Suchabsicht unterscheiden. Umplatzieren darf sie ärgern. |
| Wiederfinden | Subjektiv wiedergefundener Besitz, keine Änderung der bestehenden Zuordnung. |
| Wegnehmen / Rückgabe | Unterbrochene Absicht, Bitte um Rückgabe, Ärger bei weiterem Vorenthalten. |
| Beschäftigung unterbrechen | Beschäftigung beenden wollen; Suchkommentare müssen auch ohne verlorenen Vorrat passen. |

Varianten verschiedener Schritte werden unabhängig ausgewählt. Daher muss jede
Kombination in sich verständlich bleiben. Kein Satz setzt eine bestimmte
vorherige Variante voraus. Objektgrammatik verwendet die vorhandenen Artikel-,
Possessiv- und Pronomenfelder. Keine festen Apfel-Pronomen in allgemeinen Texten.
Ein Verdacht gegen den User wird als Frage formuliert, nicht als erfundene
Beobachtung. Erfolgloses Suchen nach einem vermissten Gegenstand und die
allgemeine Suche während einer Unterbrechung bleiben getrennt.

## Prüfung und Abgrenzung

Der Katalog bleibt die einzige Laufzeitquelle. Das bestehende
`DIALOGUE_REVIEW.md` bleibt als historischer Vergleich mit seinen bisherigen
Review-Zellen erhalten; es ist nach dieser Überarbeitung kein aktueller
Wortlautnachweis. Aktuelle Texte stehen in `aiko_pet/data/dialogues.de.json`.

Die Prüfung umfasst vollständige Folgen, grammatische Einsetzung aller
bekannten Objektnamen sowie unbekannter Gegenstände, Stufenabdeckung und
gezielte Auswahl bei mehreren Bedürfnissen. Die maximale Blasenlänge und
vorhandene Emote-/Pausenverträge gelten weiter. Automatische Prüfungen belegen
Katalog- und Auswahlkonsistenz; eine sprachliche Bewertung bleibt redaktionell.

## Umgesetzter Bestand

| Merkmal | Vorher | Nachher |
| --- | ---: | ---: |
| Katalogfolgen | 1.052 | 1.052 |
| Dialoganlässe | 119 | 119 |
| Reden-Folgen | 48 | 48 |
| Einzelne Textblasen | 1.302 | 1.196 |

Alle bisherigen Folgen wurden redaktionell geprüft. Drei bereits passende
Formulierungen zum Erkennen und erstmaligen Vermissen bleiben erhalten.
839 Folgen verwenden bestehende IDs; 213 entfallene Varianten werden durch
213 passend zugeordnete Varianten ersetzt. Es gibt keinen zusätzlichen
Laufzeitkatalog und keine neuen Dialoganlässe.

Die kürzeren Reaktionen verbinden die bisher auf zwei Blasen verteilten
Aussagen. Die 48 Reden-Folgen behalten jeweils vier Textblasen und ihre
Emote-/Pausenfolge. Die gesprochenen Pflege-Fallbacks wurden mitgeprüft;
der bereits passende Satz zur wiederholten Essenssorte bleibt erhalten.

Zusätzliche lokale Auswahlprüfungen bestätigen 6.912 Kombinationen aus
Freundschaft, Stimmung und Bedürfnissen sowie 48 tatsächlich geroutete
Streichelreaktionen vor der Pflegewirkung, jeweils mit und ohne Arbeit.
4.374 mögliche Kombinationen der sieben Grundschritte eines Objektablaufs
wurden auf vorhandene Folgen und fehlende vorzeitige Namensnennung geprüft.
Die Grammatikprüfung formatiert sämtliche Objektfolgen mit allen vorhandenen
Gegenständen und einer unbekannten Identität. Bekannte Namen, Artikel und
Pronomen bleiben an ihre vorhandenen Grammatikfelder gebunden.

Reaktionen ohne übergebenen Beziehungskontext haben weiterhin wenige
eigenständige Rückfalltexte. Bei übergebenem Kontext haben die passenden
Stufenvarianten Vorrang. Auch diese Rückfalltexte zählen zu den 1.052 Folgen.
Die Zuwendungs- oder Freundschaftswerte selbst, die Pflegeeffekte und die
Animationen der Aktionen wurden nicht verändert. Eine ablehnende Äußerung
ist daher noch keine neue mechanische Ablehnungsregel.

Abschlussprüfung: Alle **1.271 bestehenden Tests** bestanden; Ruff und
`git diff --check` ebenfalls erfolgreich. Alte wörtliche Texterwartungen in
fünf Testdateien wurden an die neue Fassung angepasst. Die Prüfungen der
Pflegeeffekte, Zustände, Objektgrammatik und vorhandenen Sprites bleiben erhalten.
Es wurden keine Python-Laufzeitmodule geändert.
