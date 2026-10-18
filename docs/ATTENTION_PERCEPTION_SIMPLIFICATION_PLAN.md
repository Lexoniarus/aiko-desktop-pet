# Vereinfachung von Blickrichtung, Aufmerksamkeit und Wahrnehmung

Die spätere [gemeinsame Fokusregel](SHARED_INTERACTION_FOCUS_PLAN.md) ersetzt
die hier historisch dokumentierte Umgebungsfreigabe während fokussierten
Hinlaufens und ergänzt Streicheln/Gespräch. Frühere Prüfergebnisse bleiben
Lieferhistorie; der neue Plan dokumentiert die Korrektur und deren Nachweise.

Stand: 18. Oktober 2026. Branch: `feature/world-foundation`.
Status: **Etappen 1–5 abgeschlossen und automatisch geprüft.**
Die menschliche Sicht-/Eingabeabnahme bleibt offen.
Der Nutzer hat Etappen 1–5 jeweils einzeln
zur Umsetzung freigegeben. Bestehende lokale Arbeit und der normale Spielstand
bleiben erhalten. Nichts mergen.

## Anlass und Abgrenzung

Praktischer Fehlerbericht: Aiko untersucht einen neu abgelegten Gegenstand.
Währenddessen werden vier andere, bereits identifizierte Gegenstände umplatziert.
Nach ihrer Untersuchung fehlen Verlustreaktion und Suche.

Die Ursache dieses konkreten Laufs ist noch nicht durch eine Aufzeichnung
bewiesen. Der Codevergleich zeigt aber eine fachliche Lücke: Blickdarstellung,
Aufmerksamkeit und Objektwahrnehmung treffen teilweise unabhängige Entscheidungen.
Dieses Vorhaben vereinfacht diese Verbindung, bevor weitere Ausnahmen entstehen.

Der [bisherige Suchplan](OBJECT_SEARCH_SIMPLIFICATION_PLAN.md) bleibt als
Liefer- und Prüfhistorie erhalten. Seine abgeschlossenen Prüfungen bestätigen
die damalige Implementierung, keine Abnahme des hier präzisierten Sichtmodells.
Für eine spätere Umsetzung ersetzt dieser Plan insbesondere die Annahme einer
allgemeinen Umgebungswahrnehmung während der Handuntersuchung. Identitäts-,
Besitz-, Speicher- und gemeinsame Suchregeln bleiben erhalten.

## Ausgangszustand vor Etappe 1

| Stelle | Aktuelles Verhalten | Geplante Korrektur |
|---|---|---|
| [VisualObservation](../aiko_pet/desktop/visual_observation.py) | Objektziel geht vor Cursorblick; Cursoraktivität und Einstellungen bestimmen den passiven Blick. | Bereits entschiedene Aufmerksamkeit darstellen; keine zweite fachliche Zielwahl. |
| [Animationslaufzeit](../aiko_pet/desktop/animation_runtime.py) | Aktion und Laufen gehen vor passivem Blick. Der passive Blicksektor wird dabei teilweise gar nicht aktualisiert. | Tatsächliche Aktion und Bewegungsrichtung als Eingaben verwenden; keinen alten Sprite-Blicksektor als Wahrnehmungswahrheit lesen. |
| [ObjectBehavior](../aiko_pet/application/object_behavior.py) | `attentive` hängt überwiegend an Wachzustand/Spiel; `blocked` steuert separat Aktionen und Reaktionen. | Beobachtungsumfang vor der Wahrnehmung aus dem aktuellen Ablauf bestimmen. |
| [ObjectAwareness](../aiko_pet/application/object_awareness.py) | Umgebung wird hauptsächlich nach Entfernung gefiltert; `committed` erhält die Bindung des Zielobjekts, begrenzt aber das Umfeld nicht. | Nur zulässige Beobachtungen an Tracker, Erkennung und Platzprüfung weitergeben. |
| [ObjectAbsencePerception](../aiko_pet/pet/mind/object_absence.py) | Eigene Entfernungs-/Aufmerksamkeitsprüfung mit Belegungs- und Zeitnachweisen. | Derselbe Sichtentscheid wie bei positiven Beobachtungen; leere Plätze bleiben eigenständige Belege. |
| [WorldRuntime](../aiko_pet/desktop/world_runtime.py) | Wahrnehmung erzeugt ein Blickziel; Cursorereignisse können unabhängig davon Transportkontinuität melden. | Cursorereignis und Tick verwenden dieselbe Aufmerksamkeitsregel, bevor eine Beobachtung bestätigt wird. |

## Fachlicher Soll-Vertrag

- Im Nahbereich kann Aiko bemerken: „Da liegt etwas.“ Das identifiziert nichts.
  Allgemeines Bemerken reicht nicht über die ganze Taskleiste.
- Beim Laufen entspricht die gerichtete Wahrnehmung ihrer tatsächlichen
  Laufrichtung; im freien Zustand kann der Cursor ihr Blickziel sein.
- Beim Aufnehmen und Untersuchen bindet der Gegenstand ihre Aufmerksamkeit.
  Andere umplatzierte Gegenstände liefern währenddessen keine neuen Umweltbelege.
- Ein identifizierter Gegenstand am exakt erinnerten Platz ist nach gültiger
  Wahrnehmung wiedererkennbar. Unbeobachtetes Umstellen hinterlässt die alte
  Erinnerung; am neuen Platz liegt zunächst ein unbekannter Fund.
- Identifikation erfolgt nur durch tatsächliche Handuntersuchung oder bewusstes
  Präsentieren vor den Augen. Eine neue Präsentationsgeste braucht ihre eigene
  kontinuierliche Präsentation, auch wenn die Identität bereits gelernt ist.
- Sieht Aiko das Aufnehmen eines bekannten Gegenstands und verfolgt den Vorgang,
  bleibt seine Zuordnung über Cursortransport und beobachtetes Ablegen erhalten.
  Der Spieler-Klick allein und ein technischer World-Verweis sind keine Beweise.
- Nach Freigabe des Gegenstandsfokus prüft sie die jetzt sichtbaren bekannten
  Plätze. Bestätigte Verluste haben Vorrang vor neuer freier Neugier und Appetit.
  Außerhalb des Sichtbereichs liegende Plätze werden erst beim Hinsehen geprüft.
- Eine gemeinsame Suche sammelt weitere bemerkte Verluste. Unbekannte Funde
  werden aufgenommen, identifiziert und zugeordnet oder wieder abgelegt.
  Ein passender Fund löst nur seinen eigenen Verlust; andere bleiben offen.

## Ein Ablauf, daraus abgeleitete Aufmerksamkeitszustände

Die folgenden Zustände sind eine fachliche Sicht auf vorhandene Aktionsphasen.
Sie werden aus Phase, tatsächlicher Bewegung und Ziel abgeleitet. Es entsteht
keine zweite veränderliche Zustandsmaschine neben `ObjectInteractionCoordinator`.
Suche bleibt ein Auftrag über mehrere Aktionen hinweg, kein zusätzlicher
Aufmerksamkeitsmodus und keine neue Bewegungssteuerung.

| Zustand | Anlass / Zuordnung | Blick und zulässige Wahrnehmung | Nächster Schritt |
|---|---|---|---|
| **Umsehen / Abgleichen** | Frei, Start/Neustart oder abgeschlossene Beschäftigung ohne anderen exklusiven Fokus | Nahbereich und aktueller gerichteter Sichtbereich; sichtbare bekannte Plätze und neue Sichtungen prüfen | Bestätigte Verluste sammeln; sonst Suchauftrag fortsetzen oder gewöhnliches Ziel wählen |
| **Cursor beobachten** | Freier Cursorblick oder bestehendes Warten auf einen tatsächlich beobachteten, vom Spieler gehaltenen Gegenstand | Cursor als Blickziel; im erlaubten Umfeld normal bemerken; nur einen bereits beobachteten Transport weiterverfolgen | Präsentation, beobachtetes Ablegen, Blickverlust oder neuer verbindlicher Ablauf |
| **Unterwegs** | Tatsächlicher Zufallsweg, Zielannäherung oder Suchweg | Blick in Laufrichtung; Nahbereich und gerichteter Sichtbereich; keine Identifikation unbekannter Bodenfunde | Ankunft; sichere Reaktion auf sichtbaren Verlust; bestehende Aktion wird nicht von freier Neugier verdrängt |
| **Gegenstandsfokus** | Verbindliches Ziel im Stand; Aufnehmen, Halten/Untersuchen, Ergebnis, Entscheidung, Essen oder Ablegen | Aktuelles Ziel beziehungsweise eigene Hand; keine allgemeine Umgebungsprüfung und keine unbeobachtete Cursorzuordnung | Bestehende Animation/Lesebestätigung abschließen; dann Abgleich oder zulässiges Warten |
| **Keine Objektbeobachtung** | Schlaf oder aktiver Spielablauf | Keine neuen Umweltbelege; gelerntes Wissen bleibt bestehen | Nach Rückkehr in einen freien Ablauf frische Beobachtung beginnen |

Warten auf Rückgabe/Setzen verwendet die bestehenden Waiting-Phasen. Eine bewusst
beobachtete Präsentation während Suche oder Warten bleibt möglich. Sie erhält
keinen pauschalen Vorrang vor einer anderen laufenden Handuntersuchung.
Temporäre Bewegungsblocker stoppen das Gehen, löschen aber keinen Suchauftrag;
sie werden nicht pauschal mit Schlaf oder fehlender Wahrnehmung gleichgesetzt.
Sprechblasen erben die Aufmerksamkeit ihrer Aktion; jede Bubble bekommt keinen
eigenen neuen fachlichen Zustand.

### Sichtumfang als kleiner, überprüfbarer Vertrag

Für Punkte mit Gegenständen und für erinnerte leere Plätze gilt derselbe
Sichtentscheid. Weltposition, Augenreferenz und Cursor werden einmal in dasselbe
Koordinatensystem überführt. Der fachliche Blick kommt aus dem Ablauf, nicht aus
einem zufällig zuletzt gerenderten Frame. Die 16 Blickframes bleiben Darstellung.

Etappe 1 legt den technischen Startwert fest: unmittelbarer Nahbereich von einer
Körperbreite; darüber die vor der Blickachse liegende Halbebene bis zur bestehenden
`notice_widths`-Grenze von sechs Körperbreiten. Höhenrichtung ist nach oben positiv.
Offsets und Blickvektor beziehen sich auf die vorhandene Augenreferenz, normiert
auf `FRAME_WIDTH * scale`. Ohne Richtung gilt nur das Nahfeld; bei Handfokus,
Schlaf und Spiel gilt keine allgemeine Umgebungswahrnehmung. Die technische
Prüfung bei 1x/2x ist im Lieferstand unten festgehalten; menschliche visuelle
Kalibrierung bleibt offen. Die tatsächliche Wahrnehmung ist seit Etappe 2
an diese Regel angeschlossen.
Keine zusätzliche Matrix von Winkeln, Reichweiten und Ausnahmemodi einführen.

