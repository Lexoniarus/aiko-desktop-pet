# Zustandsabhängige Idle-Abläufe und V3-Bausteine

Stand: 28.10.2026. **Umsetzung in sechs Commits beauftragt; in Arbeit.**
Der Folgeauftrag erlaubt den dokumentierten Codeumbau mit gezielten Prüfungen.
Keine Bildgenerierung, Assetinstallation oder Save-Migration; kein Push/Merge.
Die vorgeschlagenen Zeiten sind Startwerte für die spätere Sichtung.

## Ausgangspunkt und Geltung

Ausgangsbasis ist `32ac4c0` auf `feature/social-optimization`. Die vier lokalen
Commits `3f4a0ef`, `009fc90`, `e94186f` und `32ac4c0` haben die zuvor freigegebenen
Punkte 1–4 umgesetzt: seitliche Cursor-Standabsicht, kompatible Darstellung mit
Blickvorrang, eigene Körperblicke und erhaltene Standpause nach Idle-Schritten.
Sie sind die technische Grundlage dieses Plans, nicht bereits seine Umsetzung.
Ihr letzter vollständiger lokaler Prüflauf bestand aus 2.395 Tests; dies ist
kein Prüfergebnis für den hier erst geplanten Umbau.

Aktuell wählt `AmbientDirector` etwa jedes dritte eigene Umsehen mit Körper
und etwa jeden zweiten kleinen Ausflug mit drei bis sechs Sekunden
Dreiviertel-Stand. Diese Auswahl hängt noch nicht von allen unten beschriebenen
Zuständen ab. `AttentionCoordinator.select_idle_animation()` wählt weiterhin
zufällig `waiting`, `review` oder `idle`; diese bisher ausgeklammerte Auswahl
soll mit dem nun geplanten Umbau fachlich passend werden.

Dieser Plan präzisiert den nächsten Idle-Umbau. Bestehende aktive Cursor-,
World-, Schlaf-, Pflege- und Spielverträge behalten ihren Vorrang. Aktuelle
Darstellung: [Körperausrichtung](IDLE_BODY_ORIENTATION.md). Cursoraufmerksamkeit:
[Stufen und Gefühle](CURSOR_ATTENTION_STAGES_PLAN.md). Architektur und Eigentümer:
[Architecture](ARCHITECTURE.md).

## Zielbild

Frontal bleibt Aikos Grundhaltung. Dreiviertel links und rechts sind zusätzlich
eigenständige Ruhehaltungen: Aiko darf dort eine Weile stehen, hoch, seitlich
und herunter schauen und aus derselben Orientierung einen kleinen Ortswechsel
entwickeln. Nach dem Schritt kann sie wieder in Dreiviertel derselben Richtung
verweilen. Die Rückkehr zur Front ergibt sich aus dem Ende der Folge, einem
passenden neuen Anlass oder notwendiger Kopffreiheit.

Ein Beispiel für eine zusammenhängende Folge:

1. Frontal ruhen und blinzeln.
2. Nach links in Dreiviertel ausrichten und die Standpose erreichen.
3. Mit Pausen ein oder zwei passende Kopfblickrichtungen wählen.
4. Bei zulässiger eigener Schrittgelegenheit ins linke Profil drehen.
5. Einen, gelegentlich zwei kleine Schritte nach links gehen.
6. Vom Profil zur linken Dreiviertelhaltung zurückdrehen und dort ruhen.
7. Später frontal werden; eine Ausrichtung nach rechts führt über die Mitte.

Die Folge darf nach dem Umsehen ohne Schritt enden. Jede Gelegenheit wird
einmal ausgewählt und fortgeführt; ein Renderaufruf würfelt sie nicht neu aus.
Eigene kleine Ausflüge erzeugen keine Sprachkommentare, Care-Gutschrift,
Freundschaftsänderung oder Maus-Moodlets.

## Zustände und konkrete Abläufe

Die Zustände beschreiben Varianten des vorhandenen Zustandsmodells. Sie sind
keine neuen Bedürfnisse oder persistierten Gefühlswerte. Ein Kontakt- oder
Versorgungswunsch ist ein zusätzlicher Anlass, kein zweiter emotionaler Zustand.

