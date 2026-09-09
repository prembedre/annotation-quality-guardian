import React, { useEffect, useState } from 'react';
import api from '../services/api';

const PROJECT_ID = 1;

function formatPercent(value) {
  if (value === null || value === undefined) {
    return '—';
  }

  return `${(value * 100).toFixed(1)}%`;
}

function AmbiguityInsights() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function loadInsights() {
    setLoading(true);
    setError('');

    try {
      const response = await api.get('/ambiguity/classes', {
        params: {
          project_id: PROJECT_ID,
        },
      });

      setData(response.data);
    } catch (err) {
      console.error('Failed to load ambiguity insights:', err);
      setError(
        err.response?.data?.detail ||
          'Failed to load ambiguity insights.'
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadInsights();
  }, []);

  if (loading) {
    return (
      <div className="page">
        <div className="page-header">
          <div>
            <h2>Ambiguous Class Insights</h2>
            <p>
              Identify labels with high disagreement between annotators.
            </p>
          </div>
        </div>

        <div className="phase4-card">
          <div className="phase4-empty-state">
            Loading ambiguity insights...
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="page-header">
          <div>
            <h2>Ambiguous Class Insights</h2>
            <p>
              Identify labels with high disagreement between annotators.
            </p>
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={loadInsights}
          >
            Retry
          </button>
        </div>

        <div className="error-banner">
          {error}
        </div>
      </div>
    );
  }

  const classes = data?.classes || [];
  const ambiguousClasses = classes.filter(
    (item) => item.ambiguous
  );

  const highestDisagreement = classes.length
    ? Math.max(
        ...classes.map(
          (item) => item.disagreement_rate || 0
        )
      )
    : 0;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2>Ambiguous Class Insights</h2>
          <p>
            Identify labels where annotators frequently disagree.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={loadInsights}
        >
          Refresh
        </button>
      </div>

      {/* Summary cards */}
      <div className="phase4-summary-grid">
        <div className="phase4-card phase4-summary-card">
          <div className="phase4-metric-label">
            Total Classes
          </div>

          <div className="phase4-metric-value">
            {data?.total_classes ?? 0}
          </div>
        </div>

        <div className="phase4-card phase4-summary-card">
          <div className="phase4-metric-label">
            Ambiguous Classes
          </div>

          <div className="phase4-metric-value">
            {data?.ambiguous_classes ?? 0}
          </div>
        </div>

        <div className="phase4-card phase4-summary-card">
          <div className="phase4-metric-label">
            Disagreement Threshold
          </div>

          <div className="phase4-metric-value">
            {formatPercent(data?.disagreement_threshold)}
          </div>
        </div>

        <div className="phase4-card phase4-summary-card">
          <div className="phase4-metric-label">
            Highest Disagreement
          </div>

          <div className="phase4-metric-value">
            {formatPercent(highestDisagreement)}
          </div>
        </div>
      </div>

      {/* Ambiguous classes callout */}
      <div className="phase4-card ambiguity-callout">
        <div className="phase4-card-header">
          <div>
            <h3>Ambiguity Summary</h3>
            <p>
              Classes are considered ambiguous when their disagreement
              rate reaches the configured threshold and they have enough
              comparisons.
            </p>
          </div>

          <span className="phase4-status-badge">
            {ambiguousClasses.length} flagged
          </span>
        </div>

        {ambiguousClasses.length === 0 ? (
          <div className="phase4-empty-state">
            No ambiguous classes were detected.
          </div>
        ) : (
          <div className="ambiguity-callout-list">
            {ambiguousClasses.map((item) => (
              <div
                key={item.label}
                className="ambiguity-callout-item"
              >
                <strong>{item.label}</strong>

                <span>
                  {formatPercent(item.disagreement_rate)} disagreement
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Disagreement chart */}
      <div className="phase4-card">
        <div className="phase4-card-header">
          <div>
            <h3>Disagreement by Class</h3>
            <p>
              Higher disagreement indicates a class may need clearer
              labeling guidance.
            </p>
          </div>
        </div>

        <div className="ambiguity-chart">
          {classes.map((item) => {
            const percentage =
              (item.disagreement_rate || 0) * 100;

            return (
              <div
                className="ambiguity-chart-row"
                key={item.label}
              >
                <div className="ambiguity-chart-label">
                  <span>{item.label}</span>

                  {item.ambiguous && (
                    <span className="ambiguity-warning">
                      Ambiguous
                    </span>
                  )}
                </div>

                <div className="ambiguity-chart-track">
                  <div
                    className="ambiguity-chart-bar"
                    style={{
                      width: `${Math.min(
                        percentage,
                        100
                      )}%`,
                    }}
                  />
                </div>

                <div className="ambiguity-chart-value">
                  {formatPercent(item.disagreement_rate)}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Detailed table */}
      <div className="phase4-card">
        <div className="phase4-card-header">
          <div>
            <h3>Class Details</h3>
            <p>
              Detailed disagreement statistics for each label.
            </p>
          </div>
        </div>

        {classes.length === 0 ? (
          <div className="phase4-empty-state">
            No class disagreement data is available.
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Class</th>
                  <th>Disagreements</th>
                  <th>Occurrences</th>
                  <th>Comparisons</th>
                  <th>Disagreement Rate</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {classes.map((item) => (
                  <tr key={item.label}>
                    <td>
                      <strong>{item.label}</strong>
                    </td>

                    <td>
                      {item.disagreements}
                    </td>

                    <td>
                      {item.occurrences}
                    </td>

                    <td>
                      {item.total_comparisons}
                    </td>

                    <td>
                      {formatPercent(
                        item.disagreement_rate
                      )}
                    </td>

                    <td>
                      {item.ambiguous ? (
                        <span className="ambiguity-badge ambiguity-badge-warning">
                          Ambiguous
                        </span>
                      ) : (
                        <span className="ambiguity-badge ambiguity-badge-ok">
                          Clear
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default AmbiguityInsights;