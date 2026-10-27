# Adaptive Mauswahrnehmung: Module, OOP-Verträge und Commitfolge

> **Nachfolgender Umbauplan, 27.10.2026:**
> [Idle, Mausinteresse, Moodlets und Menü-Erreichbarkeit](ADAPTIVE_CURSOR_REWORK_PLAN.md).
> Dieses Dokument bewahrt den ersten technischen Implementierungsverlauf.
> Dessen spätere vollständige CI ist auf `2ecca2f` grün, aber die praktische
> Verhaltenswirkung ist vom Nutzer ausdrücklich nicht abgenommen: Aiko führt
> Kopf und Körper noch zu hektisch nach. Die neue Konzeptfassung ersetzt die
> widersprechenden Zielregeln. Der neue Umbau ist inzwischen umgesetzt; seine
> technische Prüfung und noch offene praktische Abnahme stehen im neuen Plan.

Stand: 27.10.2026. Umsetzung auf `feature/social-optimization`, ausgehend von
`93f1c22`. Die Freigabe zur Umsetzung erfolgte nach diesem Plan; lokaler
Abschluss und verbleibende Abnahmen sind unten getrennt festgehalten.
Produktgrundlage: [Mauswahrnehmungs-Konzept](ADAPTIVE_CURSOR_CONCEPT.md).

## Umfang und Arbeitsweise

Aiko steht überwiegend frontal. Der Kopf reagiert zuerst; anhaltendes Interesse
auf einer Seite darf den Körper mitnehmen. Kleine Idle-Schritte, neugierige
Annäherung und Rückzug erhalten verschiedene Auslöser und denselben Ausführer.
Geschwindigkeit, körpernahe Entfernung und Annäherungsrichtung werden gemeinsam
bewertet. Eigene Aiko-Bewegung zählt nicht als Geschwindigkeit des Zeigers.

Zunächst neugierige Annäherung an einen ruhig bleibenden, erreichbaren Zeiger.
Längeres Hinterhergehen hinter einem bewegten Zeiger und autonomes Berühren
sind spätere Erweiterungen. Kurze Rückschritte und begrenzte Flucht gehören
zur geplanten Reaktion auf Nähe und schnelle Annäherung.

Die abgenommene Schrittvorschau liefert Bewegungsreferenzen. Ihre Strecke und
Taktung sind keine festgelegten Verhaltensschwellen. Vorhandene Quellen werden
wiederverwendet; kein Generierungsauftrag entsteht durch diesen Plan.

**Pro Commit ausschließlich die gezielten Tests seines Änderungsumfangs.
Gesamtsuite, globale statische Prüfungen und echte GitHub-CI erst im Abschluss.**
Keine Computer-Use-/UI-Fernsteuerung; praktische Sichtung übernimmt der Nutzer.
Die anschließende Umsetzungsfreigabe umfasst die lokale Commitfolge.
Push und PR bleiben dem unten beschriebenen Freigabeschritt vorbehalten;
ein Merge ist nicht beauftragt.

## Existierende Module, die angepasst werden müssen

Pfade in dieser Tabelle sind relativ zu `aiko_pet/`, soweit nicht anders benannt.
Die Tabelle benennt Verantwortlichkeiten, keine zusätzlichen Managerklassen.