Gezielte Verfolgung eines bereits beobachteten Cursortransports kann diesen
Gegenstand über den normalen Nahbereich hinaus begleiten. Sie öffnet kein neues
Umfeld am entfernten Cursor. Fokuswechsel oder tatsächlicher Sichtverlust
beenden diese Kontinuität; alte Bindungen ersetzen keine aktuelle Beobachtung.

## Übergänge und Reihenfolge

```text
Umsehen / bekannte Plätze abgleichen
  → neuer zulässiger Fund → hinlaufen → aufnehmen → untersuchen
  → Ergebnis / normale Entscheidung → essen oder sicher ablegen
  → Umsehen / bekannte Plätze erneut abgleichen
      → sichtbare Verluste → gemeinsame Suche
          → unbekannten Fund untersuchen → zuordnen / ablegen
          → weiter abgleichen und denselben Suchauftrag fortsetzen
```

1. Aktionsphase, Bewegung und Cursorlage bestimmen die aktuelle Aufmerksamkeit.
   Dieselbe Entscheidung steuert Sichtprüfung und sichtbaren Blick. Für die
   Erstauswahl eines neuen Ziels zählt der bisherige Blick; ein verborgenes
   Objekt darf sich nicht durch seine eigene Auswahl erst sichtbar machen.
2. Zulässige positive Beobachtungen und negative Platzbelege aktualisieren das
   subjektive Wissen. Sichtverlust unterbricht laufende Wahrnehmungszeiten.
3. Nach Gegenstandsfokus beginnt dieser Umgebungsnachweis frisch. Ein leerer
   bekannter Platz braucht den bestehenden kontinuierlichen Abwesenheitsnachweis;
   niemand behauptet rückwirkend, das Umstellen gesehen zu haben.
4. Alle in diesem Durchlauf bestätigten sichtbaren Verluste werden übernommen,
   bevor eine freie neue Untersuchung gewählt wird. Weitere Plätze kommen beim
   Hinsehen dazu. Kein vollständiger unsichtbarer Bildschirmabgleich als Startgate.
5. Ein unklar belegter Platz bleibt ungeklärt. Er blockiert weder andere eindeutig
   leere Plätze noch deren Suchstart global. Ein erforderliches Untersuchen des
   unbekannten Belegers muss möglich bleiben; auf dessen Identifikation zu warten
   und gleichzeitig jede Untersuchung zu verbieten wäre ein Stillstand.
6. Nach Hinweis und Lesebestätigung beginnt beziehungsweise läuft die bestehende
   Suche weiter. Vollständige tatsächlich abgelaufene Route und ausgeschöpfte
   zulässige Fundprüfungen erlauben erfolglosen Abschluss; alle Verluste aufgelöst
   erlauben frühen Abschluss. Das zeitweilig enge Sichtfeld während einer
   Handaktion darf nicht als fertig geprüfte Umgebung zählen.

„Nach der Untersuchung“ bedeutet Rückkehr aus der gesamten verbindlichen
Beschäftigung einschließlich erforderlichem Essen/Ablegen und deren Abschluss.
Ein bereits bestätigter Verlust bleibt als Wissen erhalten, auch wenn Aiko
zwischenzeitlich wieder beschäftigt ist. Es werden lediglich keine zusätzlichen
Umweltbelege während exklusiven Gegenstandsfokus erfunden.

## OOP-Zuständigkeiten und geplanter Rückbau im Code

| Besitzer | Verantwortung | Was dort entfällt / dort nicht entstehen soll |
|---|---|---|
| Bestehende Application-Koordination | Aus vorhandener Aktion und Host-Fakten eine kleine unveränderliche Aufmerksamkeitsentscheidung ableiten: Zustand, Blickziel/-richtung und zulässiger Beobachtungsumfang | Unabhängige fachliche Zielwahl durch Renderer; verstreute Annahmen aus `blocked`, `committed`, `attentive` |
| Reine Wahrnehmungsregel in `pet/mind` | Sichtbarkeit eines Orts und erlaubte Zielbeobachtung anhand dieser Eingaben bestimmen | Doppelte Sichtregeln für Objekt, leeren Platz und Cursorereignis |
| `ObjectAwareness`, Tracker und Memory | Zulässige Sinnesdaten verarbeiten; Erinnerung und beobachtete Kontinuität getrennt halten | Ungeprüfte Cursor-Verfolgung aus einer noch vorhandenen Bindung; globale Umgebungsbeobachtung im Handfokus |
| `ObjectInteractionCoordinator` / SearchTask | Aktion, Besitzübergänge, Lesebestätigungen und Suchauftrag mit bestehender Route führen | Zusätzliche Verlust-/Nachscan-Flags, Ersatzsuche oder parallele Phasenmaschine |
| Desktop / UI | Native Geometrie und Pointer erfassen; bestehende Bewegung ausführen; entschiedene Aufmerksamkeit darstellen | Fachliche Wahrnehmung aus Sprite-Frames rekonstruieren; neue Positionsschreiber oder Timer |

Ein kleines internes Wertobjekt und reine Ableitung genügen als Zielarchitektur.
Kein neuer dauerhaft zustandsbehafteter Aufmerksamkeitsdienst und keine
Strategiehierarchie. `DesktopAttentionRuntime` für soziale Kommentare ist kein
neuer Besitzer der Objektwahrnehmung. Schlaf, aktive Animationen, Laufdarstellung,
Cursor-Einstellung und Blickhysterese behalten ihre eindeutige Priorität.

Vor jedem Löschen: Nutzung in Anwendung, Tests, Tools und Dokumenten nachweisen.
Parameter nur entfernen, wenn ihre verbliebenen Aufgaben tatsächlich entfallen.
Erinnerungsformat und Migrationen, körperliche Zuordnung, care origin und
einmalige Ernährungseffekte sind kein Rückbauziel.

## Testplan: ersetzen, zusammenführen, erhalten

Tests werden nach fachlicher Aussage bewertet, nicht nach Dateigröße oder
gewünschter Gesamtzahl. Jede entfernte Aussage erhält entweder eine explizite
Soll-Änderung oder einen benannten verbliebenen Nachweis. Gleicher Szenenaufbau
allein macht Tests verschiedener Besitzer nicht redundant.

### Konkret zum Rückbau markierte Szenarien

Die folgende Tabelle dokumentiert die ursprüngliche Rückbauentscheidung;
R1–R3 sind in Etappe 4 umgesetzt. Die alten Testnamen bleiben hier als historische
Zuordnung erhalten. „Unerreichbar“ bezeichnet den künstlich erzwungenen Ablauf unter
Umgehung der aktuellen Anwendungsvoraussetzungen; die World-API kann solche
Zustände für einen isolierten Test weiterhin herstellen.

| Kennung / Test | Warum dieser Aufbau kein regulärer Anwendungspfad ist | Rückbaustand und verbleibender Nachweis |
|---|---|---|
| R1 — `test_object_awareness.py::test_hand_inspection_uses_available_observation_instead_of_hidden_truth` | `create_held` und unmittelbar `WorldState.accept_handover_on_release` setzen eine Portion ohne vorherige Awareness-/Memory-Zuordnung in die Hand. Der reguläre Einstieg `offer_on_release` verlangt bereits einen Record; `can_acquire` verlangt aktuelle Beobachtung und Reichweite. Der Test erzwingt eine nachträgliche Entdeckung des bereits pet-held Gegenstands. | **Entfernt in Etappe 4.** Der künstliche Wiederherstellungsaufbau entfällt, ohne neuen Teleport-Sonderfall. Identifikation erst nach tatsächlicher Übernahme bleibt durch `test_world_gui.py::test_unpresented_unknown_item_is_accepted_and_identified_in_hands` und die Wahrnehmungsregeln abgesichert. |
| R2 — `test_object_retrieval.py::test_recalled_apple_replaced_by_another_apple_is_valid_stock` | `_replace_recalled_portion` überschreibt den privaten `_resolve_instance`-Callback und erzwingt die Zuordnung einer neuen Portion zur alten Erinnerung. Der Test erwartet anschließend Essen ohne erneute Untersuchung. Die reguläre Wahrnehmung kann eine neue Portion nicht allein wegen desselben Katalogtyps oder Platzes so identifizieren. | **Entfernt in Etappe 4.** Der erzwungene Auflösungsweg und seine Erwartung entfallen. Die gültige Wiederverwendung derselben bekannten Portion bleibt in den normalen Retrieval-Tests. Getrennte gleichartige Portionen bleiben durch `test_object_behavior.py::test_other_same_type_portion_cannot_end_physical_subject_search` sowie die nativen Nahpaar-/Suchläufe abgesichert. |
| R3 — `test_object_retrieval.py::test_recalled_apple_replaced_by_cookie_requires_hand_inspection` | Derselbe private Callback bindet einen Cookie unter den alten Apfel-Record und umgeht die reale Sichtungs-/Identitätszuordnung. Der reale Austausch am alten Ort bleibt möglich; künstlich ist die erzwungene alte Zuordnung, bevor erst in der Hand korrigiert wird. | **Entfernt in Etappe 4.** Der erzwungene Einstieg entfällt. Den realen Austausch und die Untersuchung eines zunächst unbekannten Ersatzes durch `test_object_awareness.py::test_unknown_replacement_at_learned_place_never_borrows_identity` und `test_world_gui.py::test_unseen_cookie_replacement_does_not_get_consumed_as_known_apple` erhalten. |

Der Testhelfer `_replace_recalled_portion` wurde in Etappe 4 mit seinen beiden
Aufrufern R2/R3 entfernt. Die erneute Suche über Anwendung, Tests, Tools und
Dokumentation fand keine weiteren Aufrufer; die verbleibenden Erwähnungen sind
ausschließlich diese Rückbauhistorie. Auch die nur dafür benötigte Cookie-
Definition im Retrieval-Fixture entfällt.

Produktionsmethoden werden dadurch nicht pauschal gelöscht. Der echte
Pickup-Abschluss verwendet `held_type_conflicts_with_memory` weiterhin.
Die Prüfung in Etappe 4 bestätigt einen unterstützten Eingabepfad: Der
Memory-Codec validiert subjektive Identität und erworbene Referenz, vergleicht
aber die erinnerte Identität nicht mit der aktuellen World-Definition.
`test_restored_conflicting_knowledge_requires_hand_inspection` ersetzt daher die
willkürliche Memory-Änderung während Pickup durch einen tatsächlich dekodierten
Widerspruch vor dem Abruf. Dieser Grenztest und der Schutz bleiben erhalten;
der Schutz identifiziert nichts. Die separate Konsumgrenze darf ebenfalls nie
einen anderen Typ aufgrund einer alten Ortshypothese essen.

Die Physik ersetzt keine reguläre Handübergabe: `CursorItemGesture.release`
versucht die explizit erlaubte Übergabe; nur bei deren Ablehnung startet Fallen.
Echte Übergabe, Bodensammeln und der oben erzwungene Handzustand sind getrennte
Fälle. Aus R1 folgt kein Rückbau von Übergabe oder Physik.

### Gezielt anpassen oder zunächst weiter prüfen

