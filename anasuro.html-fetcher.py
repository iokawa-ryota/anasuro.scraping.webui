import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os
from datetime import datetime
from bs4 import BeautifulSoup
import time

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
        time.sleep(1)
        driver.execute_script("arguments[0].scrollIntoView(true);", link_element)
        ActionChains(driver).move_to_element(link_element).pause(0.5).click().perform()
        #time.sleep(2)

# Chrome起動
options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")

driver = uc.Chrome(options=options)

# 広告除去スクリプト（強化版）
adblock_script = """
    document.querySelectorAll('iframe, ins, [class*="ad"], [id*="ad"], #overlay_ads_area').forEach(el => el.remove());
"""

try:
    for index, row in pd.read_excel("D:/Users/Documents/python/saved_html/store_list.xlsx").iterrows():
        list_url = row["store_url"]
        save_dir = row["data_directory"]
        print(f"\n[開始] 店舗URL: {list_url}")

        os.makedirs(save_dir, exist_ok=True)
        existing_files = set(f.replace(".html", "") for f in os.listdir(save_dir) if f.endswith(".html"))

        driver.get(list_url)
        #time.sleep(2)

        if detect_cloudflare(driver):
            cloudflare_count += 1
            print(f"[警告] Cloudflare認証検知（{cloudflare_count}回目）")

            if cloudflare_count >= MAX_CLOUDFLARE_RETRY:
                input("[入力待ち] 認証を手動で通過してください。完了後Enterキーを押してください。")
                cloudflare_count = 0
            else:
                print("[巻き戻し] 日付一覧から再試行します")
                driver.get(list_url)
                #time.sleep(2)
                driver.execute_script(adblock_script)
                continue

        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.date-table .table-row")))
        driver.execute_script(adblock_script)
        print("[状態] 一覧ページにアクセス完了")

        date_rows = driver.find_elements(By.CSS_SELECTOR, "div.date-table .table-row")

        date_list = []
        for row in reversed(date_rows):
            try:
                a_tag = row.find_element(By.TAG_NAME, "a")
                date_text = a_tag.text.strip().split("(")[0].replace("/", "-")
                datetime.strptime(date_text, "%Y-%m-%d")
                if date_text not in existing_files:
                    date_list.append(date_text)
            except:
                continue

        print(f"[対象] 新規データ日数: {len(date_list)} 件")

        for date_str in date_list:
            retry_flag = False
            while True:
                print(f"[処理] 日付 {date_str} にアクセス中...")
                date_rows = driver.find_elements(By.CSS_SELECTOR, "div.date-table .table-row")
                link_element = None
                for row in reversed(date_rows):
                    try:
                        a_tag = row.find_element(By.TAG_NAME, "a")
                        if a_tag.text.strip().startswith(date_str.replace("-", "/")):
                            link_element = a_tag
                            break
                    except:
                        continue

                if not link_element:
                    print(f"[警告] リンクが見つかりません（日付: {date_str}）")
                    break

                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", link_element)
                    ActionChains(driver).move_to_element(link_element).pause(0.5).click().perform()
                    #time.sleep(2)
                    handle_vignette(driver, link_element)
                    #WebDriverWait(driver, 10).until(lambda d: "-data" in d.current_url)
                    driver.execute_script(adblock_script)

                    if detect_cloudflare(driver):
                        cloudflare_count += 1
                        print(f"[警告] Cloudflare認証検知（{cloudflare_count}回目）")
                        if cloudflare_count >= MAX_CLOUDFLARE_RETRY:
                            input("[入力待ち] 認証を手動で通過してください。完了後Enterキーを押してください。")
                            cloudflare_count = 0

                            # ✅ Cloudflare突破後にすでにページ表示されてる → 保存
                            print("[情報] Cloudflare認証通過後のページを保存します")
                            save_html(driver, date_str, save_dir)

                            break  # この日付の処理は完了、次へ
                        else:
                            print("[巻き戻し] 日付一覧から再試行します")
                            driver.get(list_url)
                            #time.sleep(2)
                            driver.execute_script(adblock_script)
                            retry_flag = True
                            continue

                    print("[状態] ページ遷移成功")
                    save_html(driver, date_str, save_dir)
                    break

                except Exception as e:
                    print(f"[エラー] 日付 {date_str} の処理中にエラー: {e}")
                    break

            driver.get(list_url)
            #time.sleep(2)
            driver.execute_script(adblock_script)

finally:
    driver.quit()
    print("[完了] 全処理が完了し、ブラウザを閉じました。")