| Existierendes Modul / Klasse | Konkreter Umbau | Zuständigkeit danach |
| --- | --- | --- |
| `pet/mind/cursor_attention.py` — `CursorAttention` | Fortlaufende Samplezeit, kurze Zeigerhistorie, geglättete Geschwindigkeit und ruhige Verweildauer ergänzen; Reset und Snapshot erweitern | Einziger Besitzer der Rohhistorie, ohne OS-Zugriff und Verhaltensentscheidung |
| `application/cursor_observation.py` — `CursorObservation` | Auch bei Stillstand ein Ergebnis liefern; aktuelle Figur-/Zeigergeometrie normieren; Bewegungsereignis für Kommentare separat ausweisen; Kontaktherkunft aus Eingabe-/Eigenbewegungsfakten zuordnen | Kopflose Aufbereitung von Wahrnehmung und Eingabeherkunft; kein Angstzustand, keine Fensterbewegung |
| `desktop/pointer_runtime.py` — `PointerRuntime` | Bestehendes Sampling in den erweiterten Observer führen; aktuellen unveränderlichen Snapshot bereitstellen; gleiche Daten an alle Leser geben | Native Eingabe mit dem einen Beobachtungsbesitzer verbinden; Kommentar-Callback weiterhin nur bei tatsächlicher Zeigerbewegung |
| `desktop/input.py` — `DesktopInput` | `Enter` über den gemeinsamen Herkunftscheck führen; direkte Klicks und F2 erhalten | Native Ereignisse übersetzen; keine eigene Neugier-/Angstlogik |
| `ui/windows/hover_ui.py` — `HoverUi` / `HoverUiPorts` | Beim Hover-Polling denselben Zulassungsport nutzen, sowohl vor Toolbaröffnung als auch vor `record_contact` | Fenster und Bedienzustand darstellen, ohne Eigenbewegung als Benutzerkontakt zu verbuchen |
| `pet/movement/contracts.py` | Unveränderliche Bewegungsaufträge, Quelle, Art und Abschlussgrund definieren; bisherige `WalkStep.animation`-Kopplung auflösen | Gemeinsamer Domain-Vertrag für Bewegung, unabhängig von Clipnamen und Tk |
| `pet/movement/controller.py` — `WalkController` | Genau einen Auftrag auswählen/ausführen; Aufträge quellenbezogen ersetzen und freigeben; Aufmerksamkeit nach zugelassenem Zweck behandeln; Richtung/Art/Fortschritt liefern | Einziger Besitzer aktiver Strecke, Subpixelreste und Ausführungsfortschritt |
| `pet/movement/random_walk.py` — `RandomWalkPlanner` | Seltene kurze Umpositionierung als Idle-Auftrag planen; bestehende Ruheplanung nutzen | Anlass und Timing eigener Idle-Ortswechsel, kein Cursorverhalten und kein neuer Timer |
| `desktop/walk_runtime.py` — `WalkDriver` | Aufträge in erreichbare Taskleistenziele übersetzen; World-/Cursor-Eingänge trennen; aktuelle harte Sperren vor jeder Ausführung prüfen; Abschluss zurückmelden | Native Geometrie und Anwendung des tatsächlichen Versatzes über den bisherigen `place_x`-Port |
| `desktop/world_runtime.py` — `DesktopWorldRuntime` | Zeiger-/Blicksnapshot für Wahrnehmung gemeinsam beziehen; zehn direkte `movement.set_goal()`-Aufrufer auf den World-Auftragseingang migrieren | World-Abläufe und ihre Zielvorgaben behalten; keine Maus- oder Idle-Ziele fremder Herkunft löschen |
| `desktop/world_access.py` — `WorldRuntimeAccess` | Kleine typisierte Lesesicht für aktuelle World-Bindung, Suche/Orientierung, Objektgeste und geschützte Phasen anbieten | Vorhandene Fakten weiterreichen; `focused()` allein genügt für Zulassung nicht |
| `desktop/visual_observation.py` — `DesktopVisualObservation` | Allgemeines Cursorinteresse aus der aktuellen Entscheidung statt pauschal vier Sekunden nach Bewegung beziehen; Objektverfolgung erhalten | Gemeinsame Blickgrundlage für Wahrnehmung und Darstellung, keine zweite Verhaltensentscheidung |
| `desktop/runtime.py` — `DesktopRuntime` / `DesktopTickPorts` | Benannte Phasen für Absicht vor World und Bewegungszulassung nach World verbinden | Reihenfolge und vorhandenen Heartbeat besitzen; keine Policy selbst berechnen |
| `desktop/animation_runtime.py` — `DesktopAnimationRuntime` | Zugelassene Bewegungsart/Richtung auf Clipdaten abbilden; Orientierungsbereitschaft vor Ortswechsel abwarten | Clip-/Darstellungspriorität und Zusammenspiel vorhandener Animationsbesitzer |
| `pet/animation/body_orientation.py` — `BodyOrientation` | Bestehende Orientierung um Profilbereitschaft für Fortbewegung und geordneten Standabschluss erweitern | Einziger Besitzer der körperlichen Ausrichtung und Drehphase; keine Weltposition |
| `pet/animation/character.py` — Clipdaten | Benötigte Bewegungs-/Kombinationsmetadaten als unveränderliche Daten ergänzen | Deklarative Zuordnung von Bewegungsart, Kopfvariante und Bildfolge |
| `infrastructure/body_pose_assets.py` und nötige Katalog-Anbindung | Optionales bestehendes Posenpaket für neue gültige Bewegungsdaten lesen/validieren; feste Vier-Clip-Annahme anpassen | Dateien und Metadaten validieren, keine Bewegungsentscheidung |
| `ui/pet_view/animated_pet.py` — `AnimatedPet` | Framecallback für deklarierte Bewegungsclips öffnen; Kopfwechsel vom Schrittfortschritt trennen; Abschluss an vorhandene Besitzer melden | Bilder, Framezeit und Weitergabe des gezeigten Fortschritts; kein eigenes Mausverhalten |
| `desktop/preferences.py` — `DesktopPreferences` | Bei deaktivierter Mausbeobachtung, deaktiviertem Auto-Walk oder Maßstabswechsel die betroffenen flüchtigen Besitzer und Cursoraufträge gezielt zurücksetzen | Bestehende Optionen auf die vorhandenen Besitzer anwenden; fremde World-Aufträge erhalten |
| `application/assembly.py`, `desktop/animation_assembly.py`, `gui.py` | Instanzen und Ports einmalig verdrahten, Tick-/Kontakt-/Reset-/Abschlusswege verbinden | Composition Root, keine ausgelagerte Verhaltenslogik in GUI-Lambdas |
| `data/balance.json`, `pet/balance_contract.py` | Erklärbare Parameter und deren bestehende Validierung erweitern | Eine kanonische Parameterquelle statt verstreuter Zahlen |
| `tools/character_body_pose_export.py`, `assets/body_poses/` | Vorhandene freigegebene Körper/Köpfe reproduzierbar als ganze Laufzeitbilder ausgeben | Vorhandene Asset-Pipeline erweitern; private HD-Originale bleiben außerhalb Git |

`ui/pet_view/body_pose_cache.py` wird nur angepasst, falls die konkrete
Bewegungsdatenzuordnung dies erfordert. Das aktuelle Cache-Grundprinzip bleibt.
Für den Export nötige gemeinsame Funktionen bleiben im bestehenden
`tools/character_export_common.py`; kein neuer paralleler Exporterrahmen.

