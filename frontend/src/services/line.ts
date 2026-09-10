import liff from "@line/liff";

let initialization: Promise<void> | null = null;

export type LineChannelContext = "mini_app" | "web";

function channelContext(): LineChannelContext {
  return new URLSearchParams(window.location.search).get("login") === "web" ? "web" : "mini_app";
}

function configuredLiffId(context: LineChannelContext) {
  return context === "web" ? import.meta.env.VITE_WEB_LIFF_ID?.trim() : import.meta.env.VITE_LIFF_ID?.trim();
}

function liffError(operation: string, cause: unknown) {
  const value = cause as { code?: unknown };
  const code = typeof value?.code === "string" && /^[A-Z0-9_-]{1,40}$/i.test(value.code)
    ? `（${value.code}）`
    : "";
  return new Error(`LINE ${operation}失敗${code}`);
}

export function initializeLiff() {
  const context = channelContext();
  const liffId = configuredLiffId(context);
  if (!liffId) return Promise.reject(new Error(context === "web" ? "缺少 VITE_WEB_LIFF_ID" : "缺少 VITE_LIFF_ID"));
  if (!initialization) initialization = liff.init({ liffId }).catch((error: unknown) => {
    initialization = null;
    throw liffError("初始化", error);
  });
  return initialization;
}
export async function getLineLogin() {
  const context = channelContext();
  await initializeLiff();
  if (!liff.isLoggedIn()) {
    try {
      liff.login({ redirectUri: window.location.href });
    } catch (error) {
      throw liffError("登入導向", error);
    }
    return new Promise<{ idToken: string; channelContext: LineChannelContext }>(() => undefined);
  }
  const token = liff.getIDToken();
  if (!token) throw new Error("LINE 登入完成，但未取得 ID token");
  return { idToken: token, channelContext: context };
}
export async function logoutLine() { await initializeLiff(); if (liff.isInClient()) { liff.closeWindow(); return; } if (liff.isLoggedIn()) liff.logout(); }
