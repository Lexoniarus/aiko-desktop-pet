@echo off
cd /d "%~dp0"
echo Starte Aiko im Diagnosemodus ...
where py >nul 2>&1
if %ERRORLEVEL% == 0 (
    py -m aiko_pet
) else (
    python -m aiko_pet
)
echo.
echo Aiko wurde beendet. Falls eine Fehlermeldung angezeigt wird, bitte mitschicken.
pause