## Genau zwei neue Produktionsmodule

| Geplantes neues Modul | Öffentliche Klasse / Werte | Alleinige Aufgabe |
| --- | --- | --- |
| `pet/mind/cursor_behaviour.py` | `CursorBehaviourPolicy`, unveränderlicher `CursorBehaviourContext` und `CursorIntent` | Wahrnehmung und kanonischen Zustand interpretieren: ignorieren, beobachten, annähern, Abstand nehmen oder fliehen; genau ein flüchtiger Neugier-/Schreck-/Erholungszustand |
| `application/cursor_behaviour.py` | `CursorBehaviourCoordinator`, kleine unveränderliche Zulassungs-/Aktivitätskontexte | Genau eine Policy koordinieren, die aktuelle Absicht teilen und mit bestehenden Interaktions-/World-Besitzern auf Zulässigkeit prüfen |

Dataclasses und kleine reine Berechnungsfunktionen liegen bei ihrem fachlichen
Besitzer. Daraus werden keine zusätzlichen Manager-, Service- oder eigenen
Modulhierarchien pro Reaktion. Neue Testmodule sind in der Commitliste separat
gekennzeichnet und keine neuen Produktionsbesitzer.

### Existierende Besitzer, die wiederverwendet werden

- `PetState` bleibt das einzige veränderliche Pet-Aggregat und liefert die
  kanonischen Bedürfnisse/Freundschaft. Keine neue gespeicherte Angstskala.
- `PetMind` behält seine eine `CursorAttention`-Instanz und vorhandene Dialogwahl.
  Die neue Policy wird nicht zusätzlich dort und im Coordinator konstruiert.
- `ObjectBehaviorCoordinator` und `ObjectInteractionCoordinator` behalten ihre
  World-Entscheidungen. Mausverhalten erhält keine Kopie dieser Regeln.
- `ContactCoordinator` bleibt Besitzer absichtlicher Kontakte. Sein bestehender
  Kontaktpfad wird erst nach der gemeinsamen Herkunftsprüfung aufgerufen.
- `AttentionCoordinator` behält Kommentare und spontane Dialoge. Weder
  Kommentarcooldown noch Zufallsziehung lösen Mausbewegung aus.
- `gaze.py` berechnet weiter Blicksektoren; `AmbientDirector` besitzt Blinzeln
  und kleine Ruhegesten; `FrameClock` besitzt die gezeigte Clipzeit.
- `DesktopWindow` bleibt der vorhandene Ort der tatsächlichen Fensterplatzierung.
  Weder neue Policy noch Coordinator schreiben `settings.x` oder Tk-Geometrie.

## OOP-Verträge und Zustand

Die folgenden Signaturen sind geplante Rollen, noch keine implementierte API.

| Besitzer | Geplante Schnittstelle | Zustand und Einschränkung |
| --- | --- | --- |
| `CursorAttention` | `observe(sample, now)`, `snapshot()`, `reset()` | Nur Rohhistorie, Zeitbasis und vorhandene Aufmerksamkeit; keine Kopie dieser Historie beim Renderer oder Coordinator |
| `CursorObservation` | `observe(sample, geometry, now) -> CursorObservationResult`; `classify_contact(input_facts, motion_facts) -> ContactOrigin` | Berechnet aus vorhandener Historie normierte Wahrnehmung und unterscheidet tatsächlichen Eintritt von Eigenbewegung; keine zusätzliche Historie |
| `CursorBehaviourPolicy` | `evaluate(perception, context, now) -> CursorIntent`; `note_motion_finished(receipt, now)`; `reset()` | Flüchtige Interpretation, Warte-/Erholungszeiten und begrenzte Versuche; keine Clipnamen, Fenster oder World-Befehle |
| `CursorBehaviourCoordinator` | `begin_frame(perception, context) -> CursorIntent`; `admit_motion(activity_context, now) -> CursorMotionIntent or None`; `gaze_intent`; `reset(reason)` | Besitzt genau eine Policy und deren aktuelle Ausgabe; `admit_motion` berechnet Neugier nicht erneut und würfelt keine zweite Entscheidung |
| `WalkDriver` | `set_world_goal(...)`, `submit_cursor_intent(...)`, `clear_cursor_request()`, `step(...)` | Geometrie übersetzen und den Controller benutzen; aktuelle harte Sperren auch zwischen Hauptticks lesen |
| `WalkController` | `replace_request(source, request)`, `release_request(source)`, `plan_step(conditions)`, `record_displacement(...)` | Ein aktiver Auftrag mit stabiler ID; Quellenfreigabe löscht keine fremde Absicht; kein Animationsclip als Domain-Entscheidung |
| `RandomWalkPlanner` | Vorhandene Abfahrts-/Ruheplanung um kurzen Idle-Auftrag erweitern | Ein bestehender Zeitplan; kein unabhängiger Timer im Renderer |
| `BodyOrientation` | Passive Blickausrichtung und angeforderte Bewegungsrichtung annehmen; `motion_ready` bereitstellen | Ein physischer Richtungs-/Drehzustand; Kopfwahl und Bewegung dürfen keine zweite Körperausrichtung speichern |
| `DesktopAnimationRuntime` | Vorhandene Auswahl-/Fortschrittsmethoden um Bewegungsergebnis erweitern | Verknüpft Orientierungsbereitschaft, Clipdaten und Driver; zeichnet nicht selbst |

