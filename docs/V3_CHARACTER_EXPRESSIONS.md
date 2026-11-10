# V3: Idle, Mimik und durchgehendes Schwanken

Nachtrag 10.11.2026: Die Raum-/iPad-Fassung leitet verbliebene historische
Sprechgesten auf die vorhandenen V3-Ausdrücke um und gibt nach Spielreaktionen
wieder den Idle-Kanal frei. Kopf-/Körperbilder bleiben unverändert.
Siehe [V3-Kommunikationsmimik im Raum](ROOM_V3_COMMUNICATION.md).

Nachtrag 03.11.2026: Die Halskontur wird vollständig aus dem passenden
vorhandenen Kopf geführt. Die Halsfläche des Körpers überdeckt sie nicht mehr;
Kragen und Kleidung bleiben davor. Das betrifft 84 bestehende Bilder:
16 frontale Blicke, 18 Dreiviertel-Stehbilder und 50 Geh-/Kopfachsenkombinationen.
Kopfposition und Größe, Körper außerhalb X165..230/Y233..258, Fußanker und
Taktung bleiben erhalten. Die acht HD-Idle-Slots verwenden unabhängig davon
die abgenommenen neutralen Augenphasen. Ausdrucksbilder, volle Profile,
Drehbilder, Essen und 1X bleiben unverändert. Keine Neugenerierung.
Details: [lokale Halskorrekturen](HD_CHARACTER_SPRITES.md#local-neck-join-corrections-2026-11-03)
und [getrennter Idle-Export](HD_CHARACTER_SPRITES.md#current-neutral-idle-and-preserved-gaze-2026-11-02).

Stand: 28.10.2026. Der neue neutrale Idle samt Körper und fünf vollständige
Kopfbewegungen wurden nach der gezielten Neutral-Mundkorrektur visuell
abgenommen. Die Laufzeit übernimmt diese 48 abgenommenen Posen. Ausschließlich
der Alphakanal wird für die Windows-Freistellung binär exportiert; sämtliche
RGB-Bildpunkte und die privaten PNG-Originale bleiben unverändert.
Es wurden keine neuen Bilder generiert. Große Originale, Prompts und der
Vorschau-Job bleiben im übergeordneten privaten Projektordner.

Nachtrag 29.10.2026: Die [Grundstimmungs- und Sprechregeln](EMOTIONAL_BASE_AND_REACTIONS.md)
präzisieren inzwischen die Gefühlsableitung und den Zeitpunkt der Mimik bei
allen sechs Spielen. Freundliche Langzeitgefühle halten keine permanente
positive Ruhepose mehr.

Präzisierung 02.11.2026: Die fünf Ausdrucksclips sind kurze
Kommunikationsanimationen, keine zustandsabhängigen Dauer-Idle-Posen. Die
bisherige Verwendung von Frame 01 als feste Grundmimik entfällt für alle
Gefühlslagen. Die neutrale Basis samt Blinzeln ist nur ein Baustein des
[vollständigen Idle-Verhaltens](IDLE_V3_BEHAVIOUR_PLAN.md).

Die verbleibenden 94 Dialogvarianten mit `review` oder `failed` sind ebenfalls
auf `idle` plus einen ausdrücklich hinterlegten V3-Kommunikationsausdruck
umgestellt: 31 fragende, 28 bestimmte, 20 besorgte und 15 positive Varianten.
Texte, IDs, Bedingungen, Gewichte, Pausen und Emoji-/Textfolgen bleiben
unverändert. Müdigkeit allein erzeugt keine Traurigkeit: schläfrige Antworten
verwenden fragende Aufmerksamkeit, wiederholte Störungen eine klare Grenze.

Das optionale Dialogfeld `expression` benennt die kurze Mimik unabhängig von
`animation`, das weiterhin eine echte Körperaktion beschreibt. Die Mimik
beginnt am ersten tatsächlichen Textabschnitt. Explizite Ereignisregeln und
ein gereizter Reaktionston haben Vorrang vor diesem redaktionellen Hinweis.
Die Dialogvalidierung weist die alten Aktionsnamen `review` und `failed`
zurück. Ihre Bilddateien bleiben als Herkunfts-/Exportbestand erhalten,
werden aber nicht mehr durch Produktionsaufrufe ausgewählt. Die stumme
`review`-Dauerpose bei Computerlast und der vorgezogene Arbeitsaktionsaufruf
entfallen; konkrete Arbeitskommentare nutzen ihren zugelassenen Sprechslot.

## Zuständigkeiten

| Eigentümer | Aufgabe |
| --- | --- |
| `pet/emotions.py` | Bestehende kanonische Gefühlsberechnung; keine neue Stimmungsspeicherung. |
| `pet/animation/expression.py` | Ausdrucks-IDs und ausdrücklich benannte Kommunikationsereignisse. Keine dauerhafte Zuordnung Gefühl → Ruhegesicht und keine Text-Sentimentanalyse. |
| `pet/mind/expression_policy.py` | Kurzer Kommunikationsausdruck aus Sprechereignis, belegtem Thema und Gesamtgefühl. |
| `application/attention.py`, `IdleBehaviourProfile` | Ein vorbereiteter Zustandsabruf beschreibt Blick-/Standpausen und Schrittbereitschaft. Er fordert keine Kommunikationsmimik an. |
| `Reaction`, `ReactionPlayer` | Optionale Mimik und ihr tatsächlicher Gesprächsabschnitt. Abbruch entwertet auch schon eingereihte alte Timer. |
| `desktop/animation_runtime.py` | Wählt zuerst Körperaktion, Bewegung und Blick. Die separate `ExpressionPlayback` darf ausschließlich eine passende frontale Ruhepose ersetzen. |
| `AmbientDirector` | Einzige Zeitbasis für Grundschwanken und Abstand zwischen Blinzlern. Mimik startet keinen zweiten Idle-Takt. |
| `AnimatedPet`, `RestPoseRenderer` | Zeichnen vorbereitete Frames und das pose-relative Schwanken. Kein eigener Gefühlsentscheid. |
| `infrastructure/expression_assets.py`, `BodyPoseCache` | Laden/prüfen das separate Paket und halten die gebackenen Tk-Bilder vor. Keine Pillow-Laufzeitabhängigkeit. |

## Verwendung

| Semantik | Clip | Grundstimmung / konkrete Reaktion |
| --- | --- | --- |
| Neutral gelassen | `rest-neutral` | Frontale Ruhe-/Blinkbasis innerhalb des Idle-Verhaltens; kein vollständiges Idle-Szenario. |
| Positiv zugewandt | `expression-positive` | Positive Äußerungen, spielerische Mausreaktionen, passende Quizreaktionen; Witzreaktion erst nach vollständigem Inhalt. |
| Aufmerksam/fragend | `expression-questioning` | Spielerisches erstes Interesse, Faktinhalt, Spielgleichstand und Nachdenken. |
| Unsicher/besorgt | `expression-worried` | Besorgte Äußerung, Mauswarnung/Angst und unterstützende Quizreaktionen. |
| Bedrückt/enttäuscht | `expression-downcast` | Äußerung aus Niedergeschlagenheit/Einsamkeit, verlorene kompetitive Spielrunde aus Aikos Perspektive. Müdigkeit allein ist keine Traurigkeit. |
| Genervt/bestimmt | `expression-firm` | Gereiztheit/Bedrängnis und vorhandene wiederholte Stör-/Schlafklickreaktionen. |

Die bestehenden Freudenhüpfer bleiben an ihren bisherigen Erfolgsanlässen
erhalten. Mastermind und Quiz unterscheiden Aikos Gastgeberrolle von einer
kompetitiven Niederlage. Die Hände-zusammen-Bittepose bleibt eine eigene,
begründete Körpergeste; sie wird nicht global durch den fragenden Kopf ersetzt.
Ebenso bleiben Essen, Buchhalten, Schlafen und andere echte Körperaktionen
eigenständig. Die entfernten `review`-/`failed`-Aufrufe werden nicht durch
eine globale Umdeutung ihrer alten PNGs ersetzt.

Idle umfasst weiterhin kontinuierliches Schwanken, Blinzeln, eigene
Kopfblickrichtungen, gelegentlichen Dreiviertelstand mit Umsehen und ein oder
zwei kleine Profil-Schritte samt anschließender Standpause. `AmbientDirector`,
`BodyOrientation` und der vorhandene Bewegungsweg führen diese Folgen aus.
Der Zustand beeinflusst ihre Häufigkeit, Ruhezeiten und Bewegungsbereitschaft;
er hält keinen Ausdrucksframe fest. Kleine eigene Ausflüge bleiben unkommentiert.

## Vorrang und Lebensdauer

1. Körperaktion, Bewegung und tatsächliche Blickführung zuerst auswählen.
2. Nur bei kompatibler frontaler Ruhepose die aktuelle Mimik darstellen.
3. Eine kurze Reaktion durchläuft einmal ihre acht abgenommenen Phasen;
   verspätete Callbacks überspringen keine ungesehenen Phasen.
4. Ein Seitenblick oder eine echte Aktion verwirft sie sofort. Eine schon bei
   Anforderung unpassende Reaktion wird ebenfalls verworfen. Keine Warteschlange,
   kein erzwungenes Frontalstellen und kein späteres Nachholen.
5. Nach Abschluss oder Abbruch übernimmt wieder die aktuell zulässige
   Idle-/Blick-/Körperfolge. Freie frontale Ruhe verwendet `rest-neutral/00`;
   kein Frame einer Kommunikationsanimation wird als Dauerpose gehalten.

Die Mimik verändert keine Aktionsdeadline und unterbricht keine Bewegung.
Nichtblockierende Mauskommentare bleiben nichtblockierend. Das Menü und die
bestehende Hover-Korrektur behalten ihre bisherigen Zuständigkeiten.

Die neuen Köpfe decken nicht alle seitlichen Blickrichtungen ab. Dort bleiben
die vorhandenen Blick-/Körperbausteine sichtbar. Die frühere Lauf-/Drehzeichnung
wird durch diese Integration nicht als vollständig auf den neuen Stil migriert
ausgegeben. Weitere passende Kopfachsen bleiben eine eigene Asset-Aufgabe.

## Blinzeln und Schwanken

Die gemeinsame Schwankphase läuft bei Unterbrechungen weiter. Geeignete Clips
kennzeichnen `rest_sway`; die Darstellung verschiebt Kopf/Schultern sanft und
lässt den Fußbereich unverändert. ±1 logischer Pixel entspricht ±2 Pixeln bei
2X. Die acht 420-ms-Phasen haben insgesamt 3,36 Sekunden. Ein Ausdruckswechsel,
Blinzeln oder Wiederkehren aus einem Seitenblick startet diese Phase nicht neu.
Schlaf und Fortbewegung zeichnen ihre eigenen Bewegungen.

Zwischen Blinzlern gilt weiterhin der bestehende Ambient-Abstand. Die langen
neutralen Haltezeiten der Vergleichsvorschau werden nicht zusätzlich vor jeden
Blink geschaltet: Die tatsächlich geschlossenen/halboffenen Phasen 02/03/04
dauern 70/100/80 ms. Kurze Mimikreaktionen verwenden ihre vollständigen
abgenommenen Zeiten und verschieben einen gleichzeitig fälligen Blink.

Ein Blink kehrt zum neutralen Ruheanker zurück. Eine zusätzlich gezeichnete,
dezente zustandsabhängige Ruhemimik ist bislang nicht vorhanden. Sie bleibt
eine getrennte Gestaltungsaufgabe; Phasen der abgenommenen Kommunikationsclips
werden dafür nicht automatisch wiederverwendet. Keine erfundenen Zwischenbilder
oder Gesichtspatches auf älteren Köpfen.

## Quellen, Export und Größen

`tools/character_expression_export.py` übernimmt ausschließlich einen vollständig
visuell abgenommenen Vorschau-Export. Vor dem Schreiben prüft es alle 48 Quellen,
Hashes, PNG-Abmessungen und Zeiten. Der Export setzt Alpha unter 128 auf 0 und
ab 128 auf 255. Tk/Windows entfernt den exakt magentafarbenen Fensterhintergrund;
teiltransparente Konturen würden sich damit mischen und magentafarbene Reste
erzeugen. Es findet keine Farbfilterung statt, auch türkise Haare bleiben
unverändert. Das Manifest führt Quell- und Exporthash getrennt.
Ziel ist `aiko_pet/assets/expressions/` mit separatem Manifest.
Die bisherigen Dateien unter `frames/`, `frames_2x/` und
`body_poses/` bleiben unverändert. Die 384×416-Bilder behalten ihren gemeinsamen
Fußanker (96,194 in logischen Koordinaten). 1X wird im Bildcache aus dem neuen
Paket abgeleitet; die alten 1X-Dateien werden nicht überschrieben.

Private Quelle relativ zum übergeordneten Projektordner:
`lokale-daten/asset-generierung/2026-10-28-v3-idle-und-kopfanimationen-vorschau/`.
Neutrale Anfangs-/Endphasen sind bytegleich. Der untere Körperbereich ab Y265
ist in allen 48 Bildern pixelgleich.

## Prüfung

Ablösung von `review`/`failed` am 02.11.2026: 151 gezielte Tests bestanden,
einschließlich der neuen Dialogfeld-Validierung, tatsächlichen Sprechzeitpunkte,
erhaltenen Grenzreaktionen und ohne stumme Voraktion zugelassenen Arbeitskommentare.
Ruff, striktes Mypy und Pyright sind grün. Die 94 Dialogänderungen wurden gegen
Git auf unveränderte Texte, Auswahlregeln, IDs und Beatfolgen geprüft.
Der vollständige Lauf ohne native Fenster erfasste 2.295 Tests mit 148
übersprungenen GUI-Fällen und einem unabhängigen Fehler im bestehenden
Start-Test (`test_entrypoints_env`: Test-Double ohne `local_social_content`).
Dieser Fehler wurde anschließend parallel korrigiert; die gezielte Nachprüfung
von `test_entrypoints_env` bestand alle acht Tests (0,168 Sekunden). In diesem
Auftrag wurde der Startbereich nicht verändert. Der ursprüngliche Gesamtlauf
bleibt als fehlgeschlagen protokolliert; ein erneuter Komplettlauf wurde nach
der gezielt nachgeprüften Korrektur nicht gestartet.
Private Prüflogs: `pruefung/2026-11-02-retired-reactions-tests.log` und `.json`
im oben genannten Vorschauordner.

Präzisierung geprüft am 02.11.2026: 133 gezielte Tests bestanden. Die
Regression durchläuft alle 17 Gefühlslagen mit neutralem Ruheanker, passenden
kurzen Sprechreaktionen und anschließend wieder möglichem eigenen Umsehen.
Bestehende Prüfungen sichern außerdem Blinkphasen, durchgehendes Schwanken,
Dreiviertelstand, kleine Schritte und Aktions-/Blickvorränge ab.
Die lokale Gesamtsuite ohne native Fenster erfasste 2.286 Tests ohne Fehler
(215,004 Sekunden); 147 GUI-Fälle wurden übersprungen. Dieser Lauf ersetzt
keine praktische Windows-Sichtprüfung. Bilder und Originale bleiben unverändert.

Gezielte Tests: `test_expression_assets`, `test_expression_playback`,
`test_expression_reactions`, `test_ambient_director`,
`test_desktop_animation_runtime`, `test_reaction_playback`,
`test_retired_character_reactions`, `test_active_time`,
`test_rock_paper_scissors_sequence` und bestehende Sprite-/Spiel-/Sozialtests.
Die Tk-Prüfung verwendet isolierte, unsichtbare Testfenster und verändert
weder Nutzerspielstand noch laufende Aiko. Praktische Sichtabnahme der neuen
Laufzeitübergänge bleibt getrennt von den automatisierten Prüfungen.

Abschlussprüfung am 28.10.2026 nach dem Alpha-Fix: 2.457 Tests bestanden
(lokale vollständige Windows-Suite, 425,823 Sekunden). Ruff, striktes Mypy und
Pyright sind grün. Alle 984 zuvor versionierten Assetdateien stimmen mit Git
überein. Für alle 48 neuen Frames wurden unveränderte RGB-Pixel gegenüber
der abgenommenen Vorschau, binäres Alpha sowie Quell-/Exporthashes geprüft.
Keine neue Generierung und kein Nutzerspielstand geändert. Codeänderungen
werden beim nächsten Aiko-Start geladen.
