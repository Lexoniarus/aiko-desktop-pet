@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish_to_github.ps1"
set "STATUS=%ERRORLEVEL%"
echo.
if not "%STATUS%"=="0" echo Veroeffentlichen nicht erfolgreich. Bitte Fehlermeldung pruefen.
pause
exit /b %STATUS%
