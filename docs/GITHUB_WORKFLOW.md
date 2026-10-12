# Entwicklung mit GitHub

Repository: https://github.com/Lexoniarus/aiko-desktop-pet
Default-Branch: `main` · Baseline: v0.13.

## Erstveröffentlichung

Das Projektpaket in einen Ordner entpacken und unter Windows `Auf_GitHub_veroeffentlichen.bat` starten. Das Skript klont `main` zunächst neu und legt **nur einen normalen Commit** an. Ohne Authentifizierung bei GitHub oder bei zwischenzeitlich geändertem Remote-Stand wird der Push abgelehnt; es wird **kein Force-Push** verwendet.

## Weiterentwicklung

Für zukünftige Arbeiten neue `feature/*`-Branches und Pull Requests nutzen. Die GitHub-Actions-Tests sollten vor Übernahmen nach `main` erfolgreich sein. Die echte Windows-GUI bleibt zusätzlich ein manueller Abnahmetest.

Keine Spielstände, persönlichen Daten, Fonts, Logs, APIschlüssel oder Test-Caches committen. `.gitignore` ist entsprechend vorbereitet. Der Character-Code und die Originalsprites sind unabhängig von den Kenney-Assets lizenziert; siehe `ASSETS.md`.
