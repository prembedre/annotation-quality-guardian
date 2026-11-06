import React, { useEffect, useState, useCallback } from 'react';
import api from '../services/api';
import {
  GitCompare,
  RefreshCw,
  Trophy,
  Zap,
  CheckCircle2,
  AlertTriangle,
  ArrowUpRight,
  Split,
  Sparkles,
  BarChart3,
  Plus,
} from 'lucide-react';
import {
  PageHeader,
  StatCard,
  EmptyState,
  ErrorState,
  LoadingState,
  Modal,
  useToast,
  useProject,
} from '../components';

function formatPercent(value) {
  if (value === null || value === undefined) return '—';
  return `${(value * 100).toFixed(1)}%`;
}

function formatDuration(value) {
  if (value === null || value === undefined) return '—';
  if (value >= 1000) return `${(value / 1000).toFixed(2)}s`;
  return `${Math.round(value)}ms`;
}

// Split Path Illustration SVG
function SplitPathGraphic() {
  return (
    <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
      <path
        d="M40 70V42M40 42C40 32 20 30 20 16M40 42C40 32 60 30 60 16"
        stroke="var(--accent-brand)"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <circle cx="20" cy="16" r="6" fill="#10B981" />
      <circle cx="60" cy="16" r="6" fill="#0EA5E9" />
      <circle cx="40" cy="70" r="5" fill="var(--text-muted)" />
    </svg>
  );
}

