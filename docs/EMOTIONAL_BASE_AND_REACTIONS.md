# Grundstimmung, Moodlets und sichtbare Reaktionen

Stand: 29.10.2026. Diese Regeln ersetzen die frühere alleinige Mehrheit der
Moodlet-Stufen für die Gefühlsbezeichnung. Die numerische Stimmung bleibt
unverändert durch Bedürfnisse und begrenzte Moodlet-Punkte berechnet.

## Ein gemeinsames Gesamtgefühl

`pet/emotions.py` leitet zuerst die Grundstimmung aus dem vorhandenen
Stimmungswert ab: unter 40 gedämpft, ab 40 ruhig, ab 70 zufrieden.
Moodlets verändern danach die emotionale Färbung:

- Bei niedriger Grundstimmung können negative Ursachen erklären, ob Aiko
  beispielsweise frustriert, einsam oder gereizt ist. Positive Erinnerungen
  machen daraus keinen insgesamt fröhlichen oder zuversichtlichen Zustand.
- Bei ruhiger Grundstimmung ändern erst deutlichere Modifikatoren die
  Bezeichnung. Die Schwelle beträgt zwei gewichtete Intensitätsstufen.
- Bei guter Grundstimmung können passende positive Eindrücke Freude, Stolz,
  Zuversicht oder Zugewandtheit ausdrücken. Schwache gegenteilige Eindrücke
  ergeben ein gemischtes Gefühl; deutlichere negative Eindrücke können es
  beispielsweise als gereizt oder besorgt färben.
- Alle langfristigen Moodlets zusammen haben pro positiver beziehungsweise
  negativer Seite höchstens das Gewicht einer Intensitätsstufe. Ihre Anteile
  an den jeweiligen Richtungen bleiben proportional erhalten. Mehrere alte
  positive Langzeitboni können aktuelle Eindrücke nicht allein überstimmen.

Die Parameter stehen in `balance.json`, Abschnitt `emotions`. Alle 17
Gefühlslagen bleiben erreichbar. Es gibt keine zweite Stimmungszahl, keinen
zusätzlichen emotionalen Timer und keine Speicherformatänderung.

Beispiel ohne weitere aktuelle Ereignisse: Wertgeschätzt I, Zuversichtlich II
und Vertrauensvoll I ergeben bei Stimmung 35 ein gedämpftes, bei 55 ein ruhiges
und bei 85 ein zuversichtliches Gesamtgefühl. Die einzelnen Moodlets behalten
dabei ihre eigenen Namen, Stufen und Ursachen.

Die Originalepisoden, Rohintensitäten, Ursachen, Richtungen und bekannten
Zuschreibungen bleiben vollständig in `EmotionalComposition` erhalten.
Gesprächsthemen werden weiterhin aus diesen Belegen gewählt. Aiko kann sich
beispielsweise wertgeschätzt fühlen und darüber sprechen, obwohl ihre
momentane Grundstimmung gedämpft ist. Die passenden vorhandenen Textvarianten
berücksichtigen das gemeinsame Gesamtgefühl.

`PetMind`, Anwendungssnapshot, Status, Idle und Dialogkontext lesen dieselbe
reine Ableitung. Körperliche Bedürfnisse bleiben eigene Fakten; geringe
Energie allein wird nicht als Traurigkeit umbenannt.

## Mimik beim Sprechen und Spielen

Die Ruhepose bleibt bei Zufriedenheit, Zuversicht, Erleichterung und
Zugewandtheit neutral. Deutliche Freude, Unbeschwertheit und Stolz dürfen die
milde positive Grundmimik halten. Damit führen langfristige freundliche
Eindrücke nicht ständig zur gleichen Lächelpose.

`pet/mind/expression_policy.py` ordnet eine kurze Mimik dem tatsächlichen
Sprechereignis, ausgewählten belegten Thema und Gesamtgefühl zu. Eine
freundliche Äußerung kann ein kurzes Lächeln bekommen, ohne daraus eine
permanente Grundmimik oder neue positive Stimmung zu erzeugen. Es gibt keine
Sentimentanalyse des Textes und keine weiteren erfundenen Erfahrungen.

Bei allen sechs Spielen liefern die vorhandenen Sequenzen `express_event`
direkt beim Beginn der jeweiligen Äußerung. Auswahl eines späteren Satzes
oder eine vorgeschaltete Emoji-Phase starten die Mimik noch nicht. Abbruch
entwertet auch verspätete alte Callbacks.

| Anlass | Kurze Reaktion |
| --- | --- |
| Aiko verliert Schere–Stein–Papier, Tic-Tac-Toe, Blackjack oder Vier gewinnt | Enttäuscht |
| Aiko gewinnt ein kompetitives Spiel | Positiv; bisherige echte Freudenhüpfer bleiben erhalten |
| Unentschieden, Nachdenken, Begrüßung/Erklärung | Aufmerksam/fragend |
| Mastermind erfolgreich vom Spieler gelöst | Freude über dessen Erfolg, bisheriger Freudenhüpfer |
| Mastermind nicht gelöst | Besorgte/unterstützende Reaktion statt Freude über eine Niederlage |
| Quiz korrekt, ermutigender Zuspruch oder Abschluss | Positiv |
| Quiz falsche Antwort | Besorgt/unterstützend |

`event_expression` ist die gemeinsame semantische Zuordnung. Die Spielsequenz
bestimmt den Zeitpunkt, `GameSpeech` präsentiert, und der bestehende
Animationsbesitzer entscheidet über Zulässigkeit. Live-Spielereignisse sind
aus Spielersicht benannt; gespeicherte Spielursachen verwenden bereits Aikos
Perspektive. Die Gesprächszuordnung unterscheidet diese Verträge ausdrücklich.

Ein neutraler Idle-Aufruf am Ende der Sprechzeit schneidet die kurze Mimik
nicht ab. Eine neue Äußerung, Spielende, echte Körperaktion oder inkompatible
Blickhaltung darf sie weiterhin verdrängen. Blick-/Körpervorrang, keine
nachgeholten Reaktionen, Hover-Korrektur und durchgehendes Schwanken bleiben
wie in [V3-Charaktermimik](V3_CHARACTER_EXPRESSIONS.md) beschrieben.

## Prüfung und Umfang

Die Regression stellt den problematischen Zustand mit niedriger Stimmung und
drei positiven Langzeit-Moodlets nach, prüft alle 17 Gefühlslagen, gemeinsame
unverändernde Status-/Dialoglesungen, erhaltene Gesprächsthemen sowie die
Sprechzeitpunkte und Abbrüche aller sechs Spiele. Die vorhandenen Bilder und
privaten Originale werden nicht verändert; keine neue Generierung und keine
Änderung des Nutzerspielstands.

Abschluss am 29.10.2026: 2.467 Tests der vollständigen lokalen Windows-Suite
bestanden (384,434 Sekunden). Ruff, striktes Mypy über 371 Quelldateien und
Pyright sind grün. Alle 984 bisher versionierten Assetdateien und die 48
V3-Mimik-/Idle-Frames sind unverändert. Die neuen Regeln werden beim nächsten
Aiko-Start geladen.
