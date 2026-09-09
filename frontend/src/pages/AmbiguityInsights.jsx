import React, { useEffect, useState } from 'react';
import api from '../services/api';
import {
  AlertTriangle,
  Layers,
  Sliders,
  TrendingUp,
  RefreshCw,
  CheckCircle2,
  AlertOctagon,
  ArrowUpDown,
} from 'lucide-react';

const PROJECT_ID = 1;

function formatPercent(value) {
  if (value === null || value === undefined) return '—';
  return `${(value * 100).toFixed(1)}%`;
}

function AmbiguityInsights() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sortField, setSortField] = useState('disagreement_rate');
  const [sortAsc, setSortAsc] = useState(false);

  async function loadInsights() {
    setLoading(true);
    setError('');

    try {
      const response = await api.get('/ambiguity/classes', {
        params: { project_id: PROJECT_ID },
      });
      setData(response.data);
    } catch (err) {
      console.error('Failed to load ambiguity insights:', err);
      setError(
        err.response?.data?.detail || 'Failed to load ambiguity insights.'
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadInsights();
  }, []);

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

  // Sort classes
  classes.sort((a, b) => {
    let valA = a[sortField] ?? 0;
    let valB = b[sortField] ?? 0;
    if (typeof valA === 'string') {
      return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
    }
    return sortAsc ? valA - valB : valB - valA;
  });

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Ambiguous Class Insights</h1>
          <p className="page-subtitle">
            Detect confusions and boundary overlaps between label definitions where annotators consistently disagree.
          </p>
        </div>

        <button
          type="button"
          className="secondary-btn"
          onClick={loadInsights}
          disabled={loading}
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          <span>Refresh Insights</span>
        </button>
      </div>

      {error && (
        <div className="alert">
          <AlertOctagon size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* 4 Standardized Stat Tiles */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-label">Total Classes</span>
            <div className="stat-icon">
              <Layers size={16} />
            </div>
          </div>
          <div className="stat-value">{data?.total_classes ?? 0}</div>
          <div className="stat-subtext">Active categories evaluated</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-label">Ambiguous Classes</span>
            <div
              className="stat-icon"
              style={{
                background:
                  (data?.ambiguous_classes ?? 0) > 0
                    ? 'var(--status-risk-bg)'
                    : 'var(--status-good-bg)',
                color:
                  (data?.ambiguous_classes ?? 0) > 0
                    ? 'var(--status-risk-text)'
                    : 'var(--status-good-text)',
              }}
            >
              <AlertTriangle size={16} />
            </div>
          </div>
          <div className="stat-value">{data?.ambiguous_classes ?? 0}</div>
          <div className="stat-subtext">
            {(data?.ambiguous_classes ?? 0) > 0 ? (
              <span className="badge badge-risk">High Friction</span>
            ) : (
              <span className="badge badge-good">High Consensus</span>
            )}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-label">Disagreement Threshold</span>
            <div className="stat-icon">
              <Sliders size={16} />
            </div>
          </div>
          <div className="stat-value">
            {formatPercent(data?.disagreement_threshold)}
          </div>
          <div className="stat-subtext">Trigger level for ambiguity flag</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-label">Peak Disagreement</span>
            <div className="stat-icon">
              <TrendingUp size={16} />
            </div>
          </div>
          <div className="stat-value">
            {formatPercent(highestDisagreement)}
          </div>
          <div className="stat-subtext">Highest category disagreement</div>
        </div>
      </div>

      {/* Visually Striking Ambiguity Alert Callout */}
      {ambiguousClasses.length > 0 && (
        <div
          className="card"
          style={{
            borderLeft: '4px solid var(--status-risk-solid)',
            background: 'linear-gradient(90deg, rgba(244, 63, 94, 0.08) 0%, var(--bg-surface) 100%)',
          }}
        >
          <div className="card-header" style={{ marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--status-risk-bg)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--status-risk-text)',
                }}
              >
                <AlertTriangle size={18} />
              </div>
              <div>
                <h2>{ambiguousClasses.length} Ambiguous Label Categories Detected</h2>
                <p>
                  These labels frequently generate conflicting annotations and likely require updated labeling guidelines or sub-class refinement.
                </p>
              </div>
            </div>

            <span className="badge badge-risk">
              {ambiguousClasses.length} flagged
            </span>
          </div>

          <div className="ambiguity-callout-list">
            {ambiguousClasses.map((item) => (
              <div key={item.label} className="ambiguity-callout-item">
                <AlertTriangle size={14} />
                <strong>{item.label}</strong>
                <span className="mono-cell">
                  {formatPercent(item.disagreement_rate)} Disagreement
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Merged Single Rich Visualization Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-subtle)' }}>
          <div className="card-header" style={{ marginBottom: 0 }}>
            <div>
              <h2>Class Disagreement &amp; Friction Analysis</h2>
              <p>
                Consolidated breakdown displaying disagreement progress bars, comparison volumes, and ambiguity statuses.
              </p>
            </div>
            <span className="badge badge-info">{classes.length} classes analyzed</span>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '1.5rem' }}>
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="skeleton-row" />
            ))}
          </div>
        ) : classes.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">
              <CheckCircle2 size={26} />
            </div>
            <h3>No Class Disagreement Detected</h3>
            <p>There are no category comparisons available for this project yet.</p>
          </div>
        ) : (
          <div className="table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
            <table>
              <thead>
                <tr>
                  <th
                    style={{ cursor: 'pointer' }}
                    onClick={() => handleSort('label')}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <span>Class Label</span>
                      <ArrowUpDown size={12} />
                    </div>
                  </th>
                  <th
                    style={{ minWidth: '260px', cursor: 'pointer' }}
                    onClick={() => handleSort('disagreement_rate')}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <span>Disagreement Rate</span>
                      <ArrowUpDown size={12} />
                    </div>
                  </th>
                  <th
                    style={{ cursor: 'pointer' }}
                    onClick={() => handleSort('occurrences')}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <span>Occurrences</span>
                      <ArrowUpDown size={12} />
                    </div>
                  </th>
                  <th
                    style={{ cursor: 'pointer' }}
                    onClick={() => handleSort('disagreements')}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <span>Disagreements</span>
                      <ArrowUpDown size={12} />
                    </div>
                  </th>
                  <th>Comparisons</th>
                  <th style={{ textAlign: 'right', paddingRight: '1.5rem' }}>Quality Tier</th>
                </tr>
              </thead>

              <tbody>
                {classes.map((item) => {
                  const pct = Math.min((item.disagreement_rate || 0) * 100, 100);
                  const isAmbiguous = item.ambiguous;

                  return (
                    <tr
                      key={item.label}
                      style={{
                        background: isAmbiguous ? 'rgba(244, 63, 94, 0.04)' : undefined,
                      }}
                    >
                      <td>
                        <strong>{item.label}</strong>
                      </td>

                      <td>
                        <div className="disagreement-cell-bar">
                          <div className="progress-track">
                            <div
                              className={`progress-fill ${
                                isAmbiguous ? 'high-disagreement' : ''
                              }`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span
                            className="mono-cell"
                            style={{
                              minWidth: '50px',
                              fontWeight: 600,
                              color: isAmbiguous
                                ? 'var(--status-risk-text)'
                                : 'var(--text-secondary)',
                            }}
                          >
                            {formatPercent(item.disagreement_rate)}
                          </span>
                        </div>
                      </td>

                      <td className="mono-cell">{item.occurrences}</td>

                      <td className="mono-cell">{item.disagreements}</td>

                      <td className="mono-cell">{item.total_comparisons}</td>

                      <td style={{ textAlign: 'right', paddingRight: '1.5rem' }}>
                        {isAmbiguous ? (
                          <span className="badge badge-risk">
                            <AlertTriangle size={11} />
                            <span>Ambiguous</span>
                          </span>
                        ) : (
                          <span className="badge badge-good">
                            <CheckCircle2 size={11} />
                            <span>Clear</span>
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default AmbiguityInsights;