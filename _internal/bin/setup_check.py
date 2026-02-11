#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
INTERNAL_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = INTERNAL_ROOT.parent
APP_DIR = INTERNAL_ROOT / "app"
RUNTIME_DIR = INTERNAL_ROOT / "runtime"
OUTPUT_DIR = PROJECT_ROOT / "output"
STORE_LIST_PATH = PROJECT_ROOT / "store_list.csv"


def check_python_version():
    print("Python バージョンを確認中...")
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"OK Python {version}")
    return sys.version_info >= (3, 8)


def check_packages():
    print("\nパッケージを確認中...")
    required_packages = {
        'flask': 'Flask',
        'pandas': 'pandas',
        'selenium': 'selenium',
        'bs4': 'beautifulsoup4',
        'undetected_chromedriver': 'undetected-chromedriver',
        'tqdm': 'tqdm',
        'lxml': 'lxml',
    }
    missing = []
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"OK {package_name}")
        except ImportError:
            print(f"NG {package_name}")
            missing.append(package_name)

    if not missing:
        return True

    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade'] + missing)
        print("OK インストール完了")
        return True
    except subprocess.CalledProcessError as e:
        print(f"NG インストール失敗: {e}")
        return False


def check_program_files():
    print("\nプログラムファイルを確認中...")
    required = {
        APP_DIR / 'app.py': 'Flask バックエンド',
        APP_DIR / 'index.html': 'フロントエンド UI',
        APP_DIR / 'anasuro_selective.py': 'スクレイピング処理',
        APP_DIR / 'offline-scraing.py': 'オフライン整形処理',
    }
    ok = True
    for path, desc in required.items():
        if path.exists():
            print(f"OK {path.name} ({desc})")
        else:
            print(f"NG {path.name} ({desc})")
            ok = False
    return ok


def check_directories():
    print("\n必要ディレクトリを確認中...")
    for p in (RUNTIME_DIR, OUTPUT_DIR):
        p.mkdir(parents=True, exist_ok=True)
        print(f"OK {p}")
    return True


def check_store_list():
    print("\n店舗リスト CSV を確認中...")
    if STORE_LIST_PATH.exists():
        import pandas as pd
        df = pd.read_csv(STORE_LIST_PATH)
        print(f"OK {STORE_LIST_PATH}")
        print(f"店舗数: {len(df)}")
        return True

    print(f"NG {STORE_LIST_PATH} が見つかりません")
    return False


def main():
    checks = [
        ("Python バージョン確認", check_python_version),
        ("パッケージ確認", check_packages),
        ("プログラムファイル確認", check_program_files),
        ("ディレクトリ確認", check_directories),
        ("店舗リスト確認", check_store_list),
    ]

    results = []
    for name, fn in checks:
        try:
            results.append((name, fn()))
        except Exception as e:
            print(f"NG {name}: {e}")
            results.append((name, False))

    print("\nチェック結果:")
    for name, result in results:
        print(("OK" if result else "NG") + f": {name}")

    if all(r for _, r in results):
        print("\nセットアップ完了")
        print("python _internal/app/app.py")
        print("http://localhost:5000")
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()

