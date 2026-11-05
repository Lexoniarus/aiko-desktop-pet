@echo off
cd /d "%~dp0"
echo Starte Aiko im Diagnosemodus ...
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -m aiko_pet
    goto finished
)
echo Die lokale Aiko-Umgebung fehlt.
echo Bitte zuerst Aiko_installieren.bat ausfuehren.
set "AIKO_DEBUG_RESULT=1"
goto report
:finished
set "AIKO_DEBUG_RESULT=%ERRORLEVEL%"
:report
echo.
echo Aiko wurde beendet. Falls eine Fehlermeldung angezeigt wird, bitte mitschicken.
pause
exit /b %AIKO_DEBUG_RESULT%