| Bestehender Nachweis | Geplante Behandlung und Ersatz |
|---|---|
| Historisch `test_object_awareness.py::test_committed_action_still_perceives_local_drops_and_losses`; jetzt `test_moving_attention_keeps_target_and_observes_forward_changes` | In Etappe 4 ausschließlich präziser benannt, Assertions unverändert. Keine ersatzlose Löschung: Der aktuelle Aufbau lässt das Ziel am Boden und setzt nur `committed`; er bildet keine Handuntersuchung ab. Gültige gerichtete Wahrnehmung unterwegs mit explizitem Zustand erhalten. Die unbeschränkte Fokus-Erwartung ersetzen; exklusiven Handfokus und späteren Umgebungsabgleich im zentralen Ablauf nachweisen. |
| `test_object_awareness.py::test_following_a_visible_take_preserves_knowledge_outside_notice_radius` und `test_witnessed_take_commits_custody_before_any_held_frame` | Sichtbare Kontinuität erhalten; echte aktuelle Cursoraufmerksamkeit als Voraussetzung ergänzen. Ein kompakter Gegenlauf mit abgewandtem Handfokus zeigt anschließend Verlust statt heimlicher Verfolgung. |
| `test_object_behavior.py::test_busy_episode_keeps_unaccepted_absence_pending` | Bereits vorher beobachtete Verlustbelege erhalten. Der Test ist kein Beleg für fortgesetztes Umgebungssehen während Beschäftigung und entfällt nicht pauschal. |
| Historisch `test_object_behavior.py::test_blocked_nearest_unassessed_observation_keeps_gaze_without_episode`; jetzt `test_blocked_observation_uses_only_current_attention_without_episode` | In Etappe 4 auf expliziten Blick umgestellt: Der nähere verdeckte Gegenstand liefert keine Bindung; nur der tatsächlich sichtbare darf Blickziel werden. Aktionssperre und fehlende Episode bleiben geprüft. Keine zweite Prioritätsmatrix. |
| Historisch `test_object_interaction.py::test_search_rechecks_losses_after_readable_recognition`; jetzt `test_pending_preinspection_loss_waits_for_readable_recognition` | In Etappe 4 auf bereits vor der Handaktion bestätigten, verzögert übernommenen Verlust umgestellt. Der Gegenstand wurde vorher vom alten Platz versetzt. Unfertiger Recognition-Receipt, genau eine Fundmeldung, Besitz und fortgesetzte Suche bleiben geprüft. Keine Umweltbeobachtung während Handfokus. |
| `test_object_tracking.py` und Exact-place-/Same-type-/Neustartfälle in Awareness/Memory | Identitäts- und Kontinuitätsregeln erhalten. Ein technischer Handle oder gleicher Katalogtyp darf keine Identifikation ersetzen. Nur echte doppelte Aussagen zusammenführen. |
| `test_gaze.py`, `test_desktop_visual_observation.py`, `test_desktop_animation_runtime.py` | Atlas, Hysterese, Cursor-Einstellung, Hardware-Unterdrückung und Aktions-/Laufpriorität erhalten. Doppeltes Auswählen eines fachlichen Ziels entfällt; Adapter prüfen, dass die gemeinsame Entscheidung sichtbar wird. |
| Gemeinsame Suche bei 1x/2x in `test_world_gui.py` | Bestehenden kombinierten Ablauf anpassen: während Untersuchung keine neuen Verluste, danach gerichteter Abgleich und eine Suche. Vier bekannte verschobene Portionen einschließlich zweier gleicher Art verwenden; native Integration nicht in eine neue Fallmatrix vervielfachen. |
| Beide nativen Face-Reunion-Einstiege und schneller beobachteter Cursortransport bei 1x/2x | Beibehalten, aktuelle Aufmerksamkeit im Aufbau herstellen. Besitz bleibt bis zur tatsächlichen Übergabe beim Spieler. |
| `test_world_runtime_flow.py`, Speicher-/Custody-/Receipt- und Architekturprüfungen | Reale Lesedauer und Animation, sichere Unterbrechung, alte Spielstände und Modulgrenzen erhalten. Sie sichern eigene Verträge, keine redundante Blickentscheidung. |

Der ursprüngliche offene Kandidat
`test_object_retrieval.py::test_conflicting_observation_during_pickup_restores_full_inspection`
ist in Etappe 4 durch `test_restored_conflicting_knowledge_requires_hand_inspection`
ersetzt. Der Codec-Nachweis rechtfertigt den verbleibenden Produktionsschutz.
Der Receipt-Kandidat ist ebenfalls entschieden: Gültige alte Verlustbelege dürfen
verzögert übernommen werden; ein neuer Handfokus-Verlust wird dafür nicht erfunden.
Die jeweiligen Zuständigkeits-/Grenzprüfungen bleiben erhalten.

### Regeln, die verbindlich erhalten bleiben

| Regel / Grenze | Verbleibender Nachweis beziehungsweise nötige Anpassung |
|---|---|
| Übernahme nur durch tatsächliche Freigabe im gültigen Handbereich oder bestätigtes Bodensammeln | `test_world_state.py::test_handover_is_an_explicit_release_operation_not_pointer_motion`; native Übergabe- und Pickup-Läufe. Ein bloßes Vorbeibewegen des Cursors überträgt nichts. |
| Unbekannte Portion darf regulär übergeben und erst danach in der Hand identifiziert werden | `test_world_gui.py::test_unpresented_unknown_item_is_accepted_and_identified_in_hands`; Aufmerksamkeit im künftigen Aufbau passend herstellen. |
| Abgelehnte identifizierte Übergabe fällt; fallende/springende Portionen sind nicht als ruhender Bodenfund aufnehmbar | `test_world_gui.py::test_refused_identified_offer_still_falls_instead_of_entering_hands` und `test_world_falling.py::test_rebounds_are_not_collectible_and_checkpoint_restores_velocity`. |
| Identität nur aus erlaubter Hand-/Gesichtsbeobachtung, exaktem bekannten Platz oder tatsächlich beobachteter Kontinuität | Wahrnehmungs-, Exact-place-, Cursortransport- und Same-type-Fälle behalten; Sicht-/Fokusbedingungen an das neue Soll anpassen. Keine Identität aus technischem Handle, Nachbarschaft oder gleichem Typ ableiten. |
| Gesicherte Verluste bleiben über Beschäftigung erhalten; unbeobachtete Ortswechsel werden nach Fokusfreigabe geprüft | Pending-Absence-Nachweis erhalten; zentralen Vier-Gegenstände-Ablauf verwenden. Globale Umweltwahrnehmung während Handuntersuchung entfällt. |
| Gemeinsame Suche, Zuordnung nur der passenden Portion und tatsächliche Routendeckung | Multiple-Loss-, Same-type-, tatsächliche Ankunfts- und 1x/2x-Neustart-/Suchläufe behalten; kein Neustart des Suchwegs durch einzelne Untersuchung. |
| Besitz, Reichweite, Revision und einmalige Ernährungseffekte | World-/Custody-/Consumption-Grenzen behalten, einschließlich `test_object_consumption.py::test_place_hypothesis_cannot_consume_a_different_catalog_item`. |
| Sichere Unterbrechung, geordnete Animation und gültige Lesebestätigungen | Pickup/Put-down, veraltete Receipts und echte Timer-Läufe behalten. Eine Sprechblasenquittung ersetzt keinen tatsächlichen Besitzwechsel. |
| Persistente gelernte Erinnerung und unterstützte Altspielstände | Memory-/Codec-/Persistence-Nachweise und Nahpaar-Neustart erhalten. Flüchtige Wahrnehmung und laufende Aktionen werden nicht als erworbenes Wissen gespeichert. |

Direkte Zustandsvorbereitung ist für Besitzer-/Grenztests weiterhin zulässig.
Beispielsweise soll `test_world_state.py::test_wrong_custody_operations_are_rejected_without_partial_change`
gerade einen unzulässigen Aufruf abweisen. Solche Negativnachweise und gezielte
Fehlerinjektion für atomare Übergänge sind keine überholten Verhaltensszenarien.
Ein Ersatz durch einen bereits vorhandenen gleichwertigen Nachweis ist möglich;
der jeweilige Vertrag darf dabei nicht verschwinden.

Der zentrale spätere Akzeptanzlauf lautet: vier gelernte Portionen und ein neuer
Fund; während dessen Handuntersuchung vier unbeobachtete Ortswechsel; keine
behauptete Beobachtung währenddessen; nach Abschluss zunächst sichtbare Verluste,
dann eine gemeinsame Suche mit echter Identifikation der Funde. Ein tatsächlich
fehlender Fund beendet die Suche erst nach dem vollständigen Durchlauf.
Der kurze Gegenlauf zeigt beobachtetes Aufnehmen/Umstellen bei Cursoraufmerksamkeit
ohne falschen Verlust. Der Nahpaar-Neustart bleibt Teil des vorhandenen nativen
Regressionspakets.

## Geplante Umsetzungsetappen

Alle fünf Etappen sind umgesetzt und automatisch geprüft. Die praktische
Sicht-/Eingabeabnahme anhand der manuellen Prüfliste bleibt offen.
Jede Lieferung protokolliert hier
Änderung, ersetzte/entfernte Tests mit Begründung, verbliebene Nachweise,
Prüfbefehl, Laufzeit/Ergebnis und offene praktische Beobachtungen. Nach jeder
Etappe prüfen und dokumentieren; die nächste Etappe nicht stillschweigend anhängen.

| Etappe | Konkretes Ergebnis | Prüfung / Abnahmekriterium | Status |
|---|---|---|---|
| 1 — Vertrag und gemeinsame Ableitung | Zustandszuordnung und kleine Aufmerksamkeitsentscheidung im bestehenden Besitzer einführen; Richtungs-/Nahbereich bei 1x/2x kalibrieren; Darstellung anbinden | Wenige Tabellenfälle für frei/Cursor/links/rechts/Handfokus/Schlaf; Aktions- und Laufpriorität sowie Cursor-Einstellung bleiben korrekt. Keine Kopie der Aktionszustände. | Umgesetzt und automatisch geprüft |
| 2 — Ein Sichtentscheid für alle Belege | Positive Sichtungen, leere bekannte Plätze und beobachtete Cursorereignisse an dieselbe Aufmerksamkeit binden; bisherige Doppelentscheidungen entfernen | Handfokus ignoriert fremdes Umstellen; Blickrichtung begrenzt Beobachtung; echtes Cursorfolgen erhält Zuordnung, Sichtverlust nicht. Zugehörige Awareness-/Gaze-Tests direkt ersetzen. | Umgesetzt und automatisch geprüft |
| 3 — Rückkehr, Abgleich und Suchpriorität | Fokusfreigabe beginnt frischen Umgebungsnachweis vor freier Zielwahl; sichtbare Verluste gemeinsam übernehmen; vorhandene Suchroute über Fundaktionen erhalten | Zentraler Vier-Gegenstände-Ablauf, keine globale Blockade durch einen unklaren Platz, keine konsumierende Zwischenaktion und keine Suche nach einem verschwundenen unbekannten Fund. | Umgesetzt und automatisch geprüft |
| 4 — Test- und Inhaltsrückbau abschließen | R1–R3 und anschließend ihren ungenutzten Ersatzhelfer zurückbauen; offene Widerspruchs-/Receipt-Fälle separat entscheiden; weitere doppelte Fokus-/Blick-/Reihenfolgeaufbauten zusammenführen; Architektur-/Verhaltensdokumente angleichen | Jede Löschung nennt Umgehung oder veraltete Erwartung und verbliebenen Nachweis. Regeln der Erhaltungstabelle und gültige Grenztests bleiben abgesichert. Produktionsschutz nur nach eigenem Nutzungs-/Erreichbarkeitsnachweis entfernen; keine neuen Bubble-Ketten oder Save-Migrationen. | Umgesetzt und automatisch geprüft |
| 5 — Vollständige Regression und praktischer Übergabestand | Gesamtes geändertes System prüfen; aktuellen Stand und offene menschliche Abnahme dokumentieren | Vollständige Windows-Suite mit Python 3.11.9/Pillow 11.3.0; Ruff 0.13.2, striktes Mypy 1.18.2, Pyright 1.1.414, Dokumentationslinks und Diff-Prüfung; kombinierte native Abläufe zusätzlich unter installiertem Python 3.14 bei 1x/2x. | Automatisch vollständig geprüft; manuelle Sichtabnahme offen |

