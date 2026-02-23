(function () {
  const CSS = `
    .test-panel {
      margin-bottom: 16px;
      padding: 10px 12px;
      border: 1px dashed #9aa7ff;
      border-radius: 8px;
      background: #f5f7ff;
    }
    .test-row {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }
    .test-row label {
      font-size: 13px;
    }
    .test-note {
      font-size: 12px;
      color: #555;
    }
  `;

  function injectCss() {
    const style = document.createElement("style");
    style.textContent = CSS;
    document.head.appendChild(style);
  }

  function mount({ mountId, maxDays }) {
    injectCss();
    const mountEl = document.getElementById(mountId);
    if (!mountEl) return;
    mountEl.innerHTML = `
      <div class="test-panel">
        <div class="test-row">
          <label>
            <input type="checkbox" id="testModeToggle">
            テストモード（件数制限）
          </label>
          <span class="test-note">ON時は各店舗の最新${maxDays}日分のみ取得</span>
        </div>
      </div>
    `;
  }

  function getOptions() {
    const toggle = document.getElementById("testModeToggle");
    return { test_mode: Boolean(toggle && toggle.checked) };
  }

  function formatMessage(result, fallbackMessage) {
    if (result && result.test_mode_applied) {
      return `${fallbackMessage}（テストモード: 最新${result.test_mode_max_days}日）`;
    }
    return fallbackMessage;
  }

  window.TestModeUI = { mount, getOptions, formatMessage };
})();
