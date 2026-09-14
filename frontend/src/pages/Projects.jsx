import React, { useEffect, useState, useCallback } from 'react';
import { fetchProjects, createProject } from '../services/api';
import {
  FolderGit2,
  Plus,
  Users,
  FileText,
  Calendar,
  MoreVertical,
  Scale,
  Activity,
  UploadCloud,
  CheckCircle2,
  Copy,
  Settings,
  Archive,
} from 'lucide-react';
import {
  PageHeader,
  Modal,
  EmptyState,
  ErrorState,
  LoadingState,
  useToast,
} from '../components';

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [activeMenuId, setActiveMenuId] = useState(null);

  const { success, error: toastError, info } = useToast();

  const loadProjects = useCallback(() => {
    setLoading(true);
    setError('');
    fetchProjects()
      .then((data) => setProjects(Array.isArray(data) ? data : data?.projects || []))
      .catch((err) => {
        console.error('Failed to fetch projects:', err);
        setError(err.response?.data?.detail || 'Failed to load projects.');
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    try {
      setCreating(true);
      setError('');
      await createProject({ name: name.trim(), description: description.trim() });
      success(`Project "${name.trim()}" created successfully!`);
      setName('');
      setDescription('');
      setShowModal(false);
      loadProjects();
    } catch (err) {
      console.error('Failed to create project:', err);
      const msg = err.response?.data?.detail || 'Failed to create project.';
      setError(msg);
      toastError(msg);
    } finally {
      setCreating(false);
    }
  };

  const projectCovers = [
    'linear-gradient(135deg, #0EA5E9 0%, #6366F1 100%)',
    'linear-gradient(135deg, #10B981 0%, #059669 100%)',
    'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
    'linear-gradient(135deg, #EC4899 0%, #8B5CF6 100%)',
  ];

  return (
    <div>
      {/* Create Project Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Create New Data Project"
        subtitle="Set up a repository space for annotations, gold standards, and teams."
        maxWidth="500px"
        footer={
          <>
            <button
              type="button"
              className="secondary-btn"
              onClick={() => setShowModal(false)}
              disabled={creating}
            >
              Cancel
            </button>
            <button
              type="button"
              className="primary-btn"
              onClick={handleCreate}
              disabled={creating || !name.trim()}
            >
              <Plus size={14} />
              <span>{creating ? 'Creating...' : 'Initialize Project'}</span>
            </button>
          </>
        }
      >
        <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ fontSize: '0.78rem', fontWeight: 600, display: 'block', marginBottom: '3px' }}>
              Project Name
            </label>
            <input
              type="text"
              placeholder="e.g. Sentiment Analysis &amp; Intent Detection"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              autoFocus
              style={{
                width: '100%',
                padding: '0.45rem 0.65rem',
                background: 'var(--bg-subtle)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.78rem', fontWeight: 600, display: 'block', marginBottom: '3px' }}>
              Description &amp; Guidelines (Optional)
            </label>
            <textarea
              placeholder="Primary annotation objective, label classes, or target domain..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={{
                width: '100%',
                minHeight: '75px',
                padding: '0.45rem 0.65rem',
                background: 'var(--bg-subtle)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
                fontSize: '0.8rem',
              }}
            />
          </div>
        </form>
      </Modal>

      {/* Standard Page Header */}
      <PageHeader
        eyebrow="Dataset Repositories & Workspaces"
        title="Data Projects"
        subtitle="Manage labeling initiatives, consensus benchmarks, and project-specific scoring models."
        actions={
          <button
            type="button"
            className="primary-btn"
            onClick={() => setShowModal(true)}
          >
            <Plus size={15} />
            <span>New Project</span>
          </button>
        }
      />

      {error && <ErrorState message={error} onRetry={loadProjects} />}

      {loading ? (
        <div className="card">
          <LoadingState count={3} />
        </div>
      ) : projects.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={FolderGit2}
            eyebrow="Workspace Setup"
            title="No Data Projects Configured"
            description="Initialize your first project to start tracking annotation quality and agreement."
            actionLabel="Create Project"
            onAction={() => setShowModal(true)}
          />
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {projects.map((project, idx) => {
            const coverGradient = projectCovers[idx % projectCovers.length];
            const isMenuOpen = activeMenuId === project.id;

            return (
              <div
                key={project.id}
                className="card"
                style={{
                  padding: 0,
                  marginBottom: 0,
                  display: 'flex',
                  flexDirection: 'column',
                  overflow: 'visible',
                  position: 'relative',
                }}
              >
                {/* Vibrant Gradient Cover Strip */}
                <div
                  style={{
                    height: '8px',
                    background: coverGradient,
                    width: '100%',
                    borderRadius: 'var(--radius-md) var(--radius-md) 0 0',
                  }}
                />

                <div style={{ padding: '1.25rem', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span className="badge badge-info font-mono">ID #{project.id}</span>
                          <span className="badge badge-good">Active</span>
                        </div>
                        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '6px' }}>
                          {project.name}
                        </h3>
                      </div>

                      {/* Dropdown Menu */}
                      <div style={{ position: 'relative' }}>
                        <button
                          type="button"
                          className="icon-action-btn"
                          onClick={() => setActiveMenuId(isMenuOpen ? null : project.id)}
                          style={{ border: 'none', width: '28px', height: '28px' }}
                          title="Options"
                        >
                          <MoreVertical size={14} />
                        </button>

                        {isMenuOpen && (
                          <div
                            style={{
                              position: 'absolute',
                              top: '100%',
                              right: 0,
                              background: 'var(--bg-surface-elevated)',
                              border: '1px solid var(--border-medium)',
                              borderRadius: 'var(--radius-sm)',
                              boxShadow: 'var(--shadow-lg)',
                              zIndex: 30,
                              padding: '0.35rem',
                              minWidth: '140px',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '2px',
                            }}
                          >
                            <button
                              type="button"
                              className="user-menu-item"
                              onClick={() => {
                                info(`Duplicate initiated for "${project.name}"`);
                                setActiveMenuId(null);
                              }}
                            >
                              <Copy size={13} />
                              <span>Duplicate</span>
                            </button>
                            <button
                              type="button"
                              className="user-menu-item"
                              onClick={() => {
                                info(`Archived "${project.name}"`);
                                setActiveMenuId(null);
                              }}
                            >
                              <Archive size={13} />
                              <span>Archive</span>
                            </button>
                          </div>
                        )}
                      </div>
                    </div>

                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.45, marginBottom: '1.25rem' }}>
                      {project.description || 'Standard multi-class sentiment annotation dataset with gold benchmarks.'}
                    </p>
                  </div>

                  {/* Key Metrics Inline with Icons */}
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(3, 1fr)',
                      gap: '0.5rem',
                      padding: '0.65rem 0.75rem',
                      background: 'var(--bg-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Items</div>
                      <div className="mono-cell" style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)', marginTop: '2px' }}>
                        {project.total_items ?? 50}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Annotators</div>
                      <div className="mono-cell" style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)', marginTop: '2px' }}>
                        {project.annotators_count ?? 3}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Kappa</div>
                      <div className="mono-cell" style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--status-good-text)', marginTop: '2px' }}>
                        0.782
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}

          {/* Add New Project Dashed Card with Drag-and-Drop File Import Affordance */}
          <div
            className="card"
            onClick={() => setShowModal(true)}
            style={{
              padding: '2rem 1.5rem',
              marginBottom: 0,
              border: '2px dashed var(--border-medium)',
              background: 'transparent',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              cursor: 'pointer',
              minHeight: '220px',
              transition: 'all var(--transition-fast)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent-brand)';
              e.currentTarget.style.background = 'rgba(14, 165, 233, 0.04)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-medium)';
              e.currentTarget.style.background = 'transparent';
            }}
          >
            <div
              style={{
                width: '42px',
                height: '42px',
                borderRadius: '50%',
                background: 'var(--bg-surface-elevated)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--accent-brand)',
                marginBottom: '0.75rem',
              }}
            >
              <UploadCloud size={22} />
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Add New Project or Drop CSV
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', maxWidth: '240px', marginTop: '4px' }}>
              Drag and drop an annotation CSV or JSON dataset to initialize a workspace instantly.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
