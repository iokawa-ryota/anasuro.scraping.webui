from bs4 import BeautifulSoup
import pandas as pd
import os
import re
from tqdm.notebook import tqdm

# 店舗一覧Excelの読み込み
store_list_path = "D:/Users/Documents/python/saved_html/store_list.xlsx"
df = pd.read_excel(store_list_path)

# 各店舗ディレクトリを順に処理
for _, row in df.iterrows():
    html_dir = row["data_directory"]
    output_path = os.path.join(html_dir, "output.xlsx")

    all_data = []

    # 既存Excelがある場合は最終日付を取得
    latest_day = None
    if os.path.exists(output_path):
        try:
            existing_df = pd.read_excel(output_path)
            existing_df["day"] = pd.to_datetime(existing_df["day"], errors='coerce')
            latest_day = existing_df["day"].max()
            print(f"📄 既存データあり: {output_path}（最新日: {latest_day.date()}）")
        except:
            print(f"⚠️ 既存Excelの読み込みに失敗しました: {output_path}")

    html_files = sorted([f for f in os.listdir(html_dir) if f.endswith(".html")])

    for file in tqdm(html_files, desc=f"{os.path.basename(html_dir)} 処理中", unit="file"):
        match = re.search(r"\d{4}-\d{2}-\d{2}", file)
        if not match:
            continue
        day = match.group(0)

        # 日付が最新日以下ならスキップ
        if latest_day and pd.to_datetime(day) <= latest_day:
            continue

        file_path = os.path.join(html_dir, file)
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "lxml")

        table = soup.find("table", {"id": "all_data_table"})
        if not table:
            continue

        rows = table.find_all("tr")[1:]  # ヘッダーをスキップ
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
            except:
                game_int = 0
            try:
                bb_int = int(bb)
            except:
                bb_int = 0
            try:
                rb_int = int(rb)
            except:
                rb_int = 0
            try:
                diff_int = int(diff)
            except:
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
                "reg_per": reg_per
            })

    if all_data:
        df_result = pd.DataFrame(all_data)

        # 既存データがあれば追記
        if latest_day:
            df_result = pd.concat([existing_df, df_result], ignore_index=True)

        df_result.to_excel(output_path, index=False)
        print(f"✅ 保存完了: {output_path}")
    else:
        print(f"⚠️ 新しいデータはありません: {html_dir}")