| Zustand | Grundlage aus vorhandenen Werten | Geplante Folge | Bewegungs- und Ruhecharakter |
| --- | --- | --- | --- |
| Ausgeglichen und entspannt | Vorhandene Gesamtgefühlslage, insbesondere `CALM`, `SATISFIED`, `CAREFREE`; ausreichende Energie | Frontal ruhen, gelegentlich Dreiviertel, dort kurz hoch/seitlich/herunter schauen, weiter stehen bleiben | Seitliche Ruhe zunächst etwa 6–10 s nach erreichter Pose; Schritt optional |
| Wach und unternehmungslustig | Ausreichende Energie und zur Aktivität passende Gefühlslage; geringer Spielspaß kann bei sonst passendem Zustand eine Gelegenheit begünstigen | Dreiviertel umsehen, ins Profil, ein oder zwei Schritte, wieder Dreiviertel derselben Seite, Ruhe | Etwas mehr eigene Orientierung und kleine Ausflüge innerhalb der vorhandenen Grenzen; kein normales Idle-Rennen |
| Müde, noch wach | Bestehende Energie-/Bedürfnisgrenzen, nicht allein ein trauriges Gefühl | Länger frontal oder dreiviertel stehen, gelegentlich ruhiger Kopfwechsel, frontal blinzeln | Weniger Schrittgelegenheiten, höchstens ein Schritt pro gewähltem Ausflug; vorhandene Mindestenergie bleibt wirksam |
| Gedrückt oder zurückgezogen | Vorhandene Gefühlslagen wie `SUBDUED`, `DOWNCAST`, `LONELY`, `RESERVED` | Ruhiger Stand, kurzer Blick nach unten oder zur Seite, längere Pause | Weniger Bewegung; passendes vorhandenes Emoji kann den Ausdruck tragen; kein automatisches Verbeugen |
| Angespannt oder gereizt | Vorhandene Gefühlslagen wie `TENSE`, `IRRITATED`, `CROWDED`, `FRUSTRATED` | Kurz orientieren, in einer Richtung stehen bleiben, gegebenenfalls ein kleiner Ortswechsel, wieder Ruhe | Kein hektisches Körperpendeln; Flucht verlangt weiterhin eine konkrete Bedrängungssituation und die bestehenden Grenzen |
| Konkreter Kontakt- oder Versorgungswunsch | Tatsächlich vorhandener, aktuell zulässiger Wunsch beziehungsweise bestehender konkreter Pflegeanlass | Seitliche Haltung verlassen, frontal ausrichten, einmal Frage-/Bitte-Geste, Hände senken, ruhen | Selten und anlassbezogen; Wunschidentität, Zulassung und vorhandene Ausdruckspausen beachten |

Für Müdigkeit, Zurückgezogenheit und Anspannung werden keine zusätzlichen
Sekundenwerte als bereits vereinbart ausgegeben. Die Umsetzung führt ihre
Häufigkeiten und Ruhezeiten in der bestehenden Balancequelle; sie bleiben
zunächst zurückhaltend und sind bei der Sichtung abzustimmen. Eigene
Blickgelegenheiten behalten als Ausgangswert 20–40 s, kleine Ausflüge 45–90 s.
Abweichungen müssen im Profil erkennbar sein und dürfen keine bewegte
Dauerschleife erzeugen.

### Gleichzeitige Zustände

- Schlaf, geschützte Aktionen und konkrete World-/Cursoraufmerksamkeit regeln
  zuerst, ob eine eigene Idle-Gelegenheit überhaupt frei ist.
- Bei freiem Idle begrenzt geringe Energie die Bewegungsbereitschaft, auch
  wenn Aiko zugleich zufrieden ist oder wenig Spielspaß hat.
- Die vorhandene `EmotionalComposition.primary` bestimmt die emotionale
  Variante. Der neue Plan berechnet keine konkurrierende Gefühlslage aus
  Einzel-Moodlets oder allein aus dem Zahlenwert der Stimmung.
- Ein echter Wunsch kann eine Frage-/Bitte-Geste zulassen. Die Geste erzeugt,
  erfüllt oder belohnt keinen Wunsch und bestätigt ihn nicht als gesprochen.
