import axios from "axios";

const configuredUrl = import.meta.env.VITE_API_URL?.trim();
if (import.meta.env.PROD && !configuredUrl) throw new Error("正式建置缺少 VITE_API_URL");
const baseURL = (configuredUrl || "http://localhost:8000/api").replace(/\/+$/, "");
let apiToken = sessionStorage.getItem("cgi_adventure_api_token") || "";
let csrfToken = "";

export const api = axios.create({ baseURL, withCredentials: true, headers: { "Content-Type": "application/json" } });

export function setApiToken(value: string) {
  apiToken = value;
  if (value) sessionStorage.setItem("cgi_adventure_api_token", value);
  else sessionStorage.removeItem("cgi_adventure_api_token");
}

export function setCsrfToken(value: string) { csrfToken = value; }

api.interceptors.request.use((config) => {
  if (apiToken) config.headers.set("Authorization", `Token ${apiToken}`);
  const method = config.method?.toLowerCase();
  if (csrfToken && method && !["get", "head", "options"].includes(method)) config.headers.set("X-CSRFToken", csrfToken);
  return config;
});