Bereits pro Umsetzungsetappe: betroffene Besitzer-Tests und Architekturgrenzen,
Ruff und beide Typprüfungen ausführen; native Integration bei Änderung von
Blickdarstellung, Cursorereignissen oder Übergängen prüfen. Vorhandene echte
Timer-Prüfungen bei Änderung von Lese-/Animationsübergängen beibehalten.
Keine Gates abschwächen, um ein neues Soll grün zu bekommen.

## Planungsnachweis und offene praktische Abnahme

Die folgenden Nachweise beschreiben die beiden reinen Planungsaufträge vor der
Umsetzungsfreigabe. Der aktuelle Lieferstand folgt im anschließenden Abschnitt.

Quellen und benannte Tests wurden für diesen Plan gelesen. Die letzten
1.102 Tests unter Python 3.11 und 52 nativen Tests unter Python 3.14 gehören
zum vorherigen [Etappe-7-Stand](OBJECT_SEARCH_SIMPLIFICATION_PLAN.md), nicht zu
einer Umsetzung dieses Plans. Für den reinen Dokumentationsauftrag ist kein
erneuter Lauf des unveränderten Anwendungscodes vorgesehen.

Prüfung der ersten Planungsfassung: Alle 15 benannten Test-/Modulreferenzen
existierten. Alle 199 lokalen Dateiverweise und 15 Abschnittsverweise in den
32 Markdown-Dokumenten im Repository-Hauptverzeichnis und unter `docs` lösten auf.
Dokument-Whitespace und `git diff --check` waren unauffällig. Ein SHA-256-Vergleich
bestätigte: Alle 788 zuvor vorhandenen Repository-Dateien waren unverändert;
hinzugekommen war ausschließlich dieses Plandokument.

Präzisierung nach anschließendem Code-/Testabgleich: R1–R3 wurden mit konkretem
Umgehungspfad und verbleibender Absicherung zum späteren Rückbau markiert.
Echte Handübergabe, Physik und die oben benannten Identitäts-/Besitz-/Speicherregeln
bleiben erhalten. Noch nicht belegte Unerreichbarkeit ist ausdrücklich als offen
markiert. Diese Präzisierung änderte ausschließlich dieses Dokument; damals war
keine Etappe begonnen und kein Test oder Produktionszweig entfernt worden.

Prüfung dieser Präzisierung: Alle 32 jetzt benannten Test-/Modulreferenzen
existieren; die 199 lokalen Dateiverweise und 15 Abschnittsverweise lösen
weiterhin auf. Whitespace-/Diff-Prüfung unauffällig. Der erneute Hashvergleich
bestätigt nur dieses Dokument als Änderung; die anderen 788 vorhandenen Dateien
sind bytegleich. Keine Dateien hinzugefügt oder gelöscht, keine Anwendungstests
erneut ausgeführt.

Bei späteren nativen Läufen ausschließlich temporäre Spielstände verwenden.
Die [bestehende manuelle Prüfliste](WORLD_SMOKE_TEST.md) bleibt unangetastet;
neue Sicht-/Fokus-Beobachtungen werden erst mit ihrer Umsetzung ergänzt und
automatische Ergebnisse nicht als menschliche Sichtabnahme ausgegeben.
Die ursprünglichen Planungsaufträge änderten ausschließlich dieses Dokument.
Die nachfolgend dokumentierte Etappe 1 ist separat freigegeben. Weitere Etappen
werden damit nicht vorweggenommen. Kein Commit, Push oder Merge.

## Lieferstand Etappe 1 — gemeinsame Ableitung und Darstellung

`choose_object_attention` in der vorhandenen Application-Koordination leitet
aus aktueller Interaktionsphase, Wach-/Spielzustand, laufender Bewegung und
vorhandenem Ziel die fünf fachlichen Aufmerksamkeitszustände ab. Der neue kleine
Wert `ObjectAttention` ist unveränderlich. Er enthält Modus und Blickvektor,
keine Erinnerung, veränderliche Aktionsphase oder zweite Bewegung.

`DesktopVisualObservation` normiert Augen-, Cursor- und Zielgeometrie und nutzt
die gemeinsame Entscheidung für die vorhandenen 16 Blickframes mit Hysterese.
Schmale Leseports beziehen Phase aus dem bestehenden World-Zugriff, Schlaf aus
PetState und Laufrichtung aus der vom Bewegungscontroller geführten Reststrecke.
Ein lediglich gesetztes, noch nicht ausgeführtes Bewegungsziel gilt nicht als
laufende Bewegung. Die vorhandene Animationssteuerung behält Aktion und Gehen
vor passivem Blick. Cursor-Einstellung und Pointer-Aktivitätsfenster bleiben
wirksam; explizite Objektziele funktionieren auch bei ausgeschaltetem Cursorblick.

Die reine Methode `sees_environment` beschreibt bereits die gemeinsame künftige
Sichtgrenze. **ObjectAwareness, Abwesenheitsprüfung und Cursor-Transportereignisse
verwenden sie noch nicht.** Das ist Etappe 2; die priorisierte Rückkehr zum
Umgebungsabgleich ist Etappe 3. Der gemeldete Vier-Gegenstände-Fehler ist durch
diesen ersten Schritt allein nicht als behoben anzusehen.

Technische Kalibrierung (Offsets in Körperbreiten ab Augenreferenz):

| Situation | Punkt / Richtung | Erwarteter Vertrag |
|---|---|---|
| Frei ohne gerichteten Blick | Punkt `(-0.5, -0.4)` | Im Nahfeld sichtbar |
| Frei ohne gerichteten Blick | Punkt `(2, -0.4)` | Außerhalb des Nahfelds nicht sichtbar |
| Unterwegs rechts / links | Punkt `(3, -0.4)` / `(-3, -0.4)` vor dem Blick | Sichtbar; derselbe Punkt hinter dem Blick außerhalb des Nahfelds nicht sichtbar |
| Cursorblick nach oben | Punkt `(2, 2)` gegenüber `(2, -2)` | Oberer Punkt sichtbar, unterer außerhalb des Nahfelds nicht sichtbar |
| Cursor rechts, sehr weit | Punkt `(7, 0)` | Außerhalb der normalen Umgebungsreichweite |
| Handfokus oder keine Beobachtung | Naher Punkt `(0.1, 0)` | Keine allgemeine Umgebungsbeobachtung |

Der Adapter prüft dieselben nativen Augen-/Zielabstände bei 1x und 2x. Bereits
vorhandene native Links-/Rechts-Pickup-Läufe bei beiden Skalen prüfen zusätzlich
die Anbindung an den echten Bewegungscontroller und den anschließenden Handfokus.
Kein neuer kombinatorischer Testbaum wurde dafür angelegt.

Prüfstand auf Windows, Python 3.11.9 / Pillow 11.3.0:

- **189 Objekt-Tests** grün; darin drei neue kompakte Vertragstests für Zustand,
  Priorität und geometrischen Umfang.
- **65 Architektur-/Adapter-/Blicktests** grün, einschließlich dieser drei
  Vertragstests, bestehender Modulgrenzen, Hysterese und Lauf-/Animationspriorität.
- **94 bestehende UI-/Animations-/Pointertests** grün in **29.656 Sekunden**.
  Diese umfassen GUI, isolierten Sprite, Schere-Stein-Papier, Food-GUI, Bewegung
  und Pointer-Laufzeit.
- **29 World-/Physik-/Persistenz-/Care-Origin-Prüfungen** grün. Die bestehenden
  Grenzen für Freigabe, Bodensammeln, springende Portionen, Besitz und
  Wiederherstellung bleiben abgesichert.
- Ruff 0.13.2, striktes Mypy 1.18.2 (185 Quellen) und Pyright 1.1.414 grün.
- **52 native World-/Echtzeit-Tests** grün in **125.626 Sekunden**, Exitcode 0,
  ohne übersprungene Tests. Enthalten sind Nahpaar-Neustart, gemeinsame Suche,
  beide Face-Reunion-Einstiege und beobachteter Transport sowie reale Timer für
  lesbare Cue-Reihenfolge, vollständige Animationen, Übergabe, Konsum und sichere
  Unterbrechung. Die bekannten nicht fehlschlagenden Tk-`ThemeChanged`-Meldungen
  beim Fensterabbau erschienen; die Tests liefen erfolgreich durch.

Die erweiterten UI-Prüfungen deckten eine zunächst zusätzlich eingeführte
Animationszeit-Sperre auf: Nach Schließen des Spiels blieb Cursorblick unnötig
blockiert. Diese doppelte Sperre wurde entfernt. Die vorhandene Spiel-/Aktions-
Priorität steuert weiter die Animation; der bestehende Wiederaufnahme-Test ist
unverändert grün. Kein Test wurde für diese Korrektur abgeschwächt.

R1–R3, ihr Ersatzhelfer und die offenen Schutzfälle wurden nicht zurückgebaut.
Identifikation, Zuordnung, SearchTask, Besitzwechsel, Physik, Care-/Konsumeffekte,
Spielstandformat und Dialogkatalog bleiben in dieser Etappe unverändert.
Der Vergleich mit dem Start dieser Etappe zeigt neun geänderte vorhandene Dateien
und zwei neue Dateien (Wertobjekt und dessen Vertragstests); 780 vorhandene Dateien
sind bytegleich. Auch die bestehenden Methoden von ObjectBehaviorCoordinator
sind laut AST-Vergleich unverändert; hinzugekommen ist die reine Ableitung.
Dokumentationslinks, Whitespace und `git diff --check` sind geprüft.
Temporäre Testspielstände wurden verwendet; keine neue menschliche Abnahme
oder vollständige Gesamtsuite wird behauptet. Die vollständige Regression und
Python-3.14-Übergabe bleiben Etappe 5. Kein Commit, Push oder Merge.

## Lieferstand Etappe 2 — gemeinsame Sichtgrenze für Wahrnehmungsbelege

