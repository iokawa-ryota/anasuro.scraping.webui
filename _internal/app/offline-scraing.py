import os
import re
import json

import pandas as pd
from bs4 import BeautifulSoup

try:
    from tqdm.notebook import tqdm
except ImportError:
    from tqdm import tqdm

APP_DIR = os.path.dirname(os.path.abspath(__file__))
INTERNAL_ROOT = os.path.dirname(APP_DIR)
PROJECT_ROOT = os.path.dirname(INTERNAL_ROOT)
RUNTIME_DIR = os.path.join(INTERNAL_ROOT, "runtime")
DEFAULT_STORE_LIST_PATH = os.path.join(PROJECT_ROOT, "store_list.csv")
EXCEL_OUTPUT_DIR = os.getenv("EXCEL_OUTPUT_DIR", os.path.join(PROJECT_ROOT, "output", "machine-excel"))
COMPLETED_STORES_PATH = os.getenv("COMPLETED_STORES_PATH", os.path.join(RUNTIME_DIR, "completed_stores.json"))

if not os.path.exists(DEFAULT_STORE_LIST_PATH):
    raise FileNotFoundError(f"store_list.csv が見つかりません: {DEFAULT_STORE_LIST_PATH}")

df = pd.read_csv(DEFAULT_STORE_LIST_PATH, encoding='utf-8-sig')
df = df.drop_duplicates(subset=["data_directory", "store_name"])

processed_outputs = set()
completed_stores = []
processed_stores = []

os.makedirs(EXCEL_OUTPUT_DIR, exist_ok=True)
os.makedirs(RUNTIME_DIR, exist_ok=True)

for i, (_, row) in enumerate(df.iterrows()):
    if i > 0:
        print("\n")

    html_dir = row["data_directory"]
    store_name = row["store_name"]

    safe_store_name = re.sub(r'[\\/*?:"<>|]', "", store_name)
    output_path = os.path.join(EXCEL_OUTPUT_DIR, f"{safe_store_name}-slotdata.csv")

    if output_path in processed_outputs:
        continue
    processed_outputs.add(output_path)

    all_data = []

    latest_day = None
    existing_days = set()
    if os.path.exists(output_path):
        try:
            existing_df = pd.read_csv(output_path)
            if "day" in existing_df.columns:
                existing_df["day"] = pd.to_datetime(existing_df["day"], errors="coerce")
                existing_days = set(existing_df["day"].dt.strftime("%Y-%m-%d").dropna())
                latest_day = existing_df["day"].max()
            else:
                existing_df = pd.DataFrame()
                latest_day = None
                existing_days = set()
        except Exception:
            existing_df = pd.DataFrame()
    else:
        existing_df = pd.DataFrame()

    if not os.path.isdir(html_dir):
        processed_stores.append(store_name)
        continue

    html_files = [
        f for f in os.listdir(html_dir)
        if f.endswith(".html") and re.search(r"\d{4}-\d{2}-\d{2}", f)
    ]
    file_day_map = {f: re.search(r"\d{4}-\d{2}-\d{2}", f).group(0) for f in html_files}
    new_files = [f for f, day in file_day_map.items() if day not in existing_days and (not latest_day or pd.to_datetime(day) > latest_day)]
    new_files.sort()

    for file in tqdm(new_files, desc=store_name[:20], unit="file"):
        day = file_day_map[file]

        file_path = os.path.join(html_dir, file)
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "lxml")

        table = soup.find("table", {"id": "all_data_table"})
        if not table:
            continue

        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 6:
                continue

            dai_name = cols[0].get_text(strip=True)
            dai_num = cols[1].get_text(strip=True).replace(",", "")
            game = cols[2].get_text(strip=True).replace(",", "")
            diff = cols[3].get_text(strip=True).replace(",", "").replace("+", "")
            bb = cols[4].get_text(strip=True)
            rb = cols[5].get_text(strip=True)

            try:
                game_int = int(game)
            except Exception:
                game_int = 0
            try:
                bb_int = int(bb)
            except Exception:
                bb_int = 0
            try:
                rb_int = int(rb)
            except Exception:
                rb_int = 0
            try:
                diff_int = int(diff)
            except Exception:
                diff_int = 0

            total = round(game_int / (bb_int + rb_int), 1) if (bb_int + rb_int) else 0
            big_per = round(game_int / bb_int, 1) if bb_int else 0
            reg_per = round(game_int / rb_int, 1) if rb_int else 0

            all_data.append({
                "day": day,
                "dai_name": dai_name,
                "dai_num": int(dai_num) if dai_num.isdigit() else 0,
                "game": game_int,
                "difference": diff_int,
                "bb": bb_int,
                "rb": rb_int,
                "Total": total,
                "big_per": big_per,
                "reg_per": reg_per,
            })

    if all_data:
        df_result = pd.DataFrame(all_data)

        if not existing_df.empty:
            df_result = pd.concat([existing_df, df_result], ignore_index=True)
            if "day" in df_result.columns:
                df_result["day"] = pd.to_datetime(df_result["day"], errors="coerce")
            df_result = df_result.drop_duplicates(subset=["day", "dai_name", "dai_num"], keep="last").reset_index(drop=True)
        else:
            if "day" in df_result.columns:
                df_result["day"] = pd.to_datetime(df_result["day"], errors="coerce")

        if "day" in df_result.columns:
            df_result["day"] = df_result["day"].dt.strftime("%Y-%m-%d")

        df_result.to_csv(output_path, index=False, encoding="utf-8-sig")
        completed_stores.append(store_name)

    processed_stores.append(store_name)

with open(COMPLETED_STORES_PATH, "w", encoding="utf-8") as f:
    json.dump({"completed": completed_stores, "processed": processed_stores}, f, ensure_ascii=False, indent=2)

