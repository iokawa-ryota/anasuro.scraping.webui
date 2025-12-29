"""
選択された店舗のみをスクレイピングするスクリプト

使い方:
  python anasuro_selective.py <店舗名1> <店舗名2> ...
  または
  python anasuro_selective.py --file temp_store_list.csv

このスクリプトは、app.py（Flask バックエンド）から呼び出されます。
選択された店舗のみに対して処理を行います。
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import os
from datetime import datetime
from bs4 import BeautifulSoup
import time
import contextlib
import gc
import sys
import argparse
from pathlib import Path

# HTMLを保存（表データのみ）
def save_html(driver, date_str, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    filename = os.path.join(save_dir, f"{date_str}.html")
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.find("table", {"id": "all_data_table"})
    if table:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(str(table))
        print(f"[保存] 表データ保存完了: {filename}")
    else:
        print(f"[警告] 表データが見つかりませんでした（日付: {date_str}）")

# Cloudflare検知
cloudflare_count = 0
MAX_CLOUDFLARE_RETRY = 2

def detect_cloudflare(driver):
    page = driver.page_source
    return (
        "人間であることを確認" in page or
        "Please stand by, while we are checking your browser" in page or
        "Checking if the site connection is secure" in page or
        "hcaptcha-box" in page
    )

def handle_vignette(driver, link_element):
    if "#google_vignette" in driver.current_url:
        print("[広告] #google_vignette 遷移検知 → 戻って再試行")
        driver.back()
        driver.execute_script("arguments[0].scrollIntoView(true);", link_element)
        ActionChains(driver).move_to_element(link_element).pause(0.5).click().perform()

def load_stores(source):
    """
    店舗リストを読み込む
    source: "csv" (元の store_list.csv) または "file" (temp_store_list.csv)
    """
    if source == "csv":
        store_list_path = "D:/Users/Documents/python/saved_html/store_list.csv"
    else:
        store_list_path = "temp_store_list.csv"

    if not os.path.exists(store_list_path):
        print(f"[エラー] ファイルが見つかりません: {store_list_path}")
        return pd.DataFrame()

    try:
        df = None
        for enc in ("utf-8", "utf-8-sig", "cp932"):
            try:
                df = pd.read_csv(store_list_path, encoding=enc)
                break
            except Exception:
                continue
        if df is None:
            raise RuntimeError("店舗CSVの読み込みに失敗（encoding不一致）")
        print(f"[情報] {len(df)} 個の店舗を読み込みました")
        return df
    except Exception as e:
        print(f"[エラー] ファイル読み込み失敗: {e}")
        return pd.DataFrame()

def filter_stores(df, selected_names):
    """
    指定された店舗名でフィルタリング
    """
    if not selected_names:
        return df
    
    # 店舗名カラムを探す（複数のカラム名に対応）
    name_columns = [col for col in df.columns if 'name' in col.lower() or 'store' in col.lower()]
    
    if not name_columns:
        print("[警告] 店舗名カラムが見つかりません")
        return df
    
    # 最初のマッチカラムを使用
    name_column = name_columns[0]
    filtered_df = df[df[name_column].isin(selected_names)]
    
    print(f"[情報] {len(filtered_df)} 個の店舗をフィルタリングしました")
    return filtered_df

def main():
    # コマンドライン引数を処理
    parser = argparse.ArgumentParser(description='選択された店舗のみをスクレイピング')
    parser.add_argument('--file', type=str, help='店舗リスト Excel ファイルを指定')
    parser.add_argument('--use-temp', action='store_true', help='temp_store_list.csv を使用')
    parser.add_argument('stores', nargs='*', help='店舗名（複数可）')
    
    args = parser.parse_args()
    
    # 店舗リストの読み込み
    if args.file:
        print(f"[情報] ファイルを指定: {args.file}")
        df = None
        for enc in ("utf-8", "utf-8-sig", "cp932"):
            try:
                df = pd.read_csv(args.file, encoding=enc)
                break
            except Exception:
                continue
        if df is None:
            print("[エラー] 指定ファイルの読み込みに失敗しました")
            return
    elif args.use_temp:
        print("[情報] temp_store_list.csv を使用します")
        df = load_stores("temp")
    else:
        # デフォルト: temp_store_list.csv を確認、なければ store_list.csv を使用
        if os.path.exists("temp_store_list.csv"):
            print("[情報] temp_store_list.csv が見つかりました")
            df = load_stores("temp")
        else:
            print("[情報] 元の store_list.csv を使用します")
            df = load_stores("csv")
    
    if df.empty:
        print("[エラー] 店舗リストが空です")
        return
    
    # Chrome起動
    print("[準備] Chrome ドライバーを初期化中...")
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    
    driver = uc.Chrome(options=options)
    
    # 広告除去スクリプト（強化版）
    adblock_script = """
        document.querySelectorAll('iframe, ins, [class*="ad"], [id*="ad"], #overlay_ads_area').forEach(el => el.remove());
    """
    
    processed_count = 0
    success_count = 0
    
    try:
        print(f"\n[開始] {len(df)} 個の店舗を処理します")
        print("=" * 60)
        
        for index, row in df.iterrows():
            list_url = row.get("store_url") or row.get("url")
            save_dir = row.get("data_directory") or row.get("directory")
            store_name = row.get("store_name") or row.get("name") or f"店舗{index}"
            
            if not list_url or not save_dir:
                print(f"[スキップ] 店舗 {store_name}: URL or ディレクトリが不足")
                continue
            
            processed_count += 1
            print(f"\n[{processed_count}/{len(df)}] 店舗: {store_name}")
            print(f"  URL: {list_url}")
            
            os.makedirs(save_dir, exist_ok=True)
            existing_files = set(f.replace(".html", "") for f in os.listdir(save_dir) if f.endswith(".html"))
            
            try:
                driver.get(list_url)
                
                if detect_cloudflare(driver):
                    print(f"[警告] Cloudflare 認証検知")
                    input("[入力待ち] 認証を手動で通過してください。完了後 Enter キーを押してください。")
                
                driver.execute_script(adblock_script)
                print("[状態] 一覧ページにアクセス完了")
                
                date_rows = driver.find_elements(By.CSS_SELECTOR, "div.date-table .table-row")
                
                date_list = []
                for row_elem in reversed(date_rows):
                    try:
                        a_tag = row_elem.find_element(By.TAG_NAME, "a")
                        date_text = a_tag.text.strip().split("(")[0].replace("/", "-")
                        datetime.strptime(date_text, "%Y-%m-%d")
                        if date_text not in existing_files:
                            date_list.append(date_text)
                    except:
                        continue
                
                print(f"  新規データ日数: {len(date_list)} 件")
                
                for date_str in date_list:
                    while True:
                        print(f"  処理中: 日付 {date_str}")
                        date_rows = driver.find_elements(By.CSS_SELECTOR, "div.date-table .table-row")
                        link_element = None
                        
                        for row_elem in reversed(date_rows):
                            try:
                                a_tag = row_elem.find_element(By.TAG_NAME, "a")
                                if a_tag.text.strip().startswith(date_str.replace("-", "/")):
                                    link_element = a_tag
                                    break
                            except:
                                continue
                        
                        if not link_element:
                            print(f"  警告: リンクが見つかりません")
                            break
                        
                        try:
                            driver.execute_script("arguments[0].scrollIntoView(true);", link_element)
                            ActionChains(driver).move_to_element(link_element).pause(0.5).click().perform()
                            handle_vignette(driver, link_element)
                            driver.execute_script(adblock_script)
                            
                            time.sleep(2)
                            soup_check = BeautifulSoup(driver.page_source, "html.parser")
                            table_check = soup_check.find("table", {"id": "all_data_table"})
                            
                            if table_check:
                                print(f"  保存: {date_str}")
                                save_html(driver, date_str, save_dir)
                                success_count += 1
                                break
                            
                            if detect_cloudflare(driver):
                                print(f"  認証待機中...")
                                time.sleep(7)
                                soup_check = BeautifulSoup(driver.page_source, "html.parser")
                                table_check = soup_check.find("table", {"id": "all_data_table"})
                                if table_check:
                                    print(f"  保存: {date_str}")
                                    time.sleep(2)
                                    save_html(driver, date_str, save_dir)
                                    success_count += 1
                                break
                            
                            print(f"  エラー: ページ遷移に失敗")
                            break
                        
                        except Exception as e:
                            print(f"  エラー: {e}")
                            break
                    
                    driver.get(list_url)
                    driver.execute_script(adblock_script)
            
            except Exception as e:
                print(f"[エラー] 店舗 {store_name} の処理中にエラー: {e}")
                continue
        
        print("\n" + "=" * 60)
        print(f"[完了] 処理完了")
        print(f"  処理店舗数: {processed_count}")
        print(f"  成功数: {success_count}")
        
    finally:
        with contextlib.suppress(Exception):
            driver.quit()
        del driver
        gc.collect()
        print("[状態] ブラウザを閉じました")

if __name__ == '__main__':
    main()
