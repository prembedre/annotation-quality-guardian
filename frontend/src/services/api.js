/**
 * API service — centralizes all backend HTTP calls.
 */

import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

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
  const { data } = await api.get('/scores', { params });
  return data;
}

export async function computeScores(projectId) {
  const { data } = await api.post('/scores/compute', null, {
    params: { project_id: projectId },
  });
  return data;
}

export default api;
