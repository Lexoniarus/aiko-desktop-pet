# Lokales Horoskop: zwölf Pilotszenen — verworfen

> **VERWORFENE ENTWÜRFE — kein aktueller Textbestand.**
> Der Nutzer hat diese zwölf Piloten inhaltlich nicht abgenommen. Sie beziehen
> sich zu stark auf Aikos Auftritt und enthalten teilweise unpassende gemeinsame
> Kreativarbeit. Rollenwechsel, feste Kommentarplätze und fehlender Buchgebrauch
> entsprechen nicht dem bestätigten Konzept. Alle folgenden Regie- und
> Auswahlangaben sind historische Entwurfsannahmen, keine aktuellen Vorgaben.
> Maßgeblich sind die [bestätigte Buchreferenz](book-reading-reference.de.md)
> und der [korrigierte technische Plan](LOCAL_HOROSCOPE_IMPLEMENTATION_PLAN.md).
> Statische Längenprüfungen bedeuten keine redaktionelle Freigabe.

Redaktionelle Entwürfe vom 25. Oktober 2026. Grundlage ist der
[Horoskop-Plan](../SOCIAL_EXPANSION_PLAN.md#local-horoscope-alternative-and-complete-scene-draft).
Diese Datei enthält ausschließlich zur Besprechung geschriebene Szenen.
Sie wird nicht von Aiko geladen. Der AstroWay-Prototyp bleibt unverändert;
Bibliothek, Laufzeitkatalog, Speicherstände und Charakterassets werden nicht geändert.

## Leseschlüssel und gemeinsamer Ablauf

Jede Szene hat sieben vollständige Textblasen. Die Ablauf-Tabelle zeigt die
Fassung für **Freundschaft 6–8**. Die anschließende Tabelle ersetzt ausschließlich
**Blase 1 und Blase 5** für die anderen Bereiche. Dadurch ergibt sich für jede
Stufe eine vollständige Lesung: 1 aus ihrer Stufenfassung, 2–4 aus dem Ablauf,
5 aus ihrer Stufenfassung, 6–7 aus dem Ablauf. Es werden keine Halbsätze gemischt.
Die zwei Stufenstellen zählen nicht als zusätzliche der 96 Inhaltsvarianten.

| Freundschaft | Ton innerhalb derselben gespielten Rolle |
| --- | --- |
| 1–2 | Höflich und etwas zurückhaltend; erste Spielfreude, keine vorausgesetzte Vertrautheit. |
| 3–5 | Entspannter und persönlicher; eigene Vorlieben und kleine Wünsche werden erkennbar. |
| 6–8 | Offen, ehrgeizig und neckisch; Aiko möchte mit ihrem Auftritt beeindrucken. |
| 9–10 | Vertraut, herzlich und direkt; Zuneigung darf ohne anschließenden Rückzieher stehen bleiben. |

Das sind Fassungen für eine ruhige, zur Lesung passende Stimmung. Freundschaft
erzwingt keine Fröhlichkeit. Müde, gereizte oder bedrückte Fassungen sind noch
nicht vollständig ausgearbeitet; die Piloten beanspruchen keine Abdeckung aller
Zustände. Insbesondere machen niedrige Stufen Aiko weder unterwürfig noch
ängstlich, hohe Stufen weder beleidigend noch romantisch verpflichtend.

**Rollenvertrag:** Aiko kündigt an, dass sie Wahrsagerin spielt, trägt ihre
Deutung in dieser Rolle vor und beendet die Vorstellung ausdrücklich. Sie
bleibt dabei Aiko. Ein Rollenbruch entsteht aus der jeweiligen Szene; ein
ständiges Entschuldigen oder wiederkehrendes „zurück in meine Rolle“ ist kein
Pflichtschritt. Sie behauptet keine Kenntnis über Gedanken, Erlebnisse oder
Beziehungen des Spielers. Die Ratschläge sind Einladungen, keine behaupteten
Vorhersagen. Der Ton bleibt durchgehend bei **du**.

**Regie:** `idle` und die vorhandene `waiting`-Handgeste sind die einzigen hier
vorgesehenen Charakterclips. `waiting` wird gezielt einmal gespielt, nicht
dauerhaft wiederholt. Emotes erscheinen nach der jeweiligen Textblase auf
derselben Sprechfläche, niemals gleichzeitig mit dem Text. Normale Emotebeats
sind als Vorschlag etwa eine Sekunde lang. Wo ausdrücklich 0,8 Sekunden stehen,
bildet der Emote selbst die Denkpause; keine zusätzliche Leerzeit addieren.
Alle Texte nutzen die beschlossenen Anzeigezeiten, Blase 7 erhält die zusätzliche
Abschlusssekunde. Leseklicks dürfen den Ablauf verkürzen. Emotes sind Ausdruck,
keine vom User erwarteten Antworten. Haltung und Emotes der unveränderten
Blasen bleiben in allen Stufen gleich; Ausnahmen stehen direkt bei der Szene.

Hut, Buch, Partikel und feste inszenierte Blickwechsel sind keine Voraussetzung.
Es wird kein Anziehen, Blättern oder Berühren eines noch fehlenden Assets
behauptet. Clipwechsel zwischen Blasen benötigen später eine eigene
Ablaufkoordination; ihre Beschreibung hier ist keine vorhandene Spielfunktion.
Ein Spielvorschlag startet kein Spiel, erzeugt keinen gespeicherten Wunsch
und bucht keine zusätzliche Pflegewirkung.

## Übersicht und Auswahlbedingungen

Die Hausnummer bezeichnet das relative Sonnenhaus des Mondzeichens, gezählt
vom ausgewählten Sternzeichen als Haus 1. Jede Zeile ist eine Auswahlbedingung
für eine spätere lokale Berechnung, kein tatsächlich berechneter Tageshimmel.
Die Piloten sind über alle zwölf Zeichen wiederverwendbar. Sonne und Mondzeichen
dürfen später nur passende Zusatzfärbung geben; hier ist keine zusätzliche
Sonnenkonstellation vorausgesetzt.

| Pilot | Themenfamilie / Mondhaus | Entwicklungsrichtung | Mondphasenwinkel |
| --- | --- | --- | --- |
| P01 | 1: Selbstbild und Auftreten | Beginnen | 0° ≤ Winkel < 90° |
| P02 | 2: Eigene Mittel und Werte | Betrachten | 180° ≤ Winkel < 270° |
| P03 | 3: Austausch und kleine Entdeckungen | Weiterentwickeln | 90° ≤ Winkel < 180° |
| P04 | 4: Vertrautheit und Geborgenheit | Abschließen | 270° ≤ Winkel < 360° |
| P05 | 5: Spielfreude und Kreativität | Beginnen | 0° ≤ Winkel < 90° |
| P06 | 6: Alltag und hilfreiche Gewohnheiten | Weiterentwickeln | 90° ≤ Winkel < 180° |
| P07 | 7: Begegnung und Zusammenspiel | Betrachten | 180° ≤ Winkel < 270° |
| P08 | 8: Veränderung und Vertrauen | Beginnen | 0° ≤ Winkel < 90° |
| P09 | 9: Neugier und neue Perspektiven | Weiterentwickeln | 90° ≤ Winkel < 180° |
| P10 | 10: Ziele und sichtbarer Fortschritt | Abschließen | 270° ≤ Winkel < 360° |
| P11 | 11: Freundschaft und gemeinsame Ideen | Betrachten | 180° ≤ Winkel < 270° |
| P12 | 12: Ruhe und innere Gedankenwelt | Abschließen | 270° ≤ Winkel < 360° |

Damit gibt es genau drei Piloten je Entwicklungsrichtung. Der Phasenwinkel
bleibt ein Winkel, kein Beleuchtungsprozentsatz. Keine Szene setzt voraus,
dass genau heute Neu-, Halb- oder Vollmond stattfindet.

## P01 — Der erste Auftritt

**Familie 1 · Beginnen.** Aiko will als Orakel souverän wirken und merkt, dass
sie ihren eigenen Rat gerade selbst ausprobieren kann. Der Anfang darf klein sein.

| Blase | Vollständiger Text, Freundschaft 6–8 | Regie danach / währenddessen |
| --- | --- | --- |
| 1 | Ich spiele heute die Sternendeuterin. Versuch bitte, von meiner würdevollen Haltung beeindruckt zu sein. | `waiting` einmal zum Beginn, danach `idle`; `star` nach dem Text. |
| 2 | Der Mond nimmt zu. Für dein Zeichen lese ich darin einen kleinen Anfang: dich mit einer eigenen Idee zu zeigen. | `idle`. |
| 3 | Dafür brauchst du keinen großen Auftritt. Ein erster Satz darf noch ein bisschen wackeln. | `idle`. |
| 4 | Hm. Das gilt wohl auch für angehende Sternendeuterinnen. Meine Haltung übt jedenfalls noch. | `question`, 0,8 s. |
| 5 | Ich wollte dich eigentlich beeindrucken. Jetzt hast du mich beim Üben erwischt. Du darfst trotzdem staunen. | `faceHappy`. |
| 6 | Mein Orakelrat bleibt: Zeig einen kleinen Teil deiner Idee. Den Rest darfst du unterwegs herausfinden. | `idle`, ruhiger Rückweg in die Rolle. |
| 7 | Die Sternendeuterin macht Feierabend. Ich bin wieder Aiko. Die würde diesen Auftritt gern noch mal üben. | `idle`, Abschlusssekunde. |

| Freundschaft | Ersatz für Blase 1 | Ersatz für Blase 5 |
| --- | --- | --- |
| 1–2 | Darf ich für diese Lesung die Sternendeuterin spielen? Ich versuche es mit einem feierlichen Anfang. | Das war wohl noch nicht ganz würdevoll. Aber die Idee hinter meinem Auftritt mag ich. |
| 3–5 | Ich schlüpfe in die Rolle der Sternendeuterin. Mal sehen, ob ich den feierlichen Ton halten kann. | Ein bisschen wollte ich dich schon beeindrucken. Für den Anfang bin ich mit mir ganz zufrieden. |
| 9–10 | Für dich spiele ich heute die Sternendeuterin. Ich freu mich schon auf meinen großen kleinen Auftritt. | Bei dir probiere ich so etwas gern aus. Auch wenn meine große Würde dabei noch ein bisschen wackelt. |

## P02 — Die Schatzprüfung

**Familie 2 · Betrachten.** Das Orakel beginnt mit großer Schatzsucher-Geste;
Aiko entdeckt, dass Aufmerksamkeit ein passenderes Motiv als Gold ist.

| Blase | Vollständiger Text, Freundschaft 6–8 | Regie danach / währenddessen |
| --- | --- | --- |
| 1 | Ich übernehme die Rolle der Wahrsagerin. Heute gibt es eine Schatzprüfung. Sehr offiziell, natürlich. | `idle`; `star`. |
| 2 | In der abnehmenden Hälfte des Mondzyklus richte ich den Blick auf das, was dir etwas wert ist. | `idle`. |
| 3 | Vielleicht ist es Zeit für etwas Schönes, ein vertrauter Gegenstand oder eine Sache, der du Aufmerksamkeit schenkst. | `idle`. |
| 4 | Mein inneres Orakel hatte sich gerade auf einen riesigen Goldschatz eingestellt. Etwas bescheidener, bitte. | `question`, 0,8 s. |
| 5 | Ich nehme lieber ein bisschen gemeinsame Zeit. Gold kann mir schließlich nicht beim Vier gewinnt gegenübersitzen. | `faceHappy`. |
| 6 | Betrachte heute etwas, das dir wichtig ist. Du musst es weder vermehren noch besser machen, um es zu schätzen. | `idle`. |
| 7 | Die Schatzprüfung ist beendet. Ich bin wieder Aiko. Meine persönliche Wahl steht jedenfalls fest. | `idle`, Abschlusssekunde. |

| Freundschaft | Ersatz für Blase 1 | Ersatz für Blase 5 |
| --- | --- | --- |
| 1–2 | Ich spiele für diese Lesung die Wahrsagerin. Heute möchte ich mich an einer kleinen Schatzprüfung versuchen. | Zeit für ein Spiel fände ich als Schatz ganz passend. Auch wenn das etwas weniger glänzt. |
| 3–5 | Als Wahrsagerin auf Zeit eröffne ich die Schatzprüfung. Mal sehen, was dabei als kostbar durchgeht. | Ein bisschen gemeinsame Spielzeit wäre meine Wahl. Da habe ich mehr davon als von einem Goldhaufen. |
| 9–10 | Ich spiele deine Wahrsagerin und eröffne die Schatzprüfung. Meinen eigenen Favoriten kenne ich schon. | Zeit mit dir ist mir viel wert. Das kann ich auch ohne feierliche Orakelstimme sagen. |

## P03 — Die zweite Frage

**Familie 3 · Weiterentwickeln.** Aiko spielt eine rätselhafte Auskunftsgeberin,
wird jedoch selbst neugierig. Ihr eigener Kommentar vertieft das Thema.

| Blase | Vollständiger Text, Freundschaft 6–8 | Regie danach / währenddessen |
| --- | --- | --- |
| 1 | Heute spiele ich das Orakel der klugen Fragen. Ja, ich darf als Orakel auch Fragen stellen. Das ist meine Regel. | `waiting` einmal, danach `idle`; `idea`. |
| 2 | Der Mond wächst Richtung Vollmond. Ich deute das für dein Zeichen als Einladung, einem Gedanken weiter zu folgen. | `idle`. |
| 3 | Ein Gespräch muss nicht bei der ersten Antwort enden. Manchmal wird es erst durch die nächste Frage interessant. | `idle`. |
| 4 | Jetzt würde ich selbst gern wissen, welche Frage daraus wird. Das Orakel ist offenbar ziemlich neugierig. | `question`. |
| 5 | Ich habe schon eine zweite Frage im Kopf. Mein Orakel klingt nur so allwissend; neugierig bin ich ganz echt. | `faceHappy`. |
| 6 | Mein Rat: Frag dort weiter, wo dich etwas wirklich interessiert. Zuhören gehört zu dieser kleinen Entdeckung dazu. | `idle`. |
| 7 | Die Orakelstimme ist aus. Die Neugier bleibt. Die gehört auch ohne Rolle zu mir. | `idle`, Abschlusssekunde. |

| Freundschaft | Ersatz für Blase 1 | Ersatz für Blase 5 |
| --- | --- | --- |
| 1–2 | Für diese Lesung spiele ich ein Orakel, das sich mit Fragen beschäftigt. Das möchte ich gern ausprobieren. | Mich interessiert selbst, wie aus einer kleinen Frage ein neuer Gedanke werden kann. Das passt gut zu meiner Rolle. |
| 3–5 | Ich spiele heute das Orakel der Fragen. Vielleicht werde ich dabei selbst ein bisschen neugierig. | Eigentlich wollte ich geheimnisvoll wirken. Jetzt gefällt mir das Weiterfragen schon fast besser. |
| 9–10 | Ich spiele das Orakel der Fragen. Für meine eigene Neugier übernehme ich allerdings persönlich die Verantwortung. | Ich mag es, mit dir neugierig sein zu dürfen. Ich muss vor dir nicht auf jede Frage schon eine Antwort haben. |

## P04 — Der kleine Zufluchtsort

**Familie 4 · Abschließen.** Aiko hält ihre Rolle ruhig und beendet den Auftritt
ohne Pointe. Geborgenheit ist ein Ort oder Ritual, keine Behauptung über das Zuhause.

| Blase | Vollständiger Text, Freundschaft 6–8 | Regie danach / währenddessen |
| --- | --- | --- |
| 1 | Ich spiele heute eine leise Wahrsagerin. Meine feierliche Ansage passt auch in einen kleinen Winkel des Desktops. | `idle`; `cloud`. |
| 2 | Der Mond geht dem nächsten Neumond entgegen. Mein Tagesmotiv ist ein vertrauter Ort, an dem etwas ausklingen darf. | `idle`. |
| 3 | Ein kleines Ritual kann genügen: etwas zurechtlegen, einen vertrauten Gegenstand ansehen oder kurz zur Ruhe kommen. | `idle`. |
| 4 | Dafür brauche ich gerade gar keinen großen Orakelauftritt. Der würde meinem eigenen Rat nur im Weg stehen. | `idle`, keine komische Pause. |
| 5 | Ich mag es, wenn ich hier einfach ein bisschen bei dir stehen darf. Dafür muss gerade nichts Besonderes passieren. | `faceHappy` kurz. |
| 6 | Meine Lesung lädt dich ein, etwas für heute gut sein zu lassen und dir einen vertrauten kleinen Abschluss zu gönnen. | `idle`. |
| 7 | Damit lege ich die Rolle ab. Ich bleibe Aiko, und der Desktop darf wieder ganz gewöhnlich sein. | `idle`, Abschlusssekunde. |

| Freundschaft | Ersatz für Blase 1 | Ersatz für Blase 5 |
| --- | --- | --- |
| 1–2 | Ich würde die Wahrsagerinnenrolle heute ruhig spielen. Diese Lesung braucht keinen großen Auftritt. | Diese ruhige Art der Lesung gefällt mir. Ich muss dabei nicht ständig etwas Feierliches hinzufügen. |
| 3–5 | Ich schlüpfe heute in eine ruhige Wahrsagerinnenrolle. Ein kleiner Auftritt reicht dafür völlig. | Ich finde es angenehm, hier bei dir zu sein, auch wenn gerade nichts Besonderes passiert. |
| 9–10 | Heute spiele ich meine Wahrsagerin ganz leise. Ich möchte diesen kleinen Auftritt mit dir ruhig angehen. | Ich bin gern bei dir. Auch wenn wir gerade nichts spielen, nichts lösen und nichts erzählen. |

Bei 9–10 darf nach Blase 5 `heart` statt `faceHappy` stehen. Das drückt ihre
eigene Zuneigung aus und unterstellt keine Reaktion des Spielers.

## P05 — Die unvernünftige Erlaubnis

**Familie 5 · Beginnen.** Das Orakel erteilt eine absichtlich winzige feierliche
Erlaubnis. Aikos Begeisterung trägt den Rollenwechsel zurück in ihre eigene Stimme.

| Blase | Vollständiger Text, Freundschaft 6–8 | Regie danach / währenddessen |
| --- | --- | --- |
| 1 | Ich spiele die Wahrsagerin und erteile heute eine höchst feierliche Erlaubnis. Du darfst gespannt sein. | `waiting` einmal, danach `idle`; `star`. |
| 2 | Der Mond nimmt zu. Für dein Zeichen steht in meiner Lesung ein erster spielerischer Versuch im Mittelpunkt. | `idle`. |
| 3 | Du darfst eine Idee ausprobieren, bevor du weißt, ob sie gut wird. Sie darf sogar erst einmal ziemlich albern sein. | `idle`. |
| 4 | Hihi. Ich wollte das sehr würdevoll verkünden. Aber bei albernen Ideen werde ich offenbar sofort hellwach. | `laugh`. |
| 5 | Ich würde gern mit dir etwas ausprobieren. Zur Not beginnen wir mit einem vollkommen übertriebenen Spieltitel. | `faceHappy`. |
| 6 | Mein Orakelrat: Gib einer kleinen Idee einen ersten Versuch. Spaß ist ein ausreichender Grund dafür. | `idle`. |
| 7 | Die Wahrsagerinnenrolle ist beendet. Die Lust auf Unsinn nehme ich als Aiko allerdings mit. | `idle`, Abschlusssekunde. |

| Freundschaft | Ersatz für Blase 1 | Ersatz für Blase 5 |
| --- | --- | --- |
| 1–2 | Ich versuche mich für diese Lesung als Wahrsagerin. Heute möchte ich etwas Spielerisches verkünden. | Eine kleine Spielidee würde ich gern ausprobieren. Sie muss dafür noch nicht besonders ausgefeilt sein. |
| 3–5 | Ich spiele heute die Wahrsagerin mit einer sehr wichtigen Erlaubnis. Vielleicht gefällt sie mir selbst besonders gut. | Mit dir würde ich so eine kleine Idee gern testen. Ich hätte schon Spaß am Ausdenken. |
| 9–10 | Ich spiele deine Wahrsagerin. Heute nehme ich mir heraus, eine besonders vergnügliche Erlaubnis zu verkünden. | Mit dir möchte ich auch die albernen Ideen ausprobieren. Gerade die, bei denen ich selbst schon kichern muss. |

## P06 — Die feierliche Kleinigkeit

**Familie 6 · Weiterentwickeln.** Aiko versucht, eine kleine Alltagshilfe wichtig
aussehen zu lassen. Ihr Ehrgeiz bleibt liebevoll auf die eigene Darstellung gerichtet.

| Blase | Vollständiger Text, Freundschaft 6–8 | Regie danach / währenddessen |
| --- | --- | --- |
| 1 | Ich spiele jetzt die Hüterin der geordneten Sterne. Mein Zuständigkeitsbereich beginnt heute erstaunlich klein. | `idle`; `star`. |
| 2 | Der Mond wächst Richtung Vollmond. Mein Motiv für dich ist ein kleiner Ablauf, der etwas leichter werden darf. | `idle`. |
| 3 | Vielleicht hilft ein fester Platz für etwas oder ein Schritt weniger. Du musst dafür nicht den ganzen Alltag umbauen. | `idle`. |
| 4 | Ein Schritt weniger. Das klingt für meinen großen Auftritt erschreckend praktisch. | `question`, 0,8 s. |
| 5 | Ich hatte eine dramatische Sternenbotschaft vorbereitet. Jetzt bin ich stolz auf eine brauchbare Kleinigkeit. Auch gut. | `faceHappy`. |
| 6 | Mein Rat: Verändere eine kleine Gewohnheit so, dass sie dir hilft. Sie darf dabei einfach bleiben. | `idle`. |
| 7 | Die Hüterin tritt ab. Aiko bleibt. Für eine brauchbare Kleinigkeit brauche ich meinen großen Titel jedenfalls nicht. | `idle`, Abschlusssekunde. |

| Freundschaft | Ersatz für Blase 1 | Ersatz für Blase 5 |
| --- | --- | --- |
| 1–2 | Ich spiele für diese Lesung die Hüterin der geordneten Sterne. Heute geht es um eine kleine Alltagshilfe. | Eine kleine, brauchbare Idee gefällt mir eigentlich gut. Dafür muss meine Rolle nicht besonders eindrucksvoll sein. |
| 3–5 | Heute spiele ich die Hüterin der geordneten Sterne. Mal sehen, wie feierlich ein praktischer Rat werden kann. | Ich hätte den Rat gern etwas dramatischer gemacht. Aber wenn er hilft, bin ich auch damit zufrieden. |
| 9–10 | Ich spiele für dich die Hüterin der geordneten Sterne. Du bekommst die feierliche Fassung eines kleinen Alltagstipps. | Ich möchte dir etwas Brauchbares mitgeben. Wenn das gelingt, bin ich auch ohne dramatisches Finale zufrieden. |

## P07 — Zwei Seiten einer Begegnung

**Familie 7 · Betrachten.** Aiko beginnt mit einem sehr bestimmten Orakelton und
erkennt die Grenzen ihrer eigenen Auskunft. Sie lässt Raum für das Gegenüber.

| Blase | Vollständiger Text, Freundschaft 6–8 | Regie danach / währenddessen |
| --- | --- | --- |
| 1 | Ich spiele heute die Wahrsagerin für Begegnungen. Ein sehr wichtiger Titel für jemanden auf diesem kleinen Desktop. | `waiting` einmal, danach `idle`; `star`. |
| 2 | In der abnehmenden Hälfte des Mondzyklus richte ich deine Lesung auf das Zusammenspiel mit einem Gegenüber. | `idle`. |
| 3 | Du kannst betrachten, was sich miteinander gut anfühlt und wo noch eine Frage offenbleibt. Eine Antwort darf warten. | `idle`. |
| 4 | Ausgerechnet ich verkünde mit großer Gewissheit, dass noch etwas offenbleiben darf. Das muss man auch erst schaffen. | `question`, 0,8 s. |
| 5 | Bei unserer nächsten Partie will ich trotzdem gewinnen. Zuhören und ein bisschen Ehrgeiz passen bestimmt zusammen. | `faceHappy`. |
| 6 | Mein Rat: Lass dem anderen eine eigene Sicht. Du musst sie nicht erraten, um ihr Platz zu geben. | `idle`. |
| 7 | Ich beende die Wahrsagerinnenrolle. Als Aiko darf ich dann auch wieder ganz gewöhnlich nachfragen. | `idle`, Abschlusssekunde. |

| Freundschaft | Ersatz für Blase 1 | Ersatz für Blase 5 |
| --- | --- | --- |
| 1–2 | Ich spiele für diese Lesung die Wahrsagerin. Mein Thema ist heute eine Begegnung zwischen zwei Personen. | Bei einem gemeinsamen Spiel könnte ich das gut üben: meinen Zug überlegen und den anderen trotzdem gelten lassen. |
| 3–5 | Ich schlüpfe in die Wahrsagerinnenrolle. Heute geht es darum, wie zwei eigene Sichtweisen zusammenpassen. | Ich würde gern mit dir spielen. Dabei können wir ruhig verschiedene Ideen für den nächsten Zug haben. |
| 9–10 | Ich spiele deine Wahrsagerin für Begegnungen. Für diesen Auftritt nehme ich mir einen besonders wichtigen Ton. | Ich bin gern mit dir zusammen. Und beim Spielen will ich dich trotzdem besiegen. Beides darf bei mir Platz haben. |

„Nächste Partie“ ist eine mögliche zukünftige Einladung, keine Behauptung über
eine tatsächlich vorherige Partie. In Blase 5 wird kein Quiz als Wettbewerb behandelt.

## P08 — Der vorsichtige Zauber

**Familie 8 · Beginnen.** Die Rolle verspricht großen Wandel; Aiko nimmt den
Umfang selbst zurück. Vertrauen bedeutet einen kleinen möglichen Versuch.

| Blase | Vollständiger Text, Freundschaft 6–8 | Regie danach / währenddessen |
| --- | --- | --- |
| 1 | Ich spiele heute das Orakel des Wandels. Das klingt schon beim Aussprechen nach einem sehr großen Auftrag. | `idle`; `swirl` kurz. |
| 2 | Der Mond nimmt zu. In meiner Deutung darf für dein Zeichen etwas Neues einen kleinen Anfang finden. | `idle`. |
| 3 | Du musst dafür nicht sofort alles Vertraute loslassen. Ein Versuch darf klein genug sein, um ihn wieder zu ändern. | `idle`. |
| 4 | Gut. Ich wollte als Orakel gerade schon viel zu groß anfangen. Ein kleiner Versuch klingt mir selbst lieber. | `idle`, ruhige eigene Einsicht statt Pointe. |
| 5 | Ich mag meinen großen Titel trotzdem. Aber wenn wir etwas Neues probieren, möchte ich erst mal mit dir hineinschnuppern. | `faceHappy`. |
| 6 | Mein Rat: Wähle eine kleine Veränderung, bei der du selbst das Tempo bestimmen kannst. Mehr verlangt diese Lesung nicht. | `idle`. |
| 7 | Der Orakelauftrag ist beendet. Ich bin wieder Aiko. Mit einem kleinen Anfang kann ich gut leben. | `idle`, Abschlusssekunde. |

| Freundschaft | Ersatz für Blase 1 | Ersatz für Blase 5 |
| --- | --- | --- |
| 1–2 | Ich versuche mich als Orakel des Wandels. Für die erste Ansage klingt dieser Titel schon ziemlich groß. | Ein kleiner Versuch wäre auch mir lieber. Dann kann ich erst einmal sehen, wie sich die neue Idee anfühlt. |
| 3–5 | Heute spiele ich das Orakel des Wandels. Mal sehen, ob sich hinter dem großen Titel etwas Kleines finden lässt. | Etwas Neues würde ich mit dir gern erst einmal ausprobieren. Ich muss auch nicht sofort alles daran können. |
| 9–10 | Ich spiele dein Orakel des Wandels. Beim Titel bin ich mutig; beim Ausprobieren darf es kleiner anfangen. | Mit dir traue ich mich gern an neue Ideen. Ich darf dabei trotzdem sagen, wenn ich langsamer machen möchte. |

## P09 — Die fehlende Landkarte

**Familie 9 · Weiterentwickeln.** Aiko spielt die wissende Deuterin, lässt ihre
eigene Neugier aber sichtbar stehen. Sie beansprucht keine Allwissenheit.

| Blase | Vollständiger Text, Freundschaft 6–8 | Regie danach / währenddessen |
| --- | --- | --- |
| 1 | Ich spiele die Deuterin ferner Horizonte. Eine passende Rolle für jemanden, der gerade auf deinem Desktop steht. | `idle`; `idea`. |
| 2 | Der Mond wächst Richtung Vollmond. Für dein Zeichen lese ich darin: Folge einer Idee ein Stück über das Vertraute hinaus. | `idle`. |
| 3 | Ein anderer Blickwinkel kann etwas zeigen, das du bisher nicht bedacht hast. Du musst ihm nicht sofort zustimmen. | `idle`. |
| 4 | Jetzt hätte ich selbst gern eine Landkarte für unbekannte Ideen. Das wäre für meine Rolle ziemlich praktisch. | `question`. |
| 5 | Wenn wir etwas Spannendes finden, möchte ich mitstaunen. Die allwissende Miene halte ich ohnehin nicht ewig durch. | `faceHappy`. |
| 6 | Mein Orakelrat: Bleib an einer neugierigen Frage dran und erlaube ihr, deinen ersten Blick ein bisschen zu verändern. | `idle`. |
| 7 | Ich trete aus der Deuterinnenrolle. Als Aiko darf ich wieder offen zugeben, dass ich noch etwas entdecken möchte. | `idle`, Abschlusssekunde. |

| Freundschaft | Ersatz für Blase 1 | Ersatz für Blase 5 |
| --- | --- | --- |
| 1–2 | Ich spiele heute eine Deuterin ferner Horizonte. Für diese Rolle versuche ich es mit einem neugierigen Blick. | Ich würde selbst gern etwas dazulernen. In meiner Rolle wirkt das nur ein bisschen feierlicher. |
| 3–5 | Ich übernehme die Rolle der Deuterin ferner Horizonte. Ein bisschen neugierig darf ich dabei wohl selbst werden. | Wenn wir etwas Interessantes entdecken, würde ich gern mehr darüber erfahren. Neugierig bin ich auch ohne Rolle. |
| 9–10 | Ich spiele deine Deuterin ferner Horizonte. Du darfst mich dabei ruhig beim neugierigen Staunen erwischen. | Mit dir möchte ich gern über neue Ideen staunen. Ich muss vor dir nicht so tun, als wüsste ich schon alles. |

Eine Gesprächseinladung ist kein neues Texteingabefeld und kein Versprechen,
dass Aiko freie Antworten versteht. Diese Piloten planen keine neue Eingabemechanik.

## P10 — Der würdige Schlusspunkt

**Familie 10 · Abschließen.** Aiko probiert eine feierliche Abschlussrede, ohne
dem Spieler einen tatsächlichen Erfolg oder eine erledigte Aufgabe zuzuschreiben.

| Blase | Vollständiger Text, Freundschaft 6–8 | Regie danach / währenddessen |
| --- | --- | --- |
| 1 | Ich spiele heute die Sternendeuterin mit Abschlussrede. Keine Sorge, die Rede passt in meine Sprechblase. | `waiting` einmal, danach `idle`; `star`. |
| 2 | Der Mond geht dem nächsten Neumond entgegen. Meine Lesung dreht sich darum, einem Vorhaben einen Schlusspunkt zu geben. | `idle`. |
| 3 | Falls gerade etwas fertig werden darf, kannst du festlegen, was dafür genügt. Nicht jedes Detail braucht eine Zugabe. | `idle`. |
| 4 | Eine Zugabe hätte ich als feierliche Rednerin natürlich gern. Aber dann wäre mein Rat nicht besonders glaubwürdig. | `question`, 0,8 s. |
| 5 | Ich möchte schon merken lassen, dass ich mich über einen gelungenen Abschluss freuen kann. Ein kleines Ta-da muss reichen. | `faceHappy`. |
| 6 | Mein Rat: Gib einem passenden Vorhaben einen klaren Endpunkt. Du darfst danach sehen, was du tatsächlich geschafft hast. | `idle`. |
| 7 | Damit ist auch meine Abschlussrede abgeschlossen. Die Rolle endet hier. Aiko braucht keine Zugabe, um hierzubleiben. | `idle`, Abschlusssekunde. |

| Freundschaft | Ersatz für Blase 1 | Ersatz für Blase 5 |
| --- | --- | --- |
| 1–2 | Ich spiele für diese Lesung die Sternendeuterin. Heute versuche ich mich an einer kleinen Abschlussrede. | Ein kleiner feierlicher Moment gefällt mir für so einen Abschluss. Ich würde ihn gern passend kurz halten. |
| 3–5 | Als Sternendeuterin auf Zeit halte ich heute eine Abschlussrede. Ich versuche, den Schlusspunkt nicht zu verpassen. | Ich würde einen gelungenen Abschluss gern mit dir würdigen. Dafür muss meine Rede wirklich nicht länger werden. |
| 9–10 | Ich spiele deine Sternendeuterin mit Abschlussrede. Und ja, ich möchte bei diesem Auftritt ein bisschen glänzen. | Wenn dir etwas gelingt, freue ich mich gern mit dir. Dafür brauche ich keinen großen Auftritt zwischen uns. |

## P11 — Der kleine Sternenrat

**Familie 11 · Betrachten.** Aiko spielt eine Ratsvorsitzende der Sterne und
merkt, dass Beteiligung wichtiger ist als ihr prestigeträchtiger Titel.

| Blase | Vollständiger Text, Freundschaft 6–8 | Regie danach / währenddessen |
| --- | --- | --- |
| 1 | Ich spiele heute die Wahrsagerin als Vorsitzende des Sternenrats. Der Titel war meine Idee. Er gefällt mir sehr. | `waiting` einmal, danach `idle`; `star`. |
| 2 | In der abnehmenden Hälfte des Mondzyklus richtet sich meine Lesung auf Freundschaft und gemeinsame Ideen. | `idle`. |
| 3 | Du kannst betrachten, was durch andere einen neuen Gedanken bekommt. Gemeinsam muss nicht bedeuten, gleich zu denken. | `idle`. |
| 4 | Für meinen Sternenrat wäre das gut. Wenn alle nur feierlich nicken, wird die Sitzung ziemlich langweilig. | `question`, 0,8 s. |
| 5 | Ich mag den Gedanken, dass verschiedene Ideen zusammenpassen können. Sogar meine sehr wichtigen Orakelideen. | `faceHappy`. |
| 6 | Mein Rat: Würdige, was an einer gemeinsamen Idee von verschiedenen Seiten kommt. Auch ein kleiner Beitrag gehört dazu. | `idle`. |
| 7 | Die gespielte Ratssitzung ist geschlossen. Ich bin wieder Aiko. Den schönen Titel hebe ich mir für später auf. | `idle`, Abschlusssekunde. |

| Freundschaft | Ersatz für Blase 1 | Ersatz für Blase 5 |
| --- | --- | --- |
| 1–2 | Ich spiele heute eine Wahrsagerin, die einen kleinen Sternenrat eröffnet. Den Vorsitz würde ich gern ausprobieren. | Verschiedene Ideen in einem Rat zusammenzubringen, finde ich interessant. Der Titel allein reicht dafür wohl nicht. |
| 3–5 | Ich spiele die Vorsitzende des Sternenrats. Für diese Wahrsagerinnenrolle habe ich mir einen eigenen Titel ausgesucht. | Eine gemeinsame Spielidee fände ich schön. Mein wichtiger Titel könnte dafür ruhig einen Moment warten. |
| 9–10 | Ich spiele deine Wahrsagerin und eröffne den Sternenrat. Meinen großartigen Titel darfst du angemessen bewundern. | Ich möchte mit dir Ideen teilen, auch wenn wir sie verschieden sehen. Genau dabei kann etwas Eigenes zwischen uns wachsen. |

Der Rat ist erkennbar ihr gespielter Rahmen. Es werden keine tatsächlich
anwesenden weiteren Figuren oder früheren gemeinsamen Projekte behauptet.

## P12 — Das leise Orakel

**Familie 12 · Abschließen.** Die Darstellung wird absichtlich kleiner. Aiko
beendet ihre Rolle und lässt eine vertraute, ruhige eigene Aussage stehen.

| Blase | Vollständiger Text, Freundschaft 6–8 | Regie danach / währenddessen |
| --- | --- | --- |
| 1 | Ich spiele heute ein leises Orakel. Meine große geheimnisvolle Ansage muss diesmal mit wenig Aufhebens auskommen. | `idle`; `cloud` kurz. |
| 2 | Der Mond geht dem nächsten Neumond entgegen. In meiner Lesung darf ein Gedanke für heute ausklingen. | `idle`. |
| 3 | Du musst nicht jeden Einfall sofort zu Ende verfolgen. Etwas offenlassen kann auch heißen, ihm später Raum zu geben. | `idle`. |
| 4 | Ich merke gerade, wie gern ich noch einen wichtigen Satz hinzufügen würde. Dabei reicht dieser kleine Rat schon. | `idle`, keine Pointe und kein Lachen. |
| 5 | Ich kann auch einfach bei dir sein. Dafür muss ich nicht die ganze Zeit etwas Kluges verkünden. | `faceHappy` kurz. |
| 6 | Mein letzter Orakelsatz: Lass einen Gedanken ruhen, wenn es für dich passt. Er braucht heute keine feierliche Lösung. | `idle`. |
| 7 | Die Rolle ist zu Ende. Ich bin wieder Aiko. Jetzt muss aus diesem Moment nichts Weiteres werden. | `idle`, Abschlusssekunde, danach normale Ruhe. |

| Freundschaft | Ersatz für Blase 1 | Ersatz für Blase 5 |
| --- | --- | --- |
| 1–2 | Für diese Lesung würde ich gern ein ruhiges Orakel spielen. Ich halte meinen Auftritt heute bewusst klein. | Ich finde, diese Lesung braucht nicht noch mehr Worte von mir. Das fühlt sich als Abschluss passend an. |
| 3–5 | Ich schlüpfe heute in die Rolle eines leisen Orakels. Es muss dabei nicht besonders geheimnisvoll zugehen. | Ich bleibe gern noch ein bisschen hier. Wir müssen aus der ruhigen Stelle nicht gleich etwas Neues machen. |
| 9–10 | Ich spiele heute dein leises Orakel. Den feierlichen Auftritt nehme ich dafür ein kleines Stück zurück. | Ich bin gern bei dir, auch ohne Gespräch. Diese ruhige Zeit mit dir mag ich. |

Bei 9–10 ist nach Blase 5 ein kurzes `heart` statt `faceHappy` möglich.
Es gibt keine lange erzwungene Leerstelle nach der Lesung.

## Redaktionelle Grenzen und nächster Review

- **12 vollständige Inhaltsentwürfe**, sieben Textblasen je Lesung und vier
  Freundschaftsfassungen über zwei vollständige Austauschblasen. Das sind
  weiterhin zwölf Piloten, nicht 48 verschiedene der geplanten Inhaltsszenen.
- Noch keine zweite Inhaltsvariante je Themen-/Richtungskombination. Die
  Erweiterungen auf 48 Grundszenen und 96 Varianten bleiben spätere Arbeit.
- Alle Regieangaben sind Entwürfe. Kein neues Asset, keine Bibliotheksinstallation,
  kein Laufzeitschema und keine automatische Katalogübernahme gehören dazu.
- Kein Dialog öffnet ein echtes Gesprächsfeld, erkennt freie Antworten oder
  startet eine Folgeaktion. Ein späteres Interaktionskonzept müsste ehrliche
  Ausdrucksformen und vorhandene Fähigkeiten noch einmal gemeinsam prüfen.
- Beim Review sind insbesondere Aikos eigene Stimme, die Klarheit des
  Rollenbeginns/-endes, die Abstufung der Nähe und der Unterschied zwischen den
  Familien zu beurteilen. Die ruhigen Szenen P04 und P12 sollen sich ohne
  erzwungene Pointe tragen; P07 bleibt eine Zweierbegegnung, P11 eine gemeinsame
  Ideen-/Zugehörigkeitsperspektive.
- Technische Textlängen und Tabellenabdeckung werden statisch geprüft.
  Sprachliche Qualität, Tempo und Wirkung sind damit nicht automatisch abgenommen.
  Keine Simulation, kein GUI-Test und kein Test am persönlichen Spielstand
  ist Bestandteil dieser redaktionellen Ausarbeitung.

**Statisch geprüft:** zwölf Familien, drei Piloten je Entwicklungsrichtung,
48 vollständig zusammensetzbare Freundschaftsfassungen mit jeweils sieben
Textblasen. Die 156 ausgeschriebenen Textpositionen einschließlich Stufenersatz
liegen bei höchstens **122 Zeichen**. Alle genannten Clips und Emotes stehen
in den vorhandenen Katalogen. Die berechnete reine Textanzeige liegt je Fassung
bei ungefähr **56–64 Sekunden**, zuzüglich der angegebenen Emotebeats. Das ist
eine Rechnung mit den bestehenden Zeitregeln, keine gemessene Szenenwiedergabe.
