@echo off
cd /d "%~dp0"
if exist "%~dp0.venv\Scripts\pythonw.exe" (
    start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0Aiko_Pet.pyw"
    exit /b 0
)
echo Die lokale Aiko-Umgebung fehlt.
echo Bitte zuerst Aiko_installieren.bat ausfuehren.
pause
exit /b 1
