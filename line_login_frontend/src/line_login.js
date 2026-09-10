(function () {
  "use strict";

  const root = document.querySelector("[data-line-login]");
  const status = root.querySelector("[data-line-login-status]");
  const retry = root.querySelector("[data-line-login-retry]");
  const config = window.LINE_LOGIN_CONFIG || {};

  function showError(message) {
    status.textContent = message;
    retry.hidden = false;
  }

  function submitToken(idToken) {
    const form = document.createElement("form");
    form.method = "post";
    form.action = config.backendLoginUrl;

    const fields = {
      id_token: idToken,
      next: new URLSearchParams(window.location.search).get("next") || "/",
    };
    for (const [name, value] of Object.entries(fields)) {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      input.value = value;
      form.appendChild(input);
    }

    document.body.appendChild(form);
    form.submit();
  }

  function loginRedirectUrl() {
    const redirectUrl = new URL(window.location.pathname, window.location.origin);
    const next = new URLSearchParams(window.location.search).get("next");
    if (next) redirectUrl.searchParams.set("next", next);
    return redirectUrl.href;
  }

  async function authenticate() {
    retry.hidden = true;
    status.textContent = "正在連接 LINE，請稍候……";

    if (!config.liffId || !config.backendLoginUrl) {
      showError("LINE 登入尚未完成環境設定，請聯絡管理者。");
      return;
    }
    if (!window.liff) {
      showError("無法載入 LINE 登入元件，請檢查網路後重試。");
      return;
    }

    try {
      await window.liff.init({ liffId: config.liffId });
      if (!window.liff.isLoggedIn()) {
        window.liff.login({ redirectUri: loginRedirectUrl() });
        return;
      }

      const idToken = window.liff.getIDToken();
      if (!idToken) throw new Error("missing-id-token");
      status.textContent = "LINE 驗證完成，正在進入遊戲……";
      submitToken(idToken);
    } catch (error) {
      showError("LINE 登入失敗，請重新嘗試。");
    }
  }

  retry.addEventListener("click", authenticate);
  authenticate();
})();