export default function ABTesting() {
  const { projectId } = useProject();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { success, error: toastError } = useToast();

  // Create Modal State
  const [showModal, setShowModal] = useState(false);
  const [newTestName, setNewTestName] = useState('');
  const [descA, setDescA] = useState('');
  const [descB, setDescB] = useState('');
  const [allocation, setAllocation] = useState('SPLIT_50_50');
  const [submittingTest, setSubmittingTest] = useState(false);
  const [promoting, setPromoting] = useState(false);

  const loadData = useCallback(async () => {
    if (!projectId) {
      setData(null);
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      setError('');
      const response = await api.get('/ab-testing/experiments', {
        params: { project_id: projectId },
      });
      const experiments = response.data?.experiments || [];
      if (experiments.length > 0) {
        try {
          const resultsRes = await api.get(`/ab-testing/experiments/${experiments[0].id}/results`);
          setData({ ...experiments[0], ...resultsRes.data });
        } catch {
          setData(experiments[0]);
        }
      } else {
        setData(null);
      }
    } catch (err) {
      console.error('Failed to load active A/B test:', err);
      setError(err.response?.data?.detail || 'Failed to load A/B testing experiment.');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateTest = async (e) => {
    e.preventDefault();
    if (!newTestName.trim() || !projectId) return;

    try {
      setSubmittingTest(true);
      await api.post('/ab-testing/experiments', {
        project_id: projectId,
        experiment_name: newTestName.trim(),
        schema_version_a: { description: descA.trim() || 'Control guidelines baseline' },
        schema_version_b: { description: descB.trim() || 'Variant instructions with contrast examples' },
        annotator_group: { allocation: allocation },
        assigned_version: allocation,
        status: 'active',
      });
      success(`A/B experiment "${newTestName.trim()}" started successfully!`);
      setShowModal(false);
      setNewTestName('');
      setDescA('');
      setDescB('');
      loadData();
    } catch (err) {
      console.error('Failed to create experiment:', err);
      toastError(err.response?.data?.detail || 'Failed to start A/B testing experiment.');
    } finally {
      setSubmittingTest(false);
    }
  };

  const handlePromoteVariantB = async () => {
    const expId = data?.experiment_id || data?.id;
    if (!expId) return;

    try {
      setPromoting(true);
      await api.post(`/ab-testing/experiments/${expId}/promote?variant=B`);
      success('Variant B successfully promoted to production! Schema and guidelines updated.');
      loadData();
    } catch (err) {
      console.error('Failed to promote Variant B:', err);
      toastError(err.response?.data?.detail || 'Failed to promote Variant B.');
    } finally {
      setPromoting(false);
    }
  };

  if (!projectId) {
    return (
      <div>
        <PageHeader
          eyebrow="Guideline Optimization & Experimentation"
          title="A/B Guidelines Testing"
          subtitle="Evaluate annotation accuracy improvements when revising labeling instructions and definitions."
        />
        <EmptyState
          title="No Project Selected"
          description="Please select or create a project from the sidebar to inspect A/B guideline tests."
        />
      </div>
    );
  }

  const expName = data?.experiment_name || data?.name || 'A/B Guideline Trial';
  const isCompleted = data?.status === 'completed';
  const variantA = data?.variant_a || {};
  const variantB = data?.variant_b || {};
  const samplesA = variantA.total_annotations ?? variantA.sample_size ?? 0;
  const samplesB = variantB.total_annotations ?? variantB.sample_size ?? 0;
  const totalSamples = samplesA + samplesB;
  const accA = variantA.accuracy ?? variantA.gold_accuracy;
  const accB = variantB.accuracy ?? variantB.gold_accuracy;
  const diffVal = data?.accuracy_difference != null ? data.accuracy_difference : (accB != null && accA != null ? accB - accA : null);
  const isWinnerB = data?.recommended_variant === 'B' || (diffVal != null && diffVal > 0);

  return (
    <div>
      {/* Create Experiment Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Start New Guideline A/B Test"
        subtitle="Split annotators randomly across guideline variants to measure accuracy improvement."
        maxWidth="540px"
        footer={
          <>
            <button
              type="button"
              className="secondary-btn"
              onClick={() => setShowModal(false)}
              disabled={submittingTest}
            >
              Cancel
            </button>
            <button
              type="button"
              className="primary-btn"
              onClick={handleCreateTest}
              disabled={submittingTest || !newTestName.trim()}
            >
              {submittingTest ? 'Launching...' : 'Launch Experiment'}
            </button>
          </>
        }
      >
        <form onSubmit={handleCreateTest} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
              Experiment Name *
            </label>
            <input
              type="text"
              className="settings-input"
              placeholder="e.g. Contrastive Edge-Case Guidelines v2"
              value={newTestName}
              onChange={(e) => setNewTestName(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
              Variant A (Control Instructions)
            </label>
            <input
              type="text"
              className="settings-input"
              placeholder="Baseline production instructions"
              value={descA}
              onChange={(e) => setDescA(e.target.value)}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
              Variant B (Treatment Guidelines)
            </label>
            <input
              type="text"
              className="settings-input"
              placeholder="Revised instructions with boundary contrast examples"
              value={descB}
              onChange={(e) => setDescB(e.target.value)}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
              Traffic Allocation
            </label>
            <select
              className="settings-input"
              value={allocation}
              onChange={(e) => setAllocation(e.target.value)}
            >
              <option value="SPLIT_50_50">50% Variant A / 50% Variant B (Recommended)</option>
              <option value="A">100% Variant A (Control)</option>
              <option value="B">100% Variant B (Treatment)</option>
            </select>
          </div>
        </form>
      </Modal>

      {/* Standard Page Header */}
      <PageHeader
        eyebrow="Guideline Optimization & Experimentation"
        title="A/B Guidelines Testing"
        subtitle="Evaluate annotation accuracy improvements when revising labeling instructions and definitions."
        actions={
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <button
              type="button"
              className="secondary-btn"
              onClick={loadData}
              disabled={loading}
            >
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
              <span>Refresh</span>
            </button>
            <button
              type="button"
              className="primary-btn"
              onClick={() => setShowModal(true)}
            >
              <Plus size={14} />
              <span>Start New Test</span>
            </button>
          </div>
        }
      />

      {error && <ErrorState message={error} onRetry={loadData} />}

      {loading ? (
        <div className="card">
          <LoadingState count={4} />
        </div>
      ) : !data ? (
        <div className="card">
          <EmptyState
            icon={Split}
            eyebrow="Split Experiments"
            title="No Active A/B Testing Experiment"
            description="Launch a randomized split-guideline trial to measure if new instructions improve annotator agreement."
            actionLabel="Start New Guideline Test"
            onAction={() => setShowModal(true)}
          >
            <div style={{ margin: '1rem 0' }}>
              <SplitPathGraphic />
            </div>
          </EmptyState>
        </div>
      ) : (
        <div>
          {/* Winner Declaration Banner once Promoted or Recommended */}
          {isWinnerB && (
            <div
              className="card"
              style={{
                borderLeft: '4px solid var(--status-good-solid)',
                background: 'linear-gradient(90deg, rgba(16, 185, 129, 0.1) 0%, var(--bg-surface) 100%)',
                marginBottom: '1.5rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                  <div
                    style={{
                      width: '38px',
                      height: '38px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'var(--status-good-bg)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--status-good-text)',
                      flexShrink: 0,
                    }}
                  >
                    <Trophy size={20} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {isCompleted ? 'Variant B Promoted to Production!' : 'Variant B Outperformed Baseline!'}
                    </h3>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {data.recommendation_reason || `Achieved accuracy difference of ${diffVal != null ? (diffVal * 100).toFixed(1) + '%' : 'uplift'} over control.`}
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <span className="badge badge-good font-mono">
                    <CheckCircle2 size={12} />
                    <span>{isCompleted ? 'Promoted & Active' : 'Recommended'}</span>
                  </span>
                  {!isCompleted && (
                    <button
                      type="button"
                      className="primary-btn"
                      onClick={handlePromoteVariantB}
                      disabled={promoting}
                    >
                      <Sparkles size={13} />
                      <span>{promoting ? 'Promoting...' : 'Promote Variant B to Production'}</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Sample Size Progress Card */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <div>
                <span className="eyebrow">{expName}</span>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {totalSamples} total annotations evaluated across variants
                </div>
              </div>
              <span className="mono-cell badge badge-info">
                Status: {data.status?.toUpperCase() || 'ACTIVE'}
              </span>
            </div>
          </div>

          {/* Two-Column Variant Comparison Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.25rem' }}>
            {/* Variant A (Control) */}
            <div className="card" style={{ marginBottom: 0 }}>
              <div className="card-header">
                <div>
                  <span className="eyebrow">Control Baseline</span>
                  <h2>Variant A (Control)</h2>
                  <p>{data.schema_version_a?.description || 'Baseline production labeling instructions.'}</p>
                </div>
                <span className="mono-cell badge badge-neutral">{samplesA} Samples</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div className="eyebrow">Gold Accuracy</div>
                  <div className="mono-cell" style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                    {formatPercent(accA)}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div className="eyebrow">Confidence</div>
                  <div className="mono-cell" style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                    {formatPercent(variantA.average_confidence)}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div className="eyebrow">Avg Duration</div>
                  <div className="mono-cell" style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-secondary)', marginTop: '2px' }}>
                    {formatDuration(variantA.average_duration_ms)}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div className="eyebrow">Status</div>
                  <div style={{ fontWeight: 600, color: 'var(--text-muted)', marginTop: '4px' }}>
                    Baseline
                  </div>
                </div>
              </div>
            </div>

            {/* Variant B (Treatment / Winner) */}
            <div
              className="card"
              style={{
                marginBottom: 0,
                borderColor: isWinnerB ? 'var(--status-good-solid)' : 'var(--border-medium)',
                boxShadow: isWinnerB ? 'var(--shadow-glow)' : 'none',
              }}
            >
              <div className="card-header">
                <div>
                  <span className="eyebrow" style={{ color: isWinnerB ? 'var(--status-good-text)' : 'var(--accent-brand)' }}>
                    {isWinnerB ? 'Recommended Winner' : 'Treatment Variant'}
                  </span>
                  <h2>Variant B (Treatment)</h2>
                  <p>{data.schema_version_b?.description || 'Modified guidelines with contrastive examples.'}</p>
                </div>
                {isWinnerB ? (
                  <span className="badge badge-good">
                    <Trophy size={12} />
                    <span>WINNER</span>
                  </span>
                ) : (
                  <span className="mono-cell badge badge-neutral">{samplesB} Samples</span>
                )}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div style={{ background: isWinnerB ? 'var(--status-good-bg)' : 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: isWinnerB ? '1px solid var(--status-good-border)' : '1px solid var(--border-subtle)' }}>
                  <div className="eyebrow" style={{ color: isWinnerB ? 'var(--status-good-text)' : 'inherit' }}>Gold Accuracy</div>
                  <div className="mono-cell" style={{ fontSize: '1.5rem', fontWeight: 700, color: isWinnerB ? 'var(--status-good-text)' : 'var(--text-primary)', marginTop: '2px' }}>
                    {formatPercent(accB)}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div className="eyebrow">Confidence</div>
                  <div className="mono-cell" style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                    {formatPercent(variantB.average_confidence)}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div className="eyebrow">Avg Duration</div>
                  <div className="mono-cell" style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                    {formatDuration(variantB.average_duration_ms)}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div className="eyebrow">Accuracy Uplift</div>
                  <div className="mono-cell" style={{ fontSize: '1.2rem', fontWeight: 700, color: diffVal != null && diffVal > 0 ? 'var(--status-good-text)' : 'var(--text-primary)', marginTop: '2px' }}>
                    {diffVal != null ? `${diffVal > 0 ? '+' : ''}${(diffVal * 100).toFixed(1)}%` : '—'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
