@echo off
echo =============================================
echo anaslot setup
echo =============================================

cd /d %~dp0

python --version >nul 2>&1
if errorlevel 1 (
  echo Python is not available in PATH.
  pause
  exit /b 1
)

python _internal\bin\setup_check.py
if errorlevel 1 (
  echo Setup check failed.
  pause
  exit /b 1
)

echo.
echo Setup complete. Run start.bat to launch.
echo.
pause
