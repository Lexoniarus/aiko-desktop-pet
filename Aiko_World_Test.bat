@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m tools.world_smoke %*
) else (
    py -m tools.world_smoke %*
)
pause