Die vorhandene Aufmerksamkeitsentscheidung wird jetzt **vor** der Objektwahrnehmung
abgefragt. Derselbe unveränderliche Wert enthält Augenreferenz und Körperbreite;
der Desktop-Adapter übersetzt ihn in World-Koordinaten. Positive Kandidaten
werden vor Tracking und Erkennung gefiltert. Die Abwesenheitsprüfung verwendet
für erinnerte Plätze dieselbe Sichtgrenze. Die getrennten Radiusentscheidungen
in Awareness, Erkennung und Abwesenheitsprüfung sind dadurch entfallen.
`ObjectPerception` akkumuliert nur noch die zeitlichen Belege bereits zugelassener
Kandidaten; es entscheidet weiterhin ausschließlich über Hand-/Face-Identifikation.

Handfokus lässt fremde Sichtungen und leere fremde Plätze aus. Der eigene gehaltene
Gegenstand bleibt aufgrund des bestehenden Eigenaktionsnachweises beobachtbar.
Beim stationären Angehen und vor dem Griff bleibt der gewählte Bodenplatz mit
seinem bisherigen kleinen Platzradius prüfbar; das öffnet keinen Rundumblick.
Das eigene Ablegen behält seine Zuordnung bis zum Ende der laufenden Aktion.
Diese Kontinuität verwendet den vorhandenen Eigenaktionsbesitzer, keine zweite
Phasenmaschine und keinen weiteren Timer.

Eine Cursor-Aufnahme wird anhand der Aufmerksamkeit **beim tatsächlichen Start
der Geste, vor dem Zurücksetzen des alten Blickziels**, bewertet. Eine alte
World-/Memory-Bindung allein genügt nicht. Bereits beobachtetes Cursorfolgen wird
über einen reinen Leseport aus dem bestehenden Tracker abgeleitet; es kann den
Cursor über die normale Umgebungsreichweite hinaus verfolgen. Handfokus,
Schlaf/Spiel und echte Sichtunterbrechung geben keinen solchen Durchgriff.
Nach beobachtetem Landen endet die besondere Cursorbindung wie bisher.
Erinnerungswissen bleibt bei Sichtverlust erhalten; ausführbare Sichtbindung und
Erstidentifikation werden daraus nicht abgeleitet.

Beim Anhalten für laufende Sicht-/Leerplatzbelege bleibt der gerade verwendete
Blickvektor erhalten. Ohne diese Weitergabe wechselte der Suchlauf zwischen
gerichtetem Blick und ungerichtetem Nahfeld und begann denselben Sichtnachweis
immer wieder neu. Die Korrektur verwendet ausschließlich die Aufmerksamkeit
dieses Updates und die vorhandenen Nachweiszustände. SearchTask und Route sind
unverändert.

### Testanpassungen und erhaltene Regeln

- Zwei kompakte Awareness-Szenarien prüfen Handfokus mit vier umgestellten
  Gegenständen, anschließenden Wegblick, frische Sicht-/Leerplatzbelege beim
  Zurückblicken und die Ablehnung einer angeblich beobachteten Aufnahme aus einer
  alten Bindung. Ein zusätzlicher kleiner Aufmerksamkeitstest prüft Bodenfokus
  bis zum Griff, Handfokus und Cursor-/Laufpriorität bei 1x/2x.
- Direkte Besitzer-Fixtures geben ihren Blick jetzt ausdrücklich als Wert an.
  Die Tests übernehmen keinen Produktions-Rundumblick als Ersatzpfad.
  Der bisherige reine Erkennertest
  `test_no_attention_or_out_of_range_supplies_no_knowledge` entfällt, weil der
  Erkenner keine Geometrie mehr entscheidet. Seine fachliche Absicherung bleibt
  in `test_known_place_and_physical_reference_both_require_current_notice`, den
  gemeinsamen Geometrietests und den neuen integrierten Awareness-Prüfungen.
  Zeitbelege, Unterbrechung und die beiden erlaubten Identifikationswege bleiben
  in den übrigen Erkennertests erhalten.
- Bestehende native Fälle geben für entfernte Funde jetzt einen tatsächlichen
  Cursorblick vor und lassen Tk angeforderte Fensterbewegungen anwenden, bevor
  sie Augenkoordinaten lesen. Der Fall zur Wahrnehmung während eines Angehens
  führt die Bewegung tatsächlich aus. Die Face-Wiedervereinigung beim Angehen
  wartet auf Sichtkontakt entlang der echten Suchroute.
- Die zwei bestehenden gemeinsamen Suchläufe bei 1x/2x verwenden jetzt echte
  Cursor-Aufnahme/Freigabe mit Physik während der fremden Handuntersuchung.
  Dabei darf keine beobachtete Umplatzierung verbucht werden. Anschließend werden
  die Untersuchung und Ablage regulär abgeschlossen, bevor der Umgebungsnachweis
  erwartet wird. Die vorhandenen Fund-, Identifikations-, Suchrouten- und
  Gleichartigkeitsassertionen bleiben bestehen. Auch die kalten Nahpaar-Neustarts
  bleiben erhalten.
- Der bestehende Echtzeittest für Untersuchung/Ablage eines satten Onigiri bleibt
  unverändert. Er deckte eine zunächst zu früh gelöste Eigenaktionszuordnung auf;
  diese wurde im Besitzer korrigiert, statt die gültige Erwartung zu entfernen.
- R1–R3 und ihr Ersatzhelfer bleiben für Etappe 4 markiert. In dieser Lieferung
  wurde keiner dieser Fälle gelöscht. Besitz, Physik, Receipt-Reihenfolge,
  Konsum-/Care-Origin, Gedächtnisformate und Dialogkatalog werden nicht umgebaut.

### Prüfung dieser Etappe

Umgebung: Windows, Python **3.11.9**, Pillow **11.3.0**, temporäre Testspielstände.

- **191 Objekt-Tests** grün (zuletzt **1.008 Sekunden**). Gegenüber Etappe 1 drei
  kompakte Tests ergänzt und ein zur anderen Besitzergrenze verlegter
  Geometrie-/Aufmerksamkeitstest entfernt.
- **95 Architektur-/Adapter-/Blick-/World-Prüfungen** grün in **0.721 Sekunden**:
  66 Architektur-/Blickprüfungen einschließlich Aufmerksamkeit sowie 29 bestehende
  World-/Physik-/Persistenz-/Care-Origin-Prüfungen.
- Ruff **0.13.2** grün; striktes Mypy **1.18.2** über 185 Quellen grün;
  Pyright **1.1.414** ohne Fehler oder Warnungen.
- **146 native/UI-Tests** grün in **155.238 Sekunden**, Exitcode 0 und keine
  übersprungenen Tests: 46 World-GUI-, sechs Echtzeitablauf- und 94 weitere
  UI-/Animations-/Pointertests. Enthalten sind die kalten Nahpaar-Neustarts,
  gemeinsame Suche und beobachteter Transport bei beiden Skalen, Face-Reunion,
  echte Übergabe, vollständige Pickup-/Ablageclips, lesbare Receipt-Reihenfolge,
  Konsumursprung sowie unveränderte Wiederaufnahme des Cursorblicks nach Spielen.
  Die bekannten Tk-`ThemeChanged`-Meldungen beim Fensterabbau erschienen ohne
  Testfehler. Der zunächst fehlschlagende Echtzeit-Ablagefall ist nach der
  Korrektur der Eigenaktionszuordnung im abschließenden Lauf ebenfalls grün.

Reproduzierbarer Objekt-Prüfbefehl:

```powershell
uv run --no-project --python 'C:\Users\Alexa\AppData\Local\Programs\Python\Python311\python.exe' --with Pillow==11.3.0 python -B -m unittest discover -s tests -p 'test_object*.py' -q
```

Der SHA-256-Abgleich mit dem Beginn dieser Etappe bestätigt **19 geänderte
vorhandene Dateien und 772 bytegleiche Dateien**; keine Datei wurde hinzugefügt
oder gelöscht. Alle bisherigen Behavior-Testmethoden sind laut AST-Vergleich
unverändert; nur ihre gemeinsame Blick-Fixture wurde angepasst. Die Module für
SearchTask/Interaktionsphasen, Tracker-Zuordnung, Memory/Codec, Physik, Care und
Dialogdaten sind gegenüber dem Start dieser Etappe bytegleich.
Die 199 lokalen Dateiverweise und 15 Abschnittsverweise in den 32 Markdown-Dateien
lösen weiterhin auf; `git diff --check` ist unauffällig.

Der Architektur-/Adapterblock lädt `test_dependency_graph`,
`test_final_architecture_audit`, `test_canonical_owner_identity`,
`test_pet_mind_boundary`, `test_pet_movement_boundary`, `test_ui_architecture`,
`test_desktop_boundary`, `test_object_attention`, `test_desktop_visual_observation`,
`test_desktop_animation_runtime`, `test_world_access`, `test_gaze`,
`test_pet_gaze_boundary`, `test_cursor_observation`, `test_world_state`,
`test_world_falling`, `test_world_persistence` und `test_consumption_origin`
über `unittest.defaultTestLoader.loadTestsFromNames` mit `tests` im Suchpfad.
Der native/UI-Block lädt auf dieselbe Weise `test_world_gui`,
`test_world_runtime_flow`, `test_gui`, `test_animated_pet_isolation`,
`test_rock_paper_scissors_gui`, `test_food_gui`, `test_motion_animation` und
`test_pointer_runtime`; Tk-Läufe erfolgen nacheinander.

**Abgrenzung:** Der verpflichtende frische Umgebungsabgleich vor jeder freien
Zielwahl und die vollständige gemeinsame Verlustübernahme sind weiterhin Etappe 3.
Die zwei aktualisierten nativen Szenarien belegen die bestehenden Suchregeln unter
korrektem Sichtumfang; sie ersetzen diese noch ausstehende Übergangsregel nicht.
Etappen 3–5 wurden nicht begonnen. Kein normaler Spielstand verändert, keine neue
menschliche Sichtabnahme, keine vollständige Gesamtsuite und kein Python-3.14-Lauf
für diese Etappe behauptet. Kein Commit, Push oder Merge.

Praktisch noch offen: Nach Fokusfreigabe bei mehreren umgestellten Portionen
beobachten, welche Plätze innerhalb des tatsächlichen Blickfelds liegen; während
der Handuntersuchung dürfen keine fremden Verlust-/Fundmeldungen entstehen.
Anschließend Cursortransport einmal sichtbar und einmal während fremden Handfokus
prüfen. Automatische Tests ersetzen diese menschliche Spielbeobachtung nicht.

## Lieferstand Etappe 3 — Abgleich vor freier Zielwahl und gemeinsame Suche

Der frische Umgebungsabgleich verwendet weiterhin die vorhandenen zeitlichen
Platzbelege. Handfokus liefert keine Umweltbelege; bei seiner Freigabe müssen
sichtbare leere Plätze ihren Nachweis neu aufbauen. Neu ist die durchgängige
Priorität dieses Nachweises gegenüber freier Neugier, Konsumwunsch und Blickwahl:

- `ObjectAwareness.update` gibt bei laufenden oder noch nicht angenommenen
  Verlustbelegen ohne gebundenen Gegenstand kein freies Ziel aus. Das gilt auch
  für einen zuvor entstandenen `CONTINUING_WISH`. Die bestehende Wunschverwaltung
  wird dabei nicht künstlich abgebrochen oder um eine neue Sperrzeit erweitert.
