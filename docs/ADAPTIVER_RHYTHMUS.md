# Aikos adaptiver Lebensrhythmus – v0.9

## Produktgrenze

Aiko ist die **Personifizierung des laufenden Computers**, hat aber gleichzeitig
ihre eigene Persönlichkeit, Bedürfnisse, Tages- und Wochentagsrhythmen. CPU-,
GPU- und RAM-Signale beschreiben ihre aktuelle **Arbeit**, nicht ihr ganzes
Leben. Windows-Uptime allein ist weder Wachzeit noch Anstrengung. Keine Academy,
keine Geschichte außerhalb des Desktops, kein LLM und keine Cloud.

## Verarbeitete Eingaben

- Lokale Systemuhr / Wochentag, vorhandene Mahlzeiten- und Ruhephasen.
- Hardware-Snapshot aus `system_activity.py`: CPU und GPU primär;
  Arbeitsspeicherdruck nur schwach. Unbekannte Sensoren bleiben unbekannt.
- System-Uptime als **Kontextinformation**, nie als Erschöpfungsmultiplikator.
- Windows-Inaktivitätsdauer über `GetLastInputInfo`, ohne Tastaturinhalt,
  Fenstertitel, Prozessnamen oder Browser-/Mikrofon-Inhalte zu erfassen.
- Bedürfnisse aus `PetState` und bestehende manuelle Pflegeinteraktionen.

## AdaptiveRoutine – separat und deterministisch testbar

`aiko_pet/adaptive.py` bietet `Observation`, `Behaviour`, `AdaptiveMemory` und
`AdaptiveRoutine`. Die GUI liest diese Schicht nur bei **neuen**
Hardwaremessungen (~6 Sekunden) ein. Sie läuft nicht in der Systemabfrage-
Worker-Thread-Umgebung, sondern auf dem Tk-Thread und benötigt selbst keine
weiteren Abhängigkeiten.

Die Modellschicht kennt folgende Beschäftigungen:

- `working`: Momentan hohe bzw. geglättet hohe Last.
- `recovering`: Kurz nach einer echten Arbeitsphase.
- `resting`: Längere ruhige Phase ohne Benutzereingaben.
- `present`: Nutzeraktivität erkennbar, keine hohe Rechenlast.
- `wandering`: Kein anderer Zustand dominiert (inklusive unbekannter Eingabe).

Die Beanspruchung (`strain`, 0–100) wächst mit anhaltender Last und sinkt bei
Entlastung. Sie bestimmt **nicht** unmittelbar Sättigung, Laune oder Energie.
Bei größerer Beanspruchung und begrenzter Energie kann sie aber die bestehende
Emotionsauswahl beeinflussen. Der Dialogtext-Katalog bleibt v0.8-Stand.

### Nacht und Pausen

- Aiko darf während **tatsächlicher hoher Rechenlast** nachts wach bleiben.
- Bei abendlicher Ruhe kann sie nach wie vor schlafen; auch wenn der PC seit
  Tagen läuft. Bei sehr niedriger Energie kann sie trotz aktiver Person zu
  Bett gehen – sie kopiert die Nutzergewohnheiten nicht blind.
- Eine vorhandene **manuelle** Schlafentscheidung wird nicht übersteuert.
- Bei längerer ungestörter Ruhe, knapper Energie oder gelernt ruhiger
  Tagesphase ist ein **einmaliger Mittagsschlaf pro Kalendertag** möglich.
  Er endet nach höchstens 45 Minuten oder früher bei neuer Arbeit/Aktivität.
- Auto-Routine aus der GUI bleibt weiterhin abschaltbar.
- Fehlende Telemetrie führt zur bisherigen v0.8-Routine statt zu erfundenen
  Nullwerten.

### Lernen der Nutzungsgewohnheiten

Je Wochentag und Stunde existieren 168 **verdichtete Buckets** für die Zeit,
mittlere Beanspruchung und Anwesenheit; die Statistik altert täglich mit
Faktor `0.965` (ungefähr 19 Tage Halbwertszeit). Jede Beobachtung zählt
höchstens 30 Sekunden, damit Rechner-Ruhemodus, Application-Pausen und
Systemuhr-Sprünge keine erfundenen Aktivitätsstunden erzeugen.

