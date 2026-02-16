import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[2]
STORE_LIST_PATH = ROOT / "store_list.csv"
APP_PATH = ROOT / "_internal" / "app" / "app.py"
BASE_HOST = "127.0.0.1"
BASE_PORT = 5010
BASE_URL = f"http://{BASE_HOST}:{BASE_PORT}"


def write_test_store_csv(path: Path) -> None:
    rows = [
        ["store_name", "store_url", "data_directory"],
        ["Store1", "https://example.com/1", ".\\data\\test"],
        ["Store2", "https://example.com/2", ".\\data\\test2"],
    ]
    text = "\n".join(",".join(row) for row in rows) + "\n"
    path.write_text(text, encoding="utf-8-sig")


def wait_for_server(url: str, timeout_sec: int = 20) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=2) as res:
                if 200 <= res.status < 500:
                    return True
        except URLError:
            pass
        except Exception:
            pass
        time.sleep(0.3)
    return False


def run():
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print("Playwright が未インストールです。")
        print("python -m pip install -r _internal/test/requirements-e2e.txt")
        print("python -m playwright install chromium")
        return 2

    if not STORE_LIST_PATH.exists():
        print(f"store_list.csv が見つかりません: {STORE_LIST_PATH}")
        return 1

    original_store = STORE_LIST_PATH.read_bytes()
    server_proc = None
    results = []

    def add_result(name: str, ok: bool, detail: str) -> None:
        results.append((name, ok, detail))

    try:
        write_test_store_csv(STORE_LIST_PATH)

        env = os.environ.copy()
        env["FLASK_HOST"] = BASE_HOST
        env["FLASK_PORT"] = str(BASE_PORT)
        env["FLASK_DEBUG"] = "0"
        server_proc = subprocess.Popen(
            [sys.executable, str(APP_PATH)],
            cwd=str(ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if not wait_for_server(f"{BASE_URL}/api/stores", timeout_sec=25):
            tail = ""
            if server_proc.stdout:
                try:
                    tail = "".join(server_proc.stdout.readlines()[-20:])
                except Exception:
                    tail = ""
            raise RuntimeError(f"Flask サーバーの起動を確認できませんでした\n{tail}".strip())

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, wait_until="domcontentloaded")

            # 1) editor open + header visible
            page.get_by_role("button", name="店舗設定を編集").click()
            panel_visible = page.locator("#storeEditorPanel").is_visible()
            header_texts = [t.strip() for t in page.locator("#storeEditorPanel .editor-header span").all_text_contents() if t.strip()]
            header_ok = header_texts == ["店舗名", "店舗URL", "保存先ディレクトリ"]
            add_result("Open store editor", panel_visible and header_ok, f"visible={panel_visible}, headers={header_texts}")

            # 2) delete modal flow
            rows_before = page.locator("#storeEditorPanel .editor-row").count()
            page.locator("#storeEditorPanel .editor-row .editor-del").first.click()
            modal_visible = page.locator("#deleteModal").is_visible()
            page.get_by_role("button", name="キャンセル").click()
            rows_after_cancel = page.locator("#storeEditorPanel .editor-row").count()
            page.locator("#storeEditorPanel .editor-row .editor-del").first.click()
            page.get_by_role("button", name="削除する").click()
            rows_after_delete = page.locator("#storeEditorPanel .editor-row").count()
            delete_ok = modal_visible and rows_after_cancel == rows_before and rows_after_delete == max(0, rows_before - 1)
            add_result(
                "Delete modal confirm",
                delete_ok,
                f"before={rows_before}, after_cancel={rows_after_cancel}, after_delete={rows_after_delete}",
            )

            # 3) add row + save
            page.get_by_role("button", name="行を追加").click()
            row_count = page.locator("#storeEditorPanel .editor-row").count()
            new_index = row_count - 1
            page.locator(f'#storeEditorPanel input[data-field="name"][data-index="{new_index}"]').fill("E2E店舗")
            page.locator(f'#storeEditorPanel input[data-field="url"][data-index="{new_index}"]').fill("https://example.com/e2e")
            page.locator(f'#storeEditorPanel input[data-field="directory"][data-index="{new_index}"]').fill("./data/e2e")
            page.get_by_role("button", name="CSVへ保存").click()
            page.wait_for_timeout(400)
            alert_text = page.locator("#alert").inner_text().strip()
            panel_hidden = not page.locator("#storeEditorPanel").is_visible()
            save_ok = ("保存" in alert_text or "件の店舗設定を保存しました" in alert_text) and panel_hidden
            add_result("Save store editor", save_ok, f"alert={alert_text}, panel_hidden={panel_hidden}")

            browser.close()

    except Exception as e:
        add_result("E2E execution", False, str(e))
    finally:
        if server_proc is not None:
            try:
                server_proc.terminate()
                server_proc.wait(timeout=5)
            except Exception:
                try:
                    server_proc.kill()
                except Exception:
                    pass
        STORE_LIST_PATH.write_bytes(original_store)

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"RESULT {passed}/{total}")
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}\t{name}\t{detail}")
    return 0 if passed == total and total > 0 else 1


if __name__ == "__main__":
    raise SystemExit(run())
