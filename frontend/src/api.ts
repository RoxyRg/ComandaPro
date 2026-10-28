import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE = '/api';
const TOKEN_KEY = 'comandapro.access';
export const getAccessToken = () => sessionStorage.getItem(TOKEN_KEY);
export const setAccessToken = (token: string | null) => { if (token) { sessionStorage.setItem(TOKEN_KEY, token); window.dispatchEvent(new CustomEvent('comandapro:token-refreshed')); } else sessionStorage.removeItem(TOKEN_KEY); };

export const api = axios.create({ baseURL: API_BASE, withCredentials: true, timeout: 15000 });
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshInFlight: Promise<string> | null = null;
api.interceptors.response.use(response => response, async (error: AxiosError) => {
  const config = error.config as (InternalAxiosRequestConfig & { _comandaRetried?: boolean }) | undefined;
  const url = config?.url ?? '';
  if (error.response?.status !== 401 || !config || config._comandaRetried || /\/auth\/(login|refresh|logout)/.test(url)) throw error;
  config._comandaRetried = true;
  try {
    if (!refreshInFlight) {
      refreshInFlight = api.post('/auth/refresh', {}).then(response => {
        const token = response.data.access_token as string;
        setAccessToken(token);
        return token;
      }).finally(() => { refreshInFlight = null; });
    }
    const fresh = await refreshInFlight;
    config.headers.Authorization = `Bearer ${fresh}`;
    return api.request(config);
  } catch (refreshError) {
    setAccessToken(null);
    window.dispatchEvent(new CustomEvent('comandapro:session-expired'));
    throw refreshError;
  }
});

export function messageOf(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data as { detail?: unknown } | undefined;
    if (typeof detail?.detail === 'string') return detail.detail;
    if (Array.isArray(detail?.detail)) return detail.detail.map(x => String((x as { msg?: string }).msg ?? x)).join(', ');
    return error.message;
  }
  return error instanceof Error ? error.message : 'Ocurrió un error inesperado';
}
