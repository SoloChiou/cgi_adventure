const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "src", "line_login.js"), "utf8");

async function runLogin({ loggedIn, idToken = "id-token", initError = null }) {
  const status = { textContent: "" };
  const retry = {
    hidden: true,
    addEventListener(_event, listener) {
      this.listener = listener;
    },
  };
  const root = {
    querySelector(selector) {
      return selector.includes("status") ? status : retry;
    },
  };
  let submittedForm = null;
  let loginConfig = null;
  const document = {
    body: {
      appendChild(element) {
        submittedForm = element;
      },
    },
    querySelector() {
      return root;
    },
    createElement(tagName) {
      if (tagName === "form") {
        return {
          children: [],
          appendChild(child) {
            this.children.push(child);
          },
          submit() {
            this.submitted = true;
          },
        };
      }
      return {};
    },
  };
  const window = {
    LINE_LOGIN_CONFIG: {
      liffId: "123-test",
      backendLoginUrl: "https://backend.example/auth/line/",
    },
    location: {
      href: "https://login.example/?next=%2Finventory%2F&code=sensitive",
      origin: "https://login.example",
      pathname: "/",
      search: "?next=%2Finventory%2F&code=sensitive",
    },
    liff: {
      async init() {
        if (initError) throw initError;
      },
      isLoggedIn() {
        return loggedIn;
      },
      login(config) {
        loginConfig = config;
      },
      getIDToken() {
        return idToken;
      },
    },
  };

  vm.runInNewContext(source, { document, window, URL, URLSearchParams });
  await new Promise((resolve) => setImmediate(resolve));
  await new Promise((resolve) => setImmediate(resolve));
  return { loginConfig, retry, status, submittedForm };
}

test("未登入時使用不含 LINE 回呼參數的短網址重新登入", async () => {
  const result = await runLogin({ loggedIn: false });
  assert.equal(result.loginConfig.redirectUri, "https://login.example/?next=%2Finventory%2F");
  assert.equal(result.submittedForm, null);
});

test("取得 ID token 後以頂層表單正文送往後端", async () => {
  const result = await runLogin({ loggedIn: true });
  assert.equal(result.submittedForm.action, "https://backend.example/auth/line/");
  assert.equal(result.submittedForm.method, "post");
  assert.equal(result.submittedForm.submitted, true);
  assert.deepEqual(
    Array.from(result.submittedForm.children, (input) => [input.name, input.value]),
    [["id_token", "id-token"], ["next", "/inventory/"]],
  );
});

test("LIFF 初始化失敗時顯示可重試狀態", async () => {
  const result = await runLogin({ loggedIn: false, initError: new Error("failed") });
  assert.equal(result.status.textContent, "LINE 登入失敗，請重新嘗試。");
  assert.equal(result.retry.hidden, false);
});
