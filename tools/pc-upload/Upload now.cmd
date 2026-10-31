@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0upload.ps1" -Once
schtasks /Run /TN "Valve Finder upload" >nul 2>&1
echo.
echo   Done. See Upload log.txt for what was added. It keeps watching the folder from now on.
pause
