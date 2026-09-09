import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Users, Scale, Trophy, Activity, RefreshCw } from 'lucide-react';

const PROJECT_ID = 1;

function formatPercent(value) {
  if (value == null) return '—';
  return `${(value * 100).toFixed(1)}%`;
}

function formatDuration(value) {
  if (value == null) return '—';
  if (value >= 1000) {
    return `${(value / 1000).toFixed(2)}s`;
  }
  return `${value.toFixed(0)}ms`;
}

function getTrustTier(value) {
  if (value == null) return { tier: 'unknown', label: 'N/A', class: '' };
  if (value >= 0.85) return { tier: 'good', label: 'Good', class: 'dashboard-good' };
  if (value >= 0.7) return { tier: 'medium', label: 'Medium', class: 'dashboard-medium' };
  return { tier: 'risk', label: 'Risk', class: 'dashboard-low' };
}

function getInitials(name) {
  if (!name) return '??';
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

function getAvatarColor(name) {
  const colors = [
    'linear-gradient(135deg, #6366F1, #8B5CF6)',
    'linear-gradient(135deg, #06B6D4, #3B82F6)',
    'linear-gradient(135deg, #10B981, #059669)',
    'linear-gradient(135deg, #F59E0B, #D97706)',
    'linear-gradient(135deg, #EC4899, #8B5CF6)',
  ];
  let hash = 0;
  for (let i = 0; i < (name || '').length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

function AgreementHeatmap({ data }) {
  if (!data || !data.annotators?.length) {
    return (
      <div className="empty-state">
        <Activity size={24} style={{ color: 'var(--text-muted)', marginBottom: '0.5rem' }} />
        <p>No agreement data available for this project.</p>
      </div>
    );
  }

  const getCell = (rowIndex, columnIndex) => {
    const value = data.matrix?.[rowIndex]?.[columnIndex];
    if (value == null) return '—';
    return formatPercent(value);
  };

  const getCellClass = (value) => {
    if (value == null) return 'heatmap-cell heatmap-na';
    if (value >= 0.85) return 'heatmap-cell heatmap-high';
    if (value >= 0.7) return 'heatmap-cell heatmap-medium';
    return 'heatmap-cell heatmap-low';
  };

  const getOverlap = (rowIndex, columnIndex) => {
    const rowAnnotatorId = data.annotator_ids?.[rowIndex];
    const columnAnnotatorId = data.annotator_ids?.[columnIndex];

    const cell = data.cells?.find(
      (item) =>
        item.annotator_a_id === rowAnnotatorId &&
        item.annotator_b_id === columnAnnotatorId
    );

    return cell?.overlap_count ?? null;
  };

  return (
    <div className="heatmap-wrapper">
      <div
        className="heatmap-grid"
        style={{
          gridTemplateColumns: `130px repeat(${data.annotators.length}, minmax(85px, 1fr))`,
        }}
      >
        <div className="heatmap-corner" />

        {data.annotators.map((name, index) => (
          <div
            key={`column-${data.annotator_ids[index]}`}
            className="heatmap-label"
            title={name}
          >
            {name}
          </div>
        ))}

        {data.annotators.map((rowName, rowIndex) => (
          <div
            key={`row-${data.annotator_ids[rowIndex]}`}
            className="heatmap-row"
          >
            <div className="heatmap-label heatmap-row-label" title={rowName}>
              {rowName}
            </div>

            {data.annotators.map((columnName, columnIndex) => {
              const value = data.matrix?.[rowIndex]?.[columnIndex];
              const overlap = getOverlap(rowIndex, columnIndex);

              return (
                <div
                  key={`${rowIndex}-${columnIndex}`}
                  className={getCellClass(value)}
                  title={`${rowName} ↔ ${columnName}: ${
                    value == null ? 'N/A' : formatPercent(value)
                  }${overlap != null ? ` • ${overlap} overlapping items` : ''}`}
                >
                  {getCell(rowIndex, columnIndex)}
                </div>
              );
            })}
          </div>
        ))}
      </div>

      <div className="heatmap-legend">
        <span>
          <span className="legend-box heatmap-na" />
          N/A
        </span>
        <span>
          <span className="legend-box heatmap-low" />
          &lt; 70% Agreement
        </span>
        <span>
          <span className="legend-box heatmap-medium" />
          70–84% Moderate
        </span>
        <span>
          <span className="legend-box heatmap-high" />
          85%+ High Agreement
        </span>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [leaderboardTotal, setLeaderboardTotal] = useState(0);
  const [heatmap, setHeatmap] = useState(null);

  const [loadingLeaderboard, setLoadingLeaderboard] = useState(true);
  const [loadingHeatmap, setLoadingHeatmap] = useState(true);

  const [leaderboardError, setLeaderboardError] = useState('');
  const [heatmapError, setHeatmapError] = useState('');

  const loadData = async () => {
    // Leaderboard
    try {
      setLoadingLeaderboard(true);
      setLeaderboardError('');
      const response = await api.get(
        `/dashboard/leaderboard?project_id=${PROJECT_ID}`
      );
      setLeaderboard(response.data.leaderboard || []);
      setLeaderboardTotal(response.data.total_annotators || 0);
    } catch (error) {
      console.error('Failed to load leaderboard:', error);
      setLeaderboardError(
        error.response?.data?.detail || 'Failed to load annotator leaderboard.'
      );
    } finally {
      setLoadingLeaderboard(false);
    }

    // Heatmap
    try {
      setLoadingHeatmap(true);
      setHeatmapError('');
      const response = await api.get(
        `/dashboard/agreement-heatmap?project_id=${PROJECT_ID}`
      );
      setHeatmap(response.data);
    } catch (error) {
      console.error('Failed to load agreement heatmap:', error);
      setHeatmapError(
        error.response?.data?.detail || 'Failed to load agreement heatmap.'
      );
    } finally {
      setLoadingHeatmap(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const topTrustScore =
    leaderboard.length > 0
      ? Math.max(...leaderboard.map((item) => item.trust_score || 0))
      : null;

  return (
    <div>
      {/* Streamlined Single Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Quality Dashboard</h1>
          <p className="page-subtitle">
            Real-time annotator performance telemetry and inter-annotator agreement metrics.
          </p>
        </div>

        <button
          type="button"
          className="secondary-btn"
          onClick={loadData}
          disabled={loadingLeaderboard || loadingHeatmap}
        >
          <RefreshCw
            size={14}
            className={loadingLeaderboard || loadingHeatmap ? 'spin' : ''}
          />
          <span>Refresh</span>
        </button>
      </div>

      {/* Top Stat Metrics */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-label">Active Annotators</span>
            <div className="stat-icon">
              <Users size={16} />
            </div>
          </div>
          <div className="stat-value">{leaderboardTotal}</div>
          <div className="stat-subtext">Registered for Project {PROJECT_ID}</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-label">Overall Kappa</span>
            <div className="stat-icon">
              <Scale size={16} />
            </div>
          </div>
          <div className="stat-value">
            {heatmap?.overall_kappa == null
              ? '—'
              : heatmap.overall_kappa.toFixed(3)}
          </div>
          <div className="stat-subtext">Inter-annotator reliability</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-label">Peak Trust Score</span>
            <div className="stat-icon">
              <Trophy size={16} />
            </div>
          </div>
          <div className="stat-value">
            {topTrustScore != null ? formatPercent(topTrustScore) : '—'}
          </div>
          <div className="stat-subtext">Top performing annotator</div>
        </div>
      </div>

      {/* Leaderboard Card */}
      <section className="card">
        <div className="card-header">
          <div>
            <h2>Annotator Leaderboard</h2>
            <p>Ranked by aggregate trust score, productivity, and gold benchmark accuracy.</p>
          </div>
          <span className="badge badge-info">
            {leaderboardTotal} annotator{leaderboardTotal === 1 ? '' : 's'}
          </span>
        </div>

        {leaderboardError && (
          <div className="alert">
            <span>{leaderboardError}</span>
          </div>
        )}

        {loadingLeaderboard ? (
          <div style={{ padding: '1rem 0' }}>
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="skeleton-row" />
            ))}
          </div>
        ) : leaderboard.length === 0 ? (
          <div className="empty-state">
            <Users size={24} style={{ color: 'var(--text-muted)', marginBottom: '0.5rem' }} />
            <h3>No Annotator Data</h3>
            <p>No annotator records found for this project yet.</p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th style={{ width: '60px' }}>Rank</th>
                  <th>Annotator</th>
                  <th>Total Annotations</th>
                  <th>Gold Accuracy</th>
                  <th>Confidence</th>
                  <th>Avg Duration</th>
                  <th style={{ minWidth: '200px' }}>Trust Score</th>
                </tr>
              </thead>

              <tbody>
                {leaderboard.map((item) => {
                  const trust = getTrustTier(item.trust_score);
                  const trustPct = (item.trust_score || 0) * 100;

                  return (
                    <tr key={item.annotator_id}>
                      <td>
                        <span className="rank-badge">#{item.rank}</span>
                      </td>

                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <div
                            style={{
                              width: '32px',
                              height: '32px',
                              borderRadius: '50%',
                              background: getAvatarColor(item.annotator_name),
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontWeight: 700,
                              fontSize: '0.75rem',
                              color: '#fff',
                              flexShrink: 0,
                            }}
                          >
                            {getInitials(item.annotator_name)}
                          </div>
                          <div>
                            <strong>{item.annotator_name}</strong>
                            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                              ID #{item.annotator_id}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td className="mono-cell">{item.total_annotations}</td>

                      <td className="mono-cell">{formatPercent(item.gold_accuracy)}</td>

                      <td className="mono-cell">{formatPercent(item.avg_confidence)}</td>

                      <td className="mono-cell">{formatDuration(item.avg_duration_ms)}</td>

                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <div
                            style={{
                              flex: 1,
                              height: '6px',
                              background: 'var(--bg-surface-elevated)',
                              borderRadius: 'var(--radius-full)',
                              overflow: 'hidden',
                            }}
                          >
                            <div
                              style={{
                                width: `${Math.min(trustPct, 100)}%`,
                                height: '100%',
                                borderRadius: 'var(--radius-full)',
                                background:
                                  trust.tier === 'good'
                                    ? 'var(--status-good-solid)'
                                    : trust.tier === 'medium'
                                    ? 'var(--status-medium-solid)'
                                    : 'var(--status-risk-solid)',
                              }}
                            />
                          </div>

                          <span className={`trust-badge ${trust.class}`}>
                            <span className="mono-cell">{formatPercent(item.trust_score)}</span>
                          </span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Agreement Heatmap Card */}
      <section className="card">
        <div className="card-header">
          <div>
            <h2>Inter-Annotator Agreement Matrix</h2>
            <p>Pairwise Cohen&apos;s agreement across overlapping labeled items.</p>
          </div>
          <div className="topbar-badge-project">
            <span>Overall Kappa:</span>
            <strong className="mono-cell" style={{ color: 'var(--text-primary)' }}>
              {heatmap?.overall_kappa == null ? '—' : heatmap.overall_kappa.toFixed(3)}
            </strong>
          </div>
        </div>

        {heatmapError && (
          <div className="alert">
            <span>{heatmapError}</span>
          </div>
        )}

        {loadingHeatmap ? (
          <div style={{ padding: '2rem 0' }}>
            {[1, 2, 3].map((i) => (
              <div key={i} className="skeleton-row" />
            ))}
          </div>
        ) : (
          <AgreementHeatmap data={heatmap} />
        )}
      </section>
    </div>
  );
}