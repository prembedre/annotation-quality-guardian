/**
 * Auth service — handles JWT storage and auth API calls.
 */

const TOKEN_KEY = 'aqg_auth_token';

/**
 * Retrieve the stored JWT from localStorage.
 * @returns {string|null}
 */
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Store the JWT in localStorage.
 * @param {string} token
 */
export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Remove the JWT from localStorage.
 */
export function removeToken() {
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * POST /auth/login — authenticate and store the returned JWT.
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{access_token: string, user: object}>}
 */
export async function login(email, password) {
  const res = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Login failed (${res.status})`);
  }

  const data = await res.json();
  setToken(data.access_token);
  return data;
}

/**
 * Remove the stored JWT (logout).
 */
export function logout() {
  removeToken();
}

/**
 * GET /auth/me — fetch the current user's profile using the stored JWT.
 * @returns {Promise<object>}
 */
export async function fetchMe() {
  const token = getToken();
  if (!token) throw new Error('No auth token found');

  const res = await fetch('/auth/me', {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    if (res.status === 401 || res.status === 403) {
      removeToken();
    }
    throw new Error(`Failed to fetch user (${res.status})`);
  }

  return res.json();
}

/**
 * POST /auth/bootstrap — one-shot first Admin creation (only works when DB is empty).
 * @param {string} email
 * @param {string} fullName
 * @param {string} password
 * @returns {Promise<{access_token: string, user: object}>}
 */
export async function bootstrap(email, fullName, password) {
  const res = await fetch('/auth/bootstrap', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, full_name: fullName, password }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Bootstrap failed (${res.status})`);
  }

  const data = await res.json();
  setToken(data.access_token);
  return data;
}