- Ein laufender ruhiger Abschnitt wird bei harmlosen Wertschwankungen nicht
  pro Frame neu gestartet. Neue Abschnittswahl liest den aktuellen Kontext;
  Schlaf, Bedienung, fehlende Bewegungszulassung und andere harte Vorränge
  unterbrechen unmittelbar.

## Vorhandene V3- und Übergangsbausteine

Versionszuordnung anhand der aktuellen Herkunftsmanifeste und
[HD-Dokumentation](HD_CHARACTER_SPRITES.md), nicht anhand alter Clipnamen.
Die jüngeren Körper-/Kopfmontagen sind eine wiederverwendete V3-Basis; eine
Montage ist kein zusätzliches natives Ganzfigur-HD-Original.

| Sichtbare Bedeutung / vorläufiger semantischer Name | Bestehende technische Quelle | Stand | Geplanter Einsatz |
| --- | --- | --- | --- |
| Ruhestand / `rest` | `idle` | Modulare V3-Fassung im regulären 2X-Satz | Frontaler Ruheanker und vorhandene Blinkfolge |
| Frontal umsehen / `look_around` | `look/00..15` | 16 modulare V3-Blicke im 2X-Satz | Alle frontalen Kopfsektoren; nachfolgende Körperabsicht separat |
| Seitlich stehen und umsehen / `side_rest` | `body-look-left/right` | Installierte Standbasis mit V3-Kopfbausteinen | Länger getragene Dreiviertelhaltung, nur passende Kopfachsen |
| Ausrichten / `turn` | `body-turn-*`, `body-orient-*` | Vorhandene installierte Drehbausteine | Frontal, Dreiviertel und Profil verbinden; Drehung verschiebt nicht selbst das Fenster |
| Kleiner Ortswechsel / `small_step` | `body-step-left/right-profil` und Kopfvarianten | Vorhandene installierte Profil-Schrittbausteine | Ein oder zwei Schritte; fünf passende Kopfachsen und volles Profil je Seite |
| Fragen/bitten / `question_request` | `waiting` | Vollständige V3-Geste im 2X-Satz | Einmal frontal bei einem tatsächlichen passenden Anlass |
| Kopf fragend neigen / `head_tilt` | `review` | Älterer HD-Bestand | Möglicher gezielter Übergangsbaustein; keine zufällige normale Idle-Zutat |
| Oberkörper/Kopf senken, verbeugen | `failed` | Älterer HD-Bestand | Exakten sozialen Anlass separat bestimmen; kein pauschales Müdigkeits-/Traurigkeits-Idle |
| Rennen / `run` | `running-left/right` | Ältere echte Rennanimation | Bestehende längere Ortswege mit passenden Kopf-/Bewegungsbedingungen; kein zufälliges Idle-Rennen |
| Freudenhüpfer | `jumping` | Älterer Bestand | Bestehende Freude-Auslöser erhalten; kein zufälliges Ruheverhalten |

Die normale Idle-Grundfolge benötigt `review` und `failed` nicht. Vorhandene
explizite Einsätze außerhalb des generischen Idle werden vor einer Änderung
vollständig nachverfolgt und nicht durch Umbenennung stillschweigend ersetzt.
Die Bedeutungszuordnung von Kopfneigen und Verbeugen ist kein Auftrag, neue
soziale Auslöser zu erfinden. Schlaf und Essen bleiben eigene Vorgänge mit
ihren vorhandenen Quellen und Zuständigkeiten.

### Maßstäbe und noch nicht verfügbare Kombinationen

- Die regulären V3-Neufassungen von `idle`, `look`, `waiting` und `eat` liegen
  im 2X-Satz. Die regulären 1X-Bilder sind weiterhin der ältere Satz. Das
  separate Körperpaket wird für 1X durch Tk-Subsampling dargestellt.
- Der Plan erzeugt keinen neuen vollständigen 1X-V3-Skin. Für jede semantische
  Handlung bleibt die tatsächlich geladene Größen-/Assetfähigkeit maßgeblich.
