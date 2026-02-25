# 今後のアップデート展望

最終更新: 2026-02-25

## 最終目標

エンドユーザーがフォルダ直下の導線だけで迷わず運用できるWebアプリにする。

## 現在の前提

1. ユーザー導線は `setup.bat` と `start.bat` に統一する。  
2. 店舗設定は原則Web UIから行い、`store_list.csv` の直接編集は最小化する。  
3. 内部実装は `_internal/` に集約し、ユーザー操作対象から分離する。  
4. ドキュメントは次の3本に統一する。  
   - `apps/_internal/docs/PRODUCT_GOALS.md`（本ファイル）  
   - `apps/STARTUP_GUIDE.md`（ユーザーガイド）  
   - `apps/_internal/docs/CHANGELOG.md`（変更履歴）

## 達成状況

- 〇 Web UIで店舗設定を編集し、`store_list.csv` へ保存できる（確認済み）
- 〇 出力CSVの列名を `total` に統一（旧 `Total` は読込時に互換対応、確認済み）
- 〇 ルート直下中心の配布構成に整理（`_internal/` 分離、確認済み）
- 〇 ドキュメントを3本構成に整理
- 〇 スクレイピング停止時の自動中断とエラー表示（2分遷移なし検知）

## 方針（優先順位）

1. 安定運用を優先し、進捗表示は必要性が高まるまで再実装しない。  
2. 店舗設定のWeb UI運用を前提に、ファイル直編集への依存をさらに減らす。  
3. 配布運用で実際に発生した課題を `CHANGELOG.md` に記録し、改善を継続する。

## 運用方針（開発/配布）

1. Gitの正本は `apps/` 配下とし、開発変更はここに集約する。  
2. `distribution/` は生成物置き場とし、手編集しない。  
3. 配布物は `build_distribution.bat` で再生成する（手動コピー運用をしない）。  
4. `distribution/slot-infomation/` と `distribution/*.zip` はGit追跡対象外とする。  
5. 変更前後でテストを実施する。  
   - API: `python apps/_internal/test/run_api_smoke_tests.py`  
   - UI E2E: `python apps/_internal/test/run_ui_e2e_playwright.py`

## アプデ展望（直近）

- 〇 フォルダ指定をエクスプローラで
- 〇 `""` をディレクトリから排除
- □ 店データ削除を確認画面込みの2段階に
