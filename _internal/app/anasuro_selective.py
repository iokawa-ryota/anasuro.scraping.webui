"""
選択された店舗のみをスクレイピングするスクリプト
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
import threading
from selenium.common.exceptions import TimeoutException, WebDriverException

APP_DIR = os.path.dirname(os.path.abspath(__file__))
INTERNAL_ROOT = os.path.dirname(APP_DIR)
PROJECT_ROOT = os.path.dirname(INTERNAL_ROOT)
RUNTIME_DIR = os.path.join(INTERNAL_ROOT, "runtime")
os.makedirs(RUNTIME_DIR, exist_ok=True)

DEFAULT_STORE_LIST_PATH = os.path.join(PROJECT_ROOT, "store_list.csv")
DEFAULT_TEMP_STORE_LIST_PATH = os.getenv("TEMP_STORE_LIST_PATH", os.path.join(RUNTIME_DIR, "temp_store_list.csv"))
CHROME_VERSION_MAIN = int(os.getenv("CHROME_VERSION_MAIN", "144"))
SCRAPE_IDLE_TIMEOUT_SECONDS = int(os.getenv("SCRAPE_IDLE_TIMEOUT_SECONDS", "120"))
SCRAPE_PAGELOAD_TIMEOUT_SECONDS = int(os.getenv("SCRAPE_PAGELOAD_TIMEOUT_SECONDS", "110"))


def save_html(driver, date_str, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    filename = os.path.join(save_dir, f"{date_str}.html")
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.find("table", {"id": "all_data_table"})
    if table:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(str(table))
        print(f"[保存] 表データ保存完了: {filename}")


def detect_cloudflare(driver):
    page = driver.page_source
    return (
        "人間であることを確認" in page
        or "Please stand by, while we are checking your browser" in page
        or "Checking if the site connection is secure" in page
        or "hcaptcha-box" in page
    )


def wait_for_cloudflare_clear(driver, timeout=300, poll_interval=2):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not detect_cloudflare(driver):
            return True
        time.sleep(poll_interval)
    return False


def handle_vignette(driver, link_element):
    if "#google_vignette" in driver.current_url:
        driver.back()
        driver.execute_script("arguments[0].scrollIntoView(true);", link_element)
        ActionChains(driver).move_to_element(link_element).pause(0.5).click().perform()


def read_csv_with_fallback(path):
    for enc in ("utf-8", "utf-8-sig", "cp932"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    raise RuntimeError(f"CSV の読み込みに失敗: {path}")


def load_stores(source):
    store_list_path = DEFAULT_STORE_LIST_PATH if source == "csv" else DEFAULT_TEMP_STORE_LIST_PATH
    if not os.path.exists(store_list_path):
        return pd.DataFrame()
    try:
        return read_csv_with_fallback(store_list_path)
    except Exception:
        return pd.DataFrame()


def main():
    parser = argparse.ArgumentParser(description='選択された店舗のみをスクレイピング')
    parser.add_argument('--file', type=str, help='店舗リスト CSV ファイルを指定')
    parser.add_argument('--use-temp', action='store_true', help='runtime/temp_store_list.csv を使用')
    parser.add_argument('--max-stores', type=int, default=0, help='処理する店舗数上限（0は無制限）')
    parser.add_argument('--max-days-per-store', type=int, default=0, help='1店舗あたり処理日数上限（0は無制限）')
    parser.add_argument('stores', nargs='*', help='店舗名（複数可）')
    args = parser.parse_args()

    if args.file:
        try:
            df = read_csv_with_fallback(args.file)
        except Exception:
            print("[エラー] 指定ファイルの読み込みに失敗しました")
            return
    elif args.use_temp:
        df = load_stores("temp")
    else:
        df = load_stores("temp") if os.path.exists(DEFAULT_TEMP_STORE_LIST_PATH) else load_stores("csv")

    if df.empty:
        print("[エラー] 店舗リストが空です")
        return

    if args.max_stores and args.max_stores > 0:
        df = df.head(args.max_stores)
        print(f"[テスト] 店舗数を {args.max_stores} 件に制限して実行します")

    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    driver = uc.Chrome(options=options, version_main=CHROME_VERSION_MAIN)
    driver.set_page_load_timeout(SCRAPE_PAGELOAD_TIMEOUT_SECONDS)

    activity = {"last_transition": time.time(), "label": "初期化"}
    watchdog_stop = threading.Event()
    watchdog_triggered = threading.Event()

    def touch_transition(label):
        activity["last_transition"] = time.time()
        activity["label"] = label

    def safe_get(url, label):
        try:
            driver.get(url)
            touch_transition(label)
        except TimeoutException as e:
            raise RuntimeError(f"ページ遷移タイムアウト: {label} ({SCRAPE_PAGELOAD_TIMEOUT_SECONDS}秒)") from e
        except WebDriverException as e:
            raise RuntimeError(f"ページ遷移失敗: {label}: {e}") from e

    def watchdog_loop():
        while not watchdog_stop.wait(5):
            idle = time.time() - activity["last_transition"]
            if idle >= SCRAPE_IDLE_TIMEOUT_SECONDS:
                watchdog_triggered.set()
                print(
                    f"[エラー] ページ遷移が{SCRAPE_IDLE_TIMEOUT_SECONDS}秒以上停止: {activity['label']}",
                    flush=True,
                )
                with contextlib.suppress(Exception):
                    driver.quit()
                return

    watchdog_thread = threading.Thread(target=watchdog_loop, daemon=True)
    watchdog_thread.start()

    adblock_script = """
        document.querySelectorAll('iframe, ins, [class*="ad"], [id*="ad"], #overlay_ads_area').forEach(el => el.remove());
    """

    total_stores = len(df)

    try:
        for store_no, (_, row) in enumerate(df.iterrows(), start=1):
            list_url = row.get("store_url") or row.get("url")
            save_dir = row.get("data_directory") or row.get("directory")
            store_name = row.get("store_name") or row.get("name") or f"店舗{store_no}"

            # 店舗単位の進捗を WebUI に通知（開始時）
            print(f"__PROGRESS__ store {store_no - 1}/{total_stores}", flush=True)
            print(f"__PROGRESS__ store_start {store_no}/{total_stores} {store_name}", flush=True)

            if not list_url or not save_dir:
                continue

            os.makedirs(save_dir, exist_ok=True)
            existing_files = set(f.replace(".html", "") for f in os.listdir(save_dir) if f.endswith(".html"))

            try:
                safe_get(list_url, f"{store_name}: 一覧ページ")
                if detect_cloudflare(driver):
                    if sys.stdin and sys.stdin.isatty():
                        input("[入力待ち] 認証通過後に Enter を押してください。")
                    else:
                        wait_for_cloudflare_clear(driver, timeout=300)

                driver.execute_script(adblock_script)
                date_rows = driver.find_elements(By.CSS_SELECTOR, "div.date-table .table-row")

                date_list = []
                for row_elem in reversed(date_rows):
                    try:
                        a_tag = row_elem.find_element(By.TAG_NAME, "a")
                        date_text = a_tag.text.strip().split("(")[0].replace("/", "-")
                        datetime.strptime(date_text, "%Y-%m-%d")
                        if date_text not in existing_files:
                            date_list.append(date_text)
                    except Exception:
                        continue

                if args.max_days_per_store and args.max_days_per_store > 0:
                    date_list = sorted(date_list)[-args.max_days_per_store:]
                    print(f"[テスト] {store_name}: 最新 {len(date_list)} 日分のみ処理")

                total_dates = max(1, len(date_list))
                for date_idx, date_str in enumerate(date_list, start=1):
                    while True:
                        date_rows = driver.find_elements(By.CSS_SELECTOR, "div.date-table .table-row")
                        link_element = None
                        for row_elem in reversed(date_rows):
                            try:
                                a_tag = row_elem.find_element(By.TAG_NAME, "a")
                                if a_tag.text.strip().startswith(date_str.replace("-", "/")):
                                    link_element = a_tag
                                    break
                            except Exception:
                                continue
                        if not link_element:
                            break

                        try:
                            driver.execute_script("arguments[0].scrollIntoView(true);", link_element)
                            ActionChains(driver).move_to_element(link_element).pause(0.5).click().perform()
                            touch_transition(f"{store_name}: {date_str} 詳細ページ")
                            handle_vignette(driver, link_element)
                            driver.execute_script(adblock_script)

                            time.sleep(2)
                            soup_check = BeautifulSoup(driver.page_source, "html.parser")
                            table_check = soup_check.find("table", {"id": "all_data_table"})
                            if table_check:
                                save_html(driver, date_str, save_dir)
                                break

                            if detect_cloudflare(driver):
                                time.sleep(7)
                                soup_check = BeautifulSoup(driver.page_source, "html.parser")
                                table_check = soup_check.find("table", {"id": "all_data_table"})
                                if table_check:
                                    time.sleep(2)
                                    save_html(driver, date_str, save_dir)
                                break
                            break
                        except Exception:
                            if watchdog_triggered.is_set():
                                raise RuntimeError("ページ遷移停止を検知したため処理を中断しました")
                            break

                    safe_get(list_url, f"{store_name}: 一覧ページ復帰")
                    driver.execute_script(adblock_script)

                    # 日付単位の進捗（店舗内）を WebUI に通知
                    pct = int((((store_no - 1) + (date_idx / total_dates)) / max(1, total_stores)) * 100)
                    print(f"__PROGRESS__ pct {min(99, max(0, pct))} {store_name} {date_idx}/{len(date_list)}日", flush=True)

            except Exception as e:
                if watchdog_triggered.is_set():
                    raise RuntimeError("ページ遷移停止を検知したため処理を中断しました") from e
                print(f"[エラー] 店舗処理失敗: {store_name}")
                # 失敗時も次店舗へ進むため進捗は進める
                print(f"__PROGRESS__ store {store_no}/{total_stores}", flush=True)
                continue

            # 店舗単位の進捗を WebUI に通知（完了時）
            print(f"__PROGRESS__ store {store_no}/{total_stores}", flush=True)

    finally:
        watchdog_stop.set()
        with contextlib.suppress(Exception):
            driver.quit()
        del driver
        gc.collect()


if __name__ == '__main__':
    main()