- Frontales Blinzeln ist vorhanden. Eine seitliche Blinkfolge ist im
  installierten Körperpaket nicht ausgewiesen. Lange Seitenphasen werden nicht
  ständig allein für einen Blinktermin frontal unterbrochen. Fehlende
  Augenvarianten sind ein später zu prüfender Bedarf, keine Freigabe zur
  Produktion oder zur ungeprüften Verwendung frontaler Augen auf Seitenköpfen.
- Das kurze V3-Lächeln ist weiterhin eine separate, nicht für die Laufzeit
  freigegebene Vorschau. Es wird nicht als verfügbarer positiver Idle-Ausdruck
  eingeplant. Die vorhandenen Freude-Auslöser behalten ihren Freudenhüpfer.
- Die Frage-/Bitte-Geste ist frontal. Es gibt damit noch keine belegte passende
  Dreiviertel-Handgeste. Vor ihrer Ausführung muss Aiko frontal ausgerichtet sein.
- Fehlt ein optionaler Körper-/Schrittbaustein, bleibt eine passende frontale
  Ruhe-/Blickfolge. Es gibt keine stille Ersetzung eines kleinen Schritts
  durch Rennen oder eine zurückgewiesene private Gehstudie.

Semantische Namen sind Planbegriffe. Zunächst ordnet eine kleine zentrale
Zuordnung sie den vorhandenen Clip-IDs zu. PNG-Dateien, Manifestversionen,
gespeicherte Werte und sämtliche Aktionsnamen werden nicht pauschal umbenannt.
Ein später ausgetauschter Clip kann dieselbe sichtbare Handlung weiterhin
erfüllen. Herkunft und Freigabestatus bleiben davon getrennt.

## Module, OOP-Aufbau und Datenfluss

| Eigentümer | Existierende Aufgabe | Geplanter Umbau |
| --- | --- | --- |
| `application/read_snapshot.py::snapshot_pet`, `pet/emotions.py`, `pet/wishes.py` | Kanonischer Zustandslesestand, Gesamtgefühl, echte Wünsche und deren Grenzen | Bestehende Werte und reine Zulassungsregeln wiederverwenden; keine neuen Gefühlsskalen oder Wish-Schreibwege |
| Neu: `pet/animation/idle_behaviour.py` | Noch kein Modul | Kleine reine Profilregel mit unveränderlichen Werten `IdleBehaviourContext` und `IdleBehaviourProfile`; keine Uhr, kein Timer, kein `PetState`, keine Desktopkoordinaten oder eigene Episode |
| `application/attention.py::AttentionCoordinator` | Aufmerksamkeits-/Ausdrucksfristen, Wunschkontext und Auswahl von Gesten | Lesestand in den kleinen Regelkontext abbilden; anlassbezogene Gesten auswählen; bisherige Zufallsauswahl ablösen |
| `desktop/attention_runtime.py::DesktopAttentionRuntime` | Anwendungsentscheidung unter aktuellen Desktop-Sperren präsentieren | Einmal im bestehenden Haupttick den aktuellen unveränderlichen Idle-Lesestand/Profileingang vorbereiten; Gestenausgabe gegen Vordergrund, Menü, Blase und Aktionen zulassen |
| `pet/animation/ambient.py::AmbientDirector` | Eine laufende passive Blick-/Standfolge samt Blink-/Schwankrhythmus | Bestehende Folge um zustandsabhängige Auswahl, Halten, passende Kopfblicke und Ankunft ergänzen; keine zweite Idle-Engine |
| `pet/animation/body_orientation.py::BodyOrientation`, `gaze.py` | Tatsächliche Körperphase, kompatible Kopfsektoren und gemeinsame Richtungsgrenzen | Profil-/Dreiviertel-/Frontübergänge und erreichte Standpose ausführen; Haltung nicht allein wegen eines neuen Zufallsticks zurücksetzen |
| `pet/movement/random_walk.py::RandomWalkPlanner` | Zeitpunkt, Richtung und Umfang eigener Ausflüge | Profilabhängige Bereitschaft/Ruhe, höchstens ein oder zwei Schritte; gewählte eigene Standrichtung als Präferenz, reale Randgrenzen weiter beachten |
| `pet/movement/contracts.py::WalkConditions`, `controller.py::WalkController`, `desktop/walk_runtime.py::WalkDriver` | Ein gemeinsamer Bewegungsweg, Priorität, tatsächlicher Fortschritt und Desktopversatz | Dieselben unveränderlichen Profilgrenzen weiterreichen; bestehende Strecke, Zulassung, Abschluss und Budgets behalten |
| `desktop/animation_runtime.py::DesktopAnimationRuntime` | Aktions-/Bewegungs-/Blickpriorität und Verbindung der vorhandenen Besitzer | Profil an vorhandene Besitzer weiterreichen; Körperabsicht und tatsächliche Bewegungsabschlüsse passend anwenden; keine neue emotionale Entscheidung im Renderer |
| `desktop/animation_assembly.py`, bestehende Renderphase aus `desktop/runtime.py`, Verdrahtung in `gui.py` | Zusammensetzen und bestehender 140-ms-Haupttick | Kleine Ports verdrahten; Profilvorbereitung innerhalb der bestehenden Renderphase nach Lifecycle, World- und Cursorzulassung; kein zweiter Heartbeat oder zusätzliche Simulationsphase |
| `desktop/visual_observation.py`, `ui/pet_view/animated_pet.py` | Tatsächliche Sicht und Wiedergabe der vorhandenen Bilder | Gemeinsame Blick-/Körpergrenzen beibehalten; nur fertige Bilder darstellen; Framecallback verändert weder Gefühle noch Wünsche oder Pet-Zeit |
| `pet/animation/animation.py`, `desktop/attention_runtime.py`, `ui/pet_view/attention_presenter.py` | Passive Clipauswahl und Ausführen freigegebener Anzeigeeffekte | Semantische Gesten auf tatsächlich vorhandene Clips abbilden; Presenter bleibt ausführend; kein zufälliger Bedeutungswechsel aus einem Dateinamen |
| `data/balance.json`, `pet/balance_contract.py`, `pet/balance.py` | Kanonische Parameter samt Validierung | Profilzeiten/-häufigkeiten zentral ergänzen; vorhandene Energie-/Bedürfnisgrenzen nutzen und neue Zeitbereiche prüfen |

