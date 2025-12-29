#!/bin/bash

# スロット店舗スクレイピング Web UI - 起動スクリプト (Linux/Mac)

echo ""
echo "===================================================="
echo " スロット店舗スクレイピング Web UI"
echo "===================================================="
echo ""

# Python が存在するか確認
if ! command -v python3 &> /dev/null; then
    echo "エラー: Python3 がインストールされていないか、"
    echo "PATH が正しく設定されていません"
    echo ""
    read -p "Enterキーを押して終了..." dummy
    exit 1
fi

# セットアップチェック
echo "1. セットアップチェック中..."
python3 setup_check.py
if [ $? -ne 0 ]; then
    echo ""
    echo "エラー: セットアップが失敗しました"
    read -p "Enterキーを押して終了..." dummy
    exit 1
fi

echo ""
echo "2. Flask サーバーを起動中..."
echo ""
echo "===================================================="
echo " サーバーが起動しました"
echo "===================================================="
echo ""
echo "ブラウザで以下の URL にアクセスしてください:"
echo "  http://localhost:5000"
echo ""
echo "サーバーを停止するには Ctrl+C を押してください"
echo ""
echo "===================================================="
echo ""

# Flask サーバーを起動
python3 app.py
