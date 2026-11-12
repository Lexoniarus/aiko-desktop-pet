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
Abschnitts. Die Ansicht wählt aus dieser Richtung und dem Blickwinkel
zum Betrachter genau eine der vier Gehfolgen. Die Einleitung beim
seitlichen Losgehen bleibt erhalten. Innerhalb eines laufenden Wegs
wechselt die Gehfolge an der Ecke, ohne die Einleitung neu abzuspielen.
