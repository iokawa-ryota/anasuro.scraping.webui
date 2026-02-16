@echo off
cd /d %~dp0
set "APP_URL=http://127.0.0.1:5000"

start "Flask Server" cmd /k "cd /d %~dp0 && python _internal\app\app.py"
timeout /t 2 /nobreak >nul
start "" chrome "%APP_URL%"
