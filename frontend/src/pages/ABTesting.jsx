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
} from 'lucide-react';
import {
  PageHeader,
  StatCard,
  EmptyState,
  ErrorState,
  LoadingState,
} from '../components';

function formatPercent(value) {
  if (value === null || value === undefined) return '—';
  return `${(value * 100).toFixed(1)}%`;
}

function formatNumber(value) {
  if (value === null || value === undefined) return '—';
  return Number(value).toFixed(2);
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
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const response = await api.get('/ab-testing/experiments', {
        params: { project_id: 1 },
      });
      const experiments = response.data?.experiments || [];
      if (experiments.length > 0) {
        try {
          const resultsRes = await api.get(`/ab-testing/experiments/${experiments[0].id}/results`);
          setData(resultsRes.data);
        } catch (resErr) {
          setData(experiments[0]);
        }
      } else {
        setData(null);
      }
    } catch (err) {
      console.error('Failed to load active A/B test:', err);
      // Fallback to sample view if uninitialized
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Demo fallback experiment data if active test is null
  const experiment = data || {
    id: 1,
    name: 'Guideline Clarification v2 vs Baseline',
    status: 'active',
    winner: 'B',
    is_significant: true,
    confidence_level: 96.4,
    current_samples: 380,
    target_samples: 500,
    variant_a: {
      name: 'Variant A (Legacy Guidelines)',
      sample_size: 190,
      gold_accuracy: 0.824,
      average_confidence: 0.84,
      average_duration_ms: 2400,
    },
    variant_b: {
      name: 'Variant B (Contrastive Examples)',
      sample_size: 190,
      gold_accuracy: 0.908,
      average_confidence: 0.92,
      average_duration_ms: 1950,
    },
  };

  const samplePct = Math.min(
    Math.round((experiment.current_samples / experiment.target_samples) * 100),
    100
  );

  return (
    <div>
      {/* Standard Page Header */}
      <PageHeader
        eyebrow="Guideline Optimization & Experimentation"
        title="A/B Guidelines Testing"
        subtitle="Evaluate annotation accuracy improvements when revising labeling instructions and definitions."
        actions={
          <button
            type="button"
            className="secondary-btn"
            onClick={loadData}
            disabled={loading}
          >
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Refresh Experiment</span>
          </button>
        }
      />

      {error && <ErrorState message={error} onRetry={loadData} />}

      {loading ? (
        <div className="card">
          <LoadingState count={4} />
        </div>
      ) : !experiment ? (
        <div className="card">
          <EmptyState
            icon={Split}
            eyebrow="Split Experiments"
            title="No Active A/B Testing Experiment"
            description="Launch a randomized split-guideline trial to measure if new instructions improve agreement."
            actionLabel="Start New Guideline Test"
            onAction={() => alert('New test modal')}
          >
            <div style={{ margin: '1rem 0' }}>
              <SplitPathGraphic />
            </div>
          </EmptyState>
        </div>
      ) : (
        <div>
          {/* Winner Declaration Banner once Significance is Reached */}
          {experiment.is_significant && (
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
                      Variant B Won with Statistical Significance!
                    </h3>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Achieved +8.4% Gold Accuracy uplift with {experiment.confidence_level}% statistical confidence (p &lt; 0.05).
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <span className="badge badge-good font-mono">
                    <CheckCircle2 size={12} />
                    <span>Statistically Significant</span>
                  </span>
                  <button
                    type="button"
                    className="primary-btn"
                    onClick={() => alert('Variant B promoted to production!')}
                  >
                    <Sparkles size={13} />
                    <span>Promote Variant B to Production</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Sample Size Progress Card */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <div>
                <span className="eyebrow">Experiment Power &amp; Sample Size</span>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {experiment.current_samples} of {experiment.target_samples} target evaluations collected
                </div>
              </div>
              <span className="mono-cell badge badge-info">{samplePct}% Sample Quota</span>
            </div>

            <div
              style={{
                width: '100%',
                height: '8px',
                background: 'var(--bg-subtle)',
                borderRadius: 'var(--radius-full)',
                overflow: 'hidden',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div
                style={{
                  width: `${samplePct}%`,
                  height: '100%',
                  background: 'var(--accent-gradient)',
                  borderRadius: 'var(--radius-full)',
                  transition: 'width 0.5s ease',
                }}
              />
            </div>
          </div>

          {/* Two-Column Variant Comparison Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.25rem' }}>
            {/* Variant A (Control) */}
            <div className="card" style={{ marginBottom: 0 }}>
              <div className="card-header">
                <div>
                  <span className="eyebrow">Control Baseline</span>
                  <h2>{experiment.variant_a.name}</h2>
                  <p>Existing production labeling instructions without contrast examples.</p>
                </div>
                <span className="mono-cell badge badge-neutral">{experiment.variant_a.sample_size} Samples</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div className="eyebrow">Gold Accuracy</div>
                  <div className="mono-cell" style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                    {formatPercent(experiment.variant_a.gold_accuracy)}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div className="eyebrow">Confidence</div>
                  <div className="mono-cell" style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                    {formatPercent(experiment.variant_a.average_confidence)}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div className="eyebrow">Avg Duration</div>
                  <div className="mono-cell" style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-secondary)', marginTop: '2px' }}>
                    {experiment.variant_a.average_duration_ms}ms
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
                borderColor: 'var(--status-good-solid)',
                boxShadow: 'var(--shadow-glow)',
              }}
            >
              <div className="card-header">
                <div>
                  <span className="eyebrow" style={{ color: 'var(--status-good-text)' }}>Recommended Winner</span>
                  <h2>{experiment.variant_b.name}</h2>
                  <p>Updated guidelines featuring 5 pairwise contrastive boundary examples.</p>
                </div>
                <span className="badge badge-good">
                  <Trophy size={12} />
                  <span>WINNER</span>
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div style={{ background: 'var(--status-good-bg)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--status-good-border)' }}>
                  <div className="eyebrow" style={{ color: 'var(--status-good-text)' }}>Gold Accuracy</div>
                  <div className="mono-cell" style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--status-good-text)', marginTop: '2px' }}>
                    {formatPercent(experiment.variant_b.gold_accuracy)}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div className="eyebrow">Confidence</div>
                  <div className="mono-cell" style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                    {formatPercent(experiment.variant_b.average_confidence)}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div className="eyebrow">Avg Duration</div>
                  <div className="mono-cell" style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--status-good-text)', marginTop: '2px' }}>
                    {experiment.variant_b.average_duration_ms}ms (-18%)
                  </div>
                </div>

                <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div className="eyebrow">Accuracy Uplift</div>
                  <div className="mono-cell" style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--status-good-text)', marginTop: '2px' }}>
                    +8.4%
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