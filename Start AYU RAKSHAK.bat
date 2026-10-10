@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python is required to run AYU RAKSHAK.
  echo Install Python from https://www.python.org/downloads/
  pause
  exit /b 1
)

start "AYU RAKSHAK API" /min python "%~dp0backend\demo_server.py"
start "AYU RAKSHAK Website" /min python "%~dp0frontend\spa_server.py"
timeout /t 2 /nobreak >nul
start "" "http://localhost:4174/login"
exit /b 0