- `ObjectBehaviorCoordinator.observe` hält währenddessen den schon verwendeten
  Blick. Ein schneller bemerkter neuer Fund darf ihn nicht vor Abschluss des
  Leerplatznachweises umlenken. Ohne gerichteten Blick bleibt nur das tatsächliche
  Nahfeld sichtbar. Verdeckte Plätze werden nicht als global geprüft behandelt.
- Bei aktiver Suche wird die freie Zielauswahl gesperrt. Eine erhaltene passive
  Konsumabsicht wird nicht als Blickziel einer Suchphase ausgegeben. Die bereits
  vorhandene `advance_search`-Koordination wählt sichtbare unbekannte Portionen
  zur Untersuchung und übernimmt sie über denselben Wunschbesitzer. Bestehende
  gebundene Kandidaten bleiben über ihre normalen Phasen erhalten.
- Die vorhandene Schleife übernimmt alle im aktuellen Durchlauf bestätigten
  Verluste in denselben SearchTask, bevor eine neue freie Aktion beginnen kann.
  Unklare Belegung verhindert nur den Leerbeleg dieses Platzes. Andere Verluste
  und die Untersuchung des unbekannten Belegers bleiben möglich.

Kein zusätzlicher Nachscan-/Verlustschalter, Timer, Aufmerksamkeitsdienst oder
zweiter Aktionsbesitzer wurde eingeführt. SearchTask, Suchroute,
Interaktionsphasen und Besitzübergänge bleiben unverändert. Der Abgleich gehört
zur vorhandenen Wahrnehmung und nicht zu einer neuen Bubble-Kette.

### Nachweise und angepasste Tests

Drei kompakte Behavior-Prüfungen ergänzen die bestehenden Besitzerprüfungen:

1. Ein neuer naher Fund liegt links, ein leerer bekannter Platz rechts. Der
   zurückgegebene Blick wird wie im nativen Adapter auf den nächsten Tick
   angewandt. Der Blick muss den Leerplatznachweis abschließen, bevor er sich
   zum neuen Fund dreht. Dieser Fall war vor der Korrektur rot: der Blick sprang
   auf den neuen Fund und verlor den bekannten Platz.
2. Ein bestehender Konsumwunsch darf den Abgleich nicht überspringen. Auch dieser
   Fall war vor der Korrektur rot: `CONTINUING_WISH` lieferte trotz laufendem
   Leerplatznachweis ein ausführbares Ziel. Jetzt kommt die Verlustreaktion zuerst.
3. Ein unbekannter Beleger am einen bekannten Platz verhindert weder den
   bestätigten Verlust eines anderen Gegenstands noch eine anschließende
   Untersuchung des Belegers innerhalb derselben Suche. Dessen Identität wird
   weder aus Typgleichheit noch aus der alten Platzbelegung übernommen.

Der vorhandene Test
`test_search_investigates_unknown_find_and_resumes_its_route` erwartet jetzt
korrekt kein freies Beobachtungsziel während der Suche. Nach der Auswahl durch
`advance_search` prüft er weiterhin denselben Untersuchungswunsch, die tatsächliche
Zuordnung, erhaltenen Routenfortschritt und das sichere Aufgeben eines
unerreichbaren Kandidaten. Es wurde keine dieser fachlichen Aussagen entfernt.

Die beiden bestehenden nativen Suchläufe wurden auf **vier gelernte Portionen**
erweitert: zwei nahe Dangos, Energy Drink und Onigiri, jeweils mit Neustart.
Während einer echten fremden Handuntersuchung werden alle vier über Cursor-
Aufnahme, Freigabe und Physik umgestellt. Währenddessen darf keine beobachtete
Transportzuordnung entstehen. Nach regulärem Abschluss wird ein gerichteter Blick
auf die alten Plätze hergestellt; ein neuer naher Cookie liegt auf der anderen
Seite. Alle vier sichtbaren Verluste müssen vor der ersten neuen Untersuchung
bestätigt sein. Anschließend gilt trotz Hunger und Durst:

- Genau eine gemeinsame Suche und echte Identifikation der zunächst unbekannten
  Funde; keine konsumierende Zwischenaktion.
- Nur die passende physische Portion löst ihren Verlust; beide Dangos bleiben
  getrennte Portionen.
- Bei 1x werden alle vier wiedergefunden; bei 2x wird eine Portion tatsächlich
  entfernt, sodass nach den übrigen Funden der volle Suchdurchlauf mit genau
  einer erfolglosen Abschlussmeldung nötig bleibt.

Der erweiterte 2x-Lauf deckte zusätzlich die freie Appetit-Blickwahl während der
Suche auf: Nach dem Ablegen eines Fundes zog ein bekannter Vorrat den Blick von
neuen Sichtbelegen weg. Der produktive Besitzer wurde korrigiert; die
Suchrouten- und Konsumgrenzen wurden nicht abgeschwächt.

R1–R3, ihr Ersatzhelfer und die offenen Receipt-/Widerspruchskandidaten wurden
nicht entfernt. Die vorhandenen Tests zu verschwundenen unbekannten Zielen ohne
Patrouille, verzögert übernommenen Verlusten, echter Handübergabe, beobachtetem
Cursortransport, kaltem Nahpaar-Neustart und tatsächlicher Routendeckung bleiben
erhalten. Der weitere Rückbau bleibt Etappe 4.

### Prüfung dieser Etappe

Windows mit Python **3.11.9** und Pillow **11.3.0**; ausschließlich temporäre
Testspielstände. Dieselben Prüfbefehle und Modullisten wie in Etappe 2:

- **194 Objekt-Tests** grün in **0.935 Sekunden**, gegenüber Etappe 2 drei neue
  Behavior-Prüfungen, keine Testlöschung.
- **95 Architektur-/Adapter-/Blick-/World-Prüfungen** grün in **0.719 Sekunden**.
- Die beiden erweiterten nativen Vier-Gegenstände-Suchläufe bei 1x/2x grün in
  **2.728 Sekunden**.
- Ruff **0.13.2**, striktes Mypy **1.18.2** über 185 Quellen und Pyright
  **1.1.414** grün; Pyright ohne Fehler oder Warnungen.
- **146 native/UI-Tests** grün in **152.961 Sekunden**, Exitcode 0, keine
  übersprungenen Tests: 46 World-GUI-Prüfungen, sechs Echtzeitabläufe und 94
  weitere UI-/Animations-/Pointerprüfungen. Die erweiterten Vier-Portionen-Läufe,
  Nahpaar-Neustarts, beide Face-Reunion-Einstiege, beobachteter Cursortransport,
  echte Übergabe, vollständige Animationen und unveränderte Lese-/Receipt-Regeln
  sind enthalten. Die bekannten Tk-`ThemeChanged`-Meldungen beim Fensterabbau
  erschienen ohne fehlschlagende Tests.

Der Hashvergleich zum Beginn dieser Etappe bestätigt **fünf geänderte vorhandene
Dateien und 786 bytegleiche Dateien**, ohne hinzugefügte oder gelöschte Dateien.
Produktiv ändern sich ausschließlich Awareness- und Behavior-Koordination.
Interaktionsphasen, SearchTask/Route, Tracker, reine Wahrnehmungs-/Abwesenheitsregeln,
Memory/Codec und die Echtzeit-Testmethoden sind gegenüber Etappe 2 bytegleich.
Der AST-Vergleich bestätigt drei zusätzliche Behavior-Tests, eine angepasste
bestehende Behavior-Prüfung und einen erweiterten nativen Szenariohelfer; alle
übrigen vorhandenen Testmethoden dieser zwei Module bleiben unverändert.
Die 199 lokalen Dateiverweise und 15 Abschnittsverweise in 32 Markdown-Dateien
lösen auf; `git diff --check` ist unauffällig.

**Abgrenzung:** Etappen 4–5 sind nicht begonnen. Die gemeinsame Sichtgrenze,
Identifikation nur in Hand oder bewusster Gesichtspräsentation, Wiedererkennen am
exakten bekannten Platz, beobachtete Kontinuität, Besitz, Physik, Gedächtnisformate
und einmalige Konsumeffekte bleiben erhalten. Keine neue menschliche
Sichtabnahme oder vollständige Gesamtsuite und kein Python-3.14-Lauf für diese
Etappe behauptet. Kein Commit, Push oder Merge.

## Lieferstand Etappe 4 — belegter Test- und Inhaltsrückbau

R1–R3 und ihr ausschließlich dafür verwendeter `_replace_recalled_portion`-Helfer
sind entfernt. Die Nutzungssuche über `aiko_pet`, `tests`, `tools` und `docs`
bestätigt: außerhalb der drei markierten Tests gab es keinen Aufrufer des Helfers.
Es entsteht kein neuer Teleport-/Ersatzzuordnungsweg. Die Cookie-Definition im
betroffenen Retrieval-Fixture war nur für diesen Ersatzaufbau nötig und entfällt.

| Entfernte Aussage | Warum sie entfällt | Verbleibender Nachweis |
|---|---|---|
| R1: verwaister, ohne Awareness-Zuordnung direkt in die Hand gesetzter Gegenstand wird nachträglich entdeckt | Der reguläre Übergabeeinstieg verlangt Record, aktuelle Wahrnehmung und Reichweite; dieser Wiederherstellungspfad umging sie. | `test_unpresented_unknown_item_is_accepted_and_identified_in_hands`, Hand-/Face-Dwell-Tests und World-Custody-Grenzen |
| R2: andere gleichartige Portion wird unter erzwungener alter Bindung sofort als Vorrat gegessen | Privater `_resolve_instance`-Ersatz umging die erforderliche Wahrnehmung/Identifikation. | reguläre Retrieval-Tests, `test_other_same_type_portion_cannot_end_physical_subject_search`, nahe Same-type-Neustarts und native Vier-Portionen-Suche |
| R3: Cookie wird unter erzwungener Apfelbindung gesammelt und nachträglich korrigiert | Derselbe künstliche Ersatz-Resolver; der echte unbekannte Austausch bleibt zulässig. | `test_unknown_replacement_at_learned_place_never_borrows_identity`, `test_unseen_cookie_replacement_does_not_get_consumed_as_known_apple` und die separate Konsum-Typgrenze |

### Offene Kandidaten entschieden und gültige Regeln erhalten

- Der Schutz `held_type_conflicts_with_memory` bleibt produktiv verdrahtet.
  Memory v1–v3 und StateStore validieren Erinnerung und World getrennt; auch ein
  syntaktisch gültiges v3-Gedächtnis kann eine gelernte Identität enthalten, die
  zur aktuellen World-Definition des erworbenen Verweises widersprüchlich ist.
  Der frühere mitten im Pickup erzwungene Memory-Widerspruch wird durch
  `test_restored_conflicting_knowledge_requires_hand_inspection` ersetzt:
  tatsächliches Encode/Decode des unterstützten Formats, Wiederherstellung vor
  dem Abruf, bestätigtes Greifen, anschließend zwingende Handprüfung ohne Konsum.
  Der Test zeigt, dass Entfernen des Schutzes den gültigen Sicherheitsvertrag
  verlieren würde. Er führt keine Identifikation aus World-Wahrheit ein.
