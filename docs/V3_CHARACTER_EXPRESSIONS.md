# V3: Idle, Mimik und durchgehendes Schwanken

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

## Zuständigkeiten

| Eigentümer | Aufgabe |
| --- | --- |
| `pet/emotions.py` | Bestehende kanonische Gefühlsberechnung; keine neue Stimmungsspeicherung. |
| `pet/animation/expression.py` | Ausdrucks-IDs, reine Zuordnung vorhandener Gefühle und ausdrücklich benannter Ereignisse. Keine Text-Sentimentanalyse. |
| `application/attention.py`, `IdleBehaviourProfile` | Ein vorbereiteter Zustandsabruf verteilt Idle-Verhalten und milde Grundmimik gemeinsam. |
| `Reaction`, `ReactionPlayer` | Optionale Mimik und ihr tatsächlicher Gesprächsabschnitt. Abbruch entwertet auch schon eingereihte alte Timer. |
| `desktop/animation_runtime.py` | Wählt zuerst Körperaktion, Bewegung und Blick. Die separate `ExpressionPlayback` darf ausschließlich eine passende frontale Ruhepose ersetzen. |
| `AmbientDirector` | Einzige Zeitbasis für Grundschwanken und Abstand zwischen Blinzlern. Mimik startet keinen zweiten Idle-Takt. |
| `AnimatedPet`, `RestPoseRenderer` | Zeichnen vorbereitete Frames und das pose-relative Schwanken. Kein eigener Gefühlsentscheid. |
| `infrastructure/expression_assets.py`, `BodyPoseCache` | Laden/prüfen das separate Paket und halten die gebackenen Tk-Bilder vor. Keine Pillow-Laufzeitabhängigkeit. |

## Verwendung

| Semantik | Clip | Grundstimmung / konkrete Reaktion |
| --- | --- | --- |
| Neutral gelassen | `rest-neutral` | Ruhige neutrale Basis; vorhandene gezeichnete Augenphasen. |
| Positiv zugewandt | `expression-positive` | Positive Gefühle, spielerische Mausreaktionen, passende Quizreaktionen; Witzreaktion erst nach vollständigem Inhalt. |
| Aufmerksam/fragend | `expression-questioning` | Spielerisches erstes Interesse, Faktinhalt, Spielgleichstand und Nachdenken. |
| Unsicher/besorgt | `expression-worried` | Angespannte/vorsichtige Grundstimmung, Mauswarnung/Angst und unterstützende Quizreaktionen. |
| Bedrückt/enttäuscht | `expression-downcast` | Niedergeschlagenheit/Einsamkeit, verlorene kompetitive Spielrunde aus Aikos Perspektive. Müdigkeit allein ist keine Traurigkeit. |
| Genervt/bestimmt | `expression-firm` | Gereiztheit/Bedrängnis und vorhandene wiederholte Stör-/Schlafklickreaktionen. |

Die bestehenden Freudenhüpfer bleiben an ihren bisherigen Erfolgsanlässen
erhalten. Mastermind und Quiz unterscheiden Aikos Gastgeberrolle von einer
kompetitiven Niederlage. Die Hände-zusammen-Bittepose bleibt eine eigene,
begründete Körpergeste; sie wird nicht global durch den fragenden Kopf ersetzt.
Ebenso bleiben Essen, Buchhalten, Schlafen und andere echte Körperaktionen
eigenständig. Alte `review`-/`failed`-IDs werden nicht global umgedeutet.

## Vorrang und Lebensdauer

1. Körperaktion, Bewegung und tatsächliche Blickführung zuerst auswählen.
2. Nur bei kompatibler frontaler Ruhepose die aktuelle Mimik darstellen.
3. Eine kurze Reaktion durchläuft einmal ihre acht abgenommenen Phasen;
   verspätete Callbacks überspringen keine ungesehenen Phasen.
4. Ein Seitenblick oder eine echte Aktion verwirft sie sofort. Eine schon bei
   Anforderung unpassende Reaktion wird ebenfalls verworfen. Keine Warteschlange,
   kein erzwungenes Frontalstellen und kein späteres Nachholen.
5. Bei Rückkehr zur Ruhe erscheint die zuletzt vorbereitete Grundstimmung in
   einer milden Phase. Die starke Reaktion wird nicht erneut abgespielt.

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

Für die milde Grundmimik gibt es noch keine gesonderten geschlossenen Augen.
Ihr Blink verwendet deshalb kurz den abgenommenen neutralen Kopf und kehrt
danach zur aktuellen milden Mimik zurück. Keine erfundenen Zwischenbilder oder
Gesichtspatches auf älteren Köpfen.

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

Gezielte Tests: `test_expression_assets`, `test_expression_playback`,
`test_expression_reactions`, `test_ambient_director`,
`test_desktop_animation_runtime`, `test_reaction_playback`,
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
