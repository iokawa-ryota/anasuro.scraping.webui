"""
Test mode backend config.
配布時に不要なら _internal/devtools/test_mode フォルダごと削除してください。
"""

ENABLE_TEST_MODE = True
MAX_DAYS_PER_STORE = 3


def get_config():
    return {
        "enabled": bool(ENABLE_TEST_MODE),
        "max_days_per_store": int(MAX_DAYS_PER_STORE),
    }
