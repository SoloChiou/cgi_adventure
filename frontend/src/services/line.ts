import liff from "@line/liff";

let initialization: Promise<void> | null = null;

function liffError(operation: string, cause: unknown) {
  const value = cause as { code?: unknown };
  const code = typeof value?.code === "string" && /^[A-Z0-9_-]{1,40}$/i.test(value.code)
    ? `（${value.code}）`
    : "";
  return new Error(`LINE ${operation}失敗${code}`);
}

export function initializeLiff() {
  const liffId = import.meta.env.VITE_LIFF_ID?.trim();
  if (!liffId) return Promise.reject(new Error("缺少 VITE_LIFF_ID"));
  if (!initialization) initialization = liff.init({ liffId }).catch((error: unknown) => {
    initialization = null;
    throw liffError("初始化", error);
  });
  return initialization;
}
export async function getLineIdToken() {
  await initializeLiff();
  if (!liff.isLoggedIn()) {
    try {
      liff.login({ redirectUri: window.location.href });
    } catch (error) {
      throw liffError("登入導向", error);
    }
    return new Promise<string>(() => undefined);
  }
  const token = liff.getIDToken();
  if (!token) throw new Error("LINE 登入完成，但未取得 ID token");
  return token;
}
export async function logoutLine() { await initializeLiff(); if (liff.isInClient()) { liff.closeWindow(); return; } if (liff.isLoggedIn()) liff.logout(); }
