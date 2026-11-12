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

Die acht Bilder des Tiefengangs entsprechen zwei Schritten mit je 620 ms
bei normalem Gehtempo. Die Wiedergabe wählt das Bild anhand der tatsächlich
zurückgelegten Strecke. Beim Seitwärtsgang wird die Schrittlänge an die
Darstellungsgröße des Profils und die horizontale Panoramaskala angepasst.

Die Wegsuche verwendet Bögen mit konstantem Kameraabstand und Geraden
entlang einer Blickrichtung. Beide Abschnitte werden gegen die vorhandenen
Möbelflächen geprüft. Die Anzeige interpoliert dieselben Abschnitte und
wechselt die Gehfolge beim tatsächlichen Abbiegen.

Der Winkel zur Kamera bestimmt die horizontale Bildschirmposition.
Fußhöhe, Größe und Überdeckung am Boden folgen demselben Kameraabstand.
Die Wandgrenzen ändern die Geometrie der Laufbahn nicht. Bei gleichem
Bodenabstand bleibt ein Gegenstand vor Aiko sichtbar.

**Aiko rufen** hält auf allen Freundschaftsstufen den normalen Raumabstand.
Ist Aiko sichtbar, bleibt ihr Ziel auf ihrer aktuellen Blickrichtung zur
Kamera. Während des Wegs haben ausdrücklich gerufene Ziele Vorrang vor
autonomen Objektinteraktionen. Nach der Ankunft wartet Aiko frontal.
