(function () {
  "use strict";

  const root = document.querySelector("[data-line-login]");
  if (!root) return;

  const status = root.querySelector("[data-line-login-status]");
  const retry = root.querySelector("[data-line-login-retry]");
  const csrfToken = root.querySelector("[name=csrfmiddlewaretoken]")?.value;

  function showError(message) {
    status.textContent = message;
    retry.hidden = false;
  }

  async function authenticate() {
    retry.hidden = true;
    status.textContent = "正在連接 LINE，請稍候……";

    if (root.dataset.loginEnabled !== "true") {
      showError("LINE 登入尚未完成環境設定，請聯絡管理者。");
      return;
    }
    if (!window.liff) {
      showError("無法載入 LINE 登入元件，請檢查網路後重試。");
      return;
    }

    try {
      const liffId = JSON.parse(document.getElementById("line-liff-id").textContent);
      await window.liff.init({ liffId: liffId });
      if (!window.liff.isLoggedIn()) {
        window.liff.login({ redirectUri: window.location.href });
        return;
      }

      const idToken = window.liff.getIDToken();
      if (!idToken) throw new Error("missing-id-token");

      const response = await fetch(root.dataset.loginEndpoint, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ id_token: idToken, next: root.dataset.next }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "line-login-failed");
      window.location.replace(result.redirect_url);
    } catch (error) {
      showError("LINE 登入失敗，請重新嘗試。");
    }
  }

  retry.addEventListener("click", authenticate);
  authenticate();
})();
