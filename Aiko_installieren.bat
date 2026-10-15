@echo off
setlocal
cd /d "%~dp0"
echo Aiko Desktop Pet - Einrichtung
echo.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\install_windows.ps1" %*
set "AIKO_SETUP_RESULT=%ERRORLEVEL%"
echo.
if not "%AIKO_SETUP_RESULT%" == "0" echo Einrichtung fehlgeschlagen. Die Fehlermeldung steht oben.
pause
exit /b %AIKO_SETUP_RESULT%
