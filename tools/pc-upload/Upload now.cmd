@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0upload.ps1" -Once
echo.
echo   Done. See Upload log.txt for what was added.
pause