Der Datenfluss bleibt:

1. Der vorhandene Haupttick führt Lifecycle/Bedürfnisse/Wünsche fort und
   verarbeitet die bestehende World-/Cursorzulassung.
2. Vor der Charakterdarstellung liest die Anwendungsgrenze einen aktuellen
   unveränderlichen Kontext. Die reine Profilregel wählt daraus die
   Idle-Ausprägung; sie ändert keine Pet-Werte.
3. `AmbientDirector` erhält das Profil für neue eigene Abschnitte;
   `RandomWalkPlanner` liest dessen Bewegungsgrenzen am bestehenden
   Abreise-/Ruheentscheid. Beide erhalten denselben unveränderlichen Wert.
4. `BodyOrientation` führt die Haltung aus; `WalkController`/`WalkDriver`
   führen ausschließlich tatsächliche Ortsbewegung aus. Erreichte Standpose
   und tatsächlich beendeter Idle-Schritt melden an die vorhandene Folge zurück.
5. Zusätzliche Sprite-Framecallbacks lesen den letzten vorbereiteten Kontext
   und den aktuellen Darstellungs-/Bewegungsstand. Sie berechnen keine neue
   Moodlet-/Wunschqualifikation und führen keinen weiteren Haupttick aus.

Das Profil ist eine kurzlebige Lesesicht, kein zweiter Zustandsspeicher. Es gibt
keinen neuen IdleManager, keinen zweiten Schrittzähler und keinen zweiten
Schreiber für Fensterposition, Gefühle oder Care. Ein eigener Richtungswunsch
ist eine Präferenz am bestehenden Bewegungsplaner; Taskleistenrand und tatsächliche
Bewegungszulassung können ihn verwerfen. Die tatsächliche Richtung steuert dann
die vorhandene Dreh-/Schrittfolge.

### Anlassgebundene Frage-/Bitte-Geste

