@echo off
cd /d "%~dp0"
echo Starte Aiko im Diagnosemodus ...
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -m aiko_pet
    goto finished
)
where py >nul 2>&1
if %ERRORLEVEL% == 0 (
    py -m aiko_pet
) else (
    python -m aiko_pet
)
:finished
set "AIKO_DEBUG_RESULT=%ERRORLEVEL%"
echo.
echo Aiko wurde beendet. Falls eine Fehlermeldung angezeigt wird, bitte mitschicken.
pause
exit /b %AIKO_DEBUG_RESULT%
