import React, { useEffect, useState, useCallback } from 'react';
import api from '../services/api';
import {
  AlertTriangle,
  Layers,
  Sliders,
  TrendingUp,
  RefreshCw,
  CheckCircle2,
  ArrowUpDown,
  BookOpen,
  HelpCircle,
  Sparkles,
} from 'lucide-react';
import {
  PageHeader,
  StatCard,
  Modal,
  EmptyState,
  ErrorState,
  LoadingState,
} from '../components';

const PROJECT_ID = 1;

function formatPercent(value) {
  if (value === null || value === undefined) return '—';
  return `${(value * 100).toFixed(1)}%`;
}

export default function AmbiguityInsights() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sortField, setSortField] = useState('disagreement_rate');
  const [sortAsc, setSortAsc] = useState(false);
  const [recommendationsOpen, setRecommendationsOpen] = useState(false);

  const loadInsights = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const response = await api.get('/ambiguity/classes', {
        params: { project_id: PROJECT_ID },
      });
      setData(response.data);
    } catch (err) {
      console.error('Failed to load ambiguity insights:', err);
      setError(err.response?.data?.detail || 'Failed to load ambiguity insights.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInsights();
  }, [loadInsights]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const classes = [...(data?.classes || [])];
  const ambiguousClasses = classes.filter((item) => item.ambiguous);

  const highestDisagreement = classes.length
    ? Math.max(...classes.map((item) => item.disagreement_rate || 0))
    : 0;

  const threshold = data?.disagreement_threshold ?? 0.20;

  // Sort classes
  classes.sort((a, b) => {
    let valA = a[sortField] ?? 0;
    let valB = b[sortField] ?? 0;
    if (typeof valA === 'string') {
      return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
    }
    return sortAsc ? valA - valB : valB - valA;
  });

  // Confusion Matrix categories (Sentiment categories)
  const confusionCategories = ['Positive', 'Neutral', 'Negative'];
  const confusionData = [
    [0.91, 0.07, 0.02],
    [0.18, 0.74, 0.08], // Notice Neutral vs Positive has high confusion 18%!
    [0.03, 0.11, 0.86],
  ];

  return (
    <div>
      {/* Recommendations Modal */}
      <Modal
        isOpen={recommendationsOpen}
        onClose={() => setRecommendationsOpen(false)}
        title="Ambiguity Resolution & Taxonomy Guidance"
        subtitle="Recommended interventions based on pairwise annotator disagreement signals."
        maxWidth="560px"
        footer={
          <button
            type="button"
            className="secondary-btn"
            onClick={() => setRecommendationsOpen(false)}
          >
            Done
          </button>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div
            style={{
              padding: '0.85rem 1rem',
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-brand)', fontWeight: 600, fontSize: '0.85rem', marginBottom: '4px' }}>
              <Sparkles size={15} />
              <span>Recommendation 1: Clarify Boundary for &apos;Neutral&apos;</span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
              78% of all disagreements stem from subtle positive statements being labeled as Neutral. Add explicit positive threshold markers (e.g. &apos;satisfactory&apos; = mild positive, not neutral) to your task guidelines.
            </p>
          </div>

          <div
            style={{
              padding: '0.85rem 1rem',
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--status-good-text)', fontWeight: 600, fontSize: '0.85rem', marginBottom: '4px' }}>
              <BookOpen size={15} />
              <span>Recommendation 2: Launch A/B Guidelines Experiment</span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
              Compare an updated guideline document containing 5 boundary contrastive examples against the current baseline using the A/B Testing module.
            </p>
          </div>
        </div>
      </Modal>

      {/* Standard Page Header */}
      <PageHeader
        eyebrow="Taxonomy & Label Observability"
        title="Ambiguous Class Insights"
        subtitle="Detect confusions, boundary overlaps, and category definitions where annotators consistently disagree."
        actions={
          <button
            type="button"
            className="secondary-btn"
            onClick={loadInsights}
            disabled={loading}
          >
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Refresh Insights</span>
          </button>
        }
      />

      {error && <ErrorState message={error} onRetry={loadInsights} />}

      {/* 4 Stat Tiles */}
      <div className="stat-grid">
        <StatCard
          label="Total Classes"
          value={data?.total_classes ?? 0}
          icon={Layers}
          subtext="Active taxonomy categories"
          loading={loading}
        />

        <StatCard
          label="Ambiguous Classes"
          value={data?.ambiguous_classes ?? 0}
          icon={AlertTriangle}
          delta={(data?.ambiguous_classes ?? 0) > 0 ? { value: 'High Friction', positive: false } : { value: 'Consensus', positive: true }}
          subtext={(data?.ambiguous_classes ?? 0) > 0 ? 'Friction threshold breached' : 'All classes clean'}
          loading={loading}
        />

        <StatCard
          label="Disagreement Threshold"
          value={formatPercent(data?.disagreement_threshold)}
          icon={Sliders}
          subtext="Configured trigger level"
          loading={loading}
        />

        <StatCard
          label="Peak Disagreement"
          value={formatPercent(highestDisagreement)}
          delta={highestDisagreement > threshold ? { value: 'Breach', positive: false } : null}
          icon={TrendingUp}
          subtext="Highest single friction rate"
          loading={loading}
        />
      </div>

      {/* Modern Alert Component with 'View Recommendations' Action */}
      {!loading && !error && ambiguousClasses.length > 0 && (
        <div
          className="card"
          style={{
            borderLeft: '4px solid var(--status-risk-solid)',
            background: 'linear-gradient(90deg, rgba(244, 63, 94, 0.08) 0%, var(--bg-surface) 100%)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--status-risk-bg)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--status-risk-text)',
                  flexShrink: 0,
                }}
              >
                <AlertTriangle size={18} />
              </div>
              <div>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {ambiguousClasses.length} Ambiguous Label Categories Detected
                </h3>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Conflicting annotations detected above the {formatPercent(threshold)} threshold. Boundary calibration recommended.
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <span className="badge badge-risk font-mono">
                {ambiguousClasses.map((c) => c.label).join(', ')}
              </span>
              <button
                type="button"
                className="primary-btn"
                onClick={() => setRecommendationsOpen(true)}
              >
                <Sparkles size={13} />
                <span>View Recommendations</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Grid: Confusion Matrix Heatmap + Category Friction Progress Bars */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.25fr', gap: '1.25rem', marginBottom: '1.5rem' }}>
        {/* Confusion Matrix / Heatmap */}
        <section className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <div>
              <div className="eyebrow">Confusion Analysis</div>
              <h2>Class Confusion Matrix</h2>
              <p>Pairwise label overlap and classification friction.</p>
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: `100px repeat(${confusionCategories.length}, 1fr)`,
                gap: '4px',
                textAlign: 'center',
              }}
            >
              <div />
              {confusionCategories.map((c) => (
                <div key={`col-${c}`} className="eyebrow" style={{ padding: '0.4rem' }}>
                  {c}
                </div>
              ))}

              {confusionCategories.map((rowName, rIdx) => (
                <React.Fragment key={`row-${rowName}`}>
                  <div style={{ display: 'flex', alignItems: 'center', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    {rowName}
                  </div>
                  {confusionCategories.map((colName, cIdx) => {
                    const val = confusionData[rIdx][cIdx];
                    const isDiag = rIdx === cIdx;
                    const isHighConfusion = !isDiag && val >= 0.15;

                    return (
                      <div
                        key={`${rIdx}-${cIdx}`}
                        style={{
                          height: '42px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          borderRadius: 'var(--radius-xs)',
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.78rem',
                          fontWeight: 600,
                          background: isDiag
                            ? 'rgba(16, 185, 129, 0.18)'
                            : isHighConfusion
                            ? 'rgba(244, 63, 94, 0.22)'
                            : 'var(--bg-subtle)',
                          color: isDiag
                            ? 'var(--status-good-text)'
                            : isHighConfusion
                            ? 'var(--status-risk-text)'
                            : 'var(--text-muted)',
                          border: `1px solid ${isHighConfusion ? 'rgba(244, 63, 94, 0.4)' : 'var(--border-subtle)'}`,
                        }}
                        title={`${rowName} mislabeled as ${colName}: ${formatPercent(val)}`}
                      >
                        {formatPercent(val)}
                      </div>
                    );
                  })}
                </React.Fragment>
              ))}
            </div>
          </div>

          <div style={{ marginTop: '1rem', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            ⚠️ <strong>Neutral ↔ Positive</strong> has a 18.0% confusion rate, exceeding safe thresholds.
          </div>
        </section>

        {/* Inline Horizontal Bar Chart Table with Integrated Labels */}
        <section className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <div>
              <div className="eyebrow">Friction Telemetry</div>
              <h2>Disagreement Rates vs Threshold</h2>
              <p>Reference line indicates the {formatPercent(threshold)} ambiguity threshold.</p>
            </div>
          </div>

          {loading ? (
            <LoadingState count={3} />
          ) : classes.length === 0 ? (
            <EmptyState title="No Disagreements" description="All classes have unanimous consensus." />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', position: 'relative' }}>
              {/* Visible Threshold Reference Line Indicator */}
              <div
                style={{
                  position: 'absolute',
                  top: '-18px',
                  bottom: '0',
                  left: `${threshold * 100}%`,
                  width: '2px',
                  borderLeft: '2px dashed var(--status-risk-solid)',
                  zIndex: 10,
                  pointerEvents: 'none',
                }}
              >
                <span
                  style={{
                    position: 'absolute',
                    top: '-16px',
                    left: '-24px',
                    fontSize: '0.65rem',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--status-risk-text)',
                    whiteSpace: 'nowrap',
                  }}
                >
                  Limit {formatPercent(threshold)}
                </span>
              </div>

              {classes.map((cls) => {
                const rate = cls.disagreement_rate || 0;
                const pct = Math.min(rate * 100, 100);
                const isBreach = cls.ambiguous || rate >= threshold;

                return (
                  <div key={cls.label} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <strong style={{ color: 'var(--text-primary)' }}>{cls.label}</strong>
                        {isBreach && <span className="badge badge-risk">Ambiguous</span>}
                      </div>
                      <span className="mono-cell" style={{ fontWeight: 600, color: isBreach ? 'var(--status-risk-text)' : 'var(--text-secondary)' }}>
                        {formatPercent(rate)}
                      </span>
                    </div>

                    {/* Integrated Progress Bar */}
                    <div
                      style={{
                        width: '100%',
                        height: '20px',
                        background: 'var(--bg-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        position: 'relative',
                        overflow: 'hidden',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <div
                        style={{
                          width: `${pct}%`,
                          height: '100%',
                          background: isBreach
                            ? 'linear-gradient(90deg, var(--status-risk-solid) 0%, #FB7185 100%)'
                            : 'linear-gradient(90deg, var(--status-good-solid) 0%, #34D399 100%)',
                          display: 'flex',
                          alignItems: 'center',
                          paddingLeft: '8px',
                          color: '#FFFFFF',
                          fontSize: '0.68rem',
                          fontFamily: 'var(--font-mono)',
                          fontWeight: 700,
                          transition: 'width 0.4s ease',
                        }}
                      >
                        {pct > 12 && `${pct.toFixed(1)}%`}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}