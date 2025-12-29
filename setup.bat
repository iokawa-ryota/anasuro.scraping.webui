@echo off
REM セットアップスクリプト - 初回だけ実行
REM このファイルを初回に ダブルクリック して実行します

echo.
echo ====================================================
echo スロット店舗スクレイピング Web UI - セットアップ
echo ====================================================
echo.

REM Python が存在するか確認
python --version >nul 2>&1
if errorlevel 1 (
    echo エラー: Python がインストールされていないか、
    echo PATH が正しく設定されていません
    echo.
    pause
    exit /b 1
)

REM セットアップチェック実行
echo セットアップを確認中...
echo.
python setup_check.py

if errorlevel 1 (
    echo.
    echo セットアップが失敗しました
    echo.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo セットアップ完了！
echo ====================================================
echo.
echo 次回から以下のいずれかを実行してください：
echo.
echo   1. start.bat   - 通常起動（推奨）
echo   2. start_silent.bat - ウィンドウなし起動
echo.
echo ====================================================
echo.

pause
