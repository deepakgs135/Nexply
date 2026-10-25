const API_BASE = import.meta.env.VITE_API_BASE || "";
let accessToken = sessionStorage.getItem("nexply_access_token") || "";

export type ApiRequest = <T>(path: string, init?: RequestInit) => Promise<T>;

export function hasAccessToken() {
  return Boolean(accessToken);
}

export function setAccessToken(token: string) {
  accessToken = token;
  if (token) sessionStorage.setItem("nexply_access_token", token);
  else sessionStorage.removeItem("nexply_access_token");
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  const result = await response.json().catch(() => ({}));
  if (response.status === 401 && accessToken && !path.startsWith("/auth/")) {
    setAccessToken("");
    window.dispatchEvent(new Event("nexply:auth-expired"));
  }
  if (!response.ok) throw new Error(result.detail || `Request failed (${response.status})`);
  return result as T;
}

export async function downloadBlob(path: string, init?: RequestInit): Promise<Blob> {
  const headers = new Headers(init?.headers);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (response.status === 401 && accessToken && !path.startsWith("/auth/")) {
    setAccessToken("");
    window.dispatchEvent(new Event("nexply:auth-expired"));
  }
  if (!response.ok) {
    const result = await response.json().catch(() => ({}));
    throw new Error(result.detail || `Request failed (${response.status})`);
  }
  return response.blob();
}
