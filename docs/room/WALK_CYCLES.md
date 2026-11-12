# Gehfolgen im Raum

Die beiden Tiefen-Gehfolgen stammen aus der abgenommenen privaten Vorschau
`2026-11-11-raum-naehe-hochformat-vorschau`. Der Raumexport verwendet die
acht Frames aus `frontalgang/zyklus` für `toward` und aus
`rueckgang/zyklus` für `away`, jeweils in der Reihenfolge 00 bis 07.
Die hochauflösenden Quellen liegen im lokalen Asset-Archiv.

Der Export überträgt alle Bilder mit demselben Maßstab `312/1158` auf die
384 × 416 Pixel große Laufzeitfläche. Der Vorschauanker `(608, 1240)`
liegt dort bei `(190, 388)`, entsprechend dem logischen Anker
`(95, 194)` der Seitenprofile. Alpha-Werte von 1 wurden vor dem
Verkleinern entfernt. Die gezeichneten Schuhstellungen und ihre Abstände
zur gemeinsamen Bodenlinie bleiben Teil der Animation.

Die Raumversion spielt jeden der acht Frames für 155 ms. Der gesamte
Zyklus deckt zwei Schritte zu je 620 ms ab und passt damit zum seitlichen
Schritttakt.

Die Wegsuche liefert nur gerade Abschnitte. Für das sichtbare Abbiegen
liefert die Positionsinterpolation außerdem die Richtung ihres aktuellen
Abschnitts. Die Wandansicht beim Beginn eines Abschnitts bestimmt zusammen
mit der Laufrichtung die Gehfolge. Die Folge wechselt beim Abbiegen, ohne
die Einleitung vom seitlichen Losgehen erneut abzuspielen.

Im geraden Bereich jeder Wandansicht bestimmt die seitliche Raumkoordinate
die Bildschirmposition. Die Tiefe bestimmt Aikos Größe nach der Kurve aus
der freigegebenen Annäherungsvorschau. Am Übergang zwischen zwei Wänden
verbindet ein schmaler Bereich die Ansichten kontinuierlich.

**Aiko rufen** behält bis Freundschaftsstufe 5 den normalen Raumabstand.
Auf Stufe 6 endet der Ruf in der Oberkörperansicht, ab Stufe 7 in der
Videocall-Nahansicht. Die Raumsteuerung wählt den erreichbaren Endpunkt
vor der zur Kamera gewandten Wand. Auf der letzten Geraden wächst der
Ausschnitt mit der tatsächlich zurückgelegten Strecke. In der Nahansicht
wartet Aiko frontal und blinzelt im gewohnten Rhythmus.
