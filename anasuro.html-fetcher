import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime

# HTML保存先
save_dir = r"D:\\Users\\Documents\\python\\saved_html\\SLOT ACT"
os.makedirs(save_dir, exist_ok=True)

# 保存済み日付一覧を取得
existing_files = set(f.replace(".html", "") for f in os.listdir(save_dir) if f.endswith(".html"))

# 広告閉じる処理
def try_close_ads(driver):
    close_patterns = [
        "//button[contains(text(), '閉じる')]",
        "//button[@aria-label='閉じる']",
        "//button[@aria-label='Close']",
        "//*[@class='google-close-button']",
        "//*[@role='button' and contains(., '閉じる')]",
        "//*[contains(@class,'close')]",
        "//div[@aria-label='広告を閉じる']",
    ]
    for xpath in close_patterns:
        try:
            close_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            print(f"広告閉じるボタンを検出: {xpath}")
            close_btn.click()
            time.sleep(1)
            return True
        except:
            continue
    print("閉じる広告ボタンは検出されませんでした。")
    return False

# HTML保存
def save_html(driver, date_str):
    filename = os.path.join(save_dir, f"{date_str}.html")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"HTMLを保存しました: {filename}")

# Chrome起動
options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")
driver = uc.Chrome(options=options)

try:
    list_url = "https://ana-slo.com/%e3%83%9b%e3%83%bc%e3%83%ab%e3%83%87%e3%83%bc%e3%82%bf/%e7%a5%9e%e5%a5%88%e5%b7%9d%e7%9c%8c/slot-act-%e3%83%87%e3%83%bc%e3%82%bf%e4%b8%80%e8%a6%a7/"
    driver.get(list_url)
    print("一覧ページにアクセスしました")

    start_date_input = input("取得開始日を入力してください（例: 2025-03-04）: ")
    start_date = datetime.strptime(start_date_input, "%Y-%m-%d")

    date_rows = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.date-table .table-row"))
    )
    date_list = []
    for row in reversed(date_rows):
        try:
            a_tag = row.find_element(By.TAG_NAME, "a")
            date_text = a_tag.text.strip().split("(")[0].replace("/", "-")
            date_obj = datetime.strptime(date_text, "%Y-%m-%d")
            if date_obj >= start_date and date_text not in existing_files:
                date_list.append(date_text)
        except:
            continue

    print(f"対象日数: {len(date_list)} 件")

    for date_str in date_list:
        print(f"日付 {date_str} にアクセスします")

        date_rows = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.date-table .table-row"))
        )
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
            print(f"{date_str} のリンクが見つかりませんでした。")
            continue

        driver.execute_script("arguments[0].scrollIntoView(true);", link_element)
        ActionChains(driver).move_to_element(link_element).pause(0.5).click().perform()

        try_close_ads(driver)

        WebDriverWait(driver, 10).until(lambda d: "-data" in d.current_url)
        print("遷移成功：", driver.current_url)

        save_html(driver, date_str)

        driver.get(list_url)

finally:
    driver.quit()
    print("ブラウザを閉じました。")