Nach einem längeren unbeobachteten App-Stopp wird veraltete aktuelle
Arbeitsbeanspruchung entschärft, ohne für die nicht beobachtete Zeit
Arbeits- oder Ruheminuten zu behaupten.

Die Zeitreihe umfasst keine Roh-Eingaben und keine Prozessnamen. Eine einzelne
ungewöhnlich intensive Nacht reicht nicht, um einen verlässlichen Rhythmus zu
behaupten. Erst nach Beobachtungen an getrennten gleichen Wochentagen
(über mehrere Wochen) wird eine Erwartung abgeleitet. Daraus können derzeit
mögliche Ruhephasen und die Anzeige einer eingespielten Gewohnheit entstehen;
detaillierte kontextsensitive Kommentare folgen bewusst erst auf diese
validierte Verhaltensbasis.

**Fehlende Daten ≠ geringe Last**: Ein Snapshot ohne CPU/GPU/verwaltbaren
Arbeitsspeicher aktualisiert keine Last-Buckets. GPU-Auslastung wird nur für
NVIDIA über `nvidia-smi` gelesen. Systemlast wird nicht mit einem bestimmten
Programm oder einer Nutzerabsicht gleichgesetzt.

## Datenspeicherung und Kontrolle

Optionaler `adaptive`-Abschnitt in der bisherigen lokalen, atomar geschriebenen
`%LOCALAPPDATA%\AikoDesktopPet\state.json` (Schema bleibt `version: 1`).
Ältere Spielstände behalten **alle** vorhandenen Bedürfnisse, Einstellungen
und Panelpositionen. Unbekannte oder ungültige Lernfelder werden verworfen.

In den Einstellungen:

- **Rechnerauslastung beobachten**: schaltet die Messung ab, einschließlich
  lernender Beobachtung.
- **Meinen Rhythmus kennenlernen**: unterbindet neue Stundenstatistik und
  ihre Nutzung, lässt *aktuelle* Arbeit/Reaktionen aber aktiv.
- **Gelerntes Tagesmuster löschen**: entfernt alle 168 Buckets, ohne Pflege-
  werte oder unmittelbaren Arbeitszustand zu löschen.

Keine versteckten Datenübertragungen; für GPU-Abfragen wird ausschließlich das
lokale `nvidia-smi` verwendet. Der Spielstand enthält keine CPU/GPU/RAM-
Rohverläufe, keine Webseiten, Texte oder Programmbezeichnungen.

## Getestete Szenarien

- 72 Stunden dauerhaft eingeschalteter PC mit nächtlichem Leerlauf und
  wechselnden intensiven Tagesphasen; keine Phantomerschöpfung nur durch Uptime.
- Intensive Rechenarbeit über die reguläre Schlafenszeit, danach Schlaf bei
  tatsächlicher Entlastung.
- Manuell gewählter Schlaf hat Vorrang.
- Ein einmaliger, begrenzter Mittagsschlaf mit Aufwachen.
- Schnelle Lastspitzen vs. stundenlange Belastung.
- Einzelner abweichender Arbeitstag beeinflusst nicht sofort das
  mehrwöchige Nutzungsprofil; wiederkehrende Muster werden langsam gelernt.
- Fehlende Sensorwerte, unterbrochene Messung, ausgeschaltetes Lernen,
  Rücksetzung, beschädigte und alte Speicherstände.

## Bewusste Grenzen für den nächsten Slice

- Die bisherigen v0.8-Sprechblasen bleiben erhalten. Die neue Vokabelmenge,
  kontextabhängige Dialogfolgen, Erinnerung an Klickeskalation und zusätzliche
  Animationen werden **nicht** stillschweigend als fertig ausgegeben.
- Kein echtes Windows-24/7-Langzeittesting in dieser Linux-Testumgebung;
  Sleep/Resume, NVIDIA-Abfragen und Tk-Z-Order brauchen einen Praxistest.
- Profil-Lernen benötigt echte längere Nutzungszeit. Zunächst zeigen nur
  Lastsituation, Schlaf- und Bewegungsverhalten die Änderung.