Die Auswahl liest echte aktive Wünsche und vorhandene Beschränkungen mit
derselben fachlichen Zulassung wie die bestehenden Wunschreaktionen. Eine
Animationsauswahl darf keinen Wunsch erzeugen oder einen unzulässigen Wunsch
anzeigen. Ein niedriger Bedürfniswert allein darf nicht heimlich einen neuen
konkreten Gegenstands- oder Kontaktwunsch erfinden.

Frontal ausrichten, genau eine vollständige Geste zeigen und danach wieder
ruhen. Der Desktop verwendet die Clipdauer aus dem bestehenden Katalog statt
die Acht-Phasen-Geste pauschal nach den bisherigen 1,6 s zu beenden. Zulassung
und tatsächlicher Start werden vor Ausführung nochmals gegen aktuelle Sperren
geprüft; abgebrochene Gesten werden nicht als alte Aufgabe nachgeholt.

Die Geste markiert keinen Wunsch als erfüllt oder gesprochen. Vorhandene
Wunschtextquittungen bleiben an tatsächlich dargestelltem Text. Eigene
Wiederholungsgrenzen bleiben beim vorhandenen Aufmerksamkeitsbesitzer; es
entsteht keine zusätzliche Dialogwarteschlange. Emojis verwenden die vorhandene
Gefühls-/Bedürfnisableitung und übernehmen keinen Vordergrunddialog.

### Prioritäten und Erreichbarkeit

- Schlaf, Spiel, Pflege, Halten/Übergabe und gebundene World-Aktionen behalten
  ihre bisherigen Grenzen. Eine eigene Idle-Folge beansprucht keinen freien
  Slot, wenn ein geschützter Vorgang läuft.
- Ausgewähltes Maus-/Gegenstandsinteresse übernimmt das Blickziel. Eine
  passende Dreiviertelhaltung darf bleiben; ein unpassender Gegenblick nutzt
  sofort Front. Eigene Blickfolgen werden dabei nicht als alte Ziele aufgestaut.
- Hover öffnet weiterhin sofort das Menü und erhält aktive Mausverfolgung.
  Tatsächliche Bedienung/harter Zugang stoppt Bewegung wie bisher. Das
  Wiederöffnen eines Menüs liefert keinen neuen Neugier-/Angstbeleg.
- Freundschaft und Moodlets behalten ihre bestehenden fachlichen Besitzer.
  Ein gehaltenes Idle-Profil verlängert weder Neugier noch Angst und plant
  keine neue Flucht. Lauf- und Fluchtbudgets sowie Tempoauswahl bleiben erhalten.
- `auto_walk=False` verhindert eigene Ortswechsel, aber nicht ruhige Blicke
  oder Standdrehungen. Fehlende Energie und echte Bewegungsblockaden gelten
  auch nach einer bereits begonnenen Drehung.

## Geplante Commitfolge

Die Bezeichnungen IV3-1 bis IV3-6 gehören zu diesem neuen Plan. Sie sind nicht
die bereits abgeschlossenen Punkte 1–4. **Die Umsetzung dieser sechs Commits ist beauftragt.** Jeder Commit enthält seine Dokumentationsanpassung
und ausschließlich die betroffenen gezielten Tests; keine Gesamtsuite pro Stufe.

