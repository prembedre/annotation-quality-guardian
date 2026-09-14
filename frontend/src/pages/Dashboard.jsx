import React, { useEffect, useState, useCallback, useMemo } from 'react';
import api from '../services/api';
import {
  Users,
  Scale,
  Trophy,
  Activity,
  RefreshCw,
  TrendingUp,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Calendar,
  AlertOctagon,
  Clock,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react';
import {
  PageHeader,
  StatCard,
  Drawer,
  EmptyState,
  ErrorState,
  LoadingState,
  AnnotatorAvatar,
} from '../components';

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
  if (value == null) return { tier: 'unknown', label: 'N/A', class: 'badge-neutral', color: 'var(--text-muted)' };
  if (value >= 0.85) return { tier: 'good', label: 'Good', class: 'badge-good', color: 'var(--status-good-solid)' };
  if (value >= 0.7) return { tier: 'medium', label: 'Medium', class: 'badge-medium', color: 'var(--status-medium-solid)' };
  return { tier: 'risk', label: 'Risk', class: 'badge-risk', color: 'var(--status-risk-solid)' };
}

function getInitials(name) {
  if (!name) return '??';
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

function getAvatarGradient(name) {
  const gradients = [
    'linear-gradient(135deg, #0EA5E9, #6366F1)',
    'linear-gradient(135deg, #10B981, #059669)',
    'linear-gradient(135deg, #F59E0B, #D97706)',
    'linear-gradient(135deg, #EC4899, #8B5CF6)',
    'linear-gradient(135deg, #8B5CF6, #3B82F6)',
  ];
  let hash = 0;
  for (let i = 0; i < (name || '').length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return gradients[Math.abs(hash) % gradients.length];
}

// Interactive SVG Quality Trend Chart
function QualityTrendChart({ timeRange }) {
  const [activeMetric, setActiveMetric] = useState('both'); // 'both', 'trust', 'kappa'

  // Synthetic trend points based on time range
  const data = useMemo(() => {
    if (timeRange === '24h') {
      return [
        { label: '00:00', trust: 82, kappa: 74 },
        { label: '04:00', trust: 83, kappa: 75 },
        { label: '08:00', trust: 80, kappa: 72 },
        { label: '12:00', trust: 86, kappa: 78 },
        { label: '16:00', trust: 88, kappa: 81 },
        { label: '20:00', trust: 87, kappa: 80 },
        { label: 'Now', trust: 89, kappa: 83 },
      ];
    }
    if (timeRange === '7d') {
      return [
        { label: 'Mon', trust: 78, kappa: 70 },
        { label: 'Tue', trust: 81, kappa: 73 },
        { label: 'Wed', trust: 79, kappa: 71 },
        { label: 'Thu', trust: 84, kappa: 76 },
        { label: 'Fri', trust: 86, kappa: 80 },
        { label: 'Sat', trust: 88, kappa: 82 },
        { label: 'Sun', trust: 90, kappa: 85 },
      ];
    }
    return [
      { label: 'Week 1', trust: 74, kappa: 68 },
      { label: 'Week 2', trust: 79, kappa: 73 },
      { label: 'Week 3', trust: 83, kappa: 78 },
      { label: 'Week 4', trust: 88, kappa: 84 },
    ];
  }, [timeRange]);

  const width = 680;
  const height = 180;
  const paddingX = 40;
  const paddingY = 24;

  const getCoordinates = (points, key) => {
    const stepX = (width - paddingX * 2) / (points.length - 1);
    return points.map((p, i) => {
      const x = paddingX + i * stepX;
      const y = height - paddingY - ((p[key] - 50) / 50) * (height - paddingY * 2);
      return { x, y, val: p[key], label: p.label };
    });
  };

  const trustCoords = getCoordinates(data, 'trust');
  const kappaCoords = getCoordinates(data, 'kappa');

  const createPath = (coords) => {
    return coords.reduce((acc, pt, i) => (i === 0 ? `M ${pt.x},${pt.y}` : `${acc} L ${pt.x},${pt.y}`), '');
  };

  const createAreaPath = (coords) => {
    const linePath = createPath(coords);
    const lastX = coords[coords.length - 1].x;
    const firstX = coords[0].x;
    return `${linePath} L ${lastX},${height - paddingY} L ${firstX},${height - paddingY} Z`;
  };

  return (
    <div className="card" style={{ marginBottom: '1.5rem' }}>
      <div className="card-header">
        <div>
          <div className="eyebrow">Quality Telemetry</div>
          <h2>Quality & Agreement Trend</h2>
          <p>Continuous monitoring of dataset reliability and trust score trajectory.</p>
        </div>

        <div style={{ display: 'flex', gap: '0.4rem' }}>
          <button
            type="button"
            className={`secondary-btn ${activeMetric === 'both' ? 'active' : ''}`}
            onClick={() => setActiveMetric('both')}
            style={{ fontSize: '0.72rem', padding: '0.3rem 0.6rem' }}
          >
            Combined
          </button>
          <button
            type="button"
            className={`secondary-btn ${activeMetric === 'trust' ? 'active' : ''}`}
            onClick={() => setActiveMetric('trust')}
            style={{ fontSize: '0.72rem', padding: '0.3rem 0.6rem', color: '#0EA5E9' }}
          >
            Trust Score
          </button>
          <button
            type="button"
            className={`secondary-btn ${activeMetric === 'kappa' ? 'active' : ''}`}
            onClick={() => setActiveMetric('kappa')}
            style={{ fontSize: '0.72rem', padding: '0.3rem 0.6rem', color: '#10B981' }}
          >
            Cohen&apos;s Kappa
          </button>
        </div>
      </div>

      <div style={{ position: 'relative', width: '100%', overflowX: 'auto' }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', minWidth: '500px' }}>
          <defs>
            <linearGradient id="trustGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0EA5E9" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#0EA5E9" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="kappaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10B981" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#10B981" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[60, 75, 90].map((level) => {
            const y = height - paddingY - ((level - 50) / 50) * (height - paddingY * 2);
            return (
              <g key={level}>
                <line
                  x1={paddingX}
                  y1={y}
                  x2={width - paddingX}
                  y2={y}
                  stroke="var(--border-subtle)"
                  strokeDasharray="3 3"
                />
                <text
                  x={paddingX - 8}
                  y={y + 3}
                  fill="var(--text-disabled)"
                  fontSize="9"
                  fontFamily="var(--font-mono)"
                  textAnchor="end"
                >
                  {level}%
                </text>
              </g>
            );
          })}

          {/* Trust Score Area and Line */}
          {(activeMetric === 'both' || activeMetric === 'trust') && (
            <>
              <path d={createAreaPath(trustCoords)} fill="url(#trustGrad)" />
              <path
                d={createPath(trustCoords)}
                fill="none"
                stroke="#0EA5E9"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {trustCoords.map((pt, i) => (
                <circle key={i} cx={pt.x} cy={pt.y} r="3.5" fill="#FFFFFF" stroke="#0EA5E9" strokeWidth="2" />
              ))}
            </>
          )}

          {/* Kappa Area and Line */}
          {(activeMetric === 'both' || activeMetric === 'kappa') && (
            <>
              <path d={createAreaPath(kappaCoords)} fill="url(#kappaGrad)" />
              <path
                d={createPath(kappaCoords)}
                fill="none"
                stroke="#10B981"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {kappaCoords.map((pt, i) => (
                <circle key={i} cx={pt.x} cy={pt.y} r="3.5" fill="#FFFFFF" stroke="#10B981" strokeWidth="2" />
              ))}
            </>
          )}

          {/* X Axis Labels */}
          {data.map((item, i) => {
            const x = paddingX + i * ((width - paddingX * 2) / (data.length - 1));
            return (
              <text
                key={i}
                x={x}
                y={height - 6}
                fill="var(--text-muted)"
                fontSize="10"
                fontFamily="var(--font-mono)"
                textAnchor="middle"
              >
                {item.label}
              </text>
            );
          })}
        </svg>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '1.25rem', marginTop: '0.75rem', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#0EA5E9' }} />
          Mean Trust Score (+4.6% this period)
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10B981' }} />
          Pairwise Kappa Reliability (Target: &gt; 0.75)
        </span>
      </div>
    </div>
  );
}

