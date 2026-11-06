import React, { useEffect, useState, useCallback } from 'react';
import api, { fetchProjects, createProject, duplicateProject, archiveProject } from '../services/api';
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
  DatasetUploadModal,
  useProject,
} from '../components';

export default function Projects() {
  const { refreshProjects } = useProject();
  const [projects, setProjects] = useState([]);
  const [projectSummaries, setProjectSummaries] = useState({});
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [droppedFile, setDroppedFile] = useState(null);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [activeMenuId, setActiveMenuId] = useState(null);

  const { success, error: toastError } = useToast();

  const loadProjects = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await fetchProjects();
      const list = Array.isArray(data) ? data : data?.projects || [];
      setProjects(list);

      // Fetch real per-project score summary (kappa, item counts, annotator counts)
      const summariesMap = {};
      await Promise.all(
        list.map(async (p) => {
          try {
            const res = await api.get('/scores/summary', { params: { project_id: p.id } });
            summariesMap[p.id] = res.data;
          } catch {
            // Keep empty if summary endpoint fails
          }
        })
      );
      setProjectSummaries(summariesMap);
    } catch (err) {
      console.error('Failed to fetch projects:', err);
      setError(err.response?.data?.detail || 'Failed to load projects.');
    } finally {
      setLoading(false);
    }
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
      refreshProjects?.();
    } catch (err) {
      console.error('Failed to create project:', err);
      const msg = err.response?.data?.detail || 'Failed to create project.';
      setError(msg);
      toastError(msg);
    } finally {
      setCreating(false);
    }
  };

  const handleDuplicate = async (projId, projName) => {
    try {
      setActiveMenuId(null);
      const copy = await duplicateProject(projId);
      success(`Project "${projName}" duplicated as "${copy.name}".`);
      loadProjects();
      refreshProjects?.();
    } catch (err) {
      console.error('Failed to duplicate project:', err);
      toastError(err.response?.data?.detail || 'Failed to duplicate project.');
    }
  };

  const handleArchive = async (projId, projName) => {
    try {
      setActiveMenuId(null);
      await archiveProject(projId);
      success(`Project "${projName}" archived successfully.`);
      loadProjects();
      refreshProjects?.();
    } catch (err) {
      console.error('Failed to archive project:', err);
      toastError(err.response?.data?.detail || 'Failed to archive project.');
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

      {/* Dataset Upload Modal */}
      <DatasetUploadModal
        isOpen={showUploadModal}
        onClose={() => {
          setShowUploadModal(false);
          setDroppedFile(null);
        }}
        projects={projects}
        initialFile={droppedFile}
        onSuccess={() => {
          loadProjects();
          success('Dataset uploaded and processed successfully!');
        }}
      />

      {/* Standard Page Header */}
      <PageHeader
        eyebrow="Dataset Repositories & Workspaces"
        title="Data Projects"
        subtitle="Manage labeling initiatives, consensus benchmarks, and project-specific scoring models."
        actions={
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              type="button"
              className="secondary-btn"
              onClick={() => {
                setDroppedFile(null);
                setShowUploadModal(true);
              }}
            >
              <UploadCloud size={15} />
              <span>Upload Dataset</span>
            </button>
            <button
              type="button"
              className="primary-btn"
              onClick={() => setShowModal(true)}
            >
              <Plus size={15} />
              <span>New Project</span>
            </button>
          </div>
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
            const summary = projectSummaries[project.id];
            const itemsCount = summary?.total_items ?? project.total_items ?? 0;
            const annotatorsCount = summary?.annotators_count ?? project.annotators_count ?? 0;
            const kappa = summary?.kappa;

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
                              onClick={() => handleDuplicate(project.id, project.name)}
                            >
                              <Copy size={13} />
                              <span>Duplicate</span>
                            </button>
                            <button
                              type="button"
                              className="user-menu-item"
                              onClick={() => handleArchive(project.id, project.name)}
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
                        {itemsCount}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Annotators</div>
                      <div className="mono-cell" style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)', marginTop: '2px' }}>
                        {annotatorsCount}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Kappa</div>
                      <div
                        className="mono-cell"
                        style={{
                          fontWeight: 700,
                          fontSize: '0.95rem',
                          color: kappa != null ? (kappa >= 0.7 ? 'var(--status-good-text)' : 'var(--status-medium-text)') : 'var(--text-muted)',
                          marginTop: '2px',
                        }}
                      >
                        {kappa != null ? kappa.toFixed(3) : '—'}
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
            onClick={() => {
              setDroppedFile(null);
              setShowUploadModal(true);
            }}
            onDragOver={(e) => {
              e.preventDefault();
              e.currentTarget.style.borderColor = 'var(--accent-brand)';
              e.currentTarget.style.background = 'rgba(14, 165, 233, 0.08)';
            }}
            onDragLeave={(e) => {
              e.preventDefault();
              e.currentTarget.style.borderColor = 'var(--border-medium)';
              e.currentTarget.style.background = 'transparent';
            }}
            onDrop={(e) => {
              e.preventDefault();
              e.currentTarget.style.borderColor = 'var(--border-medium)';
              e.currentTarget.style.background = 'transparent';
              const file = e.dataTransfer.files?.[0];
              if (file) {
                setDroppedFile(file);
                setShowUploadModal(true);
              }
            }}
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
              Upload Dataset or Drop CSV / JSON
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', maxWidth: '240px', marginTop: '4px' }}>
              Drag and drop an annotation CSV or JSON dataset to ingest records and compute quality scores.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