- Der alte Recognition-Receipt-Fall heißt jetzt
  `test_pending_preinspection_loss_waits_for_readable_recognition`.
  Sein unveränderlicher Verlustbeleg stammt ausdrücklich vom alten leeren Platz
  **vor** der Handaktion; der Gegenstand liegt inzwischen anderswo. Die spätere
  Übergabe dieses vorbereiteten Faktenwerts an den Phasenbesitzer repräsentiert
  eine verzögerte Reaktion, keine neue Wahrnehmung während der Untersuchung.
  Gültigkeit des aktuellen Receipts, genau eine Fundmeldung, kein Konsum,
  sicheres Ablegen und Wiederaufnahme der anderen Suche bleiben geprüft.
- Die frühere allgemeine Blickauswahlprüfung wird zu
  `test_blocked_observation_uses_only_current_attention_without_episode`:
  Ein geometrisch näherer verdeckter Gegenstand darf weder Bindung noch Blickziel
  liefern; der sichtbare Kandidat darf bemerkt werden, ohne eine gesperrte Aktion
  zu beginnen. Die gemeinsame Sichtentscheidung bleibt in `ObjectAttention`.
- Der bestehende Nachweis während gerichteter Bewegung heißt nun
  `test_moving_attention_keeps_target_and_observes_forward_changes`.
  Nur der Name ändert sich; Aufbau und Assertions bleiben bytegleich. Handfokus
  und spätere Platzprüfung sind getrennt durch die bestehenden integrierten
  Awareness-/Vier-Gegenstände-Läufe abgesichert.

Weitere gleich aussehende Aufbauten wurden nicht pauschal gelöscht: reine
Blickgeometrie, native Koordinaten-/Hystereseanbindung, Sichtungs-/Memory-Zuordnung,
World-Besitz und Receipt-/Animationsreihenfolge prüfen unterschiedliche Besitzer.
Die offenen Kandidaten sind damit konkret entschieden; es wird keine neue
Fallmatrix für dieselbe Blickpriorität angelegt. Außer R1–R3 entfällt kein Test.

### Dokumentation und Umfang

[Architektur](ARCHITECTURE.md), [Verhaltensvertrag](WORLD_OBJECT_CONTRACTS.md) und
[manuelle Prüfliste](WORLD_SMOKE_TEST.md) beschreiben jetzt die gemeinsame
Aufmerksamkeitsableitung und Sichtgrenze, fehlende Umweltbelege während Handfokus,
frische Platzprüfung mit stabilem Blick und Suchpriorität vor Neugier/Appetit.
Die widersprüchliche pauschale Umgebungswahrnehmung bei jeder gebundenen Aktion
ist korrigiert. Die frühere Aussage, eine andere gleichartige Portion am alten
Platz sei bereits bekannter Vorrat, ist im praktischen Austauschcheck korrigiert.
Frühere Lieferpläne bleiben als Historie erhalten. Neue manuelle Punkte sind
weiterhin offen; automatische Läufe werden nicht als menschliche Abnahme markiert.

**Kein Produktionscode, Dialogkatalog oder Spielstandformat wurde geändert.**
Vier bestehende Testmethoden werden präzisiert/umbenannt, drei entfernt und ein
nicht mehr verwendeter Helfer entfernt. Identifikation, exakter bekannter Platz,
beobachtete Kontinuität, Physik, Handübergabe, sichere Unterbrechung, SearchTask,
tatsächliche Routendeckung und einmalige Ernährung/Care bleiben unverändert.

### Prüfung dieser Etappe

Windows, Python **3.11.9** und Pillow **11.3.0**, temporäre Spielstände:

- **191 Objekt-Tests** grün in **0.867 Sekunden**; gegenüber Etappe 3 genau drei
  Tests weniger, kein neuer Test. Die vier präzisierten Fälle ersetzen ihre
  bisherigen Methoden innerhalb derselben Besitzerpakete.
- **95 Architektur-/Adapter-/Blick-/World-Prüfungen** grün in **0.770 Sekunden**.
- Ruff **0.13.2**, striktes Mypy **1.18.2** (185 Quellen) und Pyright **1.1.414**
  grün; Pyright ohne Fehler oder Warnungen.
- **52 native World-/Echtzeit-Prüfungen** grün in **127.074 Sekunden**,
  Exitcode 0, keine übersprungenen Tests. Darin bleiben Vier-Portionen-Suche und
  Nahpaar-Neustarts bei 1x/2x, beide Face-Reunion-Einstiege, beobachteter Transport,
  echte unbekannte Handübergabe, abgelehnte Übergabe mit Fallen, tatsächliche
  Animationen und Lese-/Receipt-Reihenfolge abgesichert. Die bekannten
  Tk-`ThemeChanged`-Meldungen beim Fensterabbau verursachten keine Testfehler.

Der SHA-256-Vergleich zum Etappenbeginn bestätigt **acht geänderte bestehende
Dateien und 783 bytegleiche Dateien**, ohne hinzugefügte oder gelöschte Dateien.
Alle Dateien unter `aiko_pet` und `tools` sind bytegleich; der Produktivablauf
bleibt vollständig auf dem praktisch getesteten Etappe-3-Stand.
Die erneute Nutzungssuche findet keinen der entfernten Helfer-/Testnamen mehr in
Anwendung, Tests oder Tools. Historische Erwähnungen bleiben im Plan erhalten.
204 lokale Dateiverweise und 15 Abschnittsverweise in 32 Markdown-Dateien lösen
auf; `git diff --check` ist unauffällig.

Es gelten die Prüfbefehle und Modullisten aus Etappe 2; der native Block lädt
hier `test_world_gui` und `test_world_runtime_flow` nacheinander. Die umfassende
Gesamtsuite und der zusätzliche Python-3.14-Lauf bleiben Etappe 5.
Etappe 5 ist nicht begonnen. Kein normaler Spielstand verändert, keine neue
menschliche Abnahme und kein Commit, Push oder Merge.

## Lieferstand Etappe 5 — vollständige Regression und Übergabestand

Der Abschluss prüft den unveränderten Produktions-/Teststand von Etappe 4.
Die bisherige lokale Arbeit bleibt erhalten; diese Etappe ändert zunächst nur
dieses Plandokument. Die Gesamtsuite wird über `unittest discover` ausgeführt,
Tk-Läufe erfolgen nacheinander. Prüfung und manuelle Abnahme bleiben getrennt.

### Umgebungen und Befehle

- Vollständige Windows-Suite: Python **3.11.9**, Pillow **11.3.0**, Tk **8.6**.
- Zusätzlicher nativer Gegenlauf: installiertes Python **3.14.0**, Pillow
  **12.3.0**, Tk **8.6**, mit denselben 1x/2x-Szenarien.
- Ruff **0.13.2**, striktes Mypy **1.18.2**, Pyright **1.1.414**.

```powershell
uv run --no-project --python 'C:\Users\Alexa\AppData\Local\Programs\Python\Python311\python.exe' --with Pillow==11.3.0 python -B -m unittest discover -s tests -q
uvx --from ruff==0.13.2 ruff check aiko_pet tests main.py tools
uv run --no-project --python 'C:\Users\Alexa\AppData\Local\Programs\Python\Python311\python.exe' --with Pillow==11.3.0 --with mypy==1.18.2 python -m mypy --strict --no-incremental aiko_pet main.py tools
uv run --no-project --python 'C:\Users\Alexa\AppData\Local\Programs\Python\Python311\python.exe' --with Pillow==11.3.0 --with pyright==1.1.414 python -m pyright --project pyrightconfig.json
git -c core.safecrlf=false diff --check
```

Der native Gegenlauf lädt in einem frischen Prozess unter installiertem Python
`test_world_gui` und `test_world_runtime_flow`. Er verwendet ausschließlich
temporäre Spielstände:

```powershell
@'
import sys, unittest
sys.path.insert(0, 'tests')
suite = unittest.defaultTestLoader.loadTestsFromNames(['test_world_gui', 'test_world_runtime_flow'])
result = unittest.TextTestRunner(verbosity=1).run(suite)
sys.exit(not result.wasSuccessful())
'@ | python -B -
```

### Ergebnisse

- Vollständige Windows-Suite unter Python **3.11.9 / Pillow 11.3.0**:
  **1.108 Tests grün in 240.856 Sekunden**, Exitcode 0, keine übersprungenen
  Tests. Enthalten sind alle Objekt-, Architektur-, Besitz-, Persistenz-,
  Care-/Konsum-, Dialog-/Ressourcen-/Asset-, Setup-, GUI- und Echtzeitprüfungen.
  Die bekannten Tk-`ThemeChanged`-Meldungen beim Fensterabbau waren nicht
  fehlschlagend. Zwei Asset-Prüfungen bestätigten jeweils 120 Posen bei 192×208
  ohne Änderung der Originalgrafik.
- Zusätzliche native World-/Echtzeitläufe unter Python **3.14.0 / Pillow 12.3.0**:
  **52 Tests grün in 125.090 Sekunden**, Exitcode 0, **0 Fehler, 0 Fehlschläge,
  0 übersprungene Tests**. Enthalten sind die Vier-Portionen-Suche mit allen
  gefundenen beziehungsweise einer fehlenden Portion, Nahpaar-Neustarts und
  beobachteter Transport bei 1x/2x, beide Face-Reunion-Einstiege, echte Übergabe,
  vollständige Pickup-/Put-down-/Konsumclips und reale Lese-/Receipt-Zeiten.
- Ruff grün; Mypy grün über **185 Quellen**; Pyright **0 Fehler, 0 Warnungen**.
- Die Windows-Desktop-Imports aus dem CI-Gate sind unter Python 3.11 erfolgreich:
  `aiko_pet.gui`, `aiko_pet.desktop.global_input`, `aiko_pet.desktop.window_stack`
  und `aiko_pet.desktop.taskbar`.
- **205 lokale Dateiverweise und 15 Abschnittsverweise** in 32 Markdown-Dateien
  lösen auf; `git diff --check` unauffällig.
- Die vollständige Testentdeckung sammelt **1.108 Tests**. Zusätzlich sind 20
  zentrale Schutzfallreferenzen gegen die tatsächlich vorhandenen Testmethoden
  geprüft: Handübergabe, Physik, erlaubte Identifikation, getrennte Portionen,
  Nahpaar-Neustarts, beobachteter Transport, frischer Abgleich, Suchpriorität,
  Routendeckung und erhaltene Widerspruchs-/Receipt-Grenzen.

Der SHA-256-Vergleich mit dem Beginn dieser Etappe bestätigt ausschließlich dieses
Plandokument als Änderung: Die übrigen **790 Repository-Dateien** sind bytegleich.
Keine Dateien wurden hinzugefügt oder gelöscht. Kein Produktions-/Testfix war
für die Abschlussprüfung erforderlich; keine Schutzregel und kein Gate wurde
abgeschwächt. Branch `feature/world-foundation` und HEAD sind unverändert. Vorhandene lokale
Änderungen wurden weder zurückgesetzt noch überschrieben.

### Praktische Übergabe

