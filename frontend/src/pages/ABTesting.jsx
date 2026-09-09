import { useEffect, useState } from 'react';
import api from '../services/api';

function formatPercent(value) {
  if (value === null || value === undefined) {
    return '—';
  }

  return `${(value * 100).toFixed(1)}%`;
}

function formatNumber(value) {
  if (value === null || value === undefined) {
    return '—';
  }

  return Number(value).toFixed(2);
}

function MetricCard({ label, value }) {
  return (
    <div className="phase4-metric-card">
      <div className="phase4-metric-label">{label}</div>
      <div className="phase4-metric-value">{value}</div>
    </div>
  );
}

function VariantPanel({ title, variant }) {
  return (
    <div className="phase4-ab-variant">
      <div className="phase4-ab-variant-header">
        <h3>{title}</h3>
      </div>

      <div className="phase4-ab-metrics">
        <MetricCard
          label="Total Annotations"
          value={variant.total_annotations}
        />

        <MetricCard
          label="Gold Annotations"
          value={variant.gold_annotations}
        />

        <MetricCard
          label="Gold Correct"
          value={variant.gold_correct}
        />

        <MetricCard
          label="Accuracy"
          value={formatPercent(variant.accuracy)}
        />

        <MetricCard
          label="Avg. Confidence"
          value={formatNumber(variant.average_confidence)}
        />

        <MetricCard
          label="Avg. Duration"
          value={
            variant.average_duration_ms === null ||
            variant.average_duration_ms === undefined
              ? '—'
              : `${Math.round(variant.average_duration_ms)} ms`
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

  async function loadExperiments() {
    try {
      setLoadingExperiments(true);
      setError('');

      const response = await api.get('/ab-testing/experiments');

      const data = response.data;
      const items = data.experiments || [];

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
        err.response?.data?.detail ||
          'Unable to load A/B testing experiments.'
      );
    } finally {
      setLoadingExperiments(false);
    }
  }

  async function loadResults(experimentId) {
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
        err.response?.data?.detail ||
          'Unable to load A/B testing results.'
      );
    } finally {
      setLoadingResults(false);
    }
  }

  useEffect(() => {
    loadExperiments();
  }, []);

  useEffect(() => {
    if (selectedExperimentId) {
      loadResults(selectedExperimentId);
    }
  }, [selectedExperimentId]);

  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <h1>A/B Testing</h1>
          <p>
            Compare label schema variants and identify which version
            performs better.
          </p>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      <section className="phase4-card">
        <div className="phase4-card-header">
          <div>
            <h2>Experiments</h2>
            <p>
              Select an experiment to view its latest analysis.
            </p>
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={loadExperiments}
            disabled={loadingExperiments}
          >
            {loadingExperiments ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {loadingExperiments ? (
          <div className="phase4-empty-state">
            Loading experiments...
          </div>
        ) : experiments.length === 0 ? (
          <div className="phase4-empty-state">
            No A/B testing experiments have been created yet.
          </div>
        ) : (
          <div className="phase4-experiment-selector">
            <label htmlFor="ab-experiment">
              Experiment
            </label>

            <select
              id="ab-experiment"
              value={selectedExperimentId}
              onChange={(event) =>
                setSelectedExperimentId(event.target.value)
              }
            >
              {experiments.map((experiment) => (
                <option
                  key={experiment.id}
                  value={experiment.id}
                >
                  {experiment.experiment_name}
                </option>
              ))}
            </select>
          </div>
        )}
      </section>

      {loadingResults && (
        <section className="phase4-card">
          <div className="phase4-empty-state">
            Loading experiment results...
          </div>
        </section>
      )}

      {results && !loadingResults && (
        <>
          <section className="phase4-card">
            <div className="phase4-card-header">
              <div>
                <h2>{results.experiment_name}</h2>
                <p>
                  Experiment ID: {results.experiment_id}
                </p>
              </div>

              <span className="phase4-status-badge">
                {results.status}
              </span>
            </div>
          </section>

          <div className="phase4-ab-grid">
            <VariantPanel
              title="Variant A"
              variant={results.variant_a}
            />

            <VariantPanel
              title="Variant B"
              variant={results.variant_b}
            />
          </div>

          <section className="phase4-card">
            <div className="phase4-card-header">
              <div>
                <h2>Recommendation</h2>
                <p>
                  The scoring engine compares gold-standard accuracy
                  between the two schema variants.
                </p>
              </div>
            </div>

            <div className="phase4-recommendation">
              <div>
                <div className="phase4-recommendation-label">
                  Recommended Variant
                </div>

                <div className="phase4-recommendation-value">
                  {results.recommended_variant || 'Insufficient data'}
                </div>
              </div>

              <div>
                <div className="phase4-recommendation-label">
                  Accuracy Difference
                </div>

                <div className="phase4-recommendation-value">
                  {formatPercent(results.accuracy_difference)}
                </div>
              </div>

              <div className="phase4-recommendation-reason">
                <strong>Reason</strong>
                <p>
                  {results.recommendation_reason ||
                    'No recommendation is currently available.'}
                </p>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}