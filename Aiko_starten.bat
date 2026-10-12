@echo off
cd /d "%~dp0"
where pyw >nul 2>&1
if %ERRORLEVEL% == 0 (
    start "" pyw Aiko_Pet.pyw
    exit /b 0
)
where pythonw >nul 2>&1
if %ERRORLEVEL% == 0 (
    start "" pythonw Aiko_Pet.pyw
    exit /b 0
)
echo Python konnte nicht gefunden werden.
echo Bitte Python von https://www.python.org/downloads/ installieren.
pause
