import liff from "@line/liff";

let initialization: Promise<void> | null = null;
export function initializeLiff() {
  const liffId = import.meta.env.VITE_LIFF_ID?.trim();
  if (!liffId) return Promise.reject(new Error("缺少 VITE_LIFF_ID"));
  if (!initialization) initialization = liff.init({ liffId }).catch((error) => { initialization = null; throw error; });
  return initialization;
}
export async function getLineIdToken() {
  await initializeLiff();
  if (!liff.isLoggedIn()) { liff.login({ redirectUri: window.location.href }); return new Promise<string>(() => undefined); }
  const token = liff.getIDToken();
  if (!token) throw new Error("LINE 未提供 ID token");
  return token;
}
export async function logoutLine() { await initializeLiff(); if (liff.isInClient()) { liff.closeWindow(); return; } if (liff.isLoggedIn()) liff.logout(); }