Die aktuelle [manuelle Prüfliste](WORLD_SMOKE_TEST.md) bleibt für menschliche
Sicht-/Eingabeabnahme offen. Besonders zu beobachten sind vier Umplatzierungen
während einer Handuntersuchung, danach der gerichtete Abgleich ohne vorzeitiges
Wegdrehen zu einem neuen Fund, eine gemeinsame Suche trotz Hunger/Durst und
sichtbarer gegenüber während Handfokus unbeobachteter Cursortransport. Dieselben
zwei nahen Portionen müssen bei Neustart ohne erneute Identifikationsschleife
wiedererkannt werden. Nur die jeweils sichtbaren Plätze liefern Verlustbelege.

Automatisierte native Fenster-/Timerprüfungen ersetzen diese menschliche Abnahme
nicht. Keine Änderung am normalen Spielstand; kein Commit, Push oder Merge.

Die automatische Umsetzung und Abschlussprüfung dieses Plans ist damit beendet.
Der nächste fachliche Nachweis ist der menschliche Testlauf anhand der offenen
Prüfliste; dessen Ergebnis wird nicht vorweggenommen. Nichts wurde gemergt.

## Praxisrückmeldung und gezielter Nachtrag — einzelne Verlustmeldungen

Die anschließende menschliche Praxisabnahme bestätigt den beobachteten Ablauf:
Aiko hielt und aß einen Gegenstand, während drei andere bekannte Portionen
unbeobachtet umplatziert wurden. Danach meldete sie einen Verlust, suchte und
fand alle drei Portionen wieder. Offen blieb ausschließlich die sichtbare
Meldung für jede weitere vermisste Portion. Diese Rückmeldung bestätigt dieses
Szenario, nicht pauschal alle offenen Punkte der manuellen Prüfliste.

### Begrenzter Fix und erhaltene Regeln

1. Ursache: `notice_absence` nahm weitere bestätigte Verluste über `SearchTask.add`
   an und quittierte sie gegenüber Awareness, erzeugte dabei aber keine Bubble.
2. Der vorhandene Interaktionsbesitzer hält diese zusätzlichen Meldungen in einer
   kleinen FIFO. Jede verwendet den eigenen Record und die eigene gelernte
   Identität sowie einen eindeutigen bestehenden Auxiliary-Receipt-Schlüssel.
   Die nächste Meldung wartet auf die aktuelle Lesebestätigung. Vor der Patrouille
   beziehungsweise bei weiteren Verlusten während der Suche werden sie einzeln
   ausgespielt; die Suchansage erscheint weiterhin nur einmal.
3. Die bestehende Suchaufgabe, ihre Portionenzuordnung und Routendeckung bleiben
   erhalten. Handphasen werden nicht unterbrochen. Bereits wiedergefundene
   Portionen erhalten keine nachträgliche veraltete Verlustmeldung; expliziter
   Abbruch verwirft die verbleibenden Meldungen zusammen mit der Aufgabe.
4. Wahrnehmungsfeld, Blick-/Aufmerksamkeitsentscheidung, lokale Verlustbelege,
   Hand-/Face-Identifikation, Physik, Konsum und Persistenz bleiben unverändert.
   Die vorhandenen Dialogtexte werden mit dem jeweiligen Gegenstand formatiert.
   Keine neue Phase, kein weiterer Suchbesitzer und keine UI-Warteschlange.

### Prüfung und Lieferstand

Die fokussierten Objekttests sind nach der Ergänzung grün: **193 Tests**.
Zwei kleine Regressionen prüfen die individuellen Receipts mehrerer Verluste
und einen weiteren Verlust bei bereits halb abgelaufener Route. Der vorhandene
Endpunkttest wartet nun auf die zusätzliche Verlustmeldung, bevor er die Suche
abschließt. Der bestehende Vier-Portionen-Neustartfall bei 1x/2x verlangt jetzt
auch genau eine korrekt zugeordnete Verlustmeldung je Portion, einschließlich
der beiden Dangos. Ein nativer Timerfall prüft drei sichtbar benannte Bubbles
mit echten Lesezeiten vor der gemeinsamen Patrouille.

Ruff ist grün, striktes Mypy über **185 Quellen** ist grün und Pyright meldet
**0 Fehler, 0 Warnungen**. Der separate native Block mit `test_world_gui` und
`test_world_runtime_flow` besteht **53 Tests in 139.132 Sekunden**, ohne Skip.
Damit sind die 1x/2x-Neustart-/Suchszenarien und die neuen tatsächlichen
Bubble-Lesezeiten abgesichert. Die bekannten Tk-`ThemeChanged`-Meldungen beim
Fensterabbau waren dabei nicht fehlschlagend.

Der erste Gesamtlauf über die unveränderte Standardentdeckung brach dagegen
prozessweit bei Tk-Bildbereinigung ab: `Image.__del__` meldete den falschen
Thread, anschließend `Tcl_AsyncDelete: async handler deleted by the wrong thread`.
Dieser Lauf liefert deshalb **kein vollständiges grünes Testergebnis**.
Der Wiederholungslauf verwendet dieselben entdeckten Tests mit ausgeschalteter
automatischer zyklischer GC und explizitem `gc.collect()` in `stopTest` auf dem
Hauptthread. Das ist ausschließlich der externe Prüfharness; Anwendung und
Repository-Testinfrastruktur werden dafür nicht geändert.

```powershell
@'
import gc, sys, unittest
gc.disable()
class MainThreadCollectionResult(unittest.TextTestResult):
    def stopTest(self, test):
        super().stopTest(test)
        gc.collect()
r = unittest.TextTestRunner(verbosity=1, resultclass=MainThreadCollectionResult).run(
    unittest.defaultTestLoader.discover('tests'))
sys.exit(not r.wasSuccessful())
'@ | uv run --no-project --python 'C:\Users\Alexa\AppData\Local\Programs\Python\Python311\python.exe' --with Pillow==11.3.0 python -B -
```

Die vollständige Wiederholung ist abgeschlossen: **1.111 Tests grün in 260.815
Sekunden**, Exitcode 0, keine übersprungenen Tests. Eingeschlossen sind Objekt-,
Architektur-, Persistenz-, Konsum-, Ressourcen-, UI- und native Timerprüfungen.
Der Standardlauf-Abbruch bleibt davon getrennt dokumentiert; der erfolgreiche
Gesamtnachweis gilt für den oben beschriebenen Hauptthread-GC-Harness.
Keine Anwendungsausnahme und kein Test wurden für diesen Nachweis unterdrückt.

**205 lokale Dateiverweise und 15 Abschnittsverweise** in 32 Markdown-Dateien
lösen auf; `git diff --check` ist unauffällig. Der Hashvergleich zum Beginn
dieses gezielten Nachtrags zeigt nur sieben geänderte Dateien: den bestehenden
Interaktionsbesitzer, drei Tests sowie Plan, World-Vertrag und manuelle Prüfliste.
Die übrigen **784 Repository-Dateien** sind bytegleich, keine Datei wurde
hinzugefügt oder gelöscht. Branch `feature/world-foundation` und HEAD bleiben
unverändert. Der normale Spielstand wurde nicht verwendet.

Der Fix ist automatisch geprüft. Der sichtbare praktische Nachtest der einzelnen
Verlust-Bubbles bleibt offen; die vom Benutzer bereits bestätigte gemeinsame
Suche bleibt erhalten. Kein Commit, Push oder Merge.

## Praxisnachtrag — bereinigter Spielstand und Statusüberblick

Nach dem Neustart wirkt das Verhalten laut Benutzer grundsätzlich richtig.
Zusätzliche Onigiri-Verlustmeldungen waren wegen alter Testhistorie nicht mehr
eindeutig interpretierbar. Der tatsächlich aktive normale Spielstand wurde
daher auf ausdrücklichen Wunsch einmalig ohne neue Sicherung bereinigt:
48 alte Vermisst-Einträge und sieben weitere verwaiste/unzugeordnete historische
Einträge wurden entfernt. Die fünf aktuell vorhandenen, bereits identifizierten
Portionen behalten ihre gültigen physischen Referenzen und ihre unveränderten
Plätze; alte Assoziationen zu entfernten Einträgen sind gelöscht. World, Pet,
Einstellungen und Allokationszähler bleiben erhalten. Die App wurde zuvor
regulär beendet, damit Autosave die Bereinigung nicht überschreibt.
Das ist keine automatische Bereinigung oder neue Persistenz-/Wahrnehmungsregel.

Die ausgeklappten Statusdetails zeigen nun tatsächliche liegende Desktop-Portionen,
identifizierte Erinnerungen, eindeutige erinnerte Zuordnungen und bestätigte
Verluste getrennt. `application/object_status.py` liefert nur einen unveränderlichen
Read-Snapshot aus den bestehenden Besitzern. Die Ansicht liefert keinerlei neue
Erkenntnis an Aiko zurück. Historische `superseded`-Zeugen zählen nicht als Bestand;
gleiche Typen zählen pro Portion. Die genaue Semantik und Darstellung stehen im
[UI-Vertrag](UI_WINDOW_CONTRACT.md).

Laune steht als breiter Gesamtbalken über den sechs Einzelanzeigen. Spaß belegt
den früheren Laune-Platz zwischen Sättigung und Energie, mit eigenem Balken;
die bisherige separate Spaß-Prozentzeile in den Details entfällt. Domänenwerte,
Bedürfniswirkung und Launenberechnung sind unverändert.

Die fokussierte Prüfung besteht **111 Tests** für Objektstatus, Projektionen,
UI-/Architekturgrenzen, Ressourcen und native GUI. Ruff, striktes Mypy über
**186 Quellen** und Pyright sind grün. Der Abschlusslauf mit allen Tests verwendet
den oben dokumentierten Hauptthread-GC-Harness: **1.113 Tests grün in 257.221
Sekunden**, Exitcode 0, keine übersprungenen Tests. Die bestehenden Such-,
Nahpaar-Neustart-, Hand-/Face-, Konsum- und Timerprüfungen bleiben enthalten.

Zusätzlich wurde die echte Tk-Toolbar mit ausgeklappten Details in einer
temporären Fünf-Portionen-Fixture angezeigt und ihr vollständiger Screenshot
bei **150 % Windows-Skalierung** visuell geprüft. Alle sieben Balken und die
Zähler **5 Desktop / 5 bekannt / 5 zugeordnet / 0 vermisst** sind lesbar und
ungekürzt. Der erste Screenshot mit logischen statt physischen Bounds war nur
ein unvollständiger Capture; die abschließende Kontrolle verwendet physische
Window-Bounds. Die Fixture wurde gelöscht, der normale Spielstand dafür nicht
verändert. Die bereinigte echte Session wurde mit dem zuvor verwendeten Python
**3.14** regulär neu gestartet: Prozess und sichtbare Aiko-Fenster laufen,
der Start-Fehlerlog ist leer. Der anschließend gelesene normale Spielstand enthält
weiterhin **5 World-Portionen / 5 Erinnerungen / 0 vermisst**. Die Anzahl bereits
vorhandener Sicherungsdateien bleibt unverändert; keine neue Sicherung entstand.
Die menschliche Praxisabnahme nach diesem UI-Nachtrag bleibt offen.
Kein Commit, Push oder Merge.
