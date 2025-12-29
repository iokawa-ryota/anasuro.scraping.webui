@echo off
REM スロット店舗スクレイピング Web UI - 起動スクリプト（タスクトレイ版）
REM このファイルを ダブルクリック して起動します
REM Flask サーバーはタスクトレイで実行され、最終的に隠れます

setlocal enabledelayedexpansion

cd /d "%~dp0"

REM VBS スクリプトでサーバーを非表示で起動
echo Creating temporary VBS script...
set "vbs_file=%temp%\flask_server_%random%.vbs"

(
    echo Set objShell = CreateObject("WScript.Shell"^)
    echo objShell.Run "python app.py", 0, False
) > "!vbs_file!"

REM VBS を実行（ウィンドウなしで）
cscript.exe "!vbs_file!" /B

REM サーバーの起動を待つ
timeout /t 3 /nobreak

REM ブラウザを開く
start http://localhost:5000

REM VBS ファイルをクリーンアップ
del "!vbs_file!"

echo.
echo ✓ サーバーが起動し、ブラウザを開きました
echo このウィンドウは自動で閉じます...
echo.

timeout /t 2 /nobreak
