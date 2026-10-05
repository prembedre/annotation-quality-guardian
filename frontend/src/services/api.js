/**
 * API service — centralizes all backend HTTP calls.
 *
 * Automatically injects Authorization: Bearer <token> on every request
 * when a JWT is present in localStorage.
 * Supports VITE_API_BASE_URL for environments where the Vite proxy is not
 * available (e.g. inside the Docker frontend container).
 */

import axios from 'axios';
import { getToken } from './authService';

const baseURL = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/api`
  : '/api';

const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor: attach JWT Bearer token ──────────────────
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token && !token.startsWith('demo_token_')) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: clear token on 401 ─────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const token = getToken();
      // Only redirect on 401 if it's an actual backend JWT token failure
      if (token && !token.startsWith('demo_token_')) {
        localStorage.removeItem('aqg_auth_token');
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// ── Projects ────────────────────────────────────────
export async function fetchProjects() {
  const { data } = await api.get('/projects');
  return data;
}

export async function fetchProject(id) {
  const { data } = await api.get(`/projects/${id}`);
  return data;
}

export async function createProject(payload) {
  const { data } = await api.post('/projects', payload);
  return data;
}

// ── Annotations ─────────────────────────────────────
export async function fetchAnnotations(params = {}) {
  const { data } = await api.get('/annotations', { params });
  return data;
}

export async function createAnnotation(payload) {
  const { data } = await api.post('/annotations', payload);
  return data;
}

// ── Scores ──────────────────────────────────────────
export async function fetchScores(params = {}) {
  const { data } = await api.get('/scores/', { params });
  return data;
}

export async function computeScores(projectId) {
  const { data } = await api.post('/scores/compute', null, {
    params: { project_id: projectId },
  });
  return data;
}

export default api;