Die rohe und normierte Wahrnehmung wird als unveränderlicher Domain-Wert bei
`pet/mind/cursor_attention.py` definiert, damit die reine Policy keine
Application- oder Desktop-Module importieren muss. Das Application-Ergebnis
kann zusätzlich ein getrenntes, optionales Kommentar-Bewegungsereignis enthalten.

### Lebenszyklus und Abhängigkeiten

`assemble_application()` konstruiert genau eine neue Policy und injiziert sie
in genau einen Coordinator. `CursorObservation` erhält weiterhin die bestehende
`mind.cursor_attention`. Die Desktop-Assembly erhält schmale typisierte Ports
auf Coordinator und vorhandene Besitzer, keine vollständige GUI als Kontext.

Ein Bewegungsauftrag behält seine ID über Frames hinweg. Wiederholtes Lesen
oder dieselbe Kopf-/Blickentscheidung startet weder Strecke noch Animation
neu. Abschluss, Randstopp oder Abbruch werden mit Quelle/ID an den zuständigen
Besitzer zurückgemeldet. Der Cursor-Coordinator gibt den Abschluss an seine
Policy weiter; daraus entsteht eine Ruhe-/Erholungsphase statt einer sofort
neu gestarteten Annäherung. Idle-Kommentare werden nicht automatisch für jede
Cursorbewegung wiederverwendet.

Abhängigkeiten laufen von Desktop/UI über Application zu reinen Pet-Modulen.
Die neuen Application-/Pet-Module importieren weder Tk noch `WalkDriver`,
`DesktopPet` oder native Eingabefunktionen. Abstrakte Kontextwerte/Ports werden
injiziert. Quellen für Cursorabsicht und World-Auftrag bleiben getrennt;
aktiver Ausführungsfortschritt und Positionsanwendung bleiben jeweils einmalig.

### Wahrnehmung und Entscheidung

Der Wahrnehmungswert enthält Position/Samplealter, gültige Zeitbasis,
geglättete Geschwindigkeit, körpernahe Entfernung, radiale Bewegungsrichtung,
ruhige Dauer, Größenmaßstab und Erreichbarkeit. Transparente Spriteränder sind
keine Körpernähe. Geschwindigkeit wird aus Zeigerverschiebung und realem
Zeitabstand berechnet; Aikos Eigenbewegung verändert nur ihre relative Geometrie.

Erstes Sample, lange Messpause, Reset und Maßstabswechsel erzeugen keinen
künstlichen Geschwindigkeitsschreck. Ruhige Mausphasen werden weiter bewertet;
Kommentare bleiben an tatsächliche Zeigerbewegung gebunden. Der derzeitige
140-ms-Haupttakt wird anhand kontrollierter Zeitreihen auf erkennbare Verläufe
geprüft. Eine vollständig zwischen Samples liegende Bewegung wird nicht
nachträglich erfunden. Eine erforderliche höhere Eingabekadenz gehört zum
bestehenden Input-/Pointer-Besitzer, nicht in World- oder Animationslogik.

Schnell und weit entfernt oder weggerichtet ist anders als schnell, nahe und
auf die Figur zu. Vertrauen beeinflusst Rückzug und Erholung graduell;
Bedürfnisse beeinflussen Interesse und verfügbare Bewegung. Keine automatische
Freundschaftsstrafe für gewöhnliche Mausarbeit und keine Fortschrittsbelohnung
für ruhenden Zeiger. Schwellwerte werden durch erklärbare Zeitreihen gewählt.

### Reihenfolge im bestehenden Update

```text
Lifecycle / erfolgreiche Bedienung aktualisieren
→ Eingabe erfassen und Wahrnehmung fortschreiben
→ Coordinator.begin_frame: Absicht und allgemeines Blickinteresse
→ World-Wahrnehmung / Angebot / neue Aktionsentscheidung
→ Coordinator.admit_motion: aktuelle Schutzlage erneut prüfen
→ Driver/Controller: einen Auftrag ausführen, falls orientiert und zulässig
→ Animationsruntime/Renderer: dazu passende Darstellung
→ bestehende Kommentare / Emotes / Wartung
```

Das gleiche Blickinteresse wird vor der Objektwahrnehmung und beim Zeichnen
verwendet. Objektfokus und verfolgte Mausgegenstände bleiben vorrangig.
`DesktopWorldRuntime._attention()` bekommt dafür dieselbe Eingabesicht statt
einer abweichenden zweiten Mausgeschichte. Bestehende native Abfragen für
Drag-Darstellung werden nicht pauschal umgebaut.

Die Zulassungsprüfung nach dem World-Update verhindert Bewegung nach einer
im selben Tick begonnenen Übergabe oder Konsumaktion. Harte Abbruchgründe
werden auch vor späteren Frame-Schritten neu gelesen. Eine neue World-Aktion,
Schlaf, Spiel, Bedienung oder abgeschaltete Option muss nicht auf den nächsten
140-ms-Tick warten. `WorldRuntimeAccess.focused()` allein bildet die benötigte
Schutzlage nicht vollständig ab; kleine explizite Lesesichten ersetzen kein
zweites Fokus-/Aktionssystem.

### Bewegung und Kontakt

