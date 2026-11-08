import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { fetchProjects } from '../services/api';
import { AuthContext } from './AuthContext';

const ProjectContext = createContext(null);
const STORAGE_KEY = 'aqg_active_project_id';

export function ProjectProvider({ children }) {
  const [projects, setProjects] = useState([]);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [error, setError] = useState(null);

  const [projectId, setProjectIdState] = useState(() => {
    if (typeof window === 'undefined') return null;
    const saved = localStorage.getItem(STORAGE_KEY);
    const parsed = saved ? parseInt(saved, 10) : null;
    return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
  });

  // Safely consume AuthContext (works inside AuthProvider or standalone in isolated unit tests)
  const auth = useContext(AuthContext);
  const token = auth?.token ?? (typeof window !== 'undefined' ? localStorage.getItem('aqg_auth_token') : null);
  const isStandalone = auth === null; // In unit tests where ProjectProvider is rendered without AuthProvider

  const refreshProjects = useCallback(async () => {
    const activeToken = auth?.token ?? (typeof window !== 'undefined' ? localStorage.getItem('aqg_auth_token') : null);
    // In normal app flow, avoid unauthenticated API calls that return 401 before user logs in
    if (!activeToken && !isStandalone) {
      setLoadingProjects(false);
      return;
    }

    try {
      setLoadingProjects(true);
      setError(null);
      const data = await fetchProjects();
      const list = Array.isArray(data) ? data : data?.projects || [];
      setProjects(list);

      setProjectIdState((currentId) => {
        if (list.length === 0) {
          // Explicit empty project list from successful backend response
          localStorage.removeItem(STORAGE_KEY);
          return null;
        }

        // 1. If currently selected project ID is in the fetched list, preserve it
        const currentExists = currentId ? list.some((p) => p.id === currentId) : false;
        if (currentExists) {
          localStorage.setItem(STORAGE_KEY, String(currentId));
          return currentId;
        }

        // 2. If stored project ID in localStorage exists in the list, restore it
        const saved = typeof window !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null;
        const savedId = saved ? parseInt(saved, 10) : null;
        const savedExists = savedId ? list.some((p) => p.id === savedId) : false;
        if (savedExists) {
          return savedId;
        }

        // 3. Select the first available project from the database
        const firstId = list[0].id;
        if (typeof window !== 'undefined') {
          localStorage.setItem(STORAGE_KEY, String(firstId));
        }
        return firstId;
      });
    } catch (err) {
      console.error('Failed to load projects in ProjectContext:', err);
      // Preserve existing projects on transient error; do not confuse error with empty project list
      setError(err?.response?.data?.detail || err?.message || 'Failed to load projects');
    } finally {
      setLoadingProjects(false);
    }
  }, [auth?.token, isStandalone]);

  // Reactive listener: automatically fetch projects when authentication state changes
  useEffect(() => {
    if (token || isStandalone) {
      refreshProjects();
    } else {
      // User logged out — clear projects and active selection
      setProjects([]);
      setProjectIdState(null);
      setError(null);
      setLoadingProjects(false);
    }
  }, [token, isStandalone, refreshProjects]);

  const setProjectId = useCallback((id) => {
    const numId = id ? parseInt(id, 10) : null;
    const validId = Number.isInteger(numId) && numId > 0 ? numId : null;
    setProjectIdState(validId);
    if (typeof window !== 'undefined') {
      if (validId) {
        localStorage.setItem(STORAGE_KEY, String(validId));
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
  }, []);

  const activeProject = projects.find((p) => p.id === projectId) || null;

  return (
    <ProjectContext.Provider
      value={{
        projectId,
        project: activeProject,
        projects,
        setProjectId,
        loadingProjects,
        error,
        refreshProjects,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
}
