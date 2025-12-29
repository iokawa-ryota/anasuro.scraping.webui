@echo off
REM スロット店舗スクレイピング Web UI - 起動スクリプト
REM このファイルを ダブルクリック して起動します

echo.
echo ====================================================
echo  スロット店舗スクレイピング Web UI
echo ====================================================
echo.
echo Flask サーバーを起動中...
echo.

REM Flask サーバーをバックグラウンドで起動（最小化）
start "Flask Server - スロット店舗スクレイピング" /min python app.py

REM サーバーの起動を待つ
timeout /t 3 /nobreak

REM ブラウザを自動で開く
start http://localhost:5000

echo ✓ サーバーが起動し、ブラウザを開きました
echo.
echo このウィンドウは自動で閉じます...
timeout /t 3 /nobreak
exit