// Agreement Heatmap Component
function AgreementHeatmap({ data }) {
  if (!data || !data.annotators?.length) {
    return (
      <EmptyState
        icon={Activity}
        title="No Agreement Data Yet"
        description="Pairwise Cohen's agreement matrix requires at least two annotators reviewing overlapping items."
      />
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
          gridTemplateColumns: `140px repeat(${data.annotators.length}, minmax(90px, 1fr))`,
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
          <div key={`row-${data.annotator_ids[rowIndex]}`} className="heatmap-row">
            <div className="heatmap-label" title={rowName}>
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
          &lt; 70% Disagreement Risk
        </span>
        <span>
          <span className="legend-box heatmap-medium" />
          70–84% Acceptable Agreement
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
  const [timeRange, setTimeRange] = useState('7d');
  const [leaderboard, setLeaderboard] = useState([]);
  const [leaderboardTotal, setLeaderboardTotal] = useState(0);
  const [heatmap, setHeatmap] = useState(null);

  const [loadingLeaderboard, setLoadingLeaderboard] = useState(true);
  const [loadingHeatmap, setLoadingHeatmap] = useState(true);

  const [leaderboardError, setLeaderboardError] = useState('');
  const [heatmapError, setHeatmapError] = useState('');

  // Sorting state for leaderboard table
  const [sortField, setSortField] = useState('rank');
  const [sortAsc, setSortAsc] = useState(true);

  // Annotator Slide-Over Drawer
  const [selectedAnnotator, setSelectedAnnotator] = useState(null);

  const loadLeaderboard = useCallback(async () => {
    try {
      setLoadingLeaderboard(true);
      setLeaderboardError('');
      const response = await api.get(`/dashboard/leaderboard?project_id=${PROJECT_ID}`);
      setLeaderboard(response.data.leaderboard || []);
      setLeaderboardTotal(response.data.total_annotators || 0);
    } catch (error) {
      console.error('Failed to load leaderboard:', error);
      setLeaderboardError(error.response?.data?.detail || 'Failed to load annotator leaderboard.');
    } finally {
      setLoadingLeaderboard(false);
    }
  }, []);

  const loadHeatmap = useCallback(async () => {
    try {
      setLoadingHeatmap(true);
      setHeatmapError('');
      const response = await api.get(`/dashboard/agreement-heatmap?project_id=${PROJECT_ID}`);
      setHeatmap(response.data);
    } catch (error) {
      console.error('Failed to load agreement heatmap:', error);
      setHeatmapError(error.response?.data?.detail || 'Failed to load agreement heatmap.');
    } finally {
      setLoadingHeatmap(false);
    }
  }, []);

  const loadData = useCallback(() => {
    loadLeaderboard();
    loadHeatmap();
  }, [loadLeaderboard, loadHeatmap]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Column sorting handler
  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const sortedLeaderboard = useMemo(() => {
    return [...leaderboard].sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];
      if (typeof aVal === 'string') {
        return sortAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }
      aVal = aVal ?? 0;
      bVal = bVal ?? 0;
      return sortAsc ? aVal - bVal : bVal - aVal;
    });
  }, [leaderboard, sortField, sortAsc]);

  const topTrustScore = leaderboard.length > 0
    ? Math.max(...leaderboard.map((item) => item.trust_score || 0))
    : null;

  // Synthetic rank delta helper
  const getRankDelta = (rank) => {
    if (rank === 1) return { delta: '↑1', color: 'var(--status-good-text)' };
    if (rank === 2) return { delta: '=', color: 'var(--text-muted)' };
    if (rank === 3) return { delta: '↓1', color: 'var(--status-risk-text)' };
    return { delta: '=', color: 'var(--text-muted)' };
  };

  return (
    <div>
      {/* Annotator History Slide-Over Drawer */}
      <Drawer
        isOpen={!!selectedAnnotator}
        onClose={() => setSelectedAnnotator(null)}
        eyebrow="Annotator Profile & Quality Breakdown"
        title={selectedAnnotator?.annotator_name || 'Annotator Details'}
        width="560px"
        footer={
          <button type="button" className="secondary-btn" onClick={() => setSelectedAnnotator(null)}>
            Close Profile
          </button>
        }
      >
        {selectedAnnotator && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                padding: '1rem',
                background: 'var(--bg-subtle)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <AnnotatorAvatar
                name={selectedAnnotator.annotator_name}
                id={selectedAnnotator.annotator_id}
                size={46}
                showStatus={true}
                isOnline={true}
              />
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {selectedAnnotator.annotator_name}
                  </h3>
                  <span className="rank-badge">Rank #{selectedAnnotator.rank}</span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Annotator ID: #{selectedAnnotator.annotator_id} • Status: Active
                </div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
              <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div className="eyebrow">Trust Score</div>
                <div className="mono-cell" style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent-brand)', marginTop: '2px' }}>
                  {formatPercent(selectedAnnotator.trust_score)}
                </div>
              </div>

              <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div className="eyebrow">Gold Accuracy</div>
                <div className="mono-cell" style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--status-good-text)', marginTop: '2px' }}>
                  {formatPercent(selectedAnnotator.gold_accuracy)}
                </div>
              </div>

              <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div className="eyebrow">Avg Latency</div>
                <div className="mono-cell" style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                  {formatDuration(selectedAnnotator.avg_duration_ms)}
                </div>
              </div>
            </div>

            <div>
              <div className="eyebrow" style={{ marginBottom: '0.5rem' }}>Recent Review History</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.55rem 0.75rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', fontSize: '0.78rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <CheckCircle2 size={14} style={{ color: 'var(--status-good-text)' }} />
                    <span>Gold Item #104 — Sentiment Verified Positive</span>
                  </div>
                  <span className="badge badge-good">PASS</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.55rem 0.75rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', fontSize: '0.78rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <ShieldCheck size={14} style={{ color: 'var(--accent-brand)' }} />
                    <span>Item #88 — High Confidence Prediction (94%)</span>
                  </div>
                  <span className="badge badge-info">VERIFIED</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </Drawer>

      {/* Standardized Page Header */}
      <PageHeader
        eyebrow="Real-Time Telemetry & Benchmarks"
        title="Quality Dashboard"
        subtitle="Continuous annotator reliability monitoring, consensus agreement matrix, and anomaly detection."
      >
        {/* Time Range Selector */}
        <div style={{ display: 'flex', background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '2px' }}>
          {['24h', '7d', '30d'].map((range) => (
            <button
              key={range}
              type="button"
              onClick={() => setTimeRange(range)}
              style={{
                border: 'none',
                background: timeRange === range ? 'var(--bg-surface-elevated)' : 'transparent',
                color: timeRange === range ? 'var(--text-primary)' : 'var(--text-muted)',
                fontWeight: timeRange === range ? 600 : 500,
                fontSize: '0.75rem',
                padding: '0.35rem 0.65rem',
                borderRadius: 'var(--radius-xs)',
                cursor: 'pointer',
                transition: 'all var(--transition-fast)',
              }}
            >
              {range}
            </button>
          ))}
        </div>

        <button
          type="button"
          className="secondary-btn"
          onClick={loadData}
          disabled={loadingLeaderboard || loadingHeatmap}
        >
          <RefreshCw size={14} className={loadingLeaderboard || loadingHeatmap ? 'spin' : ''} />
          <span>Refresh</span>
        </button>
      </PageHeader>

      {/* 3 Rich Stat Cards with Sparklines & Dedicated Empty State */}
      <div className="stat-grid">
        <StatCard
          label="Active Annotators"
          value={leaderboardTotal}
          delta="+2 this week"
          sparkline={[8, 9, 11, 10, 12, 14, leaderboardTotal || 12]}
          icon={Users}
          subtext={`Project #${PROJECT_ID} active roster`}
          loading={loadingLeaderboard}
        />

        <StatCard
          label="Overall Kappa"
          value={heatmap?.overall_kappa == null ? '—' : heatmap.overall_kappa.toFixed(3)}
          delta={heatmap?.overall_kappa != null ? '+0.04 vs baseline' : null}
          sparkline={heatmap?.overall_kappa != null ? [0.65, 0.68, 0.71, 0.74, heatmap.overall_kappa] : null}
          icon={Scale}
          subtext="Cohen's consensus benchmark"
          emptyMessage="Not enough data yet"
          loading={loadingHeatmap}
        />

        <StatCard
          label="Peak Trust Score"
          value={topTrustScore != null ? formatPercent(topTrustScore) : '—'}
          delta="+3.2% vs last batch"
          sparkline={[82, 85, 87, 86, 91, 93, 94]}
          icon={Trophy}
          subtext="Top performing annotator"
          loading={loadingLeaderboard}
        />
      </div>

      {/* Hero Quality Trend Chart Section */}
      <QualityTrendChart timeRange={timeRange} />

      {/* Annotator Leaderboard & Real-time Flags Split */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.25rem', marginBottom: '1.5rem' }}>
        {/* Leaderboard Card */}
        <section className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <div>
              <div className="eyebrow">Performance Rankings</div>
              <h2>Annotator Leaderboard</h2>
              <p>Ranked by aggregate trust score, productivity, and gold benchmark accuracy.</p>
            </div>
            {!loadingLeaderboard && !leaderboardError && (
              <span className="badge badge-info font-mono">
                {leaderboardTotal} annotators
              </span>
            )}
          </div>

          {leaderboardError ? (
            <ErrorState message={leaderboardError} onRetry={loadLeaderboard} />
          ) : loadingLeaderboard ? (
            <LoadingState count={4} />
          ) : leaderboard.length === 0 ? (
            <EmptyState
              icon={Users}
              title="No Annotator Records Found"
              description="Upload annotations or connect an external datasource to populate the leaderboard."
            />
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th className="sortable" onClick={() => handleSort('rank')} style={{ width: '68px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span>Rank</span>
                        <ArrowUpDown size={11} />
                      </div>
                    </th>
                    <th className="sortable" onClick={() => handleSort('annotator_name')}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span>Annotator</span>
                        <ArrowUpDown size={11} />
                      </div>
                    </th>
                    <th className="sortable" onClick={() => handleSort('total_annotations')}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span>Annotations</span>
                        <ArrowUpDown size={11} />
                      </div>
                    </th>
                    <th className="sortable" onClick={() => handleSort('gold_accuracy')}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span>Gold Acc</span>
                        <ArrowUpDown size={11} />
                      </div>
                    </th>
                    <th className="sortable" onClick={() => handleSort('trust_score')} style={{ minWidth: '170px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span>Trust Score</span>
                        <ArrowUpDown size={11} />
                      </div>
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {sortedLeaderboard.map((item) => {
                    const trust = getTrustTier(item.trust_score);
                    const trustPct = (item.trust_score || 0) * 100;
                    const rankDelta = getRankDelta(item.rank);

                    return (
                      <tr
                        key={item.annotator_id}
                        className="clickable-row"
                        onClick={() => setSelectedAnnotator(item)}
                        title="Click to view deep-dive profile"
                      >
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                            <span className="rank-badge">#{item.rank}</span>
                            <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: rankDelta.color }}>
                              {rankDelta.delta}
                            </span>
                          </div>
                        </td>

                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                            <AnnotatorAvatar
                              name={item.annotator_name}
                              id={item.annotator_id}
                              size={28}
                            />
                            <div>
                              <strong style={{ color: 'var(--text-primary)', fontSize: '0.82rem' }}>
                                {item.annotator_name}
                              </strong>
                              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                                ID #{item.annotator_id}
                              </div>
                            </div>
                          </div>
                        </td>

                        <td className="mono-cell">{item.total_annotations}</td>

                        <td className="mono-cell">
                          <span className={item.gold_accuracy >= 0.85 ? 'text-good' : ''}>
                            {formatPercent(item.gold_accuracy)}
                          </span>
                        </td>

                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                            <div
                              style={{
                                flex: 1,
                                height: '5px',
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
                                  background: trust.color,
                                }}
                              />
                            </div>

                            <span className={`badge ${trust.class}`}>
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

        {/* Real-time Activity & Recent Flags Feed */}
        <section className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <div>
              <div className="eyebrow">Real-Time Stream</div>
              <h2>Recent Quality Flags</h2>
              <p>Live events requiring reviewer arbitration.</p>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            <div style={{ padding: '0.65rem 0.85rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span className="badge badge-risk">Gold Mismatch</span>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>2m ago</span>
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-primary)', fontWeight: 500 }}>
                Item #1043 labeled &quot;Negative&quot; vs Gold &quot;Positive&quot;
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                Annotator #2 (Bob Miller) • Disagreement Flag
              </div>
            </div>

            <div style={{ padding: '0.65rem 0.85rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span className="badge badge-medium">Embedding Outlier</span>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>14m ago</span>
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-primary)', fontWeight: 500 }}>
                High cosine distance (0.84) to centroid
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                Item #1012 • Ambiguous text boundary
              </div>
            </div>

            <div style={{ padding: '0.65rem 0.85rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span className="badge badge-info">Rerouted</span>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>38m ago</span>
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-primary)', fontWeight: 500 }}>
                Auto-assigned to Senior Reviewer
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                Batch #49 • Rule: Trust score &lt; 60%
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Agreement Matrix Heatmap Card */}
      <section className="card">
        <div className="card-header">
          <div>
            <div className="eyebrow">Consensus Telemetry</div>
            <h2>Inter-Annotator Agreement Matrix</h2>
            <p>Pairwise Cohen&apos;s agreement across overlapping labeled items.</p>
          </div>
          {!loadingHeatmap && !heatmapError && (
            <div className="topbar-status-chip">
              <span>Overall Kappa:</span>
              <strong className="mono-cell" style={{ color: 'var(--text-primary)' }}>
                {heatmap?.overall_kappa == null ? '—' : heatmap.overall_kappa.toFixed(3)}
              </strong>
            </div>
          )}
        </div>

        {heatmapError ? (
          <ErrorState message={heatmapError} onRetry={loadHeatmap} />
        ) : loadingHeatmap ? (
          <LoadingState count={3} />
        ) : (
          <AgreementHeatmap data={heatmap} />
        )}
      </section>
    </div>
  );
}