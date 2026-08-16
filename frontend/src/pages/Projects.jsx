import React, { useEffect, useState } from 'react';
import { fetchProjects } from '../services/api';

function Projects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProjects()
      .then((data) => setProjects(data.projects || []))
      .catch((err) => console.error('Failed to fetch projects:', err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 className="page-title">Projects</h1>

      {loading ? (
        <p style={{ color: 'var(--color-text-muted)' }}>Loading projects...</p>
      ) : projects.length === 0 ? (
        <div className="card">
          <p style={{ color: 'var(--color-text-muted)' }}>
            No projects found. Create one via the API or connect the backend.
          </p>
        </div>
      ) : (
        projects.map((project) => (
          <div className="card" key={project.id}>
            <h2>{project.name}</h2>
            <p>{project.description}</p>
          </div>
        ))
      )}
    </div>
  );
}

export default Projects;