World veröffentlicht seinen eigenen Auftrag über den Driver. Ein World-`Hold`
gibt diesen Auftrag frei; er löscht keinen Cursorauftrag. Der Controller wählt
unter bereits zugelassenen Aufträgen genau einen aus. Geschützte World-Abläufe
haben Vorrang; ein gewöhnlicher Idle-Weg kann einem zugelassenen Rückzug weichen.
Aktuell bestehen zehn produktive `movement.set_goal()`-Aufrufe in
`desktop/world_runtime.py`; diese Migration erfolgt vollständig zusammen.

Aufmerksamkeit darf gewöhnliches Wandern weiterhin anhalten. Eine ausdrücklich
zugelassene Annäherung darf nicht durch ihre eigene Mausaufmerksamkeit blockiert
werden. Dazu werden Quelle und Zulassung ausgewertet, statt `attention_active`
pauschal zu entfernen. Clipnamen werden aus Bewegungsart und Richtung in der
Animationsruntime ermittelt. Reine Bewegung bleibt unabhängig von Bilddateien.

`BodyOrientation` macht die vorhandenen Frontal-/Dreiviertel-/Profilübergänge
sichtbar und gibt Ortsbewegung erst bei passender Ausrichtung frei. Beim
Abschluss ist der Stand wieder stabil. Der Kopf kann wechseln, ohne diesen
Ablauf zurückzusetzen. Keine zusätzliche Step-Sequencer-Klasse oder neue Gehloop.
Eine noch nicht fertig abgenommene längere Gehschleife wird nicht vorausgesetzt.

Für Hover gibt es aktuell zwei Wege: `DesktopInput.initialize()` bindet
Tk-`Enter`; zusätzlich öffnet `HoverUi.refresh_hover()` die Toolbar und ruft
`record_contact()` auf. Beide Wege müssen dieselbe Herkunftsprüfung verwenden.
Eigenbewegung unter einen ruhigen Zeiger zählt nicht als Benutzerkontakt.
Tatsächliche frische Zeigerbewegung in die Figur ist Benutzerkontakt; bei
zusätzlicher eigener Figurbewegung behält der nachgewiesene Benutzerkontakt
Vorrang. Direkte Klicks und F2 bleiben absichtlich. Der Herkunftscheck läuft
vor `ContactCoordinator.enter()` und vor der Kontaktregistrierung im Polling;
kein alleiniger Fix am Tk-Binding. Eine sichtbare, unbenutzte Settings-Ansicht
unterbindet autonomes Verhalten nicht dauerhaft.

## Neue und bestehende Tests

Neue Testmodule sind geplant, nicht bereits vorhanden:
`test_cursor_behaviour_policy.py`, `test_movement_requests.py`,
`test_cursor_contact_origin.py`, `test_cursor_behaviour_coordinator.py`,
`test_cursor_behaviour_integration.py`, `test_idle_steps.py`.
Bestehende fachlich passende Tests werden erweitert. Tests gehören jeweils
mit der Produktion in denselben Commit. Keine erst am Schluss nachgelieferten
Unit- oder erforderlichen Integrationstests.

## Daraus abgeleitete Commitfolge

Die bisherigen Commits bleiben unverändert:
`d72176e` (Exporter), `11b8df8` (HD-Assets), `93f1c22` (Körperausrichtung).
Zum Planungsbeginn waren nur dieser Plan und der Konzeptverweis offen.
Die damals zwölf lokalen Commits gegenüber dem vorhandenen Remote-Tracking-Stand
enthalten auch getrennte parallele Arbeiten; sie werden weder neu gepackt
noch umgeschrieben.

In der Testspalte sind Modulnamen relativ zu `tests/` angegeben.
`Neu:` kennzeichnet erst mit diesem Commit zu erstellende Tests.

