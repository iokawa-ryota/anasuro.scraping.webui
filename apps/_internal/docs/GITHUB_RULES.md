# GitHub Rules

このリポジトリの運用ルールを定義する。

## 1. ブランチ運用

- `main` は常に安定状態を保つ。
- 変更作業は必ず作業ブランチで行う。
- ブランチ命名例:
  - `feature/<topic>`
  - `fix/<topic>`
  - `chore/<topic>`

## 2. コミット運用

- 1コミット1目的を基本にする。
- 大規模変更は機能単位でコミットを分割する。
- 生成物をコミットしない（`distribution/` など）。

## 3. PR 運用

- `main` へ直接 push しない。PR 経由でマージする。
- PR 前に最低限のテストを実行する。
  - `python apps/_internal/test/run_api_smoke_tests.py`
  - `python apps/_internal/test/run_ui_e2e_playwright.py`
- PR本文に以下を記載する。
  - 目的
  - 変更点
  - テスト結果
  - 影響範囲

## 4. マージ後運用

- マージ後は作業ブランチを削除する（GitHub/ローカル両方）。
- 次の作業は最新 `main` から新しいブランチを切る。

## 5. 配布運用

- 開発正本は `apps/` 配下。
- 配布物は `build_distribution.bat` で生成する。
- 配布生成物（`distribution/slot-infomation/`, `distribution/*.zip`）は Git 追跡対象外。
