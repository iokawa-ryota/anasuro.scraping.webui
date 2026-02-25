@echo off
cd /d %~dp0

python apps\_internal\bin\build_distribution.py --zip
if errorlevel 1 (
  echo Distribution build failed.
  exit /b 1
)

echo Distribution build complete.