| Nr. / Commit | Betroffene Produktionsmodule und abgeschlossener Vertrag | Ausschließlich gezielte Tests dieses Commits |
| --- | --- | --- |
| 1 — `docs(cursor): define module ownership interfaces and commit sequence` | Dieser Plan plus Konzeptverweis; klare Zustände, Eingänge und Abhängigkeiten | Nur Dokumentverweise, existierende Modul-/Testpfade und Widerspruchsfreiheit; keine Laufzeittests |
| 2 — `feat(cursor): expose continuous motion and proximity snapshots` | `cursor_attention`, `cursor_observation`, `pointer_runtime`, nötige Daten-/Inputports: Stillstand und Bewegungsereignis getrennt, normierte Nähe/Geschwindigkeit/Richtung, Zeitbasis und Reset | `test_cursor_attention.py`, `test_cursor_observation.py`, `test_pointer_runtime.py`; neue Zeitreihenfälle dort für Stillstand, Jitter, Vorbeifahrt, Wegbewegung, Eigenbewegung,1X/2X und Samplinglücken |
| 3 — `feat(cursor): model curiosity threat and recovery` | Neues `pet/mind/cursor_behaviour.py`; `data/balance.json` und `balance_contract.py`: reine Policy, Absicht, Reaktionsabschluss und begrenzte Erholung, noch keine Aktivierung | Neu: `test_cursor_behaviour_policy.py`; gezielte Balance-/Validierungsfälle in den vorhandenen Kontrakttests; Zustands-/Zeitreihen ohne Tk |
| 4 — `refactor(movement): own source specific requests in the existing controller` | `movement/contracts`, `controller`, `walk_runtime`, alle zehn World-Zielstellen: Quellenfreigabe, ein aktiver Auftrag/Abschluss, Bewegungsdaten statt Domain-Clipnamen. Notwendige Adapter auf die typisierte Ausgabe gemeinsam migrieren, vorhandene Renndarstellung erhalten | Neu: `test_movement_requests.py`; `test_goal_walk.py`, `test_desktop_walk_runtime.py`, Klasse `WalkControllerTests` aus `test_motion_animation.py`; ausgewählte World-Fälle für Bindung, Zielverlust und Unterbrechung, unten konkretisiert |
| 5 — `fix(input): share contact origin admission across enter and hover polling` | `cursor_observation.classify_contact`, `desktop/input`, `HoverUiPorts`/`refresh_hover` und GUI-Verdrahtung: gleicher Herkunftscheck für Öffnen und Registrieren; vorhandener `ContactCoordinator` bleibt zuständig | Neu: `test_cursor_contact_origin.py`; `test_desktop_input_controller.py` und ausgewählte Hover-/Kontaktfälle für Enter, Polling, Klick, F2 und bestehende Controls; keine gesamte GUI-Suite |
| 6 — `feat(assets): export reviewed step and head combinations` | Vorhandener Exporter, Clipdaten, Posenmanifest/-lader und falls nötig Cache-Zuordnung: ganze abgenommene Laufzeitbilder und Metadaten, passende Profile und Übergänge. Keine neue Pipeline | `test_character_body_pose_export.py`, `test_body_pose_assets.py`, `test_body_pose_cache.py` sowie konkret betroffene Katalogfälle; deterministischer Export, Pfade, Größen, Anker, Alpha, erhaltene1X-Quellen |
| 7 — `feat(animation): play oriented steps without resetting head independent progress` | `BodyOrientation`, `DesktopAnimationRuntime`, `AnimatedPet`, Assembly: vor Ortswechsel drehen, neue Bewegungsclips über vorhandenen Framecallback ausführen, Kopfwechsel unabhängig halten, stabil abschließen | `test_body_orientation.py`, `test_desktop_animation_runtime.py`, `FrameClockTests` aus `test_motion_animation.py`; ausgewählte Bewegungs-/Maßstabsfälle aus `test_animated_pet_isolation.py` einschließlich neuer Schritt-/Kopfwechseltests |
| 8 — `feat(cursor): coordinate shared gaze and admitted approach or retreat` | Neues `application/cursor_behaviour.py`; `application/assembly`, Runtimeports, World-Lesesichten, `visual_observation`, `preferences`, Animation-/GUI-Verdrahtung: Absicht vor World, Zulassung danach, Abschlussrückmeldung und gezielter Reset; erste vollständige Cursorverbindung | Neu: `test_cursor_behaviour_coordinator.py`, `test_cursor_behaviour_integration.py`; `test_application_assembly.py`, `test_desktop_runtime.py`, `test_desktop_visual_observation.py` und ausgewählte Präferenz-/World-Szenarien für genau diese Verbindung |
| 9 — `feat(idle): submit occasional small resting steps through existing planning` | `RandomWalkPlanner` und dessen vorhandene Zulassungs-/Darstellungsanbindung: eigener seltener Idle-Auftrag und Ruhe danach; derselbe Controller/Driver | Neu: `test_idle_steps.py`; gezielte Planner-/Bewegungsfälle und `test_ambient_director.py` für erhaltenes Blinzeln/Umsehen; Cursor-/Objekt-/Bedienvorrang in diesen Tests |
| 10 — `test(cursor): complete acceptance and wire final CI coverage` | Abschließende systemübergreifende Abnahmefälle, nötige neue Windows-Testeinträge in `.github/workflows/tests.yml`, aktualisierte Architektur-/Verhaltensdokumentation und Nutzer-Sichtbefund; keine aufgeschobenen Funktionsmodule | Einmal vollständige lokale Tests und globale statische Gates; anschließend echte vollständige GitHub-Actions-CI auf dem abschließenden Stand, siehe Abschlussablauf |

### Präzisierung der gezielten Testauswahl

Für Commit4 sind aus `WorldGuiTests` zunächst diese bestehenden Fälle relevant:

- `test_observed_alternative_cannot_replace_committed_approach`
- `test_taken_target_is_followed_through_hops_and_resumes_at_both_scales`
- `test_missing_unknown_approach_target_releases_without_patrol`
- `test_hover_clicks_and_other_cancelled_gesture_keep_the_episode`

Für Commit5 gehören `ContactCoordinatorTests.test_hover_opens_toolbar_and_interrupts_walk`
und `test_hover_greeting_and_ui_contact_do_not_renew_durable_care` zum
bestehenden Kontaktvertrag. Die neuen Herkunftstests decken insbesondere
beide Öffnungswege, Kontaktregistrierung, eigene Bewegung und gleichzeitig
bewegten Zeiger ab. Bei Commit8 prüfen neue gezielte Integrationsfälle unter
anderem eine im selben Tick beginnende World-Aktion, ein verfolgt angebotenes
Objekt, deaktivierte Optionen und eine zwischen Frames neu auftretende Sperre.

Bei der Umsetzung werden für jeden Commit die tatsächlich betroffenen
Methoden/Klassen als Testkommando festgehalten. Zusätzliche Tests nur bei einer
konkret berührten Abhängigkeit oder einem neuen Fehler. Kein pauschales
`unittest discover -s tests`, kein projektweites Ruff/Mypy/Pyright und kein
CI-Lauf nach jedem Zwischencommit. Ein gezielter Prüfer für geänderte Dateien
kann ergänzend eingesetzt werden, ersetzt aber keinen Fachtest.

