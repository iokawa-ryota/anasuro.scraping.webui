@echo off
echo =============================================
echo anaslot setup
echo =============================================

cd /d %~dp0

set "PYTHON_CMD="

python --version >nul 2>&1
if not errorlevel 1 (
  set "PYTHON_CMD=python"
) else (
  py -3 --version >nul 2>&1
  if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
  )
)

if not defined PYTHON_CMD (
  echo Python が見つかりません。winget で自動インストールを試みます...
  where winget >nul 2>&1
  if errorlevel 1 (
    echo winget が利用できません。手動で Python をインストールしてください。
    echo https://www.python.org/downloads/windows/
    start "" https://www.python.org/downloads/windows/
    pause
    exit /b 1
  )

  winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
  if errorlevel 1 (
    echo Python の自動インストールに失敗しました。手動でインストールしてください。
    echo https://www.python.org/downloads/windows/
    start "" https://www.python.org/downloads/windows/
    pause
    exit /b 1
  )

  python --version >nul 2>&1
  if not errorlevel 1 (
    set "PYTHON_CMD=python"
  ) else (
    py -3 --version >nul 2>&1
    if not errorlevel 1 (
      set "PYTHON_CMD=py -3"
    )
  )
)

if not defined PYTHON_CMD (
  echo Python のインストールは完了しましたが、この画面では認識できませんでした。
  echo setup.bat をもう一度実行してください。
  pause
  exit /b 1
)

call %PYTHON_CMD% _internal\bin\setup_check.py
if errorlevel 1 (
  echo Setup check failed.
  pause
  exit /b 1
)

echo.
echo Setup complete. Run start.bat to launch.
echo.
pause
