import { Api } from "./Api";

// ponytail: module-level singleton, swap for DI if multiple backends are ever needed
export let apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8095";

export const api = new Api({ baseURL: apiBaseUrl });

export function setApiBaseUrl(url: string) {
  apiBaseUrl = url;
  api.instance.defaults.baseURL = url;
}
