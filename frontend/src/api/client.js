import axios from "axios";

const ACCESS_TOKEN_KEY = "ssp_access_token";
const REFRESH_TOKEN_KEY = "ssp_refresh_token";

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens({ access, refresh }) {
  if (access) localStorage.setItem(ACCESS_TOKEN_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

const api = axios.create({ baseURL: "/api/" });

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On a 401, try refreshing the access token once before giving up -- keeps
// a logged-in session alive across the JWT's 8-hour access token lifetime
// without forcing a re-login every time it's close to expiring.
let refreshPromise = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status !== 401 || original._retried) {
      throw error;
    }
    const refresh = getRefreshToken();
    if (!refresh) {
      clearTokens();
      throw error;
    }
    original._retried = true;
    try {
      if (!refreshPromise) {
        refreshPromise = axios
          .post("/api/auth/token/refresh/", { refresh })
          .finally(() => {
            refreshPromise = null;
          });
      }
      const { data } = await refreshPromise;
      setTokens({ access: data.access });
      original.headers.Authorization = `Bearer ${data.access}`;
      return api(original);
    } catch (refreshError) {
      clearTokens();
      throw refreshError;
    }
  }
);

export default api;
