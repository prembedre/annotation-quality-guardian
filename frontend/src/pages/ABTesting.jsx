import React, { useEffect, useState, useCallback } from 'react';
import api from '../services/api';
import { GitCompare, RefreshCw, Trophy, Zap } from 'lucide-react';
import { ErrorState, EmptyState, LoadingState } from '../components';

function formatPercent(value) {
  if (value === null || value === undefined) return '—';
  return `${(value * 100).toFixed(1)}%`;
}

function formatNumber(value) {
  if (value === null || value === undefined) return '—';
  return Number(value).toFixed(2);
}

function MetricCard({ label, value, isHighlight = false }) {
  return (
    <div
      style={{
        background: 'var(--bg-subtle)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-sm)',
        padding: '0.85rem 1rem',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <span
        style={{
          fontSize: '0.68rem',
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
          color: 'var(--text-muted)',
          marginBottom: '0.35rem',
        }}
      >
        {label}
      </span>
      <span
        className="mono-cell"
        style={{
          fontSize: '1.25rem',
          fontWeight: 700,
          color: isHighlight ? 'var(--status-good-text)' : 'var(--text-primary)',
        }}
      >
        {value}
      </span>
    </div>
  );
}

function VariantPanel({ title, variant, isWinner }) {
  if (!variant) return null;

  return (
    <div
      className="phase4-ab-variant"
      style={{
        borderColor: isWinner ? 'var(--accent-500)' : 'var(--border-subtle)',
        boxShadow: isWinner ? 'var(--shadow-glow)' : 'var(--shadow-sm)',
      }}
    >
      <div
        className="phase4-ab-variant-header"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            {title}
          </h3>
          {isWinner && (
            <span className="badge badge-good">
              <Trophy size={11} />
              <span>Recommended</span>
            </span>
          )}
        </div>
        <span
          className="mono-cell"
          style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}
        >
          {variant.sample_size} Samples
        </span>
      </div>

      <div className="phase4-ab-metric-grid">
        <MetricCard
          label="Gold Accuracy"
          value={formatPercent(variant.gold_accuracy)}
          isHighlight={isWinner}
        />

        <MetricCard
          label="Gold Correct"
          value={variant.gold_correct ?? '—'}
        />

        <MetricCard
          label="Total Annotations"
          value={variant.total_annotations ?? '—'}
        />

        <MetricCard
          label="Gold Annotations"
          value={variant.gold_annotations ?? '—'}
        />

        <MetricCard
          label="Avg Confidence"
          value={formatNumber(variant.average_confidence)}
        />

        <MetricCard
          label="Avg Duration"
          value={
            variant.average_duration_ms == null
              ? '—'
              : `${Math.round(variant.average_duration_ms)}ms`
          }
        />
      </div>
    </div>
  );
}

export default function ABTesting() {
  const [experiments, setExperiments] = useState([]);
  const [selectedExperimentId, setSelectedExperimentId] = useState('');
  const [results, setResults] = useState(null);

  const [loadingExperiments, setLoadingExperiments] = useState(true);
  const [loadingResults, setLoadingResults] = useState(false);
  const [error, setError] = useState('');

  const loadExperiments = useCallback(async () => {
    try {
      setLoadingExperiments(true);
      setError('');

      const response = await api.get('/ab-testing/experiments');
      const items = response.data?.experiments || [];
      setExperiments(items);

      if (items.length > 0) {
        setSelectedExperimentId(String(items[0].id));
      } else {
        setSelectedExperimentId('');
        setResults(null);
      }
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail || 'Unable to load A/B testing experiments.'
      );
    } finally {
      setLoadingExperiments(false);
    }
  }, []);

  const loadResults = useCallback(async (experimentId) => {
    if (!experimentId) {
      setResults(null);
      return;
    }

    try {
      setLoadingResults(true);
      setError('');

      const response = await api.get(
        `/ab-testing/experiments/${experimentId}/results`
      );
      setResults(response.data);
    } catch (err) {
      console.error(err);
      setResults(null);
      setError(
        err.response?.data?.detail || 'Unable to load A/B testing results.'
      );
    } finally {
      setLoadingResults(false);
    }
  }, []);

  useEffect(() => {
    loadExperiments();
  }, [loadExperiments]);

  useEffect(() => {
    if (selectedExperimentId) {
      loadResults(selectedExperimentId);
    }
  }, [selectedExperimentId, loadResults]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">A/B Testing Experiments</h1>
          <p className="page-subtitle">
            Compare annotation label schemas and guidelines to statistically determine the highest-accuracy variant.
          </p>
        </div>

        <button
          type="button"
          className="secondary-btn"
          onClick={loadExperiments}
          disabled={loadingExperiments}
        >
          <RefreshCw size={14} className={loadingExperiments ? 'spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {error && <ErrorState message={error} onRetry={loadExperiments} />}

      {/* Experiment Selector Bar */}
      {!error && (
        <div className="card">
          <div className="card-header" style={{ marginBottom: 0 }}>
            <div style={{ flex: '1 1 300px' }}>
              <h2>Select Active Experiment</h2>
              <p>Choose an experiment run to evaluate variant performance.</p>
            </div>

            <div style={{ minWidth: '240px' }}>
              {loadingExperiments ? (
                <div className="skeleton-row" style={{ height: '38px' }} />
              ) : experiments.length === 0 ? (
                <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  No active experiments found.
                </span>
              ) : (
                <select
                  id="ab-experiment"
                  value={selectedExperimentId}
                  onChange={(e) => setSelectedExperimentId(e.target.value)}
                >
                  {experiments.map((exp) => (
                    <option key={exp.id} value={exp.id}>
                      {exp.experiment_name} (ID #{exp.id})
                    </option>
                  ))}
                </select>
              )}
            </div>
          </div>
        </div>
      )}

      {!error && (
        <>
          {loadingExperiments ? (
            <div className="card">
              <LoadingState count={3} />
            </div>
          ) : experiments.length === 0 ? (
            <div className="card">
              <EmptyState
                icon={GitCompare}
                type="neutral"
                title="No A/B Experiments Created"
                description="Compare two annotation prompt variations, UI schema changes, or labeling instructions to determine which produces superior quality data."
              />
            </div>
          ) : loadingResults ? (
            <div className="card">
              <LoadingState count={3} />
            </div>
          ) : results ? (
            <>
              {/* Side by Side Variants */}
              <div className="phase4-ab-grid">
                <VariantPanel
                  title="Variant A"
                  variant={results.variant_a}
                  isWinner={results.recommended_variant === 'Variant A'}
                />

                <VariantPanel
                  title="Variant B"
                  variant={results.variant_b}
                  isWinner={results.recommended_variant === 'Variant B'}
                />
              </div>

              {/* Recommendation Banner */}
              <div className="card">
                <div className="card-header">
                  <div>
                    <h2>Engine Recommendation</h2>
                    <p>
                      Statistical comparison based on gold-standard accuracy and annotator consensus.
                    </p>
                  </div>
                  <span className="badge badge-info">{results.status}</span>
                </div>

                <div className="phase4-recommendation">
                  <div>
                    <div className="phase4-recommendation-label">Winner Variant</div>
                    <div
                      className="phase4-recommendation-value"
                      style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                    >
                      <Trophy size={20} style={{ color: 'var(--status-good-solid)' }} />
                      <span>{results.recommended_variant || 'Inconclusive'}</span>
                    </div>
                  </div>

                  <div>
                    <div className="phase4-recommendation-label">Accuracy Delta</div>
                    <div className="phase4-recommendation-value">
                      +{formatPercent(results.accuracy_difference)}
                    </div>
                  </div>

                  <div
                    style={{
                      background: 'var(--bg-surface)',
                      padding: '1rem',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.4rem',
                        fontSize: '0.72rem',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        color: 'var(--accent-600)',
                        marginBottom: '0.35rem',
                      }}
                    >
                      <Zap size={13} />
                      <span>Decision Rationale</span>
                    </div>
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                      {results.recommendation_reason ||
                        'Sufficient statistical significance has not yet been achieved.'}
                    </p>
                  </div>
                </div>
              </div>
            </>
          ) : null}
        </>
      )}
    </div>
  );
}