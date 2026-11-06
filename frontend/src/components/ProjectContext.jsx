import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { fetchProjects } from '../services/api';

const ProjectContext = createContext(null);
const STORAGE_KEY = 'aqg_active_project_id';

export function ProjectProvider({ children }) {
  const [projects, setProjects] = useState([]);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [projectId, setProjectIdState] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? parseInt(saved, 10) : null;
  });

  const refreshProjects = useCallback(async () => {
    try {
      setLoadingProjects(true);
      const data = await fetchProjects();
      const list = Array.isArray(data) ? data : data?.projects || [];
      setProjects(list);

      setProjectIdState((currentId) => {
        if (list.length === 0) {
          localStorage.removeItem(STORAGE_KEY);
          return null;
        }

        const exists = list.some((p) => p.id === currentId);
        if (exists) {
          return currentId;
        }

        const firstId = list[0].id;
        localStorage.setItem(STORAGE_KEY, String(firstId));
        return firstId;
      });
    } catch (err) {
      console.error('Failed to load projects in ProjectContext:', err);
    } finally {
      setLoadingProjects(false);
    }
  }, []);

  useEffect(() => {
    refreshProjects();
  }, [refreshProjects]);

  const setProjectId = useCallback((id) => {
    const numId = id ? parseInt(id, 10) : null;
    setProjectIdState(numId);
    if (numId) {
      localStorage.setItem(STORAGE_KEY, String(numId));
    } else {
      localStorage.removeItem(STORAGE_KEY);
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