| Commit | Konkreter Umfang | Gezielte Tests und relevante Fälle |
| --- | --- | --- |
| IV3-1 — `feat(idle): derive immutable behaviour profiles from existing state` | Neue reine Regel `pet/animation/idle_behaviour.py`; Kontextabbildung aus bestehendem Lesestand in `application/attention.py`; nötige Balancefelder/-prüfung. Noch keine Darstellungsumschaltung. | Neu geplant: `test_idle_behaviour.py`. Außerdem relevante Fälle aus `test_emotional_reads.py`, `test_resource_validation.py`: Zustandskombinationen, Energiebegrenzung trotz positiver Stimmung, kein Aktivitätszwang bei wenig Spielspaß, unveränderter Pet-Lesestand, ungültige Profile/Zeiträume. |
| IV3-2 — `refactor(desktop): share one prepared idle profile across existing owners` | `DesktopAttentionRuntime`, `AnimationRuntimePorts`/Assembly, bestehende Renderphase und nötige minimale GUI-Verdrahtung; aktuelles Profil an Ambient- und Bewegungsgrenze weitergeben. Neutralprofil erhält zunächst das bisherige Verhalten. | `test_desktop_attention_runtime.py`, `test_desktop_animation_runtime.py`, `test_desktop_runtime.py`, `test_ui_architecture.py`, `test_final_architecture_audit.py`: Vorbereitung nach Lifecycle/World/Cursor vor Rendern, gleiche Profilversion für beide Besitzer, keine zusätzliche Policyauswertung oder Pet-Zeit im Framecallback, keine zweite Positionseigentümerschaft. |
| IV3-3 — `feat(idle): compose stateful resting and looking sequences` | `AmbientDirector`, `AmbientIntent`, `BodyOrientation`, `DesktopAnimationRuntime`: ruhige zustandsabhängige Abschnitte, länger getragene Dreiviertelhaltung, passende Kopfwechsel, gezielte Rückkehr/Unterbrechung; keine neue Bein-/Kopfmontage. | `test_ambient_director.py`, `test_body_orientation.py`, `test_desktop_animation_runtime.py`, passende Fälle in `test_animated_pet_isolation.py`: drei Ruheorientierungen, Haltezeit ab erreichter Pose, stabile Folge trotz harmloser Kontextänderung, harte Unterbrechung, kein Wiederaufleben alter Ziele, vorhandenes frontales Blinzeln/Schwanken, keine erfundenen seitlichen Augenphasen. |
| IV3-4 — `feat(idle): align short outings with state and resting orientation` | `RandomWalkPlanner`, `WalkConditions`, `WalkDriver` und bestehende Ankunftsanbindung: Bereitschaft/Ruhe nach Profil, eigene Seitenpräferenz, Profil vor Bewegung, ein/selten zwei Schritte, gleiche Dreiviertelseite nach Ankunft. Keine zweite Ablaufuhr für Abreisen. | `test_idle_steps.py`, `test_movement_requests.py`, `test_desktop_walk_runtime.py`, passende Tk-Fälle in `test_animated_pet_isolation.py`: beide Seiten/Größen, Taskleistenränder, geringe Energie, `auto_walk=False`, genau ein tatsächlicher Abschluss, kein Extraweg im Stand, Unterbrechung ohne Budgetreset, World-/Cursorabschlüsse erzeugen keine Idle-Ankunft. |
| IV3-5 — `refactor(idle): select grounded gestures through semantic clip mappings` | `AttentionCoordinator.select_idle_animation`, passive Auswahl in `animation.py`, `DesktopAttentionRuntime`, vorhandener Presenter/Katalogzugriff: Zufall aus `waiting/review/idle` ablösen; echte Bitte mit frontalem Ein-/Ausgang und vollständiger Clipdauer; technische IDs zentral zuordnen. Automatischer `failed`-Einsatz allein wegen schlechter Stimmung/Müdigkeit weicht dem Profil. Explizite Nicht-Idle-Aufrufer erst prüfen und erhalten. | `test_attention_policy.py`, `test_attention_decisions.py`, `test_desktop_attention_runtime.py`, `test_attention_presenter.py`, `test_wish_expression.py`, `test_pet_idle_emote_boundary.py`, `test_cursor_front_pose.py`, betroffene passive Auswahlfälle aus `test_motion_animation.py`: wirklicher zulässiger Anlass, freier Slot, keine pauschale Bitte/Verbeugung, vollständiger Einmalzyklus, keine Wunschtextquittung/Care durch Bilder, Abbruch ohne Nachspiel, ältere Clip-IDs und vorhandene Freude-/Renntrigger bleiben gültig. |
| IV3-6 — `test(idle): verify state transitions and complete local regression` | Verbleibende Integrationsfälle und endgültige Dokumentation; Herkunfts-/Maßstabsgrenzen ausdrücklich festhalten. Danach einmal die komplette lokale Prüfung. | Zuerst relevante Fälle in `test_cursor_behaviour_integration.py`, `test_cursor_menu_access.py`, `test_desktop_visual_observation.py`, `test_world_runtime_flow.py` und `test_animated_pet_isolation.py`: lange Folgen und Zustandswechsel, kein Bewegungspendeln, Hover/Bedienzugang, Gegenblick und echte World-Sicht, Style-/Größenfallback ohne fehlende Clips. Anschließend Gesamtsuite und vollständige statische Prüfungen. |

