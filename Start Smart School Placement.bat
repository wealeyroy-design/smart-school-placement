@echo off
REM One-click launcher: starts the API and the web app, then opens the app in your browser.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\launch.ps1"
echo.
echo You can close this window. The servers keep running in their own minimised windows.
pause
