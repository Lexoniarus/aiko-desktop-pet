# Fixplan Formular und Aikos Handlungen entkoppeln

Hover über Aiko soll das Status- und Aktionsformular öffnen, ohne eine laufende
Handlung abzubrechen, anzuhalten oder ihren nächsten Schritt zu verhindern.
Auch das Betrachten, Offenhalten, Verschieben und Durchblättern des Formulars
ist kein neuer Auftrag an Aiko. Erst eine konkrete Interaktion darf die
bestehende Aktionssteuerung um eine zulässige Unterbrechung bitten.

Status am 30. Oktober 2026: **Alle fünf Etappen und beide Nachbesserungen
umgesetzt, in zehn fachlichen Commits getrennt und abschließend geprüft.**
Die ursprünglichen Prüfprotokolle unten gehören zum damaligen uncommittierten
Stand. Die anschließende kritische Nachprüfung fand zwei weitere Abbruchpfade
über Fokusverlust und Klicks in die Einstellungen. Beide sind mit eigenen
Regressionstests geschlossen. Die aktuellen Ergebnisse stehen unter
[Commitfolge und Abschlussprüfung](#commitfolge-und-abschlussprüfung).
Prüfgrundlage ist der lokale Arbeitsstand auf `feature/social-optimization`,
`HEAD 3acabeebc358e4642341eb864254074ef3b0a3a6`, einschließlich der vorhandenen
uncommitteten Social-Änderungen. Die aktuelle Spielpräsentation aus dem
[Spielplan](GAME_FRONTEND_IMPLEMENTATION_PLAN.md) gehört zu dieser Grundlage.
Ältere Testergebnisse dieses Chats ersetzen die folgende erneute Prüfung nicht.

## Kopplungen im geprüften Ausgangsstand

| Pfad | Aktuelle Wirkung | Konsequenz für den Fix |
| --- | --- | --- |
| [`ContactCoordinator.enter`](../aiko_pet/application/contact.py), aufgerufen durch natives Enter und Hover-Polling | Kann Rückkehr-/Essensabwechslungsreaktionen auswählen und `interrupt_walk` aufrufen. In der Desktop-Verdrahtung führt das über `World.interrupt`, einschließlich Freigabe von Absicht und Bewegungsziel. Ausnahmen schützen bereits bestimmte aktive Besitzer. | Den passiven Hover-Einstieg von akzeptiertem direktem Kontakt trennen. |
| [`HoverUi.menu_engaged`](../aiko_pet/ui/windows/hover_ui.py) | Mischt Sichtbarkeit, Offenhalten, Maus über Formular/Übergangsbereich, Ziehen, Tastatureingaben, Untermenüs und Einstellungen. | Dieser UI-Zustand darf keine Verhaltenszulassung mehr liefern. |
| [`PointerRuntime.control_active`](../aiko_pet/desktop/pointer_runtime.py) | Kann auch ohne Klick allein wegen zugelassenem Hover wahr sein. `_access_claimed` bleibt bis zum Verlassen der UI und Ende der Menübedienung gesetzt. | Keine räumlich festgehaltene Bedienungssperre; ausdrücklichen Kontakt als Ereignis behandeln. |
| [`DesktopInput.on_menu`](../aiko_pet/desktop/input.py) | Shift-Rechtsklick beansprucht bereits Cursorzugriff, bevor nur die Einstellungen geöffnet werden. | Das Öffnen eines Fensters darf keinen Charakterkontakt beanspruchen. |
| [`WalkDriver.step`](../aiko_pet/desktop/walk_runtime.py) und [`WalkController.plan_step`](../aiko_pet/pet/movement/controller.py) | `hard_access`/`menu_engaged` verhindern Bewegung; Cursoraufträge werden entfernt und Idle-Abgänge verschoben. Ein World-Ziel bleibt erhalten, kommt aber nicht voran. | Beide Sperrpfade einschließlich ihrer Verträge entfernen. |
| [`CursorBehaviourCoordinator`](../aiko_pet/application/cursor_behaviour.py) und [`pause_for_menu`](../aiko_pet/pet/mind/cursor_behaviour.py) | Menübedienung ersetzt Annäherung/Flucht durch Beobachten, verändert zeitliche Evidenz und verwirft Warnungen. Die Bewegungszulassung blockiert zusätzlich. | Formularzustand aus Auswahl und Zulassung entfernen, nicht nur aus dem Renderer. |
| [`DesktopAttentionRuntime`](../aiko_pet/desktop/attention_runtime.py) und [`AttentionCoordinator`](../aiko_pet/application/attention.py) | Unterdrücken Cursorhinweise, spontane Bedürfnis-/Wunschäußerungen und Benachrichtigungen. Eine vorbereitete Wunschgeste wird verworfen. | UI-Sperren an Adapter und Policy gemeinsam entfernen. Reale Sprach-/Aktionsbesitzer bleiben geschützt. |
| [`HoverUi.refresh_hover`](../aiko_pet/ui/windows/hover_ui.py) → `record_contact` | Aufenthalt über Aiko, Formular oder Übergangsbereich aktualisiert `mind.last_contact`. Das beeinflusst Rückkehrreaktionen, schreibt aber keine dauerhafte Pflegegutschrift. | Sichtbarkeitstiming und tatsächlichen Kontakt getrennt halten. |
| [`ActionToolbar.hide`](../aiko_pet/ui/windows/action_toolbar.py) → `close_selector` → `close_social_menu` → `SocialMenu.close` → `_social_menu_closed` | Automatisches Ausblenden ruft dasselbe `social_cancel` auf wie ausdrückliches Schließen. Ein angeforderter, noch ausstehender Inhalt verliert seinen Auswahl-Token. | Anzeige schließen und Anforderung stornieren benötigen unterschiedliche Gründe. Das ist keine Aussage darüber, ob ein HTTP-Aufruf im Hintergrund beendet wird. |

Die World-Auswahl bekommt in `BehaviorFacts` bereits tatsächliche
Aktionsbesitzer statt eines Menüflags. Die indirekte Blockade sitzt weiterhin
im gemeinsamen Bewegungsadapter. Die Ausnahme `menu_engaged and not committed`
in dessen späteren `WalkConditions` hilft nicht: Die frühe Rückkehr in `step`
erfolgt davor. Die Aussage in [Architecture](ARCHITECTURE.md), Menübedienung
blockiere keine verbindliche Objektbewegung, stimmt damit im Prüfstand nicht.

Die Lebenszeit und Bedürfnisentwicklung laufen weiter. Hover stoppt auch nicht
pauschal jede Animation: Der aktuelle native Fixture-Test lässt die vollständige
Trinkanimation trotz Enter-Ereignis zu Ende laufen. Der Fix soll die nachgewiesenen
UI-Einflüsse entfernen, ohne diese bereits funktionierenden Schutzregeln zu ändern.

## Zusätzliche Absicherung des Ausgangsstands

Produktionsmethoden wurden mit kontrollierten Eingaben und Assertions geprüft.
Die folgenden Ergebnisse beschreiben das bestehende Verhalten, nicht das Ziel:

| Situation | `menu_engaged` |
| --- | --- |
| Sichtbares, nicht offengehaltenes Formular, keine Cursorbeobachtung, Maus außerhalb | `True` |
| Dasselbe Formular, Maus über Aiko/Formular/Übergangsbereich | `True` |
| Offengehaltenes Formular, Maus außerhalb, keine weitere Bedienung | `False` |
| Offengehaltenes Formular, Maus darüber | `True` |
| Aktive Cursorbeobachtung, Maus nur über Aiko | `False` |
| Aktive Cursorbeobachtung, Maus über Formular oder Übergangsbereich | `True` |
| Maus außerhalb, aber Social-Auswahl offen oder Tastaturbedienung aktiv | `True` |

Zusätzlich bestätigt:

- `control_active()` ist bei passendem Sprite-Hover auch ohne Menü und Klick
  wahr. Ein echter Klick hinterlässt darüber hinaus eine räumliche Zugriffssperre.
- Shift-Rechtsklick ruft `claim_access` schon vor `show_menu` auf.
- Die vollständige Produktionskette mit `SocialMenu.close` storniert beim
  automatischen Ausblenden die ausstehende Auswahl genau einmal.
- `refresh_hover` läuft im Desktop-Tick vor `poll_social`. Deshalb muss die
  Umsetzung auch eine bereits eingetroffene Antwort im selben Tick absichern.
- Die älteren Methoden `AttentionCoordinator.cursor_reaction` und
  `select_cursor_comment_event` haben UI-abhängige Parameter, aber im Prüfstand
  keine Aufrufer aus dem aktuellen Produktionspfad. Ihre Tests sind keine
  zusätzliche aktive Laufzeitursache; der Fix darf diesen Pfad nicht aktivieren.

Die gezielte Baseline umfasst **200 Tests aus 26 Modulen in 44,030 Sekunden**,
ohne Fehler, Fehlschläge oder Skips. Der Prozess endete mit Exitcode 0.
Tk meldete bei einzelnen Fenster-Teardowns `ThemeChanged`-Diagnostik; der
Testlauf blieb erfolgreich. Die Tests verwendeten temporäre Saves und
kontrollierte Eingaben, ohne Live-API und ohne Zugriff auf den normalen Save.
Das ist keine manuelle Sichtabnahme und kein vollständiger Repository-Testlauf.

Die Module waren:

- Kontakt/Eingabe: `test_contact_coordinator`, `test_desktop_input_controller`,
  `test_cursor_contact_origin`.
- Cursor/Bewegung: `test_cursor_menu_access`, `test_cursor_behaviour_coordinator`,
  `test_desktop_walk_runtime`, `test_goal_walk`, `test_movement_requests`.
- Aufmerksamkeit: `test_attention_policy`, `test_attention_decisions`,
  `test_desktop_attention_runtime`, `test_idle_gesture`.
- Desktop/Formular: `test_menu_action_decoupling`, `test_desktop_session_runtime`,
  `test_application_gui`, `test_persistent_windows`, `test_world_runtime_flow`,
  `test_hover_geometry`, `test_hover_isolation`, `test_desktop_runtime`.
- Unterhaltung: `test_social_runtime`, `test_social_gui`.
- Spiele: `test_game_menu`, `test_game_animation_playback`,
  `test_game_expression_events`, `test_other_game_input`.

## Ziel und Zuständigkeiten

Bei identischen Zeit-, Pet-, World- und Zeigerwahrnehmungsdaten darf allein der
Formularzustand keine andere Handlungsentscheidung erzeugen. Natürliche
Reaktionen auf die tatsächliche Mausbewegung bleiben erlaubt. Ein Test darf
deshalb nicht veränderte Zeigerwahrnehmung mit einer reinen UI-Änderung verwechseln.

| Verantwortlicher | Zielverantwortung |
| --- | --- |
| `HoverUi`, `ActionToolbar`, `SettingsWindow` | Anzeigen, Verbergen, Position, Fokus, Offenhalten, Auswahl und Beschreibung. Keine Lebenszeit-, Kontakt- oder Handlungssperre. |
| `DesktopInput` | Eingaben an vorhandene Ports weitergeben; Fensteröffnung und Charakterkontakt unterscheiden. |
| `ContactCoordinator` | Tatsächliche direkte Interaktion und deren Klick-/Fortsetzungs-/Weckregeln. Hover erzeugt keine Reaktion und keinen Kontaktbeleg. |
| `PointerRuntime`, `CursorBehaviourCoordinator`, `CursorBehaviourPolicy` | Zeiger beobachten und ausdrücklichen Kontakt entgegennehmen; kein Formularzustand als Verhaltensfakt. |
| `WalkDriver`, `WalkController` | Einziger bestehender Weg für Bewegung und Position. Zulassung folgt Energie, Schlaf, Einstellungen und wirklichen Aktivitäten. |
| `DesktopAttentionRuntime`, `AttentionCoordinator` | Freie Ausdrucks-/Sprachslots anhand tatsächlicher Besitzer auswählen. |
| `SocialConversationRuntime` | Einziger Besitzer der ausstehenden angeforderten Auswahl und ihrer Tokens, unabhängig von der sichtbaren Auswahlansicht. |
| World, Care, ReactionPlayer und Spielabläufe | Bestehende Zulassung, sichere Unterbrechung, Objektfreigabe, Abschluss und Rückmeldungen. |

Es entstehen kein zweiter Aktionskoordinator, keine zweite Positionssteuerung
und kein weiterer Tick. Saveformat, Assets, Dialogkataloge und Provider ändern
sich durch diesen Fix nicht. Die bestehenden GamePresentation-/GameSpeech-
Verantwortlichkeiten und die Entwertung alter Spiel-Callbacks bleiben erhalten.

## Umsetzung in fünf Etappen

### 1 Hover und direkten Kontakt trennen

Betroffene Dateien: `application/contact.py`, `desktop/input.py`, `gui.py`,
`ui/windows/hover_ui.py` und deren Kontakt-/Eingabetests.

- Der native und der gepollte Hover-Einstieg dürfen nur Öffnung und
  Sichtbarkeitstiming anfordern. Die bestehende Herkunftsprüfung für
  Eigenbewegung unter einem ruhenden Zeiger bleibt eine UI-Öffnungsregel.
- `record_contact` aus dem Hover-Polling und seiner Port-Verdrahtung entfernen.
  `last_hover` bleibt für das Ausblenden erhalten; `mind.last_contact` wird
  weiter ausschließlich von tatsächlichen Kontaktpfaden bedient.
- `interrupt_walk`, Reaktionsauswahl und Cursorzugriff aus dem passiven
  `enter`-Pfad lösen. Direkten Kontakt mit einem schmalen Effektport nach
  seiner bestehenden Zulassung an `PointerRuntime.claim_access` anbinden.
- Fensteröffnung per Shift-Rechtsklick darf keinen Cursorzugriff beanspruchen.
  F2, Offenhalten, Details und Auswahlöffnung bleiben reine UI-Befehle.
- `click()` darf nicht einfach durch `can_interact("pet")` ersetzt werden:
  Story-Fortsetzung, wiederholte Klickreaktionen und Wecken haben eigene Regeln.
  Keine zusätzliche Rückkehrbegrüßung neben einer gewählten Klickreaktion starten.
  Bestehende geschützte Dialogdefinitionen werden nicht gelöscht.

Prüfpunkt: Wiederholter nativer/gepollter Hover öffnet die UI, ohne World-
Unterbrechung, Klickereignis, Reaktionsstart oder Änderung der Kontaktzeit.
Akzeptierter direkter Kontakt behält seine bisherige Wirkung.

### 2 Sperren für Bewegung und Cursor entfernen

Betroffene Dateien: `desktop/pointer_runtime.py`, `desktop/animation_assembly.py`,
`desktop/walk_runtime.py`, `application/cursor_behaviour.py`,
`pet/mind/cursor_behaviour.py`, `pet/movement/contracts.py`,
`pet/movement/controller.py`, `gui.py` und die zugehörigen Tests.

- `menu_engaged` aus den genannten Verhaltens-/Bewegungsverträgen und allen
  Aufrufern entfernen. Auch der spätere Domain-Guard in `plan_step` muss entfallen.
- Die Verdrahtung `hard_access=pointer.control_active` und die frühe
  UI-Rückkehr in `WalkDriver.step` entfernen. Keine Reparatur nur durch
  `committed_goal`: Auch eigene Schritte und Cursorbewegung müssen weiterlaufen.
- `claim_access` bleibt ein ausdrückliches Ereignis, das den aktuellen
  Cursorversuch über dessen bestehenden Policy-Besitzer beendet. Die räumliche
  `_access_claimed`-Dauersperre und `control_active` entfallen; ebenso ihre nicht
  mehr benötigten Port-/Kontextfelder nach dem Verbrauchernachweis.
- `CursorActivityContext.direct_contact` wird nach Wegfall seines Produzenten
  nicht durch ein zweites gehaltenes Flag ersetzt. Reale Kontaktaufnahme läuft
  über die unmittelbare Methode. Die bestehende Policy-Sicherung gegen sofortiges
  erneutes Ausweichen nach einem Klick bleibt bestehen.
- Den formulargetriebenen `pause_for_menu`-Zweig samt Zulassung entfernen.
  Spielmodus, Schlaf, geschützte World-Aktivität, echte Reaktionsbesitzer,
  deaktivierte Cursorverfolgung und tatsächliche Wahrnehmung bleiben wirksam.
- Sprite-Zugangsgeometrie bleibt für zuverlässige UI-Erreichbarkeit verfügbar;
  sie ist kein Bewegungsbesitzer.

Prüfpunkt: Laufender World-Auftrag behält Identität und Ziel und setzt seine
Bewegung unter Formular-Hover fort. Ein Cursorversuch wird durch denselben
Formularwechsel weder ersetzt noch beendet. Idle-Abgangszeit und Schrittfolge
werden nicht durch Formularanzeige zurückgesetzt.

### 3 Aufmerksamkeit von Fenstern lösen

Betroffene Dateien: `desktop/attention_runtime.py`, `application/attention.py`,
`gui.py` sowie Aufmerksamkeits-/Wunschgestentests.

- Die UI-Ports `menu_engaged` und `settings_engaged` aus der Attention-Runtime
  entfernen. Dasselbe gilt für `toolbar_visible`/`popup_visible` als
  Verhaltensparameter der aufgerufenen Policies.
- Cursorhinweise dürfen nicht wegen eines sichtbaren Formulars verworfen werden.
  Wünsche und spontane Kommentare verwenden ihre bisherigen Bedingungen für
  echte Sprach-/Aktionsbelegung. Kein Formularzustand verwirft eine vorbereitete
  Wunschgeste oder deren Ausrichtung.
- Benachrichtigungen bleiben während Schlaf, belegter Sprache und tatsächlicher
  geschützter Aktionen zurückgestellt. Formulare allein stellen sie nicht zurück.
- `SessionRuntimePorts.toolbar_visible` bleibt erhalten: Der Port steuert nur
  das Aktualisieren sichtbarer UI und ist keine Handlungssperre.
- Unbenutzte UI-Ableitungen, Tastatur-Beschäftigungstimer und Policy-Helfer erst
  nach Prüfung sämtlicher Code-, Test-, Tool- und Doku-Verbraucher bereinigen.
  Einen ungenutzten alten Cursor-Kommentarweg nicht erneut aktivieren.

Prüfpunkt: Zwei Läufe mit identischen Wahrnehmungsdaten und nur verschiedenem
Formularzustand treffen dieselben Aufmerksamkeitsentscheidungen. Reale
Belegung verhindert weiterhin Übersprechen und doppelte Benachrichtigungen.

### 4 Ausblenden und Abbrechen unterscheiden

Betroffene Dateien: `ui/windows/hover_ui.py`, `ui/windows/action_toolbar.py`,
`ui/windows/embedded_selector.py`, ihre schmalen UI-Verträge und Auswahlansichten.
`desktop/social_runtime.py` behält die bestehende Token-Verantwortung.

Einen schmalen UI-Schließgrund durch die vorhandene Callbackkette führen. Die
Klassifikation muss bereits beim Aufruf feststehen; kein globales temporäres
Flag und keine nachträgliche Rekonstruktion aus der aktuellen Mausposition.

| Anlass | Auswahlansicht | Ausstehende Social-Anforderung |
| --- | --- | --- |
| Hover-Timeout oder formularbedingte automatische Ausblendung | Schließen/verbergen | Beibehalten |
| Wechsel zur Essens-/Spielauswahl ohne konkreten neuen Charakterauftrag | Schließen/ersetzen | Beibehalten |
| Ausdrücklich Zurück, Escape oder Außenklick zur Auswahlaufgabe | Schließen | Weiterhin genau einmal stornieren |
| Akzeptierter neuer Care-/Spiel-/Social-Auftrag | Nach bestehendem Ablauf schließen | Bisherige ausdrückliche Ablösung beibehalten |
| Online-Opt-out oder Shutdown | Aufräumen | Bestehenden Runtime-Abbruch verwenden |

- Ein abgelehnter neuer Charakterauftrag darf nicht allein durch vorbereitendes
  Schließen des Formulars eine bestehende Anforderung abbrechen.
- Erneutes Öffnen zeigt den laufenden Zustand derselben Runtime; keine zweite
  Anfrage oder neue Warteschlange. Tatsächlicher Antwortstart bleibt von deren
  aktueller Zulassung abhängig und vergibt seine Gutschrift genau einmal.
- Falls eine Antwort im selben Tick wie das Ausblenden bereit ist, bleibt ihre
  ausgewählte Anforderung gültig. Nach ausdrücklichem Abbruch bleiben verspätete
  Antworten und bereits eingereihte Start-Callbacks dagegen unwirksam.
- `close_selector`, `SocialMenu.close` und `_social_menu_closed` müssen
  zusammenpassen: keine rekursive Doppelstornierung oder verwaiste Auswahlansicht.

Prüfpunkt: Vollständiger Ablauf Auswahl → Warten → automatisches Verbergen →
Antwort → einmaliger Start funktioniert ohne offenes Formular. Derselbe Ablauf
mit ausdrücklichem Abbruch startet anschließend nichts.

### 5 Integration und praktische Abnahme

Bestehende Tests mit alter Produktregel gezielt umschreiben, darunter
`test_hover_opens_toolbar_and_interrupts_walk`,
`test_tracking_toolbar_holds_world_motion_then_releases_without_reset`,
`test_stationary_hover_pauses_travel_and_preserves_search_and_candidate` und
`test_hovered_controls_defer_notification_until_pointer_leaves`. Beim Test
`test_menu_use_preserves_committed_object_approach` genügt der Name nicht:
Seine aktuellen Assertions verlangen Stillstand bei erhaltenem Ziel.

Die gemeinsamen Regressionsfälle gehören zusätzlich in eine fokussierte
`tests/test_hover_action_decoupling.py`. Sie variieren allein die Darstellung
bei ansonsten gleichen Eingaben. Vor der jeweiligen Änderung müssen die
betroffenen Zielassertionen am Prüfstand fehlschlagen und danach bestehen.

| Abnahmefall | Erwartung nach dem Fix |
| --- | --- |
| Native Enter-Ereignisse und Hover-Polling mehrfach hintereinander | UI öffnet, kein Auftragsabbruch, keine Kontakt-/Klick-/Pflegegutschrift. |
| Maus über Aiko, Formular, Übergangsbereich, geöffneten Auswahlansichten oder Einstellungen | Eigene Schritte, World-Wege und zulässiges Cursorverhalten laufen weiter. |
| Formular offenhalten, F2, Details, Scrollen, Tastaturfokus und Formularziehen | Nur Anzeige/Bedienung verändert sich; keine Idle-/Cursor-Zeit wird künstlich angehalten. |
| Aiko läuft unter einen ruhenden Zeiger; das unverschobene Formular folgt ihr | Keine neue Kontaktwirkung, kein wiederholtes Öffnen/Stoppen durch Eigenbewegung. |
| Annäherung, Suche und Wiederaufnahme nach einer Suche | Zielidentität, Suchroute und Bewegungsfortschritt bleiben korrekt. |
| Aufheben, Inspizieren, Essen, Trinken und Lesen | Volle bestehende Sequenzen, sichere Objektzuständigkeit, keine doppelte Wirkung. |
| Social-Warten vor und nach eingetroffener Antwort, beide Callback-Reihenfolgen | Passive Schließung erhält Anforderung, ausdrücklicher Abbruch entwertet sie. |
| Echter Klick, Care-Auftrag oder ausgewählter Spielstart | Bestehende Zulassung und sichere Unterbrechung bleiben wirksam; abgelehnte Bedienung verdrängt keinen Besitzer. |
| Alle sechs Spiele, Startreservierung, Schließen und bereits eingereihte Cues | Kein Hover-Einfluss auf Spielmodus, Eingabesperren, Ausdruck, Reward oder Callback-Lebensdauer. |
| Schlaf, Weckklicks, aktive Story und echte Sprachbelegung | Schutz-/Fortsetzungsregeln bleiben bestehen. |
| Freier Benachrichtigungsslot bei offenem Formular | Genau eine Zustellung; echte Belegung stellt weiterhin zurück. |

Die native Windows-Abnahme verwendet ausschließlich einen temporären Save,
kontrollierte beziehungsweise gefälschte Online-Antworten und 1X/2X. Tatsächliche
Mausbewegung, Hover-Timeout, Formularziehen und Erreichbarkeit bei laufender
Aiko werden separat geprüft. Das Formular folgt Aiko bereits heute, sofern
keine eigene Position gespeichert ist; dieser Fix friert es nicht automatisch
ein. Offenhalten und Positionierung bleiben getrennt. Für längere Bedienung
bleibt das vorhandene Verschieben verfügbar. Eine Änderung dieses Layoutverhaltens
wäre eine eigene Produktentscheidung.

## Prüfungen und Abschluss

Nach jeder Etappe laufen ihre betroffenen Module in einem frischen Prozess;
Fixture-Importe benötigen `tests` im Python-Suchpfad oder `unittest discover -s
tests`. Testeingaben und Saves bleiben isoliert. Nach Vertragsänderungen werden
sämtliche Aufrufer aktualisiert, nicht durch dauerhafte `False`-Adapter kaschiert.

Zum Abschluss gehören die 26 Baseline-Module, die neuen Regressionen und die
betroffenen Cursor-/Bewegungs-/GUI-/Spielmodule sowie die Repository-Gates aus
[Tests](../.github/workflows/tests.yml):

```text
python -m ruff check aiko_pet tests main.py tools
python -m mypy --strict --follow-imports=silent aiko_pet/pet/mind/adaptive_policy.py aiko_pet/pet/mind/click_policy.py aiko_pet/pet/movement/controller.py aiko_pet/ui/pet_view/reaction_player.py
python -m mypy --strict --no-incremental aiko_pet main.py tools
python -m pyright --project pyrightconfig.json
python -m unittest discover -s tests -q
```

Die CI prüft Python 3.11 und 3.13 sowie eigene Windows-Grenzen. Ein lokaler
gezielter Lauf ersetzt diese Gates und die native Sichtabnahme nicht. Falls
vorhandene parallele Änderungen Fehler verursachen, werden diese am zugehörigen
unveränderten Stand reproduziert und getrennt ausgewiesen; kein grüner
Gesamtstatus allein aufgrund der gezielten Tests.

Abschließend die Aussagen in `ARCHITECTURE.md`, `UI_WINDOW_CONTRACT.md` und den
betroffenen aktiven Cursor-/Care-Plänen mit der neuen Regel abgleichen. Alte
Verlaufsabschnitte als Verlauf erhalten und bei widersprechender aktiver Regel
auf diesen Fix verweisen. Die bestehende Social-Arbeit bleibt erhalten.

Der Fix ist erst vollständig, wenn die Anzeige keinen Verhaltensbesitzer mehr
simuliert, passive Schließung keinen angenommenen Auftrag storniert und
ausdrückliche Interaktionen weiterhin über ihre bisherigen Besitzer abgewickelt
werden. Die folgenden Ergebnisse dokumentieren die Umsetzung ohne Commit, Push oder Merge.


## Umsetzung und Prüfung am 30 Oktober 2026

Vor dem Umbau wurde der vollständige nicht ignorierte Arbeitsstand außerhalb
von Git gesichert. Die vorhandenen Social-Änderungen werden beibehalten.

| Etappe | Ergebnis |
| --- | --- |
| 1 Kontakt | Drei neue Gegenproben schlugen am alten Stand fehl. Nach Trennung von Hover, Kontaktbuchung und Cursorzugriff bestanden 64 Kontakt-, Eingabe-, Klick-, Story- und Social-Tests. |
| 2 Bewegung und Cursor | Die neue Probe schlug zunächst in allen vier Zeigerregionen fehl und besteht nach dem Umbau. 110 weitere Cursor-/Bewegungs-/Animationsprüfungen sowie abschließend 18 Desktop-/World-/Hover-Integrationsprüfungen bestanden. Die alte Erwartung eingefrorener Cursoraufmerksamkeit wurde durch fortlaufende Wahrnehmung ersetzt. |
| 3 Aufmerksamkeit | Die neue Benachrichtigungsprobe schlug für Formular und Einstellungen fehl und besteht nach Entfernen der UI-Sperren. 77 betroffene Prüfungen bestanden. Nur der Sichtbarkeitsport zum UI-Aktualisieren bleibt bestehen. |
| 4 Schließgründe | Drei neue Proben belegten den alten Abbruch beim Ausblenden beziehungsweise Navigieren. Danach bestanden 60 Social-/Spielauswahl-/Fensterprüfungen und zwei zusätzliche Proben für akzeptierten Spielstart und abgelehnte Befehle. |
| 5 Integration | Zwei weitere alte Stillstandsassertionen wurden im ersten vollständigen Lauf gefunden und nach Umstellung gezielt erfolgreich geprüft. Der abschließende frische Gesamtlauf bestand mit 2.485 Tests ohne Fehler, Fehlschläge oder Skips; native Eingabeprobe abgeschlossen. |

Ruff und die beiden Mypy-Gates bestanden. Fünf zunächst von Pyright gefundene
alte Testaufrufe wurden an die neuen Verträge angepasst; danach meldete Pyright
null Fehler, Warnungen oder Hinweise. Ein bereits gestarteter Gesamtlauf wurde
nach diesen Testkorrekturen beendet und mit Testfortschritt und Stack-Diagnostik
frisch gestartet; der beendete Lauf wird nicht als erfolgreicher Lauf gezählt.


### Native Windows Eingabeprobe

Die isolierte Testinstanz nutzte den echten Tk-Sprite, den bestehenden
Bewegungsadapter und reale Zeiger-/Rad-/Zieheingaben über Computer Use.
Ein kontrollierter World-Bewegungsauftrag lief zwischen zwei Track-Zielen.
Die Objektbeobachtung wurde in dieser Probe ausgesetzt, damit sie den vom
Testtreiber vorgegebenen Auftrag nicht durch ihre eigene Auswahl ersetzt;
Objektwahrnehmung und vollständige Objektabläufe bleiben durch die World-Tests
abgedeckt. Cursorverfolgung war aus, um reine Hover-Sperren unabhängig von einer
natürlichen Reaktion auf den Zeiger zu prüfen.

Für die Auswahl durch das Windows-Werkzeug bekamen Sprite und Toolbar im
Testtreiber normale Fensterrahmen; die Toolwindow-Eigenschaft der Toolbar
wurde dort ausgeschaltet. Die Produktionsfenster und ihre Eingabe-Handler
wurden dafür nicht geändert. Diese Probe ist eine Eingabe-/Bewegungsprüfung,
keine erneute Bild- oder DPI-Abnahme der rahmenlosen Gestaltung.

| Reale Eingabe | Gemessener Fortschritt |
| --- | --- |
| Zeiger über Aiko bei 1X | 83 Samples mit tatsächlicher Bewegung, X von 1672 bis 1862, kein Klick und unveränderte Kontaktzeit. |
| Zeiger über Aiko bei 2X | 27 Samples mit tatsächlicher Bewegung, X von 915 bis 1098, kein Klick und unveränderte Kontaktzeit. |
| Formular folgt Aiko bei 1X, Zeiger auf dem Formular | 266 Samples, X von 1882 bis 2338; der einzige Sample ohne Translation lag am Routenende. |
| Formularheader ziehen und Radbedienung bei 1X | 575 Samples über dem Formular mit Translation, X von 819 bis 2337, keine Klickreaktion und unveränderte Kontaktzeit. Die eigene Formularposition wurde im Testspeicher als 1277/631 gespeichert. |

Alle Testinstanzen wurden beendet. Die Saves und Messdaten liegen ausschließlich
unter temporären `aiko-hover-native-*`-Verzeichnissen. Die tatsächliche
World- und Spielintegration wird nicht aus diesen kontrollierten Routen
abgeleitet, sondern mit den zugehörigen Integrationstests geprüft.


### Abschlussprüfungen

| Prüfung | Ergebnis |
| --- | --- |
| Ruff über `aiko_pet`, `tests`, `main.py`, `tools` | Bestanden. |
| Striktes Mypy mit `--follow-imports=silent` über die vier CI-Kernmodule | Vier Module ohne Befund. |
| Striktes frisches Mypy über `aiko_pet`, `main.py`, `tools` | 382 Quelldateien ohne Befund. |
| Repository-Pyright einschließlich Tests | Null Fehler, Warnungen oder Hinweise. |
| Vollständiges `unittest discover -s tests` mit temporärem Standard-Save | 2.485 Tests in 415,644 Sekunden, null Fehlschläge, Fehler oder Skips; Exitcode 0. |
| Zusätzliche gemeinsame Regressionen nach Erweiterung auf beide Skalen | Vier Tests bestanden. |
| Zusätzliche Social-/Hover-/Cursor-/Wunschprüfung einschließlich einmaligem ausdrücklichem Abbruch | 42 Tests bestanden. |
| Reale Windows-Eingaben mit isoliertem Save | Die oben begrenzte Eingabe-/Bewegungsprobe bestand. |

Der erste vollständige Lauf umfasste 2.484 Tests und meldete zwei weitere alte
Hover-Stillstandserwartungen in `test_gui.py` und `test_world_gui.py`. Beide
wurden auf tatsächliches Weiterlaufen bei erhaltenem Ziel/Objektfokus geändert
und zunächst gezielt geprüft. Anschließend lief die vollständige Suite erneut
in einem frischen Prozess erfolgreich durch. Die geänderten Tests wurden nicht
übersprungen. Die bekannte Tk-Teardown-Diagnostik trat auch im erfolgreichen
Gesamtlauf auf und verursachte keinen Testfehler.

Lokal wurde Python 3.11 verwendet. Die CI-Matrix mit Python 3.13 wurde nicht
remote gestartet. Kein Commit, Push oder Merge wurde ausgeführt; `HEAD` bleibt
auf der oben genannten Ausgangsrevision. 26 bereits vorhandene Änderungsdateien
blieben bytegleich. Die überlappenden Änderungen in `gui.py`, `test_social_gui.py`,
dem Doku-Index und diesem Plan wurden ergänzt, nicht verworfen. Die bestehende
Social-Fetch-Verdrahtung und die parallelen Provider-/History-/Schemaänderungen
sind erhalten. Die Sicherung des Ausgangsstands und die Testprotokolle befinden
sich außerhalb von Git unter temporären `aiko-hover-baseline-*` beziehungsweise
`aiko-hover-validation-*`-Verzeichnissen.

## Commitfolge und Abschlussprüfung

Auf ausdrücklichen Folgeauftrag wurde der gesamte bestehende Arbeitsbestand
erhalten und in kleine, voneinander prüfbare Commits aufgeteilt. Vorher standen
80 geänderte und sechs neue Dateien bei leerem Index aus. Eine zusätzliche
Sicherung aller 2.230 vorhandenen Repository-Dateien, des Index und des Diffs
liegt außerhalb von Git unter `aiko-clean-commits-*`.

Gemeinsam bearbeitete Dateien wie `gui.py`, `test_social_gui.py` und die
Kandidatentests wurden nach Änderungsblöcken aufgeteilt. Jeder Zwischenstand
wurde als isolierter Abzug des tatsächlichen Index mit seinen gezielten Tests
und Ruff über die betroffenen Python-Dateien geprüft. Spätere Änderungen im
Arbeitsbaum konnten dadurch keine fehlende Abhängigkeit verdecken. Die
Gesamtsuite wurde erst nach der vollständigen Integration gestartet.

| Commit | Abgeschlossene Etappe | Gezielte Tests bestanden |
| --- | --- | --- |
| `1fdd319` | Fetch-Verträge und reine Kandidatenregeln | 27 |
| `cb645de` | Ausschluss-Historie, Transfer und SQLite-Migration | 30 |
| `0bcc16e` | JokeAPI-Metadaten, ID-Bereiche und Ablehnungsgründe | 36 |
| `e9e02dc` | Kandidatensteuerung, Suchgrenzen und Social-Status | 80 |
| `a10283e` | Passiver Hover und ausdrücklicher Kontakt | 60 |
| `6f0bbac` | Cursor- und World-Bewegung ohne Formularsperren | 105 + 21 |
| `2f436a4` | Aufmerksamkeit anhand wirklicher Aktionsbesitzer | 59 |
| `a49f245` | Anforderung unabhängig von der Auswahlansicht | 52 |
| `6a4e77f` | Passiver Fokusverlust ohne Social-Stornierung | 35 |
| `8df0733` | Einstellungsnavigation ohne Social-Stornierung | 45 |

Die beiden Folgekorrekturen wurden zunächst gegen den jeweils noch fehlerhaften
Stand abgesichert: Drei Fokus-Regressionen schlugen wegen unerwünschtem
`cancel()` fehl; zwei Einstellungs-Regressionen reproduzierten denselben Fehler
über Tk-Eingabe und globales Polling. Der echte Außenklick blieb dabei wirksam.
Nach den Korrekturen bestehen die Fälle für `fetching`, `admitting` und bereits
laufende Unterhaltung. Doppelte Klick-/Fokusmeldungen stornieren nicht doppelt;
beibehaltene Antworten starten und vergüten genau einmal. Zusätzlich prüfen
vier reine Kandidatentests überlappende Intervalle, Ablauf/Filterrevision,
Kategoriegrenzen und unveränderten Wiederholungsschutz bei erschöpftem Pool.

Die Fokusprüfung hat einen eigenen passiven Desktop-Port. Nur die UI übersetzt
ihn in automatisches Schließen; der Eingabeadapter importiert dafür keine
UI-Schließgründe. Klicks im vorhandenen Einstellungsfenster gelten für beide
Klickpfade als Navigation. Die Einstellungen werden nicht in die allgemeine
Hover-/Offenhaltegeometrie aufgenommen. Online-Opt-out, Shutdown und zugelassene
Ersatzaufträge behalten ihren zuständigen Abbruchpfad. Die Social-Runtime und
die gemeinsame Bewegungssteuerung bleiben die bisherigen Besitzer.

| Abschließende Prüfung des integrierten Codes auf `8df0733` | Ergebnis |
| --- | --- |
| Gesamte native Windows-/Tk-Suite, Python 3.11 | **2.499 Tests in 471,750 Sekunden; null Fehlschläge, Fehler oder Skips; Exitcode 0.** |
| Ruff über `aiko_pet`, `tests`, `main.py`, `tools` | Bestanden. |
| Striktes Mypy mit `--follow-imports=silent`, vier CI-Kernmodule | Bestanden. |
| Striktes frisches Mypy über Anwendung und Tools | 382 Quelldateien ohne Befund. |
| Pyright einschließlich Tests | Null Fehler, Warnungen oder Hinweise. |
| Erhalt des vorhandenen Bestands | 2.221 von 2.230 Dateien bytegleich; nur neun Dateien für die beiden Nachbesserungen, ihre Regressionen und Doku ergänzt. Keine vorhandene Datei verworfen. |

Die gesamte Suite verwendete einen temporären Standard-Save; die Social-Proben
kontrollierte Worker ohne Live-API. Der normale Nutzersave wurde nicht benutzt.
Die bekannte Tk-`ThemeChanged`-Teardown-Diagnostik trat auf, ohne einen Testfehler
oder Skip zu verursachen. Remote CI und die Python-3.13-Matrix wurden nicht
gestartet, weil kein Push erfolgte.

Die zusätzliche native 1X-Fokusprobe mit Computer Use bestand: Alt-Tab löste
passive Schließung aus, die Anfrage blieb in `fetching`, und die anschließend
gelieferte Antwort startete als `talk` mit genau einer Sozialgutschrift von
10 auf 36, ohne Stornierung oder Tk-Callbackfehler. Diese Testinstanz verwendete
einen eigenen Save, einen kontrollierten Worker, native Fensterrahmen zur
Adressierbarkeit sowie das echte Fokus-/Eingaberouting bei gestopptem regulärem
Tick. Sie ist eine gezielte Funktionsprobe, keine vollständige visuelle Abnahme.
Die anschließende native 2X-Einstellungsprobe wurde vor ihrer Bedienung durch
die physische Escape-Taste gestoppt. Es wurden keine weiteren UI-Eingaben
gesendet; alle isolierten Testinstanzen wurden beendet. Diese manuelle
2X-Bedienprobe bleibt unvollständig. Die automatisierten Einstellungs- und
1X/2X-Bewegungsprüfungen sind davon getrennt und bestanden.

Nach den zehn fachlichen Commits war der Tree bereits sauber. Dieses Protokoll
ist die einzige anschließende Dokuänderung; der geprüfte Code bleibt unverändert.
Push und Merge wurden nicht ausgeführt.