## Abschluss einschließlich echter CI

1. Alle fachlichen Commits lokal mit ihren gezielten Prüfungen abschließen.
   Vor jedem Commit aktuellen Status und enthaltene Dateien kontrollieren;
   parallele Änderungen bleiben getrennt. Kein Zwischenpush zur bloßen
   wiederholten Auslösung einer umfassenden CI.
2. Die neuen Testmodule im vorhandenen Windows-Smoke-Aufruf ergänzen, soweit
   sie dort benötigt werden; die Linux-Discovery erfasst sie bereits. Keinen
   zweiten Workflow für dieselben Prüfungen einführen.
3. Am finalen Stand einmal vollständig prüfen: Ruff über Code/Tests/Tools,
   striktes Mypy, projektweites Pyright, gesamte Unit-/Tk-GUI-Suite und
   Windows-relevante Grenzen. Praktische Sichtung1X/2X durch den Nutzer,
   ohne Computer Use und mit isolierten Daten, falls ein vollständiger
   App-Smoke-Test nötig ist.
4. Zum Abschluss gehört auch die echte GitHub-CI, nicht nur ein lokaler
   Nachbau. Der vorhandene `Tests`-Workflow läuft auf Pull Requests und auf
   Push nach `main`; ein bloßer Arbeitsbranch-Push löst ihn derzeit nicht aus.
   Nach Freigabe des Push-/PR-Schritts den finalen Branchstand über den
   zugehörigen PR prüfen, ohne dafür zu mergen. Falls ein passender PR bereits
   existiert, diesen verwenden. Ergebnisse auf den richtigen Head beziehen.
5. Die bestehende CI umfasst Linux mit Python3.11/3.13, globale statische
   Prüfungen, gesamte Unit-/GUI-Suite und Windows-Smoke. Der manuell startbare
   `full_static_audit.yml` ersetzt diese vollständige CI nicht und wird nicht
   zusätzlich ohne eigenen Prüfgrund doppelt ausgeführt.
6. Fehler gezielt korrigieren und die betroffenen Tests wiederholen; relevante
   Abschlussprüfungen/CI am korrigierten Head erneut ausführen. Erst bestätigte
   Ergebnisse als grün ausweisen. Kein automatischer Merge.

## Noch festzulegende Parameter

Nähe-/Geschwindigkeitsschwellen, Erholung, Häufigkeit eigener Idle-Schritte,
maximale Annäherung pro Versuch und Fluchtdauer werden anhand der gezielten
Zeitreihen und späterer Nutzersichtung abgestimmt. Das erzeugt weder zusätzliche
persistente Zustände noch einen pauschalen Auftrag zur Bildgenerierung.


## Umsetzungsstand und Prüfnachweis

Die fachlichen Schritte sind lokal umgesetzt. Es gibt genau zwei neue
Produktionsmodule: die reine Cursorpolicy und ihren Anwendungskoordinator.
`assemble_pointer()` bleibt im vorhandenen Desktop-Assemblymodul; Eingabe,
Kontaktprüfung und Reset gehören zu `PointerRuntime`, nicht in die GUI.
`application/object_behavior.py` erlaubt beim kleinen Seitenschritt passende
Kopfachsen derselben Seite; World-/Objektphasen behalten Vorrang.

| Schritt | Commit | Gezielter Nachweis vor diesem Commit |
| --- | --- | --- |
| 1 | `f8abc6a` | Plan, Pfade und Zuständigkeiten geprüft |
| 2 | `2b8959a` | 12 Beobachtungs-/Pointertests |
| 3 | `d51e7ed` | 16 Policy-/Ressourcentests |
| 4 | `37265a4` | 26 Bewegungs-/Worldtests |
| 5 | `bbde658` | 10 Herkunfts-/Eingabetests |
| 6 | `c40d3ce` | 11 Export-/Katalog-/Cachetests; Atlas-Hashes unverändert |
| 7 | `97f2c60` | 52 Animations-/Orientierungs-/Fortschrittstests |
| 8 | `586d14a` | 25 Koordinator-/Runtime-/Präferenztests und 7 Integrations-/Worldtests |
| 9 | `fd4a531` | 26 Idle-/Controller-/Ambienttests |
| 10 | Abschlusscommit | Gesamtsuite und globale Prüfungen, Ergebnis siehe unten |