Vor jedem zukünftigen Commit: Status/Diff prüfen, fremde Arbeit erhalten, nur
die benannten Pfade aufnehmen und gezielte Tests sowie passende lokale
Lint-/Typprüfung ausführen. Neue Testmodule sind in der Tabelle ausdrücklich
als geplant gekennzeichnet. Vorhandene Tests werden bei geänderter Semantik
begründet angepasst; Grenzen für Blick, Pflege, Wünsche und Eingaben werden
nicht zur Bequemlichkeit abgeschwächt.

Der abschließende lokale Lauf entspricht den bestehenden Repository-Gates:

```powershell
.venv/Scripts/python.exe -m ruff check aiko_pet tests main.py tools
if ($LASTEXITCODE -ne 0) { throw 'Ruff fehlgeschlagen' }
.venv/Scripts/python.exe -m mypy --strict --no-incremental aiko_pet main.py tools
if ($LASTEXITCODE -ne 0) { throw 'Mypy fehlgeschlagen' }
.venv/Scripts/python.exe -m pyright --project pyrightconfig.json
if ($LASTEXITCODE -ne 0) { throw 'Pyright fehlgeschlagen' }
.venv/Scripts/python.exe -m unittest discover -s tests -q
if ($LASTEXITCODE -ne 0) { throw 'Gesamtsuite fehlgeschlagen' }
```

Bei der Ausführung muss jedes fehlgeschlagene Kommando die jeweilige Prüfphase
stoppen; ein späteres erfolgreiches Kommando macht einen früheren Fehler nicht
grün. GUI-Prüfungen verwenden isolierte Spielstände, kontrollierte Zeit und
beide Maßstäbe; der persönliche Spielstand und der laufende Nutzerprozess
werden nicht für Tests benutzt. Remote-CI gehört erst zu einem gesondert
freigegebenen Push; Merge bleibt separat freigabepflichtig.

## Abnahme und offene Bildarbeit

Praktisch zu sichten sind die Ruhe der Haltephasen, die erkennbare
Zustandsausprägung und die Übergänge zwischen aktuellem V3- und älterem Material.
Technisch grüne Tests ersetzen diese Sichtung nicht. Insbesondere bei 1X bleibt
die Version der regulären Altclips sichtbar zu berücksichtigen.

Vor einer Änderung expliziter `review`-/`failed`-Auslöser ist deren bestehende
Nutzung nachzuverfolgen. Ihre weiteren sozialen Bedeutungen, seitliche
Blinzelbilder, seitliche Handgesten und die Lächeln-Vorschau bleiben gesonderte
Diskussions-/Sichtungsaufgaben. Daraus folgt kein Generierungsauftrag und kein
pauschaler Ersatz aller älteren Frames. Für die normale Idle-Grundfolge werden
die vorhandenen Stand-, Blick-, Dreh- und Schrittbilder wiederverwendet.

Dokumentationsprüfung dieses Planungsauftrags ist getrennt von den erst später
auszuführenden Umsetzungstests. Private Originale und die gemeinsame
Assetkonzeption bleiben außerhalb Git; dort wird auf diesen Modulplan verwiesen.

## Umsetzung IV3

- IV3-1: Reine unveränderliche Profile und kanonischer Anwendungslesestand;
  körperliche Energiegrenzen gehen positiver Aktivitätsneigung vor.
- IV3-2: Ein unveraenderliches Profil wird in der bestehenden Renderphase
  nach Lifecycle/World/Cursor vorbereitet und an beide Besitzer weitergegeben.
  Framecallbacks berechnen es nicht neu; 60 gezielte Tests und scoped Mypy gruen.
- IV3-3: Stand-/Blickabschnitte halten das bei Beginn gewaehlte Profil;
  aktuelle Profile gelten erst fuer neue Abschnitte. Passende Hoch-/Runterblicke
  und ruhigere Blickabstaende sind vorhanden; 77 gezielte Pruefungen gruen.
