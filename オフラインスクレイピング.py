import os
import re

import pandas as pd
from bs4 import BeautifulSoup
from tqdm.notebook import tqdm

# 店舗一覧 CSV の読み込み（エンコーディング自動フォールバック）
store_list_path = "D:/Users/Documents/python/saved_html/store_list.csv"
_df = None
for _enc in ("utf-8", "utf-8-sig", "cp932"):
    try:
        _df = pd.read_csv(store_list_path, encoding=_enc)
        break
    except Exception:
        continue
if _df is None:
    raise RuntimeError("store_list.csv の読み込みに失敗しました（encoding不一致）")
df = _df
df = df.drop_duplicates(subset=["data_directory", "store_name"])  # 重複店舗を除外

# すでに出力済みのoutput_pathを記録して、同じファイルへの重複処理・重複ログを防ぐ
processed_outputs = set()

# 出力先ディレクトリ（全店舗共通）
excel_output_dir = r"G:\マイドライブ\machine-Excel"
os.makedirs(excel_output_dir, exist_ok=True)

# 各店舗ディレクトリを順に処理
for idx, row in df.iterrows():
    html_dir = row["data_directory"]
    store_name = row["store_name"]

    # ファイル名に使えない文字を削除
    safe_store_name = re.sub(r'[\\/*?:"<>|]', "", store_name)
    # 拡張子をcsvに変更
    output_path = os.path.join(excel_output_dir, f"{safe_store_name}-slotdata.csv")

    # すでに処理したoutput_pathならスキップ（重複処理・重複ログ防止）
    if output_path in processed_outputs:
        continue
    processed_outputs.add(output_path)

    all_data = []

    # 既存CSVがある場合は最終日付を取得
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
        except Exception as e:
            existing_df = pd.DataFrame()  # 読めなかった場合は空として扱う
    else:
        existing_df = pd.DataFrame()

    # HTMLファイルを並び替え取得
    # 1. 店舗ごとにHTMLファイルリストを最初にset化しておき、既存日付との集合演算で新規ファイルだけ抽出
    html_files = [
        f for f in os.listdir(html_dir)
        if f.endswith(".html") and re.search(r"\d{4}-\d{2}-\d{2}", f)
    ]
    # ファイル名から日付を抽出し、既存Excelの"day"と照合して新規ファイルのみ処理
    file_day_map = {f: re.search(r"\d{4}-\d{2}-\d{2}", f).group(0) for f in html_files}
    new_files = [f for f, day in file_day_map.items() if day not in existing_days and (not latest_day or pd.to_datetime(day) > latest_day)]
    new_files.sort()
    for file in tqdm(new_files, desc=store_name[:20], unit="file"):
        day = file_day_map[file]
        # 日付が最新日以下ならスキップ
        if latest_day and pd.to_datetime(day) <= latest_day:
            continue

        # ここで初めてファイルを開く
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

            all_data.append(
                {
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
                }
            )

    if all_data:
        df_result = pd.DataFrame(all_data)

        # 既存データがあれば追記
        if not existing_df.empty:
            df_result = pd.concat([existing_df, df_result], ignore_index=True)
            if "day" in df_result.columns:
                df_result["day"] = pd.to_datetime(df_result["day"], errors="coerce")
            df_result = df_result.drop_duplicates(subset=["day", "dai_name", "dai_num"], keep="last").reset_index(drop=True)
        else:
            if "day" in df_result.columns:
                df_result["day"] = pd.to_datetime(df_result["day"], errors="coerce")

        # 最終更新日付を取得
        final_date = df_result["day"].max() if "day" in df_result.columns else None
        
        # "day"カラムをyyyy-mm-dd形式の文字列に変換
        if "day" in df_result.columns:
            df_result["day"] = df_result["day"].dt.strftime("%Y-%m-%d")

        # CSVで出力
        df_result.to_csv(output_path, index=False, encoding="utf-8-sig")
        
        # store_list.xlsxのlast_update列を更新
        if pd.notnull(final_date):
            df.loc[idx, "last_update"] = final_date.strftime("%Y-%m-%d")
        
        print(f"✅ {store_name}: 処理完了")

# store_list.csv を保存（Excelでの文字化け防止のためUTF-8 BOM付き）
df.to_csv(store_list_path, index=False, encoding='utf-8-sig')
print(f"\n✅ 全店舗の処理が完了しました")