Der Abschluss korrigiert zusätzlich durch die Gesamtkontrolle aufgedeckte
Verdrahtung, Typisierung und Testadapter. Der bestehende GUI-Größenvertrag
bleibt bei 640 Zeilen. Ein vorhandener Schere-Stein-Papier-Test erhielt nur
eine konkrete Typprüfung seiner Detaildaten für Pyright; das Spielverhalten
wurde nicht verändert. Die Windows-CI erfasst die neuen Testmodule ausdrücklich.
Die Gesamtsuite deckte außerdem einen schon vorher vorhandenen, veralteten
Quiz-Aufruf im Pflege-Simulationswerkzeug auf: Quizrunden werden dort nun wie
im Produkt als `completed` ohne Wettbewerbsresultate geführt. Der Sprachschalter-
Test erhält einen echten Niedrigstimmungsanlass statt eine Äußerung ohne Grund
zu erwarten; entfernte Cursor und der Neustart nach Spielen werden über die
neue Wahrnehmung geprüft. Parallele UI-Implementierungen bleiben unverändert.
Die World-Komponententests veröffentlichen vor manuellen World-Ticks die
gemeinsame Wahrnehmung und Absicht. Ein eigener Test sichert aktuelle native
Greifpositionen zwischen zwei Sensor-Ticks. Ältere Testdaten erhalten vom
Gedächtnisbesitzer vergebene Kennungen; Dialogtests prüfen die ausgewählte
Folge und genau einen regulären Abschluss statt eine feste alte Textanzahl.
Die bereits bestehende Annahme unerwünschten Essens mit anschließendem
Hinlegen bleibt erhalten; weder der Besitz- noch der Verzehrvertrag wird
für einen alten Test verschärft.
Alte optionale Posenpakete ohne Schrittbilder behalten die bisherige
Bewegungsdarstellung; die neue Drehbereitschaft verlangt dann keine fehlenden Clips.

Aktuelle Startwerte: Körperreaktion nach 1,2 Sekunden auf derselben Blickseite,
Neugier nach 2,5 Sekunden ruhigem erreichbarem Zeiger, ein Schritt von
16 logischen Pixeln (32 in 2X), mindestens 12 Sekunden Pause nach einem Versuch.
Idle plant nach kleinen Schritten 35–65 Sekunden Ruhe und geht pro
Schritt ebenfalls 16 logische Pixel. Nähe/Geschwindigkeit werden in Figurenbreiten
normiert; eine Flucht ist auf 0,35 Figurenbreiten begrenzt. Diese Werte sind
Abstimmungswerte, keine neue persistente Persönlichkeitsskala.

Das optionale HD-Posenpaket umfasst 18 Clips mit 102 PNGs: die bisherigen
26 Bilder plus 76 zusätzliche Exporte aus bereits abgenommenen Quellen.
Private Originale bleiben außerhalb Git, beide regulären Atlanten unverändert.
Es wurden keine Bilder generiert. Die vorhandene Renndarstellung bleibt für
kurze Flucht und bestehende World-Wege erhalten; eine neue längere Geh-/Rennfolge,
ständiges Mausverfolgen und autonomes Berühren sind nicht Teil dieses Schritts.

Praktische Sichtabnahme durch den Nutzer und echte GitHub-CI stehen noch aus.
Computer Use wurde nicht verwendet. Ein Branch-Push allein startet den
vorhandenen vollständigen Tests-Workflow nicht; hierfür ist der freizugebende
Push-/PR-Schritt erforderlich.


### Noch offene praktische Sichtabnahme

Für den neuen Python-Code die Anwendung einmal neu starten. Computer Use ist
nicht Teil der Abnahme; der Nutzer beurteilt die Darstellung selbst.

1. Idle mit Blinzeln beobachten: leichtes Schwanken und gelegentliches Umsehen
   bleiben erhalten; kleine Ortswechsel zeigen den ganzen Körper in Bewegung.
2. Den Zeiger kurz links/rechts wechseln, danach auf einer Seite halten:
   zunächst Kopfreaktion, erst bei anhaltender Richtung Körperdrehung.
3. Einen erreichbaren Zeiger ruhig halten: höchstens ein kleiner Versuch,
   danach Ruhe; ein bewegter Zeiger zieht Aiko nicht endlos hinterher.
4. Langsame Nähe, schnelle seitliche Vorbeifahrt und schnelle Annäherung
   vergleichen: Nähe allein ist kein Fluchtgrund, die Richtung zählt mit.
5. Während Menü, Spiel, Schlaf, Gespräch und Objektübergabe prüfen, dass diese
   Interaktionen Vorrang behalten. Bewegung unter einem ruhenden Zeiger darf
   weder die Toolbar öffnen noch absichtlichen Benutzerkontakt verbuchen.
6. In beiden Größen Bodenlinie, Halsübergänge, passende Kopfachsen und die
   Rückkehr über Dreiviertel zur Front sichten.


### Lokale Abschlussprüfung

Am abschließenden Code-Stand unter Windows mit Python 3.11.9 erfolgreich:

- `python -X faulthandler -m unittest discover -s tests -q`: **2.284 Tests, OK**
  (343,047 Sekunden; vollständiger erneuter Lauf nach den Korrekturen).
- `python -m ruff check aiko_pet tests main.py tools`: **grün**.
- `python -m mypy --strict --no-incremental aiko_pet main.py tools`:
  **keine Fehler in 360 Quelldateien**.
- `python -m pyright --project pyrightconfig.json`: **0 Fehler, 0 Warnungen**.
- Git-Diff-Prüfung ohne Whitespacefehler; beide regulären Atlanten unverändert
  gegenüber dem Ausgangsstand `93f1c22`. Genau zwei neue Produktionsmodule.
- 86 vorhandene/ergänzte Windows-Testmuster auf vorhandene Dateien und doppelte
  Einträge geprüft. Die neue Abdeckung bleibt im vorhandenen Tests-Workflow.

Diese lokale Abnahme ersetzt die noch ausstehende GitHub-CI und praktische
Nutzersichtung nicht. Auf der Arbeitsbranch existiert bereits PR #11;
nach der vorgesehenen Push-Freigabe kann dessen vollständiger Tests-Workflow
am neuen Head laufen. Kein Merge ist beauftragt.
