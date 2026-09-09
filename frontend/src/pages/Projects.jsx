import React, { useEffect, useState } from 'react';
import { fetchProjects, createProject } from '../services/api';
import { FolderGit2, Plus, Users, FileText, Calendar, ArrowUpRight, X } from 'lucide-react';

function Projects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');

  const loadProjects = () => {
    setLoading(true);
    fetchProjects()
      .then((data) => setProjects(Array.isArray(data) ? data : data?.projects || []))
      .catch((err) => console.error('Failed to fetch projects:', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    try {
      setCreating(true);
      setError('');
      await createProject({ name: name.trim(), description: description.trim() });
      setName('');
      setDescription('');
      setShowModal(false);
      loadProjects();
    } catch (err) {
      console.error('Failed to create project:', err);
      setError(err.response?.data?.detail || 'Failed to create project.');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Data Projects</h1>
          <p className="page-subtitle">
            Configure dataset repositories, scoring profiles, and annotator teams.
          </p>
        </div>

        <button
          type="button"
          className="primary-btn"
          onClick={() => setShowModal(true)}
        >
          <Plus size={16} />
          <span>New Project</span>
        </button>
      </div>

      {loading ? (
        <div className="project-grid">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card" style={{ height: '220px' }}>
              <div className="skeleton-row" style={{ width: '60%' }} />
              <div className="skeleton-row" style={{ width: '90%', height: '20px' }} />
              <div className="skeleton-row" style={{ width: '40%', marginTop: 'auto' }} />
            </div>
          ))}
        </div>
      ) : projects.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">
              <FolderGit2 size={24} />
            </div>
            <h3>No Projects Configured</h3>
            <p>
              Get started by creating your first dataset project to begin tracking annotation quality.
            </p>
            <button
              type="button"
              className="primary-btn"
              onClick={() => setShowModal(true)}
            >
              <Plus size={16} />
              <span>Create Project</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="project-grid">
          {projects.map((project) => (
            <div className="project-card" key={project.id}>
              <div>
                <div className="project-card-header">
                  <span className="badge badge-good">Active</span>
                  <span
                    className="mono-cell"
                    style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}
                  >
                    ID #{project.id}
                  </span>
                </div>

                <h2 className="project-card-title">{project.name}</h2>
                <p className="project-card-desc">
                  {project.description || 'No description provided.'}
                </p>
              </div>

              <div>
                <div className="project-card-metrics">
                  <div className="project-metric-item">
                    <span className="project-metric-label">Items</span>
                    <span className="project-metric-value">
                      {project.items_count != null ? project.items_count : '—'}
                    </span>
                  </div>

                  <div className="project-metric-item">
                    <span className="project-metric-label">Annotators</span>
                    <span className="project-metric-value">
                      {project.annotators_count != null ? project.annotators_count : '—'}
                    </span>
                  </div>
                </div>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginTop: '0.75rem',
                  }}
                >
                  <span
                    style={{
                      fontSize: '0.75rem',
                      color: 'var(--text-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                    }}
                  >
                    <Calendar size={12} />
                    <span>Project {project.id}</span>
                  </span>

                  <a
                    href="/"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      color: 'var(--accent-300)',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      textDecoration: 'none',
                    }}
                  >
                    <span>View Dashboard</span>
                    <ArrowUpRight size={13} />
                  </a>
                </div>
              </div>
            </div>
          ))}

          {/* Quick Add Project Card */}
          <div
            className="project-card"
            style={{
              borderStyle: 'dashed',
              background: 'transparent',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              minHeight: '220px',
            }}
            onClick={() => setShowModal(true)}
          >
            <div className="empty-state" style={{ padding: '1rem' }}>
              <div
                className="empty-state-icon"
                style={{
                  width: '44px',
                  height: '44px',
                  marginBottom: '0.75rem',
                }}
              >
                <Plus size={20} />
              </div>
              <h3 style={{ fontSize: '0.95rem' }}>Add New Project</h3>
              <p style={{ fontSize: '0.75rem', marginBottom: 0 }}>
                Set up a new dataset schema
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Create Project Modal */}
      {showModal && (
        <div className="modal-backdrop" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2>Create Dataset Project</h2>
                <p>Register a new annotation repository with AQG.</p>
              </div>
              <button
                type="button"
                className="modal-close"
                onClick={() => setShowModal(false)}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreate} className="modal-body">
              {error && <div className="alert">{error}</div>}

              <div style={{ marginBottom: '1.25rem' }}>
                <label htmlFor="proj-name">Project Name *</label>
                <input
                  id="proj-name"
                  type="text"
                  placeholder="e.g. Autonomous Driving Lidar Labels"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  autoFocus
                />
              </div>

              <div style={{ marginBottom: '1.25rem' }}>
                <label htmlFor="proj-desc">Description</label>
                <textarea
                  id="proj-desc"
                  placeholder="Dataset purpose, quality goals, guidelines..."
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="secondary-btn"
                  onClick={() => setShowModal(false)}
                  disabled={creating}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="primary-btn"
                  disabled={creating || !name.trim()}
                >
                  {creating ? 'Creating...' : 'Create Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Projects;
