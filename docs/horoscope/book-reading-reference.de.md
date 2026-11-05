# Bestätigte Stilreferenz: Aiko liest aus dem Horoskopbuch

Vom Nutzer am 25. Oktober 2026 im Chat als „ja perfekt“ bestätigt.
Dies ist die inhaltliche Referenz für die nächste redaktionelle Arbeit,
kein Laufzeitkatalog und keine Implementierungsfreigabe. Der bisherige
API-Prototyp ist verworfen; sein vollständiger Ersatz durch diesen lokalen
Buchansatz ist beschlossen. Er bleibt weder Alternativmodus noch Fallback.
Der [technische Umbauplan](LOCAL_HOROSCOPE_IMPLEMENTATION_PLAN.md) beschreibt
die inzwischen separat freigegebene Integration; der [Gesamtplan](../SOCIAL_EXPANSION_PLAN.md#local-horoscope-alternative-and-complete-scene-draft)
enthält Umfang und Auswahlmodell.

## Rahmen

Das Buch ist ein tatsächlicher Gegenstand in Aikos Desktop-Welt. Der Spieler
platziert es per Drag-and-drop auf der Taskleiste. Aiko hebt es auf und benutzt
es zum Lesen. Es gilt **ein Buch für den Tageseintrag und höchstens ein lebendes
Buch**: Nach vollständigem Lesen wird es geschlossen und abgelegt. Nach
vollständiger erster Lesung und Ablegen bleibt es noch
eine feste Stunde bestehen. Erneutes Überreichen liest denselben Eintrag von
vorn, ohne weitere Gutschrift oder Fristverlängerung. Unterbrechen allein
startet diese Frist noch nicht. Ein unvollständiges Buch vom Vortag wird entfernt;
ein abgeschlossenes behält auch über Mitternacht seinen Text und seine Frist.
Erst nach seinem Verschwinden kann das nächste Tagesbuch platziert werden.
Die vorhandene Haltepose bildet die Grundlage. Das inzwischen vorhandene
[violette V1-Buchpaket](../HOROSCOPE_BOOK_ASSETS.md) liefert vier Bildzustände;
die Integration nutzt die mittige Halteregistrierung mit +12 px bei 1x.

Aiko bleibt zu jeder Zeit Aiko. Das Buch gibt den vorgelesenen Text vor;
Aiko kann auf eine konkrete Passage mit einer eigenen Bemerkung reagieren.
Sie kündigt keinen Identitätswechsel an und wird anschließend nicht „wieder
Aiko“. Ein Kommentar ist optional. Hut, Hutgeschenk als Zugangsvoraussetzung
und schwebendes Buch gehören nicht zum ersten Buchentwurf. Eine spätere
Huterweiterung bleibt davon getrennte Zukunftsplanung.

## Vollständiges Beispiel für Stier

Das Beispiel ist noch keinem konkreten Tagesdatum oder berechneten Himmel
zugeordnet. Vor Aufnahme in einen späteren Katalog sind Auswahlbedingungen
redaktionell festzulegen. Ein ausgetauschter Sternzeichenname allein macht es
nicht zu einer passenden Lesung für jedes andere Zeichen.

**Aiko hält das aufgehobene Buch. Eigener Einstieg:**

> Mal sehen, was heute für dein Sternzeichen im Buch steht.

**Bucheintrag — jede Zeile ist eine vollständige Textblase:**

> Stier, heute fällt deine ruhige Art besonders auf. Du musst dich nicht in den Vordergrund drängen, um gehört zu werden.

> In einer Begegnung findet ein beiläufiger Gedanke mehr Anklang, als du erwartest. Sprich ihn aus, statt ihn zurückzuhalten.

> Die Lust auf Neues wächst. Ein kleiner erster Versuch liegt dir heute mehr als ein Plan, der schon jedes Detail festlegt.

> Vertraue deinem eigenen Tempo. Du darfst dich zeigen, ohne dabei jemand anderes werden zu müssen.

Der Bucheintrag endet hier. Aiko lässt den letzten Satz kurz wirken. Wenn ein
Kommentar zu ihrer aktuellen Verfassung passt, wird **eine** der folgenden
Freundschaftsfassungen verwendet; keine davon gehört zum eigentlichen Buchtext.

| Freundschaft | Eigener Kommentar |
| --- | --- |
| 1–2 | Der letzte Satz gefällt mir. Sich zeigen, ohne sich zu verstellen … Das klingt angenehm. |
| 3–5 | Das mit dem eigenen Tempo gefällt mir. Ich mag es, wenn ich eine Sache erst in Ruhe anschauen kann. |
| 6–8 | Das mit dem eigenen Tempo behalte ich. Ich lasse mich schließlich auch nicht gern herumscheuchen. |
| 9–10 | Den letzten Satz mag ich. Bei dir bin ich gern einfach ich. |

**Aikos Abschluss:**

> Das war dein Eintrag für heute.

## Vortrag und Ausdruck

- Das Vorlesen bleibt zusammenhängend. Bei diesem Beispiel kommt die mögliche
  Bemerkung nach dem letzten Buchabschnitt; andere Einträge dürfen eine passende
  Zwischenstelle haben, wenn der Zusammenhang erhalten bleibt.
- Aiko bleibt während der Lesung in der Haltepose. Keine Handgeste darf das
  weiterhin gehaltene Buch unbeabsichtigt aus der Darstellung verschwinden lassen.
- Vor dem Kommentar kann kurz `idea` erscheinen; bei der vertrauten Fassung
  kann anschließend `faceHappy` passen. Emote und Text wechseln sich auf derselben
  Sprechfläche ab. Buchpassagen brauchen keine dauernden Zwischenemotes.
- Es gelten die gemeinsamen Textzeiten, höchstens zwölf Textblasen insgesamt
  und die zusätzliche Sekunde an der letzten tatsächlich gesprochenen Textblase.
  Eine 0,8-Sekunden-Pointenpause ist hier nicht vorgeschrieben: Die Szene hat
  keine Pflichtpointe. Leseklicks bleiben möglich.
- Nähe verändert Offenheit und Ansprache, nicht den Inhalt des Bucheintrags.
  Müdigkeit oder Gereiztheit erzwingen keinen heiteren Kommentar. Noch nicht
  geschriebene Zustandsfassungen dürfen nicht durch unpassende Nähe ersetzt werden.
- Der Kommentar bezieht sich auf das gerade Gelesene oder ein tatsächlich
  belegtes Desktop-Erlebnis. Keine erfundene gemeinsame Kreativarbeit, kein
  freier Chat und kein verpflichtender Übergang zu einem Minispiel.

## Bedeutung für den weiteren Textbestand

Zuerst entsteht ein eigenständig lesbares Tageshoroskop mit einer persönlichen
Tageslage, Entwicklung oder Spannung für das ausgewählte Zeichen. Daraus kann
ein Impuls folgen. Keine Ansage interner Themenfamilien, keine fortlaufenden
Erklärungen von Auswahlregeln und keine künstliche Streckung eines einzigen Rats.
Danach werden Aikos Rahmen und mögliche Kommentare ergänzt.

Die zwölf früheren [Pilotszenen](pilot-scenes.de.md) und die ältere Neun-Blasen-
Szene sind **verworfen bzw. überholt**, nicht zwölf abgenommene Starttexte.
Diese eine bestätigte Referenz ersetzt sie als Stilmaßstab. Weitere Piloten
müssen separat in diesem Stil ausgearbeitet und beurteilt werden.
